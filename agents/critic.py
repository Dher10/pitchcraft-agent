"""Rule-based Critic / Fact-check Agent."""

from __future__ import annotations

from typing import Any


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
    checks.extend(_pitch_claim_checks(matchup_input))
    checks.append(_command_check(report, matchup_input))
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


def _pitch_claim_checks(matchup_input: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    for slot in ("away_starter", "home_starter"):
        starter = matchup_input["starters"][slot]
        profile = starter["pitching_profile"]
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


def _command_check(report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    report_text = _report_text(report).lower()
    command_values = {
        slot: _strength_value(matchup_input, "Command", slot)
        for slot in ("away_starter", "home_starter")
    }
    below_average = [
        slot
        for slot in ("away_starter", "home_starter")
        if "below-average command" in matchup_input["starters"][slot]["pitching_profile"]["command_label"].lower()
    ]
    plus_or_solid = [
        slot
        for slot in ("away_starter", "home_starter")
        if any(
            term in matchup_input["starters"][slot]["pitching_profile"]["command_label"].lower()
            for term in ("plus", "solid")
        )
    ]

    if "below-average command" in report_text and below_average:
        slot = below_average[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": f"{starter['name']} carries below-average command risk.",
            "status": "supported",
            "evidence": f"Command signal is {command_values[slot]} in the strength profile.",
        }

    if "command" in report_text and plus_or_solid:
        slot = plus_or_solid[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": f"{starter['name']}'s command label is supported.",
            "status": "supported",
            "evidence": f"Command signal is {command_values[slot]} in the strength profile.",
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
