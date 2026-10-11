"""Rate-based labels, D24 sample thresholds and data scopes (PLAN.md P0.5).

Phase 0 Gherkin: "Limited sample is flagged, not filled" and "Labels use rates,
not counts". Pure functions, nothing fetched.
"""

from __future__ import annotations

import pytest

from data_pipeline import labels

REG = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")
REG_POST = labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-07-14")


def sample(pitches=500, bf=400, k=90, bb=30, hr=10, arsenal_scope=REG, rates_scope=REG):
    return labels.build_sample(
        pitches=pitches,
        arsenal_scope=arsenal_scope,
        batters_faced=bf,
        strikeouts=k,
        walks=bb,
        home_runs=hr,
        rates_source="mlb_api",
        rates_scope=rates_scope,
    )


# --- D24 thresholds ---------------------------------------------------------------


def test_thresholds_are_the_approved_d24_values():
    assert labels.THRESHOLDS == {"arsenal": 100, "strikeout": 70, "control": 170}


@pytest.mark.parametrize("pitches, limited", [(99, True), (100, False), (0, True)])
def test_arsenal_threshold_is_100_pitches(pitches, limited):
    assert sample(pitches=pitches)["limited"]["arsenal"] is limited


@pytest.mark.parametrize("bf, limited", [(69, True), (70, False), (0, True)])
def test_strikeout_threshold_is_70_batters_faced(bf, limited):
    assert sample(bf=bf, k=10)["limited"]["strikeout"] is limited


@pytest.mark.parametrize("bf, limited", [(169, True), (170, False), (0, True)])
def test_control_threshold_is_170_batters_faced(bf, limited):
    assert sample(bf=bf, bb=10)["limited"]["control"] is limited


def test_dimensions_are_independent():
    flags = sample(pitches=60, bf=120, k=30, bb=10)["limited"]

    assert flags == {"arsenal": True, "strikeout": False, "control": True}


def test_a_missing_number_is_limited_never_zero():
    missing = labels.build_sample(
        pitches=500,
        arsenal_scope=REG,
        batters_faced=None,
        strikeouts=None,
        walks=None,
        home_runs=None,
        rates_source="mlb_api",
        rates_scope=REG,
    )

    assert missing["limited"] == {"arsenal": False, "strikeout": True, "control": True}
    assert labels.strikeout_label(missing) is None
    assert labels.control_label(missing) is None


def test_a_missing_count_with_enough_batters_is_still_limited():
    s = sample(bf=400, k=None, bb=None)

    assert s["limited"]["strikeout"] and s["limited"]["control"]


# --- labels come from rates ---------------------------------------------------------


@pytest.mark.parametrize(
    "k, expected",
    [
        (50, "Above-average swing-and-miss ability"),  # 25.0% of 200
        (49, "Average swing-and-miss ability"),  # 24.5%
        (36, "Average swing-and-miss ability"),  # 18.0%
        (35, "Below-average swing-and-miss ability"),  # 17.5%
    ],
)
def test_strikeout_label_bands(k, expected):
    assert labels.strikeout_label(sample(bf=200, k=k)) == expected


@pytest.mark.parametrize(
    "bb, expected",
    [
        (14, "Solid command"),  # 7.0% of 200
        (15, "Average command"),  # 7.5%
        (19, "Average command"),  # 9.5%
        (20, "Below-average command"),  # 10.0%
    ],
)
def test_control_label_bands(bb, expected):
    assert labels.control_label(sample(bf=200, bb=bb)) == expected


def test_same_walk_rate_with_different_innings_gets_the_same_label():
    # Gherkin "Labels use rates, not counts": 15 walks in 200 BF and 45 in 600 BF
    # are both 7.5%, so they must get the same command label.
    short = labels.control_label(sample(bf=200, bb=15))
    long = labels.control_label(sample(bf=600, bb=45))

    assert short == long == "Average command"


def test_many_walks_in_a_big_sample_are_not_below_average_just_for_the_count():
    # 45 walks used to be "below-average" by count; at 600 BF it is 7.5%.
    assert labels.control_label(sample(bf=600, bb=45)) != "Below-average command"


def test_limited_dimensions_get_no_label():
    s = sample(bf=60, k=30, bb=10)

    assert labels.strikeout_label(s) is None
    assert labels.control_label(s) is None


def test_contact_risk_never_gets_a_rate_label():
    profile = {"style_label": "x", "contact_risk_label": "stale"}

    labels.apply_profile_labels(profile, sample())

    assert profile["contact_risk_label"] is None


def test_apply_profile_labels_sets_both_rate_labels():
    profile = {"style_label": "Four-seam-Slider starter"}

    labels.apply_profile_labels(profile, sample(bf=200, k=50, bb=14))

    assert profile["swing_miss_label"] == "Above-average swing-and-miss ability"
    assert profile["command_label"] == "Solid command"
    assert profile["style_label"] == "Four-seam-Slider starter"


def test_limited_arsenal_replaces_the_style_label():
    profile = {"style_label": "Four-seam-Slider starter"}

    labels.apply_profile_labels(profile, sample(pitches=40))

    assert profile["style_label"] == "Arsenal data limited"


# --- scopes ---------------------------------------------------------------------------


def test_scope_carries_kind_date_and_a_readable_label():
    assert REG == {
        "kind": "regular_season",
        "through": "2026-07-14",
        "label": "regular season through 2026-07-14",
    }
    assert REG_POST["label"] == "regular season and postseason through 2026-07-14"


def test_every_figure_group_in_the_sample_carries_its_scope():
    s = sample(arsenal_scope=REG_POST, rates_scope=REG)

    assert s["arsenal"]["scope"] == REG_POST
    assert s["rates"]["scope"] == REG


def test_scopes_differ_only_when_the_kinds_differ():
    assert labels.scopes_differ(sample(arsenal_scope=REG_POST, rates_scope=REG)) is True
    assert labels.scopes_differ(sample(arsenal_scope=REG, rates_scope=REG)) is False
    assert labels.scopes_differ(
        sample(arsenal_scope=labels.make_scope(labels.SCOPE_REGULAR, "2026-07-01"), rates_scope=REG)
    ) is False


def test_unknown_scope_kind_is_rejected():
    with pytest.raises(ValueError):
        labels.make_scope("whole_career", "2026-07-14")
