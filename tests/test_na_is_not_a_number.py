"""An unavailable ERA, WHIP or IP ("N/A") is never turned into a number (QA-01 invariant).

No agent reads a number out of those fields, and the analyst makes no claim that names
them when they are unavailable. The card showing a dash instead of "N/A" is a component
test (components/__tests__), because that is where the frontend is checked.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re

import pytest

from agents import critic, data_scout, matchup_analyst, report_writer
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from tests.test_live_starters_no_demo_fields import _fake_live_game

KEEP = object()  # leave the real numbers of the fake live game
SLOTS = ("away_starter", "home_starter")
FIELDS = ("era", "whip", "innings")
NAMED = re.compile(r"\b(ERA|WHIP|innings)\b")
NUMBER_ARTIFACTS = re.compile(r"\bN/A\b|\bnan\b|\binf\b|\b0\.0+\b", re.IGNORECASE)


@pytest.fixture()
def template() -> dict:
    payload = demo_inputs.build_demo_payload()
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


@pytest.fixture()
def matchup_with(monkeypatch, template):
    def build(unavailable=KEEP) -> dict:
        game = _fake_live_game(template)
        for slot in SLOTS:
            # Pitch data includes the postseason, season figures do not: the scopes differ,
            # which is the case where the analyst's scope note lists the figures it covers.
            game[slot]["sample"]["arsenal"]["scope"] = labels.make_scope(
                labels.SCOPE_REGULAR_POSTSEASON, "2026-07-04"
            )
        if unavailable is not KEEP:
            for slot in SLOTS:
                for field in FIELDS:
                    game[slot]["season_summary"][field] = unavailable
        monkeypatch.setattr(gdj, "_live", {"fetched_date": "2026-07-04", "live_games": [game]})
        return gdj._apply_live_game_to_matchup(
            deepcopy(template), game, matchup_id="matchup_001", is_featured=True
        )

    return build


def run_agents(matchup: dict) -> dict:
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, matchup)
    review = critic.run(report, matchup)
    return {"findings": findings, "report": report, "review": review}


@pytest.mark.parametrize("unavailable", ["N/A", None])
def test_no_agent_text_names_or_computes_unavailable_era_whip_or_innings(matchup_with, unavailable):
    matchup = matchup_with(unavailable)
    for slot in SLOTS:
        assert all(matchup["starters"][slot]["season_summary"][f] in ("N/A", None) for f in FIELDS)

    text = json.dumps(run_agents(matchup))

    assert not NAMED.search(text), NAMED.search(text)
    assert not NUMBER_ARTIFACTS.search(text), NUMBER_ARTIFACTS.search(text)


def test_the_analyst_makes_no_claim_with_those_fields_but_keeps_the_counts_claim(matchup_with):
    notes = " ".join(run_agents(matchup_with("N/A"))["findings"]["scope_notes"])

    assert not NAMED.search(notes)
    assert "strikeout, walk and home-run counts" in notes


def test_available_fields_are_still_named(matchup_with):
    # Non-vacuous: with real numbers the same note does name them.
    notes = " ".join(run_agents(matchup_with())["findings"]["scope_notes"])

    assert "ERA, WHIP, innings" in notes


def test_a_mix_of_available_and_unavailable_names_only_the_available_ones(matchup_with):
    matchup = matchup_with()
    for slot in SLOTS:
        matchup["starters"][slot]["season_summary"]["whip"] = "N/A"

    notes = " ".join(run_agents(matchup)["findings"]["scope_notes"])

    assert "ERA, innings" in notes and "WHIP" not in notes


def test_the_two_unavailable_spellings_give_identical_agent_output(matchup_with):
    # "N/A" and None both mean unavailable: nothing downstream may tell them apart.
    assert run_agents(matchup_with("N/A")) == run_agents(matchup_with(None))
