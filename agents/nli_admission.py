"""The local NLI stage of the publication cascade (docs/SECURITY.md; eval-spec section 8; plan P2.3).

Each factual sentence of a candidate is checked against the verified fact sentences of the paths it cites
(`agents/fact_renderer.py`), by the pinned CPU model of `agents/nli_cache.py`. It runs after the code gates.

Fail closed: no calibration, a calibration that is not from human labels, an identity that differs from the model, runtime,
fact renderer or threshold of the run, an unrenderable or oversize premise, a worker that fails, or a score below the threshold
all REJECT. "Watch" sentences state something to look at, not a fact, so they are not entailment-checked (they still pass every
lexical gate). A score is not an accuracy guarantee.
"""
from __future__ import annotations

import math
from typing import Any, Callable

from agents import fact_renderer, nli_cache, writer_checks

BATCH = 32  # nli_cache caps a worker call at 32 pairs

CODES = ("NLI.uncalibrated", "NLI.unrenderable", "NLI.oversize", "NLI.unavailable", "NLI.unsupported")


def calibration_ok(calibration: Any) -> bool:
    """A usable calibration: from HUMAN labels, bound to this model, runtime, renderer and a finite threshold in (0, 1]."""

    try:
        return (
            isinstance(calibration, dict)
            and calibration.get("labels") == "human"
            and calibration.get("admission_allowed") is True
            and type(calibration.get("human_labels")) is int and calibration["human_labels"] > 0
            and calibration.get("identity") == nli_cache.identity()
            and calibration.get("renderer") == fact_renderer.renderer_identity()
            and type(calibration.get("threshold")) in (int, float)
            and math.isfinite(calibration["threshold"])
            and 0 < calibration["threshold"] <= 1
        )
    except Exception:
        return False


def plan_pairs(candidate: dict, doc: dict) -> list[dict]:
    """One entry per sentence to check: {"index", "text", "premise", "problem"}; Watch sentences are skipped."""

    watch = {id(s) for s in candidate["sections"]["watch"]}
    summary_watch = {id(s) for s in candidate["summary_lines"] if writer_checks._WATCH_FORM.match(s["text"])}
    entries = []
    for index, sentence in enumerate(writer_checks._all_sentences(candidate)):
        if id(sentence) in watch or id(sentence) in summary_watch:
            continue  # a thing to watch (the watch section, or a Watch line among the summary lines) is not a claim of fact
        premise, problem = fact_renderer.premise_for(doc, [e["path"] for e in sentence["evidence"]])
        text = writer_checks._nfc(sentence["text"])
        if problem is None and not 0 < len(text) <= 300:
            premise, problem = None, "oversize"
        entries.append({"index": index, "text": text, "premise": premise, "problem": problem})
    return entries


def score_candidate(candidate: dict, doc: dict, *, cache, python=None, scorer: Callable = None, timeout=120) -> list[dict]:
    """Plan the pairs and score the checkable ones; each result gets "score" (None when it could not be scored)."""

    scorer = scorer or nli_cache.scores
    entries = plan_pairs(candidate, doc)
    checkable = [e for e in entries if e["problem"] is None]
    for start in range(0, len(checkable), BATCH):
        chunk = checkable[start:start + BATCH]
        values = scorer(cache, [(e["premise"], e["text"]) for e in chunk], python=python, timeout=timeout)
        for entry, value in zip(chunk, values if values is not None and len(values) == len(chunk) else [None] * len(chunk)):
            entry["score"] = value
    for entry in entries:
        entry.setdefault("score", None)
    return entries


def verdict(results: list[dict], calibration: Any) -> tuple[list[str], list[dict]]:
    """(closed failure codes, per-sentence detail without the premise text). Empty codes means every checked sentence is supported."""

    if not calibration_ok(calibration):
        return ["NLI.uncalibrated"], [_brief(r, None) for r in results]
    threshold = calibration["threshold"]
    codes: list[str] = []
    for r in results:
        if r["problem"] == "unrenderable":
            codes.append("NLI.unrenderable")
        elif r["problem"] == "oversize":
            codes.append("NLI.oversize")
        elif r["score"] is None or not math.isfinite(r["score"]):
            codes.append("NLI.unavailable")
        elif r["score"] < threshold:
            codes.append("NLI.unsupported")
    return list(dict.fromkeys(codes)), [_brief(r, threshold) for r in results]


def _brief(result: dict, threshold: float | None) -> dict:
    return {"index": result["index"], "sentence": result["text"], "score": result["score"], "problem": result["problem"],
            "premise_chars": len(result["premise"] or ""), "threshold": threshold}


def make_gate(*, cache, python=None, calibration=None, scorer: Callable = None) -> Callable[[dict, dict], tuple[list[str], list[dict]]]:
    """A gate for `llm_report_writer.write(nli=...)`. With no (or an unusable) calibration it rejects every report: nothing is sent to
    the worker and the cascade falls back to the rules writer."""

    def gate(candidate: dict, doc: dict) -> tuple[list[str], list[dict]]:
        if not calibration_ok(calibration):
            return ["NLI.uncalibrated"], []
        try:
            results = score_candidate(candidate, doc, cache=cache, python=python, scorer=scorer)
            return verdict(results, calibration)
        except Exception:
            return ["NLI.unavailable"], []

    return gate
