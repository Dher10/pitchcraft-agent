"""The manifest of a live payload: rules 1 and 2 of the data contract (P0.15-D3.3b-2).

`data_pipeline/provenance.py` says, for every leaf of a live file, whether it is a source value, a documented
derivation, a label, a recorded sentence or an unavailable state, and checks what it can: the type, a value
that stands for something the source did not give, a derivation recomputed, and the evidence a zero needs.

The negative tests feed it a payload that breaks one rule and require the code of that rule. The structure
tests hold the manifest to the payloads: no leaf without an entry, no entry that nothing uses.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline import labels, provenance
from data_pipeline.contract_checks import check_contract
from tests.corpus import build, published
from tests.matrix import hard_outcome, outcomes

AWAY, HOME = "away_starter", "home_starter"


@pytest.fixture(scope="module")
def live():
    """A live payload with everything the pipeline can give: the base for the negative tests."""

    with pytest.MonkeyPatch.context() as monkeypatch:
        return published(build(monkeypatch, "live_complete"))


def codes(payload) -> set[str]:
    return {code for code, _, _ in provenance.findings(payload)}


def matchup(payload, slot=None):
    found = payload["matchups"][0]
    return found if slot is None else found["starters"][slot]


# --- the manifest holds the payloads ----------------------------------------------------------------


def test_every_leaf_of_every_live_payload_has_an_entry():
    unlisted = {
        code
        for outcome in outcomes().values()
        if outcome.payload
        for code in codes(outcome.payload)
        if code.startswith("rule1:unlisted")
    }

    assert unlisted == set()


def test_every_entry_of_the_manifest_is_used_by_some_payload():
    """A dead entry is a field that no longer exists (or never did): it is deleted, not kept."""

    used = set()
    for outcome in outcomes().values():
        if not outcome.payload or not outcome.live:
            continue
        for path, _ in provenance._leaves(outcome.payload):
            if provenance._in_scope(outcome.payload, path):
                entry = provenance.entry_for(provenance.normalize(path))
                if entry:
                    used.add(entry.pattern)
    dead = sorted({entry.pattern for entry in provenance.MANIFEST} - used)

    assert dead == []


def test_the_patterns_of_the_manifest_are_unique():
    patterns = [entry.pattern for entry in provenance.MANIFEST]

    assert len(patterns) == len(set(patterns))


def test_a_fact_names_its_finding_and_only_a_fact_does():
    for entry in provenance.MANIFEST:
        assert (entry.kind == provenance.FACT) == bool(entry.finding), entry.pattern


def test_a_demo_file_is_not_asked_and_neither_are_the_demo_matchups_of_a_live_file(live):
    demo = deepcopy(live)
    demo["metadata"]["data_mode"] = "demo_cached"
    demo["matchups"][0]["new_field"] = 1

    assert provenance.findings(demo) == []
    mixed = deepcopy(live)
    # a demo matchup in a live file (the generator writes none since D2.4a) is rule 6's finding, not walked here
    mixed["matchups"].append({"id": "matchup_002", "data_confidence": {"level": "cached"}, "a_demo_field_nobody_listed": 1})

    assert not any("a_demo_field_nobody_listed" in where for _, where, _ in provenance.findings(mixed))


# --- rule 1: provenance --------------------------------------------------------------------------


def test_rule_1_a_field_with_no_entry_is_unlisted(live):
    payload = deepcopy(live)
    payload["matchups"][0]["game"]["weather"] = "sunny"

    assert "rule1:unlisted#matchups[].game.weather" in codes(payload)


def test_rule_1_a_null_where_the_entry_does_not_allow_one_is_not_declared(live):
    payload = deepcopy(live)
    matchup(payload)["game"]["title"] = None

    assert "rule1:null_not_declared#matchups[].game.title" in codes(payload)


def test_rule_1_an_archive_row_in_a_live_file_is_found(live):
    """F4 (D2.4a): the live archive is empty; a row has no entry in the manifest (unlisted) as well as being rule 6's finding."""

    from data_pipeline import demo_inputs

    assert live["archive"] == [] and not any(w.startswith("archive") for _, w, _ in provenance.findings(live))
    payload = deepcopy(live)
    row = deepcopy(demo_inputs.build_demo_payload()["archive"][1])
    row["id"] = matchup(live)["id"]  # a row of a live matchup is walked; one of a demo matchup is rule 6's finding
    payload["archive"] = [row]

    assert "rule1:unlisted#archive[].id" in codes(payload)


