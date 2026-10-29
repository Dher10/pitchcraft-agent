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
