"""Every sentence of the published file is recorded with what it is made of (P0.15-D3.1, contract rule 4).

`attach_claims` walks the text fields of a payload, turns each phrase into a claim (`id`, catalog
`key`, `args`, `subject`, `location`) and leaves plain strings in the file. `verify_claims` is what
`validate_payload` runs on the published JSON: it renders every claim again and compares it with the
text in the file, so the text of a report is exactly its registered phrases and nothing else.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from agents.language import catalog_for
from data_pipeline.claims import (
    MATCHUP_TEXT_PATHS,
    ROOT_TEXT_PATHS,
    UnregisteredTextError,
    attach_claims,
    text_leaves,
    verify_claims,
)
from data_pipeline.generator_texts import generator_catalog

t = catalog_for("en")
g = generator_catalog()


def tiny_payload() -> dict:
    """A payload with one matchup whose every text field is a phrase."""

    evidence = t("critic.names.supported")
    with t.subject("away_starter"):
        strength = t("writer.strength_none", name="Alpha Livearm")
        body = t.join(" ", [t("analyst.read.he"), t("writer.arsenal.no_contrast")])
    matchup = {
        "id": "matchup_001",
        "report": {
            "headline": t("analyst.label.against", away="Sinker starter", home="Four-seam starter"),
            "short_summary": [strength],
            "sections": [
                {"title": t("writer.section.arsenal"), "body": body},
                {"title": t("writer.section.watch"), "bullets": [t("analyst.watch.deep")]},
            ],
        },
        "critic_review": {
            "status": "reviewed",
            "summary": t("critic.summary.supported", checked=1),
            "checks": [{"claim": t("critic.names.claim"), "status": "supported", "evidence": evidence}],
            "revision_notes": [evidence],
        },
        "data_confidence": {
            "level": "fetched_snapshot",
            "notes": [g("generator.confidence.live_note", date="2026-07-04", matchup_id="matchup_001")],
        },
        "postgame": None,
    }
    return {
        "metadata": {"data_mode": "fetched_snapshot", "last_updated_label": g(
            "generator.metadata.last_updated.live", date="2026-07-04"
        )},
        "matchups": [matchup],
        "agent_workflow": {
            "description": g("generator.workflow.description"),
            "steps": [{"agent": "Data Scout Agent", "status": "completed", "output": g("generator.workflow.generated")}],
        },
    }


def attached() -> dict:
    payload = tiny_payload()
    attach_claims(payload)
    return payload


def published() -> dict:
    """The payload as the file holds it: after attaching and a trip through JSON."""

    return json.loads(json.dumps(attached()))


def claims_of(payload: dict) -> list[dict]:
    return payload["matchups"][0]["report"]["claims"]


def at(claims: list[dict], location: str) -> list[dict]:
    return [claim for claim in claims if claim["location"] == location]


# --- attaching -----------------------------------------------------------------------------------


def test_each_text_field_gets_a_claim_with_its_key_and_arguments():
    payload = attached()

    [headline] = at(claims_of(payload), "report.headline")

    assert headline["key"] == "analyst.label.against"
    assert headline["args"] == {"away": "Sinker starter", "home": "Four-seam starter"}
    assert headline["subject"] is None
    assert isinstance(headline["id"], str) and headline["id"]


def test_a_join_is_a_claim_whose_parts_are_claims():
    claims = claims_of(attached())
    by_id = {claim["id"]: claim for claim in claims}

    [body] = at(claims, "report.sections[0].body")

    assert body["key"] == "@join" and body["args"]["sep"] == " "
    parts = [by_id[ref["claim"]] for ref in body["args"]["parts"]]
    assert [part["key"] for part in parts] == ["analyst.read.he", "writer.arsenal.no_contrast"]
    assert all(part["location"] is None for part in parts)  # a part has no field of its own


def test_the_subject_of_a_sentence_is_recorded():
    claims = claims_of(attached())

    [strength] = at(claims, "report.short_summary[0]")
    [body] = at(claims, "report.sections[0].body")

    assert strength["subject"] == "away_starter" and body["subject"] == "away_starter"


def test_text_that_is_in_two_fields_has_a_claim_in_each():
    claims = claims_of(attached())

    in_checks = at(claims, "critic_review.checks[0].evidence")
    in_notes = at(claims, "critic_review.revision_notes[0]")

    assert len(in_checks) == len(in_notes) == 1
    assert in_checks[0]["key"] == in_notes[0]["key"] == "critic.names.supported"
    assert in_checks[0]["id"] != in_notes[0]["id"]


def test_the_phrases_of_the_generator_are_in_the_claims_of_the_root():
    payload = attached()

    root = payload["claims"]

    assert {claim["location"] for claim in root} == {
        "metadata.last_updated_label",
        "agent_workflow.description",
        "agent_workflow.steps[0].output",
    }
    [label] = at(root, "metadata.last_updated_label")
    assert (label["key"], label["args"]) == ("generator.metadata.last_updated.live", {"date": "2026-07-04"})
    assert not any(claim["location"] and claim["location"].startswith("report.") for claim in root)


def test_the_language_of_the_file_is_recorded():
    assert attached()["metadata"]["language"] == "en"


def test_after_attaching_the_text_is_plain_strings():
    payload = attached()
    matchup = payload["matchups"][0]

    assert type(matchup["report"]["headline"]) is str
    assert type(matchup["report"]["sections"][0]["body"]) is str
    assert type(matchup["critic_review"]["checks"][0]["evidence"]) is str
    assert type(payload["metadata"]["last_updated_label"]) is str
    assert type(payload["agent_workflow"]["steps"][0]["output"]) is str


def test_every_text_field_of_the_payload_has_a_claim():
    payload = attached()
    matchup = payload["matchups"][0]

    leaves = {path for path, _ in text_leaves(matchup, MATCHUP_TEXT_PATHS)}
    root_leaves = {path for path, _ in text_leaves(payload, ROOT_TEXT_PATHS)}

    assert leaves == {claim["location"] for claim in claims_of(payload) if claim["location"]}
    assert root_leaves == {claim["location"] for claim in payload["claims"] if claim["location"]}
    assert "report.sections[1].bullets[0]" in leaves and "data_confidence.notes[0]" in leaves


def test_a_plain_string_where_text_is_expected_is_refused_with_its_location():
    payload = tiny_payload()
    payload["matchups"][0]["report"]["short_summary"][0] = "Alpha Livearm has no claimed strength."

    with pytest.raises(UnregisteredTextError, match=r"report\.short_summary\[0\]"):
        attach_claims(payload)


def test_a_phrase_that_lost_its_identity_by_editing_is_refused():
    payload = tiny_payload()
    headline = payload["matchups"][0]["report"]["headline"]
    payload["matchups"][0]["report"]["headline"] = headline.rstrip(".")

    with pytest.raises(UnregisteredTextError, match=r"report\.headline"):
        attach_claims(payload)


def test_an_argument_that_is_not_a_payload_value_is_refused():
    payload = tiny_payload()
    payload["matchups"][0]["report"]["headline"] = t("analyst.label.against", away=object(), home="B")

    with pytest.raises(TypeError, match="away"):
        attach_claims(payload)


def test_a_payload_with_no_text_fields_has_empty_claim_lists():
    payload = {"metadata": {}, "matchups": [{"report": {}, "postgame": None}]}

    attach_claims(payload)

    assert payload["claims"] == [] and payload["matchups"][0]["report"]["claims"] == []


# --- verifying -----------------------------------------------------------------------------------


def test_an_attached_payload_verifies():
    assert verify_claims(published()) == []


def test_text_edited_after_the_claims_were_made_is_found():
    payload = published()
    payload["matchups"][0]["report"]["sections"][0]["body"] += " Extra."

    problems = verify_claims(payload)

    assert any("report.sections[0].body" in problem for problem in problems), problems


def test_a_sentence_swapped_for_another_one_is_found():
    payload = published()
    payload["matchups"][0]["report"]["short_summary"][0] = "Alpha Livearm is a lock to dominate."

    assert any("report.short_summary[0]" in problem for problem in verify_claims(payload))


def test_an_argument_changed_in_the_claim_is_found():
    payload = published()
    [headline] = at(claims_of(payload), "report.headline")
    headline["args"]["away"] = "Slider starter"

    assert any("report.headline" in problem for problem in verify_claims(payload))


def test_a_text_field_without_a_claim_is_found():
    payload = published()
    claims = claims_of(payload)
    claims.remove(at(claims, "report.headline")[0])

    assert any("report.headline" in problem and "no claim" in problem for problem in verify_claims(payload))


def test_a_claim_for_a_field_that_does_not_exist_is_found():
    payload = published()
    claims_of(payload).append(
        {"id": "extra", "key": "analyst.watch.deep", "args": {}, "subject": None, "location": "report.sections[9].body"}
    )

    assert any("report.sections[9].body" in problem for problem in verify_claims(payload))


def test_a_part_that_nothing_uses_is_found():
    payload = published()
    claims_of(payload).append(
        {"id": "orphan", "key": "analyst.watch.deep", "args": {}, "subject": None, "location": None}
    )

    assert any("orphan" in problem for problem in verify_claims(payload))


def test_a_key_that_is_not_in_any_catalog_is_found():
    payload = published()
    [headline] = at(claims_of(payload), "report.headline")
    headline["key"] = "analyst.no_such_message"

    assert any("analyst.no_such_message" in problem for problem in verify_claims(payload))


def test_a_reference_to_a_claim_that_does_not_exist_is_found():
    payload = published()
    [body] = at(claims_of(payload), "report.sections[0].body")
    body["args"]["parts"][0] = {"claim": "missing"}

    assert any("missing" in problem for problem in verify_claims(payload))


def test_a_claim_that_refers_to_itself_is_found_and_does_not_loop():
    payload = published()
    [body] = at(claims_of(payload), "report.sections[0].body")
    body["args"]["parts"][0] = {"claim": body["id"]}

    assert verify_claims(payload)


def test_two_claims_with_one_id_are_found():
    payload = published()
    claims = claims_of(payload)
    claims[1]["id"] = claims[0]["id"]

    assert any("duplicate" in problem for problem in verify_claims(payload))


def test_a_language_without_a_catalog_is_found():
    payload = published()
    payload["metadata"]["language"] = "xx"

    assert any("language" in problem for problem in verify_claims(payload))


def test_a_payload_without_its_claim_lists_is_found():
    payload = published()
    del payload["matchups"][0]["report"]["claims"]
    del payload["claims"]

    problems = verify_claims(payload)

    assert any("report.claims" in problem for problem in problems)
    assert any("claims" in problem and "root" in problem for problem in problems)


def test_the_root_claims_are_verified_too():
    payload = published()
    payload["agent_workflow"]["steps"][0]["output"] = "Checked every claim against the data."

    assert any("agent_workflow.steps[0].output" in problem for problem in verify_claims(payload))


def test_claims_do_not_change_the_text_of_the_agents():
    # The claims record the text; they never rewrite it.
    payload = tiny_payload()
    before = deepcopy(json.loads(json.dumps(payload)))

    attach_claims(payload)
    after = json.loads(json.dumps(payload))
    for document in (before, after):
        document["matchups"][0]["report"].pop("claims", None)
        document.pop("claims", None)
        document["metadata"].pop("language", None)

    assert after == before