def test_rule_1_a_value_of_the_wrong_type_is_found(live):
    payload = deepcopy(live)
    matchup(payload, AWAY)["throws"] = 1

    assert "rule1:wrong_type#matchups[].starters.*.throws" in codes(payload)


def test_rule_1_a_constant_that_asserts_a_fact_is_a_violation_whatever_its_value(live):
    found = codes(live)

    # F5 (closed in D2.5a): the status and the lineup status are the schedule's, no longer constants; no fact is left
    assert not {code for code in found if code.startswith("rule1:constant_asserts_fact")}
    assert "rule1:constant_asserts_fact#metadata.data_sources[]" not in found  # F3 (D2.4b): a label of a closed set


def test_rule_1_the_sources_and_disclaimers_of_a_live_file_are_the_ones_it_may_say(live):
    """F3 (D2.4b): a live file lists the live sources and the live disclaimers; the demo's are not labels of a live file."""

    assert "rule1:wrong_type#metadata.data_sources[]" not in codes(live)
    assert "rule1:wrong_type#disclaimers[]" not in codes(live)
    for edit, pattern in (
        (lambda p: p["metadata"]["data_sources"].append("Cached demo snapshots (always available)"), "metadata.data_sources[]"),
        (lambda p: p["disclaimers"].append("PitchCraft is a capstone demo and not a betting or gambling tool."), "disclaimers[]"),
    ):
        payload = deepcopy(live)
        edit(payload)

        assert f"rule1:wrong_type#{pattern}" in codes(payload), pattern


def test_rule_1_no_step_of_the_workflow_is_a_constant_that_asserts_a_fact(live):
    """F19 (closed in D2.4d): each of the five statuses is read from the result of its step (tests/test_workflow_step_status.py)."""

    assert not [w for code, w, _ in provenance.findings(live) if code.startswith("rule1:constant_asserts_fact#agent_workflow")]


def test_rule_1_the_postgame_step_must_agree_with_what_it_reports(live):
    payload = deepcopy(live)
    payload["agent_workflow"]["steps"][4]["status"] = "completed"  # its output says no starter was graded (a live file)

    assert "rule1:derivation_mismatch#agent_workflow.steps[].status" in codes(payload)


@pytest.mark.parametrize(
    "checks",
    [[], None, [{"claim": "c", "status": "revised", "evidence": "e"}]],
    ids=["no checks", "no list", "a status outside the closed set"],
)
def test_rule_1_the_critic_status_needs_checks_that_ran(live, checks):
    """Owner, 2026-10-14: `reviewed` is a derivation, but with evidence; without it, a constant that asserts a fact."""

    payload = deepcopy(live)
    review = matchup(payload)["critic_review"]
    if checks is None:
        del review["checks"]
    else:
        review["checks"] = checks

    assert "rule1:constant_asserts_fact#matchups[].critic_review.status" in codes(payload)


def test_rule_1_the_critic_status_is_clean_when_the_checks_ran(live):
    assert "rule1:constant_asserts_fact#matchups[].critic_review.status" not in codes(live)


def test_rule_1_a_team_abbreviation_that_is_a_placeholder_is_found(live):
    payload = deepcopy(live)
    matchup(payload)["teams"]["away"]["abbreviation"] = "???"

    assert "rule1:placeholder#matchups[].teams.*.abbreviation" in codes(payload)


def test_rule_1_a_family_for_a_pitch_the_map_does_not_know_is_invented(live):
    payload = deepcopy(live)
    movement = matchup(payload)["charts"]["pitch_movement"][AWAY]
    movement["Mystery"] = {"h_break": 1.0, "v_break": 2.0, "family": "Fastball"}

    assert "rule1:invented_derivation#matchups[].charts.pitch_movement.*.*.family" in codes(payload)


def test_rule_1_a_family_that_is_not_the_one_of_its_pitch_is_a_mismatch(live):
    payload = deepcopy(live)
    movement = matchup(payload)["charts"]["pitch_movement"][AWAY]
    movement["Slider"]["family"] = "Fastball"

    assert "rule1:derivation_mismatch#matchups[].charts.pitch_movement.*.*.family" in codes(payload)


@pytest.mark.parametrize(
    "field, value",
    [
        ("primary_pitch", "Cutter"),  # not the most thrown
        ("putaway_pitch", "Not available"),  # the second pitch is above 15%
        ("style_label", "Cutter-Slider starter"),
        ("command_label", "Plus command"),
        ("swing_miss_label", "Below-average swing-and-miss ability"),
    ],
)
def test_rule_1_the_profile_is_recomputed_from_the_mix_and_the_sample(live, field, value):
    payload = deepcopy(live)
    matchup(payload, AWAY)["pitching_profile"][field] = value

    assert f"rule1:derivation_mismatch#matchups[].starters.*.pitching_profile.{field}" in codes(payload)


