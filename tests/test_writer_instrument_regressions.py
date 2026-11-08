"""Run-4 rigidity positives and strict accuracy controls, tested on dev only."""
from copy import deepcopy

import pytest
import json

from agents import writer_checks as wc, writer_input as wi
from pathlib import Path
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals/data/dataset"
REGRESSIONS = json.loads((DATASET.parent / "writer/run4-gate-regressions.json").read_text(encoding="utf-8"))["findings"]
OWNER_CONTROLS = json.loads((DATASET.parent / "writer/owner-binding-regressions.json").read_text(encoding="utf-8"))


def document(case="postseason-849842"):
    return wi.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case), wi.load_glossary(DATASET / "glossary.json"))


def findings(doc, text, paths):
    index = wi.evidence_index(doc)
    sentence = {"text": text, "evidence": [{"path": p, "value": wc._value_text(index[p])} for p in paths]}
    out = []
    wc._check_sentence(sentence, text, doc, index, wc._phrases(doc, index), wc._vocabulary(doc, index),
                       doc["glossary"], set(), lambda code, token=None: out.append(code))
    return out


def test_all_47_original_findings_have_provenance_and_expectations():
    assert len(REGRESSIONS) == 47
    assert sum(r["token"] == "10.4" for r in REGRESSIONS) == 1
    assert all(len(r["source_sha256"]) == 64 and r["expectation"] and r["prior_verdict"] for r in REGRESSIONS)


@pytest.mark.parametrize("row", OWNER_CONTROLS, ids=lambda r: f"run{r['run']}-{r['case']}-{r['attempt']}")
def test_supported_owner_comparison_and_affiliation_phrasing_is_not_rejected(row):
    assert len(row["source_sha256"]) == 64
    assert "W1.number" not in findings(document(row["case"]), row["text"], row["paths"])


@pytest.mark.parametrize("row", [r for r in REGRESSIONS if r["expectation"] == "check_specific_must_pass"], ids=lambda r: f"{r['case']}-{r['attempt']}-{r['check']}")
def test_every_prior_rigidity_verdict_passes_its_named_check(row):
    from agents import fact_table as ft
    doc = document(row["case"])
    table = ft.build_fact_table(doc)
    ids = [table.id_for_path(e["path"]) for e in row["original_evidence"]]
    assert all(ids), "rigidity control must have strict source bindings"
    resolved = ft.resolve_fact_ids(list(dict.fromkeys(ids)), table)
    checked = findings(doc, row["sentence"], [e["path"] for e in resolved])
    if row["check"] == "W2.comparison" and (row["case"], row["sentence"]) not in {
        ("opener-823769", "Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup"),
        ("limited-823836", "The Angels lineup has a .687 OPS versus right-handed pitching."),
    }:
        assert row["check"] in checked  # D62 supersedes historical comparison permission.
    else:
        assert row["check"] not in checked


@pytest.mark.parametrize("text,paths", [
    ("Probable pitchers are listed for this matchup.", ["data_confidence.lineup_status"]),
    ("Findings indicate Atlanta has strong OPS against this pitcher's hand; draws walks at an above-average rate.", ["findings.lineup_notes.away"]),
])
def test_common_sentence_openers_are_not_entities(text, paths):
    assert "W1.entity" not in findings(document("limited-825104"), text, paths)


