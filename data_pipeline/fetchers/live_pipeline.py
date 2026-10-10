"""Fetch and cache a live MLB matchup snapshot for PitchCraft."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


PYBASEBALL_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "pybaseball"
TEAM_BATTING_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "team_batting"
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

# Statcast's own team codes where they differ from MLB_TEAM_ABBR_BY_ID.
STATCAST_TEAM_CODE_BY_MLB_ABBR = {"ARI": "AZ"}

# Savant caps a search CSV at 25,000 rows; a full chunk may be truncated.
SAVANT_ROW_CAP = 25000
# Request budget for the team-batting fetch: 30 teams x 7 monthly chunks, once.
SAVANT_MAX_REQUESTS_PER_RUN = 210
SAVANT_PAUSE_SECONDS = 2.0
SAVANT_BATTING_URL = (
    "https://baseballsavant.mlb.com/statcast_search/csv?all=true&type=details"
    "&player_type=batter&hfGT=R%7C&min_pitches=0&min_results=0&group_by=name"
    "&sort_col=pitches&sort_order=desc"
    "&team={team}&game_date_gt={start}&game_date_lt={end}"
)
TEAM_BATTING_COLUMNS = (
    "game_date",
    "game_type",
    "game_pk",
    "home_team",
    "away_team",
    "inning_topbot",
    "p_throws",
    "stand",
    "batter",
    "at_bat_number",
    "events",
)

HIT_BASES = {"single": 1, "double": 2, "triple": 3, "home_run": 4}
WALK_EVENTS = {"walk", "intent_walk"}
STRIKEOUT_EVENTS = {"strikeout", "strikeout_double_play"}
SAC_FLY_EVENTS = {"sac_fly", "sac_fly_double_play"}
SAC_BUNT_EVENTS = {"sac_bunt", "sac_bunt_double_play"}
# Not plate appearances in MLB's official stats.
NON_PA_EVENTS = {"truncated_pa"}

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

POSTSEASON_GAME_TYPES = ("F", "D", "L", "W")


def _parse_as_of(as_of: str | date | None) -> date:
    """
    Resolve the data cutoff. `as_of` is inclusive: data dated on or before it.
    None means today. Raises ValueError on anything that is not an ISO date.
    """

    if as_of is None:
        return date.today()
    if isinstance(as_of, datetime):
        return as_of.date()
    if isinstance(as_of, date):
        return as_of
    if isinstance(as_of, str):
        return date.fromisoformat(as_of)
    raise ValueError(f"as_of must be an ISO date string or a date, got {as_of!r}")


def _get_text(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "PitchCraft-Capstone/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


class SavantRequestCapExceeded(RuntimeError):
    """A run tried to make more Savant requests than SAVANT_MAX_REQUESTS_PER_RUN."""


_savant_run = {"requests": 0}


def _savant_get(url: str) -> str:
    """
    One paced, counted Savant request. Sleeps SAVANT_PAUSE_SECONDS before every
    request except the first of the run and raises before exceeding the cap.
    Cache hits never reach this function.
    """

    if _savant_run["requests"] >= SAVANT_MAX_REQUESTS_PER_RUN:
        raise SavantRequestCapExceeded(
            f"more than {SAVANT_MAX_REQUESTS_PER_RUN} Savant requests in one run"
        )
    if _savant_run["requests"] > 0:
        time.sleep(SAVANT_PAUSE_SECONDS)
    _savant_run["requests"] += 1
    return _get_text(url)


def _get_json(url: str, timeout: int = 8) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "PitchCraft-Capstone/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


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
                        "away_team_id": away.get("team", {}).get("id"),
                        "away_team_abbr": _team_abbreviation(away.get("team", {})),
                        "home_team": home.get("team", {}).get("name", "Unknown"),
                        "home_team_id": home.get("team", {}).get("id"),
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


def fetch_pitcher_season_stats(
    pitcher_id: int,
    season: int = 2026,
    as_of: str | date | None = None,
) -> dict[str, Any]:
    """
    Fetch season pitching stats for a pitcher from the MLB Stats API.

    With `as_of`, the stats cover Jan 1 of the season through that date
    (inclusive); `as_of` must fall in `season`. Raises ValueError otherwise.
    Returns {} on any error so Statcast counts can remain the fallback.
    """

    if as_of is None:
        stats_query = "stats=season"
    else:
        cutoff = _parse_as_of(as_of)
        if cutoff.year != season:
            raise ValueError(f"as_of {cutoff.isoformat()} is not in season {season}")
        stats_query = (
            f"stats=byDateRange&startDate={season}-01-01&endDate={cutoff.isoformat()}"
        )
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
        f"?{stats_query}&group=pitching&season={season}"
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


def fetch_team_splits(
    team_id: int,
    season: int = 2026,
    as_of: str | date | None = None,
    season_start: str = "2026-03-20",
) -> dict[str, Any]:
    """
    Fetch team hitting splits vs LHP and vs RHP for the season.

    Returns {"vl": {...}, "vr": {...}} each with ops, avg, strikeouts, walks,
    plate_appearances, k_rate, and bb_rate. Returns {} on failure.

    With `as_of` the splits are derived from Statcast plate appearances from
    `season_start` through that date, because the MLB API ignores startDate and
    endDate on statSplits. `as_of` must fall in `season` (ValueError otherwise).
    """

    if as_of is not None:
        cutoff = _parse_as_of(as_of)
        if cutoff.year != season:
            raise ValueError(f"as_of {cutoff.isoformat()} is not in season {season}")
        mlb_abbr = MLB_TEAM_ABBR_BY_ID.get(team_id)
        code = STATCAST_TEAM_CODE_BY_MLB_ABBR.get(mlb_abbr, mlb_abbr)
        if not code:
            print(f"[LIVE] Team splits: unknown team id {team_id}")
            return {}
        try:
            df = fetch_team_batting_statcast(code, date.fromisoformat(season_start), cutoff)
            return derive_team_splits(df, code, cutoff)
        except SavantRequestCapExceeded:
            raise
        except Exception as exc:
            print(f"[LIVE] Team splits from Statcast failed for team {team_id}: {exc}")
            return {}
    url = (
        f"https://statsapi.mlb.com/api/v1/teams/{team_id}/stats"
        f"?stats=statSplits&sitCodes=vl,vr&group=hitting&season={season}"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PitchCraft-Capstone/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())
        out = {}
        for stats_entry in data.get("stats", []):
            for split in stats_entry.get("splits", []):
                code = split.get("split", {}).get("code")
                if code in ("vl", "vr"):
                    stat = split.get("stat", {})
                    plate_appearances = stat.get("plateAppearances")
                    strikeouts = stat.get("strikeOuts", 0)
                    walks = stat.get("baseOnBalls", 0)
                    out[code] = {
                        "ops": stat.get("ops"),
                        "avg": stat.get("avg"),
                        "strikeouts": strikeouts,
                        "walks": walks,
                        "plate_appearances": plate_appearances,
                        "k_rate": round(strikeouts / plate_appearances * 100, 1)
                        if plate_appearances
                        else None,
                        "bb_rate": round(walks / plate_appearances * 100, 1)
                        if plate_appearances
                        else None,
                    }
        return out
    except Exception as exc:
        print(f"[LIVE] Team splits fetch failed for team {team_id}: {exc}")
        return {}


def _month_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into non-overlapping calendar-month ranges."""

    chunks = []
    cursor = start
    while cursor <= end:
        month_end = (cursor.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(
            days=1
        )
        chunk_end = min(month_end, end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def fetch_team_batting_statcast(statcast_team: str, start: date, end: date) -> Any:
    """
    Statcast pitch rows from the batting side of one team, `start` to `end`
    inclusive, regular season only.

    pybaseball.statcast(team=...) filters by pitching team, so this asks Savant
    directly with player_type=batter, one request per calendar month (about 7
    per season, never league-wide), paced and capped per run (see _savant_get).
    Finished months are cached on disk, trimmed to the columns the splits need;
    a month that includes today is not cached. Raises RuntimeError if a month
    hits Savant's row cap (possible truncation) and SavantRequestCapExceeded
    when the run's request budget is spent.
    """

    import pandas as pd

    frames = []
    for chunk_start, chunk_end in _month_chunks(start, end):
        cache_file = (
            TEAM_BATTING_CACHE_DIR / f"{statcast_team}_{chunk_start}_{chunk_end}.csv"
        )
        if cache_file.exists():
            frames.append(pd.read_csv(cache_file))
            continue
        text = _savant_get(
            SAVANT_BATTING_URL.format(
                team=statcast_team, start=chunk_start.isoformat(), end=chunk_end.isoformat()
            )
        )
        if not text.strip():
            continue
        chunk = pd.read_csv(io.StringIO(text))
        if len(chunk) >= SAVANT_ROW_CAP:
            raise RuntimeError(
                f"Savant returned {len(chunk)} rows for {statcast_team} "
                f"{chunk_start}..{chunk_end}: result may be truncated"
            )
        chunk = chunk[[c for c in TEAM_BATTING_COLUMNS if c in chunk.columns]]
        if chunk_end < date.today():
            TEAM_BATTING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            chunk.to_csv(cache_file, index=False)
        frames.append(chunk)
    if not frames:
        return pd.DataFrame(columns=list(TEAM_BATTING_COLUMNS))
    return pd.concat(frames, ignore_index=True)


def _rate3(value: float | None) -> str | None:
    """Format like the MLB API: .750, 1.012."""

    return None if value is None else f"{value:.3f}".lstrip("0")


def _split_line(events: Any) -> dict[str, Any]:
    plate_appearances = len(events)
    hits = int(events.isin(HIT_BASES).sum())
    total_bases = sum(HIT_BASES.get(event, 0) for event in events)
    walks = int(events.isin(WALK_EVENTS).sum())
    strikeouts = int(events.isin(STRIKEOUT_EVENTS).sum())
    hit_by_pitch = int((events == "hit_by_pitch").sum())
    sac_flies = int(events.isin(SAC_FLY_EVENTS).sum())
    sac_bunts = int(events.isin(SAC_BUNT_EVENTS).sum())
    interference = int((events == "catcher_interf").sum())
    at_bats = (
        plate_appearances - walks - hit_by_pitch - sac_flies - sac_bunts - interference
    )
    on_base_chances = at_bats + walks + hit_by_pitch + sac_flies
    obp = (hits + walks + hit_by_pitch) / on_base_chances if on_base_chances else None
    slg = total_bases / at_bats if at_bats else None
    return {
        "ops": _rate3(obp + slg) if obp is not None and slg is not None else None,
        "avg": _rate3(hits / at_bats) if at_bats else None,
        "strikeouts": strikeouts,
        "walks": walks,
        "plate_appearances": plate_appearances,
        "k_rate": round(strikeouts / plate_appearances * 100, 1),
        "bb_rate": round(walks / plate_appearances * 100, 1),
    }


def derive_team_splits(df: Any, statcast_team: str, as_of: str | date | None) -> dict[str, Any]:
    """
    Team hitting splits vs LHP ("vl") and RHP ("vr") from Statcast rows, same
    shape as fetch_team_splits' API path. Counts completed regular-season plate
    appearances by `statcast_team` dated on or before `as_of`. A hand with no
    plate appearances is omitted; no rows at all gives {}.
    """

    import pandas as pd

    cutoff = _parse_as_of(as_of)
    if len(df) == 0:
        return {}
    batting = ((df["inning_topbot"] == "Top") & (df["away_team"] == statcast_team)) | (
        (df["inning_topbot"] == "Bot") & (df["home_team"] == statcast_team)
    )
    keep = (
        batting
        & df["events"].notna()
        & ~df["events"].isin(NON_PA_EVENTS)
        & (pd.to_datetime(df["game_date"]).dt.date <= cutoff)
    )
    if "game_type" in df.columns:
        keep &= df["game_type"] == "R"
    plate_appearances = df[keep]
    splits = {}
    for code, hand in (("vl", "L"), ("vr", "R")):
        sub = plate_appearances[plate_appearances["p_throws"] == hand]
        if len(sub):
            splits[code] = _split_line(sub["events"])
    return splits


def fetch_series_status(
    game_pk: int,
    as_of: str | date | None = None,
) -> dict[str, Any]:
    """
    Postseason series standing before first pitch of `game_pk`, using only
    games dated on or before `as_of` (default today).

    The schedule's seriesStatus is the standing after each game, so the
    standing before this game is the one after the last earlier game of the
    same series. Game 1 (or a cutoff before any game) gives 0-0. `wins` and
    `losses` follow the MLB convention (leader first). Returns {} for games
    outside a postseason series or on any error.
    """

    cutoff = _parse_as_of(as_of)
    schedule = "https://statsapi.mlb.com/api/v1/schedule?sportId=1"
    try:
        data = _get_json(f"{schedule}&gamePk={game_pk}&hydrate=seriesStatus")
        games = [g for d in data.get("dates", []) for g in d.get("games", [])]
        game = next((g for g in games if g.get("gamePk") == game_pk), None)
        if not game or game.get("gameType") not in POSTSEASON_GAME_TYPES:
            return {}
        number = game.get("seriesGameNumber")
        if not number:
            return {}
        game_date = date.fromisoformat(game["officialDate"])
        game_type = game["gameType"]
        home_id = game["teams"]["home"]["team"]["id"]
        team_ids = {home_id, game["teams"]["away"]["team"]["id"]}

        window_start = (game_date - timedelta(days=10)).isoformat()
        window_end = min(cutoff, game_date).isoformat()
        data = _get_json(
            f"{schedule}&teamId={home_id}&startDate={window_start}"
            f"&endDate={window_end}&gameType={game_type}&hydrate=seriesStatus"
        )
        earlier = []
        for entry in (g for d in data.get("dates", []) for g in d.get("games", [])):
            entry_teams = {
                entry["teams"]["home"]["team"]["id"],
                entry["teams"]["away"]["team"]["id"],
            }
            if (
                entry.get("gameType") == game_type
                and entry_teams == team_ids
                and (entry.get("seriesGameNumber") or 0) < number
                and date.fromisoformat(entry["officialDate"]) <= cutoff
                and entry.get("status", {}).get("abstractGameState") == "Final"
            ):
                earlier.append(entry)

        base = {"game_number": number, "as_of": cutoff.isoformat()}
        if not earlier:
            return {
                **base,
                "games_played": 0,
                "result": None,
                "wins": 0,
                "losses": 0,
                "is_over": False,
                "source_game_pk": None,
            }
        last = max(earlier, key=lambda entry: entry["seriesGameNumber"])
        status = last.get("seriesStatus")
        if not status:
            return {}
        return {
            **base,
            "games_played": last["seriesGameNumber"],
            "result": status.get("result"),
            "wins": status.get("wins"),
            "losses": status.get("losses"),
            "is_over": bool(status.get("isOver")),
            "source_game_pk": last["gamePk"],
        }
    except Exception as exc:
        print(f"[LIVE] Series status fetch failed for game {game_pk}: {exc}")
        return {}


def fetch_pitcher_statcast(
    pitcher_id: int,
    pitcher_name: str,
    season_start: str = "2026-03-20",
    as_of: str | date | None = None,
) -> dict[str, Any] | None:
    """
    Fetch and process Statcast data for one pitcher, or return None on failure.

    Only pitches dated on or before `as_of` (default today) are used, for the
    pitch data and for the season stats, and only from regular-season and
    postseason games (never spring training). A bad `as_of` raises ValueError.
    """

    cutoff = _parse_as_of(as_of)
    try:
        print(f"[LIVE] Fetching Statcast for {pitcher_name} (id={pitcher_id})...")
        df = statcast_pitcher(season_start, cutoff.isoformat(), player_id=pitcher_id)
        if df is not None and "game_date" in df.columns:
            import pandas as pd

            df = df[pd.to_datetime(df["game_date"]).dt.date <= cutoff]
        if df is not None and "game_type" in df.columns:
            # pybaseball asks for regular season, postseason and spring training.
            # Spring never counts; postseason counts only up to the cutoff above.
            df = df[df["game_type"].isin(("R",) + POSTSEASON_GAME_TYPES)]
        if df is None or len(df) == 0:
            print(f"[LIVE] No Statcast data for {pitcher_name}")
            return None
        print(f"[LIVE] {pitcher_name}: {len(df)} pitches fetched")
        processed = process_pitcher_statcast(df, pitcher_name)
        if not processed["pitch_mix"]:
            print(f"[LIVE] No usable pitch mix for {pitcher_name}")
            return None
        statcast_summary = processed["season_summary"]
        mlb_stats = fetch_pitcher_season_stats(pitcher_id, as_of=as_of)
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
        update_pitching_profile_labels(processed)
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
    kept_names = [row["pitch"] for row in pitch_mix]
    movement = compute_movement(df, kept_names)
    throws = (
        df["p_throws"].dropna().iloc[0]
        if "p_throws" in df.columns and len(df["p_throws"].dropna()) > 0
        else "R"
    )

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
        "throws": throws,
        "pitch_mix": pitch_mix,
        "velocity_by_pitch": velocity_rows,
        "movement": movement,
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
            "command_label": derive_command_label(walks),
            "swing_miss_label": derive_swing_miss_label(strikeouts, total),
            "contact_risk_label": derive_contact_risk_label(home_runs),
        },
    }


