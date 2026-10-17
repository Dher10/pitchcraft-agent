"""Fetch and cache a live MLB matchup snapshot for PitchCraft."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


PYBASEBALL_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "pybaseball"
TEAM_BATTING_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "team_batting"
PITCHER_HAND_CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache" / "raw" / "pitcher_hand"
os.environ.setdefault("PYBASEBALL_CACHE", str(PYBASEBALL_CACHE_DIR))

import numpy as np
import pybaseball
from pybaseball import statcast_pitcher

from data_pipeline import labels  # noqa: E402
from data_pipeline.fetchers import mlb_schemas  # noqa: E402
from data_pipeline.fetchers.statcast_events import COMPLETED_EVENTS, STATCAST_EVENTS  # noqa: E402
from data_pipeline.schema import SCHEMA_VERSION  # noqa: E402

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
# D29: the month that holds `as_of` is not closed, so it is refreshed on every run.
# Its requests have their own budget, apart from the 210 above: 5 candidate games x 2 teams.
SAVANT_MAX_OPEN_MONTH_REQUESTS_PER_RUN = 10
SAVANT_PAUSE_SECONDS = 2.0
# Throwing-hand lookups (MLB people endpoint) when a Statcast frame cannot say the hand. A hand
# does not change, so an answer is cached for good; only a cache miss counts. 10 is the most a
# run can need: 5 candidate games x 2 starters.
PITCHER_HAND_MAX_REQUESTS_PER_RUN = 10
PITCHER_HANDS = ("L", "R", "S")
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


def _team_abbreviation(team: dict[str, Any]) -> str | None:
    """The abbreviation the schedule gives, else the id and name maps; None for a team they do not know (F7), never a placeholder."""

    raw_abbr = team.get("abbreviation")
    if raw_abbr:
        return raw_abbr
    team_id = team.get("id")
    if team_id in MLB_TEAM_ABBR_BY_ID:
        return MLB_TEAM_ABBR_BY_ID[team_id]
    return MLB_TEAM_ABBR_BY_NAME.get(team.get("name"))


def game_label(game: dict[str, Any]) -> str:
    """"AWAY @ HOME" for a log or a skipped game, each team by its abbreviation or, if it has none, its name."""

    away = labels.team_label(game["away_team_abbr"], game["away_team"])
    home = labels.team_label(game["home_team_abbr"], game["home_team"])
    return f"{away} @ {home}"

POSTSEASON_GAME_TYPES = ("F", "D", "L", "W")

# MLB's official game date is the New York date, whatever the runner's clock says (D29).
MLB_TIMEZONE = ZoneInfo("America/New_York")


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


def today_eastern() -> date:
    """Today's date in New York: the date MLB uses for a game, never the runner's UTC date."""

    return datetime.now(MLB_TIMEZONE).date()


def resolve_as_of(game_date: str | date, as_of: str | date | None = None) -> date:
    """
    The data cutoff for a game (D29): the day before its official date.

    An explicit `as_of` is accepted only if it is before the game date, so a
    caller can narrow the cutoff but never reach the game day or later. A missing
    game date raises: the cutoff is never guessed from the runner's clock.
    """

    if game_date is None:
        raise ValueError("a game date is required to resolve as_of")
    game = _parse_as_of(game_date)
    if as_of is None:
        return game - timedelta(days=1)
    cutoff = _parse_as_of(as_of)
    if cutoff >= game:
        raise ValueError(
            f"as_of {cutoff.isoformat()} must be before the game date {game.isoformat()}"
        )
    return cutoff


def _get_text(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "PitchCraft-Capstone/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8-sig")


class SavantRequestCapExceeded(RuntimeError):
    """A run tried to make more Savant requests than SAVANT_MAX_REQUESTS_PER_RUN."""


class SavantOpenMonthBudgetExceeded(RuntimeError):
    """A run spent its SAVANT_MAX_OPEN_MONTH_REQUESTS_PER_RUN (D29)."""


# One class per code of a source that answered but did not give what was asked (rule 8: the file says only the
# code; the message stays in the local run record). `error_code` is the only place that maps an exception to it.
class MalformedResponse(ValueError):
    """The answer is not the document the source sends (an error page, a truncated or empty body)."""


class TruncatedResponse(RuntimeError):
    """A month of Savant rows reached the row cap, so it may be cut short."""


class MissingColumn(ValueError):
    """A column the pipeline needs is not in the frame."""


class MalformedRows(ValueError):
    """Rows of the frame cannot be read (an unparseable date, an unknown game type, a missing team)."""


class UnusableColumn(ValueError):
    """A column is present but no row of it can be used."""


class UnknownValue(ValueError):
    """A value outside the set the pipeline knows (a throwing hand that is not L, R or S)."""


_savant_run = {"requests": 0, "open_requests": 0}
_pitcher_hand_run = {"requests": 0}

# Failures of the current run, written to data_cache/processed/live_run.json by main().
_run_errors: list[dict[str, Any]] = []
# What the run saw and could carry on from: an unmapped pitch, a team the maps do not know. They are in the run
# record and never change its status; publishing them is a matter of rule 8 (D2.3).
_run_warnings: list[dict[str, Any]] = []


def error_code(exc: BaseException) -> str:
    """
    The code (`contract_checks.RUN_ERROR_CODES`) of an exception a fetcher caught: the only place that maps one.

    A class this module or `mlb_schemas` raises says what it is; a network or transport failure (`OSError` covers
    `URLError`, `HTTPError`, timeouts and `requests`) is `request_failed`; anything else is `unexpected_error`.
    """

    import pandas as pd

    if isinstance(exc, (SavantRequestCapExceeded, SavantOpenMonthBudgetExceeded)):
        return "budget_spent"
    if isinstance(exc, MissingColumn):
        return "missing_column"
    if isinstance(exc, MalformedRows):
        return "malformed_rows"
    if isinstance(exc, UnusableColumn):
        return "unusable_column"
    if isinstance(exc, UnknownValue):
        return "unknown_value"
    if isinstance(
        exc,
        (MalformedResponse, TruncatedResponse, mlb_schemas.SourceShapeError, json.JSONDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError),
    ):
        return "malformed_response"
    if isinstance(exc, OSError):
        return "request_failed"
    return "unexpected_error"


def _record_error(source: str, code: str, message: str, **context: Any) -> None:
    """
    Keep a failure for the run record; every fetcher still returns empty, never raises.

    `source` and `code` belong to the closed sets of `contract_checks` (RUN_SOURCES, RUN_ERROR_CODES): they are all
    that a published error may say (rule 8). The message and the ids stay in the local record.
    """

    _run_errors.append({"source": source, "code": code, "message": str(message)[:300], **context})


def _record_failure(source: str, exc: BaseException, **context: Any) -> None:
    """`_record_error` for a caught exception: its code comes from `error_code`, its text stays local."""

    _record_error(source, error_code(exc), f"{type(exc).__name__}: {exc}", **context)


def _record_warning(source: str, code: str, message: str, **context: Any) -> None:
    """
    Keep a warning for the run record: the run goes on, with the figure unavailable (rules 1 and 2).

    `source` and `code` belong to the closed sets of `contract_checks` (RUN_SOURCES, RUN_WARNING_CODES): they are
    what a published warning may say (rule 8); the message stays in the local record.
    """

    _run_warnings.append({"source": source, "code": code, "message": str(message)[:300], **context})


def _savant_get(url: str, open_month: bool = False) -> str:
    """
    One paced, counted Savant request. Sleeps SAVANT_PAUSE_SECONDS before every
    request except the first of the run and raises before exceeding the cap.
    Requests for the open month (D29) are counted apart, against their own budget.
    Cache hits never reach this function.
    """

    closed_made = _savant_run.get("requests", 0)
    open_made = _savant_run.get("open_requests", 0)
    if open_month:
        if open_made >= SAVANT_MAX_OPEN_MONTH_REQUESTS_PER_RUN:
            raise SavantOpenMonthBudgetExceeded(
                f"more than {SAVANT_MAX_OPEN_MONTH_REQUESTS_PER_RUN} open-month "
                "Savant requests in one run"
            )
    elif closed_made >= SAVANT_MAX_REQUESTS_PER_RUN:
        raise SavantRequestCapExceeded(
            f"more than {SAVANT_MAX_REQUESTS_PER_RUN} Savant requests in one run"
        )
    if closed_made + open_made > 0:
        time.sleep(SAVANT_PAUSE_SECONDS)
    counter = "open_requests" if open_month else "requests"
    _savant_run[counter] = _savant_run.get(counter, 0) + 1
    return _get_text(url)


def _get_json(url: str, timeout: int = 8) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "PitchCraft-Capstone/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def _schedule_games(data: Any, schema: Any, where: str) -> list[dict[str, Any]]:
    """
    The games of a schedule response, after the whole answer is checked against
    `schema` (mlb_schemas): every date entry, every game and the inner objects the fetcher reads.

    `{"dates": []}` is a valid answer for a day without games and so is a date entry with an
    empty `games` list; a missing list, an error envelope or a game without a field the
    pipeline needs raises `SourceShapeError`, so it is recorded as a source failure.
    """

    mlb_schemas.validate(schema, data, where)
    return [game for entry in data["dates"] for game in entry["games"]]


def _stat_splits(data: Any, schema: Any, where: str) -> list[dict[str, Any]]:
    """
    The splits of a stats response (people or teams endpoint), after the whole answer is
    checked against `schema`: every splits entry carries its `stat` object (and `split.code`
    for a team). `{"stats": []}` and `{"stats": [{"splits": []}]}` are valid answers for a
    player or team without figures; anything else malformed raises `SourceShapeError`.
    """

    mlb_schemas.validate(schema, data, where)
    return [split for entry in data["stats"] for split in entry["splits"]]


@lru_cache(maxsize=None)
def season_dates(season: int) -> tuple[date, date]:
    """
    (first day, last day) of the regular season, from the MLB seasons endpoint.

    Cached for the run; a failed lookup raises and is not cached, so callers
    report the data as unavailable instead of guessing dates.
    """

    data = _get_json(f"https://statsapi.mlb.com/api/v1/seasons/{season}?sportId=1")
    mlb_schemas.validate(mlb_schemas.SEASONS, data, "seasons response")
    entry = data["seasons"][0]
    return (
        date.fromisoformat(entry["regularSeasonStartDate"]),
        date.fromisoformat(entry["regularSeasonEndDate"]),
    )


def fetch_todays_games(target_date: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch today's MLB games with probable pitchers.

    Returns [] on any error so the demo data path stays available.
    """

    date_str = target_date or today_eastern().isoformat()
    url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={date_str}&hydrate=probablePitcher,venue(timezone)"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PitchCraft-Capstone/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())

        games = []
        for game in _schedule_games(data, mlb_schemas.SCHEDULE_DAY, "schedule response"):
            away = game["teams"]["away"]
            home = game["teams"]["home"]
            # Not announced yet is a normal answer: no probablePitcher object at all.
            away_pp = away.get("probablePitcher") or {}
            home_pp = home.get("probablePitcher") or {}
            venue = game.get("venue") or {}
            games.append(
                {
                    "game_pk": game.get("gamePk"),
                    # The official MLB date, not the UTC date of the start time (D29).
                    "official_date": game["officialDate"],
                    "away_team": away["team"]["name"],
                    "away_team_id": away["team"]["id"],
                    "away_team_abbr": _team_abbreviation(away["team"]),
                    "home_team": home["team"]["name"],
                    "home_team_id": home["team"]["id"],
                    "home_team_abbr": _team_abbreviation(home["team"]),
                    "away_pitcher_name": away_pp.get("fullName"),
                    "away_pitcher_id": away_pp.get("id"),
                    "home_pitcher_name": home_pp.get("fullName"),
                    "home_pitcher_id": home_pp.get("id"),
                    "venue": venue.get("name"),
                    # D33: the schedule's UTC instant, and the venue's zone only when it says one.
                    "start_time_utc": game["gameDate"],
                    "venue_timezone": (venue.get("timeZone") or {}).get("id"),
                    "status": (game.get("status") or {}).get("abstractGameState"),
                    # A postponed or cancelled game is "Final" in the first; this says which (D40, F5).
                    "detailed_state": (game.get("status") or {}).get("detailedState"),
                }
            )
        print(f"[LIVE] Fetched {len(games)} games for {date_str}")
        return games
    except Exception as exc:
        print(f"[LIVE] Schedule fetch failed: {exc}")
        _record_failure("mlb_schedule", exc, date=date_str)
        return []


