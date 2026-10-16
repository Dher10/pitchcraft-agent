"""Lightweight stdlib validation for the PitchCraft v0.5.0 demo payload."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
import re
from typing import Any

from data_pipeline.claims import verify_claims
from data_pipeline.contract_checks import check_contract
from data_pipeline.known_violations import KNOWN_VIOLATIONS
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
    is_utc_instant,
)
from data_pipeline.labels import SCOPE_REGULAR, SEASON_RATE_FIELDS, is_available


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
        f"metadata.version is {SCHEMA_VERSION}",
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

    # Contract rule 4: every sentence is a registered phrase and the text is exactly what it renders to.
    claim_problems = verify_claims(payload)
    for problem in claim_problems:
        record(f"claims: {problem}", False)
    if not claim_problems:
        record("claims: every sentence is registered and matches its text", True)

    # Contract rules 3, 4, 6 and 8 (D34). The violations the code has today are tolerated until the
    # fix of their class lands (known_violations.py); any other violation stops publication.
    try:
        violations = check_contract(payload)
    except (AttributeError, KeyError, TypeError) as exc:
        record("contract: the payload has the shape the checks read", False, f"{type(exc).__name__}: {exc}")
        violations = []
    unknown = [v for v in violations if v.code not in KNOWN_VIOLATIONS]
    for violation in unknown:
        record(f"contract: {violation.code}", False, f"{violation.where}: {violation.message}")
    if not unknown:
        tolerated = sorted({finding for v in violations for finding in KNOWN_VIOLATIONS[v.code]})
        record(
            "contract: rules 3, 4, 6 and 8 hold except the known violations"
            + (f" ({', '.join(tolerated)})" if tolerated else ""),
            True,
        )

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
                f"{label}: {slot} includes bio (or marks it unavailable)",
                isinstance(starter, Mapping)
                and "bio" in starter
                and (starter["bio"] is None or isinstance(starter["bio"], Mapping)),
                "bio missing",
            )
            record(
                f"{label}: {slot}.throws is L or R",
                isinstance(starter, Mapping) and starter.get("throws") in ("L", "R"),
                f"found {starter.get('throws')!r}" if isinstance(starter, Mapping) else "starter missing",
            )

    charts = matchup.get("charts")
    record(
        f"{label}: charts include pitch mix, velocity, strength, and movement",
        has_nested_keys(charts, CHART_KEYS),
        _missing_keys(charts, CHART_KEYS),
    )
    _validate_pitch_mix(charts, label, record, starters)
    _validate_pitch_movement(charts, label, record)

    pitch_locations = matchup.get("pitch_locations")
    record(
        f"{label}: pitch_locations include both starters",
        has_nested_keys(pitch_locations, STARTER_SLOTS),
        _missing_keys(pitch_locations, STARTER_SLOTS),
    )
    _validate_pitch_locations(pitch_locations, label, record)

    _validate_data_cutoff(matchup, label, record)
    _validate_live_game_time(matchup, label, record)
    _validate_figure_scopes(matchup, label, record)
    _validate_final_postgame(matchup, label, record)
    _validate_critic_review(matchup.get("critic_review"), label, record)
    _validate_report_betting_terms(matchup.get("report"), label, record)


def _iso_date(value: Any) -> date | None:
    """A date written exactly as YYYY-MM-DD, or None."""

    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _scope_throughs(matchup: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """(where, last day covered) of every group of figures the matchup says how far it reaches."""

    found: list[tuple[str, Any]] = []

    def add(where: str, scope: Any) -> None:
        if isinstance(scope, Mapping):
            found.append((where, scope.get("through")))

    starters = matchup.get("starters")
    for slot in STARTER_SLOTS:
        starter = starters.get(slot) if isinstance(starters, Mapping) else None
        if not isinstance(starter, Mapping):
            continue
        sample = starter.get("sample")
        if isinstance(sample, Mapping):
            for group in ("arsenal", "rates"):
                part = sample.get(group)
                add(f"{slot} {group}", part.get("scope") if isinstance(part, Mapping) else None)
        summary = starter.get("season_summary")
        scopes = summary.get("scopes") if isinstance(summary, Mapping) else None
        for group, scope in (scopes.items() if isinstance(scopes, Mapping) else ()):
            add(f"{slot} season summary {group}", scope)
    teams = matchup.get("teams")
    for side in TEAM_SIDES:
        team = teams.get(side) if isinstance(teams, Mapping) else None
        offense = team.get("offense_profile") if isinstance(team, Mapping) else None
        add(f"{side} offense", offense.get("scope") if isinstance(offense, Mapping) else None)
    return found


def _validate_data_cutoff(matchup: Mapping[str, Any], label: str, record: Any) -> None:
    """No figure of a game may cover that game's own day or later (D29): last line of defense."""

    scopes = _scope_throughs(matchup)
    if not scopes:
        return
    game_day = _iso_date(matchup.get("date"))
    late = []
    for where, through in scopes:
        day = _iso_date(through)
        if game_day is None or day is None or day >= game_day:
            late.append(f"{where} through {through!r}")
    record(
        f"{label}: data cutoff is before the game date",
        not late,
        f"game date {matchup.get('date')!r}: {', '.join(late)}",
    )


