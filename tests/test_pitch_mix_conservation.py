"""QA5-01: selecting chart rows cannot change source facts for either starter.

Removing full source retention must restore the false sixth-pitch zero. The
oracle counts source rows, never the processed mix or a sum of displayed rows.
All matrix sources are mocked; alias counts are grouped by published name.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.matrix import HARD_CASES, MATRIX, hard_outcome, outcomes, pitcher_frame


SLOTS = {"away": "away_starter", "home": "home_starter"}


def source_frame(outcome, side):
    source = pitcher_frame(getattr(outcome.scenario, side))
    if source.empty:
        return source
    cutoff = date.fromisoformat(outcome.scenario.game_day) - timedelta(days=1)
    source = source[(pd.to_datetime(source["game_date"]).dt.date <= cutoff) & source["game_type"].isin(("R", "F", "D", "L", "W"))]
    source = source[source["pitch_type"].notna() & (source["pitch_type"] != "")].copy()
    source["published_pitch"] = source["pitch_type"].map(lambda code: lp.PITCH_NAME_MAP.get(code, code))
    return source


@pytest.mark.parametrize("name,side,pitch", [
    ("six_type_overlap", "away", "Cutter"),
    ("six_type_overlap_reversed", "home", "Cutter"),
    ("six_type_alias_overlap", "away", "Curveball"),
])
def test_probe_a_a_displayed_sixth_pitch_keeps_its_source_count_and_measurements(name, side, pitch):
    outcome = hard_outcome(name)
    assert outcome.live and outcome.failed == [] and outcome.blocked is None
    matchup, slot = outcome.matchup, SLOTS[side]
    row = next(row for row in matchup["charts"]["pitch_mix"] if row["pitch"] == pitch)
    assert row[slot]["count"] == 10
    assert row[slot]["total"] == 1150
    assert row[slot]["overall"] == 0.9

    source = source_frame(outcome, side)
    selected = source[source["published_pitch"] == pitch]
    assert len(selected) == 10
    velocity = next(row for row in matchup["charts"]["velocity_by_pitch"] if row["pitch"] == pitch)
    assert velocity[f"{side}_starter_velocity"] == round(float(selected["release_speed"].mean()), 1)
    movement = matchup["charts"]["pitch_movement"][slot]
    assert pitch in movement
    assert movement[pitch]["h_break"] == round(float(selected["pfx_x"].median()) * 12, 1)
    assert movement[pitch]["v_break"] == round(float(selected["pfx_z"].median()) * 12, 1)
    for split, hand in (("vs_lhh", "L"), ("vs_rhh", "R")):
        raw = selected[selected["stand"] == hand]
        assert len(raw) == 5
        point = next(point for point in matchup["pitch_locations"][slot][split] if point["pitch"] == pitch)
        assert point["x"] == round((float(raw["plate_x"].median()) + 1.7) / 3.4, 3)
        assert point["y"] == round(1 - (float(raw["plate_z"].median()) - 0.5) / 4.5, 3)


def test_control_top_five_selection_does_not_publish_a_sixth_pitch_neither_starter_selects():
    outcome = hard_outcome("six_type_no_overlap")
    assert outcome.live and outcome.failed == []
    assert "Cutter" not in {row["pitch"] for row in outcome.matchup["charts"]["pitch_mix"]}
    assert "Cutter" not in {row["pitch"] for row in outcome.matchup["charts"]["velocity_by_pitch"]}
    assert "Cutter" not in outcome.matchup["charts"]["pitch_movement"]["away_starter"]
    for split in ("vs_lhh", "vs_rhh"):
        assert "Cutter" not in {row["pitch"] for row in outcome.matchup["pitch_locations"]["away_starter"][split]}


def test_control_a_pitch_absent_from_the_full_mix_remains_a_measured_zero():
    outcome = hard_outcome("six_type_overlap")
    row = next(row for row in outcome.matchup["charts"]["pitch_mix"] if row["pitch"] == "Four-seam")
    assert row["home_starter"] == {
        "overall": 0, "vs_lhh": 0, "vs_rhh": 0, "count": 0, "total": 900,
    }


def test_every_displayed_count_and_share_matches_its_source_frame_across_the_matrix():
    checked, cases = 0, 0
    for label, outcome in outcomes().items():
        if not outcome.live:
            continue
        cases += 1
        for side, slot in SLOTS.items():
            sample = outcome.matchup["starters"][slot]["sample"]["arsenal"]
            if sample["pitches"] is None:
                # F21 deliberately discards an incomplete source group; it
                # cannot supply trusted counts for this invariant.
                continue
            source = source_frame(outcome, side)
            counts = Counter(source["published_pitch"]) if len(source) else Counter()
            total = len(source)
            assert sample["pitches"] == total, (label, slot)
            for row in outcome.matchup["charts"]["pitch_mix"]:
                cell = row[slot]
                expected = counts[row["pitch"]]
                assert cell["count"] == expected, (label, slot, row["pitch"], cell, expected)
                assert cell["total"] == total, (label, slot, row["pitch"])
                assert cell["overall"] == (round(expected / total * 100, 1) if total else None)
                for field, hand in (("vs_lhh", "L"), ("vs_rhh", "R")):
                    against = source[source["stand"] == hand] if total else source
                    side_total = len(against)
                    count = int((against["published_pitch"] == row["pitch"]).sum()) if side_total else 0
                    assert cell[field] == (round(count / side_total * 100, 1) if side_total else None), (label, slot, field)
                checked += 1
    assert cases >= len(MATRIX) and checked > 0
    assert {"six_type_overlap", "six_type_overlap_reversed", "six_type_alias_overlap"} <= set(HARD_CASES)
