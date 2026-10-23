"""Deterministic Postgame Grader Agent for completed PitchCraft matchups.

The numeric value is the original Bill James Game Score, introduced in 1988
and still used as a public, reproducible single-game starting pitcher metric.
PitchCraft's letter grade is only a readability layer on top of that score.

This module is intentionally rule-based: no LLM calls, no APIs, and no
randomness. It evaluates the starting pitcher line, not the team result.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog, catalog_for
from data_pipeline.schema import STARTER_SLOTS


def parse_ip(ip: str) -> tuple[int, int]:
    """Parse an innings string such as '6.2' into full innings and partial outs."""

    full_raw, separator, partial_raw = ip.partition(".")
    full_innings = int(full_raw)
    partial_outs = int(partial_raw) if separator else 0
    if partial_outs not in (0, 1, 2):
        raise ValueError(f"Invalid innings pitched partial outs: {ip!r}")
    return full_innings, partial_outs


def game_score(line: dict[str, Any]) -> int:
    """
    Original Bill James Game Score (1988).

    outs = full_innings*3 + partial_outs
    innings_after_4th = max(0, full_innings - 4)
    score = 50 + outs + 2*innings_after_4th + strikeouts
            - 2*hits_allowed - 4*earned_runs - 2*unearned_runs - walks

    Note: the original James formula does not use home runs separately.
    The integer score is returned unclamped.
    """

    full_innings, partial_outs = parse_ip(line["innings_pitched"])
    outs = full_innings * 3 + partial_outs
    innings_after_4th = max(0, full_innings - 4)
    return (
        50
        + outs
        + 2 * innings_after_4th
        + int(line["strikeouts"])
        - 2 * int(line["hits_allowed"])
        - 4 * int(line["earned_runs"])
        - 2 * int(line["unearned_runs"])
        - int(line["walks"])
    )


def run(matchup_input: dict[str, Any], language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Return generated postgame grading output for a final matchup, written in `language`."""

    t = catalog_for(language)
    raw_postgame = matchup_input.get("postgame")
    if not isinstance(raw_postgame, dict):
        raise ValueError(f"{matchup_input.get('id', '<unknown>')} is missing raw postgame facts")

    raw_lines = raw_postgame.get("starter_lines")
    if not isinstance(raw_lines, dict):
        raise ValueError(f"{matchup_input.get('id', '<unknown>')} is missing starter lines")

    starter_lines: dict[str, dict[str, Any]] = {}
    for slot in STARTER_SLOTS:
        line = deepcopy(raw_lines[slot])
        score = game_score(line)
        line["game_score"] = score
        line["pitchcraft_grade"] = pitchcraft_grade(score)
        starter = matchup_input["starters"][slot]
        with t.subject(slot):
            line["grade_explanation"] = _grade_explanation(t, score)
            line["plan_vs_execution"] = _plan_vs_execution(t, starter, line)
            line["what_to_watch_next"] = _what_to_watch_next(t, starter, line)
        starter_lines[slot] = line

    duel_winner_slot = _starter_duel_winner_slot(starter_lines)
    return {
        "final_score": deepcopy(raw_postgame["final_score"]),
        "starter_lines": starter_lines,
        "starter_duel_winner": starter_lines[duel_winner_slot]["name"],
        "call_check": _call_check(t, matchup_input, starter_lines),
    }


def pitchcraft_grade(score: int) -> str:
    """Map Game Score to PitchCraft's fan-readable letter grade."""

    if score >= 85:
        return "A+"
    if score >= 75:
        return "A"
    if score >= 68:
        return "A-"
    if score >= 62:
        return "B+"
    if score >= 56:
        return "B"
    if score >= 50:
        return "B-"
    if score >= 45:
        return "C+"
    if score >= 40:
        return "C"
    if score >= 35:
        return "C-"
    if score >= 28:
        return "D"
    return "F"


def _starter_duel_winner_slot(starter_lines: dict[str, dict[str, Any]]) -> str:
    def sort_key(slot: str) -> tuple[int, int]:
        line = starter_lines[slot]
        full_innings, partial_outs = parse_ip(line["innings_pitched"])
        return int(line["game_score"]), full_innings * 3 + partial_outs

    return max(STARTER_SLOTS, key=sort_key)


