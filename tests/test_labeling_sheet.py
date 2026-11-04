"""Plan B labeling sheets (docs/plans/P2-planB-labeling.md): sampler, blind sheets, manifest, U1 pairs, metrics.

Synthetic items only. No real B1 output (and no test-split output) is read by these tests.
"""
import csv
import io
import json
import math
from types import SimpleNamespace

import pytest

from evals import labeling_sheet as ls
from evals import seal

SECTION_KEYS = ("summary", "away_vs_home", "home_vs_away", "arsenal", "watch", "confidence")


# ---------------------------------------------------------------- synthetic items

def _candidate(case, n, evidence_key="ids"):
    def s(tag):
        text = f"{case.replace('-', '')} a{n} {tag} sentence."
        ev = ["F001", "F002"] if evidence_key == "ids" else [{"path": "p.q", "value": "1"}]
        return {"text": text, "evidence": ev}

    return {
        "headline": s("headline"),
        "summary_lines": [s(f"line{k}") for k in range(3)],
        "sections": {"summary": [s("sum")], "away_vs_home": [s("avh")], "home_vs_away": [s("hva")],
                     "arsenal": [s("ars")], "watch": [s(f"w{k}") for k in range(3)], "confidence": [s("conf")]},
    }


def _texts(candidate):
    out = [candidate["headline"], *candidate["summary_lines"]]
    for key in SECTION_KEYS:
        out.extend(candidate["sections"][key])
    return [x["text"] for x in out]


def _attempt(case, n, *, flagged=None, scores=None, checks=None, structure_fail=False, style=True):
    """flagged: {position: [check codes]}; scores: list or None (all 0.95)."""
    if structure_fail:
        return {"content_attempt": n, "candidate": None, "checks": ["W17.structure"]}
    cand = _candidate(case, n)
    resolved = _candidate(case, n, evidence_key="paths")
    texts = _texts(cand)
    flagged = flagged or {}
    detail = []
    for pos, codes in flagged.items():
        for code in codes:
            detail.append({"check": code, "sentence": texts[pos], "token": "x"})
    if style:
        detail.append({"check": "S-4", "sentence": texts[0], "token": "y"})      # style: never a class
        detail.append({"check": "W12.scope", "sentence": "", "token": None})     # report level: no sentence
        detail.append({"check": "W17.length", "sentence": None, "token": None})
    gate_codes = checks if checks is not None else sorted({c for cs in flagged.values() for c in cs})
    scores = scores if scores is not None else [0.95] * len(texts)
    nli = [{"index": i, "sentence": t, "score": sc, "problem": None if sc is not None else "unrenderable"}
           for i, (t, sc) in enumerate(zip(texts, scores))]
    return {"content_attempt": n, "candidate": cand, "resolved_candidate": resolved, "checks": gate_codes,
            "check_detail": detail, "nli": nli, "model": "m-secret", "path": "primary"}


def _item(case, attempts, path="rules"):
    return {"case_id": case, "path": path, "content_attempts": len(attempts), "attempts": attempts,
            "report": {"headline": f"{case} model headline", "short_summary": ["a", "b", "c"],
                       "sections": [{"title": "Matchup Summary", "body": f"{case} model body"}]},
            "rules_report": {"headline": f"{case} rules headline", "short_summary": ["x", "y", "z"],
                             "sections": [{"title": "Matchup Summary", "bullets": [f"{case} rules bullet"]}]}}


class _Table:
    def __init__(self, case):
        self.rows = [{"id": "F001", "subject": "Ace", "field": "era", "value": 2.5, "scope": "2026 season"},
                     {"id": "F002", "subject": "Ace", "field": "whip", "value": 1.1, "scope": "2026 season"},
                     {"id": "F003", "subject": case, "field": "other", "value": "z", "scope": None}]


def _tables(case):
    return _Table(case)


GLOSSARY = [{"term": "ERA", "short": "earned run average", "definition": "Earned runs per nine."}]


def _world():
    """Six accepted dev cases, plus rejected ones with flags in several classes and NLI bands."""
    items = {}
    for k in range(6):
        case = f"acc-{k}"
        items[f"{case}.json"] = _item(case, [_attempt(case, 1, checks=[], style=False)], path="primary")
    classes = ["W1.entity", "W1.number", "W2.comparison", "W5.label", "W10.cause"]
    for k in range(10):
        case = f"rej-{k}"
        flagged = {1 + (k % 3): [classes[k % 5]], 5: [classes[(k + 1) % 5]], 9: ["W1.entity"]}
        scores = [0.05, 0.3, 0.7, 0.97, None, 0.2, 0.6, 0.99, 0.02, 0.5, 0.95, 0.4]
        items[f"{case}.json"] = _item(case, [_attempt(case, 1, flagged=flagged, scores=scores),
                                             _attempt(case, 2, flagged={0: ["W1.number"]}, scores=scores)])
    return items


