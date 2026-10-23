"""Schema constants for the PitchCraft v0.9.0 demo payload."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from collections.abc import Mapping
import re
from typing import Any
from zoneinfo import ZoneInfo

SCHEMA_VERSION = "0.9.0"


def is_no_games_run(run: Any) -> bool:
    """Only a sound empty schedule, never an error or missing data, is an empty live day (D43)."""
    if not isinstance(run, Mapping):
        return False
    try:
        target, cutoff = (date.fromisoformat(run[key]) for key in ("target_date", "as_of"))
        return (
            run["status"] == "no_games"
            and target.isoformat() == run["target_date"] and cutoff.isoformat() == run["as_of"]
            and cutoff == target - timedelta(days=1)
            and new_york_day(run["run_at"]) is not None
            and all(type(run[key]) is int and run[key] == 0 for key in ("games_scheduled", "games_live"))
            and run["errors"] == [] and run["warnings"] == []
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def is_no_games_file(payload: Any) -> bool:
    """The complete empty-live state; shared by validation and the manifest."""
    try:
        metadata = payload["metadata"]
        status = metadata["data_status"]
        return (
            metadata["data_mode"] == status["mode"] == "fetched_snapshot"
            and status["reason"] is None and is_no_games_run(status["live_run"])
            and metadata["data_fetched_at"] == status["live_run"]["run_at"]
            and payload["matchups"] == [] and payload["featured_matchup_id"] is None
        )
    except (KeyError, TypeError):
        return False
# 0.9.0 (P1.5-a, D43): `matchups[].series` is null for a game that is not a postseason game and an object
# `{series_name, game_number, games_in_series, standing}` for one that is (null until the producer of row 7); `matchups` may
# be empty and `featured_matchup_id` null for a day with no games, and `archive[].result_label` and `grade_label` may be
# null (the page reads them; the producers are rows 7 and 9), so a reader of 0.8.0 breaks.
# 0.8.0 (P0.15-D2.5, D40): `matchups[].status` is the schedule's game state (`upcoming`, `live`, `final`) or null, and
# `data_confidence.lineup_status` follows it and may be null, so a reader of 0.7.0 (always `upcoming`) breaks.
# 0.7.0 (P0.15-D2.4c, D39): `metadata.data_fetched_at` is the instant of the live fetch (null in a demo file) and
# `metadata.generated_at` the instant the file was built, so a reader of 0.6.0 (one field for both) breaks.
# 0.6.0 (P0.15-D2.3, D38): `offense_profile.vs_pitcher_hand` is null for a starter whose hand is not L or R, a starter's
# `throws` may be `S`, and `data_status.live_run.errors`, `warnings` and `reason` are `{source, code}` from closed
# sets, so a reader of 0.5.0 breaks.
# 0.5.0 (P0.15-D2.2c, D37): a pitch family, a team abbreviation (`teams.*.abbreviation`, `starters.*.team`) and
# a pitch share (`charts.pitch_mix[].<slot>.overall`) are null when unknown (an unmapped pitch, an unknown team,
# a starter with no pitches), so a reader of 0.4.0 breaks.
# 0.4.0 (P0.15-D2.1a): the scope of a group of figures is null when the group has no figure
# (`sample.rates.scope`, `sample.arsenal.scope`, `offense_profile.scope`), so a reader of 0.3.0 breaks.
# A live snapshot carries the schema it was written under and is read only if that is exactly this one.


def snapshot_matches_schema(version: Any) -> bool:
    """True when a snapshot was written under exactly the schema of this code (a missing or different one is not read)."""

    return isinstance(version, str) and version == SCHEMA_VERSION


_UTC_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def is_utc_instant(value: Any) -> bool:
    """True for an explicit UTC instant written as YYYY-MM-DDTHH:MM:SSZ (what the MLB schedule sends)."""

    if not isinstance(value, str) or not _UTC_INSTANT.fullmatch(value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


NEW_YORK = ZoneInfo("America/New_York")  # the zone of the official date (D29) and of every day the page says
_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})")


def new_york_day(value: Any) -> str | None:
    """The day (YYYY-MM-DD) an instant falls on in America/New_York, or None when `value` is not an instant with a zone."""

    if not isinstance(value, str) or not _INSTANT.fullmatch(value):
        return None
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if instant.tzinfo is None:
        return None
    return instant.astimezone(NEW_YORK).date().isoformat()


# The five agents of the workflow, in order (the one place that names them), and what a step may say (D2.4d, F19).
WORKFLOW_AGENTS = (
    "Data Scout Agent",
    "Matchup Analyst Agent",
    "Report Writer Agent",
    "Critic / Fact-check Agent",
    "Postgame Grader Agent",
)
STEP_STATUSES = ("completed", "not_applicable", "pending")

# The state of a game (rule 7, F5). A game that was not played arrives with `abstractGameState` "Final" and the truth in
# `detailedState` (measured 2026-10-16 over 208 games: "Postponed" and "Cancelled"), so the pair decides, never the first
# alone. Only the pairs the owner named or a real answer showed are listed; every other pair, and a missing part, is
# unknown (`null`): never `upcoming` and never `final`. The table grows with real answers, not by guess.
GAME_STATUS: dict[tuple[str, str], str] = {
    ("Preview", "Scheduled"): "upcoming",
    ("Preview", "Pre-Game"): "upcoming",
    ("Live", "In Progress"): "live",
    ("Final", "Final"): "final",
    ("Final", "Game Over"): "final",
    ("Final", "Completed Early"): "final",
}
# The state a published status stands for: what the registry's conditions ask ("Preview" for the lineups sentence).
STATE_OF_STATUS: dict[str, str] = {
    "upcoming": "Preview",
    "live": "Live",
    "final": "Final",
}
LINEUP_STATUS: dict[str, str] = {
    "upcoming": "probable_pitchers",
    "live": "game_started",
    "final": "game_started",
}


def game_status(abstract_state: Any, detailed_state: Any) -> str | None:
    """The published status of a game from the schedule's two states, or None when the table does not know the pair."""

    if not isinstance(abstract_state, str) or not isinstance(detailed_state, str):
        return None
    return GAME_STATUS.get((abstract_state, detailed_state))


