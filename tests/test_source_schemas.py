"""One explicit schema per MLB Stats API endpoint, and a negative test for every required field (QA3-02).

The negative tests are generated from the schemas in `mlb_schemas.py`, not listed by hand: add a
required field to a schema and a new case appears. Each case takes a complete valid answer,
breaks one field in the first populated element, runs the real fetcher and expects an empty result
plus one recorded source error that names the path. Valid empty lists and absent optional figures
stay valid.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Any, Callable

import pytest

from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.fetchers import mlb_schemas as schemas
from tests.test_fetchers_as_of import _game_entry, install_urlopen


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )


# --- complete valid answers (every required AND every optional field present) ----------------


def schedule_day() -> dict:
    def side(team_id: int, name: str, pitcher_id: int, pitcher: str) -> dict:
        return {
            "team": {"id": team_id, "name": name},
            "probablePitcher": {"id": pitcher_id, "fullName": pitcher},
        }

    return {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 1,
                        "officialDate": "2026-07-15",
                        "gameDate": "2026-07-15T23:05:00Z",
                        "status": {"abstractGameState": "Preview"},
                        "venue": {"name": "Yankee Stadium", "timeZone": {"id": "America/New_York"}},
                        "teams": {
                            "away": side(111, "Boston Red Sox", 11, "Away Ace"),
                            "home": side(147, "New York Yankees", 22, "Home Ace"),
                        },
                    }
                ],
            }
        ]
    }


def pitcher_stats() -> dict:
    return {
        "stats": [
            {
                "splits": [
                    {
                        "stat": {
                            "era": "3.10",
                            "whip": "1.05",
                            "inningsPitched": "101.0",
                            "strikeOuts": 100,
                            "baseOnBalls": 30,
                            "homeRuns": 10,
                            "battersFaced": 400,
                        }
                    }
                ]
            }
        ]
    }


def team_splits() -> dict:
    def split(code: str) -> dict:
        return {
            "split": {"code": code},
            "stat": {
                "ops": ".700",
                "avg": ".250",
                "plateAppearances": 200,
                "strikeOuts": 40,
                "baseOnBalls": 20,
            },
        }

    return {"stats": [{"splits": [split("vl"), split("vr")]}]}


def series_window() -> dict:
    # Game 2 (final, with its standing) and game 3, the game being previewed.
    return {"dates": [{"games": [_game_entry(102), _game_entry(103)]}]}


def person() -> dict:
    return {"people": [{"pitchHand": {"code": "L"}}]}


def seasons() -> dict:
    return {
        "seasons": [{"regularSeasonStartDate": "2026-03-25", "regularSeasonEndDate": "2026-09-27"}]
    }


# --- how each real fetcher is called, and what "it failed" looks like ------------------------


@dataclass(frozen=True)
class Case:
    name: str
    schema: Any
    prefix: tuple[Any, ...]  # where in the answer this schema applies
    answer: Callable[[], dict]
    call: Callable[[], Any]
    failed: Callable[[Any], bool]  # the fetcher's empty result
    source: str | None  # the recorded error's source; None: the call raises instead


_REAL_SEASON_DATES = lp.season_dates  # the autouse fixture replaces it for the other cases


def _seasons_call() -> Any:
    _REAL_SEASON_DATES.__wrapped__(2026)  # without the lru_cache


CASES = [
    Case("schedule", schemas.SCHEDULE_DAY, (), schedule_day,
         lambda: lp.fetch_todays_games("2026-07-15"), lambda r: r == [], "mlb_schedule"),
    Case("pitcher_stats", schemas.PITCHER_STATS, (), pitcher_stats,
         lambda: lp.fetch_pitcher_season_stats(11, as_of="2026-07-14"), lambda r: r == {},
         "mlb_season_stats"),
    Case("team_splits", schemas.TEAM_SPLITS, (), team_splits,
         lambda: lp.fetch_team_splits(147, season=2026), lambda r: r == {}, "mlb_team_splits"),
    Case("series_schedule", schemas.SERIES_SCHEDULE, (), series_window,
         lambda: lp.fetch_series_status(103, as_of="2026-10-05"), lambda r: r == {},
         "mlb_series_status"),
    # The standing of the last earlier final game: required only on that game.
    Case("series_status", schemas.SERIES_STATUS, ("dates", 0, "games", 0, "seriesStatus"),
         series_window, lambda: lp.fetch_series_status(103, as_of="2026-10-05"),
         lambda r: r == {}, "mlb_series_status"),
    Case("person", schemas.PERSON, (), person, lambda: lp.fetch_pitcher_hand(11),
         lambda r: r is None, "mlb_person"),
    Case("seasons", schemas.SEASONS, (), seasons, _seasons_call, lambda r: False, None),
]
BY_NAME = {case.name: case for case in CASES}


def at(data: Any, path: tuple[Any, ...]) -> Any:
    for step in path:
        data = data[step]
    return data


def broken(case: Case, relative: tuple[Any, ...], action: str, value: Any = None) -> dict:
    """The case's valid answer with the field at `relative` deleted, replaced or emptied."""

    assert relative, "the root cannot be broken"
    data = case.answer()
    parent = at(data, (*case.prefix, *relative[:-1]))
    key = relative[-1]
    if action == "delete":
        del parent[key]
    else:
        parent[key] = value
    return data


