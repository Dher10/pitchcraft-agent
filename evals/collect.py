"""P2.4 gate 4a: the dataset collector, selection and seal (docs/plans/P2.4.md sections 2 to 4).

`select` reads the schedule (8 requests), builds one candidate pool per stratum from the schedule ALONE with fixed rules
(the start-index rules written into `build_dataset.SEED_TEXT` before any pool is read), then walks each pool in seeded
rank order and looks up only the pitchers a candidate game needs, one request per pitcher for the whole season. A
pitcher fetched for one stratum costs nothing in the next. The ledger ceilings are the hard stop; a per-stratum
screening cap (`--screen-cap`) keeps one stratum from using the others' lookups.

`seal` writes `split.json` and `split.lock` from `selection.json` once, and refuses to rewrite them.
This module never touches `public/data/` or `evals/live/`.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

from data_pipeline import series as series_module
from data_pipeline.fetchers import live_pipeline
from data_pipeline.fetchers.mlb_schemas import SourceShapeError
from evals import build_dataset as bd
from evals import collect_sources as cs
from evals import request_ledger as rl

REPO_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (("public", "data"), ("evals", "live"))
SELECTION_VERSION = 1
OPENER_MIN_INDEX = 2  # an opener needs a previous start to have an average
LIMITED_INDEXES = range(2, 7)  # the 2nd to the 6th listed start of the season: the early starts, where samples are small
VETERAN_MIN_INDEX = 10
STRATUM_LABELS = {
    "postseason": "postseason games",
    "opener": "starters with short recent outings (opener-like)",
    "limited": "starters with limited samples",
    "veteran": "veteran starters",
}
DEFAULT_SCREEN_CAPS = {"postseason": 24, "opener": 40, "limited": 24, "veteran": 24}


class NotComplete(RuntimeError):
    """The selection has a short stratum and was not sealed with --allow-short."""


class SelectionChanged(RuntimeError):
    """A re-run does not contain a case of the earlier selection, or changed a field recorded for it."""


class ForbiddenPath(ValueError):
    """An output path inside the published data."""


@dataclass(frozen=True)
class Plan:
    season_start: date
    season_end: date
    collection_date: date
    postseason_end: date | None  # None: up to the day before the collection date, and the last final game found is reported
    screen_caps: dict
    schedule_dir: Path | None = None  # where the schedule answers are kept; None: no cache


@dataclass(frozen=True)
class Loaded:
    games: list
    postseason_end: date | None  # the date of the last final postseason game found


@dataclass
class Result:
    selection: bd.Selection
    facts: dict = field(default_factory=dict)  # case_id -> StarterFacts per starter
    series: dict = field(default_factory=dict)  # game_pk -> standing before first pitch
    lookups: dict = field(default_factory=dict)  # stratum -> pitcher lookups it spent
    skipped: dict = field(default_factory=dict)  # stratum -> {game_pk: reason}
    stopped: dict = field(default_factory=dict)  # stratum -> why it stopped early
    screened: dict = field(default_factory=dict)  # stratum -> pitchers it touched for the first time (what its cap limits)
    ended: set = field(default_factory=set)  # game_pk of the games that ended their series
    series_calls: int = 0  # series standings asked for (each is one or two ledger requests)
    halted: str | None = None


# --- paths ---------------------------------------------------------------------------------------------------


def check_output_path(path: Path) -> None:
    """Refuse a path inside the published data (D15): the collection writes under evals/data and the caches only."""

    candidate = Path(os.path.normpath(path))
    if candidate.is_absolute():
        try:
            candidate = candidate.relative_to(REPO_ROOT)
        except ValueError:
            return
    parts = candidate.parts
    for forbidden in FORBIDDEN:
        width = len(forbidden)
        if any(tuple(parts[i : i + width]) == forbidden for i in range(len(parts))):
            raise ForbiddenPath(f"{path} is inside {'/'.join(forbidden)}, which the collection never writes")


# --- the schedule ----------------------------------------------------------------------------------------------


def load_games(plan: Plan) -> Loaded:
    """Final games before the collection date: the regular season by calendar month, then the postseason in one request."""

    one_day = timedelta(days=1)
    games: list = []
    extra = {"cache_dir": plan.schedule_dir} if plan.schedule_dir else {}
    for start, end in live_pipeline._month_chunks(plan.season_start, plan.season_end):
        games += cs.fetch_schedule(start, end, "R", **extra)
    last = plan.collection_date - one_day
    post_end = min(plan.postseason_end, last) if plan.postseason_end else last
    post_start = plan.season_end + one_day
    if post_start <= post_end:
        games += cs.fetch_schedule(post_start, post_end, "F,D,L,W", **extra)
    kept: dict = {}
    for game in games:
        if not game.final or date.fromisoformat(game.official_date) >= plan.collection_date:
            continue
        kept[game.game_pk] = game  # a replayed game appears twice; only the final row is kept
    final = sorted(kept.values(), key=lambda g: (g.official_date, g.game_pk))
    post = [g.official_date for g in final if g.game_type in series_module.POSTSEASON_GAME_TYPES]
    return Loaded(final, date.fromisoformat(max(post)) if post else None)


# --- pools: objective filters from the schedule alone --------------------------------------------------------


def _regular(games):
    return [g for g in games if g.game_type == "R" and g.final]


def start_indexes(games) -> tuple:
    """(game_pk, pitcher_id) -> the 1-based number of that pitcher's listed start of the season; pitcher_id -> total."""

    per: dict = {}
    for game in sorted(_regular(games), key=lambda g: (g.official_date, g.game_pk)):
        for starter in game.starters:
            if starter is not None:
                per.setdefault(starter[0], []).append(game.game_pk)
    index = {(pk, pitcher): position + 1 for pitcher, pks in per.items() for position, pk in enumerate(pks)}
    return index, {pitcher: len(pks) for pitcher, pks in per.items()}


