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
from tests.test_fetchers_as_of import _series_router, install_urlopen, query
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
    assert record["status"] == "no_games"
    assert record["errors"] == []


# --- nested envelopes (QA2-03) ----------------------------------------------------------------------
# The real API answers a day without games with `dates: []` and puts a `games` list in every date
# entry that exists (checked 2026-10-11 against 2026-07-16, 2026-12-25 and two date ranges).

BAD_DATE_ENTRIES = [
    {"date": "2026-07-15"},
    {"date": "2026-07-15", "games": None},
    {"date": "2026-07-15", "games": {}},
    {"date": "2026-07-15", "games": "x"},
    "x",
    None,
]


@pytest.mark.parametrize("entry", BAD_DATE_ENTRIES, ids=repr)
def test_a_schedule_date_without_a_games_list_is_an_error(monkeypatch, entry):
    route(monkeypatch, [("schedule", {"dates": [entry]})])

    assert lp.fetch_todays_games("2026-07-15") == []

    assert [e["source"] for e in lp._run_errors] == ["mlb_schedule"]


def test_the_qa_probe_a_date_entry_without_games_fails_the_run_instead_of_no_games(monkeypatch):
    route(monkeypatch, [("schedule", {"dates": [{"date": "2026-07-15"}]})])

    record, snapshot = lp.run_live_pipeline("2026-07-15")

    assert snapshot is None
    assert record["status"] == "failed"
    assert record["errors"][0]["source"] == "mlb_schedule"


def test_a_date_entry_with_an_empty_games_list_is_still_no_games(monkeypatch):
    route(monkeypatch, [("schedule", {"dates": [{"date": "2026-07-15", "games": []}]})])

    record, snapshot = lp.run_live_pipeline("2026-07-15")

    assert snapshot is None
    assert record["status"] == "no_games"
    assert record["errors"] == []


BAD_STATS_ENVELOPES = [
    {"message": "Internal error"},
    {"stats": None},
    {"stats": "x"},
    {"stats": [{}]},
    {"stats": [{"splits": None}]},
    {"stats": ["x"]},
    [],
    None,
]
VALID_EMPTY_STATS = [{"stats": []}, {"stats": [{"splits": []}]}]


@pytest.mark.parametrize("envelope", BAD_STATS_ENVELOPES, ids=repr)
def test_a_season_stats_error_envelope_is_a_recorded_failure(monkeypatch, envelope):
    route(monkeypatch, [("/stats?", envelope)])

    assert lp.fetch_pitcher_season_stats(11, as_of="2026-07-14") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_season_stats"]


@pytest.mark.parametrize("envelope", VALID_EMPTY_STATS, ids=repr)
def test_a_pitcher_without_season_stats_is_not_a_failure(monkeypatch, envelope):
    route(monkeypatch, [("/stats?", envelope)])

    assert lp.fetch_pitcher_season_stats(11, as_of="2026-07-14") == {}

    assert lp._run_errors == []


def test_the_qa_probe_the_hidden_season_stats_failure_is_logged_and_statcast_stays_the_fallback(
    monkeypatch,
):
    route(monkeypatch, [("/stats?", {"message": "Internal error"})])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame())

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result is not None and result["sample"]["rates"]["source"] == "statcast"
    assert [e["source"] for e in lp._run_errors] == ["mlb_season_stats"]


def test_a_frame_without_events_makes_the_counts_unavailable_not_zero(monkeypatch):
    # QA probe: stats {} + 200 pitches without an `events` column gave BF/K/BB/HR = 0, no error.
    route(monkeypatch, [("/stats?", {"stats": []})])
    monkeypatch.setattr(
        lp, "statcast_pitcher", lambda *a, **k: frame(n_plain=200).drop(columns=["events"])
    )

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    sample = result["sample"]
    rates = sample["rates"]
    assert rates["source"] == "unavailable"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (
        None,
        None,
        None,
        None,
    )
    assert sample["limited"] == {"arsenal": False, "strikeout": True, "control": True}
    summary = result["season_summary"]
    assert (summary["strikeouts"], summary["walks"], summary["home_runs_allowed"]) == (None, None, None)
    assert [e["source"] for e in lp._run_errors] == ["statcast_pitcher"]
    assert "events" in lp._run_errors[0]["message"]


def test_a_frame_with_events_records_no_error(monkeypatch):
    route(monkeypatch, [("/stats?", {"stats": []})])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame(n_plain=200))

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result["sample"]["rates"]["source"] == "statcast"
    assert result["sample"]["rates"]["batters_faced"] == 0  # a real count of zero plate appearances
    assert lp._run_errors == []


# --- series status ----------------------------------------------------------------------------------

BAD_SCHEDULE_ENVELOPES = [
    {"message": "Internal error"},
    {"dates": None},
    {"dates": [{"date": "2026-10-06"}]},
    {"dates": [{"games": None}]},
    [],
    None,
]


@pytest.mark.parametrize("envelope", BAD_SCHEDULE_ENVELOPES, ids=repr)
def test_a_malformed_game_lookup_is_a_recorded_series_failure(monkeypatch, envelope):
    install_urlopen(monkeypatch, lambda url: envelope)

    assert lp.fetch_series_status(103, as_of="2026-10-05") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_series_status"]


@pytest.mark.parametrize("envelope", BAD_SCHEDULE_ENVELOPES, ids=repr)
def test_a_malformed_series_window_is_a_recorded_failure_not_a_zero_zero(monkeypatch, envelope):
    def router(url):
        return _series_router(url) if "gamePk" in query(url) else envelope

    install_urlopen(monkeypatch, router)

    assert lp.fetch_series_status(103, as_of="2026-10-05") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_series_status"]


def test_an_empty_series_window_is_still_the_standing_zero_zero(monkeypatch):
    def router(url):
        return _series_router(url) if "gamePk" in query(url) else {"dates": []}

    install_urlopen(monkeypatch, router)

    result = lp.fetch_series_status(103, as_of="2026-10-05")

    assert result["games_played"] == 0 and (result["wins"], result["losses"]) == (0, 0)
    assert lp._run_errors == []


# --- team splits through the MLB API (the path without `as_of`) -------------------------------------


@pytest.mark.parametrize("envelope", BAD_STATS_ENVELOPES, ids=repr)
def test_a_team_splits_error_envelope_is_a_recorded_failure(monkeypatch, envelope):
    install_urlopen(monkeypatch, lambda url: envelope)

    assert lp.fetch_team_splits(147, season=2026) == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_team_splits"]


@pytest.mark.parametrize("envelope", VALID_EMPTY_STATS, ids=repr)
def test_a_team_without_splits_is_not_a_failure(monkeypatch, envelope):
    install_urlopen(monkeypatch, lambda url: envelope)

    assert lp.fetch_team_splits(147, season=2026) == {}

    assert lp._run_errors == []


def test_a_missing_count_in_a_team_split_is_unavailable_not_zero(monkeypatch):
    split = {
        "split": {"code": "vl"},
        "stat": {"plateAppearances": 200, "ops": ".700", "avg": ".250", "baseOnBalls": 20},
    }
    install_urlopen(monkeypatch, lambda url: {"stats": [{"splits": [split]}]})

    result = lp.fetch_team_splits(147, season=2026)

    assert result["vl"]["strikeouts"] is None and result["vl"]["k_rate"] is None
    assert result["vl"]["walks"] == 20 and result["vl"]["bb_rate"] == 10.0
