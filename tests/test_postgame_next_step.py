"""The postgame "what to watch next" matches the Average label only (sweep of QA2-02).

The rule suggests more chase from the put-away pitch when a starter with an average
swing-and-miss label struck out three or fewer. It tested `"average" in label`, which also
matches "Above-average" and "Below-average", so every labelled starter qualified.
"""

from __future__ import annotations

import pytest

from agents import postgame_grader
from agents.language import catalog_for

T = catalog_for("en")
QUIET_LINE = {"walks": 1, "hits_allowed": 4, "earned_runs": 1, "strikeouts": 2}


def next_step(label, strikeouts=2) -> str:
    starter = {"pitching_profile": {"swing_miss_label": label, "putaway_pitch": "Slider"}}
    return postgame_grader._what_to_watch_next(T, starter, {**QUIET_LINE, "strikeouts": strikeouts})


CHASE = T("grader.next.chase", putaway="slider")
DEFAULT = T("grader.next.default")


@pytest.mark.parametrize(
    "label",
    ["Average swing-and-miss ability", "Average swing-and-miss", "average swing-and-miss ability"],
)
def test_an_average_label_with_few_strikeouts_asks_for_more_chase(label):
    assert next_step(label) == CHASE


@pytest.mark.parametrize(
    "label",
    [
        "Above-average swing-and-miss ability",
        "Above-average swing-and-miss",
        "Below-average swing-and-miss ability",
        "Below-average swing-and-miss",
        None,
        "",
    ],
)
def test_any_other_label_gets_the_default_step(label):
    assert next_step(label) == DEFAULT


def test_an_average_label_with_enough_strikeouts_gets_the_default_step():
    assert next_step("Average swing-and-miss ability", strikeouts=4) == DEFAULT
