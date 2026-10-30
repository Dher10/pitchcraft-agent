"""P2.2: the offline B1 runner on dev cases, with a fake provider. No key, no network."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

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
    assert "### Rules text (A)" in text and "### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks" in text
    assert "checks ['W10.cause']" in text and "run 3 of 8" in text
    assert "Kyle Freeland and José Soriano start this game." in text


def test_the_review_document_lists_each_failed_check_with_its_sentence_and_token_and_the_capacity_share(tmp_path, monkeypatch):
    case = "veteran-824027"
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    doc = writer_input.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
    control = tlw.twc.candidate(doc)
    monkeypatch.setattr(writer_checks, "rules_length", lambda report: writer_checks.report_length(control))
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=8)
    fake = tlw.Fake(tlw.ProviderResponse(503, {}, None), tlw.answer(tlw.bad(control)), tlw.answer(tlw.bad(control)))
    item = run_b1.run_item(case, DATASET, glossary, fake, budget, tmp_path / "items", sleep=lambda s: None)
    info = {"started_local": "2026-10-30 22:00", "started_utc": "2026-10-31 03:00", "finished_local": "2026-10-30 22:20", "timezone": "COT"}

    text = run_b1.review_markdown([item], budget, info, calibrate=True)

    assert "`W10.cause` token `because` in: Kyle Freeland throws his Four-seam because it works." in text
    assert "Capacity failures (503/429) in this run: 1 of 3 finished calls." in text
    assert "Calibration note: the rules text of veteran-824027" in text and "`W15.question`" in text
    assert "time of day of the run" not in text  # 1 of 3 is not more than a third


def test_more_than_a_third_capacity_failures_reports_the_time_of_day(tmp_path):
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=8)
    for code in ("http_503", "http_503", "ok"):
        budget.finish(budget.reserve("x", "m"), code)
    info = {"started_local": "2026-10-30 22:00", "started_utc": "2026-10-31 03:00", "finished_local": "2026-10-30 22:20", "timezone": "COT"}

    text = run_b1.review_markdown([], budget, info)

    assert "time of day of the run: 2026-10-30 22:00 to 2026-10-30 22:20 local (COT)" in text


def test_the_shown_candidate_is_the_one_with_the_fewest_failed_checks_and_a_later_one_wins_a_tie():
    def attempt(n, checks):
        return {"content_attempt": n, "checks": checks, "candidate": {"n": n}}

    assert run_b1.best_attempt({"attempts": [attempt(1, ["a", "b"]), attempt(2, ["a"])]})[0] == 2
    assert run_b1.best_attempt({"attempts": [attempt(1, ["a"]), attempt(2, ["a"])]})[0] == 2
    assert run_b1.best_attempt({"attempts": [attempt(1, []), attempt(2, ["a"])]})[0] == 1
    assert run_b1.best_attempt({"attempts": [{"content_attempt": 1, "checks": ["W17.structure"]}]}) is None


def test_a_readability_note_may_only_quote_text_that_is_shown(tmp_path, monkeypatch):
    case = "veteran-824027"
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    doc = writer_input.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
    control = tlw.twc.candidate(doc)
    monkeypatch.setattr(writer_checks, "rules_length", lambda report: writer_checks.report_length(control))
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=8)
    item = run_b1.run_item(case, DATASET, glossary, tlw.Fake(tlw.answer(tlw.bad(control)), tlw.answer(tlw.bad(control))), budget, tmp_path / "items", sleep=lambda s: None)

    good = {case: {"text": "Reads fine.", "quotes": ["throws his Four-seam because it works"]}}
    bad = {case: {"text": "Reads fine.", "quotes": ["a sentence the model never wrote"]}}

    assert "Reads fine." in run_b1.review_markdown([item], budget, notes=good)
    with pytest.raises(ValueError):
        run_b1.review_markdown([item], budget, notes=bad)
