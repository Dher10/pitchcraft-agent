"""Private, bounded, single-writer append ledger. Never stores wire payloads."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import json
import math
import os
from pathlib import Path
import re
import stat

from agents.model_transport import RATE_FIELDS
from evals.provider_protocol import MODELS, RESERVATION, canonical, digest, _pairs


# "connection_failed" is kept so generation 2's recorded row stays readable.
NO_STATUS_CODES = ("key_unavailable", "connection_failed", "connection_failed_timeout", "connection_failed_other")


def reject():
    raise ValueError("request_failed") from None


def protect(path):
    """Fail before writing evidence if owner/System/admin-only ACL cannot be set."""
    if os.name != "nt":
        path.chmod(0o700 if path.is_dir() else 0o600)
        return
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = adv.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    apply = adv.SetFileSecurityW
    apply.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    apply.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    descriptor = ctypes.c_void_p()
    # Protected DACL; inherited full access only to owner, SYSTEM, administrators.
    if not convert("D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)", 1, ctypes.byref(descriptor), None):
        reject()
    try:
        if not apply(str(path), 0x80000004, descriptor):
            reject()
    finally:
        kernel.LocalFree(descriptor)


def regular(path, directory=False):
    info = path.lstat()
    if path.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
        reject()
    if not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)):
        reject()
    if not directory and info.st_nlink != 1:
        reject()
    return info


def validate_result(value):
    expected = {"event", "code", "http_status", "input_tokens", "output_tokens", "reasoning_tokens", "total_tokens", "fingerprint_digest", "output_digest", "rate"}
    if type(value) is not dict or set(value) != expected:
        reject()
    if value["event"] not in ("accepted", "rejected") or value["code"] not in (None, "request_failed", "malformed_response", "budget_spent") + NO_STATUS_CODES:
        reject()
    # These codes cannot have an HTTP status: nothing was sent, or nothing came back.
    if value["code"] in NO_STATUS_CODES and value["http_status"] is not None:
        reject()
    for key in ("input_tokens", "output_tokens", "reasoning_tokens", "total_tokens"):
        if value[key] is not None and (type(value[key]) is not int or not 0 <= value[key] <= RESERVATION):
            reject()
    if value["http_status"] is not None and (type(value["http_status"]) is not int or not 100 <= value["http_status"] <= 599):
        reject()
    for key in ("fingerprint_digest", "output_digest"):
        if value[key] is not None and (type(value[key]) is not str or re.fullmatch(r"[0-9a-f]{64}", value[key]) is None):
            reject()
    rates = value["rate"]
    if type(rates) is not dict or set(rates) - RATE_FIELDS or any(type(n) is not int or not 0 <= n <= 999999999 for n in rates.values()):
        reject()
    if value["event"] == "accepted":
        if value["code"] is not None or value["http_status"] != 200 or value["total_tokens"] is None or value["output_digest"] != digest({"ok": True}):
            reject()
    elif value["code"] is None:
        reject()


def read_ledger(path):
    if not path.exists():
        return []
    if regular(path).st_size > 64000:
        reject()
    raw = path.read_text(encoding="utf-8")
    if raw and not raw.endswith("\n"):
        reject()
    rows, previous, pending, providers = [], "0" * 64, None, set()
    for line in raw.splitlines():
        row = json.loads(line, object_pairs_hook=_pairs)
        if type(row) is not dict or set(row) != {"kind", "identity", "at", "reserved_tokens", "result", "previous", "digest"}:
            reject()
        if row["previous"] != previous or digest({k: v for k, v in row.items() if k != "digest"}) != row["digest"]:
            reject()
        identity = row["identity"]
        if type(identity) is not dict or set(identity) != {"request_digest", "commit", "dirty_digest", "provider", "model", "body_digest", "protocol_digest", "guide_digest", "prompt_digest", "schema_digest", "evaluator_digest", "input_digest"}:
            reject()
        if identity["provider"] not in MODELS or identity["model"] != MODELS[identity["provider"]]:
            reject()
        for key, value in identity.items():
            if key not in ("provider", "model") and (type(value) is not str or re.fullmatch(r"[0-9a-f]{" + ("40" if key == "commit" else "64") + "}", value) is None):
                reject()
        if identity["request_digest"] != digest({k: v for k, v in identity.items() if k != "request_digest"}):
            reject()
        if type(row["at"]) not in (int, float) or not math.isfinite(row["at"]) or row["at"] < 0 or row["reserved_tokens"] != RESERVATION:
            reject()
        if rows and row["at"] < rows[-1]["at"]:
            reject()
        if row["kind"] == "reserve":
            if pending is not None or identity["provider"] in providers or row["result"] is not None:
                reject()
            pending = identity
            providers.add(identity["provider"])
        elif row["kind"] == "result":
            if pending != identity:
                reject()
            validate_result(row["result"])
            pending = None
        else:
            reject()
        rows.append(row)
        previous = row["digest"]
    return rows


def append(path, rows, kind, identity, at, result=None):
    if result is not None:
        validate_result(result)
    row = {"kind": kind, "identity": identity, "at": at, "reserved_tokens": RESERVATION,
           "result": result, "previous": rows[-1]["digest"] if rows else "0" * 64}
    row["digest"] = digest(row)
    if path.exists():
        regular(path)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        protect(path)
        handle.write(canonical(row) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    rows.append(row)


@contextmanager
def locked(directory):
    directory = Path(directory).absolute()
    # Reject redirected parents too, before mkdir/open.
    for parent in (*reversed(directory.parents), directory):
        if parent.exists():
            regular(parent, directory=True)
    directory.mkdir(parents=True, exist_ok=True)
    regular(directory, directory=True)
    protect(directory)
    if set(p.name for p in directory.iterdir()) - {"ledger.jsonl"}:
        reject()
    lock = directory / "runner.lock"
    descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        protect(lock)
        yield directory / "ledger.jsonl"
    finally:
        os.close(descriptor)
        lock.unlink()
