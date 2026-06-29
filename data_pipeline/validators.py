"""Lightweight stdlib validation for the PitchCraft v0.2.0 demo payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any

from data_pipeline.schema import (
    BATTER_HAND_SPLITS,
    BETTING_TERMS,
    CHART_KEYS,
    CRITIC_STATUSES,
    MATCHUP_REQUIRED_KEYS,
    PITCH_LOCATION_SPLITS,
    POSTGAME_STARTER_LINE_REQUIRED_KEYS,
    SCHEMA_VERSION,
    STARTER_SLOTS,
    TEAM_SIDES,
    TOP_LEVEL_REQUIRED_KEYS,
)


@dataclass(frozen=True)
class ValidationCheck:
    """A single validation result for CLI logging."""

    description: str
    passed: bool
    detail: str = ""


class ValidationError(Exception):
    """Raised when one or more payload validation checks fail."""

    def __init__(self, checks: list[ValidationCheck]) -> None:
        failures = [check for check in checks if not check.passed]
        message = "; ".join(
            f"{failure.description}: {failure.detail}" if failure.detail else failure.description
            for failure in failures
        )
        super().__init__(message)
        self.checks = checks


def validate_payload(payload: Mapping[str, Any]) -> list[ValidationCheck]:
    """Validate the assembled payload and return pass/fail check records."""

    checks: list[ValidationCheck] = []

    def record(description: str, passed: bool, detail: str = "") -> None:
        checks.append(ValidationCheck(description, passed, "" if passed else detail))

    def has_keys(value: Any, keys: Sequence[str]) -> bool:
        return isinstance(value, Mapping) and all(key in value for key in keys)

    record(
        "top-level required keys",
        has_keys(payload, TOP_LEVEL_REQUIRED_KEYS),
        _missing_keys(payload, TOP_LEVEL_REQUIRED_KEYS),
    )

    metadata = payload.get("metadata")
    record(
        "metadata.version is 0.2.0",
        isinstance(metadata, Mapping) and metadata.get("version") == SCHEMA_VERSION,
        f"found {metadata.get('version')!r}" if isinstance(metadata, Mapping) else "metadata missing",
    )

    matchups = payload.get("matchups")
    matchup_ids = (
        {matchup.get("id") for matchup in matchups if isinstance(matchup, Mapping)}
        if isinstance(matchups, list)
        else set()
    )
    featured_matchup_id = payload.get("featured_matchup_id")
    record(
        "featured_matchup_id resolves to an existing matchup",
        featured_matchup_id in matchup_ids,
        f"{featured_matchup_id!r} not in {sorted(matchup_ids)!r}",
    )

    if isinstance(matchups, list):
        for index, matchup in enumerate(matchups):
            matchup_label = _matchup_label(matchup, index)
            _validate_matchup(matchup, matchup_label, record)
    else:
        record("matchups is a list", False, f"found {type(matchups).__name__}")

    failures = [check for check in checks if not check.passed]
    if failures:
        raise ValidationError(checks)

    return checks


def _validate_matchup(matchup: Any, label: str, record: Any) -> None:
    if not isinstance(matchup, Mapping):
        record(f"{label}: matchup is an object", False, f"found {type(matchup).__name__}")
        return

    record(
        f"{label}: required matchup keys",
        all(key in matchup for key in MATCHUP_REQUIRED_KEYS),
        _missing_keys(matchup, MATCHUP_REQUIRED_KEYS),
    )

    teams = matchup.get("teams")
    record(
        f"{label}: teams.home and teams.away",
        has_nested_keys(teams, TEAM_SIDES),
        _missing_keys(teams, TEAM_SIDES),
    )

    starters = matchup.get("starters")
    record(
        f"{label}: starters.away_starter and starters.home_starter",
        has_nested_keys(starters, STARTER_SLOTS),
        _missing_keys(starters, STARTER_SLOTS),
    )
    if isinstance(starters, Mapping):
        for slot in STARTER_SLOTS:
            starter = starters.get(slot)
            record(
                f"{label}: {slot} includes bio",
                isinstance(starter, Mapping) and "bio" in starter,
                "bio missing",
            )

    charts = matchup.get("charts")
    record(
        f"{label}: charts include pitch mix, velocity, and strength",
        has_nested_keys(charts, CHART_KEYS),
        _missing_keys(charts, CHART_KEYS),
    )
    _validate_pitch_mix(charts, label, record)

    pitch_locations = matchup.get("pitch_locations")
    record(
        f"{label}: pitch_locations include both starters",
        has_nested_keys(pitch_locations, STARTER_SLOTS),
        _missing_keys(pitch_locations, STARTER_SLOTS),
    )
    _validate_pitch_locations(pitch_locations, label, record)

    _validate_final_postgame(matchup, label, record)
    _validate_critic_review(matchup.get("critic_review"), label, record)
    _validate_report_betting_terms(matchup.get("report"), label, record)


def _validate_pitch_mix(charts: Any, label: str, record: Any) -> None:
    pitch_mix = charts.get("pitch_mix") if isinstance(charts, Mapping) else None
    if not isinstance(pitch_mix, list):
        record(f"{label}: charts.pitch_mix is a list", False, f"found {type(pitch_mix).__name__}")
        return

    for index, row in enumerate(pitch_mix):
        row_label = f"{label}: pitch_mix[{index}]"
        if not isinstance(row, Mapping):
            record(f"{row_label} is an object", False, f"found {type(row).__name__}")
            continue
        for slot in STARTER_SLOTS:
            starter_mix = row.get(slot)
            record(
                f"{row_label}.{slot} has overall/vs_lhh/vs_rhh",
                isinstance(starter_mix, Mapping)
                and all(split in starter_mix for split in BATTER_HAND_SPLITS),
                _missing_keys(starter_mix, BATTER_HAND_SPLITS),
            )


def _validate_pitch_locations(pitch_locations: Any, label: str, record: Any) -> None:
    if not isinstance(pitch_locations, Mapping):
        return

    for slot in STARTER_SLOTS:
        starter_locations = pitch_locations.get(slot)
        for split in PITCH_LOCATION_SPLITS:
            locations = starter_locations.get(split) if isinstance(starter_locations, Mapping) else None
            record(
                f"{label}: pitch_locations.{slot}.{split} is an array",
                isinstance(locations, list),
                f"found {type(locations).__name__}",
            )
            if isinstance(locations, list):
                for index, location in enumerate(locations):
                    record(
                        f"{label}: pitch_locations.{slot}.{split}[{index}] has pitch/x/y",
                        has_nested_keys(location, ("pitch", "x", "y")),
                        _missing_keys(location, ("pitch", "x", "y")),
                    )


def _validate_final_postgame(matchup: Mapping[str, Any], label: str, record: Any) -> None:
    if matchup.get("status") != "final":
        return

    postgame = matchup.get("postgame")
    starter_lines = postgame.get("starter_lines") if isinstance(postgame, Mapping) else None
    record(
        f"{label}: final matchup includes postgame.starter_lines",
        isinstance(starter_lines, Mapping),
        "starter_lines missing",
    )
    if not isinstance(starter_lines, Mapping):
        return

    for slot in STARTER_SLOTS:
        line = starter_lines.get(slot)
        record(
            f"{label}: postgame.starter_lines.{slot} includes grade and follow-up fields",
            isinstance(line, Mapping)
            and all(key in line for key in POSTGAME_STARTER_LINE_REQUIRED_KEYS),
            _missing_keys(line, POSTGAME_STARTER_LINE_REQUIRED_KEYS),
        )


def _validate_critic_review(critic_review: Any, label: str, record: Any) -> None:
    checks = critic_review.get("checks") if isinstance(critic_review, Mapping) else None
    if not isinstance(checks, list):
        record(f"{label}: critic_review.checks is a list", False, f"found {type(checks).__name__}")
        return

    for index, check in enumerate(checks):
        status = check.get("status") if isinstance(check, Mapping) else None
        record(
            f"{label}: critic_review.checks[{index}].status is allowed",
            status in CRITIC_STATUSES,
            f"found {status!r}",
        )


def _validate_report_betting_terms(report: Any, label: str, record: Any) -> None:
    sections = report.get("sections") if isinstance(report, Mapping) else None
    if not isinstance(sections, list):
        record(f"{label}: report.sections is a list", False, f"found {type(sections).__name__}")
        return

    pattern = re.compile(
        "|".join(rf"\b{re.escape(term)}\b" for term in BETTING_TERMS),
        flags=re.IGNORECASE,
    )
    flagged: list[str] = []
    for index, section in enumerate(sections):
        if not isinstance(section, Mapping):
            continue
        body = section.get("body")
        if isinstance(body, str) and pattern.search(body):
            flagged.append(f"section {index}: {section.get('title', '<untitled>')}")

    record(
        f"{label}: report section bodies contain no betting terms",
        not flagged,
        ", ".join(flagged),
    )


def has_nested_keys(value: Any, keys: Sequence[str]) -> bool:
    return isinstance(value, Mapping) and all(key in value for key in keys)


def _missing_keys(value: Any, keys: Sequence[str]) -> str:
    if not isinstance(value, Mapping):
        return f"expected object, found {type(value).__name__}"
    missing = [key for key in keys if key not in value]
    return f"missing {missing!r}" if missing else ""


def _matchup_label(matchup: Any, index: int) -> str:
    if isinstance(matchup, Mapping) and matchup.get("id"):
        return str(matchup["id"])
    return f"matchup[{index}]"

