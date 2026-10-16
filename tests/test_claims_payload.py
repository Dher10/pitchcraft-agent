"""The published payload records every sentence it contains (P0.15-D3.1, contract rule 4).

The same checks run over four real payloads (demo, demo after a failed live run, a live game with
everything the pipeline can give, a live game of two debuts), over the eighteen golden scenarios of
the agents, and over the file the app serves. The text of the agents does not change; what changes
is that every sentence is registered with the key and arguments it was made from.
"""

from __future__ import annotations

import json

import pytest

from data_pipeline.schema import SCHEMA_VERSION
from tests.corpus import GOLDEN_NAMES, KINDS, SERVED, build, golden_payload, published
from tests.live_helpers import GAME_DAY, failed_checks

LABEL_KEY = {
    "demo": "generator.metadata.last_updated.demo",
    "fallback": "generator.metadata.last_updated.fallback",
    "live_complete": "generator.metadata.last_updated.live",
    "live_debuts": "generator.metadata.last_updated.live",
    "live_errors": "generator.metadata.last_updated.live",
}


@pytest.fixture(params=KINDS)
def built(request, monkeypatch):
    return request.param, build(monkeypatch, request.param)


def at(claims: list[dict], location: str) -> list[dict]:
    return [claim for claim in claims if claim["location"] == location]


def descendants(claim: dict, by_id: dict[str, dict]):
    """The claim and every claim it is made of."""

    yield claim
    args = claim["args"]
    refs = [args[name] for name in args if isinstance(args[name], dict) and "claim" in args[name]]
    refs += [part for part in args.get("parts", []) if isinstance(part, dict) and "claim" in part]
    for ref in refs:
        yield from descendants(by_id[ref["claim"]], by_id)


# --- the schema ----------------------------------------------------------------------------------


def test_the_schema_version_is_0_4_0():
    assert SCHEMA_VERSION == "0.6.0"


def test_every_payload_says_its_version_and_language(built):
    _, payload = built

    assert payload["metadata"]["version"] == SCHEMA_VERSION
    assert payload["metadata"]["language"] == "en"


def test_every_payload_has_claims_for_each_matchup_and_for_the_root(built):
    _, payload = built

    assert payload["claims"], "the generator's own sentences have no claims"
    for matchup in payload["matchups"]:
        assert matchup["report"]["claims"], matchup["id"]


def test_the_claims_of_every_payload_verify(built):
    from data_pipeline.claims import verify_claims

    _, payload = built

    assert verify_claims(published(payload)) == []


def test_every_payload_passes_the_validator(built):
    _, payload = built

    assert failed_checks(payload) == []


def test_the_text_in_the_payload_is_plain_strings(built):
    _, payload = built
    matchup = payload["matchups"][0]

    for text in (
        matchup["report"]["headline"],
        matchup["critic_review"]["summary"],
        payload["metadata"]["last_updated_label"],
        payload["agent_workflow"]["steps"][0]["output"],
    ):
        assert type(text) is str


# --- what the generator says ---------------------------------------------------------------------


def test_the_label_of_the_data_is_a_claim_of_the_root(built):
    kind, payload = built

    [label] = at(payload["claims"], "metadata.last_updated_label")

    assert label["key"] == LABEL_KEY[kind]
    if kind.startswith("live"):
        assert label["args"] == {"date": GAME_DAY}
        assert payload["metadata"]["last_updated_label"] == f"Live data fetched {GAME_DAY}"
    else:
        assert label["args"] == {}


