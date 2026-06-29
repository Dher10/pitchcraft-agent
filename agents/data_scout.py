"""Data Scout Agent for cached PitchCraft matchup inputs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SECTION_CHECKS = (
    ("game", ("game",)),
    ("teams", ("teams",)),
    ("away_starter", ("starters", "away_starter")),
    ("home_starter", ("starters", "home_starter")),
    ("pitch_mix", ("charts", "pitch_mix")),
    ("velocity", ("charts", "velocity_by_pitch")),
    ("strength", ("charts", "strength_profile")),
    ("pitch_locations", ("pitch_locations",)),
)


def run(matchup_input: dict[str, Any]) -> dict[str, Any]:
    """
    Receive raw matchup input and return a full matchup packet.

    The packet passes through the matchup data, adds section availability flags,
    and supplies deterministic cached-demo confidence metadata.
    """

    packet = deepcopy(matchup_input)
    status = packet.get("status")
    lineup_status = "final" if status == "final" else "not_required_for_demo"
    notes = (
        [
            "Completed demo game used to show the postgame grading flow.",
            "Grades are PitchCraft-specific and explainable, not official metrics.",
        ]
        if status == "final"
        else [
            "This demo uses cached data to guarantee stable judging.",
            "Live data integration can be added after the capstone.",
        ]
    )

    packet["availability"] = {
        label: _has_path(packet, path)
        for label, path in SECTION_CHECKS
    }
    packet["data_confidence"] = {
        "level": "demo_cached",
        "lineup_status": lineup_status,
        "pitch_data_status": "cached",
        "notes": notes,
    }
    return packet


def _has_path(value: dict[str, Any], path: tuple[str, ...]) -> bool:
    current: Any = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    return current is not None

