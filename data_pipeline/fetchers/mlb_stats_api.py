"""
Optional lightweight fetcher for MLB Stats API public endpoints.
Only runs when explicitly called - never required for the demo.

Public endpoints used (no auth, no API key):
- Schedule: https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=YYYY-MM-DD
- Probable pitchers are included in the schedule response.

Usage:
  from data_pipeline.fetchers import mlb_stats_api
  from data_pipeline.fetchers.cache_manager import save_raw
  data = mlb_stats_api.fetch_schedule("2026-06-28")
  if data:
      save_raw("schedule_2026-06-28", data)
"""

from __future__ import annotations

import json
import urllib.request

MLB_SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"


def fetch_schedule(date_str: str, timeout: int = 5) -> dict | None:
    """
    Fetch MLB schedule for a given date (YYYY-MM-DD).
    Returns the parsed JSON response or None on any error.
    Never raises - the demo must survive without this.
    """
    url = f"{MLB_SCHEDULE_URL}?sportId=1&date={date_str}&hydrate=probablePitcher"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            print(
                f"[FETCH] MLB schedule for {date_str}: "
                f"{len(data.get('dates', []))} date(s) returned"
            )
            return data
    except Exception as exc:
        print(f"[FETCH] MLB Stats API unavailable ({exc}) - falling back to demo data")
        return None


def extract_probable_pitchers(schedule_data: dict) -> list[dict]:
    """
    Extract probable pitcher names and team from a schedule API response.
    Returns a list of dicts: [{game_pk, away_team, home_team, away_pitcher, home_pitcher}]
    """
    results = []
    for date in schedule_data.get("dates", []):
        for game in date.get("games", []):
            away = game.get("teams", {}).get("away", {})
            home = game.get("teams", {}).get("home", {})
            results.append(
                {
                    "game_pk": game.get("gamePk"),
                    "away_team": away.get("team", {}).get("name"),
                    "home_team": home.get("team", {}).get("name"),
                    "away_pitcher": away.get("probablePitcher", {}).get("fullName"),
                    "home_pitcher": home.get("probablePitcher", {}).get("fullName"),
                }
            )
    return results