# ---------------------------------------------------------------- frame

def test_frame_lists_every_sentence_in_report_order_with_cited_ids_scores_and_hard_classes():
    item = _item("c1", [_attempt("c1", 1, flagged={2: ["W1.entity", "W2.comparison"]}, scores=[None] + [0.5] * 11)])
    frame = ls.extract_frame({"c1.json": item}, _tables)
    assert [r["pos"] for r in frame] == list(range(12))
    assert frame[0]["text"] == "c1 a1 headline sentence." and frame[0]["cited"] == ["F001", "F002"]
    assert frame[0]["score"] is None and frame[1]["score"] == 0.5
    assert frame[2]["classes"] == ["W1.entity", "W2.comparison"]
    assert all(r["case_id"] == "c1" and r["attempt"] == 1 for r in frame)


def test_style_report_level_and_sentenceless_findings_are_not_classes():
    item = _item("c1", [_attempt("c1", 1, flagged={})])
    frame = ls.extract_frame({"c1.json": item}, _tables)
    assert all(r["classes"] == [] for r in frame)          # S-4, W12.scope (empty sentence), W17.length (None)


def test_a_candidate_without_a_resolved_form_has_no_sentences():
    item = _item("c1", [_attempt("c1", 1, structure_fail=True), _attempt("c1", 2)])
    frame = ls.extract_frame({"c1.json": item}, _tables)
    assert {r["attempt"] for r in frame} == {2}


def test_only_the_final_clean_candidate_of_an_accepted_report_is_accepted():
    item = _item("c1", [_attempt("c1", 1, flagged={0: ["W1.entity"]}), _attempt("c1", 2, checks=[], style=False)], path="primary")
    frame = ls.extract_frame({"c1.json": item}, _tables)
    assert {r["attempt"] for r in frame if r["accepted"]} == {2}
    assert not any(r["accepted"] for r in frame if r["attempt"] == 1)
    rules = _item("c2", [_attempt("c2", 1, flagged={0: ["W1.entity"]})])
    assert not any(r["accepted"] for r in ls.extract_frame({"c2.json": rules}, _tables))


def test_stratum_priority_is_flagged_then_accepted_then_clean_rejected():
    flagged = {"accepted": True, "classes": ["W1.entity"]}
    assert ls.stratum_of(flagged) == "B"
    assert ls.stratum_of({"accepted": True, "classes": []}) == "A"
    assert ls.stratum_of({"accepted": False, "classes": []}) == "C"


# ---------------------------------------------------------------- sampler

def _drawn(split="dev", seed=ls.SEED, world=None):
    frame = ls.extract_frame(world or _world(), _tables)
    return frame, ls.draw(frame, split, seed)


def test_the_recorded_seed_is_the_owners():
    assert ls.SEED == 20261106


def test_draw_is_deterministic_and_the_seed_matters():
    _, a = _drawn()
    _, b = _drawn()
    _, c = _drawn(seed=1)
    keys = lambda d: [r["key"] for r in d]
    assert keys(a) == keys(b)
    assert sorted(keys(a)) != sorted(keys(c))


def test_every_selected_sentence_is_in_exactly_one_stratum_and_none_is_drawn_twice():
    _, drawn = _drawn()
    assert len({r["key"] for r in drawn}) == len(drawn)
    assert {r["stratum"] for r in drawn} <= {"A", "B", "C"}


def test_stratum_a_takes_whole_reports_three_of_the_six_in_dev():
    frame, drawn = _drawn()
    a = [r for r in drawn if r["stratum"] == "A"]
    cases = {r["case_id"] for r in a}
    assert len(cases) == 3 and cases <= {f"acc-{k}" for k in range(6)}
    for case in cases:      # every sentence of the chosen report
        assert sum(r["case_id"] == case for r in a) == 12
    assert {r["p"] for r in a} == {0.5}


