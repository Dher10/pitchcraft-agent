"""P1.5-b: the report's series sentence (D43; docs/DATA_CONTRACT.md section 3.1, keys `analyst.series.*`).

Two cited sentences, written by the analyst through the catalog like every other phrase and placed by the writer at the end
of the Matchup Summary:

    This is Game {n} of the {series_name}. Before first pitch, {result}.        (a game after the first, standing known)
    This is Game 1 of the {series_name}; the series has not started.            (the first game)

They are written only when the matchup has a series object; there is no sentence for a game with `series: null` and none
for a game after the first whose standing is unavailable ("Series standing not available" is the page's line, not a claim).
The games are built by the real pipeline (`tests/matrix.py` hard cases `series_*`); each negative test changes the series
the sentence cites and requires the registry to fail the condition of that sentence.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline.contract_checks import check_contract
from tests.matrix import hard_outcome

STANDING = "This is Game 3 of the AL Championship Series. Before first pitch, BOS leads 2-0."
TIED = "This is Game 3 of the NL Division Series. Before first pitch, series tied 1-1."
OPENING = "This is Game 1 of the World Series; the series has not started."
KEYS = ("analyst.series.standing", "analyst.series.opening")


def matchup(name: str) -> dict:
    return hard_outcome(name).payload["matchups"][0]


def summary_body(m: dict) -> str:
    (section,) = [s for s in m["report"]["sections"] if s["title"] == "Matchup Summary"]
    return section["body"]


def series_claims(m: dict) -> list[dict]:
    return [claim for claim in m["report"]["claims"] if claim["key"] in KEYS]


def codes(payload: dict) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


# --- the text -------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, sentence",
    [("series_standing", STANDING), ("series_tied", TIED), ("series_opening", OPENING)],
)
def test_the_summary_ends_with_the_sentence_the_owner_approved(name, sentence):
    body = summary_body(matchup(name))

    assert body.endswith(" " + sentence), body
    assert body.count(sentence) == 1


def test_a_standing_that_is_unavailable_after_game_1_writes_no_sentence():
    m = matchup("series_standing_unavailable")

    assert series_claims(m) == [] and "Game 3" not in summary_body(m) and "Before first pitch" not in summary_body(m)
    assert m["series"]["game_number"] == 3 and m["series"]["standing"] is None


@pytest.mark.parametrize("name", ["live_state_live", "two_debuts", "api_zeros_are_zeros", "unknown_team"])
def test_a_game_with_no_series_writes_no_series_sentence(name):
    m = matchup(name)

    assert m["series"] is None and series_claims(m) == []
    assert "This is Game" not in summary_body(m) and "the series has not started" not in summary_body(m)


# --- the claims -----------------------------------------------------------------------------------------------------


def test_the_standing_sentence_is_a_claim_with_its_arguments_and_no_subject():
    (claim,) = series_claims(matchup("series_standing"))

    assert claim["key"] == "analyst.series.standing"
    assert claim["args"] == {"n": 3, "series_name": "AL Championship Series", "result": "BOS leads 2-0"}
    assert claim["subject"] is None


def test_the_opening_sentence_is_a_claim_with_its_name_only():
    (claim,) = series_claims(matchup("series_opening"))

    assert claim["key"] == "analyst.series.opening" and claim["args"] == {"series_name": "World Series"}


@pytest.mark.parametrize("name", ["series_standing", "series_tied", "series_opening", "series_standing_unavailable"])
def test_the_outcome_of_a_series_game_publishes_and_breaks_no_rule(name):
    outcome = hard_outcome(name)

    assert outcome.blocked is None and outcome.failed == [] and outcome.violations == []


# --- the registry fails a sentence whose condition is false -----------------------------------------------------------


def changed(name: str, edit) -> tuple[set[str], set[str]]:
    outcome = hard_outcome(name)
    before = codes(outcome.payload)
    payload = deepcopy(outcome.payload)
    edit(payload["matchups"][0])
    return codes(payload) - before, before


@pytest.mark.parametrize(
    "name, edit, reason",
    [
        ("series_standing", lambda m: m["series"].update(standing="BOS leads 1-0"), "standing"),
        ("series_standing", lambda m: m["series"].update(standing=None), "standing"),
        ("series_standing", lambda m: m["series"].update(standing="BOS wins 4-0"), "standing"),
        ("series_standing", lambda m: m["series"].update(games_in_series=None, standing="BOS leads 4-0", game_number=5), "standing"),
        ("series_standing", lambda m: m["series"].update(series_name="World Series"), "name"),
        ("series_standing", lambda m: m["series"].update(game_number=4, standing="BOS leads 2-0"), "game_number"),
        ("series_standing", lambda m: m["series"].update(game_number=1, standing=None), "game_number"),
        ("series_standing", lambda m: m["series"].update(game_number=8, games_in_series=None), "game_number"),
        ("series_standing", lambda m: m.update(series=None), "series"),
        ("series_tied", lambda m: m["series"].update(standing="Series tied 2-2"), "standing"),
        ("series_opening", lambda m: m["series"].update(game_number=2, standing="BOS leads 1-0"), "game_number"),
        ("series_opening", lambda m: m["series"].update(series_name="NL Division Series"), "name"),
        ("series_opening", lambda m: m.update(series=None), "series"),
    ],
)
def test_a_sentence_about_a_series_the_matchup_does_not_have_fails_its_condition(name, edit, reason):
    key = "analyst.series.opening" if name == "series_opening" else "analyst.series.standing"

    new, _ = changed(name, edit)

    assert f"rule4:{key}#{reason}" in new, new


def test_a_standing_the_series_cannot_have_had_fails_even_when_the_sentence_cites_it_faithfully():
    # The sentence quotes the matchup's own (impossible) standing: the condition still refuses it.
    outcome = hard_outcome("series_standing")
    payload = deepcopy(outcome.payload)
    m = payload["matchups"][0]
    m["series"]["standing"] = "BOS leads 3-1"
    for claim in m["report"]["claims"]:
        if claim["key"] == "analyst.series.standing":
            claim["args"]["result"] = "BOS leads 3-1"
    for section in m["report"]["sections"]:
        if "body" in section:  # the watch section has bullets
            section["body"] = section["body"].replace("BOS leads 2-0", "BOS leads 3-1")

    assert "rule4:analyst.series.standing#standing" in codes(payload) - codes(outcome.payload)


def test_the_two_keys_are_registered_rules_of_the_registry():
    from data_pipeline import claims_registry

    assert all(key in claims_registry.RULES for key in KEYS)


def test_the_catalog_has_both_templates_and_they_are_the_approved_wording():
    from agents.messages_en import EN_MESSAGES

    assert EN_MESSAGES["analyst.series.standing"] == "This is Game {n} of the {series_name}. Before first pitch, {result}."
    assert EN_MESSAGES["analyst.series.opening"] == "This is Game 1 of the {series_name}; the series has not started."
