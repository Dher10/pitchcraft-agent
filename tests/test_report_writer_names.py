"""Starter names are never split in the report text (PLAN.md P0.6, Phase 0 Gherkin
"Pitcher name is never split")."""

from __future__ import annotations

from copy import deepcopy

import pytest

from agents import data_scout, matchup_analyst, report_writer
from data_pipeline import demo_inputs

NAMES = [
    "Corbin Burnes",
    "Luis Garcia Jr.",
    "Jesús Luzardo",
    "Hyun-Jin Ryu",
    "A.J. Puk",
    "José De La Cruz",
    "Ryan O'Hearn",
    "Madison Bumgarner III",
    "Pitcher A",
    "Demo Starter",
    "Ohtani",
]


def _matchup_with_away_name(name: str) -> dict:
    matchup = deepcopy(demo_inputs.build_demo_payload()["matchups"][0])
    matchup["starters"]["away_starter"]["name"] = name
    return matchup


def _report(matchup: dict) -> dict:
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    return report_writer.run(findings, matchup)


@pytest.mark.parametrize("name", NAMES)
def test_what_to_watch_keeps_the_full_starter_name(name):
    report = _report(_matchup_with_away_name(name))

    sentence = report["short_summary"][2]

    assert sentence.startswith(f"The early what to watch is whether {name} can ")
    assert "can can" not in sentence


@pytest.mark.parametrize("name", NAMES)
def test_every_starter_name_in_the_report_text_is_complete(name):
    matchup = _matchup_with_away_name(name)
    report = _report(matchup)
    home_name = matchup["starters"]["home_starter"]["name"]

    text = "\n".join(
        [report["headline"], *report["short_summary"]]
        + [s.get("body", "") for s in report["sections"]]
        + [b for s in report["sections"] for b in s.get("bullets", [])]
    )

    # The first name never appears detached from the surname in the sentence that
    # used to be split ("whether Corbin can Burnes ...").
    first, _, rest = name.partition(" ")
    if rest:
        assert f"whether {first} can {rest}" not in text
    assert name in text and home_name in text


def test_home_starter_name_is_not_split_either():
    matchup = _matchup_with_away_name("Corbin Burnes")
    matchup["starters"]["home_starter"]["name"] = "Luis Garcia Jr."

    assert "Luis Garcia Jr." in "\n".join(
        s.get("body", "") for s in _report(matchup)["sections"]
    )


def test_an_unknown_subject_is_left_untouched_instead_of_guessing_a_split():
    assert (
        report_writer._watch_observation("Can Somebody Else keep it down?", ("Corbin Burnes",))
        == "Can Somebody Else keep it down"
    )
