"""Mandatory source structure is checked before filtering (QA-05).

A missing integrity column, a null Statcast result or a schedule without `dates` is a
source failure and goes to the run record. A valid empty frame (a debut) and a valid
empty schedule (`{"dates": []}`) are not failures.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import API_STATS, frame, route


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )


# --- pitcher Statcast ---------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["game_date", "game_type"])
def test_a_statcast_frame_without_an_integrity_column_is_an_error(monkeypatch, missing):
    route(monkeypatch, [("/stats?", API_STATS), ("/people/", {"people": [{"pitchHand": {"code": "R"}}]})])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame().drop(columns=[missing]))

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result is None
    error = lp._run_errors[0]
    assert error["source"] == "statcast_pitcher" and error["pitcher_id"] == 11
    assert missing in error["message"]


def test_a_null_statcast_result_is_an_error_not_a_debut(monkeypatch):
    route(monkeypatch, [("/stats?", API_STATS), ("/people/", {"people": [{"pitchHand": {"code": "R"}}]})])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: None)

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result is None
    assert [e["source"] for e in lp._run_errors] == ["statcast_pitcher"]


def test_a_valid_empty_frame_is_still_a_debut(monkeypatch):
    route(
        monkeypatch,
        [("/stats?", {"stats": [{"splits": []}]}), ("/people/", {"people": [{"pitchHand": {"code": "L"}}]})],
    )
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame(n_plain=0))

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result is not None and result["sample"]["limited"]["arsenal"] is True
    assert lp._run_errors == []


def test_a_frame_with_no_columns_and_no_rows_is_also_a_debut(monkeypatch):
    # pybaseball answers a pitcher without pitches with an empty DataFrame.
    route(
        monkeypatch,
        [("/stats?", {"stats": [{"splits": []}]}), ("/people/", {"people": [{"pitchHand": {"code": "L"}}]})],
    )
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: pd.DataFrame())

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result is not None and result["sample"]["limited"]["arsenal"] is True
    assert lp._run_errors == []


# --- team splits from Statcast --------------------------------------------------------------------


def _team_rows(**drop) -> pd.DataFrame:
    rows = [
        {
            "game_date": "2026-07-10",
            "game_type": "R",
            "home_team": "NYY",
            "away_team": "BOS",
            "inning_topbot": "Bot",
            "p_throws": "R",
            "events": "field_out",
        }
        for _ in range(5)
    ]
    return pd.DataFrame(rows).drop(columns=list(drop))


@pytest.mark.parametrize("missing", ["game_date", "game_type", "events", "p_throws"])
def test_team_splits_reject_a_frame_without_a_mandatory_column(missing):
    with pytest.raises(ValueError, match=missing):
        lp.derive_team_splits(_team_rows(**{missing: 1}), "NYY", "2026-07-14")


def test_team_splits_accept_an_empty_frame():
    assert lp.derive_team_splits(pd.DataFrame(), "NYY", "2026-07-14") == {}


def test_a_team_frame_missing_game_type_is_recorded_as_a_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0})
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        lp, "_get_text", lambda url, timeout=60: _team_rows(game_type=1).to_csv(index=False)
    )

    assert lp.fetch_team_splits(147, as_of="2026-07-14") == {}

    assert [e["source"] for e in lp._run_errors] == ["savant_team_batting"]
    assert "game_type" in lp._run_errors[0]["message"]


# --- schedule -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [{}, {"message": "Internal error"}, {"dates": None}, {"dates": "x"}, [], None],
)
def test_a_schedule_without_a_list_of_dates_is_an_error(monkeypatch, payload):
    route(monkeypatch, [("schedule", payload)])

    assert lp.fetch_todays_games("2026-07-15") == []

    assert [e["source"] for e in lp._run_errors] == ["mlb_schedule"]


def test_a_malformed_schedule_makes_the_run_fail_not_report_no_games(monkeypatch):
    route(monkeypatch, [("schedule", {})])

    record, snapshot = lp.run_live_pipeline("2026-07-15")

    assert snapshot is None
    assert record["status"] == "failed"
    assert record["errors"][0]["source"] == "mlb_schedule"


def test_a_valid_empty_schedule_is_still_no_games(monkeypatch):
    route(monkeypatch, [("schedule", {"dates": []})])

    record, snapshot = lp.run_live_pipeline("2026-07-15")

    assert snapshot is None
    assert record["status"] == "no_games" and record["errors"] == []
