"""P2.4 strata, seeded selection and the 20/20 split (docs/plans/P2.4.md sections 2 and 3)."""

from __future__ import annotations

from datetime import date, timedelta
import hashlib

import pytest

from data_pipeline import labels
from evals import build_dataset as bd

COLLECTION = date(2026, 10, 29)


def starter(pid, arsenal=2000, strikeout=500, control=500, seasons=6, innings=(6.0, 5.0, 6.0), flag=False):
    return bd.StarterFacts(
        pitcher_id=pid,
        samples={"arsenal": arsenal, "strikeout": strikeout, "control": control},
        prior_seasons=seasons,
        previous_innings=tuple(innings),
        flagged_opener=flag,
    )


def game(pk, a=None, b=None, kind="R", day=date(2026, 6, 1), played=True):
    return bd.Candidate(
        game_pk=pk,
        official_date=day.isoformat(),
        game_type=kind,
        played=played,
        starters=(a or starter(pk * 10 + 1), b or starter(pk * 10 + 2)),
    )


def stratum(c):
    result = bd.classify(c, COLLECTION)
    return None if result is None else result.primary


# --- the objective rules ------------------------------------------------------------------------


def test_the_seed_is_the_hash_of_the_frozen_strata_text_and_is_pinned():
    assert bd.SEED == hashlib.sha256(bd.SEED_TEXT.encode()).hexdigest()
    assert bd.SEED == "00672a7f0dc9483cc8d7d88e86cd6ed692c3a358f8a66043e7671d84d4927c99"  # pinned (pool rules added Oct 30, before any pool was read): any edit to the frozen text changes the seed and must be deliberate
    assert bd.STRATA == ("postseason", "opener", "limited", "veteran")  # the priority order of the plan


def test_a_veteran_game_needs_both_starters_to_clear_every_d24_threshold_and_three_prior_seasons():
    assert stratum(game(1)) == "veteran"
    for dim in labels.THRESHOLDS:  # the threshold itself clears; one below does not
        at = labels.THRESHOLDS[dim]
        assert stratum(game(2, starter(21, **{dim: at}))) == "veteran", dim
        assert stratum(game(3, starter(31, **{dim: at - 1}))) != "veteran", dim
    assert stratum(game(4, starter(41, seasons=3))) == "veteran"
    assert stratum(game(5, starter(51, seasons=2))) is None  # neither veteran nor any other stratum


def test_unknown_is_never_a_veteran_and_never_a_limited_sample():
    for unknown in (starter(61, arsenal=None), starter(62, strikeout=None), starter(63, control=None), starter(64, seasons=None)):
        assert stratum(game(6, unknown)) is None, unknown


def test_limited_is_positive_but_below_the_threshold_and_a_zero_sample_is_not_limited():
    assert stratum(game(7, starter(71, arsenal=1))) == "limited"
    assert stratum(game(8, starter(81, control=labels.THRESHOLDS["control"] - 1))) == "limited"
    assert stratum(game(9, starter(91, arsenal=0, strikeout=0, control=0))) is None  # a debut belongs to the regression suite
    assert stratum(game(10, starter(101, arsenal=0))) is None


def test_opener_is_an_average_under_two_innings_over_previous_starts():
    assert stratum(game(11, starter(111, innings=(1.0, 1.5, 2.0)))) == "opener"  # true decimal innings: average 1.5
    assert stratum(game(12, starter(121, innings=(2.0, 2.0)))) != "opener"  # exactly 2.0 is not under 2.0
    assert stratum(game(13, starter(131, innings=(1.9, 1.9)))) == "opener"


def test_a_pitcher_with_no_previous_start_is_not_an_opener_unless_the_schedule_flags_him():
    assert stratum(game(14, starter(141, innings=()))) != "opener"  # unknown average is not zero
    flagged = bd.classify(game(15, starter(151, innings=(), flag=True)), COLLECTION)
    assert flagged.primary == "opener"
    assert flagged.traits["opener"] == {"pitcher_id": 151, "evidence": "schedule_flag"}


