"""D49: failure policy and path record of every Gemini writer call (synthetic, no network)."""
import pytest

from agents import model_transport as transport
from agents.model_transport import ProviderResponse
from agents import writer_policy as policy

PRIMARY, FALLBACK = "gemini-3.1-flash-lite", "gemini-3.5-flash"
OK = ProviderResponse(200, {}, {"candidates": []})


def script(*steps):
    """A call that replays steps in order: a response, or an exception class to raise."""
    seen = []
    queue = list(steps)

    def call(model, timeout):
        seen.append((model, timeout))
        step = queue.pop(0)
        if isinstance(step, type) and issubclass(step, Exception):
            raise step()
        return step
    call.seen = seen
    return call


def run(*steps):
    sleeps = []
    call = script(*steps)
    outcome = policy.write_with_policy(call, sleep=sleeps.append)
    return outcome, call.seen, sleeps


def test_constants_are_the_owner_decision():
    assert policy.WRITER_MODELS == (PRIMARY, FALLBACK)
    assert policy.WRITER_TIMEOUT == 120
    assert 0 < policy.BACKOFF_SECONDS <= 10


def test_success_on_the_first_call_is_primary_with_the_120_second_timeout():
    outcome, seen, sleeps = run(OK)
    assert outcome.path == "primary" and outcome.response is OK and outcome.attempts == ()
    assert seen == [(PRIMARY, 120)] and sleeps == []


@pytest.mark.parametrize("failure,code", ((ProviderResponse(503, {}, None), "http_503"),
                                          (ProviderResponse(429, {}, None), "http_429"),
                                          (transport.ConnectionTimeout, "timeout")))
def test_retryable_failure_retries_the_same_model_once_after_backoff(failure, code):
    outcome, seen, sleeps = run(failure, OK)
    assert outcome.path == "primary_retry"
    assert outcome.attempts == ({"model": PRIMARY, "try": 1, "code": code},)
    assert seen == [(PRIMARY, 120)] * 2 and sleeps == [policy.BACKOFF_SECONDS]


def test_two_primary_failures_go_to_the_fallback_which_is_not_retried_when_it_succeeds():
    outcome, seen, sleeps = run(ProviderResponse(503, {}, None), transport.ConnectionTimeout, OK)
    assert outcome.path == "fallback"
    assert [a["code"] for a in outcome.attempts] == ["http_503", "timeout"]
    assert [m for m, _ in seen] == [PRIMARY, PRIMARY, FALLBACK]
    assert len(sleeps) == 1


def test_fallback_has_the_same_policy_one_retry_then_rules():
    bad = ProviderResponse(429, {}, None)
    outcome, seen, sleeps = run(bad, bad, bad, OK)
    assert outcome.path == "fallback_retry" and [m for m, _ in seen][-2:] == [FALLBACK, FALLBACK]
    outcome, seen, sleeps = run(bad, bad, bad, bad)
    assert outcome.path == "rules" and outcome.response is None
    assert [a["code"] for a in outcome.attempts] == ["http_429"] * 4
    assert len(seen) == 4 and len(sleeps) == 2


@pytest.mark.parametrize("status", (400, 401, 403, 404, 422))
def test_other_4xx_go_straight_to_rules_without_retry_or_fallback(status):
    outcome, seen, sleeps = run(ProviderResponse(status, {}, None))
    assert outcome.path == "rules" and outcome.response is None
    assert outcome.attempts == ({"model": PRIMARY, "try": 1, "code": "http_4xx"},)
    assert len(seen) == 1 and sleeps == []


@pytest.mark.parametrize("failure,code", ((ProviderResponse(500, {}, None), "http_5xx"),
                                          (transport.ConnectionFailed, "connection_failed"),
                                          (ProviderResponse(200, {}, None), "malformed_response"),
                                          (transport.ProviderRejected, "malformed_response")))
def test_unlisted_failures_are_not_retried_but_try_the_fallback(failure, code):
    outcome, seen, sleeps = run(failure, OK)
    assert outcome.path == "fallback" and outcome.attempts == ({"model": PRIMARY, "try": 1, "code": code},)
    assert [m for m, _ in seen] == [PRIMARY, FALLBACK] and sleeps == []


def test_an_unexpected_exception_never_escapes_and_never_leaks_its_text():
    class Boom(Exception):
        pass
    outcome, _, _ = run(Boom, Boom)
    assert outcome.path == "rules"
    assert all(a["code"] == "malformed_response" for a in outcome.attempts)
    assert "Boom" not in repr(outcome)


def test_attempt_codes_and_paths_are_closed():
    assert set(policy.CODES) == {"timeout", "http_429", "http_503", "http_4xx", "http_5xx",
                                 "connection_failed", "malformed_response", "call_cap_reached"}
    assert set(policy.PATHS) == {"primary", "primary_retry", "fallback", "fallback_retry", "rules"}


def test_summary_reports_coverage_and_fallback_rate():
    bad = ProviderResponse(503, {}, None)
    outcomes = [run(OK)[0], run(bad, OK)[0], run(bad, bad, OK)[0], run(ProviderResponse(400, {}, None))[0]]
    summary = policy.summarize(outcomes)
    assert summary["calls"] == 4
    assert summary["paths"] == {"primary": 1, "primary_retry": 1, "fallback": 1, "fallback_retry": 0, "rules": 1}
    assert summary["llm_coverage"] == 0.75 and summary["fallback_rate"] == 0.5
    assert policy.summarize([]) == {"calls": 0, "paths": {p: 0 for p in policy.PATHS},
                                    "llm_coverage": None, "fallback_rate": None}
