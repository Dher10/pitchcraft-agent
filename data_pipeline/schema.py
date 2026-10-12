"""Schema constants for the PitchCraft v0.2.0 demo payload."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any

SCHEMA_VERSION = "0.2.0"

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


TOP_LEVEL_REQUIRED_KEYS = (
    "metadata",
    "featured_matchup_id",
    "matchups",
    "archive",
    "agent_workflow",
    "disclaimers",
)

MATCHUP_REQUIRED_KEYS = (
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

