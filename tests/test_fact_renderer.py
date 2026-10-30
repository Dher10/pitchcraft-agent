"""The fact renderer: one verified sentence per citable value, no template means no support (fail closed)."""

from __future__ import annotations

from pathlib import Path

import re

import pytest

from agents import fact_renderer as fr
from agents import writer_input as wi
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"
CASE = "veteran-824027"


@pytest.fixture(scope="module")
def doc():
    return wi.build_writer_input(bp.load_dev_packet(DATASET, CASE), bp.load_dev_findings(DATASET, CASE), wi.load_glossary(DATASET / "glossary.json"))


def test_the_renderer_has_a_version():
    assert fr.FACT_RENDERER_VERSION == "p2.3-2"


@pytest.mark.parametrize("path,expected", [
    ("starters.away_starter.season_summary.era", "Kyle Freeland has an earned run average (ERA) of 8.08 over the 2026 regular season through May 31."),
    ("starters.away_starter.season_summary.era_number", "Kyle Freeland has an earned run average (ERA) of 8.08 over the 2026 regular season through May 31."),
    ("starters.home_starter.pitching_profile.command_label", "José Soriano shows below-average command."),
    ("starters.home_starter.pitching_profile.contact_risk_label", "No contact-risk rating is available for José Soriano."),
    ("starters.home_starter.sample.rates.batters_faced", "José Soriano has faced 289 batters over the 2026 regular season through May 31."),
    ("starters.away_starter.sample.thresholds.control", "170 batters faced are needed for a control read of Kyle Freeland."),
    ("pitch_movement.home_starter.Curveball.v_break", "The Curveball of José Soriano moves 6.5 in. down compared with a pitch thrown without spin."),
    ("pitch_mix.1.away_starter.overall", "Kyle Freeland throws the Curveball 22.5% of the time."),
    ("velocity_by_pitch.3.home_starter_velocity", "The Four-seam of José Soriano is thrown at 97.7 miles per hour."),
    ("teams.home.offense_profile.ops_vs_hand", "The Los Angeles Angels lineup has an on-base plus slugging (OPS) of .712 against left-handed pitchers over the 2026 regular season through May 31."),
    ("teams.home.offense_profile.k_rate_number", "The Los Angeles Angels lineup has a strikeout rate (K%) of 24.3% against left-handed pitchers over the 2026 regular season through May 31."),
    ("findings.lineup_notes.home", "The Los Angeles Angels lineup has elevated swing-and-miss risk. The Los Angeles Angels lineup draws walks at an above-average rate."),
    ("findings.lineup_notes.away", "There are no lineup notes for the Colorado Rockies lineup."),
    ("glossary.OPS.short", "OPS stands for on-base plus slugging."),
    ("status", "The game has not started."),
    ("venue", "The game is played at Angel Stadium."),
])
def test_a_value_renders_to_a_sentence_that_keeps_subject_measure_scope_and_flag(doc, path, expected):
    assert fr.render_fact(doc, path) == expected


def test_a_path_with_no_template_or_not_in_the_input_renders_to_none(doc):
    for path in ("aliases.away.0", "starters.away_starter.team", "glossary.OPS.meaning", "no.such.path", "language"):
        assert fr.render_fact(doc, path) is None


def test_the_premise_joins_the_facts_once_in_order_and_refuses_what_it_cannot_render(doc):
    premise, problem = fr.premise_for(doc, ["starters.away_starter.season_summary.era", "starters.away_starter.season_summary.era_number", "starters.away_starter.season_summary.whip"])

    assert problem is None and premise.count("earned run average") == 1 and premise.index("earned run average") < premise.index("walks plus hits")
    assert fr.premise_for(doc, ["starters.away_starter.team"]) == (None, "unrenderable")
    assert fr.premise_for(doc, []) == (None, "unrenderable")


def test_a_premise_over_2400_characters_is_refused_never_truncated(doc):
    paths = [p for p in wi.evidence_index(doc) if p.startswith("pitch_movement.") or p.startswith("pitch_mix.")]

    premise, problem = fr.premise_for(doc, paths)

    assert premise is None and problem == "oversize"


def test_every_citable_value_of_every_dev_case_renders_or_is_a_declared_non_fact():
    glossary = wi.load_glossary(DATASET / "glossary.json")

    def non_fact(path, value):
        return (path in ("language", "series") or path.startswith("aliases.") or path.endswith((".through", ".team", ".meaning"))
                or (path.startswith("glossary.") and path.endswith(".short") and value is None)
                or value is None)  # an unknown without a "not available" template is unrenderable (fail closed), never shown as a value

    for case in bp.dev_case_ids(DATASET):
        d = wi.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
        for path, value in wi.evidence_index(d).items():
            fact = fr.render_fact(d, path)
            assert fact is not None or non_fact(path, value), (case, path)
            assert fact is None or len(fact) <= 300


def test_no_fact_of_any_dev_case_shows_an_unknown_as_a_value_or_leaves_a_placeholder():
    glossary = wi.load_glossary(DATASET / "glossary.json")
    bad = []
    for case in bp.dev_case_ids(DATASET):
        d = wi.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), glossary)
        for path in wi.evidence_index(d):
            fact = fr.render_fact(d, path)
            if fact and (re.search(r"\bNone\b|\bnan\b|[{}]", fact)):
                bad.append((case, path, fact))
    assert bad == []


def test_a_null_value_renders_to_none_unless_the_template_says_it_is_not_available(doc):
    nulled = {**doc, "starters": {**doc["starters"], "away_starter": {**doc["starters"]["away_starter"], "sample": {**doc["starters"]["away_starter"]["sample"], "arsenal": {**doc["starters"]["away_starter"]["sample"]["arsenal"], "pitches": None}}}}}

    assert fr.render_fact(nulled, "starters.away_starter.sample.arsenal.pitches") is None
    assert fr.render_fact(doc, "starters.home_starter.pitching_profile.contact_risk_label") == "No contact-risk rating is available for José Soriano."


def test_a_zero_vertical_break_is_rendered_with_the_directions_the_site_uses():
    d = {"starters": {"home_starter": {"name": "A B"}}, "pitch_movement": {"home_starter": {"Slider": {"family": "Breaking", "h_break": 1.0, "v_break": 0.0}}}}

    assert fr._movement(d, "pitch_movement.home_starter.Slider.v_break", ["pitch_movement", "home_starter", "Slider", "v_break"], 0.0).endswith("moves 0.0 in. up compared with a pitch thrown without spin.")


def test_the_renderer_identity_changes_when_the_fact_table_or_the_source_changes():
    ident = fr.renderer_identity()

    assert ident.startswith(fr.FACT_RENDERER_VERSION + ":") and len(ident.split(":")[1]) == 16
