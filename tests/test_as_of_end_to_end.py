"""Phase 0 Gherkin "As-of cutoff prevents leakage", end to end (PLAN.md P0.11).

    Given a game played on 2026-07-15
    When the pipeline runs with as_of 2026-07-14
    Then no Statcast row, season stat or team split is dated after 2026-07-14

The whole live pipeline runs (`run_live_pipeline`) over sources that do leak: Statcast
returns pitches from after the cutoff and from spring training, the season-stats API
answers with "future" numbers for any end date after the cutoff, and the Savant
team-batting source ignores the requested end date. The snapshot is then inspected.

Series status joins the snapshot in P1.5-b (tests/test_series_snapshot.py); its cutoff is covered at fetcher
level in test_fetchers_as_of.py and, for the historical dataset, by P2.4 (D28).
"""

from __future__ import annotations

from datetime import date
import json
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp

CUTOFF = "2026-07-14"
GAME_DAY = "2026-07-15"

# The API line that goes with the Statcast rows below: 37 plate appearances up to the cutoff (every fourth of 150
# pitches ends one), and 46 over every regular-season row the source holds, so neither line says more than the
# frame it is compared with (F21). The counts differ from Statcast's, which has no strikeout, so the test can tell
# which source gave them.
EARLY_STATS = {"era": "3.10", "whip": "1.05", "inningsPitched": "9.1", "strikeOuts": 9,
               "baseOnBalls": 3, "homeRuns": 2, "battersFaced": 37}
FUTURE_STATS = {"era": "9.99", "whip": "2.50", "inningsPitched": "12.1", "strikeOuts": 12,
                "baseOnBalls": 4, "homeRuns": 3, "battersFaced": 46}

SCHEDULE = {
    "dates": [
        {
            "games": [
                {
                    "gamePk": 1,
                    "officialDate": GAME_DAY,
                    "gameDate": f"{GAME_DAY}T23:05:00Z",
                    "status": {"abstractGameState": "Preview", "detailedState": "Scheduled"},
                    "venue": {"name": "Yankee Stadium"},
                    "teams": {
                        "away": {
                            "team": {"id": 111, "name": "Boston Red Sox"},
                            "probablePitcher": {"id": 11, "fullName": "Away Ace"},
                        },
                        "home": {
                            "team": {"id": 147, "name": "New York Yankees"},
                            "probablePitcher": {"id": 22, "fullName": "Home Ace"},
                        },
                    },
                }
            ]
        }
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


def pitcher_rows(game_date: str, game_type: str, pitch_type: str, n: int) -> list[dict]:
    """Rows as Statcast sends them: a plate appearance ends on about every fourth pitch (`events`)."""

    return [
        {
            "game_date": pd.Timestamp(game_date),
            "game_type": game_type,
            "pitch_type": pitch_type,
            "stand": "R",
            "p_throws": "R",
            "release_speed": 94.0,
            "pfx_x": 0.5,
            "pfx_z": 1.1,
            "plate_x": 0.1,
            "plate_z": 2.5,
            "events": "field_out" if index % 4 == 3 else None,
        }
        for index in range(n)
    ]


# 150 pitches up to the cutoff, then leaks: sweepers after it, knuckleballs in spring.
STATCAST = pd.DataFrame(
    pitcher_rows("2026-07-10", "R", "FF", 120)
    + pitcher_rows("2026-07-14", "R", "SL", 30)
    + pitcher_rows("2026-07-15", "R", "ST", 25)  # the game day itself
    + pitcher_rows("2026-07-20", "R", "ST", 15)
    + pitcher_rows("2026-03-10", "S", "KN", 25)  # spring training
)


def batting_csv(team: str, month_start: str) -> str:
    """Savant-like rows for one team's July: 20 PA up to the cutoff, 50 home runs after."""

    if not month_start.startswith("2026-07"):
        return ""
    home = team == "NYY"
    base = {
        "game_type": "R",
        "home_team": "NYY" if home else "BAL",
        "away_team": "BOS" if not home else "TOR",
        "inning_topbot": "Bot" if home else "Top",
        "p_throws": "R",
    }
    rows = [{**base, "game_date": "2026-07-10", "events": "field_out"} for _ in range(20)]
    rows += [{**base, "game_date": "2026-07-20", "events": "home_run"} for _ in range(50)]
    return pd.DataFrame(rows).to_csv(index=False)


@pytest.fixture
def leaky_sources(monkeypatch, tmp_path):
    api_urls: list[str] = []
    savant_urls: list[str] = []

    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0})
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        api_urls.append(url)
        if "schedule" in url:
            return FakeResponse(SCHEDULE)
        if "/stats?" in url:
            query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
            stat = EARLY_STATS if query.get("endDate", "9999") <= CUTOFF else FUTURE_STATS
            return FakeResponse({"stats": [{"splits": [{"stat": stat}]}]})
        raise AssertionError(f"unexpected URL {url}")

    def fake_statcast(start, end, player_id):
        # A source that ignores the end date: it returns everything it has.
        return STATCAST.copy()

    def fake_savant(url, timeout=60):
        savant_urls.append(url)
        query = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        # Ignores game_date_lt: a July chunk comes back with the days after the cutoff too.
        return batting_csv(query["team"], query["game_date_gt"])

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(lp, "statcast_pitcher", fake_statcast)
    monkeypatch.setattr(lp, "_get_text", fake_savant)
    return api_urls, savant_urls


