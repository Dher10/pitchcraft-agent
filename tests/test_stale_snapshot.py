"""A snapshot is live only if the latest ok run proves it owns it (QA-06).

Run and snapshot must both carry the same non-empty run identifier, and agree on the
game date and on the cutoff. A missing identifier is never "equal" to another one.
"""

from __future__ import annotations

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager

RUN_AT = "2026-07-15T12:00:00+00:00"


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    return tmp_path


def save(run: dict | None, snapshot: dict | None) -> None:
    if run is not None:
        cache_manager.save_processed("live_run", run)
    if snapshot is not None:
        cache_manager.save_processed("live_matchup", snapshot)


def good_run(**overrides) -> dict:
    return {
        "status": "ok",
        "run_at": RUN_AT,
        "target_date": "2026-07-15",
        "as_of": "2026-07-14",
        "games_scheduled": 1,
        "games_live": 1,
        "skipped_games": [],
        "errors": [],
        **overrides,
    }


def good_game(**overrides) -> dict:
    """The least a live game must say for the generator to trust it (dates, hands, what the schedule always sends)."""

    return {
        "featured_game": {
            "official_date": "2026-07-15",
            "away_team": "Boston Red Sox",
            "away_team_id": 111,
            "away_team_abbr": "BOS",
            "home_team": "New York Yankees",
            "home_team_id": 147,
            "home_team_abbr": "NYY",
            "away_pitcher_id": 11,
            "home_pitcher_id": 22,
            "start_time_utc": "2026-07-15T23:05:00Z",
        },
        "as_of": "2026-07-14",
        "away_starter": {"name": "Alpha Livearm", "throws": "R"},
        "home_starter": {"name": "Bravo Liveleft", "throws": "L"},
        **overrides,
    }


def good_snapshot(**overrides) -> dict:
    return {
        "run_at": RUN_AT,
        "fetched_date": "2026-07-15",
        "as_of": "2026-07-14",
        "live_games": [good_game()],
        **overrides,
    }


def test_a_complete_matching_pair_is_live():
    save(good_run(), good_snapshot())

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is not None and status["mode"] == "fetched_snapshot"


def test_a_run_and_a_snapshot_that_both_lack_run_at_are_not_live():
    run = good_run()
    del run["run_at"]
    legacy = good_snapshot()
    del legacy["run_at"]
    save(run, legacy)

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"


def test_a_legacy_snapshot_without_run_at_is_not_live_even_if_the_run_has_one():
    legacy = good_snapshot()
    del legacy["run_at"]
    save(good_run(), legacy)

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


def test_a_run_without_run_at_is_not_live():
    run = good_run()
    del run["run_at"]
    save(run, good_snapshot())

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


@pytest.mark.parametrize("bad", ["", "   ", None, 0, 12345, ["x"]])
def test_an_empty_or_non_string_run_at_is_never_an_identifier(bad):
    save(good_run(run_at=bad), good_snapshot(run_at=bad))

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


def test_a_snapshot_for_another_game_date_is_not_live():
    save(good_run(), good_snapshot(fetched_date="2026-07-04"))

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"
    assert "date" in status["reason"]


def test_a_snapshot_with_another_cutoff_is_not_live():
    save(good_run(), good_snapshot(as_of="2026-07-10"))

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


@pytest.mark.parametrize("missing", ["as_of", "fetched_date"])
def test_a_snapshot_without_its_date_or_cutoff_is_not_live(missing):
    snapshot_data = good_snapshot()
    del snapshot_data[missing]
    save(good_run(), snapshot_data)

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


def test_a_run_without_a_cutoff_cannot_vouch_for_a_snapshot():
    run = good_run()
    del run["as_of"]
    save(run, good_snapshot(as_of=None))

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_fallback"


def test_the_qa_probe_a_legacy_snapshot_next_to_a_july_15_run_is_not_accepted():
    save(
        {"status": "ok", "target_date": "2026-07-15"},
        {"fetched_date": "2026-07-04", "live_games": [{"some": "legacy data"}]},
    )

    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None
    assert status["mode"] == "demo_fallback"
