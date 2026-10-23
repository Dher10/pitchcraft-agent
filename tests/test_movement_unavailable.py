"""Unavailable movement is None, never a measured 0.0 (QA-03, Python half).

compute_movement used to emit zeroes when the movement columns were missing or a pitch had
fewer than three observations; the detail panel then described those zeroes as a real shape.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import frame


def test_missing_movement_columns_are_none_not_zero():
    df = frame().drop(columns=["pfx_x", "pfx_z"])

    result = lp.compute_movement(df, ["Four-seam"])

    assert result == {"Four-seam": {"h_break": None, "v_break": None, "family": "Fastball"}}


def test_columns_that_are_all_null_are_none_not_zero():
    df = frame()
    df["pfx_x"] = None
    df["pfx_z"] = None

    assert lp.compute_movement(df, ["Four-seam"])["Four-seam"]["h_break"] is None


def test_the_qa_probe_survives_the_whole_pitcher_processing():
    df = frame()
    df["pfx_x"] = None
    df["pfx_z"] = None

    result = lp.process_pitcher_statcast(df, "No Movement")

    assert result["movement"]["Four-seam"] == {"h_break": None, "v_break": None, "family": "Fastball"}


@pytest.mark.parametrize("observations", [0, 1, 2])
def test_fewer_than_three_observations_is_none(observations):
    df = frame(n_plain=0, extra_rows=[{}] * observations + [{"pfx_x": None, "pfx_z": None}] * 5)

    result = lp.compute_movement(df, ["Four-seam"])

    assert result["Four-seam"]["h_break"] is None and result["Four-seam"]["v_break"] is None


def test_three_observations_give_the_median_in_inches():
    df = frame(n_plain=3)

    result = lp.compute_movement(df, ["Four-seam"])

    assert result["Four-seam"] == {"h_break": 6.0, "v_break": 13.2, "family": "Fastball"}


def test_a_real_zero_movement_is_kept_as_zero():
    df = frame(n_plain=3)
    df["pfx_x"] = 0.0
    df["pfx_z"] = 0.0

    result = lp.compute_movement(df, ["Four-seam"])

    assert (result["Four-seam"]["h_break"], result["Four-seam"]["v_break"]) == (0.0, 0.0)


def test_one_pitch_without_movement_does_not_hide_another_with_it():
    df = pd.concat([frame(n_plain=5), frame(n_plain=5).assign(pitch_type="SL", pfx_x=None, pfx_z=None)])

    result = lp.compute_movement(df, ["Four-seam", "Slider"])

    assert result["Four-seam"]["h_break"] == 6.0
    assert result["Slider"]["h_break"] is None
