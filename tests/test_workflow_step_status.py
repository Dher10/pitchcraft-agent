"""Each step of the agent workflow says what it did (P0.15-D2.4d, F19, rule 1).

At HEAD the status of the first four steps was the literal `completed`: no step read its own result, so the file
asserted a fact it never checked. Now `_run_agents` records which matchups each agent finished, `_build_agent_workflow`
writes `completed` only for a step every counted matchup went through (else `pending`), and the manifest recomputes each
status from the payload: the sentences each agent left in `report.claims` (`analyst.*`, `writer.*`, `critic.*`), the
`critic_review`, the confidence packet of the scout. A status the payload does not back up is a derivation mismatch.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline import provenance
from data_pipeline.schema import MATCHUP_REQUIRED_KEYS, WORKFLOW_AGENTS
from tests.corpus import build, published

SCOUT, ANALYST, WRITER, CRITIC, GRADER = WORKFLOW_AGENTS
STATUS = "rule1:derivation_mismatch#agent_workflow.steps[].status"
FACT = "rule1:constant_asserts_fact#agent_workflow.steps[].status"


def codes(payload) -> set[str]:
    return {code for code, _, _ in provenance.findings(payload)}


def status_of(workflow, agent):
    return next(step["status"] for step in workflow["steps"] if step["agent"] == agent)


@pytest.fixture(scope="module")
def live():
    with pytest.MonkeyPatch.context() as monkeypatch:
        return published(build(monkeypatch, "live_complete"))


def keys_removed(matchup, prefix):
    matchup["report"]["claims"] = [c for c in matchup["report"]["claims"] if not c["key"].startswith(prefix)]


# --- the names ---------------------------------------------------------------------------------------------------


def test_the_five_agents_are_named_once():
    assert WORKFLOW_AGENTS == (
        "Data Scout Agent",
        "Matchup Analyst Agent",
        "Report Writer Agent",
        "Critic / Fact-check Agent",
        "Postgame Grader Agent",
    )


# --- the generator: a step is completed by what the agents finished ---------------------------------------------


def done(*ids):
    return list(ids)


def test_every_step_every_matchup_went_through_is_completed():
    run = gdj.AgentRun(0, 0, {SCOUT: done("a", "b"), ANALYST: done("a", "b"), WRITER: done("a", "b"), CRITIC: done("a", "b")})

    workflow = gdj._build_agent_workflow(["a", "b"], run)

    assert [status_of(workflow, agent) for agent in (SCOUT, ANALYST, WRITER, CRITIC)] == ["completed"] * 4
    assert status_of(workflow, GRADER) == "not_applicable"


def test_a_step_a_matchup_did_not_finish_is_pending_and_the_others_are_not_touched():
    run = gdj.AgentRun(0, 0, {SCOUT: done("a", "b"), ANALYST: done("a", "b"), WRITER: done("a", "b"), CRITIC: done("a")})

    workflow = gdj._build_agent_workflow(["a", "b"], run)

    assert status_of(workflow, CRITIC) == "pending"
    assert [status_of(workflow, agent) for agent in (SCOUT, ANALYST, WRITER)] == ["completed"] * 3


def test_a_run_that_finished_nothing_has_every_step_pending():
    workflow = gdj._build_agent_workflow(["a"], gdj.AgentRun(0, 0, {}))

    assert [status_of(workflow, agent) for agent in (SCOUT, ANALYST, WRITER, CRITIC)] == ["pending"] * 4


def test_a_matchup_the_agents_finished_but_the_file_does_not_count_is_not_evidence():
    run = gdj.AgentRun(0, 0, {SCOUT: done("x"), ANALYST: done("a"), WRITER: done("a"), CRITIC: done("a")})

    assert status_of(gdj._build_agent_workflow(["a"], run), SCOUT) == "pending"


def test_the_postgame_step_still_follows_the_starters_it_graded():
    run = gdj.AgentRun(0, 2, {SCOUT: done("a"), ANALYST: done("a"), WRITER: done("a"), CRITIC: done("a")})

    workflow = gdj._build_agent_workflow(["a"], run)

    assert status_of(workflow, GRADER) == "completed"
    assert workflow["steps"][4]["output"] == "Graded 2 completed starter(s) with Bill James Game Score."


@pytest.mark.parametrize("kind", ["demo", "live_complete", "live_debuts"])
def test_the_real_run_records_that_each_agent_finished_each_matchup(monkeypatch, kind):
    payload = build(monkeypatch, kind)
    ids = [m["id"] for m in payload["matchups"]]
    run = gdj._run_agents(deepcopy(payload["matchups"]))

    assert isinstance(run, gdj.AgentRun)
    for agent in (SCOUT, ANALYST, WRITER, CRITIC):
        assert sorted(run.finished[agent]) == sorted(ids), agent
    assert [step["status"] for step in payload["agent_workflow"]["steps"][:4]] == ["completed"] * 4


# --- the manifest: a status the payload does not back up ---------------------------------------------------------


def test_a_generated_live_file_has_no_finding_about_its_steps(live):
    found = codes(live)

    assert STATUS not in found
    assert FACT not in found


@pytest.mark.parametrize(
    "step, edit",
    [
        (0, lambda m: m.pop("data_confidence")),
        (1, lambda m: keys_removed(m, "analyst.")),
        (2, lambda m: keys_removed(m, "writer.")),
        (2, lambda m: m["report"].update(sections=[])),
        (3, lambda m: m.pop("critic_review")),
        (3, lambda m: m["critic_review"].update(checks=[])),
    ],
    ids=["no-scout-packet", "no-analyst-sentence", "no-writer-sentence", "no-sections", "no-critic-review", "no-checks"],
)
def test_a_completed_step_whose_work_is_not_in_the_file_is_a_mismatch(live, step, edit):
    payload = deepcopy(live)
    edit(payload["matchups"][0])
    assert payload["agent_workflow"]["steps"][step]["status"] == "completed"

    assert STATUS in codes(payload)


@pytest.mark.parametrize("step", [0, 1, 2, 3])
def test_a_pending_step_whose_work_is_all_in_the_file_is_a_mismatch(live, step):
    payload = deepcopy(live)
    payload["agent_workflow"]["steps"][step]["status"] = "pending"

    assert STATUS in codes(payload)


def test_a_pending_step_is_right_when_its_work_is_missing(live):
    payload = deepcopy(live)
    payload["matchups"][0].pop("critic_review")
    payload["agent_workflow"]["steps"][3]["status"] = "pending"

    # other findings may be there (the review is gone); the step itself is right
    assert not [w for c, w, _ in provenance.findings(payload) if c == STATUS and w.endswith("steps[3].status")]


@pytest.mark.parametrize(
    "bad, code",
    [
        ("done", STATUS),
        ("", STATUS),
        ("Completed", STATUS),
        (None, "rule1:null_not_declared#agent_workflow.steps[].status"),
        (1, "rule1:wrong_type#agent_workflow.steps[].status"),
    ],
)
def test_a_status_outside_the_vocabulary_is_found_with_its_code(live, bad, code):
    payload = deepcopy(live)
    payload["agent_workflow"]["steps"][0]["status"] = bad

    assert code in codes(payload)


def test_the_limit_the_scout_leaves_no_trace_of_its_own_in_the_file(live):
    """
    Written in contract 6.2: the scout's only evidence is the confidence packet, which the schema requires. So a file
    with the packet is refuted only if the scout is `pending`, and nothing in the file can tell a scout that did not run
    from one that did; the run record (`AgentRun.finished`, tested above) is what backs the scout's `completed`.
    """

    assert "data_confidence" in MATCHUP_REQUIRED_KEYS
    assert STATUS not in codes(live)  # packet present, `completed`: nothing to refute
    payload = deepcopy(live)
    payload["agent_workflow"]["steps"][0]["status"] = "pending"

    assert STATUS in codes(payload)  # the only refutable direction
