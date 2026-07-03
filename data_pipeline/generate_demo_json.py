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
            "home_team_id": str(fg.get("home_team_id", matchup["game"]["home_team_id"])),
            "away_team_id": str(fg.get("away_team_id", matchup["game"]["away_team_id"])),
        }
    )

    matchup["teams"]["away"].update(
        {
            "id": str(fg.get("away_team_id", matchup["teams"]["away"]["id"])),
            "name": fg["away_team"],
            "abbreviation": fg["away_team_abbr"],
        }
    )
    matchup["teams"]["home"].update(
        {
            "id": str(fg.get("home_team_id", matchup["teams"]["home"]["id"])),
            "name": fg["home_team"],
            "abbreviation": fg["home_team_abbr"],
        }
    )

    _apply_live_starter(matchup["starters"]["away_starter"], away, fg["away_team_abbr"], fg.get("away_pitcher_id"))
    _apply_live_starter(matchup["starters"]["home_starter"], home, fg["home_team_abbr"], fg.get("home_pitcher_id"))

    _apply_offense_split(
        matchup["teams"]["home"]["offense_profile"],
        live_game.get("home_team_splits", {}),
        away.get("throws", "R"),
    )
    _apply_offense_split(
        matchup["teams"]["away"]["offense_profile"],
        live_game.get("away_team_splits", {}),
        home.get("throws", "L"),
    )

    matchup["charts"]["pitch_mix"] = live_game["combined_charts"]["pitch_mix"]
    matchup["charts"]["velocity_by_pitch"] = live_game["combined_charts"]["velocity_by_pitch"]
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
    starter["bio"]["throws"] = throws
    starter["season_summary"].update(live_starter["season_summary"])
    starter["pitching_profile"].update(live_starter["pitching_profile"])
    _sanitize_pitching_profile(starter)


def _sanitize_pitching_profile(starter: dict[str, Any]) -> None:
    profile = starter["pitching_profile"]
    season = starter["season_summary"]
    if _is_placeholder_label(profile.get("command_label")):
        profile["command_label"] = _derive_command_label(_safe_int(season.get("walks")))
    if _is_placeholder_label(profile.get("swing_miss_label")):
        profile["swing_miss_label"] = _derive_swing_miss_label(_safe_int(season.get("strikeouts")))
    if _is_placeholder_label(profile.get("contact_risk_label")):
        profile["contact_risk_label"] = _derive_contact_risk_label(_safe_int(season.get("home_runs_allowed")))


def _is_placeholder_label(value: Any) -> bool:
    return not value or str(value).strip().lower() == "see live data"


def _derive_swing_miss_label(strikeouts: int) -> str:
    if strikeouts >= 80:
        return "Above-average swing-and-miss ability"
    if strikeouts >= 40:
        return "Moderate swing-and-miss ability"
    return "Limited swing-and-miss data available"


def _derive_command_label(walks: int) -> str:
    if walks <= 25:
        return "Solid command this season"
    if walks <= 40:
        return "Average command this season"
    return "Below-average command this season"


def _derive_contact_risk_label(home_runs: int) -> str:
    if home_runs <= 8:
        return "Limited hard contact allowed"
    if home_runs <= 15:
        return "Moderate contact risk"
    return "Elevated contact risk"


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _apply_offense_split(
    offense_profile: dict[str, Any],
    splits: dict[str, Any],
    starter_hand: str,
) -> None:
    hand = starter_hand if starter_hand in ("L", "R") else starter_hand[:1]
    split = splits.get("vl" if hand == "L" else "vr", {})
    if not split:
        offense_profile["vs_pitcher_hand"] = f"{hand}HP"
        return

    offense_profile["summary_label"] = f"Real season split vs {hand}HP"
    offense_profile["vs_pitcher_hand"] = f"{hand}HP"
    offense_profile["ops_vs_hand"] = _format_ops(split.get("ops"))
    offense_profile["k_rate_vs_hand"] = _format_pct(split.get("k_rate"))
    offense_profile["bb_rate_vs_hand"] = _format_pct(split.get("bb_rate"))
    offense_profile["recent_form"] = "Season split"


def _format_ops(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("0."):
            return stripped[1:]
        return stripped
    return f"{float(value):.3f}".replace("0.", ".", 1)


def _format_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    return f"{float(value):.1f}%"


def _live_confidence_note(matchup_id: str) -> dict[str, Any]:
    return {
        "level": "fetched_snapshot",
        "lineup_status": "probable_pitchers",
        "pitch_data_status": "fetched_snapshot",
        "notes": [
            f"Live snapshot fetched {_live['fetched_date']} for {matchup_id}.",
            "If live fetching fails, PitchCraft falls back to cached demo data.",
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
