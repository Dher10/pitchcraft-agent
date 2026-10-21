"""P0.16-f: genuine false claim conditions affected by the QA5 fixes.

Generated claims and their text stay intact while payload facts change. The
ordinary checking mechanism is never replaced. Source conservation, finite
numbers and event-domain tests supply evidence the registry cannot reconstruct;
frontend conditions are separately exercised by MeasuredPitchFacts.test.tsx.
"""

from copy import deepcopy

import pytest

from data_pipeline import claims_registry as registry
from data_pipeline.claims import catalogs_of, verify_claims
from data_pipeline.contract_checks import check_contract
from tests.corpus import build, golden_payload, published
from tests.matrix import hard_outcome, pitcher_frame


AWAY, HOME = "away_starter", "home_starter"


def source(monkeypatch, name):
    return published(build(monkeypatch, name) if name == "live_complete" else golden_payload(monkeypatch, name))


def codes(payload):
    return {violation.code for violation in check_contract(payload)}


def assert_false_condition(original, changed, key, reason, slot=None):
    # No stale-text failure can masquerade as a predicate failure. A claim
    # must actually exist, and its exact reason must be new after the edit.
    assert verify_claims(original) == verify_claims(changed) == []
    claims = original["matchups"][0]["report"]["claims"]
    assert any(claim["key"] == key and (slot is None or claim["subject"] == slot) for claim in claims)
    code = f"rule4:{key}#{reason}"
    assert code not in codes(original)
    assert code in codes(changed) - codes(original)


@pytest.mark.parametrize("key,path,value,reason,fixture,slot", [
    ("analyst.have.pitches", ("sample", "arsenal", "pitches"), None, "count", "live_both_limited", AWAY),
    ("analyst.have.pitches", ("sample", "arsenal", "pitches"), 11, "count", "live_both_limited", AWAY),
    ("analyst.have.batters", ("sample", "rates", "batters_faced"), None, "count", "live_both_limited", AWAY),
    ("analyst.have.batters", ("sample", "rates", "batters_faced"), 4, "count", "live_both_limited", AWAY),
    # Unlike the earlier zero/unknown regression, keep BF exactly zero and
    # falsify only the source guard, so deleting that guard is detectable.
    ("analyst.have.no_batters", ("sample", "rates", "source"), "unavailable", "unknown_not_zero", "live_measured_zero_counts", AWAY),
    ("analyst.data.contact", ("sample", "rates", "home_runs"), None, "unknown", "live_complete", AWAY),
    ("analyst.data.contact", ("sample", "rates", "batters_faced"), None, "unknown", "live_complete", AWAY),
    ("analyst.data.no_home_runs", ("sample", "rates", "home_runs"), 1, "known", "live_no_home_runs", AWAY),
    ("analyst.read.shows", ("pitching_profile", "swing_miss_label"), None, "label", "live_complete", AWAY),
    ("analyst.read.shows", ("pitching_profile", "command_label"), None, "label", "live_complete", AWAY),
    ("analyst.strength.swing_miss", ("pitching_profile", "swing_miss_label"), None, "label", "live_complete", AWAY),
    ("analyst.strength.command", ("pitching_profile", "command_label"), None, "label", "live_strong_strikeouts_weak_command", HOME),
    ("analyst.strength.command", ("sample", "limited", "control"), True, "limited", "live_strong_strikeouts_weak_command", HOME),
    ("analyst.data.strikeout", ("sample", "limited", "strikeout"), False, "not_limited", "live_both_limited", AWAY),
    ("analyst.data.control", ("sample", "limited", "control"), False, "not_limited", "live_both_limited", AWAY),
])
def test_a_retained_count_or_rate_claim_needs_its_actual_data(monkeypatch, key, path, value, reason, fixture, slot):
    payload = source(monkeypatch, fixture)
    changed = deepcopy(payload)
    parent = changed["matchups"][0]["starters"][slot]
    for part in path[:-1]:
        parent = parent[part]
    assert parent[path[-1]] != value
    parent[path[-1]] = value
    assert_false_condition(payload, changed, key, reason, slot)


