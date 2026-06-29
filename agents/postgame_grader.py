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


def run(matchup_input: dict[str, Any]) -> dict[str, Any]:
    """Return generated postgame grading output for a final matchup."""

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
        line["grade_explanation"] = _grade_explanation(line, score)
        line["plan_vs_execution"] = _plan_vs_execution(starter, line)
        line["what_to_watch_next"] = _what_to_watch_next(starter, line)
        starter_lines[slot] = line

    duel_winner_slot = _starter_duel_winner_slot(starter_lines)
    return {
        "final_score": deepcopy(raw_postgame["final_score"]),
        "starter_lines": starter_lines,
        "starter_duel_winner": starter_lines[duel_winner_slot]["name"],
        "call_check": _call_check(matchup_input, starter_lines),
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


def _grade_explanation(line: dict[str, Any], score: int) -> str:
    if score >= 68:
        return (
            f"A Game Score of {score} reflects a standout start - he worked deep, "
            "missed bats, and controlled the run damage."
        )
    if score >= 56:
        return (
            f"A Game Score of {score} reflects a solid, above-average start - he worked "
            "deep, limited walks, and kept the damage in check."
        )
    if score >= 45:
        return (
            f"A Game Score of {score} reflects a mixed start - there were useful innings, "
            "but traffic kept it from becoming a clean outing."
        )
    if score >= 35:
        return (
            f"A Game Score of {score} reflects a rough outing - the hits and walks piled "
            "up and shortened his night."
        )
    return (
        f"A Game Score of {score} reflects a difficult outing - too much traffic and "
        "run damage overwhelmed the bright spots."
    )


def _plan_vs_execution(starter: dict[str, Any], line: dict[str, Any]) -> str:
    profile = starter["pitching_profile"]
    primary = profile["primary_pitch"].lower()
    putaway = profile["putaway_pitch"].lower()

    if int(line["walks"]) <= 1 and int(line["earned_runs"]) <= 2:
        return (
            f"The plan was to command the {primary} and finish with the {putaway}; "
            f"{_plural(line['walks'], 'walk')} and {_plural(line['earned_runs'], 'earned run')} "
            "show the execution mostly matched it."
        )
    if int(line["walks"]) >= 3:
        return (
            f"The plan was to use the {primary} to reach {putaway} counts, but "
            f"{_plural(line['walks'], 'walk')} kept him from controlling the sequence."
        )
    return (
        f"The plan was built around the {primary} and {putaway}, but "
        f"{_plural(line['hits_allowed'], 'hit')} and {_plural(line['earned_runs'], 'earned run')} "
        "left only partial execution."
    )


def _what_to_watch_next(starter: dict[str, Any], line: dict[str, Any]) -> str:
    profile = starter["pitching_profile"]
    if int(line["walks"]) >= 3:
        return "The next checkpoint is tightening strike-zone control before traffic builds."
    if int(line["hits_allowed"]) >= 7:
        return "The next checkpoint is limiting contact before counts turn stressful."
    if int(line["earned_runs"]) >= 4:
        return "The next checkpoint is cutting off big innings after the first damage."
    if int(line["strikeouts"]) <= 3 and "average" in profile["swing_miss_label"].lower():
        return f"The next checkpoint is getting more chase from the {profile['putaway_pitch'].lower()}."
    return "The next checkpoint is repeating that walk suppression deep into another start."


def _call_check(
    matchup_input: dict[str, Any],
    starter_lines: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    away_starter = matchup_input["starters"]["away_starter"]
    home_starter = matchup_input["starters"]["home_starter"]
    away_line = starter_lines["away_starter"]
    home_line = starter_lines["home_starter"]

    return [
        _command_check(home_starter, home_line),
        _walk_risk_check(away_starter, away_line),
        _swing_miss_check(away_starter, away_line),
    ]


def _command_check(starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    walks = int(line["walks"])
    result = "held_up" if walks <= 1 else "partially_held_up" if walks <= 3 else "did_not_hold_up"
    return {
        "pregame_note": f"{starter['name']} needed his command edge to limit free passes.",
        "result": result,
        "postgame_evidence": (
            f"He issued {_plural(walks, 'walk')} over {line['innings_pitched']} innings."
        ),
    }


def _walk_risk_check(starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    walks = int(line["walks"])
    result = "held_up" if walks >= 3 else "partially_held_up" if walks == 2 else "did_not_hold_up"
    return {
        "pregame_note": f"{starter['name']} carried elevated walk risk.",
        "result": result,
        "postgame_evidence": (
            f"He walked {_plural(walks, 'batter')} and exited after {line['innings_pitched']} innings."
        ),
    }


def _swing_miss_check(starter: dict[str, Any], line: dict[str, Any]) -> dict[str, str]:
    strikeouts = int(line["strikeouts"])
    score = int(line["game_score"])
    result = "held_up" if strikeouts >= 6 else "partially_held_up" if strikeouts >= 4 else "did_not_hold_up"
    return {
        "pregame_note": f"{starter['name']} had swing-and-miss upside from the scouting profile.",
        "result": result,
        "postgame_evidence": (
            f"He recorded {_plural(strikeouts, 'strikeout')}, but the full line landed at "
            f"a Game Score of {score}."
        ),
    }


def _plural(value: int, singular: str) -> str:
    suffix = "" if value == 1 else "s"
    return f"{value} {singular}{suffix}"
