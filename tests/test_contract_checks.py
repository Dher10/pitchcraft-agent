"""The generic checks of the data contract (P0.15-D3.2): rules 3, 4, 6 and 8.

Each rule has a negative test: a payload that breaks it must be reported with the code of that rule.
The payloads are built by the generator (the corpus) and then broken on purpose, one thing at a time,
so a code appears only because of what the test changed. A code that is also there before the change is
a violation the code has today (`known_violations.py`); the tests look at what the change adds.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pytest

from data_pipeline import claims_registry as registry
from data_pipeline import contract_checks
from data_pipeline.contract_checks import (
    RUN_ERROR_CODES,
    RUN_SOURCES,
    Violation,
    check_contract,
)
from tests.corpus import build, published

AWAY, HOME = "away_starter", "home_starter"


def codes(payload: dict[str, Any]) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


@pytest.fixture
def live(monkeypatch):
    return published(build(monkeypatch, "live_complete"))


@pytest.fixture
def debuts(monkeypatch):
    return published(build(monkeypatch, "live_debuts"))


@pytest.fixture
def demo(monkeypatch):
    return published(build(monkeypatch, "demo"))


def broken(payload: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    """A copy of the payload with `edit(first matchup)` applied."""

    copy = deepcopy(payload)
    edit(copy["matchups"][0])
    return copy


def added(payload: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> set[str]:
    """The codes the edit adds."""

    return codes(broken(payload, edit)) - codes(payload)


def test_a_violation_has_a_code_a_place_and_a_message(live):
    violations = check_contract(live)

    assert violations and all(isinstance(v, Violation) for v in violations)
    assert all(v.code and v.where and v.message for v in violations)


# --- rule 3: scope -------------------------------------------------------------------------------


def starter(m, slot=AWAY):
    return m["starters"][slot]


def test_rule_3_a_healthy_live_matchup_has_no_scope_violation(live):
    assert {c for c in codes(live) if c.startswith("rule3:")} == set()


def test_rule_3_does_not_look_at_a_demo_matchup(demo):
    assert {c for c in codes(demo) if c.startswith("rule3:")} == set()


def test_rule_3_a_measured_zero_has_its_scope(debuts):
    """A debut's 0 pitches come from a valid answer: a measured zero is a figure and has its scope."""

    sample = starter(debuts["matchups"][0])["sample"]
    assert sample["arsenal"]["pitches"] == 0 and sample["arsenal"]["scope"] is not None

    assert {c for c in codes(debuts) if c.startswith("rule3:pitch_data")} == set()


def test_rule_3_a_scope_for_a_pitch_count_that_is_unknown_is_a_scope_without_figures(debuts):
    def unknown(m):
        starter(m)["sample"]["arsenal"]["pitches"] = None

    assert "rule3:pitch_data#scope_without_figures" in added(debuts, unknown)


def test_rule_3_a_group_that_is_unavailable_has_no_scope_in_any_field_that_carries_one(debuts):
    """F17: the counts are unavailable, yet `sample.rates.scope` is set."""

    sample = starter(debuts["matchups"][0])["sample"]
    assert sample["rates"]["source"] == "unavailable" and sample["rates"]["scope"] is not None

    assert "rule3:counts#scope_without_figures" in codes(debuts)


def test_rule_3_the_counts_scope_of_the_summary_is_checked_as_well(live):
    def with_no_counts(m):
        s = starter(m)
        s["sample"]["rates"]["source"] = "unavailable"

    assert "rule3:counts#scope_without_figures" in added(live, with_no_counts)


def test_rule_3_an_offense_scope_with_no_offense_figure_is_found(debuts):
    """F2: both lineups have a scope and not one figure."""

    assert "rule3:offense#scope_without_figures" in codes(debuts)


