"""Rule-based Matchup Analyst Agent."""

from __future__ import annotations

from typing import Any

from data_pipeline import labels


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

    away_sample = away_starter.get("sample")
    home_sample = home_starter.get("sample")

    three_things = [
        (
            f"Can {away_starter['name']} stay ahead of hitters early in counts?"
            if _arsenal_limited(away_sample) or not labels.pitch_named(away_profile["putaway_pitch"])
            else f"Can {away_starter['name']} land the {_pitch_short_name(away_profile['putaway_pitch']).lower()} early in counts?"
        ),
        (
            f"Can {home_starter['name']} work efficiently through the lineup?"
            if _arsenal_limited(home_sample)
            else f"Can {home_starter['name']} keep the ball {_location_goal(home_profile['primary_pitch'])}?"
        ),
        "Which lineup forces more deep counts by the third inning?",
    ]

    if away_sample is None:
        away_vs_home = (
            f"{away_starter['name']}'s {_pitch_short_name(away_profile['primary_pitch']).lower()}-"
            f"{_pitch_short_name(away_profile['putaway_pitch']).lower()} combination gives him "
            f"{_safe_label(away_profile.get('swing_miss_label'), 'a defined swing-and-miss path').lower()}. "
            f"{_offense_read(home_team, away_starter)}"
        )
    else:
        away_vs_home = f"{_live_pitcher_read(away_starter, away_sample)} {_offense_read(home_team, away_starter)}"

    if home_sample is None:
        home_vs_away = (
            f"{home_starter['name']} needs to {_command_note(home_profile['command_label'])} and use the "
            f"{_pitch_short_name(home_profile['putaway_pitch']).lower()} to {_contact_note(home_profile['contact_risk_label'])}. "
            f"{_offense_read(away_team, home_starter)}"
        )
    else:
        home_vs_away = f"{_live_pitcher_read(home_starter, home_sample)} {_offense_read(away_team, home_starter)}"

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
        "matchup_headline": _matchup_label(away_starter, home_starter),
        "away_vs_home_offense": away_vs_home,
        "home_vs_away_offense": home_vs_away,
        "matchup_summary": (
            f"This matchup features {_matchup_label(away_starter, home_starter)}. "
            "The scouting note is matchup fit, with each pressure point shaping what to watch."
        ),
        "away_data_notes": _data_notes(away_starter["name"], away_sample) if away_sample else [],
        "home_data_notes": _data_notes(home_starter["name"], home_sample) if home_sample else [],
        "scope_notes": _scope_notes(matchup_packet),
        "away_style": away_style,
        "home_style": home_style,
    }


def _offense_read(team: dict[str, Any], starter: dict[str, Any]) -> str:
    offense = team["offense_profile"]
    hand = offense.get("vs_pitcher_hand") or _throws_label(starter.get("throws", "R"))
    starter_name = starter["name"]
    ops_text = offense.get("ops_vs_hand")
    ops = _optional_rate(ops_text)
    k_rate = _optional_rate(offense.get("k_rate_vs_hand"))
    bb_rate = _optional_rate(offense.get("bb_rate_vs_hand"))

    if ops is None:
        read = f"Season offense data against {hand} pitching is not available for this lineup yet."
    elif ops >= 0.750:
        read = (
            f"This lineup hits well against {hand} pitching ({ops_text} OPS), "
            f"so {starter_name} cannot live over the middle."
        )
    elif ops >= 0.700:
        read = (
            f"This lineup is roughly average against {hand} pitching ({ops_text} OPS), "
            "with no glaring weakness to attack."
        )
    else:
        read = (
            f"This lineup has struggled against {hand} pitching ({ops_text} OPS), "
            f"which gives {starter_name} an edge if he gets ahead."
        )

    notes = []
    if k_rate is not None and k_rate >= 23:
        notes.append("They also strike out often, which favors a swing-and-miss approach")
    if bb_rate is not None and bb_rate >= 9:
        notes.append(f"They draw walks at an above-average rate, so {starter_name} needs efficient strikes")
    if notes:
        read = f"{read} {'; '.join(notes)}."
    return read


def _throws_label(raw_hand: str) -> str:
    hand = raw_hand[:1] if raw_hand else "R"
    return f"{hand}HP"


