"""Game identity and results of the archive family (R4-D3; D66; docs/DATA_CONTRACT.md section 7).

Pure: no network and no file access. What it does:

- reads one day of the MLB schedule (`ARCHIVE_SCHEDULE_DAY`, validated whole) into game records: the `gamePk`, the round,
  the series line after the game, and the final score **only** for a game that ended (`schema.GAME_STATUS`, rule 7);
- keeps one record per game that was played (a postponed game is listed twice by the schedule, once as "Final" /
  "Postponed" and once on the day it was made up);
- recovers the `gamePk` of a report the daily job published (its id is `matchup_001` every day) by date, teams and
  starters, refusing zero or several candidate games;
- builds the envelope of a game file around a payload and checks its shape (`validate_game_file`).

The payload of a **reconstructed** report is judged by `validate_payload` and `check_contract` as it is for the daily
file. The payload of a **published_live** report was written under the catalogs of its day (other disclaimers, scope
labels and workflow grammar than today's: measured on the World Series game 1 file, which today's `validate_payload`
refuses), so it is not rejudged with today's text, as `archive.py` does for carried rows; its **values** are kept identical (the file
is re-serialized compact, so not byte for byte) and its lineage is recorded in `origin.source`: the commit and the
SHA-256 of the blob the bot committed, taken from the committed bytes (`parse_published`), never from a re-serialized copy. This module checks the
envelope and that lineage. Nothing here grades, scores or evaluates a game (D41).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import re
from typing import Any

from data_pipeline import series as series_module
from data_pipeline.fetchers import mlb_schemas
from data_pipeline.schema import READABLE_VERSIONS, game_status, is_utc_instant

ARCHIVE_VERSION = "1.0.0"
GAME_PK = re.compile(r"[1-9][0-9]{5,8}", re.ASCII)
POSTSEASON_GAME_TYPES = series_module.POSTSEASON_GAME_TYPES

# The round of a postseason game, from `gameType` (a closed table; anything else has no round).
ROUND_OF_TYPE: dict[str, str] = {
    "F": "Wild Card Series",
    "D": "Division Series",
    "L": "League Championship Series",
    "W": "World Series",
}

# The closed codes of rule 8 that this family adds (D66).
GAME_NOT_FOUND = "game_not_found"
STARTER_UNCONFIRMED = "starter_unconfirmed"
CEILING_REACHED = "ceiling_reached"
ARCHIVE_CODES = (GAME_NOT_FOUND, STARTER_UNCONFIRMED, CEILING_REACHED)

ORIGIN_KINDS = ("published_live", "reconstructed")
STARTER_STATES = ("started", "did_not_start", "unknown")
SIDES = ("away", "home")
FINAL_LINE_FIELDS = ("innings_pitched", "hits", "earned_runs", "walks", "strikeouts")
_INNINGS = re.compile(r"[0-9]{1,2}(?:\.[0-2])?", re.ASCII)

_TEAM_REF = mlb_schemas.Obj({"id": mlb_schemas.Scalar("int"), "name": mlb_schemas.Scalar("str")})

# schedule?sportId=1&date=...&gameType=F,D,L,W&hydrate=probablePitcher,venue(timezone),seriesStatus   (R4-D3)
# The fields the archive reads. Score and winner are optional because a game that did not end has none; a final game
# that lacks them has no result (the record says so), it is not an error of the day.
ARCHIVE_SCHEDULE_DAY = mlb_schemas.Obj(
    {
        "dates": mlb_schemas.Arr(
            mlb_schemas.Obj(
                {
                    "games": mlb_schemas.Arr(
                        mlb_schemas.Obj(
                            {
                                "gamePk": mlb_schemas.Scalar("positive"),
                                "gameType": mlb_schemas.Scalar("str"),
                                "officialDate": mlb_schemas.Scalar("date"),
                                "gameDate": mlb_schemas.Scalar("utc_instant"),
                                "status": mlb_schemas.Obj(
                                    {
                                        "abstractGameState": mlb_schemas.Scalar("str"),
                                        "detailedState": mlb_schemas.Scalar("str"),
                                    }
                                ),
                                "venue": mlb_schemas.Obj({"name": mlb_schemas.Scalar("str", required=False)}, required=False),
                                "seriesDescription": mlb_schemas.Scalar("str", required=False),
                                "seriesGameNumber": mlb_schemas.Scalar("positive", required=False),
                                "gamesInSeries": mlb_schemas.Scalar("positive", required=False),
                                "seriesStatus": mlb_schemas.Obj(
                                    {
                                        "isOver": mlb_schemas.Scalar("bool", required=False),
                                        "result": mlb_schemas.Scalar("str", required=False),
                                    },
                                    required=False,
                                ),
                                "teams": mlb_schemas.Obj(
                                    {
                                        side: mlb_schemas.Obj(
                                            {
                                                "team": _TEAM_REF,
                                                "score": mlb_schemas.Scalar("count", required=False),
                                                "isWinner": mlb_schemas.Scalar("bool", required=False),
                                                "probablePitcher": mlb_schemas._PROBABLE_PITCHER,
                                            }
                                        )
                                        for side in SIDES
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


class ArchiveError(ValueError):
    """A game or a file cannot be accepted; `code` is one of ARCHIVE_CODES (rule 8: never free text)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def is_game_pk(value: Any) -> bool:
    """True for the text of an id that names a game file. The only test before any path is built from an id."""

    return isinstance(value, str) and GAME_PK.fullmatch(value) is not None