def test_test_stratum_a_keeps_all_reports_and_drops_whole_ones_above_the_cap():
    world = _world()
    frame = ls.extract_frame(world, _tables)
    drawn = ls.draw(frame, "test", ls.SEED)
    a = [r for r in drawn if r["stratum"] == "A"]
    assert len({r["case_id"] for r in a}) == 6 and len(a) == 72
    quotas = dict(ls.QUOTAS["test"], A_max=40)
    drawn = ls.draw(frame, "test", ls.SEED, quotas=quotas)
    a = [r for r in drawn if r["stratum"] == "A"]
    assert len(a) <= 40 and len(a) % 12 == 0 and len(a) > 0
    assert {r["p"] for r in a} == {len({r["case_id"] for r in a}) / 6}


def test_stratum_b_is_round_robin_over_classes_and_takes_small_classes_whole():
    world = _world()
    frame = ls.extract_frame(world, _tables)
    quotas = dict(ls.QUOTAS["dev"], B=9)
    drawn = ls.draw(frame, "dev", ls.SEED, quotas=quotas)
    b = [r for r in drawn if r["stratum"] == "B"]
    assert len(b) == 9
    per_class = {}
    for r in b:
        per_class[r["group"]] = per_class.get(r["group"], 0) + 1
    assert set(per_class) == {"W1.entity", "W1.number", "W2.comparison", "W5.label", "W10.cause"}
    assert max(per_class.values()) - min(per_class.values()) <= 1
    supply = {}
    for r in frame:
        for c in r["classes"]:
            supply[c] = supply.get(c, 0) + 1
    for r in b:
        assert r["p"] == pytest.approx(per_class[r["group"]] / supply[r["group"]])


def test_b_is_limited_by_supply_not_topped_up_from_other_strata():
    item = _item("only", [_attempt("only", 1, flagged={0: ["W1.entity"]})])
    frame = ls.extract_frame({"only.json": item}, _tables)
    drawn = ls.draw(frame, "dev", ls.SEED)
    b = [r for r in drawn if r["stratum"] == "B"]
    assert len(b) == 1 and b[0]["p"] == 1.0
    assert len([r for r in drawn if r["stratum"] == "C"]) <= ls.QUOTAS["dev"]["C_band"] * 4 + ls.QUOTAS["dev"]["C_none"]


def test_stratum_c_is_clean_rejected_sentences_balanced_over_nli_bands_plus_scoreless():
    frame, drawn = _drawn()
    c = [r for r in drawn if r["stratum"] == "C"]
    assert c and all(r["classes"] == [] and not r["accepted"] for r in c)
    bands = {}
    for r in c:
        bands[r["group"]] = bands.get(r["group"], 0) + 1
    assert set(bands) <= {"<0.1", "0.1-0.5", "0.5-0.9", ">=0.9", "none"}
    assert all(n <= ls.QUOTAS["dev"]["C_band"] for g, n in bands.items() if g != "none")
    assert bands.get("none", 0) <= ls.QUOTAS["dev"]["C_none"]
    for r in c:
        assert ls.band_of(r["score"]) == r["group"]


def test_bands_and_edges():
    assert [ls.band_of(x) for x in (0.0, 0.099, 0.1, 0.499, 0.5, 0.899, 0.9, 1.0, None)] == \
        ["<0.1", "<0.1", "0.1-0.5", "0.1-0.5", "0.5-0.9", "0.5-0.9", ">=0.9", ">=0.9", "none"]


# ---------------------------------------------------------------- blind sheet and manifest

def _build(split="dev", world=None):
    return ls.build_split(world or _world(), _tables, GLOSSARY, split, source_hashes={"a.json": "h"}, protocol_sha256="p" * 64)


def _csv_text(rows):
    buf = io.StringIO()
    ls.write_csv(buf, rows, ls.SHEET_FIELDS)
    return buf.getvalue()


def test_sheet_columns_are_the_protocols_and_labels_start_blank():
    built = _build()
    assert ls.SHEET_FIELDS == ["item", "case_group", "sentence", "cited_facts", "label", "unsure", "note"]
    assert built["sheet"] and all(r["label"] == "" and r["unsure"] == "" and r["note"] == "" for r in built["sheet"])
    assert ls.LABELS == ("supported", "wrong-number-or-name", "unsupported", "not-a-claim")


def test_sheet_hides_cases_gates_scores_strata_attempts_and_models():
    text = _csv_text(_build()["sheet"])
    for secret in ("acc-", "rej-", "W1.", "W2.", "W5.", "W10.", "m-secret", "primary", "0.95", "0.05", "stratum", "attempt"):
        assert secret not in text
    sheet = _build()["sheet"]
    assert all(set(r) == set(ls.SHEET_FIELDS) for r in sheet)
    assert all("rej-" not in r["item"] and "acc-" not in r["item"] and r["case_group"].startswith("G") for r in sheet)


