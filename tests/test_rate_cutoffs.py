"""One cut-off for the lineup K% and BB% notes (D32).

The analyst used two different cut-offs for the same idea: the offense read said "strike out
often" from 23% and "draws walks" from 9%, while the pressure points said "elevated
swing-and-miss risk" above 22% and "draws walks" above 9%. A lineup at 22.5% got a pressure
point but no note. Both now read the same constants in `labels.py`, and the comparison is
made on the rate as the fan reads it: the one-decimal figure of the card.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from agents import matchup_analyst
from agents.language import catalog_for
from data_pipeline import demo_inputs, labels

T = catalog_for("en")


def packet(k_rate: str | None, bb_rate: str | None) -> dict:
    base = deepcopy(demo_inputs.build_demo_payload()["matchups"][0])
    offense = base["teams"]["home"]["offense_profile"]
    offense.update(ops_vs_hand=".700", k_rate_vs_hand=k_rate, bb_rate_vs_hand=bb_rate)
    return {"teams": base["teams"], "starters": base["starters"]}


def strikeout_note(k_rate: str) -> bool:
    team = packet(k_rate, "5.0%")["teams"]["home"]
    read = matchup_analyst._offense_read(T, team, packet(k_rate, "5.0%")["starters"]["away_starter"])
    return T("analyst.offense.note_strikeouts") in read


def walk_note(bb_rate: str) -> bool:
    team = packet("15.0%", bb_rate)["teams"]["home"]
    starter = packet("15.0%", bb_rate)["starters"]["away_starter"]
    return T("analyst.offense.note_walks", name=starter["name"]) in matchup_analyst._offense_read(T, team, starter)


def pressure(k_rate: str | None, bb_rate: str | None) -> list[str]:
    points = matchup_analyst._lineup_pressure_points(T, packet(k_rate, bb_rate))
    return points[packet(k_rate, bb_rate)["teams"]["home"]["id"]]


def test_the_cutoffs_are_the_values_the_fan_already_sees():
    assert labels.OFFENSE_K_NOTE_PCT == 23.0
    assert labels.OFFENSE_BB_NOTE_PCT == 9.0


@pytest.mark.parametrize("rate", ["21.9%", "22.0%", "22.5%", "22.9%", "23.0%", "23.1%", "30.0%"])
def test_the_strikeout_note_and_the_pressure_point_agree(rate):
    has_note = strikeout_note(rate)
    has_point = T("analyst.pressure.strikeouts") in pressure(rate, "5.0%")

    assert has_note == has_point
    assert has_note == (float(rate.rstrip("%")) >= labels.OFFENSE_K_NOTE_PCT)


@pytest.mark.parametrize("rate", ["8.0%", "8.9%", "9.0%", "9.1%", "12.0%"])
def test_the_walk_note_and_the_pressure_point_agree(rate):
    has_note = walk_note(rate)
    has_point = T("analyst.pressure.walks") in pressure("15.0%", rate)

    assert has_note == has_point
    assert has_note == (float(rate.rstrip("%")) >= labels.OFFENSE_BB_NOTE_PCT)


def test_the_qa_style_boundary_22_5_is_neither_a_note_nor_a_pressure_point():
    assert not strikeout_note("22.5%")
    assert T("analyst.pressure.strikeouts") not in pressure("22.5%", "5.0%")


def test_exactly_9_percent_is_a_walk_pressure_point_too():
    assert T("analyst.pressure.walks") in pressure("15.0%", "9.0%")


def test_an_unavailable_rate_makes_no_note_and_no_point():
    assert pressure(None, None) == []


# --- OPS (D32): the same cut-off for the sentence and the pressure point ------------------------------


def ops_packet(ops: str) -> dict:
    data = packet("15.0%", "5.0%")
    data["teams"]["home"]["offense_profile"]["ops_vs_hand"] = ops
    return data


def strong_sentence(ops: str) -> bool:
    data = ops_packet(ops)
    team, starter = data["teams"]["home"], data["starters"]["away_starter"]
    hand = team["offense_profile"].get("vs_pitcher_hand") or "RHP"
    read = matchup_analyst._offense_read(T, team, starter)
    return T("analyst.offense.strong", hand=hand, ops=ops, name=starter["name"]) in read


def strong_point(ops: str) -> bool:
    data = ops_packet(ops)
    points = matchup_analyst._lineup_pressure_points(T, data)[data["teams"]["home"]["id"]]
    return T("analyst.pressure.ops") in points


def test_the_ops_cutoff_is_the_value_the_fan_already_sees():
    assert labels.OFFENSE_OPS_STRONG == 0.750


@pytest.mark.parametrize("ops, strong", [(".749", False), (".750", True), (".751", True), (".700", False), (".820", True)])
def test_the_ops_sentence_and_the_pressure_point_agree_at_the_edge(ops, strong):
    assert strong_sentence(ops) is strong
    assert strong_point(ops) is strong


def test_an_unavailable_ops_makes_no_strong_claim():
    data = ops_packet(None)
    team = data["teams"]["home"]
    assert T("analyst.pressure.ops") not in matchup_analyst._lineup_pressure_points(T, data)[team["id"]]