def test_rule_1_a_limited_flag_that_the_sample_does_not_give_is_a_mismatch(live):
    payload = deepcopy(live)
    matchup(payload, AWAY)["sample"]["limited"]["arsenal"] = True  # 1,150 pitches

    assert "rule1:derivation_mismatch#matchups[].starters.*.sample.limited.*" in codes(payload)


def test_rule_1_a_scope_whose_label_is_not_made_of_its_parts_is_a_mismatch(live):
    payload = deepcopy(live)
    matchup(payload, AWAY)["sample"]["arsenal"]["scope"]["label"] = "regular season through never"

    assert "rule1:derivation_mismatch#matchups[].starters.*.sample.arsenal.scope.label" in codes(payload)


def test_rule_1_a_lineup_that_faces_the_wrong_hand_is_a_mismatch(live):
    payload = deepcopy(live)
    matchup(payload)["teams"]["home"]["offense_profile"]["vs_pitcher_hand"] = "RHP"  # the away starter throws left

    assert "rule1:derivation_mismatch#matchups[].teams.*.offense_profile.vs_pitcher_hand" in codes(payload)


def test_rule_1_a_clean_payload_has_no_finding(live):
    assert codes(live) == set()


# --- rule 2: unknown is never zero ---------------------------------------------------------------


def test_rule_2_a_count_of_zero_from_statcast_with_pitches_but_no_batter_has_no_evidence(live):
    """
    F6b: an unusable `events` column used to publish measured zeros. The pipeline no longer produces them
    (`tests/test_statcast_frame_usable.py`), so the payload is the one it used to produce, written by hand:
    the manifest must still refuse it.
    """

    payload = deepcopy(live)
    rates = matchup(payload, "away_starter")["sample"]["rates"]
    rates.update(source="statcast", batters_faced=0, strikeouts=0, walks=0, home_runs=0)

    found = codes(payload)

    assert "rule2:zero_without_evidence#matchups[].starters.*.sample.rates.batters_faced" in found
    assert "rule2:zero_without_evidence#matchups[].starters.*.sample.rates.strikeouts" in found


def test_rule_2_a_zero_the_api_measured_is_a_zero():
    payload = hard_outcome("api_zeros_are_zeros").payload

    assert not [c for c in codes(payload) if c.startswith("rule2:zero_without_evidence#matchups[].starters")]


def test_rule_2_a_zero_that_statcast_counted_around_is_a_zero(live):
    payload = deepcopy(live)
    rates = matchup(payload, AWAY)["sample"]["rates"]
    rates.update(source="statcast", batters_faced=120, strikeouts=0, walks=0, home_runs=0)

    assert not [c for c in codes(payload) if c.startswith("rule2:zero_without_evidence#matchups[].starters")]


def test_rule_2_a_count_for_counts_that_are_unavailable_is_an_unknown_written_as_a_value(live):
    payload = deepcopy(live)
    rates = matchup(payload, AWAY)["sample"]["rates"]
    rates.update(source="unavailable")

    assert "rule2:unknown_written_as_value#matchups[].starters.*.sample.rates.strikeouts" in codes(payload)


@pytest.mark.parametrize("text", ["N/A", "0", ""])
def test_rule_2_an_unknown_written_as_text_in_a_numeric_field_is_found(live, text):
    payload = deepcopy(live)
    matchup(payload, AWAY)["sample"]["rates"]["walks"] = text

    assert "rule2:unknown_written_as_value#matchups[].starters.*.sample.rates.walks" in codes(payload)


@pytest.mark.parametrize("value", [0, 3, "3.10 ERA", 4.5])
def test_rule_2_era_is_text_by_type_and_unknown_is_the_sentinel(live, value):
    payload = deepcopy(live)
    matchup(payload, AWAY)["season_summary"]["era"] = value

    assert codes(payload) & {
        "rule2:unknown_written_as_value#matchups[].starters.*.season_summary.era",
        "rule1:wrong_type#matchups[].starters.*.season_summary.era",
    }


def test_rule_2_the_sentinel_and_a_number_written_as_text_are_clean(live):
    payload = deepcopy(live)
    summary = matchup(payload, AWAY)["season_summary"]
    summary.update(era="N/A", whip="1.05", innings="101.1")

    assert not [c for c in codes(payload) if "season_summary.era" in c or "season_summary.whip" in c]


