"""Opening day keeps its game (QA3-01, Phase 0 "Debut with zero pitches").

On the first game day of the regular season the cutoff (the day before the game, D29) falls before
the season starts: no Statcast range exists. The starters are still known, so the game is shown
with every pitch-based dimension limited, exactly like a debut later in the season. Nothing is
asked of Statcast or Savant, nothing is invented, and the game reaches the published payload.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import validate_payload
from tests.test_as_of_end_to_end import SCHEDULE, FakeResponse

OPENING_DAY = "2026-03-25"
DAY_BEFORE = "2026-03-24"
PITCH_WORDS = ("four-seam", "sinker", "cutter", "slider", "sweeper", "curveball", "changeup", "splitter")


@pytest.fixture
def opening_day(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0})
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )
    schedule = deepcopy(SCHEDULE)
    game = schedule["dates"][0]["games"][0]
    game["officialDate"] = OPENING_DAY
    game["gameDate"] = f"{OPENING_DAY}T23:05:00Z"
    asked: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        asked.append(url)
        if "schedule" in url:
            return FakeResponse(schedule)
        if "/stats?" in url:  # before the season starts the API has no line: a valid empty answer
            return FakeResponse({"stats": [{"splits": []}]})
        if "/people/11" in url:
            return FakeResponse({"people": [{"pitchHand": {"code": "R"}}]})
        if "/people/22" in url:
            return FakeResponse({"people": [{"pitchHand": {"code": "L"}}]})
        raise AssertionError(f"unexpected URL {url}")

    def no_statcast(*args, **kwargs):
        pytest.fail("Statcast must not be asked for a range that ends before the season starts")

    def no_savant(*args, **kwargs):
        pytest.fail("Savant must not be asked for a range that ends before the season starts")

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(lp, "statcast_pitcher", no_statcast)
    monkeypatch.setattr(lp, "_get_text", no_savant)
    return asked


def test_the_qa_probe_an_opening_day_game_with_known_starters_is_kept(opening_day):
    record, snapshot = lp.run_live_pipeline(OPENING_DAY)

    assert record["status"] == "ok" and record["errors"] == []
    assert record["games_scheduled"] == 1 and record["games_live"] == 1
    assert record["skipped_games"] == []
    assert record["as_of"] == DAY_BEFORE and snapshot["as_of"] == DAY_BEFORE

    away, home = snapshot["away_starter"], snapshot["home_starter"]
    assert (away["name"], away["throws"]) == ("Away Ace", "R")
    assert (home["name"], home["throws"]) == ("Home Ace", "L")  # the hand comes from the lookup
    for starter in (away, home):
        sample = starter["sample"]
        assert starter["pitch_mix"] == []
        assert sample["arsenal"]["pitches"] == 0
        assert sample["limited"] == {"arsenal": True, "strikeout": True, "control": True}
        assert sample["arsenal"]["scope"]["through"] == DAY_BEFORE
        assert starter["pitching_profile"]["primary_pitch"] == "Not available"
    assert snapshot["away_team_splits"] == {} and snapshot["home_team_splits"] == {}


def test_a_failed_hand_lookup_on_opening_day_still_skips_the_game_and_says_why(
    opening_day, monkeypatch
):
    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        if "schedule" in url:
            schedule = deepcopy(SCHEDULE)
            schedule["dates"][0]["games"][0]["officialDate"] = OPENING_DAY
            return FakeResponse(schedule)
        if "/stats?" in url:
            return FakeResponse({"stats": []})
        raise OSError("down")

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)

    record, snapshot = lp.run_live_pipeline(OPENING_DAY)

    assert snapshot is None
    assert "mlb_person" in {error["source"] for error in record["errors"]}


def test_the_opening_day_game_reaches_the_published_payload_with_every_dimension_limited(
    opening_day, monkeypatch
):
    # The whole way: pipeline -> run record + snapshot on disk -> generator input check -> agents -> validator.
    assert lp.main_with_args(OPENING_DAY, None) == 0
    snapshot, status = gdj._resolve_live_input()
    assert snapshot is not None, status
    assert status["mode"] == "fetched_snapshot"
    monkeypatch.setattr(gdj, "_live", snapshot)
    monkeypatch.setattr(gdj, "_live_status", status)

    payload = gdj.build_payload()

    assert payload["metadata"]["data_mode"] == "fetched_snapshot"
    live = payload["matchups"][0]
    assert [s["name"] for s in live["starters"].values()] == ["Away Ace", "Home Ace"]
    for starter in live["starters"].values():
        assert starter["sample"]["limited"] == {"arsenal": True, "strikeout": True, "control": True}
        assert starter["season_summary"]["strikeouts"] is None  # unknown, never a measured zero
    text = json.dumps(live["report"]).lower()
    assert not any(word in text for word in PITCH_WORDS), "the report describes pitches nobody threw"
    assert "unsupported" not in {check["status"] for check in live["critic_review"]["checks"]}
    failed = [check for check in validate_payload(payload) if not check.passed]
    assert failed == []
