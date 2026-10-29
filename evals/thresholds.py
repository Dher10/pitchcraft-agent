"""D32 recompute (docs/plans/P2.4.md section 1): the upper quartile of lineup-vs-hand K%, BB% and OPS over the
60 team-hand rows of one regular season, compared with the cutoffs in `labels.py`.

Method, fixed before any data was read: one row per team and pitcher hand from the pipeline's own split code
(`derive_team_splits`, regular season through the cutoff); a row needs at least MIN_PA plate appearances; K% and
BB% are taken from the counts (unrounded), OPS is the three-decimal figure the card shows; percentiles are linear
(numpy default) over the pooled rows; K% and BB% round half up to a whole percent and OPS half up to .005. The
cases of the dataset are never used here. This module never changes `labels.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
import hashlib
import json
from pathlib import Path
import platform

import numpy

from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline

MIN_PA = 200
QUARTILES = (25, 50, 75)
MIN_ROWS = 20  # fewer rows than this cannot give a quartile worth comparing
CONSTANTS = {"k": "OFFENSE_K_NOTE_PCT", "bb": "OFFENSE_BB_NOTE_PCT", "ops": "OFFENSE_OPS_STRONG"}


@dataclass(frozen=True)
class TeamHand:
    team: str
    hand: str
    pa: int
    k: float  # percent, unrounded
    bb: float  # percent, unrounded
    ops: float  # as the card shows it, three decimals


@dataclass(frozen=True)
class Result:
    n_used: int
    excluded: tuple[TeamHand, ...]
    pooled: dict
    by_hand: dict
    cutoffs: dict


@dataclass(frozen=True)
class Comparison:
    unchanged: bool
    changed: dict  # figure -> (current, recomputed)


def percentile(values, q):
    return float(numpy.percentile(numpy.asarray(values, dtype=float), q))


def _half_up(value, step):
    units = (Decimal(repr(float(value))) / Decimal(step)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
    return float(units * Decimal(step))


def round_k_bb(value):
    """Whole percent, half up."""

    return _half_up(value, "1")


def round_ops(value):
    """To .005, half up."""

    return round(_half_up(value, "0.005"), 3)


def team_hand_rows(frames, cutoff):
    """One row per team and hand from cached team-batting frames, through `cutoff`, regular season only."""

    rows = []
    for team in sorted(frames):
        splits = live_pipeline.derive_team_splits(frames[team], team, cutoff)
        for key, hand in (("vl", "L"), ("vr", "R")):
            line = splits.get(key)
            if line is None or not line["plate_appearances"] or line["ops"] is None:
                continue
            pa = line["plate_appearances"]
            rows.append(TeamHand(team, hand, pa, line["strikeouts"] / pa * 100, line["walks"] / pa * 100, float(line["ops"])))
    return rows


def _quartiles(rows):
    return {name: {q: percentile([getattr(r, name) for r in rows], q) for q in QUARTILES} for name in CONSTANTS}


def recompute(rows):
    used = [r for r in rows if r.pa >= MIN_PA]
    excluded = tuple(r for r in rows if r.pa < MIN_PA)
    if len(used) < MIN_ROWS:
        raise ValueError(f"{len(used)} usable team-hand rows: too few for a quartile")
    pooled = _quartiles(used)
    by_hand = {hand: _quartiles([r for r in used if r.hand == hand]) for hand in ("L", "R")}
    cutoffs = {
        "k": round_k_bb(pooled["k"][75]),
        "bb": round_k_bb(pooled["bb"][75]),
        "ops": round_ops(pooled["ops"][75]),
    }
    return Result(len(used), excluded, pooled, by_hand, cutoffs)


def compare(result):
    changed = {}
    for name, constant in CONSTANTS.items():
        current = getattr(labels, constant)
        if result.cutoffs[name] != current:
            changed[name] = (current, result.cutoffs[name])
    return Comparison(not changed, changed)


def statcast_team_codes():
    abbreviations = sorted(set(live_pipeline.MLB_TEAM_ABBR_BY_ID.values()))
    return [live_pipeline.STATCAST_TEAM_CODE_BY_MLB_ABBR.get(a, a) for a in abbreviations]


def load_frames(season_start, season_end):
    """The cached or (through the counted fetcher) fetched frames of the 30 teams for the whole regular season."""

    return {
        code: live_pipeline.fetch_team_batting_statcast(code, season_start, season_end, season_end=season_end)
        for code in statcast_team_codes()
    }


def cache_manifest(season_start, season_end):
    """File name, size and SHA-256 of every cached month the recompute read, with the file's modified time."""

    entries = []
    for code in statcast_team_codes():
        for start, end in live_pipeline._month_chunks(season_start, season_end):
            path = live_pipeline.TEAM_BATTING_CACHE_DIR / f"{code}_{start}_{end}.csv"
            data = path.read_bytes()
            stamp = path.stat().st_mtime
            entries.append({"file": path.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "mtime": stamp})
    return entries


def evidence(result, comparison, manifest, season_start, season_end):
    import pandas

    def fmt(table):
        return {name: {str(q): round(v, 4) for q, v in qs.items()} for name, qs in table.items()}

    return {
        "season": season_end.year,
        "window": [season_start.isoformat(), season_end.isoformat()],
        "min_pa": MIN_PA,
        "rows_used": result.n_used,
        "excluded": [{"team": r.team, "hand": r.hand, "pa": r.pa} for r in result.excluded],
        "pooled": fmt(result.pooled),
        "by_hand": {hand: fmt(table) for hand, table in result.by_hand.items()},
        "rounded_cutoffs": result.cutoffs,
        "current_cutoffs": {n: getattr(labels, c) for n, c in CONSTANTS.items()},
        "unchanged": comparison.unchanged,
        "changed": {n: {"current": a, "recomputed": b} for n, (a, b) in comparison.changed.items()},
        "software": {"python": platform.python_version(), "numpy": numpy.__version__, "pandas": pandas.__version__},
        "cache": manifest,
    }


def run(season_start, season_end, out_path):
    """Gate 3: recompute from the (fetched) cache and write the evidence file. Does not touch labels.py."""

    frames = load_frames(season_start, season_end)
    result = recompute(team_hand_rows(frames, season_end))
    comparison = compare(result)
    record = evidence(result, comparison, cache_manifest(season_start, season_end), season_start, season_end)
    Path(out_path).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result, comparison, record


def main():  # pragma: no cover - the network entry point of gate 3
    from evals.request_ledger import RequestLedger, counted_savant

    season_start, season_end = date(2026, 3, 25), date(2026, 9, 27)
    ledger = RequestLedger(Path("evals/data/request_ledger.jsonl"))
    with counted_savant(ledger):
        result, comparison, _ = run(season_start, season_end, Path("evals/data/d32_recompute.json"))
    print(json.dumps({"cutoffs": result.cutoffs, "unchanged": comparison.unchanged, "changed": comparison.changed}))
    return 0 if comparison.unchanged else 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