def _ids(game) -> tuple:
    return tuple(s[0] for s in game.starters)


def pools(games) -> dict:
    index, totals = start_indexes(games)
    listed = [g for g in games if g.final and all(g.starters)]
    by_rank = lambda g: bd.rank(g.game_pk)  # noqa: E731

    def start(game, pitcher):
        return index.get((game.game_pk, pitcher), 0)

    regular = [g for g in listed if g.game_type == "R"]
    opener = [g for g in regular if any(start(g, p) >= OPENER_MIN_INDEX for p in _ids(g))]
    return {
        "postseason": sorted((g for g in listed if g.game_type in series_module.POSTSEASON_GAME_TYPES), key=by_rank),
        "opener": sorted(
            opener,
            key=lambda g: (min(totals[p] for p in _ids(g) if start(g, p) >= OPENER_MIN_INDEX), bd.rank(g.game_pk)),
        ),
        "limited": sorted((g for g in regular if any(start(g, p) in LIMITED_INDEXES for p in _ids(g))), key=by_rank),
        "veteran": sorted((g for g in regular if all(start(g, p) >= VETERAN_MIN_INDEX for p in _ids(g))), key=by_rank),
    }


# --- lazy selection ------------------------------------------------------------------------------------------------


def series_ended(games) -> set:
    """game_pk of the last game of each matchup (same game type, same two clubs): the game that ended its series.

    Read from the schedule already fetched, so it costs no request. It is only as complete as the schedule: a series with
    games still to be played after the collection date would be marked early, so it is meaningful once the round is over.
    """

    last: dict = {}
    for game in sorted(games, key=lambda g: (g.official_date, g.game_pk)):
        if game.game_type in series_module.POSTSEASON_GAME_TYPES and game.teams:
            last[(game.game_type, frozenset(game.teams))] = game.game_pk
    return set(last.values())


