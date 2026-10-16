"""A value outside a closed map is unknown, not a default (P0.15-D2.2e, F6e and F7).

F6e: a pitch code the name map does not know got the family "Fastball" and, if he threw it most, was named
as the starter's primary pitch ("works off a xx-slider combination"). F7: a team the abbreviation maps do
not know was published as "???". One mechanism: a miss in a closed map keeps the source value, gives
`null` for what it would have derived, and records a warning (it does not change the status of the run).

Decision B (owner, 2026-10-15): the roles are ranked over ALL pitches; a role whose holder is an unmapped
pitch is "Not available", and the report says nothing about that starter's arsenal except why. A role is
never given to the next pitch: calling the second pitch "primary" would be a false statement.

Controls (they pass before the change): a mapped pitch keeps its family, mapped roles keep their pitches.
"""

from __future__ import annotations

import re

import pytest

from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline as lp
from tests.matrix import hard_outcome
from tests.test_live_sample_pipeline import frame

NOT_AVAILABLE = labels.PITCH_NOT_AVAILABLE


# --- the family (F6e) ------------------------------------------------------------------------------------


def test_an_unmapped_pitch_has_no_family_and_a_mapped_one_keeps_its_own():
    movement = lp.compute_movement(frame(n_plain=60), ["Four-seam", "XX"])

    assert movement["Four-seam"]["family"] == "Fastball"
    assert movement["XX"]["family"] is None
    assert movement["XX"]["h_break"] is None and movement["XX"]["v_break"] is None  # nothing measured for a code it cannot name


# --- the roles (decision B) ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "counts,expected",
    [
        ({"Four-seam": 60, "Slider": 40}, ("Four-seam", "Slider")),  # control: all mapped
        ({"Four-seam": 90, "Slider": 10}, ("Four-seam", NOT_AVAILABLE)),  # control: the second is under 15%
        ({"XX": 120, "Slider": 60}, (NOT_AVAILABLE, "Slider")),  # the lead pitch has no name: no primary
        ({"Slider": 100, "XX": 80}, ("Slider", NOT_AVAILABLE)),  # the second has no name: no put-away, at 44%
        ({"Slider": 170, "XX": 10}, ("Slider", NOT_AVAILABLE)),
        ({"XX": 50}, (NOT_AVAILABLE, NOT_AVAILABLE)),
        ({}, (NOT_AVAILABLE, NOT_AVAILABLE)),
    ],
)
def test_a_role_held_by_an_unmapped_pitch_is_not_available_and_never_passes_to_the_next(counts, expected):
    assert labels.profile_pitches(counts) == expected


def test_the_share_of_a_role_is_taken_on_all_the_pitches_of_the_starter():
    """The mix keeps the top five pitches; the total is the starter's, so it is given."""

    assert labels.profile_pitches({"Four-seam": 300, "Slider": 55}, total=400) == ("Four-seam", NOT_AVAILABLE)  # 13.75% of 400
    assert labels.profile_pitches({"Four-seam": 300, "Slider": 55}) == ("Four-seam", "Slider")  # 15.5% of the two


def test_a_pitch_is_mapped_if_the_family_map_names_it():
    assert labels.is_mapped_pitch("Slider") and not labels.is_mapped_pitch("XX")


# --- through the pipeline, the generator, the report and the contract ----------------------------------------


@pytest.fixture(scope="module")
def unmapped():
    return hard_outcome("unmapped_pitch_code")


def report_text(outcome) -> str:
    report = outcome.matchup["report"]
    parts = [report["headline"], *report["short_summary"]]
    for section in report["sections"]:
        parts += [section.get("body") or "", *section.get("bullets", [])]
    return "\n".join(parts)


def test_the_source_value_is_kept_and_its_family_is_null(unmapped):
    matchup = unmapped.matchup

    assert "XX" in [row["pitch"] for row in matchup["charts"]["pitch_mix"]]
    assert matchup["charts"]["pitch_movement"]["away_starter"]["XX"]["family"] is None
    assert matchup["charts"]["pitch_movement"]["away_starter"]["Slider"]["family"] == "Breaking"  # control


def test_his_roles_are_not_available_where_an_unmapped_pitch_holds_them(unmapped):
    profile = unmapped.matchup["starters"]["away_starter"]["pitching_profile"]

    assert profile["primary_pitch"] == NOT_AVAILABLE
    assert profile["putaway_pitch"] == "Slider"
    assert profile["style_label"] == labels.ARSENAL_LIMITED_STYLE
    assert unmapped.matchup["starters"]["away_starter"]["sample"]["limited"]["arsenal"] is False


def test_a_warning_is_recorded_and_the_run_is_still_ok(unmapped):
    warnings = [w for w in unmapped.record["warnings"] if (w["source"], w["code"]) == ("statcast_pitcher", "unmapped_pitch_type")]

    assert len(warnings) == 1 and "XX" in warnings[0]["message"]
    assert unmapped.record["status"] == "ok" and unmapped.record["errors"] == []


def test_no_sentence_names_the_unmapped_pitch_and_the_report_says_why(unmapped):
    text = report_text(unmapped)

    assert not re.search(r"\bxx\b", text, re.IGNORECASE)
    assert "Away Ace throws pitches the data does not name, so this report makes no arsenal claim for him." in text
    assert "Away Ace works off" not in text
    assert unmapped.matchup["report"]["headline"] == "Away Ace against Home Ace"  # the names, not the styles