def _validate_live_game_time(matchup: Mapping[str, Any], label: str, record: Any) -> None:
    """
    A live game's start is an explicit UTC instant and its zone is text or unknown (D33).

    Live means the matchup says so itself (`data_confidence.level`); the demo matchups keep their
    pre-formatted local time. A live game that lost the field fails: the page would otherwise have no
    time, or fall back to a demo one.
    """

    confidence = matchup.get("data_confidence")
    if not isinstance(confidence, Mapping) or confidence.get("level") != "fetched_snapshot":
        return
    game = matchup.get("game")
    game = game if isinstance(game, Mapping) else {}
    zone = game.get("timezone")
    record(
        f"{label}: live game start time is a UTC instant and its zone is text or unknown",
        is_utc_instant(game.get("start_time_utc")) and (zone is None or (isinstance(zone, str) and zone.strip() != "")),
        f"start_time_utc {game.get('start_time_utc')!r}, timezone {zone!r}",
    )


def _scope_problem(starter: Mapping[str, Any]) -> str | None:
    """
    Why the scope of a live starter's groups of figures does not match the source of each, or None.

    ERA, WHIP and innings come from the MLB API: regular season only, and no scope when unavailable.
    The counts have the scope the sample records for them, which must agree with the source that
    gave them: the API is regular season, Statcast covers the same games as the pitch data.
    """

    sample = starter.get("sample")
    summary = starter.get("season_summary")
    if not isinstance(sample, Mapping) or not isinstance(summary, Mapping):
        return None  # the demo's starters have no sample and no scopes
    scopes = summary.get("scopes")
    if not isinstance(scopes, Mapping) or set(scopes) != {"season_rates", "counts"}:
        return "the summary has no scope for ERA, WHIP and innings and one for the counts"

    rates_scope, counts_scope = scopes["season_rates"], scopes["counts"]
    if any(is_available(summary.get(key)) for key in SEASON_RATE_FIELDS):
        if not isinstance(rates_scope, Mapping) or rates_scope.get("kind") != SCOPE_REGULAR:
            return (
                "ERA, WHIP and innings come from the MLB API (regular season only) "
                f"but are scoped {_kind(rates_scope)}"
            )
    elif rates_scope is not None:
        return "ERA, WHIP and innings are unavailable but carry a scope"

    arsenal_part = sample.get("arsenal") if isinstance(sample.get("arsenal"), Mapping) else {}
    if (arsenal_part.get("pitches") is None) != (arsenal_part.get("scope") is None):
        return "the pitch data have a scope if and only if the pitch count is known"
    rates = sample.get("rates") if isinstance(sample.get("rates"), Mapping) else {}
    source = rates.get("source")
    if source == "unavailable":
        carried = counts_scope is not None or rates.get("scope") is not None
        return "the counts are unavailable but carry a scope" if carried else None
    if not isinstance(counts_scope, Mapping) or counts_scope != rates.get("scope"):
        return "the counts' scope in the summary is not the one in the sample"
    if source == "mlb_api" and counts_scope.get("kind") != SCOPE_REGULAR:
        return f"the counts come from the MLB API (regular season only) but are scoped {_kind(counts_scope)}"
    arsenal = (sample.get("arsenal") or {}).get("scope") or {}
    if source == "statcast" and counts_scope.get("kind") != arsenal.get("kind"):
        return f"the counts come from the Statcast pitches ({_kind(arsenal)}) but are scoped {_kind(counts_scope)}"
    if source not in ("mlb_api", "statcast"):
        return f"the counts have an unknown source {source!r}"
    return None


