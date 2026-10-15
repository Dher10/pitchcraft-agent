"""Shared builders for the tests that look at a live matchup (PLAN.md P0.15-A).

Snapshots are made with the pipeline's own functions (`process_pitcher_statcast`, `_attach_sample`,
`_empty_pitcher_data`, `_combine_pitch_mix`), never copied from the demo, so a value that equals the demo's
can only have been inherited from it or be a real coincidence the test then has to explain.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterator

import pandas as pd

from data_pipeline import generate_demo_json as gdj
from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.schema import SCHEMA_VERSION
from data_pipeline.validators import ValidationError, validate_payload

GAME_DAY = "2026-07-04"
CUTOFF = "2026-07-03"
RUN_AT = "2026-07-04T12:00:00+00:00"
LIVE_STATUS = {"mode": "fetched_snapshot", "reason": "Live run ok", "live_run": None}


def leaves(value: Any, path: tuple = ()) -> Iterator[tuple[tuple, Any]]:
    """Every (path, value) of the scalar leaves of a nested dict/list; empty containers have none."""

    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, (*path, index))
    else:
        yield path, value


def summary_scopes(sample: dict[str, Any]) -> dict[str, Any]:
    """The `season_summary.scopes` the pipeline writes for a sample: the API's ERA is regular season, the
    counts have the sample's own scope (None when the source is unavailable)."""

    rates = sample["rates"]
    return {
        "season_rates": labels.make_scope(labels.SCOPE_REGULAR, rates["scope"]["through"]),
        "counts": None if rates["source"] == "unavailable" else rates["scope"],
    }


def failed_checks(payload: dict[str, Any]) -> list[str]:
    """The descriptions of the publication checks that fail ([] when the payload validates)."""

    try:
        checks = validate_payload(payload)
    except ValidationError as exc:
        checks = exc.checks
    return [check.description for check in checks if not check.passed]


def use_snapshot(monkeypatch, snapshot: dict[str, Any]) -> None:
    """Make the generator read `snapshot` as the live input of this test."""

    monkeypatch.setattr(gdj, "_live", snapshot)
    monkeypatch.setattr(gdj, "_live_status", dict(LIVE_STATUS))


def _pitcher_frame(pitches: dict[str, int], throws: str) -> pd.DataFrame:
    rows = []
    for pitch_type, count in pitches.items():
        for index in range(count):
            rows.append(
                {
                    "game_date": pd.Timestamp("2026-06-20"),
                    "game_type": "R",
                    "pitch_type": pitch_type,
                    "stand": "L" if index % 2 else "R",
                    "p_throws": throws,
                    "release_speed": 91.0 + len(pitch_type),
                    "pfx_x": 0.3 + 0.01 * (index % 7),
                    "pfx_z": 1.0 + 0.01 * (index % 5),
                    "plate_x": -0.4 + 0.05 * (index % 9),
                    "plate_z": 1.9 + 0.05 * (index % 11),
                    "events": None,
                }
            )
    return pd.DataFrame(rows)


def _starter(name: str, throws: str, pitches: dict[str, int], api: dict[str, Any]) -> dict[str, Any]:
    frame = _pitcher_frame(pitches, throws)
    data = lp.process_pitcher_statcast(frame, name)
    lp._attach_sample(data, lp._statcast_counts(frame), api, date.fromisoformat(CUTOFF))
    return data


def _debut(name: str, throws: str) -> dict[str, Any]:
    data = lp._empty_pitcher_data(name, throws)
    lp._attach_sample(data, None, {}, date.fromisoformat(CUTOFF))
    return data


def featured_game(game_day: str = GAME_DAY) -> dict[str, Any]:
    """The `featured_game` the pipeline writes, with only what the schedule always sends."""

    return {
        "game_pk": 777001,
        "official_date": game_day,
        "away_team": "Test Away Club",
        "away_team_id": 901,
        "away_team_abbr": "TAW",
        "home_team": "Test Home Club",
        "home_team_id": 902,
        "home_team_abbr": "THM",
        "away_pitcher_name": "Alpha Livearm",
        "away_pitcher_id": 111,
        "home_pitcher_name": "Bravo Liveleft",
        "home_pitcher_id": 222,
        "start_time_utc": f"{game_day}T18:07:00Z",
    }


