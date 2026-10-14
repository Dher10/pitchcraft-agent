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

    with t.subject("away_starter"):
        away_strengths, away_risks = _starter_findings(t, away_starter)
    with t.subject("home_starter"):
        home_strengths, home_risks = _starter_findings(t, home_starter)
    pressure_points = _lineup_pressure_points(t, matchup_packet)

    away_profile = away_starter["pitching_profile"]
    home_profile = home_starter["pitching_profile"]
    with t.subject("away_starter"):
        away_style = _style_description(t, away_profile)
    with t.subject("home_starter"):
        home_style = _style_description(t, home_profile)

    away_sample = away_starter.get("sample")
    home_sample = home_starter.get("sample")

    with t.subject("away_starter"):
        away_action = (
            t("analyst.watch.action.ahead")
            if _arsenal_limited(away_sample) or not labels.pitch_named(away_profile["putaway_pitch"])
            else t(
                "analyst.watch.action.land",
                putaway=_pitch_short_name(away_profile["putaway_pitch"]).lower(),
            )
        )
        away_watch = t("analyst.watch.question", name=away_starter["name"], action=away_action)
    with t.subject("home_starter"):
        home_action = (
            t("analyst.watch.action.efficient")
            if _arsenal_limited(home_sample)
            else t("analyst.watch.action.keep", goal=_location_goal(t, home_profile["primary_pitch"]))
        )
        home_watch = t("analyst.watch.question", name=home_starter["name"], action=home_action)
    three_things = [away_watch, home_watch, t("analyst.watch.deep")]

    with t.subject("away_starter"):
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
            away_vs_home = t.join(
                " ", [_live_pitcher_read(t, away_starter, away_sample), _offense_read(t, home_team, away_starter)]
            )

    with t.subject("home_starter"):
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
            home_vs_away = t.join(
                " ", [_live_pitcher_read(t, home_starter, home_sample), _offense_read(t, away_team, home_starter)]
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
        "matchup_headline": _matchup_label(t, away_starter, home_starter),
        "away_vs_home_offense": away_vs_home,
        "home_vs_away_offense": home_vs_away,
        "matchup_summary": t("analyst.summary", label=_matchup_label(t, away_starter, home_starter)),
        "away_data_notes": _subject_notes(t, "away_starter", away_starter["name"], away_sample),
        "home_data_notes": _subject_notes(t, "home_starter", home_starter["name"], home_sample),
        "scope_notes": _scope_notes(t, matchup_packet),
        "away_style": away_style,
        "home_style": home_style,
    }


def _subject_notes(t: Catalog, slot: str, name: str, sample: dict[str, Any] | None) -> list[str]:
    """The data notes of one starter, written as sentences about him."""

    if not sample:
        return []
    with t.subject(slot):
        return _data_notes(t, name, sample)


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
    elif ops >= labels.OFFENSE_OPS_STRONG:
        read = t("analyst.offense.strong", hand=hand, ops=ops_text, name=starter_name)
    elif ops >= 0.700:
        read = t("analyst.offense.average", hand=hand, ops=ops_text)
    else:
        read = t("analyst.offense.weak", hand=hand, ops=ops_text, name=starter_name)

    notes = []
    if k_rate is not None and k_rate >= labels.OFFENSE_K_NOTE_PCT:
        notes.append(t("analyst.offense.note_strikeouts"))
    if bb_rate is not None and bb_rate >= labels.OFFENSE_BB_NOTE_PCT:
        notes.append(t("analyst.offense.note_walks", name=starter_name))
    if notes:
        read = t("analyst.offense.with_notes", read=read, notes=t.join("; ", notes))
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
    qualifier = _rate_qualifier(t, starter)
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
    return t.join(" ", parts)


