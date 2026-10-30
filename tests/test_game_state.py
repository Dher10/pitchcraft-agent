"""The state of a game comes from the schedule (P0.15-D2.5a, F5, rule 7; schema 0.8.0, D40).

At HEAD every live matchup said `status: "upcoming"` and `lineup_status: "probable_pitchers"` whatever the schedule said.
Measured on 2026-10-16 (D16, one request over 208 games): a game that was postponed or cancelled arrives with
`abstractGameState` "Final" and the truth in `detailedState` ("Postponed", "Cancelled"), so "Final" alone never means that
the game was played. One table turns the pair (`abstractGameState`, `detailedState`) into the published status
(`upcoming`, `live`, `final`) and anything it does not list, a missing value included, into `null`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from data_pipeline import provenance
from data_pipeline.contract_checks import check_contract
from data_pipeline.schema import (
    GAME_STATUS,
    SCHEMA_VERSION,
    STATE_OF_STATUS,
    game_status,
    lineup_status_of,
    snapshot_matches_schema,
)
from tests.corpus import build, published
from tests.live_helpers import failed_checks
from tests.matrix import HARD_CASES, hard_outcome
from tests.test_live_game_time import fetch_game

REAL = json.loads((Path(__file__).parent / "fixtures" / "mlb_schedule_states_2026-09.json").read_text(encoding="utf-8"))["games"]


def codes(payload) -> set[str]:
    return {violation.code for violation in check_contract(published(payload))}


# --- the schema ------------------------------------------------------------------------------------------------------


def test_the_schema_is_0_8_0_and_a_snapshot_of_0_7_0_is_not_read():
    assert SCHEMA_VERSION == "0.10.0"
    assert snapshot_matches_schema("0.10.0") and not snapshot_matches_schema("0.9.0") and not snapshot_matches_schema("0.8.0") and not snapshot_matches_schema("0.7.0")


# --- the table -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "abstract, detailed, status",
    [
        ("Preview", "Scheduled", "upcoming"),
        ("Preview", "Pre-Game", "upcoming"),
        ("Live", "In Progress", "live"),
        ("Final", "Final", "final"),
        ("Final", "Game Over", "final"),
        ("Final", "Completed Early", "final"),
        # what the real schedule sent for a game that was not played (2026-09-22 and 2026-09-27): "Final" is not enough
        ("Final", "Postponed", None),
        ("Final", "Cancelled", None),
        ("Final", "Suspended", None),
        # anything the table does not list, and a missing part, is unknown: never upcoming, never final
        ("Preview", "Postponed", None),
        ("Live", "Suspended", None),
        ("Preview", None, None),
        ("Final", None, None),
        (None, "Final", None),
        (None, None, None),
        ("Scheduled", "Scheduled", None),
        ("Preview", "Something New", None),
        ("final", "final", None),
        (1, 2, None),
    ],
)
def test_the_table_turns_the_pair_into_a_status_or_null(abstract, detailed, status):
    assert game_status(abstract, detailed) == status


def test_the_table_has_only_the_pairs_the_owner_named_or_the_real_answers_showed():
    assert dict(GAME_STATUS) == {
        ("Preview", "Scheduled"): "upcoming",
        ("Preview", "Pre-Game"): "upcoming",
        ("Live", "In Progress"): "live",
        ("Final", "Final"): "final",
        ("Final", "Game Over"): "final",
        ("Final", "Completed Early"): "final",
    }


def test_the_registry_reads_the_same_table_the_generator_writes():
    assert STATE_OF_STATUS == {"upcoming": "Preview", "live": "Live", "final": "Final"}


@pytest.mark.parametrize("status, lineup", [("upcoming", "probable_pitchers"), ("live", "game_started"), ("final", "game_started"), (None, None)])
def test_the_lineup_status_follows_the_status(status, lineup):
    assert lineup_status_of(status) == lineup


# --- the real answers, through the fetcher ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kind, detail, status",
    [("final", "Final", "final"), ("postponed", "Postponed", None), ("cancelled", "Cancelled", None)],
)
def test_a_real_game_keeps_its_detailed_state_and_is_never_final_when_it_was_not_played(monkeypatch, kind, detail, status):
    games, _ = fetch_game(monkeypatch, {"dates": [{"games": [REAL[kind]]}]})

    [game] = games
    assert game["status"] == "Final"  # all three arrive as Final
    assert game["detailed_state"] == detail
    assert game_status(game["status"], game["detailed_state"]) == status


# --- the published matchup, through the real pipeline ----------------------------------------------------------------

EXPECTED = {
    "two_debuts": ("upcoming", "probable_pitchers"),  # control: a Preview game, as before
    "live_state_live": ("live", "game_started"),
    "live_state_final": ("final", "game_started"),
    "live_state_postponed": (None, None),
    "live_state_cancelled": (None, None),
    "live_state_suspended": (None, None),
    "live_state_missing": (None, None),
    "live_state_unknown": (None, None),
}


def test_the_hard_cases_of_the_state_exist():
    assert set(EXPECTED) - {"two_debuts"} <= set(HARD_CASES)


@pytest.mark.parametrize("name", EXPECTED)
def test_the_published_status_and_lineup_status_follow_the_schedule(name):
    outcome = hard_outcome(name)

    assert outcome.payload is not None and outcome.live, name
    matchup = outcome.payload["matchups"][0]
    assert (matchup["status"], matchup["data_confidence"]["lineup_status"]) == EXPECTED[name]
    assert outcome.failed == [], outcome.failed


@pytest.mark.parametrize("name", [n for n in EXPECTED if n != "two_debuts"])
def test_a_live_matchup_is_never_upcoming_by_default(name):
    matchup = hard_outcome(name).payload["matchups"][0]

    assert matchup["status"] != "upcoming"


def test_a_live_game_that_is_final_keeps_its_pregame_report_and_has_no_postgame():
    """Rule 7: the postgame stays null until the daily postgame exists; a live final game has no box score to grade."""

    payload = hard_outcome("live_state_final").payload

    assert payload["matchups"][0]["status"] == "final" and payload["matchups"][0]["postgame"] is None
    assert payload["matchups"][0]["report"]["headline"]
    steps = {step["agent"]: step for step in payload["agent_workflow"]["steps"]}
    assert steps["Postgame Grader Agent"]["status"] == "not_applicable"


# --- the manifest ----------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def live():
    with pytest.MonkeyPatch.context() as monkeypatch:
        return published(build(monkeypatch, "live_complete"))


def manifest_codes(payload) -> set[str]:
    return {code for code, _, _ in provenance.findings(payload)}


def test_a_generated_live_file_has_no_finding_about_status(live):
    assert live["matchups"][0]["status"] == "upcoming"
    assert not {c for c in manifest_codes(live) if c.endswith("matchups[].status") or c.endswith("matchups[].data_confidence.lineup_status")}


@pytest.mark.parametrize(
    "status, lineup, code",
    [
        ("upcoming", "game_started", "rule1:derivation_mismatch#matchups[].data_confidence.lineup_status"),
        ("final", "probable_pitchers", "rule1:derivation_mismatch#matchups[].data_confidence.lineup_status"),
        ("live", None, "rule1:derivation_mismatch#matchups[].data_confidence.lineup_status"),
        (None, "probable_pitchers", "rule1:derivation_mismatch#matchups[].data_confidence.lineup_status"),
        ("sometime", "probable_pitchers", "rule1:wrong_type#matchups[].status"),
        ("Final", "game_started", "rule1:wrong_type#matchups[].status"),
        ("demo", "probable_pitchers", "rule1:wrong_type#matchups[].status"),
    ],
)
def test_a_status_and_a_lineup_status_that_disagree_or_are_not_in_the_set_are_found(live, status, lineup, code):
    payload = deepcopy(live)
    payload["matchups"][0]["status"] = status
    payload["matchups"][0]["data_confidence"]["lineup_status"] = lineup

    assert code in manifest_codes(payload)


@pytest.mark.parametrize("status, lineup", [("live", "game_started"), ("final", "game_started"), (None, None), ("upcoming", "probable_pitchers")])
def test_a_status_and_a_lineup_status_that_agree_are_clean(live, status, lineup):
    payload = deepcopy(live)
    payload["matchups"][0]["status"] = status
    payload["matchups"][0]["data_confidence"]["lineup_status"] = lineup

    assert not {c for c in manifest_codes(payload) if c.endswith("matchups[].status") or c.endswith("lineup_status")}


def test_a_demo_final_matchup_still_needs_its_box_score(monkeypatch):
    """The control of the loosened validator: only a LIVE final game may have no postgame; a demo one must have it."""

    demo = published(build(monkeypatch, "demo"))
    final = next(m for m in demo["matchups"] if m["status"] == "final")
    assert final["data_confidence"]["level"] != "fetched_snapshot" and failed_checks(demo) == []
    final["postgame"] = None

    assert any("final matchup includes postgame.starter_lines" in d for d in failed_checks(demo))


def test_a_status_in_a_demo_file_is_not_asked(monkeypatch):
    demo = published(build(monkeypatch, "demo"))

    assert {m["status"] for m in demo["matchups"]} == {"upcoming", "final"}
    assert failed_checks(demo) == []
