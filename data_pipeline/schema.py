"""Schema constants for the PitchCraft v0.2.0 demo payload."""

from __future__ import annotations

SCHEMA_VERSION = "0.2.0"

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
CHART_KEYS = ("pitch_mix", "velocity_by_pitch", "strength_profile")
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
    "revised",
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

