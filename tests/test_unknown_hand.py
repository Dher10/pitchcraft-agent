"""The analyst never names a hand the data does not give (P0.15-D2.3a, F15).

`matchup_analyst._offense_read` took the hand from `starter.get("throws", "R")`: a starter with no hand was a
right-hander, and a switch pitcher was "SHP". A lineup is read against the hand of the starter it faces, and only `L`
and `R` are a hand a lineup has a split against. With any other value (`S`, or none) the lineup read says it cannot be
matched and makes no offense claim (`analyst.offense.unavailable_no_hand`).

The lineup that faces the switch pitcher is written by `live_matchup.build_offense("S", ...)`; since D2.3b the pipeline
publishes that game and the golden scenario `live_switch_pitcher` is its real path. Before D2.3b the same lineup carried
the label "SHP" and the right-handed split, and these tests show the analyst did not trust it.

Controls (they pass before the fix): a known hand keeps its sentences, word for word.
"""

from __future__ import annotations

import pytest

from agents import data_scout, matchup_analyst, report_writer
from agents.language import catalog_for
from data_pipeline import labels, live_matchup
from tests.corpus import payload_of, published
from tests.golden_scenarios import SPLITS_VR, scenarios
from tests.test_contract_checks import added, codes

T = catalog_for("en")
SENTENCE = "Season offense data cannot be matched to this pitcher's hand, so the lineup read makes no offense claims."
AWAY = "away_starter"


def report_text(matchup: dict) -> str:
    packet = data_scout.run(matchup)
    return str(report_writer.run(matchup_analyst.run(packet), matchup))


def test_the_sentence_is_the_one_the_owner_approved():
    assert T("analyst.offense.unavailable_no_hand") == SENTENCE


def test_a_starter_with_no_hand_is_not_a_right_hander(monkeypatch):
    """The probe of F15: no `throws` and no hand on the lineup used to read as RHP."""

    matchup = scenarios(monkeypatch)["live_healthy"]
    for team in matchup["teams"].values():
        team["offense_profile"]["vs_pitcher_hand"] = None
    for starter in matchup["starters"].values():
        del starter["throws"]

    text = report_text(matchup)

    assert SENTENCE in text
    assert "RHP" not in text and "LHP" not in text and "SHP" not in text


def switch_matchup(monkeypatch) -> dict:
    """The away starter is a switch pitcher; the home lineup is what `build_offense` writes for him."""

    matchup = scenarios(monkeypatch)["live_with_offense_splits"]
    matchup["starters"][AWAY]["throws"] = "S"
    scope = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-03")
    matchup["teams"]["home"]["offense_profile"] = live_matchup.build_offense("S", SPLITS_VR, scope)
    return matchup


def test_a_switch_pitcher_has_no_hand_in_any_sentence(monkeypatch):
    matchup = switch_matchup(monkeypatch)

    text = report_text(matchup)

    assert SENTENCE in text
    assert "SHP" not in text
    # the other lineup faces a left-hander and keeps its hand
    assert "LHP pitching" in text


def test_the_lineup_that_faces_the_switch_pitcher_makes_no_offense_claim(monkeypatch):
    matchup = switch_matchup(monkeypatch)

    read = matchup_analyst._offense_read(T, matchup["teams"]["home"], matchup["starters"][AWAY])

    assert read == SENTENCE  # not even a note about strikeouts or walks, whatever figures the lineup carries


def test_control_a_known_hand_keeps_its_sentences(monkeypatch):
    matchup = scenarios(monkeypatch)["live_with_offense_splits"]
    home = matchup["teams"]["home"]
    home["offense_profile"]["ops_vs_hand"] = ".801"

    read = matchup_analyst._offense_read(T, home, matchup["starters"][AWAY])

    assert T("analyst.offense.strong", hand="RHP", ops=".801", name=matchup["starters"][AWAY]["name"]) in read
    assert SENTENCE not in read


def test_control_an_unavailable_ops_with_a_known_hand_keeps_its_sentence(monkeypatch):
    matchup = scenarios(monkeypatch)["live_healthy"]
    home = matchup["teams"]["home"]
    home["offense_profile"]["ops_vs_hand"] = None

    read = matchup_analyst._offense_read(T, home, matchup["starters"][AWAY])

    assert read == T("analyst.offense.unavailable", hand="RHP")


# --- the registry (rule 4) ---------------------------------------------------------------------------------


@pytest.fixture
def switch(monkeypatch):
    return published(payload_of(switch_matchup(monkeypatch)))


def test_rule_4_the_switch_pitcher_payload_has_no_violation_of_the_new_phrase(switch):
    claimed = [c for c in switch["matchups"][0]["report"]["claims"] if c["key"] == "analyst.offense.unavailable_no_hand"]

    assert claimed, "the report of the switch pitcher records the new phrase"
    assert not {c for c in codes(switch) if c.startswith("rule4:analyst.offense.")}


def test_rule_4_the_new_phrase_needs_a_hand_that_is_not_l_or_r(switch):
    def known_hand(m):
        m["starters"][AWAY]["throws"] = "R"

    assert "rule4:analyst.offense.unavailable_no_hand#hand" in added(switch, known_hand)


# --- the two readings of the hand ----------------------------------------------------------------------------


def test_control_a_lineup_with_no_label_takes_the_hand_the_starter_throws_with(monkeypatch):
    """The hand is real data in `starter.throws` as well: L or R names it, whichever field carries it."""

    matchup = scenarios(monkeypatch)["live_with_offense_splits"]
    home = matchup["teams"]["home"]
    home["offense_profile"]["vs_pitcher_hand"] = None
    for figure in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand"):
        home["offense_profile"][figure] = None

    read = matchup_analyst._offense_read(T, home, matchup["starters"][AWAY])

    assert read == T("analyst.offense.unavailable", hand=f"{matchup['starters'][AWAY]['throws']}HP")


def test_rule_4_a_lineup_label_that_names_a_hand_the_starter_does_not_have_is_found(monkeypatch):
    """The analyst does not hide an inconsistent payload: the registry flags it."""

    matchup = scenarios(monkeypatch)["live_with_offense_splits"]
    matchup["starters"][AWAY]["throws"] = "S"  # the home lineup still says RHP and has an OPS
    payload = published(payload_of(matchup))

    assert any(c.startswith("rule4:analyst.offense.") and c.endswith("#hand") for c in codes(payload))
