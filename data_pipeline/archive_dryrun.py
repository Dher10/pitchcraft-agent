"""The report of the R4-D7 dry run (docs/plans/R4.md 4.1; D66). Pure: it reads files and prints; no network, no writes.

It answers four questions about a few built days:

1. REQUESTS: how many requests each source took, against the ceilings of D66.
2. STARTERS: probable against actual starter, and, for every starter that is unknown, WHY. An unknown because MLB gave
   nothing is the data's; an unknown because the boxscore has the data in a shape the parser does not read is ours, and
   stops the work (owner, Nov 12): a real run never publishes starters unknown because of a parser mismatch.
3. NOTABLE: how many games each notable reason tags, and the veteran rule at several values of V (nothing is tuned here).
4. PRIOR MLB SEASONS: the spread among the starters seen, for the owner to set V from.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

from data_pipeline import archive_games as ag
from data_pipeline import archive_index as ai
from data_pipeline.archive_boxscore import _FIELDS, _line, _side, _starter

SOURCES = ("mlb", "savant")
FIXED_REASONS = tuple(reason for reason in ai.REASONS if reason != "veteran_duel")
STOP_CLASSES = ("parser_mismatch", "boxscore_not_fetched")
EXIT_STOP, EXIT_USAGE = 3, 2


def _is_id(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def classify_side(raw: Any, side: str, probable_id: Any) -> str:
    """
    Why a side is, or is not, readable from `raw` (a boxscore answer as received, or None when none was kept):
    `readable`, `boxscore_not_fetched`, `no_probable_starter`, `mlb_lacks_data` (the answer says no pitcher was listed) or
    `parser_mismatch` (anything else: there is data, or a shape, that the parser does not read).
    """

    if raw is None:
        return "boxscore_not_fetched"
    # The boxscore side is judged first: a report with no probable starter must not hide a shape the parser cannot read.
    node = _side(raw, side)
    if _starter(node) is not None:
        return "readable" if _is_id(probable_id) else "no_probable_starter"
    if node is not None and isinstance(node.get("pitchers"), list) and node["pitchers"] == []:
        return "mlb_lacks_data"  # a judgment: the answer itself lists no pitcher for this side
    return "parser_mismatch"


def line_mismatches(raw: Any, side: str) -> list[str]:
    """The final-line fields the answer gives (not null) but the parser rejects; `stats` when the starter has no stats."""

    if raw is None:
        return []
    found = _starter(_side(raw, side))
    if found is None:
        return []
    _who, stats = found
    if stats is None:
        return ["stats"]
    line = _line(stats)
    return [name for name, key in _FIELDS.items() if stats.get(key) is not None and (line is None or line[name] is None)]


def _probable_name(document: Mapping[str, Any], side: str) -> str | None:
    try:
        value = document["payload"]["matchups"][0]["starters"][f"{side}_starter"]["name"]
    except (KeyError, TypeError, IndexError):
        return None
    return value if isinstance(value, str) else None


def starter_rows(documents: Sequence[Mapping[str, Any]], raws: Mapping[int, Any]) -> list[dict[str, Any]]:
    """One row per game side: the probable starter, who started, the check, and why it is (not) readable."""

    rows = []
    for document in documents:
        pk = document["game_pk"]
        raw = raws.get(pk)
        for side in ag.SIDES:
            fact = document["starter_facts"][side]
            probable = fact["id"] if isinstance(fact, Mapping) else None
            rows.append({
                "game_pk": pk,
                "side": side,
                "probable_id": probable,
                "probable_name": _probable_name(document, side),
                "actual": document["starters_check"]["actual"][side],
                "check": document["starters_check"][side],
                "class": classify_side(raw, side, probable),
                "line_mismatches": line_mismatches(raw, side),
            })
    return rows


def stop_reasons(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """What stops the work: our parser's failures, and a boxscore that was not fetched (that is not proof MLB lacks it)."""

    reasons = []
    for row in rows:
        if row["class"] in STOP_CLASSES:
            reasons.append(f"game {row['game_pk']} {row['side']}: {row['class']}")
        if row["line_mismatches"]:
            reasons.append(f"game {row['game_pk']} {row['side']}: final-line field given but not read: {', '.join(row['line_mismatches'])}")
    return reasons


