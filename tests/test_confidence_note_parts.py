"""The confidence note of a live report is built from parts, each with its own condition (P0.15-D2.1b, F1).

The first sentence lists only what is complete: probable pitchers, Statcast pitch data when BOTH starters
have a pitch on record, season offense splits when BOTH lineups have a split ("A, B, and C" / "A and B" /
"A"), so the text is the one of before when everything holds. What is missing is said apart, in the past
and with its consequence. Pitch data is judged per starter (both / one / none) and offense per lineup
(both / one / none): nine combinations, and 16 when "one" is told by which side it is. A sentence about one
part names that starter or that team, never "it".

The matchups come from the golden scenarios' builder (live-shaped, nothing fetched); only the sample of a
starter and the offense figures of a lineup are set here, which are exactly what the parts read.
"""

from __future__ import annotations

import re

import pytest

from agents import report_writer
from agents.language import catalog_for
from tests.test_limited_samples import build, debut_sample, sample

SNAPSHOT = "This report uses a fetched live snapshot with {items}."
LINEUPS = "Lineups can still change before first pitch."
LIMITED = "Samples below the minimum are flagged as limited and no claim is made from them."
OFFENSE_FIELDS = ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand")
FIGURES = {"ops_vs_hand": ".801", "k_rate_vs_hand": "24.5%", "bb_rate_vs_hand": "10.2%"}

# who has a pitch on record / a split, by case id
PITCH_CASES = ("both", "away_only", "home_only", "none")
OFFENSE_CASES = ("both", "away_only", "home_only", "none")


def matchup_of(monkeypatch, pitch: str, offense: str) -> dict:
    away = sample() if pitch in ("both", "away_only") else debut_sample()
    home = sample() if pitch in ("both", "home_only") else debut_sample()
    matchup = build(monkeypatch, away=away, home=home)
    for side, has in (("away", offense in ("both", "away_only")), ("home", offense in ("both", "home_only"))):
        profile = matchup["teams"][side]["offense_profile"]
        for field in OFFENSE_FIELDS:
            profile[field] = FIGURES[field] if has else None
    return matchup


def note_of(matchup: dict) -> str:
    return str(report_writer._confidence_note(catalog_for("en"), matchup, {"scope_notes": []}))


def expected_first_sentence(pitch: str, offense: str) -> str:
    items = ["probable pitchers"]
    if pitch == "both":
        items.append("Statcast pitch data")
    if offense == "both":
        items.append("season offense splits")
    listed = items[0] if len(items) == 1 else " and ".join(items) if len(items) == 2 else f"{items[0]}, {items[1]}, and {items[2]}"
    return SNAPSHOT.format(items=listed)


def expected_pitch_sentence(matchup: dict, pitch: str) -> str | None:
    away, home = (matchup["starters"][slot]["name"] for slot in ("away_starter", "home_starter"))
    return {
        "both": None,
        "away_only": f"Statcast pitch data was available for {away} but not for {home}, so the pitch read makes no arsenal claims about {home}.",
        "home_only": f"Statcast pitch data was available for {home} but not for {away}, so the pitch read makes no arsenal claims about {away}.",
        "none": "Statcast pitch data was not available for either starter, so the pitch read makes no arsenal claims.",
    }[pitch]


def expected_offense_sentence(matchup: dict, offense: str) -> str | None:
    away, home = (matchup["teams"][side]["name"] for side in ("away", "home"))

    def one(has: str, lacks: str) -> str:
        return (
            f"Season offense splits were available for the {has} lineup but not for the {lacks} lineup, "
            f"so the lineup read makes no offense claims about the {lacks} lineup."
        )

    return {
        "both": None,
        "away_only": one(away, home),
        "home_only": one(home, away),
        "none": "Season offense splits were not available for this game, so the lineup read makes no offense claims.",
    }[offense]


