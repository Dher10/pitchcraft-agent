"""D49: failure policy and path record for every Gemini writer call.

The caller supplies call(model, timeout) -> ProviderResponse (transport with_metadata).
Nothing here reads a key, a body or an error message; only closed codes are kept.
The daily report never waits on Gemini beyond this bounded policy.
"""
from __future__ import annotations

from dataclasses import dataclass
import time

from agents.model_transport import ConnectionFailed, ConnectionTimeout

WRITER_MODELS = ("gemini-3.5-flash", "gemini-3.1-flash-lite")
WRITER_TIMEOUT = 120
BACKOFF_SECONDS = 3
PATHS = ("primary", "primary_retry", "fallback", "fallback_retry", "rules")
CODES = ("timeout", "http_429", "http_503", "http_4xx", "http_5xx", "connection_failed", "malformed_response", "call_cap_reached")
class CapReached(Exception):
    """The durable call cap (agents/call_budget.py) refused the next request; nothing was sent."""

    def __init__(self):
        super().__init__("call_cap_reached")


_RETRYABLE = ("timeout", "http_429", "http_503")


@dataclass(frozen=True)
class WriterOutcome:
    path: str
    response: object = None
    attempts: tuple = ()


def _classify(call, model):
    """Return (response, None) on success, else (None, closed code)."""
    try:
        response = call(model, WRITER_TIMEOUT)
    except CapReached:
        return None, "call_cap_reached"
    except ConnectionTimeout:
        return None, "timeout"
    except ConnectionFailed:
        return None, "connection_failed"
    except Exception:
        return None, "malformed_response"
    status = getattr(response, "status", None)
    if type(status) is not int:
        return None, "malformed_response"
    if status == 200:
        return (response, None) if type(getattr(response, "body", None)) is dict else (None, "malformed_response")
    if status in (429, 503):
        return None, f"http_{status}"
    if 400 <= status < 500:
        return None, "http_4xx"
    return None, "http_5xx"


def write_with_policy(call, *, sleep=time.sleep):
    attempts = []
    for index, model in enumerate(WRITER_MODELS):
        for number in (1, 2):
            response, code = _classify(call, model)
            if code is None:
                suffix = "" if number == 1 else "_retry"
                return WriterOutcome(("primary", "fallback")[index] + suffix, response, tuple(attempts))
            attempts.append({"model": model, "try": number, "code": code})
            if code in ("http_4xx", "call_cap_reached"):
                return WriterOutcome("rules", None, tuple(attempts))
            if code not in _RETRYABLE or number == 2:
                break
            sleep(BACKOFF_SECONDS)
    return WriterOutcome("rules", None, tuple(attempts))


def summarize(outcomes):
    paths = {path: 0 for path in PATHS}
    for outcome in outcomes:
        paths[outcome.path] += 1
    calls = len(outcomes)
    if not calls:
        return {"calls": 0, "paths": paths, "llm_coverage": None, "fallback_rate": None}
    llm = calls - paths["rules"]
    off_primary = paths["fallback"] + paths["fallback_retry"] + paths["rules"]
    return {"calls": calls, "paths": paths, "llm_coverage": llm / calls, "fallback_rate": off_primary / calls}
