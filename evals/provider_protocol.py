"""P2.1 fixed synthetic probes, not a writer/judge or publication adapter.

Provider references and entitlement limits are recorded in docs/RUNBOOK.md.
Only the boolean probe result is retained; text/reasoning/errors are discarded.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from agents.model_transport import ProviderResponse, RATE_FIELDS

MODELS = {"gemini": "gemini-3.8-flash", "groq": "openai/gpt-oss-120b"}
OUTPUT_CAP = 1024
RESERVATION = 4096
SCHEMA = {"type": "object", "properties": {"ok": {"type": "boolean"}},
          "required": ["ok"], "additionalProperties": False}
PROMPT = 'Return only the JSON object {"ok":true}. This is a synthetic access probe.'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def probe_request(provider):
    model = MODELS[provider]
    if provider == "gemini":
        body = {"contents": [{"role": "user", "parts": [{"text": PROMPT}]}],
                # No temperature: Google keeps Gemini 3 at its default (lower may loop).
                # gemini-3.8-flash supports LOW/MEDIUM/HIGH, so LOW is the lowest level.
                "generationConfig": {"maxOutputTokens": OUTPUT_CAP,
                    "thinkingConfig": {"thinkingLevel": "LOW"}, "responseMimeType": "application/json",
                    "responseJsonSchema": SCHEMA}}
    else:
        body = {"model": model, "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0, "max_completion_tokens": OUTPUT_CAP,
                "reasoning_effort": "low", "include_reasoning": False, "stream": False,
                "response_format": {"type": "json_schema", "json_schema": {
                    "name": "access_probe", "strict": True, "schema": SCHEMA}}}
    return model, body


def request_identity(provider, commit, dirty_digest):
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or not re.fullmatch(r"[0-9a-f]{64}", dirty_digest):
        raise ValueError("malformed_response")
    model, body = probe_request(provider)
    identity = {"commit": commit, "dirty_digest": dirty_digest, "provider": provider, "model": model,
        "body_digest": digest(body), "protocol_digest": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "guide_digest": digest("not-created-synthetic-probe-only"), "prompt_digest": digest(PROMPT),
        "schema_digest": digest(SCHEMA), "evaluator_digest": digest("boolean-probe-v1"),
        "input_digest": digest("no-packet-no-report-no-held-out-evidence")}
    return {"request_digest": digest(identity), **identity}


def _count(value, cap=RESERVATION):
    if type(value) is not int or not 0 <= value <= cap:
        raise ValueError("malformed_response")
    return value


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("malformed_response")
        value[key] = item
    return value


def _usage(provider, body):
    if provider == "gemini":
        usage = body["usageMetadata"]
        inp = _count(usage["promptTokenCount"])
        out = _count(usage["candidatesTokenCount"], OUTPUT_CAP)
        reasoning = _count(usage["thoughtsTokenCount"], OUTPUT_CAP) if "thoughtsTokenCount" in usage else None
        total = _count(usage["totalTokenCount"])
        if total != inp + out + (reasoning or 0) or out + (reasoning or 0) > OUTPUT_CAP:
            raise ValueError("malformed_response")
    else:
        usage = body["usage"]
        inp = _count(usage["prompt_tokens"])
        out = _count(usage["completion_tokens"], OUTPUT_CAP)
        total = _count(usage["total_tokens"])
        details = usage.get("completion_tokens_details") or {}
        reasoning = _count(details["reasoning_tokens"], out) if "reasoning_tokens" in details else None
        if total != inp + out:
            raise ValueError("malformed_response")
    return {"input_tokens": inp, "output_tokens": out, "reasoning_tokens": reasoning, "total_tokens": total}


def parse_probe(provider, response: ProviderResponse):
    result = {"event": "rejected", "code": "malformed_response", "http_status": None,
        "input_tokens": None, "output_tokens": None, "reasoning_tokens": None,
        "total_tokens": None, "fingerprint_digest": None, "output_digest": None, "rate": {}}
    try:
        if provider not in MODELS or type(response.status) is not int or not 100 <= response.status <= 599:
            return result
        result["http_status"] = response.status
        result["rate"] = {key: _count(value, 999_999_999) for key, value in response.rate.items() if key in RATE_FIELDS}
        if response.status != 200:
            result["code"] = "budget_spent" if response.status == 429 else "request_failed"
            return result
        body = response.body
        result.update(_usage(provider, body))
        if provider == "gemini":
            version = body["modelVersion"]
            if type(version) is not str or re.fullmatch(re.escape(MODELS[provider]) + r"(?:-[0-9]{3,14})?", version) is None:
                return result
            choices = body["candidates"]
            if type(choices) is not list or len(choices) != 1 or body.get("promptFeedback", {}).get("blockReason"):
                return result
            choice = choices[0]
            if choice["finishReason"] != "STOP" or choice["content"]["role"] != "model":
                return result
            parts = choice["content"]["parts"]
            # Gemini may attach an opaque thoughtSignature to any part; never retained.
            if type(parts) is not list or len(parts) != 1 or set(parts[0]) - {"thoughtSignature"} != {"text"}:
                return result
            if type(parts[0].get("thoughtSignature", "")) is not str:
                return result
            text = parts[0]["text"]
            fingerprint = version
        else:
            if body["model"] != MODELS[provider]:
                return result
            choices = body["choices"]
            if type(choices) is not list or len(choices) != 1:
                return result
            choice = choices[0]
            message = choice["message"]
            if choice["finish_reason"] != "stop" or message["role"] != "assistant" or message.get("refusal") or message.get("tool_calls") or message.get("function_call"):
                return result
            text = message["content"]
            fingerprint = body.get("system_fingerprint")
            if fingerprint is not None and (type(fingerprint) is not str or not 1 <= len(fingerprint) <= 200):
                return result
        # Usage is retained even for invalid/truncated probe text once verified.
        result["fingerprint_digest"] = digest(fingerprint) if fingerprint is not None else None
        if type(text) is not str or len(text) > 100:
            return result
        parsed = json.loads(text, object_pairs_hook=_pairs)
        if type(parsed) is not dict or set(parsed) != {"ok"} or parsed["ok"] is not True:
            return result
        result.update(event="accepted", code=None, output_digest=digest(parsed))
    except Exception:
        # Only a closed record escapes; no provider strings or exception repr.
        pass
    return result
