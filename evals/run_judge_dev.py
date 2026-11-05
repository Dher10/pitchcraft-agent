"""Owner-PC runner for one Groq judge dev calibration pass (docs/plans/P2-planB-judge-freeze.md).

    python -m evals.run_judge_dev --pass 1

Dev sample only. The key is read from the USER variable by `evals.local_runner._local_key`. One pass makes one call per
batch (case group) at the frozen pacing, writes a record with counts, estimated against actual tokens and the Groq
rate headers, and prints aggregates only: no response text, no per-sentence label, no gate finding. The record file is
write-once per pass number.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from evals import judge_freeze as jf
from evals import labeling_sheet as ls

SPLIT = "dev"


def owner_labels(rows):
    """{item: label} for the rows the owner has labeled with a valid label; others are left out and counted by the caller."""

    return {i: v[0] for i, v in ls.clean_labels(rows).items() if v[0] is not None}


class PassAborted(RuntimeError):
    """The first batch could not be judged (for example the daily quota is spent): no record is written, the pass number stays free."""


def run_pass(call, batches, owner, sleep=None):
    """Judge every batch, then compare with the owner's labels. `call(body)` returns (status, rate_headers, body).
    Returns the record only: per-sentence verdicts are not kept, so the owner's labels cannot be reconstructed from it."""

    seen = []

    def plain(body):
        status, rate, value = call(body)
        seen.append({"status": status, **rate})
        if status != 200 or not isinstance(value, dict):
            raise RuntimeError("transport")
        return value

    verdicts, records = jf.judge_all(plain, batches[:1], sleep=sleep)
    if all(v == jf.MISSING for v in verdicts.values()):
        raise PassAborted("the first batch was not judged; nothing was recorded")
    if sleep is not None and batches[1:]:
        sleep(jf.PACING_SECONDS)                 # the pacing continues across the split
    more_verdicts, more_records = jf.judge_all(plain, batches[1:], sleep=sleep)
    verdicts, records = {**verdicts, **more_verdicts}, records + more_records
    scored = {i: owner[i] for i in owner if i in verdicts}
    agreement = jf.judge_agreement(scored, verdicts)
    estimated = sum(r["estimated_tokens"] for r in records)
    actual = sum(r["tokens"] for r in records)
    return {"prompt_version": jf.PROMPT_VERSION, "spec_digest": jf.spec_digest(), "calls": len(records),
            "attempts": sum(r["attempts"] for r in records), "sentences": len(verdicts), "labeled": len(scored),
            "agreement": agreement["percent_of_all"], "agreement_answered": agreement["percent_of_answered"],
            "kappa": agreement["kappa"], "missing": agreement["missing"], "unsure": sum(r["unsure"] for r in records), "confusion": agreement["confusion"],
            "error_vs_supported": agreement["error_vs_supported"],
            "tokens": {"estimated": estimated, "actual": actual, "largest_estimated": max((r["estimated_tokens"] for r in records), default=0)},
            "headers": seen, "batches": records}


def write_record(out, number, record):
    """Exclusive create: a pass record is written once, and no per-sentence verdict file exists."""

    path = Path(out) / f"judge_dev_pass{number}.json"
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    except FileExistsError:
        raise SystemExit(f"{path} exists; a pass is written once") from None


def groq_call(key):
    from agents import model_transport as mt

    def call(body):
        r = mt.post_json("groq", jf.JUDGE_MODEL, body, api_key=key, timeout=60, with_metadata=True)
        return r.status, r.rate, r.body

    return call


def main(argv=None):  # pragma: no cover - owner-PC entry point
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pass", dest="number", type=int, required=True, choices=range(1, jf.MAX_PASSES + 1))
    parser.add_argument("--out", type=Path, default=ls.OUT)
    args = parser.parse_args(argv)
    record_path = args.out / f"judge_dev_pass{args.number}.json"
    if record_path.exists():
        raise SystemExit(f"{record_path} exists; a pass is written once")
    from evals import local_runner

    batches = jf.inputs_from_files(args.out, SPLIT)
    owner = owner_labels(ls.read_csv(args.out / f"{SPLIT}_sheet.csv"))
    key = local_runner._local_key(local_runner.KEY_NAMES["groq"])
    record = run_pass(groq_call(key), batches, owner, sleep=time.sleep)
    record["pass"] = args.number
    summary = {k: record[k] for k in ("prompt_version", "calls", "attempts", "sentences", "labeled", "agreement", "agreement_answered", "kappa", "missing", "unsure", "confusion", "error_vs_supported", "tokens")}
    print(json.dumps(summary, indent=1, sort_keys=True), flush=True)     # printed first: a failed write must not lose a spent quota-day pass
    write_record(args.out, args.number, record)


if __name__ == "__main__":  # pragma: no cover
    main()
