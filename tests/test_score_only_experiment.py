"""D54-D57: offline scores do not relax code gates or publish model prose."""
import pytest

from agents import llm_report_writer as lw, nli_admission as na, writer_policy as wp
from agents import writer_checks as wc
from evals import run_b1
from tests.test_llm_report_writer import parts, Fake, answer, bad
from tests.test_nli_admission import Scorer


@pytest.mark.parametrize("value", [0.01, None])
def test_default_score_only_records_low_or_missing_scores_without_retry(parts, monkeypatch, value):
    packet, findings, glossary, candidate = parts
    monkeypatch.setattr(wc, "rules_length", lambda _: wc.report_length(candidate))
    score = na.make_scorer(cache="unused", scorer=Scorer(value))
    fake = Fake(answer(candidate, version="gemini-3.1-flash-lite"))
    result = lw.write(findings, packet, glossary, provider=fake, nli=score, sleep=lambda _: None)
    assert result.path == "primary" and len(fake.calls) == 1
    assert result.attempts[0]["nli_mode"] == "score_only"
    detail = result.attempts[0]["nli"]
    assert len(detail) == len(wc._all_sentences(candidate))
    assert any(d["score"] == value for d in detail if d["problem"] != "not_applicable")
    assert all("evidence_paths" in d for d in detail)
    assert result.attempts[0]["checks"] == []


def test_score_only_still_rejects_code_failures_and_scores_rejected_sentences(parts, monkeypatch):
    packet, findings, glossary, candidate = parts
    monkeypatch.setattr(wc, "rules_length", lambda _: wc.report_length(candidate))
    fake = Fake(answer(bad(candidate), version="gemini-3.1-flash-lite"), answer(bad(candidate), version="gemini-3.1-flash-lite"))
    result = lw.write(findings, packet, glossary, provider=fake,
                      nli=na.make_scorer(cache="unused", scorer=Scorer(0.99)), sleep=lambda _: None)
    assert result.path == "rules" and result.failures == ["W10.cause"]
    assert len(fake.calls) == 2 and all(a["nli"] for a in result.attempts)


def test_explicit_gate_without_calibration_still_fails_closed(parts, monkeypatch):
    packet, findings, glossary, candidate = parts
    monkeypatch.setattr(wc, "rules_length", lambda _: wc.report_length(candidate))
    fake = Fake(answer(candidate, version="gemini-3.1-flash-lite"))
    result = lw.write(findings, packet, glossary, provider=fake, nli_mode="gate",
                      nli=na.make_gate(cache="unused"), sleep=lambda _: None)
    assert result.path == "rules" and result.failures == ["NLI.uncalibrated"] and len(fake.calls) == 1


@pytest.mark.parametrize("cases,calls,want", [(4, 20, False), (5, 15, False), (5, 16, True), (6, 18, False), (6, 19, True)])
def test_average_stop_boundaries(cases, calls, want):
    assert run_b1.average_stop(cases, calls) is want


def test_writer_order_and_request_settings(parts, monkeypatch):
    packet, findings, glossary, candidate = parts
    monkeypatch.setattr(wc, "rules_length", lambda _: wc.report_length(candidate))
    fake = Fake(answer(candidate, version="gemini-3.1-flash-lite"))
    result = lw.write(findings, packet, glossary, provider=fake, sleep=lambda _: None)
    assert result.path == "primary" and fake.calls[0][0] == "gemini-3.1-flash-lite"
    assert wp.WRITER_MODELS == ("gemini-3.1-flash-lite", "gemini-3.5-flash")
    assert wp.PACING_SECONDS == 20
    config = fake.calls[0][2]["generationConfig"]
    assert config["thinkingConfig"] == {"thinkingLevel": "LOW"} and "temperature" not in config


def test_changed_model_or_mode_cannot_reuse_a_saved_item(tmp_path, monkeypatch):
    from agents import call_budget as cb, writer_input
    glossary = writer_input.load_glossary(run_b1.DATASET / "glossary.json")
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=8)
    fake = Fake()
    # A finalized client error is saved; unlike a cap result it is resumable.
    from tests.test_llm_report_writer import status
    run_b1.run_item("veteran-824027", run_b1.DATASET, glossary, Fake(status(403)), budget, tmp_path / "items", sleep=lambda _: None)
    monkeypatch.setattr(wp, "WRITER_MODELS", ("changed", "fallback"))
    with pytest.raises(ValueError, match="identity"):
        run_b1.run_item("veteran-824027", run_b1.DATASET, glossary, fake, budget, tmp_path / "items", sleep=lambda _: None)
    assert budget.used_run == 1