def snapshot_from_starters(
    away: dict[str, Any], home: dict[str, Any], *, game_day: str = GAME_DAY, cutoff: str = CUTOFF
) -> dict[str, Any]:
    """A one-game snapshot around starters the real fetchers built (named Alpha Livearm and Bravo Liveleft)."""

    game = {
        "featured_game": featured_game(game_day),
        "as_of": cutoff,
        "away_starter": away,
        "home_starter": home,
        "combined_charts": {
            "pitch_mix": lp._combine_pitch_mix(away, home),
            "velocity_by_pitch": lp._combine_velocity(away, home),
        },
        "away_team_splits": {},
        "home_team_splits": {},
    }
    return {
        "data_mode": "fetched_snapshot",
        "schema_version": SCHEMA_VERSION,
        "run_at": RUN_AT,
        "fetched_date": game_day,
        "as_of": cutoff,
        "live_games": [game],
    }


debut_starter = _debut


def hand_snapshot(complete: bool) -> dict[str, Any]:
    """
    A live snapshot made by hand. `complete`: every optional thing the pipeline can give (venue and its
    time zone, team splits, real pitch mixes, a measured season line). Otherwise the least it can give:
    two debut starters, no venue, no zone, no splits. The hands are the opposite of the demo's.
    """

    featured = {
        "game_pk": 777001,
        "official_date": GAME_DAY,
        "away_team": "Test Away Club",
        "away_team_id": 901,
        "away_team_abbr": "TAW",
        "home_team": "Test Home Club",
        "home_team_id": 902,
        "home_team_abbr": "THM",
        "away_pitcher_name": "Alpha Livearm",
        "away_pitcher_id": 111,
        "home_pitcher_name": "Bravo Liveleft",
        "home_pitcher_id": 222,
        "start_time_utc": f"{GAME_DAY}T18:07:00Z",
    }
    if complete:
        featured.update(venue="Test Park", venue_timezone="America/Chicago", status="Preview")
        api_away = {
            "era": "2.71", "whip": "0.93", "innings": "150.1", "batters_faced": 600,
            "strikeouts": 187, "walks": 41, "home_runs_allowed": 12,
        }
        api_home = {
            "era": "4.52", "whip": "1.31", "innings": "88.2", "batters_faced": 380,
            "strikeouts": 72, "walks": 38, "home_runs_allowed": 15,
        }
        # Alpha is right-handed in the demo too; the hands here are the opposite of the demo's.
        away = _starter("Alpha Livearm", "L", {"SI": 700, "SL": 300, "CH": 150}, api_away)
        home = _starter("Bravo Liveleft", "R", {"FF": 500, "CU": 200}, api_home)
        splits = {
            "vl": {"ops": ".655", "k_rate": 26.3, "bb_rate": 7.7, "plate_appearances": 410},
            "vr": {"ops": ".801", "k_rate": 19.4, "bb_rate": 10.6, "plate_appearances": 1520},
        }
        away_splits, home_splits = splits, {"vl": splits["vr"], "vr": splits["vl"]}
    else:
        away = _debut("Alpha Livearm", "L")
        home = _debut("Bravo Liveleft", "R")
        away_splits = home_splits = {}

    game = {
        "featured_game": featured,
        "as_of": CUTOFF,
        "away_starter": away,
        "home_starter": home,
        "combined_charts": {
            "pitch_mix": lp._combine_pitch_mix(away, home),
            "velocity_by_pitch": lp._combine_velocity(away, home),
        },
        "away_team_splits": away_splits,
        "home_team_splits": home_splits,
    }
    return {
        "data_mode": "fetched_snapshot",
        "schema_version": SCHEMA_VERSION,
        "run_at": RUN_AT,
        "fetched_date": GAME_DAY,
        "as_of": CUTOFF,
        "live_games": [game],
    }


def schedule_with_zone(base: dict[str, Any], zone: str | None) -> dict[str, Any]:
    """The `test_as_of_end_to_end` schedule with a venue time zone as the hydrated schedule gives it."""

    from copy import deepcopy

    schedule = deepcopy(base)
    venue = schedule["dates"][0]["games"][0]["venue"]
    if zone is not None:
        venue["timeZone"] = {"id": zone, "tz": "EDT", "offset": -4, "offsetAtGameTime": -4}
    return schedule