def test_rule_2_a_share_of_no_pitches_is_unknown_not_zero():
    """
    F20: a starter who threw nothing had a 0% share of each pitch his opponent threw. The pipeline writes
    `null` now (`tests/test_pitch_share_of_no_pitches.py`); the manifest still refuses the zero from any writer.
    """

    payload = deepcopy(hard_outcome("home_debut_away_healthy").payload)
    cells = [row["home_starter"] for row in payload["matchups"][0]["charts"]["pitch_mix"] if row["home_starter"]["total"] == 0]
    assert cells and all(cell["overall"] is None for cell in cells)
    assert "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.overall" not in codes(payload)

    for cell in cells:
        cell["overall"] = 0

    assert "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.overall" in codes(payload)


def test_rule_2_a_share_of_real_pitches_that_is_zero_is_a_zero(live):
    found = [c for c in codes(live) if c.startswith("rule2:zero_without_evidence#matchups[].charts")]

    assert found == []  # the home starter threw 700 pitches, none of them a sinker: 0% is a real zero


def test_rule_2_a_total_of_zero_with_pitches_thrown_has_no_evidence(live):
    payload = deepcopy(live)
    matchup(payload)["charts"]["pitch_mix"][0][AWAY]["total"] = 0

    assert "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.total" in codes(payload)


def test_rule_2_a_pitch_count_of_zero_out_of_nothing_for_a_starter_with_pitches_is_found(live):
    payload = deepcopy(live)
    cell = matchup(payload)["charts"]["pitch_mix"][0][AWAY]
    cell.update(count=0, total=0)

    assert codes(payload) & {
        "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.count",
        "rule2:zero_without_evidence#matchups[].charts.pitch_mix[].*.total",
    }


def test_rule_2_a_velocity_of_zero_is_not_a_measurement(live):
    payload = deepcopy(live)
    matchup(payload)["charts"]["velocity_by_pitch"][0]["away_starter_velocity"] = 0

    assert "rule2:zero_without_evidence#matchups[].charts.velocity_by_pitch[].*" in codes(payload)


def test_rule_2_pitches_of_zero_while_the_mix_has_pitches_has_no_evidence(live):
    payload = deepcopy(live)
    matchup(payload, AWAY)["sample"]["arsenal"]["pitches"] = 0

    assert "rule2:zero_without_evidence#matchups[].starters.*.sample.arsenal.pitches" in codes(payload)


# --- wired into the contract ---------------------------------------------------------------------


def test_the_contract_runs_the_manifest_on_a_live_file_and_only_there(live):
    broken = deepcopy(live)
    broken["matchups"][0]["game"]["weather"] = "sunny"  # a field nobody listed
    assert any(v.code.startswith("rule1:") for v in check_contract(broken))
    demo = deepcopy(broken)
    demo["metadata"]["data_mode"] = "demo_cached"

    assert not any(v.code.startswith(("rule1:", "rule2:")) for v in check_contract(demo))


def test_a_violation_of_rule_1_or_2_that_is_not_in_the_table_fails_publication(live):
    from tests.live_helpers import failed_checks
    with pytest.MonkeyPatch.context() as monkeypatch:
        payload = build(monkeypatch, "live_complete")
        payload["matchups"][0]["game"]["weather"] = "sunny"

        assert any("rule1:unlisted#matchups[].game.weather" in d for d in failed_checks(payload))


def test_the_pitch_family_table_is_the_one_the_pipeline_uses():
    from data_pipeline.fetchers import live_pipeline

    for name in set(live_pipeline.PITCH_NAME_MAP.values()):
        assert name in labels.PITCH_FAMILY, f"{name} has no family: it would be published as an invented one"


def test_rule_1_pitch_data_status_follows_the_starters_it_summarizes(live):
    """F1: `fetched_snapshot` when at least one starter has pitches, `unavailable` when none has."""

    assert "rule1:derivation_mismatch#matchups[].data_confidence.pitch_data_status" not in codes(live)
    assert "rule1:constant_asserts_fact#matchups[].data_confidence.pitch_data_status" not in codes(live)

    both_unpitched = deepcopy(live)
    for slot in ("away_starter", "home_starter"):
        matchup(both_unpitched, slot)["sample"]["arsenal"]["pitches"] = 0
    assert "rule1:derivation_mismatch#matchups[].data_confidence.pitch_data_status" in codes(both_unpitched)

    one_pitched = deepcopy(both_unpitched)
    matchup(one_pitched, "home_starter")["sample"]["arsenal"]["pitches"] = 30
    matchup(one_pitched)["data_confidence"]["pitch_data_status"] = "unavailable"
    assert "rule1:derivation_mismatch#matchups[].data_confidence.pitch_data_status" in codes(one_pitched)
