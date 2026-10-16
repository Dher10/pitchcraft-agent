"""Build a live matchup from a snapshot game, from nothing (PLAN.md P0.15-A, D33).

A live matchup used to be a deep copy of the demo's `matchup_001` patched field by field, so every
field nobody remembered to overwrite was a demo value under a live game (QA4-03: the Oracle Park time
zone on a Yankee Stadium game). Here nothing is copied. Each field is either supplied by the snapshot
or explicitly unavailable (None, an empty list, "N/A"). This module must not import the demo; a test
fails if it does.

The agents add `report`, `critic_review` and `data_confidence` afterwards, as for every matchup.
"""

from __future__ import annotations

from typing import Any

from data_pipeline import labels
from data_pipeline.generator_texts import generator_catalog

# What a live starter shows for a field its snapshot does not supply (never a demo value).
UNAVAILABLE_SUMMARY = {
    "era": "N/A",
    "whip": "N/A",
    "innings": "N/A",
    "strikeouts": None,
    "walks": None,
    "home_runs_allowed": None,
}
UNAVAILABLE_PROFILE = {
    "style_label": labels.ARSENAL_LIMITED_STYLE,
    "primary_pitch": "Not available",
    "putaway_pitch": "Not available",
    "command_label": None,
    "swing_miss_label": None,
    "contact_risk_label": None,
}

# What the pitch location numbers are, as `normalize_plate_x` / `normalize_plate_z` write them. It says
# nothing about how the frontend draws the strike zone and nothing about any game or pitcher.
PITCH_LOCATIONS_NOTE = (
    "x,y are 0-1 within the plot area, as the catcher sees it. 0,0 is the top-left corner; "
    "x grows to the catcher's right and y grows downward."
)


def build_matchup(
    live_game: dict[str, Any],
    *,
    matchup_id: str,
    is_featured: bool,
    fetched_date: str,
    through: str,
) -> dict[str, Any]:
    """One live matchup. `fetched_date` is the game day, `through` the last day its figures cover."""

    fg = live_game["featured_game"]
    away = live_game["away_starter"]
    home = live_game["home_starter"]
    offense_scope = labels.make_scope(labels.SCOPE_REGULAR, through)
    starters = {
        "away_starter": build_starter(away, fg["away_team_abbr"], fg["away_pitcher_id"], through),
        "home_starter": build_starter(home, fg["home_team_abbr"], fg["home_pitcher_id"], through),
    }
    return {
        "id": matchup_id,
        "date": fetched_date,
        "status": "upcoming",
        "is_featured": is_featured,
        "game": {
            "title": f"{fg['away_team']} vs {fg['home_team']}",
            "venue": fg.get("venue") or None,
            # D33: the schedule's UTC instant, and the venue's zone only if the source gave one.
            "start_time_utc": fg["start_time_utc"],
            "start_time_local": None,
            "timezone": fg.get("venue_timezone") or None,
            # No live source for a broadcast note.
            "broadcast_note": None,
            "home_team_id": str(fg["home_team_id"]),
            "away_team_id": str(fg["away_team_id"]),
        },
        "teams": {
            "home": {
                "id": str(fg["home_team_id"]),
                "name": fg["home_team"],
                "abbreviation": fg["home_team_abbr"],
                "record": None,
                # The home lineup faces the away starter.
                "offense_profile": build_offense(away["throws"], live_game.get("home_team_splits"), offense_scope),
            },
            "away": {
                "id": str(fg["away_team_id"]),
                "name": fg["away_team"],
                "abbreviation": fg["away_team_abbr"],
                "record": None,
                "offense_profile": build_offense(home["throws"], live_game.get("away_team_splits"), offense_scope),
            },
        },
        "starters": starters,
        "charts": {
            "pitch_mix": live_game["combined_charts"]["pitch_mix"],
            "velocity_by_pitch": live_game["combined_charts"]["velocity_by_pitch"],
            # There is no live source for the 0-100 strength scores.
            "strength_profile": [],
            "pitch_movement": {
                "away_starter": away.get("movement") or {},
                "home_starter": home.get("movement") or {},
            },
        },
        "pitch_locations": {
            "note": PITCH_LOCATIONS_NOTE,
            "away_starter": {
                "vs_lhh": away["pitch_locations"]["vs_lhh"],
                "vs_rhh": away["pitch_locations"]["vs_rhh"],
            },
            "home_starter": {
                "vs_lhh": home["pitch_locations"]["vs_lhh"],
                "vs_rhh": home["pitch_locations"]["vs_rhh"],
            },
        },
        "postgame": None,
        "data_confidence": confidence_note(matchup_id, fetched_date, starters),
    }