def run_problems(summaries: Sequence[Mapping[str, Any]], totals: Mapping[str, Mapping[str, Any]], files: int) -> list[str]:
    """What the runs themselves report as wrong: a failed game, a stop, a ceiling passed, or files that are not the games built."""

    problems = []
    for index, summary in enumerate(summaries, start=1):
        for item in summary.get("failed", []):
            problems.append(f"run {index}: failed {json.dumps(item, sort_keys=True)}")
        if summary.get("stopped") is not None:
            problems.append(f"run {index}: stopped by {summary['stopped']}")
    for source in SOURCES:
        if not totals[source]["within"]:
            problems.append(f"{source}: {totals[source]['used']} requests, past the ceiling of {totals[source]['ceiling']}")
    expected = sum(len(s.get("built", [])) + len(s.get("skipped", [])) for s in summaries)
    if files != expected:
        problems.append(f"{files} game files, but the runs built or skipped {expected}")
    return problems


def parse_summaries(text: str) -> list[dict[str, Any]]:
    """The `archive: {...}` summary lines the builder prints, in order. A line that is not JSON is refused."""

    found = []
    for line in text.splitlines():
        if line.startswith("archive: "):
            value = json.loads(line[len("archive: "):])
            if not isinstance(value, dict):
                raise ValueError("a summary is an object")
            found.append(value)
    return found


