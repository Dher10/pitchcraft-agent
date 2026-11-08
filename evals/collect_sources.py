"""P2.4 gate 4a: the two MLB adapters of the dataset collection (docs/plans/P2.4.md sections 2 and 4).

Neither makes a request of its own kind: both read through `live_pipeline._get_json`, which `request_ledger.counted_mlb`
wraps, so every request is reserved in the ledger before it is sent and a cache hit costs nothing.

- `fetch_schedule`: one request per calendar-month range, the final games of the range with their listed starters.
- `fetch_history`: ONE request per pitcher and season (`people/{id}/stats?stats=gameLog,yearByYear`). Its answer carries
  every start of the season and every earlier season, so it serves the sample counts, the innings of the previous
  starts (the opener test) and the prior-seasons count (the veteran test) of every game that pitcher starts; it is
  cached on disk and read again for free. Facts for a game use only rows dated before the game (`as_of`, D29).

The shape of the `gameLog` and `yearByYear` answers is written from the Stats API documentation: the sandbox that wrote
this module had no network, so no answer of these two kinds was recorded. `HISTORY` is strict and fails closed
(`SourceShapeError`, never a default), so the first real lookup either matches it or stops the collection with one
request used.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from data_pipeline import labels, schema
from data_pipeline.fetchers import live_pipeline, mlb_schemas
from data_pipeline.fetchers.mlb_schemas import Arr, Obj, Scalar, SourceShapeError
from evals import build_dataset as bd

SCHEDULE_URL = (
    "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start}&endDate={end}"
    "&gameType={types}&hydrate=probablePitcher"
)
HISTORY_URL = (
    "https://statsapi.mlb.com/api/v1/people/{pitcher_id}/stats"
    "?stats=gameLog,yearByYear&group=pitching&season={season}&sportId=1"
)
GAME_TYPES = "R,F,D,L,W"  # regular season and the four postseason rounds

_PROBABLE = Obj({"id": Scalar("int"), "fullName": Scalar("str")}, required=False)
SCHEDULE = Obj(
    {
        "dates": Arr(
            Obj(
                {
                    "games": Arr(
                        Obj(
                            {
                                "gamePk": Scalar("int"),
                                "gameType": Scalar("str"),
                                "officialDate": Scalar("date"),
                                "seriesGameNumber": Scalar("positive", required=False),
                                "status": Obj({"abstractGameState": Scalar("str"), "detailedState": Scalar("str")}),
                                "teams": Obj(
                                    {
                                        side: Obj({"team": Obj({"id": Scalar("int")}), "probablePitcher": _PROBABLE})
                                        for side in ("away", "home")
                                    }
                                ),
                            }
                        )
                    )
                }
            )
        )
    }
)

_LINE = Obj(
    {
        "inningsPitched": Scalar("text", required=False),
        "battersFaced": Scalar("count", required=False),
        "gamesStarted": Scalar("count", required=False),
        "gamesPlayed": Scalar("count", required=False),
    }
)
HISTORY = Obj(
    {
        "stats": Arr(
            Obj(
                {
                    "type": Obj({"displayName": Scalar("str")}),
                    "splits": Arr(Obj({"season": Scalar("str", required=False), "date": Scalar("date", required=False), "stat": _LINE})),
                }
            )
        )
    }
)


class HistoryMissing(FileNotFoundError):
    """A packet needs the cached history of a pitcher and there is none; the build never asks for it."""


@dataclass(frozen=True)
class ListedGame:
    game_pk: int
    official_date: str
    game_type: str
    series_game_number: int | None
    final: bool
    starters: tuple  # (pitcher_id, name) per side, away first; None for a side with no listed starter
    teams: tuple = ()  # (away team id, home team id)


@dataclass(frozen=True)
class Appearance:
    date: str
    innings: float | None
    batters_faced: int | None
    started: bool


@dataclass(frozen=True)
class History:
    pitcher_id: int
    appearances: tuple
    prior_seasons: int | None  # None: the answer did not say, which is unknown and never zero


def _digest(response: Any) -> str:
    return hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def fetch_schedule(start: date, end: date, game_types: str = GAME_TYPES, cache_dir=None) -> list[ListedGame]:
    """The games of [start, end] in one request. `final` follows the published status table, so a postponed or cancelled game is not final.

    With `cache_dir` the answer is kept on disk with its fetch time and digest and read again for free, so a re-run of
    the same ranges (the same collection date) costs no request. A malformed answer is never cached.
    """

    url = SCHEDULE_URL.format(start=start.isoformat(), end=end.isoformat(), types=game_types)
    path = Path(cache_dir) / f"schedule_{start.isoformat()}_{end.isoformat()}_{game_types.replace(',', '')}.json" if cache_dir else None
    if path is not None and path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
        if _digest(record["response"]) != record["sha256"]:
            raise SourceShapeError(f"cached schedule {path.name} does not match its digest")
        data = record["response"]
        mlb_schemas.validate(SCHEDULE, data, "cached collection schedule response")
        return _schedule_games(data)
    data = live_pipeline._get_json(url)
    mlb_schemas.validate(SCHEDULE, data, "collection schedule response")
    games = _schedule_games(data)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {"url": url, "fetched_at": round(time.time(), 3), "sha256": _digest(data), "response": data}
        path.write_text(json.dumps(record, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    return games


def _schedule_games(data: dict) -> list[ListedGame]:
    games = []
    for entry in data["dates"]:
        for game in entry["games"]:
            pitchers = []
            for side in ("away", "home"):
                listed = game["teams"][side].get("probablePitcher")
                pitchers.append((listed["id"], listed["fullName"]) if listed else None)
            games.append(
                ListedGame(
                    game_pk=game["gamePk"],
                    official_date=game["officialDate"],
                    game_type=game["gameType"],
                    series_game_number=game.get("seriesGameNumber"),
                    final=schema.game_status(game["status"]["abstractGameState"], game["status"]["detailedState"]) == "final",
                    starters=tuple(pitchers),
                    teams=(game["teams"]["away"]["team"]["id"], game["teams"]["home"]["team"]["id"]),
                )
            )
    return games


def _appearance(split: dict) -> Appearance:
    stat = split["stat"]
    if "date" not in split:
        raise SourceShapeError("game log split has no date")
    return Appearance(
        date=split["date"],
        innings=bd.innings_from_ip(stat.get("inningsPitched")),
        batters_faced=stat.get("battersFaced"),
        started=stat.get("gamesStarted") == 1,
    )


def parse_history(pitcher_id: int, data: Any, season: int) -> History:
    mlb_schemas.validate(HISTORY, data, "collection pitcher history response")
    by_type = {block["type"]["displayName"]: block["splits"] for block in data["stats"]}
    if "gameLog" not in by_type:
        raise SourceShapeError("pitcher history response has no gameLog block")
    appearances = tuple(sorted((_appearance(s) for s in by_type["gameLog"]), key=lambda a: a.date))
    prior = None
    if "yearByYear" in by_type:
        seasons = set()
        for split in by_type["yearByYear"]:
            if "season" not in split or not split["season"].isdigit():
                raise SourceShapeError("year-by-year split has no season")
            played = split["stat"].get("gamesPlayed")
            if int(split["season"]) < season and played is not None and played > 0:
                seasons.add(int(split["season"]))
        prior = len(seasons)
    return History(pitcher_id, appearances, prior)


class HistoryStore:
    """The per-pitcher answer, fetched once through the ledger and kept on disk with its fetch time and digest."""

    def __init__(self, directory, season: int) -> None:
        self.directory = Path(directory)
        self.season = season
        self.memory: dict[int, History] = {}
        self.lookups = 0  # requests this store sent (a read from disk or memory is not one)

    def _path(self, pitcher_id: int) -> Path:
        return self.directory / f"{pitcher_id}_{self.season}.json"

    def known(self, pitcher_id: int) -> bool:
        """True when `get` costs no request: the answer is in memory or in the disk cache."""

        return pitcher_id in self.memory or self._path(pitcher_id).exists()

    def _record(self, pitcher_id: int) -> dict:
        """The cached record of a pitcher, digest-checked. Never a request: a missing file is `HistoryMissing`."""

        path = self._path(pitcher_id)
        if not path.exists():
            raise HistoryMissing(f"no cached history for pitcher {pitcher_id} (season {self.season}); the packet build never fetches")
        record = json.loads(path.read_text(encoding="utf-8"))
        body = json.dumps(record["response"], sort_keys=True, separators=(",", ":"))
        if hashlib.sha256(body.encode("utf-8")).hexdigest() != record["sha256"]:
            raise SourceShapeError(f"cached history of {pitcher_id} does not match its digest")
        return record

    def cached_response(self, pitcher_id: int) -> dict:
        """The raw `gameLog,yearByYear` answer from disk (the packet's season line is derived from it)."""

        return self._record(pitcher_id)["response"]

    def cached_digest(self, pitcher_id: int) -> str:
        return self._record(pitcher_id)["sha256"]

    def get(self, pitcher_id: int) -> History:
        if pitcher_id in self.memory:
            return self.memory[pitcher_id]
        path = self._path(pitcher_id)
        if path.exists():
            record = json.loads(path.read_text(encoding="utf-8"))
            body = json.dumps(record["response"], sort_keys=True, separators=(",", ":"))
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != record["sha256"]:
                raise SourceShapeError(f"cached history of {pitcher_id} does not match its digest")
        else:
            url = HISTORY_URL.format(pitcher_id=pitcher_id, season=self.season)
            self.lookups += 1  # counted before the request: a failed one used the ledger too
            response = live_pipeline._get_json(url)
            body = json.dumps(response, sort_keys=True, separators=(",", ":"))
            record = {"url": url, "fetched_at": round(time.time(), 3), "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "response": response}
            history = parse_history(pitcher_id, response, self.season)  # a malformed answer is never cached
            self.directory.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
            self.memory[pitcher_id] = history
            return history
        history = parse_history(pitcher_id, record["response"], self.season)
        self.memory[pitcher_id] = history
        return history


def facts_as_of(history: History, official_date: str) -> bd.StarterFacts:
    """The starter's facts before `official_date`: only appearances dated before the game count (as_of is the day before)."""

    game = date.fromisoformat(official_date)
    before = [a for a in history.appearances if date.fromisoformat(a.date) < game]
    bd.reject_rows_on_or_after([a.date for a in before], official_date)  # belt and braces: nothing from the game day on
    known = [a.batters_faced for a in before]
    batters = sum(known) if before and all(n is not None for n in known) else (0 if not before else None)
    samples = {
        "strikeout": batters,
        "control": batters,
        # Pitches are not in this answer. Every batter faced took at least one pitch, so batters faced is a lower
        # bound: it proves a dimension at or above its threshold and says nothing below it.
        "arsenal": batters if batters is not None and batters >= labels.THRESHOLDS["arsenal"] else None,
    }
    return bd.StarterFacts(
        pitcher_id=history.pitcher_id,
        samples=samples,
        prior_seasons=history.prior_seasons,
        previous_innings=tuple(a.innings for a in before if a.started),
        flagged_opener=False,  # the schedule answer carries no opener flag (see the plan, section 2)
    )


@dataclass(frozen=True)
class CachedGame:
    raw: dict  # the game exactly as the schedule answered
    file: str  # the cache file it came from
    sha256: str  # the digest of that file's answer


def cached_schedule(cache_dir) -> dict[int, CachedGame]:
    """game_pk -> the raw game from the schedule answers on disk, each file digest-checked. Never a request.

    A game that appears twice (postponed, then replayed) keeps its final row; among final rows the later file wins."""

    games: dict[int, CachedGame] = {}
    for path in sorted(Path(cache_dir).glob("schedule_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if _digest(record["response"]) != record["sha256"]:
            raise SourceShapeError(f"cached schedule {path.name} does not match its digest")
        mlb_schemas.validate(SCHEDULE, record["response"], "cached collection schedule response")
        for entry in record["response"]["dates"]:
            for game in entry["games"]:
                final = schema.game_status(game["status"]["abstractGameState"], game["status"]["detailedState"]) == "final"
                earlier = games.get(game["gamePk"])
                if earlier is None or final or not _is_final(earlier.raw):
                    games[game["gamePk"]] = CachedGame(game, path.name, record["sha256"])
    return games


def _is_final(game: dict) -> bool:
    return schema.game_status(game["status"]["abstractGameState"], game["status"]["detailedState"]) == "final"
