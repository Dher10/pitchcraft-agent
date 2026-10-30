"""Pinned offline CPU NLI worker. Unconfigured calibration always rejects.

Not connected to publication in P2-SEC. No downloads or model-controlled code.
Real cache/CPU smoke and dev calibration remain prerequisites for admission.
"""
from __future__ import annotations

import hashlib
from importlib import metadata
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys

MANIFEST = json.loads(Path(__file__).with_name("nli_manifest.json").read_text(encoding="utf-8"))
LOCK = Path(__file__).resolve().parents[1] / "requirements-nli-windows.txt"


class NliRejected(ValueError):
    def __init__(self):
        super().__init__("request_failed")


def identity():
    # Code/fact renderer/lock changes invalidate an old calibration too.
    digest = hashlib.sha256(json.dumps(MANIFEST, sort_keys=True).encode())
    root = Path(__file__).resolve().parents[1]
    for path in (Path(__file__), root/"data_pipeline/prompt_boundary.py", root/"agents/security_instructions.json", LOCK):
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise NliRejected()
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(NliRejected()))


def _safe_file(path, *, directory=False):
    info = path.lstat()
    if path.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
        raise NliRejected()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        raise NliRejected()
    return info


def _tensor_header(path):
    with path.open("rb") as handle:
        size = struct.unpack("<Q", handle.read(8))[0]
        if not 2 <= size <= 8_000_000:
            raise NliRejected()
        header = _json(handle.read(size))
    available = path.stat().st_size - 8 - size
    spans = []
    for key, tensor in header.items():
        if key == "__metadata__":
            continue
        width = {"F32":4, "I64":8}.get(tensor["dtype"])
        shape, offsets = tensor["shape"], tensor["data_offsets"]
        if width is None or type(shape) is not list or len(shape) > 8 or any(type(n) is not int or not 0 <= n <= 1_000_000 for n in shape):
            raise NliRejected()
        if type(offsets) is not list or len(offsets) != 2 or any(type(n) is not int for n in offsets):
            raise NliRejected()
        start, end = offsets
        if not 0 <= start <= end <= available or end-start != math.prod(shape)*width:
            raise NliRejected()
        spans.append((start,end))
    spans.sort()
    if not spans or spans[0][0] != 0 or spans[-1][1] != available or any(a[1]!=b[0] for a,b in zip(spans,spans[1:])):
        raise NliRejected()


def verify_cache(directory):
    try:
        directory = Path(directory).absolute()
        _safe_file(directory, directory=True)
        files = MANIFEST["files"]
        if not re.fullmatch(r"[0-9a-f]{40}", MANIFEST["revision"]) or set(p.name for p in directory.iterdir()) != set(files):
            raise NliRejected()
        if "model.safetensors" not in files:
            raise NliRejected()
        for name, expected in files.items():
            if name != Path(name).name or name.endswith((".bin", ".py", ".pkl")):
                raise NliRejected()
            path = directory/name
            info = _safe_file(path)
            if info.st_size != expected["size"] or info.st_size > 600_000_000:
                raise NliRejected()
            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1_048_576), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected["sha256"]:
                raise NliRejected()
        config = _json((directory/"config.json").read_bytes())
        tokenizer = _json((directory/"tokenizer_config.json").read_bytes())
        for value in (config, tokenizer):
            if any(key in value for key in ("auto_map", "custom_pipelines", "_auto_class", "trust_remote_code")):
                raise NliRejected()
        if config["model_type"] != "deberta-v2" or config["architectures"] != ["DebertaV2ForSequenceClassification"]:
            raise NliRejected()
        if config["id2label"] != {"0":"contradiction", "1":"entailment", "2":"neutral"}:
            raise NliRejected()
        if config["max_position_embeddings"] != 512 or tokenizer["model_max_length"] != 512:
            raise NliRejected()
        _tensor_header(directory/"model.safetensors")
        return directory.resolve()
    except Exception:
        raise NliRejected() from None


def _pairs_valid(pairs):
    return type(pairs) is list and 1 <= len(pairs) <= 32 and all(
        type(pair) in (list,tuple) and len(pair)==2 and all(type(t) is str and 0 < len(t) <= cap
        for t,cap in zip(pair,(2400,300))) for pair in pairs)


