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

from data_pipeline.schema import READABLE_VERSIONS
from data_pipeline.validators import ValidationError, validate_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVED = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"
MODES = {"demo_cached", "demo_fallback", "fetched_snapshot"}
CACHING_NOTE = "Requests to the data sources are cached and the data is not downloaded in bulk."
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


def live_file_problem(payload: dict) -> str | None:
    """What is wrong with a live file's matchups: it has one, or its run record says there were no games."""

    if not live_matchups(payload):
        run = (payload["metadata"].get("data_status") or {}).get("live_run") or {}
        if not (run.get("status") == "no_games" and payload["matchups"] == []):
            return "a live file with no live matchup that is not a no_games run"
    if "live data fetched" not in payload["metadata"]["last_updated_label"].lower():
        return "a live file that does not say when its data was fetched"
    return None


def test_a_live_file_has_a_live_matchup_or_is_a_no_games_run_and_says_when(payload):
    if payload["metadata"]["data_mode"] != "fetched_snapshot":
        pytest.skip("demo file")
    assert live_file_problem(payload) is None


def test_the_served_file_is_valid_for_its_own_schema_version_whatever_its_content(payload):
    """The file is the bot's and changes on its own: a `no_games` run with 0 matchups is as valid as a game day."""

    assert payload["metadata"]["version"] in READABLE_VERSIONS
    validate_payload(payload)


def test_control_a_live_file_with_no_matchup_is_only_valid_as_a_no_games_run():
    no_games = {"metadata": {"last_updated_label": "Live data fetched 2026-10-30",
                             "data_status": {"live_run": {"status": "no_games"}}}, "matchups": []}
    assert live_file_problem(no_games) is None

    failed_run = {"metadata": {"last_updated_label": "Live data fetched 2026-10-30",
                               "data_status": {"live_run": {"status": "ok"}}}, "matchups": []}
    assert live_file_problem(failed_run) is not None

    no_date = {"metadata": {"last_updated_label": "Demo data", "data_status": {"live_run": {"status": "no_games"}}},
               "matchups": []}
    assert live_file_problem(no_date) is not None


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
    # The caching note says requests are cached; it is not the demo wording (P1.9; tests/test_live_file_neutral_text.py).
    notes = [n for n in payload["disclaimers"] if n != CACHING_NOTE]
    text = json.dumps([notes, payload["metadata"]["data_sources"], payload["agent_workflow"]])

    assert not re.search(r"cached|capstone|demo|judging", text, re.IGNORECASE)


def test_the_served_file_says_when_it_was_built_and_a_demo_file_never_says_it_was_fetched(payload):
    """Schema 0.7.0 (D39): `generated_at` is always a real instant; `data_fetched_at` is an instant in a live file, null otherwise."""

    from datetime import datetime

    metadata = payload["metadata"]
    assert datetime.fromisoformat(metadata["generated_at"]).tzinfo is not None
    assert metadata["generated_at"] != "2026-06-28T09:00:00-05:00"  # the demo's old constant
    if metadata["data_mode"] == "fetched_snapshot":
        assert datetime.fromisoformat(metadata["data_fetched_at"]).tzinfo is not None
    else:
        assert metadata["data_fetched_at"] is None
