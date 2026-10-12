"""Assemble, validate, and write the PitchCraft v0.2.0 demo JSON."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from agents.language import DEFAULT_LANGUAGE
from data_pipeline import config
from data_pipeline import demo_inputs
from data_pipeline import labels
from data_pipeline import live_matchup
from data_pipeline import schema
from data_pipeline.fetchers.cache_manager import load_processed
from data_pipeline.validators import ValidationError, validate_payload

def _status(mode: str, reason: str, live_run: dict[str, Any] | None) -> dict[str, Any]:
    return {"mode": mode, "reason": reason, "live_run": live_run}


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": run.get("status"),
        "run_at": run.get("run_at"),
        "target_date": run.get("target_date"),
        "as_of": run.get("as_of"),
        "games_scheduled": run.get("games_scheduled"),
        "games_live": run.get("games_live"),
        "errors": list(run.get("errors", []))[:20],
    }


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
        return None, _status(
            config.DATA_MODE_FALLBACK, f"Live run record unreadable: {exc}", None
        )
    if run is None:
        return None, _status(config.DATA_MODE_DEMO, "No live run; showing demo data", None)

    summary = _run_summary(run)
    if run.get("status") != "ok":
        return None, _status(
            config.DATA_MODE_FALLBACK,
            f"Live run {run.get('status')}; showing demo data",
            summary,
        )
    try:
        snapshot = load_processed("live_matchup")
    except Exception as exc:
        return None, _status(
            config.DATA_MODE_FALLBACK, f"Live snapshot unreadable: {exc}", summary
        )
    mismatch = _snapshot_mismatch(run, snapshot)
    if mismatch:
        return None, _status(
            config.DATA_MODE_FALLBACK,
            f"Live snapshot does not belong to the latest live run ({mismatch}); showing demo data",
            summary,
        )
    unsafe = _snapshot_unsafe(run, snapshot)
    if unsafe:
        return None, _status(
            config.DATA_MODE_FALLBACK,
            f"Live snapshot rejected ({unsafe}); showing demo data",
            summary,
        )
    return snapshot, _status(config.DATA_MODE_SNAPSHOT, "Live run ok", summary)


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


def _snapshot_unsafe(run: dict[str, Any], snapshot: dict[str, Any]) -> str | None:
    """
    Why a snapshot that belongs to its run still cannot be published as live, or None.

    Equal strings prove ownership, not safety (QA2-01). Every date is parsed and the
    relationships D29 relies on are checked: the cutoff of the run and of every game is before
    the game's official date, the game is the run's game day, and no figure of any starter
    reaches past the cutoff. A game without its dates or its starters' hands is malformed.
    """

    target = _parse_date(run.get("target_date"))
    cutoff = _parse_date(run.get("as_of"))
    if target is None:
        return f"run game date {run.get('target_date')!r} is not a date"
    if cutoff is None:
        return f"run cutoff {run.get('as_of')!r} is not a date"
    if cutoff >= target:
        return f"run cutoff {cutoff} is not before the game date {target}"

    games = snapshot.get("live_games")
    if not isinstance(games, list) or not games:
        return "the snapshot has no games"
    for index, game in enumerate(games, start=1):
        problem = _game_unsafe(game, target, cutoff)
        if problem:
            return f"game {index}: {problem}"
    return None


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
        if starter.get("throws") not in ("L", "R"):
            return f"{slot} throws {starter.get('throws')!r}, not L or R"
        for through in _starter_throughs(starter):
            reached = _parse_date(through)
            if reached is None:
                return f"{slot} has a figure through {through!r}, not a date"
            if reached > game_cutoff:
                return f"{slot} has a figure through {reached}, after the cutoff {game_cutoff}"
    return None


_REQUIRED_GAME_TEXT = ("away_team", "home_team", "away_team_abbr", "home_team_abbr")
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
    scopes.append((starter.get("season_summary") or {}).get("scope"))
    return [scope.get("through") for scope in scopes if isinstance(scope, dict)]


_live, _live_status = _resolve_live_input()
print(f"[CONFIG] Data mode: {_live_status['mode']} - {_live_status['reason']}")
if _live:
    print(f"[CONFIG] Live snapshot found: {_live.get('fetched_date')} - using live data")


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"


class CriticBlocked(RuntimeError):
    """The critic found a claim the data does not back up: nothing is published (QA-04)."""


def build_payload(language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """The full payload; every agent writes its text in `language` (English by default)."""

    payload = demo_inputs.build_demo_payload()
    payload["metadata"]["data_mode"] = _live_status["mode"]
    payload["metadata"]["data_sources"] = config.SOURCE_LABELS
    payload["metadata"]["data_status"] = deepcopy(_live_status)
    if _live_status["mode"] == config.DATA_MODE_FALLBACK:
        payload["metadata"]["last_updated_label"] = "Live data unavailable; showing demo data"
    _apply_live_snapshot(payload)
    total_warnings, graded_starters = _run_agents(payload["matchups"], language)
    _apply_live_confidence(payload)
    _update_archive_postgame_labels(payload)
    payload["agent_workflow"] = _build_agent_workflow(
        len(payload["matchups"]),
        total_warnings,
        graded_starters,
    )
    return payload


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

    # The featured slot is taken by the live game; nothing of the matchup that was there is kept.
    slot = next(
        (index for index, matchup in enumerate(payload["matchups"]) if matchup["id"] == "matchup_001"),
        None,
    )
    if slot is None:
        return

    fetched_date = _live["fetched_date"]
    payload["matchups"][slot] = _build_live_matchup(live_games[0], "matchup_001", True)
    extra_matchups = [
        _build_live_matchup(live_game, f"matchup_live_{index}", False)
        for index, live_game in enumerate(live_games[1:3], start=2)
    ]
    if extra_matchups:
        payload["matchups"][slot + 1 : slot + 1] = extra_matchups

    # The archive row of the live game is made from the game, never patched from the demo row.
    payload["archive"][:1] = [
        live_matchup.archive_row(live_games[0], matchup_id="matchup_001", fetched_date=fetched_date)
    ]

    payload["metadata"]["data_mode"] = "fetched_snapshot"
    payload["metadata"]["generated_at"] = _live["run_at"]
    payload["metadata"]["last_updated_label"] = f"Live data fetched {fetched_date}"



def _build_live_matchup(live_game: dict[str, Any], matchup_id: str, is_featured: bool) -> dict[str, Any]:
    return live_matchup.build_matchup(
        live_game,
        matchup_id=matchup_id,
        is_featured=is_featured,
        fetched_date=_live["fetched_date"],
        through=_live_through(),
    )


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
            matchup["data_confidence"] = live_matchup.confidence_note(matchup["id"], _live["fetched_date"])

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
    postgame_step = (
        {
            "agent": "Postgame Grader Agent",
            "status": "completed",
            "output": (
                f"Graded {graded_starters} completed starter(s) with Bill James Game Score."
            ),
        }
        if graded_starters
        else {
            "agent": "Postgame Grader Agent",
            "status": "not_applicable",
            "output": "Featured game has not been completed.",
        }
    )

    return {
        "description": (
            "PitchCraft uses a multi-agent workflow to convert matchup data into a "
            "fan-facing scouting report."
        ),
        "steps": [
            {
                "agent": "Data Scout Agent",
                "status": "completed",
                "output": f"Loaded cached data for {matchup_count} matchups.",
            },
            {
                "agent": "Matchup Analyst Agent",
                "status": "completed",
                "output": "Identified pitcher strengths, risks, and lineup pressure points.",
            },
            {
                "agent": "Report Writer Agent",
                "status": "completed",
                "output": "Generated fan-friendly scouting report.",
            },
            {
                "agent": "Critic / Fact-check Agent",
                "status": "completed",
                "output": (
                    "Checked every claim against the data: none unsupported, "
                    f"{total_warnings} warning(s) across all matchups."
                ),
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
