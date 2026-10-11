"""Shared fixtures.

The pitcher-hand cache lives under data_cache/raw; no test may read or write the real one.
"""

from __future__ import annotations

import sys

import pytest


@pytest.fixture(autouse=True)
def _isolated_pitcher_hand_cache(monkeypatch, tmp_path_factory):
    # Only tests that imported the live pipeline need it; the others never touch the cache.
    live_pipeline = sys.modules.get("data_pipeline.fetchers.live_pipeline")
    if live_pipeline is not None:
        monkeypatch.setattr(
            live_pipeline,
            "PITCHER_HAND_CACHE_DIR",
            tmp_path_factory.mktemp("pitcher_hand"),
            raising=False,
        )
        monkeypatch.setattr(live_pipeline, "_pitcher_hand_run", {"requests": 0}, raising=False)
