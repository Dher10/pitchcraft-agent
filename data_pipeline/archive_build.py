"""The backfill of the archive: one game at a time, within hard request ceilings (R4-D4; D66; docs/plans/R4.md 4.1-4.5).

    python -m data_pipeline.archive_build --out DIR [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--game-pk N]
        [--published-dir DIR] [--no-resume]

`DIR` must not be under `public/data/` or `evals/live/` (D15): the files are candidates; only the publish job of the
backfill workflow, on `main`, copies them to the published paths.

What it does for each game of the days asked: read the day's schedule, keep the games that were **played**, build the
report as of the day before (`as_of = game_date - 1`, D29) with the same pipeline as the daily job, read the boxscore
(who started, the final line), build the game file and write it, compact and atomically. Every step is one game:

- **Ceilings.** Each source (MLB Stats API, Baseball Savant) has its own counter at the HTTP layer (D66: 319 and 190). They
  are two totals; the sub-figures of the plan's table (106 frames, 84 team-batting chunks, 20 hand lookups) are estimates
  inside them, not separate limits.
  A request past a ceiling raises `CeilingReached`, which is a `BaseException` so no `except Exception` of the fetchers
  can swallow it and fill the game with a missing request. The game in progress is not written and the run stops; the
  games already built stay.
- **Resume.** A game whose file exists, is valid and is the same game is skipped and costs nothing.
- **Isolation (rule 5 per game file).** A game that fails validation or the critic is not written and is recorded with a
  closed code; the other games go on. Nothing that fails reaches a file.
- **No private data.** It reads no path under `evals/` and no sealed set (D64).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from datetime import date, timedelta
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any, Iterator

from data_pipeline import archive_boxscore, archive_games as ag

CEILINGS = {"mlb": 319, "savant": 190}
MLB_PAUSE_SECONDS = 0.5
OUT_FORBIDDEN = ("public/data", "evals/live")
FILE_NAME = "{game_pk}.json"


class CeilingReached(BaseException):
    """A request would pass its ceiling. A BaseException on purpose: the fetchers' `except Exception` must not catch it."""

    def __init__(self, source: str) -> None:
        super().__init__(source)
        self.source = source


class Ledger:
    """Requests made by this run, by source, against the ceilings of D66."""

    def __init__(self, ceilings: Mapping[str, int] | None = None) -> None:
        self.ceilings = dict(CEILINGS if ceilings is None else ceilings)
        self.used = {source: 0 for source in self.ceilings}

    def charge(self, source: str, count: int = 1) -> None:
        """Count `count` requests of `source` and raise `CeilingReached` if that passes the ceiling (nothing is added)."""

        if source not in self.ceilings or count < 0:
            raise ValueError("unknown source or negative count")
        if self.used[source] + count > self.ceilings[source]:
            raise CeilingReached(source)
        self.used[source] += count

    def summary(self) -> dict[str, dict[str, int]]:
        return {source: {"used": self.used[source], "ceiling": self.ceilings[source]} for source in self.ceilings}


