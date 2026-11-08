"""The index, the notable-duel tags and the manifest of the archive (R4-D5; D66; docs/plans/R4.md 4.4 and 4.6).

Pure: no network and no file access; it reads game files already parsed and gives the index and the manifest as values.
Everything in the index is **recomputable from the game files alone**: `index_matches_documents` rebuilds it and compares.

The notable duels (owner's answer to OQ5): a game is notable when it has at least one of four reasons, each a fixed rule
on stored facts and never a score or a model:

- `series_clincher`: the game ended its series (`series.over` is true after it);
- `strikeout_duel`: **both** starters have the strikeout label "Above-average swing-and-miss ability" (D25) and a strikeout
  sample that is not limited (D24), as of the day before;
- `veteran_duel`: **both** starters have at least V earlier MLB seasons. V is **not fixed in code**: it is given by the caller
  and is approved by the owner after the R4-D7 distribution; without it the index is refused;
- `world_series`: the game is a World Series game that was played.

A missing or unknown input never makes a tag (rule 2). Order: more reasons first, then the later date, then the larger
`gamePk` (a deterministic tie-break).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
import hashlib
import re
from typing import Any

from data_pipeline import archive_games as ag
from data_pipeline import labels

REASONS = ("series_clincher", "strikeout_duel", "veteran_duel", "world_series")
INDEX_FILE = "index-{season}.json"
MANIFEST_VERSION = ag.ARCHIVE_VERSION
MAX_VETERAN_MIN = 30


class ArchiveIndexError(ValueError):
    """The index cannot be built or does not match; `code` is a short closed label, never a value."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _starter(document: Mapping[str, Any], side: str) -> Mapping[str, Any]:
    return document["payload"]["matchups"][0]["starters"][f"{side}_starter"]


def _strong_strikeout(starter: Mapping[str, Any]) -> bool:
    """True only for the above-average label with a strikeout sample that is known not to be limited."""

    try:
        label = starter["pitching_profile"]["swing_miss_label"]
        limited = starter["sample"]["limited"]["strikeout"]
    except (KeyError, TypeError):
        return False
    return label == labels.SWING_MISS_ABOVE and limited is False


def _veteran(fact: Any, veteran_min: int) -> bool:
    if not isinstance(fact, Mapping):
        return False
    seasons = fact.get("prior_mlb_seasons")
    return isinstance(seasons, int) and not isinstance(seasons, bool) and seasons >= veteran_min


def check_veteran_min(value: Any) -> int:
    """V: a positive integer the owner approved. Anything else (None included) refuses the index."""

    if not (isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_VETERAN_MIN):
        raise ArchiveIndexError("veteran_min_not_set")
    return value


def notable_reasons(document: Mapping[str, Any], veteran_min: int) -> list[str]:
    """The reasons a played game is notable, in the fixed order of `REASONS`; `[]` when none holds."""

    v = check_veteran_min(veteran_min)
    found: list[str] = []
    series = document["series"]
    if series.get("over") is True:
        found.append("series_clincher")
    try:
        if all(_strong_strikeout(_starter(document, side)) for side in ag.SIDES):
            found.append("strikeout_duel")
    except (KeyError, TypeError, IndexError):
        pass
    facts = document["starter_facts"]
    if all(_veteran(facts[side], v) for side in ag.SIDES):
        found.append("veteran_duel")
    if document["round"] == ag.ROUND_OF_TYPE["W"]:
        found.append("world_series")
    return found


def _abbreviation(document: Mapping[str, Any], side: str) -> str | None:
    try:
        value = document["payload"]["matchups"][0]["teams"][side]["abbreviation"]
    except (KeyError, TypeError, IndexError):
        return None
    return value if isinstance(value, str) and value else None


def _starter_name(document: Mapping[str, Any], side: str) -> str | None:
    try:
        value = _starter(document, side)["name"]
    except (KeyError, TypeError, IndexError):
        return None
    return value if isinstance(value, str) and value.strip() else None


def index_row(document: Mapping[str, Any], veteran_min: int) -> dict[str, Any]:
    """The index row of a valid game file (about 0.5 KB)."""

    if ag.validate_game_file(document):
        raise ArchiveIndexError("invalid_game_file")
    series = document["series"]
    check = document["starters_check"]
    return {
        "game_pk": document["game_pk"],
        "date": document["date"],
        "season": document["season"],
        "round": document["round"],
        "series": {key: series[key] for key in ("series_name", "game_number", "games_in_series")},
        "away": {"id": document["teams"]["away"]["id"], "name": document["teams"]["away"]["name"],
                 "abbreviation": _abbreviation(document, "away")},
        "home": {"id": document["teams"]["home"]["id"], "name": document["teams"]["home"]["name"],
                 "abbreviation": _abbreviation(document, "home")},
        "status": document["result"]["status"],
        "result": {key: document["result"][key] for key in ("away_runs", "home_runs", "winner")},
        "starters": {"away": _starter_name(document, "away"), "home": _starter_name(document, "home")},
        "report": {
            "origin": document["origin"]["kind"],
            "as_of": document["origin"]["as_of"],
            "starters_check": {side: check[side] for side in ag.SIDES},
        },
        "notable": notable_reasons(document, veteran_min),
    }


def _order(row: Mapping[str, Any]) -> tuple[str, int]:
    return (row["date"], row["game_pk"])


