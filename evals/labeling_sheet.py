"""Plan B labeling sheets (docs/plans/P2-planB-labeling.md, approved version 1).

Draws the stratified sentence sample from the B1 outputs, writes blind sheets for the owner, keeps the answer key
(stratum, gate findings, NLI score, inclusion probability) in a separate manifest, builds the U1 blind pair sheet and
computes the metrics from the labels. Nothing here calls a model. The test outputs are read only through
`evals/seal.py` (purpose "evaluation", after the FROZEN file exists); the dev command never lists the test folder.

    python -m evals.labeling_sheet dev        # dev sheet, facts files and dev U1 pairs under .local/p2-2/labeling/
    python -m evals.labeling_sheet freeze     # write FROZEN for the B1 test outputs (hashes only, no content)
    python -m evals.labeling_sheet test       # test sheet and test U1 pairs (refused until FROZEN exists)
    python -m evals.labeling_sheet snapshot --split dev|test   # log which items are labeled today
    python -m evals.labeling_sheet relabel --split test        # blind re-label sheet from earlier days only
    python -m evals.labeling_sheet check --split dev|test      # validate a saved sheet; writes nothing
    python -m evals.labeling_sheet metrics --split dev|test
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import random
import sys
import unicodedata
from datetime import date
from pathlib import Path

from evals import seal

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".local" / "p2-2"
B1_ROOT = WORK / "b1-full"
OUT = WORK / "labeling"
PROTOCOL = ROOT / "docs" / "plans" / "P2-planB-labeling.md"
SEED = 20261106
LABELS = ("supported", "wrong-number-or-name", "unsupported", "not-a-claim")
ERRORS = ("wrong-number-or-name", "unsupported")
SECTION_KEYS = ("summary", "away_vs_home", "home_vs_away", "arsenal", "watch", "confidence")
SHEET_FIELDS = ["item", "case_group", "sentence", "cited_facts", "label", "unsure", "note"]
FACT_FIELDS = ["id", "subject", "field", "value", "scope"]
PAIR_FIELDS = ["pair", "left", "right", "more_useful", "note"]
CHOICES = ("left", "right", "tie")
NOT_ACCEPTED = ("rules", "not_attempted")
MIN_ERRORS_FOR_RECALL = 10

# Section 3 of the protocol. B: sentences flagged by a hard gate; A: whole accepted reports; C: clean sentences of
# rejected candidates, per NLI band (the score-less sentences are a fifth stratum). Dev: 25 + 3 reports + 4x5 + 2.
QUOTAS = {
    "dev": {"B": 25, "A_reports": 3, "C_band": 5, "C_none": 2},
    "test": {"B": 150, "A_max": 130, "C_band": 20, "C_none": 10},
}
BANDS = ("<0.1", "0.1-0.5", "0.5-0.9", ">=0.9")


# ------------------------------------------------------------------ frame

def band_of(score):
    if score is None:
        return "none"
    return "<0.1" if score < 0.1 else "0.1-0.5" if score < 0.5 else "0.5-0.9" if score < 0.9 else ">=0.9"


def sentences_of(candidate):
    out = [candidate["headline"], *candidate["summary_lines"]]
    for key in SECTION_KEYS:
        out.extend(candidate["sections"][key])
    return out


def _is_gate(code):
    from agents import writer_checks

    return writer_checks.is_gate(code)


def extract_frame(items, tables):
    """One record per sentence of every model candidate that has a resolved form. `tables(case_id)` gives the fact table."""

    frame = []
    for name in sorted(items):
        item = items[name]
        case = item["case_id"]
        table = None
        for attempt in item.get("attempts", []):
            resolved = attempt.get("resolved_candidate")
            if not resolved:
                continue
            if table is None:
                table = tables(case)
            expected, identity = attempt.get("fact_table_identity"), getattr(table, "identity", None)
            if expected and identity and expected != identity:
                raise ValueError(f"the fact table of {case} differs from the one the writer received")
            accepted = item.get("path") not in NOT_ACCEPTED and attempt.get("checks") == []
            cited = sentences_of(attempt["candidate"])
            texts = sentences_of(resolved)
            scores = {n.get("index"): n.get("score") for n in attempt.get("nli") or []}
            gate = [f for f in attempt.get("check_detail", []) if f.get("sentence") and _is_gate(f["check"])]
            for pos, sentence in enumerate(texts):
                text = sentence["text"]
                found = [f for f in gate if f["sentence"] == text]
                frame.append({
                    "key": f"{case}|{attempt['content_attempt']}|{pos}", "case_id": case, "attempt": attempt["content_attempt"],
                    "pos": pos, "text": text, "cited": list(cited[pos]["evidence"]), "score": scores.get(pos),
                    "classes": sorted({f["check"] for f in found}),
                    "findings": [{"check": f["check"], "token": f.get("token")} for f in found],
                    "accepted": accepted, "report": case,
                })
    return frame


def stratum_of(record):
    return "B" if record["classes"] else "A" if record["accepted"] else "C"


# ------------------------------------------------------------------ sampler

def draw(frame, split, seed=SEED, quotas=None):
    """The stratified sample. Deterministic for a seed; each sentence is in one stratum (B, then A, then C).
    `p` is the inclusion probability used as the sampling weight (B: per drawn class; A: per report; C: per band)."""

    q = quotas or QUOTAS[split]
    rows = sorted(frame, key=lambda r: r["key"])
    chosen = []

    # B: round robin over the flagged classes, one sentence at a time from each (random order inside the class).
    rng = random.Random(f"{seed}:{split}:B")
    pool = [r for r in rows if stratum_of(r) == "B"]
    # A sentence flagged by several classes belongs to its rarest class only, so every B stratum is exclusive and
    # its inclusion probability (drawn / pool size) is the true one. The metrics still credit it to every class it names.
    overall = {}
    for r in pool:
        for c in r["classes"]:
            overall[c] = overall.get(c, 0) + 1
    home = {r["key"]: min(r["classes"], key=lambda c: (overall[c], c)) for r in pool}
    supply = {}
    for c in home.values():
        supply[c] = supply.get(c, 0) + 1
    queues = {c: [r for r in pool if home[r["key"]] == c] for c in sorted(supply)}
    for queue in queues.values():
        rng.shuffle(queue)
    taken, count, picked = set(), {c: 0 for c in queues}, []
    while len(picked) < q["B"]:
        progressed = False
        order = sorted(queues)
        rng.shuffle(order)
        for c in order:
            if len(picked) >= q["B"]:
                break
            while queues[c] and queues[c][0]["key"] in taken:
                queues[c].pop(0)
            if queues[c]:
                r = queues[c].pop(0)
                taken.add(r["key"])
                count[c] += 1
                picked.append((r, c))
                progressed = True
        if not progressed:
            break
    chosen += [dict(r, stratum="B", group=c, p=count[c] / supply[c]) for r, c in picked]

    # A: whole accepted reports.
    rng = random.Random(f"{seed}:{split}:A")
    accepted = [r for r in rows if stratum_of(r) == "A"]
    by_case = {}
    for r in accepted:
        by_case.setdefault(r["case_id"], []).append(r)
    cases = sorted(by_case)
    if "A_reports" in q:
        keep = sorted(rng.sample(cases, min(q["A_reports"], len(cases))))
    else:
        keep = list(cases)
        while keep and sum(len(by_case[c]) for c in keep) > q["A_max"]:
            keep.remove(rng.choice(keep))
    for case in keep:
        chosen += [dict(r, stratum="A", group="report", p=len(keep) / len(cases)) for r in by_case[case]]

    # C: clean sentences of rejected candidates, balanced over the NLI bands, score-less ones apart.
    rng = random.Random(f"{seed}:{split}:C")
    pool = [r for r in rows if stratum_of(r) == "C"]
    for band in (*BANDS, "none"):
        members = [r for r in pool if band_of(r["score"]) == band]
        rng.shuffle(members)
        take = members[: q["C_none"] if band == "none" else q["C_band"]]
        chosen += [dict(r, stratum="C", group=band, p=len(take) / len(members)) for r in take]
    return chosen


# ------------------------------------------------------------------ sheets

def _s(value):
    return "" if value is None else str(value)


def _fact_row(row):
    return {k: _s(row.get(k)) for k in FACT_FIELDS}


def cited_text(ids, rows_by_id):
    return "\n".join(" | ".join(_fact_row(rows_by_id[i]).values()) for i in ids if i in rows_by_id)


def _opaque_ids(n, seed, split, prefix, salt):
    rng = random.Random(f"{seed}:{split}:{salt}")
    return [f"{prefix}{x:06d}" for x in rng.sample(range(100000, 1000000), n)]


def build_split(items, tables, glossary, split, seed=SEED, source_hashes=None, protocol_sha256=None, quotas=None):
    """The blind sheet, the answer-key manifest and one facts table per case group."""

    q = dict(quotas or QUOTAS[split])
    sample = draw(extract_frame(items, tables), split, seed, quotas=q)
    rng = random.Random(f"{seed}:{split}:layout")
    cases = sorted({r["case_id"] for r in sample})
    rng.shuffle(cases)
    group_of = {c: f"G{n:02d}" for n, c in enumerate(cases, 1)}
    ordered = []
    for case in cases:
        members = sorted((r for r in sample if r["case_id"] == case), key=lambda r: r["key"])
        rng.shuffle(members)
        ordered += members
    ids = _opaque_ids(len(ordered), seed, split, "I", "ids")
    fact_rows = {c: tables(c).rows for c in cases}
    sheet, manifest_items = [], {}
    for item_id, r in zip(ids, ordered):
        by_id = {x["id"]: x for x in fact_rows[r["case_id"]]}
        sheet.append({"item": item_id, "case_group": group_of[r["case_id"]], "sentence": r["text"],
                      "cited_facts": cited_text(r["cited"], by_id), "label": "", "unsure": "", "note": ""})
        manifest_items[item_id] = {k: r[k] for k in ("key", "case_id", "attempt", "pos", "stratum", "group", "classes",
                                                     "findings", "score", "p", "accepted")}
        # The canonical text of the read-only columns: Excel edits to them are ignored and never reach a later sheet.
        manifest_items[item_id]["shown"] = {k: sheet[-1][k] for k in ("case_group", "sentence", "cited_facts")}
    glossary_rows = [{"id": "GLOSSARY", "subject": t["term"], "field": _s(t.get("short")), "value": t["definition"], "scope": ""}
                     for t in glossary]
    facts = {group_of[c]: [_fact_row(x) for x in fact_rows[c]] + glossary_rows for c in cases}
    manifest = {"protocol": "planB-labeling-v1", "protocol_sha256": protocol_sha256, "seed": seed, "split": split,
                "facts_sha256": {g: facts_digest(rows) for g, rows in facts.items()},
                "quotas": q, "source_hashes": dict(source_hashes or {}), "groups": {g: c for c, g in group_of.items()},
                "items": manifest_items}
    return {"sheet": sheet, "manifest": manifest, "facts": facts}


def facts_digest(rows):
    """SHA-256 of a facts table as issued (all cells as text), to detect an edited facts file."""

    return hashlib.sha256(json.dumps([[_s(r.get(k)) for k in FACT_FIELDS] for r in rows], ensure_ascii=True).encode()).hexdigest()


def write_csv(target, rows, fields):
    def dump(handle):
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)

    if hasattr(target, "write"):
        dump(target)
    else:
        with open(target, "w", encoding="utf-8-sig", newline="") as handle:
            dump(handle)


def decode_bytes(raw):
    """UTF-8 with or without a BOM (Excel 'CSV UTF-8'), else Windows-1252 (Excel plain 'CSV' on a Spanish PC)."""

    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def sniff_delimiter(text):
    """Comma, semicolon (Spanish-locale Excel) or tab, chosen from the header line."""

    header = text.split("\n", 1)[0]
    counts = {d: header.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=lambda d: (counts[d], d == ","))
    return best if counts[best] else ","


def read_csv(path):
    """Tolerant reader: BOM, delimiter, Windows line endings, header case and spaces. Cells become plain strings."""

    text = decode_bytes(Path(path).read_bytes())
    table = csv.reader(io.StringIO(text, newline=""), delimiter=sniff_delimiter(text))
    header = None
    out = []
    for cells in table:
        if not any(c.strip() for c in cells):
            continue
        if header is None:
            header = [c.strip().lower() for c in cells]
            continue
        cells = [c.replace("\r\n", "\n").replace("\r", "\n") for c in cells]
        cells = (cells + [""] * len(header))[: len(header)]
        out.append(dict(zip(header, cells)))
    return out


def normalize_label(value):
    """Case and spacing only (Excel autocapitalizes); a misspelled label stays invalid."""

    return " ".join((value or "").split()).lower()


# ------------------------------------------------------------------ U1 pairs

def render_report(report):
    lines = [report["headline"], ""]
    lines += [f"- {x}" for x in report["short_summary"]]
    for section in report["sections"]:
        lines += ["", section["title"]]
        body = section.get("body")
        lines += [body] if body else [f"- {b}" for b in section.get("bullets", [])]
    return "\n".join(lines)


def build_pairs(items, split, seed=SEED):
    """Each accepted B1 report beside the rules report of its case, random sides, no source labels in the sheet."""

    accepted = sorted(n for n, i in items.items() if i.get("path") not in NOT_ACCEPTED)
    rng = random.Random(f"{seed}:{split}:pairs")
    rng.shuffle(accepted)
    ids = _opaque_ids(len(accepted), seed, split, "P", "pairs")
    sheet, pairs = [], {}
    for pair_id, name in zip(ids, accepted):
        item = items[name]
        model, rules = render_report(item["report"]), render_report(item["rules_report"])
        model_left = rng.random() < 0.5
        left, right = (model, rules) if model_left else (rules, model)
        sheet.append({"pair": pair_id, "left": left, "right": right, "more_useful": "", "note": ""})
        pairs[pair_id] = {"case_id": item["case_id"], "left_source": "b1" if model_left else "rules"}
    return {"sheet": sheet, "manifest": {"seed": seed, "split": split, "question": "more useful for a casual fan", "pairs": pairs}}


def u1_summary(manifest, rows):
    win = tie = loss = unanswered = 0
    for row in rows:
        choice = normalize_label(row.get("more_useful"))
        if choice == "":
            unanswered += 1
            continue
        if choice not in CHOICES:
            raise ValueError(f"unknown choice {choice!r}")
        if choice == "tie":
            tie += 1
        elif (choice == "left") == (manifest["pairs"][row["pair"].strip()]["left_source"] == "b1"):
            win += 1
        else:
            loss += 1
    n = win + tie + loss
    lo, hi = wilson(win, n)
    return {"win": win, "tie": tie, "loss": loss, "unanswered": unanswered, "n": n,
            "win_rate": win / n if n else None, "lo": lo, "hi": hi}


# ------------------------------------------------------------------ seal, loading, freeze

def load_split_items(root, split):
    """Dev: purpose "label". Test: purpose "evaluation", which `seal` refuses until the FROZEN file matches the files."""

    return seal.read_outputs(root, split, seal.EVALUATION if split == "test" else "label")


def freeze_status(root, require=False):
    frozen = Path(root) / seal.FROZEN
    ok = frozen.exists() and frozen.read_text(encoding="utf-8") == seal.freeze_line(root)
    if require and not ok:
        raise seal.Sealed("the test outputs are sealed until the freeze")
    return ok


def write_freeze(root):
    """Hashes only; no output content is opened."""

    line = seal.freeze_line(root)
    (Path(root) / seal.FROZEN).write_text(line, encoding="utf-8", newline="\n")
    return line


# ------------------------------------------------------------------ re-label (self agreement)

def clean_labels(rows, id_col="item"):
    """{id: (label or None, unsure)} with the normalization `check` uses: trimmed ids, case-folded labels, invalid labels
    are None, duplicated ids are refused."""

    out = {}
    for row in rows:
        i = (row.get(id_col) or "").strip()
        if i in out:
            raise ValueError(f"duplicated item {i!r}")
        label = normalize_label(row.get("label"))
        out[i] = (label if label in LABELS else None, normalize_label(row.get("unsure")) == "y", bool(label))
    return out


def snapshot_log(log, rows, today):
    out = dict(log)
    for i, (label, _, _) in clean_labels(rows).items():
        if label and i not in out:
            out[i] = today
    return out


def draw_relabel(log, today, n=None, fraction=0.10, seed=SEED):
    """Items first seen labeled on an earlier day than `today`; n defaults to a tenth of all labeled items."""

    earlier = sorted(i for i, day in log.items() if day < today)
    n = math.ceil(fraction * len(log)) if n is None else n
    rng = random.Random(f"{seed}:relabel:{today}")
    return rng.sample(earlier, min(n, len(earlier)))


def build_relabel(built, ids, seed=SEED):
    rows = {r["item"]: r for r in built["sheet"]}
    new_ids = _opaque_ids(len(ids), seed, "relabel", "R", "-".join(sorted(ids))[:200])
    rng = random.Random(f"{seed}:relabel:order")
    order = list(zip(new_ids, ids))
    rng.shuffle(order)
    sheet = [dict(rows[old], item=new, label="", unsure="", note="") for new, old in order]
    return {"sheet": sheet, "manifest": {"seed": seed, "origin": {new: old for new, old in order}}}


# ------------------------------------------------------------------ labels and metrics

def join_labels(manifest, rows):
    joined, unlabeled, nac, unsure = [], 0, 0, 0
    seen = set()
    for row in rows:
        row = dict(row, item=row["item"].strip())
        meta = manifest["items"].get(row["item"])
        if meta is None:
            raise ValueError(f"unknown item {row['item']!r}")
        if row["item"] in seen:
            raise ValueError(f"duplicated item {row['item']!r}")
        seen.add(row["item"])
        label = normalize_label(row.get("label", ""))
        if label == "":
            unlabeled += 1
            continue
        if label not in LABELS:
            raise ValueError(f"unknown label {label!r} for {row['item']}")
        nac += label == "not-a-claim"
        flag = (row.get("unsure") or "").strip().upper() == "Y"
        unsure += flag
        joined.append({"item": row["item"], "label": label, "unsure": flag, "stratum": meta.get("stratum"),
                       "classes": list(meta.get("classes", [])), "group": meta.get("group"), "p": meta.get("p", 1.0),
                       "score": meta.get("score"), "report": meta.get("case_id")})
    return joined, {"labeled": len(joined), "unlabeled": unlabeled, "not_a_claim": nac, "unsure": unsure}


def wilson(k, n, z=1.96):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def weighted_share(items, predicate):
    """Inverse-inclusion-weighted share with a Wilson interval on the effective sample size (Kish)."""

    if not items:
        return {"estimate": None, "n": 0, "n_eff": 0, "lo": None, "hi": None}
    w = [1.0 / x["p"] for x in items]
    total = sum(w)
    est = sum(wi for wi, x in zip(w, items) if predicate(x)) / total
    n_eff = total * total / sum(wi * wi for wi in w)
    lo, hi = wilson(est * n_eff, n_eff)
    return {"estimate": est, "n": len(items), "n_eff": n_eff, "lo": lo, "hi": hi}


def _claims(joined):
    return [j for j in joined if j["label"] != "not-a-claim"]


def gate_metrics(joined):
    """Per hard-gate class, over the labeled flagged sentences (stratum B)."""

    flagged = [j for j in joined if j["stratum"] == "B"]
    out = {}
    for c in sorted({c for j in flagged for c in j["classes"]}):
        members = [j for j in flagged if c in j["classes"]]
        claims = _claims(members)
        out[c] = {"n": len(claims), "not_a_claim": len(members) - len(claims),
                  "precision": weighted_share(claims, lambda x: x["label"] in ERRORS),
                  "wrong_name_share": weighted_share(claims, lambda x: x["label"] == "wrong-number-or-name"),
                  "rigidity": weighted_share(claims, lambda x: x["label"] == "supported")}
    return out


def false_accept(joined):
    a = _claims([j for j in joined if j["stratum"] == "A"])
    reports = {}
    for j in a:
        reports.setdefault(j["report"], []).append(j)
    per_report = [{"p": v[0]["p"], "bad": any(x["label"] in ERRORS for x in v)} for v in reports.values()]
    return {"reports": len(reports), "reports_with_error": sum(r["bad"] for r in per_report),
            "sentences": len(a), "error_sentences": sum(j["label"] in ERRORS for j in a),
            "report_share": weighted_share(per_report, lambda r: r["bad"]),
            "sentence_share": weighted_share(a, lambda x: x["label"] in ERRORS)}


def recall(joined):
    errors = [j for j in joined if j["stratum"] in ("B", "C") and j["label"] in ERRORS]

    def block(members):
        if len(members) < MIN_ERRORS_FOR_RECALL:
            return "insufficient"
        classes = sorted({c for j in members for c in j["classes"]})
        by_class = {}
        for c in classes:     # a class needs ten errors of its own too
            own = sum(c in j["classes"] for j in members)
            by_class[c] = weighted_share(members, lambda x, c=c: c in x["classes"]) if own >= MIN_ERRORS_FOR_RECALL else "insufficient"
        return {"n_errors": len(members), "gate_set": weighted_share(members, lambda x: bool(x["classes"])), "by_class": by_class}

    out = {kind: block([j for j in errors if j["label"] == kind]) for kind in ERRORS}
    out["all"] = block(errors)
    return out


def _auroc(positive, negative):
    if not positive or not negative:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def nli_metrics(joined, thresholds=(0.5, 0.9)):
    scored = [j for j in _claims(joined) if j["score"] is not None]
    supported = [j for j in scored if j["label"] == "supported"]
    out = {"n_scored": len(scored),
           "auroc": _auroc([j["score"] for j in supported], [j["score"] for j in scored if j["label"] in ERRORS]),
           "thresholds": {}, "cross_table": {}}
    for t in thresholds:
        above = [j for j in scored if j["score"] >= t]
        out["thresholds"][str(t)] = {"precision": weighted_share(above, lambda x: x["label"] == "supported"),
                                     "recall": weighted_share(supported, lambda x, t=t: x["score"] >= t)}
    for flagged in (True, False):
        for t in thresholds:
            cell = [j for j in scored if bool(j["classes"]) == flagged and j["score"] >= t]
            out["cross_table"][f"gate_flagged={flagged},nli>={t}"] = {
                "n": len(cell), "supported": sum(j["label"] == "supported" for j in cell),
                "error": sum(j["label"] in ERRORS for j in cell)}
    return out


def agreement(first, second):
    n = len(first)
    if not n:
        return {"n": 0, "percent": None, "kappa": None}
    observed = sum(a == b for a, b in zip(first, second)) / n
    expected = sum((first.count(x) / n) * (second.count(x) / n) for x in set(first) | set(second))
    kappa = 1.0 if expected == 1 else (observed - expected) / (1 - expected)
    return {"n": n, "percent": observed, "kappa": kappa}


def acceptance(counts):
    out = {}
    total = {"accepted": 0, "cases": 0}
    for split, c in counts.items():
        lo, hi = wilson(c["accepted"], c["cases"])
        out[split] = {"accepted": c["accepted"], "cases": c["cases"], "rate": c["accepted"] / c["cases"], "lo": lo, "hi": hi}
        total = {k: total[k] + c[k] for k in total}
    lo, hi = wilson(total["accepted"], total["cases"])
    out["all"] = dict(total, rate=total["accepted"] / total["cases"], lo=lo, hi=hi)
    return out


def reliability(first_rows, second_rows, origin):
    """Self-agreement of the re-labeled items (second sheet ids map to first sheet ids) and the unsure share."""

    first, second = clean_labels(first_rows), clean_labels(second_rows)
    pairs = [(first[origin[i]][0], label) for i, (label, _, _) in second.items()
             if label and origin.get(i) in first and first[origin[i]][0]]
    labeled = [v for v in first.values() if v[0]]
    return {"agreement": agreement([a for a, _ in pairs], [b for _, b in pairs]),
            "unsure_share": sum(v[1] for v in labeled) / len(labeled) if labeled else None,
            "unanswered": sum(not v[2] for v in second.values())}


def acceptance_from_record(record):
    def cases(entry):
        return len(entry) if isinstance(entry, dict) else entry

    return acceptance({split: {"accepted": record[key]["accepted"], "cases": cases(record[key]["cases"])}
                       for split, key in (("dev", "dev"), ("test", "held_out"))})


def metrics_report(manifest, rows):
    """A metric is published only when every sampled item of the strata it needs is labeled (protocol section 4)."""

    joined, summary = join_labels(manifest, rows)
    sampled = {s: sum(m["stratum"] == s for m in manifest["items"].values()) for s in "ABC"}
    labeled = {s: sum(j["stratum"] == s for j in joined) for s in "ABC"}

    def need(strata, build):
        return build() if all(labeled[s] == sampled[s] for s in strata) else "unlabeled"

    return {"split": manifest["split"], "seed": manifest["seed"], "protocol_sha256": manifest.get("protocol_sha256"),
            "labels": summary, "strata": {s: {"sampled": sampled[s], "labeled": labeled[s]} for s in "ABC"},
            "gates": need("B", lambda: gate_metrics(joined)),
            "false_accept": need("A", lambda: false_accept(joined)),
            "recall": need("BC", lambda: recall(joined)),
            "nli": need("ABC", lambda: nli_metrics(joined))}


# ------------------------------------------------------------------ command line (owner PC)

def protocol_sha256():
    return hashlib.sha256(PROTOCOL.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _tables_for(split):
    from agents import fact_table, writer_input
    from evals import build_packets as bp
    from evals import run_b1_full as full

    dataset = full.DATASET
    glossary = writer_input.load_glossary(dataset / "glossary.json")
    packets = bp if split == "dev" else full._Packets(bp)      # the dev reader refuses test ids by design

    def tables(case_id):
        doc = writer_input.build_writer_input(packets.load_dev_packet(dataset, case_id), packets.load_dev_findings(dataset, case_id), glossary)
        return fact_table.build_fact_table(doc)

    return tables, glossary


def guard_no_answers(path, column):
    if Path(path).exists() and any((r.get(column) or "").strip() for r in read_csv(path)):
        raise SystemExit(f"{path} already holds answers; it is not overwritten")


def _dump(path, data):
    Path(path).write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8", newline="\n")


REQUIRED = {"sheet": ("item", "label"), "pairs": ("pair", "more_useful"), "relabel": ("item", "label")}
ANSWERS = {"sheet": ("label", "unsure", "note"), "pairs": ("more_useful", "note"), "relabel": ("label", "unsure", "note")}


def _valid(column, value):
    value = normalize_label(value)
    if column == "label":
        return value in LABELS
    if column == "unsure":
        return value in ("", "y")
    if column == "more_useful":
        return value in CHOICES
    return True


def _plain(value):
    return unicodedata.normalize("NFC", (value or "").replace("\r\n", "\n").replace("\r", "\n")).strip()


def check_rows(kind, rows, expected, shown=None):
    """Validate a saved sheet against the ids it was issued with. Pure: reads nothing else, writes nothing."""

    id_col = REQUIRED[kind][0]
    report = {"rows": len(rows), "missing_columns": [], "missing_ids": [], "duplicate_ids": [], "unknown_ids": [],
              "columns": {}, "readonly_cells_changed": 0}
    if rows:
        report["missing_columns"] = [c for c in REQUIRED[kind] if c not in rows[0]]
    ids = [(r.get(id_col) or "").strip() for r in rows]
    counts = {i: ids.count(i) for i in set(ids)}
    report["duplicate_ids"] = sorted(i for i, n in counts.items() if n > 1)
    report["unknown_ids"] = sorted(i for i in counts if i not in expected)
    report["missing_ids"] = sorted(i for i in expected if i not in counts)
    for column in ANSWERS[kind]:
        stats = {"labeled": 0, "unlabeled": 0, "invalid": []}
        for i, row in zip(ids, rows):
            raw = row.get(column, "")
            if not (raw or "").strip():
                stats["unlabeled"] += 1
            elif not _valid(column, raw):
                stats["invalid"].append((i, raw))
            elif column != "unsure" or normalize_label(raw) == "y":
                stats["labeled"] += 1
        report["columns"][column] = stats
    if shown:
        done = set()
        for i, row in zip(ids, rows):
            if i in shown and i not in done:
                done.add(i)
                report["readonly_cells_changed"] += sum(_plain(row.get(k)) != _plain(v) for k, v in shown[i].items())
    return report


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_report(out, split):
    out = Path(out)
    result = {}
    manifest = _load_json(out / f"{split}_manifest.json")
    result["sheet"] = check_rows("sheet", read_csv(out / f"{split}_sheet.csv"), set(manifest["items"]),
                                 {i: m["shown"] for i, m in manifest["items"].items() if "shown" in m})
    if (out / f"{split}_pairs.csv").exists():
        pairs = _load_json(out / f"{split}_pairs_manifest.json")
        result["pairs"] = check_rows("pairs", read_csv(out / f"{split}_pairs.csv"), set(pairs["pairs"]))
    if (out / f"{split}_relabel.csv").exists():
        origin = _load_json(out / f"{split}_relabel_manifest.json")["origin"]
        result["relabel"] = check_rows("relabel", read_csv(out / f"{split}_relabel.csv"), set(origin))
    return result


def cmd_check(out, split):
    """(text, exit code): 0 clean, 1 refused (columns or item ids not intact), 2 invalid values to fix."""

    try:
        reports = check_report(out, split)
    except (FileNotFoundError, KeyError) as error:
        return f"REFUSED: a required file is missing or unreadable ({type(error).__name__}: {error})", 1
    lines, refused, invalid = [], False, False
    for kind, r in reports.items():
        lines.append(f"[{kind}] {r['rows']} rows")
        if r["missing_columns"]:
            refused = True
            lines.append(f"  REFUSED: missing column(s) {', '.join(r['missing_columns'])}")
        for key, text in (("missing_ids", "missing"), ("duplicate_ids", "duplicated"), ("unknown_ids", "unknown or altered")):
            if r[key]:
                refused = True
                lines.append(f"  REFUSED: {len(r[key])} {text} id(s): {', '.join(r[key][:8])}{' ...' if len(r[key]) > 8 else ''}")
        for column, c in r["columns"].items():
            lines.append(f"  {column}: {c['labeled']} filled, {c['unlabeled']} blank, {len(c['invalid'])} invalid")
            for i, raw in c["invalid"][:10]:
                lines.append(f"    invalid {column} for {i}: {raw!r}")
            invalid = invalid or bool(c["invalid"])
        if r["readonly_cells_changed"]:
            lines.append(f"  {r['readonly_cells_changed']} read-only cell(s) were changed in the file; ignored")
    code = 1 if refused else 2 if invalid else 0
    if code == 1:
        lines.append("REFUSED: fix the file or restore the original ids before labeling further")
    elif code == 2:
        lines.append("Some values are invalid; fix them (labels: " + ", ".join(LABELS) + ")")
    else:
        lines.append("OK: ids intact, every filled value is valid")
    return "\n".join(lines), code


def require_judge_freeze(path, committed=None):
    """The FROZEN step needs the judge freeze (prompt, schema, model, parameters) verified and committed first."""

    from evals import judge_freeze as jf

    try:
        jf.verify_freeze(path)
    except jf.JudgeFrozenChanged as error:
        raise SystemExit(f"cannot freeze the test outputs: {error}") from None
    if not (committed or jf.is_committed)(path):
        raise SystemExit("cannot freeze the test outputs: the judge freeze file is not committed")


def cmd_snapshot(out, split, today):
    """Log the items labeled today that were not logged before. Run it at the end of each labeling day."""

    path = Path(out) / f"{split}_label_log.json"
    log = snapshot_log(json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}, read_csv(Path(out) / f"{split}_sheet.csv"), today)
    _dump(path, log)
    return len(log)


def cmd_relabel(out, split, today):
    out = Path(out)
    ids = draw_relabel(json.loads((out / f"{split}_label_log.json").read_text(encoding="utf-8")), today)
    if not ids:
        return 0
    guard_no_answers(out / f"{split}_relabel.csv", "label")
    manifest = _load_json(out / f"{split}_manifest.json")
    rows = read_csv(out / f"{split}_sheet.csv")
    for row in rows:       # the read-only columns come from the manifest, never from the (possibly Excel-edited) file
        row["item"] = row["item"].strip()
        row.update(manifest["items"].get(row["item"], {}).get("shown", {}))
    built = build_relabel({"sheet": rows}, ids)
    write_csv(out / f"{split}_relabel.csv", built["sheet"], SHEET_FIELDS)
    _dump(out / f"{split}_relabel_manifest.json", built["manifest"])
    return len(ids)


def cmd_metrics(out, split, record):
    out = Path(out)
    rows = read_csv(out / f"{split}_sheet.csv")
    report = metrics_report(json.loads((out / f"{split}_manifest.json").read_text(encoding="utf-8")), rows)
    if (out / f"{split}_relabel.csv").exists():
        origin = json.loads((out / f"{split}_relabel_manifest.json").read_text(encoding="utf-8"))["origin"]
        report["reliability"] = reliability(rows, read_csv(out / f"{split}_relabel.csv"), origin)
    if (out / f"{split}_pairs.csv").exists():
        report["u1"] = u1_summary(json.loads((out / f"{split}_pairs_manifest.json").read_text(encoding="utf-8")), read_csv(out / f"{split}_pairs.csv"))
    if record is not None:
        report["acceptance"] = acceptance_from_record(record)
    return report


def _write_all(split, items, out):
    tables, glossary = _tables_for(split)
    built = build_split(items, tables, glossary, split, source_hashes=seal.hashes(B1_ROOT, split), protocol_sha256=protocol_sha256())
    pairs = build_pairs(items, split)
    out.mkdir(parents=True, exist_ok=True)
    guard_no_answers(out / f"{split}_sheet.csv", "label")
    guard_no_answers(out / f"{split}_pairs.csv", "more_useful")
    write_csv(out / f"{split}_sheet.csv", built["sheet"], SHEET_FIELDS)
    for group, rows in built["facts"].items():
        write_csv(out / f"{split}_facts_{group}.csv", rows, FACT_FIELDS)
    write_csv(out / f"{split}_pairs.csv", pairs["sheet"], PAIR_FIELDS)
    _dump(out / f"{split}_manifest.json", built["manifest"])
    _dump(out / f"{split}_pairs_manifest.json", pairs["manifest"])
    counts = {s: sum(m["stratum"] == s for m in built["manifest"]["items"].values()) for s in "ABC"}
    print(f"{split}: {len(built['sheet'])} sentences ({counts}), {len(built['facts'])} case groups, {len(pairs['sheet'])} U1 pairs -> {out}")


def main(argv=None):  # pragma: no cover - owner-PC entry point
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["dev", "freeze", "test", "snapshot", "relabel", "metrics", "check"])
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--today", default=date.today().isoformat())
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    if args.command == "dev":
        _write_all("dev", load_split_items(B1_ROOT, "dev"), args.out)
    elif args.command == "freeze":
        from evals import judge_freeze

        require_judge_freeze(judge_freeze.FREEZE_PATH)
        print("FROZEN written for the B1 test outputs:", write_freeze(B1_ROOT).strip())
    elif args.command == "test":
        _write_all("test", load_split_items(B1_ROOT, "test"), args.out)
    elif args.command == "check":
        text, code = cmd_check(args.out, args.split)
        print(text)
        return code
    elif args.command == "snapshot":
        print(f"{cmd_snapshot(args.out, args.split, args.today)} items logged as labeled")
    elif args.command == "relabel":
        print(f"{cmd_relabel(args.out, args.split, args.today)} items labeled on earlier days -> {args.split}_relabel.csv")
    else:
        record = json.loads((ROOT / "evals" / "data" / "writer" / "b1-run-record.json").read_text(encoding="utf-8"))
        print(json.dumps(cmd_metrics(args.out, args.split, record), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
