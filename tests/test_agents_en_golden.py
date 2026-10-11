"""The English output of the text-writing agents does not change when the text moves to a
catalog (P0.12-D). The golden file was captured from the agents before the refactor, over
thirteen matchups that cover every branch: demo, live, limited and debut arsenals, different
scopes, missing putaway pitch, unavailable season figures, offense splits.

If the English text is changed on purpose, regenerate the file in the same commit and say so.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.golden_scenarios import agent_outputs, scenarios

GOLDEN = Path(__file__).parent / "fixtures" / "agents_en_golden.json"


@pytest.fixture(scope="module")
def golden() -> dict:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def _roundtrip(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def test_every_scenario_is_in_the_golden_file(monkeypatch, golden):
    assert set(scenarios(monkeypatch)) == set(golden)


@pytest.mark.parametrize("name", list(json.loads(GOLDEN.read_text(encoding="utf-8"))))
def test_english_output_is_unchanged(monkeypatch, golden, name):
    matchup = scenarios(monkeypatch)[name]

    assert _roundtrip(agent_outputs(matchup)) == golden[name]
