"""P2.2: the offline B1 runner on dev cases, with a fake provider. No key, no network."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from agents import call_budget as cb
from agents import writer_checks, writer_input
from evals import build_packets as bp
from evals import run_b1

sys.path.insert(0, str(Path(__file__).parent))
import test_llm_report_writer as tlw  # noqa: E402

DATASET = run_b1.DATASET


def test_the_ten_examples_are_dev_cases_three_three_two_two_in_the_split_order():
    chosen = run_b1.pick_cases()
    sealed = {c["id"]: c["split"] for c in json.loads((DATASET / "split.json").read_text(encoding="utf-8"))["cases"]}

    assert len(chosen) == 10 and all(sealed[c] == "dev" for c in chosen)
    assert [c.split("-")[0] for c in chosen].count("veteran") == 3 and [c.split("-")[0] for c in chosen].count("postseason") == 2
    assert chosen == [c for c in bp.dev_case_ids(DATASET) if c in chosen]


def test_the_runner_opens_no_test_split_file():
    source = Path(run_b1.__file__).read_text(encoding="utf-8")

    assert "split/test" not in source and "/test/" not in source and "load_dev_packet" in source


def test_an_item_is_saved_and_a_resumed_run_repeats_no_call(tmp_path, monkeypatch):
    case = "veteran-824027"
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    doc = writer_input.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
    control = tlw.twc.candidate(doc)
    monkeypatch.setattr(writer_checks, "rules_length", lambda report: writer_checks.report_length(control))
    fake = tlw.Fake(tlw.answer(control))
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=4)

    first = run_b1.run_item(case, DATASET, glossary, fake, budget, tmp_path / "items", sleep=lambda s: None)
    again = run_b1.run_item(case, DATASET, glossary, tlw.Fake(), budget, tmp_path / "items", sleep=lambda s: None)

    assert first["path"] == "primary" and again == first and len(fake.calls) == 1 and budget.used_run == 1
    assert first["attempts"][0]["request_digest"] and first["guide_sha256"] == run_b1.lw.guide_sha256()


def test_the_review_document_puts_both_texts_and_the_path_and_checks_side_by_side(tmp_path, monkeypatch):
    case = "veteran-824027"
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    doc = writer_input.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
    control = tlw.twc.candidate(doc)
    monkeypatch.setattr(writer_checks, "rules_length", lambda report: writer_checks.report_length(control))
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=8)
    ok = run_b1.run_item(case, DATASET, glossary, tlw.Fake(tlw.answer(control)), budget, tmp_path / "a", sleep=lambda s: None)
    rejected = run_b1.run_item(case, DATASET, glossary, tlw.Fake(tlw.answer(tlw.bad(control)), tlw.answer(tlw.bad(control))), budget, tmp_path / "b", sleep=lambda s: None)

    text = run_b1.review_markdown([ok, rejected], budget)

    assert "Path: **primary**" in text and "Path: **rules** (reason: `checks_failed`)" in text
    assert "### Rules text (A)" in text and "### Model text (B1)" in text and "rejected; the last candidate" in text
    assert "Failed checks: ['W10.cause']" in text and "run 3 of 8" in text
    assert "Kyle Freeland and José Soriano start this game." in text
