"""Offline B1 capture on DEV cases only (plan P2.2). Explicit owner-PC mode; never publishes; never opens the test split.

The key is read here (Windows USER variable, as evals/local_runner.py does) and never printed or stored. Every Gemini HTTP
request is counted first by the CallBudget ledger (`.local/p2-2/calls.jsonl`). Each item's complete result is saved under
`.local/p2-2/items/` so a resumed run repeats nothing. The review document lists, per case, the rules text beside the model text.
"""
from __future__ import annotations

import argparse
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Callable

from agents import call_budget as cb
from agents import llm_report_writer as lw
from agents import writer_input, writer_policy, nli_admission, nli_cache, fact_renderer
from agents.model_transport import post_json
from evals import build_packets as bp

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals" / "data" / "dataset"
WORK = ROOT / ".local" / "p2-2"
KEY_NAME = "PITCHCRAFT_GEMINI_API_KEY_LOCAL"
QUOTA = {"veteran": 3, "limited": 3, "opener": 2, "postseason": 2}  # the ten dev examples, in the manifest order
RUN_ID = "b1-dev-examples-4"  # fresh capture; previous 105 calls remain in the same experiment ledger
ITEMS_DIR = "items-4"
STOP_MIN_CALLS = 9  # the early stop needs at least this many finished calls, so one early 429 does not end a run
DEFAULT_RUN_CAP = 30  # owner decision: no change to the 400-call experiment cap


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


def run_identity(packet, findings, glossary, nli_mode, nli=None):
    return lw.digest({"packet": packet, "findings": findings, "glossary": glossary,
                      "models": writer_policy.WRITER_MODELS, "prompt": lw.PROMPT_VERSION,
                      "body": lw.build_body(writer_input.build_writer_input(packet, findings, glossary), lw.writer_checks.rules_length(lw.rules_report_for(packet))),
                      "nli_mode": nli_mode, "nli_adapter": None if nli is None else getattr(nli, "identity", "custom-unversioned"),
                      "nli": nli_cache.identity(), "renderer": fact_renderer.renderer_identity(),
                      "code": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                               ("agents/writer_checks.py", "agents/llm_report_writer.py", "agents/writer_policy.py", "agents/nli_admission.py")}})