def day_url(day: str) -> str:
    """The one request of a day of the backfill; `day` must be an ISO date."""

    if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
        raise ValueError("day must be YYYY-MM-DD")
    return (
        "https://statsapi.mlb.com/api/v1/schedule"
        f"?sportId=1&date={day}&gameType=F,D,L,W&hydrate=probablePitcher,venue(timezone),seriesStatus"
    )


def _count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def series_after(result: Any, is_over: Any, game_type: Any = None) -> str | None:
    """
    The standing **after** a game, as the schedule writes it, when it is a text the code knows whose numbers can be true.

    "X leads a-b" needs a > b and a series that is not over; "X wins a-b" needs a > b and a series that is over; "Series
    tied a-a" needs a series that is not over. Anything else is None (unavailable), never an unchecked string.
    """

    if not isinstance(result, str) or not isinstance(is_over, bool):
        return None
    match = series_module.STANDING.fullmatch(result)
    if match is None:
        return None
    if match["verb"] is not None:
        wins, losses = int(match["a"]), int(match["b"])
        if wins <= losses:
            return None
        if (match["verb"] == "wins") != is_over:
            return None
        return result
    if is_over or int(match["t"]) != int(match["u"]) or int(match["t"]) == 0:
        return None
    return result


def parse_day(data: Any) -> list[dict[str, Any]]:
    """
    Every game of one schedule answer as a record, in the schedule's order. Raises `SourceShapeError` for a malformed
    answer (recorded by the caller as a source failure); a valid empty day gives `[]`.
    """

    mlb_schemas.validate(ARCHIVE_SCHEDULE_DAY, data, "archive schedule response")
    return [game_record(game) for entry in data["dates"] for game in entry["games"]]


