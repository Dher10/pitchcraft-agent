"""The local NLI stage: fail closed everywhere, wired into the cascade after the code gates. Fake scorers; the real model is in test_nli_real_smoke."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_llm_report_writer as tlw  # noqa: E402
import test_positive_control as tpc  # noqa: E402
from agents import fact_renderer as fr  # noqa: E402
from agents import nli_admission as na  # noqa: E402
from agents import nli_cache  # noqa: E402
from agents import llm_report_writer as lw  # noqa: E402
from agents import writer_policy as wp  # noqa: E402
from agents import writer_checks as wc  # noqa: E402

parts = tlw.parts


def good_calibration(threshold=0.9, **over):
    base = {"labels": "human", "human_labels": 120, "admission_allowed": True, "identity": nli_cache.identity(), "renderer": fr.renderer_identity(), "threshold": threshold}
    return {**base, **over}


class Scorer:
    def __init__(self, value=0.99, fail=False):
        self.value, self.fail, self.calls = value, fail, []

    def __call__(self, cache, pairs, python=None, timeout=60):
        self.calls.append(list(pairs))
        return None if self.fail else [self.value(p) if callable(self.value) else self.value for p in pairs]


def control():
    case, doc, candidate = tpc.load()
    return doc, candidate


@pytest.mark.parametrize("calibration", [
    None, {}, good_calibration(labels="synthetic"), good_calibration(admission_allowed=False), good_calibration(identity="0" * 64),
    good_calibration(renderer="p0"), good_calibration(renderer=fr.FACT_RENDERER_VERSION), good_calibration(human_labels=0), good_calibration(human_labels=None), good_calibration(threshold=None), good_calibration(threshold=0), good_calibration(threshold=1.5),
    good_calibration(threshold=float("nan")), good_calibration(threshold=float("inf")), "0.9",
])
def test_only_a_human_calibration_bound_to_this_identity_is_usable(calibration):
    assert na.calibration_ok(calibration) is False


def test_a_human_calibration_bound_to_this_model_runtime_and_renderer_is_usable():
    assert na.calibration_ok(good_calibration()) is True


def test_the_control_has_a_checkable_premise_for_every_factual_sentence_and_watch_sentences_are_skipped():
    doc, candidate = control()

    entries = na.plan_pairs(candidate, doc)

    assert entries and all(e["problem"] is None and e["premise"] for e in entries)
    watch_texts = {s["text"] for s in candidate["sections"]["watch"]} | {candidate["summary_lines"][2]["text"]}
    assert not [e for e in entries if e["text"] in watch_texts]
    assert len(entries) == len(wc._all_sentences(candidate)) - len(watch_texts)


def test_scoring_batches_at_most_32_pairs_and_passes_premise_then_sentence():
    doc, candidate = control()
    scorer = Scorer(0.99)

    results = na.score_candidate(candidate, doc, cache="c", scorer=scorer)

    assert all(len(call) <= 32 for call in scorer.calls) and len(scorer.calls) >= 1
    assert all(r["score"] == 0.99 for r in results)
    premise, text = scorer.calls[0][0]
    assert text == candidate["headline"]["text"] and "Kyle Freeland" in premise


def test_a_supported_report_passes_and_a_low_score_is_unsupported():
    doc, candidate = control()
    ok = na.verdict(na.score_candidate(candidate, doc, cache="c", scorer=Scorer(0.99)), good_calibration())
    low = na.verdict(na.score_candidate(candidate, doc, cache="c", scorer=Scorer(0.5)), good_calibration())

    assert ok[0] == [] and all(d["score"] == 0.99 for d in ok[1])
    assert low[0] == ["NLI.unsupported"]


def test_a_worker_failure_is_unavailable_never_a_pass():
    doc, candidate = control()

    codes, detail = na.verdict(na.score_candidate(candidate, doc, cache="c", scorer=Scorer(fail=True)), good_calibration())

    assert codes == ["NLI.unavailable"] and all(d["score"] is None for d in detail)


def test_an_unrenderable_citation_and_an_oversize_premise_are_rejected_without_a_score():
    doc, candidate = control()
    candidate["sections"]["arsenal"][0]["evidence"] = [{"path": "starters.away_starter.team", "value": "COL"}]
    paths = [p for p in wc.wi.evidence_index(doc) if p.startswith(("pitch_movement.", "pitch_mix."))]
    candidate["sections"]["arsenal"][1]["evidence"] = [{"path": p, "value": "x"} for p in paths]

    results = na.score_candidate(candidate, doc, cache="c", scorer=Scorer(0.99))
    codes, _ = na.verdict(results, good_calibration())

    assert set(codes) == {"NLI.unrenderable", "NLI.oversize"}
    assert [r["score"] for r in results if r["problem"]] == [None, None]


def test_no_usable_calibration_rejects_everything_and_never_calls_the_worker():
    doc, candidate = control()
    scorer = Scorer(0.99)

    for calibration in (None, good_calibration(labels="synthetic")):
        codes, detail = na.make_gate(cache="c", calibration=calibration, scorer=scorer)(candidate, doc)
        assert codes == ["NLI.uncalibrated"] and detail == []

    assert scorer.calls == []


def test_the_detail_never_carries_the_premise_text():
    doc, candidate = control()

    _, detail = na.verdict(na.score_candidate(candidate, doc, cache="c", scorer=Scorer(0.99)), good_calibration())

    assert all(set(d) == {"index", "sentence", "score", "problem", "premise_chars", "threshold"} for d in detail) and '"premise":' not in json.dumps(detail)


# --- wired into the cascade -----------------------------------------------------------------------------------------------------


@pytest.fixture
def lengths(monkeypatch, parts):
    monkeypatch.setattr(wc, "rules_length", lambda report: wc.report_length(parts[3]))


def go(parts, fake, nli):
    packet, findings, glossary, _ = parts
    return lw.write(findings, packet, glossary, provider=fake, item_id="x", sleep=lambda s: None, pacer=wp.Pacer(0, sleep=lambda s: None), nli=nli, nli_mode="gate")


def test_without_an_nli_gate_the_cascade_is_unchanged(parts, lengths):
    packet, findings, glossary, _ = parts
    result = lw.write(findings, packet, glossary, provider=tlw.Fake(tlw.answer(parts[3])), sleep=lambda _: None)

    assert result.path == "primary" and "nli" not in result.attempts[0]


def test_a_supported_report_is_accepted_and_the_scores_are_recorded(parts, lengths):
    gate = na.make_gate(cache="c", calibration=good_calibration(), scorer=Scorer(0.99))

    result = go(parts, tlw.Fake(tlw.answer(parts[3])), gate)

    assert result.path == "primary" and result.attempts[0]["nli"] and result.attempts[0]["checks"] == []


def test_an_unsupported_report_gets_one_informed_retry_naming_the_closed_code_and_then_the_rules_report(parts, lengths):
    gate = na.make_gate(cache="c", calibration=good_calibration(), scorer=Scorer(0.1))
    fake = tlw.Fake(tlw.answer(parts[3]), tlw.answer(parts[3]))

    result = go(parts, fake, gate)

    second = fake.calls[1][2]["contents"][0]["parts"][0]["text"]
    assert result.path == "rules" and result.reason == "checks_failed" and len(fake.calls) == 2 and result.failures == ["NLI.unsupported"]
    assert "NLI.unsupported" in second


def test_with_no_calibration_the_whole_cascade_falls_back_to_the_rules_report(parts, lengths):
    gate = na.make_gate(cache="c", calibration=None, scorer=Scorer(0.99))

    fake = tlw.Fake(tlw.answer(parts[3]), tlw.answer(parts[3]))

    result = go(parts, fake, gate)

    assert result.path == "rules" and result.failures == ["NLI.uncalibrated"] and result.reason == "nli_unavailable"
    assert len(fake.calls) == 1  # a second Gemini call cannot fix a missing calibration


def test_the_nli_stage_does_not_run_when_a_code_gate_already_failed(parts, lengths):
    scorer = Scorer(0.99)
    gate = na.make_gate(cache="c", calibration=good_calibration(), scorer=scorer)
    bad = tlw.bad(parts[3])

    go(parts, tlw.Fake(tlw.answer(bad), tlw.answer(bad)), gate)

    assert scorer.calls == []
