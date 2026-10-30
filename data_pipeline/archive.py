"""D43: carry earlier published live reports, never demo rows or today's game.

Historical lineage is established at the previous-file boundary. The public
row has no origin field; its shape alone cannot prove that lineage. We check
all consumed fields without rejudging an older report with today's text catalog.
"""

from collections.abc import Mapping
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
from typing import Any

from data_pipeline.schema import READABLE_VERSIONS, STATE_OF_STATUS, is_no_games_run, new_york_day

LIMIT = 60
KEYS = {"id", "date", "title", "status", "featured", "starter_summary", "result_label", "grade_label"}


class ArchiveError(ValueError):
    """The previous published input cannot supply trusted live rows."""


def _day(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def row_valid(row: Any, target: str) -> bool:
    """A historical, ungraded live report row of v2.0-a (D41/D43)."""
    if not isinstance(row, Mapping) or set(row) != KEYS:
        return False
    return (
        _day(target) and _day(row["date"]) and row["date"] < target
        and isinstance(row["id"], str) and row["id"].startswith(row["date"] + ":")
        and bool(row["id"][11:])
        and all(isinstance(row[key], str) and bool(row[key].strip()) for key in ("title", "starter_summary"))
        and (row["status"] is None or (isinstance(row["status"], str) and row["status"] in STATE_OF_STATUS))
        and type(row["featured"]) is bool
        and row["result_label"] is None and row["grade_label"] is None
    )


def rows_valid(rows: Any, target: str) -> bool:
    return (
        isinstance(rows, list) and len(rows) <= LIMIT
        and all(row_valid(row, target) for row in rows)
        and len({row["id"] for row in rows}) == len(rows)
        and rows == sorted(rows, key=lambda row: (row["date"], row["id"]), reverse=True)
    )


def _reject_constant(value: str) -> None:
    raise ArchiveError("non-finite JSON constant")


def read_previous(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise ArchiveError("previous published file is unreadable") from exc


def carry_forward(previous: Any, target: str) -> list[dict[str, Any]]:
    if previous is None:
        return []
    try:
        metadata = previous["metadata"]
        mode = metadata["data_mode"]
        if mode in ("demo_cached", "demo_fallback"):
            return []
        status = metadata["data_status"]
        run = status["live_run"]
        prior_day = run["target_date"]
        matchups = previous["matchups"]
        rows = previous["archive"]
        if not (
            mode == status["mode"] == "fetched_snapshot"
            and metadata["version"] in READABLE_VERSIONS and status["reason"] is None
            and metadata["data_fetched_at"] == run["run_at"] and new_york_day(run["run_at"]) is not None
            and _day(prior_day) and _day(target) and isinstance(matchups, list)
            and rows_valid(rows, prior_day)
            and ((bool(matchups) and run["status"] == "ok"
                  and type(run["games_live"]) is int and run["games_live"] == len(matchups)
                  and _day(run["as_of"]) and run["as_of"] < prior_day)
                 or (not matchups and is_no_games_run(run)))
        ):
            raise ArchiveError("previous file is not a valid live archive source")
        rows = deepcopy(rows)
        ids = set()
        for matchup in matchups:
            if not (
                matchup["data_confidence"]["level"] == "fetched_snapshot"
                and matchup["date"] == prior_day and isinstance(matchup["id"], str) and matchup["id"]
                and matchup["id"] not in ids and matchup["postgame"] is None
            ):
                raise ArchiveError("previous matchup is not a live report")
            ids.add(matchup["id"])
            row = {
                "id": f"{prior_day}:{matchup['id']}", "date": prior_day,
                "title": matchup["game"]["title"], "status": matchup["status"],
                "featured": matchup["is_featured"],
                "starter_summary": " vs ".join(matchup["starters"][slot]["name"] for slot in ("away_starter", "home_starter")),
                "result_label": None, "grade_label": None,
            }
            # Check every consumed scalar before it can reach the next public file.
            if not row_valid(row, (date.fromisoformat(prior_day) + timedelta(days=1)).isoformat()):
                raise ArchiveError("previous matchup has malformed archive fields")
            if any(not isinstance(matchup["starters"][slot]["name"], str) or not matchup["starters"][slot]["name"].strip()
                   for slot in ("away_starter", "home_starter")):
                raise ArchiveError("previous starter has no name")
            rows.append(row)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ArchiveError("previous file has a malformed archive source") from exc
    unique = {row["id"]: row for row in rows if row["date"] < target}
    return sorted(unique.values(), key=lambda row: (row["date"], row["id"]), reverse=True)[:LIMIT]
