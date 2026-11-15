"""R4-D3: game identity, results and the envelope of a game file (D66, docs/DATA_CONTRACT.md section 7).

No network. The one real file is the World Series game 1 report the daily job published on 2026-10-23 (commit abf58e1),
kept as a fixture; the schedule days are built here and are synthetic, with the real `gamePk` 849805 of that game
(tests/fixtures/mlb_series_2026-10.json) and **invented scores**.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from data_pipeline import archive_games as ag
from data_pipeline.fetchers import mlb_schemas
from data_pipeline.validators import validate_payload

FIXTURES = Path(__file__).parent / "fixtures"
PUBLISHED = json.loads((FIXTURES / "archive_published_ws_g1.json").read_text(encoding="utf-8"))


def schedule_game(pk=849805, day="2026-10-23", away=139, home=158, away_pp=607259, home_pp=694819, abstract="Final",
                  detailed="Final", away_score=3, home_score=5, winners=None, start="2026-10-24T00:00:00Z",
                  game_type="W", series_status=None, **extra):
    game = {
        "gamePk": pk, "gameType": game_type, "officialDate": day, "gameDate": start,
        "status": {"abstractGameState": abstract, "detailedState": detailed},
        "seriesDescription": "World Series", "seriesGameNumber": 1, "gamesInSeries": 7,
        "seriesStatus": series_status if series_status is not None else {"isOver": False, "result": "MIL leads 1-0"},
        "venue": {"name": "American Family Field"},
        "teams": {
            "away": {"team": {"id": away, "name": "Tampa Bay Rays"}, "score": away_score,
                     "isWinner": (home_score < away_score) if winners is None else winners[0],
                     "probablePitcher": {"id": away_pp, "fullName": "Nick Martinez"}},
            "home": {"team": {"id": home, "name": "Milwaukee Brewers"}, "score": home_score,
                     "isWinner": (home_score > away_score) if winners is None else winners[1],
                     "probablePitcher": {"id": home_pp, "fullName": "Jacob Misiorowski"}},
        },
    }
    game.update(extra)
    return game


def day(*games):
    return {"dates": [{"games": list(games)}]}


def records(*games):
    return ag.parse_day(day(*games))


# --- ids ------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["849805", "100000", "123456789"])
def test_a_game_pk_text_is_accepted(value):
    assert ag.is_game_pk(value)


@pytest.mark.parametrize(
    "value",
    ["", "0", "012345", "99999", "1234567890", "849805/", "../849805", "849805.json", " 849805", "849805\n", "٨٤٩٨٠٥",
     "84980a", "-849805", None, 849805, 849805.0, True],
)
def test_anything_else_is_not_a_game_pk_so_no_path_is_ever_built_from_it(value):
    assert not ag.is_game_pk(value)


def test_the_day_url_names_the_postseason_types_and_the_hydrations():
    url = ag.day_url("2026-10-23")
    assert "date=2026-10-23" in url and "gameType=F,D,L,W" in url
    assert "probablePitcher" in url and "seriesStatus" in url
    for bad in ("2026-10-3", "2026-13-01", "20261023", "2026-10-23&x=1", "", None):
        with pytest.raises((ValueError, TypeError)):
            ag.day_url(bad)


# --- the schedule shape -------------------------------------------------------------------------------------------------

def test_a_valid_empty_day_is_valid():
    assert ag.parse_day({"dates": []}) == []
    assert ag.parse_day({"dates": [{"games": []}]}) == []


def _without(value, path):
    value = deepcopy(value)
    node = value
    for step in path[:-1]:
        node = node[step]
    del node[path[-1]]
    return value


@pytest.mark.parametrize(
    "path", [path for path, _ in mlb_schemas.required_paths(ag.ARCHIVE_SCHEDULE_DAY)], ids=lambda p: ".".join(map(str, p))
)
def test_every_required_field_of_the_day_is_required(path):
    """One negative test per required path: a missing field is a source failure, never a defaulted game."""

    data = day(schedule_game())
    full = [step if not isinstance(step, int) else 0 for step in path]
    # the schema paths use 0 for list elements; "dates" and "games" lists are walked as such
    broken = _without(data, full)
    with pytest.raises(mlb_schemas.SourceShapeError):
        ag.parse_day(broken)


@pytest.mark.parametrize("bad", [None, [], "x", {"dates": None}, {"message": "Internal error"}, {"dates": [{}]}])
def test_a_malformed_answer_is_an_error_not_an_empty_day(bad):
    with pytest.raises(mlb_schemas.SourceShapeError):
        ag.parse_day(bad)


# --- results ---------------------------------------------------------------------------------------------------------

def test_a_final_game_has_its_score_and_winner():
    (record,) = records(schedule_game())
    assert record["status"] == "final"
    assert record["result"] == {"away_runs": 3, "home_runs": 5, "winner": "home"}
    assert record["round"] == "World Series" and record["season"] == 2026 and record["game_pk"] == 849805
    assert record["series"]["after"] == "MIL leads 1-0" and record["series"]["over"] is False


def test_a_measured_zero_is_a_score_not_a_missing_one():
    """Control for rule 2: a shutout is a real 0, kept as 0."""

    (record,) = records(schedule_game(away_score=0, home_score=4))
    assert record["result"] == {"away_runs": 0, "home_runs": 4, "winner": "home"}


@pytest.mark.parametrize(
    ("abstract", "detailed"),
    [("Preview", "Scheduled"), ("Live", "In Progress"), ("Final", "Postponed"), ("Final", "Cancelled"), ("Final", "Suspended"),
     ("Final", "Unknown State")],
)
def test_a_game_that_did_not_end_has_no_result_even_if_the_schedule_sends_a_score(abstract, detailed):
    (record,) = records(schedule_game(abstract=abstract, detailed=detailed, away_score=2, home_score=4))
    assert record["result"] is None
    assert ag.played_games([record]) == []


def test_a_final_game_without_a_score_has_no_result_and_is_not_zero():
    game = schedule_game()
    del game["teams"]["away"]["score"]
    (record,) = records(game)
    assert record["status"] == "final" and record["result"] is None
    assert ag.played_games([record]) == []


def test_equal_scores_and_a_contradicting_winner_flag_are_unavailable():
    assert records(schedule_game(away_score=2, home_score=2))[0]["result"] is None
    assert records(schedule_game(away_score=2, home_score=2, winners=(None, None)))[0]["result"] is None  # no flag to contradict
    assert records(schedule_game(away_score=3, home_score=5, winners=(True, False)))[0]["result"] is None
    assert records(schedule_game(away_score=3, home_score=5, winners=(False, True)))[0]["result"] is not None


@pytest.mark.parametrize("bad", [-1, 3.5, "3", True])
def test_a_score_that_is_not_a_count_is_a_source_failure(bad):
    with pytest.raises(mlb_schemas.SourceShapeError):
        ag.parse_day(day(schedule_game(away_score=bad, winners=(False, True))))


def test_a_postponed_game_is_kept_once_in_its_played_form():
    first = schedule_game(abstract="Final", detailed="Postponed", day="2026-10-10", away_score=0, home_score=0)
    again = schedule_game(abstract="Final", detailed="Final", day="2026-10-11")
    kept = ag.played_games(records(first) + records(again))
    assert [r["date"] for r in kept] == ["2026-10-11"] and len(kept) == 1


def test_two_played_records_of_one_game_that_disagree_are_dropped():
    a = records(schedule_game(away_score=3, home_score=5))
    b = records(schedule_game(away_score=4, home_score=5))
    assert ag.played_games(a + b) == []
    assert len(ag.played_games(a + a)) == 1


def test_played_games_does_not_alias_its_input():
    source = records(schedule_game())
    kept = ag.played_games(source)
    kept[0]["result"]["away_runs"] = 99
    assert source[0]["result"]["away_runs"] == 3


# --- the series line after a game ------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("result", "over", "expected"),
    [("MIL leads 1-0", False, "MIL leads 1-0"), ("Series tied 1-1", False, "Series tied 1-1"),
     ("MIL wins 4-1", True, "MIL wins 4-1")],
)
def test_a_standing_whose_numbers_can_be_true_is_kept(result, over, expected):
    assert ag.series_after(result, over) == expected


@pytest.mark.parametrize(
    ("result", "over"),
    [("MIL leads 1-1", False), ("MIL leads 0-1", False), ("MIL wins 4-1", False), ("MIL leads 4-1", True),
     ("Series tied 0-0", False), ("Series tied 2-1", False), ("Series tied 2-2", True), ("whatever", False),
     ("MIL leads 1-0", None), (None, False), ("MIL leads 1-0 <b>", False)],
)
def test_a_standing_that_cannot_be_true_or_is_not_a_known_text_is_unavailable(result, over):
    assert ag.series_after(result, over) is None


def test_an_unknown_series_name_gives_no_series_and_a_bad_standing_keeps_the_game():
    (record,) = records(schedule_game(seriesDescription="Some Other Series"))
    assert record["series"] is None
    (record,) = records(schedule_game(series_status={"isOver": False, "result": "garbage"}))
    assert record["series"]["after"] is None and record["series"]["over"] is None


# --- recovering the game of a published report ----------------------------------------------------------------------

def test_the_published_report_is_matched_to_exactly_its_game():
    other = schedule_game(pk=849999, away=147, home=111, away_pp=1, home_pp=2)
    matched = ag.match_published_report(PUBLISHED, records(other, schedule_game()))
    assert matched["game_pk"] == 849805


@pytest.mark.parametrize(
    "change",
    [dict(day="2026-10-24"), dict(away=158, home=139), dict(away_pp=1), dict(home_pp=2), dict(away_pp=694819, home_pp=607259)],
    ids=["other day", "teams swapped", "away starter changed", "home starter changed", "starters swapped"],
)
def test_a_report_with_any_difference_matches_no_game(change):
    with pytest.raises(ag.ArchiveError) as caught:
        ag.match_published_report(PUBLISHED, records(schedule_game(**change)))
    assert caught.value.code == ag.GAME_NOT_FOUND


def test_a_game_without_a_probable_starter_is_not_a_match():
    game = schedule_game()
    del game["teams"]["home"]["probablePitcher"]
    with pytest.raises(ag.ArchiveError):
        ag.match_published_report(PUBLISHED, records(game))


def test_two_games_that_fit_the_report_are_refused_not_guessed():
    twin = schedule_game(pk=849806)
    with pytest.raises(ag.ArchiveError) as caught:
        ag.match_published_report(PUBLISHED, records(schedule_game(), twin))
    assert caught.value.code == ag.GAME_NOT_FOUND


def test_a_file_that_is_not_one_matchup_is_refused():
    two = deepcopy(PUBLISHED)
    two["matchups"].append(deepcopy(two["matchups"][0]))
    none = deepcopy(PUBLISHED)
    none["matchups"] = []
    for payload in (two, none, {}, {"matchups": [{}]}):
        with pytest.raises(ag.ArchiveError):
            ag.match_published_report(payload, records(schedule_game()))


# --- origin ------------------------------------------------------------------------------------------------------------

def _origin(run_at, start):
    payload = deepcopy(PUBLISHED)
    payload["metadata"]["data_status"]["live_run"]["run_at"] = run_at
    (record,) = records(schedule_game(start=start))
    return ag.published_origin(payload, record, SOURCE)


def test_a_report_is_published_live_only_when_its_run_was_before_first_pitch():
    live = _origin("2026-10-23T22:05:37+00:00", "2026-10-24T00:00:00Z")
    assert live["kind"] == "published_live" and live["published_at"] == "2026-10-23T22:05:37+00:00"
    assert live["as_of"] == PUBLISHED["metadata"]["data_status"]["live_run"]["as_of"]


@pytest.mark.parametrize("run_at", ["2026-10-24T00:00:00+00:00", "2026-10-24T00:00:01+00:00", "2026-10-25T10:00:00+00:00"])
def test_a_report_made_at_or_after_first_pitch_is_reconstructed(run_at):
    origin = _origin(run_at, "2026-10-24T00:00:00Z")
    assert origin["kind"] == "reconstructed" and origin["published_at"] is None


def test_instants_are_compared_as_instants_not_as_text():
    """A run at 22:05 UTC on the 23rd, written with another offset, is still before a 00:00 UTC start on the 24th."""

    assert _origin("2026-10-23T18:05:37-04:00", "2026-10-24T00:00:00Z")["kind"] == "published_live"
    assert _origin("2026-10-23T20:05:37-04:00", "2026-10-24T00:00:00Z")["kind"] == "reconstructed"


def test_an_unreadable_run_time_is_reconstructed_never_published():
    assert _origin("not a time", "2026-10-24T00:00:00Z")["kind"] == "reconstructed"


# --- the lineage of a published report -------------------------------------------------------------------------------------

def test_todays_checks_refuse_the_published_payload_so_it_is_not_rejudged_with_them():
    """The measured reason for the lineage rule: the file the bot published on 2026-10-23 was written under other
    catalogs, so today's validator refuses it. If this ever passes, the lineage rule can be dropped."""

    from data_pipeline.validators import ValidationError

    with pytest.raises(ValidationError):
        validate_payload(PUBLISHED)