def test_rule_3_a_figure_with_no_scope_is_found(live):
    def no_offense_scope(m):
        m["teams"]["home"]["offense_profile"]["scope"] = None

    def no_arsenal_scope(m):
        starter(m)["sample"]["arsenal"]["scope"] = None

    def no_rates_scope(m):
        starter(m)["season_summary"]["scopes"]["season_rates"] = None

    def no_counts_scope(m):
        starter(m)["season_summary"]["scopes"]["counts"] = None

    assert "rule3:offense#figures_without_scope" in added(live, no_offense_scope)
    assert "rule3:pitch_data#figures_without_scope" in added(live, no_arsenal_scope)
    assert "rule3:season_rates#figures_without_scope" in added(live, no_rates_scope)
    assert "rule3:counts#figures_without_scope" in added(live, no_counts_scope)


def test_rule_3_a_scope_that_disagrees_with_its_source_is_found(live):
    post = {"kind": "regular_and_postseason", "through": "2026-07-03", "label": "regular season and postseason through 2026-07-03"}

    def offense(m):
        m["teams"]["home"]["offense_profile"]["scope"] = post

    def api_rates(m):
        starter(m)["season_summary"]["scopes"]["season_rates"] = post

    def api_counts(m):
        starter(m)["season_summary"]["scopes"]["counts"] = post
        starter(m)["sample"]["rates"]["scope"] = post

    def statcast_counts(m):
        s = starter(m)
        s["sample"]["rates"]["source"] = "statcast"  # the pitch data is regular season, the counts are not

        s["season_summary"]["scopes"]["counts"] = post
        s["sample"]["rates"]["scope"] = post

    def not_a_scope(m):
        starter(m)["sample"]["arsenal"]["scope"] = {"kind": "whenever"}

    assert "rule3:offense#scope_disagrees_with_source" in added(live, offense)
    assert "rule3:season_rates#scope_disagrees_with_source" in added(live, api_rates)
    assert "rule3:counts#scope_disagrees_with_source" in added(live, api_counts)
    assert "rule3:counts#scope_disagrees_with_source" in added(live, statcast_counts)
    assert "rule3:pitch_data#scope_disagrees_with_source" in added(live, not_a_scope)


def test_rule_3_season_rates_that_are_unavailable_carry_no_scope(live):
    def unavailable(m):
        s = starter(m)
        s["season_summary"].update(era="N/A", whip="N/A", innings="N/A")

    assert "rule3:season_rates#scope_without_figures" in added(live, unavailable)


# --- rule 4: claims ------------------------------------------------------------------------------


def where(payload, code):
    return [v for v in check_contract(payload) if v.code == code]


def test_rule_4_a_claim_whose_condition_holds_is_not_reported(live):
    assert not where(live, "rule4:analyst.have.pitches#count")
    assert not where(live, "rule4:analyst.read.combination#putaway_share")


def test_rule_4_a_key_that_is_in_no_registry_is_reported(live, monkeypatch):
    monkeypatch.setattr(contract_checks, "classify", lambda key: (None, None) if key == "analyst.watch.deep" else registry.classify(key))

    assert "rule4:analyst.watch.deep#unregistered" in codes(live)


def test_rule_4_is_left_to_the_claims_check_when_the_claims_do_not_verify(live):
    payload = deepcopy(live)
    payload["matchups"][0]["report"]["headline"] += " tampered"

    assert {c for c in codes(payload) if c.startswith("rule4:")} == set()


def test_rule_4_a_count_that_is_not_the_data_is_found(live):
    def edit(m):
        starter(m)["sample"]["rates"]["home_runs"] += 1

    assert "rule4:analyst.data.contact#count" in added(live, edit)


def test_rule_4_a_rate_label_the_data_does_not_support_is_found(live):
    def edit(m):
        starter(m)["pitching_profile"]["swing_miss_label"] = "Below-average swing-and-miss ability"

    assert "rule4:analyst.read.shows#label" in added(live, edit)


