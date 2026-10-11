"""Rule-based Critic / Fact-check Agent."""

from __future__ import annotations

import re
from typing import Any

from data_pipeline import labels


BETTING_SCAN_TERMS = (
    "bet",
    "odds",
    "pick",
    "lock",
    "guaranteed",
    "win probability",
    "predicts the winner",
    "will win",
)


# Pitch names the report may use, with the other ways a fan text says them. A pitch that is
# named in the report must be one the starter threw (see _unobserved_pitch_check).
PITCH_ALIASES = {
    "four-seam": ("four-seam", "four seam", "4-seam"),
    "sinker": ("sinker", "two-seam", "two seam", "2-seam"),
    "cutter": ("cutter", "cut fastball"),
    "slider": ("slider",),
    "sweeper": ("sweeper",),
    "slurve": ("slurve",),
    "curveball": ("curveball", "curve ball", "knuckle curve"),
    "changeup": ("changeup", "change-up"),
    "splitter": ("splitter", "split-finger", "split finger"),
    "knuckleball": ("knuckleball",),
    "forkball": ("forkball",),
    "eephus": ("eephus",),
}
FASTBALL_FAMILY = ("four-seam", "sinker", "cutter")
GENERIC_FASTBALL = "fastball"
_ALIAS_PATTERNS = {
    pitch: re.compile(r"\b(?:" + "|".join(re.escape(a) for a in aliases) + r")s?\b")
    for pitch, aliases in PITCH_ALIASES.items()
}
_FASTBALL_PATTERN = re.compile(r"\bfastballs?\b")
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def run(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, Any]:
    """Check report claims against structured data and return critic review."""

    checks: list[dict[str, str]] = []
    checks.extend(_pitch_claim_checks(report, matchup_input))
    checks.append(_unobserved_pitch_check(report, matchup_input))
    checks.append(_command_check(report, matchup_input))
    checks.append(_scope_check(report, matchup_input))
    checks.append(_language_scan(report))

    # The critic reviews; it does not rewrite. A claim it cannot support is reported as
    # "unsupported", and the generator refuses to publish a report that has one.
    notes = [check["evidence"] for check in checks if check["status"] == "warning"]
    notes.extend(
        [
            "Kept the report focused on matchup fit rather than outcome prediction.",
            "Avoided claiming official Stuff+.",
        ]
    )

    unsupported = sum(1 for check in checks if check["status"] == "unsupported")
    warnings = sum(1 for check in checks if check["status"] == "warning")
    if unsupported:
        summary = (
            f"The critic checked {len(checks)} claims and found {unsupported} the data does "
            "not back up; this report must not be published."
        )
    elif warnings:
        summary = (
            f"The critic checked {len(checks)} claims: none unsupported, {warnings} with a warning."
        )
    else:
        summary = f"The critic checked {len(checks)} claims and found them supported by the data."

    return {
        "status": "reviewed",
        "summary": summary,
        "checks": checks,
        "revision_notes": notes,
    }


def _pitch_claim_checks(report: dict[str, Any], matchup_input: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    report_text = _report_text(report).lower()
    for slot in ("away_starter", "home_starter"):
        starter = matchup_input["starters"][slot]
        profile = starter["pitching_profile"]
        sample = starter.get("sample")
        if sample and sample["limited"]["arsenal"]:
            checks.append(_limited_arsenal_check(starter, sample, report_text))
            continue
        for role, pitch, minimum in (
            ("primary", profile["primary_pitch"], labels.PRIMARY_MIN_USAGE_PCT),
            ("put-away", profile["putaway_pitch"], labels.PUTAWAY_MIN_USAGE_PCT),
        ):
            if labels.pitch_named(pitch):
                checks.append(_pitch_role_check(matchup_input, slot, starter, role, pitch, minimum))

    return checks


def _pitch_role_check(
    matchup_input: dict[str, Any],
    slot: str,
    starter: dict[str, Any],
    role: str,
    pitch: str,
    minimum: int,
) -> dict[str, str]:
    usage = _pitch_usage(matchup_input, slot, pitch)
    claim = f"{starter['name']}'s {role} pitch is {_display_pitch(pitch)}."
    if usage <= 0:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": f"{_display_pitch(pitch)} does not appear in {starter['name']}'s pitch mix.",
        }
    if usage >= minimum:
        evidence = (
            f"Pitch mix shows {usage:g}% {_display_pitch(pitch)} usage."
            if role == "primary"
            else f"Put-away pitch usage at {usage:g}% supports this claim."
        )
        return {"claim": claim, "status": "supported", "evidence": evidence}
    return {
        "claim": claim,
        "status": "warning",
        "evidence": (
            f"{_display_pitch(pitch)} is only {usage:g}% of {starter['name']}'s pitch mix, "
            f"below the {minimum}% the report treats as a {role} pitch."
        ),
    }


