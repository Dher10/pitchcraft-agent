"""Every derived field of a demo matchup is what the live pipeline's functions give for its data (P0.15-D2.1c, F18).

A demo matchup is written by hand, so a field the live pipeline derives (the primary and the put-away pitch,
the family of a pitch, the hand a lineup faces, the title) can disagree with the data it is derived from: the
demo's Demo Pitcher C had a "Changeup" put-away pitch at 12% of his pitches while his curveball was thrown 26%
of the time (F18). This test recomputes each derivation with the function the live pipeline uses and compares.

The labels that need a sample the demo does not have (command, swing-and-miss and contact-risk labels, the
offense summaries, the 0-100 strength scores) are declared inputs of the demo, not derivations: they are not
recomputed here.
"""

from __future__ import annotations

import inspect

import pytest

from data_pipeline import demo_inputs, labels
from data_pipeline.fetchers import live_pipeline

DEMO = demo_inputs.build_demo_payload()
SLOTS = ("away_starter", "home_starter")
STARTERS = [(m["id"], slot) for m in DEMO["matchups"] for slot in SLOTS]
MATCHUP_IDS = [m["id"] for m in DEMO["matchups"]]


def plain(pitch: str) -> str:
    """How a pitch is compared: no ` fastball`, lower case ("Four-seam fastball" is the mix's "Four-seam")."""

    return pitch.replace(labels.FASTBALL_SUFFIX, "").strip().lower()


def matchup(matchup_id):
    return next(m for m in DEMO["matchups"] if m["id"] == matchup_id)


def shares(m, slot) -> dict[str, int]:
    return {row["pitch"]: row[slot]["overall"] for row in m["charts"]["pitch_mix"] if row[slot]["overall"]}


@pytest.mark.parametrize("matchup_id,slot", STARTERS)
def test_the_primary_and_the_putaway_pitch_are_the_ones_the_live_rule_gives(matchup_id, slot):
    m = matchup(matchup_id)
    profile = m["starters"][slot]["pitching_profile"]

    primary, putaway = labels.profile_pitches(shares(m, slot))

    assert plain(profile["primary_pitch"]) == plain(primary)
    assert plain(profile["putaway_pitch"]) == plain(putaway), (
        f"{m['starters'][slot]['name']}: the profile says {profile['putaway_pitch']!r}, the mix gives {putaway!r}"
    )


def names(style: str, pitch: str) -> bool:
    """The prose of a demo style label says "fastball" for a four-seam; otherwise it uses the pitch's own name."""

    words = {plain(pitch)} | ({"fastball"} if plain(pitch) == "four-seam" else set())
    return any(word in style for word in words)


@pytest.mark.parametrize("matchup_id,slot", STARTERS)
def test_the_style_label_names_the_two_pitches_it_is_made_of(matchup_id, slot):
    m = matchup(matchup_id)
    style = m["starters"][slot]["pitching_profile"]["style_label"].lower()
    primary, putaway = labels.profile_pitches(shares(m, slot))

    for pitch in (primary, putaway):
        if labels.pitch_named(pitch):
            assert names(style, pitch), f"{style!r} does not name {pitch!r}"


@pytest.mark.parametrize("matchup_id,slot", STARTERS)
def test_the_family_of_every_pitch_is_the_one_of_the_live_table(matchup_id, slot):
    m = matchup(matchup_id)

    for pitch, movement in m["charts"]["pitch_movement"][slot].items():
        assert movement["family"] == labels.PITCH_FAMILY[pitch], f"{pitch}: {movement['family']}"


@pytest.mark.parametrize("matchup_id", MATCHUP_IDS)
def test_the_hand_a_lineup_faces_is_the_hand_of_the_starter_it_faces(matchup_id):
    m = matchup(matchup_id)

    # The home lineup faces the away starter and the other way round, as `build_offense` is called.
    assert m["teams"]["home"]["offense_profile"]["vs_pitcher_hand"] == f"{m['starters']['away_starter']['throws']}HP"
    assert m["teams"]["away"]["offense_profile"]["vs_pitcher_hand"] == f"{m['starters']['home_starter']['throws']}HP"


@pytest.mark.parametrize("matchup_id", MATCHUP_IDS)
def test_the_title_and_the_starter_team_follow_the_teams(matchup_id):
    m = matchup(matchup_id)

    assert m["game"]["title"] == f"{m['teams']['away']['name']} vs {m['teams']['home']['name']}"
    for slot, side in (("away_starter", "away"), ("home_starter", "home")):
        assert m["starters"][slot]["team"] == m["teams"][side]["abbreviation"]


def test_the_archive_rows_follow_their_matchup():
    """The row lists the starters and the teams away first, as the title of the live pipeline does."""

    rows = {row["id"]: row for row in DEMO["archive"]}

    for m in DEMO["matchups"]:
        row = rows[m["id"]]
        assert row["starter_summary"] == f"{m['starters']['away_starter']['name']} vs {m['starters']['home_starter']['name']}"
        away, home = row["title"].split(" vs ")
        assert m["teams"]["away"]["name"].endswith(away), f"{row['title']!r}: the away team is {m['teams']['away']['name']}"
        assert m["teams"]["home"]["name"].endswith(home), f"{row['title']!r}: the home team is {m['teams']['home']['name']}"


def test_the_demo_is_checked_with_the_same_function_the_live_pipeline_calls():
    """The test is only worth something if the live pipeline derives its profile with `labels.profile_pitches`."""

    assert "labels.profile_pitches(" in inspect.getsource(live_pipeline.process_pitcher_statcast)
