"""The starter check and the final line, from one boxscore per game (R4-D4; D66; docs/plans/R4.md 4.2).

Pure: no network. One boxscore answer gives, for each side, who started and what he did; it costs no request beyond the
one the starter check already needs. Everything here is a **source value**: nothing is graded, scored or compared (D41).

The shape is checked strictly. It was written from the documented `GET /api/v1/game/{gamePk}/boxscore` answer
(`teams.<side>.pitchers`: ids in the order the pitchers appeared; `teams.<side>.players.ID<id>.person` and
`.stats.pitching`); **no real answer was recorded when this was written**, so the first real one either matches or stops
the build (a malformed answer is `starter_unconfirmed` for the game, never a guess). R4-D7's dry run is where it is first
seen.

Rules (contract section 7, rule 2): a starter is the first pitcher listed. A side whose first pitcher cannot be read, or
whose probable starter is unknown, is `unknown`, never `started`. A line field the boxscore does not give is `None`; a
real 0 stays 0. The line is that of the pitcher who started, and a probable starter who did not start gets
`did_not_start`, with the line of the one who did.
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from data_pipeline.archive_games import FINAL_LINE_FIELDS, SIDES

BOXSCORE_URL = "https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
_INNINGS = re.compile(r"[0-9]{1,2}(?:\.[0-2])?", re.ASCII)
_FIELDS = {"innings_pitched": "inningsPitched", "hits": "hits", "earned_runs": "earnedRuns", "walks": "baseOnBalls",
           "strikeouts": "strikeOuts"}


def boxscore_url(game_pk: int) -> str:
    if not isinstance(game_pk, int) or isinstance(game_pk, bool) or game_pk <= 0:
        raise ValueError("game_pk must be a positive integer")
    return BOXSCORE_URL.format(game_pk=game_pk)


def _count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _side(data: Any, side: str) -> Mapping[str, Any] | None:
    try:
        node = data["teams"][side]
    except (KeyError, TypeError):
        return None
    return node if isinstance(node, Mapping) else None


def _starter(node: Mapping[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any] | None] | None:
    """(who, his pitching stats) for the first pitcher listed, or None when it cannot be read."""

    if node is None:
        return None
    pitchers, players = node.get("pitchers"), node.get("players")
    if not (isinstance(pitchers, list) and pitchers and isinstance(players, Mapping)):
        return None
    pitcher_id = pitchers[0]
    if not (isinstance(pitcher_id, int) and not isinstance(pitcher_id, bool) and pitcher_id > 0):
        return None
    entry = players.get(f"ID{pitcher_id}")
    if not isinstance(entry, Mapping):
        return None
    person = entry.get("person")
    if not (isinstance(person, Mapping) and person.get("id") == pitcher_id
            and isinstance(person.get("fullName"), str) and person["fullName"].strip()):
        return None
    stats = (entry.get("stats") or {}).get("pitching") if isinstance(entry.get("stats"), Mapping) else None
    return {"id": pitcher_id, "name": person["fullName"]}, stats if isinstance(stats, Mapping) else None


def _line(stats: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The final line, field by field: a value only if it has its type, else None. None for the whole line if no stats."""

    if stats is None:
        return None
    line: dict[str, Any] = {}
    for name, key in _FIELDS.items():
        value = stats.get(key)
        if name == "innings_pitched":
            line[name] = value if isinstance(value, str) and _INNINGS.fullmatch(value) else None
        else:
            line[name] = value if _count(value) else None
    return line if set(line) == set(FINAL_LINE_FIELDS) else None


def starters_and_lines(data: Any, probable_ids: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    `(starters_check, final_line)` of a game from its boxscore and the ids of the starters the report is about.

    `probable_ids` maps `away` and `home` to the report's starter id (or None). An unreadable answer gives every side
    `unknown` with no line.
    """

    check: dict[str, Any] = {"away": "unknown", "home": "unknown", "actual": {"away": None, "home": None}}
    final: dict[str, Any] = {"away": None, "home": None}
    for side in SIDES:
        found = _starter(_side(data, side))
        probable = probable_ids.get(side)
        if found is None or not (isinstance(probable, int) and not isinstance(probable, bool)):
            continue
        who, stats = found
        check[side] = "started" if who["id"] == probable else "did_not_start"
        check["actual"][side] = who
        final[side] = _line(stats)
    return check, final