@pytest.mark.parametrize("ip,expected", [("6.0", 6.0), ("1.2", 1 + 2 / 3), ("0.1", 1 / 3), ("5.1", 5 + 1 / 3)])
def test_innings_pitched_text_is_outs_not_a_decimal(ip, expected):
    assert bd.innings_from_ip(ip) == pytest.approx(expected)  # MLB writes 1.2 for one and two thirds


@pytest.mark.parametrize("bad", ["1.3", "x", "", None, "-1.0", "1.20", 1.2])
def test_a_malformed_innings_text_is_unknown_not_zero(bad):
    assert bd.innings_from_ip(bad) is None


def test_opener_evidence_records_the_average_and_the_number_of_starts():
    result = bd.classify(game(16, starter(161, innings=(1.0, 2.0, 1.0))), COLLECTION)
    assert result.traits["opener"]["evidence"] == {"average_innings": pytest.approx(4 / 3), "starts": 3}


def test_postseason_needs_a_final_game_before_the_collection_date():
    assert stratum(game(17, kind="D")) == "postseason"
    for kind in ("F", "D", "L", "W"):
        assert stratum(game(18, kind=kind)) == "postseason"
    assert bd.classify(game(19, kind="W", played=False), COLLECTION) is None  # scheduled, not final
    assert bd.classify(game(20, kind="W", day=COLLECTION), COLLECTION) is None  # not before the collection date
    assert bd.classify(game(21, day=COLLECTION + timedelta(days=1)), COLLECTION) is None
    assert stratum(game(22, kind="S")) is None and stratum(game(23, kind="E")) is None  # spring, exhibition


def test_overlapping_traits_take_the_priority_order_and_are_recorded_not_hidden():
    both = game(24, starter(241, arsenal=5, innings=(1.0,)), kind="L")
    result = bd.classify(both, COLLECTION)
    assert result.primary == "postseason"
    assert set(result.traits) == {"postseason", "opener", "limited"}
    assert bd.classify(game(25, starter(251, arsenal=5, innings=(1.0,))), COLLECTION).primary == "opener"
    assert bd.classify(game(26, starter(261, arsenal=5)), COLLECTION).primary == "limited"


# --- as_of ----------------------------------------------------------------------------------------


def test_the_historical_builder_rejects_a_missing_as_of_and_any_as_of_but_the_day_before():
    assert bd.check_as_of("2026-06-10", "2026-06-09") == date(2026, 6, 9)
    for bad in (None, "2026-06-10", "2026-06-11", "2026-06-08", ""):
        with pytest.raises(ValueError):
            bd.check_as_of("2026-06-10", bad)


def test_any_source_row_on_or_after_the_game_date_is_a_leak():
    bd.reject_rows_on_or_after(["2026-06-08", "2026-06-09"], "2026-06-10")  # control
    for leaked in ("2026-06-10", "2026-06-11"):
        with pytest.raises(bd.LeakageError):
            bd.reject_rows_on_or_after(["2026-06-01", leaked], "2026-06-10")


# --- seeded selection -----------------------------------------------------------------------------


def pool(n_per=40):
    """A pool with n_per candidate games for each stratum; every starter is distinct."""
    out, pk = [], 1000
    for kind, make in (
        ("postseason", lambda i: dict(kind="D")),
        ("opener", lambda i: dict(a=starter(pk * 10 + 1, innings=(1.0, 1.0)))),
        ("limited", lambda i: dict(a=starter(pk * 10 + 1, arsenal=50))),
        ("veteran", lambda i: dict()),
    ):
        for i in range(n_per):
            pk += 1
            out.append(game(pk, day=date(2026, 5, 1) + timedelta(days=i), **make(i)))
    return out


def test_selection_is_deterministic_and_independent_of_the_order_of_the_pool():
    a = bd.select(pool(), COLLECTION)
    b = bd.select(list(reversed(pool())), COLLECTION)
    assert [c.case_id for s in bd.STRATA for c in a.cases[s]] == [c.case_id for s in bd.STRATA for c in b.cases[s]]


