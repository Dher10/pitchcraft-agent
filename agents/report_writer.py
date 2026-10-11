"""Rule-based Report Writer Agent."""

from __future__ import annotations

from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog, catalog_for


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
    first_watch = findings["three_things_to_watch"][0].rstrip("?")

    report = {
        "headline": findings["matchup_headline"],
        "short_summary": [
            _strength_line(t, away, findings["away_starter_strengths"], away_strength),
            _strength_line(t, home, findings["home_starter_strengths"], home_strength),
            t("writer.watch_line", observation=_watch_observation(t, first_watch, (away["name"], home["name"]))),
        ],
        "sections": [
            {"title": t("writer.section.summary"), "body": findings["matchup_summary"]},
            {
                "title": t("writer.section.vs_team", pitcher=away["name"], team=teams["home"]["name"]),
                "body": findings["away_vs_home_offense"],
            },
            {
                "title": t("writer.section.vs_team", pitcher=home["name"], team=teams["away"]["name"]),
                "body": findings["home_vs_away_offense"],
            },
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
    sample = starter.get("sample")
    return bool(sample and sample["limited"]["arsenal"])


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
    for starter, notes, style in (
        (away, findings["away_data_notes"], findings["away_style"]),
        (home, findings["home_data_notes"], findings["home_style"]),
    ):
        if _arsenal_limited(starter):
            parts.append(notes[0])  # the limitation, and nothing more about his pitches
        else:
            parts.append(t("writer.arsenal.works_off", name=starter["name"], style=style))
    parts.append(t("writer.arsenal.no_contrast"))
    return " ".join(parts)


def _confidence_note(t: Catalog, matchup_input: dict[str, Any], findings: dict[str, Any]) -> str:
    note = _base_confidence_note(t, matchup_input)
    extra = list(findings.get("scope_notes", []))
    starters = matchup_input["starters"].values()
    if any(
        any(s.get("sample", {}).get("limited", {}).values()) for s in starters if s.get("sample")
    ):
        extra.append(t("writer.confidence.limited"))
    return " ".join([note, *extra]) if extra else note


def _base_confidence_note(t: Catalog, matchup_input: dict[str, Any]) -> str:
    confidence = matchup_input.get("data_confidence", {})
    if confidence.get("level") == "fetched_snapshot":
        has_offense = all(
            matchup_input["teams"][side]["offense_profile"].get("ops_vs_hand") is not None
            for side in ("home", "away")
        )
        if not has_offense:
            return t("writer.confidence.live_no_offense")
        return t("writer.confidence.live_full")
    return t("writer.confidence.demo")


def _first(values: list[str], fallback: str) -> str:
    return values[0] if values else fallback


def _watch_observation(t: Catalog, watch_item: str, starter_names: tuple[str, ...] = ()) -> str:
    """
    Turn "Can <starter> <action>?" into "whether <starter> can <action>".

    The subject is matched against the full starter names of the packet. Where a
    name ends is never guessed from word positions: names have one to four words
    ("Corbin Burnes", "Luis Garcia Jr."), so an unmatched subject is left as is.
    """

    prefix = t("writer.watch_prefix")
    item = watch_item.rstrip("?")
    if not item.startswith(prefix):
        return item[:1].lower() + item[1:]
    rest = item[len(prefix):]
    for name in sorted(starter_names, key=len, reverse=True):
        if rest.startswith(f"{name} "):
            return t("writer.watch_whether", name=name, action=rest[len(name) + 1:])
    return item


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
