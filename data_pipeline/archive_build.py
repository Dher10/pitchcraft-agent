"""The backfill of the archive: one game at a time, within hard request ceilings (R4-D4; D66; docs/plans/R4.md 4.1-4.5).

    python -m data_pipeline.archive_build --out DIR [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--game-pk N]
        [--published-dir DIR] [--no-resume] [--dry-run]

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
- **Resume.** A complete valid game is skipped at no boxscore cost. Every restored incomplete game is rechecked,
  including games outside the requested dates or filter; only its boxscore-derived check and line are refreshed.
- **Parser guard.** A missing boxscore, parser mismatch or rejected source line stops the strict run. An internal
  latch prevents finalization until a successful strict recovery checks every stopped game. `--dry-run` keeps the
  diagnostic evidence and incomplete files but still latches parser failures against publication.
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
import urllib.request
from typing import Any, Iterator

from data_pipeline import archive_boxscore, archive_games as ag

CEILINGS = {"mlb": 319, "savant": 190}
MLB_PAUSE_SECONDS = 0.5
OUT_FORBIDDEN = ("public/data", "evals/live")
FILE_NAME = "{game_pk}.json"
BACKFILL_START, BACKFILL_END = "2026-09-28", "2026-10-31"
STOP_FILE = ".starter-unconfirmed.json"  # internal candidate state; never part of the public archive family


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # a redirect is a failed request, never an uncharged second send


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
    original_urlopen = urllib.request.urlopen

    def urlopen(url, data=None, timeout=8, *, context=None):
        handlers = [_NoRedirect()]
        if context is not None:
            handlers.append(urllib.request.HTTPSHandler(context=context))
        return urllib.request.build_opener(*handlers).open(url, data, timeout)

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
    urllib.request.urlopen = urlopen
    try:
        yield
    finally:
        live_pipeline._get_json, live_pipeline._savant_get, live_pipeline._statcast_pitcher_frame = (
            original_get, original_savant, original_frame,
        )
        urllib.request.urlopen = original_urlopen


def out_dir_allowed(path: Path, repo_root: Path) -> bool:
    """D15: candidates are never written under the published paths of the repository."""

    resolved = path.resolve()
    for forbidden in OUT_FORBIDDEN:
        base = (repo_root / forbidden).resolve()
        if resolved == base or base in resolved.parents:
            return False
    return True


def _candidate_games_allowed(directory: Path) -> bool:
    """A restored games directory must be a real child, never a link to another output tree."""

    games = directory / "games"
    try:
        return (not directory.is_symlink() and not directory.is_junction()
                and not games.is_symlink() and not games.is_junction()
                and games.resolve().parent == directory.resolve())
    except OSError:
        return False


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


def write_raw_boxscore(directory: Path, game_pk: int, data: Any) -> None:
    """Keep one boxscore answer exactly as received (compact JSON), for the dry run's report."""

    write_atomically(directory / FILE_NAME.format(game_pk=game_pk), json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n")


def existing_valid(path: Path, game_pk: int, record: Mapping[str, Any] | None = None,
                   published: tuple[dict[str, Any], str, str] | None = None) -> bool:
    """True when `path` already holds a valid file of this game: it is skipped, at no cost."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    from data_pipeline.archive_finalize import game_problems

    if game_problems(document) or document.get("game_pk") != game_pk:
        return False
    if record is not None:
        expected = ag.build_game_file(record, document["payload"], document["origin"],
                                      document["starters_check"], document["final_line"], document["starter_facts"])
        if not ag.same_json_values(expected, document):
            return False
        if published is not None:
            payload, commit, digest = published
            if not ag.same_json_values(document["payload"], payload) or not ag.same_json_values(
                document["origin"], ag.published_origin(payload, record, {"commit": commit, "sha256": digest})
            ):
                return False
        elif document["origin"]["kind"] == "published_live":
            return False  # no recovered committed source proves this cached report
    return True


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
        save_boxscore: Callable[[int, Any], None] | None = None,
    ) -> None:
        self.fetch_day = fetch_day
        self.build_report = build_report
        self.fetch_boxscore = fetch_boxscore
        self.prior_seasons = prior_seasons
        # Optional (the dry run of R4-D7): keeps each boxscore answer as received, so a parser mismatch can be told from
        # data MLB did not give. Recording raw data does not select diagnostic behavior.
        self.save_boxscore = save_boxscore
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


class StarterUnconfirmed(ag.ArchiveError):
    """A source parser stop, distinct from an isolated game validation failure."""

    def __init__(self, game_pk: int) -> None:
        super().__init__(ag.STARTER_UNCONFIRMED)
        self.game_pk = game_pk


class _Boxscores:
    """One fetch/save per game per run, with the same source judgment in both modes."""

    def __init__(self, deps: Dependencies, diagnostic: bool, on_problem: Callable[[int], None] | None = None) -> None:
        self.deps, self.diagnostic, self.on_problem = deps, diagnostic, on_problem
        self.raws: dict[int, Any] = {}

    def parts(self, game_pk: int, payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        starters = report_starters(payload)
        first = game_pk not in self.raws
        if first:
            try:
                raw = self.deps.fetch_boxscore(game_pk)
            except CeilingReached:
                if self.on_problem is not None:
                    try:
                        self.on_problem(game_pk)
                    except StarterUnconfirmed:
                        pass  # the ceiling remains the reason; the failed latch still blocks publication when possible
                raise
            except Exception:
                raw = None
            self.raws[game_pk] = raw
        raw = self.raws[game_pk]
        unconfirmed = archive_boxscore.source_unconfirmed(raw, starters)
        if unconfirmed:
            if self.on_problem is not None:
                self.on_problem(game_pk)
        # Persist the stop before optional diagnostics: an evidence-write failure
        # must not turn a parser stop into an isolated ordinary game failure.
        if first and raw is not None and self.deps.save_boxscore is not None:
            try:
                self.deps.save_boxscore(game_pk, raw)
            except Exception:
                if unconfirmed and not self.diagnostic:
                    raise StarterUnconfirmed(game_pk) from None
                raise
        if unconfirmed and not self.diagnostic:
            raise StarterUnconfirmed(game_pk)
        return archive_boxscore.starters_and_lines(raw, starters)


def _incomplete_boxscore(document: Mapping[str, Any]) -> bool:
    return any(document["starters_check"][side] == "unknown"
               or document["starters_check"]["actual"][side] is None
               or document["final_line"][side] is None
               or any(value is None for value in document["final_line"][side].values()) for side in ag.SIDES)


def _recovered_cache_matches(document: Mapping[str, Any], published: Sequence[tuple[dict[str, Any], str, str]]) -> bool:
    """Bind restored historical values to recovered bytes even outside the requested schedule dates."""

    return document["origin"]["kind"] != "published_live" or any(
        ag.same_json_values(document["payload"], payload)
        and ag.same_json_values(document["origin"]["source"], {"commit": commit, "sha256": digest})
        for payload, commit, digest in published
    )


def _stopped_ids(path: Path) -> set[int]:
    if path.is_symlink() or path.is_junction():
        raise ValueError("unreadable internal stop")
    if not path.exists():
        return set()
    value = json.loads(path.read_text(encoding="utf-8"))
    if not (isinstance(value, dict) and set(value) == {"game_pks"} and isinstance(value["game_pks"], list)
            and value["game_pks"] and all(type(pk) is int and ag.is_game_pk(str(pk)) for pk in value["game_pks"])):
        raise ValueError("invalid internal stop")
    return set(value["game_pks"])


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
    diagnostic: bool = False,
    boxscores: _Boxscores | None = None,
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
    check, line = (boxscores or _Boxscores(deps, diagnostic)).parts(record["game_pk"], payload)
    facts = {}
    for side in ag.SIDES:
        pid = starters[side]
        facts[side] = None if pid is None else {"id": pid, "prior_mlb_seasons": deps.prior_seasons(pid)}
    document = ag.build_game_file(record, payload, origin, check, line, facts)
    problems = ag.validate_game_file(document)
    if problems:
        raise ag.ArchiveError(ag.STARTER_UNCONFIRMED if any(p.startswith(("starters_check", "final_line")) for p in problems) else ag.GAME_NOT_FOUND)
    return document


def run(days: Sequence[str], out: Path, deps: Dependencies, ledger: Ledger, only: int | None = None,
        resume: bool = True, diagnostic: bool = False) -> dict[str, Any]:
    """Build selected games; source parser failures and ceilings stop the run, other game failures stay isolated."""

    built: list[int] = []
    skipped: list[int] = []
    failed: list[dict[str, Any]] = []
    stopped: str | None = None
    if not _candidate_games_allowed(out) or not out_dir_allowed(out, Path(__file__).resolve().parents[1]):
        return {"built": [], "skipped": [], "failed": [{"game_pk": None, "code": ag.GAME_NOT_FOUND}],
                "stopped": ag.GAME_NOT_FOUND, "requests": ledger.summary()}
    stop_path = out / STOP_FILE
    try:
        pending = _stopped_ids(stop_path)
    except (OSError, ValueError):
        return {"built": [], "skipped": [], "failed": [{"game_pk": None, "code": ag.STARTER_UNCONFIRMED}],
                "stopped": ag.STARTER_UNCONFIRMED, "requests": ledger.summary()}
    confirmed: set[int] = set()

    def latch(pk: int) -> None:
        pending.add(pk)
        try:
            write_atomically(stop_path, json.dumps({"game_pks": sorted(pending)}, separators=(",", ":")) + "\n")
        except OSError:
            # A torn/failed internal state must never look like a clean old
            # manifest. A malformed sentinel fails closed on subsequent runs.
            try:
                stop_path.write_text("!", encoding="utf-8")
            except OSError:
                pass  # even when storage cannot retain state, this run must stop immediately with a closed reason
            raise StarterUnconfirmed(pk) from None

    boxscores = _Boxscores(deps, diagnostic, latch)
    try:
        from data_pipeline.archive_finalize import game_problems, load_games

        # Restored artifacts may contain games beyond today's dates/filter. Judge every existing report before a
        # complete cache is trusted, then refresh only the boxscore-derived parts of valid incomplete reports.
        documents, _texts, _problems = load_games(out)
        for pk, document in documents.items():
            selected = document.get("date") in days and (only is None or pk == only)
            if game_problems(document) or not _recovered_cache_matches(document, deps.published):
                if selected:
                    continue  # the ordinary full resume check removes it and attempts a rebuild from its source
                latch(pk)
                raise StarterUnconfirmed(pk)
            if not _incomplete_boxscore(document) and pk not in pending:
                continue
            # Latch before reading: an exhausted ceiling must not leave an old valid manifest publishable.
            latch(pk)
            check, line = boxscores.parts(pk, document["payload"])
            refreshed = dict(document, starters_check=check, final_line=line)
            if game_problems(refreshed):
                raise StarterUnconfirmed(pk)
            write_atomically(out / "games" / FILE_NAME.format(game_pk=pk), ag.compact_json(refreshed))
            confirmed.add(pk)
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
                if resume and existing_valid(path, pk, record, matched.get(pk)):
                    skipped.append(pk)
                    continue
                try:
                    path.unlink(missing_ok=True)  # a rejected cache must not survive a failed rebuild
                    document = build_one(record, deps, ledger, matched.get(pk), diagnostic, boxscores)
                    write_atomically(path, ag.compact_json(document))
                    built.append(pk)
                    confirmed.add(pk)
                except StarterUnconfirmed:
                    raise  # source shape failures stop the entire candidate, never just this game
                except ag.ArchiveError as exc:
                    failed.append({"game_pk": pk, "code": exc.code})
                except Exception:
                    # The class is not published and not even logged with a message: rule 8.
                    failed.append({"game_pk": pk, "code": "unexpected_error"})
    except StarterUnconfirmed as exc:
        stopped = ag.STARTER_UNCONFIRMED
        failed.append({"game_pk": exc.game_pk, "code": ag.STARTER_UNCONFIRMED})
    except CeilingReached as exc:
        stopped = ag.CEILING_REACHED
        failed.append({"game_pk": None, "code": ag.CEILING_REACHED, "source": exc.source})
    except OSError:
        stopped = ag.STARTER_UNCONFIRMED
        failed.append({"game_pk": None, "code": ag.STARTER_UNCONFIRMED})
    # Only a successful strict run can discharge an earlier stop. A narrow run cannot forget an ID whose failed build
    # wrote no game file, and diagnostic evidence never authorizes publication.
    if not diagnostic and stopped is None:
        pending.difference_update(confirmed)
        try:
            if pending:
                write_atomically(stop_path, json.dumps({"game_pks": sorted(pending)}, separators=(",", ":")) + "\n")
            else:
                stop_path.unlink(missing_ok=True)
        except OSError:
            stopped = ag.STARTER_UNCONFIRMED
            failed.append({"game_pk": None, "code": ag.STARTER_UNCONFIRMED})
    if pending and not diagnostic and stopped is None:
        stopped = ag.STARTER_UNCONFIRMED
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


def real_dependencies(
    ledger: Ledger, history_dir: Path, season: int, published: list[tuple[dict[str, Any], str, str]], raw_dir: Path | None = None
):
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

    saver = None if raw_dir is None else (lambda pk, data: write_raw_boxscore(raw_dir, pk, data))
    return Dependencies(fetch_day, build_report, fetch_boxscore, history.prior_seasons, published, saver)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the game files of the archive backfill (R4-D4, D66).")
    parser.add_argument("--out", type=Path, required=True, help="directory for the candidate files (never under public/data or evals/live)")
    parser.add_argument("--start", help="first day, YYYY-MM-DD")
    parser.add_argument("--end", help="last day, YYYY-MM-DD")
    parser.add_argument("--game-pk", type=int, help="build only this game (its day must be inside --start/--end)")
    parser.add_argument("--published-dir", type=Path, help="the committed daily files, one `<40-hex commit>.json` each")
    parser.add_argument("--history-dir", type=Path, help="cache of the per-pitcher answers (default: OUT/history)")
    parser.add_argument("--raw-dir", type=Path, help="keep every boxscore answer here as received; does not select --dry-run (never under public/data)")
    parser.add_argument("--dry-run", action="store_true", help="keep diagnostic incomplete games and evidence; source failures still block finalization")
    parser.add_argument("--no-resume", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    writable = (args.out, args.raw_dir, args.history_dir or args.out / "history")
    if any(p is not None and not out_dir_allowed(p, repo_root) for p in writable):
        print("archive: failed out_under_published_paths", file=sys.stderr)
        return 2
    try:
        days = days_between(args.start, args.end) if args.start and args.end else None
        if days is None:
            raise ValueError("--start and --end are required")
        if days[0] < BACKFILL_START or days[-1] > BACKFILL_END:
            raise ValueError("outside the approved postseason window")
        published = _read_published(args.published_dir) if args.published_dir else []
    except (ValueError, OSError) as exc:
        print(f"archive: failed usage {type(exc).__name__}", file=sys.stderr)
        return 2
    from data_pipeline.fetchers import live_pipeline

    ledger = Ledger()
    season = int(days[0][:4])
    with enforced(ledger, live_pipeline, pause=time.sleep):
        deps = real_dependencies(ledger, args.history_dir or args.out / "history", season, published, args.raw_dir)
        summary = run(days, args.out, deps, ledger, only=args.game_pk, resume=not args.no_resume, diagnostic=args.dry_run)
    print("archive: " + json.dumps(summary, sort_keys=True))
    fatal = summary["stopped"] or any(item.get("game_pk") is None for item in summary["failed"])
    return 1 if fatal or (summary["failed"] and not (summary["built"] or summary["skipped"])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
