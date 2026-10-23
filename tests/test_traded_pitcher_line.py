"""A pitcher traded in-season has his season line from the aggregate split, not from the first club (P0.15-D2.3d, F22).

`fetch_pitcher_season_stats` read `splits[0]`. For a pitcher who played for two clubs the MLB Stats API answers one
split per club and then an aggregate that rolls them up, so `splits[0]` was the first club only (605242: 15 batters
faced instead of 61; 670167: 203 instead of 246), and with it F21 (a Statcast sample with fewer plate appearances
than the API line) was not reliable for him.

The real answers (`tests/fixtures/mlb_traded_pitcher_lines.json`, taken 2026-10-15, one request each) show the
aggregate is marked by its sport, `{"id": 0, "code": "All"}`, not by a missing team: the answer of a pitcher with one
club is that club's split twice, the second one with the roll-up sport. The plan said "the split with no `team`"; that
holds for the two traded pitchers and would have rejected every pitcher with one club (28 of 28 in the calibration), so
the rule is: no splits, `{}`; one split, it; several, the one with the roll-up sport, which must not have fewer batters
faced than any club split; several and no (or two) roll-ups, or one smaller than a club, a malformed answer (recorded,
`{}`), never the first and never a sum.

Controls (they pass before the change): a pitcher with one club reads the same line, an empty answer is `{}`, a
malformed answer is still `{}` with its recorded code.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.fetchers import mlb_schemas
from tests.test_live_sample_pipeline import isolated  # noqa: F401  (an autouse fixture)

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "mlb_traded_pitcher_lines.json").read_text(encoding="utf-8"))
ANSWERS = {int(pid): item for pid, item in FIXTURE["answers"].items()}
TRADED = (605242, 670167)
ONE_CLUB = 518585


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fetch(monkeypatch, pitcher_id, answer=None):
    body = answer if answer is not None else ANSWERS[pitcher_id]["response"]
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp.urllib.request, "urlopen", lambda req, timeout=None: FakeResponse(body))
    return lp.fetch_pitcher_season_stats(pitcher_id, as_of=ANSWERS[pitcher_id]["through"])


def splits_of(pitcher_id):
    return deepcopy(ANSWERS[pitcher_id]["response"]["stats"][0]["splits"])


def answer_with(pitcher_id, splits):
    body = deepcopy(ANSWERS[pitcher_id]["response"])
    body["stats"][0]["splits"] = splits
    return body


# --- the real answers -------------------------------------------------------------------------------------------


@pytest.mark.parametrize(("pitcher_id", "batters_faced", "first_club"), [(605242, 61, 15), (670167, 246, 203)])
def test_a_traded_pitcher_has_the_line_of_the_aggregate(monkeypatch, pitcher_id, batters_faced, first_club):
    splits = splits_of(pitcher_id)
    assert splits[0]["stat"]["battersFaced"] == first_club  # the line `splits[0]` read

    line = fetch(monkeypatch, pitcher_id)

    assert line["batters_faced"] == batters_faced
    rollup = next(s for s in splits if (s["sport"] or {}).get("id") == 0)["stat"]
    assert (line["era"], line["whip"], line["innings"]) == (rollup["era"], rollup["whip"], rollup["inningsPitched"])
    assert (line["strikeouts"], line["walks"], line["home_runs_allowed"]) == (
        rollup["strikeOuts"],
        rollup["baseOnBalls"],
        rollup["homeRuns"],
    )
    assert lp._run_errors == []


def test_the_line_is_not_a_sum_of_the_clubs(monkeypatch):
    splits = splits_of(605242)
    clubs = [s for s in splits if s["sport"]["id"] == 1]

    line = fetch(monkeypatch, 605242)

    assert len(clubs) == 2 and line["batters_faced"] == sum(c["stat"]["battersFaced"] for c in clubs) == 61


@pytest.mark.parametrize(("pitcher_id", "statcast_plate_appearances"), [(605242, 46), (670167, 43)])
def test_with_the_aggregate_the_incomplete_frames_of_the_calibration_are_flagged(
    monkeypatch, pitcher_id, statcast_plate_appearances
):
    """F21 on the path that production takes: both cached frames hold only the second club."""

    line = fetch(monkeypatch, pitcher_id)

    assert lp.statcast_is_short(statcast_plate_appearances, line["batters_faced"])


def test_control_a_pitcher_with_one_club_has_his_line(monkeypatch):
    line = fetch(monkeypatch, ONE_CLUB)

    assert line["batters_faced"] == 234 and lp._run_errors == []


def test_control_the_real_answer_of_a_pitcher_with_one_club_is_his_club_twice():
    first, second = splits_of(ONE_CLUB)

    assert first["stat"] == second["stat"] and first["team"] == second["team"]
    assert first["sport"]["id"] == 1 and second["sport"]["id"] == 0


# --- the rule on the shapes the API can give -----------------------------------------------------------------------


def test_one_split_is_the_line(monkeypatch):
    only = splits_of(ONE_CLUB)[0]

    assert fetch(monkeypatch, ONE_CLUB, answer_with(ONE_CLUB, [only]))["batters_faced"] == 234


def test_several_splits_and_no_aggregate_are_a_malformed_answer(monkeypatch):
    clubs = [s for s in splits_of(605242) if s["sport"]["id"] == 1]

    line = fetch(monkeypatch, 605242, answer_with(605242, clubs))

    assert line == {}
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("mlb_season_stats", "malformed_response")]
    assert "aggregate" in lp._run_errors[0]["message"]


def test_two_aggregates_are_a_malformed_answer(monkeypatch):
    splits = splits_of(605242)
    splits.append(deepcopy(splits[-1]))

    assert fetch(monkeypatch, 605242, answer_with(605242, splits)) == {}
    assert [e["code"] for e in lp._run_errors] == ["malformed_response"]


def test_an_aggregate_with_fewer_batters_faced_than_a_club_is_a_malformed_answer(monkeypatch):
    splits = splits_of(605242)
    splits[-1]["stat"]["battersFaced"] = 40  # a roll-up cannot be smaller than the club it contains (46)

    assert fetch(monkeypatch, 605242, answer_with(605242, splits)) == {}
    assert [e["code"] for e in lp._run_errors] == ["malformed_response"]


def test_a_split_that_does_not_say_its_sport_cannot_be_an_aggregate(monkeypatch):
    splits = splits_of(605242)
    for split in splits:
        split.pop("sport")

    assert fetch(monkeypatch, 605242, answer_with(605242, splits)) == {}
    assert [e["code"] for e in lp._run_errors] == ["malformed_response"]


def test_the_order_of_the_splits_does_not_matter(monkeypatch):
    splits = splits_of(605242)[::-1]

    assert fetch(monkeypatch, 605242, answer_with(605242, splits))["batters_faced"] == 61


def test_the_schema_knows_the_fields_the_rule_reads():
    with pytest.raises(mlb_schemas.SourceShapeError):
        mlb_schemas.validate(
            mlb_schemas.PITCHER_STATS,
            answer_with(605242, [{**splits_of(605242)[0], "sport": {"id": "zero"}}]),
            "season stats response",
        )


# --- controls --------------------------------------------------------------------------------------------------------


def test_control_an_empty_answer_is_an_empty_line(monkeypatch):
    assert fetch(monkeypatch, ONE_CLUB, answer_with(ONE_CLUB, [])) == {}
    assert lp._run_errors == []


def test_control_a_malformed_answer_is_still_recorded(monkeypatch):
    assert fetch(monkeypatch, ONE_CLUB, {"stats": "nope"}) == {}
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("mlb_season_stats", "malformed_response")]
