"""D64: B1 on all 40 cases (20 dev, 20 test) with the instrument frozen at 0426c02.

The ten dev examples of run 5 are reused as they were saved (same frozen inputs, same run identity); the other
ten dev cases and the twenty test cases are run now. Test outputs go to the sealed layout of evals/seal.py
(`<root>/<split>/<case>.json`) and this module never prints, summarizes or reads them back for content: it
reports per-split counts only. Writing the FROZEN file that opens the test outputs for the labeling is not done here.
`evals/run_b1.py` is not modified (its hash is part of the freeze); only the packet loader it calls is wrapped.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from agents import call_budget as cb
from agents import llm_report_writer as lw
from agents import nli_admission, writer_input
from evals import build_packets as bp
from evals import experiment_freeze as freeze
from evals import run_b1 as r
from evals import seal

ROOT = r.ROOT
DATASET = r.DATASET
WORK = r.WORK
RUN_ID = "b1-full-1"
OUT = WORK / "b1-full"                       # sealed layout: OUT/<split>/<case>.json
REUSED_DIR = WORK / r.ITEMS_DIR              # run 5, the first ten dev cases
RECORD = ROOT / "evals" / "data" / "writer" / "b1-run-record.json"
REPORT = ROOT / "docs" / "b1-dev-run6.md"
RUN_CAP = 100


class _Packets:
    """Stands in for `build_packets` inside `run_b1`: dev ids as before, other sealed ids through the manifest."""

    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def _load(self, directory, case_id, kind, key):
        manifest = bp.read_manifest(directory)
        entry = next(e for e in manifest["cases"] if e["id"] == case_id)
        side = entry["split"]
        data = bp._file(Path(directory), kind, side, case_id).read_bytes()
        if bp.sha256(data) != entry[key]:
            raise bp.PacketSetChanged(f"{kind} of {case_id} differs from the frozen hash")
        return json.loads(data)

    def load_dev_packet(self, directory, case_id):
        return self._load(directory, case_id, "packets", "packet_sha256")

    def load_dev_findings(self, directory, case_id):
        return self._load(directory, case_id, "findings", "findings_sha256")


def plan_cases() -> tuple[list[str], list[str], list[str]]:
    """(reused dev ids, new dev ids, held-out ids), all in the sealed split order. Ids only."""

    split = bp._split(DATASET)
    reused = r.pick_cases()
    new_dev = [c["id"] for c in split if c["split"] == "dev" and c["id"] not in reused]
    held = [c["id"] for c in split if c["split"] != "dev"]
    assert len(reused) == 10 and len(new_dev) == 10 and len(held) == 20
    return reused, new_dev, held


def split_of(case_id: str) -> str:
    return next(c["split"] for c in bp._split(DATASET) if c["id"] == case_id)


def run_cases(case_ids, glossary, provider, budget, nli, on_item=None, clock=time.time):
    """Every case in order, with the two early stops of D57 over this run's calls. Returns (items, stop or None)."""

    items, stop = [], None
    for case_id in case_ids:
        directory = OUT / split_of(case_id)
        if stop is not None and not (directory / f"{case_id}.json").exists():
            items.append({"case_id": case_id, "path": "not_attempted", "reason": stop["reason"]})
            continue
        items.append(r.run_item(case_id, DATASET, glossary, provider, budget, directory, nli=nli))
        if on_item:
            on_item(items[-1])
        capacity, done = r.capacity_share(budget)
        attempted = {x["item"] for x in budget.rows if x["kind"] == "reserve" and x["run"] == budget.run}
        reason = "capacity_stop" if r.should_stop(capacity, done) else "average_call_stop" if r.average_stop(len(attempted), budget.used_run) else None
        if reason and stop is None:
            stop = {"reason": reason, "cases": len(attempted), "after_case": case_id, "at_epoch": clock(), "capacity": capacity,
                    "calls": budget.used_run, "by_model": r.capacity_by_model(budget)}
    return items, stop


def counts(items):
    """Per-split numbers that reveal no content: outcomes, paths and attempt counts."""

    paths = {}
    for i in items:
        paths[i["path"]] = paths.get(i["path"], 0) + 1
    return {"cases": len(items), "accepted": sum(i["path"] not in ("rules", "not_attempted") for i in items),
            "rejected": sum(i["path"] == "rules" for i in items), "not_attempted": sum(i["path"] == "not_attempted" for i in items),
            "paths": dict(sorted(paths.items())), "content_attempts": sum(i.get("content_attempts", 0) for i in items)}