@contextmanager
def enforced(ledger: Ledger, live_pipeline: Any, pause: Callable[[float], None] | None = None) -> Iterator[None]:
    """
    Charge every MLB request, every Savant team-batting request and every Statcast pitcher request of `live_pipeline`
    to `ledger` while the block runs. The pitcher fetch is charged by what the pipeline's own HTTP-layer counter says it
    sent (a call may send several requests), after it returns.
    """

    original_get = live_pipeline._get_json
    original_savant = live_pipeline._savant_get
    original_frame = live_pipeline._statcast_pitcher_frame

    def get_json(url: str, *args: Any, **kwargs: Any) -> Any:
        ledger.charge("mlb")
        if pause is not None:
            pause(MLB_PAUSE_SECONDS)
        return original_get(url, *args, **kwargs)

    def savant_get(url: str, *args: Any, **kwargs: Any) -> Any:
        ledger.charge("savant")
        return original_savant(url, *args, **kwargs)

    def frame(*args: Any, **kwargs: Any) -> Any:
        # A hard ceiling is checked BEFORE a request is sent: the pipeline's own per-run cap is lowered, for the length of
        # this call, so that the call cannot send more requests than the ledger has left. If that cap is what stops it, the
        # pipeline would record a missing frame and go on; here it is the end of the run instead.
        remaining = ledger.ceilings["savant"] - ledger.used["savant"]
        if remaining <= 0:
            raise CeilingReached("savant")
        before = live_pipeline._pitcher_statcast_run["requests"]
        original_cap = live_pipeline.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN
        live_pipeline.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN = min(original_cap, before + remaining)
        try:
            return original_frame(*args, **kwargs)
        except live_pipeline.PitcherStatcastBudgetExceeded:
            if live_pipeline._pitcher_statcast_run["requests"] - before >= remaining:
                raise CeilingReached("savant") from None
            raise
        finally:
            live_pipeline.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN = original_cap
            ledger.charge("savant", live_pipeline._pitcher_statcast_run["requests"] - before)

    live_pipeline._get_json, live_pipeline._savant_get, live_pipeline._statcast_pitcher_frame = get_json, savant_get, frame
    try:
        yield
    finally:
        live_pipeline._get_json, live_pipeline._savant_get, live_pipeline._statcast_pitcher_frame = (
            original_get, original_savant, original_frame,
        )


def out_dir_allowed(path: Path, repo_root: Path) -> bool:
    """D15: candidates are never written under the published paths of the repository."""

    resolved = path.resolve()
    for forbidden in OUT_FORBIDDEN:
        base = (repo_root / forbidden).resolve()
        if resolved == base or base in resolved.parents:
            return False
    return True