def test_control_the_other_starter_is_described_as_before(unmapped):
    text = report_text(unmapped)

    assert "Home Ace works off" in text and "four-seam" in text.lower()


def test_the_critic_names_no_pitch_for_him(unmapped):
    checks = unmapped.matchup["critic_review"]["checks"]

    assert not any(check["status"] == "unsupported" for check in checks)
    assert "XX" not in " ".join(check["claim"] for check in checks if "Away Ace" in check["claim"])


def test_the_published_file_passes_publication_and_the_contract(unmapped):
    assert unmapped.blocked is None and unmapped.failed == []
    assert not [v for v in unmapped.violations if "family" in v.code or v.code.startswith("rule4:analyst.")]


# --- the team (F7) -----------------------------------------------------------------------------------------


def test_the_abbreviation_of_a_team_the_maps_do_not_know_is_none():
    assert lp._team_abbreviation({"id": 999, "name": "Brand New Club"}) is None
    assert lp._team_abbreviation({"id": 999, "name": "Brand New Club", "abbreviation": "BNC"}) == "BNC"  # control
    assert lp._team_abbreviation({"id": 147, "name": "New York Yankees"}) == "NYY"  # control


@pytest.fixture(scope="module")
def unknown_team():
    return hard_outcome("unknown_team")


def test_a_team_with_no_abbreviation_is_published_by_its_name(unknown_team):
    matchup = unknown_team.matchup

    assert matchup["teams"]["away"]["name"] == "Brand New Club" and matchup["teams"]["away"]["abbreviation"] is None
    assert matchup["starters"]["away_starter"]["team"] is None
    assert matchup["teams"]["home"]["abbreviation"] == "NYY" and matchup["starters"]["home_starter"]["team"] == "NYY"  # control
    assert unknown_team.payload["archive"][0]["title"] == "Brand New Club vs NYY"


def test_an_unknown_team_has_no_offense_split_and_the_run_says_why(unknown_team):
    assert unknown_team.matchup["teams"]["away"]["offense_profile"]["ops_vs_hand"] is None
    warnings = [w for w in unknown_team.record["warnings"] if (w["source"], w["code"]) == ("savant_team_batting", "unknown_team")]

    assert len(warnings) == 1 and "999" in warnings[0]["message"]
    assert unknown_team.record["status"] == "ok" and unknown_team.record["errors"] == []


def test_the_file_with_an_unknown_team_passes_publication_and_has_no_placeholder(unknown_team):
    assert unknown_team.failed == []
    assert "???" not in str(unknown_team.payload)
    assert not [v for v in unknown_team.violations if "abbreviation" in v.code or v.code.endswith("starters.*.team")]


def test_a_game_that_is_skipped_is_named_by_its_team_name_when_it_has_no_abbreviation():
    assert labels.team_label(None, "Brand New Club") == "Brand New Club"
    assert lp.game_label({"away_team_abbr": None, "away_team": "Brand New Club", "home_team_abbr": "NYY", "home_team": "New York Yankees"}) == "Brand New Club @ NYY"


# --- why there is no contrast (a separate sentence for an unnamed arsenal) -----------------------------------------

NO_CONTRAST_LIMITED = "No arsenal contrast is drawn because at least one arsenal has too little data."
NO_CONTRAST_UNNAMED = "No arsenal contrast is drawn because one starter's pitches are not named in the data."


def arsenal_scout(outcome) -> str:
    return next(s["body"] for s in outcome.matchup["report"]["sections"] if s["title"] == "Arsenal Scout")


def test_the_report_says_the_contrast_is_missing_because_a_starters_pitches_are_not_named(unmapped):
    body = arsenal_scout(unmapped)

    assert body.endswith(NO_CONTRAST_UNNAMED)
    assert "too little data" not in body


def test_control_a_limited_arsenal_keeps_the_sentence_about_too_little_data():
    outcome = hard_outcome("two_limited")

    assert arsenal_scout(outcome).endswith(NO_CONTRAST_LIMITED)
    assert "not named" not in arsenal_scout(outcome)


@pytest.fixture
def unnamed_payload(monkeypatch):
    from tests.corpus import golden_payload, published

    return published(golden_payload(monkeypatch, "live_unnamed_lead_pitch"))


def test_rule_4_the_unnamed_sentence_needs_a_starter_whose_pitches_have_no_name(unnamed_payload):
    from tests.test_contract_checks import added, codes

    assert not {c for c in codes(unnamed_payload) if c.startswith("rule4:writer.arsenal.no_contrast")}

    def name_the_pitch(m):
        m["starters"]["away_starter"]["pitching_profile"]["primary_pitch"] = "Slider"

    assert "rule4:writer.arsenal.no_contrast_unnamed#unnamed" in added(unnamed_payload, name_the_pitch)


def test_rule_4_the_unnamed_sentence_is_not_the_one_for_a_limited_arsenal(unnamed_payload):
    from tests.test_contract_checks import added

    def limit_the_other(m):
        sample = m["starters"]["home_starter"]["sample"]
        sample["arsenal"]["pitches"] = 40
        sample["limited"]["arsenal"] = True

    assert "rule4:writer.arsenal.no_contrast_unnamed#limited" in added(unnamed_payload, limit_the_other)
