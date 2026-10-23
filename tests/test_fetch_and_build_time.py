"""The time of the fetch and the time the file was built are two fields (P0.15-D2.4c, F9, rule 6; schema 0.7.0, D39).

At HEAD `metadata.generated_at` was the fetch time in a live file and a demo constant (2026-06-28) in a demo file, and
the labels that say "fetched" showed the game day. Now `metadata.data_fetched_at` is the instant of the live fetch (null
in a demo file), `generated_at` is the instant the file was built (always real, from an injected clock), and every label
that says "fetched" shows the day of `data_fetched_at` in America/New_York (D29's zone).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.contract_checks import check_contract
from data_pipeline.schema import SCHEMA_VERSION, new_york_day, snapshot_matches_schema
from tests.corpus import KINDS, build, published
from tests.live_helpers import GAME_DAY, failed_checks, hand_snapshot, use_snapshot

# A fetch at 01:30 UTC on the 6th is the evening of the 5th in New York; the game is on the 4th: three different days.
FETCHED_AT = "2026-07-06T01:30:00+00:00"
FETCH_DAY_NY = "2026-07-05"
BUILT_AT = datetime(2026, 7, 6, 9, 0, 0, tzinfo=timezone.utc)


def build_live(monkeypatch, now=BUILT_AT, fetched_at=FETCHED_AT):
    snapshot = hand_snapshot(complete=True)
    snapshot["run_at"] = fetched_at
    use_snapshot(monkeypatch, snapshot)
    return gdj.build_payload(now=now)


def build_demo(monkeypatch, mode, now=BUILT_AT):
    monkeypatch.setattr(gdj, "_live", None)
    if mode == "demo_cached":
        reason = {"source": "pipeline", "code": "no_live_run"}
    else:
        reason = {"source": "mlb_schedule", "code": "request_failed"}
    monkeypatch.setattr(gdj, "_live_status", {"mode": mode, "reason": reason, "live_run": None})
    return gdj.build_payload(now=now)


def codes(payload):
    return {violation.code for violation in check_contract(published(payload))}


# --- the schema ------------------------------------------------------------------------------------------------------


def test_a_snapshot_of_0_6_0_is_not_read_and_the_two_times_came_with_0_7_0():
    assert not snapshot_matches_schema("0.6.0")  # the two fields came with 0.7.0 (D39); a snapshot without them is rejected


# --- two fields, two times -------------------------------------------------------------------------------------------


def test_a_live_file_says_when_it_was_fetched_and_when_it_was_built(monkeypatch):
    metadata = build_live(monkeypatch)["metadata"]

    assert metadata["data_fetched_at"] == FETCHED_AT
    assert metadata["generated_at"] == "2026-07-06T09:00:00+00:00"
    assert metadata["data_fetched_at"] != metadata["generated_at"]


@pytest.mark.parametrize("mode", ["demo_cached", "demo_fallback"])
def test_a_demo_file_has_no_fetch_time_and_a_real_build_time(monkeypatch, mode):
    metadata = build_demo(monkeypatch, mode)["metadata"]

    assert metadata["data_fetched_at"] is None
    assert metadata["generated_at"] == "2026-07-06T09:00:00+00:00"  # not the demo's constant of 2026-06-28


def test_the_build_time_moves_with_the_clock_and_the_fetch_time_does_not(monkeypatch):
    first = build_live(monkeypatch, now=BUILT_AT)["metadata"]
    later = build_live(monkeypatch, now=BUILT_AT + timedelta(hours=5))["metadata"]

    assert later["generated_at"] == "2026-07-06T14:00:00+00:00"
    assert later["data_fetched_at"] == first["data_fetched_at"]


@pytest.mark.parametrize("kind", KINDS)
def test_without_an_injected_clock_the_build_time_is_now(monkeypatch, kind):
    before = datetime.now(timezone.utc)
    built = datetime.fromisoformat(build(monkeypatch, kind)["metadata"]["generated_at"])
    after = datetime.now(timezone.utc)

    assert built.tzinfo is not None
    assert before - timedelta(seconds=1) <= built <= after + timedelta(seconds=1)


def test_a_clock_without_a_zone_is_refused(monkeypatch):
    with pytest.raises(ValueError):
        build_live(monkeypatch, now=datetime(2026, 7, 6, 9, 0, 0))


# --- the labels that say "fetched" ----------------------------------------------------------------------------------


def test_new_york_day_is_the_day_in_new_york_not_in_utc():
    assert new_york_day("2026-07-06T01:30:00+00:00") == "2026-07-05"
    assert new_york_day("2026-07-06T03:30:00Z") == "2026-07-05"
    assert new_york_day("2026-07-06T04:30:00Z") == "2026-07-06"
    assert new_york_day("2026-07-05T23:30:00-04:00") == "2026-07-05"  # New York is UTC-4 in July
    assert new_york_day("2026-07-05T23:30:00-05:00") == "2026-07-06"  # one hour later there: already the 6th
    for bad in (None, 5, "", "2026-07-06", "2026-07-06T01:30:00", "tomorrow"):
        assert new_york_day(bad) is None


def test_the_label_and_the_confidence_note_show_the_day_of_the_fetch_in_new_york(monkeypatch):
    payload = build_live(monkeypatch)

    assert payload["metadata"]["last_updated_label"] == f"Live data fetched {FETCH_DAY_NY}"
    [note] = payload["matchups"][0]["data_confidence"]["notes"]
    assert note == f"Live snapshot fetched {FETCH_DAY_NY} for matchup_001."
    assert payload["matchups"][0]["date"] == GAME_DAY  # the game day is still the game day


def test_a_file_whose_labels_follow_its_fetch_time_has_no_violation_of_that_rule(monkeypatch):
    found = codes(build_live(monkeypatch))

    assert not {c for c in found if c.endswith("#fetched_at")}
    assert "rule6:data_fetched_at" not in found


def test_a_label_that_shows_another_day_than_the_fetch_is_found(monkeypatch):
    payload = published(build_live(monkeypatch))
    payload["metadata"]["data_fetched_at"] = "2026-07-07T12:00:00+00:00"  # the labels say the 5th

    found = codes(payload)

    assert "rule4:generator.metadata.last_updated.live#fetched_at" in found
    assert "rule4:generator.confidence.live_note#fetched_at" in found


def test_the_day_of_the_fetch_is_read_in_new_york_not_cut_from_the_text(monkeypatch):
    """03:30 UTC on the 6th is 23:30 on the 5th in New York: the labels say the 5th and that is right."""

    payload = published(build_live(monkeypatch))
    payload["metadata"]["data_fetched_at"] = "2026-07-06T03:30:00+00:00"

    assert not {c for c in codes(payload) if c.endswith("#fetched_at")}


# --- rule 6 and the manifest -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [None, "yesterday", 12, "2026-07-06", "2026-07-06T01:30:00"])
def test_a_live_file_needs_an_instant_for_its_fetch(monkeypatch, bad):
    payload = published(build_live(monkeypatch))
    payload["metadata"]["data_fetched_at"] = bad

    assert "rule6:data_fetched_at" in codes(payload)


def test_a_live_file_without_the_field_is_found(monkeypatch):
    payload = published(build_live(monkeypatch))
    del payload["metadata"]["data_fetched_at"]

    assert "rule6:data_fetched_at" in codes(payload)


@pytest.mark.parametrize("mode", ["demo_cached", "demo_fallback"])
def test_a_demo_file_with_a_fetch_time_is_found(monkeypatch, mode):
    payload = published(build_demo(monkeypatch, mode))
    assert failed_checks(payload) == []  # control: the generator writes null

    payload["metadata"]["data_fetched_at"] = FETCHED_AT

    assert "a demo file has no time of fetch" in failed_checks(payload)


def test_the_manifest_knows_the_field_and_its_type(monkeypatch):
    payload = published(build_live(monkeypatch))
    assert not {c for c in codes(payload) if "data_fetched_at" in c and c.startswith("rule1:")}

    payload["metadata"]["data_fetched_at"] = 12

    assert "rule1:wrong_type#metadata.data_fetched_at" in codes(payload)


# --- a run whose time is not an instant is not live ------------------------------------------------------------------


@pytest.mark.parametrize("bad", ["yesterday", "2026-07-06", "2026-07-06T01:30:00", "", 12])
def test_a_run_whose_time_is_not_an_instant_with_a_zone_is_not_published_as_live(bad):
    run = {"run_at": bad, "target_date": GAME_DAY, "as_of": "2026-07-03"}
    snapshot = {"live_games": [{}]}

    assert "not an instant" in (gdj._snapshot_unsafe(run, snapshot) or "")


def test_control_a_run_with_an_instant_passes_that_check():
    run = {"run_at": FETCHED_AT, "target_date": GAME_DAY, "as_of": "2026-07-03"}

    assert gdj._snapshot_unsafe(run, {"live_games": [{}]}) is None
