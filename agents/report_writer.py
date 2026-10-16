"""Rule-based Report Writer Agent."""

from __future__ import annotations

from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog, catalog_for
from data_pipeline import labels


def run(
    findings: dict[str, Any],
    matchup_input: dict[str, Any],
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    """Return a v0.2.0 report dict from structured findings, written in `language`."""

    t = catalog_for(language)
    starters = matchup_input["starters"]
    teams = matchup_input["teams"]
    away = starters["away_starter"]
    home = starters["home_starter"]
    default_strength = t("writer.default_strength")
    away_strength = _first(findings["away_starter_strengths"], default_strength)
    home_strength = _first(findings["home_starter_strengths"], default_strength)
    first_watch = findings["three_things_to_watch"][0]

    with t.subject("away_starter"):
        away_line = _strength_line(t, away, findings["away_starter_strengths"], away_strength)
        away_title = t("writer.section.vs_team", pitcher=away["name"], team=teams["home"]["name"])
    with t.subject("home_starter"):
        home_line = _strength_line(t, home, findings["home_starter_strengths"], home_strength)
        home_title = t("writer.section.vs_team", pitcher=home["name"], team=teams["away"]["name"])

    report = {
        "headline": findings["matchup_headline"],
        "short_summary": [
            away_line,
            home_line,
            t("writer.watch_line", observation=_watch_observation(t, first_watch)),
        ],
        "sections": [
            {"title": t("writer.section.summary"), "body": findings["matchup_summary"]},
            {"title": away_title, "body": findings["away_vs_home_offense"]},
            {"title": home_title, "body": findings["home_vs_away_offense"]},
            {
                "title": t("writer.section.arsenal"),
                "body": _arsenal_scout(t, findings, away, home),
            },
            {"title": t("writer.section.watch"), "bullets": findings["three_things_to_watch"]},
            {
                "title": t("writer.section.confidence"),
                "body": _confidence_note(t, matchup_input, findings),
            },
        ],
    }
    _enforce_language_rules(t, report)
    return report


def _arsenal_limited(starter: dict[str, Any]) -> bool:
    """True when the report says nothing of his arsenal: too small a sample, or a lead pitch with no name (F6e)."""

    return labels.arsenal_unspoken(starter)


def _strength_line(t: Catalog, starter: dict[str, Any], strengths: list[str], strength: str) -> str:
    if not strengths and starter.get("sample") is not None:
        return t("writer.strength_none", name=starter["name"])
    return t("writer.strength", name=starter["name"], strength=strength)


def _arsenal_scout(t: Catalog, findings: dict[str, Any], away: dict[str, Any], home: dict[str, Any]) -> str:
    if not (_arsenal_limited(away) or _arsenal_limited(home)):
        return t(
            "writer.arsenal.contrast",
            away_style=findings["away_style"],
            home_style=findings["home_style"],
            away_primary=away["pitching_profile"]["primary_pitch"],
            home_primary=home["pitching_profile"]["primary_pitch"],
        )
    parts: list[str] = []
    for slot, starter, notes, style in (
        ("away_starter", away, findings["away_data_notes"], findings["away_style"]),
        ("home_starter", home, findings["home_data_notes"], findings["home_style"]),
    ):
        if _arsenal_limited(starter):
            parts.append(notes[0])  # the limitation, and nothing more about his pitches
        else:
            with t.subject(slot):
                parts.append(t("writer.arsenal.works_off", name=starter["name"], style=style))
    # Why there is no contrast: a limited sample ("too little data") or, when none is limited, a lead pitch with no name.
    limited = any((s.get("sample") or {}).get("limited", {}).get("arsenal") for s in (away, home))
    if limited:
        parts.append(t("writer.arsenal.no_contrast"))
    else:
        parts.append(t("writer.arsenal.no_contrast_unnamed"))
    return t.join(" ", parts)


def _confidence_note(t: Catalog, matchup_input: dict[str, Any], findings: dict[str, Any]) -> str:
    note = _base_confidence_note(t, matchup_input)
    extra = list(findings.get("scope_notes", []))
    starters = matchup_input["starters"].values()
    if any(any(s["sample"]["limited"].values()) for s in starters if s.get("sample")):
        extra.append(t("writer.confidence.limited"))
    return t.join(" ", [note, *extra]) if extra else note


def _base_confidence_note(t: Catalog, matchup_input: dict[str, Any]) -> str:
    confidence = matchup_input.get("data_confidence", {})
    if confidence.get("level") != "fetched_snapshot":
        return t("writer.confidence.demo")
    starters, teams = matchup_input["starters"], matchup_input["teams"]
    both_pitched = all(labels.has_pitch_data(starters[slot]) for slot in ("away_starter", "home_starter"))
    both_split = all(labels.has_offense_figure(teams[side]["offense_profile"]) for side in ("away", "home"))
    # The first sentence lists only what is complete; what is missing is said apart, with its consequence.
    items = [t("writer.confidence.item.pitchers")]
    if both_pitched:
        items.append(t("writer.confidence.item.pitch_data"))
    if both_split:
        items.append(t("writer.confidence.item.offense"))
    parts = [t("writer.confidence.snapshot", items=_listed(t, items))]
    if not both_pitched:
        parts.append(_pitch_data_missing(t, starters))
    if not both_split:
        parts.append(_offense_missing(t, teams))
    # A time claim: only a game that has not started can still change its lineups (F16). Any other state, an unknown
    # one included, says nothing about them.
    if matchup_input.get("status") == "upcoming":
        parts.append(t("writer.confidence.lineups"))
    return t.join(" ", parts)


def _listed(t: Catalog, items: list[str]) -> str:
    """"A", "A and B" or "A, B, and C"."""

    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return t("writer.confidence.list_two", first=items[0], second=items[1])
    return t("writer.confidence.list_three", first=items[0], second=items[1], third=items[2])


def _pitch_data_missing(t: Catalog, starters: dict[str, Any]) -> str:
    """Which starter has no Statcast pitch data (one, named) or that neither has."""

    away, home = starters["away_starter"], starters["home_starter"]
    having = [s for s in (away, home) if labels.has_pitch_data(s)]
    if not having:
        return t("writer.confidence.pitch_data.none")
    without = home if having[0] is away else away
    return t("writer.confidence.pitch_data.one", with_data=having[0]["name"], without_data=without["name"])


def _offense_missing(t: Catalog, teams: dict[str, Any]) -> str:
    """Which lineup has no season offense split (one, named) or that neither has."""

    away, home = teams["away"], teams["home"]
    having = [team for team in (away, home) if labels.has_offense_figure(team["offense_profile"])]
    if not having:
        return t("writer.confidence.offense.none")
    without = home if having[0] is away else away
    return t("writer.confidence.offense.one", with_split=having[0]["name"], without_split=without["name"])


def _first(values: list[str], fallback: str) -> str:
    return values[0] if values else fallback


def _watch_observation(t: Catalog, first_watch: str) -> str:
    """
    "whether <starter> can <action>", from the first thing to watch.

    The question was written as "Can <name> <action>?" from a starter and an action, and the phrase
    keeps both, so neither is cut out of its text: the name is never guessed (names have one to four
    words) and the action is the same claim the question is made of.
    """

    args = getattr(first_watch, "args", {})
    if getattr(first_watch, "key", None) != "analyst.watch.question" or not {"name", "action"} <= set(args):
        raise ValueError(f"the first thing to watch is not a question about a starter: {str(first_watch)[:80]!r}")
    return t("writer.watch_whether", name=args["name"], action=args["action"])


def _enforce_language_rules(t: Catalog, report: dict[str, Any]) -> None:
    text_parts: list[str] = [report["headline"], *report["short_summary"]]
    for section in report["sections"]:
        if section.get("body"):
            text_parts.append(section["body"])
        text_parts.extend(section.get("bullets", []))

    lower_text = "\n".join(text_parts).lower()
    blocked = [term for term in t.terms("writer.forbidden_terms") if term in lower_text]
    if blocked:
        raise ValueError(f"Report contains forbidden term(s): {', '.join(blocked)}")

    missing = [term for term in t.terms("writer.required_terms") if term not in lower_text]
    if missing:
        raise ValueError(f"Report is missing required term(s): {', '.join(missing)}")