def game_record(game: Mapping[str, Any]) -> dict[str, Any]:
    """
    One schedule game. `status` is the published status of `schema.GAME_STATUS` (None when the pair is unknown). A score
    exists only for a game whose status is `final` and whose two scores are counts that agree with `isWinner`; otherwise
    `result` is None (rule 2: a missing or contradictory score is unavailable, never 0).
    """

    away, home = game["teams"]["away"], game["teams"]["home"]
    state = game["status"]
    status = game_status(state["abstractGameState"], state["detailedState"])
    game_type = game["gameType"]
    result = _result(status, away, home)
    after = None
    over = None
    standing = game.get("seriesStatus") or {}
    if game_type in POSTSEASON_GAME_TYPES:
        after = series_after(standing.get("result"), standing.get("isOver"))
        over = standing.get("isOver") if after is not None else None
    name = series_module.series_name(game.get("seriesDescription")) if game_type in POSTSEASON_GAME_TYPES else None
    length = game.get("gamesInSeries")
    if length not in series_module.SERIES_LENGTHS:
        length = None
    return {
        "game_pk": game["gamePk"],
        "date": game["officialDate"],
        "season": int(game["officialDate"][:4]),
        "game_type": game_type,
        "round": ROUND_OF_TYPE.get(game_type),
        "start_time_utc": game["gameDate"],
        "status": status,
        "result": result,
        "series": (
            {
                "series_name": name,
                "game_number": game.get("seriesGameNumber"),
                "games_in_series": length,
                "after": after,
                "over": over,
            }
            if name is not None
            else None
        ),
        "venue": (game.get("venue") or {}).get("name"),
        "teams": {
            side: {"id": entry["team"]["id"], "name": entry["team"]["name"]}
            for side, entry in (("away", away), ("home", home))
        },
        "probable": {
            side: ({"id": pp["id"], "name": pp["fullName"]} if (pp := entry.get("probablePitcher")) else None)
            for side, entry in (("away", away), ("home", home))
        },
    }


def _result(status: str | None, away: Mapping[str, Any], home: Mapping[str, Any]) -> dict[str, Any] | None:
    if status != "final":
        return None
    runs = {"away": away.get("score"), "home": home.get("score")}
    if not all(_count(value) for value in runs.values()):
        return None
    if runs["away"] == runs["home"]:
        return None  # a baseball game that ended has a winner; a tie here is not a result we can state
    winner = "away" if runs["away"] > runs["home"] else "home"
    flags = (away.get("isWinner"), home.get("isWinner"))
    if flags != (None, None) and flags != (winner == "away", winner == "home"):
        return None  # the schedule contradicts itself: unavailable, not a guess
    return {"away_runs": runs["away"], "home_runs": runs["home"], "winner": winner}