def test_parse_published_gives_the_payload_and_the_hash_of_the_exact_bytes():
    import hashlib

    raw = (FIXTURES / "archive_published_ws_g1.json").read_bytes()
    payload, digest = ag.parse_published(raw)
    assert payload == PUBLISHED and digest == hashlib.sha256(raw).hexdigest()
    assert ag.parse_published(raw + b"\n")[1] != digest  # one byte more is another file


@pytest.mark.parametrize("raw", [b'{"x": NaN}', b'{"x": Infinity}', b"[1]", b"not json", "text", b"\xff"])
def test_parse_published_refuses_what_is_not_a_strict_daily_file(raw):
    with pytest.raises((ValueError, TypeError)):
        ag.parse_published(raw)


def test_a_published_payload_that_is_not_a_live_single_report_is_refused():
    assert ag.published_lineage_problems(PUBLISHED) == []
    cases = {
        "version": lambda p: p["metadata"].__setitem__("version", "0.8.0"),
        "data_mode": lambda p: p["metadata"].__setitem__("data_mode", "demo_cached"),
        "matchups": lambda p: p["matchups"].append(deepcopy(p["matchups"][0])),
        "matchup_mode": lambda p: p["matchups"][0]["data_confidence"].__setitem__("level", "demo_cached"),
        "postgame": lambda p: p["matchups"][0].__setitem__("postgame", {"final_score": {}}),
        "live_run": lambda p: p["metadata"]["data_status"]["live_run"].__setitem__("run_at", "soon"),
    }
    for label, mutate in cases.items():
        payload = deepcopy(PUBLISHED)
        mutate(payload)
        assert label in ag.published_lineage_problems(payload), label
    assert ag.published_lineage_problems({}) == ["shape"]