def run(monkeypatch, case: Case, data: dict) -> tuple[Any, list[dict], Exception | None]:
    install_urlopen(monkeypatch, lambda url: data)
    result, error = None, None
    try:
        result = case.call()
    except Exception as exc:  # noqa: BLE001 - the case decides whether raising is expected
        error = exc
    return result, list(lp._run_errors), error


def expect_failure(monkeypatch, case: Case, data: dict, path: tuple[Any, ...]) -> None:
    result, errors, raised = run(monkeypatch, case, data)
    shown = schemas.format_path(path)
    if case.source is None:
        assert isinstance(raised, schemas.SourceShapeError), f"{case.name}: {shown} was accepted"
        assert shown in str(raised)
        return
    assert raised is None
    assert case.failed(result), f"{case.name}: {shown} was accepted, result {result!r}"
    assert [e["source"] for e in errors] == [case.source], f"{case.name}: {shown} left no error"
    assert shown in errors[0]["message"], errors[0]["message"]


def expect_success(monkeypatch, case: Case, data: dict) -> Any:
    result, errors, raised = run(monkeypatch, case, data)
    assert raised is None, raised
    assert errors == []
    return result


def ids(items):
    return [f"{case.name}:{schemas.format_path(path)}" for case, path, *_ in items]


REQUIRED = [(case, path, node) for case in CASES for path, node in schemas.required_paths(case.schema)]
OPTIONAL = [(case, path) for case in CASES for path, _ in schemas.optional_paths(case.schema)]
LISTS = [(case, path, node.min_items) for case in CASES for path, node in schemas.list_paths(case.schema)]
NON_EMPTY = [(case, path) for case in CASES for path, _ in schemas.non_empty_paths(case.schema)]


# --- the fixtures are complete, so every control below tests something -----------------------


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_the_valid_answer_is_valid_for_the_schema_and_the_fetcher(monkeypatch, case):
    schemas.validate(case.schema, at(case.answer(), case.prefix))
    expect_success(monkeypatch, case, case.answer())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_the_valid_answer_carries_every_field_the_schema_knows(case):
    data = at(case.answer(), case.prefix)
    for path, _ in [*schemas.required_paths(case.schema), *schemas.optional_paths(case.schema)]:
        at(data, path)  # raises KeyError/IndexError when the fixture lacks the field


# --- negative: one test per required field, generated from the schemas -----------------------


@pytest.mark.parametrize(("case", "path", "node"), REQUIRED, ids=ids(REQUIRED))
def test_a_missing_required_field_is_a_recorded_source_failure(monkeypatch, case, path, node):
    expect_failure(monkeypatch, case, broken(case, path, "delete"), path)


@pytest.mark.parametrize(("case", "path", "node"), REQUIRED, ids=ids(REQUIRED))
def test_a_required_field_replaced_by_an_error_envelope_is_a_recorded_source_failure(
    monkeypatch, case, path, node
):
    wrong = "Internal error" if isinstance(node, schemas.Obj) else {"message": "Internal error"}
    expect_failure(monkeypatch, case, broken(case, path, "set", wrong), path)


@pytest.mark.parametrize(("case", "path"), NON_EMPTY, ids=ids(NON_EMPTY))
def test_an_object_with_none_of_the_expected_figures_is_a_recorded_source_failure(
    monkeypatch, case, path
):
    data = broken(case, path, "set", {"message": "Internal error"})
    expect_failure(monkeypatch, case, data, path)


@pytest.mark.parametrize(("case", "path", "minimum"), [x for x in LISTS if x[2]], ids=ids([x for x in LISTS if x[2]]))
def test_a_list_that_needs_an_element_is_a_failure_when_empty(monkeypatch, case, path, minimum):
    expect_failure(monkeypatch, case, broken(case, path, "set", []), path)


# --- controls: what stays valid ----------------------------------------------------------------


@pytest.mark.parametrize(("case", "path", "minimum"), [x for x in LISTS if not x[2]], ids=ids([x for x in LISTS if not x[2]]))
def test_a_valid_empty_list_is_not_a_failure(monkeypatch, case, path, minimum):
    if not path:
        pytest.skip("the root is not a list")
    expect_success(monkeypatch, case, broken(case, path, "set", []))