# The API's roll-up of a pitcher's splits: `sport` is `{"id": 0, "code": "All"}`.
ALL_SPORTS_ID = 0


def _season_line_split(splits: list[dict[str, Any]]) -> dict[str, Any]:
    """
    The split that is the pitcher's season line (F22).

    The API answers one split per club and then an aggregate that rolls them up (sport `All`); a pitcher with one club
    has his club's split twice, the second one with that sport. One split is the line. With several, the line is the
    aggregate: never the first (one club only: 15 batters faced instead of 61) and never a sum made here. No
    aggregate, two of them, or one with fewer batters faced than a club it contains is a malformed answer.
    """

    if len(splits) == 1:
        return splits[0]
    rollups = [s for s in splits if (s.get("sport") or {}).get("id") == ALL_SPORTS_ID]
    if len(rollups) != 1:
        raise mlb_schemas.SourceShapeError(
            f"season stats response: {len(splits)} splits and {len(rollups)} aggregate (sport All) splits, "
            "the aggregate is the line and there must be exactly one"
        )
    rollup = rollups[0]
    faced = rollup["stat"].get("battersFaced")
    for split in splits:
        club = split["stat"].get("battersFaced")
        if split is not rollup and club is not None and (faced is None or club > faced):
            raise mlb_schemas.SourceShapeError(
                f"season stats response: the aggregate split has {faced} batters faced, fewer than a club's {club}"
            )
    return rollup