def _rate_qualifier(t: Catalog, starter: dict[str, Any]) -> str:
    """
    A rate claim ("shows above-average swing-and-miss") is made of the counts. When the groups of
    figures do not all cover the same games it says which games the counts cover.
    """

    counts = labels.figure_scopes(starter).get("counts")
    if counts is None or not labels.scopes_differ(starter):
        return ""
    if counts["kind"] == labels.SCOPE_REGULAR:
        return t("analyst.read.qualifier")
    return t("analyst.read.qualifier_both")


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
    groups: dict[tuple, list[str]] = {}
    for slot in ("away_starter", "home_starter"):
        starter = packet["starters"][slot]
        if starter.get("sample") is None:
            continue
        groups.setdefault(_scope_note_plan(t, starter), []).append(starter["name"])
    for plan, names in groups.items():
        who = _names(t, names)
        mode = plan[0]
        if mode == "none":
            notes.append(t("analyst.scope.none", who=who))
        elif mode == "same":
            notes.append(t("analyst.scope.same", who=who, label=plan[1]))
        elif mode == "season_vs_pitch":
            _, season_label, pitch_label, figures = plan
            # Only figures that exist are named: "N/A" is never a claim.
            season = (
                t("analyst.scope.season_figures", figures=figures, label=season_label)
                if figures
                else t("analyst.scope.no_season_figures")
            )
            notes.append(t("analyst.scope.differ", who=who, season=season, arsenal=pitch_label))
        else:
            parts = t.join(
                "; ", [t("analyst.scope.group_part", figures=figures, label=label) for label, figures in plan[1]]
            )
            notes.append(t("analyst.scope.groups", who=who, parts=parts))
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


def _scope_note_plan(t: Catalog, starter: dict[str, Any]) -> tuple:
    """
    What the scope note of a starter says, as a hashable plan (starters with the same plan share a note).

    - ("none",): he has no figure at all (a debut): there is nothing for a scope to cover, so none is claimed.
    - ("same", label, figures): every group he has covers the same games.
    - ("season_vs_pitch", season label, pitch label, figures): the season figures (API and counts)
      agree among themselves and differ from the pitch data.
    - ("groups", ((label, figures), ...)): the season figures themselves differ (the API's ERA is
      regular season, the Statcast counts are not), so each scope is listed with what it covers.
    """

    scopes = labels.figure_scopes(starter)
    if not scopes:
        return ("none",)
    if not labels.scopes_differ(starter):
        # The figures are part of the plan only so that starters are grouped as before (the text ignores them).
        return ("same", next(iter(scopes.values()))["label"], _available_figures(t, starter, starter["sample"]))
    season = [scopes[group] for group in ("season_rates", "counts") if group in scopes]
    if "pitch_data" in scopes and season and len({scope["kind"] for scope in season}) == 1:
        return (
            "season_vs_pitch",
            season[0]["label"],
            scopes["pitch_data"]["label"],
            _available_figures(t, starter, starter["sample"]),
        )
    by_label: dict[str, list[str]] = {}
    for group in ("season_rates", "counts", "pitch_data"):
        if group in scopes:
            by_label.setdefault(scopes[group]["label"], []).append(_group_figures(t, starter, group))
    return (
        "groups",
        tuple((label, _join(t, figures)) for label, figures in by_label.items()),
    )


def _group_figures(t: Catalog, starter: dict[str, Any], group: str) -> str:
    """What one group of figures is called in a sentence ("ERA and WHIP", "the pitch mix, ...")."""

    if group == "pitch_data":
        return t("analyst.figure.pitch_data")
    if group == "counts":
        return t("analyst.figure.counts")
    summary = starter.get("season_summary") or {}
    return _join(
        t, [t(f"analyst.figure.{key}") for key in labels.SEASON_RATE_FIELDS if labels.is_available(summary.get(key))]
    )


def _join(t: Catalog, names: list[str]) -> str:
    if len(names) > 1:
        return t("analyst.figure.list_and", head=t.join(", ", names[:-1]), last=names[-1])
    return names[0] if names else ""


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
    return _join(t, names)


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
        if ops is not None and ops >= labels.OFFENSE_OPS_STRONG:
            team_points.append(t("analyst.pressure.ops"))
        if k_rate is not None and k_rate >= labels.OFFENSE_K_NOTE_PCT:
            team_points.append(t("analyst.pressure.strikeouts"))
        if bb_rate is not None and bb_rate >= labels.OFFENSE_BB_NOTE_PCT:
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