def test_rule_4_a_put_away_pitch_under_15_percent_is_found(live):
    def edit(m):
        name = starter(m)["pitching_profile"]["putaway_pitch"].lower().replace(" fastball", "")
        for row in m["charts"]["pitch_mix"]:
            if row["pitch"].lower().replace(" fastball", "").replace("-seam", "") == name.replace("-seam", ""):
                row[AWAY]["count"] = 1

    assert "rule4:analyst.read.combination#putaway_share" in added(live, edit)


def test_rule_4_an_offense_sentence_in_the_wrong_band_is_found(live):
    def edit(m):
        for side in ("home", "away"):
            m["teams"][side]["offense_profile"]["ops_vs_hand"] = ".600"

    assert any(c.startswith("rule4:analyst.offense.") and c.endswith("#band") for c in added(live, edit))


def test_rule_4_a_scope_note_for_groups_that_now_differ_is_found(live):
    post = {"kind": "regular_and_postseason", "through": "2026-07-03", "label": "regular season and postseason through 2026-07-03"}

    def edit(m):
        starter(m)["season_summary"]["scopes"]["counts"] = post

    assert "rule4:analyst.scope.same#groups" in added(live, edit)


def test_rule_4_a_strength_that_is_not_the_first_the_labels_support_is_found(live):
    """The away starter's strength line cites his swing-and-miss label; with an average label it should not."""

    def edit(m):
        starter(m)["pitching_profile"]["swing_miss_label"] = "Average swing-and-miss ability"

    assert {"rule4:writer.strength#first", "rule4:analyst.strength.swing_miss#label"} <= added(live, edit)


def test_rule_4_a_limited_note_without_a_limited_sample_is_found(debuts):
    def edit(m):
        for slot in (AWAY, HOME):
            m["starters"][slot]["sample"]["limited"] = {"arsenal": False, "strikeout": False, "control": False}

    assert {"rule4:writer.confidence.limited#no_limit", "rule4:analyst.data.arsenal#not_limited"} <= added(debuts, edit)


def test_rule_4_a_time_claim_for_a_game_that_is_not_known_to_be_a_preview_is_found(demo):
    """Demo `upcoming` is Preview and may say 'Today's Matchup Summary'; the same matchup `Live` may not."""

    first = demo["matchups"][0]
    assert not [v for v in where(demo, "rule4:writer.section.summary#game_state") if first["id"] in v.where]

    def live_now(m):
        m["status"] = "Live"

    assert any(first["id"] in v.where for v in where(broken(demo, live_now), "rule4:writer.section.summary#game_state"))


def test_rule_4_a_live_game_has_no_known_state_so_its_time_claims_fail(live):
    assert "rule4:writer.section.summary#game_state" in codes(live)
    assert "rule4:writer.confidence.live_full#game_state" in codes(live)


def test_rule_4_the_confidence_note_must_have_pitch_data_to_say_so(debuts):
    """F1: a game of two debuts says 'Statcast pitch data'."""

    assert any(c.startswith("rule4:writer.confidence.live_") and c.endswith("#pitch_data") for c in codes(debuts))


def test_rule_4_a_pitch_that_is_under_the_minimum_of_its_role_is_found(live):
    def edit(m):
        name = starter(m)["pitching_profile"]["primary_pitch"].lower().replace(" fastball", "").replace("-seam", "")
        for row in m["charts"]["pitch_mix"]:
            if row["pitch"].lower().replace(" fastball", "").replace("-seam", "") == name:
                row[AWAY]["count"] = 1

    assert "rule4:critic.pitch.supported_primary#minimum" in added(live, edit)


def test_rule_4_a_critic_summary_that_does_not_count_its_warnings_is_found(live):
    def edit(m):
        m["critic_review"]["checks"][0]["status"] = "warning"

    assert "rule4:critic.summary.supported#count" in added(live, edit)


def test_rule_4_a_note_about_betting_language_needs_the_check_to_have_run(live):
    def edit(m):
        for check in m["critic_review"]["checks"]:
            if check["status"] == "not_present":
                check["status"] = "warning"

    assert "rule4:critic.note.focus#check" in added(live, edit)


