"""Rule-based Report Writer Agent."""

from __future__ import annotations

from typing import Any


FORBIDDEN_TERMS = (
    "bet",
    "odds",
    "pick",
    "lock",
    "guaranteed",
    "win probability",
    "prediction",
)


def run(findings: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, Any]:
    """Return a v0.2.0 report dict from structured findings."""

    starters = matchup_input["starters"]
    teams = matchup_input["teams"]
    away = starters["away_starter"]
    home = starters["home_starter"]
    away_strength = _first(findings["away_starter_strengths"], "Has a defined scouting note for this matchup fit")
    home_strength = _first(findings["home_starter_strengths"], "Has a defined scouting note for this matchup fit")
    away_sample = away.get("sample")
    home_sample = home.get("sample")
    first_watch = findings["three_things_to_watch"][0].rstrip("?")

    report = {
        "headline": findings["matchup_headline"],
        "short_summary": [
            _strength_line(away, findings["away_starter_strengths"], away_strength),
            _strength_line(home, findings["home_starter_strengths"], home_strength),
            f"The early what to watch is {_watch_observation(first_watch, (away['name'], home['name']))}.",
        ],
        "sections": [
            {"title": "Today's Matchup Summary", "body": findings["matchup_summary"]},
            {"title": f"{away['name']} vs {teams['home']['name']}", "body": findings["away_vs_home_offense"]},
            {"title": f"{home['name']} vs {teams['away']['name']}", "body": findings["home_vs_away_offense"]},
            {
                "title": "Arsenal Scout",
                "body": _arsenal_scout(findings, away, home),
            },
            {"title": "Three Things to Watch", "bullets": findings["three_things_to_watch"]},
            {
                "title": "Data Confidence Note",
                "body": _confidence_note(matchup_input, findings),
            },
        ],
    }
    _enforce_language_rules(report)
    return report


def _arsenal_limited(starter: dict[str, Any]) -> bool:
    sample = starter.get("sample")
    return bool(sample and sample["limited"]["arsenal"])


def _strength_line(starter: dict[str, Any], strengths: list[str], strength: str) -> str:
    if not strengths and starter.get("sample") is not None:
        return f"{starter['name']} has no claimed strength because the data is limited."
    return f"{starter['name']} brings this strength: {strength}."


def _arsenal_scout(findings: dict[str, Any], away: dict[str, Any], home: dict[str, Any]) -> str:
    if not (_arsenal_limited(away) or _arsenal_limited(home)):
        return (
            f"The main contrast is {findings['away_style']} versus {findings['home_style']}. "
            f"The primary pitch contrast is {away['pitching_profile']['primary_pitch']} "
            f"against {home['pitching_profile']['primary_pitch']}, a scouting note for matchup fit "
            "and each pressure point."
        )
    parts: list[str] = []
    for starter, notes, style in (
        (away, findings["away_data_notes"], findings["away_style"]),
        (home, findings["home_data_notes"], findings["home_style"]),
    ):
        if _arsenal_limited(starter):
            parts.append(notes[0])  # the limitation, and nothing more about his pitches
        else:
            parts.append(f"{starter['name']} works off {style}.")
    parts.append("No arsenal contrast is drawn because at least one arsenal has too little data.")
    return " ".join(parts)


def _confidence_note(matchup_input: dict[str, Any], findings: dict[str, Any]) -> str:
    note = _base_confidence_note(matchup_input)
    extra = list(findings.get("scope_notes", []))
    starters = matchup_input["starters"].values()
    if any(
        any(s.get("sample", {}).get("limited", {}).values()) for s in starters if s.get("sample")
    ):
        extra.append("Samples below the minimum are flagged as limited and no claim is made from them.")
    return " ".join([note, *extra]) if extra else note


def _base_confidence_note(matchup_input: dict[str, Any]) -> str:
    confidence = matchup_input.get("data_confidence", {})
    if confidence.get("level") == "fetched_snapshot":
        has_offense = all(
            matchup_input["teams"][side]["offense_profile"].get("ops_vs_hand") is not None
            for side in ("home", "away")
        )
        if not has_offense:
            return (
                "This report uses a fetched live snapshot with probable pitchers and Statcast pitch data. "
                "Season offense splits were not available for this game, so the lineup read makes no "
                "offense claims. Lineups can still change before first pitch."
            )
        return (
            "This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, "
            "and season offense splits. Lineups can still change before first pitch."
        )
    return (
        "This report is based on cached demo data for the capstone. Live lineup "
        "confirmation is not required for this version."
    )


def _first(values: list[str], fallback: str) -> str:
    return values[0] if values else fallback


def _watch_observation(watch_item: str, starter_names: tuple[str, ...] = ()) -> str:
    """
    Turn "Can <starter> <action>?" into "whether <starter> can <action>".

    The subject is matched against the full starter names of the packet. Where a
    name ends is never guessed from word positions: names have one to four words
    ("Corbin Burnes", "Luis Garcia Jr."), so an unmatched subject is left as is.
    """

    item = watch_item.rstrip("?")
    if not item.startswith("Can "):
        return item[:1].lower() + item[1:]
    rest = item[4:]
    for name in sorted(starter_names, key=len, reverse=True):
        if rest.startswith(f"{name} "):
            return f"whether {name} can {rest[len(name) + 1:]}"
    return item


def _enforce_language_rules(report: dict[str, Any]) -> None:
    text_parts: list[str] = [report["headline"], *report["short_summary"]]
    for section in report["sections"]:
        if section.get("body"):
            text_parts.append(section["body"])
        text_parts.extend(section.get("bullets", []))

    lower_text = "\n".join(text_parts).lower()
    blocked = [term for term in FORBIDDEN_TERMS if term in lower_text]
    if blocked:
        raise ValueError(f"Report contains forbidden term(s): {', '.join(blocked)}")

    required_terms = ("matchup fit", "what to watch", "scouting note", "pressure point")
    missing = [term for term in required_terms if term not in lower_text]
    if missing:
        raise ValueError(f"Report is missing required term(s): {', '.join(missing)}")

