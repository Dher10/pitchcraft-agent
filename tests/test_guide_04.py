"""P2.2 guide 0.4: hard gates versus style rules (D52), the adopted Part A changes and the S-1..S-9 detectors."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_llm_report_writer as tlw  # noqa: E402
import test_writer_checks as base  # noqa: E402
from agents import call_budget as cb  # noqa: E402
from agents import llm_report_writer as lw  # noqa: E402
from agents import writer_checks as wc  # noqa: E402
from agents import writer_policy as wp  # noqa: E402

doc = base.doc
candidate, check, length, replace, SCOPE = base.candidate, base.check, base.length, base.replace, base.SCOPE
ARS = "starters.away_starter.pitching_profile.primary_pitch"
A, H = "starters.away_starter", "starters.home_starter"


def put(c, where, text, *paths, doc):
    return replace(c, where, text, *paths, doc=doc)


def detail(c, doc):
    return wc.check_report_detailed(c, doc, length(candidate(doc)))


def codes(c, doc):
    return {f["check"] for f in detail(c, doc)}


# --- D52: hard gates versus style -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("code,gate", [
    ("W1.entity", True), ("W1.number", True), ("W1.evidence_path", True), ("W2.comparison", True), ("W2.arithmetic", True), ("W3.prediction", True),
    ("W4.topic", True), ("W5.intensity", True), ("W5.label", True), ("W6.arsenal", True), ("W7.missing", True), ("W8.form", True), ("W8.value", True),
    ("W10.cause", True), ("W11.unknown_term", True), ("W12.time", True), ("W13.standing", True), ("W15.outcome", True), ("W16.internal", True),
    ("W0.sentence", True), ("W0.error", True), ("W17.structure", True), ("W-unknown", True), ("W11.definition", True),
    ("W11.expansion", False), ("W11.repeat", False), ("W11.inline", False), ("W12.scope", False), ("W14.starter", False), ("W14.team", False),
    ("W15.form", False), ("W15.question", False), ("W17.length", False),
    ("S-1", False), ("S-2", False), ("S-4", False), ("S-5", False), ("S-7", False), ("S-8", False),
])
def test_each_check_is_a_gate_or_a_style_rule_and_an_unknown_code_is_a_gate(code, gate):
    assert wc.is_gate(code) is gate


def test_split_failures_separates_gates_from_style():
    found = [{"check": "W10.cause", "sentence": "s", "token": "t"}, {"check": "S-4", "sentence": "s", "token": "utilizes"}]

    gates, styles = wc.split_failures(found)

    assert [f["check"] for f in gates] == ["W10.cause"] and [f["check"] for f in styles] == ["S-4"]


def style_only(parts):
    """The control candidate with one style problem (plain verb S-4) and no gate problem."""

    bad = deepcopy(parts[3])
    bad["sections"]["arsenal"][0]["text"] = "Kyle Freeland utilizes his Four-seam most."
    return bad


@pytest.fixture
def lengths(monkeypatch, request):
    parts = request.getfixturevalue("parts")
    monkeypatch.setattr(wc, "rules_length", lambda report: wc.report_length(parts[3]))


parts = tlw.parts


def go(parts, fake, budget=None):
    packet, findings, glossary, _ = parts
    return lw.write(findings, packet, glossary, provider=fake, budget=budget, item_id="x", sleep=lambda s: None, pacer=wp.Pacer(0, sleep=lambda s: None))


def test_a_report_that_fails_only_style_rules_is_accepted_with_its_style_findings_recorded(parts, lengths):
    fake = tlw.Fake(tlw.answer(style_only(parts)))

    result = go(parts, fake)

    assert result.path == "primary" and result.content_attempts == 1 and len(fake.calls) == 1
    assert [f["check"] for f in result.style_findings] == ["S-4"] and result.style_findings[0]["token"] == "utilizes"
    assert result.failures == [] and result.report["sections"][3]["body"].startswith("Kyle Freeland utilizes")
    assert result.attempts[0]["style_findings"][0]["check"] == "S-4" and result.attempts[0]["checks"] == []


def test_a_gate_failure_still_sends_the_item_to_retry_and_then_rules_and_the_retry_names_the_style_findings_too(parts, lengths):
    both = style_only(parts)
    both["sections"]["confidence"][0]["text"] = "The starters listed are the probable pitchers because it works."
    fake = tlw.Fake(tlw.answer(both), tlw.answer(both))

    result = go(parts, fake)

    second = fake.calls[1][2]["contents"][0]["parts"][0]["text"]
    assert result.path == "rules" and result.reason == "checks_failed" and len(fake.calls) == 2
    assert "W10.cause" in second and "S-4" in second and "Kyle Freeland utilizes his Four-seam most." not in json.dumps(fake.calls[1][2])
    assert result.failures == ["W10.cause"]


def test_style_findings_are_not_sent_back_when_the_first_attempt_is_accepted(parts, lengths):
    fake = tlw.Fake(tlw.answer(style_only(parts)), tlw.answer(parts[3]))

    go(parts, fake)

    assert len(fake.calls) == 1


def test_a_retry_that_fixes_the_gate_but_keeps_a_style_problem_is_accepted(parts, lengths):
    both = style_only(parts)
    both["sections"]["confidence"][0]["text"] = "The starters listed are the probable pitchers because it works."
    fake = tlw.Fake(tlw.answer(both), tlw.answer(style_only(parts)))

    result = go(parts, fake)

    assert result.path == "primary" and result.content_attempts == 2 and [f["check"] for f in result.style_findings] == ["S-4"]


def test_the_control_has_no_gate_and_no_style_finding(doc):
    assert detail(candidate(doc), doc) == []


# --- Part A ---------------------------------------------------------------------------------------------------------------


def era_whip(text, doc, *extra):
    c = put(candidate(doc), "sections.arsenal.0", text, f"{A}.season_summary.era", "glossary.ERA.short", f"{A}.season_summary.whip", "glossary.WHIP.short", *extra, doc=doc)
    return codes(c, doc)


def test_a1_the_short_form_may_come_first_or_in_parentheses_and_is_checked_either_way(doc):
    assert "W11.expansion" not in era_whip("Kyle Freeland has an 8.08 earned run average (ERA) and a 1.75 walks plus hits per inning (WHIP).", doc)
    assert "W11.expansion" not in era_whip("Kyle Freeland has an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning).", doc)
    assert "W11.expansion" in era_whip("Kyle Freeland has an 8.08 ERA and a 1.75 WHIP.", doc)
    assert "W11.expansion" in era_whip("Kyle Freeland has an 8.08 earned run average (ERA) and a 1.75 WHIP.", doc)


def test_a1_in_either_order_the_form_appears_once_and_is_cited(doc):
    c = put(candidate(doc), "sections.arsenal.0", "Kyle Freeland has an 8.08 earned run average (ERA).", f"{A}.season_summary.era", "glossary.ERA.short", doc=doc)
    c = put(c, "sections.arsenal.1", "José Soriano has a 2.65 ERA (earned run average).", f"{H}.season_summary.era", "glossary.ERA.short", doc=doc)
    assert "W11.repeat" in codes(c, doc)

    uncited = put(candidate(doc), "sections.arsenal.0", "Kyle Freeland has an 8.08 earned run average (ERA).", f"{A}.season_summary.era", doc=doc)
    assert "W11.expansion" in codes(uncited, doc)


MOVE = ("pitch_movement.home_starter.Curveball.h_break", "pitch_movement.home_starter.Curveball.v_break")


@pytest.mark.parametrize("text", [
    "His Curveball moves 12.5 in. sideways and 6.5 in. down compared with a pitch thrown without spin.",
    "His Curveball is moving 12.5 in. sideways and 6.5 in. down, compared with a pitch thrown without spin.",
    "Compared with a pitch thrown without spin, his Curveball moves 12.5 in. sideways and 6.5 in. down.",
])
def test_a2_moves_or_moving_with_the_comparison_clause_at_either_end(doc, text):
    c = put(candidate(doc), "sections.arsenal.1", text, *MOVE, doc=doc)

    assert detail(c, doc) == []  # accepted whole: no gate and no style finding, not just no W8 code


@pytest.mark.parametrize("text,code", [
    ("His Curveball moves 12.5 in. sideways and 6.5 in. down.", "W8.form"),
    ("His Curveball moves 12.5 in. sideways compared with a pitch thrown without spin, and 6.5 in. down.", "W8.form"),
    ("Compared with a pitch thrown without spin, his Curveball moves 12.5 in. sideways and 6.5 in. down compared with a pitch thrown without spin.", "W8.form"),
    ("His Curveball moves 12.5 in. sideways and 6.5 in. up compared with a pitch thrown without spin.", "W8.value"),
    ("His Curveball moving 12.4 in. sideways and 6.5 in. down compared with a pitch thrown without spin.", "W8.value"),
])
def test_a2_the_numbers_directions_and_the_single_clause_are_still_verified(doc, text, code):
    assert code in codes(put(candidate(doc), "sections.arsenal.1", text, *MOVE, doc=doc), doc)


def test_a3_watch_if_is_a_watch_form(doc):
    c = put(candidate(doc), "sections.watch.1", "Watch if José Soriano goes to his Sinker early.", f"{H}.pitching_profile.primary_pitch", doc=doc)
    d = put(candidate(doc), "sections.watch.1", "Watch José Soriano and his Sinker.", f"{H}.pitching_profile.primary_pitch", doc=doc)

    assert "W15.form" not in codes(c, doc) and "W15.form" in codes(d, doc)


def test_a5_numeric_twins_exist_for_the_five_figures_and_not_for_innings(doc):
    index = wc.wi.evidence_index(doc)

    assert index[f"{A}.season_summary.era_number"] == 8.08 and index[f"{H}.season_summary.whip_number"] == 1.15
    assert index["teams.home.offense_profile.ops_number"] == 0.712 and index["teams.home.offense_profile.k_rate_number"] == 24.3
    assert index["teams.away.offense_profile.bb_rate_number"] == 8.3
    assert not [p for p in index if "innings_number" in p] and index[f"{A}.season_summary.innings"] == "42.1"
    assert wc.wi.scope_label(doc, f"{A}.season_summary.era_number") == "2026 regular season through May 31"


def test_a5_a_comparison_on_the_numeric_twins_is_verified_in_order_and_scope(doc):
    def run(text, *paths):
        return codes(put(candidate(doc), "sections.arsenal.0", text, *paths, "glossary.ERA.short", doc=doc), doc)

    twins = (f"{H}.season_summary.era_number", f"{A}.season_summary.era_number")
    assert "W2.comparison" not in run("José Soriano has a lower ERA (earned run average) than Kyle Freeland, 2.65 to 8.08.", *twins)
    assert "W2.comparison" in run("José Soriano has a higher ERA (earned run average) than Kyle Freeland, 2.65 to 8.08.", *twins)
    strings = (f"{H}.season_summary.era", f"{A}.season_summary.era")
    assert "W2.comparison" in run("José Soriano has a lower ERA (earned run average) than Kyle Freeland, 2.65 to 8.08.", *strings)


def test_a5_k_rate_and_ops_comparisons_use_their_twins(doc):
    c = put(candidate(doc), "sections.arsenal.0", "The Angels have the higher K% (strikeout rate), 24.3% to 22.7%.", "teams.home.offense_profile.k_rate_number", "teams.away.offense_profile.k_rate_number", "glossary.K%.short", doc=doc)

    assert "W2.comparison" not in codes(c, doc)


def test_a9_the_finding_lists_are_one_string_each_and_none_when_empty(doc):
    index = wc.wi.evidence_index(doc)

    assert index["findings.away_starter_strengths"] == "Solid command supports strike-zone control; Four-seam to set up, Curveball to finish"
    assert index["findings.away_starter_risks"] is None
    assert index["findings.home_starter_risks"] == "Below-average command can create deep-count traffic"
    assert not [p for p in index if p.startswith("findings.away_starter_strengths.")]


# --- A8: pacing -----------------------------------------------------------------------------------------------------------------


class Clock:
    def __init__(self):
        self.now, self.slept = 1000.0, []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def test_a8_the_setting_is_twenty_seconds_and_the_d49_backoff_is_unchanged():
    assert wp.PACING_SECONDS == 20 and wp.BACKOFF_SECONDS == 3


def test_a8_a_call_starts_at_least_the_interval_after_the_previous_call_started():
    clock = Clock()
    pacer = wp.Pacer(20, clock=clock.time, sleep=clock.sleep)

    pacer.wait()                      # first call: no wait
    clock.now += 5
    pacer.wait()                      # 5 s later: waits 15
    clock.now += 25
    pacer.wait()                      # 25 s later: no wait

    assert clock.slept == [15]


def test_a8_the_production_writer_path_paces_every_call_including_the_d49_retries(parts, lengths):
    clock = Clock()
    pacer = wp.Pacer(20, clock=clock.time, sleep=clock.sleep)
    fake = tlw.Fake(tlw.status(503), tlw.status(503), tlw.status(503), tlw.answer(parts[3], version="gemini-3.1-flash-lite"))
    packet, findings, glossary, _ = parts

    result = lw.write(findings, packet, glossary, provider=fake, item_id="x", sleep=clock.sleep, pacer=pacer)

    assert result.path == "fallback_retry" and len(fake.calls) == 4
    # D49 backoff (3 s) after each retryable failure; the pacer tops every gap up to 20 s between call starts
    assert clock.slept == [3, 17, 20, 3, 17]


def test_a8_the_default_pacer_of_write_uses_the_shared_setting(monkeypatch, parts, lengths):
    waits = []
    monkeypatch.setattr(wp, "DEFAULT_PACER", wp.Pacer(20, clock=lambda: 0.0, sleep=waits.append))
    packet, findings, glossary, _ = parts

    lw.write(findings, packet, glossary, provider=tlw.Fake(tlw.answer(parts[3])), item_id="x")
    lw.write(findings, packet, glossary, provider=tlw.Fake(tlw.answer(parts[3])), item_id="x")

    assert waits == [20.0]  # the second call starts at the same fake instant: it must wait the whole interval


# --- Part B: detectors that feed S1, never gates --------------------------------------------------------------------------------


def style_codes(c, doc):
    return {f["check"]: f for f in detail(c, doc) if not wc.is_gate(f["check"])}


@pytest.mark.parametrize("word", ["utilizes", "possesses", "exhibits", "displays", "features", "maintains", "demonstrates", "showcases", "highlights"])
def test_s4_ai_verbs_are_flagged_as_style(doc, word):
    c = put(candidate(doc), "sections.arsenal.0", f"Kyle Freeland {word} his Four-seam.", ARS, doc=doc)

    found = style_codes(c, doc)

    assert found["S-4"]["token"] == word and all(not wc.is_gate(x) for x in codes(c, doc))


def test_s4_plain_verbs_are_not_flagged(doc):
    assert "S-4" not in style_codes(put(candidate(doc), "sections.arsenal.0", "Kyle Freeland uses his Four-seam and has a Curveball.", ARS, doc=doc), doc)


@pytest.mark.parametrize("headline,flagged", [
    ("Freeland and Soriano bring different looks to Angel Stadium.", False),
    ("Colorado visits Los Angeles at Angel Stadium.", False),
    ("Freeland and Soriano Meet at Angel Stadium", True),
    ("Freeland and Soriano Matchup", True),
    ("Freeland and Soriano preview", True),
])
def test_s5_headlines_are_sentence_case_without_a_matchup_tag(doc, headline, flagged):
    c = put(candidate(doc), "headline", headline, f"{A}.name", f"{H}.name", "venue", doc=doc)

    assert ("S-5" in style_codes(c, doc)) is flagged


@pytest.mark.parametrize("tail", ["in that matchup", "in this matchup", "in these encounters", "in that split", "over the same period", "in the same period"])
def test_s7_filler_tails_are_flagged(doc, tail):
    c = put(candidate(doc), "sections.arsenal.0", f"Kyle Freeland throws his Four-seam {tail}.", ARS, doc=doc)

    assert style_codes(c, doc)["S-7"]["token"] == tail


def test_s8_borrowed_authority_is_flagged(doc):
    c = put(candidate(doc), "sections.arsenal.0", "According to their profiles, Kyle Freeland throws his Four-seam.", ARS, doc=doc)

    assert "S-8" in style_codes(c, doc)


def test_s1_the_same_scope_in_two_sentences_of_a_report_is_a_style_finding_and_two_scopes_once_each_are_not(doc):
    c = candidate(doc)
    c["sections"]["home_vs_away"][0] = {"text": f"José Soriano shows below-average command over the {SCOPE}.", "evidence": base.ev(doc, f"{H}.pitching_profile.command_label", f"{H}.season_summary.scopes.counts.label")}

    assert style_codes(c, doc)["S-1"]["token"] == SCOPE

    other = deepcopy(doc)
    other["starters"]["home_starter"]["season_summary"]["scopes"]["counts"]["label"] = "2026 regular season through May 30"
    c2 = candidate(other)
    c2["sections"]["home_vs_away"][0] = {"text": "José Soriano shows below-average command over the 2026 regular season through May 30.", "evidence": base.ev(other, f"{H}.pitching_profile.command_label", f"{H}.season_summary.scopes.counts.label")}
    assert "S-1" not in style_codes(c2, other)


def test_s2_one_word_opening_more_than_four_sentences_or_a_repeated_this_that_frame_is_flagged(doc):
    c = candidate(doc)
    for i in range(3):
        c["sections"]["arsenal"].append({"text": "The Angels lineup keeps its place.", "evidence": base.ev(doc, "teams.home.name")})
    c["sections"]["arsenal"] = c["sections"]["arsenal"][:6]
    many = style_codes(c, doc)

    frame = candidate(doc)
    frame["sections"]["home_vs_away"][1] = {"text": "This lineup has a .709 OPS against right-handed pitchers.", "evidence": base.ev(doc, "teams.away.offense_profile.ops_vs_hand", "teams.away.offense_profile.vs_pitcher_hand")}
    frame["sections"]["away_vs_home"][1] = {"text": "That lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers.", "evidence": base.ev(doc, "teams.home.offense_profile.ops_vs_hand", "glossary.OPS.short", "teams.home.offense_profile.vs_pitcher_hand")}

    assert "S-2" in many and "S-2" in style_codes(frame, doc)


def test_the_style_detectors_name_the_sentence_and_token(doc):
    c = put(candidate(doc), "sections.arsenal.0", "Kyle Freeland utilizes his Four-seam in that matchup.", ARS, doc=doc)

    found = [f for f in detail(c, doc) if f["check"] in ("S-4", "S-7")]

    assert {f["check"] for f in found} == {"S-4", "S-7"} and all(f["sentence"] == "Kyle Freeland utilizes his Four-seam in that matchup." for f in found)
