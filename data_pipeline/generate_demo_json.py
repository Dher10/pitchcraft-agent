"""Assemble, validate, and write the PitchCraft v0.2.0 demo JSON."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from data_pipeline import config
from data_pipeline import demo_inputs
from data_pipeline import labels
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
    if not snapshot or snapshot.get("run_at") != run.get("run_at"):
        return None, _status(
            config.DATA_MODE_FALLBACK,
            "Live snapshot does not belong to the latest live run; showing demo data",
            summary,
        )
    return snapshot, _status(config.DATA_MODE_SNAPSHOT, "Live run ok", summary)


_live, _live_status = _resolve_live_input()
print(f"[CONFIG] Data mode: {_live_status['mode']} - {_live_status['reason']}")
if _live:
    print(f"[CONFIG] Live snapshot found: {_live.get('fetched_date')} - using live data")


REPO_ROOT = Path(__file__).resolve().parents[1]
OFFENSE_UNAVAILABLE_FIELDS = (
    "summary_label",
    "ops_vs_hand",
    "k_rate_vs_hand",
    "bb_rate_vs_hand",
    "recent_form",
)
OUTPUT_PATH = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"


def build_payload() -> dict[str, Any]:
    payload = demo_inputs.build_demo_payload()
    payload["metadata"]["data_mode"] = _live_status["mode"]
    payload["metadata"]["data_sources"] = config.SOURCE_LABELS
    payload["metadata"]["data_status"] = deepcopy(_live_status)
    if _live_status["mode"] == config.DATA_MODE_FALLBACK:
        payload["metadata"]["last_updated_label"] = "Live data unavailable; showing demo data"
    _apply_live_snapshot(payload)
    total_revised, graded_starters = _run_agents(payload["matchups"])
    _apply_live_confidence(payload)
    _update_archive_postgame_labels(payload)
    payload["agent_workflow"] = _build_agent_workflow(
        len(payload["matchups"]),
        total_revised,
        graded_starters,
    )
    return payload


def main() -> int:
    payload = build_payload()
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


def _run_agents(matchups: list[dict[str, Any]]) -> tuple[int, int]:
    total_revised = 0
    graded_starters = 0
    for matchup_input in matchups:
        packet = data_scout.run(matchup_input)
        available_count = sum(1 for available in packet["availability"].values() if available)
        print(f"[AGENT] Data Scout: {available_count} sections available")

        findings = matchup_analyst.run(packet)
        print(f"[AGENT] Matchup Analyst: headline = {findings['matchup_headline'][:50]}")

        report = report_writer.run(findings, matchup_input)
        print(f"[AGENT] Report Writer: {len(report['sections'])} sections generated")

        critic_review = critic.run(report, matchup_input)
        revised_count = sum(
            1 for check in critic_review["checks"] if check["status"] == "revised"
        )
        total_revised += revised_count
        print(
            f"[AGENT] Critic: {len(critic_review['checks'])} checks, "
            f"{revised_count} revised"
        )

        matchup_input["report"] = report
        matchup_input["critic_review"] = critic_review
        matchup_input["data_confidence"] = packet["data_confidence"]

        if matchup_input["status"] == "final":
            postgame = postgame_grader.run(matchup_input)
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

    return total_revised, graded_starters


def _apply_live_snapshot(payload: dict[str, Any]) -> None:
    live_games = _live_game_entries()
    if not live_games:
        return

    template_index = next(
        (
            index
            for index, matchup in enumerate(payload["matchups"])
            if matchup["id"] == "matchup_001"
        ),
        None,
    )
    if template_index is None:
        return

    template = deepcopy(payload["matchups"][template_index])
    primary = _apply_live_game_to_matchup(
        deepcopy(template),
        live_games[0],
        matchup_id="matchup_001",
        is_featured=True,
    )
    payload["matchups"][template_index] = primary

    extra_matchups = [
        _apply_live_game_to_matchup(
            deepcopy(template),
            live_game,
            matchup_id=f"matchup_live_{index}",
            is_featured=False,
        )
        for index, live_game in enumerate(live_games[1:3], start=2)
    ]
    if extra_matchups:
        payload["matchups"][template_index + 1 : template_index + 1] = extra_matchups

    fg = live_games[0]["featured_game"]
    away = live_games[0]["away_starter"]
    home = live_games[0]["home_starter"]
    if payload["archive"]:
        payload["archive"][0]["title"] = f"{fg['away_team_abbr']} vs {fg['home_team_abbr']}"
        payload["archive"][0]["starter_summary"] = f"{away['name']} vs {home['name']}"

    payload["metadata"]["data_mode"] = "fetched_snapshot"
    payload["metadata"]["last_updated_label"] = f"Live data fetched {_live['fetched_date']}"


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


def _apply_live_game_to_matchup(
    matchup: dict[str, Any],
    live_game: dict[str, Any],
    matchup_id: str,
    is_featured: bool,
) -> dict[str, Any]:
    fg = live_game["featured_game"]
    away = live_game["away_starter"]
    home = live_game["home_starter"]

    matchup["id"] = matchup_id
    matchup["date"] = _live.get("fetched_date", matchup["date"])
    matchup["status"] = "upcoming"
    matchup["is_featured"] = is_featured
    matchup["postgame"] = None

    matchup["game"].update(
        {
            "title": f"{fg['away_team']} vs {fg['home_team']}",
            "venue": fg.get("venue", matchup["game"]["venue"]),
            "start_time_local": fg.get("start_time", matchup["game"]["start_time_local"]),
            # No live source for a broadcast note; never keep the demo template's text.
            "broadcast_note": None,
            "home_team_id": str(fg.get("home_team_id", matchup["game"]["home_team_id"])),
            "away_team_id": str(fg.get("away_team_id", matchup["game"]["away_team_id"])),
        }
    )

    matchup["teams"]["away"].update(
        {
            "id": str(fg.get("away_team_id", matchup["teams"]["away"]["id"])),
            "name": fg["away_team"],
            "abbreviation": fg["away_team_abbr"],
            "record": None,
        }
    )
    matchup["teams"]["home"].update(
        {
            "id": str(fg.get("home_team_id", matchup["teams"]["home"]["id"])),
            "name": fg["home_team"],
            "abbreviation": fg["home_team_abbr"],
            "record": None,
        }
    )

    _apply_live_starter(matchup["starters"]["away_starter"], away, fg["away_team_abbr"], fg.get("away_pitcher_id"))
    _apply_live_starter(matchup["starters"]["home_starter"], home, fg["home_team_abbr"], fg.get("home_pitcher_id"))

    offense_scope = labels.make_scope(labels.SCOPE_REGULAR, _live_through())
    _apply_offense_split(
        matchup["teams"]["home"]["offense_profile"],
        live_game.get("home_team_splits", {}),
        away.get("throws", "R"),
        offense_scope,
    )
    _apply_offense_split(
        matchup["teams"]["away"]["offense_profile"],
        live_game.get("away_team_splits", {}),
        home.get("throws", "L"),
        offense_scope,
    )

    matchup["charts"]["pitch_mix"] = live_game["combined_charts"]["pitch_mix"]
    matchup["charts"]["velocity_by_pitch"] = live_game["combined_charts"]["velocity_by_pitch"]
    # The demo template's 0-100 strength scores would sit under real pitcher names.
    matchup["charts"]["strength_profile"] = []
    matchup["charts"]["pitch_movement"] = {
        "away_starter": away.get("movement", {}),
        "home_starter": home.get("movement", {}),
    }

    matchup["pitch_locations"]["away_starter"] = {
        "vs_lhh": away["pitch_locations"]["vs_lhh"],
        "vs_rhh": away["pitch_locations"]["vs_rhh"],
    }
    matchup["pitch_locations"]["home_starter"] = {
        "vs_lhh": home["pitch_locations"]["vs_lhh"],
        "vs_rhh": home["pitch_locations"]["vs_rhh"],
    }

    matchup["data_confidence"] = _live_confidence_note(matchup_id)
    return matchup


def _apply_live_starter(
    starter: dict[str, Any],
    live_starter: dict[str, Any],
    team_abbr: str,
    pitcher_id: int | None,
) -> None:
    throws = live_starter.get("throws", "R")
    starter["id"] = str(pitcher_id or starter["id"])
    starter["name"] = live_starter["name"]
    starter["team"] = team_abbr
    starter["throws"] = throws
    # No live source yet (P1.5 adds bio); never keep the demo template's values.
    starter["bio"] = None
    starter["recent_form"] = None
    starter["season_summary"].update(live_starter["season_summary"])
    starter["pitching_profile"].update(live_starter["pitching_profile"])
    # The sample decides every label. A snapshot from before samples existed has
    # none: every dimension is then limited, never filled from the demo template.
    sample = live_starter.get("sample") or _unknown_sample()
    starter["sample"] = sample
    starter["season_summary"].setdefault("scope", sample["rates"]["scope"])
    labels.apply_profile_labels(starter["pitching_profile"], sample)


def _live_through() -> str:
    return (_live or {}).get("as_of") or (_live or {}).get("fetched_date") or ""


def _unknown_sample() -> dict[str, Any]:
    scope = labels.make_scope(labels.SCOPE_REGULAR, _live_through())
    return labels.build_sample(
        pitches=None,
        arsenal_scope=scope,
        batters_faced=None,
        strikeouts=None,
        walks=None,
        home_runs=None,
        rates_source="unavailable",
        rates_scope=scope,
    )


def _apply_offense_split(
    offense_profile: dict[str, Any],
    splits: dict[str, Any],
    starter_hand: str,
    scope: dict[str, str] | None = None,
) -> None:
    hand = starter_hand if starter_hand in ("L", "R") else starter_hand[:1]
    split = splits.get("vl" if hand == "L" else "vr", {})

    # The team profile comes from the demo template; none of it may survive
    # unless this split provides it. Missing means None, never a demo value.
    for field in OFFENSE_UNAVAILABLE_FIELDS:
        offense_profile[field] = None
    offense_profile["vs_pitcher_hand"] = f"{hand}HP"
    offense_profile["scope"] = scope
    if not split:
        return

    offense_profile["summary_label"] = f"Real season split vs {hand}HP"
    offense_profile["ops_vs_hand"] = _format_ops(split.get("ops"))
    offense_profile["k_rate_vs_hand"] = _format_pct(split.get("k_rate"))
    offense_profile["bb_rate_vs_hand"] = _format_pct(split.get("bb_rate"))
    offense_profile["recent_form"] = "Season split"


def _format_ops(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("0."):
            return stripped[1:]
        return stripped
    return f"{float(value):.3f}".replace("0.", ".", 1)


def _format_pct(value: Any) -> str | None:
    if value is None:
        return None
    return f"{float(value):.1f}%"


def _live_confidence_note(matchup_id: str) -> dict[str, Any]:
    return {
        "level": "fetched_snapshot",
        "lineup_status": "probable_pitchers",
        "pitch_data_status": "fetched_snapshot",
        "notes": [
            f"Live snapshot fetched {_live['fetched_date']} for {matchup_id}.",
        ],
    }

def _apply_live_confidence(payload: dict[str, Any]) -> None:
    if not _live:
        return

    live_ids = {"matchup_001"}
    live_ids.update(f"matchup_live_{index}" for index in range(2, len(_live_game_entries()) + 1))
    for matchup in payload["matchups"]:
        if matchup["id"] in live_ids:
            matchup["data_confidence"] = _live_confidence_note(matchup["id"])

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
    total_revised: int,
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
                    f"Verified claims. {total_revised} claim(s) revised across all matchups."
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