def test_second_physical_sentence_opener_is_not_an_entity():
    doc = document("opener-824280")
    text = "The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%)."
    paths = [f"teams.away.offense_profile.{k}" for k in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand")]
    assert "W1.entity" not in findings(doc, text, paths)


@pytest.mark.parametrize("name", ["Mike Trout", "Shohei Ohtani", "Invented Club"])
def test_unknown_entities_at_second_sentence_start_still_fail(name):
    assert "W1.entity" in findings(document(), f"The starters are listed. {name} starts.", ["data_confidence.lineup_status"])


def test_split_scope_versus_is_not_a_comparison():
    doc = document("limited-823836")
    assert "W2.comparison" not in findings(doc, "The Angels lineup has a .687 OPS versus right-handed pitching.", ["teams.away.offense_profile.ops_vs_hand"])


def test_matchup_versus_is_not_a_comparison():
    doc = document("opener-823769")
    assert "W2.comparison" not in findings(doc, "Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup", ["starters.away_starter.name", "starters.home_starter.name", "teams.away.name", "teams.home.name"])


PAIRS = [f"starters.{s}.season_summary.{k}_number" for k in ("era", "whip") for s in ("home_starter", "away_starter")]
MULTI = "Pivetta has a lower ERA (2.86 vs 4.51) and a lower WHIP (1.01 vs 1.27) than Gausman."


def test_d62_several_true_cited_pairs_are_forbidden():
    assert "W2.comparison" in findings(document(), MULTI, PAIRS)


def test_d62_comparisons_with_changing_subject_are_forbidden():
    text = "Gausman has a higher ERA (4.51 vs 2.86) than Pivetta, while Pivetta has a lower WHIP (1.01 vs 1.27) than Gausman."
    assert "W2.comparison" in findings(document(), text, PAIRS)


@pytest.mark.parametrize("text,paths", [(MULTI.replace("lower WHIP", "higher WHIP"), PAIRS), (MULTI, PAIRS[:-1])])
def test_wrong_or_unsupported_pair_stays_strict(text, paths):
    assert "W2.comparison" in findings(document(), text, paths)


def test_different_cutoff_is_not_equal_scope():
    doc = document()
    doc["starters"]["away_starter"]["season_summary"]["scopes"]["season_rates"]["through"] = "2026-09-28"
    assert "W2.comparison" in findings(doc, MULTI, PAIRS)


def test_comparison_cannot_swap_owners_or_measures():
    assert "W2.comparison" in findings(document(), MULTI.replace("Pivetta", "Gausman").replace("than Gausman", "than Pivetta"), PAIRS)
    assert "W2.comparison" in findings(document(), MULTI.replace("ERA", "WHIP", 1), PAIRS)


@pytest.mark.parametrize("bad", ["2026-09-28", "Sep 28", "Oct 29"])
def test_wrong_cutoff_cannot_borrow_other_cited_numbers(bad):
    doc = document()
    doc["starters"]["away_starter"]["season_summary"]["innings"] = "28.0"
    paths = ["starters.away_starter.sample.arsenal.scope.label", "starters.away_starter.sample.arsenal.scope.through", "starters.away_starter.season_summary.innings"]
    assert "W12.time" in findings(doc, f"The pitch figures cover the 2026 regular season through {bad}.", paths)


def test_true_natural_scope_and_scope_owner_controls():
    doc = document()
    paths = ["starters.away_starter.sample.arsenal.scope.label", "starters.away_starter.sample.arsenal.scope.through"]
    assert "W12.time" not in findings(doc, "Gausman's pitch figures cover the 2026 regular season through Sep 29.", paths)
    assert "W12.time" in findings(doc, "Pivetta's pitch figures cover the 2026 regular season through Sep 29.", paths)
    other = deepcopy(doc)
    other["starters"]["home_starter"]["sample"]["arsenal"]["scope"]["through"] = "2026-09-28"
    assert "W12.time" in findings(other, "All figures cover the 2026 regular season through Sep 29.", paths)
    other = deepcopy(doc)
    other["starters"]["home_starter"]["sample"]["arsenal"]["scope"]["label"] = "2026 regular season and postseason"
    assert "W12.time" in findings(other, "All figures cover the 2026 regular season through Sep 29.", paths)


def test_starter_scope_may_name_his_own_team():
    doc = document("limited-825104")
    paths = ["starters.away_starter.season_summary.scopes.season_rates.label", "starters.away_starter.season_summary.scopes.season_rates.through"]
    assert "W12.time" not in findings(doc, "Bryce Elder's ERA for Atlanta covers the 2026 regular season through Apr 3.", paths)


def test_both_supported_missing_labels_allow_cause_but_official_still_fails():
    doc = document("limited-825104")
    paths = []
    for slot in wi.SLOTS:
        paths += [f"starters.{slot}.sample.rates.batters_faced"]
        for dim, label in (("control", "command"), ("strikeout", "swing_miss")):
            paths += [f"starters.{slot}.sample.limited.{dim}", f"starters.{slot}.sample.thresholds.{dim}", f"starters.{slot}.pitching_profile.{label}_label"]
    original = "Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples."
    assert "W10.cause" not in findings(doc, original, paths)
    assert "W1.authority" in findings(doc, original, paths)
    assert not findings(doc, original.replace("official ", ""), paths)


def test_wrong_measure_does_not_borrow_a_coincident_value():
    doc = document()
    doc["starters"]["away_starter"]["season_summary"]["era_number"] = 10.4
    paths = ["starters.away_starter.season_summary.era_number", "teams.away.offense_profile.bb_rate_vs_hand"]
    assert "W1.number" in findings(doc, "That group has a 10.4% walk rate (BB%).", paths)


def test_measure_cannot_borrow_an_opponents_fact():
    doc = document()
    paths = ["starters.home_starter.season_summary.era_number", "starters.away_starter.name"]
    assert "W1.number" in findings(doc, "Gausman has a 2.86 ERA.", paths)
    assert "W1.number" not in findings(doc, "Pivetta has a 2.86 ERA.", paths)
    doc = document("opener-824280")
    paths = ["teams.home.offense_profile.ops_number", "teams.away.name"]
    assert "W1.number" in findings(doc, "Toronto has a .725 OPS.", paths)


@pytest.mark.parametrize("text", [
    "Gausman has a 4.51 ERA; Pivetta has a 2.86 ERA.",
    "Gausman has a 4.51 ERA. Pivetta has a 2.86 ERA.",
    "Gausman has a 4.51 ERA and Pivetta has a 2.86 ERA.",
    "A 4.51 ERA for Gausman and a 2.86 ERA for Pivetta.",
    "Gausman's 4.51 ERA versus Pivetta's 2.86 ERA.",
    "The away starter has a 4.51 ERA, while the home starter has a 2.86 ERA.",
])
def test_each_measurement_keeps_its_owner_in_multi_subject_text(text):
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    assert "W1.number" not in findings(document(), text, paths)
    swapped = text.replace("4.51", "SWAP").replace("2.86", "4.51").replace("SWAP", "2.86")
    assert "W1.number" in findings(document(), swapped, paths)


def test_valid_comparison_does_not_license_a_separate_owner_swap():
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    text = "Pivetta has a lower ERA (2.86 vs 4.51) than Gausman; Gausman has a 2.86 ERA."
    assert "W1.number" in findings(document(), text, paths)


def test_multi_subject_lineup_rates_keep_their_owners():
    doc = document("opener-824280")
    paths = [f"teams.{side}.offense_profile.ops_number" for side in wi.SIDES]
    assert "W1.number" not in findings(doc, "Toronto has a .701 OPS and Detroit has a .725 OPS.", paths)
    assert "W1.number" in findings(doc, "Toronto has a .725 OPS and Detroit has a .701 OPS.", paths)


def test_inherited_owner_and_two_comparison_pairs_remain_supported():
    text = "Gausman has a 4.51 ERA and a 1.27 WHIP; Pivetta has a 2.86 ERA and a 1.01 WHIP."
    assert "W1.number" not in findings(document(), text, PAIRS)
    assert "W1.number" not in findings(document(), MULTI, PAIRS)


@pytest.mark.parametrize("correct,wrong", [
    ("Gausman has a 4.51 ERA and a 1.27 WHIP for Chicago.", "Gausman has a 4.51 ERA and a 1.01 WHIP for Chicago."),
    ("Pivetta has a lower ERA (2.86 vs 4.51) than Gausman, who holds a 4.51 ERA.", "Pivetta has a lower ERA (2.86 vs 4.51) than Gausman, who holds a 2.86 ERA."),
    ("Pivetta has a 2.86 ERA and a 1.01 WHIP compared with the 4.51 ERA and 1.27 WHIP of Gausman.", "Pivetta has a 2.86 ERA and a 1.01 WHIP compared with the 4.51 ERA and 1.01 WHIP of Gausman."),
])
def test_supported_owner_frames_do_not_license_opponents_values(correct, wrong):
    assert "W1.number" not in findings(document(), correct, PAIRS)
    assert "W1.number" in findings(document(), wrong, PAIRS)


def test_shared_subject_claim_cannot_borrow_only_one_players_value():
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    assert "W1.number" in findings(document(), "Gausman and Pivetta have 2.86 and 2.86 ERA respectively.", paths)
    doc = document()
    doc["starters"]["away_starter"]["season_summary"]["era_number"] = 2.86
    doc["starters"]["away_starter"]["season_summary"]["era"] = "2.86"
    assert "W1.number" not in findings(doc, "Gausman and Pivetta have a 2.86 ERA.", paths)


def test_shared_role_claim_requires_both_owners_even_without_names():
    doc = document("limited-825104")
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    text = "Both starters have a 0.00 ERA."
    assert "W1.number" not in findings(doc, text, paths)
    assert "W1.number" in findings(doc, text, paths[:1])


def test_postpositive_shared_owners_each_need_the_value():
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    text = "A 4.51 ERA for Gausman and Pivetta."
    assert "W1.number" in findings(document(), text, paths)
    doc = document()
    doc["starters"]["home_starter"]["season_summary"]["era_number"] = 4.51
    doc["starters"]["home_starter"]["season_summary"]["era"] = "4.51"
    assert "W1.number" not in findings(doc, text, paths)


@pytest.mark.parametrize("text,path", [
    ("Chicago has a 4.51 ERA.", "starters.away_starter.season_summary.era_number"),
    ("A 4.51 ERA for Chicago.", "starters.away_starter.season_summary.era_number"),
    ("Gausman has a .757 OPS.", "teams.away.offense_profile.ops_number"),
])
def test_explicit_owner_of_wrong_measure_type_cannot_fall_back_to_citation(text, path):
    assert "W1.number" in findings(document(), text, [path])


def test_comparison_role_names_cannot_swap_owners():
    paths = [f"starters.{s}.season_summary.era_number" for s in ("home_starter","away_starter")]
    assert "W2.comparison" in findings(document(), "The away starter has a lower ERA, 2.86 versus 4.51.", paths)


@pytest.mark.parametrize("text", ["The command rating for Hagen Smith is missing due to a limited sample and home runs.", "The command rating for Hagen Smith is missing due to a limited sample, so hitters miss.",
    "The command rating for Hagen Smith is missing and hitters miss due to a limited sample.",
    "The command rating for Hagen Smith is not missing due to a limited sample."])
def test_sample_proof_does_not_license_extra_causal_consequences(text):
    doc = document("postseason-849849")
    prefix = "starters.away_starter."
    paths = [prefix + p for p in ("sample.limited.control", "sample.rates.batters_faced", "sample.thresholds.control", "pitching_profile.command_label")]
    assert "W10.cause" in findings(doc, text, paths)


@pytest.mark.parametrize("text", [
    "Watch if AJ Blubaugh encounters deep-count traffic and home runs due to his command.",
    "Watch if AJ Blubaugh avoids deep-count traffic due to his command.",
])
def test_finding_cause_does_not_license_extra_or_reversed_consequence(text):
    assert "W10.cause" in findings(document("postseason-849849"), text, ["findings.home_starter_risks"])


@pytest.mark.parametrize("text", [
    "Gausman's pitch figures cover the 2026 regular season and postseason through Sep 29.",
    "All figures cover the 2026 regular season and postseason through Sep 29.",
    "Gausman's pitch figures cover the 2026 postseason through Sep 29.",
    "Gausman's pitch figures cover the 2026 regular season and postseason.",
])
def test_scope_kind_must_match_its_evidence(text):
    paths = ["starters.away_starter.sample.arsenal.scope.label", "starters.away_starter.sample.arsenal.scope.through"]
    assert "W12.time" in findings(document(), text, paths)


def test_combined_season_scope_has_both_positive_and_subset_negative_controls():
    doc = document()
    doc["starters"]["away_starter"]["sample"]["arsenal"]["scope"]["label"] = "2026 regular season and postseason"
    paths = ["starters.away_starter.sample.arsenal.scope.label", "starters.away_starter.sample.arsenal.scope.through"]
    assert "W12.time" not in findings(doc, "Gausman's pitch figures cover the 2026 regular season and postseason through Sep 29.", paths)
    assert "W12.time" in findings(doc, "Gausman's pitch figures cover the 2026 regular season through Sep 29.", paths)


def test_split_scope_must_match_cited_lineup_hand_without_a_numeric_comparison():
    doc = document("limited-823836")
    paths = ["teams.away.offense_profile.ops_vs_hand"]
    assert "W12.time" in findings(doc, "The Angels lineup has a .687 OPS versus left-handed pitching.", paths)
    assert "W2.comparison" not in findings(doc, "The Angels lineup has a .687 OPS versus right-handed pitching.", paths)


def test_postseason_game_context_is_not_a_figure_scope_claim():
    doc = document("postseason-849849")
    assert "W12.time" not in findings(doc, "Chicago and Houston play in this postseason matchup.", ["teams.away.name", "teams.home.name", "series.series_name"])


def test_lineup_finding_retains_its_verified_handedness_context():
    doc = document()
    paths = ["findings.lineup_notes.away"]
    assert "W12.time" not in findings(doc, "They draw walks at an above-average rate against right-handed pitchers.", paths)
    assert "W12.time" in findings(doc, "They draw walks at an above-average rate against left-handed pitchers.", paths)


def test_wrong_value_stays_a_real_error():
    assert "W1.number" in findings(document(), "That group shows a 21.2% strikeout rate (K%) and a 10.4% walk rate (BB%).",
                                    ["teams.away.offense_profile.k_rate_vs_hand", "teams.away.offense_profile.bb_rate_vs_hand"])


def test_cited_finding_cause_is_supported_but_unrelated_consequence_is_not():
    doc = document("postseason-849849")
    paths = ["findings.home_starter_risks"]
    text = "Watch if AJ Blubaugh encounters deep-count traffic due to his command."
    assert "W10.cause" not in findings(doc, text, paths)
    assert "W10.cause" in findings(doc, text.replace("deep-count traffic", "home runs"), paths)
    assert "W10.cause" in findings(doc, text.replace("AJ Blubaugh", "Hagen Smith"), paths)


def test_limited_rule_requires_all_proof_and_rejects_official():
    doc = document("postseason-849849")
    prefix = "starters.away_starter."
    paths = [prefix + p for p in ("sample.limited.control", "sample.rates.batters_faced", "sample.thresholds.control", "pitching_profile.command_label")]
    text = "The command rating for Hagen Smith is missing due to a limited sample."
    assert "W10.cause" not in findings(doc, text, paths)
    assert "W10.cause" in findings(doc, text, paths[:-1])
    assert "W1.authority" in findings(doc, text.replace("command rating", "official command rating"), paths)
    equal = deepcopy(doc)
    equal["starters"]["away_starter"]["sample"]["rates"]["batters_faced"] = 170
    assert "W10.cause" in findings(equal, text, paths)


@pytest.mark.parametrize("relation", ["lower", "higher", "more", "fewer", "faster", "slower", "better", "worse", "than", "versus", "vs", "compared with", "compared to"])
def test_d62_forbids_comparing_even_correct_cited_figures(relation):
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    text = f"Pivetta has a 2.86 ERA {relation} Gausman's 4.51 ERA."
    assert "W2.comparison" in findings(document(), text, paths)


@pytest.mark.parametrize("object_name", ["home starter", "away starter", "Chicago"])
def test_d62_round_three_comparison_is_forbidden_even_if_relation_is_true(object_name):
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    text = f"Pivetta has a lower ERA (2.86 vs 4.51) than the {object_name}."
    assert "W2.comparison" in findings(document(), text, paths)


def test_d62_side_by_side_control_passes_and_swapped_owners_fail():
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    assert not findings(document(), "Pivetta has a 2.86 ERA and Gausman a 4.51 ERA.", paths)
    assert "W1.number" in findings(document(), "Pivetta has a 4.51 ERA and Gausman a 2.86 ERA.", paths)


def test_d62_matchup_word_cannot_license_versus_between_figures():
    paths = [f"starters.{slot}.season_summary.era_number" for slot in wi.SLOTS]
    assert "W2.comparison" in findings(document(), "Pivetta has a 2.86 ERA versus Gausman's 4.51 ERA in this matchup.", paths)


@pytest.mark.parametrize("text,expected", [
    ("Kyle Freeland brings below-average command to the mound for Colorado.", True),
    ("Kyle Freeland brings average command to the mound for Colorado.", True),
    ("Kyle Freeland brings solid command to the mound for Colorado.", False),
    ("Kyle Freeland brings SOLID COMMAND to the mound for Colorado.", False),
    ("Kyle Freeland's command is below-average.", True),
    ("Kyle Freeland's command is solid.", False),
])
def test_d63_stored_freeland_label_must_match_cited_value(text, expected):
    checked = findings(document("veteran-824027"), text, ["starters.away_starter.pitching_profile.command_label"])
    assert ("W5.label" in checked) == expected


@pytest.mark.parametrize("field,value,correct,wrong", [
    ("swing_miss_label", "Average swing-and-miss ability", "average swing-and-miss ability", "below-average swing-and-miss ability"),
    ("contact_risk_label", "Low-to-moderate contact risk", "low-to-moderate contact risk", "elevated contact risk"),
    ("command_label", "Below-average command", "below average command", "average command"),
    ("style_label", "Four-seam-Curveball starter", "Four-seam-Curveball starter", "Sinker-Curveball starter"),
])
def test_d63_each_label_type_matches_full_normalized_value(field, value, correct, wrong):
    doc = document("veteran-824027")
    doc["starters"]["away_starter"]["pitching_profile"][field] = value
    paths = [f"starters.away_starter.pitching_profile.{field}"]
    assert "W5.label" not in findings(doc, f"Kyle Freeland shows {correct}.", paths)
    assert "W5.label" in findings(doc, f"Kyle Freeland shows {wrong}.", paths)


@pytest.mark.parametrize("correct,wrong", [
    ("Atlanta has strong OPS against this pitcher's hand.", "Atlanta has weak OPS against this pitcher's hand."),
    ("Atlanta draws walks at an above-average rate.", "Atlanta draws walks at a below-average rate."),
])
def test_d63_lineup_note_label_values_are_not_a_bag_of_words(correct, wrong):
    doc = document("limited-825104")
    paths = ["findings.lineup_notes.away"]
    assert "W5.label" not in findings(doc, correct, paths)
    assert "W5.label" in findings(doc, wrong, paths)


def test_d63_intensity_from_one_note_cannot_license_a_different_phrase():
    doc = document("limited-825104")
    paths = ["findings.lineup_notes.away"]
    assert "W5.intensity" not in findings(doc, "Atlanta has strong OPS.", paths)
    assert "W5.intensity" in findings(doc, "Atlanta has strong command.", paths)
    assert "W5.intensity" in findings(doc, "Atlanta has very strong OPS.", paths)


def test_d63_lineup_rate_label_keeps_its_dimension():
    doc = document("limited-825104")
    paths = ["findings.lineup_notes.away"]
    assert "W5.label" not in findings(doc, "Atlanta draws walks at an above-average rate.", paths)
    assert "W5.label" in findings(doc, "Atlanta strikes out at an above-average rate.", paths)


@pytest.mark.parametrize("style", ["curveball-four-seam starter", "curveball four seam starter", "knuckleball-four-seam starter", "power starter"])
def test_d63_absent_style_value_cannot_escape_the_matcher(style):
    doc = document("veteran-824027")
    path = "starters.away_starter.pitching_profile.style_label"
    assert doc["starters"]["away_starter"]["pitching_profile"]["style_label"] == "Four-seam-Curveball starter"
    assert "W5.label" in findings(doc, f"Kyle Freeland shows {style}.", [path])


@pytest.mark.parametrize("text", [
    "Kyle Freeland shows four-seam-curveball starter.",
    "Kyle Freeland is a four seam curveball starter.",
])
def test_d63_matching_lowercase_style_control(text):
    assert "W5.label" not in findings(document("veteran-824027"), text, ["starters.away_starter.pitching_profile.style_label"])


def test_d63_starter_role_is_not_a_style_label_control():
    assert "W5.label" not in findings(document("veteran-824027"), "Kyle Freeland is the away starter.", ["starters.away_starter.name"])


@pytest.mark.parametrize("text", [
    "Kyle Freeland is the away starter's namesake.",
    "The Rockies is the home team and the visiting starter’s lineup is set.",
    "Kyle Freeland is a probable starter's equal.",
])
def test_d63_starter_possessive_is_not_a_style_label(text):
    """Word boundary: "starter's" is the role word with a possessive, not a style label."""
    assert "W5.label" not in findings(document("veteran-824027"), text, ["starters.away_starter.name"])


@pytest.mark.parametrize("text", [
    "Kyle Freeland is a 'finesse-power starter' tonight.",
    "Kyle Freeland is a ‘finesse-power starter’ tonight.",
    "Kyle Freeland is a “finesse-power starter” tonight.",
])
def test_d63_quoted_wrong_style_label_still_fails(text):
    """The possessive exclusion must not hide a label that ends in a closing quote."""
    assert "W5.label" in findings(document("veteran-824027"), text, ["starters.away_starter.name"])


def test_d63_unlisted_hyphenated_starter_style_still_fails_control():
    assert "W5.label" in findings(document("veteran-824027"), "Kyle Freeland shows a sinker-slider starter.", ["starters.away_starter.name"])


@pytest.mark.parametrize("text", [
    "Kyle Freeland brings erratic command to the mound for Colorado.",
    "Kyle Freeland brings solid-esque command to the mound for Colorado.",
    "Kyle Freeland's command is erratic.",
])
def test_d63_unlisted_asserted_label_value_is_still_checked(text):
    assert "W5.label" in findings(document("veteran-824027"), text, ["starters.away_starter.pitching_profile.command_label"])


@pytest.mark.parametrize("text,case,paths", [
    ("Watch if the Angels swing-and-miss risk shows up against the Sweeper from Phillips.", "limited-823836", ["findings.lineup_notes.away"]),
    ("Watch whether the Milwaukee hitters can control their strikeout rate against a left-handed starter.", "opener-823769", ["starters.away_starter.throws"]),
    ("The Chicago Cubs have a higher OPS (.757 vs .722) than the San Diego Padres.", "postseason-849842", ["teams.away.offense_profile.ops_number", "teams.home.offense_profile.ops_number"]),
])
def test_d63_names_handedness_and_numeric_comparators_are_not_label_modifiers(text, case, paths):
    assert "W5.label" not in findings(document(case), text, paths)
