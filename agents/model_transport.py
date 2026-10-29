"""Credential destinations are code, never model data or an environment URL.

No credentials are read here; the future approved runner supplies local keys.
Provider-specific schemas/quota pacing belong to P2.1; no live calls in tests.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
import re
import ssl
import urllib.error
import urllib.request


class ProviderRejected(ValueError):
    def __init__(self):
        super().__init__("request_failed")


class ConnectionFailed(ProviderRejected):
    """The request was built and handed to the network, but no HTTP status came back."""


class ConnectionTimeout(ConnectionFailed):
    """No HTTP status arrived before the transport timeout."""


# Fixed product agent. Cloudflare in front of api.groq.com answers the default
# "Python-urllib/x" agent with 403 (error 1010) before authentication.
USER_AGENT = "pitchcraft-agent/1.0"


def _is_timeout(error):
    return isinstance(error, TimeoutError) or isinstance(getattr(error, "reason", None), TimeoutError)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


RATE_FIELDS = frozenset(("retry-after", "x-ratelimit-limit-requests",
    "x-ratelimit-limit-tokens", "x-ratelimit-remaining-requests",
    "x-ratelimit-remaining-tokens", "x-ratelimit-reset-requests", "x-ratelimit-reset-tokens"))


@dataclass(frozen=True)
class ProviderResponse:
    status: int
    rate: dict
    body: dict | None = field(repr=False)


def _rates(headers):
    result = {}
    for name in RATE_FIELDS:
        value = headers.get(name) if headers else None
        if name.startswith("x-ratelimit-reset-"):
            if type(value) is not str or not 1 <= len(value) <= 40:
                continue
            match = re.fullmatch(r"(?:(\d{1,6})h)?(?:(\d{1,6})m)?(?:(\d{1,6}(?:\.\d{1,3})?)s)?(?:(\d{1,6})ms)?", value)
            if match and any(part is not None for part in match.groups()):
                units = (3600000, 60000, 1000, 1)
                milliseconds = sum(Decimal(part or "0") * unit for part, unit in zip(match.groups(), units))
                if 0 <= milliseconds <= 999999999:
                    result[name] = int(milliseconds)
            continue
        if type(value) is str and re.fullmatch(r"[0-9]{1,9}", value):
            result[name] = int(value)
    return result


def _unique_pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ProviderRejected()
        result[key] = value
    return result


_TOOLS = frozenset(("tools", "tool_choice", "functions", "function_call", "code_execution",
                    "google_search", "web_search", "retrieval", "url_context", "file_search"))


def _has_tools(value):
    if isinstance(value, dict):
        return bool(set(value) & _TOOLS) or any(_has_tools(v) for v in value.values())
    if isinstance(value, list):
        return any(_has_tools(v) for v in value)
    return False


def post_json(provider, model, body, *, api_key, timeout=30, with_metadata=False):
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
        headers["User-Agent"] = USER_AGENT
        request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        try:
            response = opener.open(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            try:
                if with_metadata and type(error.code) is int and 100 <= error.code <= 599:
                    return ProviderResponse(error.code, _rates(error.headers), None)
                raise ProviderRejected() from None
            finally:
                error.close()
        except Exception as error:
            raise (ConnectionTimeout if _is_timeout(error) else ConnectionFailed)() from None
        with response:
            status = getattr(response, "status", 200)
            rate = _rates(getattr(response, "headers", None))
            raw = response.read(131_073)
        if len(raw) > 131_072:
            raise ProviderRejected()
        def invalid_constant(_):
            raise ProviderRejected()
        value = json.loads(raw.decode("utf-8"), parse_constant=invalid_constant,
                           object_pairs_hook=_unique_pairs)
        if type(value) is not dict:
            raise ProviderRejected()
        return ProviderResponse(status, rate, value) if with_metadata else value
    except ConnectionFailed as error:
        raise type(error)() from None
    except Exception:
        # Never export urllib exceptions, request repr, response bodies or headers.
        raise ProviderRejected() from None
