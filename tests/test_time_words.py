"""A time word carries its condition (P0.15-D2.5c, F16, rules 4 and 7).

At HEAD every report said "Today's Matchup Summary" and every live report ended its confidence note with "Lineups can
still change before first pitch.", whatever the state of the game and whenever the file is read. Now the title is the
neutral "Matchup Summary", and the sentence about the lineups is written only for a game whose state is Preview
(`status` `upcoming`). Nothing is promised about "today" or about a game that has not started in a file that is read
later, and a game in progress, a finished one or one whose state is unknown says nothing about its lineups.
"""

from __future__ import annotations

import json
import re

import pytest

from data_pipeline import claims_registry as registry
from data_pipeline.contract_checks import check_contract
from tests.corpus import GOLDEN_NAMES, KINDS, build, golden_payload, published
from tests.matrix import hard_outcome
from tests.test_game_state import EXPECTED

LINEUPS = "Lineups can still change before first pitch."
TIME_WORDS = re.compile(r"\b(today|tonight|upcoming|before first pitch)\b|\btoday's\b", re.IGNORECASE)


def text_of(matchup) -> str:
    """Every sentence the agents wrote for a matchup: the report and the confidence notes."""

    return json.dumps([matchup["report"], matchup["data_confidence"]["notes"]])


def section_titles(matchup) -> list[str]:
    return [section["title"] for section in matchup["report"]["sections"]]


# --- the title -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_the_summary_is_titled_matchup_summary_in_every_mode(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    for matchup in payload["matchups"]:
        assert section_titles(matchup)[0] == "Matchup Summary", (kind, matchup["id"])
        assert not any("today" in title.lower() for title in section_titles(matchup))


@pytest.mark.parametrize("name", GOLDEN_NAMES)
def test_no_golden_scenario_titles_a_section_with_today(monkeypatch, name):
    matchup = golden_payload(monkeypatch, name)["matchups"][0]

    assert "Matchup Summary" in section_titles(matchup)
    assert not any("today" in title.lower() for title in section_titles(matchup))


def test_the_title_asserts_nothing_so_no_rule_asks_a_state_of_it():
    assert registry.classify("writer.section.summary")[0] == "nothing"


# --- the sentence about the lineups ----------------------------------------------------------------------------------


@pytest.mark.parametrize("name, expected", EXPECTED.items())
def test_the_lineups_sentence_is_written_only_for_a_game_that_is_upcoming(name, expected):
    matchup = hard_outcome(name).payload["matchups"][0]

    assert (LINEUPS in text_of(matchup)) == (matchup["status"] == "upcoming"), (name, matchup["status"])
    assert matchup["status"] == expected[0]


def test_the_sentence_is_a_claim_only_where_it_is_written():
    """The claim exists for the Preview game and for no other, so the registry's condition is checked where it matters."""

    for name in EXPECTED:
        matchup = hard_outcome(name).payload["matchups"][0]
        keys = {claim["key"] for claim in matchup["report"]["claims"]}

        assert ("writer.confidence.lineups" in keys) == (matchup["status"] == "upcoming"), name


def test_a_game_that_is_not_upcoming_has_no_time_word_in_its_report():
    for name in EXPECTED:
        matchup = hard_outcome(name).payload["matchups"][0]
        if matchup["status"] == "upcoming":
            continue

        assert not TIME_WORDS.search(text_of(matchup)), (name, TIME_WORDS.search(text_of(matchup)))


def test_control_a_game_that_is_upcoming_may_say_before_first_pitch_and_nothing_about_today():
    matchup = hard_outcome("two_debuts").payload["matchups"][0]

    assert LINEUPS in text_of(matchup)
    assert not re.search(r"\btoday|tonight", text_of(matchup), re.IGNORECASE)


# --- the registry still holds a sentence that is written without its condition --------------------------------------


def test_a_lineups_sentence_in_a_game_that_is_not_upcoming_is_a_violation(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    assert "rule4:writer.confidence.lineups#game_state" not in {v.code for v in check_contract(payload)}  # control

    for status in ("live", "final", None):
        edited = json.loads(json.dumps(payload))
        edited["matchups"][0]["status"] = status

        assert "rule4:writer.confidence.lineups#game_state" in {v.code for v in check_contract(edited)}, status