def build_starter(
    live_starter: dict[str, Any],
    team_abbr: str | None,
    pitcher_id: int,
    through: str,
) -> dict[str, Any]:
    """A starter made of unavailable defaults plus what the snapshot supplies, never anything else."""

    sample = live_starter.get("sample") or unknown_sample(through)
    # A summary that does not say the scope of a group has none for it: a scope is never invented.
    summary = {
        **UNAVAILABLE_SUMMARY,
        "scopes": {"season_rates": None, "counts": None},
        **(live_starter.get("season_summary") or {}),
    }
    profile = {**UNAVAILABLE_PROFILE, **(live_starter.get("pitching_profile") or {})}
    # The sample decides every label. A snapshot from before samples existed has none: every
    # dimension is then limited.
    labels.apply_profile_labels(profile, sample)
    return {
        "id": str(pitcher_id),
        "name": live_starter["name"],
        "team": team_abbr,
        # Never guessed: `_game_unsafe` rejects a starter without it.
        "throws": live_starter["throws"],
        # No live source yet (P1.5 adds bio).
        "bio": None,
        "season_summary": summary,
        "pitching_profile": profile,
        "recent_form": None,
        "sample": sample,
    }


def unknown_sample(through: str) -> dict[str, Any]:
    scope = labels.make_scope(labels.SCOPE_REGULAR, through)
    return labels.build_sample(
        pitches=None,
        arsenal_scope=scope,
        batters_faced=None,
        strikeouts=None,
        walks=None,
        home_runs=None,
        rates_source="unavailable",
        rates_scope=scope,
    )


def build_offense(
    starter_hand: str,
    splits: dict[str, Any] | None,
    scope: dict[str, str],
) -> dict[str, Any]:
    """
    A lineup's figures against `starter_hand`; every figure the split lacks is None.

    The scope, the summary label and the recent-form label say there is a split, so they exist only when
    the lineup has a figure (DATA_CONTRACT rule 3): a split with no OPS, K% or BB% is no split.
    """

    # A lineup has a split only against L or R. Against a switch pitcher ("S") or an unknown hand it has none: no label, no
    # figure, no scope. It used to read the right-handed split for him under the label "SHP" (F11, D38).
    hand = starter_hand if starter_hand in ("L", "R") else None
    profile: dict[str, Any] = {
        "summary_label": None,
        "vs_pitcher_hand": f"{hand}HP" if hand else None,
        "ops_vs_hand": None,
        "k_rate_vs_hand": None,
        "bb_rate_vs_hand": None,
        "recent_form": None,
        "scope": None,
    }
    if hand is None:
        return profile
    split = (splits or {}).get("vl" if hand == "L" else "vr", {})
    figures = {
        "ops_vs_hand": _format_ops(split.get("ops")),
        "k_rate_vs_hand": _format_pct(split.get("k_rate")),
        "bb_rate_vs_hand": _format_pct(split.get("bb_rate")),
    }
    if any(value is not None for value in figures.values()):
        profile.update(figures)
        profile["summary_label"] = f"Real season split vs {hand}HP"
        profile["recent_form"] = "Season split"
        profile["scope"] = scope
    return profile


PITCH_DATA_FETCHED = "fetched_snapshot"
PITCH_DATA_UNAVAILABLE = "unavailable"  # the word `sample.rates.source` uses for a figure that was not given


def confidence_note(matchup_id: str, fetched_date: str, starters: dict[str, Any]) -> dict[str, Any]:
    """
    The confidence block of a live matchup. `pitch_data_status` is computed: `fetched_snapshot` when at
    least one starter has a pitch on record, `unavailable` when none has (DATA_CONTRACT, F1).
    """

    pitched = any(labels.has_pitch_data(starter) for starter in starters.values())
    return {
        "level": "fetched_snapshot",
        "lineup_status": "probable_pitchers",
        "pitch_data_status": PITCH_DATA_FETCHED if pitched else PITCH_DATA_UNAVAILABLE,
        "notes": [generator_catalog()("generator.confidence.live_note", date=fetched_date, matchup_id=matchup_id)],
    }


def _format_ops(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("0."):
            return stripped[1:]
        return stripped
    return f"{float(value):.3f}".replace("0.", ".", 1)


def _format_pct(value: Any) -> str | None:
    if value is None:
        return None
    return f"{float(value):.1f}%"
