"""Whole synthetic envelopes with zero, absent and hostile metadata controls."""
import copy
import importlib
import json
from pathlib import Path

import pytest

from agents.model_transport import ProviderResponse

FIXTURES = json.loads((Path(__file__).parent / "fixtures/provider_probes.json").read_text())


def protocol():
    module = importlib.util.find_spec("evals.provider_protocol") if importlib.util.find_spec("evals") else None
    assert module is not None, "P2.1 provider probe protocol is missing"
    return importlib.import_module("evals.provider_protocol")


@pytest.mark.parametrize("provider", ("gemini", "groq"))
def test_complete_probe_preserves_usage_without_raw_reasoning(provider):
    result = protocol().parse_probe(provider, ProviderResponse(200, {}, FIXTURES[provider]))
    assert result["event"] == "accepted"
    assert result["code"] is None
    assert result["total_tokens"] == (50 if provider == "gemini" else 70)
    assert result["reasoning_tokens"] == (20 if provider == "gemini" else 35)
    assert "SENTINEL" not in json.dumps(result)
    assert len(result["fingerprint_digest"]) == 64


@pytest.mark.parametrize("provider", ("gemini", "groq"))
@pytest.mark.parametrize("mutation", ("missing-usage", "negative", "bool", "wrong-model", "truncated", "extra-output", "tools", "duplicate", "bad-total"))
def test_incomplete_hostile_or_wrong_identity_is_not_accepted(provider, mutation):
    body = copy.deepcopy(FIXTURES[provider])
    usage_key = "usageMetadata" if provider == "gemini" else "usage"
    input_key = "promptTokenCount" if provider == "gemini" else "prompt_tokens"
    total_key = "totalTokenCount" if provider == "gemini" else "total_tokens"
    choice = body["candidates" if provider == "gemini" else "choices"][0]
    if mutation == "missing-usage":
        del body[usage_key]
    elif mutation in ("negative", "bool"):
        body[usage_key][input_key] = -1 if mutation == "negative" else True
    elif mutation == "wrong-model":
        body["modelVersion" if provider == "gemini" else "model"] = "SECRET-SENTINEL"
    elif mutation == "bad-total":
        body[usage_key][total_key] = 1
    elif mutation == "truncated":
        choice["finishReason" if provider == "gemini" else "finish_reason"] = "MAX_TOKENS"
    elif provider == "gemini":
        choice["content"]["parts"] = ([{"functionCall": {"name": "SECRET-SENTINEL"}}] if mutation == "tools" else
            [{"text": '{"ok":true,"extra":"SECRET-SENTINEL"}' if mutation == "extra-output" else '{"ok":false,"ok":true}'}])
    else:
        if mutation == "tools":
            choice["message"]["tool_calls"] = [{"SECRET-SENTINEL": True}]
        else:
            choice["message"]["content"] = ('{"ok":true,"extra":"SECRET-SENTINEL"}' if mutation == "extra-output" else '{"ok":false,"ok":true}')
    result = protocol().parse_probe(provider, ProviderResponse(200, {}, body))
    assert result["event"] == "rejected"
    assert result["code"] == "malformed_response"
    assert "SENTINEL" not in json.dumps(result)


@pytest.mark.parametrize("status,code", ((401, "request_failed"), (403, "request_failed"), (429, "budget_spent"), (500, "request_failed")))
def test_auth_quota_and_server_failures_keep_only_existing_codes(status, code):
    result = protocol().parse_probe("groq", ProviderResponse(status, {"retry-after": 60}, None))
    assert result["event"] == "rejected" and result["code"] == code
    assert result["http_status"] == status and result["total_tokens"] is None


def test_zero_reasoning_is_measured_and_absent_reasoning_is_unknown():
    module = protocol()
    body = copy.deepcopy(FIXTURES["groq"])
    body["usage"]["completion_tokens_details"]["reasoning_tokens"] = 0
    assert module.parse_probe("groq", ProviderResponse(200, {}, body))["reasoning_tokens"] == 0
    del body["usage"]["completion_tokens_details"]
    assert module.parse_probe("groq", ProviderResponse(200, {}, body))["reasoning_tokens"] is None
    body["usage"]["completion_tokens_details"] = None
    result = module.parse_probe("groq", ProviderResponse(200, {}, body))
    assert result["event"] == "accepted" and result["reasoning_tokens"] is None and result["total_tokens"] == 70


