"""P2.2 guide 0.3: short forms in parentheses, scope once per section, entity aliases, hyphenated intensity words, failure detail."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_writer_checks as base  # noqa: E402
from agents import writer_checks as wc  # noqa: E402

doc = base.doc
candidate, check, length, replace, SCOPE = base.candidate, base.check, base.length, base.replace, base.SCOPE
ARS = "starters.away_starter.pitching_profile.primary_pitch"


def with_first(c, key, i, text, *paths, doc):
    return replace(c, f"sections.{key}.{i}", text, *paths, doc=doc)


def detail(c, doc, rules_length=None):
    return wc.check_report_detailed(c, doc, length(candidate(doc)) if rules_length is None else rules_length)


def test_the_control_passes(doc):
    assert check(candidate(doc), doc) == []


def test_the_glossary_is_cited_by_term_with_a_short_form_and_there_is_no_index_path(doc):
    index = wc.wi.evidence_index(doc)

    assert index["glossary.OPS.short"] == "on-base plus slugging" and index["glossary.K%.short"] == "strikeout rate"
    assert index["glossary.command.short"] is None and "glossary.LHH / RHH.meaning" in index
    assert not [p for p in index if p.startswith("glossary.") and p.split(".")[1].isdigit()]


def test_a_term_with_a_short_form_gets_it_in_parentheses_once_on_first_use(doc):
    ops = ("teams.home.offense_profile.ops_vs_hand", "teams.home.offense_profile.scope.label")
    bare = with_first(candidate(doc), "away_vs_home", 1, f"The Angels lineup has a .712 OPS against left-handed pitchers, over the {SCOPE}.", *ops, doc=doc)
    assert "W11.expansion" in check(bare, doc)

    twice = with_first(candidate(doc), "home_vs_away", 1, "The Rockies lineup has a .709 OPS (on-base plus slugging) against right-handed pitchers.", "teams.away.offense_profile.ops_vs_hand", "glossary.OPS.short", doc=doc)
    assert "W11.repeat" in check(twice, doc)

    uncited = with_first(candidate(doc), "away_vs_home", 1, f"The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers, over the {SCOPE}.", *ops, doc=doc)
    assert "W11.expansion" in check(uncited, doc)

    wrong = with_first(candidate(doc), "away_vs_home", 1, f"The Angels lineup has a .712 OPS (a hitting number) against left-handed pitchers, over the {SCOPE}.", ops[0], "glossary.OPS.short", ops[1], doc=doc)
    assert "W11.expansion" in check(wrong, doc)


@pytest.mark.parametrize("text,path,code", [
    # the approved wording written into the prose is a style finding (guide: never write a definition) ...
    ("On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup.", "glossary.OPS.meaning", "W11.inline"),
    ("OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup.", "glossary.OPS.meaning", "W11.inline"),
    ("Command is how well a pitcher puts the ball where he wants it.", "glossary.command.meaning", "W11.inline"),
    # ... but a definition in other words, or only part of the approved one, fails (accuracy, D52)
    ("OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for.", "glossary.OPS.meaning", "W11.definition"),
    ("Command is how well a pitcher throws strikes.", "glossary.command.meaning", "W11.definition"),
])
def test_a_definition_in_the_prose_is_a_gate_unless_it_is_the_approved_wording(doc, text, path, code):
    found = check(with_first(candidate(doc), "arsenal", 0, text, path, doc=doc), doc)

    assert code in found
    assert ("W11.definition" in found) is (code == "W11.definition") and (code == "W11.inline") is not wc.is_gate(code)


def test_terms_without_a_short_form_need_no_expansion(doc):
    c = with_first(candidate(doc), "arsenal", 0, "Kyle Freeland has faced 202 batters, and his swing-and-miss ability is average.",
                   "starters.away_starter.sample.rates.batters_faced", "starters.away_starter.pitching_profile.swing_miss_label", doc=doc)

    assert not [f for f in check(c, doc) if f.startswith("W11")]


def test_labels_may_be_written_in_lowercase_inside_a_sentence(doc):
    paths = ("starters.away_starter.pitching_profile.command_label", "starters.away_starter.pitching_profile.swing_miss_label")
    lower = with_first(candidate(doc), "away_vs_home", 0, "Kyle Freeland shows solid command and average swing-and-miss ability.", *paths, doc=doc)
    capitalized = with_first(candidate(doc), "away_vs_home", 0, "Kyle Freeland shows Solid command and Average swing-and-miss ability.", *paths, doc=doc)

    assert check(lower, doc) == [] and "W5.intensity" not in check(capitalized, doc)


@pytest.mark.parametrize("text", [
    "Kyle Freeland throws an elite-level Four-seam.", "Kyle Freeland has a super-strong Curveball.", "Kyle Freeland throws a dominant-looking Four-seam.",
])
def test_a_hyphenated_intensity_word_is_caught(doc, text):
    assert "W5.intensity" in check(with_first(candidate(doc), "arsenal", 0, text, ARS, doc=doc), doc)


def test_hyphenated_labels_and_pitch_names_are_still_allowed(doc):
    c = with_first(candidate(doc), "arsenal", 0, "José Soriano shows below-average command and throws a Four-seam.",
                   "starters.home_starter.pitching_profile.command_label", "starters.home_starter.pitching_profile.primary_pitch", doc=doc)

    assert check(c, doc) == []


def test_aliases_are_built_from_the_packet_only_and_nothing_else_is_accepted(doc):
    names = wc.wi.name_aliases(doc)

    assert names["away_starter"] == ["Freeland"] and names["home_starter"] == ["Soriano"]
    assert set(names["away"]) == {"Rockies", "Colorado", "COL"} and set(names["home"]) == {"Angels", "Los Angeles", "LAA"}

    def run(text):
        return check(with_first(candidate(doc), "arsenal", 0, text, ARS, doc=doc), doc)

    for ok in ("Freeland throws his Four-seam most.", "Kyle Freeland throws his Four-seam most.", "The Rockies starter throws his Four-seam most.",
               "Colorado sends out a starter with a Four-seam.", "COL starts a pitcher who throws a Four-seam."):
        assert "W1.entity" not in run(ok), ok
    for bad in ("Kyle throws his Four-seam most.", "Angel Freeland throws his Four-seam most.", "Los throws his Four-seam most.",
                "The Dodgers hit his Four-seam.", "Rocky Mountain Freeland throws his Four-seam."):
        assert "W1.entity" in run(bad), bad


def test_a_shared_city_is_not_an_alias_and_a_two_word_nickname_is_kept(doc):
    shared = deepcopy(doc)
    shared["teams"]["away"].update(name="Chicago White Sox", abbreviation="CWS")
    shared["teams"]["home"].update(name="Chicago Cubs", abbreviation="CHC")

    names = wc.wi.name_aliases(shared)

    assert set(names["away"]) == {"White Sox", "CWS"} and set(names["home"]) == {"Cubs", "CHC"}


def test_every_failure_is_reported_with_its_sentence_and_the_offending_token(doc):
    text = "Kyle Freeland throws his Four-seam because it works, 41 times."
    found = detail(with_first(candidate(doc), "arsenal", 0, text, ARS, doc=doc), doc)

    assert {"check": "W10.cause", "sentence": text, "token": "because"} in found
    assert {"check": "W1.number", "sentence": text, "token": "41"} in found
    trout = "Kyle Freeland faces Mike Trout with his Four-seam."
    entity = detail(with_first(candidate(doc), "arsenal", 0, trout, ARS, doc=doc), doc)
    assert {"check": "W1.entity", "sentence": trout, "token": "Mike Trout"} in entity
    assert all(set(f) == {"check", "sentence", "token"} for f in found + entity)


def test_a_failure_outside_any_sentence_has_no_sentence_and_the_codes_stay_the_same(doc):
    c = candidate(doc)
    found = detail(c, doc, 100000)
    length_failure = [f for f in found if f["check"] == "W17.length"]

    assert length_failure and length_failure[0]["sentence"] is None
    assert wc.check_report(c, doc, 100000) == list(dict.fromkeys(f["check"] for f in found))


def test_a_lineup_note_may_speak_of_swing_and_miss_without_the_pitcher_label(doc):
    c = with_first(candidate(doc), "away_vs_home", 1, f"The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers and an elevated swing-and-miss risk, over the {SCOPE}.",
                   "teams.home.offense_profile.ops_vs_hand", "glossary.OPS.short", "findings.lineup_notes.home", "teams.home.offense_profile.scope.label", doc=doc)

    assert "W5.label" not in check(c, doc)


def test_the_calibration_helper_finds_what_the_guide_forbids_in_citation_free_text(doc):
    found = wc.lexical_failures("Kyle Freeland needs efficient strikes because hitters wait. Can Kyle Freeland throw strikes? The lineup draws walks, so he pitches carefully.", doc)
    codes = {f["check"] for f in found}

    assert {"W10.cause", "W15.question"} <= codes
    assert {"because", "so"} <= {f["token"] for f in found if f["check"] == "W10.cause"}
    assert wc.lexical_failures("Kyle Freeland throws his Four-seam most.", doc) == []


def run_text(doc, text, *paths):
    return check(with_first(candidate(doc), "arsenal", 0, text, *(paths or (ARS,)), doc=doc), doc)


@pytest.mark.parametrize("text", [
    "OPS is a way to add up how good a lineup is.", "ERA is the average of earned runs given up over nine innings.",
    "OPS means how often a lineup reaches base and how much power it has.",
])
def test_a_sentence_that_starts_with_the_term_and_defines_it_is_rejected(doc, text):
    assert "W11.definition" in run_text(doc, text)


def test_ordinary_prose_that_contains_a_short_meaning_or_a_figure_is_not_a_definition(doc):
    assert "W11.definition" not in run_text(doc, "Kyle Freeland has 39 strikeouts.", "starters.away_starter.sample.rates.strikeouts")
    assert "W11.definition" not in run_text(doc, "Kyle Freeland has an 8.08 ERA (earned run average).", "starters.away_starter.season_summary.era", "glossary.ERA.short")


def test_a_statistic_the_glossary_lacks_is_rejected_and_an_allowed_term_is_not(doc):
    assert "W11.unknown_term" in run_text(doc, "Kyle Freeland has a high BABIP with his Four-seam.")
    assert "W11.unknown_term" not in run_text(doc, "Kyle Freeland has faced 202 batters.", "starters.away_starter.sample.rates.batters_faced")


@pytest.mark.parametrize("text", [
    "Angels' hitters see his Four-seam.", "The Rockies' bats see his Four-seam.", "Meanwhile, Freeland throws his Four-seam.",
    "Overall, Freeland throws his Four-seam.", "Across the lineup, Freeland throws his Four-seam.", "Looking at Freeland, he throws a Four-seam.",
    "Another look at Freeland shows a Four-seam.", "Next up is Freeland and his Four-seam.", "Angels\u2019 hitters see his Four-seam.",
])
def test_natural_openers_and_plural_possessives_are_not_unknown_names(doc, text):
    assert "W1.entity" not in run_text(doc, text)


@pytest.mark.parametrize("text", [
    "Colorado Angels throws his Four-seam.", "Los Angeles Rockies throws his Four-seam.", "COL Rockies throws his Four-seam.",
    "Trout is a left-handed hitter facing his Four-seam.", "Freeland Angels throws his Four-seam.",
])
def test_two_names_side_by_side_are_not_a_team(doc, text):
    assert "W1.entity" in run_text(doc, text)


def test_a_lineup_note_exempts_only_the_words_that_are_in_the_note(doc):
    note = "findings.lineup_notes.home"  # "has elevated swing-and-miss risk"
    assert "W5.label" not in run_text(doc, "The Angels carry an elevated swing-and-miss risk.", note, "teams.home.offense_profile.vs_pitcher_hand")
    assert "W5.label" in run_text(doc, "His command is sloppy.", note, "teams.home.offense_profile.vs_pitcher_hand")


def test_the_whole_lineup_note_is_a_citable_path_and_an_empty_one_is_null(doc):
    index = wc.wi.evidence_index(doc)

    assert index["findings.lineup_notes.home"] == "has elevated swing-and-miss risk; draws walks at an above-average rate"
    assert index["findings.lineup_notes.away"] is None
    c = with_first(candidate(doc), "away_vs_home", 1, "The Angels draw walks at an above-average rate and have an elevated swing-and-miss risk.", "findings.lineup_notes.home", doc=doc)
    assert "W1.evidence_path" not in check(c, doc) and "W5.intensity" not in check(c, doc)


def test_a_missing_lineup_note_does_not_exempt_a_label_term(doc):
    # the away lineup has no notes (None): citing it must not turn the word "none" into an exemption for "command"
    c = with_first(candidate(doc), "away_vs_home", 1, "His command is sloppy.", "findings.lineup_notes.away", doc=doc)

    assert "W5.label" in check(c, doc)


def test_a_sentence_unrelated_to_a_term_that_cites_its_meaning_is_a_definition_gate(doc):
    c = with_first(candidate(doc), "arsenal", 0, "Kyle Freeland throws his Four-seam most.", ARS, "glossary.OPS.meaning", doc=doc)

    found = check(c, doc)

    assert "W11.definition" in found and wc.is_gate("W11.definition")