def test_item_ids_are_unique_opaque_and_stable_for_a_seed():
    a, b = _build(), _build()
    ids = [r["item"] for r in a["sheet"]]
    assert len(set(ids)) == len(ids) and ids == [r["item"] for r in b["sheet"]]
    assert all(i.startswith("I") and i[1:].isdigit() for i in ids)


def test_groups_hold_one_case_each_and_items_are_grouped_then_shuffled():
    built = _build()
    case_of = {i: m["case_id"] for i, m in built["manifest"]["items"].items()}
    by_group = {}
    for row in built["sheet"]:
        by_group.setdefault(row["case_group"], set()).add(case_of[row["item"]])
    assert all(len(v) == 1 for v in by_group.values())
    seq = [r["case_group"] for r in built["sheet"]]
    assert seq == sorted(seq, key=lambda g: seq.index(g))            # contiguous groups
    assert len({g for g in seq}) == len(by_group)
    assert built["manifest"]["groups"] == {g: next(iter(v)) for g, v in by_group.items()}


def test_cited_facts_are_shown_as_the_enumerated_rows_and_unknown_ids_are_dropped():
    item = _item("c1", [_attempt("c1", 1, flagged={0: ["W1.entity"]})])
    item["attempts"][0]["candidate"]["headline"]["evidence"] = ["F002", "F999", "F001"]
    built = ls.build_split({"c1.json": item}, _tables, GLOSSARY, "dev")
    row = next(r for r in built["sheet"] if r["sentence"] == "c1 a1 headline sentence.")
    assert row["cited_facts"].split("\n") == ["F002 | Ace | whip | 1.1 | 2026 season", "F001 | Ace | era | 2.5 | 2026 season"]


def test_manifest_keeps_stratum_gates_score_p_hashes_and_protocol_apart_from_the_sheet():
    built = _build()
    m = built["manifest"]
    assert m["seed"] == ls.SEED and m["split"] == "dev" and m["protocol_sha256"] == "p" * 64
    assert m["source_hashes"] == {"a.json": "h"} and m["quotas"] == ls.QUOTAS["dev"]
    for item, rec in m["items"].items():
        assert set(rec) >= {"case_id", "attempt", "pos", "stratum", "group", "classes", "score", "p", "accepted", "findings"}
        assert 0 < rec["p"] <= 1
    assert len(m["items"]) == len(built["sheet"])
    b = next(r for r in m["items"].values() if r["stratum"] == "B")
    assert b["classes"] and b["findings"]


def test_facts_file_per_group_has_the_complete_table_and_the_glossary():
    built = _build()
    assert set(built["facts"]) == set(built["manifest"]["groups"])
    rows = next(iter(built["facts"].values()))
    assert [r["id"] for r in rows if r["id"].startswith("F")] == ["F001", "F002", "F003"]
    gloss = [r for r in rows if r["id"] == "GLOSSARY"]
    assert gloss == [{"id": "GLOSSARY", "subject": "ERA", "field": "earned run average", "value": "Earned runs per nine.", "scope": ""}]


def test_a_missing_score_or_scope_renders_as_empty_not_none():
    built = _build()
    text = "".join(_csv_text(built["sheet"])) + json.dumps(built["facts"])
    assert "None" not in text


# ---------------------------------------------------------------- seal and loading

def test_dev_items_load_without_touching_test_and_test_stays_sealed_without_frozen(tmp_path):
    (tmp_path / "dev").mkdir()
    (tmp_path / "test").mkdir()
    (tmp_path / "dev" / "a.json").write_text(json.dumps({"case_id": "a"}), encoding="utf-8")
    (tmp_path / "test" / "b.json").write_text("{not json", encoding="utf-8")      # would explode if read
    assert ls.load_split_items(tmp_path, "dev") == {"a.json": {"case_id": "a"}}
    with pytest.raises(seal.Sealed):
        ls.load_split_items(tmp_path, "test")
    with pytest.raises(seal.Sealed):
        ls.freeze_status(tmp_path, require=True)


