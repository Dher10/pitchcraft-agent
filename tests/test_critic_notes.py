"""The notes of the critic say what it verified (P0.15-D2.1c, F8).

"Kept the report focused on matchup fit rather than outcome prediction." and "Avoided claiming official
Stuff+." were written for every report, whatever the critic had checked: the second one has no check behind it
at all. The surviving note is "No betting or outcome-prediction language found.", written only when the
betting-language check ran and found nothing.
"""

from __future__ import annotations

from copy import deepcopy
import inspect

from agents import critic
from agents.language import catalog_for
from data_pipeline import report_facts as facts
from data_pipeline.claims_registry import classify
from data_pipeline.contract_checks import check_contract
from tests.corpus import build, published
from tests.golden_scenarios import agent_outputs, scenarios

NOTE = "No betting or outcome-prediction language found."
RETIRED = ("Avoided claiming official Stuff+.", "Kept the report focused on matchup fit rather than outcome prediction.")


def test_a_report_with_no_betting_language_gets_the_note_that_says_what_was_verified(monkeypatch):
    matchup = scenarios(monkeypatch)["live_healthy"]

    review = critic.run(agent_outputs(matchup)["report"], matchup)

    betting = next(check for check in review["checks"] if check["claim"] == catalog_for("en")("critic.betting.claim"))
    assert betting["status"] == "not_present"
    assert review["revision_notes"][-1] == NOTE
    assert review["revision_notes"].count(NOTE) == 1


def test_the_note_about_stuff_plus_is_gone_because_no_check_stands_behind_it(monkeypatch):
    for name, matchup in scenarios(monkeypatch).items():
        notes = critic.run(agent_outputs(matchup)["report"], matchup)["revision_notes"]
        assert not any("Stuff+" in note for note in notes), name
        assert not any(note in RETIRED for note in notes), name


def test_the_note_is_not_written_when_the_betting_check_found_language(monkeypatch):
    matchup = scenarios(monkeypatch)["live_healthy"]
    report = deepcopy(agent_outputs(matchup)["report"])
    report["headline"] = "A lock for the home side"

    review = critic.run(report, matchup)

    flagged = next(c for c in review["checks"] if c["status"] == "unsupported")
    assert flagged["claim"] == catalog_for("en")("critic.betting.claim")
    assert NOTE not in review["revision_notes"]


def test_the_note_follows_the_check_not_the_other_way_round(monkeypatch):
    """If the betting check says anything but not_present there is no note."""

    matchup = scenarios(monkeypatch)["live_healthy"]
    monkeypatch.setattr(
        critic,
        "_language_scan",
        lambda t, report: {"claim": t("critic.betting.claim"), "status": "warning", "evidence": "x"},
    )

    assert NOTE not in critic.run(agent_outputs(matchup)["report"], matchup)["revision_notes"]


def test_the_catalog_and_the_registry_have_the_new_key_and_not_the_retired_ones():
    assert catalog_for("en").render("critic.note.no_betting", {}) == NOTE
    assert classify("critic.note.no_betting")[0] == "rule"
    for retired in ("critic.note.focus", "critic.note.stuff_plus"):
        assert classify(retired) == (None, None), retired


# --- the notes are the critic's output, never its input ----------------------------------------------------


def test_the_revision_notes_are_never_part_of_the_text_the_critic_and_report_facts_read(monkeypatch):
    """
    The note names betting ("bet" is one of the terms the scan looks for), so it must not be possible for it
    to reach the scan: the readers take the report only (headline, summary lines, sections), whatever else
    sits next to it in the matchup or the report dict.
    """

    payload = published(build(monkeypatch, "live_complete"))
    t = catalog_for("en")
    for matchup in payload["matchups"]:
        notes = matchup["critic_review"]["revision_notes"]
        report = matchup["report"]
        bare = {key: report[key] for key in ("headline", "short_summary", "sections")}
        # the note sits in the report dict, in the matchup the critic is given, under any key a careless reader might take
        carrying = {**bare, "revision_notes": notes, "critic_review": matchup["critic_review"], "claims": report["claims"]}

        assert facts.report_locations(carrying) == facts.report_locations(bare)
        assert critic._report_locations(carrying) == critic._report_locations(bare)
        assert facts.betting_terms(carrying, t) == [] and facts.betting_terms(bare, t) == []
        assert not any(note in facts.report_text(carrying) for note in notes if note)

        without_review = {key: value for key, value in matchup.items() if key not in ("critic_review", "report")}
        assert critic.run(bare, matchup)["checks"] == critic.run(bare, without_review)["checks"]
        assert facts.owned_sentences(matchup, carrying) == facts.owned_sentences(without_review, bare)

    note_text = [note for m in payload["matchups"] for note in m["critic_review"]["revision_notes"]]
    assert NOTE in note_text, "the control: the payload does carry the note that names betting"
    assert not [v for v in check_contract(payload) if v.code.startswith("rule4:critic.betting")]


def test_report_facts_does_not_read_the_review_at_all():
    """A reader of the text that mentions the notes or the review could not be trusted not to scan them."""

    for module in (facts,):
        source = inspect.getsource(module)
        assert "revision_notes" not in source and "critic_review" not in source, module.__name__

    scan = inspect.getsource(critic._language_scan) + inspect.getsource(critic._report_locations)
    assert "revision_notes" not in scan and "critic_review" not in scan
