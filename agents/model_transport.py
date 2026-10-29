"""Credential destinations are code, never model data or an environment URL.

No credentials are read here; the future approved runner supplies local keys.
Provider-specific schemas/quota pacing belong to P2.1; no live calls in tests.
"""
from __future__ import annotations

import json
import re
import ssl
import urllib.request


class ProviderRejected(ValueError):
    def __init__(self):
        super().__init__("request_failed")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_TOOLS = frozenset(("tools", "tool_choice", "functions", "function_call", "code_execution",
                    "google_search", "web_search", "retrieval", "url_context", "file_search"))


def _has_tools(value):
    if isinstance(value, dict):
        return bool(set(value) & _TOOLS) or any(_has_tools(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_tools(v) for v in value)
    return False


def post_json(provider, model, body, *, api_key, timeout=30):
    try:
        if type(provider) is not str or provider not in ("gemini", "groq"):
            raise ProviderRejected()
        pattern = r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}" + (r"(?:/[A-Za-z0-9][A-Za-z0-9._-]{0,99})?" if provider=="groq" else "")
        if type(model) is not str or re.fullmatch(pattern, model) is None:
            raise ProviderRejected()
        if type(api_key) is not str or not 1 <= len(api_key) <= 512 or any(ord(c)<33 or ord(c)>126 for c in api_key):
            raise ProviderRejected()
        if type(timeout) not in (int,float) or not 0 < timeout <= 60:
            raise ProviderRejected()
        if type(body) is not dict or _has_tools(body):
            raise ProviderRejected()
        body = dict(body)
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            headers = {"x-goog-api-key":api_key}
        else:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization":" ".join(("Bearer", api_key))}
            if body.get("model", model) != model:
                raise ProviderRejected()
            body["model"] = model
        encoded = json.dumps(body, allow_nan=False, ensure_ascii=True).encode("utf-8")
        if len(encoded) > 64_000:
            raise ProviderRejected()
        headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(131_073)
        if len(raw) > 131_072:
            raise ProviderRejected()
        def invalid_constant(_):
            raise ProviderRejected()
        value = json.loads(raw.decode("utf-8"), parse_constant=invalid_constant)
        if type(value) is not dict:
            raise ProviderRejected()
        return value
    except Exception:
        # Never export urllib exceptions, request repr, response bodies or headers.
        raise ProviderRejected() from None
