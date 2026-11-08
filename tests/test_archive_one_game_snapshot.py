"""R4-D4: the live pipeline builds one named game from a day already read, with a season line from a provider (D66).

The daily job passes none of these arguments, so its behavior is the one the other tests lock; here the new arguments.
"""

from __future__ import annotations

import pytest

from data_pipeline.fetchers import live_pipeline as lp

STARTER = {
    "pitch_mix": [{"pitch": "Four-seam", "away_starter": {"overall": 50, "vs_lhh": 50, "vs_rhh": 50, "count": 50, "total": 100}}],
    "velocity_by_pitch": [{"pitch": "Four-seam", "away_starter_velocity": 94.0}],
}


def game(pk, away_pitcher=11, home_pitcher=22, day="2026-07-15"):
    return {
        "game_pk": pk, "official_date": day, "away_team": "Boston Red Sox", "away_team_id": 111, "away_team_abbr": "BOS",
        "home_team": "New York Yankees", "home_team_id": 147, "home_team_abbr": "NYY",
        "away_pitcher_name": "Away Ace", "away_pitcher_id": away_pitcher, "home_pitcher_name": "Home Ace",
        "home_pitcher_id": home_pitcher, "venue": "Yankee Stadium", "start_time_utc": "2026-07-15T23:05:00Z",
        "status": "Final", "detailed_state": "Final",
    }


@pytest.fixture
def seen(monkeypatch):
    log = {"statcast": [], "schedule": [], "provider": []}
    monkeypatch.setattr(lp, "fetch_todays_games", lambda target: log["schedule"].append(target) or [game(1)])
    monkeypatch.setattr(
        lp, "fetch_pitcher_statcast",
        lambda pid, name, **kw: log["statcast"].append((pid, kw.get("as_of"), kw.get("season_stats"))) or {"name": name, **STARTER},
    )
    monkeypatch.setattr(lp, "fetch_team_splits", lambda tid, **kw: {})
    monkeypatch.setattr(lp, "fetch_series_context", lambda g, **kw: None)
    return log


def test_without_the_new_arguments_the_day_is_asked_and_the_season_line_is_the_pipelines_own(seen):
    snapshot = lp.build_live_snapshot("2026-07-15", as_of="2026-07-14")
    assert seen["schedule"] == ["2026-07-15"] and snapshot is not None
    assert seen["statcast"] == [(11, "2026-07-14", None), (22, "2026-07-14", None)]  # None: each fetch asks the API itself


def test_one_named_game_is_built_from_a_day_already_read_and_the_schedule_is_not_asked_again(seen):
    day = [game(1), game(2, 33, 44), game(3, 55, 66)]
    snapshot = lp.build_live_snapshot("2026-07-15", only_game_pk=2, games=day)
    assert seen["schedule"] == []
    assert [c[0] for c in seen["statcast"]] == [33, 44]
    assert [g["featured_game"]["game_pk"] for g in snapshot["live_games"]] == [2]
    assert snapshot["featured_game"]["game_pk"] == 2


def test_the_run_record_counts_the_days_games_and_the_one_built(seen):
    info = {}
    lp.build_live_snapshot("2026-07-15", only_game_pk=3, games=[game(1), game(2, 33, 44), game(3, 55, 66)], run_info=info)
    assert info["games_scheduled"] == 3 and info["games_live"] == 1


def test_a_game_that_is_not_in_the_day_or_has_no_probable_starter_gives_no_snapshot(seen):
    day = [game(1), game(2, away_pitcher=None)]
    assert lp.build_live_snapshot("2026-07-15", only_game_pk=99, games=day) is None
    assert lp.build_live_snapshot("2026-07-15", only_game_pk=2, games=day) is None
    assert seen["statcast"] == []


def test_the_provider_gives_each_starters_season_line_as_of_the_games_own_date(seen):
    lines = {11: {"era": "3.00", "innings": "10.0"}, 22: {}}
    asked = []

    def provider(pitcher_id, official_date):
        asked.append((pitcher_id, official_date))
        return lines[pitcher_id]

    lp.build_live_snapshot("2026-07-15", only_game_pk=1, games=[game(1)], season_stats_provider=provider)
    assert asked == [(11, "2026-07-15"), (22, "2026-07-15")]
    # `{}` is "unavailable" and is passed on as it is: never turned into a request or into a zero line
    assert seen["statcast"] == [(11, "2026-07-14", lines[11]), (22, "2026-07-14", {})]


def test_an_empty_day_given_by_the_caller_is_a_day_with_no_games(seen):
    info = {}
    assert lp.build_live_snapshot("2026-07-15", games=[], run_info=info) is None
    assert seen["schedule"] == [] and info["games_scheduled"] == 0
