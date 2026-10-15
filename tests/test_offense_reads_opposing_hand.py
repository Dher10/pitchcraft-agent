"""A lineup is read against the hand of the starter it faces (P0.15-D2.1b, first step).

Before the confidence note is built from the offense of each lineup, the test shows the pipeline reads
the right key of the split: `vr` for a lineup that faces a right-handed starter, `vl` for one that faces
a left-handed starter. In the matrix world the away starter throws L and the home starter throws R, so the
away lineup faces an R and the home lineup an L. The two splits of the faked Savant month differ, so a
swapped key would show.
"""

from __future__ import annotations

from tests.matrix import MATRIX, matrix_outcome

CASE = next(c for c in MATRIX if c.id == "complete-regular-healthy-normal-present")


def _figures(split: dict) -> tuple[str, str, str]:
    return split["ops"], f"{split['k_rate']:.1f}%", f"{split['bb_rate']:.1f}%"


def _shown(offense: dict) -> tuple[str, str, str]:
    return offense["ops_vs_hand"], offense["k_rate_vs_hand"], offense["bb_rate_vs_hand"]


def test_the_two_splits_of_the_world_differ_so_a_swapped_key_would_show():
    snapshot = matrix_outcome(CASE).snapshot
    for key in ("away_team_splits", "home_team_splits"):
        assert _figures(snapshot[key]["vl"]) != _figures(snapshot[key]["vr"])


def test_the_lineup_facing_a_right_handed_starter_shows_the_vr_split():
    outcome = matrix_outcome(CASE)
    assert outcome.matchup["starters"]["home_starter"]["throws"] == "R"
    offense = outcome.matchup["teams"]["away"]["offense_profile"]
    assert offense["vs_pitcher_hand"] == "RHP"
    assert _shown(offense) == _figures(outcome.snapshot["away_team_splits"]["vr"])


def test_the_lineup_facing_a_left_handed_starter_shows_the_vl_split():
    outcome = matrix_outcome(CASE)
    assert outcome.matchup["starters"]["away_starter"]["throws"] == "L"
    offense = outcome.matchup["teams"]["home"]["offense_profile"]
    assert offense["vs_pitcher_hand"] == "LHP"
    assert _shown(offense) == _figures(outcome.snapshot["home_team_splits"]["vl"])
