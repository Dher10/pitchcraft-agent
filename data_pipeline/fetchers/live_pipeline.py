"""Fetch and cache a live MLB matchup snapshot for PitchCraft."""

from __future__ import annotations

from datetime import date
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any


PYBASEBALL_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "pybaseball"
os.environ.setdefault("PYBASEBALL_CACHE", str(PYBASEBALL_CACHE_DIR))

import numpy as np
import pybaseball
from pybaseball import statcast_pitcher

pybaseball.cache.enable()

MLB_TEAM_ABBR_BY_ID = {
    108: "LAA",
    109: "ARI",
    110: "BAL",
    111: "BOS",
    112: "CHC",
    113: "CIN",
    114: "CLE",
    115: "COL",
    116: "DET",
    117: "HOU",
    118: "KC",
    119: "LAD",
    120: "WSH",
    121: "NYM",
    133: "ATH",
    134: "PIT",
    135: "SD",
    136: "SEA",
    137: "SF",
    138: "STL",
    139: "TB",
    140: "TEX",
    141: "TOR",
    142: "MIN",
    143: "PHI",
    144: "ATL",
    145: "CWS",
    146: "MIA",
    147: "NYY",
    158: "MIL",
}

MLB_TEAM_ABBR_BY_NAME = {
    "Arizona Diamondbacks": "ARI",
    "Athletics": "ATH",
    "Atlanta Braves": "ATL",
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "Chicago Cubs": "CHC",
    "Chicago White Sox": "CWS",
    "Cincinnati Reds": "CIN",
    "Cleveland Guardians": "CLE",
    "Colorado Rockies": "COL",
    "Detroit Tigers": "DET",
    "Houston Astros": "HOU",
    "Kansas City Royals": "KC",
    "Los Angeles Angels": "LAA",
    "Los Angeles Dodgers": "LAD",
    "Miami Marlins": "MIA",
    "Milwaukee Brewers": "MIL",
    "Minnesota Twins": "MIN",
    "New York Mets": "NYM",
    "New York Yankees": "NYY",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "PHI",
    "Pittsburgh Pirates": "PIT",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF",
    "Seattle Mariners": "SEA",
    "St. Louis Cardinals": "STL",
    "Tampa Bay Rays": "TB",
    "Texas Rangers": "TEX",
    "Toronto Blue Jays": "TOR",
    "Washington Nationals": "WSH",
}

PITCH_NAME_MAP = {
    "FF": "Four-seam",
    "SI": "Sinker",
    "FC": "Cutter",
    "SL": "Slider",
    "CH": "Changeup",
    "CU": "Curveball",
    "KC": "Curveball",
    "FS": "Splitter",
    "ST": "Sweeper",
    "SV": "Slurve",
    "EP": "Eephus",
    "CS": "Curveball",
    "FO": "Forkball",
    "KN": "Knuckleball",
}


def _team_abbreviation(team: dict[str, Any]) -> str:
    raw_abbr = team.get("abbreviation")
    if raw_abbr:
        return raw_abbr
    team_id = team.get("id")
    if team_id in MLB_TEAM_ABBR_BY_ID:
        return MLB_TEAM_ABBR_BY_ID[team_id]
    return MLB_TEAM_ABBR_BY_NAME.get(team.get("name"), "???")