def test_no_row_stat_or_split_after_the_cutoff_reaches_the_snapshot(leaky_sources):
    api_urls, savant_urls = leaky_sources

    record, snapshot = lp.run_live_pipeline(GAME_DAY, as_of=CUTOFF)

    assert record["status"] == "ok" and record["errors"] == []
    assert snapshot["as_of"] == CUTOFF and record["as_of"] == CUTOFF

    # Statcast: only the 150 pitches up to the cutoff; no game-day, later or spring pitch.
    for slot in ("away_starter", "home_starter"):
        starter = snapshot[slot]
        assert {row["pitch"] for row in starter["pitch_mix"]} == {"Four-seam", "Slider"}
        assert starter["sample"]["arsenal"]["pitches"] == 150
        assert starter["sample"]["arsenal"]["scope"]["through"] == CUTOFF

    # Season stats: the cutoff numbers, not the ones the API gives for later dates.
    for slot in ("away_starter", "home_starter"):
        summary = snapshot[slot]["season_summary"]
        rates = snapshot[slot]["sample"]["rates"]
        assert (summary["era"], summary["strikeouts"], summary["walks"]) == ("3.10", 9, 3)
        assert (rates["batters_faced"], rates["home_runs"]) == (37, 2)
        assert rates["scope"]["through"] == CUTOFF

    # Team splits: 20 plate appearances up to the cutoff; the 50 home runs after it are out.
    for key in ("away_team_splits", "home_team_splits"):
        splits = snapshot[key]
        assert set(splits) == {"vr"}
        assert splits["vr"]["plate_appearances"] == 20
        assert splits["vr"]["ops"] == ".000"

    # Nothing from after the cutoff anywhere in the serialized snapshot.
    # Scan the data (starters, charts, splits), not the game's own schedule metadata:
    # the requested game day and its start time legitimately name the game day.
    data = [
        {key: value for key, value in game.items() if key != "featured_game"}
        for game in snapshot["live_games"]
    ]
    dump = json.dumps(data)
    for leaked in ("Sweeper", "Knuckleball", "9.99", GAME_DAY, "2026-07-20"):
        assert leaked not in dump, f"{leaked!r} reached the snapshot"

    # And no request asked a source for data past the cutoff.
    stats_urls = [u for u in api_urls if "/stats?" in u]
    assert stats_urls and all(f"endDate={CUTOFF}" in u for u in stats_urls)
    assert savant_urls
    assert all(
        parse_qs(urlparse(u).query)["game_date_lt"][0] <= CUTOFF for u in savant_urls
    )


def test_the_same_sources_do_leak_when_a_fetcher_is_given_a_late_cutoff(leaky_sources):
    # Control: proves the fixtures really contain post-cutoff data, so the test above
    # is not passing just because the leaks were never reachable. It calls the fetchers
    # directly with a late cutoff: the pipeline itself no longer accepts one (D29).
    starter = lp.fetch_pitcher_statcast(11, "Away Ace", as_of="2026-10-10")

    sweepers = {row["pitch"] for row in starter["pitch_mix"]}
    assert "Sweeper" in sweepers
    assert starter["season_summary"]["era"] == "9.99"