def fetch_pitcher_season_stats(
    pitcher_id: int,
    season: int | None = None,
    as_of: str | date | None = None,
) -> dict[str, Any]:
    """
    Fetch season pitching stats for a pitcher from the MLB Stats API.

    `season` defaults to the year of `as_of` (today when None). With `as_of`,
    the stats cover Jan 1 of the season through that date (inclusive); `as_of`
    must fall in `season`. Raises ValueError otherwise.
    Returns {} on any error so Statcast counts can remain the fallback.

    Scope: REGULAR SEASON ONLY. Both `stats=season` and `stats=byDateRange` leave
    out postseason games even when the range ends after them (checked 2026-10-10:
    a pitcher with 12.2 postseason IP still returned 162.2 regular-season IP);
    postseason needs an explicit gameType. Statcast pitches do include postseason,
    so callers must not present the two as one sample.
    """

    cutoff = _parse_as_of(as_of)
    if season is None:
        season = cutoff.year
    if as_of is None:
        stats_query = "stats=season"
    else:
        if cutoff.year != season:
            raise ValueError(f"as_of {cutoff.isoformat()} is not in season {season}")
        stats_query = (
            f"stats=byDateRange&startDate={season}-01-01&endDate={cutoff.isoformat()}"
        )
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
        f"?{stats_query}&group=pitching&season={season}&sportId=1"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "PitchCraft-Capstone/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())
        splits = _stat_splits(data, mlb_schemas.PITCHER_STATS, "season stats response")
        if not splits:
            return {}
        stat = _season_line_split(splits)["stat"]
        result = {
            "era": stat.get("era", "N/A"),
            "whip": stat.get("whip", "N/A"),
            "innings": stat.get("inningsPitched", "N/A"),
            "strikeouts": stat.get("strikeOuts"),
            "walks": stat.get("baseOnBalls"),
            "home_runs_allowed": stat.get("homeRuns"),
            "batters_faced": stat.get("battersFaced"),
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
        _record_failure("mlb_season_stats", exc, pitcher_id=pitcher_id)
        return {}


def fetch_team_splits(
    team_id: int,
    season: int | None = None,
    as_of: str | date | None = None,
    season_start: str | None = None,
) -> dict[str, Any]:
    """
    Fetch team hitting splits vs LHP and vs RHP for the season.

    Returns {"vl": {...}, "vr": {...}} each with ops, avg, strikeouts, walks,
    plate_appearances, k_rate, and bb_rate. Returns {} on failure.

    `season` defaults to the year of `as_of` (today when None). With `as_of` the
    splits are derived from Statcast plate appearances from `season_start`
    (default: opening day) through that date, never past the end of the regular
    season, because the MLB API ignores startDate and endDate on statSplits.
    `as_of` must fall in `season` (ValueError otherwise).
    """

    if season is None:
        season = _parse_as_of(as_of).year
    if as_of is not None:
        cutoff = _parse_as_of(as_of)
        if cutoff.year != season:
            raise ValueError(f"as_of {cutoff.isoformat()} is not in season {season}")
        mlb_abbr = MLB_TEAM_ABBR_BY_ID.get(team_id)
        code = STATCAST_TEAM_CODE_BY_MLB_ABBR.get(mlb_abbr, mlb_abbr)
        if not code:
            print(f"[LIVE] Team splits: unknown team id {team_id}")
            _record_warning(
                "savant_team_batting",
                "unknown_team",
                f"team id {team_id} is not in the abbreviation map: no Statcast team code, no offense split",
                team_id=team_id,
            )
            return {}
        try:
            first_day, last_day = season_dates(season)
            start = date.fromisoformat(season_start) if season_start else first_day
            df = fetch_team_batting_statcast(
                code, start, min(cutoff, last_day), season_end=last_day
            )
            return derive_team_splits(df, code, cutoff)
        except SavantRequestCapExceeded:
            raise
        except Exception as exc:
            print(f"[LIVE] Team splits from Statcast failed for team {team_id}: {exc}")
            _record_failure("savant_team_batting", exc, team_id=team_id)
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
        for split in _stat_splits(data, mlb_schemas.TEAM_SPLITS, "team splits response"):
            code = split["split"]["code"]
            if code in ("vl", "vr"):
                stat = split["stat"]
                plate_appearances = stat.get("plateAppearances")
                # A count the source does not give is unavailable (None), never a measured zero.
                strikeouts = stat.get("strikeOuts")
                walks = stat.get("baseOnBalls")
                out[code] = {
                    "ops": stat.get("ops"),
                    "avg": stat.get("avg"),
                    "strikeouts": strikeouts,
                    "walks": walks,
                    "plate_appearances": plate_appearances,
                    "k_rate": round(strikeouts / plate_appearances * 100, 1)
                    if plate_appearances and strikeouts is not None
                    else None,
                    "bb_rate": round(walks / plate_appearances * 100, 1)
                    if plate_appearances and walks is not None
                    else None,
                }
        return out
    except Exception as exc:
        print(f"[LIVE] Team splits fetch failed for team {team_id}: {exc}")
        _record_failure("mlb_team_splits", exc, team_id=team_id)
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


def _is_open_chunk(chunk_end: date, season_end: date | None) -> bool:
    """
    A chunk is open (D29) when its month is not complete yet: it ends today or later,
    or before the last day of its month and before the end of the regular season.
    """

    if chunk_end >= date.today():
        return True
    if season_end is not None and chunk_end >= season_end:
        return False
    month_end = (chunk_end.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return chunk_end < month_end


def fetch_team_batting_statcast(
    statcast_team: str, start: date, end: date, season_end: date | None = None
) -> Any:
    """
    Statcast pitch rows from the batting side of one team, `start` to `end`
    inclusive, regular season only.

    pybaseball.statcast(team=...) filters by pitching team, so this asks Savant
    directly with player_type=batter, one request per calendar month (about 7
    per season, never league-wide), paced and capped per run (see _savant_get).
    Finished months are cached on disk, trimmed to the columns the splits need,
    and so are valid empty ones (a blank answer); a response that is not the CSV is an
    error and is never cached. A month that includes today is not cached. The month that holds `end` is open
    (see _is_open_chunk): it is a partial chunk cached under its end date, and its
    requests are counted against the open-month budget of D29. Raises RuntimeError
    if a month hits Savant's row cap (possible truncation), SavantRequestCapExceeded
    when the run's request budget is spent and SavantOpenMonthBudgetExceeded when
    its open-month budget is.
    """

    import pandas as pd

    frames = []
    for chunk_start, chunk_end in _month_chunks(start, end):
        cache_file = (
            TEAM_BATTING_CACHE_DIR / f"{statcast_team}_{chunk_start}_{chunk_end}.csv"
        )
        if cache_file.exists():
            try:
                cached = pd.read_csv(cache_file)
                _validate_team_batting_month(cached, f"cached team batting {statcast_team} {chunk_start}..{chunk_end}")
            except (OSError, ValueError, TruncatedResponse) as exc:
                # A poisoned month is a miss. Keep its bytes until a validated
                # replacement is available; recovery uses the same budgets.
                print(f"[LIVE] Ignoring invalid team batting cache {cache_file.name}: {exc}")
            else:
                if len(cached):
                    frames.append(cached)
                continue
        text = _savant_get(
            SAVANT_BATTING_URL.format(
                team=statcast_team, start=chunk_start.isoformat(), end=chunk_end.isoformat()
            ),
            open_month=_is_open_chunk(chunk_end, season_end),
        )
        if text.strip():
            chunk = pd.read_csv(io.StringIO(text))
            if "game_date" not in chunk.columns:
                # An error page or an error envelope, not Savant's CSV: a failure, never an empty month.
                raise MalformedResponse(
                    f"Savant did not send the batting CSV for {statcast_team} "
                    f"{chunk_start}..{chunk_end}: {text.strip()[:80]!r}"
                )
            _validate_team_batting_month(chunk, f"team batting {statcast_team} {chunk_start}..{chunk_end}")
            chunk = chunk[[c for c in TEAM_BATTING_COLUMNS if c in chunk.columns]]
        else:
            # A blank answer is a valid empty month (off-season, no games): it is cached
            # like any other so the same finished month is never requested twice (D23).
            chunk = pd.DataFrame(columns=list(TEAM_BATTING_COLUMNS))
        if chunk_end < date.today():
            TEAM_BATTING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            chunk.to_csv(cache_file, index=False)
        if len(chunk):
            frames.append(chunk)
    if not frames:
        return pd.DataFrame(columns=list(TEAM_BATTING_COLUMNS))
    return pd.concat(frames, ignore_index=True)


TEAM_SPLIT_REQUIRED_COLUMNS = (
    "game_date",
    "game_type",
    "events",
    "inning_topbot",
    "home_team",
    "away_team",
    "p_throws",
)
PITCHER_STATCAST_REQUIRED_COLUMNS = ("game_date", "game_type")
# What the pitch data of a starter reads from every row (F6c). `events` is not here: without it the counts
# are unavailable and the game stays (F6b). `p_throws` is not here: the hand has its own lookup. `pfx_x`
# and `pfx_z` are not here: without them the movement is `null`, on purpose (`compute_movement`).
PITCH_DATA_REQUIRED_COLUMNS = ("pitch_type", "stand", "release_speed", "plate_x", "plate_z")
# These are all numeric Statcast columns read by the pipeline. Team batting derives
# its figures from categorical events and row counts, not numeric measurements.
PITCH_MEASUREMENT_GROUPS = (
    ("velocity", ("release_speed",)),
    ("movement", ("pfx_x", "pfx_z")),
    ("locations", ("plate_x", "plate_z")),
)
# Every game type Statcast writes: regular season, spring training, exhibition, all-star, then the
# postseason rounds (wild card, division, league championship, world series).
KNOWN_STATCAST_GAME_TYPES = ("R", "S", "E", "A") + POSTSEASON_GAME_TYPES
# The most plate appearances the API can credit to a starter that his Statcast frame does not hold (F21).
# Measured, not assumed (tests/fixtures/statcast_vs_api_pairs.json): 28 real pitchers, 818 appearances, 9,414
# batters faced, a gap of 0 in every one, intentional walks included (Statcast writes a row for each).
STATCAST_PA_TOLERANCE = 0


def _require_columns(df: Any, required: tuple[str, ...], source: str) -> None:
    """A source frame without its integrity columns is a source failure, never a pass-through."""

    missing = [column for column in required if column not in df.columns]
    if missing:
        raise MissingColumn(f"{source} data is missing required column(s): {', '.join(missing)}")


def validate_statcast_rows(df: Any, source: str) -> None:
    """
    Every row of a populated Statcast frame must say when it was played and what kind of game it was.

    A row without a parseable `game_date` or with a `game_type` outside the known set cannot be
    judged against the cutoff or the season, so it is a malformed answer, not an exclusion (QA4-02):
    this raises ValueError naming how many rows and the first one, and the fetcher records it as a
    source failure. Called before any filtering. A frame with no rows is valid (a debut); rows that
    are well formed but do not count (spring training, dates after the cutoff) are filtered later,
    legitimately, and are not errors.
    """

    import pandas as pd

    if len(df) == 0:
        return
    _require_columns(df, PITCHER_STATCAST_REQUIRED_COLUMNS, source)

    game_date = df["game_date"]
    if pd.api.types.is_datetime64_any_dtype(game_date):
        parsed = game_date
    else:
        # Text or date objects only: a number is not a date, however pandas would read it.
        is_text_or_date = game_date.map(lambda value: isinstance(value, (str, date)))
        parsed = pd.to_datetime(game_date.where(is_text_or_date), errors="coerce")
    bad_date = parsed.isna()
    bad_type = ~df["game_type"].isin(KNOWN_STATCAST_GAME_TYPES)
    bad = bad_date | bad_type
    if not bad.any():
        return

    first = df.index[bad][0]
    problems = []
    if bad_date.any():
        problems.append(f"{int(bad_date.sum())} without a valid game_date")
    if bad_type.any():
        problems.append(f"{int(bad_type.sum())} with a missing or unknown game_type")
    raise MalformedRows(
        f"{source} data has {int(bad.sum())} malformed row(s) of {len(df)} ({'; '.join(problems)}); "
        f"first at row {first}: game_date={df.at[first, 'game_date']!r}, game_type={df.at[first, 'game_type']!r}"
    )


def validate_pitcher_frame(df: Any, source: str) -> None:
    """
    `validate_statcast_rows`, plus the columns the pitch data of a starter reads (F6c).

    A populated frame without one of them cannot be turned into a pitch mix: it is a malformed answer,
    rejected whole with the column named, instead of a `KeyError` deep inside the processing. A frame
    with no rows (a debut) is valid and has no columns at all.
    """

    validate_statcast_rows(df, source)
    if len(df) == 0:
        return
    _require_columns(df, PITCH_DATA_REQUIRED_COLUMNS, source)


def require_usable_pitch_columns(df: Any, source: str) -> None:
    """
    A frame that has rows must have a usable value where the pitch data needs one (F6a).

    `pitch_type` null or empty in every row is a pitch table with no pitch in it: published as a debut it
    would say he threw nothing. `stand` with no `L` or `R` in any row makes every share against a side
    `null`, which the page reads as "No left-handed batters faced.", a claim the data does not support.
    Both are malformed answers (contract rule 2, "Malformed or incomplete"), rejected whole. A partial
    null is normal (0.26% of the pitch types of a real season) and stays.
    """

    if len(df) == 0:
        return
    typed = df["pitch_type"].map(lambda value: isinstance(value, str) and value.strip() != "")
    if not typed.any():
        raise UnusableColumn(f"{source} data has {len(df)} row(s) and no usable pitch_type")
    if not df["stand"].isin(("L", "R")).any():
        raise UnusableColumn(f"{source} data has {len(df)} row(s) and no usable stand (no L or R in any row)")


def _finite_pitch_measurements(df: Any, *, pitcher_id: int | None = None) -> Any:
    """Contain malformed numeric cells before filtering or aggregation (QA5-03).

    Null measurements are absent, as before. A populated non-finite cell makes
    its whole measurement group unavailable; dropping only that row would turn
    a malformed answer into an apparently complete mean/median. Counts, mix,
    hand and other groups stay usable. Never mutate the source/cache frame.
    """

    import pandas as pd

    clean = df
    for group, columns in PITCH_MEASUREMENT_GROUPS:
        bad_columns = []
        for column in columns:
            if column not in df.columns:
                continue
            values = pd.to_numeric(df[column], errors="coerce")
            bad = df[column].notna() & ~np.isfinite(values)
            if bad.any():
                bad_columns.append(f"{column} ({int(bad.sum())} row(s), first at {df.index[bad][0]})")
        if not bad_columns:
            continue
        _record_error(
            "statcast_pitcher", "malformed_rows",
            f"pitcher Statcast has non-finite or non-numeric measurements in {', '.join(bad_columns)}; "
            f"{group} unavailable",
            pitcher_id=pitcher_id,
        )
        if clean is df:
            clean = df.copy()
        for column in columns:
            if column in clean.columns:
                clean[column] = np.nan
    return clean


def validate_team_batting_rows(df: Any, source: str) -> None:
    """
    `validate_statcast_rows`, plus the columns that decide whether a row is this team's plate
    appearance and against which hand: the half-inning, both teams and the pitcher's hand. A row
    missing one would be left out of the split without a word, the same silent undercount. The
    cached real Savant rows (53,941 on 2026-10-12) have none of them missing.
    """

    validate_statcast_rows(df, source)
    if len(df) == 0:
        return
    _require_columns(df, TEAM_SPLIT_REQUIRED_COLUMNS, source)
    problem = _event_column_problem(df, source)
    if problem is not None:
        raise problem
    text = lambda column: df[column].map(lambda value: isinstance(value, str) and value.strip() != "")  # noqa: E731
    bad = (
        ~df["inning_topbot"].isin(("Top", "Bot"))
        | ~text("home_team")
        | ~text("away_team")
        | ~df["p_throws"].isin(("L", "R"))
    )
    if bad.any():
        first = df.index[bad][0]
        raise MalformedRows(
            f"{source} data has {int(bad.sum())} malformed row(s) of {len(df)} (a missing or unknown "
            f"inning_topbot, home_team, away_team or p_throws); first at row {first}: "
            f"inning_topbot={df.at[first, 'inning_topbot']!r}, home_team={df.at[first, 'home_team']!r}, "
            f"away_team={df.at[first, 'away_team']!r}, p_throws={df.at[first, 'p_throws']!r}"
        )


def _validate_team_batting_month(df: Any, source: str) -> None:
    """One CSV/cache boundary, including the columns of a header-only month."""

    _require_columns(df, TEAM_SPLIT_REQUIRED_COLUMNS, source)
    if len(df) >= SAVANT_ROW_CAP:
        raise TruncatedResponse(f"{source} has {len(df)} rows: result may be truncated")
    validate_team_batting_rows(df, source)


def _unknown_event_problem(events: Any, source: str) -> UnknownValue | None:
    known = events.map(lambda value: isinstance(value, str) and value in STATCAST_EVENTS)
    if (~known).any():
        first = events[~known].iloc[0]
        return UnknownValue(f"{source} has {int((~known).sum())} unknown events value(s); first: {first!r}")
    return None


def _event_column_problem(df: Any, source: str) -> ValueError | None:
    """Unknown populated outcomes and all-null columns are not measured outs."""

    if len(df) == 0:
        return None
    if "events" not in df.columns:
        return UnusableColumn(f"{source} has no usable events column (missing)")
    events = df["events"].dropna()
    if len(events) == 0:
        return UnusableColumn(f"{source} has no usable events (all rows null)")
    return _unknown_event_problem(events, source)


def _plate_appearance_events(df: Any) -> Any | None:
    """
    The `events` of the rows that end a plate appearance, or None when `events` cannot say (F6b): the column is
    missing or no row of the frame ends one. A truncated plate appearance does not count.
    """

    if "events" not in df.columns or _event_column_problem(df, "Statcast") is not None:
        return None
    events = df["events"].dropna()
    plate_appearances = events[events.isin(COMPLETED_EVENTS)]
    return plate_appearances if len(plate_appearances) else None


def regular_season_plate_appearances(df: Any) -> int | None:
    """
    Plate appearances that end in a regular-season row of the frame: the window of the API line (regular season
    only, opening day to the cutoff), so a postseason plate appearance never fills a gap in it. A frame with no
    rows has none (0); None when `events` cannot say how many there are.
    """

    if len(df) == 0:
        return 0
    if _plate_appearance_events(df) is None:
        return None
    regular = _plate_appearance_events(df[df["game_type"] == "R"])
    return 0 if regular is None else len(regular)


def statcast_is_short(statcast_plate_appearances: int, api_batters_faced: int) -> bool:
    """Fewer plate appearances in Statcast than the API credits to the starter, beyond the measured tolerance."""

    return statcast_plate_appearances + STATCAST_PA_TOLERANCE < api_batters_faced


def incomplete_sample(df: Any, api_batters_faced: int | None) -> str | None:
    """
    Why the Statcast frame is an incomplete sample next to the API line (F21), or None.

    The API line covers January 1 to the cutoff, so a `season_start` later than that makes the frame shorter than
    the line and flags good data; the production callers do not pass one. Nothing is compared when the API gave no batters faced (nothing to compare with) or when `events` cannot
    say how many plate appearances the frame has (its own error is recorded). Statcast with more plate
    appearances than the API is not flagged: the API is the official line. A frame with no rows next to a line
    above zero is the extreme case: not a debut, a gap.
    """

    if api_batters_faced is None:
        return None
    statcast = regular_season_plate_appearances(df)
    if statcast is None or not statcast_is_short(statcast, api_batters_faced):
        return None
    return (
        f"pitcher Statcast data is incomplete: {statcast} regular-season plate appearance(s) in Statcast, "
        f"{api_batters_faced} batters faced in the API line; the pitch data is not used"
    )


def _rate3(value: float | None) -> str | None:
    """Format like the MLB API: .750, 1.012."""

    return None if value is None else f"{value:.3f}".lstrip("0")


def _split_line(events: Any) -> dict[str, Any]:
    events = events.dropna()
    problem = _unknown_event_problem(events, "Statcast")
    if problem is not None:
        raise problem
    outcomes = [STATCAST_EVENTS[event] for event in events if event in COMPLETED_EVENTS]
    plate_appearances = len(outcomes)
    hits = sum(outcome.kind == "hit" for outcome in outcomes)
    total_bases = sum(outcome.bases for outcome in outcomes)
    walks = sum(outcome.kind == "walk" for outcome in outcomes)
    strikeouts = sum(outcome.kind == "strikeout" for outcome in outcomes)
    hit_by_pitch = sum(outcome.kind == "hit_by_pitch" for outcome in outcomes)
    sac_flies = sum(outcome.kind == "sac_fly" for outcome in outcomes)
    sac_bunts = sum(outcome.kind == "sac_bunt" for outcome in outcomes)
    interference = sum(outcome.kind == "interference" for outcome in outcomes)
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
        "k_rate": round(strikeouts / plate_appearances * 100, 1) if plate_appearances else None,
        "bb_rate": round(walks / plate_appearances * 100, 1) if plate_appearances else None,
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
    _require_columns(df, TEAM_SPLIT_REQUIRED_COLUMNS, "team batting")
    validate_team_batting_rows(df, "team batting")
    batting = ((df["inning_topbot"] == "Top") & (df["away_team"] == statcast_team)) | (
        (df["inning_topbot"] == "Bot") & (df["home_team"] == statcast_team)
    )
    keep = (
        batting
        & df["events"].isin(COMPLETED_EVENTS)
        & (pd.to_datetime(df["game_date"]).dt.date <= cutoff)
    )
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
        games = _schedule_games(data, mlb_schemas.SERIES_SCHEDULE, "series game response")
        game = next((g for g in games if g["gamePk"] == game_pk), None)
        if not game or game["gameType"] not in POSTSEASON_GAME_TYPES:
            return {}
        number = game["seriesGameNumber"]
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
        for entry in _schedule_games(data, mlb_schemas.SERIES_SCHEDULE, "series window response"):
            entry_teams = {
                entry["teams"]["home"]["team"]["id"],
                entry["teams"]["away"]["team"]["id"],
            }
            if (
                entry["gameType"] == game_type
                and entry_teams == team_ids
                and entry["seriesGameNumber"] < number
                and date.fromisoformat(entry["officialDate"]) <= cutoff
                and entry["status"]["abstractGameState"] == "Final"
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
        # The hydrated standing of a final series game is mandatory: its absence is a failure,
        # not "no standing".
        mlb_schemas.validate(
            mlb_schemas.SERIES_STATUS,
            last.get("seriesStatus"),
            f"seriesStatus of game {last['gamePk']}",
        )
        status = last["seriesStatus"]
        return {
            **base,
            "games_played": last["seriesGameNumber"],
            "result": status["result"],
            "wins": status["wins"],
            "losses": status["losses"],
            "is_over": status["isOver"],
            "source_game_pk": last["gamePk"],
        }
    except Exception as exc:
        print(f"[LIVE] Series status fetch failed for game {game_pk}: {exc}")
        _record_failure("mlb_series_status", exc, game_pk=game_pk)
        return {}


def fetch_pitcher_statcast(
    pitcher_id: int,
    pitcher_name: str,
    season_start: str | None = None,
    as_of: str | date | None = None,
) -> dict[str, Any] | None:
    """
    Fetch and process Statcast data for one pitcher, or return None on failure.

    Only pitches dated on or before `as_of` (default today) are used, for the
    pitch data and for the season stats, and only from regular-season and
    postseason games (never spring training). The season is the year of
    `as_of`; it starts at `season_start` or opening day. A bad `as_of` raises
    ValueError.
    """

    import pandas as pd

    cutoff = _parse_as_of(as_of)
    try:
        start = season_start or season_dates(cutoff.year)[0].isoformat()
        if cutoff.isoformat() < start:
            # Opening day (D29: the cutoff is the day before the game) or earlier: no pitch can
            # have been thrown this season and there is no valid Statcast range to ask for. The
            # starter is still known, so he is built as a debut below: every pitch-based
            # dimension limited, the game kept (D1). Prior-season carry-over is deferred.
            print(
                f"[LIVE] Season {cutoff.year} has not started as of {cutoff.isoformat()}; "
                "no Statcast request"
            )
            df = pd.DataFrame()
        else:
            print(f"[LIVE] Fetching Statcast for {pitcher_name} (id={pitcher_id})...")
            df = statcast_pitcher(start, cutoff.isoformat(), player_id=pitcher_id)
        if df is None:
            raise MalformedResponse("Statcast returned no result (None)")
        event_problem = None
        # An empty frame is a valid answer (a debut) and may have no columns at all.
        if len(df) > 0:
            validate_pitcher_frame(df, "pitcher Statcast")
            df = _finite_pitch_measurements(df, pitcher_id=pitcher_id)
            event_problem = _event_column_problem(df, "pitcher Statcast")
            df = df[pd.to_datetime(df["game_date"]).dt.date <= cutoff]
            # pybaseball asks for regular season, postseason and spring training.
            # Spring never counts; postseason counts only up to the cutoff above.
            df = df[df["game_type"].isin(("R",) + POSTSEASON_GAME_TYPES)]
            require_usable_pitch_columns(df, "pitcher Statcast")
        processed = None
        counts = None
        if len(df) > 0:
            print(f"[LIVE] {pitcher_name}: {len(df)} pitches fetched")
            counts = _unavailable_statcast_counts(df) if event_problem is not None else _statcast_counts(df)
            if counts["batters_faced"] is None:
                event_problem = event_problem or UnusableColumn(
                    "pitcher Statcast data has no usable 'events' (the column is missing or has no plate "
                    "appearance in any row): batters faced, strikeouts, walks and home runs are "
                    "unavailable from it"
                )
        if event_problem is not None:
            _record_failure("statcast_pitcher", event_problem, pitcher_id=pitcher_id)
        if len(df) > 0:
            processed = process_pitcher_statcast(df, pitcher_name)
            if not processed["pitch_mix"]:
                processed = None
            elif processed["throws"] is None:
                # The frame cannot say which hand he throws with; never assume the right one.
                throws = fetch_pitcher_hand(pitcher_id)
                if throws is None:
                    return None
                processed["throws"] = throws
        if processed is None:
            # No MLB pitches on record (a debut) or none usable. The game is still
            # shown: every pitch-based dimension is flagged limited, never skipped.
            print(f"[LIVE] No usable Statcast pitches for {pitcher_name}; limited-sample starter")
            throws = fetch_pitcher_hand(pitcher_id)
            if throws is None:
                return None
            processed = _empty_pitcher_data(pitcher_name, throws)
            counts = None
        mlb_stats = fetch_pitcher_season_stats(pitcher_id, as_of=as_of)
        # Invalid events cannot establish an incomplete sample either. Preserve
        # sound pitch data and let the independent API line supply its figures.
        problem = None if event_problem is not None else incomplete_sample(df, mlb_stats.get("batters_faced"))
        if problem:
            # A well-formed but incomplete answer is degraded (contract rule 2): the part that cannot be trusted,
            # his pitch data, is unavailable (unknown, not 0) and an error is recorded; the API counts are kept
            # and his hand stays. A mix, a velocity or a primary pitch made from a piece of what he threw would
            # be a claim the data does not support.
            print(f"[LIVE] {pitcher_name}: {problem}")
            _record_error("statcast_pitcher", "incomplete_sample", problem, pitcher_id=pitcher_id)
            processed = _empty_pitcher_data(pitcher_name, processed["throws"])
            counts = None
        elif processed["pitch_mix"]:
            _warn_unmapped_pitch_types(df, pitcher_id)
        _attach_sample(processed, counts, mlb_stats, cutoff, pitches_known=problem is None)
        return processed
    except Exception as exc:
        print(f"[LIVE] Statcast fetch failed for {pitcher_name}: {exc}")
        _record_failure("statcast_pitcher", exc, pitcher_id=pitcher_id)
        return None


def _cached_pitcher_hand(pitcher_id: int) -> str | None:
    """The cached hand, or None when there is no usable cache entry (a bad file is ignored)."""

    path = PITCHER_HAND_CACHE_DIR / f"{pitcher_id}.json"
    try:
        throws = json.loads(path.read_text(encoding="utf-8")).get("throws")
    except (OSError, ValueError, AttributeError):
        return None
    return throws if throws in PITCHER_HANDS else None


def fetch_pitcher_hand(pitcher_id: int) -> str | None:
    """
    Throwing hand ("R", "L" or "S") from the MLB people endpoint, or None (error recorded).

    A hand does not change, so a valid answer is cached for good under
    data_cache/raw/pitcher_hand and a cache hit costs nothing. Only a request counts against
    the budget of PITCHER_HAND_MAX_REQUESTS_PER_RUN per run (a failed one too); past it the
    answer is unavailable and the error says why, without a call. A failed or invalid answer
    is never cached.
    """

    cached = _cached_pitcher_hand(pitcher_id)
    if cached is not None:
        return cached
    if _pitcher_hand_run["requests"] >= PITCHER_HAND_MAX_REQUESTS_PER_RUN:
        message = (
            f"pitcher hand request budget of {PITCHER_HAND_MAX_REQUESTS_PER_RUN} per run "
            "is spent"
        )
        print(f"[LIVE] Pitcher hand lookup skipped for id={pitcher_id}: {message}")
        _record_error("mlb_person", "budget_spent", message, pitcher_id=pitcher_id)
        return None
    _pitcher_hand_run["requests"] += 1
    try:
        data = _get_json(f"https://statsapi.mlb.com/api/v1/people/{pitcher_id}")
        mlb_schemas.validate(mlb_schemas.PERSON, data, "person response")
        throws = data["people"][0]["pitchHand"]["code"]
        if throws not in PITCHER_HANDS:
            raise UnknownValue(f"unknown throwing hand {throws!r}")
    except Exception as exc:
        print(f"[LIVE] Pitcher hand lookup failed for id={pitcher_id}: {exc}")
        _record_failure("mlb_person", exc, pitcher_id=pitcher_id)
        return None
    try:
        PITCHER_HAND_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (PITCHER_HAND_CACHE_DIR / f"{pitcher_id}.json").write_text(
            json.dumps({"pitcher_id": pitcher_id, "throws": throws}), encoding="utf-8"
        )
    except OSError as exc:  # the answer is still good; only the cache is lost
        print(f"[LIVE] Could not cache the hand of id={pitcher_id}: {exc}")
    return throws


def _unavailable_statcast_counts(df: Any) -> dict[str, Any]:
    return {
        "batters_faced": None, "strikeouts": None, "walks": None, "home_runs": None,
        "has_postseason": "game_type" in df.columns and bool((df["game_type"] != "R").any()),
    }


def _statcast_counts(df: Any) -> dict[str, Any]:
    """
    Plate-appearance counts from the Statcast frame (regular season + postseason).

    A frame whose `events` cannot say how many batters he faced, because the column is missing or no row
    ends a plate appearance, has unavailable counts (None), never a measured zero (F6b). The limit: a
    starter hurt on his first pitch has pitches and no plate appearance, and cannot be told from an
    unusable column; his counts are unavailable rather than 0 (contract 6.4).
    """

    unavailable = _unavailable_statcast_counts(df)
    plate_appearances = _plate_appearance_events(df)
    if plate_appearances is None:
        return unavailable
    line = _split_line(plate_appearances)
    return {
        "batters_faced": int(len(plate_appearances)),
        "strikeouts": line["strikeouts"],
        "walks": line["walks"],
        "home_runs": sum(STATCAST_EVENTS[event].bases == 4 for event in plate_appearances),
        "has_postseason": unavailable["has_postseason"],
    }


def _warn_unmapped_pitch_types(df: Any, pitcher_id: int) -> None:
    """A pitch code the name map does not know is published as the source value, with no family (F6e)."""

    unmapped = sorted({code for code in df["pitch_type"].dropna().unique() if code and code not in PITCH_NAME_MAP})
    if unmapped:
        rows = int(df["pitch_type"].isin(unmapped).sum())
        _record_warning(
            "statcast_pitcher",
            "unmapped_pitch_type",
            f"pitch code(s) {', '.join(unmapped)} are not in the name map ({rows} pitch(es)): "
            "published as source values with no family, and no role is given to them",
            pitcher_id=pitcher_id,
        )


def _empty_pitcher_data(pitcher_name: str, throws: str) -> dict[str, Any]:
    return {
        "name": pitcher_name,
        "throws": throws,
        "pitch_mix": [],
        "velocity_by_pitch": [],
        "movement": {},
        "pitch_locations": {"vs_lhh": [], "vs_rhh": []},
        "pitching_profile": {
            "style_label": labels.ARSENAL_LIMITED_STYLE,
            "primary_pitch": "Not available",
            "putaway_pitch": "Not available",
            "command_label": None,
            "swing_miss_label": None,
            "contact_risk_label": None,
        },
    }


def _attach_sample(
    processed: dict[str, Any],
    counts: dict[str, Any] | None,
    mlb_stats: dict[str, Any],
    cutoff: date,
    pitches_known: bool = True,
) -> None:
    """
    Build the sample, the season summary and the rate labels, each with its scope.

    `pitches_known` is False for a starter whose Statcast answer was found incomplete (F21): his pitch count is
    unknown (`None`), not the 0 of a debut, and the pitch group has no scope.

    Arsenal pitches come from the Statcast frame behind the pitch mix (regular
    season, plus postseason when such games are in it). Rate counts come from the
    MLB API when it answers (regular season only, like ERA/WHIP), otherwise from
    the same Statcast frame, and the sample records which.
    """

    through = cutoff.isoformat()
    arsenal_kind = (
        labels.SCOPE_REGULAR_POSTSEASON
        if counts and counts["has_postseason"]
        else labels.SCOPE_REGULAR
    )
    pitches = processed.pop("pitches_used", 0) if processed["pitch_mix"] else 0
    if not pitches_known:
        pitches = None
    api_numbers = {
        "batters_faced": mlb_stats.get("batters_faced"),
        "strikeouts": mlb_stats.get("strikeouts"),
        "walks": mlb_stats.get("walks"),
        "home_runs": mlb_stats.get("home_runs_allowed"),
    }
    api_complete = all(value is not None for value in api_numbers.values())
    api_partial = any(value is not None for value in api_numbers.values())
    statcast_counts = counts is not None and counts["batters_faced"] is not None
    # A valid API line can lack some counts (they are optional figures). It is the source only
    # when it has all four: a line without them never hides valid Statcast counts (QA3-02), and a
    # partial one is used only when Statcast has nothing. Sources are never mixed field by field.
    if api_complete or (api_partial and not statcast_counts):
        source, rates_kind = "mlb_api", labels.SCOPE_REGULAR
        numbers = api_numbers
    elif statcast_counts:
        source, rates_kind = "statcast", arsenal_kind
        numbers = {key: counts[key] for key in ("batters_faced", "strikeouts", "walks", "home_runs")}
    else:
        source, rates_kind = "unavailable", labels.SCOPE_REGULAR
        numbers = {"batters_faced": None, "strikeouts": None, "walks": None, "home_runs": None}

    rates_scope = labels.make_scope(rates_kind, through)
    sample = labels.build_sample(
        pitches=pitches,
        arsenal_scope=labels.make_scope(arsenal_kind, through),
        batters_faced=numbers["batters_faced"],
        strikeouts=numbers["strikeouts"],
        walks=numbers["walks"],
        home_runs=numbers["home_runs"],
        rates_source=source,
        rates_scope=rates_scope,
    )
    processed["sample"] = sample
    summary = {
        "era": mlb_stats.get("era", "N/A") if mlb_stats else "N/A",
        "whip": mlb_stats.get("whip", "N/A") if mlb_stats else "N/A",
        "innings": mlb_stats.get("innings", "N/A") if mlb_stats else "N/A",
        "strikeouts": numbers["strikeouts"],
        "walks": numbers["walks"],
        "home_runs_allowed": numbers["home_runs"],
    }
    # One scope per group of figures (QA4-01): ERA, WHIP and innings are the API's (regular season only);
    # the counts have the scope of the source that gave them, which can be Statcast's. A group with no
    # figures has no scope.
    has_season_rates = any(labels.is_available(summary[key]) for key in labels.SEASON_RATE_FIELDS)
    summary["scopes"] = {
        "season_rates": labels.make_scope(labels.SCOPE_REGULAR, through) if has_season_rates else None,
        "counts": None if source == "unavailable" else rates_scope,
    }
    processed["season_summary"] = summary
    processed.pop("statcast_counts", None)
    labels.apply_profile_labels(processed["pitching_profile"], sample)


def normalize_plate_x(x: float) -> float:
    """Normalize plate_x (-1.7 to 1.7) to 0-1, left to right."""

    return round(float(np.clip((x + 1.7) / 3.4, 0.0, 1.0)), 3)


def normalize_plate_z(z: float) -> float:
    """Normalize plate_z (0.5 to 5.0) to 0-1, inverted for SVG coordinates."""

    return round(float(np.clip(1.0 - (z - 0.5) / 4.5, 0.0, 1.0)), 3)


def process_pitcher_statcast(df: Any, pitcher_name: str) -> dict[str, Any]:
    """Convert raw Statcast rows into the PitchCraft v0.2.0 chart shape."""

    import pandas as pd

    # Also protect direct callers; an already validated frame is unchanged.
    df = _finite_pitch_measurements(df)
    df = df.dropna(subset=["pitch_type"])
    df = df[df["pitch_type"] != ""].copy()
    df["pitch_name"] = df["pitch_type"].map(PITCH_NAME_MAP).fillna(df["pitch_type"])

    total = len(df)
    lhh = df[df["stand"] == "L"]
    rhh = df[df["stand"] == "R"]

    pitch_mix = []
    velocity_rows = []
    # Raw pitch counts: ranking and the put-away rule (D30) never use the rounded share.
    pitch_counts: dict[str, int] = {}

    for pitch_name, sub in df.groupby("pitch_name"):
        sub_l = lhh[lhh["pitch_name"] == pitch_name]
        sub_r = rhh[rhh["pitch_name"] == pitch_name]
        pitch_counts[pitch_name] = len(sub)

        pitch_mix.append(
            {
                "pitch": pitch_name,
                "away_starter": {
                    "overall": _usage_pct(len(sub), total),
                    "vs_lhh": _usage_pct(len(sub_l), len(lhh)),
                    "vs_rhh": _usage_pct(len(sub_r), len(rhh)),
                    # Raw counts behind the rounded shares: decisions use these (QA3-03).
                    "count": len(sub),
                    "total": total,
                },
                "home_starter": {"overall": 0, "vs_lhh": 0, "vs_rhh": 0, "count": 0, "total": 0},
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

    # Most thrown first by raw count (two pitches that both read 20.0% are not a tie);
    # a real tie in the counts is ranked by name so the order is stable.
    pitch_mix.sort(key=lambda row: (-pitch_counts[row["pitch"]], row["pitch"]))
    pitch_mix = pitch_mix[:5]
    top_pitch_names = {row["pitch"] for row in pitch_mix}
    velocity_rows = [row for row in velocity_rows if row["pitch"] in top_pitch_names]
    kept_names = [row["pitch"] for row in pitch_mix]
    movement = compute_movement(df, kept_names)
    # None when the frame cannot say: the fetcher then asks the MLB people endpoint. A guess
    # of "R" would pick the wrong team split and print the wrong hand.
    throws = (
        df["p_throws"].dropna().iloc[0]
        if "p_throws" in df.columns and len(df["p_throws"].dropna()) > 0
        else None
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

    # Only pitches that were thrown: no pitch is invented to fill a slot.
    top, second = labels.profile_pitches(pitch_counts)
    style = f"{top}-{second} starter" if labels.pitch_named(second) else f"{top} starter"
    if not labels.pitch_named(top):
        style = labels.ARSENAL_LIMITED_STYLE

    return {
        "name": pitcher_name,
        "throws": throws,
        "pitch_mix": pitch_mix,
        "velocity_by_pitch": velocity_rows,
        "movement": movement,
        "pitch_locations": pitch_locations,
        "pitches_used": total,
        "pitching_profile": {
            "style_label": style,
            "primary_pitch": top,
            "putaway_pitch": second,
            "command_label": None,
            "swing_miss_label": None,
            "contact_risk_label": None,
        },
    }


def compute_movement(df: Any, pitch_types_kept: list[str]) -> dict[str, Any]:
    """
    For each pitch type, compute median horizontal and vertical movement in inches.

    Pitch families are mapped for frontend color and copy. Movement that is missing
    (no columns, all null, or fewer than three observations) is None, never zero: the
    keys stay so the JSON shape is stable, but a zero would read as a measured shape.
    """

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
            h_break, v_break = None, None
        result[name] = {
            "h_break": h_break,
            "v_break": v_break,
            "family": labels.PITCH_FAMILY.get(name),  # a pitch the map does not know has none (F6e)
        }
    return result


def pick_featured_games(games: list[dict[str, Any]], max_games: int = 3) -> list[dict[str, Any]]:
    """Return up to max_games where both probable pitchers are known."""

    eligible = [game for game in games if game["away_pitcher_id"] and game["home_pitcher_id"]]
    return eligible[:max_games]


def build_live_snapshot(
    target_date: str | None = None,
    as_of: str | date | None = None,
    run_info: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """
    Fetch schedule and Statcast data, returning a generator-ready snapshot.

    `target_date` is the official MLB date of the games (default: today in New
    York). The data cutoff passed to every pitcher and team fetch is the day
    before each game (D29); an explicit `as_of` may only be earlier than that.
    `run_info`, when given, is filled with games_scheduled, games_live and
    skipped_games for the run record.
    """

    info = run_info if run_info is not None else {}
    target = target_date or today_eastern().isoformat()
    if as_of is not None:
        resolve_as_of(target, as_of)  # reject an as_of on or after the game day up front
    games = fetch_todays_games(target)
    info.update(games_scheduled=len(games), games_live=0, skipped_games=[])
    if not games:
        return None

    candidates = pick_featured_games(games, 5)
    if not candidates:
        print("[LIVE] No game with both probable pitchers found")
        info["skipped_games"] = [
            f"{game_label(g)} (probable pitcher not announced)"
            for g in games
        ]
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

        game_as_of = resolve_as_of(featured.get("official_date") or target, as_of).isoformat()
        away_data = fetch_pitcher_statcast(
            featured["away_pitcher_id"],
            featured["away_pitcher_name"],
            as_of=game_as_of,
        )
        home_data = fetch_pitcher_statcast(
            featured["home_pitcher_id"],
            featured["home_pitcher_name"],
            as_of=game_as_of,
        )

        if not away_data or not home_data:
            skipped = (
                f"{game_label(featured)} "
                f"({featured['away_pitcher_name']} vs {featured['home_pitcher_name']})"
            )
            skipped_games.append(skipped)
            print(f"[LIVE] Skipping {skipped} - insufficient pitch data")
            continue

        away_splits = fetch_team_splits(featured["away_team_id"], as_of=game_as_of)
        home_splits = fetch_team_splits(featured["home_team_id"], as_of=game_as_of)
        live_games.append(
            {
                "featured_game": featured,
                "as_of": game_as_of,
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

    info.update(games_live=len(live_games), skipped_games=skipped_games)
    if not live_games:
        print("[LIVE] No live games had sufficient Statcast data - no snapshot written")
        return None

    primary = live_games[0]
    snapshot = {
        # The schema the snapshot's figures were written under: an older one is not read (D2.1a).
        "schema_version": SCHEMA_VERSION,
        "data_mode": "fetched_snapshot",
        "fetched_date": target,
        "as_of": primary["as_of"],
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

def _usage_pct(part: int, total: int) -> float | None:
    """A share of `total`, or None when there is nothing to take a share of (never 0%)."""

    return round(part / total * 100, 1) if total > 0 else None


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

    def not_thrown(data: dict[str, Any]) -> dict[str, Any]:
        # A pitch he never threw: a real zero out of his own total (every row carries it), and a
        # real zero against a side he faced. Against a side he never faced it is unavailable.
        rows = [row["away_starter"] for row in data["pitch_mix"]]
        total = rows[0]["total"] if rows else 0

        def against(side: str) -> int | None:
            return 0 if any(usage[side] is not None for usage in rows) else None

        # A starter who threw nothing (total 0) has no share of anything: `null`, not 0% (F20). A pitch he never
        # threw out of a positive total is a real 0%.
        return {
            "overall": None if total == 0 else 0,
            "vs_lhh": against("vs_lhh"),
            "vs_rhh": against("vs_rhh"),
            "count": 0,
            "total": total,
        }

    return [
        {
            "pitch": pitch_name,
            "away_starter": away_pitches.get(pitch_name, {}).get("away_starter", not_thrown(away_data)),
            "home_starter": home_pitches.get(pitch_name, {}).get("away_starter", not_thrown(home_data)),
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


def _run_status(info: dict[str, Any], errors: list[dict[str, Any]]) -> str:
    """
    ok: at least one live game was built (errors, if any, are in the record).
    failed: nothing usable and something went wrong.
    no_games: nothing scheduled and nothing went wrong.
    no_usable_games: games scheduled but none had both probable pitchers and pitch data.
    """

    if info.get("games_live"):
        return "ok"
    if errors:
        return "failed"
    if not info.get("games_scheduled"):
        return "no_games"
    return "no_usable_games"


def _run_as_of(target: str, as_of: str | date | None) -> str | None:
    """The cutoff of a run that produced no snapshot, or None if it was rejected."""

    try:
        return resolve_as_of(target, as_of).isoformat()
    except ValueError:
        return None


def run_live_pipeline(
    target_date: str | None = None,
    as_of: str | date | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    Run the live fetch and return (run record, snapshot or None). No file I/O.

    The record always says what happened, including failures, so a failed run
    can never be mistaken for a live one.
    """

    _run_errors.clear()
    _run_warnings.clear()
    _savant_run.update(requests=0, open_requests=0)  # the Savant budgets are per run
    _pitcher_hand_run.update(requests=0)  # so is the pitcher-hand budget
    info: dict[str, Any] = {}
    run_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    target = target_date or today_eastern().isoformat()
    try:
        snapshot = build_live_snapshot(target, as_of, run_info=info)
    except Exception as exc:
        _record_failure("pipeline", exc)
        snapshot = None
    record = {
        "status": _run_status(info, _run_errors),
        "run_at": run_at,
        "target_date": target,
        "as_of": snapshot["as_of"] if snapshot is not None else _run_as_of(target, as_of),
        "games_scheduled": info.get("games_scheduled", 0),
        "games_live": info.get("games_live", 0),
        "skipped_games": info.get("skipped_games", []),
        "errors": list(_run_errors),
        "warnings": list(_run_warnings),
    }
    if snapshot is not None:
        snapshot["run_at"] = run_at
    return record, snapshot


def main_with_args(target_date: str | None, as_of: str | None) -> int:
    from data_pipeline.fetchers.cache_manager import save_processed

    print("[LIVE] PitchCraft live data pipeline starting...")
    record, snapshot = run_live_pipeline(target_date, as_of)
    save_processed("live_run", record)
    print(
        f"[LIVE] Run status: {record['status']} "
        f"({record['games_live']}/{record['games_scheduled']} games, "
        f"{len(record['errors'])} error(s))"
    )
    if snapshot is None:
        print("[LIVE] No live snapshot written; the generator will not present demo data as live.")
        return 1 if record["status"] == "failed" else 0

    save_processed("live_matchup", snapshot)
    print(
        "[LIVE] Snapshot saved. Featured: "
        f"{snapshot['featured_game']['away_team']} @ "
        f"{snapshot['featured_game']['home_team']}"
    )
    print(f"[LIVE] Live games processed: {len(snapshot['live_games'])}")
    if snapshot.get("skipped_games"):
        print(f"[LIVE] Skipped games: {', '.join(snapshot['skipped_games'])}")
    for side in ("away", "home"):
        starter = snapshot[f"{side}_starter"]
        top = starter["pitch_mix"][0] if starter["pitch_mix"] else None
        detail = (
            f"top pitch: {top['pitch']} {top['away_starter']['overall']}%"
            if top
            else "no pitches on record (limited sample)"
        )
        print(f"[LIVE] {side.capitalize()}: {starter['name']} - {detail}")
    return 0


def main() -> int:
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    as_of = sys.argv[2] if len(sys.argv) > 2 else None
    return main_with_args(target_date, as_of)


if __name__ == "__main__":
    raise SystemExit(main())
