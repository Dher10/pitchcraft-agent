"""A group of figures has a scope if and only if it has a figure (DATA_CONTRACT rule 3; F2 and F17, P0.15-D2.1a).

The constructors that make a group decide its scope from the figures they were given:

- `labels.build_sample`: the pitch data (`arsenal`) and the counts (`rates`) of a starter;
- `live_matchup.build_offense`: the figures of a lineup.

A measured zero is a figure: a debut's 0 pitches come from a valid Statcast answer and keep their scope.
"""

from __future__ import annotations

import pytest

from data_pipeline import labels
from data_pipeline.live_matchup import build_offense
from data_pipeline.schema import SCHEMA_VERSION

SCOPE = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-03")


def sample(*, pitches=1200, source="mlb_api", counts=(800, 190, 60, 20)):
    batters, strikeouts, walks, home_runs = counts if source != "unavailable" else (None,) * 4
    return labels.build_sample(
        pitches=pitches,
        arsenal_scope=SCOPE,
        batters_faced=batters,
        strikeouts=strikeouts,
        walks=walks,
        home_runs=home_runs,
        rates_source=source,
        rates_scope=SCOPE,
    )


# --- starters: F17 -------------------------------------------------------------------------------


def test_the_schema_version_is_the_one_that_makes_scopes_nullable():
    assert SCHEMA_VERSION == "0.7.0"


def test_counts_that_are_unavailable_have_no_scope():
    assert sample(source="unavailable")["rates"]["scope"] is None


@pytest.mark.parametrize("source", ["mlb_api", "statcast"])
def test_counts_from_a_source_keep_its_scope(source):
    assert sample(source=source)["rates"]["scope"] == SCOPE


def test_a_pitch_count_that_is_unknown_has_no_scope():
    assert sample(pitches=None)["arsenal"]["scope"] is None


@pytest.mark.parametrize("pitches", [0, 1, 1200])
def test_a_pitch_count_that_was_measured_keeps_its_scope_even_when_it_is_zero(pitches):
    assert sample(pitches=pitches)["arsenal"]["scope"] == SCOPE


# --- lineups: F2 ---------------------------------------------------------------------------------

SPLITS = {"vr": {"ops": ".801", "k_rate": 24.5, "bb_rate": 10.2}}


@pytest.mark.parametrize("splits", [None, {}, {"vl": {"ops": ".700", "k_rate": 20.0, "bb_rate": 8.0}}])
def test_a_lineup_with_no_split_against_the_hand_has_no_scope_and_nothing_that_says_it_has_one(splits):
    offense = build_offense("R", splits, SCOPE)

    assert offense["scope"] is None
    assert offense["summary_label"] is None and offense["recent_form"] is None
    assert offense["ops_vs_hand"] is None and offense["k_rate_vs_hand"] is None and offense["bb_rate_vs_hand"] is None


def test_a_split_that_carries_no_figure_is_no_split():
    offense = build_offense("R", {"vr": {}}, SCOPE)

    assert offense["scope"] is None and offense["summary_label"] is None


def test_a_lineup_with_a_split_keeps_the_scope_and_its_labels():
    offense = build_offense("R", SPLITS, SCOPE)

    assert offense["scope"] == SCOPE
    assert offense["ops_vs_hand"] == ".801"
    assert offense["summary_label"] == "Real season split vs RHP" and offense["recent_form"] == "Season split"


def test_one_figure_is_enough_for_the_scope():
    offense = build_offense("R", {"vr": {"k_rate": 24.5}}, SCOPE)

    assert offense["scope"] == SCOPE and offense["ops_vs_hand"] is None


# --- publication refuses the old shape -------------------------------------------------------------


def test_a_payload_that_scopes_counts_it_does_not_have_fails_publication(monkeypatch):
    from tests.corpus import build
    from tests.live_helpers import failed_checks

    payload = build(monkeypatch, "live_debuts")
    sample_ = payload["matchups"][0]["starters"]["away_starter"]["sample"]
    assert sample_["rates"]["source"] == "unavailable" and failed_checks(payload) == []

    sample_["rates"]["scope"] = SCOPE

    assert any("scope of each group of figures matches its source" in d for d in failed_checks(payload))


def test_a_payload_that_scopes_a_pitch_count_it_does_not_have_fails_publication(monkeypatch):
    from tests.corpus import build
    from tests.live_helpers import failed_checks

    payload = build(monkeypatch, "live_complete")
    arsenal = payload["matchups"][0]["starters"]["away_starter"]["sample"]["arsenal"]
    arsenal["pitches"] = None

    assert any("scope of each group of figures matches its source" in d for d in failed_checks(payload))
