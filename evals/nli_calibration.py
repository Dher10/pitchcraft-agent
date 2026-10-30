"""PROVISIONAL calibration of the local NLI on DEV data only (plan P2.3; docs/SECURITY.md "Calibrate threshold on dev human
entailment labels with wrong-subject, quantity, causal and unsupported semantic negatives").

What exists today, and what does not:
- positives: the hand-written positive control (labels by construction) and the rules writer's own sentences, whose evidence is
  found by matching the values and labels they state to the case's cited-able paths (true by construction of the catalog);
- negatives: deterministic perturbations of those positives (wrong quantity, wrong subject, flipped direction or label, shifted
  scope, an unsupported added claim, an added cause);
- NO human labels, and no accepted B1 model output yet. A threshold from this data is evidence about the NLI, not an admission:
  the artifact says `labels: synthetic` and `admission_allowed: false`, and `agents.nli_admission.calibration_ok` rejects it.

It never opens the test split.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import zlib

from agents import fact_renderer, nli_cache, writer_input
from evals import build_packets as bp

SWAPS = (("left-handed", "right-handed"), (" up ", " down "), ("above-average", "below-average"), ("solid", "poor"), ("average", "weak"))
UNSUPPORTED = " He also leads the league in strikeouts."
CAUSE = " This is because he trusts his fastball."
MAX_NEGATIVES_PER_POSITIVE = 2


def auto_paths(doc: dict, text: str) -> list[str]:
    """Cite-able paths whose value the sentence states: numbers and label or pitch strings, matched in the text."""

    index = writer_input.evidence_index(doc)
    lowered = text.lower()
    numbers = set(re.findall(r"(?<![\w.])\d+(?:\.\d+)?|(?<![\w])\.\d+", text))
    found: list[str] = []
    for path, value in index.items():
        if path.startswith(("aliases.", "glossary.")) or path.endswith((".through", ".name", ".team", ".abbreviation")):
            continue
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float)):
            token = ("%g" % value) if isinstance(value, float) else str(value)
            if any(token == n.lstrip("0") or token == n or ("%g" % abs(float(n))) == ("%g" % abs(value)) for n in numbers):
                found.append(path)
        elif isinstance(value, str) and len(value) >= 4 and value.lower() in lowered and not path.endswith(".label"):
            found.append(path)
    return [p for p in found if fact_renderer.render_fact(doc, p) is not None]


def perturbations(text: str, doc: dict) -> list[tuple[str, str]]:
    """Deterministic (kind, wrong sentence) pairs derived from a true sentence."""

    out: list[tuple[str, str]] = []
    numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?", text)
    if numbers:
        n = numbers[0]
        wrong = str(int(n) + 7) if n.isdigit() else f"{float(n) + 1.7:.{len(n.split('.')[1])}f}"
        out.append(("quantity", text.replace(n, wrong, 1)))
    names = [doc["starters"][s]["name"] for s in writer_input.SLOTS] + [doc["teams"][s]["name"] for s in writer_input.SIDES]
    for a, b in ((names[0], names[1]), (names[2], names[3])):
        if a in text and b not in text:
            out.append(("subject", text.replace(a, b)))
        elif b in text and a not in text:
            out.append(("subject", text.replace(b, a)))
    for a, b in SWAPS:
        if a in text:
            out.append(("flip", text.replace(a, b, 1)))
            break
    scope = re.search(r"through [A-Z][a-z]{2} \d{1,2}", text)
    if scope:
        out.append(("scope", text.replace(scope.group(0), "through Jul 31", 1)))
    out.append(("unsupported", text.rstrip() + UNSUPPORTED))
    out.append(("cause", text.rstrip() + CAUSE))
    return [(k, t) for k, t in out if t != text and len(t) <= 300]


def control_positives(dataset: Path, control_path: Path) -> list[dict]:
    data = json.loads(control_path.read_text(encoding="utf-8"))
    case = data["case_id"]
    doc = writer_input.build_writer_input(bp.load_dev_packet(dataset, case), bp.load_dev_findings(dataset, case), writer_input.load_glossary(dataset / "glossary.json"))
    raw = data["candidate"]
    sentences = [raw["headline"], *raw["summary_lines"], *(s for key in ("summary", "away_vs_home", "home_vs_away", "arsenal", "confidence") for s in raw["sections"][key])]
    out = []
    for s in sentences:
        premise, problem = fact_renderer.premise_for(doc, s["paths"])
        if problem is None and not s["text"].startswith("Watch"):
            out.append({"case": case, "source": "positive_control", "text": s["text"], "premise": premise, "doc": doc})
    return out


def rules_positives(dataset: Path, case_ids: list[str]) -> list[dict]:
    from agents import llm_report_writer as lw

    glossary = writer_input.load_glossary(dataset / "glossary.json")
    out = []
    for case in case_ids:
        packet, findings = bp.load_dev_packet(dataset, case), bp.load_dev_findings(dataset, case)
        doc = writer_input.build_writer_input(packet, findings, glossary)
        report = lw.rules_report_for(packet)
        texts = [report["headline"], *report["short_summary"]]
        for section in report["sections"]:
            texts += re.split(r"(?<=[.;])\s+(?=[A-Z])", section["body"]) if section.get("body") else []
        for text in dict.fromkeys(t.strip() for t in texts):
            if text.startswith(("Can ", "Which ")) or not 20 <= len(text) <= 300:
                continue
            paths = auto_paths(doc, text)
            premise, problem = fact_renderer.premise_for(doc, paths) if paths else (None, "unrenderable")
            if problem is None:
                out.append({"case": case, "source": "rules_writer", "text": text, "premise": premise, "doc": doc})
    return out


def build_dataset(dataset: Path, control_path: Path, case_ids: list[str]) -> list[dict]:
    """Labelled pairs: label 1 = entailed (by construction), 0 = a deterministic perturbation. DEV cases only."""

    dev = set(bp.dev_case_ids(dataset))
    if not set(case_ids) <= dev:
        raise ValueError("calibration uses dev cases only")
    pairs = []
    for positive in [*control_positives(dataset, control_path), *rules_positives(dataset, case_ids)]:
        pairs.append({"case": positive["case"], "source": positive["source"], "kind": "positive", "label": 1, "premise": positive["premise"], "text": positive["text"]})
        options = perturbations(positive["text"], positive["doc"])
        start = zlib.crc32(positive["text"].encode("utf-8"))  # deterministic rotation, so every kind of negative is represented
        chosen = [options[(start + i) % len(options)] for i in range(min(MAX_NEGATIVES_PER_POSITIVE, len(options)))]
        for kind, wrong in chosen:
            pairs.append({"case": positive["case"], "source": positive["source"], "kind": kind, "label": 0, "premise": positive["premise"], "text": wrong})
    return pairs


def score_pairs(pairs: list[dict], cache, python, scorer=None, batch=32) -> list[dict]:
    scorer = scorer or nli_cache.scores
    for start in range(0, len(pairs), batch):
        chunk = pairs[start:start + batch]
        values = scorer(cache, [(p["premise"], p["text"]) for p in chunk], python=python, timeout=300)
        for pair, value in zip(chunk, values if values and len(values) == len(chunk) else [None] * len(chunk)):
            pair["score"] = value
    return pairs


def summarize(pairs: list[dict], thresholds=(0.5, 0.8, 0.9, 0.95, 0.99)) -> dict:
    scored = [p for p in pairs if p.get("score") is not None]
    pos, neg = [p["score"] for p in scored if p["label"] == 1], [p["score"] for p in scored if p["label"] == 0]
    table = []
    for t in thresholds:
        tpr = sum(s >= t for s in pos) / len(pos) if pos else None
        tnr = sum(s < t for s in neg) / len(neg) if neg else None
        table.append({"threshold": t, "tpr": tpr, "tnr": tnr})
    recall_by_source = {src: {str(t): round(sum(p["score"] >= t for p in scored if p["label"] == 1 and p["source"] == src) / max(1, sum(1 for p in scored if p["label"] == 1 and p["source"] == src)), 3)
                              for t in thresholds} for src in sorted({p["source"] for p in scored if p["label"] == 1})}
    by_kind = {}
    for kind in sorted({p["kind"] for p in scored if p["label"] == 0}):
        values = [p["score"] for p in scored if p["kind"] == kind]
        by_kind[kind] = {"n": len(values), "wrongly_entailed_at_0.9": sum(v >= 0.9 for v in values)}
    return {"pairs": len(pairs), "scored": len(scored), "positives": len(pos), "negatives": len(neg), "by_kind_of_negative": by_kind,
            "positives_by_source": dict(Counter(p["source"] for p in scored if p["label"] == 1)), "recall_by_source": recall_by_source, "table": table}


def artifact(summary: dict) -> dict:
    return {
        "labels": "synthetic", "human_labels": 0, "admission_allowed": False,
        "identity": nli_cache.identity(), "renderer": fact_renderer.renderer_identity(), "model": nli_cache.MANIFEST["repository"],
        "revision": nli_cache.MANIFEST["revision"], "threshold": None, "summary": summary,
        "missing": [
            "no human entailment labels (owner labeling is Nov 4-6)",
            "no accepted B1 model output yet; no sentence written by a model has a human label",
            "negatives are deterministic perturbations, not the errors a model actually makes",
            "the rules writer's sentences are true by construction and phrased in catalog wording, not in model prose",
            "no threshold is proposed: a threshold needs human labels bound to this identity",
        ],
    }


def main(argv=None) -> int:  # pragma: no cover - runs the real model
    parser = argparse.ArgumentParser(description="provisional NLI calibration on dev data")
    parser.add_argument("--cache", default=".local/nli-cache")
    parser.add_argument("--python", default=".local/nli-venv/Scripts/python.exe")
    parser.add_argument("--out", default="evals/data/writer/nli_calibration_provisional.json")
    parser.add_argument("--pairs-out", default=".local/nli-calibration-pairs.jsonl")
    parser.add_argument("--from-pairs", action="store_true", help="recompute the artifact from the saved scored pairs; runs no model")
    parser.add_argument("--label-pool", action="store_true", help="score the real dev model sentences of runs 2 and 3 and write the owner's labeling pool; changes no artifact")
    args = parser.parse_args(argv)
    dataset = Path("evals/data/dataset")
    if args.label_pool:
        pool = label_pool(dataset, [Path(".local/p2-2/items-2"), Path(".local/p2-2/items-3")])
        score_pairs(pool, args.cache, args.python)
        out = Path(".local/nli-label-pool-dev.jsonl")
        out.write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in pool) + "\n", encoding="utf-8")
        scored = [p["score"] for p in pool if p["score"] is not None]
        print(json.dumps({"sentences": len(pool), "scored": len(scored), **{f"share_at_least_{t}": round(sum(v >= t for v in scored) / max(1, len(scored)), 3) for t in (0.5, 0.9)}}))
        return 0
    if args.from_pairs:
        pairs = [json.loads(line) for line in Path(args.pairs_out).read_text(encoding="utf-8").splitlines() if line]
    else:
        pairs = build_dataset(dataset, Path("evals/data/writer/positive_control.json"), bp.dev_case_ids(dataset))
        score_pairs(pairs, args.cache, args.python)
    Path(args.pairs_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.pairs_out).write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in pairs) + "\n", encoding="utf-8")
    Path(args.out).write_text(json.dumps(artifact(summarize(pairs)), ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(summarize(pairs), indent=1))
    return 0



def label_pool(dataset: Path, items_dirs: list[Path], cases: list[str] | None = None) -> list[dict]:
    """Unlabelled real model sentences (dev only) with their rendered premise, for the owner's entailment labeling.

    Only sentences whose evidence paths all exist and render are included; each entry has `owner_label: None`."""

    dev = set(bp.dev_case_ids(dataset))
    glossary = writer_input.load_glossary(dataset / "glossary.json")
    docs: dict[str, dict] = {}
    pool = []
    for directory in items_dirs:
        for path in sorted(Path(directory).glob("*.json")):
            item = json.loads(path.read_text(encoding="utf-8"))
            case = item["case_id"]
            if case not in dev or (cases is not None and case not in cases):
                continue
            if case not in docs:
                docs[case] = writer_input.build_writer_input(bp.load_dev_packet(dataset, case), bp.load_dev_findings(dataset, case), glossary)
            doc = docs[case]
            index = writer_input.evidence_index(doc)
            for attempt in item["attempts"]:
                candidate = attempt.get("candidate")
                if not isinstance(candidate, dict):
                    continue
                try:
                    sentences = [candidate["headline"], *candidate["summary_lines"], *(s for k, v in candidate["sections"].items() if k != "watch" for s in v)]
                    for sentence in sentences:
                        paths = [e["path"] for e in sentence["evidence"]]
                        if not paths or any(p not in index for p in paths) or sentence["text"].startswith("Watch") or len(sentence["text"]) > 300:
                            continue
                        premise, problem = fact_renderer.premise_for(doc, paths)
                        if problem is None:
                            pool.append({"case": case, "run": Path(directory).name, "attempt": attempt["content_attempt"], "model": attempt.get("model"),
                                         "text": sentence["text"], "paths": paths, "premise": premise, "label": None, "kind": "model_sentence", "source": "model"})
                except (KeyError, TypeError):
                    continue
    return pool


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