@pytest.mark.parametrize("fixture,key,field,value,reason", [
    ("live_complete", "analyst.offense.strong", "ops_vs_hand", None, "ops"),
    ("live_complete", "analyst.offense.note_walks", "bb_rate_vs_hand", None, "rate"),
    ("live_unknown_figures", "analyst.offense.note_strikeouts", "k_rate_vs_hand", None, "rate"),
    ("live_no_home_runs", "analyst.offense.unavailable", "ops_vs_hand", ".801", "known"),
])
def test_a_retained_offense_claim_needs_the_figure_for_the_facing_lineup(monkeypatch, fixture, key, field, value, reason):
    payload = source(monkeypatch, fixture)
    changed = deepcopy(payload)
    offense = changed["matchups"][0]["teams"]["home"]["offense_profile"]
    assert offense[field] != value
    offense[field] = value
    assert_false_condition(payload, changed, key, reason, AWAY)


def test_an_offense_scope_sentence_needs_at_least_one_figure(monkeypatch):
    payload = source(monkeypatch, "live_complete")
    changed = deepcopy(payload)
    offense = changed["matchups"][0]["teams"]["home"]["offense_profile"]
    for field in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand"):
        offense[field] = None
    # Deliberately retain the scope and sentence while removing its evidence.
    assert offense["scope"] is not None
    assert_false_condition(payload, changed, "analyst.scope.offense", "no_offense_figure")


def test_a_counts_scope_sentence_cannot_outlive_the_counts_group(monkeypatch):
    payload = source(monkeypatch, "live_scopes_differ")
    changed = deepcopy(payload)
    starter = changed["matchups"][0]["starters"][AWAY]
    rates = starter["sample"]["rates"]
    for field in ("batters_faced", "strikeouts", "walks", "home_runs"):
        rates[field] = None
    rates.update(source="unavailable", scope=None)
    starter["season_summary"]["scopes"]["counts"] = None
    for field in ("strikeouts", "walks", "home_runs_allowed"):
        starter["season_summary"][field] = None
    starter["sample"]["limited"].update(strikeout=True, control=True)
    starter["pitching_profile"].update(command_label=None, swing_miss_label=None, contact_risk_label=None)
    assert_false_condition(payload, changed, "analyst.scope.season_figures", "figures")


@pytest.mark.parametrize("slot", [AWAY, HOME])
def test_supported_putaway_evidence_must_quote_its_actual_numeric_share(monkeypatch, slot):
    payload = source(monkeypatch, "live_complete")
    changed = deepcopy(payload)
    matchup = changed["matchups"][0]
    pitch = matchup["starters"][slot]["pitching_profile"]["putaway_pitch"]
    row = next(row for row in matchup["charts"]["pitch_mix"] if row["pitch"] == pitch)
    row[slot]["overall"] += 1
    assert_false_condition(payload, changed, "critic.pitch.supported_putaway", "usage", slot)


@pytest.mark.parametrize("slot,control_name,present_name", [
    (AWAY, "no_offense_data", "six_type_overlap"),
    (HOME, "six_type_no_overlap", "six_type_overlap_reversed"),
])
def test_a_sixth_pitch_present_in_the_full_source_cannot_have_an_absence_claim(slot, control_name, present_name):
    control, present = hard_outcome(control_name), hard_outcome(present_name)
    assert control.live and present.live and control.payload is not None and present.payload is not None
    side = "away" if slot == AWAY else "home"
    assert (pitcher_frame(getattr(control.scenario, side))["pitch_type"] == "FC").sum() == 0
    assert (pitcher_frame(getattr(present.scenario, side))["pitch_type"] == "FC").sum() == 10
    cell = next(row for row in present.matchup["charts"]["pitch_mix"] if row["pitch"] == "Cutter")[slot]
    assert cell["count"] == 10 and cell["overall"] == 0.9

    def failures(outcome):
        payload, matchup = outcome.payload, outcome.matchup
        claim = {"id": "absence-probe", "key": "critic.pitch.absent", "subject": slot,
                 "args": {"pitch": "Cutter", "name": matchup["starters"][slot]["name"]}, "location": None}
        index = registry.ClaimIndex([*matchup["report"]["claims"], claim], catalogs_of(payload))
        return registry.run_rule(claim["key"], registry.Ctx(payload, matchup, claim, index, {}))

    assert failures(control) == []  # genuinely absent in this starter's full source
    assert {failure.reason for failure in failures(present)} == {"thrown"}