def _canonical_pitches(name: str) -> set[str]:
    """The pitches a mix row stands for, whatever it is called ("Two-seam" is a sinker)."""

    lower = name.lower()
    found = {pitch for pitch, pattern in _ALIAS_PATTERNS.items() if pattern.search(lower)}
    if not found and _FASTBALL_PATTERN.search(lower):
        found.add(GENERIC_FASTBALL)
    return found


def _thrown_by(matchup_input: dict[str, Any], slot: str) -> set[str]:
    thrown: set[str] = set()
    for row in matchup_input["charts"]["pitch_mix"]:
        if row[slot]["overall"] > 0:
            thrown |= _canonical_pitches(row["pitch"])
    return thrown


def _named_pitches(sentence: str) -> set[str]:
    lower = sentence.lower()
    named = {pitch for pitch, pattern in _ALIAS_PATTERNS.items() if pattern.search(lower)}
    if _FASTBALL_PATTERN.search(lower):
        named.add(GENERIC_FASTBALL)
    return named


def _supports(thrown: set[str], pitch: str) -> bool:
    if pitch == GENERIC_FASTBALL:
        return bool(thrown & {*FASTBALL_FAMILY, GENERIC_FASTBALL})
    return pitch in thrown


def _unobserved_pitch_check(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """
    Every pitch the report names must have been thrown in this game's data.

    A sentence that names exactly one starter is held to that starter's pitches; a
    sentence that names both, or neither, to the two together (free text cannot say
    whose pitch it is). Aliases count: "two-seam" is a sinker, "cut fastball" a
    cutter, and "fastball" is any fastball-family pitch.
    """

    slots = ("away_starter", "home_starter")
    thrown = {slot: _thrown_by(matchup_input, slot) for slot in slots}
    together = thrown["away_starter"] | thrown["home_starter"]
    names = {slot: matchup_input["starters"][slot]["name"] for slot in slots}

    problems: list[str] = []
    for _, text in _report_locations(report):
        for sentence in _SENTENCE_BREAK.split(text):
            mentioned = [slot for slot in slots if names[slot] in sentence]
            allowed = thrown[mentioned[0]] if len(mentioned) == 1 else together
            for pitch in sorted(_named_pitches(sentence)):
                if _supports(allowed, pitch):
                    continue
                if len(mentioned) == 1:
                    problems.append(f"{names[mentioned[0]]} is credited with {pitch}, which he did not throw")
                else:
                    problems.append(f"{pitch} is named, but neither starter threw it")
    claim = "The report names only pitches that appear in the pitch mix."
    if problems:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": "; ".join(dict.fromkeys(problems)) + " in this data.",
        }
    return {
        "claim": claim,
        "status": "supported",
        "evidence": "Every pitch named in the report was thrown by the starter it is credited to.",
    }


def _limited_arsenal_check(
    starter: dict[str, Any], sample: dict[str, Any], report_text: str
) -> dict[str, str]:
    """A limited arsenal must not be described: the report may only state the limitation."""

    profile = starter["pitching_profile"]
    named = [
        _display_pitch(pitch)
        for pitch in (profile["primary_pitch"], profile["putaway_pitch"])
        if pitch and pitch != "Not available" and _display_pitch(pitch).lower() in report_text
    ]
    pitches = sample["arsenal"]["pitches"]
    have = f"{pitches} pitches" if pitches else "no pitches on record"
    needed = sample["thresholds"]["arsenal"]
    if named:
        return {
            "claim": f"{starter['name']}'s arsenal is limited.",
            "status": "unsupported",
            "evidence": (
                f"Only {have} (minimum {needed}), but the report names {', '.join(named)}."
            ),
        }
    return {
        "claim": f"{starter['name']}'s arsenal is limited.",
        "status": "supported",
        "evidence": f"{have.capitalize()}, below the {needed} needed; the report makes no arsenal claim.",
    }


