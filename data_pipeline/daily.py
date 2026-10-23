"""The daily job: build the day's file, and replace nothing unless it is valid and live (docs/plans/P1.md, 4.2).

    python -m data_pipeline.daily --out PATH [--date YYYY-MM-DD] [--dry-run]
    python -m data_pipeline.daily --check FILE

It runs the live fetch, the generator and `validate_payload`, and writes the candidate to `--out` only if every step
passed and the payload is a live one (`fetched_snapshot`). Any other outcome leaves `--out` as it was and exits 1 after
printing one line on stderr, `daily: failed {"source": ..., "code": ...}`. A demo or fallback payload is never a
candidate. A sound no-games run publishes an empty live day with the earlier live archive (P1.6).

The run record and snapshot are the hand-off between the fetch and the generator. They go to a private temporary
directory that is removed afterwards, so a record left by an earlier run, or by the developer's own run, can never be
taken for this one and the local cache is not touched.

`--check FILE` is the publish job's second look at the artifact it downloaded: no network, nothing written. It reads the
file as strict JSON, requires a live `fetched_snapshot` payload and runs `validate_payload`; exit 0 when all hold, 1 with
the same `daily: failed {source, code}` line otherwise (the text of the file is never printed).

Exit codes: 0 a valid live game day; 1 a failure; 2 a usage error; 3 a valid no-games live file.
`--dry-run` guarantees the repository's published files stay as they are: it refuses an `--out` under
`public/data/` or `evals/live/` (D15's paths) before asking any source for anything.

The `{source, code}` printed here is for the log and the workflow summary. It never reaches the public file, where
rule 8 applies; the sources and codes of a failed fetch are the closed sets of that rule, the two that belong to this
job (`critic_unsupported`, `validation_failed`) are its own.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Sequence

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline import config
from data_pipeline import archive
from data_pipeline import generate_demo_json as gdj
from data_pipeline.contract_checks import RUN_ERROR_CODES, RUN_SOURCES
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline
from data_pipeline.validators import ValidationError, validate_payload

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_PATHS = (REPO_ROOT / "public" / "data", REPO_ROOT / "evals" / "live")

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_NO_GAMES = 3

CRITIC_UNSUPPORTED = {"source": "pipeline", "code": "critic_unsupported"}
VALIDATION_FAILED = {"source": "pipeline", "code": "validation_failed"}
UNEXPECTED = {"source": "pipeline", "code": "unexpected_error"}


class DailyFailure(Exception):
    """The run produced no candidate; `reason` is the `{source, code}` it printed."""

    def __init__(self, reason: dict[str, str]) -> None:
        super().__init__(f"{reason['source']}/{reason['code']}")
        self.reason = reason


def _closed(reason: Any) -> dict[str, str]:
    """`reason` if it is exactly a source and a code of rule 8's closed sets, else an unexpected error."""

    if (
        isinstance(reason, dict)
        and set(reason) == {"source", "code"}
        and reason["source"] in RUN_SOURCES
        and reason["code"] in RUN_ERROR_CODES
    ):
        return {"source": reason["source"], "code": reason["code"]}
    return dict(UNEXPECTED)


def _require_live(status: Any) -> None:
    if not isinstance(status, dict) or status.get("mode") != config.DATA_MODE_SNAPSHOT:
        raise DailyFailure(_closed(status.get("reason") if isinstance(status, dict) else None))


def _build_candidate(target_date: str | None) -> dict[str, Any]:
    """The validated live payload for the day, or a `DailyFailure`. Touches nothing outside a temporary directory."""

    saved_dir = cache_manager.PROCESSED_DIR
    saved_input = (gdj._live, gdj._live_status)
    with tempfile.TemporaryDirectory(prefix="pitchcraft-daily-") as scratch:
        cache_manager.PROCESSED_DIR = Path(scratch)
        try:
            record, snapshot = live_pipeline.run_live_pipeline(target_date)
            print(f"daily: requests {json.dumps(record.get('requests', {}), sort_keys=True)}")
            cache_manager.save_processed("live_run", record)
            if snapshot is not None:
                cache_manager.save_processed("live_matchup", snapshot)
            gdj.refresh_live_input()
            _require_live(gdj._live_status)
            try:
                payload = gdj.build_payload(previous=archive.read_previous(gdj.OUTPUT_PATH))
            except gdj.CriticBlocked:
                raise DailyFailure(dict(CRITIC_UNSUPPORTED)) from None
            except archive.ArchiveError:
                raise DailyFailure({"source": "snapshot", "code": "malformed_response"}) from None
            _require_live(payload["metadata"]["data_status"])
            if payload["metadata"].get("data_mode") != config.DATA_MODE_SNAPSHOT:
                raise DailyFailure(dict(UNEXPECTED))
            try:
                validate_payload(payload)
            except ValidationError:
                raise DailyFailure(dict(VALIDATION_FAILED)) from None
            return payload
        finally:
            cache_manager.PROCESSED_DIR = saved_dir
            gdj._live, gdj._live_status = saved_input


