"""A live file holds only live content, and the season line asks for the MLB only (P0.15-D2.4a, F4).

At HEAD `build_payload` started from the demo payload and replaced only `matchup_001` and `archive[0]`: a live file
carried the demo's other matchups (one of them a graded final), five demo archive rows, and a workflow that counted
the demo matchups and graded starters nobody had pitched. Rule 6: a live file contains only live matchups and live
archive rows. The live archive is empty (today's game is not a past report), the workflow counts only the live
matchups, and its postgame step is `not_applicable`. The page says "No past reports yet" (component test).

Controls (they pass before the change): a demo file and a fallback file keep the demo matchups and archive rows.

`sportId=1` (D2.4, decision 5b): the season-stats request asks for the major leagues only, so the roll-up of a traded
pitcher's splits (F22) can never include a minor-league club. Checked with one real request on 2026-10-16: the answer
for 605242 has the same shape with and without it (both clubs and the `All` roll-up, 61 batters faced).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_pipeline import demo_inputs
from data_pipeline.fetchers import live_pipeline as lp
from tests import corpus
from tests.test_live_sample_pipeline import isolated  # noqa: F401  (an autouse fixture)
from tests.test_traded_pitcher_line import FakeResponse

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def live(monkeypatch):
    return corpus.build(monkeypatch, "live_complete")


def is_live(matchup):
    return matchup["data_confidence"]["level"] == "fetched_snapshot"


def test_a_live_file_has_no_demo_matchup(live):
    assert live["matchups"] and all(is_live(m) for m in live["matchups"])
    assert [m["id"] for m in live["matchups"]][0] == "matchup_001"


def test_a_live_file_has_no_archive_row(live):
    assert live["archive"] == []


def test_the_workflow_counts_only_the_live_matchups(live):
    count = len(live["matchups"])
    steps = {step["agent"]: step for step in live["agent_workflow"]["steps"]}

    assert f"for {count} matchup" in steps["Data Scout Agent"]["output"]
    assert steps["Postgame Grader Agent"]["status"] == "not_applicable"
    assert all(m["postgame"] is None for m in live["matchups"])


def test_the_featured_matchup_is_a_live_one(live):
    featured = [m for m in live["matchups"] if m["is_featured"]]

    assert len(featured) == 1 and is_live(featured[0])


@pytest.mark.parametrize("kind", ["demo", "fallback"])
def test_control_a_demo_or_fallback_file_keeps_its_demo_content(monkeypatch, kind):
    demo = demo_inputs.build_demo_payload()
    payload = corpus.build(monkeypatch, kind)

    assert [m["id"] for m in payload["matchups"]] == [m["id"] for m in demo["matchups"]]
    assert [row["id"] for row in payload["archive"]] == [row["id"] for row in demo["archive"]] and payload["archive"]
    assert not any(is_live(m) for m in payload["matchups"])


# --- sportId=1 ---------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("pitcher_id", "through", "batters_faced"),
    [(605242, "2026-09-24", 61), (518585, "2026-08-25", 234)],  # traded in-season; one club
)
def test_the_season_line_asks_for_the_major_leagues_only(monkeypatch, pitcher_id, through, batters_faced):
    """The answers are the real ones of that request (2026-10-16): both shapes keep the `All` roll-up."""

    asked = []

    def urlopen(req, timeout=None):
        asked.append(req.full_url)
        return FakeResponse(json.loads((FIXTURES / f"mlb_sportid1_{pitcher_id}.json").read_text(encoding="utf-8")))

    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp.urllib.request, "urlopen", urlopen)

    line = lp.fetch_pitcher_season_stats(pitcher_id, as_of=through)

    assert "sportId=1" in asked[0] and "group=pitching" in asked[0]
    assert line["batters_faced"] == batters_faced and lp._run_errors == []


def test_the_answer_with_sport_id_1_is_the_answer_without_it_for_605242():
    """Why `sportId=1` changes no figure: the real answer of 2026-10-16 equals the one of 2026-10-15 (no `sportId`)."""

    with_it = json.loads((FIXTURES / "mlb_sportid1_605242.json").read_text(encoding="utf-8"))
    without = json.loads((FIXTURES / "mlb_traded_pitcher_lines.json").read_text(encoding="utf-8"))["answers"]["605242"]

    assert with_it["stats"] == without["response"]["stats"]