def _grade_explanation(t: Catalog, score: int) -> str:
    if score >= 68:
        return t("grader.explanation.standout", score=score)
    if score >= 56:
        return t("grader.explanation.solid", score=score)
    if score >= 45:
        return t("grader.explanation.mixed", score=score)
    if score >= 35:
        return t("grader.explanation.rough", score=score)
    return t("grader.explanation.difficult", score=score)


def _plan_vs_execution(t: Catalog, starter: dict[str, Any], line: dict[str, Any]) -> str:
    profile = starter["pitching_profile"]
    primary = profile["primary_pitch"].lower()
    putaway = profile["putaway_pitch"].lower()
    walks = t.count("walk", line["walks"])
    earned_runs = t.count("earned_run", line["earned_runs"])

    if int(line["walks"]) <= 1 and int(line["earned_runs"]) <= 2:
        return t("grader.plan.matched", primary=primary, putaway=putaway, walks=walks, earned_runs=earned_runs)
    if int(line["walks"]) >= 3:
        return t("grader.plan.walks", primary=primary, putaway=putaway, walks=walks)
    return t(
        "grader.plan.partial",
        primary=primary,
        putaway=putaway,
        hits=t.count("hit", line["hits_allowed"]),
        earned_runs=earned_runs,
    )


def _what_to_watch_next(t: Catalog, starter: dict[str, Any], line: dict[str, Any]) -> str:
    profile = starter["pitching_profile"]
    if int(line["walks"]) >= 3:
        return t("grader.next.walks")
    if int(line["hits_allowed"]) >= 7:
        return t("grader.next.hits")
    if int(line["earned_runs"]) >= 4:
        return t("grader.next.runs")
    # Only the "Average ..." label: "Above-average" and "Below-average" also contain "average".
    swing_miss = (profile.get("swing_miss_label") or "").lower()
    if int(line["strikeouts"]) <= 3 and swing_miss.startswith("average"):
        return t("grader.next.chase", putaway=profile["putaway_pitch"].lower())
    return t("grader.next.default")


def _call_check(
    t: Catalog,
    matchup_input: dict[str, Any],
    starter_lines: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    away_starter = matchup_input["starters"]["away_starter"]
    home_starter = matchup_input["starters"]["home_starter"]
    away_line = starter_lines["away_starter"]
    home_line = starter_lines["home_starter"]

    with t.subject("home_starter"):
        command = _command_check(t, home_starter, home_line)
    with t.subject("away_starter"):
        walk_risk = _walk_risk_check(t, away_starter, away_line)
        swing_miss = _swing_miss_check(t, away_starter, away_line)
    return [command, walk_risk, swing_miss]


def _command_check(t: Catalog, starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    walks = int(line["walks"])
    result = "held_up" if walks <= 1 else "partially_held_up" if walks <= 3 else "did_not_hold_up"
    return {
        "pregame_note": t("grader.call.command.note", name=starter["name"]),
        "result": result,
        "postgame_evidence": t(
            "grader.call.command.evidence", walks=t.count("walk", walks), innings=line["innings_pitched"]
        ),
    }


def _walk_risk_check(t: Catalog, starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    walks = int(line["walks"])
    result = "held_up" if walks >= 3 else "partially_held_up" if walks == 2 else "did_not_hold_up"
    return {
        "pregame_note": t("grader.call.walk_risk.note", name=starter["name"]),
        "result": result,
        "postgame_evidence": t(
            "grader.call.walk_risk.evidence", batters=t.count("batter", walks), innings=line["innings_pitched"]
        ),
    }


def _swing_miss_check(t: Catalog, starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    strikeouts = int(line["strikeouts"])
    score = int(line["game_score"])
    result = "held_up" if strikeouts >= 6 else "partially_held_up" if strikeouts >= 4 else "did_not_hold_up"
    return {
        "pregame_note": t("grader.call.swing_miss.note", name=starter["name"]),
        "result": result,
        "postgame_evidence": t(
            "grader.call.swing_miss.evidence", strikeouts=t.count("strikeout", strikeouts), score=score
        ),
    }