def run_item(case_id: str, dataset, glossary, provider, budget, items_dir: Path, sleep=None, nli=None, nli_mode="score_only") -> dict:
    path = items_dir / f"{case_id}.json"
    packet, findings = bp.load_dev_packet(dataset, case_id), bp.load_dev_findings(dataset, case_id)
    identity = run_identity(packet, findings, glossary, nli_mode, nli)
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved.get("run_identity") == identity:
            return saved
        raise ValueError("cached item identity differs")
    result = lw.write(findings, packet, glossary, provider=provider, budget=budget, item_id=case_id, sleep=sleep, nli=nli, nli_mode=nli_mode)
    item = {
        "case_id": case_id, "path": result.path, "reason": result.reason, "content_attempts": result.content_attempts,
        "failures": result.failures, "attempts": result.attempts, "report": result.report,
        "rules_report": lw.rules_report_for(packet),
        "style_findings": result.style_findings,
        "guide_sha256": lw.guide_sha256(), "prompt_version": lw.PROMPT_VERSION,
        "run_identity": identity, "nli_mode": nli_mode,
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


def writer_checks_is_gate(code: str) -> bool:
    from agents import writer_checks

    return writer_checks.is_gate(code)


def capacity_share(budget: cb.CallBudget) -> tuple[int, int]:
    """(503/429 answers, finished calls) of this run, from the ledger."""

    done = [r for r in budget.rows if r["kind"] == "finish" and r["run"] == budget.run]
    return sum(1 for r in done if r["code"] in ("http_503", "http_429")), len(done)


def should_stop(capacity: int, done: int) -> bool:
    """More than a third of the finished calls failed on capacity, after at least STOP_MIN_CALLS of them."""

    return done >= STOP_MIN_CALLS and capacity * 3 > done


def average_stop(cases: int, calls: int) -> bool:
    """D57: evaluate after the first five cases, using reserved calls (including failures)."""
    return cases >= 5 and calls > 3 * cases


def capacity_by_model(budget: cb.CallBudget) -> dict[str, dict[str, int]]:
    """Per model of this run: finished calls and capacity failures (503/429)."""

    model_of = {r["seq"]: r["model"] for r in budget.rows if r["kind"] == "reserve" and r["run"] == budget.run}
    out: dict[str, dict[str, int]] = {}
    for r in budget.rows:
        if r["kind"] == "finish" and r["run"] == budget.run:
            entry = out.setdefault(model_of.get(r["ticket"], "?"), {"calls": 0, "capacity": 0})
            entry["calls"] += 1
            entry["capacity"] += r["code"] in ("http_503", "http_429")
    return out


def run_all(case_ids, dataset, glossary, provider, budget, items_dir: Path, sleep=None, clock=time.time, on_item=None, nli=None, nli_mode="score_only") -> tuple[list[dict], dict | None]:
    """Every case in order. If more than a third of this run's finished calls failed on capacity (after STOP_MIN_CALLS calls), stop:
    the remaining cases are recorded as not_attempted and the partial results are kept. Returns (items, stop info or None)."""

    items: list[dict] = []
    stop = None
    for case_id in case_ids:
        if stop is not None and not (items_dir / f"{case_id}.json").exists():
            items.append({"case_id": case_id, "path": "not_attempted", "reason": stop["reason"], "content_attempts": 0, "attempts": [],
                          "report": None, "rules_report": lw.rules_report_for(bp.load_dev_packet(dataset, case_id)), "style_findings": [],
                          "failures": [], "guide_sha256": None, "prompt_version": None})
            continue
        items.append(run_item(case_id, dataset, glossary, provider, budget, items_dir, sleep=sleep, nli=nli, nli_mode=nli_mode))
        if on_item:
            on_item(items[-1])
        capacity, done = capacity_share(budget)
        attempted = {r["item"] for r in budget.rows if r["kind"] == "reserve" and r["run"] == budget.run}
        attempted.update(i["case_id"] for i in items if i["path"] != "not_attempted")
        reason = "capacity_stop" if should_stop(capacity, done) else "average_call_stop" if average_stop(len(attempted), budget.used_run) else None
        if reason and stop is None:
            last_attempted = next(c for c in reversed(case_ids) if c in attempted)
            stop = {"reason": reason, "cases": len(attempted), "after_case": last_attempted, "at_epoch": clock(), "capacity": capacity, "calls": budget.used_run, "by_model": capacity_by_model(budget)}
    return items, stop


def calibration_section(case_id="veteran-824027", dataset=DATASET) -> list[str]:
    """Calibration note only: the rules text of one dev case through the word-level checks (no citations)."""

    from agents import writer_checks

    packet = bp.load_dev_packet(dataset, case_id)
    doc = writer_input.build_writer_input(packet, bp.load_dev_findings(dataset, case_id), writer_input.load_glossary(dataset / "glossary.json"))
    rules = lw.rules_report_for(packet)
    text = " ".join([rules["headline"], *rules["short_summary"], *((s.get("body") or " ".join(s.get("bullets", []))) for s in rules["sections"])])
    found = writer_checks.lexical_failures(text, doc)
    lines = [f"\n## Calibration note: the rules text of {case_id} through the word-level checks\n",
             "Not a defect list. These are the words and shapes the word-level checks flag in the text the rules writer publishes today. Whether each would be a violation depends on citations (a comparison word is allowed when both values are quoted; a sentence-opening question word is a limit of the entity heuristic). The checks that need citations were not run.\n"]
    for check in sorted({f["check"] for f in found}):
        tokens = sorted({f["token"] for f in found if f["check"] == check})
        lines.append(f"- `{check}`: {', '.join(repr(t) for t in tokens)}")
    return lines + [""]


def _run_lines(budget: cb.CallBudget, run_info: dict | None) -> list[str]:
    capacity, done = capacity_share(budget)
    lines = [f"Capacity failures (503/429) in this run: {capacity} of {done} finished calls. By model: " + "; ".join(
        f"`{m}` {v['capacity']} of {v['calls']}" for m, v in sorted(capacity_by_model(budget).items())) + "."]
    if run_info and run_info.get("stopped"):
        stop = run_info["stopped"]
        if stop.get("reason") == "average_call_stop":
            lines.append(f"**The run stopped early** after case `{stop['after_case']}`: {stop['calls']} reserved calls / {stop['cases']} attempted cases exceeds 3. Partial results kept; remaining cases are `not_attempted`.")
        else:
            lines.append(f"**The run stopped early** after case `{stop['after_case']}` at {stop['at_local']} local ({stop['at_utc']} UTC): {stop['capacity']} of {stop['calls']} finished calls "
                     f"were capacity failures (more than a third). Failing model(s): " + ", ".join(f"`{m}` ({v['capacity']} of {v['calls']})" for m, v in sorted(stop['by_model'].items()) if v['capacity']) + ". The remaining cases are `not_attempted`.")
    if run_info:
        lines.append(f"Run started {run_info['started_local']} local ({run_info['started_utc']} UTC), finished {run_info['finished_local']} local.")
        if done and capacity * 3 > done:
            lines.append(f"More than a third of the calls failed on capacity; time of day of the run: {run_info['started_local']} to {run_info['finished_local']} local ({run_info['timezone']}).")
    return lines


def best_attempt(item: dict) -> tuple[int, dict] | None:
    """(number, attempt) of the model candidate with the fewest failed checks; a later one wins a tie."""

    ranked = [(len(a.get("checks") or []), -a["content_attempt"], a) for a in item["attempts"] if a.get("candidate")]
    if not ranked:
        return None
    best = min(ranked, key=lambda r: (r[0], r[1]))
    return best[2]["content_attempt"], best[2]


def review_markdown(items: list[dict], budget: cb.CallBudget, run_info: dict | None = None, calibrate: bool = False,
                    summary: str | None = None, notes: dict | None = None) -> str:
    paths = {p: 0 for p in (*writer_policy.PATHS, "not_attempted")}
    for item in items:
        paths[item["path"]] += 1
    llm = len(items) - paths["rules"] - paths["not_attempted"]
    accepted = sum(1 for i in items if i["path"] not in ("rules", "not_attempted"))
    out = [
        "# B1 dev examples: model text beside the rules text (owner gate)\n",
        f"Dev split only. Guide digest(s) recorded in this run: {', '.join('`' + g + '`' for g in sorted({i.get('guide_sha256') for i in items if i.get('guide_sha256')})) or 'none'}; "
        f"prompt version(s) recorded in this run: {', '.join('`' + v + '`' for v in sorted({i.get('prompt_version') for i in items if i.get('prompt_version')})) or 'none'}. "
        "Nothing here is published; rules stay live.\n",
        "S1 code detectors: S-1, S-2, S-4, S-5, S-7, S-8; S-3, S-6 and S-9 require judge/human assessment and are not evaluated here. NLI is score-only unless explicitly recorded as gate; no human-calibrated entailment claim.\n",
        f"Gemini HTTP calls: run {budget.used_run} of {budget.run_cap}, experiment {budget.used_experiment} of {budget.experiment_cap}.",
        *_run_lines(budget, run_info),
        f"Paths: {', '.join(f'{k} {v}' for k, v in paths.items())}. LLM coverage {llm}/{len(items)}; accepted {accepted}, rejected {paths['rules']}, not attempted {paths['not_attempted']}; "
        f"not written by the primary model {len(items) - paths['primary']}/{len(items)} (a fallback or rules result is not a primary first-attempt success).\n",
    ]
    if summary:
        out.append(summary)
    for item in items:
        out.append(f"\n## {item['case_id']}\n")
        stop_label = "calls-per-case stop" if item.get("reason") == "average_call_stop" else "capacity stop"
        verdict = {"rules": "REJECTED (the rules report is used)", "not_attempted": f"NOT ATTEMPTED ({stop_label})"}.get(item["path"], "ACCEPTED (model text; style findings below)")
        out.append(f"- Outcome: **{verdict}**")
        out.append(f"- Path: **{item['path']}**" + (f" (reason: `{item['reason']}`)" if item["reason"] else "") + f"; content attempts: {item['content_attempts']}")
        if item["path"] == "not_attempted":
            out.append("")
            continue
        for attempt in item["attempts"]:
            usage = attempt.get("usage") or {}
            out.append(f"- Content attempt {attempt['content_attempt']}: transport path `{attempt['path']}`, transport failures "
                       f"{[(a['model'], a['try'], a['code']) for a in attempt['transport']] or 'none'}, model `{attempt.get('model', '-')}`, "
                       f"gate checks {attempt.get('checks', 'not reached')}, style findings {sorted({f['check'] for f in attempt.get('style_findings', [])}) or 'none'}, tokens {usage or '-'}")
            for failure in attempt.get("check_detail", []):
                kind = "gate" if writer_checks_is_gate(failure["check"]) else "style"
                out.append(f"  - {kind} `{failure['check']}` token `{failure['token']}` in: {failure['sentence'] or '(whole report)'}")
            for entry in attempt.get("nli", []):
                out.append(f"  - NLI ({attempt.get('nli_mode', 'gate')}) score `{entry['score']}`, problem `{entry['problem']}`, paths `{entry.get('evidence_paths', [])}`: {entry['sentence']}")
            candidate = attempt.get("candidate")
            if candidate and "W17.structure" not in attempt.get("checks", []):
                for sentence in lw.writer_checks._all_sentences(candidate):
                    out.append(f"  - Sentence evidence `{sentence['evidence']}`: {sentence['text']}")
        rules = item["rules_report"]
        out.append(f"- Length: rules {length_of(rules)} characters; shown text {length_of(item['report'])} characters.\n")
        out.append("### Rules text (A)\n")
        for title, body in report_text(rules):
            out.append(f"**{title}**\n\n{body}\n")
        candidate_shown = item["path"] != "rules"
        best = best_attempt(item)
        shown_text = ""
        if candidate_shown:
            out.append("### Model text (B1): accepted\n")
            shown = item["report"]
            styles = item.get("style_findings", [])
            out.append("Style findings recorded for S1 (never a reason to reject): " + (", ".join(f"`{f['check']}` `{f['token']}`" for f in styles) or "none") + "\n")
        elif best is not None:
            from agents import writer_checks

            number, attempt = best
            out.append(f"### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt {number} of {item['content_attempts']}, "
                       f"model `{attempt.get('model', '-')}`, gate checks {attempt['checks']}, style findings {sorted({f['check'] for f in attempt.get('style_findings', [])}) or 'none'}"
                       + ("; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable"
                          if "W17.structure" in attempt["checks"] else "") + "\n")
            shown = writer_checks.to_report(attempt["candidate"], rules)
        else:
            shown = None
            out.append("### Model text (B1)\n\nNo model text: the call never produced a usable answer.\n")
        if item["path"] == "not_attempted":
            shown = None
        if shown is not None:
            for title, body in report_text(shown):
                out.append(f"**{title}**\n\n{body}\n")
                shown_text += "\n" + body + "\n" + title
        note = (notes or {}).get(item["case_id"])
        if note:
            missing = [q for q in note.get("quotes", []) if q not in shown_text]
            if missing:
                raise ValueError(f"readability note for {item['case_id']} quotes text that is not in the text shown: {missing}")
            out.append("### Readability for a casual fan\n\n" + note["text"] + "\n")
    return "\n".join(out + (calibration_section() if calibrate else [])) + "\n"


def make_provider(key: str) -> Callable[[str, float, dict], Any]:
    def provider(model, timeout, body):
        return post_json("gemini", model, body, api_key=key, timeout=timeout, with_metadata=True)

    return provider


def main(argv=None) -> int:  # pragma: no cover - the network entry point
    parser = argparse.ArgumentParser(description="P2.2 offline B1 capture on dev cases")
    parser.add_argument("--owner-pc-offline", action="store_true")
    parser.add_argument("--doc-only", action="store_true", help="rebuild the review document from the saved items; makes no request")
    parser.add_argument("--doc-inputs", default=str(ROOT / "docs" / "b1-run3-doc-inputs.json"))
    parser.add_argument("--out", default=str(ROOT / "docs" / "b1-dev-examples.md"))
    parser.add_argument("--run-cap", type=int, default=DEFAULT_RUN_CAP)
    args = parser.parse_args(argv)
    case_ids = pick_cases()
    run_info_file = WORK / "run-info-4.json"
    if args.doc_only:
        inputs = json.loads(Path(args.doc_inputs).read_text(encoding="utf-8"))
        budget = cb.CallBudget(WORK / "calls.jsonl", run=RUN_ID, run_cap=args.run_cap)
        items = [json.loads((WORK / ITEMS_DIR / f"{c}.json").read_text(encoding="utf-8")) if (WORK / ITEMS_DIR / f"{c}.json").exists()
                 else _not_attempted(c) for c in case_ids]
        run_info = inputs.get("run_info") or json.loads(run_info_file.read_text(encoding="utf-8"))
        text = review_markdown(items, budget, run_info, calibrate=True, summary=inputs["summary"], notes=inputs["notes"])
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print(json.dumps({"rebuilt": args.out, "items": len(items)}))
        return 0
    if not args.owner_pc_offline:
        parser.error("--owner-pc-offline is required to make requests")
    from evals import experiment_freeze as freeze
    try:
        frozen = freeze.verify_frozen(freeze.FREEZE_PATH, DATASET, case_ids)
    except freeze.FrozenInputsChanged:
        print(json.dumps({"stopped": "frozen_inputs_changed"}))
        return 1
    if args.run_cap > frozen["run_cap"]:
        print(json.dumps({"stopped": "run_cap_exceeds_freeze"}))
        return 1
    from evals.local_runner import _local_key

    glossary = writer_input.load_glossary(DATASET / "glossary.json")
    budget = cb.CallBudget(WORK / "calls.jsonl", run=RUN_ID, run_cap=args.run_cap)
    started = datetime.now(timezone.utc)
    try:
        key = _local_key(KEY_NAME)
    except Exception:
        print(json.dumps({"stopped": "key_unavailable"}))
        return 1
    provider = make_provider(key)

    def report(item):
        print(json.dumps({"case": item["case_id"], "path": item["path"], "reason": item["reason"], "calls_run": budget.used_run}), flush=True)

    scorer = nli_admission.make_scorer(cache=ROOT / ".local/nli-cache", python=ROOT / ".local/nli-venv/Scripts/python.exe")
    items, stop = run_all(case_ids, DATASET, glossary, provider, budget, WORK / ITEMS_DIR, on_item=report, nli=scorer)
    finished = datetime.now(timezone.utc)
    zone = started.astimezone().tzinfo
    run_info = {"freeze_sha256": lw.digest(frozen["inputs"]),
                "started_utc": started.strftime("%Y-%m-%d %H:%M"), "finished_utc": finished.strftime("%Y-%m-%d %H:%M"),
                "started_local": started.astimezone().strftime("%Y-%m-%d %H:%M"), "finished_local": finished.astimezone().strftime("%Y-%m-%d %H:%M"),
                "timezone": str(zone)}
    if stop:
        at = datetime.fromtimestamp(stop["at_epoch"], timezone.utc)
        run_info["stopped"] = {**{k: v for k, v in stop.items() if k != "at_epoch"}, "at_utc": at.strftime("%Y-%m-%d %H:%M"), "at_local": at.astimezone().strftime("%Y-%m-%d %H:%M")}
    run_info_file.write_text(json.dumps(run_info, indent=1), encoding="utf-8", newline="\n")
    Path(args.out).write_text(review_markdown(items, budget, run_info, calibrate=True), encoding="utf-8", newline="\n")
    print(json.dumps({"run_calls": budget.used_run, "run_cap": budget.run_cap, "experiment_calls": budget.used_experiment, "experiment_cap": budget.experiment_cap, "stopped": bool(stop)}))
    return 0


def _not_attempted(case_id: str) -> dict:
    return {"case_id": case_id, "path": "not_attempted", "reason": "capacity_stop", "content_attempts": 0, "attempts": [], "report": None,
            "rules_report": lw.rules_report_for(bp.load_dev_packet(DATASET, case_id)), "style_findings": [], "failures": [],
            "guide_sha256": None, "prompt_version": None}  # nothing was sent: no guide or prompt version was used


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