@pytest.mark.parametrize(
    "source",
    [None, {}, {"commit": "abf58e1", "sha256": "ab" * 32}, {"commit": "a" * 40, "sha256": "AB" * 32},
     {"commit": "a" * 40, "sha256": "ab" * 31}, {"commit": "a" * 40, "sha256": "ab" * 32, "x": 1}],
)
def test_a_published_file_without_its_lineage_is_refused(source):
    document = good_file()
    document["origin"]["source"] = source
    assert ag.validate_game_file(document) != []


def test_a_reconstructed_file_has_no_lineage_and_a_published_one_has_it():
    document = good_file()
    document["origin"].update(kind="reconstructed", published_at=None)
    assert ag.validate_game_file(document) != []  # still has a source
    document["origin"]["source"] = None
    assert ag.validate_game_file(document) == []


# --- the file ---------------------------------------------------------------------------------------------------------

SOURCE = {"commit": "abf58e1" + "0" * 33, "sha256": "ab" * 32}


def good_file():
    (record,) = records(schedule_game())
    origin = ag.published_origin(PUBLISHED, record, SOURCE)
    return ag.build_game_file(record, PUBLISHED, origin)


def test_a_published_report_is_copied_unchanged_into_a_valid_file():
    document = good_file()
    assert document["payload"] == PUBLISHED
    assert document["payload"] is not PUBLISHED
    assert ag.validate_game_file(document) == []
    assert document["origin"]["source"] == SOURCE
    assert ag.published_lineage_problems(document["payload"]) == []
    # Nothing in the file grades, scores or evaluates a game (D41).
    text = ag.compact_json(document)
    for word in ("grade", "game_score", "verdict"):
        assert f'"{word}"' not in text.replace('"pitchcraft_grade"', "")


