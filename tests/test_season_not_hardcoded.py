"""No hardcoded season year or start date in the live fetchers (PLAN.md P0.7).

The season comes from `as_of` (or today), and its regular-season dates from the
MLB seasons endpoint. Everything is mocked; nothing is fetched or written.
"""

from __future__ import annotations

from datetime import date
import inspect
import json

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp

SEASONS_PAYLOAD = {
    "seasons": [
        {"regularSeasonStartDate": "2026-03-25", "regularSeasonEndDate": "2026-09-27"}
    ]
}


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_season_dates(season: int) -> tuple[date, date]:
    return date(season, 3, 25), date(season, 9, 27)


@pytest.fixture
def stubbed_seasons(monkeypatch):
    monkeypatch.setattr(lp, "season_dates", fake_season_dates)


@pytest.fixture
def urls(monkeypatch):
    seen: list[str] = []

    def fake_urlopen(req, timeout=None):
        seen.append(req.full_url if hasattr(req, "full_url") else req)
        return FakeResponse({})

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    return seen


def query_value(url: str, key: str) -> str:
    from urllib.parse import parse_qs, urlparse

    return parse_qs(urlparse(url).query)[key][0]


# --- no hardcoded defaults ---------------------------------------------------


@pytest.mark.parametrize(
    "func", [lp.fetch_pitcher_season_stats, lp.fetch_team_splits, lp.fetch_pitcher_statcast]
)
def test_season_parameters_default_to_none(func):
    params = inspect.signature(func).parameters
    for name in ("season", "season_start"):
        if name in params:
            assert params[name].default is None, f"{func.__name__}.{name}"


# --- season_dates -------------------------------------------------------------


@pytest.fixture
def real_season_dates(monkeypatch):
    lp.season_dates.cache_clear()
    yield
    lp.season_dates.cache_clear()


def test_season_dates_come_from_the_mlb_seasons_endpoint(monkeypatch, real_season_dates):
    seen = []

    def fake_urlopen(req, timeout=None):
        seen.append(req.full_url)
        return FakeResponse(SEASONS_PAYLOAD)

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)

    assert lp.season_dates(2026) == (date(2026, 3, 25), date(2026, 9, 27))
    assert lp.season_dates(2026) == (date(2026, 3, 25), date(2026, 9, 27))

    assert len(seen) == 1  # cached for the rest of the run
    assert "/seasons/2026" in seen[0] and "sportId=1" in seen[0]


def test_season_dates_failure_raises_and_is_not_cached(monkeypatch, real_season_dates):
    calls = {"n": 0}

    def flaky(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("down")
        return FakeResponse(SEASONS_PAYLOAD)

    monkeypatch.setattr(lp.urllib.request, "urlopen", flaky)

    with pytest.raises(OSError):
        lp.season_dates(2026)
    assert lp.season_dates(2026) == (date(2026, 3, 25), date(2026, 9, 27))


# --- pitcher fetchers ---------------------------------------------------------


def test_season_stats_season_follows_as_of_year(urls):
    lp.fetch_pitcher_season_stats(7, as_of="2025-07-14")

    assert query_value(urls[0], "season") == "2025"
    assert query_value(urls[0], "startDate") == "2025-01-01"


def test_season_stats_without_as_of_use_the_current_year(urls):
    lp.fetch_pitcher_season_stats(7)

    assert query_value(urls[0], "season") == str(date.today().year)


def _statcast_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_date": pd.Timestamp("2025-07-10"),
                "game_type": "R",
                "pitch_type": "FF",
                "stand": "R",
                "p_throws": "R",
                "release_speed": 94.0,
                "pfx_x": 0.5,
                "pfx_z": 1.1,
                "plate_x": 0.1,
                "plate_z": 2.5,
                "events": None,
            }
        ]
    )


def test_statcast_starts_on_opening_day_of_the_as_of_season(monkeypatch, stubbed_seasons, urls):
    seen = {}

    def fake_statcast(start, end, player_id):
        seen["range"] = (start, end)
        return _statcast_frame()

    monkeypatch.setattr(lp, "statcast_pitcher", fake_statcast)

    lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="2025-07-14")

    assert seen["range"] == ("2025-03-25", "2025-07-14")
    assert query_value(urls[0], "season") == "2025"


def test_explicit_season_start_is_still_honored(monkeypatch, stubbed_seasons, urls):
    seen = {}

    def fake_statcast(start, end, player_id):
        seen["range"] = (start, end)
        return _statcast_frame()

    monkeypatch.setattr(lp, "statcast_pitcher", fake_statcast)

    lp.fetch_pitcher_statcast(1, "Test Pitcher", season_start="2025-05-01", as_of="2025-07-14")

    assert seen["range"] == ("2025-05-01", "2025-07-14")