def test_the_workflow_is_claims_of_the_root_with_the_numbers_of_the_file(built):
    _, payload = built
    root = payload["claims"]
    matchups = payload["matchups"]
    warnings = sum(
        1 for matchup in matchups for check in matchup["critic_review"]["checks"] if check["status"] == "warning"
    )
    graded = sum(len(m["postgame"]["starter_lines"]) for m in matchups if m.get("postgame"))

    [loaded] = at(root, "agent_workflow.steps[0].output")
    [checked] = at(root, "agent_workflow.steps[3].output")
    [last] = at(root, "agent_workflow.steps[4].output")

    assert (loaded["key"], loaded["args"]) == ("generator.workflow.loaded", {"count": len(matchups)})
    assert (checked["key"], checked["args"]) == ("generator.workflow.checked", {"warnings": warnings})
    assert last["key"] == ("generator.workflow.graded" if graded else "generator.workflow.graded_none")
    assert last["args"] == ({"count": graded} if graded else {})
    assert [claim["key"] for claim in (at(root, "agent_workflow.steps[1].output") + at(root, "agent_workflow.steps[2].output"))] == [
        "generator.workflow.identified",
        "generator.workflow.generated",
    ]
    assert at(root, "agent_workflow.description")[0]["key"] == "generator.workflow.description"


def test_the_text_of_the_generator_is_the_one_it_always_wrote(built):
    _, payload = built
    steps = [step["output"] for step in payload["agent_workflow"]["steps"]]
    count = len(payload["matchups"])

    assert steps[0] == f"Loaded cached data for {count} matchups."
    assert steps[1] == "Identified pitcher strengths, risks, and lineup pressure points."
    assert steps[2] == "Generated fan-friendly scouting report."
    assert steps[3].startswith("Checked every claim against the data: none unsupported, ")
    assert payload["agent_workflow"]["description"] == (
        "PitchCraft uses a multi-agent workflow to convert matchup data into a fan-facing scouting report."
    )


