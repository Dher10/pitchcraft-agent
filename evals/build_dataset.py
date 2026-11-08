"""P2.4 dataset builder (docs/plans/P2.4.md sections 2 and 3): objective strata, seeded selection, the 20/20 split
and the leakage guards. Pure logic over recorded facts: this module makes no request.

The rules below are fixed before any pool is read. Changing SEED_TEXT changes the seed (a test pins it).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any

from data_pipeline import labels, series

PER_STRATUM = 10
STRATA = ("postseason", "opener", "limited", "veteran")  # the priority order for a case with overlapping traits
OPENER_MAX_AVERAGE_INNINGS = 2.0
VETERAN_MIN_SEASONS = 3
SPLIT_VERSION = 1

SEED_TEXT = (
    "pitchcraft-p2.4-strata-v1|"
    "veteran: every D24 dimension of both starters at or above its threshold and at least 3 prior MLB seasons|"
    "limited: a starter has a D24 dimension positive but below its threshold|"
    "opener: a starter averaged under 2.0 innings in his previous starts of the season, or the schedule flags him|"
    "postseason: game type F, D, L or W, final, dated before the collection date|"
    "priority: postseason, opener, limited, veteran|"
    "pools from the schedule alone, both starters listed, final games before the collection date: "
    "postseason = all postseason games; "
    "opener = regular games where a starter has a listed start number of 2 or more, tried in order of that starter's fewest listed starts of the season; "
    "limited = regular games where a starter has listed start number 2 to 6; "
    "veteran = regular games where both starters have listed start number 10 or more; "
    "within a pool, sha256 rank order; one request per pitcher for the whole season, a pitcher fetched once is reused|"
    "rank: sha256(seed + game_pk)|no shared starter or game|10 per stratum|split 5 dev, 5 test by sha256(seed + 'split' + game_pk)"
)
SEED = hashlib.sha256(SEED_TEXT.encode()).hexdigest()


class LeakageError(ValueError):
    """A source value from the game day or later reached a case."""


class SplitChanged(RuntimeError):
    """The sealed split is missing its lock, has no file, or differs from what the lock pins."""


@dataclass(frozen=True)
class StarterFacts:
    pitcher_id: int
    samples: dict  # D24 dimension -> raw count as of `as_of`, or None when unknown
    prior_seasons: int | None
    previous_innings: tuple  # innings of each start of the season before the game, oldest first
    flagged_opener: bool = False


@dataclass(frozen=True)
class Candidate:
    game_pk: int
    official_date: str
    game_type: str
    played: bool
    starters: tuple


@dataclass(frozen=True)
class Classification:
    primary: str
    traits: dict


@dataclass(frozen=True)
class Case:
    case_id: str
    game_pk: int
    official_date: str
    as_of: str
    stratum: str
    traits: dict
    pitcher_ids: tuple


@dataclass(frozen=True)
class Selection:
    cases: dict
    short: dict = field(default_factory=dict)


def innings_from_ip(text: Any) -> float | None:
    """True innings from MLB's inningsPitched text: "1.2" is one and two thirds (the digit after the point is outs)."""

    if not isinstance(text, str):
        return None
    whole, point, outs = text.partition(".")
    if not whole.isascii() or not whole.isdigit() or (point and (len(outs) != 1 or outs not in "012")):
        return None
    return int(whole) + (int(outs) / 3 if point else 0)


def check_as_of(official_date: str, as_of: Any) -> date:
    """D29: every case is built as of the day before its official date. A missing or any other cutoff is refused."""

    if as_of is None or as_of == "":
        raise ValueError("a historical case needs an explicit as_of, never None")
    game = date.fromisoformat(official_date)
    cutoff = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
    if cutoff != game - timedelta(days=1):
        raise ValueError(f"as_of {cutoff.isoformat()} must be the day before the game date {game.isoformat()}")
    return cutoff


def reject_rows_on_or_after(row_dates, official_date: str) -> None:
    game = date.fromisoformat(official_date)
    for value in row_dates:
        if date.fromisoformat(str(value)[:10]) >= game:
            raise LeakageError(f"a source row dated {value} is not before the game date {official_date}")


def case_series(game: dict, status: dict) -> dict:
    """The standing before first pitch for one postseason game, refused when anything could be from the game or later."""

    number = game["seriesGameNumber"]
    if not status or status.get("game_number") != number:
        raise LeakageError("no series standing for this game number")
    if status.get("games_played") != number - 1 or status.get("is_over"):
        raise LeakageError("the series standing is not the one before this game")
    result = status.get("result")
    if number > 1 and series.STANDING.fullmatch(result or "") is None:
        raise LeakageError("the series standing is not a recognized pre-game text")
    if number == 1 and result is not None:
        raise LeakageError("game 1 has no prior result")
    if result is not None and " wins " in result:
        raise LeakageError("a finished series is never the standing before a game")
    return {"game_number": number, "games_played": status["games_played"], "result": result, "is_over": False}


# --- strata -----------------------------------------------------------------------------------------------


def _veteran(s: StarterFacts) -> bool:
    return (
        s.prior_seasons is not None
        and s.prior_seasons >= VETERAN_MIN_SEASONS
        and all(s.samples.get(dim) is not None and s.samples[dim] >= minimum for dim, minimum in labels.THRESHOLDS.items())
    )