def test_rule_4_a_critic_check_that_the_critic_does_not_find_again_is_found(live):
    def edit(m):
        for row in m["charts"]["pitch_mix"]:
            row[AWAY]["count"] = 0
            row[AWAY]["overall"] = 0.0

    assert any(c.endswith("#recomputed") for c in added(live, edit))


def test_rule_4_a_stuff_plus_note_has_no_check_behind_it(live):
    assert "rule4:critic.note.stuff_plus#no_check" in codes(live)


def test_rule_4_a_grade_that_is_not_the_box_score_is_found(demo):
    final = next(i for i, m in enumerate(demo["matchups"]) if m["status"] == "final")
    payload = deepcopy(demo)
    payload["matchups"][final]["postgame"]["starter_lines"][AWAY]["game_score"] += 20

    added_codes = codes(payload) - codes(demo)

    assert any(c.startswith("rule4:grader.explanation.") and c.endswith("#figure") for c in added_codes)
    assert any(c.startswith("rule4:grader.explanation.") and c.endswith("#band") for c in added_codes)


def test_rule_4_the_workflow_must_count_what_the_file_counts(demo):
    payload = deepcopy(demo)
    payload["matchups"].pop()  # the claims still say the old number

    assert "rule4:generator.workflow.loaded#count" in codes(payload)


def test_rule_4_the_workflow_of_a_live_file_counts_only_live_matchups(live):
    """F4: the live file counts its demo matchup."""

    assert "rule4:generator.workflow.loaded#count" in codes(live)
    assert "rule4:generator.workflow.loaded#cached" in codes(live)


def test_rule_4_the_label_of_a_live_file_needs_the_time_of_the_fetch(live):
    """F9: `metadata.data_fetched_at` does not exist yet."""

    assert "rule4:generator.metadata.last_updated.live#fetched_at" in codes(live)

    payload = deepcopy(live)
    payload["metadata"]["data_fetched_at"] = "2026-07-04T12:00:00Z"

    assert "rule4:generator.metadata.last_updated.live#fetched_at" not in codes(payload)


def test_rule_4_an_internal_finding_must_not_be_published(live, monkeypatch):
    monkeypatch.setitem(registry.RULES, "analyst.watch.deep", registry._internal)  # any sentence of the file stands in

    assert "rule4:analyst.watch.deep#published" in codes(live)


# --- rule 6: honest mode -------------------------------------------------------------------------


def clean_live(payload: dict[str, Any]) -> dict[str, Any]:
    """A live file with only live content and a time of fetch: what rule 6 asks for."""

    copy = deepcopy(payload)
    copy["matchups"] = [m for m in copy["matchups"] if m["data_confidence"]["level"] == "fetched_snapshot"]
    ids = {m["id"] for m in copy["matchups"]}
    copy["archive"] = [row for row in copy["archive"] if row["id"] in ids]
    copy["metadata"]["data_sources"] = [s for s in copy["metadata"]["data_sources"] if "ached" not in s]
    copy["disclaimers"] = [d for d in copy["disclaimers"] if "ached" not in d]
    copy["metadata"]["data_fetched_at"] = "2026-07-04T12:00:00Z"
    return copy


def rule6(payload):
    return {c for c in codes(payload) if c.startswith("rule6:")}


def test_rule_6_a_live_file_with_demo_content_is_reported(live):
    assert rule6(live) == {
        "rule6:matchup_not_live",
        "rule6:archive_not_live",
        "rule6:cached_wording",
        "rule6:data_fetched_at",
    }


def test_rule_6_a_live_file_with_only_live_content_and_a_fetch_time_is_clean(live):
    assert rule6(clean_live(live)) == set()


@pytest.mark.parametrize("kind", ["demo", "fallback"])
def test_rule_6_asks_nothing_of_a_demo_file(monkeypatch, kind):
    assert rule6(published(build(monkeypatch, kind))) == set()


