"""Offline B1 capture on DEV cases only (plan P2.2). Explicit owner-PC mode; never publishes; never opens the test split.

The key is read here (Windows USER variable, as evals/local_runner.py does) and never printed or stored. Every Gemini HTTP
request is counted first by the CallBudget ledger (`.local/p2-2/calls.jsonl`). Each item's complete result is saved under
`.local/p2-2/items/` so a resumed run repeats nothing. The review document lists, per case, the rules text beside the model text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable

from agents import call_budget as cb
from agents import llm_report_writer as lw
from agents import writer_input, writer_policy
from agents.model_transport import post_json
from evals import build_packets as bp

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "data" / "dataset"
WORK = ROOT / ".local" / "p2-2"
KEY_NAME = "PITCHCRAFT_GEMINI_API_KEY_LOCAL"
QUOTA = {"veteran": 3, "limited": 3, "opener": 2, "postseason": 2}  # the ten dev examples, in the manifest order
RUN_ID = "b1-dev-examples-1"
PAUSE_SECONDS = 5


def pick_cases(dataset=DATASET) -> list[str]:
    """Ten dev cases: the first of each stratum in the sealed split order, 3 + 3 + 2 + 2. Dev ids only."""

    taken = {k: 0 for k in QUOTA}
    chosen = []
    for case_id in bp.dev_case_ids(dataset):
        stratum = case_id.split("-")[0]
        if stratum in taken and taken[stratum] < QUOTA[stratum]:
            taken[stratum] += 1
            chosen.append(case_id)
    return chosen


def run_item(case_id: str, dataset, glossary, provider, budget, items_dir: Path, sleep=time.sleep) -> dict:
    path = items_dir / f"{case_id}.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("guide_sha256") == lw.guide_sha256() and saved.get("prompt_version") == lw.PROMPT_VERSION:
            return saved
    packet, findings = bp.load_dev_packet(dataset, case_id), bp.load_dev_findings(dataset, case_id)
    result = lw.write(findings, packet, glossary, provider=provider, budget=budget, item_id=case_id, sleep=sleep)
    item = {
        "case_id": case_id, "path": result.path, "reason": result.reason, "content_attempts": result.content_attempts,
        "failures": result.failures, "attempts": result.attempts, "report": result.report,
        "rules_report": lw.rules_report_for(packet),
        "guide_sha256": lw.guide_sha256(), "prompt_version": lw.PROMPT_VERSION,
    }
    if result.reason == "call_cap_reached":
        return item  # not final: a resumed run with room left tries this item again
    items_dir.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(item, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)
    return item


def report_text(report: dict) -> list[tuple[str, str]]:
    rows = [("Headline", report["headline"]), ("Short summary", "\n".join(f"- {x}" for x in report["short_summary"]))]
    for section in report["sections"]:
        body = section.get("body") or "\n".join(f"- {b}" for b in section.get("bullets", []))
        rows.append((section["title"], body))
    return rows


def length_of(report: dict) -> int:
    from agents import writer_checks

    return writer_checks.rules_length(report)


def review_markdown(items: list[dict], budget: cb.CallBudget) -> str:
    paths = {p: 0 for p in writer_policy.PATHS}
    for item in items:
        paths[item["path"]] += 1
    llm = len(items) - paths["rules"]
    out = [
        "# B1 dev examples: model text beside the rules text (owner gate)\n",
        f"Dev split only. Guide digest `{lw.guide_sha256()}`, prompt `{lw.PROMPT_VERSION}`. Nothing here is published; rules stay live.\n",
        f"Gemini HTTP calls: run {budget.used_run} of {budget.run_cap}, experiment {budget.used_experiment} of {budget.experiment_cap}.",
        f"Paths: {', '.join(f'{k} {v}' for k, v in paths.items())}. LLM coverage {llm}/{len(items)}; "
        f"not written by the primary model {len(items) - paths['primary']}/{len(items)} (a fallback or rules result is not a primary first-attempt success).\n",
    ]
    for item in items:
        out.append(f"\n## {item['case_id']}\n")
        out.append(f"- Path: **{item['path']}**" + (f" (reason: `{item['reason']}`)" if item["reason"] else "") + f"; content attempts: {item['content_attempts']}")
        for attempt in item["attempts"]:
            usage = attempt.get("usage") or {}
            out.append(f"- Content attempt {attempt['content_attempt']}: transport path `{attempt['path']}`, transport failures "
                       f"{[(a['model'], a['try'], a['code']) for a in attempt['transport']] or 'none'}, model `{attempt.get('model', '-')}`, "
                       f"checks {attempt.get('checks', 'not reached')}, tokens {usage or '-'}")
        rules = item["rules_report"]
        out.append(f"- Length: rules {length_of(rules)} characters; shown text {length_of(item['report'])} characters.\n")
        out.append("### Rules text (A)\n")
        for title, body in report_text(rules):
            out.append(f"**{title}**\n\n{body}\n")
        candidate_shown = item["path"] != "rules"
        out.append(f"### Model text (B1){'' if candidate_shown else ' (rejected; the last candidate, not published)'}\n")
        last = next((a for a in reversed(item["attempts"]) if a.get("candidate")), None)
        if candidate_shown:
            for title, body in report_text(item["report"]):
                out.append(f"**{title}**\n\n{body}\n")
        elif last is not None:
            from agents import writer_checks

            shown = writer_checks.to_report(last["candidate"], rules)
            out.append(f"Failed checks: {last['checks']}\n")
            for title, body in report_text(shown):
                out.append(f"**{title}**\n\n{body}\n")
        else:
            out.append("No model text: the call never produced a usable answer.\n")
    return "\n".join(out) + "\n"


def make_provider(key: str) -> Callable[[str, float, dict], Any]:
    def provider(model, timeout, body):
        return post_json("gemini", model, body, api_key=key, timeout=timeout, with_metadata=True)

    return provider


def main(argv=None) -> int:  # pragma: no cover - the network entry point
    parser = argparse.ArgumentParser(description="P2.2 offline B1 capture on dev cases")
    parser.add_argument("--owner-pc-offline", action="store_true", required=True)
    parser.add_argument("--out", default=str(ROOT / "docs" / "b1-dev-examples.md"))
    args = parser.parse_args(argv)
    from evals.local_runner import _local_key

    case_ids = pick_cases()
    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    budget = cb.CallBudget(WORK / "calls.jsonl", run=RUN_ID, run_cap=cb.run_cap_for(len(case_ids)))
    try:
        key = _local_key(KEY_NAME)
    except Exception:
        print(json.dumps({"stopped": "key_unavailable"}))
        return 1
    provider = make_provider(key)
    items = []
    for case_id in case_ids:
        fresh = not (WORK / "items" / f"{case_id}.json").exists()
        items.append(run_item(case_id, DATASET, glossary, provider, budget, WORK / "items"))
        print(json.dumps({"case": case_id, "path": items[-1]["path"], "reason": items[-1]["reason"], "calls_run": budget.used_run}), flush=True)
        if fresh:
            time.sleep(PAUSE_SECONDS)
    Path(args.out).write_text(review_markdown(items, budget), encoding="utf-8", newline="\n")
    print(json.dumps({"run_calls": budget.used_run, "run_cap": budget.run_cap, "experiment_calls": budget.used_experiment, "experiment_cap": budget.experiment_cap}))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
