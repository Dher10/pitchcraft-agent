"""`pitch_data_status` is computed from the starters, not written (P0.15-D2.1b, F1).

It is `fetched_snapshot` when at least one starter has a pitch on record and `unavailable` when none
has (the word `rates.source` uses for a figure that was not given), over the real pipeline (faked sources) for the cases of the matrix and the hard cases.
"""

from __future__ import annotations

import pytest

from tests.matrix import MATRIX, hard_outcome, matrix_outcome

PITCHED = ("two_limited", "home_limited_away_healthy", "home_debut_away_healthy")


@pytest.mark.parametrize("name", PITCHED)
def test_a_game_where_some_starter_has_pitches_is_fetched(name):
    assert hard_outcome(name).matchup["data_confidence"]["pitch_data_status"] == "fetched_snapshot"


def test_a_game_of_two_debuts_has_no_pitch_data():
    assert hard_outcome("two_debuts").matchup["data_confidence"]["pitch_data_status"] == "unavailable"


def test_the_status_agrees_with_the_samples_in_every_live_case_of_the_matrix():
    seen = set()
    for case in MATRIX:
        outcome = matrix_outcome(case)
        if not outcome.live:
            continue
        matchup = outcome.matchup
        pitched = any(s["sample"]["arsenal"]["pitches"] for s in matchup["starters"].values())
        expected = "fetched_snapshot" if pitched else "unavailable"
        assert matchup["data_confidence"]["pitch_data_status"] == expected, case.id
        seen.add(expected)
    assert seen == {"fetched_snapshot", "unavailable"}  # opening day: both are debuts


def test_the_status_is_computed_by_the_generator_not_read_from_the_snapshot():
    """The snapshot holds no confidence block, so nothing the sources send can write the status."""

    outcome = hard_outcome("two_debuts")
    snapshot_text = str(outcome.snapshot)

    assert "pitch_data_status" not in snapshot_text and "data_confidence" not in snapshot_text
    assert outcome.matchup["data_confidence"]["pitch_data_status"] == "unavailable"