def compute_movement(df: Any, pitch_types_kept: list[str]) -> dict[str, Any]:
    """
    For each pitch type, compute median horizontal and vertical movement in inches.

    Pitch families are mapped for frontend color and copy. Empty or sparse movement
    data falls back to zeroes so the JSON shape remains stable.
    """

    family_map = {
        "Four-seam": "Fastball",
        "Sinker": "Fastball",
        "Cutter": "Fastball",
        "Slider": "Breaking",
        "Curveball": "Breaking",
        "Sweeper": "Breaking",
        "Slurve": "Breaking",
        "Changeup": "Offspeed",
        "Splitter": "Offspeed",
        "Forkball": "Offspeed",
        "Knuckleball": "Offspeed",
        "Screwball": "Offspeed",
        "Eephus": "Offspeed",
    }
    result = {}
    for name in pitch_types_kept:
        codes = [code for code, display_name in PITCH_NAME_MAP.items() if display_name == name]
        if "pfx_x" in df.columns and "pfx_z" in df.columns:
            sub = df[df["pitch_type"].isin(codes)].dropna(subset=["pfx_x", "pfx_z"])
        else:
            sub = []
        if len(sub) >= 3:
            h_break = round(float(sub["pfx_x"].median()) * 12, 1)
            v_break = round(float(sub["pfx_z"].median()) * 12, 1)
        else:
            h_break, v_break = 0.0, 0.0
        result[name] = {
            "h_break": h_break,
            "v_break": v_break,
            "family": family_map.get(name, "Fastball"),
        }
    return result