def checked_tokens(tokenizer, premise, sentence):
    tokens = tokenizer(premise, sentence, truncation=False, return_tensors="pt")
    if tokens["input_ids"].shape[1] > MANIFEST["max_tokens"]:
        raise NliRejected()
    return tokens


def _worker_python(python):
    """The interpreter of the isolated NLI environment: an explicit regular file, never taken from the environment."""

    if python is None:
        return sys.executable
    path = Path(python).absolute()
    _safe_file(path)
    if path.name.lower() != "python.exe" and path.name != "python":
        raise NliRejected()
    return str(path)


def _run_worker(directory, pairs, python, timeout, limit=600):
    """Entailment probabilities from the disposable worker, or None on any failure."""

    try:
        if not _pairs_valid(pairs) or type(timeout) not in (float, int) or not 0 < timeout <= limit:
            return None
        path = verify_cache(directory)
        interpreter = _worker_python(python)
        env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH", "TEMP", "TMP") if key in os.environ}
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", TOKENIZERS_PARALLELISM="false")
        result = subprocess.run([interpreter, "-I", str(Path(__file__).resolve()), "--worker"],
            input=json.dumps({"cache":str(path), "pairs":pairs, "identity":identity()}),
            text=True, encoding="utf-8", capture_output=True, timeout=timeout, env=env)
        if result.returncode != 0 or len(result.stdout) > 4096:
            return None
        values = _json(result.stdout)
        if type(values) is list and len(values) == len(pairs) and all(type(v) in (float, int) and math.isfinite(v) and 0 <= v <= 1 for v in values):
            return [float(v) for v in values]
        return None
    except Exception:
        return None


def scores(directory, pairs, *, python=None, timeout=60):
    """Raw entailment probabilities for (premise, sentence) pairs, or None on any failure.

    For calibration and evidence only: a score is never an admission (see `entails`, which needs a calibrated threshold)."""

    return _run_worker(directory, pairs, python, timeout)


def entails(directory, pairs, *, calibration=None, timeout=30, python=None):
    """Internal primitive; calibration must be an explicitly supplied dev artifact.

    It never reads a threshold or credential from environment/files implicitly.
    No fake/test threshold enables publication: this is not wired into it.
    """
    try:
        if type(calibration) is not dict or set(calibration) != {"threshold", "identity"}:
            return False
        threshold = calibration["threshold"]
        if type(threshold) not in (float,int) or not math.isfinite(threshold) or not 0 < threshold <= 1 or calibration["identity"] != identity():
            return False
        values = _run_worker(directory, pairs, python, timeout, limit=120)  # entails keeps its original 120 s bound
        return values is not None and all(threshold <= value <= 1 for value in values)
    except Exception:
        return False


def _worker():
    request = _json(sys.stdin.buffer.read(65_537))
    if request["identity"] != identity() or not _pairs_valid(request["pairs"]):
        raise NliRejected()
    path = verify_cache(request["cache"])
    for package, version in MANIFEST["runtime"].items():
        if metadata.version(package) != version:
            raise NliRejected()
    # Check the complete optional lock, not only the four direct imports.
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith(("#", "https://")):
            continue
        package, version = line.split("==")
        if metadata.version(package) != version:
            raise NliRejected()
    import torch
    from transformers import DebertaV2ForSequenceClassification, DebertaV2Tokenizer
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    tokenizer = DebertaV2Tokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False)
    model = DebertaV2ForSequenceClassification.from_pretrained(str(path), local_files_only=True,
        trust_remote_code=False, use_safetensors=True, dtype=torch.float32).to("cpu").eval()
    values = []
    with torch.inference_mode():
        for premise, sentence in request["pairs"]:
            tokens = checked_tokens(tokenizer, premise, sentence)
            logits = model(**tokens).logits
            if tuple(logits.shape) != (1,3) or not bool(torch.isfinite(logits).all()):
                raise NliRejected()
            values.append(float(torch.softmax(logits,dim=-1)[0,1]))
    print(json.dumps(values, allow_nan=False))


if __name__ == "__main__":
    try:
        if sys.argv[1:] != ["--worker"]:
            raise NliRejected()
        _worker()
    except Exception:
        # No traceback/exception/prompt/secret output even from optional runtimes.
        sys.exit(1)