def test_freeze_writes_only_hashes_and_then_test_opens(tmp_path):
    (tmp_path / "test").mkdir()
    (tmp_path / "dev").mkdir()
    (tmp_path / "test" / "b.json").write_text(json.dumps({"case_id": "b"}), encoding="utf-8")
    line = ls.write_freeze(tmp_path)
    assert (tmp_path / "FROZEN").read_text(encoding="utf-8") == line == seal.freeze_line(tmp_path)
    assert ls.load_split_items(tmp_path, "test") == {"b.json": {"case_id": "b"}}


# ---------------------------------------------------------------- U1 pairs

def test_pairs_cover_accepted_reports_only_blind_with_sides_in_the_manifest():
    world = _world()
    built = ls.build_pairs(world, "dev")
    assert len(built["sheet"]) == 6 and len(built["manifest"]["pairs"]) == 6
    assert ls.PAIR_FIELDS == ["pair", "left", "right", "more_useful", "note"]
    for row in built["sheet"]:
        assert row["more_useful"] == "" and row["note"] == ""
        rec = built["manifest"]["pairs"][row["pair"]]
        assert rec["left_source"] in ("b1", "rules")
        left_is_model = "model" in row["left"]
        assert left_is_model == (rec["left_source"] == "b1")
        assert ("model" in row["right"]) != left_is_model


def _csv_text_pairs(rows):
    buf = io.StringIO()
    ls.write_csv(buf, rows, ls.PAIR_FIELDS)
    return buf.getvalue()


def test_pair_sides_are_randomised_deterministically():
    world = _world()
    a = ls.build_pairs(world, "dev")
    b = ls.build_pairs(world, "dev")
    sources = lambda x: sorted((r["case_id"], r["left_source"]) for r in x["manifest"]["pairs"].values())
    assert sources(a) == sources(b)
    seen = set()
    for seed in range(40):
        seen |= {r["left_source"] for r in ls.build_pairs(world, "dev", seed=seed)["manifest"]["pairs"].values()}
    assert seen == {"b1", "rules"}


def test_both_reports_are_rendered_in_the_same_shape():
    item = _item("c1", [_attempt("c1", 1, checks=[], style=False)], path="primary")
    model, rules = ls.render_report(item["report"]), ls.render_report(item["rules_report"])
    for text in (model, rules):
        assert text.splitlines()[0].endswith("headline") and "Matchup Summary" in text
    assert "rules bullet" in rules and "- " in rules


# ---------------------------------------------------------------- re-label (self agreement)

def test_relabel_draws_only_from_items_labeled_on_an_earlier_day():
    built = _build()
    ids = [r["item"] for r in built["sheet"]]
    log = {i: "2026-11-06" for i in ids[:60]}
    log.update({i: "2026-11-07" for i in ids[60:80]})
    log.update({i: "2026-11-08" for i in ids[80:]})
    chosen = ls.draw_relabel(log, "2026-11-08", n=10)
    assert len(chosen) == 10 and set(chosen) <= set(ids[:80])
    assert chosen == ls.draw_relabel(log, "2026-11-08", n=10)
    default_n = ls.draw_relabel(log, "2026-11-08")
    assert len(default_n) == math.ceil(0.10 * len(log))


def test_relabel_sheet_uses_new_ids_and_is_blind_and_unlabeled():
    built = _build()
    ids = [r["item"] for r in built["sheet"]]
    out = ls.build_relabel(built, ids[:10], seed=5)
    assert len(out["sheet"]) == 10
    assert not {r["item"] for r in out["sheet"]} & set(ids)
    assert all(r["label"] == "" for r in out["sheet"])
    assert set(out["manifest"]["origin"].values()) == set(ids[:10])


def test_snapshot_records_the_first_day_an_item_is_seen_labeled_and_never_moves_it():
    rows = [{"item": "I1", "label": "supported"}, {"item": "I2", "label": ""}, {"item": "I3", "label": "unsupported"}]
    log = ls.snapshot_log({}, rows, "2026-11-06")
    assert log == {"I1": "2026-11-06", "I3": "2026-11-06"}
    log = ls.snapshot_log(log, rows + [{"item": "I2", "label": "supported"}], "2026-11-07")
    assert log == {"I1": "2026-11-06", "I3": "2026-11-06", "I2": "2026-11-07"}


# ---------------------------------------------------------------- labels and metrics

def _joined(spec):
    """spec: list of (label, stratum, classes, p, score, report)."""
    out = []
    for n, (label, stratum, classes, p, score, report) in enumerate(spec):
        out.append({"item": f"I{n}", "label": label, "unsure": "", "stratum": stratum, "classes": classes,
                    "p": p, "score": score, "report": report, "group": (classes or ["x"])[0]})
    return out


