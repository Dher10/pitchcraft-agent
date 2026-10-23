"""QA5-03: source infinities cannot become measurements or valid-looking locations.

Probe B runs the real fetcher, generator and validator over mocked sources.
Deleting the source gate must restore its error-free infinity/clipping bug;
deleting the payload gate or strict serializer must permit invalid JSON again.
Null and measured-zero cases are named controls and must pass before the fix.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import ValidationError, validate_payload
from tests.live_helpers import hand_snapshot, snapshot_from_starters, use_snapshot
from tests import test_as_of_end_to_end as e2e
from tests.test_as_of_end_to_end import leaky_sources  # noqa: F401
from tests.test_live_sample_pipeline import API_STATS, events_frame, isolated, route  # noqa: F401
from tests.test_statcast_rows import batting


MEASUREMENTS = {
    "release_speed": "velocity_by_pitch",
    "pfx_x": "movement",
    "pfx_z": "movement",
    "plate_x": "pitch_locations",
    "plate_z": "pitch_locations",
}


def fetch_pair(monkeypatch, source):
    route(monkeypatch, [("/stats?", API_STATS)])
    monkeypatch.setattr(
        lp, "statcast_pitcher",
        lambda *args, player_id: source.copy() if player_id == 11 else events_frame(),
    )
    return (
        lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03"),
        lp.fetch_pitcher_statcast(22, "Bravo Liveleft", as_of="2026-07-03"),
    )


@pytest.mark.parametrize("column", MEASUREMENTS)
@pytest.mark.parametrize("value", [float("inf"), float("-inf")], ids=["inf", "negative-inf"])
@pytest.mark.parametrize("rows", ["all", "one"])
def test_probe_b_disables_only_the_bad_measurement_group_and_keeps_the_game(monkeypatch, column, value, rows):
    source = events_frame()
    source.loc[source.index if rows == "all" else [0], column] = value

    away, home = fetch_pair(monkeypatch, source)

    assert away is not None and home is not None
    assert away["sample"]["arsenal"]["pitches"] == 170
    assert away["sample"]["rates"]["batters_faced"] == 19
    assert away["season_summary"]["era"] == "3.10"
    assert away["pitch_mix"] == home["pitch_mix"]
    assert len(lp._run_errors) == 1
    error = lp._run_errors[0]
    assert (error["source"], error["code"]) == ("statcast_pitcher", "malformed_rows")
    assert column in error["message"]

    affected = MEASUREMENTS[column]
    for group in set(MEASUREMENTS.values()) - {affected}:
        assert away[group] == home[group]
    if affected == "velocity_by_pitch":
        assert away[affected] == []
    elif affected == "movement":
        assert all(m["h_break"] is None and m["v_break"] is None for m in away[affected].values())
    else:
        assert away[affected] == {"vs_lhh": [], "vs_rhh": []}

    use_snapshot(monkeypatch, snapshot_from_starters(away, home))
    payload = gdj.build_payload()
    assert len(payload["matchups"]) == 1
    validate_payload(payload)
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize("column", MEASUREMENTS)
@pytest.mark.parametrize("value", [None, 0.0], ids=["null", "finite"])
def test_control_missing_and_finite_measurements_stay_valid(monkeypatch, column, value):
    source = events_frame()
    # Velocity's existing domain is positive; zero is valid for movement/location.
    if column == "release_speed" and value is not None:
        value = 94.0
    source[column] = value
    away, home = fetch_pair(monkeypatch, source)

    assert away is not None and lp._run_errors == []
    if value is not None:
        if column == "release_speed":
            assert away["velocity_by_pitch"][0]["away_starter_velocity"] == 94.0
        elif column.startswith("pfx_"):
            axis = "h_break" if column == "pfx_x" else "v_break"
            assert away["movement"]["Four-seam"][axis] == 0.0
        else:
            assert len(away["pitch_locations"]["vs_rhh"]) == 1
    use_snapshot(monkeypatch, snapshot_from_starters(away, home))
    payload = gdj.build_payload()
    validate_payload(payload)
    json.dumps(payload, allow_nan=False)


def test_a_nonfinite_measurement_is_recorded_before_date_filtering(monkeypatch):
    source = events_frame()
    source.loc[0, "release_speed"] = float("inf")
    source.loc[0, "game_date"] = source.loc[0, "game_date"].replace(day=20)

    away, home = fetch_pair(monkeypatch, source)

    assert away is not None and home is not None
    assert away["velocity_by_pitch"] == []
    assert away["sample"]["arsenal"]["pitches"] == 169
    assert any(error["code"] == "malformed_rows" for error in lp._run_errors)


def test_the_pipeline_publishes_the_kept_game_and_the_numeric_source_error(leaky_sources, monkeypatch):
    def source(*args, player_id):
        frame = e2e.STATCAST.copy()
        if player_id == 11:
            frame["plate_x"] = float("inf")
        return frame

    monkeypatch.setattr(lp, "statcast_pitcher", source)
    record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)

    assert snapshot is not None and len(snapshot["live_games"]) == 1
    assert [(e["source"], e["code"]) for e in record["errors"]] == [("statcast_pitcher", "malformed_rows")]
    cache_manager.save_processed("live_run", record)
    cache_manager.save_processed("live_matchup", snapshot)
    live, status = gdj._resolve_live_input()
    monkeypatch.setattr(gdj, "_live", live)
    monkeypatch.setattr(gdj, "_live_status", status)
    payload = gdj.build_payload()
    validate_payload(payload)
    assert payload["metadata"]["data_status"]["live_run"]["errors"] == [
        {"source": "statcast_pitcher", "code": "malformed_rows"},
    ]
    assert payload["matchups"][0]["pitch_locations"]["away_starter"] == {"vs_lhh": [], "vs_rhh": []}
    json.dumps(payload, allow_nan=False)


def test_control_team_rates_do_not_read_unused_numeric_identifiers():
    source = batting()
    source["game_pk"] = float("inf")
    assert lp.derive_team_splits(source, "NYY", "2026-07-14")["vr"]["plate_appearances"] == 20
    assert lp._run_errors == []


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "negative-inf"])
@pytest.mark.parametrize("location", ["metadata", "archive", "matchups"])
def test_every_payload_number_is_checked_even_outside_known_numeric_fields(monkeypatch, value, location):
    use_snapshot(monkeypatch, hand_snapshot(True))
    payload = gdj.build_payload()
    validate_payload(payload)
    if location == "metadata":
        payload[location]["future_field"] = {"nested": [value]}
    elif location == "matchups":
        payload[location][0]["future_field"] = {"nested": [value]}
    else:
        payload[location].append({"future_field": {"nested": [value]}})

    with pytest.raises(ValidationError) as rejected:
        validate_payload(payload)
    failures = [check for check in rejected.value.checks if not check.passed]
    finite_checks = [check for check in failures if check.description == "every payload number is finite"]
    assert len(finite_checks) == 1
    assert location in finite_checks[0].detail and "future_field" in finite_checks[0].detail


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")], ids=["nan", "inf", "negative-inf"])
def test_strict_serialization_keeps_the_previous_file_if_validation_misses_a_nonfinite_number(monkeypatch, tmp_path, value):
    use_snapshot(monkeypatch, hand_snapshot(True))
    payload = deepcopy(gdj.build_payload())
    payload["metadata"]["future_field"] = value
    output = tmp_path / "published.json"
    output.write_text("previous file", encoding="utf-8")
    monkeypatch.setattr(gdj, "OUTPUT_PATH", output)
    monkeypatch.setattr(gdj, "build_payload", lambda: payload)
    # Exercise the independent final guard, assuming a future validation hole.
    monkeypatch.setattr(gdj, "validate_payload", lambda payload: [])

    assert gdj.main() == 1
    assert output.read_text(encoding="utf-8") == "previous file"
