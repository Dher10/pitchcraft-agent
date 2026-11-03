"""D60 offline dev replay. The suffix estimate is deliberately isolated here.

Strict resolution never invents a path. The estimate changes nonexistent paths
only: require an explicit subject and exactly one valid same-subject field
suffix. Dimension fields retain their parent (thresholds.control versus
limited.control); all other fields use their terminal field name. No values
or prose are repaired. This module imports no provider or generation runner.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

from agents import fact_table as ft, writer_input as wi, writer_checks as wc, nli_admission, fact_renderer, nli_cache, llm_report_writer as lw
from evals import build_packets as bp

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evals/data/dataset"
WORK = ROOT / ".local/p2-2"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _suffix(path):
    parts = path.split(".")
    return ".".join(parts[-2:]) if parts[-1] in ("control", "strikeout", "arsenal") else parts[-1]


def map_path(path, table, *, estimated=False, run=None):
    """Strict lineage, optionally the owner-approved REPLAY-ONLY estimate."""
    # Run 2 predates numeric twins; ERA/WHIP and lineup formatted rates have
    # declared, lossless numeric counterparts. Never convert innings notation.
    twins = {"era": "era_number", "whip": "whip_number", "ops_vs_hand": "ops_number", "k_rate_vs_hand": "k_rate_number", "bb_rate_vs_hand": "bb_rate_number"}
    if run == 2 and path in wi.evidence_index(table.doc) and path.rsplit(".", 1)[-1] in twins:
        twin = path.rsplit(".", 1)[0] + "." + twins[path.rsplit(".", 1)[-1]]
        if table.id_for_path(twin):
            return table.id_for_path(twin)
    fact_id = table.id_for_path(path)
    if fact_id:
        return fact_id
    # Run 2 used lists for findings; current projection joins the same list.
    if run == 2 and path.startswith("findings.") and path.rsplit(".", 1)[-1].isdigit():
        fact_id = table.id_for_path(path.rsplit(".", 1)[0])
        if fact_id:
            return fact_id
    if not estimated or path in wi.evidence_index(table.doc):
        return None
    try:
        subject, _ = ft.subject_field(table.doc, path)
    except (KeyError, IndexError, TypeError):
        return None
    if subject == "game":  # unqualified season_summary.* is not an identified subject
        return None
    suffix = _suffix(path)
    matches = [p for p in table.by_path if ft.subject_field(table.doc, p)[0] == subject and (p == suffix or p.endswith("." + suffix))]
    # Uniqueness is by VALID PATH, not equal values or coalesced fact IDs.
    return table.id_for_path(matches[0]) if len(matches) == 1 else None


def migrate(candidate, table, *, run, estimated):
    result = deepcopy(candidate)
    mappings, unmappable = [], []
    # Preserve malformed output shape; do not repair it into a valid report.
    if not wc._structure_ok(candidate):
        return None, mappings, [{"reason": "original_structure"}]
    for index, sentence in enumerate(wc._all_sentences(result)):
        ids = []
        if not sentence["evidence"]:
            missing = {"sentence_index": index, "old_path": None, "old_value": None, "fact_id": None,
                       "source_bindings": [], "reason": "missing_citation", "supplied_value_differs": False}
            mappings.append(missing)
            unmappable.append(missing)
        for evidence in sentence["evidence"]:
            path = evidence["path"]
            fact_id = map_path(path, table, estimated=estimated, run=run)
            actual = wi.evidence_index(table.doc).get(path)
            mapping = {"sentence_index": index, "old_path": path, "old_value": evidence["value"], "fact_id": fact_id,
                       "source_bindings": table.bindings.get(fact_id, []),
                       "reason": "run2_numeric_twin" if table.id_for_path(path) and fact_id != table.id_for_path(path) else "exact" if table.id_for_path(path) else "run2_list_join" if run == 2 and path.startswith("findings.") and path.rsplit(".",1)[-1].isdigit() and fact_id else "unique_suffix_estimate" if fact_id else "unmappable",
                       "supplied_value_differs": path in wi.evidence_index(table.doc) and not wc._same_value(evidence["value"], actual)}
            mappings.append(mapping)
            if fact_id is None:
                unmappable.append(mapping)
            elif fact_id not in ids:
                ids.append(fact_id)
        sentence["evidence"] = ids
    return result, mappings, unmappable


def recheck(candidate, doc, rules_len, *, run, estimated, scorer=None):
    table = ft.build_fact_table(doc)
    migrated, mappings, unmappable = migrate(candidate, table, run=run, estimated=estimated)
    if migrated is None:
        detail = [{"check": "W17.structure", "sentence": None, "token": None}]
        resolved = None
    else:
        resolved, detail = ft.resolve_candidate(migrated, doc)
        if resolved is not None:
            detail += wc.check_report_detailed(resolved, doc, rules_len)
        if unmappable:
            detail += [{"check": "REPLAY.unmappable", "sentence": m["sentence_index"], "token": m["old_path"]} for m in unmappable]
    gates, styles = wc.split_failures(detail)
    nli = []
    if scorer is not None and resolved is not None:
        _, nli = scorer(resolved, doc)
    return {"accepted": not gates, "mapping_complete": not unmappable, "unmappable": unmappable,
            "mappings": mappings, "gate_findings": gates, "style_findings": styles, "nli": nli,
            "fact_table_identity": table.identity, "candidate_fact_ids": migrated}


def replay(*, scorer=None):
    allowed = set(bp.dev_case_ids(DATASET))
    glossary = wi.load_glossary(DATASET / "glossary.json")
    sources = [WORK / "calls.jsonl", *(p for run in (2,3,4) for p in sorted((WORK / f"items-{run}").glob("*.json")))]
    before = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    rows, transport = [], []
    for run in (2,3,4):
        for path in sorted((WORK / f"items-{run}").glob("*.json")):
            if path.stem not in allowed:
                raise ValueError("non-dev capture")
            packet, findings = bp.load_dev_packet(DATASET, path.stem), bp.load_dev_findings(DATASET, path.stem)
            doc = wi.build_writer_input(packet, findings, glossary)
            saved = json.loads(path.read_text(encoding="utf-8"))
            for attempt in saved["attempts"]:
                candidate = attempt.get("candidate")
                identity = {"run": run, "case": path.stem, "attempt": attempt["content_attempt"]}
                if candidate is None:
                    transport.append(identity)
                    continue
                row = {**identity, "model": attempt.get("model"), "saved_prompt": saved.get("prompt_version"),
                       "saved_guide": saved.get("guide_sha256"), "source_sha256": sha(path), "original_candidate": candidate}
                for mode in ("strict", "estimated"):
                    row[mode] = recheck(candidate, doc, wc.rules_length(saved["rules_report"]), run=run, estimated=mode == "estimated", scorer=scorer)
                rows.append(row)
    after = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    if before != after:
        raise RuntimeError("historical sources changed")
    return {"estimate_label": "estimate of fact-ID behaviour; replay-only unique subject/field suffix normalization",
            "instrument": {"fact_table_version": ft.VERSION, "renderer": fact_renderer.renderer_identity(), "prompt": lw.PROMPT_VERSION,
                           "guide_sha256": lw.guide_sha256(), "nli": nli_cache.identity(),
                           "prompt_sha256": lw.digest({"version": lw.PROMPT_VERSION, "lexicon": lw.LEX, "schema": lw.SCHEMA,
                                                        "guide": lw.guide_text(), "max_output_tokens": lw.MAX_OUTPUT_TOKENS}),
                           "sources": {p: sha(ROOT / p) for p in ("agents/fact_table.py", "agents/writer_checks.py", "agents/fact_renderer.py", "agents/nli_admission.py", "evals/replay_writer.py")}},
            "sources_sha256": before, "sources_unchanged": True, "gemini_calls": 0, "experiment_calls": 127,
            "candidates": rows, "transport_only": transport,
            "totals": {mode: {"accepted": sum(r[mode]["accepted"] for r in rows), "rejected": sum(not r[mode]["accepted"] for r in rows),
                              "structure_rejected": sum(r[mode]["candidate_fact_ids"] is None for r in rows),
                              "unmappable_citations": sum(sum(m.get("old_path") is not None for m in r[mode]["unmappable"]) for r in rows),
                              "missing_citation_sentences": sum(sum(m["reason"] == "missing_citation" for m in r[mode]["unmappable"]) for r in rows)} for mode in ("strict", "estimated")}}


def rejection_counts(rows, mode, *, mapped_only=False):
    """Recorded non-mapping findings, with one affected-candidate count per ID.

    The mapped subset excludes findings on text whose old citations remain
    unmappable: those number/evidence failures can be mapping artefacts.
    Report-level checks and original structure failures remain counted.
    """
    counts = {}
    for row in rows:
        result = row[mode]
        bad_indexes = {m["sentence_index"] for m in result["unmappable"] if "sentence_index" in m}
        bad_texts = {s["text"] for i, s in enumerate(wc._all_sentences(row["original_candidate"])) if i in bad_indexes} if bad_indexes else set()
        seen = set()
        for finding in result["gate_findings"]:
            code = finding["check"]
            if code == "REPLAY.unmappable" or (mapped_only and finding["sentence"] in bad_texts):
                continue
            entry = counts.setdefault(code, {"check": code, "findings": 0, "candidates": 0})
            entry["findings"] += 1
            if code not in seen:
                entry["candidates"] += 1
                seen.add(code)
    return [counts[code] for code in sorted(counts)]


def write_report(record, path):
    lines = ["# Offline writer instrument replay", "", record["estimate_label"], "",
             "Zero Gemini calls. All original candidate text and capture/ledger hashes preserved. NLI scores are diagnostic.", "",
             "| Run | Case | Attempt | Strict accepted (0/1) | Estimated accepted (0/1) | Strict reasons | Estimated reasons |", "|---|---|---:|---:|---:|---|---|"]
    for r in record["candidates"]:
        reasons = lambda mode: ", ".join(sorted({f["check"] for f in r[mode]["gate_findings"]})) or "accepted"
        lines.append(f"| {r['run']} | {r['case']} | {r['attempt']} | {int(r['strict']['accepted'])} | {int(r['estimated']['accepted'])} | {reasons('strict')} | {reasons('estimated')} |")
    lines += ["", "Totals: " + json.dumps(record["totals"], sort_keys=True), "",
              "Every candidate's unchanged text, per-sentence gates, S1 findings, NLI scores, old citations, resolved bindings and unmappable reasons are in [the replay record](../evals/data/writer/instrument-replay.json).",
              "", "Strict leaves nonexistent/ambiguous paths rejected. The estimate normalizes a nonexistent path only when exactly one valid path ends in the same field suffix for the explicit same subject. Dimension fields keep their parent (thresholds.control differs from limited.control); other fields use the terminal name. Equal values never resolve ambiguity. The experiment and production harness do not import this tool.", "",
              "Declared run-2 lineage maps finding-list items to their joined finding and formatted ERA/WHIP/lineup rates to numeric twins. It never converts innings notation. Valid paths resolve to actual code-owned values; supplied-value discrepancies are recorded, never copied into facts. No prose is changed. The five original structure rejects are counted separately from unmappable citation occurrences.", "",
              "Empty original citation lists are explicitly unmappable in both modes (missing_citation). Missing-citation sentences are counted separately from nonexistent/ambiguous path occurrences and are excluded from the fully-mapped-text subset.", "",
              "Real-error controls still fail in BOTH modes: run 4 postseason-849842 attempt 2 retains W1.number for 10.4% BB% versus the actual 10.6%; run 4 limited-825104 attempt 1 retains W1.authority for unverified official ratings. The cause alone has a separate fully evidenced must-pass regression; the original official sentence is never accepted.", "",
              "NLI score coverage (score-only; no threshold or calibration claim):", ""]
    for mode in ("strict", "estimated"):
        scores = [n for r in record["candidates"] for n in r[mode]["nli"]]
        lines.append(f"- {mode}: {sum(n['score'] is not None for n in scores)} scored, {sum(n['problem'] == 'not_applicable' for n in scores)} Watch/not applicable, {sum(n['problem'] == 'unrenderable' for n in scores)} unrenderable, {sum(n['problem'] == 'unavailable' for n in scores)} unavailable.")
    lines += ["", "There are 34 candidates in 18 captures / 35 attempt records. The extra run-3 attempt is transport-only. All five malformed candidates stay rejected. Run-2 prompt metadata is p2.2-1; saved metadata takes precedence over its old report header. Experiment calls remain 127/400; this replay spends 0 calls, and no dev pass or forty-case B1 was started.", ""]
    lines += ["## Rejection reasons excluding unmappable paths", "",
              "Counts below exclude REPLAY.unmappable and cover all 34 candidates. Findings are distinct recorded gate findings; a candidate can contribute more than one. The last column additionally excludes findings on sentences with any missing citation or remaining unmappable path, to avoid treating mapping-induced number/evidence failures as independent factual errors. Report-level checks and the five original structure failures remain. S1 and NLI are diagnostics, not rejection reasons.", "",
              "| Check ID | Strict findings | Strict candidates | Estimated findings | Estimated candidates | Estimated findings on fully mapped text |",
              "|---|---:|---:|---:|---:|---:|"]
    groups = [{v["check"]: v for v in rejection_counts(record["candidates"], mode, mapped_only=clean)} for mode, clean in (("strict", False), ("estimated", False), ("estimated", True))]
    for code in sorted(set().union(*(set(g) for g in groups))):
        a,b,c = (g.get(code, {"findings": 0, "candidates": 0}) for g in groups)
        lines.append(f"| {code} | {a['findings']} | {a['candidates']} | {b['findings']} | {b['candidates']} | {c['findings']} |")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    memo = {}

    def cached_scores(cache, pairs, **kwargs):
        missing = list(dict.fromkeys(pair for pair in pairs if pair not in memo))
        if missing:
            values = nli_cache.scores(cache, missing, **kwargs)
            if values is not None and len(values) == len(missing):
                memo.update(zip(missing, values))
        return [memo.get(pair) for pair in pairs] if all(pair in memo for pair in pairs) else None

    scorer = nli_admission.make_scorer(cache=ROOT / ".local/nli-cache", python=ROOT / ".local/nli-venv/Scripts/python.exe", scorer=cached_scores)
    record = replay(scorer=scorer)
    (ROOT / "evals/data/writer/instrument-replay.json").write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    write_report(record, ROOT / "docs/writer-instrument-replay.md")
    print(json.dumps(record["totals"], sort_keys=True))