def pick_featured_games(games: list[dict[str, Any]], max_games: int = 3) -> list[dict[str, Any]]:
    """Return up to max_games where both probable pitchers are known."""

    eligible = [game for game in games if game["away_pitcher_id"] and game["home_pitcher_id"]]
    return eligible[:max_games]


def build_live_snapshot(target_date: str | None = None) -> dict[str, Any] | None:
    """Fetch schedule and Statcast data, returning a generator-ready snapshot."""

    games = fetch_todays_games(target_date)
    if not games:
        return None

    candidates = pick_featured_games(games, 5)
    if not candidates:
        print("[LIVE] No game with both probable pitchers found")
        return None

    live_games = []
    skipped_games = []
    for featured in candidates:
        if len(live_games) >= 3:
            break

        print(f"[LIVE] Candidate: {featured['away_team']} @ {featured['home_team']}")
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
            skipped = (
                f"{featured['away_team_abbr']} @ {featured['home_team_abbr']} "
                f"({featured['away_pitcher_name']} vs {featured['home_pitcher_name']})"
            )
            skipped_games.append(skipped)
            print(f"[LIVE] Skipping {skipped} - insufficient pitch data")
            continue

        away_splits = fetch_team_splits(featured["away_team_id"])
        home_splits = fetch_team_splits(featured["home_team_id"])
        live_games.append(
            {
                "featured_game": featured,
                "away_starter": away_data,
                "home_starter": home_data,
                "combined_charts": {
                    "pitch_mix": _combine_pitch_mix(away_data, home_data),
                    "velocity_by_pitch": _combine_velocity(away_data, home_data),
                },
                "away_team_splits": away_splits,
                "home_team_splits": home_splits,
            }
        )

    if not live_games:
        print("[LIVE] No live games had sufficient Statcast data - falling back to demo")
        return None

    primary = live_games[0]
    snapshot = {
        "data_mode": "fetched_snapshot",
        "fetched_date": target_date or date.today().isoformat(),
        "live_games": live_games,
        "skipped_games": skipped_games,
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
        "featured_game": primary["featured_game"],
        "away_starter": primary["away_starter"],
        "home_starter": primary["home_starter"],
        "combined_charts": primary["combined_charts"],
        "away_team_splits": primary["away_team_splits"],
        "home_team_splits": primary["home_team_splits"],
    }
    return snapshot

