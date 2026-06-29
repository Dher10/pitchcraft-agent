"""Rule-based Matchup Analyst Agent."""

from __future__ import annotations

from typing import Any


def run(matchup_packet: dict[str, Any]) -> dict[str, Any]:
    """Analyze a matchup packet and return deterministic structured findings."""

    starters = matchup_packet["starters"]
    teams = matchup_packet["teams"]
    away_starter = starters["away_starter"]
    home_starter = starters["home_starter"]
    home_team = teams["home"]
    away_team = teams["away"]

    away_strengths, away_risks = _starter_findings(away_starter)
    home_strengths, home_risks = _starter_findings(home_starter)
    pressure_points = _lineup_pressure_points(matchup_packet)

    away_profile = away_starter["pitching_profile"]
    home_profile = home_starter["pitching_profile"]
    away_style = _style_description(away_profile)
    home_style = _style_description(home_profile)

    three_things = [
        f"Can {away_starter['name']} land the {_pitch_short_name(away_profile['putaway_pitch']).lower()} early in counts?",
        f"Can {home_starter['name']} keep the ball {_location_goal(home_profile['primary_pitch'])}?",
        "Which lineup forces more deep counts by the third inning?",
    ]

    away_pressure = pressure_points[home_team["id"]][0] if pressure_points[home_team["id"]] else "applies consistent pressure"
    away_vs_home = (
        f"{away_starter['name']}'s {_pitch_short_name(away_profile['primary_pitch']).lower()}-"
        f"{_pitch_short_name(away_profile['putaway_pitch']).lower()} combination gives him "
        f"{away_profile['swing_miss_label'].lower()}, but the opposing lineup {away_pressure}."
    )

    home_pressure = pressure_points[away_team["id"]][0] if pressure_points[away_team["id"]] else "applies consistent pressure"
    home_vs_away = (
        f"{home_starter['name']} needs to {_command_note(home_profile['command_label'])} and use the "
        f"{_pitch_short_name(home_profile['putaway_pitch']).lower()} to {_contact_note(home_profile['contact_risk_label'])}. "
        f"His margin is {home_profile['contact_risk_label'].lower()} against a lineup with "
        f"{away_team['offense_profile']['ops_vs_hand']} OPS; the pressure point is that the opposing lineup "
        f"{home_pressure}."
    )

    return {
        "away_starter_strengths": away_strengths,
        "away_starter_risks": away_risks,
        "home_starter_strengths": home_strengths,
        "home_starter_risks": home_risks,
        "lineup_pressure_points": [
            point
            for team_points in pressure_points.values()
            for point in team_points
        ],
        "lineup_pressure_points_by_team": pressure_points,
        "three_things_to_watch": three_things,
        "matchup_headline": f"{away_profile['style_label']} against {home_profile['style_label']}",
        "away_vs_home_offense": away_vs_home,
        "home_vs_away_offense": home_vs_away,
        "matchup_summary": (
            f"This matchup features {away_profile['style_label']} against {home_profile['style_label']}. "
            "The scouting note is matchup fit, with each pressure point shaping what to watch."
        ),
        "away_style": away_style,
        "home_style": home_style,
    }


def _starter_findings(starter: dict[str, Any]) -> tuple[list[str], list[str]]:
    profile = starter["pitching_profile"]
    recent = starter["recent_form"]["label"].lower()
    strengths: list[str] = []
    risks: list[str] = []

    swing_miss = profile["swing_miss_label"].lower()
    command = profile["command_label"].lower()
    contact = profile["contact_risk_label"].lower()

    if "above-average" in swing_miss:
        strengths.append("Above-average swing-and-miss ability")
    if "plus" in command or "solid" in command:
        strengths.append(f"{profile['command_label']} supports strike-zone control")
    if "below-average" in command:
        risks.append("Below-average command can create deep-count traffic")
    if "elevated" in contact or "high" in contact:
        risks.append("Contact risk can turn missed spots into damage")
    if "low" in contact:
        strengths.append("Low contact-risk profile supports contact management")
    if "volatile" in recent:
        risks.append("Recent form has been volatile")
    if "trending" in recent:
        strengths.append("Recent form is trending in the right direction")

    strengths.append(_style_description(profile))
    return strengths, risks


def _lineup_pressure_points(matchup_packet: dict[str, Any]) -> dict[str, list[str]]:
    teams = matchup_packet["teams"]
    points: dict[str, list[str]] = {}
    for side in ("home", "away"):
        team = teams[side]
        offense = team["offense_profile"]
        team_points: list[str] = []
        if _rate_value(offense["ops_vs_hand"]) > 0.750:
            team_points.append("has strong OPS against this pitcher's hand")
        if _rate_value(offense["k_rate_vs_hand"]) > 22:
            team_points.append("has elevated swing-and-miss risk")
        if _rate_value(offense["bb_rate_vs_hand"]) > 9:
            team_points.append("draws walks at an above-average rate")
        points[team["id"]] = team_points
    return points


def _rate_value(raw_value: str) -> float:
    return float(raw_value.replace("%", ""))


def _style_description(profile: dict[str, Any]) -> str:
    return (
        f"{profile['primary_pitch']} to set up, "
        f"{profile['putaway_pitch']} to finish"
    )


def _location_goal(primary_pitch: str) -> str:
    primary = primary_pitch.lower()
    if "sinker" in primary or "changeup" in primary:
        return "low"
    return "in the zone"


def _command_note(command_label: str) -> str:
    command = command_label.lower()
    if "plus" in command or "solid" in command:
        return "keep the command edge visible"
    if "below-average" in command:
        return "avoid letting below-average command turn into free passes"
    return "avoid predictable counts"


def _contact_note(contact_risk_label: str) -> str:
    contact = contact_risk_label.lower()
    if "low" in contact:
        return "manage contact"
    if "elevated" in contact or "high" in contact:
        return "limit hard contact"
    return "disrupt timing"


def _pitch_short_name(pitch: str) -> str:
    return pitch.replace(" fastball", "")

