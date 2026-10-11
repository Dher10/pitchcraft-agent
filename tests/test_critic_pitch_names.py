"""The critic's check of pitch names in the report text (QA-04, owner's follow-up).

Aliases: a correct text may say "two-seam" for a Sinker, "cut fastball" for a Cutter,
"fastball" for any fastball-family pitch. Scope: a pitch credited to one starter must be
one that starter threw; a sentence that names both starters, or neither, can only be held
to the pitches of the two together (the known limit of reading free text).
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from agents import critic
from data_pipeline import demo_inputs

CLAIM = "The report names only pitches that appear in the pitch mix."
A, B = "Demo Pitcher A", "Demo Pitcher B"


def matchup(away: dict[str, float], home: dict[str, float]) -> dict:
    """A demo matchup whose pitch mix and profiles are exactly the given pitches."""

    base = deepcopy(demo_inputs.build_demo_payload()["matchups"][0])
    names = list(dict.fromkeys([*away, *home]))
    zero = {"overall": 0, "vs_lhh": 0, "vs_rhh": 0}

    def usage(value: float) -> dict:
        return {"overall": value, "vs_lhh": value, "vs_rhh": value}

    base["charts"]["pitch_mix"] = [
        {"pitch": n, "away_starter": usage(away[n]) if n in away else zero,
         "home_starter": usage(home[n]) if n in home else zero}
        for n in names
    ]
    for slot, pitches in (("away_starter", away), ("home_starter", home)):
        ordered = sorted(pitches, key=pitches.get, reverse=True)
        profile = base["starters"][slot]["pitching_profile"]
        profile["primary_pitch"] = ordered[0]
        profile["putaway_pitch"] = ordered[1] if len(ordered) > 1 else "Not available"
        base["starters"][slot]["name"] = A if slot == "away_starter" else B
    return base


def verdict(game: dict, *sentences: str) -> dict:
    report = {"headline": "h", "short_summary": [], "sections": [{"title": "t", "body": " ".join(sentences)}]}
    return next(c for c in critic.run(report, game)["checks"] if c["claim"] == CLAIM)


GAME = matchup(
    away={"Four-seam": 55, "Slider": 30, "Curveball": 15},
    home={"Sinker": 50, "Cutter": 20, "Changeup": 20, "Splitter": 10},
)


# --- aliases ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence",
    [
        f"{A} leans on a four-seam fastball.",
        f"{A} leans on a four seam.",
        f"{A} leans on the 4-seam.",
        f"{A} works off a fastball.",  # generic: any fastball-family pitch
        f"{A} has a sharp curve ball.",
        f"{B} runs a two-seam in on righties.",  # a Sinker
        f"{B} runs a two seam in on righties.",
        f"{B} throws a sinker.",
        f"{B} has a cut fastball.",  # a Cutter
        f"{B} throws a change-up.",
        f"{B} throws a split-finger.",
        f"{B} throws a split finger.",
        f"{B} throws two-seam fastballs and changeups.",
    ],
)
def test_a_correct_text_with_an_alias_is_not_unsupported(sentence):
    assert verdict(GAME, sentence)["status"] == "supported", sentence


@pytest.mark.parametrize(
    "sentence",
    [
        f"{A} runs a two-seam in on righties.",  # A has no Sinker
        f"{A} has a cut fastball.",  # A has no Cutter
        f"{A} throws a change-up.",
        f"{A} throws a split-finger.",
        f"{B} leans on the 4-seam.",  # B has no Four-seam
        f"{B} has a sharp curve ball.",
    ],
)
def test_an_alias_of_a_pitch_the_starter_did_not_throw_is_unsupported(sentence):
    assert verdict(GAME, sentence)["status"] == "unsupported", sentence


def test_a_generic_fastball_needs_a_fastball_family_pitch():
    breaking_only = matchup(
        away={"Slider": 60, "Curveball": 40}, home={"Changeup": 60, "Splitter": 40}
    )

    assert verdict(breaking_only, f"{A} sets up hitters with his fastball.")["status"] == "unsupported"
    assert verdict(breaking_only, f"{B} lives off his slider.")["status"] == "unsupported"


def test_a_sinker_in_the_mix_counts_as_two_seam_in_either_spelling():
    game = matchup(away={"Two-seam": 70, "Slider": 30}, home={"Sinker": 60, "Changeup": 40})

    assert verdict(game, f"{A} runs a sinker in on righties.")["status"] == "supported"
    assert verdict(game, f"{B} runs a two-seam in on righties.")["status"] == "supported"


# --- scope per pitcher ------------------------------------------------------------------------------


def test_naming_for_a_starter_a_pitch_only_the_other_throws_is_unsupported():
    result = verdict(GAME, f"{A} gets his swings and misses with a changeup.")  # only B throws it

    assert result["status"] == "unsupported"
    assert A in result["evidence"] and "changeup" in result["evidence"].lower()


def test_the_same_pitch_credited_to_the_one_who_throws_it_is_supported():
    assert verdict(GAME, f"{B} gets his swings and misses with a changeup.")["status"] == "supported"


def test_each_sentence_is_held_to_its_own_starter():
    both_right = verdict(GAME, f"{A} throws a slider. {B} throws a changeup.")
    swapped = verdict(GAME, f"{A} throws a changeup. {B} throws a slider.")

    assert both_right["status"] == "supported"
    assert swapped["status"] == "unsupported"


def test_a_starter_with_no_arsenal_cannot_be_credited_with_any_pitch():
    game = matchup(away={"Four-seam": 100}, home={"Sinker": 100})
    for row in game["charts"]["pitch_mix"]:
        row["away_starter"] = {"overall": 0, "vs_lhh": 0, "vs_rhh": 0}

    assert verdict(game, f"{A} throws a four-seam.")["status"] == "unsupported"


def test_a_sentence_naming_both_starters_is_held_to_the_two_together():
    # The known limit: it cannot say which of them the pitch belongs to.
    assert verdict(GAME, f"{A} and {B} both throw a changeup.")["status"] == "supported"
    assert verdict(GAME, f"{A} and {B} both throw a knuckleball.")["status"] == "unsupported"


def test_a_sentence_naming_nobody_is_held_to_the_two_together():
    assert verdict(GAME, "The main contrast is a slider against a changeup.")["status"] == "supported"
    assert verdict(GAME, "The main contrast is a sweeper against a changeup.")["status"] == "unsupported"


def test_a_name_with_a_period_does_not_hide_the_attribution():
    game = matchup(away={"Four-seam": 70, "Slider": 30}, home={"Sinker": 60, "Changeup": 40})
    game["starters"]["away_starter"]["name"] = "Luis Garcia Jr."

    assert verdict(game, "Luis Garcia Jr. throws a changeup.")["status"] == "unsupported"
    assert verdict(game, "Luis Garcia Jr. throws a slider.")["status"] == "supported"
