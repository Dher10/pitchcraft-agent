"""as_of cutoff in the live fetchers (PLAN.md P0.2, Phase 0 Gherkin "As-of cutoff
prevents leakage").

Every network call and the Statcast download are mocked; nothing is fetched,
and nothing is written under public/data or data_cache.
"""

from __future__ import annotations

from datetime import date
import json
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def install_urlopen(monkeypatch, router) -> list[str]:
    """Route every urlopen call through router(url) -> payload; return the URL log."""

    urls: list[str] = []

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        urls.append(url)
        return FakeResponse(router(url))

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    return urls


def query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


# --- _parse_as_of -----------------------------------------------------------


def test_parse_as_of_accepts_str_and_date_and_defaults_to_today():
    assert lp._parse_as_of("2026-07-14") == date(2026, 7, 14)
    assert lp._parse_as_of(date(2026, 7, 14)) == date(2026, 7, 14)
    assert lp._parse_as_of(None) == date.today()


@pytest.mark.parametrize("bad", ["14/07/2026", "not-a-date", 20260714])
def test_parse_as_of_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        lp._parse_as_of(bad)


# --- Statcast ---------------------------------------------------------------


def _statcast_frame() -> pd.DataFrame:
    rows = []
    for game_date in ("2026-07-10", "2026-07-14", "2026-07-15", "2026-07-20"):
        for pitch_type, stand in (("FF", "L"), ("FF", "R"), ("SL", "R")):
            rows.append(
                {
                    "game_date": pd.Timestamp(game_date),
                    "pitch_type": pitch_type,
                    "stand": stand,
                    "p_throws": "R",
                    "release_speed": 94.0,
                    "pfx_x": 0.5,
                    "pfx_z": 1.1,
                    "plate_x": 0.1,
                    "plate_z": 2.5,
                    "events": None,
                }
            )
    return pd.DataFrame(rows)


def test_statcast_stops_at_as_of(monkeypatch):
    calls = {}

    def fake_statcast(start, end, player_id):
        calls["range"] = (start, end)
        return _statcast_frame()  # a source that ignores the end date

    seen = {}
    real_process = lp.process_pitcher_statcast

    def spy_process(df, name):
        seen["df"] = df
        return real_process(df, name)

    monkeypatch.setattr(lp, "statcast_pitcher", fake_statcast)
    monkeypatch.setattr(lp, "process_pitcher_statcast", spy_process)
    install_urlopen(monkeypatch, lambda url: {})

    result = lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="2026-07-14")

    assert result is not None
    assert calls["range"][1] == "2026-07-14"
    assert pd.to_datetime(seen["df"]["game_date"]).max() == pd.Timestamp("2026-07-14")
    assert len(seen["df"]) == 6  # 3 pitches on 07-10 and 3 on 07-14


def test_statcast_keeps_only_regular_season_and_postseason_before_as_of(monkeypatch):
    rows = []
    # (game_date, game_type): spring and exhibition never count; postseason only
    # when dated on or before as_of.
    for game_date, game_type in (
        ("2026-03-10", "S"),  # spring training, before as_of
        ("2026-04-02", "E"),  # exhibition
        ("2026-04-03", "A"),  # all-star
        ("2026-05-01", "R"),
        ("2026-07-10", "R"),
        ("2026-07-12", "D"),  # postseason on or before as_of: counts
        ("2026-07-16", "D"),  # postseason after as_of: dropped by the date filter
        ("2026-07-16", "R"),
    ):
        rows.append({**_statcast_frame().iloc[0].to_dict(), "game_date": pd.Timestamp(game_date), "game_type": game_type})
    frame = pd.DataFrame(rows)

    seen = {}
    real_process = lp.process_pitcher_statcast

    def spy_process(df, name):
        seen["df"] = df
        return real_process(df, name)

    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame)
    monkeypatch.setattr(lp, "process_pitcher_statcast", spy_process)
    install_urlopen(monkeypatch, lambda url: {})

    result = lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="2026-07-14")

    assert result is not None
    kept = seen["df"][["game_date", "game_type"]]
    assert sorted(zip(kept["game_date"].dt.strftime("%Y-%m-%d"), kept["game_type"])) == [
        ("2026-05-01", "R"),
        ("2026-07-10", "R"),
        ("2026-07-12", "D"),
    ]


def test_statcast_without_as_of_ends_today(monkeypatch):
    calls = {}

    def fake_statcast(start, end, player_id):
        calls["range"] = (start, end)
        return _statcast_frame()

    monkeypatch.setattr(lp, "statcast_pitcher", fake_statcast)
    install_urlopen(monkeypatch, lambda url: {})

    lp.fetch_pitcher_statcast(1, "Test Pitcher")

    assert calls["range"][1] == date.today().isoformat()


def test_statcast_rejects_bad_as_of(monkeypatch):
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: _statcast_frame())
    with pytest.raises(ValueError):
        lp.fetch_pitcher_statcast(1, "Test Pitcher", as_of="yesterday")


# --- Pitcher season stats ---------------------------------------------------

_SEASON_PAYLOAD = {
    "stats": [
        {
            "splits": [
                {
                    "stat": {
                        "era": "3.10",
                        "whip": "1.05",
                        "inningsPitched": "101.0",
                        "strikeOuts": 110,
                        "baseOnBalls": 30,
                        "homeRuns": 10,
                    }
                }
            ]
        }
    ]
}


