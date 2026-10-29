"""The process seal of the test split (docs/plans/P2.4.md section 3, honest scope).

The test outputs live on this machine and in this repo, so the seal is a rule enforced by the one function that
opens them, not a cryptographic barrier. Dev tools, reports and labeling never open test outputs; the hashes are
always readable; the evaluation opens them only after a FROZEN file records the hash of exactly those files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

DEV_PURPOSES = ("dev_tool", "report", "label")
EVALUATION = "evaluation"
FROZEN = "FROZEN"


class Sealed(PermissionError):
    """The requested outputs are sealed for this purpose."""


def _files(root, split):
    return sorted(p for p in (Path(root) / split).glob("*.json") if p.is_file())


def hashes(root, split):
    """name -> SHA-256 of each output file. Safe for any caller: it reveals no content."""

    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in _files(root, split)}


def freeze_line(root):
    """What FROZEN must contain: the SHA-256 of the test files' names and hashes."""

    return hashlib.sha256(json.dumps(hashes(root, "test"), sort_keys=True).encode()).hexdigest() + "\n"


def read_outputs(root, split, purpose):
    if purpose not in DEV_PURPOSES + (EVALUATION,):
        raise ValueError(f"unknown purpose {purpose!r}")
    if split not in ("dev", "test"):
        raise ValueError(f"unknown split {split!r}")
    if split == "test":
        frozen = Path(root) / FROZEN
        if purpose != EVALUATION or not frozen.exists() or frozen.read_text(encoding="utf-8") != freeze_line(root):
            raise Sealed("the test outputs are sealed until the freeze, and only the evaluation opens them")
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in _files(root, split)}