def write_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def existing_valid(path: Path, game_pk: int) -> bool:
    """True when `path` already holds a valid file of this game: it is skipped, at no cost."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return ag.validate_game_file(document) == [] and document.get("game_pk") == game_pk


def days_between(start: str, end: str) -> list[str]:
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first or (last - first).days > 120:
        raise ValueError("a backfill covers at most 121 days")
    return [(first + timedelta(days=n)).isoformat() for n in range((last - first).days + 1)]


class Dependencies:
    """What the run needs from outside; tests give fakes, `main` gives the real thing."""

    def __init__(
        self,
        fetch_day: Callable[[str], Sequence[Mapping[str, Any]]],
        build_report: Callable[[Mapping[str, Any]], tuple[dict[str, Any], Mapping[str, Any]]],
        fetch_boxscore: Callable[[int], Any],
        prior_seasons: Callable[[int], int | None],
        published: Sequence[tuple[dict[str, Any], str, str]] | None = None,
    ) -> None:
        self.fetch_day = fetch_day
        self.build_report = build_report
        self.fetch_boxscore = fetch_boxscore
        self.prior_seasons = prior_seasons
        # The reports the daily job published, as (payload, commit, sha256 of the committed bytes). Their `gamePk` is not
        # in the file; it is found by matching each to the schedule of its day (`ag.match_published_report`).
        self.published = list(published or [])


def report_starters(payload: Mapping[str, Any]) -> dict[str, int | None]:
    """The ids of the starters the report is about (the probable starters it was written for)."""

    out: dict[str, int | None] = {}
    starters = payload["matchups"][0]["starters"]
    for side, key in (("away", "away_starter"), ("home", "home_starter")):
        try:
            out[side] = int(starters[key]["id"])
        except (KeyError, TypeError, ValueError):
            out[side] = None
    return out


def _is_report(payload: Any) -> bool:
    """False for a daily file that holds no report (a day with no games) or is not live (a demo file); anything else is
    judged, and refused with a closed code if it is not a sound single live report."""

    try:
        return bool(payload["matchups"]) and payload["metadata"]["data_mode"] == "fetched_snapshot"
    except (KeyError, TypeError):
        return True  # malformed: let the lineage check refuse it, never skip it silently


def published_by_game(
    published: Sequence[tuple[dict[str, Any], str, str]], day: str, day_records: Sequence[Mapping[str, Any]]
) -> tuple[dict[int, tuple[dict[str, Any], str, str]], list[dict[str, Any]]]:
    """
    The published reports of `day` keyed by the `gamePk` they are matched to, and the failures (a report that matches no
    game or an ambiguous one, or whose lineage is not that of a live single report): `game_not_found`, never a guess.
    """

    found: dict[int, tuple[dict[str, Any], str, str]] = {}
    failed: list[dict[str, Any]] = []
    for item in published:
        payload = item[0]
        if not _is_report(payload):
            continue  # a no-games day or a demo file is not a report: nothing to match, nothing to refuse
        try:
            if ag.published_lineage_problems(payload):
                raise ag.ArchiveError(ag.GAME_NOT_FOUND)
            if payload["matchups"][0]["date"] != day:
                continue
            pk = ag.match_published_report(payload, day_records)["game_pk"]
            if pk in found:
                raise ag.ArchiveError(ag.GAME_NOT_FOUND)
            found[pk] = item
        except ag.ArchiveError as exc:
            failed.append({"game_pk": None, "code": exc.code})
    return found, failed


def build_one(
    record: Mapping[str, Any],
    deps: Dependencies,
    ledger: Ledger,
    published: tuple[dict[str, Any], str, str] | None = None,
) -> dict[str, Any]:
    """The game file of one played game, or an exception (`ArchiveError`, `CeilingReached`, a closed failure)."""

    if published is not None:
        payload, commit, digest = published
        origin = ag.published_origin(payload, record, {"commit": commit, "sha256": digest})
    else:
        payload, _run = deps.build_report(record)
        origin = ag.published_origin(payload, record, None)
        origin["kind"], origin["published_at"] = "reconstructed", None
    starters = report_starters(payload)
    try:
        box = deps.fetch_boxscore(record["game_pk"])
    except Exception:
        box = None  # an unreadable boxscore is `unknown`, never `started`
    check, line = archive_boxscore.starters_and_lines(box, starters)
    facts = {}
    for side in ag.SIDES:
        pid = starters[side]
        facts[side] = None if pid is None else {"id": pid, "prior_mlb_seasons": deps.prior_seasons(pid)}
    document = ag.build_game_file(record, payload, origin, check, line, facts)
    problems = ag.validate_game_file(document)
    if problems:
        raise ag.ArchiveError(ag.STARTER_UNCONFIRMED if any(p.startswith(("starters_check", "final_line")) for p in problems) else ag.GAME_NOT_FOUND)
    return document


def run(days: Sequence[str], out: Path, deps: Dependencies, ledger: Ledger, only: int | None = None, resume: bool = True) -> dict[str, Any]:
    """Build every played game of `days` into `out`. Returns the summary; a ceiling stops the run, a failed game does not."""

    built: list[int] = []
    skipped: list[int] = []
    failed: list[dict[str, Any]] = []
    stopped: str | None = None
    try:
        for day in days:
            try:
                records = list(deps.fetch_day(day))
            except Exception as exc:  # a day that cannot be read is recorded and the other days go on (rule 5, rule 8)
                failed.append({"game_pk": None, "day": day, "code": "malformed_response" if isinstance(exc, ValueError) else "request_failed"})
                continue
            matched, unmatched = published_by_game(deps.published, day, records)
            failed.extend(unmatched)
            for record in ag.played_games(records):
                pk = record["game_pk"]
                if only is not None and pk != only:
                    continue
                path = out / "games" / FILE_NAME.format(game_pk=pk)
                if resume and existing_valid(path, pk):
                    skipped.append(pk)
                    continue
                try:
                    document = build_one(record, deps, ledger, matched.get(pk))
                    write_atomically(path, ag.compact_json(document))
                    built.append(pk)
                except ag.ArchiveError as exc:
                    failed.append({"game_pk": pk, "code": exc.code})
                except Exception:
                    # The class is not published and not even logged with a message: rule 8.
                    failed.append({"game_pk": pk, "code": "unexpected_error"})
    except CeilingReached as exc:
        stopped = ag.CEILING_REACHED
        failed.append({"game_pk": None, "code": ag.CEILING_REACHED, "source": exc.source})
    return {
        "built": built, "skipped": skipped, "failed": failed, "stopped": stopped,
        "requests": ledger.summary(),
    }


# --- the real wiring ----------------------------------------------------------------------------------------------


def _read_published(directory: Path) -> list[tuple[dict[str, Any], str, str]]:
    """
    The daily files the bot committed, taken out of git history by the workflow into `directory` as `<commit>.json`
    (the exact committed bytes). Each is parsed strictly and hashed from its bytes.
    """

    items = []
    for path in sorted(directory.glob("*.json")):
        commit = path.stem
        if ag.COMMIT.fullmatch(commit) is None:
            raise ValueError("a published file is named by its 40-hex commit")
        payload, digest = ag.parse_published(path.read_bytes())
        items.append((payload, commit, digest))
    return items


def real_dependencies(ledger: Ledger, history_dir: Path, season: int, published: list[tuple[dict[str, Any], str, str]]):
    """The pipeline, the schedule, the boxscore and the history store, all through the charged HTTP layer."""

    from data_pipeline import daily
    from data_pipeline.archive_history import HistoryStore
    from data_pipeline.fetchers import live_pipeline, mlb_schemas

    pipeline_games: dict[str, list[dict[str, Any]]] = {}
    history = HistoryStore(history_dir, season, lambda url: live_pipeline._get_json(url))

    def fetch_day(day: str) -> list[dict[str, Any]]:
        data = live_pipeline._get_json(ag.day_url(day))
        # One answer, judged by both schemas: the archive's and the pipeline's own (it reads `venue.timeZone` and more).
        mlb_schemas.validate(mlb_schemas.SCHEDULE_DAY, data, "archive schedule response (pipeline)")
        records = ag.parse_day(data)
        pipeline_games[day] = [
            live_pipeline.game_record(game) for entry in data["dates"] for game in entry["games"]
        ]
        return records

    def build_report(record: Mapping[str, Any]) -> tuple[dict[str, Any], Mapping[str, Any]]:
        out: list[Mapping[str, Any]] = []
        payload = daily._build_candidate(
            record["date"], only_game_pk=record["game_pk"], games=pipeline_games[record["date"]],
            season_stats_provider=history.season_stats, record_out=out,
        )
        return payload, (out[0] if out else {})

    def fetch_boxscore(game_pk: int) -> Any:
        return live_pipeline._get_json(archive_boxscore.boxscore_url(game_pk))

    return Dependencies(fetch_day, build_report, fetch_boxscore, history.prior_seasons, published)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the game files of the archive backfill (R4-D4, D66).")
    parser.add_argument("--out", type=Path, required=True, help="directory for the candidate files (never under public/data or evals/live)")
    parser.add_argument("--start", help="first day, YYYY-MM-DD")
    parser.add_argument("--end", help="last day, YYYY-MM-DD")
    parser.add_argument("--game-pk", type=int, help="build only this game (its day must be inside --start/--end)")
    parser.add_argument("--published-dir", type=Path, help="the committed daily files, one `<40-hex commit>.json` each")
    parser.add_argument("--history-dir", type=Path, help="cache of the per-pitcher answers (default: OUT/history)")
    parser.add_argument("--no-resume", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    if not out_dir_allowed(args.out, repo_root):
        print("archive: failed out_under_published_paths", file=sys.stderr)
        return 2
    try:
        days = days_between(args.start, args.end) if args.start and args.end else None
        if days is None:
            raise ValueError("--start and --end are required")
        published = _read_published(args.published_dir) if args.published_dir else []
    except (ValueError, OSError) as exc:
        print(f"archive: failed usage {type(exc).__name__}", file=sys.stderr)
        return 2
    from data_pipeline.fetchers import live_pipeline

    ledger = Ledger()
    season = int(days[0][:4])
    with enforced(ledger, live_pipeline, pause=time.sleep):
        deps = real_dependencies(ledger, args.history_dir or args.out / "history", season, published)
        summary = run(days, args.out, deps, ledger, only=args.game_pk, resume=not args.no_resume)
    print("archive: " + json.dumps(summary, sort_keys=True))
    return 1 if summary["failed"] or summary["stopped"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