def _usage_pct(part: int, total: int) -> float:
    return round(part / total * 100, 1) if total > 0 else 0


def derive_swing_miss_label(strikeouts: int, total_pitches: int) -> str:
    if total_pitches == 0:
        return "Limited swing-and-miss data available"
    if strikeouts >= 80:
        return "Above-average swing-and-miss ability"
    if strikeouts >= 40:
        return "Moderate swing-and-miss ability"
    return "Limited swing-and-miss data available"


def derive_command_label(walks: int, innings_str: str | None = None) -> str:
    if walks <= 25:
        return "Solid command this season"
    if walks <= 40:
        return "Average command this season"
    return "Below-average command this season"


def derive_contact_risk_label(home_runs: int) -> str:
    if home_runs <= 8:
        return "Limited hard contact allowed"
    if home_runs <= 15:
        return "Moderate contact risk"
    return "Elevated contact risk"


def update_pitching_profile_labels(processed: dict[str, Any]) -> None:
    season = processed.get("season_summary", {})
    profile = processed.get("pitching_profile", {})
    strikeouts = _safe_int(season.get("strikeouts"))
    walks = _safe_int(season.get("walks"))
    home_runs = _safe_int(season.get("home_runs_allowed"))
    total_pitches = sum(
        _safe_int(row.get("away_starter", {}).get("overall"))
        for row in processed.get("pitch_mix", [])
    )
    profile["command_label"] = derive_command_label(walks, season.get("innings"))
    profile["swing_miss_label"] = derive_swing_miss_label(strikeouts, total_pitches)
    profile["contact_risk_label"] = derive_contact_risk_label(home_runs)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


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
    print(f"[LIVE] Live games processed: {len(snapshot['live_games'])}")
    if snapshot.get("skipped_games"):
        print(f"[LIVE] Skipped games: {', '.join(snapshot['skipped_games'])}")
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