def test_ten_per_stratum_mutually_exclusive_and_no_shared_game_or_starter():
    sel = bd.select(pool(), COLLECTION)
    assert {s: len(sel.cases[s]) for s in bd.STRATA} == {s: 10 for s in bd.STRATA}
    assert sel.short == {}
    ids = [c.case_id for s in bd.STRATA for c in sel.cases[s]]
    pks = [c.game_pk for s in bd.STRATA for c in sel.cases[s]]
    pitchers = [p for s in bd.STRATA for c in sel.cases[s] for p in c.pitcher_ids]
    assert len(set(ids)) == len(set(pks)) == 40 and len(set(pitchers)) == len(pitchers) == 80


def test_the_pick_follows_the_seeded_rank_not_the_date():
    sel = bd.select(pool(), COLLECTION)
    veterans = [c for c in pool() if stratum(c) == "veteran"]
    expected = sorted(veterans, key=lambda c: bd.rank(c.game_pk))[:10]
    assert [c.game_pk for c in sel.cases["veteran"]] == [c.game_pk for c in expected]
    assert bd.rank(5) == hashlib.sha256((bd.SEED + "5").encode()).hexdigest()


def test_a_starter_or_game_already_used_is_skipped_to_the_next_rank():
    shared = starter(777)
    candidates = [game(pk, shared, starter(pk * 10 + 2)) for pk in range(1, 30)]
    sel = bd.select(candidates, COLLECTION)
    assert len(sel.cases["veteran"]) == 1  # the one starter is in one case only; the others are skipped, not reused
    assert sel.short == {"postseason": 10, "opener": 10, "limited": 10, "veteran": 9}


def test_a_short_stratum_is_reported_short_not_padded():
    c = [x for x in pool() if stratum(x) != "postseason"] + [x for x in pool() if stratum(x) == "postseason"][:4]
    sel = bd.select(c, COLLECTION)
    assert len(sel.cases["postseason"]) == 4 and sel.short == {"postseason": 6}
    assert all(len(sel.cases[s]) == 10 for s in bd.STRATA[1:])  # the others are not topped up from the short one


def test_an_ineligible_candidate_is_never_selected():
    bad = [game(pk, kind="W", played=False) for pk in range(1, 20)] + [game(pk, day=COLLECTION) for pk in range(20, 40)]
    sel = bd.select(bad, COLLECTION)
    assert all(len(v) == 0 for v in sel.cases.values())


def test_every_case_has_as_of_the_day_before_and_its_traits_recorded():
    sel = bd.select(pool(), COLLECTION)
    for s in bd.STRATA:
        for c in sel.cases[s]:
            assert bd.check_as_of(c.official_date, c.as_of) == date.fromisoformat(c.official_date) - timedelta(days=1)
            assert s in c.traits and c.stratum == s


# --- the split --------------------------------------------------------------------------------------


def test_split_is_five_and_five_per_stratum_and_seeded():
    sel = bd.select(pool(), COLLECTION)
    split = bd.assign_split(sel)
    assert len(split) == 40
    for s in bd.STRATA:
        marks = [split[c.case_id] for c in sel.cases[s]]
        assert marks.count("dev") == marks.count("test") == 5
    assert split == bd.assign_split(bd.select(list(reversed(pool())), COLLECTION))  # same cases, same split


def test_a_short_stratum_splits_with_the_test_half_rounded_down():
    c = [x for x in pool() if stratum(x) != "veteran"] + [x for x in pool() if stratum(x) == "veteran"][:7]
    split = bd.assign_split(bd.select(c, COLLECTION))
    vets = [cid for cid in split if cid.startswith("veteran")]
    assert sorted(split[v] for v in vets).count("test") == 3 and sorted(split[v] for v in vets).count("dev") == 4


def test_an_unreadable_start_is_skipped_not_counted_as_zero_innings():
    assert stratum(game(30, starter(301, innings=(None, 5.0, 6.0)))) != "opener"  # 0 would average 3.7; skipped gives 5.5
    assert stratum(game(31, starter(311, innings=(None, None)))) != "opener"  # nothing readable: unknown
    assert stratum(game(32, starter(321, innings=(None, 1.0)))) == "opener"