def test_a_live_matchup_says_when_its_snapshot_was_fetched_through_a_claim(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    live = payload["matchups"][0]

    [note] = at(live["report"]["claims"], "data_confidence.notes[0]")

    assert note["key"] == "generator.confidence.live_note"
    assert note["args"] == {"date": GAME_DAY, "matchup_id": "matchup_001"}
    assert live["data_confidence"]["notes"] == [f"Live snapshot fetched {GAME_DAY} for matchup_001."]


# --- what the agents say -------------------------------------------------------------------------


def test_every_text_field_of_every_matchup_has_a_claim(built):
    from data_pipeline.claims import MATCHUP_TEXT_PATHS, ROOT_TEXT_PATHS, text_leaves

    _, payload = built

    for matchup in payload["matchups"]:
        leaves = {path for path, _ in text_leaves(matchup, MATCHUP_TEXT_PATHS)}
        located = {claim["location"] for claim in matchup["report"]["claims"] if claim["location"]}
        assert leaves == located, matchup["id"]
        assert "report.headline" in leaves and "critic_review.summary" in leaves
    root_leaves = {path for path, _ in text_leaves(payload, ROOT_TEXT_PATHS)}
    assert root_leaves == {claim["location"] for claim in payload["claims"] if claim["location"]}


def test_a_final_demo_matchup_has_claims_for_its_postgame_text(monkeypatch):
    payload = build(monkeypatch, "demo")
    final = next(m for m in payload["matchups"] if m["status"] == "final")
    locations = {claim["location"] for claim in final["report"]["claims"]}

    for slot in ("away_starter", "home_starter"):
        for field in ("grade_explanation", "plan_vs_execution", "what_to_watch_next"):
            assert f"postgame.starter_lines.{slot}.{field}" in locations
    assert "postgame.call_check[0].pregame_note" in locations
    assert "postgame.call_check[2].postgame_evidence" in locations


def test_the_strength_line_of_each_starter_names_its_subject(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    claims = payload["matchups"][0]["report"]["claims"]

    [away] = at(claims, "report.short_summary[0]")
    [home] = at(claims, "report.short_summary[1]")

    assert (away["key"], away["subject"]) == ("writer.strength", "away_starter")
    assert (home["key"], home["subject"]) == ("writer.strength", "home_starter")


@pytest.mark.parametrize("section, slot", [(1, "away_starter"), (2, "home_starter")])
def test_what_is_said_about_a_starter_in_his_section_has_him_as_subject(monkeypatch, section, slot):
    payload = build(monkeypatch, "live_complete")
    claims = payload["matchups"][0]["report"]["claims"]
    by_id = {claim["id"]: claim for claim in claims}

    [body] = at(claims, f"report.sections[{section}].body")
    about_him = [
        part
        for part in descendants(body, by_id)
        if part["key"].startswith(("analyst.read.", "analyst.offense.", "analyst.data."))
    ]

    assert about_him, "the section says nothing about the starter"
    assert {part["subject"] for part in about_him} == {slot}


def test_each_check_of_the_critic_names_the_starter_it_is_about(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    matchup = payload["matchups"][0]
    claims = matchup["report"]["claims"]
    names = {slot: matchup["starters"][slot]["name"] for slot in ("away_starter", "home_starter")}
    seen = 0

    for index, _ in enumerate(matchup["critic_review"]["checks"]):
        [claim] = at(claims, f"critic_review.checks[{index}].claim")
        if claim["key"] in ("critic.pitch.claim", "critic.limited.claim"):
            seen += 1
            assert claim["subject"] in names
            assert names[claim["subject"]] == claim["args"]["name"]

    assert seen, "the critic made no claim about a starter"


def test_a_sentence_made_of_other_sentences_keeps_them_as_claims(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    claims = payload["matchups"][0]["report"]["claims"]
    by_id = {claim["id"]: claim for claim in claims}

    [confidence] = at(claims, "report.sections[5].body")

    assert confidence["key"] == "@join"
    keys = {part["key"] for part in descendants(confidence, by_id)}
    assert {"writer.confidence.snapshot", "writer.confidence.item.offense", "writer.confidence.lineups"} <= keys


def test_a_numbered_noun_inside_a_sentence_is_a_claim_with_its_count(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    claims = payload["matchups"][0]["report"]["claims"]

    contact = [claim for claim in claims if claim["key"] == "analyst.data.contact"]
    assert contact, "no contact-risk sentence in the live report"
    by_id = {claim["id"]: claim for claim in claims}
    home_runs = by_id[contact[0]["args"]["home_runs"]["claim"]]

    assert home_runs["key"].startswith("count.home_run.")
    assert home_runs["args"]["count"] >= 0


def test_every_argument_of_a_claim_is_json(built):
    _, payload = built
    allowed = (str, int, float, bool, type(None))

    def check(value):
        if isinstance(value, dict):  # a reference to another claim: {"claim": id}
            assert set(value) == {"claim"}, value
            check(value["claim"])
        elif isinstance(value, list):
            for child in value:
                check(child)
        else:
            assert isinstance(value, allowed), value

    for claim in payload["claims"] + [c for m in payload["matchups"] for c in m["report"]["claims"]]:
        assert isinstance(claim["args"], dict)
        for argument in claim["args"].values():
            check(argument)
        assert set(claim) == {"id", "key", "args", "subject", "location"}
        assert claim["subject"] in (None, "away_starter", "home_starter")


# --- the validator -------------------------------------------------------------------------------


def test_the_validator_refuses_a_sentence_edited_after_the_claims(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    payload["matchups"][0]["report"]["sections"][1]["body"] += " He is a lock."

    failed = failed_checks(payload)

    assert any(description.startswith("claims") for description in failed), failed


def test_the_validator_refuses_a_payload_without_claims(monkeypatch):
    payload = build(monkeypatch, "demo")
    del payload["claims"]

    failed = failed_checks(payload)

    assert any("claims" in description for description in failed), failed


# --- the golden scenarios ------------------------------------------------------------------------


@pytest.mark.parametrize("name", GOLDEN_NAMES)
def test_every_golden_scenario_registers_all_of_its_text(monkeypatch, name):
    from agents.language import catalog_for
    from data_pipeline.claims import verify_claims

    payload = golden_payload(monkeypatch, name)
    assert catalog_for("en")  # the language the scenarios are written in

    assert verify_claims(published(payload)) == []


# --- the file the app serves ---------------------------------------------------------------------


def test_the_served_file_has_its_claims_and_they_verify():
    from data_pipeline.claims import verify_claims

    served = json.loads(SERVED.read_text(encoding="utf-8"))

    assert served["metadata"]["version"] == SCHEMA_VERSION
    assert served["metadata"]["language"] == "en"
    assert served["claims"]
    assert verify_claims(served) == []
