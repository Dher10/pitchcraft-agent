"""NLI supply-chain controls using real local files and a tiny tensor fixture."""
import hashlib
import importlib
import json
from pathlib import Path
import struct
import time

import pytest


def nli():
    return importlib.import_module("agents.nli_cache")


@pytest.fixture
def cache(tmp_path, monkeypatch):
    module = nli()
    config = {"model_type": "deberta-v2", "architectures": ["DebertaV2ForSequenceClassification"],
              "id2label": {"0":"contradiction", "1":"entailment", "2":"neutral"}, "max_position_embeddings":512}
    header = json.dumps({"weight": {"dtype":"F32", "shape":[1], "data_offsets":[0,4]}}).encode()
    files = {"config.json": json.dumps(config).encode(), "tokenizer_config.json": b'{"model_max_length":512}',
             "tokenizer.json": b'{"version":"1.0"}', "model.safetensors": struct.pack("<Q",len(header))+header+b'\0'*4}
    manifest = {"repository":"fixture/nli", "revision":"a"*40, "license":"Apache-2.0",
                "max_tokens":512, "files":{}, "runtime":{}}
    for name, data in files.items():
        (tmp_path/name).write_bytes(data)
        manifest["files"][name] = {"size":len(data), "sha256":hashlib.sha256(data).hexdigest()}
    # Test-only trusted identity; production verify_cache has no caller-supplied manifest.
    monkeypatch.setattr(module, "MANIFEST", manifest)
    return tmp_path


def test_control_exact_regular_files_and_tensor_header(cache):
    module = nli()
    assert module.verify_cache(cache) == cache.resolve()


@pytest.mark.parametrize("kind", ("missing", "corrupt", "pickle", "extra", "remote_code", "labels", "truncated_tensor"))
def test_corrupt_unsupported_or_executable_cache_is_rejected_before_loading(cache, kind):
    module = nli()
    if kind == "missing": (cache/"tokenizer.json").unlink()
    elif kind == "corrupt": (cache/"tokenizer.json").write_bytes(b'changed')
    elif kind in ("pickle", "extra"): (cache/("pytorch_model.bin" if kind=="pickle" else "extra.py")).write_bytes(b'bad')
    else:
        name = "model.safetensors" if kind=="truncated_tensor" else "config.json"
        if kind=="truncated_tensor": data = struct.pack("<Q",1_000_000)+b'{}'
        else:
            value = json.loads((cache/name).read_text())
            value["auto_map" if kind=="remote_code" else "id2label"] = {"0":"evil"}
            data = json.dumps(value).encode()
        (cache/name).write_bytes(data)
        # A trusted manifest alone still cannot enable remote code/unsupported config.
        module.MANIFEST["files"][name] = {"size":len(data),"sha256":hashlib.sha256(data).hexdigest()}
    with pytest.raises(module.NliRejected, match="^request_failed$"):
        module.verify_cache(cache)


def test_missing_calibration_rejects_without_worker_or_download(cache, monkeypatch):
    module = nli()
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError("worker must not run")
    monkeypatch.setattr(module.subprocess, "run", forbidden)
    assert module.entails(cache, [("A verified fact.", "A sentence.")], calibration=None) is False
    assert calls == []


def test_timeout_is_a_bounded_disposable_worker_and_never_a_pass(cache, monkeypatch):
    module = nli()
    calls = []
    def timeout(*args, **kwargs):
        calls.append(kwargs)
        raise module.subprocess.TimeoutExpired(args[0], 0.1, output=b'SECRET-SENTINEL')
    monkeypatch.setattr(module.subprocess, "run", timeout)
    assert module.entails(cache, [("Fact.", "Sentence.")], calibration={"threshold":0.9, "identity":module.identity()}, timeout=0.1) is False
    assert len(calls) == 1
    assert calls[0]["timeout"] == 0.1
    assert calls[0]["capture_output"] is True
    assert set(calls[0]["env"]) <= {"SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "TOKENIZERS_PARALLELISM"}


@pytest.mark.parametrize("value", ([], [("x"*2401,"Sentence.")], [("Fact.","x"*301)], [("Fact.","Sentence.")]*33))
def test_oversize_or_empty_inputs_never_start_inference(cache, monkeypatch, value):
    module = nli()
    calls = []
    monkeypatch.setattr(module.subprocess, "run", lambda *a,**k: calls.append(a))
    assert module.entails(cache, value, calibration={"threshold":0.9,"identity":module.identity()}) is False
    assert calls == []


def test_tokenizer_never_silently_truncates(cache):
    module = nli()
    calls = []
    class Tensor:
        shape = (1, 513)
    def tokenizer(*args, **kwargs):
        calls.append(kwargs)
        return {"input_ids": Tensor()}
    with pytest.raises(module.NliRejected):
        module.checked_tokens(tokenizer, "Fact.", "Sentence.")
    assert calls == [{"truncation":False, "return_tensors":"pt"}]


def test_pinned_production_manifest_has_immutable_identity_and_no_pickle():
    manifest = json.loads((Path(__file__).parents[1]/"agents/nli_manifest.json").read_text())
    assert len(manifest["revision"]) == 40
    assert manifest["license"] == "Apache-2.0"
    assert "model.safetensors" in manifest["files"]
    assert all(not name.endswith((".bin", ".py", ".pkl")) for name in manifest["files"])
    assert all(len(item["sha256"])==64 and item["size"]>0 for item in manifest["files"].values())