def _limited_dimensions(s: StarterFacts) -> list:
    return [
        dim
        for dim, minimum in labels.THRESHOLDS.items()
        if s.samples.get(dim) is not None and 0 < s.samples[dim] < minimum
    ]


def _opener(s: StarterFacts):
    if s.flagged_opener:
        return {"pitcher_id": s.pitcher_id, "evidence": "schedule_flag"}
    known = [n for n in s.previous_innings if n is not None]  # an unreadable start is skipped, never counted as 0
    if known:
        average = sum(known) / len(known)
        if average < OPENER_MAX_AVERAGE_INNINGS:
            return {"pitcher_id": s.pitcher_id, "evidence": {"average_innings": average, "starts": len(known)}}
    return None  # no previous start: the average is unknown, not zero


def classify(candidate: Candidate, collection_date: date) -> Classification | None:
    """None when the game cannot be a case (not final, not before the collection date, or in no stratum)."""

    day = date.fromisoformat(candidate.official_date)
    if not candidate.played or day >= collection_date:
        return None
    traits: dict = {}
    if candidate.game_type in series.POSTSEASON_GAME_TYPES:
        traits["postseason"] = {"game_type": candidate.game_type}
    elif candidate.game_type != "R":
        return None
    for s in candidate.starters:
        evidence = _opener(s)
        if evidence is not None:
            traits.setdefault("opener", evidence)
        limited = _limited_dimensions(s)
        if limited:
            traits.setdefault("limited", {"pitcher_id": s.pitcher_id, "dimensions": limited})
    if all(_veteran(s) for s in candidate.starters):
        traits["veteran"] = {"pitcher_ids": [s.pitcher_id for s in candidate.starters]}
    for name in STRATA:
        if name in traits:
            return Classification(name, traits)
    return None


# --- seeded selection -------------------------------------------------------------------------------------


def rank(game_pk: int) -> str:
    return hashlib.sha256((SEED + str(game_pk)).encode()).hexdigest()


def select(candidates, collection_date: date) -> Selection:
    ordered = sorted(candidates, key=lambda c: rank(c.game_pk))
    classified = [(c, classify(c, collection_date)) for c in ordered]
    cases = {name: [] for name in STRATA}
    used_games: set = set()
    used_pitchers: set = set()
    for name in STRATA:
        for candidate, result in classified:
            if len(cases[name]) == PER_STRATUM:
                break
            if result is None or result.primary != name or candidate.game_pk in used_games:
                continue
            pitchers = tuple(s.pitcher_id for s in candidate.starters)
            if used_pitchers.intersection(pitchers):
                continue
            used_games.add(candidate.game_pk)
            used_pitchers.update(pitchers)
            cases[name].append(
                Case(
                    case_id=f"{name}-{candidate.game_pk}",
                    game_pk=candidate.game_pk,
                    official_date=candidate.official_date,
                    as_of=(date.fromisoformat(candidate.official_date) - timedelta(days=1)).isoformat(),
                    stratum=name,
                    traits=result.traits,
                    pitcher_ids=pitchers,
                )
            )
    short = {name: PER_STRATUM - len(found) for name, found in cases.items() if len(found) < PER_STRATUM}
    return Selection({name: tuple(found) for name, found in cases.items()}, short)


def assign_split(selection: Selection) -> dict:
    """case_id -> "dev" or "test": within each stratum, the test half (rounded down) is the last by seeded rank."""

    split = {}
    for name in STRATA:
        found = sorted(selection.cases[name], key=lambda c: hashlib.sha256((SEED + "split" + str(c.game_pk)).encode()).hexdigest())
        test_count = len(found) // 2
        for position, case in enumerate(found):
            split[case.case_id] = "dev" if position < len(found) - test_count else "test"
    return split


# --- the sealed split file --------------------------------------------------------------------------------


def write_split(directory, selection: Selection, case_hashes: dict) -> str:
    """Write split.json (ids, strata, side and the SHA-256 of each case) and split.lock (the SHA-256 of that file)."""

    directory = Path(directory)
    if (directory / "split.json").exists() or (directory / "split.lock").exists():
        raise SplitChanged("a split already exists here; it is sealed and is never rewritten")
    sides = assign_split(selection)
    cases = [
        {"id": c.case_id, "stratum": c.stratum, "split": sides[c.case_id], "sha256": case_hashes[c.case_id]}
        for name in STRATA
        for c in selection.cases[name]
    ]
    text = json.dumps({"version": SPLIT_VERSION, "seed": SEED, "cases": cases}, indent=1, sort_keys=True) + "\n"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "split.json").write_bytes(text.encode("utf-8"))
    lock = hashlib.sha256(text.encode("utf-8")).hexdigest()
    (directory / "split.lock").write_bytes((lock + "\n").encode("ascii"))
    return lock


def verify_split_lock(directory) -> None:
    directory = Path(directory)
    split, lock = directory / "split.json", directory / "split.lock"
    if not split.exists() or not lock.exists():
        raise SplitChanged("the split and its lock must both exist")
    if hashlib.sha256(split.read_bytes()).hexdigest() != lock.read_text(encoding="ascii").strip():
        raise SplitChanged("split.json differs from the hash pinned in split.lock")
