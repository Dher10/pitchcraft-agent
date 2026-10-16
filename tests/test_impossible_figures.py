"""Figures of a live starter that cannot be true together are a violation of the contract (P0.15-D2.2f, F21).

The strict invariants of a pitching line: a home run is a batter faced, so `home_runs <= batters_faced`; a
strikeout, a walk and a home run are different plate appearances, so their sum is at most `batters_faced`;
and every batter faced took at least one typed pitch, so `batters_faced <= pitches`. A starter whose figures
break one is published with figures from two different samples.

The check is `provenance.impossible_figures`, next to the manifest, under the rule 1 code
`rule1:impossible_figures#<which>`. It is added with its fix, so it is not in `known_violations.py`.

Tolerance, documented in the contract (6.5): an intentional walk is a batter with no typed pitch (Statcast writes
a row for it with no `pitch_type`), so `batters_faced <= pitches` could fail only for a sample smaller than one
pitch per batter, which is a sample of a few batters. A figure that is `None` is unknown and is not compared.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pytest

from data_pipeline import provenance
from data_pipeline.contract_checks import check_contract
from data_pipeline.known_violations import KNOWN_VIOLATIONS
from tests.corpus import GOLDEN_NAMES, build, published
from tests.golden_scenarios import scenarios

AWAY, HOME = "away_starter", "home_starter"
HOME_RUNS = "rule1:impossible_figures#home_runs_over_batters_faced"
OUTCOMES = "rule1:impossible_figures#outcomes_over_batters_faced"
PITCHES = "rule1:impossible_figures#batters_faced_over_pitches"
ALL = {HOME_RUNS, OUTCOMES, PITCHES}


@pytest.fixture
def live(monkeypatch):
    return published(build(monkeypatch, "live_complete"))


def codes(payload: dict[str, Any]) -> set[str]:
    return {code for code, _where, _message in provenance.impossible_figures(payload)}


def with_figures(payload: dict[str, Any], slot: str = AWAY, **figures: Any) -> dict[str, Any]:
    """A copy whose first matchup's starter has the given figures (`pitches` is the arsenal's, the rest the rates')."""

    copy = deepcopy(payload)
    sample = copy["matchups"][0]["starters"][slot]["sample"]
    for key, value in figures.items():
        if key == "pitches":
            sample["arsenal"]["pitches"] = value
        else:
            sample["rates"][key] = value
    return copy


def test_the_check_is_in_the_rules_of_the_contract_and_not_in_the_table_of_tolerated_violations():
    assert not any("impossible_figures" in code for code in KNOWN_VIOLATIONS)


def test_a_coherent_live_payload_has_no_impossible_figure(live):
    sample = live["matchups"][0]["starters"][AWAY]["sample"]
    assert sample["rates"]["batters_faced"] is not None and sample["arsenal"]["pitches"] is not None  # something to compare

    assert codes(live) == set()


@pytest.mark.parametrize("slot", [AWAY, HOME])
def test_more_home_runs_than_batters_faced_is_impossible(live, slot):
    assert codes(with_figures(live, slot, batters_faced=10, strikeouts=0, walks=0, home_runs=11)) >= {HOME_RUNS}


@pytest.mark.parametrize("slot", [AWAY, HOME])
def test_more_strikeouts_walks_and_home_runs_than_batters_faced_is_impossible(live, slot):
    found = codes(with_figures(live, slot, batters_faced=30, strikeouts=15, walks=10, home_runs=6))

    assert OUTCOMES in found and HOME_RUNS not in found  # each alone fits; together they do not


@pytest.mark.parametrize("slot", [AWAY, HOME])
def test_more_batters_faced_than_pitches_is_impossible(live, slot):
    found = codes(with_figures(live, slot, pitches=100, batters_faced=101, strikeouts=1, walks=1, home_runs=1))

    assert found == {PITCHES}


