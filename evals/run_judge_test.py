"""Owner-PC runner for the frozen judge on the TEST sample (docs/plans/P2-planB-judge-freeze.md, pre-freeze test scope).

    python -m evals.run_judge_test

Needs a verified, committed `judge-freeze.json`; judges the test batches (one case group per call, frozen spec, 60 s
pacing) and keeps a resumable state file under `.local/p2-2/labeling/`. A quota stop (two consecutive failed batches)
pauses the run; the next invocation continues after the last completed batch, never from the start. The runner never
reads the owner's test labels and never prints a verdict, a sentence or a gate finding: it prints counts only.
The state holds the judge's labels per sentence id (needed for the metrics step), the call/token counts, no text.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from evals import judge_freeze as jf
from evals import labeling_sheet as ls

SPLIT = "test"
ABORT_AFTER = 2                    # consecutive failed batches (every sentence missing after the declared retry) that pause the run
STATE_NAME = "judge_test_state.json"


def new_state(version, total_batches):
    return {"version": version, "total_batches": total_batches, "verdicts": {}, "done": [], "calls": 0, "attempts": 0,
            "tokens": 0, "unsure": 0, "failed_attempts_batches": 0, "headers": []}


def load_state(path, version, total_batches):
    path = Path(path)
    if not path.exists():
        return new_state(version, total_batches)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("version") != version or state.get("total_batches") != total_batches:
        raise SystemExit(f"{path} belongs to another judge version or batch set; refusing to resume")
    return state


def save_state(path, state):
    """Atomic replace, so a crash never leaves a half-written state."""

    path = Path(path)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def run(call, batches, state, save, sleep=None):
    """Judge every batch not yet done, in order. `call(body)` returns (status, rate_headers, body). A completed batch (at least
    one verdict that is not missing; judge_batch makes a batch all-valid or all-missing) is recorded in `state` and never
    called again. ABORT_AFTER consecutive failed batches pause the run. Returns counts only."""

    version = state["version"]
    seen, streak, failed, waited, tries = [], 0, 0, False, []

    def plain(body):
        if tries and sleep is not None:
            sleep(jf.PACING_SECONDS)             # the declared retry of one batch is paced like any other call
        tries.append(1)
        status, rate, value = call(body)
        seen.append({"status": status, **rate})
        if status != 200 or not isinstance(value, dict):
            raise RuntimeError("transport")
        return value

    status = "complete"
    for batch in batches:
        ids = [i["id"] for i in batch["items"]]
        body = jf.build_request(batch["fact_table"], batch["glossary"], batch["items"], version)
        digest = jf.request_digest(body)
        if digest in state["done"]:
            continue
        if sleep is not None and waited:
            sleep(jf.PACING_SECONDS)
        waited = True
        tries.clear()
        out = jf.judge_batch(plain, body, ids, version)
        state["calls"] += 1
        state["attempts"] += out["attempts"]
        state["tokens"] += out["tokens"]
        if all(v == jf.MISSING for v in out["verdicts"].values()):
            failed += 1
            streak += 1
            state["failed_attempts_batches"] += 1
            save(state)
            if streak >= ABORT_AFTER:
                status = "paused"
                break
            status = "incomplete"
            continue
        streak = 0
        state["verdicts"].update(out["verdicts"])
        state["done"].append(digest)
        state["unsure"] += out["unsure"]
        state["headers"] += seen
        seen.clear()
        save(state)
    if status == "complete" and len(state["done"]) < len(batches):
        status = "incomplete"
    result = {"status": status, "batches_done": len(state["done"]), "batches_total": len(batches), "failed_batches": failed,
              "calls": state["calls"], "attempts": state["attempts"], "tokens": state["tokens"], "unsure": state["unsure"],
              "sentences_judged": len(state["verdicts"])}
    if status == "paused":
        result["reason"] = "two_consecutive_failed_batches"
    return result


def require_freeze(path, committed=jf.is_committed, verify=jf.verify_freeze):
    """The frozen judge: the file verifies against the code and is committed. Returns its prompt version."""

    try:
        record = verify(path)
    except jf.JudgeFrozenChanged as error:
        raise SystemExit(f"REFUSED: {error}") from None
    if not committed(path):
        raise SystemExit("REFUSED: judge-freeze.json is not committed and unmodified")
    return record["spec"]["prompt_version"]


def main(argv=None):  # pragma: no cover - owner-PC entry point
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=ls.OUT)
    args = parser.parse_args(argv)
    version = require_freeze(jf.FREEZE_PATH)
    from evals import local_runner
    from evals.run_judge_dev import groq_call

    batches = jf.inputs_from_files(args.out, SPLIT, version)
    state_path = args.out / STATE_NAME
    state = load_state(state_path, version, len(batches))
    key = local_runner._local_key(local_runner.KEY_NAMES["groq"])
    result = run(groq_call(key), batches, state, lambda s: save_state(state_path, s), sleep=time.sleep)
    print(json.dumps(result, indent=1, sort_keys=True), flush=True)


if __name__ == "__main__":  # pragma: no cover
    main()
