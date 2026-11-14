"""Finish and re-check an archive candidate folder: the index, the manifest, and every file again (R4-D6; D66).

    python -m data_pipeline.archive_finalize build --dir DIR --veteran-min V
    python -m data_pipeline.archive_finalize check --dir DIR [--veteran-min V]

`DIR` holds `games/<gamePk>.json` (written by `archive_build`). `build` validates every game file, writes
`index-<season>.json` and `manifest.json` next to them, and verifies what it wrote. `check` is the publish job's second
look at a folder it downloaded: **no network**, nothing written, every file read again as strict JSON and judged:

- the envelope of each game file (`validate_game_file`) and its name (`<game_pk>.json`);
- the payload of a **reconstructed** report by `validate_payload` (which runs the contract checks); a **published_live**
  payload by its lineage only (docs/DATA_CONTRACT.md section 7);
- the index against the game files (`index_matches_documents`), its shape, and the manifest against the files present;
- the files on disk against the manifest: any file the manifest does not list (hidden or not, in the root or in `games/`)
  is a problem.

`--veteran-min` is required by `build`: there is no default, the owner approves V after the dry run (docs/plans/R4.md 4.6).
Exit codes: 0 clean, 1 a problem (printed as closed labels), 2 usage. Nothing printed carries a value from a file.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

from data_pipeline import archive_games as ag
from data_pipeline import archive_index as ix
from data_pipeline.validators import ValidationError, validate_payload

MANIFEST_FILE = "manifest.json"


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def _read(path: Path) -> tuple[Any, str]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, parse_constant=_reject_constant), text


def load_games(directory: Path) -> tuple[dict[int, dict[str, Any]], dict[str, str], list[str]]:
    """
    (documents by game_pk, the file texts by relative name, problems). A file that cannot be read, or whose name is not its
    own `game_pk`, is a problem and is not among the documents.
    """

    documents: dict[int, dict[str, Any]] = {}
    texts: dict[str, str] = {}
    problems: list[str] = []
    folder = directory / "games"
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        name = f"games/{path.name}"
        try:
            document, text = _read(path)
        except (OSError, ValueError):
            problems.append("unreadable")
            continue
        texts[name] = text
        pk = document.get("game_pk") if isinstance(document, dict) else None
        if not (isinstance(pk, int) and not isinstance(pk, bool)) or path.name != f"{pk}.json":
            problems.append("name")
            continue
        documents[pk] = document
    return documents, texts, problems


def game_problems(document: dict[str, Any]) -> list[str]:
    """Problems of one game file: the envelope, then the payload by the rule of its origin."""

    found = [f"envelope:{p}" for p in ag.validate_game_file(document)]
    if found:
        return found
    payload = document["payload"]
    if document["origin"]["kind"] == "published_live":
        return [f"lineage:{p}" for p in ag.published_lineage_problems(payload)]
    try:
        validate_payload(payload)
    except ValidationError:
        return ["payload"]
    except Exception:  # a payload so malformed that a check raised is still a refusal, with a closed label
        return ["payload"]
    return []


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def build(directory: Path, veteran_min: Any, built_at: str | None = None) -> dict[str, Any]:
    """
    Validate every game file, write the index and the manifest, verify them. Returns `{"problems": [...], "games": n}`;
    a game with a problem is **left out of the index** (and reported), and a folder with any problem is not clean.
    """

    from data_pipeline.archive_build import out_dir_allowed

    if not out_dir_allowed(directory, Path(__file__).resolve().parents[1]):
        raise ix.ArchiveIndexError("out_under_published_paths")
    ix.check_veteran_min(veteran_min)
    documents, texts, problems = load_games(directory)
    good: dict[int, dict[str, Any]] = {}
    for pk, document in documents.items():
        found = game_problems(document)
        if found:
            problems.extend(f"game:{label}" for label in found)
            texts.pop(f"games/{pk}.json", None)
        else:
            good[pk] = document
    seasons = sorted({d["season"] for d in good.values()})
    if len(seasons) != 1:
        return {"problems": problems + ["season"], "games": len(good)}
    season = seasons[0]
    index = ix.build_index(list(good.values()), season, veteran_min)
    index_text = ag.compact_json(index)
    index_name = ix.INDEX_FILE.format(season=season)
    files = dict(texts, **{index_name: index_text})
    stamp = built_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = ix.build_manifest(files, index, stamp)
    if built_at is None:
        try:
            previous, _ = _read(directory / MANIFEST_FILE)
            if ix.verify_manifest(previous, files) == []:
                manifest = previous
        except (OSError, ValueError):
            pass
    _write(directory / index_name, index_text)
    _write(directory / MANIFEST_FILE, ag.compact_json(manifest))
    return {"problems": problems, "games": len(good)}


def check(directory: Path, veteran_min: int | None = None) -> list[str]:
    """Every problem of a folder, read again from disk with no network; `[]` when it is clean."""

    documents, texts, problems = load_games(directory)
    for pk, document in documents.items():
        problems.extend(f"game:{label}" for label in game_problems(document))
    try:
        manifest, _ = _read(directory / MANIFEST_FILE)
    except (OSError, ValueError):
        return problems + ["manifest"]
    index_files = sorted(p.name for p in directory.glob("index-*.json"))
    if len(index_files) != 1:
        return problems + ["index"]
    try:
        index, index_text = _read(directory / index_files[0])
    except (OSError, ValueError):
        return problems + ["index"]
    files = dict(texts, **{index_files[0]: index_text})
    # Every file on disk, hidden or not, must be one the manifest lists (plus the manifest itself): a stray file would be
    # copied and served without ever having been judged.
    on_disk = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if on_disk != set(files) | {MANIFEST_FILE}:
        problems.append("files:set")
    problems.extend(f"index:{p}" for p in ix.validate_index(index))
    if not ix.index_matches_documents(index, list(documents.values())):
        problems.append("index:rows")
    if veteran_min is not None and isinstance(index, dict) and index.get("veteran_min") != veteran_min:
        problems.append("index:veteran_min")
    if index_files[0] != ix.INDEX_FILE.format(season=index.get("season") if isinstance(index, dict) else 0):
        problems.append("index:name")
    problems.extend(f"manifest:{p}" for p in ix.verify_manifest(manifest, files))
    return sorted(set(problems))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m data_pipeline.archive_finalize", description=__doc__.split("\n\n")[0])
    parser.add_argument("action", choices=("build", "check"))
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--veteran-min", type=int, help="V, approved by the owner; required by `build`")
    parser.add_argument("--built-at", help="the instant to record in the manifest (default: now)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.dir.is_dir():
        print("finalize: failed usage", file=sys.stderr)
        return 2
    if args.action == "build":
        try:
            result = build(args.dir, args.veteran_min, args.built_at)
        except ix.ArchiveIndexError as exc:
            print(f"finalize: failed {exc.code}", file=sys.stderr)
            return 2
        for label in sorted(set(result["problems"])):
            print(f"finalize: problem {label}", file=sys.stderr)
        print(f"finalize: {result['games']} games indexed")
        return 1 if result["problems"] else 0
    problems = check(args.dir, args.veteran_min)
    for label in problems:
        print(f"finalize: problem {label}", file=sys.stderr)
    print("finalize: clean" if not problems else f"finalize: {len(problems)} problem label(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
