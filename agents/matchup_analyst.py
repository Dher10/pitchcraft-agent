"""Rule-based Matchup Analyst Agent."""

from __future__ import annotations

from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog, catalog_for
from data_pipeline import labels


def run(matchup_packet: dict[str, Any], language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Analyze a matchup packet and return deterministic structured findings, in `language`."""

    t = catalog_for(language)
    starters = matchup_packet["starters"]
    teams = matchup_packet["teams"]
    away_starter = starters["away_starter"]
    home_starter = starters["home_starter"]
    home_team = teams["home"]
    away_team = teams["away"]

    away_strengths, away_risks = _starter_findings(t, away_starter)
    home_strengths, home_risks = _starter_findings(t, home_starter)
    pressure_points = _lineup_pressure_points(t, matchup_packet)

    away_profile = away_starter["pitching_profile"]
    home_profile = home_starter["pitching_profile"]
    away_style = _style_description(t, away_profile)
    home_style = _style_description(t, home_profile)

    away_sample = away_starter.get("sample")
    home_sample = home_starter.get("sample")

    three_things = [
        (
            t("analyst.watch.ahead", name=away_starter["name"])
            if _arsenal_limited(away_sample) or not labels.pitch_named(away_profile["putaway_pitch"])
            else t(
                "analyst.watch.land",
                name=away_starter["name"],
                putaway=_pitch_short_name(away_profile["putaway_pitch"]).lower(),
            )
        ),
        (
            t("analyst.watch.efficient", name=home_starter["name"])
            if _arsenal_limited(home_sample)
            else t(
                "analyst.watch.keep",
                name=home_starter["name"],
                goal=_location_goal(t, home_profile["primary_pitch"]),
            )
        ),
        t("analyst.watch.deep"),
    ]

    if away_sample is None:
        away_vs_home = t(
            "analyst.demo.away_read",
            name=away_starter["name"],
            primary=_pitch_short_name(away_profile["primary_pitch"]).lower(),
            putaway=_pitch_short_name(away_profile["putaway_pitch"]).lower(),
            swing_miss=_safe_label(away_profile.get("swing_miss_label"), t("analyst.fallback.swing_path")).lower(),
            offense=_offense_read(t, home_team, away_starter),
        )
    else:
        away_vs_home = f"{_live_pitcher_read(t, away_starter, away_sample)} {_offense_read(t, home_team, away_starter)}"

    if home_sample is None:
        home_vs_away = t(
            "analyst.demo.home_read",
            name=home_starter["name"],
            command_note=_command_note(t, home_profile["command_label"]),
            putaway=_pitch_short_name(home_profile["putaway_pitch"]).lower(),
            contact_note=_contact_note(t, home_profile["contact_risk_label"]),
            offense=_offense_read(t, away_team, home_starter),
        )
    else:
        home_vs_away = f"{_live_pitcher_read(t, home_starter, home_sample)} {_offense_read(t, away_team, home_starter)}"

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
        "matchup_headline": _matchup_label(t, away_starter, home_starter),
        "away_vs_home_offense": away_vs_home,
        "home_vs_away_offense": home_vs_away,
        "matchup_summary": t("analyst.summary", label=_matchup_label(t, away_starter, home_starter)),
        "away_data_notes": _data_notes(t, away_starter["name"], away_sample) if away_sample else [],
        "home_data_notes": _data_notes(t, home_starter["name"], home_sample) if home_sample else [],
        "scope_notes": _scope_notes(t, matchup_packet),
        "away_style": away_style,
        "home_style": home_style,
    }


def _offense_read(t: Catalog, team: dict[str, Any], starter: dict[str, Any]) -> str:
    offense = team["offense_profile"]
    hand = offense.get("vs_pitcher_hand") or _throws_label(starter.get("throws", "R"))
    starter_name = starter["name"]
    ops_text = offense.get("ops_vs_hand")
    ops = _optional_rate(ops_text)
    k_rate = _optional_rate(offense.get("k_rate_vs_hand"))
    bb_rate = _optional_rate(offense.get("bb_rate_vs_hand"))

    if ops is None:
        read = t("analyst.offense.unavailable", hand=hand)
    elif ops >= 0.750:
        read = t("analyst.offense.strong", hand=hand, ops=ops_text, name=starter_name)
    elif ops >= 0.700:
        read = t("analyst.offense.average", hand=hand, ops=ops_text)
    else:
        read = t("analyst.offense.weak", hand=hand, ops=ops_text, name=starter_name)

    notes = []
    if k_rate is not None and k_rate >= 23:
        notes.append(t("analyst.offense.note_strikeouts"))
    if bb_rate is not None and bb_rate >= 9:
        notes.append(t("analyst.offense.note_walks", name=starter_name))
    if notes:
        read = t("analyst.offense.with_notes", read=read, notes="; ".join(notes))
    return read


def _throws_label(raw_hand: str) -> str:
    hand = raw_hand[:1] if raw_hand else "R"
    return f"{hand}HP"


def _safe_label(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    label = str(value).strip()
    if not label or label.lower() == labels.LEGACY_PLACEHOLDER_LABEL:
        return fallback
    return label


def _starter_findings(t: Catalog, starter: dict[str, Any]) -> tuple[list[str], list[str]]:
    sample = starter.get("sample")
    if sample is not None:
        return _live_starter_findings(t, starter, sample)
    profile = starter["pitching_profile"]
    recent = ((starter.get("recent_form") or {}).get("label") or "").lower()
    strengths: list[str] = []
    risks: list[str] = []

    swing_miss_label = _safe_label(profile.get("swing_miss_label"), t("analyst.fallback.swing_data"))
    command_label = _safe_label(profile.get("command_label"), t("analyst.fallback.command"))
    contact_label = _safe_label(profile.get("contact_risk_label"), t("analyst.fallback.contact"))
    swing_miss = swing_miss_label.lower()
    command = command_label.lower()
    contact = contact_label.lower()

    if "above-average" in swing_miss:
        strengths.append(t("analyst.strength.swing_miss"))
    if "plus" in command or "solid" in command:
        strengths.append(t("analyst.strength.command", label=command_label))
    if "below-average" in command:
        risks.append(t("analyst.risk.command"))
    if "elevated" in contact or "high" in contact:
        risks.append(t("analyst.risk.contact"))
    if "low" in contact:
        strengths.append(t("analyst.strength.contact"))
    if "volatile" in recent:
        risks.append(t("analyst.risk.volatile"))
    if "trending" in recent:
        strengths.append(t("analyst.strength.trending"))

    strengths.append(_style_description(t, profile))
    return strengths, risks


def _arsenal_limited(sample: dict[str, Any] | None) -> bool:
    return bool(sample and sample["limited"]["arsenal"])


def _matchup_label(t: Catalog, away: dict[str, Any], home: dict[str, Any]) -> str:
    """Headline subject: the two styles, or the names when an arsenal is too thin to describe."""

    if _arsenal_limited(away.get("sample")) or _arsenal_limited(home.get("sample")):
        return t("analyst.label.against", away=away["name"], home=home["name"])
    return t(
        "analyst.label.against",
        away=away["pitching_profile"]["style_label"],
        home=home["pitching_profile"]["style_label"],
    )


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _live_starter_findings(
    t: Catalog, starter: dict[str, Any], sample: dict[str, Any]
) -> tuple[list[str], list[str]]:
    """Strengths and risks for a live starter: only from labels that cleared their sample threshold."""

    profile = starter["pitching_profile"]
    strengths: list[str] = []
    risks: list[str] = []
    swing = profile.get("swing_miss_label")
    command = profile.get("command_label")
    if swing and "above-average" in swing.lower():
        strengths.append(t("analyst.strength.swing_miss"))
    if command and "solid" in command.lower():
        strengths.append(t("analyst.strength.command", label=command))
    if command and "below-average" in command.lower():
        risks.append(t("analyst.risk.command"))
    if not sample["limited"]["arsenal"]:
        strengths.append(_style_description(t, profile))
    return strengths, risks


def _live_pitcher_read(t: Catalog, starter: dict[str, Any], sample: dict[str, Any]) -> str:
    """What the data supports about a live starter, plus what it does not."""

    name = starter["name"]
    profile = starter["pitching_profile"]
    qualifier = t("analyst.read.qualifier") if labels.scopes_differ(sample) else ""
    parts: list[str] = []
    if not sample["limited"]["arsenal"]:
        primary = _pitch_short_name(profile["primary_pitch"]).lower()
        if labels.pitch_named(profile["putaway_pitch"]):
            parts.append(
                t(
                    "analyst.read.combination",
                    name=name,
                    primary=primary,
                    putaway=_pitch_short_name(profile["putaway_pitch"]).lower(),
                )
            )
        else:
            parts.append(t("analyst.read.mainly", name=name, primary=primary))
    # Name the pitcher in the first rate sentence unless the arsenal sentence already did.
    subject = t("analyst.read.he") if parts else name
    for label in (profile.get("swing_miss_label"), profile.get("command_label")):
        if label:
            parts.append(t("analyst.read.shows", subject=subject, label=_lower_first(label), qualifier=qualifier))
            subject = t("analyst.read.he")
    parts.extend(_data_notes(t, name, sample))
    return " ".join(parts)


def _data_notes(t: Catalog, name: str, sample: dict[str, Any]) -> list[str]:
    """One sentence per limited dimension, and the contact-risk count (never a rate label)."""

    needed = sample["thresholds"]
    rates = sample["rates"]
    limited = sample["limited"]
    batters = rates["batters_faced"]
    have_batters = t("analyst.have.batters", count=batters) if batters else t("analyst.have.no_batters")
    notes: list[str] = []
    if limited["arsenal"]:
        pitches = sample["arsenal"]["pitches"]
        have = t("analyst.have.pitches", count=pitches) if pitches else t("analyst.have.no_pitches")
        notes.append(t("analyst.data.arsenal", name=name, have=have, needed=needed["arsenal"]))
    if limited["strikeout"]:
        notes.append(t("analyst.data.strikeout", name=name, have=have_batters, needed=needed["strikeout"]))
    if limited["control"]:
        notes.append(t("analyst.data.control", name=name, have=have_batters, needed=needed["control"]))
    home_runs = rates["home_runs"]
    if home_runs is not None and batters:
        notes.append(
            t("analyst.data.contact", name=name, home_runs=t.count("home_run", home_runs), batters=batters)
        )
    else:
        notes.append(t("analyst.data.no_home_runs", name=name))
    return notes


def _names(t: Catalog, names: list[str]) -> str:
    return names[0] if len(names) == 1 else t("analyst.list_and", first=names[0], second=names[1])


def _scope_notes(t: Catalog, packet: dict[str, Any]) -> list[str]:
    """Which games each group of figures covers, so they are never read as one sample."""

    notes: list[str] = []
    groups: dict[tuple[bool, str, str, str], list[str]] = {}
    for slot in ("away_starter", "home_starter"):
        starter = packet["starters"][slot]
        sample = starter.get("sample")
        if sample is None:
            continue
        key = (
            labels.scopes_differ(sample),
            sample["rates"]["scope"]["label"],
            sample["arsenal"]["scope"]["label"],
            _available_figures(t, starter, sample),
        )
        groups.setdefault(key, []).append(starter["name"])
    for (differ, rates_label, arsenal_label, figures), names in groups.items():
        who = _names(t, names)
        if differ:
            # Only figures that exist are named: "N/A" is never a claim.
            season = (
                t("analyst.scope.season_figures", figures=figures, label=rates_label)
                if figures
                else t("analyst.scope.no_season_figures")
            )
            notes.append(t("analyst.scope.differ", who=who, season=season, arsenal=arsenal_label))
        else:
            notes.append(t("analyst.scope.same", who=who, label=rates_label))
    offense_labels = list(
        dict.fromkeys(
            scope["label"]
            for side in ("home", "away")
            if (scope := packet["teams"][side]["offense_profile"].get("scope"))
        )
    )
    for label in offense_labels:
        notes.append(t("analyst.scope.offense", label=label))
    return notes


def _available_figures(t: Catalog, starter: dict[str, Any], sample: dict[str, Any]) -> str:
    """The season figures a starter really has, as a phrase ("ERA, innings and the ... counts")."""

    summary = starter.get("season_summary") or {}
    names = [
        t(f"analyst.figure.{key}")
        for key in ("era", "whip", "innings")
        if labels.is_available(summary.get(key))
    ]
    rates = sample["rates"]
    if any(rates[key] is not None for key in ("strikeouts", "walks", "home_runs")):
        names.append(t("analyst.figure.counts"))
    if len(names) > 1:
        return t("analyst.figure.list_and", head=", ".join(names[:-1]), last=names[-1])
    return names[0] if names else ""


def _lineup_pressure_points(t: Catalog, matchup_packet: dict[str, Any]) -> dict[str, list[str]]:
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
            team_points.append(t("analyst.pressure.ops"))
        if k_rate is not None and k_rate > 22:
            team_points.append(t("analyst.pressure.strikeouts"))
        if bb_rate is not None and bb_rate > 9:
            team_points.append(t("analyst.pressure.walks"))
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


def _style_description(t: Catalog, profile: dict[str, Any]) -> str:
    if not labels.pitch_named(profile["putaway_pitch"]):
        return t("analyst.style.single", primary=profile["primary_pitch"])
    return t("analyst.style.pair", primary=profile["primary_pitch"], putaway=profile["putaway_pitch"])


def _location_goal(t: Catalog, primary_pitch: str) -> str:
    primary = primary_pitch.lower()
    if "sinker" in primary or "changeup" in primary:
        return t("analyst.goal.low")
    return t("analyst.goal.zone")


def _command_note(t: Catalog, command_label: str) -> str:
    command = _safe_label(command_label, t("analyst.fallback.command")).lower()
    if "plus" in command or "solid" in command:
        return t("analyst.command_note.edge")
    if "below-average" in command:
        return t("analyst.command_note.below")
    return t("analyst.command_note.default")


def _contact_note(t: Catalog, contact_risk_label: str) -> str:
    contact = _safe_label(contact_risk_label, t("analyst.fallback.contact")).lower()
    if "low" in contact:
        return t("analyst.contact_note.low")
    if "elevated" in contact or "high" in contact:
        return t("analyst.contact_note.high")
    return t("analyst.contact_note.default")


def _pitch_short_name(pitch: str) -> str:
    return pitch.replace(labels.FASTBALL_SUFFIX, "")