def select_cases(
    games,
    store,
    plan: Plan,
    series_fn: Callable[[int, str], dict],
    refused: Callable[[], bool] = lambda: False,
    known_series: dict | None = None,
    keep: dict | None = None,
) -> Result:
    """`known_series`: game_pk -> standing recorded by an earlier run, reused so a re-run asks for no series again.

    The screening cap counts a pitcher the first time a stratum touches it (one touched by an earlier stratum is free),
    whatever the disk cache holds, so the same caps choose the same cases on a cold or a warm cache and a re-run with
    larger caps can only add cases.

    `keep`: stratum -> game_pks of the cases an earlier run found, in order. They are taken first and unchanged, then the
    seeded pool is walked for the rest, so a re-run with larger caps adds cases after them and never replaces one (a
    walk from the start would let a newly reachable earlier game push a later case out of a full stratum). A kept game
    that is no longer in its stratum stops the run (`SelectionChanged`).
    """

    pool = pools(games)
    known_series = known_series or {}
    keep = keep or {}
    by_pk = {g.game_pk: g for g in games}
    touched: set = set()
    cases: dict = {name: [] for name in bd.STRATA}
    result = Result(bd.Selection({}, {}))
    result.ended = series_ended(games)
    for name in bd.STRATA:
        result.lookups[name], result.screened[name], result.skipped[name] = 0, 0, {}
    used_games: set = set()
    used_pitchers: set = set()

    def consider(game, stratum: str, capped: bool) -> bool:
        """Evaluate one game for `stratum`; True when it became a case. Only the pool walk is limited by the cap."""

        ids = _ids(game)
        if game.game_pk in used_games or len(set(ids)) < 2 or used_pitchers.intersection(ids):
            return False
        new = len(set(ids) - touched)
        if capped and result.screened[stratum] + new > plan.screen_caps.get(stratum, 0):
            result.stopped[stratum] = "screen_cap"
            return False  # a later game whose pitchers are already touched costs nothing
        touched.update(ids)
        result.screened[stratum] += new
        facts = tuple(cs.facts_as_of(store.get(pitcher), game.official_date) for pitcher in ids)
        candidate = bd.Candidate(game.game_pk, game.official_date, game.game_type, True, facts)
        verdict = bd.classify(candidate, plan.collection_date)
        if verdict is None or verdict.primary != stratum:
            return False
        as_of = (date.fromisoformat(game.official_date) - timedelta(days=1)).isoformat()
        if stratum == "postseason":
            if game.game_pk in known_series:
                standing = known_series[game.game_pk]
            else:
                answer = series_fn(game.game_pk, as_of)
                result.series_calls += 1
                if refused():  # the fetcher swallows every error, so a refused reservation looks like "no standing"
                    raise rl.CeilingReached("the ledger refused a series request")
                try:
                    standing = bd.case_series({"seriesGameNumber": game.series_game_number}, answer)
                except bd.LeakageError:
                    result.skipped[stratum][game.game_pk] = "series_leak"
                    return False
            result.series[game.game_pk] = standing
        case = bd.Case(f"{stratum}-{game.game_pk}", game.game_pk, game.official_date, as_of, stratum, verdict.traits, ids)
        cases[stratum].append(case)
        result.facts[case.case_id] = facts
        used_games.add(game.game_pk)
        used_pitchers.update(ids)
        return True


    # Kept cases of every stratum are claimed before any pool is walked: a newly reachable game of an earlier stratum
    # must not take a game or pitcher that a kept case of a later stratum already uses.
    try:
        for stratum in bd.STRATA:
            spent = store.lookups
            try:
                for pk in keep.get(stratum, ()):
                    if pk not in by_pk or not consider(by_pk[pk], stratum, capped=False):
                        raise SelectionChanged(f"kept game {pk} is no longer a {stratum} case")
            finally:
                result.lookups[stratum] = store.lookups - spent
    except rl.CeilingReached:
        result.halted = "ceiling_reached"
    except SourceShapeError:
        result.halted = "source_shape"
    for stratum in bd.STRATA:
        spent_before = store.lookups
        try:
            for game in [] if result.halted else pool[stratum]:
                if len(cases[stratum]) == bd.PER_STRATUM:
                    break
                consider(game, stratum, capped=True)
        except rl.CeilingReached:
            result.halted = "ceiling_reached"
        except SourceShapeError:
            result.halted = "source_shape"  # a malformed answer stops the collection; what was found is kept
        finally:
            result.lookups[stratum] += store.lookups - spent_before
        if result.halted:
            break
    short = {name: bd.PER_STRATUM - len(found) for name, found in cases.items() if len(found) < bd.PER_STRATUM}
    result.selection = bd.Selection({name: tuple(found) for name, found in cases.items()}, short)
    return result


