"""Live starters carry no demo fields (PLAN.md P0.1, Phase 0 Gherkin).

Importing generate_demo_json only reads data_cache; main() is never called, so
nothing is written under public/data or data_cache.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from agents import critic, data_scout, matchup_analyst, report_writer
from data_pipeline import demo_inputs
from data_pipeline import generate_demo_json as gdj

SLOTS = ("away_starter", "home_starter")


def _fake_live_game(template: dict) -> dict:
    def live_starter(name: str, throws: str) -> dict:
        source = template["starters"]["away_starter"]
        return {
            "name": name,
            "throws": throws,
            "movement": {},
            "pitch_locations": deepcopy(template["pitch_locations"]["away_starter"]),
            "season_summary": {
                "era": "3.10",
                "whip": "1.05",
                "innings": "101.0",
                "strikeouts": 110,
                "walks": 30,
                "home_runs_allowed": 10,
            },
            "pitching_profile": deepcopy(source["pitching_profile"]),
        }

    return {
        "featured_game": {
            "game_pk": 1,
            "away_team": "Test Away",
            "away_team_id": 901,
            "away_team_abbr": "TAW",
            "home_team": "Test Home",
            "home_team_id": 902,
            "home_team_abbr": "THM",
            "away_pitcher_name": "Alpha Livearm",
            "away_pitcher_id": 111,
            "home_pitcher_name": "Bravo Liveleft",
            "home_pitcher_id": 222,
            "venue": "Test Park",
            "start_time": "2026-07-04T15:05:00Z",
            "status": "Preview",
        },
        "away_starter": live_starter("Alpha Livearm", "R"),
        "home_starter": live_starter("Bravo Liveleft", "L"),
        "combined_charts": {
            "pitch_mix": deepcopy(template["charts"]["pitch_mix"]),
            "velocity_by_pitch": deepcopy(template["charts"]["velocity_by_pitch"]),
        },
        "away_team_splits": {},
        "home_team_splits": {},
    }


def _demo_strings(starter: dict) -> list[str]:
    bio = starter["bio"]
    form = starter["recent_form"]
    return [
        form["label"],
        form["last_three_starts_summary"],
        bio["mlb_service"],
        *bio["accolades"],
    ]


@pytest.fixture()
def demo_template() -> dict:
    payload = demo_inputs.build_demo_payload()
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


@pytest.fixture()
def live_matchup(monkeypatch, demo_template) -> dict:
    live_game = _fake_live_game(demo_template)
    monkeypatch.setattr(gdj, "_live", {"fetched_date": "2026-07-04", "live_games": [live_game]})
    return gdj._apply_live_game_to_matchup(
        deepcopy(demo_template), live_game, matchup_id="matchup_001", is_featured=True
    )


def test_live_starters_mark_bio_and_recent_form_unavailable(live_matchup, demo_template):
    for slot in SLOTS:
        starter = live_matchup["starters"][slot]
        assert starter["bio"] is None
        assert starter["recent_form"] is None
        serialized = json.dumps(starter)
        for text in _demo_strings(demo_template["starters"][slot]):
            assert text not in serialized


def test_agents_run_on_live_starters_without_demo_text(live_matchup, demo_template):
    packet = data_scout.run(live_matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, live_matchup)
    review = critic.run(report, live_matchup)
    assert review["checks"]

    produced = json.dumps([findings, report])
    for slot in SLOTS:
        for text in _demo_strings(demo_template["starters"][slot]):
            assert text not in produced
    assert "Recent form is trending" not in produced
    assert "Recent form has been volatile" not in produced


def test_demo_starters_keep_bio_and_recent_form(demo_template):
    for slot in SLOTS:
        starter = demo_template["starters"][slot]
        assert starter["bio"]["mlb_service"]
        assert starter["recent_form"]["last_three_starts_summary"]
