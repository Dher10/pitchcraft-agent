"""The per-starter history of the archive backfill (R4-D4; D66): one `gameLog,yearByYear` answer per pitcher.

It gives two things, from one request per starter instead of one per game:

- the starter's regular-season line **as of the day before a game**, summed from the game-log rows dated strictly before
  the game (D29: a row on the game date is never summed), in the shape `fetch_pitcher_season_stats` returns;
- the number of earlier MLB seasons he pitched in (the veteran rule of the notable duels, docs/plans/R4.md 4.6).

Ported from the P2.4 collection (`evals/collect_sources.py`, `evals/build_packets.py`) so that R4 imports nothing from
`evals/` (D64). The answer is kept on disk with its fetch time and its SHA-256, and a record that no longer matches its
digest is refused. A malformed answer is never cached and never defaulted: unknown is `{}` or `None`, never zero.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any

from data_pipeline.fetchers import mlb_schemas
from data_pipeline.fetchers.mlb_schemas import Arr, Obj, Scalar, SourceShapeError

HISTORY_URL = (
    "https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    "?stats=gameLog,yearByYear&group=pitching&season={season}&sportId=1"
)
_OUTS = re.compile(r"(?P<whole>[0-9]+)(?:\.(?P<outs>[012]))?", re.ASCII)
_COUNTS = ("earnedRuns", "hits", "baseOnBalls", "strikeOuts", "homeRuns", "battersFaced")

HISTORY = Obj(
    {
        "stats": Arr(
            Obj(
                {
                    "type": Obj({"displayName": Scalar("str")}),
                    "splits": Arr(
                        Obj(
                            {
                                "season": Scalar("str", required=False),
                                "date": Scalar("date", required=False),
                                "gameType": Scalar("str", required=False),
                                "stat": Obj(
                                    {
                                        "inningsPitched": Scalar("text", required=False),
                                        "gamesPlayed": Scalar("count", required=False),
                                        **{name: Scalar("count", required=False) for name in _COUNTS},
                                    }
                                ),
                            }
                        )
                    ),
                }
            )
        )
    }
)


class HistoryMissing(FileNotFoundError):
    """No cached answer for a pitcher and the caller may not fetch."""


def _blocks(response: Any) -> dict[str, list[Any]]:
    mlb_schemas.validate(HISTORY, response, "archive pitcher history response")
    return {block["type"]["displayName"]: block["splits"] for block in response["stats"]}


def _outs(text: Any) -> int | None:
    match = _OUTS.fullmatch(text) if isinstance(text, str) else None
    return int(match["whole"]) * 3 + int(match["outs"] or 0) if match else None


def _count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _ratio(numerator: int, outs: int) -> str:
    return format((Decimal(numerator) / Decimal(outs)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def season_line_as_of(response: Any, official_date: str) -> dict[str, Any]:
    """
    The starter's regular-season line over the game-log rows dated STRICTLY before `official_date`, with the keys of
    `fetch_pitcher_season_stats`. `{}` (unavailable, never zero) when no row is before the date, or when any row before it
    lacks a figure, a game type or a readable innings text. A row on the game date or later is never summed.
    """

    game_day = date.fromisoformat(official_date)
    blocks = _blocks(response)
    if "gameLog" not in blocks:
        raise SourceShapeError("the history answer has no gameLog block")
    outs = earned = hits = walks = strikeouts = homers = faced = rows = 0
    for split in blocks["gameLog"]:
        if "date" not in split:
            return {}
        if date.fromisoformat(split["date"]) >= game_day:
            continue
        if split.get("gameType") is None:
            return {}
        if split["gameType"] != "R":
            continue
        stat = split["stat"]
        row_outs = _outs(stat.get("inningsPitched"))
        if row_outs is None or not all(_count(stat.get(key)) for key in _COUNTS):
            return {}
        outs += row_outs
        earned += stat["earnedRuns"]
        hits += stat["hits"]
        walks += stat["baseOnBalls"]
        strikeouts += stat["strikeOuts"]
        homers += stat["homeRuns"]
        faced += stat["battersFaced"]
        rows += 1
    if rows == 0:
        return {}
    return {
        "era": _ratio(27 * earned, outs) if outs else "-.--",
        "whip": _ratio(3 * (hits + walks), outs) if outs else "-.--",
        "innings": f"{outs // 3}.{outs % 3}",
        "strikeouts": strikeouts,
        "walks": walks,
        "home_runs_allowed": homers,
        "batters_faced": faced,
    }


def prior_seasons(response: Any, season: int) -> int | None:
    """
    How many seasons before `season` the pitcher pitched in (a season counts when he played in at least one game).
    `None` when the answer has no `yearByYear` block: unknown, never 0.
    """

    blocks = _blocks(response)
    if "yearByYear" not in blocks:
        return None
    seasons = set()
    for split in blocks["yearByYear"]:
        if "season" not in split or not split["season"].isdigit():
            raise SourceShapeError("year-by-year split has no season")
        if int(split["season"]) >= season:
            continue
        played = split["stat"].get("gamesPlayed")
        if played is None:
            return None  # an earlier season with no games figure: the count is unknown, never a smaller number
        if played > 0:
            seasons.add(int(split["season"]))
    return len(seasons)


def _write_atomically(path: Path, text: str) -> None:
    """Replace `path` in one step: a kill half way never leaves truncated JSON that every later game would trip on."""

    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _digest(response: Any) -> str:
    return hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class HistoryStore:
    """
    The per-pitcher answer, fetched once through `fetch` (which counts the request) and kept on disk. `fetch` is given the
    URL and returns the parsed JSON; tests give a fake, the builder gives the counted MLB request.
    """

    def __init__(self, directory: Path | str, season: int, fetch: Callable[[str], Any]) -> None:
        self.directory = Path(directory)
        self.season = season
        self._fetch = fetch
        self.memory: dict[int, Any] = {}
        self.lookups = 0  # requests this store sent (a read from disk or memory is not one)

    def _path(self, pitcher_id: int) -> Path:
        return self.directory / f"{pitcher_id}_{self.season}.json"

    def known(self, pitcher_id: int) -> bool:
        return pitcher_id in self.memory or self._path(pitcher_id).exists()

    def response(self, pitcher_id: int) -> Any:
        """The answer for a pitcher: memory, then disk (digest-checked), then one request. A bad answer is never cached."""

        if not isinstance(pitcher_id, int) or isinstance(pitcher_id, bool) or pitcher_id <= 0:
            raise ValueError("pitcher id must be a positive integer")
        if pitcher_id in self.memory:
            return self.memory[pitcher_id]
        path = self._path(pitcher_id)
        url = HISTORY_URL.format(pitcher_id=pitcher_id, season=self.season)
        if path.exists():
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                valid = (isinstance(record, dict) and set(record) == {"url", "fetched_at", "sha256", "response"}
                         and record["url"] == url and _digest(record["response"]) == record["sha256"])
            except (ValueError, TypeError):
                valid = False
            if not valid:
                raise SourceShapeError("cached history identity or digest is invalid")
            response = record["response"]
            _blocks(response)
        else:
            self.lookups += 1  # counted before the request: a failed one used the ceiling too
            response = self._fetch(url)
            _blocks(response)  # a malformed answer raises here and is never written
            record = {"url": url, "fetched_at": round(time.time(), 3), "sha256": _digest(response), "response": response}
            self.directory.mkdir(parents=True, exist_ok=True)
            _write_atomically(path, json.dumps(record, sort_keys=True, indent=1) + "\n")
        self.memory[pitcher_id] = response
        return response

    def season_stats(self, pitcher_id: int, official_date: str) -> dict[str, Any]:
        """The line `fetch_pitcher_statcast(season_stats=...)` takes: as of the day before `official_date`."""

        return season_line_as_of(self.response(pitcher_id), official_date)

    def prior_seasons(self, pitcher_id: int) -> int | None:
        return prior_seasons(self.response(pitcher_id), self.season)