def test_season_stats_use_date_range_when_as_of_is_set(monkeypatch):
    urls = install_urlopen(monkeypatch, lambda url: _SEASON_PAYLOAD)

    result = lp.fetch_pitcher_season_stats(7, season=2026, as_of="2026-07-14")

    q = query(urls[0])
    assert q["stats"] == "byDateRange"
    assert q["startDate"] == "2026-01-01"
    assert q["endDate"] == "2026-07-14"
    assert result["era"] == "3.10"


def test_season_stats_without_as_of_keep_season_request(monkeypatch):
    urls = install_urlopen(monkeypatch, lambda url: _SEASON_PAYLOAD)

    lp.fetch_pitcher_season_stats(7, season=2026)

    q = query(urls[0])
    assert q["stats"] == "season"
    assert "endDate" not in q


def test_season_stats_reject_as_of_from_another_season():
    with pytest.raises(ValueError):
        lp.fetch_pitcher_season_stats(7, season=2026, as_of="2025-07-14")


# --- Team splits ------------------------------------------------------------


# With as_of the splits come from Statcast, not this API: tests/test_team_splits_as_of.py.


def test_team_splits_without_as_of_still_fetch(monkeypatch):
    payload = {
        "stats": [
            {
                "splits": [
                    {
                        "split": {"code": "vr"},
                        "stat": {
                            "ops": ".750",
                            "avg": ".250",
                            "strikeOuts": 100,
                            "baseOnBalls": 50,
                            "plateAppearances": 500,
                        },
                    }
                ]
            }
        ]
    }
    urls = install_urlopen(monkeypatch, lambda url: payload)

    result = lp.fetch_team_splits(147, season=2026)

    assert result["vr"]["k_rate"] == 20.0
    assert "startDate" not in query(urls[0])


# --- Series status ----------------------------------------------------------

# A best-of-five: game 1 on 10-03, game 2 on 10-04, game 3 on 10-06 (the game we
# preview), game 4 on 10-07. seriesStatus is the standing AFTER each game.
_SERIES = {
    "gameType": "D",
    "seriesDescription": "NL Division Series",
    "gamesInSeries": 5,
}
_GAMES = {
    101: {"num": 1, "date": "2026-10-03", "result": "LAD leads 1-0", "w": 1, "l": 0},
    102: {"num": 2, "date": "2026-10-04", "result": "Series tied 1-1", "w": 1, "l": 1},
    103: {"num": 3, "date": "2026-10-06", "result": "LAD leads 2-1", "w": 2, "l": 1},
    104: {"num": 4, "date": "2026-10-07", "result": "LAD wins 3-1", "w": 3, "l": 1},
}


def _game_entry(pk: int) -> dict:
    g = _GAMES[pk]
    return {
        "gamePk": pk,
        "officialDate": g["date"],
        "seriesGameNumber": g["num"],
        "status": {"abstractGameState": "Final"},
        "teams": {
            "away": {"team": {"id": 144, "name": "Atlanta Braves"}},
            "home": {"team": {"id": 119, "name": "Los Angeles Dodgers"}},
        },
        "seriesStatus": {
            "result": g["result"],
            "wins": g["w"],
            "losses": g["l"],
            "isOver": g["result"].endswith("wins 3-1"),
        },
        **_SERIES,
    }


def _series_router(url: str) -> dict:
    q = query(url)
    if "gamePk" in q:
        return {"dates": [{"games": [_game_entry(int(q["gamePk"]))]}]}
    # Series lookup: deliberately ignores endDate, like a misbehaving source,
    # so the fetcher has to enforce the cutoff itself.
    return {
        "dates": [{"games": [_game_entry(pk) for pk in sorted(_GAMES)]}],
    }


def test_series_status_first_game_is_zero_zero(monkeypatch):
    install_urlopen(monkeypatch, _series_router)

    result = lp.fetch_series_status(101, as_of="2026-10-02")

    assert result["games_played"] == 0
    assert (result["wins"], result["losses"]) == (0, 0)
    assert result["is_over"] is False
    assert result["source_game_pk"] is None


def test_series_status_is_the_standing_before_first_pitch(monkeypatch):
    install_urlopen(monkeypatch, _series_router)

    result = lp.fetch_series_status(103, as_of="2026-10-05")

    assert result["result"] == "Series tied 1-1"
    assert result["games_played"] == 2
    assert result["source_game_pk"] == 102
    assert result["as_of"] == "2026-10-05"


def test_series_status_never_shows_games_after_the_cutoff(monkeypatch):
    install_urlopen(monkeypatch, _series_router)

    # Cutoff after game 1 only: games 2, 3 and 4 are in the source but must not leak.
    result = lp.fetch_series_status(103, as_of="2026-10-03")

    assert result["result"] == "LAD leads 1-0"
    assert result["source_game_pk"] == 101
    assert "LAD wins 3-1" not in json.dumps(result)


def test_series_status_never_includes_the_game_itself(monkeypatch):
    install_urlopen(monkeypatch, _series_router)

    # as_of is the game's own date: game 3 is finished in the source, but the
    # standing before its first pitch is still the one after game 2.
    result = lp.fetch_series_status(103, as_of="2026-10-06")

    assert result["source_game_pk"] == 102


def test_series_status_is_empty_for_regular_season_games(monkeypatch):
    def router(url):
        entry = _game_entry(103)
        entry["gameType"] = "R"
        return {"dates": [{"games": [entry]}]}

    install_urlopen(monkeypatch, router)

    assert lp.fetch_series_status(103, as_of="2026-10-05") == {}


def test_series_status_returns_empty_on_network_failure(monkeypatch):
    def boom(req, timeout=None):
        raise OSError("down")

    monkeypatch.setattr(lp.urllib.request, "urlopen", boom)

    assert lp.fetch_series_status(103, as_of="2026-10-05") == {}