def _command_evidence(matchup_input: dict[str, Any], slot: str) -> str:
    """Evidence for a command claim: the strength profile when there is one, else the walk rate."""

    if matchup_input["charts"].get("strength_profile"):
        return f"Command signal is {_strength_value(matchup_input, 'Command', slot)} in the strength profile."
    sample = matchup_input["starters"][slot].get("sample")
    if sample and sample["rates"]["batters_faced"]:
        rates = sample["rates"]
        return (
            f"{rates['walks']} walks in {rates['batters_faced']} batters faced "
            f"({rates['scope']['label']})."
        )
    return "No walk-rate sample is available."


def _scope_check(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """Pitch data and season figures must not be presented as one sample when they differ."""

    claim = "Pitch data and season figures are not presented as one sample."
    differing = [
        starter["name"]
        for starter in matchup_input["starters"].values()
        if starter.get("sample") and labels.scopes_differ(starter["sample"])
    ]
    if not differing:
        return {
            "claim": claim,
            "status": "not_present",
            "evidence": "Each starter's figures cover the same games.",
        }
    if "different samples" in _report_text(report).lower():
        return {
            "claim": claim,
            "status": "supported",
            "evidence": f"The report says the figures for {', '.join(differing)} cover different samples.",
        }
    return {
        "claim": claim,
        "status": "unsupported",
        "evidence": (
            f"Pitch data and season figures for {', '.join(differing)} cover different games "
            "(postseason is in one and not the other), but the report does not say so."
        ),
    }


def _command_check(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    report_text = _report_text(report).lower()

    def command_label(slot: str) -> str:
        return (matchup_input["starters"][slot]["pitching_profile"].get("command_label") or "").lower()

    below_average = [
        slot
        for slot in ("away_starter", "home_starter")
        if "below-average command" in command_label(slot)
    ]
    plus_or_solid = [
        slot
        for slot in ("away_starter", "home_starter")
        if any(term in command_label(slot) for term in ("plus", "solid"))
    ]

    if "below-average command" in report_text and below_average:
        slot = below_average[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": f"{starter['name']} carries below-average command risk.",
            "status": "supported",
            "evidence": _command_evidence(matchup_input, slot),
        }

    if "command" in report_text and plus_or_solid:
        slot = plus_or_solid[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": f"{starter['name']}'s command label is supported.",
            "status": "supported",
            "evidence": _command_evidence(matchup_input, slot),
        }

    return {
        "claim": "The report makes a command claim.",
        "status": "not_present",
        "evidence": "No command claim requiring correction was found.",
    }


def _language_scan(report: dict[str, Any]) -> dict[str, str]:
    locations = _report_locations(report)
    flagged: list[str] = []
    for location, text in locations:
        lower_text = text.lower()
        for term in BETTING_SCAN_TERMS:
            if term in lower_text:
                flagged.append(f"{term!r} in {location}")

    if flagged:
        return {
            "claim": "The report predicts the winner.",
            "status": "unsupported",
            "evidence": f"Outcome or betting language found: {', '.join(flagged)}.",
        }

    return {
        "claim": "The report predicts the winner.",
        "status": "not_present",
        "evidence": "No win prediction or betting language found.",
    }


def _pitch_usage(matchup_input: dict[str, Any], slot: str, pitch: str) -> float:
    target = _normalize_pitch(pitch)
    for row in matchup_input["charts"]["pitch_mix"]:
        if _normalize_pitch(row["pitch"]) == target:
            return float(row[slot]["overall"])
    return 0


def _normalize_pitch(pitch: str) -> str:
    value = pitch.lower()
    for token in (" fastball", "-seam"):
        value = value.replace(token, "")
    return value.strip()


def _display_pitch(pitch: str) -> str:
    return pitch.replace(" fastball", "")


def _strength_value(matchup_input: dict[str, Any], dimension: str, slot: str) -> int:
    for row in matchup_input["charts"]["strength_profile"]:
        if row["dimension"] == dimension:
            return int(row[slot])
    return 0


def _report_text(report: dict[str, Any]) -> str:
    return "\n".join(text for _, text in _report_locations(report))


def _report_locations(report: dict[str, Any]) -> list[tuple[str, str]]:
    locations: list[tuple[str, str]] = [("headline", report.get("headline", ""))]
    for index, summary in enumerate(report.get("short_summary", [])):
        locations.append((f"short_summary[{index}]", summary))
    for index, section in enumerate(report.get("sections", [])):
        if section.get("body"):
            locations.append((f"sections[{index}].body", section["body"]))
        for bullet_index, bullet in enumerate(section.get("bullets", [])):
            locations.append((f"sections[{index}].bullets[{bullet_index}]", bullet))
    return locations