@pytest.mark.parametrize("as_of", ["2026-03-10", "2026-03-24"])  # opening day is 2026-03-25
def test_statcast_before_opening_day_builds_an_empty_limited_starter_without_fetching(
    monkeypatch, stubbed_seasons, as_of
):
    # QA3-01: a cutoff before the season is not a reason to drop the game. Statcast is not asked
    # (there is no valid range), the starter is built like a debut, and nothing fails.
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: pytest.fail("must not fetch"))
    monkeypatch.setattr(lp, "_run_errors", [])
    requested: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        requested.append(url)
        if "/stats?" in url:
            return FakeResponse({"stats": [{"splits": []}]})  # no line before the season starts
        return FakeResponse({"people": [{"pitchHand": {"code": "L"}}]})

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)

    starter = lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of=as_of)

    assert starter is not None and starter["throws"] == "L"
    assert starter["pitch_mix"] == []
    assert starter["sample"]["arsenal"]["pitches"] == 0
    assert starter["sample"]["limited"] == {"arsenal": True, "strikeout": True, "control": True}
    assert lp._run_errors == []
    assert len(requested) == 2  # the hand and the (empty) season line, nothing else


def test_statcast_before_opening_day_still_fails_when_the_hand_is_unknown(monkeypatch, stubbed_seasons, urls):
    # `urls` answers every request with {}: not a person. The hand is never guessed (QA2-03).
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: pytest.fail("must not fetch"))
    monkeypatch.setattr(lp, "_run_errors", [])

    assert lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="2026-03-10") is None
    assert [e["source"] for e in lp._run_errors] == ["mlb_person"]


def test_statcast_returns_none_when_season_dates_are_unavailable(monkeypatch):
    def boom(season):
        raise OSError("down")

    monkeypatch.setattr(lp, "season_dates", boom)
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: pytest.fail("must not fetch"))

    assert lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="2026-07-14") is None


# --- team splits --------------------------------------------------------------


@pytest.fixture
def batting_calls(monkeypatch, stubbed_seasons):
    calls = {}

    def fake_batting(code, start, end, **kw):
        calls["args"] = (code, start, end)
        return pd.DataFrame([])

    monkeypatch.setattr(lp, "fetch_team_batting_statcast", fake_batting)
    return calls


def test_team_splits_run_from_opening_day_to_the_cutoff(batting_calls):
    lp.fetch_team_splits(147, as_of="2025-07-14")

    assert batting_calls["args"] == ("NYY", date(2025, 3, 25), date(2025, 7, 14))


def test_team_splits_stop_at_the_end_of_the_regular_season(batting_calls):
    # An as_of in October still only needs regular-season months (7 per team, D23).
    lp.fetch_team_splits(147, as_of="2026-10-05")

    assert batting_calls["args"] == ("NYY", date(2026, 3, 25), date(2026, 9, 27))


def test_team_splits_honor_an_explicit_season_start(batting_calls):
    lp.fetch_team_splits(147, as_of="2026-07-14", season_start="2026-05-01")

    assert batting_calls["args"][1] == date(2026, 5, 1)


def test_team_splits_return_empty_when_season_dates_are_unavailable(monkeypatch):
    def boom(season):
        raise OSError("down")

    monkeypatch.setattr(lp, "season_dates", boom)

    assert lp.fetch_team_splits(147, as_of="2026-07-14") == {}


def test_team_splits_api_path_uses_the_current_year(urls):
    lp.fetch_team_splits(147)

    assert query_value(urls[0], "season") == str(date.today().year)


# --- build_live_snapshot --------------------------------------------------------


def test_build_live_snapshot_passes_as_of_to_every_fetcher(monkeypatch):
    game = {
        "game_pk": 1,
        "away_team": "Boston Red Sox",
        "away_team_id": 111,
        "away_team_abbr": "BOS",
        "home_team": "New York Yankees",
        "home_team_id": 147,
        "home_team_abbr": "NYY",
        "away_pitcher_name": "Away Ace",
        "away_pitcher_id": 11,
        "home_pitcher_name": "Home Ace",
        "home_pitcher_id": 22,
        "venue": "Yankee Stadium",
        "start_time": "2026-07-15T23:05:00Z",
        "status": "Final",
    }
    starter = {
        "pitch_mix": [
            {"pitch": "Four-seam", "away_starter": {"overall": 50, "vs_lhh": 50, "vs_rhh": 50, "count": 50, "total": 100}}
        ],
        "velocity_by_pitch": [{"pitch": "Four-seam", "away_starter_velocity": 94.0}],
    }
    seen = {"statcast": [], "splits": []}

    monkeypatch.setattr(lp, "fetch_todays_games", lambda target: [game])
    monkeypatch.setattr(
        lp,
        "fetch_pitcher_statcast",
        lambda pid, name, **kw: seen["statcast"].append(kw.get("as_of")) or {"name": name, **starter},
    )
    monkeypatch.setattr(
        lp, "fetch_team_splits", lambda tid, **kw: seen["splits"].append(kw.get("as_of")) or {}
    )

    snapshot = lp.build_live_snapshot("2026-07-15", as_of="2026-07-14")

    assert seen["statcast"] == ["2026-07-14", "2026-07-14"]
    assert seen["splits"] == ["2026-07-14", "2026-07-14"]
    assert snapshot["as_of"] == "2026-07-14"
