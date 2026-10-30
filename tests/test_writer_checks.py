"""P2.2: the guide's rules W1-W17 as code. Each rule has a passing control and a failing sentence."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from agents import writer_checks as wc
from agents import writer_input as wi
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"
SCOPE = "2026 regular season through May 31"
OPS_DEF = "OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup."  # forbidden since 0.3


def ev(doc, *paths):
    index = wi.evidence_index(doc)
    return [{"path": p, "value": "null" if index[p] is None else str(index[p])} for p in paths]


@pytest.fixture(scope="module")
def doc():
    packet, findings = bp.load_dev_packet(DATASET, "veteran-824027"), bp.load_dev_findings(DATASET, "veteran-824027")
    return wi.build_writer_input(packet, findings, wi.load_glossary(DATASET / "glossary.json"))


def candidate(doc):
    A, H = "starters.away_starter", "starters.home_starter"
    s = lambda text, *paths: {"text": text, "evidence": ev(doc, *paths)}
    return {
        "headline": s("Kyle Freeland and José Soriano start this game.", f"{A}.name", f"{H}.name"),
        "summary_lines": [
            s("Kyle Freeland leans on a Four-seam and finishes with a Curveball.", f"{A}.pitching_profile.primary_pitch", f"{A}.pitching_profile.putaway_pitch"),
            s("José Soriano leans on a Sinker and finishes with a Curveball.", f"{H}.pitching_profile.primary_pitch", f"{H}.pitching_profile.putaway_pitch"),
            s("Watch how often each starter uses his Curveball.", f"{A}.pitching_profile.putaway_pitch", f"{H}.pitching_profile.putaway_pitch"),
        ],
        "sections": {
            "summary": [s("The Colorado Rockies visit the Los Angeles Angels at Angel Stadium.", "teams.away.name", "teams.home.name", "venue")],
            "away_vs_home": [
                s("Kyle Freeland shows solid command.", f"{A}.pitching_profile.command_label"),
                s(f"The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers, over the {SCOPE}.", "teams.home.offense_profile.ops_vs_hand", "glossary.OPS.short", "teams.home.offense_profile.scope.label"),
            ],
            "home_vs_away": [
                s("José Soriano shows below-average command.", f"{H}.pitching_profile.command_label"),
                s("The Rockies lineup has a .709 OPS against right-handed pitchers.", "teams.away.offense_profile.ops_vs_hand"),
            ],
            "arsenal": [
                s("Kyle Freeland throws his Four-seam most and his Curveball second most.", f"{A}.pitching_profile.primary_pitch", f"{A}.pitching_profile.putaway_pitch"),
                s("His Curveball moves 0.5 in. sideways and 6.2 in. down compared with a pitch thrown without spin.", "pitch_movement.away_starter.Curveball.h_break", "pitch_movement.away_starter.Curveball.v_break"),
            ],
            "watch": [
                s("Watch how often Kyle Freeland throws his Curveball.", f"{A}.pitching_profile.putaway_pitch"),
                s("Watch whether José Soriano goes to his Sinker early.", f"{H}.pitching_profile.primary_pitch"),
                s("Watch how the Angels lineup handles left-handed pitching.", "teams.home.offense_profile.vs_pitcher_hand"),
            ],
            "confidence": [
                s("The starters listed are the probable pitchers.", "data_confidence.lineup_status"),
                s("Lineups can change before first pitch.", "status"),
            ],
        },
    }


def length(c):
    return wc.report_length(c)


def check(c, doc, rules_length=None):
    return wc.check_report(c, doc, rules_length if rules_length is not None else length(c))


def replace(c, where, text, *paths, doc):
    """Replace the sentence at `where` ('headline', 'summary_lines.0', 'sections.watch.1') by `text` citing `paths`."""
    c = deepcopy(c)
    node = c
    keys = where.split(".")
    for key in keys[:-1]:
        node = node[int(key)] if isinstance(node, list) else node[key]
    last = int(keys[-1]) if isinstance(node, list) else keys[-1]
    node[last] = {"text": text, "evidence": ev(doc, *paths) if paths else node[last]["evidence"]}
    return c


def test_the_control_candidate_passes_every_rule(doc):
    assert check(candidate(doc), doc) == []


@pytest.mark.parametrize("where,text,paths,expected", [
    # W1: entities and numbers only from the packet
    ("sections.summary.0", "The Colorado Rockies visit Mike Trout at Angel Stadium.", (), "W1.entity"),
    ("sections.away_vs_home.0", "Kyle Freeland shows solid command in 41 starts.", (), "W1.number"),
    ("sections.away_vs_home.1", f"The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers, over the {SCOPE}.", ("teams.home.offense_profile.scope.label", "glossary.OPS.short"), "W1.number"),
    # W2: no arithmetic, comparisons only with both values
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam twice as often as his Curveball.", ("starters.away_starter.pitching_profile.primary_pitch",), "W2.arithmetic"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam more than his Curveball.", ("starters.away_starter.pitching_profile.primary_pitch",), "W2.comparison"),
    # W3: no predictions, outcomes or questions
    ("sections.watch.0", "Watch how Kyle Freeland will pitch.", ("starters.away_starter.pitching_profile.putaway_pitch",), "W3.prediction"),
    ("sections.arsenal.0", "Kyle Freeland is likely to throw his Four-seam.", ("starters.away_starter.pitching_profile.primary_pitch",), "W3.prediction"),
    # W4: forbidden topics
    ("sections.arsenal.0", "Kyle Freeland signed a contract with his Four-seam.", ("starters.away_starter.pitching_profile.primary_pitch",), "W4.topic"),
    # W5: intensity words only from labels
    ("sections.away_vs_home.0", "Kyle Freeland has elite command.", ("starters.away_starter.pitching_profile.command_label",), "W5.intensity"),
    ("sections.arsenal.0", "Kyle Freeland has a dominant Four-seam.", ("starters.away_starter.pitching_profile.primary_pitch",), "W5.intensity"),
    ("sections.arsenal.0", "Kyle Freeland has good swing-and-miss ability with his Four-seam.", ("starters.away_starter.pitching_profile.primary_pitch",), "W5.label"),
    # W10: no cause words
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam because it works.", ("starters.away_starter.pitching_profile.primary_pitch",), "W10.cause"),
    # W12: no time claims
    ("sections.arsenal.0", "Kyle Freeland has recently thrown his Four-seam.", ("starters.away_starter.pitching_profile.primary_pitch",), "W12.time"),
    # W15: statements, not questions
    ("sections.watch.0", "Can Kyle Freeland land the Curveball early?", ("starters.away_starter.pitching_profile.putaway_pitch",), "W15.question"),
    ("sections.watch.0", "Look at the Curveball of Kyle Freeland.", ("starters.away_starter.pitching_profile.putaway_pitch",), "W15.form"),
    ("sections.watch.0", "Watch whether Kyle Freeland wins with the Curveball.", ("starters.away_starter.pitching_profile.putaway_pitch",), "W15.outcome"),
    # W16: no internals
    ("sections.confidence.1", "Lineups can change before the snapshot is refreshed.", ("status",), "W16.internal"),
    # W8: movement is a measurement
    ("sections.arsenal.1", "His Curveball dives away from hitters and fools them.", ("pitch_movement.away_starter.Curveball.h_break", "pitch_movement.away_starter.Curveball.v_break"), "W8.form"),
    ("sections.arsenal.1", "His Curveball moves 0.5 in. sideways and 6.2 in. up compared with a pitch thrown without spin.", ("pitch_movement.away_starter.Curveball.h_break", "pitch_movement.away_starter.Curveball.v_break"), "W8.value"),
])
def test_each_rule_rejects_its_violation(doc, where, text, paths, expected):
    base = candidate(doc)
    # the control's own length is the rules length, so only the rule under test can fail
    c = replace(base, where, text, *paths, doc=doc)

    assert expected in wc.check_report(c, doc, length(base)), wc.check_report(c, doc, length(base))


def test_evidence_must_exist_and_carry_the_value_it_quotes(doc):
    c = candidate(doc)
    c["sections"]["arsenal"][0]["evidence"] = [{"path": "starters.away_starter.nickname", "value": "x"}]
    assert "W1.evidence_path" in check(c, doc)

    c = candidate(doc)
    c["sections"]["arsenal"][0]["evidence"][0]["value"] = "Sinker"
    assert "W1.evidence_value" in check(c, doc)

    c = candidate(doc)
    c["sections"]["arsenal"][0]["evidence"] = []
    assert "W1.no_evidence" in check(c, doc)


def test_a_comparison_needs_both_values_quoted_with_one_scope(doc):
    same = replace(candidate(doc), "sections.arsenal.0", "Kyle Freeland has faced fewer batters, 202 against 289 for José Soriano.", "starters.away_starter.sample.rates.batters_faced", "starters.home_starter.sample.rates.batters_faced", doc=doc)
    assert "W2.comparison" not in check(same, doc)

    one = replace(candidate(doc), "sections.arsenal.0", "Kyle Freeland has faced fewer batters, 202 of them.", "starters.away_starter.sample.rates.batters_faced", doc=doc)
    assert "W2.comparison" in check(one, doc)

    other_scope = deepcopy(doc)
    other_scope["starters"]["home_starter"]["sample"]["rates"]["scope"]["label"] = "2026 regular season through May 30"
    assert "W2.comparison" in check(same, other_scope)

    mixed = replace(candidate(doc), "sections.arsenal.0", "Kyle Freeland has faced fewer batters, 202 against 12 home runs allowed by José Soriano.", "starters.away_starter.sample.rates.batters_faced", "starters.home_starter.sample.rates.home_runs", doc=doc)
    assert "W2.comparison" in check(mixed, doc)


def test_a_missing_value_is_said_to_be_not_available_and_never_zero(doc):
    path = "starters.home_starter.pitching_profile.contact_risk_label"
    assert wc.wi.evidence_index(doc)[path] is None

    good = replace(candidate(doc), "sections.home_vs_away.0", "José Soriano has no contact-risk rating, which is not available.", path, doc=doc)
    bad = replace(candidate(doc), "sections.home_vs_away.0", "José Soriano has a contact-risk rating of zero.", path, doc=doc)

    assert "W7.missing" not in check(good, doc)
    assert "W7.missing" in check(bad, doc)


def test_a_limited_arsenal_gets_no_description_of_pitch_shapes_and_must_say_it_is_limited(doc):
    limited = deepcopy(doc)
    limited["starters"]["away_starter"]["sample"]["limited"]["arsenal"] = True

    failures = check(candidate(limited), limited)

    assert "W6.arsenal" in failures and "W6.unsaid" in failures
    said = replace(candidate(limited), "sections.arsenal.0", "Arsenal data for Kyle Freeland is limited, with not enough data for a read.", "starters.away_starter.sample.limited.arsenal", doc=limited)
    said = replace(said, "sections.arsenal.1", "Arsenal data is limited for Kyle Freeland.", "starters.away_starter.sample.limited.arsenal", doc=limited)
    said["summary_lines"][0] = {"text": "José Soriano leans on a Sinker.", "evidence": ev(limited, "starters.home_starter.pitching_profile.primary_pitch")}
    said["summary_lines"][2] = {"text": "Watch how the Angels lineup handles left-handed pitching.", "evidence": ev(limited, "teams.home.offense_profile.vs_pitcher_hand")}
    said["sections"]["watch"][0] = {"text": "Watch how the Angels lineup handles left-handed pitching.", "evidence": ev(limited, "teams.home.offense_profile.vs_pitcher_hand")}
    assert "W6.arsenal" not in check(said, limited) and "W6.unsaid" not in check(said, limited)


def test_the_series_rules_apply_only_with_a_series(doc):
    assert "W13.series" in check(replace(candidate(doc), "sections.summary.0", "This is Game 2 of the series.", "teams.away.name", doc=doc), doc)

    postseason = deepcopy(doc)
    postseason["series"] = {"series_name": "NL Wild Card Series", "standing": None, "game_number": 1, "games_in_series": 3}
    c = replace(candidate(postseason), "sections.summary.0", "This is Game 1 of the NL Wild Card Series, and the Rockies lead.", "series.series_name", "series.game_number", doc=postseason)
    assert "W13.standing" in check(c, postseason)
    c = replace(candidate(postseason), "sections.summary.0", "This is Game 1 of the NL Wild Card Series.", "series.series_name", "series.game_number", doc=postseason)
    assert "W13.standing" not in check(c, postseason) and "W13.series" not in check(c, postseason)


def test_both_starters_both_teams_and_the_scope_are_covered(doc):
    c = candidate(doc)
    for sentence in wc._all_sentences(c):
        sentence["text"] = (sentence["text"].replace("José Soriano", "Kyle Freeland").replace("Colorado Rockies", "Los Angeles Angels")
                            .replace("Rockies", "Angels").replace(SCOPE, "that stretch"))

    failures = check(c, doc)

    assert "W14.starter" in failures and "W14.team" in failures and "W12.scope" in failures


def test_structure_is_checked(doc):
    c = candidate(doc)
    del c["sections"]["watch"]
    assert "W17.structure" in wc.check_report(c, doc, 1000)

    c = candidate(doc)
    c["summary_lines"] = c["summary_lines"][:2]
    assert "W17.structure" in wc.check_report(c, doc, 1000)

    c = candidate(doc)
    c["sections"]["watch"].append(c["sections"]["watch"][0])
    assert "W17.structure" in wc.check_report(c, doc, 1000)


@pytest.mark.parametrize("ratio,ok", [(0.79, False), (0.80, True), (1.20, True), (1.21, False)])
def test_length_must_be_within_twenty_percent_of_the_rules_report(doc, ratio, ok):
    c = candidate(doc)
    import math

    rules_length = math.floor(length(c) / ratio) if ratio < 1 else math.ceil(length(c) / ratio)

    assert ("W17.length" not in wc.check_report(c, doc, rules_length)) is ok


def test_a_sentence_over_the_security_cap_or_with_markup_is_rejected(doc):
    long = replace(candidate(doc), "sections.arsenal.0", "Kyle Freeland throws his Four-seam. " * 12, "starters.away_starter.pitching_profile.primary_pitch", doc=doc)
    markup = replace(candidate(doc), "sections.arsenal.0", "Kyle Freeland throws his <b>Four-seam</b>.", "starters.away_starter.pitching_profile.primary_pitch", doc=doc)

    assert "W0.sentence" in check(long, doc) and "W0.sentence" in check(markup, doc)


def test_names_compare_after_nfc_normalization(doc):
    import unicodedata

    c = replace(candidate(doc), "headline", unicodedata.normalize("NFD", "Kyle Freeland and José Soriano start this game."), "starters.away_starter.name", "starters.home_starter.name", doc=doc)

    assert "W1.entity" not in check(c, doc)


def test_the_candidate_becomes_the_standard_report_shape_with_the_rules_titles(doc):
    rules = {"headline": "h", "short_summary": ["a", "b", "c"], "sections": [{"title": f"T{i}"} for i in range(6)]}

    report = wc.to_report(candidate(doc), rules)

    assert report["headline"].startswith("Kyle Freeland")
    assert len(report["short_summary"]) == 3 and [s["title"] for s in report["sections"]] == [f"T{i}" for i in range(6)]
    assert report["sections"][4]["bullets"] and "body" in report["sections"][0]


FRE = ("starters.away_starter.pitching_profile.primary_pitch",)
BF = ("starters.away_starter.sample.rates.batters_faced", "starters.home_starter.sample.rates.batters_faced")


@pytest.mark.parametrize("where,text,paths,expected", [
    # review round 1: variants of the guide's own forbidden words
    ("sections.arsenal.0", "Kyle Freeland is unlikely to throw his Four-seam.", FRE, "W3.prediction"),
    ("sections.arsenal.0", "Kyle Freeland might throw his Four-seam.", FRE, "W3.prediction"),
    ("sections.arsenal.0", "Kyle Freeland is winning with his Four-seam.", FRE, "W3.prediction"),
    ("sections.watch.0", "Watch whether Kyle Freeland strikes out the side with his Curveball.", ("starters.away_starter.pitching_profile.putaway_pitch",), "W15.outcome"),
    ("sections.watch.0", "Watch whether Kyle Freeland surrenders runs with his Curveball.", ("starters.away_starter.pitching_profile.putaway_pitch",), "W15.outcome"),
    ("sections.arsenal.0", "Does Kyle Freeland throw his Four-seam", FRE, "W15.question"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam？", FRE, "W15.question"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam, hence the results.", FRE, "W10.cause"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam, thus hitters miss.", FRE, "W10.cause"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam owing to his arm.", FRE, "W10.cause"),
    ("sections.arsenal.0", "Kyle Freeland throws his Four-seam so hitters miss.", FRE, "W10.cause"),
    ("sections.arsenal.0", "Kyle Freeland now throws his Four-seam.", FRE, "W12.time"),
    ("sections.arsenal.0", "Kyle Freeland currently throws his Four-seam.", FRE, "W12.time"),
    ("sections.arsenal.0", "In his recent starts Kyle Freeland threw his Four-seam.", FRE, "W12.time"),
    # numbers: spelled out, and a claimed zero with no zero cited
    ("sections.arsenal.0", "Kyle Freeland has allowed three home runs with his Four-seam.", FRE, "W1.number"),
    ("sections.arsenal.0", "Kyle Freeland has no strikeouts with his Four-seam.", FRE, "W1.number"),
    ("sections.arsenal.0", "Kyle Freeland threw none of his Four-seam.", FRE, "W1.number"),
    # entities: a lone sentence-initial name and a non-ASCII capital
    ("sections.arsenal.0", "Trout is a left-handed hitter facing his Four-seam.", FRE, "W1.entity"),
    ("sections.arsenal.0", "Kyle Freeland faces Álvarez with his Four-seam.", FRE, "W1.entity"),
    ("sections.arsenal.0", "Trout and Skubal watch his Four-seam.", FRE, "W1.entity"),
])
def test_review_round_one_variants_are_rejected(doc, where, text, paths, expected):
    base = candidate(doc)
    c = replace(base, where, text, *paths, doc=doc)

    assert expected in wc.check_report(c, doc, length(base))


def test_a_comparison_must_agree_with_its_numbers_and_use_two_distinct_values(doc):
    def run(text, *paths):
        return check(replace(candidate(doc), "sections.arsenal.0", text, *paths, doc=doc), doc)

    assert "W2.comparison" not in run("Kyle Freeland has faced more batters, 289 against 202 for José Soriano.", *BF[::-1])
    assert "W2.comparison" in run("Kyle Freeland has faced more batters, 202 against 289 for José Soriano.", *BF)
    assert "W2.comparison" in run("Kyle Freeland has faced fewer batters, 289 against 202 for José Soriano.", *BF[::-1])
    assert "W2.comparison" in run("Kyle Freeland has faced more batters: 202 and 202.", BF[0], BF[0])
    assert "W2.comparison" in run("Kyle Freeland has faced 202 batters, which exceeds 289.", *BF)
    assert "W2.comparison" not in run("Kyle Freeland has faced 289 batters, which exceeds 202.", *BF[::-1])


def test_a_malformed_citation_rejects_the_candidate_and_never_crashes(doc):
    def codes(where, text, *paths):
        c = candidate(doc)
        node = c
        for key in where.split("."):
            node = node[int(key)] if isinstance(node, list) else node[key]
        node["text"], node["evidence"] = text, [{"path": p, "value": "1"} for p in paths]
        return wc.check_report(c, doc, length(candidate(doc)))

    movement = "His Curveball moves 0.5 in. sideways and 6.2 in. down compared with a pitch thrown without spin."
    assert "W1.evidence_path" in codes("sections.arsenal.1", movement, "pitch_movement.away_starter.Bogus.h_break", "pitch_movement.away_starter.Bogus.v_break")

    limited = deepcopy(doc)
    limited["starters"]["away_starter"]["sample"]["limited"]["arsenal"] = True
    c = candidate(limited)
    c["sections"]["arsenal"][0]["evidence"] = [{"path": "pitch_mix.0", "value": "x"}]
    assert wc.check_report(c, limited, length(c))  # returns codes, does not raise

    nulled = deepcopy(doc)
    nulled["pitch_movement"]["away_starter"]["Curveball"]["h_break"] = None
    c = candidate(nulled)
    c["sections"]["arsenal"][1]["evidence"] = ev(nulled, "pitch_movement.away_starter.Curveball.h_break", "pitch_movement.away_starter.Curveball.v_break")
    assert "W8.value" in wc.check_report(c, nulled, length(c))


def test_the_guides_own_missing_value_sentence_passes(doc):
    path = "starters.home_starter.pitching_profile.contact_risk_label"
    c = replace(candidate(doc), "sections.home_vs_away.0", "There is not enough data yet to rate the contact risk of José Soriano.", path, doc=doc)

    assert "W7.missing" not in check(c, doc) and "W5.label" not in check(c, doc)