def test_rule_6_each_demo_leftover_is_reported_alone(live):
    base = clean_live(live)
    demo_matchup = live["matchups"][1]

    with_matchup = deepcopy(base)
    with_matchup["matchups"].append(demo_matchup)
    with_row = deepcopy(base)
    with_row["archive"].append(live["archive"][1])
    with_wording = deepcopy(base)
    with_wording["disclaimers"].append("Cached demo data may be used to ensure stable public evaluation.")
    with_no_time = deepcopy(base)
    del with_no_time["metadata"]["data_fetched_at"]

    assert rule6(with_matchup) == {"rule6:matchup_not_live"}
    assert rule6(with_row) == {"rule6:archive_not_live"}
    assert rule6(with_wording) == {"rule6:cached_wording"}
    assert rule6(with_no_time) == {"rule6:data_fetched_at"}


def test_rule_6_the_time_of_the_fetch_is_a_time(live):
    for bad in ("yesterday", 12, "2026-07-04", "2026-07-04T12:00:00"):
        payload = clean_live(live)
        payload["metadata"]["data_fetched_at"] = bad

        assert rule6(payload) == {"rule6:data_fetched_at"}, bad


# --- rule 8: no internals ------------------------------------------------------------------------


def rule8(payload):
    return {c for c in codes(payload) if c.startswith("rule8:")}


@pytest.fixture
def errored(monkeypatch):
    return published(build(monkeypatch, "live_errors"))


def test_rule_8_a_raw_error_message_in_a_live_file_is_reported(errored):
    assert errored["metadata"]["data_status"]["live_run"]["errors"][0]["message"]

    assert "rule8:error_shape" in rule8(errored)


def test_rule_8_the_reason_of_a_live_file_is_a_source_and_a_code_not_free_text(live):
    assert isinstance(live["metadata"]["data_status"]["reason"], str)

    assert "rule8:reason" in rule8(live)


def test_rule_8_errors_and_a_reason_made_of_a_source_and_a_code_are_clean(errored):
    payload = deepcopy(errored)
    status = payload["metadata"]["data_status"]
    status["reason"] = {"source": "snapshot", "code": "game_rejected"}
    status["live_run"]["errors"] = [{"source": "statcast_pitcher", "code": "malformed_rows"}]
    status["live_run"]["warnings"] = [{"source": "statcast_pitcher", "code": "unmapped_pitch_type"}]

    assert rule8(payload) == set()


def test_rule_8_a_reason_that_is_unavailable_is_clean(errored):
    payload = deepcopy(errored)
    payload["metadata"]["data_status"]["reason"] = None
    payload["metadata"]["data_status"]["live_run"]["errors"] = []

    assert rule8(payload) == set()


@pytest.mark.parametrize(
    "error",
    [
        {"source": "statcast_pitcher", "code": "malformed_rows", "message": "KeyError: 'stand'"},
        {"source": "statcast_pitcher"},
        {"source": "my_laptop", "code": "malformed_rows"},
        {"source": "statcast_pitcher", "code": "KeyError"},
        "KeyError: 'stand'",
    ],
)
def test_rule_8_an_error_is_exactly_a_source_and_a_code_from_the_closed_sets(errored, error):
    payload = deepcopy(errored)
    payload["metadata"]["data_status"]["live_run"]["errors"] = [error]
    payload["metadata"]["data_status"]["reason"] = None

    assert rule8(payload) == {"rule8:error_shape"}


def test_rule_8_a_warning_has_the_same_shape(errored):
    payload = deepcopy(errored)
    status = payload["metadata"]["data_status"]
    status["reason"], status["live_run"]["errors"] = None, []
    status["live_run"]["warnings"] = [{"source": "statcast_pitcher", "code": "unmapped_pitch_type", "pitch": "FA"}]

    assert rule8(payload) == {"rule8:warning_shape"}


def test_rule_8_asks_nothing_of_a_demo_file(monkeypatch):
    payload = published(build(monkeypatch, "fallback"))

    assert rule8(payload) == set()