def test_a_published_file_is_compact_and_deterministic():
    text = ag.compact_json(good_file())
    assert text == ag.compact_json(good_file())
    assert "\n" not in text[:-1] and text.endswith("}\n") and len(text) < 30_000
    assert json.loads(text) == good_file()
    with pytest.raises(ValueError):
        ag.compact_json({"x": float("nan")})


def test_the_starters_of_a_file_are_unknown_until_a_boxscore_says_otherwise():
    document = good_file()
    assert document["starters_check"] == {"away": "unknown", "home": "unknown", "actual": {"away": None, "home": None}}
    assert document["final_line"] == {"away": None, "home": None}


def test_a_game_that_was_not_played_has_no_file():
    for kwargs in (dict(abstract="Final", detailed="Postponed"), dict(abstract="Preview", detailed="Scheduled")):
        (record,) = records(schedule_game(**kwargs))
        with pytest.raises(ag.ArchiveError) as caught:
            ag.build_game_file(record, PUBLISHED, ag.published_origin(PUBLISHED, record))
        assert caught.value.code == ag.GAME_NOT_FOUND


def _set(document, path, value):
    node = document
    for step in path[:-1]:
        node = node[step]
    node[path[-1]] = value
    return document


LINE = {"innings_pitched": "6.1", "hits": 4, "earned_runs": 1, "walks": 2, "strikeouts": 7}
ACTUAL = {"id": 607259, "name": "Nick Martinez"}