def main(argv=None) -> int:  # pragma: no cover - the network entry point
    parser = argparse.ArgumentParser(description="D64 B1 on 40 cases")
    parser.add_argument("--owner-pc-offline", action="store_true")
    parser.add_argument("--run-cap", type=int, default=RUN_CAP)
    args = parser.parse_args(argv)
    if not args.owner_pc_offline:
        parser.error("--owner-pc-offline is required to make requests")
    try:
        frozen = freeze.verify_frozen(freeze.FREEZE_PATH, DATASET, r.pick_cases())
        bp.verify_packet_set(DATASET)
    except (freeze.FrozenInputsChanged, bp.PacketSetChanged, bp.PacketSetMismatch):
        print(json.dumps({"stopped": "frozen_inputs_changed"}))
        return 1
    if args.run_cap > RUN_CAP:
        print(json.dumps({"stopped": "run_cap_above_decision"}))
        return 1
    from evals.local_runner import _local_key

    r.bp = _Packets(bp)
    reused, new_dev, held = plan_cases()
    for case_id in reused:  # the saved run-5 items, copied into the layout without change
        target = OUT / "dev" / f"{case_id}.json"
        if not target.exists():
            (OUT / "dev").mkdir(parents=True, exist_ok=True)
            target.write_bytes((REUSED_DIR / f"{case_id}.json").read_bytes())
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    budget = cb.CallBudget(WORK / "calls.jsonl", run=RUN_ID, run_cap=args.run_cap)
    started = datetime.now(timezone.utc)
    try:
        key = _local_key(r.KEY_NAME)
    except Exception:
        print(json.dumps({"stopped": "key_unavailable"}))
        return 1
    provider = r.make_provider(key)
    scorer = nli_admission.make_scorer(cache=ROOT / ".local/nli-cache", python=ROOT / ".local/nli-venv/Scripts/python.exe")

    def progress(item):
        where = "dev" if item["case_id"] in new_dev else "held-out"
        print(json.dumps({"split": where, "path": item["path"], "reason": item["reason"], "calls_run": budget.used_run}), flush=True)

    items, stop = run_cases(new_dev + held, glossary, provider, budget, scorer, on_item=progress)
    finished = datetime.now(timezone.utc)
    by_id = {i["case_id"]: i for i in items}
    dev_items = [json.loads((OUT / "dev" / f"{c}.json").read_text(encoding="utf-8")) if (OUT / "dev" / f"{c}.json").exists() else by_id[c] for c in reused + new_dev]
    held_items = [by_id[c] for c in held]
    capacity, done = r.capacity_share(budget)
    record = {
        "decision": "D64", "run": RUN_ID, "frozen_at": "0426c02", "freeze_sha256": lw.digest(frozen["inputs"]),
        "started_utc": started.strftime("%Y-%m-%d %H:%M"), "finished_utc": finished.strftime("%Y-%m-%d %H:%M"),
        "run_calls": budget.used_run, "run_cap": budget.run_cap, "experiment_calls": budget.used_experiment, "experiment_cap": budget.experiment_cap,
        "capacity_failures": capacity, "finished_calls": done, "by_model": r.capacity_by_model(budget),
        "stopped": None if stop is None else {k: v for k, v in stop.items() if k != "at_epoch"},
        "dev": {**counts(dev_items), "reused_from_run5": len(reused), "cases": {i["case_id"]: {"path": i["path"], "content_attempts": i.get("content_attempts", 0)} for i in dev_items}},
        "held_out": counts(held_items),
    }
    record["held_out"]["sealed_file_sha256"] = seal.hashes(OUT, split_of(held[0]))  # names and hashes only, no content
    RECORD.write_text(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    new_dev_items = [by_id[c] for c in new_dev if by_id[c]["path"] != "not_attempted"]
    run_info = {"freeze_sha256": record["freeze_sha256"], "started_utc": record["started_utc"], "finished_utc": record["finished_utc"],
                "started_local": started.astimezone().strftime("%Y-%m-%d %H:%M"), "finished_local": finished.astimezone().strftime("%Y-%m-%d %H:%M"),
                "timezone": str(started.astimezone().tzinfo)}
    if stop:
        run_info["stopped"] = {**{k: v for k, v in stop.items() if k != "at_epoch"}, "at_utc": "", "at_local": ""}
    REPORT.write_text(r.review_markdown(new_dev_items, budget, run_info, calibrate=True), encoding="utf-8", newline="\n")
    print(json.dumps({k: record[k] for k in ("run_calls", "run_cap", "experiment_calls", "experiment_cap", "capacity_failures", "finished_calls", "stopped")}))
    print(json.dumps({"dev": {k: record["dev"][k] for k in ("cases", "accepted", "rejected", "not_attempted", "paths")},
                      "held_out": {k: record["held_out"][k] for k in ("cases", "accepted", "rejected", "not_attempted", "paths")}}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