def test_rule_8_the_closed_sets_are_the_ones_of_the_contract():
    assert RUN_SOURCES == (
        "mlb_schedule",
        "mlb_person",
        "mlb_season_stats",
        "statcast_pitcher",
        "savant_team_batting",
        "snapshot",
    )
    assert RUN_ERROR_CODES == (
        "request_failed",
        "malformed_response",
        "malformed_rows",
        "missing_column",
        "unusable_column",
        "budget_spent",
        "unknown_value",
        "game_rejected",
    )


# --- more conditions that a wrong payload must break ---------------------------------------------


def test_rule_4_the_headline_must_be_made_of_what_the_profiles_say(live):
    def edit(m):
        starter(m)["pitching_profile"]["style_label"] = "Another starter"

    assert "rule4:analyst.label.against#pair" in added(live, edit)


def test_rule_4_a_hand_that_is_not_the_one_he_throws_with_is_found_and_never_guessed(live):
    def switch(m):
        starter(m)["throws"] = "S"

    def other_hand(m):
        starter(m)["throws"] = "R"  # the lineup he faces is split against LHP

    for edit in (switch, other_hand):
        assert any(c.startswith("rule4:analyst.offense.") and c.endswith("#hand") for c in added(live, edit))


def test_rule_4_a_demo_note_in_a_live_matchup_is_found(live):
    def edit(m):
        m["data_confidence"]["level"] = "demo_cached"

    assert any(c.startswith("rule4:writer.confidence.live") and c.endswith("#not_live") for c in added(live, edit))


def test_rule_4_a_final_note_for_a_game_that_is_not_final_is_found(demo):
    first = demo["matchups"][0]
    payload = deepcopy(demo)
    payload["matchups"][0]["status"] = "final"

    assert any(
        v.code.startswith("rule4:scout.demo.") and first["id"] in v.where and v.code.endswith("#status")
        for v in check_contract(payload)
    )


def test_rule_4_the_grade_band_must_follow_the_line(demo):
    final = next(i for i, m in enumerate(demo["matchups"]) if m["status"] == "final")
    payload = deepcopy(demo)
    line = payload["matchups"][final]["postgame"]["starter_lines"][AWAY]
    line["walks"], line["earned_runs"], line["hits_allowed"] = 0, 0, 2  # a clean line; the sentences say walks

    added_codes = codes(payload) - codes(demo)

    assert any(c.startswith("rule4:grader.plan.") and c.endswith("#band") for c in added_codes)
    assert any(c.startswith("rule4:grader.next.") and c.endswith("#band") for c in added_codes)


def test_rule_4_the_watch_line_is_made_of_the_first_question_not_of_a_copy_of_it():
    from data_pipeline.claims import catalogs_of

    payload = {"metadata": {"language": "en", "data_mode": "demo_cached"}}
    catalogs = catalogs_of(payload)
    claims = [
        {"id": "c1", "key": "analyst.watch.question", "args": {"name": "Alpha", "action": {"claim": "c2"}}, "subject": None, "location": "report.sections[4].bullets[0]"},
        {"id": "c2", "key": "analyst.watch.action.ahead", "args": {}, "subject": None, "location": None},
        {"id": "c3", "key": "analyst.watch.action.ahead", "args": {}, "subject": None, "location": None},
        {"id": "c4", "key": "writer.watch_whether", "args": {"name": "Alpha", "action": {"claim": "c3"}}, "subject": None, "location": None},
    ]
    index = registry.ClaimIndex(claims, catalogs)

    fails = registry.run_rule("writer.watch_whether", registry.Ctx(payload, {}, claims[3], index, {}))

    assert [f.reason for f in fails] == ["first_watch"]
    claims[3]["args"]["action"] = {"claim": "c2"}
    assert registry.run_rule("writer.watch_whether", registry.Ctx(payload, {}, claims[3], index, {})) == []