@pytest.mark.parametrize("offense", OFFENSE_CASES)
@pytest.mark.parametrize("pitch", PITCH_CASES)
def test_the_note_says_only_what_each_part_supports(monkeypatch, pitch, offense):
    matchup = matchup_of(monkeypatch, pitch, offense)

    parts = [
        expected_first_sentence(pitch, offense),
        expected_pitch_sentence(matchup, pitch),
        expected_offense_sentence(matchup, offense),
        LINEUPS,
    ]
    parts = [part for part in parts if part]
    if pitch != "both":  # a debut is flagged as limited
        parts.append(LIMITED)

    assert note_of(matchup) == " ".join(parts)


@pytest.mark.parametrize("offense", OFFENSE_CASES)
@pytest.mark.parametrize("pitch", PITCH_CASES)
def test_the_sentence_of_one_part_names_the_starter_or_the_team_never_it(monkeypatch, pitch, offense):
    matchup = matchup_of(monkeypatch, pitch, offense)
    note = note_of(matchup)
    names = [matchup["starters"][slot]["name"] for slot in ("away_starter", "home_starter")]
    teams = [matchup["teams"][side]["name"] for side in ("away", "home")]

    assert not re.search(r"\bit\b", note, re.IGNORECASE)
    if pitch in ("away_only", "home_only"):
        assert all(name in note for name in names)
    if offense in ("away_only", "home_only"):
        assert all(f"the {team} lineup" in note for team in teams)


def test_a_lineup_with_only_a_strikeout_rate_has_a_split(monkeypatch):
    """The scope of a lineup exists when it has an OPS, a K% or a BB% (F2); the note reads the same figures."""

    matchup = matchup_of(monkeypatch, "both", "none")
    matchup["teams"]["away"]["offense_profile"]["k_rate_vs_hand"] = "24.5%"

    assert expected_offense_sentence(matchup, "away_only") in note_of(matchup)


def test_a_pitch_count_of_zero_or_unknown_is_not_pitch_data(monkeypatch):
    matchup = matchup_of(monkeypatch, "both", "both")
    matchup["starters"]["away_starter"]["sample"]["arsenal"]["pitches"] = None

    note = note_of(matchup)
    assert expected_pitch_sentence(matchup, "home_only") in note
    assert "Statcast pitch data" not in note.split(".")[0]  # the first sentence lists only what is complete


def test_the_lineup_sentence_has_its_own_key(monkeypatch):
    matchup = matchup_of(monkeypatch, "both", "both")

    keys = _keys(report_writer._confidence_note(catalog_for("en"), matchup, {"scope_notes": []}))

    assert keys[-1] == "writer.confidence.lineups"  # the last of the parts, after what is missing
    assert {"writer.confidence.snapshot", "writer.confidence.item.pitch_data", "writer.confidence.item.offense"} <= set(keys)
    assert not {"writer.confidence.live_full", "writer.confidence.live_no_offense"} & set(keys)


def test_the_first_sentence_lists_its_items_as_the_note_of_before_did(monkeypatch):
    """With every part complete the opening is the old list; with one missing it is the shorter list."""

    assert note_of(matchup_of(monkeypatch, "both", "both")).startswith(
        "This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can"
    )
    assert note_of(matchup_of(monkeypatch, "both", "none")).startswith(
        "This report uses a fetched live snapshot with probable pitchers and Statcast pitch data. Season offense splits were not available"
    )
    assert note_of(matchup_of(monkeypatch, "none", "both")).startswith(
        "This report uses a fetched live snapshot with probable pitchers and season offense splits. Statcast pitch data was not available"
    )
    assert note_of(matchup_of(monkeypatch, "none", "none")).startswith(
        "This report uses a fetched live snapshot with probable pitchers. Statcast pitch data was not available for either starter"
    )


def _keys(phrase) -> list[str]:
    """The keys of a phrase and of the phrases it is made of, in the order they are read."""

    found = [phrase.key]
    for value in phrase.args.values():
        for item in value if isinstance(value, list) else [value]:
            if hasattr(item, "key"):
                found += _keys(item)
    return found
