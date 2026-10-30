"""The LLM report writer (P2.2): offline candidate reports with the fail-closed cascade.

`write(...)` builds the closed input, asks Gemini under the D49 transport policy, checks the candidate against the writer guide
(agents/writer_checks.py), makes ONE informed content retry (D2), and otherwise returns the rules writer's report. At most 8 HTTP
calls per item; every call is counted first by the CallBudget supplied by the caller. This module reads no key and no environment:
the caller supplies `provider(model, timeout, body) -> ProviderResponse`. Nothing here publishes anything; the candidate report is
an internal structure and rules stay live (D44/D45).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Callable

from agents import matchup_analyst, report_writer, writer_checks, writer_input, writer_policy
from agents.language import DEFAULT_LANGUAGE
from agents.security_policy import ModelRejected, bounded_text

def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()).hexdigest()


PROMPT_VERSION = "p2.2-1"
ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT / "docs" / "writer-guide.md"
MAX_OUTPUT_TOKENS = 8192
MAX_BODY_BYTES = 60_000
ROUTED = {"gemini-3.5-flash": ("gemini-3.6-flash",)}

_SENTENCE = {"type": "object", "additionalProperties": False, "required": ["text", "evidence"], "properties": {
    "text": {"type": "string"},
    "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["path", "value"],
                                            "properties": {"path": {"type": "string"}, "value": {"type": "string"}}}}}}
_LIST = {"type": "array", "items": _SENTENCE}
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["headline", "summary_lines", "sections"], "properties": {
    "headline": _SENTENCE, "summary_lines": _LIST,
    "sections": {"type": "object", "additionalProperties": False, "required": list(writer_checks.SECTION_KEYS),
                 "properties": {key: _LIST for key in writer_checks.SECTION_KEYS}}}}

LEX = json.loads((Path(__file__).with_name("writer_lexicon.json")).read_text(encoding="utf-8"))["en"]  # English wording lives in data (D6)
HINTS = LEX["hints"]
_PROMPT = LEX["prompt"]


class PromptRejected(ValueError):
    """The writer input holds a string the P2-SEC policy rejects; no request is built."""


def guide_text() -> str:
    text = GUIDE_PATH.read_bytes().decode("utf-8").replace("\r\n", "\n")
    text = text[text.index("## 1.") : text.index("## 6.")]
    # The writer must not see case ids or the dataset's folder names (W16).
    for pattern, replacement in _PROMPT["scrub"]:
        text = re.sub(pattern, replacement, text)
    return _PROMPT["guide_title"] + text.rstrip() + "\n"


def guide_sha256() -> str:
    return hashlib.sha256(GUIDE_PATH.read_bytes().decode("utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()


def system_instruction(rules_len: int) -> str:
    low, high = int(rules_len * 0.8), int(rules_len * 1.2)
    layout = _PROMPT["format"].replace("@LOW@", str(low)).replace("@HIGH@", str(high)).replace("@RULES@", str(rules_len))
    return _PROMPT["preface"] + guide_text() + layout


def _validate_strings(doc: dict) -> None:
    def walk(node, parent=""):
        if isinstance(node, dict):
            for key, value in node.items():
                # Pitch names and glossary terms are keys and reach the prompt too: short, plain characters only.
                pattern = LEX["patterns"]["term_key_chars" if parent == "glossary" else "key_chars"]
                if type(key) is not str or re.fullmatch(pattern, key) is None:
                    raise ModelRejected()
                walk(value, key)
        elif isinstance(node, list):
            for value in node:
                walk(value, parent)
        elif isinstance(node, str):
            bounded_text(node, 400)

    try:
        walk(doc)
    except ModelRejected:
        raise PromptRejected() from None


def build_body(doc: dict, rules_len: int, failures: list[str] | None = None) -> dict:
    """The Gemini request body. `failures` are closed check codes from the previous content attempt (the informed retry)."""

    _validate_strings(doc)
    data = {"DATA": doc}
    if failures:
        notes = [f"{code}: {HINTS.get(code, HINTS.get(code.split('.')[0], LEX['fallback_hint']))}" for code in failures]
        data["PREVIOUS_ATTEMPT_FAILED_THESE_CHECKS"] = notes
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    body = {
        "systemInstruction": {"parts": [{"text": system_instruction(rules_len)}]},
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        # D48/D49: default temperature (field omitted), lowest supported thinking level.
        "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS, "thinkingConfig": {"thinkingLevel": "LOW"},
                             "responseMimeType": "application/json", "responseJsonSchema": SCHEMA},
    }
    if len(json.dumps(body, ensure_ascii=True).encode("utf-8")) > MAX_BODY_BYTES:
        raise PromptRejected()
    return body


def request_identity(model: str, body: dict) -> str:
    return digest({"model": model, "body": body, "prompt": PROMPT_VERSION, "guide": guide_sha256()})


def parse_candidate(response: Any, model: str) -> tuple[dict | None, dict]:
    """(candidate or None, usage). A malformed, truncated or blocked answer gives None."""

    usage: dict = {}
    try:
        body = response.body
        meta = body.get("usageMetadata", {})
        usage = {k: meta[k] for k in ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount", "totalTokenCount") if type(meta.get(k)) is int}
        names = (model, *ROUTED.get(model, ()))
        version = body.get("modelVersion")
        if type(version) is not str or re.fullmatch("(?:" + "|".join(re.escape(n) for n in names) + r")(?:-[0-9]{3,14})?", version) is None:
            return None, usage
        choices = body["candidates"]
        if type(choices) is not list or len(choices) != 1 or body.get("promptFeedback", {}).get("blockReason"):
            return None, usage
        choice = choices[0]
        if choice["finishReason"] != "STOP":
            return None, usage
        parts = [p for p in choice["content"]["parts"] if not p.get("thought")]
        if len(parts) != 1 or type(parts[0].get("text")) is not str:
            return None, usage
        value = json.loads(parts[0]["text"], object_pairs_hook=_pairs)
        return (value if type(value) is dict else None), usage
    except Exception:
        return None, usage


@dataclass
class WriterResult:
    report: dict
    path: str  # primary, primary_retry, fallback, fallback_retry (model prose) or rules
    content_attempts: int = 0
    attempts: list = field(default_factory=list)  # one dict per content attempt: transport attempts, usage, check codes
    candidate: dict | None = None
    failures: list = field(default_factory=list)  # the check codes of the last rejected candidate
    reason: str | None = None  # closed code when the rules report was used


def rules_report_for(matchup_input: dict) -> dict:
    """The rules writer's report (A) for a packet. The analyst is deterministic: on a frozen packet it reproduces the frozen
    findings exactly (tested), and unlike the saved JSON it keeps the claim objects the rules writer reads."""

    return report_writer.run(matchup_analyst.run(matchup_input), matchup_input)


def rules_result(rules_report: dict, reason: str, **kw) -> WriterResult:
    return WriterResult(rules_report, "rules", reason=reason, **kw)


def write(
    findings: dict,
    matchup_input: dict,
    glossary: list[dict],
    *,
    provider: Callable[[str, float, dict], Any] | None = None,
    budget: Any = None,
    item_id: str = "item",
    sleep: Callable[[float], None] | None = None,
) -> WriterResult:
    rules_report = rules_report_for(matchup_input)
    if provider is None:
        return rules_result(rules_report, "no_provider")
    try:
        doc = writer_input.build_writer_input(matchup_input, findings, glossary)
        rules_len = writer_checks.rules_length(rules_report)
        body = build_body(doc, rules_len)
    except (writer_input.WriterInputError, PromptRejected):
        return rules_result(rules_report, "input_rejected")
    result = WriterResult(rules_report, "rules")
    failures: list[str] | None = None
    for content_attempt in (1, 2):
        if failures is not None:
            try:
                body = build_body(doc, rules_len, failures)
            except PromptRejected:
                return rules_result(rules_report, "input_rejected", content_attempts=result.content_attempts, attempts=result.attempts)

        def call(model, timeout, body=body):
            return provider(model, timeout, body)

        guarded = budget.guard(item_id, call) if budget is not None else call
        kwargs = {"sleep": sleep} if sleep is not None else {}
        outcome = writer_policy.write_with_policy(guarded, **kwargs)
        record: dict = {"content_attempt": content_attempt, "transport": list(outcome.attempts), "path": outcome.path}
        result.attempts.append(record)
        result.content_attempts = content_attempt
        if outcome.path == "rules":
            codes = [a["code"] for a in outcome.attempts]
            return rules_result(rules_report, codes[-1] if codes else "unavailable", content_attempts=content_attempt, attempts=result.attempts)
        model = writer_policy.WRITER_MODELS[0 if outcome.path.startswith("primary") else 1]
        candidate, usage = parse_candidate(outcome.response, model)
        record["usage"] = usage
        record["model"] = model
        record["request_digest"] = request_identity(model, body)
        record["candidate"] = candidate  # kept for the owner's review of rejected attempts too (dev only, local)
        if candidate is None:
            failures = result.failures = ["W17.structure"]
            record["checks"] = failures
            continue
        detail = writer_checks.check_report_detailed(candidate, doc, rules_len)
        failures = list(dict.fromkeys(f["check"] for f in detail))
        record["checks"] = failures
        record["check_detail"] = detail  # sentence, check and offending token: the local run record only, never fed back
        if not failures:
            return WriterResult(writer_checks.to_report(candidate, rules_report), outcome.path, content_attempt, result.attempts, candidate, [])
        result.failures = failures
    return rules_result(rules_report, "checks_failed", content_attempts=2, attempts=result.attempts, failures=result.failures)


def run(findings: dict, matchup_input: dict, language: str = DEFAULT_LANGUAGE, **kwargs) -> dict:
    """Same signature as the rules writer; without a provider this returns the rules report."""

    if language != DEFAULT_LANGUAGE:
        raise ValueError("English only")
    return write(findings, matchup_input, kwargs.pop("glossary", []), **kwargs).report