def test_join_rejects_unknown_labels_and_counts_blanks_and_not_a_claim():
    manifest = {"items": {"I1": {"stratum": "B"}, "I2": {"stratum": "B"}, "I3": {"stratum": "B"}}}
    rows = [{"item": "I1", "label": "supported", "unsure": "Y", "note": ""}, {"item": "I2", "label": "", "unsure": "", "note": ""},
            {"item": "I3", "label": "not-a-claim", "unsure": "", "note": ""}]
    joined, summary = ls.join_labels(manifest, rows)
    assert [j["item"] for j in joined] == ["I1", "I3"]
    assert summary == {"labeled": 2, "unlabeled": 1, "not_a_claim": 1, "unsure": 1}
    with pytest.raises(ValueError):
        ls.join_labels(manifest, [{"item": "I1", "label": "Supported ", "unsure": "", "note": ""}])
    with pytest.raises(ValueError):
        ls.join_labels(manifest, [{"item": "I9", "label": "supported", "unsure": "", "note": ""}])


def test_wilson_interval():
    lo, hi = ls.wilson(5, 10)
    assert lo == pytest.approx(0.2366, abs=1e-3) and hi == pytest.approx(0.7634, abs=1e-3)
    assert ls.wilson(0, 0) == (None, None)
    lo, hi = ls.wilson(0, 20)
    assert lo == 0.0 and 0 < hi < 0.2


def test_weighted_share_uses_inverse_inclusion_weights():
    items = [{"p": 1.0, "hit": True}, {"p": 0.25, "hit": False}]
    est = ls.weighted_share(items, lambda x: x["hit"])
    assert est["estimate"] == pytest.approx(1 / (1 + 4)) and est["n"] == 2
    assert 0 <= est["lo"] <= est["estimate"] <= est["hi"] <= 1
    assert ls.weighted_share([], lambda x: True)["estimate"] is None


def test_gate_precision_and_rigidity_per_class_exclude_not_a_claim():
    joined = _joined([
        ("wrong-number-or-name", "B", ["W1.number"], 1.0, 0.9, "r1"),
        ("unsupported", "B", ["W1.number"], 1.0, 0.4, "r1"),
        ("supported", "B", ["W1.number"], 1.0, 0.99, "r1"),
        ("supported", "B", ["W1.number"], 1.0, 0.99, "r1"),
        ("not-a-claim", "B", ["W1.number"], 1.0, None, "r1"),
        ("supported", "B", ["W2.comparison"], 0.5, 0.9, "r2"),
    ])
    m = ls.gate_metrics(joined)
    assert m["W1.number"]["precision"]["estimate"] == pytest.approx(0.5)
    assert m["W1.number"]["rigidity"]["estimate"] == pytest.approx(0.5)
    assert m["W1.number"]["wrong_name_share"]["estimate"] == pytest.approx(0.25)
    assert m["W1.number"]["not_a_claim"] == 1 and m["W1.number"]["n"] == 4
    assert m["W2.comparison"]["precision"]["estimate"] == 0.0


def test_false_accept_counts_reports_with_an_error_and_error_sentences():
    joined = _joined([
        ("supported", "A", [], 0.5, 0.9, "ra"), ("supported", "A", [], 0.5, 0.9, "ra"),
        ("unsupported", "A", [], 0.5, 0.9, "rb"), ("supported", "A", [], 0.5, 0.9, "rb"),
        ("not-a-claim", "A", [], 0.5, 0.9, "rb"),
    ])
    m = ls.false_accept(joined)
    assert m["reports"] == 2 and m["reports_with_error"] == 1 and m["sentences"] == 4 and m["error_sentences"] == 1
    assert m["report_share"]["estimate"] == pytest.approx(0.5)


def test_recall_is_reported_only_with_at_least_ten_errors_of_that_kind():
    spec = [("wrong-number-or-name", "B", ["W1.number"], 1.0, 0.5, "r")] * 10 + \
           [("unsupported", "C", [], 0.5, 0.5, "r")] * 3 + [("unsupported", "B", ["W2.comparison"], 1.0, 0.5, "r")] * 2
    m = ls.recall(_joined(spec))
    assert m["wrong-number-or-name"]["gate_set"]["estimate"] == 1.0
    assert m["unsupported"] == "insufficient"
    assert m["all"]["gate_set"]["estimate"] == pytest.approx((10 + 2) / (10 + 2 + 6))
    assert m["wrong-number-or-name"]["by_class"]["W1.number"]["estimate"] == 1.0


