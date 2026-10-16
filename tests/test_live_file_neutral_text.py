"""A live file describes its data in neutral words, and a demo file keeps its demo wording (P0.15-D2.4b, F3, rule 6).

At HEAD a live file listed "Cached demo snapshots" among its sources, carried the demo's disclaimers ("a capstone demo",
"Cached demo data may be used ...") and its workflow said "Loaded cached data". Rule 6: the texts that describe the data
source say "cached" or "demo" only in a demo file. The expected strings are written out here, not imported, so a change
of the product's text is a change of a test.
"""

from __future__ import annotations

import json
import re

import pytest

from data_pipeline import config, generate_demo_json as gdj
from data_pipeline.contract_checks import RUN_ERROR_CODES, check_contract
from tests.corpus import build, published

LIVE_KINDS = ("live_complete", "live_debuts", "live_errors")
DEMO_KINDS = ("demo", "fallback")
DEMO_WORDS = re.compile(r"cached|capstone|demo|judging", re.IGNORECASE)

LIVE_DISCLAIMERS = [
    "Data from the MLB Stats API and Baseball Savant (Statcast). Not affiliated with MLB.",
    "For information only: no predictions and no betting advice.",
]


@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_a_live_file_carries_the_live_disclaimers_and_nothing_else(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert payload["disclaimers"] == LIVE_DISCLAIMERS


@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_a_live_file_lists_the_sources_it_uses_and_no_demo_source(monkeypatch, kind):
    sources = published(build(monkeypatch, kind))["metadata"]["data_sources"]

    assert sources and not any(DEMO_WORDS.search(source) for source in sources), sources
    assert any("MLB Stats API" in source for source in sources)
    assert any("Baseball Savant" in source for source in sources)


@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_nothing_a_live_file_says_about_its_data_is_a_demo_wording(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))
    text = json.dumps([payload["disclaimers"], payload["metadata"]["data_sources"], payload["agent_workflow"]])

    assert not DEMO_WORDS.search(text), DEMO_WORDS.search(text)


@pytest.mark.parametrize("kind", DEMO_KINDS)
def test_control_a_demo_file_keeps_its_demo_wording(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert any("Cached demo snapshots" in source for source in payload["metadata"]["data_sources"])
    assert "PitchCraft is a capstone demo and not a betting or gambling tool." in payload["disclaimers"]
    assert "Cached demo data may be used to ensure stable public evaluation." in payload["disclaimers"]


@pytest.mark.parametrize("kind", (*LIVE_KINDS, *DEMO_KINDS))
def test_the_first_step_of_the_workflow_says_it_loaded_data_not_cached_data(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert payload["agent_workflow"]["steps"][0]["output"] == f"Loaded data for {len(payload['matchups'])} matchups."


@pytest.mark.parametrize("kind", LIVE_KINDS)
def test_a_live_file_does_not_violate_rule_6_wording_or_the_manifest_on_its_texts(monkeypatch, kind):
    codes = {v.code for v in check_contract(published(build(monkeypatch, kind)))}

    assert "rule6:cached_wording" not in codes
    assert "rule4:generator.workflow.loaded#cached" not in codes
    assert "rule1:constant_asserts_fact#metadata.data_sources[]" not in codes


# --- the reason of a demo file with no live run ----------------------------------------------------------------------


def test_a_demo_file_for_a_day_with_no_live_run_says_why_as_a_source_and_a_code(isolated_run_record):
    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == config.DATA_MODE_DEMO
    assert status["reason"] == {"source": "pipeline", "code": "no_live_run"}


def test_no_live_run_is_a_code_of_the_closed_set():
    assert "no_live_run" in RUN_ERROR_CODES


@pytest.fixture
def isolated_run_record(tmp_path, monkeypatch):
    """No run record on disk: the cache directory is empty."""

    from data_pipeline.fetchers import cache_manager

    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path)
    return tmp_path
