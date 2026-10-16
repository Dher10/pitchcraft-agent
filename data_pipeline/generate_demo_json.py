"""Assemble, validate, and write the PitchCraft v0.2.0 demo JSON."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from agents.language import DEFAULT_LANGUAGE
from data_pipeline import claims
from data_pipeline import config
from data_pipeline import demo_inputs
from data_pipeline import labels
from data_pipeline import live_matchup
from data_pipeline import schema
from data_pipeline.contract_checks import RUN_ERROR_CODES, RUN_SOURCES, RUN_WARNING_CODES
from data_pipeline.fetchers.cache_manager import load_processed
from data_pipeline.generator_texts import generator_catalog
from data_pipeline.schema import new_york_day
from data_pipeline.validators import ValidationError, validate_payload

# Rule 8: what the file says about a failure is a source and a code of the closed sets (D38); the text goes to this log
# and the local run record. The reasons of a fallback that no fetcher recorded:
SNAPSHOT_SCHEMA_MISMATCH = {"source": "snapshot", "code": "snapshot_schema_mismatch"}
SNAPSHOT_MISMATCH = {"source": "snapshot", "code": "snapshot_mismatch"}
SNAPSHOT_UNREADABLE = {"source": "snapshot", "code": "malformed_response"}
GAME_REJECTED = {"source": "snapshot", "code": "game_rejected"}
NO_GAMES = {"source": "mlb_schedule", "code": "no_games"}
NO_USABLE_GAMES = {"source": "pipeline", "code": "no_usable_games"}
NO_LIVE_RUN = {"source": "pipeline", "code": "no_live_run"}  # a demo file for a day with no live run at all (D39)
UNEXPECTED = {"source": "pipeline", "code": "unexpected_error"}
PUBLISHED_LIST_LIMIT = 20


def _status(mode: str, reason: dict[str, str] | None, live_run: dict[str, Any] | None) -> dict[str, Any]:
    return {"mode": mode, "reason": reason, "live_run": live_run}


def _published(items: Any, codes: tuple[str, ...], unknown: dict[str, str] | None) -> list[dict[str, str]]:
    """
    The errors (or warnings) of a run record as the file may say them: exactly a source and a code of the closed
    sets, the first of each kind only, at most 20. An item the sets do not know is `unknown` (an error) or left out
    (a warning): fail closed, never the text of the record.
    """

    shown: list[dict[str, str]] = []
    for item in items if isinstance(items, list) else []:
        source = item.get("source") if isinstance(item, dict) else None
        code = item.get("code") if isinstance(item, dict) else None
        if source in RUN_SOURCES and code in codes:
            entry = {"source": source, "code": code}
        elif unknown is not None:
            entry = {
                "source": source if source in RUN_SOURCES else unknown["source"],
                "code": unknown["code"],
            }
        else:
            continue
        if entry not in shown:
            shown.append(entry)
    return shown[:PUBLISHED_LIST_LIMIT]


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": run.get("status"),
        "run_at": run.get("run_at"),
        "target_date": run.get("target_date"),
        "as_of": run.get("as_of"),
        "games_scheduled": run.get("games_scheduled"),
        "games_live": run.get("games_live"),
        "errors": _published(run.get("errors"), RUN_ERROR_CODES, UNEXPECTED),
        "warnings": _published(run.get("warnings"), RUN_WARNING_CODES, None),
    }


def _run_failure_reason(summary: dict[str, Any]) -> dict[str, str]:
    """Why a run that is not `ok` produced no live page, as a source and a code."""

    status = summary["status"]
    if status == "no_games":
        return dict(NO_GAMES)
    if status == "no_usable_games":
        return dict(NO_USABLE_GAMES)
    if status == "failed" and summary["errors"]:
        return dict(summary["errors"][0])
    return dict(UNEXPECTED)


def _resolve_live_input() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """
    Decide what the published data is, from the live run record and its snapshot.

    Returns (snapshot or None, status). The snapshot is used only when the latest
    live run succeeded and wrote it; a failed run, a missing or unreadable record,
    or a snapshot left by an earlier run never counts as live.
    """

    try:
        run = load_processed("live_run")
    except Exception as exc:
        print(f"[CONFIG] Live run record unreadable: {exc}")
        return None, _status(config.DATA_MODE_FALLBACK, dict(SNAPSHOT_UNREADABLE), None)
    if run is None:
        return None, _status(config.DATA_MODE_DEMO, dict(NO_LIVE_RUN), None)

    summary = _run_summary(run)
    if run.get("status") != "ok":
        print(f"[CONFIG] Live run {run.get('status')}; showing demo data")
        return None, _status(config.DATA_MODE_FALLBACK, _run_failure_reason(summary), summary)
    try:
        snapshot = load_processed("live_matchup")
    except Exception as exc:
        print(f"[CONFIG] Live snapshot unreadable: {exc}")
        return None, _status(config.DATA_MODE_FALLBACK, dict(SNAPSHOT_UNREADABLE), summary)
    mismatch = _snapshot_mismatch(run, snapshot)
    if mismatch:
        print(f"[CONFIG] Live snapshot does not belong to the latest live run ({mismatch}); showing demo data")
        return None, _status(config.DATA_MODE_FALLBACK, dict(SNAPSHOT_MISMATCH), summary)
    # Rejected by the schema it was written under, not by looking inside it (0.4.0 made the scope of a group
    # with no figure null). The file says only {source, code} (rule 8); the detail stays in this log.
    if not schema.snapshot_matches_schema(snapshot.get("schema_version")):
        print(
            f"[CONFIG] Live snapshot rejected: schema {snapshot.get('schema_version')!r}, this code reads "
            f"{schema.SCHEMA_VERSION!r} (a snapshot from before P0.15-D2.1, or from newer code)"
        )
        return None, _status(config.DATA_MODE_FALLBACK, dict(SNAPSHOT_SCHEMA_MISMATCH), summary)
    unsafe = _snapshot_unsafe(run, snapshot)
    if unsafe:
        print(f"[CONFIG] Live snapshot rejected ({unsafe}); showing demo data")
        return None, _status(config.DATA_MODE_FALLBACK, dict(SNAPSHOT_MISMATCH), summary)
    # Rule 5: an unsafe game is dropped with a recorded reason and the others are published; the page falls back to the
    # demo only when no game is left. The checks above are about the run and the snapshot as a whole.
    safe, dropped = _split_games(run, snapshot)
    if not safe:
        index, problem = dropped[0]
        print(f"[CONFIG] Live snapshot rejected (game {index}: {problem}); showing demo data")
        return None, _status(config.DATA_MODE_FALLBACK, dict(GAME_REJECTED), summary)
    if dropped:
        for index, problem in dropped:
            print(f"[CONFIG] Live game dropped: game {index}: {problem}")
        snapshot = {**snapshot, **_primary_game(safe[0]), "live_games": safe}
        summary["games_live"] = len(safe)  # the games the file shows, not the ones the run built
        if GAME_REJECTED not in summary["errors"] and len(summary["errors"]) < PUBLISHED_LIST_LIMIT:
            summary["errors"] = [*summary["errors"], dict(GAME_REJECTED)]
    return snapshot, _status(config.DATA_MODE_SNAPSHOT, None, summary)


def _snapshot_mismatch(run: dict[str, Any], snapshot: Any) -> str | None:
    """
    Why `snapshot` cannot be proven to belong to `run`, or None if it can.

    Both need the same non-empty run identifier, the same game date and the same
    cutoff. A missing value is never equal to another missing value.
    """

    if not isinstance(snapshot, dict) or not snapshot:
        return "no snapshot"
    run_at = run.get("run_at")
    if not isinstance(run_at, str) or not run_at.strip():
        return "the run record has no run identifier"
    if snapshot.get("run_at") != run_at:
        return "different run identifier"
    for key, snapshot_key in (("target_date", "fetched_date"), ("as_of", "as_of")):
        expected, found = run.get(key), snapshot.get(snapshot_key)
        if not isinstance(expected, str) or not expected or expected != found:
            return f"{snapshot_key.replace('_', ' ')} does not match the run"
    return None


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_SLOTS = ("away_starter", "home_starter")


def _parse_date(value: Any) -> date | None:
    """A date written exactly as YYYY-MM-DD, or None. Anything else is not a date."""

    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _run_dates(run: dict[str, Any]) -> tuple[date | None, date | None]:
    return _parse_date(run.get("target_date")), _parse_date(run.get("as_of"))


def _snapshot_unsafe(run: dict[str, Any], snapshot: dict[str, Any]) -> str | None:
    """
    Why a snapshot that belongs to its run still cannot be published as live at all, or None.

    Equal strings prove ownership, not safety (QA2-01). The dates of the run are parsed and the relationship D29
    relies on is checked: the cutoff of the run is before the game day. This is about the run and the snapshot as a
    whole; a game that is unsafe on its own is dropped by `_split_games` (rule 5).
    """

    target, cutoff = _run_dates(run)
    if target is None:
        return f"run game date {run.get('target_date')!r} is not a date"
    if cutoff is None:
        return f"run cutoff {run.get('as_of')!r} is not a date"
    if cutoff >= target:
        return f"run cutoff {cutoff} is not before the game date {target}"

    if new_york_day(run.get("run_at")) is None:
        return f"run time {run.get('run_at')!r} is not an instant with a time zone"
    games = snapshot.get("live_games")
    if not isinstance(games, list) or not games:
        return "the snapshot has no games"
    return None


def _split_games(run: dict[str, Any], snapshot: dict[str, Any]) -> tuple[list[Any], list[tuple[int, str]]]:
    """The games that are safe to publish and, for each of the others, its place (from 1) and why it is not."""

    target, cutoff = _run_dates(run)
    assert target is not None and cutoff is not None  # `_snapshot_unsafe` has accepted them
    safe: list[Any] = []
    dropped: list[tuple[int, str]] = []
    for index, game in enumerate(snapshot["live_games"], start=1):
        problem = _game_unsafe(game, target, cutoff)
        if problem:
            dropped.append((index, problem))
        else:
            safe.append(game)
    return safe, dropped


_PRIMARY_KEYS = ("featured_game", "away_starter", "home_starter", "combined_charts", "away_team_splits", "home_team_splits")


def _primary_game(game: dict[str, Any]) -> dict[str, Any]:
    """The fields of the snapshot that repeat its first game, taken from the first game that is left."""

    return {key: game[key] for key in _PRIMARY_KEYS if key in game}


def _game_unsafe(game: Any, target: date, cutoff: date) -> str | None:
    if not isinstance(game, dict) or not isinstance(game.get("featured_game"), dict):
        return "no game record"
    official_raw = game["featured_game"].get("official_date")
    official = _parse_date(official_raw)
    if official is None:
        return f"official date {official_raw!r} is not a date"
    if official != target:
        return f"official date {official} is not the run's game date {target}"
    game_cutoff_raw = game.get("as_of")
    game_cutoff = _parse_date(game_cutoff_raw)
    if game_cutoff is None:
        return f"cutoff {game_cutoff_raw!r} is not a date"
    if game_cutoff >= official:
        return f"cutoff {game_cutoff} is not before the official date {official}"
    if game_cutoff != cutoff:
        return f"cutoff {game_cutoff} is not the run's cutoff {cutoff}"
    problem = _featured_game_problem(game["featured_game"])
    if problem:
        return problem

    for slot in _SLOTS:
        starter = game.get(slot)
        if not isinstance(starter, dict) or not starter.get("name"):
            return f"{slot} has no name"
        # A switch pitcher ("S") is a hand: the lineup he faces has no split and the page says so (F11, D38).
        if starter.get("throws") not in ("L", "R", "S"):
            return f"{slot} throws {starter.get('throws')!r}, not L, R or S"
        scopes = (starter.get("season_summary") or {}).get("scopes")
        if not isinstance(scopes, dict) or set(scopes) != {"season_rates", "counts"}:
            return f"{slot} has no scope for each group of figures (a snapshot from before P0.15-B)"
        for through in _starter_throughs(starter):
            reached = _parse_date(through)
            if reached is None:
                return f"{slot} has a figure through {through!r}, not a date"
            if reached > game_cutoff:
                return f"{slot} has a figure through {reached}, after the cutoff {game_cutoff}"
    return None


_REQUIRED_GAME_TEXT = ("away_team", "home_team")
# The schedule and the maps may not know a team's abbreviation (F7): the field is there and says so with null.
_NULLABLE_GAME_TEXT = ("away_team_abbr", "home_team_abbr")
_REQUIRED_GAME_IDS = ("away_team_id", "home_team_id", "away_pitcher_id", "home_pitcher_id")


def _featured_game_problem(featured: dict[str, Any]) -> str | None:
    """
    What the schedule always sends and a live game cannot do without. A game missing one is
    malformed; the matchup is never completed from the demo (QA4-03). The venue, its zone, the status
    and the game number are optional: the schedule may leave them out and they are then unavailable.
    """

    for field in _REQUIRED_GAME_TEXT:
        value = featured.get(field)
        if not isinstance(value, str) or not value.strip():
            return f"featured_game.{field} is missing"
    for field in _NULLABLE_GAME_TEXT:
        if field not in featured or not (featured[field] is None or (isinstance(featured[field], str) and featured[field].strip())):
            return f"featured_game.{field} is missing"
    for field in _REQUIRED_GAME_IDS:
        value = featured.get(field)
        if not isinstance(value, int) or isinstance(value, bool):
            return f"featured_game.{field} is missing"
    if not schema.is_utc_instant(featured.get("start_time_utc")):
        return f"featured_game.start_time_utc {featured.get('start_time_utc')!r} is not a UTC instant"
    return None


def _starter_throughs(starter: dict[str, Any]) -> list[Any]:
    """The last day every group of figures of a starter claims to cover."""

    scopes = []
    sample = starter.get("sample")
    if isinstance(sample, dict):
        scopes += [(sample.get("arsenal") or {}).get("scope"), (sample.get("rates") or {}).get("scope")]
    scopes += ((starter.get("season_summary") or {}).get("scopes") or {}).values()
    return [scope.get("through") for scope in scopes if isinstance(scope, dict)]


_live, _live_status = _resolve_live_input()
print(f"[CONFIG] Data mode: {_live_status['mode']} - {_live_status['reason']}")
if _live:
    print(f"[CONFIG] Live snapshot found: {_live.get('fetched_date')} - using live data")


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"


class CriticBlocked(RuntimeError):
    """The critic found a claim the data does not back up: nothing is published (QA-04)."""


def build_payload(language: str = DEFAULT_LANGUAGE, now: datetime | None = None) -> dict[str, Any]:
    """
    The full payload; every agent writes its text in `language` (English by default).

    `now` is the clock of the build (injected by tests): `metadata.generated_at` is that instant, in every mode.
    `metadata.data_fetched_at` is the live fetch (null in a demo file), set by `_apply_live_snapshot` (D39).
    """

    payload = demo_inputs.build_demo_payload()
    _stamp_times(payload, now)
    payload["metadata"]["data_mode"] = _live_status["mode"]
    payload["metadata"]["data_sources"] = config.SOURCE_LABELS
    payload["metadata"]["data_status"] = deepcopy(_live_status)
    text = generator_catalog()
    payload["metadata"]["last_updated_label"] = (
        text("generator.metadata.last_updated.fallback")
        if _live_status["mode"] == config.DATA_MODE_FALLBACK
        else text("generator.metadata.last_updated.demo")
    )
    _apply_live_snapshot(payload)
    total_warnings, graded_starters = _run_agents(payload["matchups"], language)
    _apply_live_confidence(payload)
    _update_archive_postgame_labels(payload)
    payload["agent_workflow"] = _build_agent_workflow(
        len(payload["matchups"]),
        total_warnings,
        graded_starters,
    )
    claims.attach_claims(payload, language)
    return payload


def _stamp_times(payload: dict[str, Any], now: datetime | None) -> None:
    """
    The two times of a file (D39): `generated_at` is the build, from the clock, in every mode (never a constant of the
    demo); `data_fetched_at` is `null` until `_apply_live_snapshot` sets the live fetch.
    """

    built = now if now is not None else datetime.now(timezone.utc)
    if built.tzinfo is None:
        raise ValueError("the clock of the build must carry a time zone")
    payload["metadata"]["generated_at"] = built.astimezone(timezone.utc).isoformat(timespec="seconds")
    payload["metadata"]["data_fetched_at"] = None


def main() -> int:
    try:
        payload = build_payload()
    except CriticBlocked as exc:
        print(f"Publication blocked by the critic: {exc}", file=sys.stderr)
        return 1
    matchup_ids = [matchup["id"] for matchup in payload["matchups"]]

    print("PitchCraft demo JSON generator")
    print(f"Assembled matchups: {', '.join(matchup_ids)}")

    try:
        checks = validate_payload(payload)
    except ValidationError as exc:
        _print_checks(exc.checks)
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    _print_checks(checks)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote v{payload['metadata']['version']} demo JSON to {OUTPUT_PATH}")
    return 0


def _run_agents(matchups: list[dict[str, Any]], language: str = DEFAULT_LANGUAGE) -> tuple[int, int]:
    total_warnings = 0
    graded_starters = 0
    for matchup_input in matchups:
        packet = data_scout.run(matchup_input, language=language)
        available_count = sum(1 for available in packet["availability"].values() if available)
        print(f"[AGENT] Data Scout: {available_count} sections available")

        findings = matchup_analyst.run(packet, language=language)
        print(f"[AGENT] Matchup Analyst: headline = {findings['matchup_headline'][:50]}")

        report = report_writer.run(findings, matchup_input, language=language)
        print(f"[AGENT] Report Writer: {len(report['sections'])} sections generated")

        critic_review = critic.run(report, matchup_input, language=language)
        unsupported = [c for c in critic_review["checks"] if c["status"] == "unsupported"]
        warnings = sum(1 for c in critic_review["checks"] if c["status"] == "warning")
        total_warnings += warnings
        print(
            f"[AGENT] Critic: {len(critic_review['checks'])} checks, "
            f"{warnings} warning(s), {len(unsupported)} unsupported"
        )
        if unsupported:
            details = "; ".join(f"{c['claim']} {c['evidence']}" for c in unsupported)
            raise CriticBlocked(f"{matchup_input['id']}: {details}")

        matchup_input["report"] = report
        matchup_input["critic_review"] = critic_review
        matchup_input["data_confidence"] = packet["data_confidence"]

        if matchup_input["status"] == "final":
            postgame = postgame_grader.run(matchup_input, language=language)
            matchup_input["postgame"] = postgame
            graded_starters += len(postgame["starter_lines"])
            al = postgame["starter_lines"]["away_starter"]
            hl = postgame["starter_lines"]["home_starter"]
            print(
                f"[AGENT] Postgame Grader: {matchup_input['id']} -> "
                f"{al['name']} GS {al['game_score']} ({al['pitchcraft_grade']}), "
                f"{hl['name']} GS {hl['game_score']} ({hl['pitchcraft_grade']}), "
                f"duel {postgame['starter_duel_winner']}"
            )
        else:
            matchup_input["postgame"] = None

    return total_warnings, graded_starters


def _apply_live_snapshot(payload: dict[str, Any]) -> None:
    live_games = _live_game_entries()
    if not live_games:
        return

    # Rule 6 (F4): a live file holds only live matchups. Nothing of the demo is kept: not its other matchups, not its
    # archive rows. The archive stays empty (today's game is not a past report; the page says "No past reports yet").
    payload["matchups"] = [
        _build_live_matchup(live_games[0], "matchup_001", True),
        *(
            _build_live_matchup(live_game, f"matchup_live_{index}", False)
            for index, live_game in enumerate(live_games[1:3], start=2)
        ),
    ]
    payload["archive"] = []
    # Rule 6 (F3): what a live file says about its data is its own, not the demo's.
    payload["metadata"]["data_sources"] = list(config.LIVE_SOURCE_LABELS)
    payload["disclaimers"] = list(config.LIVE_DISCLAIMERS)

    payload["metadata"]["data_mode"] = "fetched_snapshot"
    payload["metadata"]["data_fetched_at"] = _live["run_at"]
    payload["metadata"]["last_updated_label"] = generator_catalog()(
        "generator.metadata.last_updated.live", date=_fetch_day()
    )



def _build_live_matchup(live_game: dict[str, Any], matchup_id: str, is_featured: bool) -> dict[str, Any]:
    return live_matchup.build_matchup(
        live_game,
        matchup_id=matchup_id,
        is_featured=is_featured,
        game_day=_live["fetched_date"],
        fetch_day=_fetch_day(),
        through=_live_through(),
    )


def _fetch_day() -> str:
    """The day of the live fetch in New York: the date every label that says "fetched" shows (D39)."""

    day = new_york_day((_live or {}).get("run_at"))
    if day is None:  # `_snapshot_unsafe` accepts a run only if its time is an instant
        raise ValueError("the live run has no time to say when the data was fetched")
    return day


def _live_game_entries() -> list[dict[str, Any]]:
    if not _live:
        return []
    live_games = _live.get("live_games")
    if isinstance(live_games, list) and live_games:
        return live_games
    return [
        {
            "featured_game": _live["featured_game"],
            "away_starter": _live["away_starter"],
            "home_starter": _live["home_starter"],
            "combined_charts": _live["combined_charts"],
            "away_team_splits": _live.get("away_team_splits", {}),
            "home_team_splits": _live.get("home_team_splits", {}),
        }
    ]


def _live_through() -> str:
    return (_live or {}).get("as_of") or (_live or {}).get("fetched_date") or ""


def _apply_live_confidence(payload: dict[str, Any]) -> None:
    if not _live:
        return

    live_ids = {"matchup_001"}
    live_ids.update(f"matchup_live_{index}" for index in range(2, len(_live_game_entries()) + 1))
    for matchup in payload["matchups"]:
        if matchup["id"] in live_ids:
            matchup["data_confidence"] = live_matchup.confidence_note(matchup["id"], _fetch_day(), matchup["starters"])

def _update_archive_postgame_labels(payload: dict[str, Any]) -> None:
    matchups_by_id = {matchup["id"]: matchup for matchup in payload["matchups"]}
    for row in payload["archive"]:
        matchup = matchups_by_id.get(row["id"])
        postgame = matchup.get("postgame") if matchup else None
        if not postgame:
            continue
        winner = postgame["starter_duel_winner"]
        winner_line = next(
            line
            for line in postgame["starter_lines"].values()
            if line["name"] == winner
        )
        row["grade_label"] = f"Starter Duel: {winner}, {winner_line['pitchcraft_grade']}"


def _build_agent_workflow(
    matchup_count: int,
    total_warnings: int,
    graded_starters: int,
) -> dict[str, Any]:
    text = generator_catalog()
    postgame_step = (
        {
            "agent": "Postgame Grader Agent",
            "status": "completed",
            "output": text("generator.workflow.graded", count=graded_starters),
        }
        if graded_starters
        else {
            "agent": "Postgame Grader Agent",
            "status": "not_applicable",
            "output": text("generator.workflow.graded_none"),
        }
    )

    return {
        "description": text("generator.workflow.description"),
        "steps": [
            {
                "agent": "Data Scout Agent",
                "status": "completed",
                "output": text("generator.workflow.loaded", count=matchup_count),
            },
            {
                "agent": "Matchup Analyst Agent",
                "status": "completed",
                "output": text("generator.workflow.identified"),
            },
            {
                "agent": "Report Writer Agent",
                "status": "completed",
                "output": text("generator.workflow.generated"),
            },
            {
                "agent": "Critic / Fact-check Agent",
                "status": "completed",
                "output": text("generator.workflow.checked", warnings=total_warnings),
            },
            postgame_step,
        ],
    }


def _print_checks(checks: list[object]) -> None:
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        detail = f" - {check.detail}" if check.detail else ""
        print(f"[{status}] {check.description}{detail}")


if __name__ == "__main__":
    raise SystemExit(main())