def build_index(documents: Sequence[Mapping[str, Any]], season: int, veteran_min: int) -> dict[str, Any]:
    """
    The index of one season: a row for every **valid** game file of that season, newest first. A file that is invalid, of
    another season or a duplicate of a game already listed is not listed (the caller records it).
    """

    v = check_veteran_min(veteran_min)
    rows: dict[int, dict[str, Any]] = {}
    for document in documents:
        if ag.validate_game_file(document) or document["season"] != season or document["game_pk"] in rows:
            continue
        rows[document["game_pk"]] = index_row(document, v)
    games = sorted(rows.values(), key=_order, reverse=True)
    return {
        "archive_version": ag.ARCHIVE_VERSION,
        "season": season,
        "veteran_min": v,
        "count": len(games),
        "notable_count": sum(1 for row in games if row["notable"]),
        "games": games,
    }


def notable_order(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """The notable list: games with at least one reason, more reasons first, then the later date, then the larger id."""

    chosen = [row for row in rows if row["notable"]]
    return sorted(chosen, key=lambda row: (len(row["notable"]), row["date"], row["game_pk"]), reverse=True)


def index_matches_documents(index: Any, documents: Sequence[Mapping[str, Any]]) -> bool:
    """The index is exactly what the game files give: the property that makes it recomputable."""

    try:
        return index == build_index(documents, index["season"], index["veteran_min"])
    except (KeyError, TypeError, ArchiveIndexError):
        return False


def validate_index(index: Any) -> list[str]:
    """
    Shape problems of an index (closed labels): the keys, the version, the counts, the order and the reasons of the rows. It
    is **not enough on its own**: the rows are judged against the game files by `index_matches_documents`.
    """

    if not isinstance(index, Mapping):
        return ["document"]
    problems: list[str] = []
    if set(index) != {"archive_version", "season", "veteran_min", "count", "notable_count", "games"}:
        problems.append("keys")
    if index.get("archive_version") != ag.ARCHIVE_VERSION:
        problems.append("archive_version")
    games = index.get("games")
    if not isinstance(games, list):
        return problems + ["games"]
    if index.get("count") != len(games):
        problems.append("count")
    if index.get("notable_count") != sum(1 for g in games if isinstance(g, Mapping) and g.get("notable")):
        problems.append("notable_count")
    seen: set[Any] = set()
    last: tuple[str, int] | None = None
    for position, row in enumerate(games):
        if not isinstance(row, Mapping) or not isinstance(row.get("game_pk"), int) or not isinstance(row.get("date"), str):
            problems.append(f"games[{position}]")
            continue
        if row["game_pk"] in seen:
            problems.append("duplicate")
        seen.add(row["game_pk"])
        if last is not None and _order(row) > last:
            problems.append("order")
        last = _order(row)
        notable = row.get("notable")
        if not (isinstance(notable, list) and all(r in REASONS for r in notable)
                and notable == [r for r in REASONS if r in notable]):
            problems.append(f"games[{position}].notable")
    return sorted(set(problems))


# --- the manifest ------------------------------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_manifest(files: Mapping[str, str], index: Mapping[str, Any], built_at: str) -> dict[str, Any]:
    """
    The manifest of the files present: `files` maps a path relative to the archive folder (`games/<pk>.json`, the index
    file) to its exact text. Lists every file with its SHA-256, so a later reader can tell a file was changed or is missing.
    """

    season = index["season"]
    index_name = INDEX_FILE.format(season=season)
    if index_name not in files:
        raise ArchiveIndexError("index_missing")
    return {
        "archive_version": MANIFEST_VERSION,
        "built_at": built_at,
        "seasons": [season],
        "counts": {"games": index["count"], "notable": index["notable_count"]},
        "files": {name: sha256_text(text) for name, text in sorted(files.items())},
    }


_GAME_FILE = re.compile(r"games/[1-9][0-9]{5,8}\.json", re.ASCII)
SHA256 = re.compile(r"[0-9a-f]{64}", re.ASCII)


def _is_year(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1900 <= value <= 2200


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_instant(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def verify_manifest(manifest: Any, files: Mapping[str, str]) -> list[str]:
    """
    Problems between a manifest and the files present, as closed labels: a malformed manifest (never an exception), a file
    missing, an extra one, a changed one, a bad name, a season whose index file is not listed and present.
    """

    if not isinstance(manifest, Mapping) or set(manifest) != {"archive_version", "built_at", "seasons", "counts", "files"}:
        return ["document"]
    if not (isinstance(files, Mapping) and all(isinstance(k, str) and isinstance(v, str) for k, v in files.items())):
        return ["files"]
    problems: list[str] = []
    if manifest["archive_version"] != MANIFEST_VERSION:
        problems.append("archive_version")
    if not _is_instant(manifest["built_at"]):
        problems.append("built_at")
    seasons = manifest["seasons"]
    if not (isinstance(seasons, list) and seasons and all(_is_year(s) for s in seasons)):
        problems.append("seasons")
        seasons = []
    counts = manifest["counts"]
    if not (isinstance(counts, Mapping) and set(counts) == {"games", "notable"} and all(_is_count(v) for v in counts.values())):
        problems.append("counts")
    listed = manifest["files"]
    if not isinstance(listed, Mapping):
        return sorted(set(problems + ["files"]))
    index_names = {INDEX_FILE.format(season=s) for s in seasons}
    for name in listed:
        if not (isinstance(name, str) and (name in index_names or _GAME_FILE.fullmatch(name))):
            problems.append("name")
    for name in index_names:
        if name not in listed or name not in files:
            problems.append("index_missing")
    if set(listed) != set(files):
        problems.append("file_set")
    for name, digest in listed.items():
        if not (isinstance(digest, str) and SHA256.fullmatch(digest)):
            problems.append("digest")
        elif name in files and sha256_text(files[name]) != digest:
            problems.append("digest")
    return sorted(set(problems))
