"""The generic checks of the data contract (decision D34, `docs/DATA_CONTRACT.md`).

`check_contract(payload)` applies rules 1 to 4, 6 and 8 to a payload and returns every violation, each
with a code, the place and a message. It does not decide what is tolerated: `validate_payload` does,
with `known_violations.KNOWN_VIOLATIONS`.

- Rules 1 and 2 (provenance, unknown is never zero): the manifest of a live file (`provenance`): every leaf is
  a source value, a documented derivation, a label, a recorded sentence or an unavailable state, and a
  number that stands for an unknown or a zero has the evidence it needs.
- Rule 3 (scope): one table of groups of figures (`GROUPS`). A scope field with no figure behind it, a
  figure with no scope, or a scope that disagrees with the source of its group is a violation. A
  measured zero is a figure and has its scope; an unknown value is not.
- Rule 4 (claims): the condition of every recorded claim (`claims_registry`) holds on the payload.
- Rule 6 (honest mode) and rule 8 (no internals): a live file only; a demo file is asked nothing.

Violation codes: `rule1:<reason>#<path>` and `rule2:<reason>#<path>` (see `provenance`), `rule3:<group>#<reason>`, `rule4:<catalog key>#<reason>`, `rule6:<reason>`, `rule8:<reason>`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from data_pipeline import labels, provenance
from data_pipeline.claims import catalogs_of, verify_claims
from data_pipeline.claims_registry import LIVE_LEVEL, ClaimIndex, Ctx, classify, run_rule
from data_pipeline.schema import new_york_day

LIVE_MODE = "fetched_snapshot"

# Rule 8: what a published error may say (DATA_CONTRACT.md, rule 8). The codes are D38's, plus `no_live_run` (D39).
RUN_SOURCES = (
    "mlb_schedule",
    "mlb_person",
    "mlb_season_stats",
    "mlb_team_splits",
    "mlb_series_status",
    "statcast_pitcher",
    "savant_team_batting",
    "snapshot",
    "pipeline",
)
RUN_ERROR_CODES = (
    "request_failed",
    "malformed_response",
    "malformed_rows",
    "missing_column",
    "unusable_column",
    "budget_spent",
    "unknown_value",
    "incomplete_sample",
    "unexpected_error",
    "no_games",
    "no_usable_games",
    "game_rejected",
    "snapshot_mismatch",
    "snapshot_schema_mismatch",
    "no_live_run",
)
RUN_WARNING_CODES = ("unmapped_pitch_type", "unknown_team")


@dataclass(frozen=True)
class Violation:
    """A place where the payload breaks the contract."""

    code: str
    where: str
    message: str


# --- rule 3: scope -------------------------------------------------------------------------------


@dataclass(frozen=True)
class Group:
    """
    A group of figures and the scope fields that describe it.

    `has_figures` says whether the group has a figure (a measured zero is one; an unknown value is not),
    `scopes` gives every field of the entity that carries the group's scope, and `source_problem` says
    why a scope disagrees with the source of the group, or None.
    """

    name: str
    entity: str  # "starter" or "offense"
    has_figures: Callable[[Mapping[str, Any]], bool]
    scopes: Callable[[Mapping[str, Any]], dict[str, Any]]
    source_problem: Callable[[Mapping[str, Any], Mapping[str, Any]], str | None]


def _kind(scope: Any) -> str | None:
    return scope.get("kind") if isinstance(scope, Mapping) else None


def _well_formed(scope: Any) -> bool:
    return (
        isinstance(scope, Mapping)
        and scope.get("kind") in (labels.SCOPE_REGULAR, labels.SCOPE_REGULAR_POSTSEASON)
        and isinstance(scope.get("through"), str)
        and isinstance(scope.get("label"), str)
    )


def _regular_only(source: str) -> Callable[[Mapping[str, Any], Mapping[str, Any]], str | None]:
    def problem(_entity: Mapping[str, Any], scope: Mapping[str, Any]) -> str | None:
        if _kind(scope) != labels.SCOPE_REGULAR:
            return f"{source} covers the regular season only, but the scope is {_kind(scope)!r}"
        return None

    return problem


def _sample(starter: Mapping[str, Any]) -> Mapping[str, Any]:
    sample = starter.get("sample")
    return sample if isinstance(sample, Mapping) else {}


def _summary(starter: Mapping[str, Any]) -> Mapping[str, Any]:
    summary = starter.get("season_summary")
    return summary if isinstance(summary, Mapping) else {}


def _summary_scopes(starter: Mapping[str, Any]) -> Mapping[str, Any]:
    scopes = _summary(starter).get("scopes")
    return scopes if isinstance(scopes, Mapping) else {}


def _counts_problem(starter: Mapping[str, Any], scope: Mapping[str, Any]) -> str | None:
    source = (_sample(starter).get("rates") or {}).get("source")
    if source == "mlb_api":
        return _regular_only("the MLB API")(starter, scope)
    if source == "statcast":
        arsenal = _kind(((_sample(starter).get("arsenal")) or {}).get("scope"))
        if _kind(scope) != arsenal:
            return f"the counts come from the Statcast pitches ({arsenal!r}) but are scoped {_kind(scope)!r}"
        return None
    return f"the counts have the source {source!r}"


GROUPS: tuple[Group, ...] = (
    Group(
        "pitch_data",
        "starter",
        lambda st: (_sample(st).get("arsenal") or {}).get("pitches") is not None,
        lambda st: {"sample.arsenal.scope": (_sample(st).get("arsenal") or {}).get("scope")},
        lambda st, scope: None,  # Statcast: the regular season, with the postseason when the frame has it
    ),
    Group(
        "season_rates",
        "starter",
        lambda st: any(labels.is_available(_summary(st).get(key)) for key in labels.SEASON_RATE_FIELDS),
        lambda st: {"season_summary.scopes.season_rates": _summary_scopes(st).get("season_rates")},
        _regular_only("the MLB API"),
    ),
    Group(
        "counts",
        "starter",
        lambda st: (_sample(st).get("rates") or {}).get("source") not in (None, "unavailable"),
        lambda st: {
            "season_summary.scopes.counts": _summary_scopes(st).get("counts"),
            "sample.rates.scope": (_sample(st).get("rates") or {}).get("scope"),
        },
        _counts_problem,
    ),
    Group(
        "offense",
        "offense",
        lambda off: any(off.get(key) is not None for key in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand")),
        lambda off: {"offense_profile.scope": off.get("scope")},
        _regular_only("the Savant plate appearances"),
    ),
)


def _is_live(matchup: Mapping[str, Any]) -> bool:
    return (matchup.get("data_confidence") or {}).get("level") == LIVE_LEVEL


def _rule3(matchup: Mapping[str, Any], label: str) -> list[Violation]:
    found: list[Violation] = []
    entities: list[tuple[Group, str, Mapping[str, Any]]] = []
    for slot, starter in (matchup.get("starters") or {}).items():
        if isinstance(starter, Mapping) and isinstance(starter.get("sample"), Mapping):
            entities += [(g, f"{label} {slot}", starter) for g in GROUPS if g.entity == "starter"]
    for side, team in (matchup.get("teams") or {}).items():
        offense = team.get("offense_profile") if isinstance(team, Mapping) else None
        if isinstance(offense, Mapping):
            entities += [(g, f"{label} {side} lineup", offense) for g in GROUPS if g.entity == "offense"]

    for group, where, entity in entities:
        scopes = group.scopes(entity)
        has_figures = group.has_figures(entity)
        present = {path: scope for path, scope in scopes.items() if scope is not None}
        if not has_figures and present:
            found.append(
                Violation(
                    f"rule3:{group.name}#scope_without_figures",
                    where,
                    f"{', '.join(present)} carry a scope but the {group.name} group has no figure",
                )
            )
        if has_figures:
            missing = [path for path, scope in scopes.items() if scope is None]
            if missing:
                found.append(
                    Violation(
                        f"rule3:{group.name}#figures_without_scope",
                        where,
                        f"the {group.name} group has figures but {', '.join(missing)} has no scope",
                    )
                )
        for path, scope in present.items():
            problem = None if _well_formed(scope) else f"{path} is not a scope"
            if problem is None and has_figures:
                problem = group.source_problem(entity, scope)
            if problem:
                found.append(Violation(f"rule3:{group.name}#scope_disagrees_with_source", where, f"{path}: {problem}"))
    return found


# --- rule 4: claims ------------------------------------------------------------------------------


def _rule4(payload: Mapping[str, Any]) -> list[Violation]:
    catalogs = catalogs_of(payload)
    if catalogs is None or verify_claims(payload):
        return []  # the claims check reports those; nothing can be evaluated on claims that do not verify
    found: list[Violation] = []
    shared: dict[str, Any] = {}

    def run(claims: Any, matchup: Mapping[str, Any] | None, label: str) -> None:
        if not isinstance(claims, list):
            return
        index = ClaimIndex(claims, catalogs)
        for claim in claims:
            key = claim["key"]
            kind, _ = classify(key)
            place = f"{label} {claim['id']}" + (f" at {claim['location']}" if claim["location"] else "")
            if kind is None:
                found.append(Violation(f"rule4:{key}#unregistered", place, "the key is neither registered nor listed as asserting nothing"))
                continue
            for fail in run_rule(key, Ctx(payload, matchup, claim, index, shared)):
                found.append(Violation(f"rule4:{key}#{fail.reason}", place, fail.message))

    run(payload.get("claims"), None, "root")
    for position, matchup in enumerate(payload.get("matchups") or []):
        if isinstance(matchup, Mapping):
            report = matchup.get("report")
            run(report.get("claims") if isinstance(report, Mapping) else None, matchup, str(matchup.get("id") or f"matchups[{position}]"))
    return found


# --- rule 6: honest mode -------------------------------------------------------------------------

_CACHED = re.compile(r"\bcached\b", re.IGNORECASE)


def _is_instant(value: Any) -> bool:
    """An instant with a zone and seconds (`...Z` or `...+00:00`): the shape `schema.new_york_day` can read."""

    return new_york_day(value) is not None


def _rule6(payload: Mapping[str, Any]) -> list[Violation]:
    found: list[Violation] = []
    matchups = [m for m in payload.get("matchups") or [] if isinstance(m, Mapping)]
    live_ids = {m.get("id") for m in matchups if _is_live(m)}
    for matchup in matchups:
        if not _is_live(matchup):
            found.append(Violation("rule6:matchup_not_live", str(matchup.get("id")), "a demo matchup is in a live file"))
    for row in payload.get("archive") or []:
        if isinstance(row, Mapping) and row.get("id") not in live_ids:
            found.append(Violation("rule6:archive_not_live", str(row.get("id")), "an archive row is not a live matchup of the file"))
    metadata = payload.get("metadata") or {}
    for name, texts in (("metadata.data_sources", metadata.get("data_sources")), ("disclaimers", payload.get("disclaimers"))):
        for position, text in enumerate(texts if isinstance(texts, list) else []):
            if isinstance(text, str) and _CACHED.search(text):
                found.append(Violation("rule6:cached_wording", f"{name}[{position}]", f"a live file says {text[:60]!r}"))
    if not _is_instant(metadata.get("data_fetched_at")):
        found.append(Violation("rule6:data_fetched_at", "metadata.data_fetched_at", "a live file has no time of fetch"))
    return found


# --- rule 8: no internals ------------------------------------------------------------------------


def _is_source_and_code(item: Any, codes: tuple[str, ...]) -> bool:
    return (
        isinstance(item, Mapping)
        and set(item) == {"source", "code"}
        and item["source"] in RUN_SOURCES
        and item["code"] in codes
    )


def _rule8(payload: Mapping[str, Any]) -> list[Violation]:
    found: list[Violation] = []
    status = (payload.get("metadata") or {}).get("data_status")
    if not isinstance(status, Mapping):
        return found
    reason = status.get("reason")
    if reason is not None and not _is_source_and_code(reason, RUN_ERROR_CODES):
        found.append(Violation("rule8:reason", "metadata.data_status.reason", f"the reason is free text: {str(reason)[:60]!r}"))
    run = status.get("live_run")
    if isinstance(run, Mapping):
        for name, codes, code in (
            ("errors", RUN_ERROR_CODES, "rule8:error_shape"),
            ("warnings", RUN_WARNING_CODES, "rule8:warning_shape"),
        ):
            for position, item in enumerate(run.get(name) or []):
                if not _is_source_and_code(item, codes):
                    shown = sorted(item) if isinstance(item, Mapping) else type(item).__name__
                    found.append(Violation(code, f"metadata.data_status.live_run.{name}[{position}]", f"not exactly a source and a code from the closed sets: {shown}"))
    return found


# --- the whole contract --------------------------------------------------------------------------


def check_contract(payload: Mapping[str, Any]) -> list[Violation]:
    """Every violation of rules 1 to 4, 6 and 8 in `payload` (rules 1, 2, 6 and 8 only for a live file)."""

    found: list[Violation] = []
    for position, matchup in enumerate(payload.get("matchups") or []):
        if isinstance(matchup, Mapping) and _is_live(matchup):
            found += _rule3(matchup, str(matchup.get("id") or f"matchups[{position}]"))
    found += _rule4(payload)
    if (payload.get("metadata") or {}).get("data_mode") == LIVE_MODE:
        found += [Violation(code, where, message) for code, where, message in provenance.findings(payload)]
        found += _rule6(payload)
        found += _rule8(payload)
    return found
