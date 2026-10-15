"""What the confidence note says follows from a missing part is true of the report (P0.15-D2.1b).

"The pitch read makes no arsenal claims about X" is said for a starter with no pitch data: no sentence of
the report names a pitch for him. "The lineup read makes no offense claims about the T lineup" is said for a
lineup with no split: the read of the starter who faces it says only that the data is not available. Checked
on every live outcome of the matrix and the hard cases and on every golden scenario, with the readers the
critic and the contract use (`report_facts`).
"""

from __future__ import annotations

import pytest

from agents.language import catalog_for
from data_pipeline import labels
from data_pipeline import report_facts as facts
from tests.corpus import GOLDEN_NAMES, golden_payload, published
from tests.matrix import outcomes

SLOTS = ("away_starter", "home_starter")
FACING = {"away_starter": "home", "home_starter": "away"}  # the lineup a starter faces
T = catalog_for("en")


def live_matchups_of_the_matrix() -> list[tuple[str, dict]]:
    return [(name, o.matchup) for name, o in outcomes().items() if o.live]


def golden_matchups() -> list[tuple[str, dict]]:
    found = []
    with pytest.MonkeyPatch.context() as monkeypatch:
        for name in GOLDEN_NAMES:
            payload = published(golden_payload(monkeypatch, name))
            found += [(f"golden:{name}", m) for m in payload["matchups"] if m["data_confidence"]["level"] == "fetched_snapshot"]
    return found


ALL = live_matchups_of_the_matrix() + golden_matchups()


def test_the_worlds_include_starters_without_pitch_data_and_lineups_without_a_split():
    assert any(not labels.has_pitch_data(m["starters"][slot]) for _, m in ALL for slot in SLOTS)
    assert any(not labels.has_offense_figure(m["teams"][side]["offense_profile"]) for _, m in ALL for side in ("away", "home"))


@pytest.mark.parametrize("name,matchup", ALL, ids=[name for name, _ in ALL])
def test_a_starter_without_pitch_data_has_no_pitch_named_for_him(name, matchup):
    for slot in SLOTS:
        starter = matchup["starters"][slot]
        if labels.has_pitch_data(starter):
            continue
        assert starter["sample"]["limited"]["arsenal"], "no pitch data must mean a limited arsenal"
        assert facts.pitches_named_for(matchup, matchup["report"], slot, T) == []


@pytest.mark.parametrize("name,matchup", ALL, ids=[name for name, _ in ALL])
def test_the_read_of_a_lineup_without_a_split_says_only_that_it_is_not_available(name, matchup):
    sections = {section["title"]: section.get("body") or "" for section in matchup["report"]["sections"]}
    for slot in SLOTS:
        starter = matchup["starters"][slot]
        lineup = matchup["teams"][FACING[slot]]["offense_profile"]
        if labels.has_offense_figure(lineup):
            continue
        body = next(text for title, text in sections.items() if title.startswith(starter["name"]))
        assert "is not available for this lineup yet" in body
        assert "OPS" not in body and "strike out often" not in body and "draw walks" not in body
