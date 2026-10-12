"""A share against a side the starter never faced is unavailable, not 0% (P0.14-C sweep).

`_usage_pct` returned 0 when the denominator was 0, so a starter who faced no left-handed batter
showed "0% vs LHH" for every pitch: a figure the fan reads as measured. It is `None` now. A real
zero (he faced lefties and never threw that pitch to them) stays 0.
"""

from __future__ import annotations

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_critic_raw_counts import failed, isolated, live_matchup, payload_for  # noqa: F401
from tests.test_live_sample_pipeline import frame


def both_sides():
    """150 four-seams to righties, 30 to lefties; 20 sliders, all to righties."""

    return frame(
        n_plain=0,
        extra_rows=[{"pitch_type": "FF", "stand": "R"}] * 150
        + [{"pitch_type": "FF", "stand": "L"}] * 30
        + [{"pitch_type": "SL", "stand": "R"}] * 20,
    )


def test_usage_pct_has_no_share_of_nothing():
    assert lp._usage_pct(0, 0) is None
    assert lp._usage_pct(3, 0) is None
    assert lp._usage_pct(0, 10) == 0.0  # a real zero
    assert lp._usage_pct(1, 3) == 33.3


def test_a_starter_who_faced_no_lefties_has_no_share_against_them():
    result = lp.process_pitcher_statcast(frame(n_plain=200), "Righties Only")  # frame() has stand R only

    for row in result["pitch_mix"]:
        usage = row["away_starter"]
        assert usage["vs_lhh"] is None
        assert usage["vs_rhh"] == 100.0
        assert usage["overall"] == 100.0


def test_a_starter_who_faced_both_sides_has_real_zeros_and_real_shares():
    result = lp.process_pitcher_statcast(both_sides(), "Both Sides")

    rows = {row["pitch"]: row["away_starter"] for row in result["pitch_mix"]}
    assert rows["Four-seam"]["vs_lhh"] == 100.0
    assert rows["Slider"]["vs_lhh"] == 0.0  # he faced lefties and never threw a slider to them
    assert rows["Slider"]["vs_rhh"] == round(20 / 170 * 100, 1)


def test_the_combined_mix_marks_an_unfaced_side_for_a_pitch_the_starter_never_threw():
    righties_only = lp.process_pitcher_statcast(frame(n_plain=100), "A")
    both = lp.process_pitcher_statcast(both_sides(), "B")
    other = lp.process_pitcher_statcast(
        frame(n_plain=0, extra_rows=[{"pitch_type": "CH", "stand": "L"}] * 10 + [{"pitch_type": "CH", "stand": "R"}] * 10),
        "C",
    )

    rows = {r["pitch"]: r for r in lp._combine_pitch_mix(righties_only, other)}
    assert rows["Changeup"]["away_starter"]["vs_lhh"] is None  # A faced no lefties: unknown, not 0
    assert rows["Changeup"]["away_starter"]["vs_rhh"] == 0  # he faced righties and threw no changeup
    assert rows["Four-seam"]["home_starter"]["vs_lhh"] == 0  # C faced lefties and threw no four-seam

    rows = {r["pitch"]: r for r in lp._combine_pitch_mix(both, other)}
    assert rows["Changeup"]["away_starter"]["vs_lhh"] == 0  # B did face lefties


def test_a_starter_with_no_pitches_has_no_shares_at_all():
    debut = {"pitch_mix": [], "velocity_by_pitch": []}
    other = lp.process_pitcher_statcast(frame(n_plain=100), "Other")

    row = lp._combine_pitch_mix(debut, other)[0]

    assert row["away_starter"] == {
        "overall": 0, "vs_lhh": None, "vs_rhh": None, "count": 0, "total": 0
    }


@pytest.mark.parametrize("value", [None, 0, 37.5])
def test_publication_accepts_a_share_that_is_a_number_or_unavailable(monkeypatch, isolated, value):
    payload = payload_for(monkeypatch, {"FF": 150, "SL": 50})
    live_matchup(payload)["charts"]["pitch_mix"][0]["away_starter"]["vs_lhh"] = value

    assert failed(payload) == []


@pytest.mark.parametrize("value", ["0%", "N/A", -1, 101, True])
def test_publication_rejects_a_share_that_is_neither(monkeypatch, isolated, value):
    payload = payload_for(monkeypatch, {"FF": 150, "SL": 50})
    live_matchup(payload)["charts"]["pitch_mix"][0]["away_starter"]["vs_rhh"] = value

    assert failed(payload)
