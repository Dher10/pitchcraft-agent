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


def starter_with(s):
    """A starter around a sample: ERA from the API (regular season) and counts with the sample's scope."""

    regular = labels.make_scope(labels.SCOPE_REGULAR, REG["through"])
    summary = {"era": "3.10", "whip": "1.05", "innings": "101.0", "scopes": {"season_rates": regular, "counts": s["rates"]["scope"]}}
    return {"sample": s, "season_summary": summary}


def test_scopes_differ_only_when_the_kinds_differ():
    assert labels.scopes_differ(starter_with(sample(arsenal_scope=REG_POST, rates_scope=REG))) is True
    assert labels.scopes_differ(starter_with(sample(arsenal_scope=REG, rates_scope=REG))) is False
    assert labels.scopes_differ(
        starter_with(sample(arsenal_scope=labels.make_scope(labels.SCOPE_REGULAR, "2026-07-01"), rates_scope=REG))
    ) is False


def test_unknown_scope_kind_is_rejected():
    with pytest.raises(ValueError):
        labels.make_scope("whole_career", "2026-07-14")


# --- QA6-03 (P0.17-d): "labels use rates, not counts" at every sample size -----------------------------------------
#
# QA run 6 broke `labels.py` with count thresholds calibrated to 200 batters faced (`walks <= 14` for Solid command,
# `strikeouts >= 50` for Above-average, `strikeouts < 36` for Below-average) and every label test still passed: they
# all used 200. Each band edge below is tried at four sample sizes with the same rate; a count threshold that is
# right for one size is wrong for the other three, so it fails here.

K_SIZES = (100, 200, 600, 1000)  # all above the 70 batters faced that D24 asks for strikeout
# 170 batters faced is the floor of the control label (D24), so its smallest size here is the first multiple above it.
BB_SIZES = (200, 600, 1000, 2000)

K_BANDS = [  # (percent of batters faced that strike out, the label)
    (40, labels.SWING_MISS_ABOVE),
    (26, labels.SWING_MISS_ABOVE),
    (25, labels.SWING_MISS_ABOVE),  # the edge: at or above
    (24, labels.SWING_MISS_AVERAGE),
    (21, labels.SWING_MISS_AVERAGE),
    (18, labels.SWING_MISS_AVERAGE),  # the edge: not below
    (17, labels.SWING_MISS_BELOW),
    (5, labels.SWING_MISS_BELOW),
]
BB_BANDS = [  # (percent of batters faced that walk, the label)
    (2, labels.COMMAND_SOLID),
    (7, labels.COMMAND_SOLID),  # the edge: at or below
    (8, labels.COMMAND_AVERAGE),
    (9, labels.COMMAND_AVERAGE),
    (10, labels.COMMAND_BELOW),  # the edge: at or above
    (15, labels.COMMAND_BELOW),
]


def _count(percent, size):
    assert (percent * size) % 100 == 0, "the case must be an exact rate"
    return percent * size // 100


def _per_mille_count(per_mille, size):
    assert (per_mille * size) % 1000 == 0, "the case must be an exact rate"
    return per_mille * size // 1000


@pytest.mark.parametrize("size", K_SIZES)
@pytest.mark.parametrize("percent, expected", K_BANDS)
def test_strikeout_bands_are_rates_at_every_sample_size(size, percent, expected):
    assert labels.strikeout_label(sample(bf=size, k=_count(percent, size))) == expected


@pytest.mark.parametrize("size", BB_SIZES)
@pytest.mark.parametrize("percent, expected", BB_BANDS)
def test_control_bands_are_rates_at_every_sample_size(size, percent, expected):
    assert labels.control_label(sample(bf=size, bb=_count(percent, size))) == expected


@pytest.mark.parametrize("percent, _expected", K_BANDS)
def test_one_strikeout_rate_gets_one_label_at_every_size(percent, _expected):
    found = {labels.strikeout_label(sample(bf=size, k=_count(percent, size))) for size in K_SIZES}

    assert len(found) == 1


@pytest.mark.parametrize("percent, _expected", BB_BANDS)
def test_one_walk_rate_gets_one_label_at_every_size(percent, _expected):
    found = {labels.control_label(sample(bf=size, bb=_count(percent, size))) for size in BB_SIZES}

    assert len(found) == 1


@pytest.mark.parametrize("size", (1000, 2000))
@pytest.mark.parametrize(
    "per_mille, expected",
    [
        (250, labels.SWING_MISS_ABOVE),  # 25.0%
        (249, labels.SWING_MISS_AVERAGE),  # 24.9%
        (180, labels.SWING_MISS_AVERAGE),  # 18.0%
        (179, labels.SWING_MISS_BELOW),  # 17.9%
    ],
)
def test_strikeout_edges_hold_to_a_tenth_of_a_point(size, per_mille, expected):
    assert labels.strikeout_label(sample(bf=size, k=_per_mille_count(per_mille, size))) == expected


@pytest.mark.parametrize("size", (1000, 2000))
@pytest.mark.parametrize(
    "per_mille, expected",
    [
        (70, labels.COMMAND_SOLID),  # 7.0%
        (71, labels.COMMAND_AVERAGE),  # 7.1%
        (99, labels.COMMAND_AVERAGE),  # 9.9%
        (100, labels.COMMAND_BELOW),  # 10.0%
    ],
)
def test_control_edges_hold_to_a_tenth_of_a_point(size, per_mille, expected):
    assert labels.control_label(sample(bf=size, bb=_per_mille_count(per_mille, size))) == expected


def test_at_100_batters_faced_strikeout_has_a_label_and_control_still_has_none():
    # D24: 70 batters faced for strikeout, 170 for control. The size 100 is in K_SIZES and not in BB_SIZES for that reason.
    assert labels.strikeout_label(sample(bf=100, k=25)) == labels.SWING_MISS_ABOVE
    assert labels.control_label(sample(bf=100, bb=7)) is None
