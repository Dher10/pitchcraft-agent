"""A live game's start time is the UTC instant of the schedule, shown in the source's zone or as UTC (QA4-03, D33).

Run 4: the schedule's UTC `gameDate` was copied into `start_time_local` and the Oracle Park demo's
`America/Los_Angeles` stayed in `timezone`, so the page printed "2026-07-15T23:05:00Z America/Los_Angeles".
Now the game keeps `start_time_utc` (an explicit instant) and `timezone` is the venue's IANA zone when the
schedule gives one (`hydrate=venue(timezone)`, checked against the live API on 2026-10-11) and None otherwise.
The page does the conversion; a zone is never taken from the demo or from the viewer's browser.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest

from data_pipeline import demo_inputs
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import live_pipeline as lp
from tests import test_as_of_end_to_end as e2e
from tests.live_helpers import CUTOFF, GAME_DAY, failed_checks, hand_snapshot, schedule_with_zone, use_snapshot
from tests.test_as_of_end_to_end import leaky_sources  # noqa: F401  (fixture)

INSTANT = "2026-07-15T23:05:00Z"  # the game of the end-to-end schedule


# --- the fetcher ------------------------------------------------------------------------------------


def fetch_game(monkeypatch, schedule: dict) -> tuple[list[dict], list[str]]:
    monkeypatch.setattr(lp, "_run_errors", [])
    asked: list[str] = []

    def fake_urlopen(req, timeout=None):
        asked.append(req.full_url if hasattr(req, "full_url") else req)
        return e2e.FakeResponse(schedule)

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    return lp.fetch_todays_games(e2e.GAME_DAY), asked


@pytest.mark.parametrize("zone", ["America/New_York", "America/Los_Angeles", "America/Phoenix", None])
def test_the_schedule_gives_the_utc_instant_and_the_venue_zone(monkeypatch, zone):
    games, asked = fetch_game(monkeypatch, schedule_with_zone(e2e.SCHEDULE, zone))

    assert len(games) == 1 and lp._run_errors == []
    assert games[0]["start_time_utc"] == INSTANT
    assert games[0]["venue_timezone"] == zone  # None when the source does not say: never a guess
    assert "start_time" not in games[0]
    assert "venue(timezone)" in asked[0]


@pytest.mark.parametrize(
    "bad",
    ["2026-07-15", "2026-07-15T23:05:00", "2026-07-15T19:05:00-04:00", "2026-13-45T23:05:00Z", "7:05 PM", "yesterday"],
)
def test_a_game_date_that_is_not_a_utc_instant_is_a_source_failure(monkeypatch, bad):
    schedule = deepcopy(e2e.SCHEDULE)
    schedule["dates"][0]["games"][0]["gameDate"] = bad

    games, _ = fetch_game(monkeypatch, schedule)

    assert games == []
    assert [error["source"] for error in lp._run_errors] == ["mlb_schedule"]
    assert "gameDate" in lp._run_errors[0]["message"]


def test_a_venue_zone_with_the_wrong_type_is_a_source_failure_and_one_without_an_id_is_just_unknown(monkeypatch):
    schedule = deepcopy(e2e.SCHEDULE)
    schedule["dates"][0]["games"][0]["venue"]["timeZone"] = {"id": 5}
    games, _ = fetch_game(monkeypatch, schedule)
    assert games == [] and [error["source"] for error in lp._run_errors] == ["mlb_schedule"]

    schedule["dates"][0]["games"][0]["venue"]["timeZone"] = {"tz": "EDT"}
    games, _ = fetch_game(monkeypatch, schedule)
    assert len(games) == 1 and games[0]["venue_timezone"] is None and lp._run_errors == []


# --- the published game -----------------------------------------------------------------------------


@pytest.mark.parametrize("zone", [None, "America/New_York"])
def test_the_published_game_keeps_the_instant_and_never_a_demo_zone(leaky_sources, monkeypatch, zone):
    monkeypatch.setattr(e2e, "SCHEDULE", schedule_with_zone(e2e.SCHEDULE, zone))
    record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)
    assert record["status"] == "ok", record
    use_snapshot(monkeypatch, snapshot)

    payload = gdj.build_payload()

    game = payload["matchups"][0]["game"]
    assert game["start_time_utc"] == INSTANT
    assert game["timezone"] == zone
    assert game["start_time_local"] is None
    assert "America/Los_Angeles" not in str(game)
    assert failed_checks(payload) == []


# --- publication validation -------------------------------------------------------------------------


@pytest.fixture()
def live_payload(monkeypatch) -> dict:
    use_snapshot(monkeypatch, hand_snapshot(complete=True))
    payload = gdj.build_payload()
    assert failed_checks(payload) == []
    return payload


def failed_time_checks(payload: dict) -> list[str]:
    return [description for description in failed_checks(payload) if "start time" in description]


@pytest.mark.parametrize(
    "bad",
    [None, "", "2026-07-04T18:07:00", "2026-07-04T14:07:00-04:00", "2026-07-04", "6:07 PM", 1783000000],
)
def test_a_live_game_without_a_utc_instant_fails_publication(live_payload, bad):
    live_payload["matchups"][0]["game"]["start_time_utc"] = bad

    assert failed_time_checks(live_payload)


def test_a_live_game_that_lost_the_field_fails_publication(live_payload):
    del live_payload["matchups"][0]["game"]["start_time_utc"]

    assert failed_time_checks(live_payload)


def test_a_live_game_zone_must_be_text_or_unknown(live_payload):
    live_payload["matchups"][0]["game"]["timezone"] = 5

    assert failed_time_checks(live_payload)


def test_the_demo_matchups_are_not_held_to_the_live_rule(live_payload):
    # F4 (D2.4a): the generator puts none in a live file; one put there by hand is rule 6's finding, not this rule's.
    demo = deepcopy(demo_inputs.build_demo_payload()["matchups"][1])
    live_payload["matchups"].append(demo)

    assert "start_time_utc" not in demo["game"] or demo["game"]["start_time_utc"] is None
    assert failed_time_checks(live_payload) == []


# --- what a snapshot must carry ---------------------------------------------------------------------


def game_and_problem(mutate) -> str | None:
    game = deepcopy(hand_snapshot(complete=True)["live_games"][0])
    mutate(game)
    return gdj._game_unsafe(game, date.fromisoformat(GAME_DAY), date.fromisoformat(CUTOFF))


def test_a_complete_game_is_safe():
    assert game_and_problem(lambda game: None) is None


@pytest.mark.parametrize(
    "field",
    [
        "away_team", "home_team", "away_team_id", "home_team_id", "away_team_abbr", "home_team_abbr",
        "away_pitcher_id", "home_pitcher_id", "start_time_utc",
    ],
)
def test_a_game_without_a_field_the_schedule_always_sends_is_rejected(field):
    problem = game_and_problem(lambda game: game["featured_game"].pop(field))

    assert problem and field in problem


def test_a_snapshot_written_with_the_old_start_time_name_is_rejected():
    def rename(game):
        game["featured_game"]["start_time"] = game["featured_game"].pop("start_time_utc")

    problem = game_and_problem(rename)

    assert problem and "start_time_utc" in problem


@pytest.mark.parametrize("bad", ["2026-07-04T18:07:00", "7:07 PM", ""])
def test_a_snapshot_start_time_that_is_not_a_utc_instant_is_rejected(bad):
    problem = game_and_problem(lambda game: game["featured_game"].update(start_time_utc=bad))

    assert problem and "start_time_utc" in problem


@pytest.mark.parametrize("field", ["venue", "venue_timezone", "status", "game_pk"])
def test_what_the_schedule_may_leave_out_does_not_reject_the_game(field):
    assert game_and_problem(lambda game: game["featured_game"].pop(field)) is None
