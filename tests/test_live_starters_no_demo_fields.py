"""Live starters carry no demo fields (PLAN.md P0.1, Phase 0 Gherkin).

Importing generate_demo_json only reads data_cache; main() is never called, so
nothing is written under public/data or data_cache.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from agents import critic, data_scout, matchup_analyst, report_writer
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj

SLOTS = ("away_starter", "home_starter")


def counted(pitch_mix: list[dict], away_pitches: int, home_pitches: int) -> list[dict]:
    """
    Give a hand-made live pitch mix the raw counts the fetcher always writes (QA3-03): each count is
    the row's share of that starter's pitches. A starter with no pitches has no mix, only zeros.
    """

    rows = [deepcopy(row) for row in pitch_mix]  # row by row: hand-made rows may share one dict
    for row in rows:
        for slot, total in (("away_starter", away_pitches), ("home_starter", home_pitches)):
            usage = row[slot]
            if total:
                usage.update(count=round(total * usage["overall"] / 100), total=total)
            else:
                usage.update(overall=0, vs_lhh=0, vs_rhh=0, count=0, total=0)
    return rows


def _fake_live_game(
    template: dict,
    away_team_splits: dict | None = None,
    home_team_splits: dict | None = None,
) -> dict:
    def live_starter(name: str, throws: str) -> dict:
        source = template["starters"]["away_starter"]
        reg = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-04")
        sample = labels.build_sample(
            pitches=1500,
            arsenal_scope=reg,
            batters_faced=400,
            strikeouts=90,
            walks=30,
            home_runs=10,
            rates_source="mlb_api",
            rates_scope=reg,
        )
        profile = deepcopy(source["pitching_profile"])
        labels.apply_profile_labels(profile, sample)
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
                "scope": reg,
            },
            "sample": sample,
            "pitching_profile": profile,
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
            "pitch_mix": counted(template["charts"]["pitch_mix"], 1500, 1500),
            "velocity_by_pitch": deepcopy(template["charts"]["velocity_by_pitch"]),
        },
        "away_team_splits": away_team_splits or {},
        "home_team_splits": home_team_splits or {},
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
def build_live_matchup(monkeypatch, demo_template):
    def build(away_team_splits: dict | None = None, home_team_splits: dict | None = None) -> dict:
        live_game = _fake_live_game(demo_template, away_team_splits, home_team_splits)
        monkeypatch.setattr(gdj, "_live", {"fetched_date": "2026-07-04", "live_games": [live_game]})
        return gdj._apply_live_game_to_matchup(
            deepcopy(demo_template), live_game, matchup_id="matchup_001", is_featured=True
        )

    return build


@pytest.fixture()
def live_matchup(build_live_matchup) -> dict:
    return build_live_matchup()


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


# --- Team fields (P0.1b) -----------------------------------------------------

OFFENSE_FIELDS = ("summary_label", "ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand", "recent_form")
SIDES = ("home", "away")


def _demo_team_strings(template: dict) -> list[str]:
    strings = []
    for side in SIDES:
        team = template["teams"][side]
        strings.append(team["record"])
        strings.extend(team["offense_profile"][field] for field in OFFENSE_FIELDS)
    return strings


def test_live_teams_without_splits_mark_offense_unavailable(live_matchup, demo_template):
    for side in SIDES:
        team = live_matchup["teams"][side]
        assert team["record"] is None
        for field in OFFENSE_FIELDS:
            assert team["offense_profile"][field] is None
    serialized = json.dumps(live_matchup["teams"])
    for text in _demo_team_strings(demo_template):
        assert text not in serialized


def test_partial_split_marks_only_the_missing_field(build_live_matchup):
    # Away starter throws R, so the home team is read against the "vr" split;
    # home starter throws L, so the away team is read against "vl".
    matchup = build_live_matchup(
        away_team_splits={"vl": {"ops": "0.700", "k_rate": 25.0, "bb_rate": 7.5}},
        home_team_splits={"vr": {"ops": "0.812", "k_rate": None, "bb_rate": 9.5}},
    )
    home = matchup["teams"]["home"]["offense_profile"]
    away = matchup["teams"]["away"]["offense_profile"]

    assert home["vs_pitcher_hand"] == "RHP"
    assert home["ops_vs_hand"] == ".812"
    assert home["k_rate_vs_hand"] is None
    assert home["bb_rate_vs_hand"] == "9.5%"

    assert away["vs_pitcher_hand"] == "LHP"
    assert away["ops_vs_hand"] == ".700"
    assert away["k_rate_vs_hand"] == "25.0%"
    assert away["bb_rate_vs_hand"] == "7.5%"

    assert "N/A" not in json.dumps(matchup["teams"])


def test_agents_make_no_offense_claims_without_splits(live_matchup, demo_template):
    packet = data_scout.run(live_matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, live_matchup)
    review = critic.run(report, live_matchup)
    assert review["checks"]

    assert findings["lineup_pressure_points"] == []
    produced = json.dumps([findings, report])
    for text in _demo_team_strings(demo_template):
        assert text not in produced
    for body in (findings["away_vs_home_offense"], findings["home_vs_away_offense"]):
        assert "OPS" not in body
        assert "struggled" not in body
        assert "hits well" not in body

    note = next(s["body"] for s in report["sections"] if s["title"] == "Data Confidence Note")
    assert "and season offense splits" not in note
    assert "not available" in note


def test_agents_skip_only_the_missing_metric(build_live_matchup):
    matchup = build_live_matchup(
        home_team_splits={"vr": {"ops": None, "k_rate": 30.0, "bb_rate": 12.0}},
    )
    findings = matchup_analyst.run(data_scout.run(matchup))

    # Home team has no OPS, so no OPS claim; its K% and BB% are real and may be used.
    body = findings["away_vs_home_offense"]
    assert "OPS" not in body and "struggled" not in body
    assert "strike out often" in body
    assert "above-average rate" in body


def test_demo_teams_keep_offense_profile_and_record(demo_template):
    for side in SIDES:
        team = demo_template["teams"][side]
        assert team["record"]
        for field in OFFENSE_FIELDS:
            assert team["offense_profile"][field]
