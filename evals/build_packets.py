"""P2.4 packets: the matchup packet and the analyst's findings of each sealed case (docs/plans/P2.4-packets.md).

A case is built by the live pipeline's own code, as of the day before the game (D29): `fetch_pitcher_statcast` for both
starters, `fetch_team_splits` for both lineups, `live_matchup.build_matchup`, `data_scout.run` (the packet) and
`matchup_analyst.run` (the findings). What differs from the daily job:

- the game record is read from the cached schedule through `live_pipeline.game_record`; its state is what the schedule said
  the day before (Preview / Scheduled), because a final state is not known as of that day;
- the season line comes from the starter's cached game log, rows dated strictly before the game date, never from a request;
- the series standing is the one recorded in `selection.json`, checked again by `build_dataset.case_series`;
- the season dates come from the selection record, never from a request.

Nothing here prints packet content. The sealed test split is read by hash only: `load_dev_packet` refuses a test case.
This module never touches `public/data/` or `evals/live/`.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable

from data_pipeline import season_calendar, series as series_module
from data_pipeline.fetchers import live_pipeline as lp
from evals import build_dataset as bd
from evals import collect as co
from evals import collect_sources as cs
from evals import request_ledger as rl
from evals import seal

PACKETS_VERSION = 1
SEASON_LINE_SOURCE = "gameLog rows dated before the game date"
STATUS_AS_OF = {"abstractGameState": "Preview", "detailedState": "Scheduled"}
BATCH_SIZE = 5  # games per pipeline "run": the per-run budgets of the live pipeline (10 open-month, 20 Statcast, 10 hand) fit five games
SIDES = ("dev", "test")
_OUTS = re.compile(r"(?P<whole>[0-9]+)(?:\.(?P<outs>[012]))?", re.ASCII)
_COUNTS = ("earnedRuns", "hits", "baseOnBalls", "strikeOuts", "homeRuns", "battersFaced")
_LINE_FIELDS = (
    ("era", "era"),
    ("whip", "whip"),
    ("innings", "inningsPitched"),
    ("strikeouts", "strikeOuts"),
    ("walks", "baseOnBalls"),
    ("home_runs_allowed", "homeRuns"),
    ("batters_faced", "battersFaced"),
)


class PacketError(RuntimeError):
    """A case cannot be built as the sealed record says; nothing is guessed."""


class PacketSetMismatch(RuntimeError):
    """The packet set is not the sealed set of case ids (a missing, extra, duplicated or misplaced case)."""


class PacketSetChanged(RuntimeError):
    """A frozen file, the manifest or the lock differs from what was frozen."""


class TestSplitSealed(seal.Sealed):
    """A dev tool asked for a case that is not a dev case."""

    __test__ = False  # not a pytest class


@dataclass(frozen=True)
class BuiltCase:
    case_id: str
    packet: dict
    findings: dict
    live_game: dict
    notes: dict = field(default_factory=dict)


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=1, allow_nan=False) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- the season line from the game log ---------------------------------------------------------------------------------


def _blocks(response: Any) -> dict:
    if not isinstance(response, dict) or not isinstance(response.get("stats"), list):
        raise PacketError("the history answer has no stats list")
    return {block["type"]["displayName"]: block["splits"] for block in response["stats"]}


def _outs(text: Any) -> int | None:
    match = _OUTS.fullmatch(text) if isinstance(text, str) else None
    return int(match["whole"]) * 3 + int(match["outs"] or 0) if match else None


def _count(value: Any) -> bool:
    return type(value) is int and value >= 0


def _ratio(numerator: int, outs: int) -> str:
    return format((Decimal(numerator) / Decimal(outs)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def season_line_as_of(response: dict, official_date: str) -> dict:
    """The starter's regular-season line over the game-log rows dated STRICTLY before `official_date` (D29).

    Same keys as `fetch_pitcher_season_stats`. `{}` (unavailable, never zero) when no row is before the date or when any
    row before it lacks a figure, a game type or a readable innings text. A row on the game date or later is never summed.
    """

    game_day = date.fromisoformat(official_date)
    blocks = _blocks(response)
    if "gameLog" not in blocks:
        raise PacketError("the history answer has no gameLog block")
    outs = earned = hits = walks = strikeouts = homers = faced = rows = 0
    for split in blocks["gameLog"]:
        try:
            day = date.fromisoformat(split["date"])
        except (KeyError, TypeError, ValueError):
            return {}
        if day >= game_day:
            continue
        if split.get("gameType") is None:
            return {}
        if split["gameType"] != "R":
            continue
        stat = split.get("stat")
        row_outs = _outs(stat.get("inningsPitched")) if isinstance(stat, dict) else None
        if row_outs is None or not all(_count(stat.get(key)) for key in _COUNTS):
            return {}
        outs += row_outs
        earned += stat["earnedRuns"]
        hits += stat["hits"]
        walks += stat["baseOnBalls"]
        strikeouts += stat["strikeOuts"]
        homers += stat["homeRuns"]
        faced += stat["battersFaced"]
        rows += 1
    if rows == 0:
        return {}
    return {
        "era": _ratio(27 * earned, outs) if outs else "-.--",
        "whip": _ratio(3 * (hits + walks), outs) if outs else "-.--",
        "innings": f"{outs // 3}.{outs % 3}",
        "strikeouts": strikeouts,
        "walks": walks,
        "home_runs_allowed": homers,
        "batters_faced": faced,
    }


def check_against_year_by_year(response: dict, season: int) -> list[str]:
    """Differences between the whole game log summed and the API's own season line; [] when they agree.

    A season with no single line (not there, or one per club) cannot be checked and is said so."""

    lines = [s for s in _blocks(response).get("yearByYear", ()) if s.get("season") == str(season)]
    if len(lines) != 1:
        return [f"no {season} line in yearByYear" if not lines else f"{len(lines)} {season} lines in yearByYear (more than one club)"]
    ours = season_line_as_of(response, f"{season + 1}-01-01")
    if not ours:
        return ["game log line unavailable"]
    stat = lines[0]["stat"]
    return [
        f"{name}: game log {ours[name]}, season line {stat.get(key)}"
        for name, key in _LINE_FIELDS
        if str(ours[name]) != str(stat.get(key))
    ]


def _check_owner(response: dict, pitcher_id: int) -> None:
    for splits in _blocks(response).values():
        for split in splits:
            player = split.get("player")
            if isinstance(player, dict) and player.get("id") != pitcher_id:
                raise PacketError(f"the history of pitcher {pitcher_id} holds a line of player {player.get('id')}")


# --- one case ------------------------------------------------------------------------------------------------------


@contextmanager
def quiet():
    """The live pipeline prints names and counts of what it fetches; a packet build prints nothing."""

    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        yield


@contextmanager
def fixed_season(season: tuple[date, date]):
    """Answer `season_dates` from the selection record, so no `seasons` request is ever made."""

    real = lp.season_dates

    def dates(year: int) -> tuple[date, date]:
        if year != season[0].year:
            raise PacketError(f"no season dates recorded for {year}")
        return season

    lp.season_dates = dates
    try:
        yield
    finally:
        lp.season_dates = real


def check_season(season: tuple[date, date]) -> None:
    """The recorded season must agree with the saved MLB calendar (one source for the end of the regular season)."""

    saved = season_calendar.regular_season_end(season[0].year)
    if saved is not None and saved != season[1]:
        raise PacketError(f"the recorded season ends {season[1]}, the saved calendar says {saved}")


def _series(record: dict, raw: dict) -> dict | None:
    postseason = raw.get("gameType") in series_module.POSTSEASON_GAME_TYPES
    recorded = record.get("series")
    if not postseason:
        if recorded is not None:
            raise PacketError(f"{record['case_id']}: a regular-season game has a recorded series")
        return None
    if not isinstance(recorded, dict):
        raise PacketError(f"{record['case_id']}: a postseason case has no recorded standing")
    try:
        standing = bd.case_series({"seriesGameNumber": raw.get("seriesGameNumber")}, recorded)
    except bd.LeakageError as exc:
        raise PacketError(f"{record['case_id']}: {exc}") from exc
    return series_module.build(
        raw.get("gameType"), raw.get("seriesDescription"), raw.get("seriesGameNumber"), raw.get("gamesInSeries"), standing["result"]
    )


def build_case(
    record: dict,
    raw_game: dict,
    histories: tuple,
    season: tuple[date, date],
    fetch_day: str,
    refused: Callable[[], bool] = lambda: False,
) -> BuiltCase:
    """One packet and its findings. `histories` are the cached game-log answers of the away and home starters.

    `refused` reports a request the ledger refused: the fetchers swallow every error, so a refused reservation would look
    like an unavailable figure; here it stops the build instead."""

    case_id, official, as_of = record["case_id"], record["official_date"], record.get("as_of")
    bd.check_as_of(official, as_of)
    if raw_game.get("gamePk") != record["game_pk"] or raw_game.get("officialDate") != official:
        raise PacketError(f"{case_id}: the schedule game is not game {record['game_pk']} of {official}")
    game = lp.game_record({**raw_game, "status": dict(STATUS_AS_OF)})
    pitchers = [game["away_pitcher_id"], game["home_pitcher_id"]]
    if pitchers != list(record["pitcher_ids"]):
        raise PacketError(f"{case_id}: the schedule lists starters {pitchers}, the record says {record['pitcher_ids']}")
    for response, pitcher_id in zip(histories, pitchers):
        _check_owner(response, pitcher_id)
    series = _series(record, raw_game)
    lines = [season_line_as_of(response, official) for response in histories]

    lp._run_errors.clear()
    lp._run_warnings.clear()
    with quiet(), fixed_season(season):
        starters = [
            lp.fetch_pitcher_statcast(pitcher_id, name, as_of=as_of, season_stats=line)
            for pitcher_id, name, line in zip(pitchers, (game["away_pitcher_name"], game["home_pitcher_name"]), lines)
        ]
        splits = [lp.fetch_team_splits(game[f"{side}_team_id"], as_of=as_of) for side in ("away", "home")]
    if refused():
        raise rl.CeilingReached(f"{case_id}: the ledger refused a request")
    if any(starter is None for starter in starters):
        failed = sorted({f"{e['source']}/{e['code']}" for e in lp._run_errors})
        raise PacketError(f"{case_id}: a starter could not be built ({', '.join(failed) or 'no error recorded'})")
    away, home = starters
    live_game = {
        "featured_game": game,
        "as_of": as_of,
        "away_starter": away,
        "home_starter": home,
        "combined_charts": {"pitch_mix": lp._combine_pitch_mix(away, home), "velocity_by_pitch": lp._combine_velocity(away, home)},
        "away_team_splits": splits[0],
        "home_team_splits": splits[1],
        "series": series,
    }
    # Only source and code: the local messages can carry names and counts, and the manifest is readable for both sides.
    errors = [{"source": e["source"], "code": e["code"]} for e in lp._run_errors]
    warnings = [{"source": w["source"], "code": w["code"]} for w in lp._run_warnings]
    with quiet():
        from agents import data_scout, matchup_analyst
        from data_pipeline import generate_demo_json, live_matchup

        unsafe = generate_demo_json._game_unsafe(live_game, date.fromisoformat(official), date.fromisoformat(as_of))
        matchup = live_matchup.build_matchup(
            live_game, matchup_id=case_id, is_featured=True, game_day=official, fetch_day=fetch_day, through=as_of
        )
        packet = data_scout.run(matchup)
        findings = matchup_analyst.run(packet)
    notes = {
        "unsafe": unsafe,
        "errors": errors,
        "warnings": warnings,
        "status_as_of": "upcoming",
        "season_line_source": SEASON_LINE_SOURCE,
        "season_line_check": [check_against_year_by_year(response, season[0].year) for response in histories],
    }
    return BuiltCase(case_id, packet, findings, live_game, notes)


# --- the frozen set ----------------------------------------------------------------------------------------------------


def refuse_published(directory) -> None:
    """The packet set is written under evals/data only: a path through public/data or evals/live is refused, absolute or not."""

    parts = Path(os.path.normpath(directory)).parts
    for forbidden in co.FORBIDDEN:
        width = len(forbidden)
        if any(tuple(parts[i : i + width]) == forbidden for i in range(len(parts))):
            raise co.ForbiddenPath(f"{directory} is inside {'/'.join(forbidden)}, which the packet build never writes")


def _read_json(path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _split(directory: Path) -> list[dict]:
    bd.verify_split_lock(directory)
    return _read_json(directory / "split.json")["cases"]


def _file(directory: Path, kind: str, side: str, case_id: str) -> Path:
    return directory / kind / side / f"{case_id}.json"


def freeze(directory, built: list[BuiltCase], inputs: dict, requests: dict) -> str:
    """Write the packets, the findings, the manifest and its lock, once. Returns the SHA-256 of the manifest."""

    directory = Path(directory)
    refuse_published(directory)
    split = _split(directory)
    if any((directory / name).exists() for name in ("packets", "findings", "packets_manifest.json", "packets.lock")):
        raise PacketSetChanged("a packet set is already frozen here; it is never rewritten")
    sealed = [c["id"] for c in split]
    ids = [b.case_id for b in built]
    missing, extra = sorted(set(sealed) - set(ids)), sorted(set(ids) - set(sealed))
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    if missing or extra or duplicated:
        raise PacketSetMismatch(f"the packet set is not the sealed case ids: missing {missing}, extra {extra}, duplicated {duplicated}")
    by_id = {b.case_id: b for b in built}
    entries = []
    for case in split:
        item, side = by_id[case["id"]], case["split"]
        packet, findings = canonical(item.packet), canonical(item.findings)
        for kind, data in (("packets", packet), ("findings", findings)):
            path = _file(directory, kind, side, case["id"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        entries.append(
            {
                "id": case["id"],
                "stratum": case["stratum"],
                "split": side,
                "selection_sha256": case["sha256"],
                "packet_sha256": sha256(packet),
                "findings_sha256": sha256(findings),
                "inputs": inputs[case["id"]],
                "notes": item.notes,
            }
        )
    manifest = canonical(
        {
            "version": PACKETS_VERSION,
            "split_lock": (directory / "split.lock").read_text(encoding="ascii").strip(),
            "requests": requests,
            "build": {
                "as_of": "official date minus one day (D29)",
                "status_as_of": "upcoming",
                "season_line": SEASON_LINE_SOURCE,
                "series": "the standing recorded in selection.json, checked by build_dataset.case_series",
                "writer_and_critic_run": False,
            },
            "cases": entries,
        }
    )
    (directory / "packets_manifest.json").write_bytes(manifest)
    lock = sha256(manifest)
    (directory / "packets.lock").write_bytes((lock + "\n").encode("ascii"))
    return lock


def read_manifest(directory) -> dict:
    """The manifest, after its lock and the split lock are checked. Reveals no packet content."""

    directory = Path(directory)
    split = _split(directory)
    manifest_bytes = (directory / "packets_manifest.json").read_bytes()
    if sha256(manifest_bytes) != (directory / "packets.lock").read_text(encoding="ascii").strip():
        raise PacketSetChanged("packets_manifest.json differs from the hash pinned in packets.lock")
    manifest = json.loads(manifest_bytes)
    if manifest["split_lock"] != (directory / "split.lock").read_text(encoding="ascii").strip():
        raise PacketSetChanged("the manifest was frozen for another split")
    expected = [(c["id"], c["split"], c["sha256"]) for c in split]
    if [(e["id"], e["split"], e["selection_sha256"]) for e in manifest["cases"]] != expected:
        raise PacketSetChanged("the manifest cases differ from the sealed split (split ids, sides or hashes)")
    return manifest


def verify_packet_set(directory) -> None:
    """The set equals the sealed ids exactly and every file hashes to the manifest. Reads hashes, never content."""

    directory = Path(directory)
    manifest = read_manifest(directory)
    for kind, key in (("packets", "packet_sha256"), ("findings", "findings_sha256")):
        found = {side: seal.hashes(directory / kind, side) for side in SIDES}
        wanted = {side: {f"{e['id']}.json": e[key] for e in manifest["cases"] if e["split"] == side} for side in SIDES}
        for side in SIDES:
            extra = sorted(set(found[side]) - set(wanted[side]))
            if extra:
                raise PacketSetMismatch(f"{kind}/{side} holds files that are not sealed cases of that side: {extra}")
        for side in SIDES:
            missing = sorted(set(wanted[side]) - set(found[side]))
            if missing:
                raise PacketSetChanged(f"{kind}/{side} is missing {missing}")
            for name, digest in wanted[side].items():
                if found[side][name] != digest:
                    raise PacketSetChanged(f"{kind}/{side}/{name} differs from the frozen hash")


def dev_case_ids(directory) -> list[str]:
    return [c["id"] for c in _split(Path(directory)) if c["split"] == "dev"]


def _load_dev(directory, case_id: str, kind: str, key: str) -> dict:
    directory = Path(directory)
    if case_id not in dev_case_ids(directory):
        raise TestSplitSealed(f"{case_id!r} is not a dev case; only dev packets and findings are opened by dev tools")
    manifest = read_manifest(directory)
    entry = next(e for e in manifest["cases"] if e["id"] == case_id)
    data = _file(directory, kind, "dev", case_id).read_bytes()
    if sha256(data) != entry[key]:
        raise PacketSetChanged(f"{kind}/dev/{case_id}.json differs from the frozen hash")
    return json.loads(data)


def load_dev_packet(directory, case_id: str) -> dict:
    return _load_dev(directory, case_id, "packets", "packet_sha256")


def load_dev_findings(directory, case_id: str) -> dict:
    return _load_dev(directory, case_id, "findings", "findings_sha256")


def summary_lines(directory) -> list[str]:
    """Ids, sides and hashes, for any caller: no content."""

    directory = Path(directory)
    manifest = read_manifest(directory)
    lines = [f"{e['id']}\t{e['split']}\tpacket {e['packet_sha256']}\tfindings {e['findings_sha256']}" for e in manifest["cases"]]
    lines.append(f"manifest {(directory / 'packets.lock').read_text(encoding='ascii').strip()}")
    return lines


# --- what a build needs, and the build ----------------------------------------------------------------------------------


def team_code(team_id: int) -> str | None:
    abbreviation = lp.MLB_TEAM_ABBR_BY_ID.get(team_id)
    return lp.STATCAST_TEAM_CODE_BY_MLB_ABBR.get(abbreviation, abbreviation)


def plan_requests(records: list[dict], schedule: dict, season: tuple[date, date], store: cs.HistoryStore, team_cache_dir=None) -> dict:
    """Offline: the requests a build of `records` would send, given the caches on disk. Sends nothing.

    Statcast pitcher requests are an upper bound (pybaseball's own cache may hold some). Hand lookups happen only when a
    Statcast answer cannot say the hand, so none are planned. MLB lookups must be 0: every input is already on disk."""

    cache = Path(team_cache_dir) if team_cache_dir else lp.TEAM_BATTING_CACHE_DIR
    missing_games = [r["case_id"] for r in records if r["game_pk"] not in schedule]
    missing_history = sorted({p for r in records for p in r["pitcher_ids"] if not store.known(p)})
    needed: dict = {"closed": set(), "open": set()}
    for record in records:
        game = schedule.get(record["game_pk"])
        if game is None:
            continue
        cutoff = date.fromisoformat(record["as_of"])
        for side in ("away", "home"):
            code = team_code(game.raw["teams"][side]["team"]["id"])
            if code is None:
                continue
            for start, end in lp._month_chunks(season[0], min(cutoff, season[1])):
                if not (cache / f"{code}_{start}_{end}.csv").exists():
                    needed["open" if lp._is_open_chunk(end, season[1]) else "closed"].add((code, start, end))
    return {
        "savant_closed_month": len(needed["closed"]),
        "savant_open_month": len(needed["open"]),
        "pitcher_statcast": 2 * len(records),
        "pitcher_hand": 0,
        "mlb": 0,
        "missing_games": missing_games,
        "missing_history": missing_history,
    }


def build_all(
    records: list[dict],
    schedule: dict,
    store: cs.HistoryStore,
    season: tuple[date, date],
    fetch_day: str,
    ledger: rl.RequestLedger,
    scratch,
) -> tuple[list[BuiltCase], dict]:
    """Every case, in batches of `BATCH_SIZE` (one pipeline run each: the per-run budgets reset per batch).

    Each built case is kept in `scratch` (untracked) so a halted build resumes without asking again, even after pybaseball's
    own cache expires. Returns the cases and, per case, the digests of the cached inputs it read."""

    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    built: list[BuiltCase] = []
    inputs: dict = {}
    with rl.counted_savant(ledger), rl.counted_statcast_pitcher(ledger), rl.counted_mlb(ledger):
        for first in range(0, len(records), BATCH_SIZE):
            lp.reset_run_budgets()
            for record in records[first : first + BATCH_SIZE]:
                case_id = record["case_id"]
                game = schedule[record["game_pk"]]
                inputs[case_id] = {
                    "schedule_file": game.file,
                    "schedule_sha256": game.sha256,
                    "history_sha256": [store.cached_digest(p) for p in record["pitcher_ids"]],
                }
                path = scratch / f"{case_id}.json"
                if path.exists():
                    saved = _read_json(path)
                    item = BuiltCase(case_id, saved["packet"], saved["findings"], {}, saved["notes"])
                else:
                    histories = tuple(store.cached_response(p) for p in record["pitcher_ids"])
                    item = build_case(record, game.raw, histories, season, fetch_day, refused=lambda: ledger.refused)
                    path.write_bytes(canonical({"packet": item.packet, "findings": item.findings, "notes": item.notes}))
                built.append(item)
    return built, inputs


def requests_used(ledger: rl.RequestLedger, since: int) -> dict:
    """Reservations per ceiling group from ledger row `since` on (the rows this build wrote)."""

    used = {group: 0 for group in rl.CEILINGS}
    for row in ledger.rows[since:]:
        if row["kind"] == "reserve":
            used[rl.GROUP[row["source"]]] += 1
    return used


# --- the command line ----------------------------------------------------------------------------------------------------


def _load(args) -> tuple[list[dict], dict, tuple[date, date], cs.HistoryStore, dict]:
    dataset = Path(args.dataset)
    selection = _read_json(dataset / "selection.json")
    season = (date.fromisoformat(selection["season"][0]), date.fromisoformat(selection["season"][1]))
    check_season(season)
    sealed = [c["id"] for c in _split(dataset)]
    by_id = {r["case_id"]: r for r in selection["cases"]}
    if sorted(by_id) != sorted(sealed):
        raise PacketSetMismatch("selection.json and the sealed split do not hold the same case ids")
    records = [by_id[i] for i in sealed]
    schedule = cs.cached_schedule(args.schedule_dir)
    return records, schedule, season, cs.HistoryStore(args.history_dir, season[0].year), selection


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="python -m evals.build_packets")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "build", "verify", "summary"):
        sub = commands.add_parser(name)
        sub.add_argument("--dataset", default="evals/data/dataset")
        sub.add_argument("--history-dir", default="data_cache/raw/pitcher_history")
        sub.add_argument("--schedule-dir", default="data_cache/raw/mlb_schedule")
        sub.add_argument("--ledger", default="evals/data/request_ledger.jsonl")
        sub.add_argument("--scratch", default="data_cache/processed/packets_build")
    return parser.parse_args(argv)


def main(argv=None) -> int:  # pragma: no cover - the network entry point of the packet build
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.command == "verify":
        verify_packet_set(args.dataset)
        print("packet set verified")
        return 0
    if args.command == "summary":
        print("\n".join(summary_lines(args.dataset)))
        return 0
    refuse_published(Path(args.dataset))
    records, schedule, season, store, selection = _load(args)
    ledger = rl.RequestLedger(args.ledger)
    plan = plan_requests(records, schedule, season, store)
    report = {"needed": plan, "ledger_used": {g: ledger.count(g) for g in rl.CEILINGS}, "ceilings": dict(rl.CEILINGS)}
    over = [g for g in rl.CEILINGS if ledger.count(g) + plan.get(g, 0) > rl.CEILINGS[g]]
    blocked = bool(over or plan["missing_games"] or plan["missing_history"] or plan["mlb"])
    if args.command == "preflight" or blocked:
        print(json.dumps({**report, "over_ceiling": over, "blocked": blocked}, indent=1, sort_keys=True))
        return 3 if blocked else 0
    marker = Path(args.scratch) / "ledger_start.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    if not marker.exists():
        marker.write_text(json.dumps({"ledger_rows_before": len(ledger.rows)}), encoding="utf-8")
    since = json.loads(marker.read_text(encoding="utf-8"))["ledger_rows_before"]
    try:
        built, inputs = build_all(records, schedule, store, season, selection["collection_date"], ledger, args.scratch)
    except (rl.CeilingReached, PacketError) as exc:
        print(json.dumps({"stopped": type(exc).__name__, "reason": str(exc)[:300], "ledger_used": report["ledger_used"]}))
        return 3
    used = requests_used(ledger, since)
    digest = freeze(args.dataset, built, inputs, used)
    print(json.dumps({"manifest_sha256": digest, "requests": used, "cases": len(built)}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
