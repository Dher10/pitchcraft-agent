"""Rule-based Critic / Fact-check Agent."""

from __future__ import annotations

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


def run(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, Any]:
    """Check report claims against structured data and return critic review."""

    checks: list[dict[str, str]] = []
    checks.extend(_pitch_claim_checks(report, matchup_input))
    checks.append(_command_check(report, matchup_input))
    checks.append(_scope_check(report, matchup_input))
    checks.append(_language_scan(report))

    revision_notes = [
        check["evidence"]
        for check in checks
        if check["status"] == "revised"
    ]
    revision_notes.extend(
        [
            "Kept the report focused on matchup fit rather than outcome prediction.",
            "Avoided claiming official Stuff+.",
        ]
    )

    revised_count = sum(1 for check in checks if check["status"] == "revised")
    if revised_count == 0:
        summary = f"The critic checked {len(checks)} claims and found them supported by the data."
    else:
        summary = (
            f"The critic checked {len(checks)} claims and revised {revised_count} "
            "where the data did not back them up."
        )

    return {
        "status": "reviewed",
        "summary": summary,
        "checks": checks,
        "revision_notes": revision_notes,
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
        primary_pitch = profile["primary_pitch"]
        putaway_pitch = profile["putaway_pitch"]
        primary_usage = _pitch_usage(matchup_input, slot, primary_pitch)
        putaway_usage = _pitch_usage(matchup_input, slot, putaway_pitch)

        if primary_usage >= 30:
            primary_status = "supported"
            primary_evidence = f"Pitch mix shows {primary_usage}% {_display_pitch(primary_pitch)} usage."
        else:
            primary_status = "revised"
            primary_evidence = (
                f"{_display_pitch(primary_pitch)} usage is only {primary_usage}%. "
                "Primary pitch revised to reflect actual usage."
            )
        checks.append(
            {
                "claim": f"{starter['name']}'s primary pitch is {_display_pitch(primary_pitch)}.",
                "status": primary_status,
                "evidence": primary_evidence,
            }
        )

        if putaway_usage >= 15:
            putaway_status = "supported"
            putaway_evidence = f"Put-away pitch usage at {putaway_usage}% supports this claim."
        else:
            putaway_status = "revised"
            putaway_evidence = (
                f"{_display_pitch(putaway_pitch)} usage is only {putaway_usage}%. "
                "Revised to reflect the higher-usage put-away pitch."
            )
        checks.append(
            {
                "claim": f"{starter['name']}'s put-away pitch is {_display_pitch(putaway_pitch)}.",
                "status": putaway_status,
                "evidence": putaway_evidence,
            }
        )

    return checks


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


def _pitch_usage(matchup_input: dict[str, Any], slot: str, pitch: str) -> int:
    target = _normalize_pitch(pitch)
    for row in matchup_input["charts"]["pitch_mix"]:
        if _normalize_pitch(row["pitch"]) == target:
            return int(row[slot]["overall"])
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