@pytest.mark.parametrize(
    "figures",
    [
        {"batters_faced": 10, "strikeouts": 4, "walks": 3, "home_runs": 3},  # the sum equals batters faced
        {"batters_faced": 10, "strikeouts": 0, "walks": 0, "home_runs": 10},  # every batter homered
        {"pitches": 40, "batters_faced": 40, "strikeouts": 10, "walks": 5, "home_runs": 5},  # one pitch each
        {"batters_faced": 0, "strikeouts": 0, "walks": 0, "home_runs": 0},  # a measured zero is coherent
    ],
)
def test_control_figures_at_the_limit_are_possible(live, figures):
    assert codes(with_figures(live, **figures)) == set()


@pytest.mark.parametrize(
    "figures",
    [
        {"pitches": None},
        {"batters_faced": None, "strikeouts": None, "walks": None, "home_runs": None},
        {"home_runs": None, "walks": None},
        {"pitches": None, "batters_faced": 500, "strikeouts": None, "walks": None, "home_runs": None},
    ],
)
def test_control_an_unknown_figure_is_not_compared(live, figures):
    assert codes(with_figures(live, **figures)) == set()


def test_the_check_names_the_starter_and_the_figures(live):
    found = provenance.impossible_figures(with_figures(live, HOME, batters_faced=10, strikeouts=0, walks=0, home_runs=11))

    assert {code for code, _where, _message in found} == {HOME_RUNS, OUTCOMES}  # 11 home runs are also 11 plate appearances
    code, where, message = next(f for f in found if f[0] == HOME_RUNS)
    assert "home_starter" in where and where.startswith("matchup_")
    assert "11" in message and "10" in message


def test_a_demo_matchup_is_not_asked(monkeypatch):
    """Only a starter with a `sample` (what a live run measures) has figures to compare; a demo starter has none."""

    demo = published(build(monkeypatch, "demo"))

    assert all("sample" not in starter for m in demo["matchups"] for starter in m["starters"].values())
    assert codes(demo) == set()


def test_the_contract_reports_it_for_a_live_file(live):
    broken = with_figures(live, batters_faced=10, strikeouts=0, walks=0, home_runs=11)

    assert HOME_RUNS in {violation.code for violation in check_contract(broken)}
    assert HOME_RUNS not in {violation.code for violation in check_contract(live)}


GOLDEN_LIVE = [name for name in GOLDEN_NAMES if name.startswith("live_")]


@pytest.mark.parametrize("name", GOLDEN_LIVE)
def test_every_live_scenario_of_the_golden_file_has_figures_that_can_be_true_together(monkeypatch, name):
    """The golden file shows states a pipeline can produce, and no pipeline produces a starter with 400 batters faced
    and 40 pitches (reviewer's coherence item)."""

    matchup = scenarios(monkeypatch)[name]

    assert provenance.impossible_figures({"matchups": [matchup]}) == [], name


def test_the_golden_file_has_live_scenarios_to_check():
    assert len(GOLDEN_LIVE) >= 10


# --- the unknown pitch count that the correction of F21 writes ----------------------------------------------------


def test_the_manifest_accepts_a_null_pitch_count_and_scope_where_the_mix_has_none_of_his_pitches(live):
    """
    The manifest entries of `arsenal.pitches`, `arsenal.scope` and the mix cell. The rest of this payload is not made
    coherent (labels, roles, claims); the end-to-end cases of the matrix (`statcast_gap`) carry that.
    """

    def unavailable(payload):
        starter = payload["matchups"][0]["starters"][AWAY]
        starter["sample"]["arsenal"] = {"pitches": None, "scope": None}
        for row in payload["matchups"][0]["charts"]["pitch_mix"]:
            row["away_starter"] = {"overall": None, "vs_lhh": None, "vs_rhh": None, "count": 0, "total": 0}

    payload = deepcopy(live)
    unavailable(payload)
    found = {c for c in (v.code for v in check_contract(payload)) if "arsenal" in c or "pitch_mix" in c}

    assert found == set(), found


def test_the_manifest_rejects_an_unknown_pitch_count_next_to_pitches_he_threw(live):
    broken = with_figures(live, pitches=None)  # the mix still holds his pitches
    broken["matchups"][0]["starters"][AWAY]["sample"]["arsenal"]["scope"] = None

    codes_found = {v.code for v in check_contract(broken)}

    assert any(c.startswith("rule1:derivation_mismatch#") and c.endswith("sample.arsenal.pitches") for c in codes_found), codes_found
