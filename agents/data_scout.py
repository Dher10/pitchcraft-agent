"""Data Scout Agent for cached PitchCraft matchup inputs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents.language import DEFAULT_LANGUAGE, catalog_for


SECTION_CHECKS = (
    ("game", ("game",)),
    ("teams", ("teams",)),
    ("away_starter", ("starters", "away_starter")),
    ("home_starter", ("starters", "home_starter")),
    ("pitch_mix", ("charts", "pitch_mix")),
    ("velocity", ("charts", "velocity_by_pitch")),
    ("strength", ("charts", "strength_profile")),
    ("pitch_movement", ("charts", "pitch_movement")),
    ("pitch_locations", ("pitch_locations",)),
)


def run(matchup_input: dict[str, Any], language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """
    Receive raw matchup input and return a full matchup packet.

    The packet passes through the matchup data, adds section availability flags,
    and supplies deterministic cached-demo confidence metadata, with its notes in
    `language`.
    """

    t = catalog_for(language)
    packet = deepcopy(matchup_input)
    status = packet.get("status")
    existing_confidence = packet.get("data_confidence")
    if isinstance(existing_confidence, dict) and existing_confidence.get("level") == "fetched_snapshot":
        data_confidence = existing_confidence
    else:
        lineup_status = "final" if status == "final" else "not_required_for_demo"
        notes = (
            [t("scout.final.note_1"), t("scout.final.note_2")]
            if status == "final"
            else [t("scout.demo.note_1"), t("scout.demo.note_2")]
        )
        data_confidence = {
            "level": "demo_cached",
            "lineup_status": lineup_status,
            "pitch_data_status": "cached",
            "notes": notes,
        }

    packet["availability"] = {
        label: _has_path(packet, path)
        for label, path in SECTION_CHECKS
    }
    packet["data_confidence"] = data_confidence
    return packet


def _has_path(value: dict[str, Any], path: tuple[str, ...]) -> bool:
    current: Any = value
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return False
        current = current[key]
    return current is not None