MUTATIONS = [
    (("archive_version",), "0.9.0"), (("archive_version",), None),
    (("game_pk",), "849805"), (("game_pk",), 12), (("game_pk",), True),
    (("date",), "2026-10-3"), (("date",), None), (("season",), 2025), (("round",), "Playoffs"),
    (("series",), None), (("teams",), {}), (("teams", "away", "name"), ""),
    (("teams", "away", "id"), None), (("teams", "home", "id"), True), (("teams", "home", "id"), "158"), (("teams", "home", "id"), 0),
    (("series", "after"), 12345), (("series", "over"), "no"), (("series", "game_number"), 0), (("series", "game_number"), "1"),
    (("series", "games_in_series"), 6), (("series", "series_name"), "Playoffs"), (("series", "after"), "MIL leads 1-1"),
    (("result", "status"), "live"), (("result", "away_runs"), -1), (("result", "away_runs"), 5), (("result", "winner"), "away"),
    (("result", "home_runs"), None),
    (("origin", "kind"), "live"), (("origin", "published_at"), None), (("origin", "built_at"), "yesterday"),
    (("origin", "as_of"), "2026-10-24"), (("origin", "as_of"), "2026-10-3"),
    (("starters_check", "away"), "started?"), (("starters_check", "actual"), {"away": None}),
    (("starters_check", "away"), "unknown", ),
    (("final_line", "away"), LINE),  # a line with no named starter who started
    (("starter_facts",), None), (("starter_facts", "away"), {"id": 1}), (("starter_facts", "away"), {"id": 0, "prior_mlb_seasons": 3}),
    (("starter_facts", "away"), {"id": 1, "prior_mlb_seasons": -1}), (("starter_facts", "away"), {"id": 1, "prior_mlb_seasons": 2.5}),
    (("starter_facts", "away"), {"id": 1, "prior_mlb_seasons": True}), (("starter_facts", "away"), {"id": 1, "prior_mlb_seasons": 3, "x": 1}),
    (("payload",), None),
]


