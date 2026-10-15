"""A count that is unknown is not written as "none on record" (P0.15-D2.2b, F14).

The analyst wrote "no batters faced on record" and "no pitches on record" for a `null` count because it
tested `if batters` / `if pitches`: a falsy test cannot tell an unknown from a measured zero. The critic did
the same for the pitch count of the starter whose arsenal is limited, and the detail panel did for a starter
with no arsenal to show (found by the sweep of the class). A measured zero keeps its sentence; an unknown has
its own: "batters faced not available", "pitch count not available".

Controls (they pass before the fix): a measured zero, a positive count, the contact sentence that needs a
positive count of batters faced.
"""

from __future__ import annotations

import pytest

from agents import critic, matchup_analyst
from agents.language import catalog_for
from data_pipeline import labels
from tests.corpus import golden_payload, published
from tests.golden_scenarios import agent_outputs, measured_zero_sample, scenarios
from tests.test_contract_checks import added, codes
from tests.test_limited_samples import REG, debut_sample, sample

T = catalog_for("en")
NAME = "Alpha Livearm"


def unknown_sample() -> dict:
    return labels.build_sample(
        pitches=None, arsenal_scope=None, batters_faced=None, strikeouts=None, walks=None, home_runs=None,
        rates_source="unavailable", rates_scope=None,
    )


def notes(smp: dict) -> list[str]:
    return [str(note) for note in matchup_analyst._data_notes(T, NAME, smp)]


def limited_sentences(have_arsenal: str, have_batters: str) -> list[str]:
    return [
        f"{NAME}'s arsenal data is limited ({have_arsenal}; 100 needed), so this report makes no arsenal claim for him.",
        f"Strikeout data for {NAME} is limited ({have_batters}; 70 needed), so no swing-and-miss claim is made.",
        f"Control data for {NAME} is limited ({have_batters}; 170 needed), so no command claim is made.",
    ]


# --- the analyst ------------------------------------------------------------------------------------------


def test_unknown_counts_are_not_available_not_none_on_record():
    assert notes(unknown_sample()) == [
        *limited_sentences("pitch count not available", "batters faced not available"),
        f"Home runs allowed are not available for {NAME}.",
    ]


def test_control_measured_zeros_keep_the_sentence_that_says_none_on_record():
    assert notes(measured_zero_sample())[:3] == limited_sentences("no pitches on record", "no batters faced on record")


def test_control_a_measured_zero_of_batters_faced_has_no_contact_sentence():
    """The contract (`analyst.data.contact`) wants `batters_faced > 0`: over zero batters there is nothing to count."""

    assert notes(measured_zero_sample())[3] == f"Home runs allowed are not available for {NAME}."


def test_control_positive_counts_are_stated_as_counts():
    assert notes(sample(pitches=40, bf=10, k=3, bb=1, hr=0))[:3] == limited_sentences("40 pitches", "10 batters faced")


def test_a_debut_whose_api_line_has_no_batters_faced_says_it_is_not_available():
    """`debut_sample` has 0 pitches measured and no batters faced given: one of each."""

    assert notes(debut_sample())[:3] == limited_sentences("no pitches on record", "batters faced not available")


# --- the critic -------------------------------------------------------------------------------------------


def critic_limited_check(monkeypatch, name: str) -> dict:
    matchup = scenarios(monkeypatch)[name]
    review = critic.run(agent_outputs(matchup)["report"], matchup)
    return next(check for check in review["checks"] if check["claim"] == T("critic.limited.claim", name=NAME))


def test_the_critic_does_not_say_none_on_record_for_an_unknown_pitch_count(monkeypatch):
    check = critic_limited_check(monkeypatch, "live_unknown_figures")

    assert check["status"] == "supported"
    assert check["evidence"] == T("critic.limited.supported_unavailable", needed=100)
    assert check["evidence"] == "Pitch count not available (the minimum is 100); the report makes no arsenal claim."


def test_control_the_critic_keeps_none_on_record_for_a_measured_zero(monkeypatch):
    check = critic_limited_check(monkeypatch, "live_measured_zero_counts")

    assert check["evidence"] == "No pitches on record, below the 100 needed; the report makes no arsenal claim."


# --- the contract (rule 4, registry) ---------------------------------------------------------------------


@pytest.fixture
def unknown(monkeypatch):
    return published(golden_payload(monkeypatch, "live_unknown_figures"))


@pytest.fixture
def zero(monkeypatch):
    return published(golden_payload(monkeypatch, "live_measured_zero_counts"))


AWAY = "away_starter"


def test_the_payloads_of_the_two_scenarios_have_no_violation_of_the_new_phrases(unknown, zero):
    for payload in (unknown, zero):
        assert not {c for c in codes(payload) if c.startswith(("rule4:analyst.have.", "rule4:critic.limited."))}


def test_rule_4_batters_faced_not_available_needs_the_count_to_be_unknown(unknown):
    def edit(m):
        m["starters"][AWAY]["sample"]["rates"]["batters_faced"] = 5

    assert "rule4:analyst.have.batters_unavailable#known" in added(unknown, edit)


def test_rule_4_pitch_count_not_available_needs_the_count_to_be_unknown(unknown):
    def edit(m):
        m["starters"][AWAY]["sample"]["arsenal"]["pitches"] = 7

    assert "rule4:analyst.have.pitches_unavailable#known" in added(unknown, edit)


def test_rule_4_none_on_record_needs_a_measured_zero(zero):
    def edit(m):
        rates = m["starters"][AWAY]["sample"]["rates"]
        rates["batters_faced"], rates["source"] = None, "unavailable"
        m["starters"][AWAY]["sample"]["arsenal"]["pitches"] = None

    new = added(zero, edit)

    assert "rule4:analyst.have.no_batters#unknown_not_zero" in new
    assert "rule4:analyst.have.no_pitches#unknown_not_zero" in new


def test_rule_4_the_critics_unavailable_evidence_needs_an_unknown_pitch_count(unknown):
    def edit(m):
        m["starters"][AWAY]["sample"]["arsenal"]["pitches"] = 0

    assert "rule4:critic.limited.supported_unavailable#count" in added(unknown, edit)