# --- the record, its hash, the seal ----------------------------------------------------------------------------------


def _facts(f: bd.StarterFacts) -> dict:
    return {
        "pitcher_id": f.pitcher_id,
        "samples": f.samples,
        "prior_seasons": f.prior_seasons,
        "previous_innings": list(f.previous_innings),
        "flagged_opener": f.flagged_opener,
    }


def case_record(case: bd.Case, result: Result) -> dict:
    return {
        "case_id": case.case_id,
        "game_pk": case.game_pk,
        "official_date": case.official_date,
        "as_of": case.as_of,
        "stratum": case.stratum,
        "traits": case.traits,
        "pitcher_ids": list(case.pitcher_ids),
        "facts": [_facts(f) for f in result.facts[case.case_id]],
        "series": result.series.get(case.game_pk),
        "prior_starts": [len(f.previous_innings) for f in result.facts[case.case_id]],
        "series_ended": (case.game_pk in result.ended) if case.stratum == "postseason" else None,
    }


def case_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def write_selection(directory, result: Result, plan: Plan, earlier: dict | None = None) -> None:
    directory = Path(directory)
    check_output_path(directory)
    records = []
    for stratum in bd.STRATA:
        for case in result.selection.cases.get(stratum, ()):
            record = case_record(case, result)
            records.append({**record, "sha256": case_hash(record)})
    document = {
        "version": SELECTION_VERSION,
        "seed": bd.SEED,
        "collection_date": plan.collection_date.isoformat(),
        "season": [plan.season_start.isoformat(), plan.season_end.isoformat()],
        "postseason_end_argument": plan.postseason_end.isoformat() if plan.postseason_end else "auto",
        "halted": result.halted,
        "short": result.selection.short,
        "stopped": result.stopped,
        "lookups": result.lookups,
        "screened": result.screened,
        "stratum_labels": STRATUM_LABELS,
        "opener_flag_read_from_schedule": False,  # the schedule answer is not read for an opener flag: unknown, not "none"
        "skipped": {k: {str(pk): why for pk, why in v.items()} for k, v in result.skipped.items()},
        "cases": records,
    }
    if earlier is not None:
        check_superset(earlier, document)  # before anything is written: a changed earlier case stops the run
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "selection.json").write_bytes((json.dumps(document, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def check_superset(old: dict, new: dict) -> None:
    """Every case of `old` is in `new` with every field it had unchanged (fields added since, and the hash, may differ)."""

    found = {r["case_id"]: r for r in new["cases"]}
    for record in old["cases"]:
        again = found.get(record["case_id"])
        if again is None:
            raise SelectionChanged(f"case {record['case_id']} of the earlier selection is missing")
        for key, value in record.items():
            if key != "sha256" and again.get(key) != value:
                raise SelectionChanged(f"case {record['case_id']}: field {key!r} changed")


def recorded_series(document: dict) -> dict:
    return {r["game_pk"]: r["series"] for r in document["cases"] if r["series"] is not None}


def kept_games(document: dict) -> dict:
    kept: dict = {name: [] for name in bd.STRATA}
    for record in document["cases"]:
        kept[record["stratum"]].append(record["game_pk"])
    return kept


def seal(directory, allow_short: bool = False) -> str:
    """Write split.json and split.lock from selection.json, once. A short selection needs allow_short."""

    directory = Path(directory)
    check_output_path(directory)
    document = json.loads((directory / "selection.json").read_text(encoding="utf-8"))
    if (document["short"] or document["halted"]) and not allow_short:
        raise NotComplete(f"strata short {document['short']}, halted {document['halted']}: sealing needs --allow-short")
    cases: dict = {name: [] for name in bd.STRATA}
    hashes = {}
    for record in document["cases"]:
        if case_hash(record) != record["sha256"]:
            raise bd.SplitChanged(f"case {record['case_id']} no longer matches its hash")
        cases[record["stratum"]].append(
            bd.Case(record["case_id"], record["game_pk"], record["official_date"], record["as_of"], record["stratum"], record["traits"], tuple(record["pitcher_ids"]))
        )
        hashes[record["case_id"]] = record["sha256"]
    return bd.write_split(directory, bd.Selection({k: tuple(v) for k, v in cases.items()}, document["short"]), hashes)


# --- the command line ---------------------------------------------------------------------------------------------------


def resolve_collection_date(value: str, today: date | None = None) -> date:
    if value == "today":
        return today or live_pipeline.today_eastern()
    return date.fromisoformat(value)


def parse_caps(text: str) -> dict:
    caps = dict(DEFAULT_SCREEN_CAPS)
    for part in filter(None, text.split(",")):
        name, _, number = part.partition("=")
        if name not in bd.STRATA or not number.isdigit():
            raise ValueError(f"bad --screen-cap entry {part!r}")
        caps[name] = int(number)
    return caps


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="python -m evals.collect")
    commands = parser.add_subparsers(dest="command", required=True)
    select = commands.add_parser("select")
    select.add_argument("--season-start", default="2026-03-25")
    select.add_argument("--season-end", default="2026-09-27")
    select.add_argument("--collection-date", default="today")
    select.add_argument("--postseason-end", default="auto")
    select.add_argument("--screen-cap", default="")
    select.add_argument("--ledger", default="evals/data/request_ledger.jsonl")
    select.add_argument("--history-dir", default="data_cache/raw/pitcher_history")
    select.add_argument("--schedule-dir", default="data_cache/raw/mlb_schedule")
    select.add_argument("--out", required=True)
    select.add_argument("--reuse", default="", help="selection.json of an earlier run: its series standings are reused and the new selection must contain all its cases")
    sealing = commands.add_parser("seal")
    sealing.add_argument("--out", required=True)
    sealing.add_argument("--allow-short", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover - the network entry point of gate 4
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.command == "seal":
        print(json.dumps({"lock": seal(args.out, args.allow_short)}))
        return 0
    check_output_path(Path(args.out))
    check_output_path(Path(args.history_dir))
    check_output_path(Path(args.schedule_dir))
    plan = Plan(
        date.fromisoformat(args.season_start),
        date.fromisoformat(args.season_end),
        resolve_collection_date(args.collection_date),
        None if args.postseason_end == "auto" else date.fromisoformat(args.postseason_end),
        parse_caps(args.screen_cap),
        Path(args.schedule_dir),
    )
    earlier = json.loads(Path(args.reuse).read_text(encoding="utf-8")) if args.reuse else None
    known_series = recorded_series(earlier) if earlier else None
    keep = kept_games(earlier) if earlier else None
    ledger = rl.RequestLedger(Path(args.ledger))
    store = cs.HistoryStore(args.history_dir, plan.season_end.year)
    with rl.counted_mlb(ledger):
        loaded = load_games(plan)
        result = select_cases(loaded.games, store, plan, live_pipeline.fetch_series_status, lambda: ledger.refused, known_series, keep)
    write_selection(args.out, result, plan, earlier)
    print(
        json.dumps(
            {
                "postseason_end_found": loaded.postseason_end.isoformat() if loaded.postseason_end else None,
                "short": result.selection.short,
                "lookups_by_stratum": result.lookups,
                "screened_by_stratum": result.screened,
                "stopped": result.stopped,
                "halted": result.halted,
                "series_calls": result.series_calls,
                "ledger_mlb_requests": ledger.count("mlb"),
            }
        )
    )
    return 0 if not result.halted else 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