def _safe_label(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    label = str(value).strip()
    if not label or label.lower() == "see live data":
        return fallback
    return label


def _starter_findings(starter: dict[str, Any]) -> tuple[list[str], list[str]]:
    sample = starter.get("sample")
    if sample is not None:
        return _live_starter_findings(starter, sample)
    profile = starter["pitching_profile"]
    recent = ((starter.get("recent_form") or {}).get("label") or "").lower()
    strengths: list[str] = []
    risks: list[str] = []

    swing_miss_label = _safe_label(profile.get("swing_miss_label"), "Limited swing-and-miss data available")
    command_label = _safe_label(profile.get("command_label"), "Average command this season")
    contact_label = _safe_label(profile.get("contact_risk_label"), "Moderate contact risk")
    swing_miss = swing_miss_label.lower()
    command = command_label.lower()
    contact = contact_label.lower()

    if "above-average" in swing_miss:
        strengths.append("Above-average swing-and-miss ability")
    if "plus" in command or "solid" in command:
        strengths.append(f"{command_label} supports strike-zone control")
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


def _arsenal_limited(sample: dict[str, Any] | None) -> bool:
    return bool(sample and sample["limited"]["arsenal"])


def _matchup_label(away: dict[str, Any], home: dict[str, Any]) -> str:
    """Headline subject: the two styles, or the names when an arsenal is too thin to describe."""

    if _arsenal_limited(away.get("sample")) or _arsenal_limited(home.get("sample")):
        return f"{away['name']} against {home['name']}"
    return f"{away['pitching_profile']['style_label']} against {home['pitching_profile']['style_label']}"


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _live_starter_findings(
    starter: dict[str, Any], sample: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Strengths and risks for a live starter: only from labels that cleared their sample threshold."""

    profile = starter["pitching_profile"]
    strengths: list[str] = []
    risks: list[str] = []
    swing = profile.get("swing_miss_label")
    command = profile.get("command_label")
    if swing and "above-average" in swing.lower():
        strengths.append("Above-average swing-and-miss ability")
    if command and "solid" in command.lower():
        strengths.append(f"{command} supports strike-zone control")
    if command and "below-average" in command.lower():
        risks.append("Below-average command can create deep-count traffic")
    if not sample["limited"]["arsenal"]:
        strengths.append(_style_description(profile))
    return strengths, risks


def _live_pitcher_read(starter: dict[str, Any], sample: dict[str, Any]) -> str:
    """What the data supports about a live starter, plus what it does not."""

    name = starter["name"]
    profile = starter["pitching_profile"]
    qualifier = " (regular-season rates)" if labels.scopes_differ(sample) else ""
    parts: list[str] = []
    if not sample["limited"]["arsenal"]:
        primary = _pitch_short_name(profile["primary_pitch"]).lower()
        if labels.pitch_named(profile["putaway_pitch"]):
            parts.append(
                f"{name} works off a {primary}-"
                f"{_pitch_short_name(profile['putaway_pitch']).lower()} combination."
            )
        else:
            parts.append(f"{name} works mainly off a {primary}.")
    # Name the pitcher in the first rate sentence unless the arsenal sentence already did.
    subject = "He" if parts else name
    for label in (profile.get("swing_miss_label"), profile.get("command_label")):
        if label:
            parts.append(f"{subject} shows {_lower_first(label)}{qualifier}.")
            subject = "He"
    parts.extend(_data_notes(name, sample))
    return " ".join(parts)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _data_notes(name: str, sample: dict[str, Any]) -> list[str]:
    """One sentence per limited dimension, and the contact-risk count (never a rate label)."""

    needed = sample["thresholds"]
    rates = sample["rates"]
    limited = sample["limited"]
    batters = rates["batters_faced"]
    have_batters = f"{batters} batters faced" if batters else "no batters faced on record"
    notes: list[str] = []
    if limited["arsenal"]:
        pitches = sample["arsenal"]["pitches"]
        have = f"{pitches} pitches" if pitches else "no pitches on record"
        notes.append(
            f"{name}'s arsenal data is limited ({have}; {needed['arsenal']} needed), "
            "so this report makes no arsenal claim for him."
        )
    if limited["strikeout"]:
        notes.append(
            f"Strikeout data for {name} is limited ({have_batters}; {needed['strikeout']} needed), "
            "so no swing-and-miss claim is made."
        )
    if limited["control"]:
        notes.append(
            f"Control data for {name} is limited ({have_batters}; {needed['control']} needed), "
            "so no command claim is made."
        )
    home_runs = rates["home_runs"]
    if home_runs is not None and batters:
        notes.append(
            f"{name} has allowed {_plural(home_runs, 'home run')} over {batters} batters faced; "
            "no contact-risk rating is given because a home-run rate needs a far larger sample."
        )
    else:
        notes.append(f"Home runs allowed are not available for {name}.")
    return notes


def _scope_notes(packet: dict[str, Any]) -> list[str]:
    """Which games each group of figures covers, so they are never read as one sample."""

    notes: list[str] = []
    groups: dict[tuple[bool, str, str], list[str]] = {}
    for slot in ("away_starter", "home_starter"):
        starter = packet["starters"][slot]
        sample = starter.get("sample")
        if sample is None:
            continue
        key = (
            labels.scopes_differ(sample),
            sample["rates"]["scope"]["label"],
            sample["arsenal"]["scope"]["label"],
            _available_figures(starter, sample),
        )
        groups.setdefault(key, []).append(starter["name"])
    for (differ, rates_label, arsenal_label, figures), names in groups.items():
        who = " and ".join(names)
        if differ:
            # Only figures that exist are named: "N/A" is never a claim.
            season = f"{figures} cover the {rates_label}; " if figures else "no season figures are available; "
            notes.append(
                f"{who}: {season}the pitch mix, velocity and movement cover the {arsenal_label}. "
                "They are different samples."
            )
        else:
            notes.append(f"{who}: all pitcher figures cover the {rates_label}.")
    offense_labels = list(
        dict.fromkeys(
            scope["label"]
            for side in ("home", "away")
            if (scope := packet["teams"][side]["offense_profile"].get("scope"))
        )
    )
    for label in offense_labels:
        notes.append(f"Team offense splits cover the {label}.")
    return notes


def _available_figures(starter: dict[str, Any], sample: dict[str, Any]) -> str:
    """The season figures a starter really has, as a phrase ("ERA, innings and the ... counts")."""

    summary = starter.get("season_summary") or {}
    names = [
        name
        for name, key in (("ERA", "era"), ("WHIP", "whip"), ("innings", "innings"))
        if labels.is_available(summary.get(key))
    ]
    rates = sample["rates"]
    if any(rates[key] is not None for key in ("strikeouts", "walks", "home_runs")):
        names.append("the strikeout, walk and home-run counts")
    if len(names) > 1:
        return f"{', '.join(names[:-1])} and {names[-1]}"
    return names[0] if names else ""


def _lineup_pressure_points(matchup_packet: dict[str, Any]) -> dict[str, list[str]]:
    teams = matchup_packet["teams"]
    points: dict[str, list[str]] = {}
    for side in ("home", "away"):
        team = teams[side]
        offense = team["offense_profile"]
        team_points: list[str] = []
        ops = _optional_rate(offense.get("ops_vs_hand"))
        k_rate = _optional_rate(offense.get("k_rate_vs_hand"))
        bb_rate = _optional_rate(offense.get("bb_rate_vs_hand"))
        if ops is not None and ops > 0.750:
            team_points.append("has strong OPS against this pitcher's hand")
        if k_rate is not None and k_rate > 22:
            team_points.append("has elevated swing-and-miss risk")
        if bb_rate is not None and bb_rate > 9:
            team_points.append("draws walks at an above-average rate")
        points[team["id"]] = team_points
    return points


def _optional_rate(raw_value: str | None) -> float | None:
    """A rate, or None when the value is unavailable (never parsed as zero)."""
    if raw_value is None:
        return None
    try:
        return float(str(raw_value).replace("%", ""))
    except ValueError:
        return None


def _style_description(profile: dict[str, Any]) -> str:
    if not labels.pitch_named(profile["putaway_pitch"]):
        return f"{profile['primary_pitch']} as the main pitch"
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
    command = _safe_label(command_label, "Average command this season").lower()
    if "plus" in command or "solid" in command:
        return "keep the command edge visible"
    if "below-average" in command:
        return "avoid letting below-average command turn into free passes"
    return "avoid predictable counts"


def _contact_note(contact_risk_label: str) -> str:
    contact = _safe_label(contact_risk_label, "Moderate contact risk").lower()
    if "low" in contact:
        return "manage contact"
    if "elevated" in contact or "high" in contact:
        return "limit hard contact"
    return "disrupt timing"


def _pitch_short_name(pitch: str) -> str:
    return pitch.replace(" fastball", "")