def total_requests(summaries: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Requests by source, added over the runs, against each source's ceiling."""

    if not summaries:
        raise ValueError("no summary")
    total = {}
    for source in SOURCES:
        ceilings = {s["requests"][source]["ceiling"] for s in summaries}
        if len(ceilings) != 1:
            raise ValueError("the runs have different ceilings")
        used = sum(s["requests"][source]["used"] for s in summaries)
        ceiling = ceilings.pop()
        total[source] = {"used": used, "ceiling": ceiling, "within": used <= ceiling}
    return total


def notable_table(documents: Sequence[Mapping[str, Any]], sweep: Sequence[int]) -> dict[str, Any]:
    """How many games each reason tags: the fixed ones once, the veteran rule and the union for each V of `sweep`."""

    games = len(documents)
    fixed = {reason: 0 for reason in FIXED_REASONS}
    for document in documents:
        for reason in ai.notable_reasons(document, 1):
            if reason in fixed:
                fixed[reason] += 1
    by_v: dict[int, dict[str, Any]] = {}
    for v in sweep:
        reasons = [ai.notable_reasons(document, v) for document in documents]
        any_count = sum(1 for found in reasons if found)
        by_v[v] = {
            "veteran_duel": sum(1 for found in reasons if "veteran_duel" in found),
            "any": any_count,
            "share": any_count / games if games else None,
        }
    return {"games": games, "fixed": fixed, "by_v": by_v}


def prior_seasons_distribution(documents: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Prior MLB seasons per distinct starter seen: a count for each known value, and how many are unknown."""

    seen: dict[int, int | None] = {}
    for document in documents:
        for side in ag.SIDES:
            fact = document["starter_facts"][side]
            if not isinstance(fact, Mapping):
                continue
            seasons = fact.get("prior_mlb_seasons")
            if fact["id"] not in seen or seen[fact["id"]] is None:
                seen[fact["id"]] = seasons
    counts = Counter(value for value in seen.values() if value is not None)
    return {
        "starters": len(seen),
        "known": dict(sorted(counts.items())),
        "unknown": sum(1 for value in seen.values() if value is None),
    }


# --- text ---------------------------------------------------------------------------------------------------------------


def render(
    totals: Mapping[str, Mapping[str, Any]], summaries: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]],
    table: Mapping[str, Any], spread: Mapping[str, Any], stops: Sequence[str],
) -> str:
    out = ["REQUESTS (added over the runs; a ceiling is the hard limit of D66)"]
    for source in SOURCES:
        entry = totals[source]
        out.append(f"  {source}: {entry['used']} of {entry['ceiling']}" + ("" if entry["within"] else "  PAST THE CEILING"))
    built = sum(len(s.get("built", [])) for s in summaries)
    skipped = sum(len(s.get("skipped", [])) for s in summaries)
    failed = [item for s in summaries for item in s.get("failed", [])]
    out.append(f"  runs: {len(summaries)}; games built {built}, skipped {skipped}, failed {len(failed)}; stopped by: {[s.get('stopped') for s in summaries]}")
    for item in failed:
        out.append(f"  failed: {json.dumps(item, sort_keys=True)}")

    out.append("")
    out.append("STARTERS (probable = the starter the report was written for; actual = first pitcher listed in the boxscore)")
    checks = Counter(row["check"] for row in rows)
    classes = Counter(row["class"] for row in rows)
    out.append(f"  check: {dict(sorted(checks.items()))}")
    out.append(f"  why readable or not: {dict(sorted(classes.items()))}")
    for row in rows:
        actual = row["actual"]["name"] if isinstance(row["actual"], Mapping) else None
        out.append(
            f"  game {row['game_pk']} {row['side']}: probable {row['probable_name']} ({row['probable_id']}), actual {actual}, "
            f"{row['check']}, {row['class']}" + (f", line fields rejected: {row['line_mismatches']}" if row["line_mismatches"] else "")
        )

    out.append("")
    out.append(f"NOTABLE ({table['games']} games; the rules are fixed, nothing is tuned here)")
    for reason, count in table["fixed"].items():
        out.append(f"  {reason}: {count}")
    out.append("  veteran_duel by V (both starters at least V prior MLB seasons), and games with any reason:")
    for v, entry in table["by_v"].items():
        share = "n/a" if entry["share"] is None else f"{entry['share'] * 100:.0f}%"
        out.append(f"    V={v}: veteran_duel {entry['veteran_duel']}, any reason {entry['any']} ({share})")

    out.append("")
    out.append(f"PRIOR MLB SEASONS ({spread['starters']} distinct starters in these games)")
    for seasons, count in spread["known"].items():
        out.append(f"  {seasons} prior seasons: {count}")
    out.append(f"  unknown: {spread['unknown']}")

    out.append("")
    if stops:
        out.append("STOP: do not run the real backfill. A parser mismatch is fixed with a recorded real fixture and a red test; a failed game or a missing boxscore is understood first:")
        out.extend(f"  {reason}" for reason in stops)
    else:
        out.append("nothing stops the work: no parser mismatch, no missing boxscore, no failed game, no ceiling passed")
    return "\n".join(out) + "\n"


def _sweep(text: str) -> list[int]:
    values = [int(part) for part in text.split(",")]
    if not values or any(not 1 <= v <= ai.MAX_VETERAN_MIN for v in values) or values != sorted(set(values)):
        raise ValueError("the sweep is strictly increasing integers from 1 to 30")
    return values


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report of the R4-D7 dry run (reads files only).")
    parser.add_argument("--out", type=Path, required=True, help="the folder the builder wrote (its games/ folder is read)")
    parser.add_argument("--raw-dir", type=Path, required=True, help="the boxscore answers the builder kept")
    parser.add_argument("--summary", type=Path, nargs="+", required=True, help="the builder's output, one file per run")
    parser.add_argument("--veteran-sweep", default="1,2,3,4,5,6,7,8,9,10", help="the values of V to count, increasing")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        sweep = _sweep(args.veteran_sweep)
        documents = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((args.out / "games").glob("*.json"))]
        if not documents or any(ag.validate_game_file(document) for document in documents):
            raise ValueError("no game files, or one is not valid")
        raws = {}
        for document in documents:
            path = args.raw_dir / f"{document['game_pk']}.json"
            if path.exists():
                raws[document["game_pk"]] = json.loads(path.read_text(encoding="utf-8"))
        summaries = [s for path in args.summary for s in parse_summaries(path.read_text(encoding="utf-8"))]
        totals = total_requests(summaries)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"dryrun: failed usage {type(exc).__name__}", file=sys.stderr)
        return EXIT_USAGE
    rows = starter_rows(documents, raws)
    stops = run_problems(summaries, totals, len(documents)) + stop_reasons(rows)
    sys.stdout.write(render(totals, summaries, rows, notable_table(documents, sweep), prior_seasons_distribution(documents), stops))
    return EXIT_STOP if stops else 0


if __name__ == "__main__":
    raise SystemExit(main())
