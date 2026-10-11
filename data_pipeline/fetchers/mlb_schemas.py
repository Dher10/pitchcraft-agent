"""
The shape of every MLB Stats API answer the pipeline consumes (QA3-02).

One explicit schema per endpoint, validated whole by the fetcher right after the answer is
parsed, including the inner objects of every element that is present. A failure raises
`SourceShapeError`, which the fetchers record as a source error; nothing is defaulted.

Rules the schemas encode:
- A required field that is missing (or null) is an error, wherever it sits.
- A valid empty list stays valid (a day without games, a pitcher without stats) unless the
  schema says the endpoint needs at least one element (`min_items`).
- An optional figure that is absent is simply absent: the fetcher reads it as `None`, never as
  zero. When it is present it must have its type.
- Fields the pipeline does not read are not listed and are not checked.

Checked against live answers on 2026-10-11 (schedule with probable pitchers and with
seriesStatus, season and byDateRange pitching stats, team statSplits, people, seasons).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
import re
from typing import Any, Iterator, Mapping


class SourceShapeError(ValueError):
    """An MLB answer does not have the shape the pipeline needs."""


_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class Scalar:
    kind: str  # "str", "int", "bool" or "date" (YYYY-MM-DD)
    required: bool = True


@dataclass(frozen=True)
class Obj:
    fields: Mapping[str, Any] = field(default_factory=dict)
    required: bool = True
    # An object whose fields are all optional figures still must carry at least one of
    # them: `{"message": "Internal error"}` is not a stat line with every figure missing.
    non_empty: bool = False


@dataclass(frozen=True)
class Arr:
    item: Any
    required: bool = True
    min_items: int = 0


def format_path(path: tuple[Any, ...]) -> str:
    """('stats', 0, 'splits') -> 'stats[0].splits'"""

    text = ""
    for step in path:
        text += f"[{step}]" if isinstance(step, int) else (f".{step}" if text else str(step))
    return text or "response"


def validate(schema: Any, data: Any, where: str = "response") -> None:
    """Raise SourceShapeError naming `where` and the path of the first problem."""

    problem = _problem(schema, data, ())
    if problem is not None:
        path, message = problem
        raise SourceShapeError(f"{where}: {format_path(path)} {message}")


def _is_scalar(kind: str, value: Any) -> bool:
    if kind == "bool":
        return isinstance(value, bool)
    if kind == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "str":
        return isinstance(value, str) and value != ""
    if kind == "date":
        if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True
    raise ValueError(f"unknown scalar kind {kind!r}")


def _problem(node: Any, value: Any, path: tuple[Any, ...]) -> tuple[tuple[Any, ...], str] | None:
    if value is None:
        return None if not node.required else (path, "is missing")
    if isinstance(node, Scalar):
        if _is_scalar(node.kind, value):
            return None
        return (path, f"is not a valid {node.kind}: {value!r}"[:120])
    if isinstance(node, Obj):
        if not isinstance(value, dict):
            return (path, f"is not an object: {type(value).__name__}")
        if node.non_empty and all(value.get(name) is None for name in node.fields):
            return (path, "has none of the expected figures")
        for name, child in node.fields.items():
            found = _problem(child, value.get(name), (*path, name))
            if found is not None:
                return found
        return None
    if isinstance(node, Arr):
        if not isinstance(value, list):
            return (path, f"is not a list: {type(value).__name__}")
        if len(value) < node.min_items:
            return (path, f"has {len(value)} element(s), at least {node.min_items} needed")
        for index, element in enumerate(value):
            if element is None:
                return ((*path, index), "is missing")
            found = _problem(node.item, element, (*path, index))
            if found is not None:
                return found
        return None
    raise TypeError(f"not a schema node: {node!r}")


# --- introspection, used by the generated tests -------------------------------------------


def _walk(node: Any, path: tuple[Any, ...] = ()) -> Iterator[tuple[tuple[Any, ...], Any]]:
    """Every (path, node) below the root, descending into the first element of each list."""

    if isinstance(node, Obj):
        for name, child in node.fields.items():
            yield (*path, name), child
            yield from _walk(child, (*path, name))
    elif isinstance(node, Arr):
        yield from _walk(node.item, (*path, 0))


def required_paths(root: Any) -> list[tuple[tuple[Any, ...], Any]]:
    """
    (path, node) of every required field. An optional object may be absent, but when it is
    there its required fields count, so they are listed too.
    """

    return [(path, node) for path, node in _walk(root) if node.required]


def optional_paths(root: Any) -> list[tuple[tuple[Any, ...], Any]]:
    return [(path, node) for path, node in _walk(root) if not node.required]


def list_paths(root: Any) -> list[tuple[tuple[Any, ...], Arr]]:
    """(path, node) of every list; the root itself may be a list, then its path is ()."""

    found = [((), root)] if isinstance(root, Arr) else []
    return found + [(path, node) for path, node in _walk(root) if isinstance(node, Arr)]


def non_empty_paths(root: Any) -> list[tuple[tuple[Any, ...], Obj]]:
    found = [((), root)] if isinstance(root, Obj) and root.non_empty else []
    return found + [(path, node) for path, node in _walk(root) if isinstance(node, Obj) and node.non_empty]


# --- the endpoints -------------------------------------------------------------------------

_TEAM_REF = Obj({"id": Scalar("int"), "name": Scalar("str")})
_PROBABLE_PITCHER = Obj({"id": Scalar("int"), "fullName": Scalar("str")}, required=False)

# schedule?date=...&hydrate=probablePitcher,venue   (fetch_todays_games)
SCHEDULE_DAY = Obj(
    {
        "dates": Arr(
            Obj(
                {
                    "games": Arr(
                        Obj(
                            {
                                # Copied into the snapshot but read by nothing yet: optional.
                                "gamePk": Scalar("int", required=False),
                                "officialDate": Scalar("date"),
                                "gameDate": Scalar("str"),
                                "status": Obj({"abstractGameState": Scalar("str", required=False)}, required=False),
                                "venue": Obj({"name": Scalar("str", required=False)}, required=False),
                                "teams": Obj(
                                    {
                                        side: Obj(
                                            {
                                                "team": _TEAM_REF,
                                                "probablePitcher": _PROBABLE_PITCHER,
                                            }
                                        )
                                        for side in ("away", "home")
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

# schedule?...&hydrate=seriesStatus   (fetch_series_status, both requests)
SERIES_SCHEDULE = Obj(
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
                                "seriesGameNumber": Scalar("int"),
                                "status": Obj({"abstractGameState": Scalar("str")}),
                                "teams": Obj(
                                    {side: Obj({"team": Obj({"id": Scalar("int")})}) for side in ("away", "home")}
                                ),
                                # Present on every game of a series; required only on the one
                                # the fetcher reads (SERIES_STATUS), so it is not listed here.
                            }
                        )
                    )
                }
            )
        )
    }
)

# The seriesStatus of the last earlier final game of the series.
SERIES_STATUS = Obj(
    {
        "wins": Scalar("int"),
        "losses": Scalar("int"),
        "isOver": Scalar("bool"),
        "result": Scalar("str"),
    }
)

# people/{id}/stats?group=pitching   (fetch_pitcher_season_stats). The figures are optional:
# a pitcher line without one of them has that figure unavailable (None), never zero.
PITCHER_STATS = Obj(
    {
        "stats": Arr(
            Obj(
                {
                    "splits": Arr(
                        Obj(
                            {
                                "stat": Obj(
                                    {
                                        "era": Scalar("str", required=False),
                                        "whip": Scalar("str", required=False),
                                        "inningsPitched": Scalar("str", required=False),
                                        "strikeOuts": Scalar("int", required=False),
                                        "baseOnBalls": Scalar("int", required=False),
                                        "homeRuns": Scalar("int", required=False),
                                        "battersFaced": Scalar("int", required=False),
                                    },
                                    non_empty=True,
                                )
                            }
                        )
                    )
                }
            )
        )
    }
)

# teams/{id}/stats?stats=statSplits&sitCodes=vl,vr   (fetch_team_splits, API path)
TEAM_SPLITS = Obj(
    {
        "stats": Arr(
            Obj(
                {
                    "splits": Arr(
                        Obj(
                            {
                                "split": Obj({"code": Scalar("str")}),
                                "stat": Obj(
                                    {
                                        "ops": Scalar("str", required=False),
                                        "avg": Scalar("str", required=False),
                                        "plateAppearances": Scalar("int", required=False),
                                        "strikeOuts": Scalar("int", required=False),
                                        "baseOnBalls": Scalar("int", required=False),
                                    },
                                    non_empty=True,
                                ),
                            }
                        )
                    )
                }
            )
        )
    }
)

# people/{id}   (fetch_pitcher_hand): no person, or a person without a hand, is no hand.
PERSON = Obj({"people": Arr(Obj({"pitchHand": Obj({"code": Scalar("str")})}), min_items=1)})

# seasons/{year}?sportId=1   (season_dates)
SEASONS = Obj(
    {
        "seasons": Arr(
            Obj(
                {
                    "regularSeasonStartDate": Scalar("date"),
                    "regularSeasonEndDate": Scalar("date"),
                }
            ),
            min_items=1,
        )
    }
)

# Every MLB Stats API endpoint the pipeline reads, by the path it is requested from.
# `tests/test_source_schemas.py` fails when live_pipeline.py asks for one that is not here.
ENDPOINTS: dict[str, Any] = {
    "schedule": SCHEDULE_DAY,
    "schedule+seriesStatus": SERIES_SCHEDULE,
    "people/stats": PITCHER_STATS,
    "teams/stats": TEAM_SPLITS,
    "people": PERSON,
    "seasons": SEASONS,
}