def _kind(scope: Any) -> str:
    return str(scope.get("kind")) if isinstance(scope, Mapping) else "nothing"


def _validate_figure_scopes(matchup: Mapping[str, Any], label: str, record: Any) -> None:
    """Each group of figures of a live starter has the scope of its source (QA4-01)."""

    starters = matchup.get("starters")
    if not isinstance(starters, Mapping):
        return
    for slot in STARTER_SLOTS:
        starter = starters.get(slot)
        if isinstance(starter, Mapping) and isinstance(starter.get("sample"), Mapping):
            problem = _scope_problem(starter)
            record(f"{label}: {slot} scope of each group of figures matches its source", problem is None, problem or "")


def _is_share_or_none(value: Any) -> bool:
    """A percentage (0-100, not a bool) or None: a side the starter never faced has no share."""

    if value is None:
        return True
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 100


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_pitch_counts(starter_mix: Any, sample: Any, row_label: str, slot: str, record: Any) -> None:
    """
    A live starter's mix row carries the raw pitch count and the total behind its share (QA3-03):
    the critic decides on them, never on the rounded `overall`. Both are whole numbers, the
    count is part of the total, the total is the starter's sample of pitches, and the share
    shown is the one they give.
    """

    count = starter_mix.get("count") if isinstance(starter_mix, Mapping) else None
    total = starter_mix.get("total") if isinstance(starter_mix, Mapping) else None
    ok = _is_count(count) and _is_count(total) and count <= total
    record(
        f"{row_label}.{slot} carries its raw pitch count and total",
        ok,
        f"count {count!r}, total {total!r}",
    )
    if not ok:
        return
    pitches = ((sample.get("arsenal") or {}).get("pitches")) if isinstance(sample, Mapping) else None
    if pitches is not None:
        record(
            f"{row_label}.{slot} total is the starter's pitches in the sample",
            total == pitches,
            f"total {total}, sample pitches {pitches}",
        )
    shown = starter_mix.get("overall")
    if total == 0:
        # A share of nothing is unknown (F20): `null` is the only right state; a 0 would read as a measured 0%.
        record(f"{row_label}.{slot} share matches its counts", shown is None, f"shows {shown!r}, out of no pitches the share is unknown (null)")
        return
    expected = round(count / total * 100, 1)
    record(
        f"{row_label}.{slot} share matches its counts",
        isinstance(shown, (int, float)) and abs(shown - expected) < 0.05,
        f"shows {shown!r}, counts give {expected}",
    )


def _validate_pitch_mix(charts: Any, label: str, record: Any, starters: Any = None) -> None:
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
            record(
                f"{row_label}.{slot} shares against each side are a percentage or unavailable (null)",
                isinstance(starter_mix, Mapping)
                and all(_is_share_or_none(starter_mix.get(split)) for split in BATTER_HAND_SPLITS),
                "found "
                + (
                    ", ".join(f"{split}={starter_mix.get(split)!r}" for split in BATTER_HAND_SPLITS)
                    if isinstance(starter_mix, Mapping)
                    else "no object"
                ),
            )
            starter = starters.get(slot) if isinstance(starters, Mapping) else None
            sample = starter.get("sample") if isinstance(starter, Mapping) else None
            if sample is not None:  # live data; the demo has no sample and no counts
                _validate_pitch_counts(starter_mix, sample, row_label, slot, record)


def _validate_pitch_movement(charts: Any, label: str, record: Any) -> None:
    pitch_movement = charts.get("pitch_movement") if isinstance(charts, Mapping) else None
    for slot in STARTER_SLOTS:
        movement = pitch_movement.get(slot) if isinstance(pitch_movement, Mapping) else None
        record(
            f"{label}: charts.pitch_movement.{slot} is an object",
            isinstance(movement, Mapping),
            f"found {type(movement).__name__}",
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
            f"{label}: postgame.starter_lines.{slot} includes raw line, Game Score, grade, and follow-up fields",
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
        record(
            f"{label}: critic_review.checks[{index}] is not an unsupported claim",
            status != "unsupported",
            "an unsupported claim must not be published",
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