@pytest.mark.parametrize("provider", ("gemini", "groq"))
def test_truncated_response_retains_validated_usage_for_capacity(provider):
    body = copy.deepcopy(FIXTURES[provider])
    choice = body["candidates" if provider == "gemini" else "choices"][0]
    choice["finishReason" if provider == "gemini" else "finish_reason"] = "MAX_TOKENS"
    result = protocol().parse_probe(provider, ProviderResponse(200, {}, body))
    assert result["event"] == "rejected"
    assert result["total_tokens"] == (50 if provider == "gemini" else 70)


def test_undisclosed_fingerprint_remains_unknown():
    body = copy.deepcopy(FIXTURES["groq"])
    del body["system_fingerprint"]
    result = protocol().parse_probe("groq", ProviderResponse(200, {}, body))
    assert result["event"] == "accepted"
    assert result["fingerprint_digest"] is None


def test_groq_gpt_oss_hides_reasoning_with_supported_parameter():
    # Groq reasoning docs: reasoning_format is not supported on gpt-oss and
    # cannot be combined with include_reasoning.
    _, body = protocol().probe_request("groq")
    assert "reasoning_format" not in body
    assert body["include_reasoning"] is False and body["reasoning_effort"] == "low"


def test_gemini_3_uses_default_temperature_and_lowest_supported_thinking_level():
    # Google: for all Gemini 3 models keep temperature at its default; lowering it
    # may cause looping. gemini-3.8-flash supports low/medium/high, so LOW is the
    # lowest (MINIMAL is unsupported). API enum names are uppercase.
    _, body = protocol().probe_request("gemini")
    config = body["generationConfig"]
    assert "temperature" not in config
    assert config["thinkingConfig"] == {"thinkingLevel": "LOW"}
    assert config["maxOutputTokens"] == 1024


def test_groq_keeps_its_own_temperature_zero_control():
    assert protocol().probe_request("groq")[1]["temperature"] == 0


def test_gemini_thought_signature_on_text_part_is_accepted_and_discarded():
    body = copy.deepcopy(FIXTURES["gemini"])
    body["candidates"][0]["content"]["parts"][0]["thoughtSignature"] = "SECRET-SENTINEL-SIGNATURE"
    result = protocol().parse_probe("gemini", ProviderResponse(200, {}, body))
    assert result["event"] == "accepted"
    assert "SENTINEL" not in json.dumps(result)


@pytest.mark.parametrize("part", ({"text": '{"ok":true}', "thoughtSignature": 7},
                                  {"text": '{"ok":true}', "thought": True},
                                  {"thoughtSignature": "x"}))
def test_gemini_part_keys_beyond_text_and_signature_stay_rejected(part):
    body = copy.deepcopy(FIXTURES["gemini"])
    body["candidates"][0]["content"]["parts"] = [part]
    assert protocol().parse_probe("gemini", ProviderResponse(200, {}, body))["event"] == "rejected"


@pytest.mark.parametrize("provider", ("gemini", "groq"))
def test_request_is_fixed_bounded_json_no_tools_and_identity_covers_all_bytes(provider):
    module = protocol()
    model, body = module.probe_request(provider)
    assert model in ("gemini-3.8-flash", "openai/gpt-oss-120b")
    assert len(json.dumps(body).encode()) < 2000
    assert not any(k in json.dumps(body) for k in ('"tools"', '"google_search"', '"web_search"'))
    first = module.request_identity(provider, "a" * 40, "b" * 64)
    assert first != module.request_identity(provider, "c" * 40, "b" * 64)
    assert first != module.request_identity(provider, "a" * 40, "c" * 64)
    assert set(first) == {"request_digest", "commit", "dirty_digest", "provider", "model", "body_digest", "protocol_digest", "guide_digest", "prompt_digest", "schema_digest", "evaluator_digest", "input_digest"}
