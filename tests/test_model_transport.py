"""Fixed hosts, no redirects/tools, bounded JSON, no provider/network calls."""
import importlib
import io
import json
from unittest.mock import Mock

import pytest


def transport():
    return importlib.import_module("agents.model_transport")


@pytest.mark.parametrize("provider,host", (("gemini","generativelanguage.googleapis.com"),("groq","api.groq.com")))
def test_control_only_fixed_https_hosts_and_sentinel_safe_failure(provider, host, monkeypatch, capsys):
    module = transport()
    calls = []
    def open_request(opener, request, **kwargs):
        calls.append((request, kwargs))
        raise OSError("SECRET-SENTINEL raw provider error")
    monkeypatch.setattr(module.urllib.request.OpenerDirector, "open", open_request)
    with pytest.raises(module.ProviderRejected) as caught:
        module.post_json(provider, "verified-model", {"messages":[]}, api_key="SECRET-SENTINEL")
    assert len(calls) == 1
    assert calls[0][0].full_url.startswith("https://"+host+"/")
    assert "SECRET-SENTINEL" not in str(caught.value) + repr(caught.value)
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("provider,model,body", (
    ("https://attacker.invalid","m",{}), ("mistral","m",{}),
    ("gemini","../evil",{}), ("gemini","m",{"tools":[]}),
    ("groq","m",{"nested":{"function_call":"shell"}}),
    ("groq","m",{"value":float("nan")}), ("groq","m",{"value":"x"*65_000}),
))
def test_bad_destinations_tools_or_oversize_never_open(provider,model,body,monkeypatch):
    module = transport()
    calls=[]
    monkeypatch.setattr(module.urllib.request.OpenerDirector,"open",lambda *a,**k:calls.append(a))
    with pytest.raises(module.ProviderRejected):
        module.post_json(provider,model,body,api_key="SECRET-SENTINEL")
    assert calls==[]


def test_redirect_handler_never_forwards_credentials():
    module = transport()
    assert module.NoRedirect().redirect_request(None,None,302,"redirect",{},"https://attacker.invalid") is None


@pytest.mark.parametrize("raw", (b'{"ok":true}', b'{"x":NaN}', b'x'*131_073, b'not-json'), ids=("valid", "nan", "over-cap", "not-json"))
def test_bounded_response_parse_with_positive_control(raw,monkeypatch):
    module = transport()
    monkeypatch.setattr(module.urllib.request.OpenerDirector,"open",lambda *a,**k:io.BytesIO(raw))
    if raw==b'{"ok":true}':
        assert module.post_json("groq","m",{},api_key="sentinel")=={"ok":True}
    else:
        with pytest.raises(module.ProviderRejected):
            module.post_json("groq","m",{},api_key="sentinel")
