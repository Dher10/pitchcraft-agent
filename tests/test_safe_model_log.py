"""No arbitrary text can enter a model attempt log or its rejection."""
import importlib
import json

import pytest


def record():
    return dict(provider="gemini", event="rejected", code="malformed_response",
                attempt=1, input_tokens=0, output_tokens=None, request_digest="a" * 64)


def test_control_safe_record_preserves_zero_and_unavailable():
    log = importlib.import_module("agents.safe_model_log")
    result = json.loads(log.encode_record(**record()))
    assert result == record()


@pytest.mark.parametrize("field", tuple(record()) + ("message", "headers", "prompt", "error"))
def test_sentinels_never_reach_any_log_or_exception(field, capsys, caplog):
    log = importlib.import_module("agents.safe_model_log")
    data = record()
    data[field] = "SECRET-SENTINEL-DO-NOT-EXPORT"
    with pytest.raises(ValueError) as caught:
        log.encode_record(**data)
    assert "SECRET-SENTINEL" not in str(caught.value)
    assert "SECRET-SENTINEL" not in repr(caught.value)
    captured = capsys.readouterr()
    assert captured.out == captured.err == caplog.text == ""


@pytest.mark.parametrize("field,value", (("attempt", True), ("attempt", 3),
    ("input_tokens", float("inf")), ("output_tokens", -1), ("request_digest", "A" * 64)))
def test_rejects_bad_counts_and_noncanonical_digest(field, value):
    log = importlib.import_module("agents.safe_model_log")
    data = record()
    data[field] = value
    with pytest.raises(ValueError):
        log.encode_record(**data)
