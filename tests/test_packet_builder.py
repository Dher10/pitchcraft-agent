"""P2.4 packets: one sealed case becomes a packet and findings through the live pipeline's own code, as of the day before.

The sources are the leaky ones of tests/test_as_of_end_to_end.py (Statcast rows from the game day and later, a Savant
month with post-cutoff home runs); any MLB request, any Savant request outside the faked month and any print fails the
test. Game logs are SYNTHETIC with the fields of the real answer.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from urllib.parse import parse_qs, urlparse

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from evals import build_packets as bp
from tests.test_as_of_end_to_end import CUTOFF, GAME_DAY, STATCAST, batting_csv
from tests.test_packet_season_line import answer, row

SEASON = (date(2026, 3, 25), date(2026, 9, 27))

RAW_GAME = {
    "gamePk": 1,
    "gameType": "R",
    "officialDate": GAME_DAY,
    "gameDate": f"{GAME_DAY}T23:05:00Z",
    "seriesGameNumber": 2,
    "status": {"abstractGameState": "Final", "detailedState": "Final"},
    "venue": {"id": 3313, "name": "Yankee Stadium"},
    "teams": {
        "away": {"team": {"id": 111, "name": "Boston Red Sox"}, "probablePitcher": {"id": 11, "fullName": "Away Ace"}},
        "home": {"team": {"id": 147, "name": "New York Yankees"}, "probablePitcher": {"id": 22, "fullName": "Home Ace"}},
    },
}
RECORD = {
    "case_id": "veteran-1",
    "game_pk": 1,
    "official_date": GAME_DAY,
    "as_of": CUTOFF,
    "stratum": "veteran",
    "pitcher_ids": [11, 22],
    "series": None,
    "series_ended": None,
}

# 37 batters faced before the game (the Statcast fixture has 37 plate appearances up to the cutoff), then a game-day row.
LOG = [
    row("2026-07-01", "6.0", 2, 5, 1, 7, 1, 20),
    row("2026-07-08", "5.2", 3, 6, 2, 4, 0, 17),
    row(GAME_DAY, "9.0", 9, 20, 9, 77, 9, 99),
]


def histories(log=LOG):
    return (answer(deepcopy(log)), answer(deepcopy(log)))


@pytest.fixture(autouse=True)
def sealed_sources(monkeypatch, tmp_path, capsys):
    """Everything the build may touch is faked; a request nobody expected fails the test."""

    def refuse(*args, **kwargs):
        raise AssertionError(f"unexpected request {args[:1]}")

    savant = []
    monkeypatch.setattr(lp, "_get_json", refuse)
    monkeypatch.setattr(lp.urllib.request, "urlopen", refuse)
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "statcast_pitcher", lambda start, end, player_id: STATCAST.copy())
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(lp, "season_dates", refuse)  # the builder supplies the season, it never asks

    def fake_savant(url, timeout=60):
        savant.append(url)
        query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        return batting_csv(query["team"], query["game_date_gt"])

    monkeypatch.setattr(lp, "_get_text", fake_savant)
    lp.reset_run_budgets()
    return savant


def build(record=RECORD, raw=RAW_GAME, logs=None):
    return bp.build_case(record, raw, logs or histories(), SEASON, "2026-10-30")


def test_the_build_makes_no_mlb_request_and_no_savant_request_outside_the_cutoff(sealed_sources):
    built = build()

    assert built.case_id == "veteran-1"
    assert sealed_sources  # the lineup splits did ask Savant for the partial month
    assert all(parse_qs(urlparse(url).query)["game_date_lt"][0] <= CUTOFF for url in sealed_sources)


def test_the_season_line_is_the_sum_of_the_rows_before_the_game():
    summary = build().packet["starters"]["away_starter"]["season_summary"]

    assert (summary["era"], summary["whip"], summary["innings"]) == ("3.86", "1.20", "11.2")
    assert (summary["strikeouts"], summary["walks"], summary["home_runs_allowed"]) == (11, 3, 1)


def test_nothing_from_the_game_day_reaches_the_packet_or_the_findings():
    built = build()
    text = json.dumps([built.packet, built.findings])

    assert "77" not in {str(built.packet["starters"][s]["season_summary"]["strikeouts"]) for s in ("away_starter", "home_starter")}
    assert "2026-07-15" not in json.dumps(built.packet["starters"])
    assert "2026-07-14" in text


def test_both_starters_are_built_as_of_the_day_before():
    built = build()

    assert built.live_game["as_of"] == CUTOFF
    for slot in ("away_starter", "home_starter"):
        starter = built.packet["starters"][slot]
        assert starter["sample"]["arsenal"]["scope"]["through"] == CUTOFF
        assert starter["sample"]["arsenal"]["pitches"] == 150


@pytest.mark.parametrize("as_of", [GAME_DAY, "2026-07-16", "2026-07-13", None, ""])
def test_an_as_of_other_than_the_day_before_is_refused(as_of):
    with pytest.raises(ValueError):
        build({**RECORD, "as_of": as_of})


def test_the_game_is_upcoming_as_of_the_day_before_and_its_final_state_is_not_in_the_packet():
    built = build()

    assert built.packet["status"] == "upcoming"
    assert built.packet["data_confidence"]["lineup_status"] != "game_started"
    assert "Final" not in json.dumps(built.packet) and "final" not in json.dumps(built.packet["game"])


def test_the_packet_is_the_scout_packet_and_the_findings_are_the_analysts():
    built = build()

    assert set(built.packet["availability"]) >= {"game", "teams", "away_starter", "home_starter"}
    assert isinstance(built.findings["matchup_headline"], str) and built.findings["matchup_headline"]


def test_a_regular_season_game_has_no_series():
    assert build().packet["series"] is None


def postseason(number, standing, ended=False, leak=None):
    raw = deepcopy(RAW_GAME)
    raw.update(gameType="D", seriesGameNumber=number, seriesDescription="AL Division Series", gamesInSeries=5)
    if leak:
        raw["seriesStatus"] = {"result": leak, "isOver": True}  # a hydrated final standing must never be read
    games_played = number - 1
    record = {**RECORD, "stratum": "postseason", "series_ended": ended}
    record["series"] = {"game_number": number, "games_played": games_played, "result": standing, "is_over": False}
    return record, raw


def test_a_later_postseason_game_carries_the_standing_before_first_pitch_from_the_record():
    record, raw = postseason(3, "BOS leads 2-0")

    series = build(record, raw).packet["series"]

    assert series["series_name"] == "AL Division Series"
    assert series["game_number"] == 3
    assert series["standing"] == "BOS leads 2-0"


def test_game_one_has_no_prior_result():
    record, raw = postseason(1, None)

    series = build(record, raw).packet["series"]

    assert series["game_number"] == 1 and series["standing"] is None


def test_the_game_that_ended_its_series_shows_no_final_result_anywhere():
    record, raw = postseason(4, "BOS leads 2-1", ended=True, leak="BOS wins 3-1")
    built = build(record, raw)
    text = json.dumps([built.packet, built.findings])

    assert built.packet["series"]["standing"] == "BOS leads 2-1"
    assert " wins " not in text and "3-1" not in text


def test_a_standing_that_is_not_the_one_before_the_game_is_refused():
    record, raw = postseason(3, "BOS leads 2-0")
    record["series"]["games_played"] = 3

    with pytest.raises(bp.PacketError):
        build(record, raw)


def test_a_postseason_record_without_its_series_is_refused():
    record, raw = postseason(3, "BOS leads 2-0")
    record["series"] = None

    with pytest.raises(bp.PacketError):
        build(record, raw)


def test_a_history_of_another_pitcher_is_refused():
    other = histories()
    other[0]["stats"][0]["splits"][0]["player"] = {"id": 999, "fullName": "Someone Else"}

    with pytest.raises(bp.PacketError, match="999"):
        build(logs=other)


def test_a_raw_game_that_is_not_the_case_is_refused():
    with pytest.raises(bp.PacketError):
        build(raw={**RAW_GAME, "gamePk": 2})
    with pytest.raises(bp.PacketError):
        build(raw={**RAW_GAME, "officialDate": "2026-07-16"})


def test_starters_that_are_not_the_recorded_pitchers_are_refused():
    with pytest.raises(bp.PacketError):
        build({**RECORD, "pitcher_ids": [11, 23]})


def test_a_starter_the_pipeline_cannot_build_stops_the_build_with_its_error(monkeypatch):
    monkeypatch.setattr(lp, "statcast_pitcher", lambda start, end, player_id: None)

    with pytest.raises(bp.PacketError, match="statcast_pitcher"):
        build()


def test_the_pipelines_own_game_check_passes_and_is_recorded():
    assert build().notes["unsafe"] is None


def test_the_notes_say_where_the_season_line_came_from():
    notes = build().notes

    assert notes["season_line_source"] == "gameLog rows dated before the game date"
    assert notes["season_line_check"] == [["no 2026 line in yearByYear"], ["no 2026 line in yearByYear"]]
    assert notes["errors"] == [] and notes["warnings"] == []


def test_the_build_prints_nothing(capsys):
    capsys.readouterr()

    build()

    assert capsys.readouterr().out == ""


def test_the_same_inputs_give_byte_identical_output():
    first, second = build(), build()

    assert bp.canonical(first.packet) == bp.canonical(second.packet)
    assert bp.canonical(first.findings) == bp.canonical(second.findings)


def test_a_request_the_ledger_refused_stops_the_build_instead_of_leaving_a_hole():
    with pytest.raises(bp.rl.CeilingReached):
        bp.build_case(RECORD, RAW_GAME, histories(), SEASON, "2026-10-30", refused=lambda: True)


def test_the_recorded_season_must_agree_with_the_saved_calendar():
    bp.check_season(SEASON)
    with pytest.raises(bp.PacketError):
        bp.check_season((date(2026, 3, 25), date(2026, 9, 28)))


def test_the_game_record_is_the_one_the_daily_fetch_builds():
    record = lp.game_record({**RAW_GAME, "status": {"abstractGameState": "Preview", "detailedState": "Scheduled"}})

    assert record["official_date"] == GAME_DAY and record["away_pitcher_id"] == 11 and record["home_team_abbr"] == "NYY"
    assert record["status"] == "Preview"