def played_games(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    One record per game that was **played**: status final **and** a result. A game seen twice (a postponed game is
    listed as Final/Postponed, then again on the day it was made up with the same `gamePk`) is kept once, in its played
    form; if two played records of one `gamePk` disagree the game is dropped (the caller records it).
    """

    kept: dict[int, dict[str, Any]] = {}
    conflicting: set[int] = set()
    for record in records:
        if record["status"] != "final" or record["result"] is None:
            continue
        pk = record["game_pk"]
        if pk in kept and kept[pk] != record:
            conflicting.add(pk)
        kept[pk] = deepcopy(dict(record))
    return [kept[pk] for pk in kept if pk not in conflicting]


# --- the five reports the daily job published ---------------------------------------------------------------------


def match_published_report(payload: Mapping[str, Any], day_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """
    The scheduled game a published daily file's report is about, or `ArchiveError(game_not_found)`.

    The file has one matchup whose id is `matchup_001` and no `gamePk`. The game is the one record of the day that has
    the matchup's date, both team ids and both probable starters; zero or more than one candidate is refused, never
    guessed (two games of one day, two teams swapped, a starter changed are all refusals).
    """

    try:
        matchups = payload["matchups"]
        if not isinstance(matchups, list) or len(matchups) != 1:
            raise ArchiveError(GAME_NOT_FOUND)
        matchup = matchups[0]
        wanted = {
            "date": matchup["date"],
            "away_team": str(matchup["teams"]["away"]["id"]),
            "home_team": str(matchup["teams"]["home"]["id"]),
            "away_pitcher": str(matchup["starters"]["away_starter"]["id"]),
            "home_pitcher": str(matchup["starters"]["home_starter"]["id"]),
        }
    except (KeyError, TypeError, AttributeError):
        raise ArchiveError(GAME_NOT_FOUND) from None
    found = []
    for record in day_records:
        probable = record["probable"]
        if (
            record["date"] == wanted["date"]
            and str(record["teams"]["away"]["id"]) == wanted["away_team"]
            and str(record["teams"]["home"]["id"]) == wanted["home_team"]
            and probable["away"] is not None and str(probable["away"]["id"]) == wanted["away_pitcher"]
            and probable["home"] is not None and str(probable["home"]["id"]) == wanted["home_pitcher"]
        ):
            found.append(record)
    if len(found) != 1:
        raise ArchiveError(GAME_NOT_FOUND)
    return dict(found[0])


SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)
COMMIT = re.compile(r"[0-9a-f]{40}", re.ASCII)


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def parse_published(raw: bytes) -> tuple[dict[str, Any], str]:
    """
    A daily file as the bot committed it: its payload and the SHA-256 of the exact bytes. Strict JSON (no NaN or
    Infinity); anything else raises `ValueError`.
    """

    if not isinstance(raw, bytes):
        raise ValueError("bytes expected")
    payload = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    if not isinstance(payload, dict):
        raise ValueError("a daily file is an object")
    return payload, hashlib.sha256(raw).hexdigest()


def published_lineage_problems(payload: Any) -> list[str]:
    """
    What a `published_live` payload must still be, without rejudging its text: a readable schema version, a live fetched
    snapshot, exactly one matchup that is a live matchup and carries no postgame (D41), and the run record that
    `published_origin` reads. Closed labels, never values.
    """

    problems: list[str] = []
    try:
        metadata = payload["metadata"]
        run = metadata["data_status"]["live_run"]
        if metadata.get("version") not in READABLE_VERSIONS:
            problems.append("version")
        if metadata.get("data_mode") != "fetched_snapshot" or metadata["data_status"].get("mode") != "fetched_snapshot":
            problems.append("data_mode")
        if not (isinstance(run, Mapping) and _aware(str(run.get("run_at"))) and isinstance(run.get("as_of"), str)):
            problems.append("live_run")
        matchups = payload["matchups"]
        if not (isinstance(matchups, list) and len(matchups) == 1 and isinstance(matchups[0], Mapping)):
            problems.append("matchups")
        else:
            if (matchups[0].get("data_confidence") or {}).get("level") != "fetched_snapshot":
                problems.append("matchup_mode")
            if matchups[0].get("postgame") is not None:
                problems.append("postgame")
    except (KeyError, TypeError, AttributeError):
        problems.append("shape")
    return problems


def published_origin(
    payload: Mapping[str, Any], record: Mapping[str, Any], source: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """
    The origin of a report the daily job published: `published_live` only when the run that wrote it (`run_at`) is
    before the game's first pitch (`start_time_utc`); otherwise `reconstructed` (contract rule 6). `as_of` is the run's
    cut-off. The instants are compared as instants, never as text.
    """

    run = payload["metadata"]["data_status"]["live_run"]
    run_at, start = run["run_at"], record["start_time_utc"]
    before = (
        isinstance(run_at, str) and _aware(run_at) and is_utc_instant(start)
        and datetime.fromisoformat(run_at.replace("Z", "+00:00")) < datetime.fromisoformat(start.replace("Z", "+00:00"))
    )
    return {
        "kind": "published_live" if before else "reconstructed",
        "as_of": run["as_of"],
        "built_at": payload["metadata"]["generated_at"],
        "published_at": run_at if before else None,
        # The lineage of the bytes: the bot's commit and the SHA-256 of the file it committed (None for a new build).
        "source": dict(source) if source is not None else None,
    }


# --- the envelope of a game file ----------------------------------------------------------------------------------


def unknown_starters_check() -> dict[str, Any]:
    """The starter check of a game whose boxscore was not read: unknown, never "started" (rule 2)."""

    return {"away": "unknown", "home": "unknown", "actual": {"away": None, "home": None}}


def build_game_file(
    record: Mapping[str, Any],
    payload: Mapping[str, Any],
    origin: Mapping[str, Any],
    starters_check: Mapping[str, Any] | None = None,
    final_line: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """The game file of a played game: the envelope around the payload, which is copied unchanged."""

    if record["status"] != "final" or record["result"] is None or not is_game_pk(str(record["game_pk"])):
        raise ArchiveError(GAME_NOT_FOUND)
    series = record["series"] or {}
    teams = {side: {"id": record["teams"][side]["id"], "name": record["teams"][side]["name"]} for side in SIDES}
    return {
        "archive_version": ARCHIVE_VERSION,
        "game_pk": record["game_pk"],
        "season": record["season"],
        "date": record["date"],
        "round": record["round"],
        "series": {
            "series_name": series.get("series_name"),
            "game_number": series.get("game_number"),
            "games_in_series": series.get("games_in_series"),
            "after": series.get("after"),
            "over": series.get("over"),
        },
        "teams": teams,
        "result": {"status": "final", **record["result"]},
        "origin": dict(origin),
        "starters_check": deepcopy(dict(starters_check)) if starters_check is not None else unknown_starters_check(),
        "final_line": deepcopy(dict(final_line)) if final_line is not None else {"away": None, "home": None},
        "payload": deepcopy(dict(payload)),
    }


def compact_json(document: Mapping[str, Any]) -> str:
    """The text a game file is written as: compact (25.7 KB, not 48.6 KB), sorted keys, finite numbers only."""

    return json.dumps(document, separators=(",", ":"), sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def _instant(value: Any) -> bool:
    return value is None or is_utc_instant(value) or (isinstance(value, str) and "T" in value and _aware(value))


def _aware(value: str) -> bool:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def _series_ok(series: Mapping[str, Any]) -> bool:
    """The series line of a file: a known name or None, a positive game number or None, a real length or None, a standing
    whose numbers can be true (with `over`) or None."""

    name, number, length, after, over = (series[key] for key in ("series_name", "game_number", "games_in_series", "after", "over"))
    if name is not None and series_module.series_name(name) is None:
        return False
    if number is not None and not (isinstance(number, int) and not isinstance(number, bool) and 1 <= number <= series_module.MAX_GAMES):
        return False
    if length is not None and not (isinstance(length, int) and not isinstance(length, bool) and length in series_module.SERIES_LENGTHS):
        return False
    if after is None:
        return over is None
    return isinstance(over, bool) and series_after(after, over) == after


def _source_ok(source: Any, kind: Any) -> bool:
    """A published report names the commit and the bytes it came from; a reconstructed one has none."""

    if kind == "reconstructed":
        return source is None
    return (
        isinstance(source, Mapping) and set(source) == {"commit", "sha256"}
        and isinstance(source["commit"], str) and COMMIT.fullmatch(source["commit"]) is not None
        and isinstance(source["sha256"], str) and SHA256.fullmatch(source["sha256"]) is not None
    )


def _final_line_problem(line: Any) -> str | None:
    if line is None:
        return None
    if not isinstance(line, Mapping) or set(line) != set(FINAL_LINE_FIELDS):
        return "keys"
    innings = line["innings_pitched"]
    if innings is not None and not (isinstance(innings, str) and _INNINGS.fullmatch(innings)):
        return "innings_pitched"
    for name in FINAL_LINE_FIELDS[1:]:
        value = line[name]
        if value is not None and not _count(value):
            return name
    return None


def validate_game_file(document: Any) -> list[str]:
    """
    Problems of the **envelope** of a game file (the payload is judged by `validate_payload` and `check_contract`).
    Empty list = valid. Each problem is a short closed label with a path, never the value (rule 8).
    """

    problems: list[str] = []

    def bad(label: str) -> None:
        problems.append(label)

    if not isinstance(document, Mapping):
        return ["document"]
    expected = {
        "archive_version", "game_pk", "season", "date", "round", "series", "teams", "result", "origin",
        "starters_check", "final_line", "payload",
    }
    if set(document) != expected:
        bad("keys")
    if document.get("archive_version") != ARCHIVE_VERSION:
        bad("archive_version")
    pk = document.get("game_pk")
    if not (isinstance(pk, int) and not isinstance(pk, bool) and is_game_pk(str(pk))):
        bad("game_pk")
    day = document.get("date")
    try:
        day_ok = isinstance(day, str) and date.fromisoformat(day).isoformat() == day
    except ValueError:
        day_ok = False
    if not day_ok:
        bad("date")
    season = document.get("season")
    if not (day_ok and season == int(day[:4])):
        bad("season")
    if document.get("round") not in ROUND_OF_TYPE.values():
        bad("round")
    series = document.get("series")
    if not (isinstance(series, Mapping) and set(series) == {"series_name", "game_number", "games_in_series", "after", "over"}
            and _series_ok(series)):
        bad("series")
    teams = document.get("teams")
    if not (
        isinstance(teams, Mapping) and set(teams) == set(SIDES)
        and all(isinstance(teams[s], Mapping) and set(teams[s]) == {"id", "name"} and isinstance(teams[s]["name"], str)
                and teams[s]["name"] and isinstance(teams[s]["id"], int) and not isinstance(teams[s]["id"], bool)
                and teams[s]["id"] > 0 for s in SIDES)
    ):
        bad("teams")
    result = document.get("result")
    if not (
        isinstance(result, Mapping) and set(result) == {"status", "away_runs", "home_runs", "winner"}
        and result["status"] == "final" and _count(result["away_runs"]) and _count(result["home_runs"])
        and result["away_runs"] != result["home_runs"]
        and result["winner"] == ("away" if result["away_runs"] > result["home_runs"] else "home")
    ):
        bad("result")
    origin = document.get("origin")
    if not (
        isinstance(origin, Mapping) and set(origin) == {"kind", "as_of", "built_at", "published_at", "source"}
        and _source_ok(origin.get("source"), origin.get("kind"))
        and origin["kind"] in ORIGIN_KINDS and _instant(origin["built_at"]) and origin["built_at"] is not None
        and (origin["published_at"] is None) == (origin["kind"] == "reconstructed")
        and _instant(origin["published_at"])
    ):
        bad("origin")
    else:
        try:
            as_of = date.fromisoformat(origin["as_of"])
            # both are exact YYYY-MM-DD texts here (day_ok, and as_of round-trips), so the comparison of texts is the dates'
            if not (day_ok and as_of.isoformat() == origin["as_of"] and origin["as_of"] < day):
                bad("origin.as_of")
        except (TypeError, ValueError):
            bad("origin.as_of")
    check = document.get("starters_check")
    if not (
        isinstance(check, Mapping) and set(check) == {"away", "home", "actual"}
        and all(check[s] in STARTER_STATES for s in SIDES)
        and isinstance(check["actual"], Mapping) and set(check["actual"]) == set(SIDES)
    ):
        bad("starters_check")
    else:
        for side in SIDES:
            actual = check["actual"][side]
            if actual is not None and not (
                isinstance(actual, Mapping) and set(actual) == {"id", "name"}
                and isinstance(actual["id"], int) and not isinstance(actual["id"], bool)
                and isinstance(actual["name"], str) and actual["name"]
            ):
                bad(f"starters_check.actual.{side}")
            if check[side] == "unknown" and actual is not None:
                bad(f"starters_check.actual.{side}")
    line = document.get("final_line")
    if not (isinstance(line, Mapping) and set(line) == set(SIDES)):
        bad("final_line")
    else:
        for side in SIDES:
            if _final_line_problem(line[side]) is not None:
                bad(f"final_line.{side}")
            elif line[side] is not None and isinstance(check, Mapping) and isinstance(check.get("actual"), Mapping) \
                    and check["actual"].get(side) is None:
                bad(f"final_line.{side}")  # a line belongs to a named pitcher who started
    if not isinstance(document.get("payload"), Mapping):
        bad("payload")
    return problems
