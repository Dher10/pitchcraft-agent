"""P2.4 gate 4a: the schedule and per-pitcher adapters of the collection (docs/plans/P2.4.md sections 2 and 4).

The schedule games are the real objects of tests/fixtures/mlb_schedule_states_2026-09.json (a final game, a postponed
one, a cancelled one) with a `probablePitcher` added to each side. The `gameLog` and `yearByYear` answers are
SYNTHETIC: written from the API documentation because no answer of those kinds was recorded; the shape check is strict
so the first real answer either matches or stops the collection.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.fetchers.mlb_schemas import SourceShapeError
from evals import collect_sources as cs
from evals import request_ledger as rl

REAL = json.loads((Path(__file__).parent / "fixtures" / "mlb_schedule_states_2026-09.json").read_text(encoding="utf-8"))["games"]


def listed(game, away=(11, "Away Ace"), home=(22, "Home Ace")):
    game = deepcopy(game)
    for side, pitcher in (("away", away), ("home", home)):
        if pitcher is not None:
            game["teams"][side]["probablePitcher"] = {"id": pitcher[0], "fullName": pitcher[1]}
    return game


def schedule_answer(*games):
    by_day = {}
    for g in games:
        by_day.setdefault(g["officialDate"], []).append(g)
    return {"dates": [{"date": d, "games": gs} for d, gs in sorted(by_day.items())]}


def log(date_, ip, bf, started):
    return {"date": date_, "stat": {"inningsPitched": ip, "battersFaced": bf, "gamesStarted": 1 if started else 0, "gamesPlayed": 1}}


def history_answer(game_log, years=(2023, 2024, 2025)):
    return {
        "stats": [
            {"type": {"displayName": "gameLog"}, "splits": game_log},
            {"type": {"displayName": "yearByYear"}, "splits": [{"season": str(y), "stat": {"gamesPlayed": 30}} for y in years]},
        ]
    }


@pytest.fixture
def wire(monkeypatch, tmp_path):
    """Route lp._get_json through a ledger and a table of canned answers, recording every url that reaches the 'network'."""

    sent = []
    answers = {}

    def get_json(url, timeout=8):
        sent.append(url)
        for fragment, answer in answers.items():
            if fragment in url:
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise AssertionError(f"unexpected request {url}")

    monkeypatch.setattr(lp, "_get_json", get_json)
    ledger = rl.RequestLedger(tmp_path / "ledger.jsonl")
    with rl.counted_mlb(ledger):
        yield sent, answers, ledger


# --- the schedule -----------------------------------------------------------------------------------------


def test_one_request_per_range_is_counted_as_a_schedule_lookup(wire):
    sent, answers, ledger = wire
    answers["/schedule?"] = schedule_answer(listed(REAL["final"]))

    games = cs.fetch_schedule(date(2026, 9, 1), date(2026, 9, 30))

    assert len(sent) == 1 and "startDate=2026-09-01&endDate=2026-09-30" in sent[0] and "hydrate=probablePitcher" in sent[0]
    assert ledger.count("mlb") == 1 and ledger.rows[0]["source"] == "mlb_schedule"
    assert [g.game_pk for g in games] == [REAL["final"]["gamePk"]]


def test_only_a_game_that_really_ended_is_final(wire):
    _, answers, _ = wire
    answers["/schedule?"] = schedule_answer(listed(REAL["final"]), listed(REAL["postponed"]), listed(REAL["cancelled"]))

    games = {g.game_pk: g.final for g in cs.fetch_schedule(date(2026, 9, 1), date(2026, 10, 15))}

    assert games[REAL["final"]["gamePk"]] is True
    assert games[REAL["postponed"]["gamePk"]] is False  # control: the abstract state of both is "Final"
    assert games[REAL["cancelled"]["gamePk"]] is False
    assert REAL["postponed"]["status"]["abstractGameState"] == "Final"


def test_starters_are_listed_away_first_and_a_missing_one_is_none(wire):
    _, answers, _ = wire
    answers["/schedule?"] = schedule_answer(listed(REAL["final"], away=(11, "A"), home=None))

    (game,) = cs.fetch_schedule(date(2026, 9, 1), date(2026, 9, 30))

    assert game.starters == ((11, "A"), None)


@pytest.mark.parametrize("damage", [lambda g: g.pop("gameType"), lambda g: g["status"].pop("detailedState"), lambda g: g["teams"]["away"].pop("team")])
def test_a_malformed_schedule_answer_stops_with_a_shape_error_after_being_counted(wire, damage):
    _, answers, ledger = wire
    bad = listed(REAL["final"])
    damage(bad)
    answers["/schedule?"] = schedule_answer(bad)

    with pytest.raises(SourceShapeError):
        cs.fetch_schedule(date(2026, 9, 1), date(2026, 9, 30))

    assert ledger.count("mlb") == 1  # the request was sent, so it is counted


def test_a_failed_request_is_counted_and_marked_failed(wire):
    _, answers, ledger = wire
    answers["/schedule?"] = OSError("down")

    with pytest.raises(OSError):
        cs.fetch_schedule(date(2026, 9, 1), date(2026, 9, 30))

    assert ledger.rows[-1]["outcome"] == "failed" and ledger.pending() == []


# --- the per-pitcher history ------------------------------------------------------------------------------


def games_of_a_season():
    return [
        log("2026-04-02", "5.0", 21, True),
        log("2026-04-08", "1.2", 8, True),  # one and two thirds
        log("2026-04-14", "1.0", 5, False),  # a relief appearance: not a start
        log("2026-04-20", "0.2", 4, True),
    ]


def test_one_lookup_serves_every_game_of_that_pitcher_and_is_cached_on_disk(wire, tmp_path):
    sent, answers, ledger = wire
    answers["/people/11/stats"] = history_answer(games_of_a_season())
    store = cs.HistoryStore(tmp_path / "h", 2026)

    first = store.get(11)
    again = store.get(11)
    reopened = cs.HistoryStore(tmp_path / "h", 2026).get(11)

    assert len(sent) == 1 and store.lookups == 1 and ledger.count("mlb") == 1 and ledger.rows[0]["source"] == "mlb_people"
    assert first is again and reopened == first
    assert "stats=gameLog,yearByYear" in sent[0] and "season=2026" in sent[0]


def test_a_cached_record_that_no_longer_matches_its_digest_is_refused(wire, tmp_path):
    _, answers, _ = wire
    answers["/people/11/stats"] = history_answer(games_of_a_season())
    cs.HistoryStore(tmp_path / "h", 2026).get(11)
    path = tmp_path / "h" / "11_2026.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["response"]["stats"][0]["splits"][0]["stat"]["battersFaced"] = 99
    path.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(SourceShapeError):
        cs.HistoryStore(tmp_path / "h", 2026).get(11)


def test_facts_use_only_rows_before_the_game(wire, tmp_path):
    _, answers, _ = wire
    answers["/people/11/stats"] = history_answer(games_of_a_season())
    history = cs.HistoryStore(tmp_path / "h", 2026).get(11)

    before_third = cs.facts_as_of(history, "2026-04-14")  # as_of 2026-04-13: two starts, 26 batters
    same_day = cs.facts_as_of(history, "2026-04-08")  # the row of the game day itself is not before it
    after = cs.facts_as_of(history, "2026-05-01")

    assert before_third.samples["control"] == 29 == 21 + 8 and before_third.samples["strikeout"] == 29
    assert same_day.samples["control"] == 21
    assert after.samples["control"] == 21 + 8 + 5 + 4
    assert before_third.previous_innings == (5.0, 1 + 2 / 3)  # the relief appearance is not a start
    assert after.previous_innings == (5.0, 1 + 2 / 3, 2 / 3)


def test_no_row_before_the_game_is_a_measured_zero_and_no_previous_start_is_an_empty_tuple(wire, tmp_path):
    _, answers, _ = wire
    answers["/people/11/stats"] = history_answer(games_of_a_season())
    facts = cs.facts_as_of(cs.HistoryStore(tmp_path / "h", 2026).get(11), "2026-04-02")

    assert facts.samples == {"strikeout": 0, "control": 0, "arsenal": None}
    assert facts.previous_innings == ()


def test_batters_faced_prove_the_arsenal_threshold_but_never_a_shortfall(wire, tmp_path):
    _, answers, _ = wire
    rows = [log(f"2026-04-{day:02d}", "6.0", 25, True) for day in range(2, 6)]  # 100 batters faced
    answers["/people/11/stats"] = history_answer(rows)
    history = cs.HistoryStore(tmp_path / "h", 2026).get(11)

    assert cs.facts_as_of(history, "2026-04-06").samples["arsenal"] == 100  # 100 batters = at least 100 pitches
    assert cs.facts_as_of(history, "2026-04-05").samples["arsenal"] is None  # 75 batters: pitches unknown, not "below"


def test_an_unreadable_figure_is_unknown_not_zero(wire, tmp_path):
    _, answers, _ = wire
    rows = games_of_a_season()
    del rows[1]["stat"]["battersFaced"]
    rows[0]["stat"]["inningsPitched"] = "garbage"
    answers["/people/11/stats"] = history_answer(rows)
    facts = cs.facts_as_of(cs.HistoryStore(tmp_path / "h", 2026).get(11), "2026-04-14")

    assert facts.samples["control"] is None  # one row without batters faced: the sum is unknown
    assert facts.previous_innings == (None, 1 + 2 / 3)


def test_prior_seasons_count_only_seasons_before_this_one_with_games(wire, tmp_path):
    _, answers, _ = wire
    answer = history_answer(games_of_a_season(), years=(2022, 2023, 2024, 2025))
    answer["stats"][1]["splits"].append({"season": "2026", "stat": {"gamesPlayed": 4}})  # this season is not a prior one
    answer["stats"][1]["splits"].append({"season": "2021", "stat": {"gamesPlayed": 0}})  # a season with no game
    answers["/people/11/stats"] = answer

    assert cs.HistoryStore(tmp_path / "h", 2026).get(11).prior_seasons == 4


def test_a_missing_year_by_year_block_is_an_unknown_count(wire, tmp_path):
    _, answers, _ = wire
    answer = history_answer(games_of_a_season())
    del answer["stats"][1]
    answers["/people/11/stats"] = answer

    history = cs.HistoryStore(tmp_path / "h", 2026).get(11)

    assert history.prior_seasons is None
    assert cs.facts_as_of(history, "2026-05-01").prior_seasons is None  # an unknown count never qualifies a veteran


@pytest.mark.parametrize(
    "damage",
    [
        lambda a: a["stats"].pop(0),  # no game log at all
        lambda a: a["stats"][0]["splits"][0].pop("date"),
        lambda a: a["stats"][0]["splits"][0]["stat"].update(battersFaced=-1),
        lambda a: a["stats"][1]["splits"][0].pop("season"),
        lambda a: a.pop("stats"),
    ],
    ids=["no-game-log", "row-without-date", "negative-count", "season-missing", "no-stats"],
)
def test_a_malformed_history_stops_closed_is_counted_and_never_cached(wire, tmp_path, damage):
    _, answers, ledger = wire
    answer = history_answer(games_of_a_season())
    damage(answer)
    answers["/people/11/stats"] = answer

    with pytest.raises(SourceShapeError):
        cs.HistoryStore(tmp_path / "h", 2026).get(11)

    assert ledger.count("mlb") == 1 and not (tmp_path / "h" / "11_2026.json").exists()


def test_the_people_ceiling_stops_the_lookup_before_anything_is_sent(wire, tmp_path, monkeypatch):
    sent, answers, ledger = wire
    answers["/people/"] = history_answer(games_of_a_season())
    monkeypatch.setitem(rl.CEILINGS, "mlb", 1)
    store = cs.HistoryStore(tmp_path / "h", 2026)
    store.get(11)

    with pytest.raises(rl.CeilingReached):
        store.get(12)

    assert len(sent) == 1
