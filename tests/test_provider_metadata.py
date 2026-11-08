"""Synthetic wire responses; never uses a credential or a provider."""
import io
import urllib.error

import pytest

from agents import model_transport as transport


class Response(io.BytesIO):
    status = 200
    headers = {
        "x-ratelimit-limit-requests": "1000",
        "x-ratelimit-remaining-tokens": "7990",
        "retry-after": "60",
        "authorization": "SECRET-SENTINEL",
        "x-ratelimit-limit-tokens": "SECRET-SENTINEL",
    }


def test_metadata_is_opt_in_closed_numeric_and_payload_repr_is_hidden(monkeypatch):
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open",
                        lambda *a, **k: Response(b'{"text":"SECRET-SENTINEL"}'))
    result = transport.post_json("groq", "m", {}, api_key="sentinel", with_metadata=True)
    assert result.status == 200
    assert result.body == {"text": "SECRET-SENTINEL"}
    assert result.rate == {"x-ratelimit-limit-requests": 1000,
                           "x-ratelimit-remaining-tokens": 7990, "retry-after": 60}
    assert "SECRET-SENTINEL" not in repr(result)


@pytest.mark.parametrize("status", (401, 403, 429, 500, 302))
def test_http_errors_keep_only_status_and_closed_rate_metadata(status, monkeypatch, capsys):
    def fail(*a, **k):
        raise urllib.error.HTTPError("https://secret.invalid/SECRET-SENTINEL", status,
                                     "SECRET-SENTINEL", Response.headers,
                                     io.BytesIO(b'{"error":"SECRET-SENTINEL"}'))
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", fail)
    result = transport.post_json("groq", "m", {}, api_key="sentinel", with_metadata=True)
    assert result.status == status
    assert result.body is None
    assert result.rate["retry-after"] == 60
    assert "SECRET-SENTINEL" not in repr(result)
    assert capsys.readouterr() == ("", "")


# Synthetic stand-in for a newer AI Studio auth-key shape: 53 printable ASCII
# characters with a dot and no AIza prefix. Not a real key.
NEW_SHAPE_KEY = "AQ.Ab8RN6" + "x" * 44


def test_new_key_shape_goes_only_in_header_never_in_url(monkeypatch):
    seen = []
    def capture(opener, request, timeout=None):
        seen.append(request)
        return Response(b'{}')
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", capture)
    assert len(NEW_SHAPE_KEY) == 53
    transport.post_json("gemini", "gemini-3.8-flash", {}, api_key=NEW_SHAPE_KEY, with_metadata=True)
    assert seen[0].get_header("X-goog-api-key") == NEW_SHAPE_KEY
    assert NEW_SHAPE_KEY not in seen[0].full_url and "key=" not in seen[0].full_url


def test_default_python_user_agent_is_never_sent(monkeypatch):
    # Cloudflare in front of api.groq.com rejects "Python-urllib/x" with a 403 (error 1010)
    # before authentication; a fixed product user-agent reaches the API.
    seen = []
    def capture(opener, request, timeout=None):
        seen.append(request)
        return Response(b'{}')
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", capture)
    for provider in ("gemini", "groq"):
        transport.post_json(provider, "m", {}, api_key="sentinel", with_metadata=True)
    agents = {r.get_header("User-agent") for r in seen}
    assert agents == {transport.USER_AGENT} and transport.USER_AGENT.startswith("pitchcraft-agent/")
    assert "python" not in transport.USER_AGENT.lower()


@pytest.mark.parametrize("error,kind", (
    (urllib.error.URLError("SECRET-SENTINEL"), "other"),
    (urllib.error.URLError(TimeoutError("SECRET-SENTINEL")), "timeout"),
    (TimeoutError("SECRET-SENTINEL"), "timeout"),
    (ConnectionResetError("SECRET-SENTINEL"), "other")))
def test_failure_before_any_http_status_is_connection_failed_with_a_kind(error, kind, monkeypatch):
    def fail(*a, **k):
        raise error
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", fail)
    with pytest.raises(transport.ConnectionFailed) as raised:
        transport.post_json("groq", "m", {}, api_key="sentinel", with_metadata=True)
    assert isinstance(raised.value, transport.ProviderRejected)
    assert isinstance(raised.value, transport.ConnectionTimeout) == (kind == "timeout")
    assert raised.value.__cause__ is None and "SENTINEL" not in repr(raised.value)


def test_failures_with_a_status_or_before_sending_are_not_connection_failed(monkeypatch):
    class Broken(Response):
        def read(self, *a):
            raise TimeoutError("SECRET-SENTINEL")
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", lambda *a, **k: Broken(b''))
    with pytest.raises(transport.ProviderRejected) as raised:
        transport.post_json("groq", "m", {}, api_key="sentinel", with_metadata=True)
    assert type(raised.value) is transport.ProviderRejected
    with pytest.raises(transport.ProviderRejected) as raised:
        transport.post_json("groq", "m", {}, api_key="has space", with_metadata=True)
    assert type(raised.value) is transport.ProviderRejected


@pytest.mark.parametrize("raw", (b'{"a":1,"a":2}', b'{"nested":{"a":1,"a":2}}'))
def test_duplicate_keys_fail_closed(raw, monkeypatch):
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open",
                        lambda *a, **k: Response(raw))
    with pytest.raises(transport.ProviderRejected):
        transport.post_json("groq", "m", {}, api_key="sentinel")


@pytest.mark.parametrize("value,expected", (("2m59.56s", 179560), ("7.66s", 7660), ("0s", 0), ("SECRET-SENTINEL", None)))
def test_reset_headers_are_normalized_milliseconds_or_discarded(value, expected, monkeypatch):
    response = Response(b'{}')
    response.headers = {"x-ratelimit-reset-tokens": value}
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", lambda *a, **k: response)
    result = transport.post_json("groq", "m", {}, api_key="sentinel", with_metadata=True)
    assert result.rate.get("x-ratelimit-reset-tokens") == expected


@pytest.mark.parametrize("timeout,ok", ((120, True), (60, True), (120.5, False), (0, False)))
def test_timeout_bound_is_120_seconds(monkeypatch, timeout, ok):
    seen = []

    def capture(opener, request, timeout=None):
        seen.append(timeout)
        raise OSError()
    monkeypatch.setattr(transport.urllib.request.OpenerDirector, "open", capture)
    with pytest.raises(transport.ProviderRejected) as raised:
        transport.post_json("gemini", "gemini-3.5-flash", {}, api_key=NEW_SHAPE_KEY, timeout=timeout)
    assert (seen == [timeout]) == ok and isinstance(raised.value, transport.ConnectionFailed) == ok
