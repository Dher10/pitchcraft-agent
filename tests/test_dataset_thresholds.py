"""P2.4 D32 recompute: the lineup-vs-hand quartiles (docs/plans/P2.4.md section 1)."""

from __future__ import annotations

from datetime import date

import pytest

from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline as lp
from evals import thresholds as th
from tests.test_team_splits_as_of import frame, pa_rows

CONSTANT = {"k": "OFFENSE_K_NOTE_PCT", "bb": "OFFENSE_BB_NOTE_PCT", "ops": "OFFENSE_OPS_STRONG"}


def row(team, hand, pa, k=20.0, bb=8.0, ops=0.700):
    return th.TeamHand(team, hand, pa, k, bb, ops)


def rows_from(ks, bbs, opss, pa=400):
    return [row(f"T{i // 2}", "L" if i % 2 else "R", pa, k, bb, ops) for i, (k, bb, ops) in enumerate(zip(ks, bbs, opss))]


def at_cutoffs():
    # 60 rows whose 75th percentile (linear, index 44.25) lies in a constant tail: exactly 23.0 / 9.0 / .750.
    return [20.0] * 44 + [23.0] * 16, [8.0] * 44 + [9.0] * 16, [0.700] * 44 + [0.750] * 16


def test_percentile_is_the_linear_default():
    assert th.percentile([1.0, 2.0, 3.0, 4.0, 5.0], 75) == 4.0
    assert th.percentile([1.0, 2.0, 3.0, 4.0], 75) == 3.25


def test_rounding_is_half_up_on_the_stated_grids():
    assert th.round_k_bb(22.5) == 23.0 and th.round_k_bb(22.4999) == 22.0
    assert th.round_k_bb(8.5) == 9.0  # half up, not the banker's rounding of round()
    assert th.round_ops(0.7525) == 0.755 and th.round_ops(0.7524) == 0.750
    assert th.round_ops(0.7475) == 0.750


def test_a_row_under_200_plate_appearances_is_excluded_and_listed():
    ks, bbs, opss = at_cutoffs()
    rows = rows_from(ks, bbs, opss)
    rows[3] = row("SHORT", "L", 199, 99.0, 99.0, 9.0)  # would dominate the top quartile if it were kept
    rows[4] = row("EDGE", "R", 200, 20.0, 8.0, 0.7)  # control: exactly 200 stays

    result = th.recompute(rows)

    assert [(e.team, e.hand, e.pa) for e in result.excluded] == [("SHORT", "L", 199)]
    assert result.n_used == 59
    assert result.cutoffs == {"k": 23.0, "bb": 9.0, "ops": 0.750}


def test_unchanged_when_the_rounded_quartiles_equal_the_current_cutoffs():
    result = th.recompute(rows_from(*at_cutoffs()))
    comparison = th.compare(result)

    assert result.cutoffs == {"k": 23.0, "bb": 9.0, "ops": 0.750}
    assert comparison.unchanged and comparison.changed == {}


@pytest.mark.parametrize("which,value", [("k", 24.0), ("bb", 10.0), ("ops", 0.780)])
def test_changed_when_any_single_cutoff_moves_and_only_that_one_is_named(which, value):
    columns = dict(zip(("k", "bb", "ops"), at_cutoffs()))
    columns[which][44:] = [value] * 16

    comparison = th.compare(th.recompute(rows_from(columns["k"], columns["bb"], columns["ops"])))

    assert not comparison.unchanged
    assert comparison.changed == {which: (getattr(labels, CONSTANT[which]), value)}


def test_the_comparison_reads_the_constants_of_labels(monkeypatch):
    monkeypatch.setattr(labels, "OFFENSE_K_NOTE_PCT", 22.0)  # a different current value: now it differs
    assert set(th.compare(th.recompute(rows_from(*at_cutoffs()))).changed) == {"k"}


def test_hands_are_reported_separately_and_pooled():
    rows = [row(f"T{i}", h, 400, k, 8.0, 0.7) for i in range(30) for h, k in (("L", 18.0), ("R", 26.0))]

    result = th.recompute(rows)

    assert result.by_hand["L"]["k"][75] == 18.0 and result.by_hand["R"]["k"][75] == 26.0
    assert result.pooled["k"][75] == 26.0  # half of the 60 rows are 26: the pooled 75th percentile lies there
    assert result.cutoffs["k"] == 26.0


def test_too_few_rows_after_exclusion_is_an_error_not_a_quartile():
    with pytest.raises(ValueError):
        th.recompute([row("A", "L", 400), row("B", "R", 400)])


def test_rows_come_from_the_split_code_of_the_pipeline_with_unrounded_rates():
    df = frame(
        pa_rows("NYY", "L", ["strikeout"] * 3 + ["walk"] + ["single"] * 6)
        + pa_rows("NYY", "R", ["double"] * 4)
    )

    got = th.team_hand_rows({"NYY": df}, date(2026, 9, 27))

    assert {(r.team, r.hand) for r in got} == {("NYY", "L"), ("NYY", "R")}
    left = next(r for r in got if r.hand == "L")
    assert (left.pa, left.k, left.bb) == (10, 30.0, 10.0)
    assert left.ops == float(lp.derive_team_splits(df, "NYY", "2026-09-27")["vl"]["ops"])  # same engine as the card
    third = frame(pa_rows("NYY", "L", ["strikeout"] * 3 + ["single"] * 4))
    (odd,) = th.team_hand_rows({"NYY": third}, date(2026, 9, 27))
    assert odd.k == pytest.approx(3 / 7 * 100)  # not 42.9: the card's rounding is not applied before the quartile


def test_a_postseason_or_post_cutoff_row_never_reaches_the_quartiles():
    df = frame(
        pa_rows("NYY", "L", ["single"] * 5)
        + pa_rows("NYY", "L", ["home_run"] * 9, game_type="D")
        + pa_rows("NYY", "L", ["home_run"] * 9, game_date="2026-09-28")
    )

    (only,) = th.team_hand_rows({"NYY": df}, date(2026, 9, 27))

    assert only.pa == 5
