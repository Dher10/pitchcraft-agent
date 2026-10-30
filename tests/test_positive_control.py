"""P2.2 positive control: a hand-written ideal report for one DEV case must pass every offline code check.

If it ever fails, the harness is wrong, not the text (owner instruction). The local NLI is not part of this test: its weights, its
runtime and the sentence-versus-fact adapter do not exist yet (P2.3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents import llm_report_writer as lw
from agents import writer_checks as wc
from agents import writer_input as wi
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"
CONTROL = Path(__file__).resolve().parents[1] / "evals" / "data" / "writer" / "positive_control.json"


def load():
    data = json.loads(CONTROL.read_text(encoding="utf-8"))
    case = data["case_id"]
    doc = wi.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), wi.load_glossary(DATASET / "glossary.json"))
    index = wi.evidence_index(doc)

    def sentence(item):
        return {"text": item["text"], "evidence": [{"path": p, "value": "null" if index[p] is None else str(index[p])} for p in item["paths"]]}

    raw = data["candidate"]
    candidate = {"headline": sentence(raw["headline"]), "summary_lines": [sentence(s) for s in raw["summary_lines"]],
                 "sections": {key: [sentence(s) for s in items] for key, items in raw["sections"].items()}}
    return case, doc, candidate


def test_the_control_is_a_dev_case():
    case, _, _ = load()

    assert case in bp.dev_case_ids(DATASET)


def test_the_ideal_report_passes_every_code_check_and_its_length_is_inside_the_rules_band():
    case, doc, candidate = load()
    rules = lw.rules_report_for(bp.load_dev_packet(DATASET, case))
    rules_len = wc.rules_length(rules)

    assert wc.check_report_detailed(candidate, doc, rules_len) == []
    assert 0.8 * rules_len <= wc.report_length(candidate) <= 1.2 * rules_len


def test_the_ideal_report_uses_each_short_form_once_and_no_definition_and_no_repeated_scope():
    _, _, candidate = load()
    text = " ".join(s["text"] for s in wc._all_sentences(candidate))

    for short in ("(earned run average)", "(walks plus hits per inning)", "(on-base plus slugging)", "(strikeout rate)", "(walk rate)"):
        assert text.count(short) == 1, short
    assert text.count("2026 regular season through May 31") == 3  # once in each of three sections


def test_the_ideal_report_reads_as_prose_not_as_a_list_of_facts():
    _, _, candidate = load()
    openers = [s["text"].split()[0] for s in wc._all_sentences(candidate)]

    assert max(openers.count(w) for w in set(openers)) <= 4  # no word opens more than four sentences
    assert not any(len(s["text"]) > 160 for s in wc._all_sentences(candidate))


def test_each_wording_rule_still_fails_on_a_spoiled_copy_of_the_ideal_report():
    _, doc, candidate = load()
    rules_len = wc.report_length(candidate)

    spoiled = json.loads(json.dumps(candidate))
    spoiled["sections"]["away_vs_home"][0]["text"] = "Kyle Freeland carries an 8.08 ERA over the 2026 regular season through May 31."
    assert "W11.expansion" in wc.check_report(spoiled, doc, rules_len)

    spoiled = json.loads(json.dumps(candidate))
    spoiled["sections"]["home_vs_away"][1]["text"] = "He shows above-average swing-and-miss ability and below-average command over the 2026 regular season through May 31."
    spoiled["sections"]["home_vs_away"][1]["evidence"].append(spoiled["sections"]["home_vs_away"][0]["evidence"][-1])
    assert "W12.repeat" in wc.check_report(spoiled, doc, rules_len)


@pytest.mark.parametrize("text", ["Kyle Freeland is great.", "Kyle Freeland will win."])
def test_the_checks_do_not_pass_everything(text):
    _, doc, candidate = load()
    candidate["sections"]["arsenal"][0]["text"] = text

    assert wc.check_report(candidate, doc, wc.report_length(candidate))


def test_pair_six_of_the_guide_is_the_ideal_reports_away_starter_section():
    guide = (Path(__file__).resolve().parents[1] / "docs" / "writer-guide.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    _, _, candidate = load()
    paragraph = " ".join(s["text"] for s in candidate["sections"]["away_vs_home"])

    assert paragraph in guide
