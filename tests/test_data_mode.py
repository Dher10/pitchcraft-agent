"""Explicit data mode and error log instead of a silent fallback to demo
(PLAN.md P0.8; Phase 0 Gherkin "Data source failure is explicit").

Network, Statcast and the cache directory are all mocked or redirected to tmp_path;
nothing is written under public/data or data_cache.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import validate_payload


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


SCHEDULE = {
    "dates": [
        {
            "games": [
                {
                    "gamePk": 1,
                    "gameDate": "2026-07-15T23:05:00Z",
                    "status": {"abstractGameState": "Preview"},
                    "venue": {"name": "Yankee Stadium"},
                    "teams": {
                        "away": {
                            "team": {"id": 111, "name": "Boston Red Sox"},
                            "probablePitcher": {"id": 11, "fullName": "Away Ace"},
                        },
                        "home": {
                            "team": {"id": 147, "name": "New York Yankees"},
                            "probablePitcher": {"id": 22, "fullName": "Home Ace"},
                        },
                    },
                }
            ]
        }
    ]
}


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(cache_manager, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )
    return tmp_path


def schedule_returns(monkeypatch, payload):
    def fake_urlopen(req, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)


# --- error log ----------------------------------------------------------------


def test_schedule_failure_is_recorded_not_just_printed(monkeypatch):
    def down(req, timeout=None):
        raise OSError("schedule down")

    monkeypatch.setattr(lp.urllib.request, "urlopen", down)

    assert lp.fetch_todays_games("2026-07-15") == []

    assert [e["source"] for e in lp._run_errors] == ["mlb_schedule"]
    assert "schedule down" in lp._run_errors[0]["message"]


def test_statcast_failure_is_recorded_with_the_pitcher(monkeypatch):
    def down(*a, **k):
        raise OSError("statcast down")

    monkeypatch.setattr(lp, "statcast_pitcher", down)

    assert lp.fetch_pitcher_statcast(11, "Away Ace", as_of="2026-07-14") is None

    error = lp._run_errors[0]
    assert error["source"] == "statcast_pitcher"
    assert error["pitcher_id"] == 11
    assert "statcast down" in error["message"]


def test_team_split_failures_are_recorded_for_both_sources(monkeypatch):
    def down(req, timeout=None):
        raise OSError("api down")

    monkeypatch.setattr(lp.urllib.request, "urlopen", down)
    monkeypatch.setattr(
        lp, "fetch_team_batting_statcast", lambda *a: (_ for _ in ()).throw(OSError("savant down"))
    )

    assert lp.fetch_team_splits(147) == {}
    assert lp.fetch_team_splits(147, as_of="2026-07-14") == {}

    assert [e["source"] for e in lp._run_errors] == ["mlb_team_splits", "savant_team_batting"]


# --- run status ----------------------------------------------------------------


@pytest.mark.parametrize(
    "info, errors, expected",
    [
        ({"games_scheduled": 3, "games_live": 2}, [], "ok"),
        ({"games_scheduled": 3, "games_live": 1}, [{"source": "x"}], "ok"),  # partial
        ({"games_scheduled": 3, "games_live": 0}, [{"source": "statcast_pitcher"}], "failed"),
        ({"games_scheduled": 0, "games_live": 0}, [{"source": "mlb_schedule"}], "failed"),
        ({"games_scheduled": 0, "games_live": 0}, [], "no_games"),
        ({"games_scheduled": 5, "games_live": 0}, [], "no_usable_games"),
    ],
)
def test_run_status(info, errors, expected):
    assert lp._run_status(info, errors) == expected


# --- Gherkin: Data source failure is explicit ------------------------------------


def test_statcast_down_records_the_failure_and_publishes_no_snapshot(monkeypatch, isolated):
    schedule_returns(monkeypatch, SCHEDULE)

    def down(*a, **k):
        raise OSError("statcast down")

    monkeypatch.setattr(lp, "statcast_pitcher", down)

    exit_code = lp.main_with_args("2026-07-15", None)

    assert exit_code == 1
    run = json.loads((isolated / "processed" / "live_run.json").read_text())
    assert run["status"] == "failed"
    assert run["games_scheduled"] == 1 and run["games_live"] == 0
    assert {e["source"] for e in run["errors"]} == {"statcast_pitcher"}
    assert not (isolated / "processed" / "live_matchup.json").exists()


def test_no_games_scheduled_exits_successfully_without_errors(monkeypatch, isolated):
    schedule_returns(monkeypatch, {"dates": []})

    exit_code = lp.main_with_args("2026-12-25", None)

    assert exit_code == 0
    run = json.loads((isolated / "processed" / "live_run.json").read_text())
    assert run["status"] == "no_games"
    assert run["errors"] == []
    assert not (isolated / "processed" / "live_matchup.json").exists()


def test_a_failed_run_does_not_keep_a_stale_snapshot_as_live(monkeypatch, isolated):
    cache_manager.save_processed("live_matchup", {"run_at": "old", "fetched_date": "2026-07-04"})
    schedule_returns(monkeypatch, SCHEDULE)
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: (_ for _ in ()).throw(OSError("down")))

    lp.main_with_args("2026-07-15", None)

    snapshot, status = gdj._resolve_live_input()
    assert snapshot is None
    assert status["mode"] == "demo_fallback"


# --- generator: mode resolution ---------------------------------------------------


def write_run(status="ok", run_at="2026-07-15T12:00:00+00:00", errors=None):
    cache_manager.save_processed(
        "live_run",
        {
            "status": status,
            "run_at": run_at,
            "target_date": "2026-07-15",
            "as_of": "2026-07-14",
            "games_scheduled": 1,
            "games_live": 1 if status == "ok" else 0,
            "skipped_games": [],
            "errors": errors or [],
        },
    )


def test_without_a_live_run_the_mode_is_plain_demo():
    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_cached"
    assert status["live_run"] is None


def test_a_failed_run_means_demo_fallback_with_the_errors():
    write_run("failed", errors=[{"source": "statcast_pitcher", "message": "down"}])
    cache_manager.save_processed("live_matchup", {"run_at": "2026-07-15T12:00:00+00:00"})

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"
    assert status["live_run"]["status"] == "failed"
    assert status["live_run"]["errors"][0]["source"] == "statcast_pitcher"


def test_a_good_run_with_its_own_snapshot_is_live():
    write_run("ok")
    cache_manager.save_processed(
        "live_matchup",
        {"run_at": "2026-07-15T12:00:00+00:00", "fetched_date": "2026-07-15", "as_of": "2026-07-14"},
    )

    snapshot, status = gdj._resolve_live_input()

    assert snapshot["fetched_date"] == "2026-07-15"
    assert status["mode"] == "fetched_snapshot"


def test_a_snapshot_from_another_run_is_not_live():
    write_run("ok", run_at="2026-07-15T12:00:00+00:00")
    cache_manager.save_processed("live_matchup", {"run_at": "2026-07-04T12:00:00+00:00"})

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"
    assert "does not belong" in status["reason"]


def test_an_unreadable_run_record_is_a_fallback_not_a_silent_demo(isolated):
    path = isolated / "processed"
    path.mkdir(parents=True)
    (path / "live_run.json").write_text("{not json")

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"
    assert "unreadable" in status["reason"]


# --- generator: published payload ---------------------------------------------------


def test_fallback_payload_is_labelled_demo_and_carries_the_failure(monkeypatch):
    status = {
        "mode": "demo_fallback",
        "reason": "Live run failed",
        "live_run": {
            "status": "failed",
            "run_at": "2026-07-15T12:00:00+00:00",
            "target_date": "2026-07-15",
            "errors": [{"source": "statcast_pitcher", "message": "down"}],
        },
    }
    monkeypatch.setattr(gdj, "_live", None)
    monkeypatch.setattr(gdj, "_live_status", status)

    payload = gdj.build_payload()

    meta = payload["metadata"]
    assert meta["data_mode"] == "demo_fallback"
    assert meta["data_status"]["live_run"]["errors"][0]["source"] == "statcast_pitcher"
    assert "unavailable" in meta["last_updated_label"].lower()
    assert all(m["data_confidence"]["level"] != "fetched_snapshot" for m in payload["matchups"])
    validate_payload(payload)


def test_plain_demo_payload_says_demo_cached(monkeypatch):
    monkeypatch.setattr(gdj, "_live", None)
    monkeypatch.setattr(gdj, "_live_status", {"mode": "demo_cached", "reason": "Demo data", "live_run": None})

    payload = gdj.build_payload()

    assert payload["metadata"]["data_mode"] == "demo_cached"
    assert payload["metadata"]["data_status"]["live_run"] is None


def test_live_matchup_has_no_demo_broadcast_note_or_fallback_promise(monkeypatch):
    from tests.test_live_starters_no_demo_fields import _fake_live_game
    from data_pipeline import demo_inputs

    template = demo_inputs.build_demo_payload()["matchups"][0]
    live_game = _fake_live_game(template)
    live_game["featured_game"] = {
        "away_team": "Boston Red Sox", "away_team_abbr": "BOS", "away_team_id": 111,
        "home_team": "New York Yankees", "home_team_abbr": "NYY", "home_team_id": 147,
        "venue": "Yankee Stadium", "start_time": "2026-07-15T23:05:00Z",
        "away_pitcher_id": 11, "home_pitcher_id": 22,
    }
    monkeypatch.setattr(gdj, "_live", {"fetched_date": "2026-07-15", "live_games": [live_game]})

    matchup = gdj._apply_live_game_to_matchup(deepcopy(template), live_game, "matchup_001", True)

    assert matchup["game"]["broadcast_note"] is None
    assert not any("falls back" in note for note in matchup["data_confidence"]["notes"])
