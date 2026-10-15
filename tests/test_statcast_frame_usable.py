"""A Statcast frame is usable, or it is a recorded source failure, or its counts are unavailable (P0.15-D2.2a).

F6a, F6b and F6c are one mistake: code that reads a pitcher frame without asking whether the columns it
reads can be used. The contract's criterion (rule 2, "Malformed or incomplete"): a malformed answer, a
column the pitch data needs that is missing or has no usable value where one is needed (`pitch_type`,
`stand`), is a source failure and the whole answer is rejected; a column whose absence only makes a figure
unavailable (`events`) gives unavailable figures and a recorded error; a well-formed answer that is merely
thin is a sample, not an error.

Controls (they pass before the fix and say what must not change): the columns that degrade to "not
available" without a claim and without a zero (`release_speed`, `plate_x`, `plate_z`, `pfx_x`, `pfx_z`), a
partial null in a needed column, and usable `events`.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import (  # noqa: F401  (isolated is an autouse fixture)
    API_STATS,
    NO_SPLITS,
    events_frame,
    frame,
    isolated,
    route,
)

CUTOFF = "2026-07-14"
NEEDED = ("stand", "release_speed", "plate_x", "plate_z", "pitch_type")


def fetch(monkeypatch, df: pd.DataFrame, api=API_STATS):
    route(monkeypatch, [("/stats?", api)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: df)
    return lp.fetch_pitcher_statcast(11, "Frame Ace", as_of=CUTOFF)


def statcast_errors() -> list[str]:
    return [error["message"] for error in lp._run_errors if error["source"] == "statcast_pitcher"]


def nulled(df: pd.DataFrame, column: str, rows=None) -> pd.DataFrame:
    out = df.copy()
    out[column] = out[column].astype(object)
    out.loc[out.index if rows is None else rows, column] = None
    return out


def shares_published(result: dict) -> list:
    """Every share and measurement of the pitch data, to look for a zero that nobody measured."""

    shares = [
        row["away_starter"][key] for row in result["pitch_mix"] for key in ("overall", "vs_lhh", "vs_rhh")
    ]
    velocities = [row["away_starter_velocity"] for row in result["velocity_by_pitch"]]
    breaks = [(m["h_break"], m["v_break"]) for m in result["movement"].values()]
    return [*shares, *velocities, *breaks]


# --- F6c: a column the pitch data needs is missing -------------------------------------------------------


@pytest.mark.parametrize("column", NEEDED)
def test_a_frame_without_a_needed_column_is_rejected_naming_the_column(monkeypatch, column):
    result = fetch(monkeypatch, events_frame().drop(columns=[column]))

    assert result is None
    assert any("missing required column" in message and column in message for message in statcast_errors()), statcast_errors()


@pytest.mark.parametrize("column", ["pfx_x", "pfx_z"])
def test_control_a_frame_without_movement_columns_keeps_the_starter_with_null_movement(monkeypatch, column):
    result = fetch(monkeypatch, events_frame().drop(columns=[column]))

    assert result is not None and statcast_errors() == []
    assert all(m["h_break"] is None and m["v_break"] is None for m in result["movement"].values())


# --- F6a: a column present with no usable value ------------------------------------------------------------


@pytest.mark.parametrize("empty", [None, ""])
def test_a_frame_with_no_usable_pitch_type_is_rejected_not_published_as_a_debut(monkeypatch, empty):
    df = events_frame()
    df["pitch_type"] = empty

    result = fetch(monkeypatch, df)

    assert result is None
    assert any("pitch_type" in message for message in statcast_errors()), statcast_errors()


def test_control_a_partial_null_pitch_type_is_normal(monkeypatch):
    result = fetch(monkeypatch, nulled(events_frame(), "pitch_type", rows=range(10)))

    assert result is not None and statcast_errors() == []
    assert result["sample"]["arsenal"]["pitches"] == len(events_frame()) - 10


def test_a_frame_with_no_usable_stand_is_rejected_because_the_page_would_say_he_faced_no_lefties(monkeypatch):
    """With `stand` null the per-side shares are null, which the page reads as "No left-handed batters faced."."""

    result = fetch(monkeypatch, nulled(events_frame(), "stand"))

    assert result is None
    assert any("stand" in message for message in statcast_errors()), statcast_errors()


def test_control_a_partial_null_stand_still_gives_the_shares_of_the_rows_that_have_it(monkeypatch):
    df = events_frame()
    df["stand"] = ["L" if i % 2 else "R" for i in range(len(df))]

    result = fetch(monkeypatch, nulled(df, "stand", rows=range(10)))

    assert result is not None and statcast_errors() == []
    top = result["pitch_mix"][0]["away_starter"]
    assert top["vs_lhh"] == 100.0 and top["vs_rhh"] == 100.0  # one pitch type; both sides faced


@pytest.mark.parametrize("column", ["release_speed", "plate_x", "plate_z", "pfx_x", "pfx_z"])
def test_control_a_column_null_in_every_row_publishes_no_zero_and_no_claim(monkeypatch, column):
    """Proof that these stay out of the rejection: velocity, locations and movement are `null`/empty, never 0."""

    result = fetch(monkeypatch, nulled(events_frame(), column))

    assert result is not None and statcast_errors() == []
    published = shares_published(result)
    assert 0 not in [value for value in published if not isinstance(value, tuple)]
    assert all(0 not in pair for pair in published if isinstance(pair, tuple))
    if column == "release_speed":
        assert result["velocity_by_pitch"] == []
    if column in ("plate_x", "plate_z"):
        assert result["pitch_locations"] == {"vs_lhh": [], "vs_rhh": []}


# --- F6b: `events` present but unusable --------------------------------------------------------------------


def test_events_null_in_every_row_gives_unavailable_counts_not_measured_zeros(monkeypatch):
    result = fetch(monkeypatch, frame(), api=NO_SPLITS)

    rates = result["sample"]["rates"]
    assert rates["source"] == "unavailable"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (None,) * 4
    assert result["season_summary"]["strikeouts"] is None
    assert any("events" in message for message in statcast_errors()), statcast_errors()


def test_the_error_is_recorded_even_when_the_api_gave_the_counts(monkeypatch):
    """The API counts are used, but the plate appearances of Statcast cannot be counted, which the F21 check needs."""

    result = fetch(monkeypatch, frame(), api=API_STATS)

    assert result["sample"]["rates"]["source"] == "mlb_api"
    assert any("events" in message for message in statcast_errors()), statcast_errors()


def test_control_a_frame_without_the_events_column_is_unchanged(monkeypatch):
    result = fetch(monkeypatch, frame().drop(columns=["events"]), api=NO_SPLITS)

    assert result["sample"]["rates"]["source"] == "unavailable"
    assert any("events" in message for message in statcast_errors())


def test_control_usable_events_give_the_statcast_counts_and_no_error(monkeypatch):
    result = fetch(monkeypatch, events_frame(), api=NO_SPLITS)

    rates = result["sample"]["rates"]
    assert rates["source"] == "statcast" and rates["batters_faced"] == 19
    assert statcast_errors() == []


def test_a_starter_hurt_on_his_first_pitch_has_pitches_and_unavailable_counts(monkeypatch):
    """The documented limit (contract 6.4): pitches and no plate appearance cannot be told from an unusable column."""

    result = fetch(monkeypatch, frame(n_plain=1), api=NO_SPLITS)

    assert result["sample"]["arsenal"]["pitches"] == 1
    assert result["sample"]["rates"]["source"] == "unavailable"