@pytest.mark.parametrize(("case", "path"), OPTIONAL, ids=ids(OPTIONAL))
def test_an_absent_optional_field_is_not_a_failure(monkeypatch, case, path):
    expect_success(monkeypatch, case, broken(case, path, "delete"))


@pytest.mark.parametrize("figure", ["strikeOuts", "baseOnBalls", "homeRuns", "battersFaced"])
def test_an_absent_pitcher_count_is_none_never_zero(monkeypatch, figure):
    data = pitcher_stats()
    del data["stats"][0]["splits"][0]["stat"][figure]
    install_urlopen(monkeypatch, lambda url: data)

    result = lp.fetch_pitcher_season_stats(11, as_of="2026-07-14")

    names = {"strikeOuts": "strikeouts", "baseOnBalls": "walks", "homeRuns": "home_runs_allowed",
             "battersFaced": "batters_faced"}
    assert result[names[figure]] is None
    assert lp._run_errors == []


@pytest.mark.parametrize("figure", ["strikeOuts", "baseOnBalls", "plateAppearances", "ops", "avg"])
def test_an_absent_team_split_figure_is_none_never_zero(monkeypatch, figure):
    data = team_splits()
    del data["stats"][0]["splits"][0]["stat"][figure]
    install_urlopen(monkeypatch, lambda url: data)

    result = lp.fetch_team_splits(147, season=2026)

    names = {"strikeOuts": "strikeouts", "baseOnBalls": "walks", "plateAppearances": "plate_appearances",
             "ops": "ops", "avg": "avg"}
    assert result["vl"][names[figure]] is None
    assert lp._run_errors == []


def test_a_game_without_a_probable_pitcher_is_still_a_game(monkeypatch):
    data = schedule_day()
    del data["dates"][0]["games"][0]["teams"]["away"]["probablePitcher"]
    install_urlopen(monkeypatch, lambda url: data)

    games = lp.fetch_todays_games("2026-07-15")

    assert len(games) == 1 and games[0]["away_pitcher_id"] is None
    assert lp._run_errors == []


# --- the three QA probes, by name --------------------------------------------------------------


def test_the_qa_probe_a_split_without_a_stat_object_is_not_an_unavailable_pitcher(monkeypatch):
    install_urlopen(monkeypatch, lambda url: {"stats": [{"splits": [{"message": "Internal error"}]}]})

    assert lp.fetch_pitcher_season_stats(11, as_of="2026-07-14") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_season_stats"]
    assert "stats[0].splits[0].stat" in lp._run_errors[0]["message"]


def test_the_qa_probe_a_team_split_without_a_stat_object_is_a_failure(monkeypatch):
    split = {"split": {"code": "vr"}, "message": "Internal error"}
    install_urlopen(monkeypatch, lambda url: {"stats": [{"splits": [split]}]})

    assert lp.fetch_team_splits(147, season=2026) == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_team_splits"]
    assert "stats[0].splits[0].stat" in lp._run_errors[0]["message"]


def test_the_qa_probe_an_earlier_final_game_without_series_status_is_a_failure(monkeypatch):
    window = series_window()
    del window["dates"][0]["games"][0]["seriesStatus"]
    install_urlopen(monkeypatch, lambda url: window)

    assert lp.fetch_series_status(103, as_of="2026-10-05") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_series_status"]
    assert "seriesStatus" in lp._run_errors[0]["message"]


def test_a_series_game_nobody_reads_does_not_need_a_series_status(monkeypatch):
    # Only the last earlier final game's standing is read; the previewed game has none yet.
    window = series_window()
    del window["dates"][0]["games"][1]["seriesStatus"]
    install_urlopen(monkeypatch, lambda url: window)

    result = lp.fetch_series_status(103, as_of="2026-10-05")

    assert result["source_game_pk"] == 102
    assert lp._run_errors == []


# --- every endpoint the pipeline asks for has a schema -----------------------------------------

SOURCE = Path(lp.__file__).read_text(encoding="utf-8")


def test_every_mlb_endpoint_in_live_pipeline_has_a_registered_schema():
    requested = set(re.findall(r"statsapi\.mlb\.com/api/v1/([a-zA-Z]+)", SOURCE))
    registered = {key.split("/")[0].split("+")[0] for key in schemas.ENDPOINTS}

    assert requested == registered, "a new MLB endpoint needs a schema in mlb_schemas.ENDPOINTS"


@pytest.mark.parametrize(
    "name",
    ["SCHEDULE_DAY", "SERIES_SCHEDULE", "SERIES_STATUS", "PITCHER_STATS", "TEAM_SPLITS", "PERSON", "SEASONS"],
)
def test_every_schema_is_validated_by_a_fetcher(name):
    assert f"mlb_schemas.{name}" in SOURCE, f"{name} is declared but no fetcher validates with it"