def lineup_status_of(status: str | None) -> str | None:
    """The lineup status that goes with a published status (None for an unknown game state)."""

    return LINEUP_STATUS.get(status) if isinstance(status, str) else None


TOP_LEVEL_REQUIRED_KEYS = (
    "metadata",
    "featured_matchup_id",
    "matchups",
    "archive",
    "agent_workflow",
    "disclaimers",
    "claims",
)

MATCHUP_REQUIRED_KEYS = (
    "series",
    "game",
    "teams",
    "starters",
    "charts",
    "pitch_locations",
    "report",
    "critic_review",
    "data_confidence",
)

TEAM_SIDES = ("home", "away")
STARTER_SLOTS = ("away_starter", "home_starter")
CHART_KEYS = ("pitch_mix", "velocity_by_pitch", "strength_profile", "pitch_movement")
BATTER_HAND_SPLITS = ("overall", "vs_lhh", "vs_rhh")
PITCH_LOCATION_SPLITS = ("vs_lhh", "vs_rhh")

POSTGAME_STARTER_LINE_REQUIRED_KEYS = (
    "name",
    "innings_pitched",
    "hits_allowed",
    "earned_runs",
    "unearned_runs",
    "strikeouts",
    "walks",
    "home_runs_allowed",
    "game_score",
    "pitchcraft_grade",
    "grade_explanation",
    "plan_vs_execution",
    "what_to_watch_next",
)

CRITIC_STATUSES = (
    "supported",
    "unsupported",
    "not_present",
    "warning",
)

BETTING_TERMS = (
    "bet",
    "odds",
    "lock",
    "guaranteed",
    "win probability",
)

