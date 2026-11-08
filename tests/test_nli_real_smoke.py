"""A real CPU smoke of the pinned NLI in the isolated environment. Skipped where the venv or the verified cache is absent (CI, other machines)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents import nli_cache

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".local" / "nli-venv" / "Scripts" / "python.exe"
CACHE = ROOT / ".local" / "nli-cache"

pytestmark = pytest.mark.skipif(not PYTHON.exists() or not CACHE.exists(), reason="the isolated NLI environment is not provisioned here")


def test_the_cache_is_the_pinned_revision_and_the_worker_scores_entailment_and_contradiction():
    assert nli_cache.verify_cache(CACHE)
    pairs = [
        ("Kyle Freeland has an earned run average (ERA) of 8.08 over the 2026 regular season through May 31.", "Kyle Freeland carries an 8.08 ERA."),
        ("Kyle Freeland has an earned run average (ERA) of 8.08 over the 2026 regular season through May 31.", "Kyle Freeland carries a 2.65 ERA."),
        ("The Los Angeles Angels lineup has an on-base plus slugging (OPS) of .712 against left-handed pitchers.", "The Colorado Rockies lineup has a .712 OPS against left-handed pitchers."),
    ]

    values = nli_cache.scores(CACHE, pairs, python=PYTHON, timeout=240)

    assert values is not None and values[0] > 0.9 and values[1] < 0.2 and values[2] < 0.2


def test_the_system_interpreter_has_no_torch_so_the_worker_fails_closed():
    assert nli_cache.scores(CACHE, [("a premise", "a sentence")], python=None, timeout=60) is None