@pytest.mark.parametrize(("path", "value"), MUTATIONS, ids=[f"{'.'.join(p)}={str(v)[:20]}" for p, v in MUTATIONS])
def test_every_mutated_envelope_field_is_refused(path, value):
    document = good_file()
    if path == ("starters_check", "away") and value == "unknown":
        document["starters_check"]["away"] = "unknown"
        document["starters_check"]["actual"]["away"] = ACTUAL  # unknown with a named pitcher
    else:
        _set(document, path, value)
    assert ag.validate_game_file(document) != [], path


def test_extra_and_missing_keys_are_refused():
    document = good_file()
    document["grade"] = "A"
    assert "keys" in ag.validate_game_file(document)
    document = good_file()
    del document["final_line"]
    assert "keys" in ag.validate_game_file(document)
    assert ag.validate_game_file(None) == ["document"]


def test_a_final_line_of_a_named_starter_is_valid_and_zero_stays_zero():
    document = good_file()
    document["starters_check"] = {"away": "started", "home": "unknown", "actual": {"away": ACTUAL, "home": None}}
    document["final_line"]["away"] = dict(LINE, hits=0, walks=0)
    assert ag.validate_game_file(document) == []
    document["final_line"]["away"]["hits"] = None  # a field the boxscore did not give is null, never 0
    assert ag.validate_game_file(document) == []


@pytest.mark.parametrize(
    "line",
    [dict(LINE, hits=-1), dict(LINE, hits=2.5), dict(LINE, hits="4"), dict(LINE, innings_pitched="6.3"),
     dict(LINE, innings_pitched=6.1), dict(LINE, innings_pitched="six"), dict(LINE, extra=1), {"hits": 1},
     dict(LINE, grade="A")],
)
def test_a_malformed_final_line_is_refused(line):
    document = good_file()
    document["starters_check"] = {"away": "started", "home": "unknown", "actual": {"away": ACTUAL, "home": None}}
    document["final_line"]["away"] = line
    assert ag.validate_game_file(document) != []


def test_no_closed_code_of_the_family_is_free_text():
    assert ag.ARCHIVE_CODES == ("game_not_found", "starter_unconfirmed", "ceiling_reached")
    assert str(ag.ArchiveError(ag.GAME_NOT_FOUND)) == "game_not_found"


# --- guards ---------------------------------------------------------------------------------------------------------------

def test_the_module_reads_no_sealed_set_and_makes_no_request():
    """D64/D15/D16: R4 imports nothing from evals/, names no sealed path, and has no network or file access."""

    source = Path(ag.__file__).read_text(encoding="utf-8")
    for forbidden in ("import evals", "from evals", ".local", "packets", "requests", "urllib", "socket", "open(", "read_text",
                      "write_text", "public/data", "evals/live"):
        assert forbidden not in source.replace("docs/DATA_CONTRACT.md", ""), forbidden