def test_nli_auroc_and_threshold_precision_recall():
    joined = _joined([("supported", "C", [], 1.0, 0.95, "r"), ("supported", "C", [], 1.0, 0.8, "r"),
                      ("unsupported", "C", [], 1.0, 0.3, "r"), ("wrong-number-or-name", "C", [], 1.0, 0.85, "r"),
                      ("supported", "C", [], 1.0, None, "r")])
    m = ls.nli_metrics(joined)
    assert m["n_scored"] == 4
    assert m["auroc"] == pytest.approx(3 / 4)               # 3 of 4 supported/error pairs are ordered
    at = m["thresholds"]["0.9"]
    assert at["precision"]["estimate"] == 1.0 and at["recall"]["estimate"] == pytest.approx(1 / 2)
    assert m["thresholds"]["0.5"]["precision"]["estimate"] == pytest.approx(2 / 3)
    assert ls.nli_metrics(_joined([("supported", "C", [], 1, 0.9, "r")]))["auroc"] is None


def test_cohens_kappa_and_agreement():
    a = ["supported", "supported", "unsupported", "unsupported"]
    assert ls.agreement(a, a) == {"n": 4, "percent": 1.0, "kappa": 1.0}
    b = ["supported", "unsupported", "unsupported", "supported"]
    out = ls.agreement(a, b)
    assert out["percent"] == 0.5 and out["kappa"] == pytest.approx(0.0)
    assert ls.agreement([], [])["kappa"] is None


def test_acceptance_rates_with_wilson_intervals():
    out = ls.acceptance({"dev": {"accepted": 6, "cases": 20}, "test": {"accepted": 5, "cases": 20}})
    assert out["all"]["accepted"] == 11 and out["all"]["cases"] == 40 and out["all"]["rate"] == pytest.approx(0.275)
    assert out["dev"]["lo"] < 0.3 < out["dev"]["hi"]


def test_u1_summary_counts_model_wins_ties_and_losses_with_an_interval():
    manifest = {"pairs": {"P1": {"left_source": "b1"}, "P2": {"left_source": "rules"}, "P3": {"left_source": "b1"},
                          "P4": {"left_source": "b1"}}}
    rows = [{"pair": "P1", "more_useful": "left"}, {"pair": "P2", "more_useful": "left"},
            {"pair": "P3", "more_useful": "tie"}, {"pair": "P4", "more_useful": ""}]
    out = ls.u1_summary(manifest, rows)
    assert (out["win"], out["tie"], out["loss"], out["unanswered"]) == (1, 1, 1, 1)
    assert out["win_rate"] == pytest.approx(1 / 3) and out["lo"] < out["win_rate"] < out["hi"]
    with pytest.raises(ValueError):
        ls.u1_summary(manifest, [{"pair": "P1", "more_useful": "both"}])


# ---------------------------------------------------------------- review round 1 fixes

def test_a_sentence_flagged_by_two_classes_is_drawn_from_its_rarest_class_with_its_true_probability():
    items = {}
    for k in range(4):
        case = f"m{k}"
        items[f"{case}.json"] = _item(case, [_attempt(case, 1, flagged={0: ["W1.entity", "W1.rare"] if k == 0 else ["W1.entity"],
                                                                      1: ["W1.entity"]})])
    frame = ls.extract_frame(items, _tables)
    both = next(r for r in frame if r["classes"] == ["W1.entity", "W1.rare"])
    for seed in range(5):
        drawn = ls.draw(frame, "dev", seed, quotas=dict(ls.QUOTAS["dev"], B=3))
        hit = [r for r in drawn if r["key"] == both["key"]]
        assert hit and hit[0]["group"] == "W1.rare" and hit[0]["p"] == 1.0
        entity = [r for r in drawn if r["stratum"] == "B" and r["group"] == "W1.entity"]
        assert all(r["p"] == pytest.approx(len(entity) / 7) for r in entity)       # 7 sentences only W1.entity