def fetch_todays_games(target_date: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch today's MLB games with probable pitchers.

    Returns [] on any error so the demo data path stays available.
    """

    date_str = target_date or date.today().isoformat()
    url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={date_str}&hydrate=probablePitcher,venue"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PitchCraft-Capstone/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())

        games = []
        for date_entry in data.get("dates", []):
            for game in date_entry.get("games", []):
                away = game["teams"]["away"]
                home = game["teams"]["home"]
                away_pp = away.get("probablePitcher", {})
                home_pp = home.get("probablePitcher", {})
                games.append(
                    {
                        "game_pk": game.get("gamePk"),
                        "away_team": away.get("team", {}).get("name", "Unknown"),
                        "away_team_abbr": _team_abbreviation(away.get("team", {})),
                        "home_team": home.get("team", {}).get("name", "Unknown"),
                        "home_team_abbr": _team_abbreviation(home.get("team", {})),
                        "away_pitcher_name": away_pp.get("fullName"),
                        "away_pitcher_id": away_pp.get("id"),
                        "home_pitcher_name": home_pp.get("fullName"),
                        "home_pitcher_id": home_pp.get("id"),
                        "venue": game.get("venue", {}).get("name", ""),
                        "start_time": game.get("gameDate", ""),
                        "status": game.get("status", {}).get(
                            "abstractGameState", "Preview"
                        ),
                    }
                )
        print(f"[LIVE] Fetched {len(games)} games for {date_str}")
        return games
    except Exception as exc:
        print(f"[LIVE] Schedule fetch failed: {exc} - using demo data")
        return []


def fetch_pitcher_season_stats(pitcher_id: int, season: int = 2026) -> dict[str, Any]:
    """
    Fetch season pitching stats for a pitcher from the MLB Stats API.

    Returns {} on any error so Statcast counts can remain the fallback.
    """

    url = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
        f"?stats=season&group=pitching&season={season}"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PitchCraft-Capstone/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())
        splits = data.get("stats", [{}])[0].get("splits", [])
        if not splits:
            return {}
        stat = splits[0].get("stat", {})
        result = {
            "era": stat.get("era", "N/A"),
            "whip": stat.get("whip", "N/A"),
            "innings": stat.get("inningsPitched", "N/A"),
            "strikeouts": stat.get("strikeOuts"),
            "walks": stat.get("baseOnBalls"),
            "home_runs_allowed": stat.get("homeRuns"),
        }
        print(
            f"[LIVE] Season stats fetched: ERA {result['era']}, "
            f"WHIP {result['whip']}, IP {result['innings']}, "
            f"K {result['strikeouts']}, BB {result['walks']}, "
            f"HR {result['home_runs_allowed']}"
        )
        return result
    except Exception as exc:
        print(f"[LIVE] Season stats fetch failed for id={pitcher_id}: {exc}")
        return {}


def fetch_pitcher_statcast(
    pitcher_id: int,
    pitcher_name: str,
    season_start: str = "2026-03-20",
) -> dict[str, Any] | None:
    """Fetch and process Statcast data for one pitcher, or return None on failure."""

    today = date.today().isoformat()
    try:
        print(f"[LIVE] Fetching Statcast for {pitcher_name} (id={pitcher_id})...")
        df = statcast_pitcher(season_start, today, player_id=pitcher_id)
        if df is None or len(df) == 0:
            print(f"[LIVE] No Statcast data for {pitcher_name}")
            return None
        print(f"[LIVE] {pitcher_name}: {len(df)} pitches fetched")
        processed = process_pitcher_statcast(df, pitcher_name)
        if not processed["pitch_mix"]:
            print(f"[LIVE] No usable pitch mix for {pitcher_name}")
            return None
        statcast_summary = processed["season_summary"]
        mlb_stats = fetch_pitcher_season_stats(pitcher_id)
        if mlb_stats:
            processed["season_summary"] = {
                "era": mlb_stats.get("era", "N/A"),
                "whip": mlb_stats.get("whip", "N/A"),
                "innings": mlb_stats.get("innings", "N/A"),
                "strikeouts": mlb_stats.get("strikeouts")
                or statcast_summary["strikeouts"],
                "walks": mlb_stats.get("walks") or statcast_summary["walks"],
                "home_runs_allowed": mlb_stats.get("home_runs_allowed")
                or statcast_summary["home_runs_allowed"],
            }
        else:
            processed["season_summary"] = {
                "era": "N/A",
                "whip": "N/A",
                "innings": "N/A",
                "strikeouts": statcast_summary["strikeouts"],
                "walks": statcast_summary["walks"],
                "home_runs_allowed": statcast_summary["home_runs_allowed"],
            }
        return processed
    except Exception as exc:
        print(f"[LIVE] Statcast fetch failed for {pitcher_name}: {exc}")
        return None


def normalize_plate_x(x: float) -> float:
    """Normalize plate_x (-1.7 to 1.7) to 0-1, left to right."""

    return round(float(np.clip((x + 1.7) / 3.4, 0.0, 1.0)), 3)


def normalize_plate_z(z: float) -> float:
    """Normalize plate_z (0.5 to 5.0) to 0-1, inverted for SVG coordinates."""

    return round(float(np.clip(1.0 - (z - 0.5) / 4.5, 0.0, 1.0)), 3)


def process_pitcher_statcast(df: Any, pitcher_name: str) -> dict[str, Any]:
    """Convert raw Statcast rows into the PitchCraft v0.2.0 chart shape."""

    import pandas as pd

    df = df.dropna(subset=["pitch_type"])
    df = df[df["pitch_type"] != ""].copy()
    df["pitch_name"] = df["pitch_type"].map(PITCH_NAME_MAP).fillna(df["pitch_type"])

    total = len(df)
    lhh = df[df["stand"] == "L"]
    rhh = df[df["stand"] == "R"]

    pitch_mix = []
    velocity_rows = []

    for pitch_name, sub in df.groupby("pitch_name"):
        sub_l = lhh[lhh["pitch_name"] == pitch_name]
        sub_r = rhh[rhh["pitch_name"] == pitch_name]

        pitch_mix.append(
            {
                "pitch": pitch_name,
                "away_starter": {
                    "overall": _usage_pct(len(sub), total),
                    "vs_lhh": _usage_pct(len(sub_l), len(lhh)),
                    "vs_rhh": _usage_pct(len(sub_r), len(rhh)),
                },
                "home_starter": {"overall": 0, "vs_lhh": 0, "vs_rhh": 0},
            }
        )

        avg_velo = sub["release_speed"].mean()
        if not pd.isna(avg_velo):
            velocity_rows.append(
                {
                    "pitch": pitch_name,
                    "away_starter_velocity": round(float(avg_velo), 1),
                    "home_starter_velocity": None,
                }
            )

    pitch_mix.sort(key=lambda row: row["away_starter"]["overall"], reverse=True)
    pitch_mix = pitch_mix[:5]
    top_pitch_names = {row["pitch"] for row in pitch_mix}
    velocity_rows = [row for row in velocity_rows if row["pitch"] in top_pitch_names]

    pitch_locations = {"vs_lhh": [], "vs_rhh": []}
    for entry in pitch_mix:
        pitch_name = entry["pitch"]
        sub_all = df[df["pitch_name"] == pitch_name].dropna(
            subset=["plate_x", "plate_z"]
        )
        for split, stand in (("vs_lhh", "L"), ("vs_rhh", "R")):
            sub = sub_all[sub_all["stand"] == stand]
            if len(sub) >= 5:
                pitch_locations[split].append(
                    {
                        "pitch": pitch_name,
                        "x": normalize_plate_x(sub["plate_x"].median()),
                        "y": normalize_plate_z(sub["plate_z"].median()),
                    }
                )

    strikeouts = int(df[df["events"] == "strikeout"]["events"].count())
    walks = int(df[df["events"] == "walk"]["events"].count())
    home_runs = int(df[df["events"] == "home_run"]["events"].count())

    top = pitch_mix[0]["pitch"] if pitch_mix else "Fastball"
    second = pitch_mix[1]["pitch"] if len(pitch_mix) > 1 else "Slider"

    return {
        "name": pitcher_name,
        "pitch_mix": pitch_mix,
        "velocity_by_pitch": velocity_rows,
        "pitch_locations": pitch_locations,
        "season_summary": {
            "era": "live",
            "whip": "live",
            "innings": "live",
            "strikeouts": strikeouts,
            "walks": walks,
            "home_runs_allowed": home_runs,
        },
        "pitching_profile": {
            "style_label": f"{top}-{second} starter",
            "primary_pitch": top,
            "putaway_pitch": second,
            "command_label": "See live data",
            "swing_miss_label": "See live data",
            "contact_risk_label": "See live data",
        },
    }


def pick_featured_game(games: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first game with both probable pitchers available."""

    for game in games:
        if game["away_pitcher_id"] and game["home_pitcher_id"]:
            return game
    return None


def build_live_snapshot(target_date: str | None = None) -> dict[str, Any] | None:
    """Fetch schedule and Statcast data, returning a generator-ready snapshot."""

    games = fetch_todays_games(target_date)
    if not games:
        return None

    featured = pick_featured_game(games)
    if not featured:
        print("[LIVE] No game with both probable pitchers found")
        return None

    print(f"[LIVE] Featured: {featured['away_team']} @ {featured['home_team']}")
    print(
        "[LIVE] Starters: "
        f"{featured['away_pitcher_name']} vs {featured['home_pitcher_name']}"
    )

    away_data = fetch_pitcher_statcast(
        featured["away_pitcher_id"],
        featured["away_pitcher_name"],
    )
    home_data = fetch_pitcher_statcast(
        featured["home_pitcher_id"],
        featured["home_pitcher_name"],
    )

    if not away_data or not home_data:
        print("[LIVE] Statcast fetch incomplete - falling back to demo")
        return None

    snapshot = {
        "data_mode": "fetched_snapshot",
        "fetched_date": target_date or date.today().isoformat(),
        "games_today": [
            {
                "away": game["away_team_abbr"],
                "home": game["home_team_abbr"],
                "away_pitcher": game["away_pitcher_name"],
                "home_pitcher": game["home_pitcher_name"],
                "status": game["status"],
            }
            for game in games
        ],
        "featured_game": featured,
        "away_starter": away_data,
        "home_starter": home_data,
        "combined_charts": {
            "pitch_mix": _combine_pitch_mix(away_data, home_data),
            "velocity_by_pitch": _combine_velocity(away_data, home_data),
        },
    }
    return snapshot


def _usage_pct(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total > 0 else 0


def _combine_pitch_mix(
    away_data: dict[str, Any],
    home_data: dict[str, Any],
) -> list[dict[str, Any]]:
    away_pitches = {row["pitch"]: row for row in away_data["pitch_mix"]}
    home_pitches = {row["pitch"]: row for row in home_data["pitch_mix"]}
    pitch_names = list(
        dict.fromkeys(
            [row["pitch"] for row in away_data["pitch_mix"]]
            + [row["pitch"] for row in home_data["pitch_mix"]]
        )
    )

    return [
        {
            "pitch": pitch_name,
            "away_starter": away_pitches.get(pitch_name, {}).get(
                "away_starter",
                {"overall": 0, "vs_lhh": 0, "vs_rhh": 0},
            ),
            "home_starter": home_pitches.get(pitch_name, {}).get(
                "away_starter",
                {"overall": 0, "vs_lhh": 0, "vs_rhh": 0},
            ),
        }
        for pitch_name in pitch_names
    ]


def _combine_velocity(
    away_data: dict[str, Any],
    home_data: dict[str, Any],
) -> list[dict[str, float | str | None]]:
    away_velos = {
        row["pitch"]: row["away_starter_velocity"]
        for row in away_data["velocity_by_pitch"]
    }
    home_velos = {
        row["pitch"]: row["away_starter_velocity"]
        for row in home_data["velocity_by_pitch"]
    }
    pitch_names = list(dict.fromkeys(list(away_velos) + list(home_velos)))
    return [
        {
            "pitch": pitch_name,
            "away_starter_velocity": away_velos.get(pitch_name),
            "home_starter_velocity": home_velos.get(pitch_name),
        }
        for pitch_name in pitch_names
    ]


def main() -> int:
    from data_pipeline.fetchers.cache_manager import save_processed

    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    print("[LIVE] PitchCraft live data pipeline starting...")

    snapshot = build_live_snapshot(target_date)
    if not snapshot:
        print("[LIVE] Pipeline failed or no data available. Demo data unchanged.")
        return 1

    save_processed("live_matchup", snapshot)
    away_top = snapshot["away_starter"]["pitch_mix"][0]
    home_top = snapshot["home_starter"]["pitch_mix"][0]
    print(
        "[LIVE] Snapshot saved. Featured: "
        f"{snapshot['featured_game']['away_team']} @ "
        f"{snapshot['featured_game']['home_team']}"
    )
    print(
        f"[LIVE] Away: {snapshot['away_starter']['name']} - "
        f"top pitch: {away_top['pitch']} {away_top['away_starter']['overall']}%"
    )
    print(
        f"[LIVE] Home: {snapshot['home_starter']['name']} - "
        f"top pitch: {home_top['pitch']} {home_top['away_starter']['overall']}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