def test_average_stop_keeps_five_cases_and_resumes_without_more_calls(tmp_path):
    from agents import call_budget as cb, writer_input
    from tests.test_llm_report_writer import status
    glossary = writer_input.load_glossary(run_b1.DATASET / "glossary.json")
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=30)
    # 500 is not a capacity failure: each candidate tries both models once,
    # followed by a content failure on a validly parsed but wrong structure.
    script = []
    for _ in range(5):
        script.extend([status(500), answer({}, version="gemini-3.5-flash"),
                       status(500), answer({}, version="gemini-3.5-flash")])
    provider = Fake(*script)
    cases = run_b1.pick_cases()
    items, stop = run_b1.run_all(cases, run_b1.DATASET, glossary, provider, budget, tmp_path / "items", sleep=lambda _: None)
    assert stop["reason"] == "average_call_stop" and stop["cases"] == 5 and stop["calls"] == 20
    assert len([i for i in items if i["path"] == "not_attempted"]) == 5
    resumed = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=30)
    again, stop2 = run_b1.run_all(cases, run_b1.DATASET, glossary, Fake(), resumed, tmp_path / "items", sleep=lambda _: None)
    assert again == items and stop2["calls"] == 20 and resumed.used_run == 20
    assert stop2["after_case"] == stop["after_case"] == cases[4]
    text = run_b1.review_markdown(items, budget)
    assert "NOT ATTEMPTED (calls-per-case stop)" in text and "NOT ATTEMPTED (capacity stop)" not in text


def test_gate_mode_without_an_adapter_fails_closed_before_any_provider_call(parts):
    packet, findings, glossary, candidate = parts
    fake = Fake(answer(candidate))
    result = lw.write(findings, packet, glossary, provider=fake, nli_mode="gate", sleep=lambda _: None)
    assert result.path == "rules" and result.reason == "nli_unavailable" and fake.calls == []


def test_score_worker_exception_is_recorded_for_each_sentence_without_a_retry(parts, monkeypatch):
    packet, findings, glossary, candidate = parts
    monkeypatch.setattr(wc, "rules_length", lambda _: wc.report_length(candidate))
    def broken(*args, **kwargs):
        raise RuntimeError("synthetic worker failure")
    fake = Fake(answer(candidate))
    result = lw.write(findings, packet, glossary, provider=fake,
                      nli=na.make_scorer(cache="unused", scorer=broken), sleep=lambda _: None)
    assert result.path == "primary" and len(fake.calls) == 1
    assert "NLI.unavailable" in result.attempts[0]["nli_findings"]
    assert all(d["score"] is None for d in result.attempts[0]["nli"])


def test_enabling_nli_does_not_reuse_items_without_scores(tmp_path):
    from agents import call_budget as cb, writer_input
    from tests.test_llm_report_writer import status
    glossary = writer_input.load_glossary(run_b1.DATASET / "glossary.json")
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=30)
    run_b1.run_item("veteran-824027", run_b1.DATASET, glossary, Fake(status(403)), budget, tmp_path / "items", sleep=lambda _: None)
    with pytest.raises(ValueError, match="identity"):
        run_b1.run_item("veteran-824027", run_b1.DATASET, glossary, Fake(), budget, tmp_path / "items", sleep=lambda _: None,
                        nli=na.make_scorer(cache="unused", scorer=Scorer(0.9)))
    assert budget.used_run == 1


@pytest.mark.parametrize("reason,label", [("average_call_stop", "calls-per-case stop"), ("capacity_stop", "capacity stop")])
def test_review_uses_the_recorded_stop_reason(tmp_path, reason, label):
    from agents import call_budget as cb
    budget = cb.CallBudget(tmp_path / "calls.jsonl", run="r", run_cap=30)
    item = {"case_id": "unused", "path": "not_attempted", "reason": reason, "content_attempts": 0}
    assert f"NOT ATTEMPTED ({label})" in run_b1.review_markdown([item], budget)