def test_an_unfinished_stratum_publishes_no_metrics_for_it():
    manifest = {"split": "dev", "seed": 1, "items": {
        "I1": {"stratum": "B", "classes": ["W1.number"], "p": 1.0, "score": 0.5, "case_id": "r"},
        "I2": {"stratum": "B", "classes": ["W1.number"], "p": 1.0, "score": 0.5, "case_id": "r"},
        "I3": {"stratum": "A", "classes": [], "p": 1.0, "score": 0.5, "case_id": "a"},
        "I4": {"stratum": "C", "classes": [], "p": 1.0, "score": 0.5, "case_id": "c"}}}
    rows = [{"item": "I1", "label": "supported"}, {"item": "I2", "label": ""}, {"item": "I3", "label": "supported"},
            {"item": "I4", "label": "unsupported"}]
    out = ls.metrics_report(manifest, rows)
    assert out["strata"] == {"A": {"sampled": 1, "labeled": 1}, "B": {"sampled": 2, "labeled": 1}, "C": {"sampled": 1, "labeled": 1}}
    assert out["gates"] == "unlabeled" and out["recall"] == "unlabeled" and out["nli"] == "unlabeled"
    assert out["false_accept"] != "unlabeled" and out["false_accept"]["reports"] == 1


def test_per_class_recall_needs_ten_errors_of_that_class_too():
    spec = [("wrong-number-or-name", "B", ["W1.number"], 1.0, 0.5, "r")] * 10 + [("wrong-number-or-name", "B", ["W2.x"], 1.0, 0.5, "r")] * 2
    by = ls.recall(_joined(spec))["wrong-number-or-name"]["by_class"]
    assert by["W1.number"]["estimate"] == pytest.approx(10 / 12) and by["W2.x"] == "insufficient"


def test_reliability_joins_the_relabel_sheet_to_the_first_labels_through_the_origin_map():
    first = [{"item": "I1", "label": "supported", "unsure": "Y"}, {"item": "I2", "label": "unsupported", "unsure": ""},
             {"item": "I3", "label": "supported", "unsure": ""}]
    second = [{"item": "R1", "label": "supported", "unsure": ""}, {"item": "R2", "label": "supported", "unsure": ""},
              {"item": "R3", "label": "", "unsure": ""}]
    origin = {"R1": "I1", "R2": "I2", "R3": "I3"}
    out = ls.reliability(first, second, origin)
    assert out["agreement"]["n"] == 2 and out["agreement"]["percent"] == 0.5
    assert out["unsure_share"] == pytest.approx(1 / 3) and out["unanswered"] == 1


def test_acceptance_from_the_run_record_counts_cases():
    record = {"dev": {"accepted": 6, "cases": {f"d{k}": {} for k in range(20)}}, "held_out": {"accepted": 5, "cases": 20}}
    out = ls.acceptance_from_record(record)
    assert out["all"]["accepted"] == 11 and out["all"]["cases"] == 40


def test_snapshot_relabel_and_metrics_commands_work_on_files(tmp_path):
    built = _build()
    ls.write_csv(tmp_path / "dev_sheet.csv", built["sheet"], ls.SHEET_FIELDS)
    (tmp_path / "dev_manifest.json").write_text(json.dumps(built["manifest"]), encoding="utf-8")
    rows = ls.read_csv(tmp_path / "dev_sheet.csv")
    for r in rows:
        r["label"] = "supported"
    ls.write_csv(tmp_path / "dev_sheet.csv", rows, ls.SHEET_FIELDS)
    assert ls.cmd_snapshot(tmp_path, "dev", "2026-11-06") == len(rows)
    report = ls.cmd_metrics(tmp_path, "dev", record=None)
    assert report["labels"]["labeled"] == len(rows) and "reliability" not in report
    n = ls.cmd_relabel(tmp_path, "dev", "2026-11-08")
    assert n == math.ceil(0.1 * len(rows))
    assert ls.cmd_relabel(tmp_path, "dev", "2026-11-06") == 0           # nothing was labeled on an earlier day
    re_rows = ls.read_csv(tmp_path / "dev_relabel.csv")
    for r in re_rows:
        r["label"] = "supported"
    ls.write_csv(tmp_path / "dev_relabel.csv", re_rows, ls.SHEET_FIELDS)
    assert ls.cmd_metrics(tmp_path, "dev", record=None)["reliability"]["agreement"]["percent"] == 1.0


def test_the_pairs_sheet_with_answers_is_not_overwritten(tmp_path):
    pairs = tmp_path / "dev_pairs.csv"
    ls.write_csv(pairs, [{"pair": "P1", "left": "a", "right": "b", "more_useful": "left", "note": ""}], ls.PAIR_FIELDS)
    with pytest.raises(SystemExit):
        ls.guard_no_answers(pairs, "more_useful")
    ls.guard_no_answers(tmp_path / "missing.csv", "label")
