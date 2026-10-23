"""QA1-01 (P1-R1fix): the series sentences against the state of the game, end to end.

At the Phase 1 gate a game that was live or final published "This is Game 1 of the World Series; the series has not
started.": a present-tense statement that was false once play had begun, and every publication check accepted it. Now

- the opening sentence is written only for a game whose state is `upcoming` (Preview), and its registry condition
  requires it;
- the standing sentence ("Before first pitch, ...") stays in every state: it says in its own words that the standing is
  the one before first pitch, and the standing is computed as of the day before the game (D29), so it is true whenever the
  file is read (docs/DATA_CONTRACT.md rule 4);
- a standing that MLB writes "Series tied 1-1" is quoted in the middle of the sentence with its first letter in lower case
  ("Before first pitch, series tied 1-1."); a team standing ("BOS leads 2-0") is quoted as it is.

The product runs the real pipeline, generator, critic, validator and contract over the four states the schedule can give a
game: upcoming, live, final and unknown.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from functools import cache

import pytest

from data_pipeline.contract_checks import check_contract
from tests.matrix import HARD_CASES, Outcome, run_scenario

STATES = {
    "upcoming": ("Preview", "Scheduled"),
    "live": ("Live", "In Progress"),
    "final": ("Final", "Final"),
    "null": (None, None),
}
PUBLISHED_STATUS = {"upcoming": "upcoming", "live": "live", "final": "final", "null": None}

OPENING = "This is Game 1 of the World Series; the series has not started."
STANDING = "This is Game 3 of the AL Championship Series. Before first pitch, BOS leads 2-0."
TIED = "This is Game 3 of the NL Division Series. Before first pitch, series tied 1-1."
SENTENCE = {"series_opening": OPENING, "series_standing": STANDING, "series_tied": TIED}
KEY = {
    "series_opening": "analyst.series.opening",
    "series_standing": "analyst.series.standing",
    "series_tied": "analyst.series.standing",
}


@cache
def outcome(name: str, state: str) -> Outcome:
    return run_scenario(replace(HARD_CASES[name], name=f"{name}-{state}", state=STATES[state]))


def matchup(name: str, state: str) -> dict:
    return outcome(name, state).payload["matchups"][0]


def summary_body(m: dict) -> str:
    (section,) = [s for s in m["report"]["sections"] if s["title"] == "Matchup Summary"]
    return section["body"]


def claim_keys(m: dict) -> list[str]:
    return [claim["key"] for claim in m["report"]["claims"]]


def codes(payload: dict) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


CELLS = [(name, state) for name in SENTENCE for state in STATES]


# --- the product -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name, state", CELLS)
def test_every_cell_publishes_with_the_state_the_schedule_gave_and_breaks_no_rule(name, state):
    result = outcome(name, state)

    assert result.blocked is None and result.failed == [] and result.violations == []
    assert result.payload["matchups"][0]["status"] == PUBLISHED_STATUS[state]
    assert result.payload["matchups"][0]["series"] is not None  # the series is read whatever the state


@pytest.mark.parametrize("state", STATES)
def test_the_opening_sentence_is_written_only_for_an_upcoming_game(state):
    m = matchup("series_opening", state)
    written = state == "upcoming"

    assert (OPENING in summary_body(m)) == written
    assert ("analyst.series.opening" in claim_keys(m)) == written
    assert "has not started" not in summary_body(m) or written


@pytest.mark.parametrize("name", ["series_standing", "series_tied"])
@pytest.mark.parametrize("state", STATES)
def test_the_standing_sentence_is_written_in_every_state_and_ends_the_summary(name, state):
    m = matchup(name, state)

    assert summary_body(m).endswith(" " + SENTENCE[name]), summary_body(m)
    assert claim_keys(m).count("analyst.series.standing") == 1
    assert "analyst.series.opening" not in claim_keys(m)


@pytest.mark.parametrize("state", ["live", "final", "null"])
def test_a_game_that_is_not_upcoming_has_no_sentence_that_says_the_series_has_not_started(state):
    for name in SENTENCE:
        body = summary_body(matchup(name, state))

        assert "has not started" not in body, (name, state)


def test_control_the_game_one_that_is_not_upcoming_still_publishes_a_summary_and_its_series_object():
    m = matchup("series_opening", "final")

    assert m["series"] == {"series_name": "World Series", "game_number": 1, "games_in_series": 7, "standing": None}
    assert summary_body(m)  # the report is written; only the sentence is not


# --- the wording -----------------------------------------------------------------------------------------------------


def test_a_tied_standing_is_quoted_with_a_lower_case_first_letter_and_the_payload_keeps_mlbs_text():
    m = matchup("series_tied", "upcoming")
    (claim,) = [c for c in m["report"]["claims"] if c["key"] == "analyst.series.standing"]

    assert m["series"]["standing"] == "Series tied 1-1"
    assert claim["args"]["result"] == "series tied 1-1"
    assert "Series tied" not in summary_body(m)


def test_a_team_standing_is_quoted_as_it_is():
    (claim,) = [c for c in matchup("series_standing", "upcoming")["report"]["claims"] if c["key"] == "analyst.series.standing"]

    assert claim["args"]["result"] == "BOS leads 2-0"


# --- the registry ----------------------------------------------------------------------------------------------------


def edited(name: str, status) -> dict:
    payload = deepcopy(outcome(name, "upcoming").payload)
    payload["matchups"][0]["status"] = status
    return payload


@pytest.mark.parametrize("status", ["live", "final", None])
def test_the_opening_sentence_in_a_game_that_is_not_upcoming_fails_its_condition(status):
    before = codes(outcome("series_opening", "upcoming").payload)

    assert "rule4:analyst.series.opening#game_state" not in before  # control: the Preview game
    assert "rule4:analyst.series.opening#game_state" in codes(edited("series_opening", status))


@pytest.mark.parametrize("name", ["series_standing", "series_tied"])
@pytest.mark.parametrize("status", ["live", "final", None])
def test_the_standing_sentence_does_not_depend_on_the_state(name, status):
    assert not {c for c in codes(edited(name, status)) if c.startswith("rule4:analyst.series.standing")}


def test_a_tied_standing_quoted_with_its_capital_fails_its_condition():
    payload = deepcopy(outcome("series_tied", "upcoming").payload)
    m = payload["matchups"][0]
    for claim in m["report"]["claims"]:
        if claim["key"] == "analyst.series.standing":
            claim["args"]["result"] = "Series tied 1-1"
    for section in m["report"]["sections"]:
        if "body" in section:
            section["body"] = section["body"].replace("series tied 1-1", "Series tied 1-1")

    assert "rule4:analyst.series.standing#standing" in codes(payload)


def test_a_team_standing_quoted_in_lower_case_fails_its_condition():
    payload = deepcopy(outcome("series_standing", "upcoming").payload)
    m = payload["matchups"][0]
    for claim in m["report"]["claims"]:
        if claim["key"] == "analyst.series.standing":
            claim["args"]["result"] = "bos leads 2-0"
    for section in m["report"]["sections"]:
        if "body" in section:
            section["body"] = section["body"].replace("BOS leads 2-0", "bos leads 2-0")

    assert "rule4:analyst.series.standing#standing" in codes(payload)
