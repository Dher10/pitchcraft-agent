"""CI validates the JSON the app actually serves (QA-01).

`lib/data.ts` reads public/data/pitchcraft-demo.json. These invariants hold for whatever
the generator (or the daily bot) writes there: live data carries no demo field, demo data
never says it is live, and the file passes the same validator as a fresh payload. They are
invariants, not a comparison with a regeneration, so a live file committed to main by the
bot passes them as well.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest

from data_pipeline.validators import ValidationError, validate_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVED = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"
MODES = {"demo_cached", "demo_fallback", "fetched_snapshot"}
SLOTS = ("away_starter", "home_starter")
PITCH_WORDS = re.compile(
    r"\b(four-seam|sinker|cutter|slider|changeup|curveball|splitter|sweeper|slurve|knuckleball)\b"
)


@pytest.fixture(scope="module")
def payload() -> dict:
    return json.loads(SERVED.read_text(encoding="utf-8"))


def live_matchups(payload: dict) -> list[dict]:
    return [
        m for m in payload["matchups"] if m["data_confidence"]["level"] == "fetched_snapshot"
    ]


def test_the_app_reads_the_file_these_tests_check():
    source = (REPO_ROOT / "lib" / "data.ts").read_text(encoding="utf-8")

    assert '"public", "data"' in source and '"pitchcraft-demo.json"' in source


def test_the_served_file_passes_the_validator(payload):
    try:
        validate_payload(payload)
    except ValidationError as exc:
        pytest.fail(str(exc))


def test_the_served_mode_is_one_the_generator_can_write(payload):
    assert payload["metadata"]["data_mode"] in MODES


def test_a_demo_file_never_says_it_is_live(payload):
    if payload["metadata"]["data_mode"] == "fetched_snapshot":
        pytest.skip("live file: covered by the live invariants")
    assert live_matchups(payload) == []
    assert "live data fetched" not in payload["metadata"]["last_updated_label"].lower()


def test_a_live_file_has_at_least_one_live_matchup_and_says_when(payload):
    if payload["metadata"]["data_mode"] != "fetched_snapshot":
        pytest.skip("demo file")
    assert live_matchups(payload)
    assert "live data fetched" in payload["metadata"]["last_updated_label"].lower()


def test_live_starters_carry_no_demo_field(payload):
    for matchup in live_matchups(payload):
        for slot in SLOTS:
            starter = matchup["starters"][slot]
            where = f"{matchup['id']} {starter['name']}"
            assert starter["bio"] is None, where
            assert starter["recent_form"] is None, where
            assert starter.get("sample"), where
            assert starter["season_summary"].get("scope"), where


def test_live_matchups_carry_no_demo_chart_note_or_record(payload):
    for matchup in live_matchups(payload):
        where = matchup["id"]
        assert matchup["charts"]["strength_profile"] == [], where
        assert matchup["game"]["broadcast_note"] is None, where
        for side in ("away", "home"):
            assert matchup["teams"][side]["record"] is None, where
            assert matchup["teams"][side]["offense_profile"].get("scope"), where
        assert "demo" not in json.dumps(matchup["game"]).lower(), where


def test_live_matchups_do_not_describe_pitches_that_are_not_in_their_mix(payload):
    for matchup in live_matchups(payload):
        mix = {row["pitch"].lower() for row in matchup["charts"]["pitch_mix"]}
        text = json.dumps(matchup["report"]).lower()
        for word in set(PITCH_WORDS.findall(text)):
            assert any(word in pitch for pitch in mix), f"{matchup['id']} names {word}"


def test_the_critic_claims_no_revision_and_no_unsupported_claim(payload):
    for matchup in payload["matchups"]:
        statuses = {c["status"] for c in matchup["critic_review"]["checks"]}
        assert not statuses & {"revised", "unsupported"}, matchup["id"]
    assert "revised" not in json.dumps(payload["agent_workflow"]).lower()


def test_unavailable_figures_are_shown_as_unavailable_not_as_numbers(payload):
    for matchup in payload["matchups"]:
        for slot in SLOTS:
            summary = matchup["starters"][slot]["season_summary"]
            for field in ("era", "whip", "innings"):
                value = summary[field]
                assert value == "N/A" or re.fullmatch(r"\d+(\.\d+)?", str(value)), (matchup["id"], field)
        assert not re.search(r"\bN/A\b", json.dumps(matchup["report"])), matchup["id"]


def test_the_reason_of_the_served_file_is_never_a_sentence(payload):
    """D39 (P0.15-D2.4b): a demo file with no live run says `{pipeline, no_live_run}`, not a sentence."""

    reason = payload["metadata"]["data_status"]["reason"]

    assert reason is None or (isinstance(reason, dict) and set(reason) == {"source", "code"}), reason


def test_a_live_served_file_describes_its_data_without_demo_wording(payload):
    # skipped while the served file is a demo one; the live case is covered by tests/test_live_file_neutral_text.py
    if payload["metadata"]["data_mode"] != "fetched_snapshot":
        pytest.skip("demo file: it keeps its demo wording")
    text = json.dumps([payload["disclaimers"], payload["metadata"]["data_sources"], payload["agent_workflow"]])

    assert not re.search(r"cached|capstone|demo|judging", text, re.IGNORECASE)