def _write_atomically(path: Path, text: str) -> None:
    """Replace `path` with `text` in one step, so a failure half way never leaves a half-written file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _summary(payload: dict[str, Any], target_date: str | None) -> dict[str, Any]:
    run = payload["metadata"]["data_status"]["live_run"]
    return {
        "target_date": run["target_date"] if target_date is None else target_date,
        "games_scheduled": run["games_scheduled"],
        "games_live": run["games_live"],
        "matchups": len(payload["matchups"]),
        "errors": run["errors"],
        "warnings": run["warnings"],
    }


def run_daily(target_date: str | None, out: Path) -> dict[str, Any]:
    """Build the day's file and write it to `out`; return the summary. Raises `DailyFailure`, leaving `out` alone."""

    try:
        payload = _build_candidate(target_date)
        text = json.dumps(payload, indent=2, allow_nan=False) + "\n"
        summary = _summary(payload, target_date)
        _write_atomically(out, text)
    except DailyFailure:
        raise
    except Exception as exc:
        # The class only: the message of an unexpected error may carry paths or values, and this log is public.
        print(f"daily: unexpected {type(exc).__name__}", file=sys.stderr)
        raise DailyFailure(dict(UNEXPECTED)) from None
    return summary


def _reject_constant(name: str) -> None:
    raise ValueError(f"{name} is not a JSON value")


def check_file(path: Path) -> None:
    """Raise `DailyFailure` unless `path` holds a valid live payload. No network, nothing written."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, ValueError):
        raise DailyFailure(dict(VALIDATION_FAILED)) from None
    if not isinstance(payload, dict):
        raise DailyFailure(dict(VALIDATION_FAILED))
    metadata = payload.get("metadata")
    status = metadata.get("data_status") if isinstance(metadata, dict) else None
    if not (
        isinstance(status, dict)
        and status.get("mode") == config.DATA_MODE_SNAPSHOT
        and metadata.get("data_mode") == config.DATA_MODE_SNAPSHOT
    ):
        raise DailyFailure(dict(UNEXPECTED))
    try:
        validate_payload(payload)
    except ValidationError:
        raise DailyFailure(dict(VALIDATION_FAILED)) from None
    except Exception as exc:
        print(f"daily: unexpected {type(exc).__name__}", file=sys.stderr)
        raise DailyFailure(dict(UNEXPECTED)) from None


def _iso_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a date (YYYY-MM-DD)") from None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m data_pipeline.daily", description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, help="where the candidate file is written, only if valid and live")
    parser.add_argument("--check", type=Path, metavar="FILE", help="re-validate a candidate file; no network, nothing written")
    parser.add_argument("--date", type=_iso_date, default=None, help="game day (default: today in New York)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="refuse an --out under public/data or evals/live, so no published file can change",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.check is not None:
        if args.out is not None or args.date is not None or args.dry_run:
            parser.error("--check is used alone")
        try:
            check_file(args.check)
        except DailyFailure as failure:
            print(f"daily: failed {json.dumps(failure.reason)}", file=sys.stderr)
            return EXIT_FAILED
        print("daily: check ok")
        return EXIT_OK
    if args.out is None:
        parser.error("the following arguments are required: --out")
    if args.dry_run:
        target = args.out.resolve()
        if any(target == path or path in target.parents for path in PUBLISHED_PATHS):
            print("daily: --dry-run refuses an --out under public/data or evals/live", file=sys.stderr)
            return EXIT_USAGE
    try:
        summary = run_daily(args.date, args.out)
    except DailyFailure as failure:
        print(f"daily: failed {json.dumps(failure.reason)}", file=sys.stderr)
        return EXIT_FAILED
    print(f"daily: ok {json.dumps(summary)}")
    return EXIT_NO_GAMES if summary["games_scheduled"] == 0 else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
