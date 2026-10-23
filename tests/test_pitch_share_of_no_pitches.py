"""A share of no pitches is unknown, not 0% (P0.15-D2.2d, F20).

A starter who threw nothing had `overall = 0` for each pitch his opponent threw: a share of zero pitches
written as 0%. His `count` of 0 out of a `total` of 0 is the measured zero; the share is what cannot be
computed, so it is `null`. A pitch he never threw out of a positive total is a real 0%.

The readers were made null-safe in commit D2.2c, so the first producer of a null breaks nothing.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.live_helpers import failed_checks
from tests.matrix import hard_outcome, outcomes
from tests.test_live_sample_pipeline import frame

SLOTS = ("away_starter", "home_starter")


def codes(payload) -> set[str]:
    from data_pipeline.contract_checks import check_contract

    return {violation.code for violation in check_contract(payload)}


# --- where the value is born -----------------------------------------------------------------------------


def test_a_starter_with_no_pitches_has_a_null_share_and_no_other_share():
    debut = {"pitch_mix": [], "velocity_by_pitch": []}
    other = lp.process_pitcher_statcast(frame(n_plain=100), "Other")

    row = lp._combine_pitch_mix(debut, other)[0]

    assert row["away_starter"] == {"overall": None, "vs_lhh": None, "vs_rhh": None, "count": 0, "total": 0}


def test_control_a_pitch_he_never_threw_out_of_real_pitches_is_a_real_zero():
    thrower = lp.process_pitcher_statcast(frame(n_plain=100), "Thrower")  # four-seams only
    other = lp.process_pitcher_statcast(frame(n_plain=100).assign(pitch_type="SL"), "Other")  # sliders only

    rows = {r["pitch"]: r for r in lp._combine_pitch_mix(thrower, other)}

    assert rows["Slider"]["away_starter"]["overall"] == 0 and rows["Slider"]["away_starter"]["total"] == 100
    assert rows["Four-seam"]["home_starter"]["overall"] == 0 and rows["Four-seam"]["home_starter"]["total"] == 100


# --- through the pipeline, the generator and the contract ------------------------------------------------------


def live_cells():
    for name, outcome in outcomes().items():
        if not outcome.live:
            continue
        matchup = outcome.matchup
        for slot in SLOTS:
            pitches = matchup["starters"][slot]["sample"]["arsenal"]["pitches"]
            for row in matchup["charts"]["pitch_mix"]:
                yield name, slot, pitches, row[slot]


def test_every_cell_of_a_starter_with_no_pitches_is_null_and_no_other_cell_is():
    seen_debut = seen_thrower = 0
    for name, slot, pitches, cell in live_cells():
        if pitches == 0:
            seen_debut += 1
            assert cell["overall"] is None and cell["total"] == 0, (name, slot, cell)
        elif pitches:
            seen_thrower += 1
            assert cell["overall"] is not None and cell["total"] == pitches, (name, slot, cell)

    assert seen_debut > 0 and seen_thrower > 0  # the matrix has both


def test_the_manifest_asks_no_evidence_of_a_share_that_is_null_out_of_nothing():
    found = set()
    for name, outcome in outcomes().items():
        found |= {v.code for v in outcome.violations if v.code.endswith("pitch_mix[].*.overall")}

    assert found == set()


def test_a_zero_share_out_of_no_pitches_is_still_refused_by_the_manifest():
    """The pipeline no longer writes it (F20); the check stays for any other writer."""

    payload = deepcopy(hard_outcome("home_debut_away_healthy").payload)
    cells = [row["home_starter"] for row in payload["matchups"][0]["charts"]["pitch_mix"] if row["home_starter"]["total"] == 0]
    assert cells
    for cell in cells:
        cell["overall"] = 0

    assert "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.overall" in codes(payload)


def test_publication_refuses_a_zero_share_out_of_no_pitches_and_accepts_a_null_one():
    payload = deepcopy(hard_outcome("home_debut_away_healthy").payload)
    assert failed_checks(payload) == []  # the pipeline's own output: null

    for row in payload["matchups"][0]["charts"]["pitch_mix"]:
        if row["home_starter"]["total"] == 0:
            row["home_starter"]["overall"] = 0

    assert any("share matches its counts" in description for description in failed_checks(payload))


@pytest.mark.parametrize("name", ["home_debut_away_healthy", "two_debuts"])
def test_the_report_of_a_game_with_a_debut_is_written_and_published(name):
    outcome = hard_outcome(name)

    assert outcome.live and outcome.blocked is None and outcome.failed == []
