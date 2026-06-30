"""Assemble, validate, and write the PitchCraft v0.2.0 demo JSON."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from data_pipeline import config
from data_pipeline import demo_inputs
from data_pipeline.fetchers.cache_manager import load_processed
from data_pipeline.validators import ValidationError, validate_payload

def _load_live_snapshot() -> dict[str, Any] | None:
    try:
        return load_processed("live_matchup")
    except Exception as exc:
        print(f"[CONFIG] Live snapshot unavailable: {exc} - using demo data")
        return None


print(f"[CONFIG] Data mode: {config.ACTIVE_MODE}")
_live = _load_live_snapshot()
if _live:
    print(f"[CONFIG] Live snapshot found: {_live.get('fetched_date')} - using live data")
else:
    print("[CONFIG] No live snapshot - using demo data")


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"


def main() -> int:
    payload = demo_inputs.build_demo_payload()
    payload["metadata"]["data_mode"] = config.ACTIVE_MODE
    payload["metadata"]["data_sources"] = config.SOURCE_LABELS
    _apply_live_snapshot(payload)
    total_revised, graded_starters = _run_agents(payload["matchups"])
    _apply_live_confidence(payload)
    _update_archive_postgame_labels(payload)
    payload["agent_workflow"] = _build_agent_workflow(
        len(payload["matchups"]),
        total_revised,
        graded_starters,
    )
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
    if not _live:
        return

    for matchup in payload["matchups"]:
        if matchup["id"] != "matchup_001":
            continue

        fg = _live["featured_game"]
        away = _live["away_starter"]
        home = _live["home_starter"]

        matchup["game"]["title"] = f"{fg['away_team']} vs {fg['home_team']}"
        matchup["game"]["venue"] = fg.get("venue", matchup["game"]["venue"])

        matchup["teams"]["away"]["name"] = fg["away_team"]
        matchup["teams"]["away"]["abbreviation"] = fg["away_team_abbr"]
        matchup["teams"]["home"]["name"] = fg["home_team"]
        matchup["teams"]["home"]["abbreviation"] = fg["home_team_abbr"]

        matchup["starters"]["away_starter"]["name"] = away["name"]
        matchup["starters"]["away_starter"]["team"] = fg["away_team_abbr"]
        matchup["starters"]["away_starter"]["season_summary"].update(
            away["season_summary"]
        )
        matchup["starters"]["away_starter"]["pitching_profile"].update(
            away["pitching_profile"]
        )

        matchup["starters"]["home_starter"]["name"] = home["name"]
        matchup["starters"]["home_starter"]["team"] = fg["home_team_abbr"]
        matchup["starters"]["home_starter"]["season_summary"].update(
            home["season_summary"]
        )
        matchup["starters"]["home_starter"]["pitching_profile"].update(
            home["pitching_profile"]
        )

        matchup["charts"]["pitch_mix"] = _live["combined_charts"]["pitch_mix"]
        matchup["charts"]["velocity_by_pitch"] = _live["combined_charts"][
            "velocity_by_pitch"
        ]

        matchup["pitch_locations"]["away_starter"] = {
            "vs_lhh": away["pitch_locations"]["vs_lhh"],
            "vs_rhh": away["pitch_locations"]["vs_rhh"],
        }
        matchup["pitch_locations"]["home_starter"] = {
            "vs_lhh": home["pitch_locations"]["vs_lhh"],
            "vs_rhh": home["pitch_locations"]["vs_rhh"],
        }

        matchup["data_confidence"] = {"level": "fetched_snapshot"}

        if payload["archive"]:
            payload["archive"][0]["title"] = (
                f"{fg['away_team_abbr']} vs {fg['home_team_abbr']}"
            )
            payload["archive"][0]["starter_summary"] = (
                f"{away['name']} vs {home['name']}"
            )
        break

    payload["metadata"]["data_mode"] = "fetched_snapshot"
    payload["metadata"]["last_updated_label"] = (
        f"Live data fetched {_live['fetched_date']}"
    )


def _apply_live_confidence(payload: dict[str, Any]) -> None:
    if not _live:
        return

    for matchup in payload["matchups"]:
        if matchup["id"] == "matchup_001":
            matchup["data_confidence"]["level"] = "fetched_snapshot"
            matchup["data_confidence"]["pitch_data_status"] = "fetched_snapshot"
            matchup["data_confidence"]["notes"] = [
                f"Live snapshot fetched {_live['fetched_date']}.",
                "If live fetching fails, PitchCraft falls back to cached demo data.",
            ]
            break


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
