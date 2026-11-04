"""The owner's save-and-check round trip on a Spanish-locale Windows PC (Excel semicolons, BOM, CRLF).

Synthetic sheets only. `check` validates a saved sheet and writes nothing.
"""
import json
import os

import pytest

from evals import labeling_sheet as ls
from tests.test_labeling_sheet import GLOSSARY, _build, _tables, _world


def _semicolon_excel(rows, fields, bom=True, eol="\r\n"):
    """What Spanish-locale Excel writes for 'CSV UTF-8': BOM, semicolons, CRLF, quotes only where needed."""

    def cell(v):
        v = "" if v is None else str(v).replace("\n", "\r\n" if eol == "\r\n" else "\n")
        return '"' + v.replace('"', '""') + '"' if any(c in v for c in ';"\r\n') else v

    lines = [";".join(fields)] + [";".join(cell(r.get(f, "")) for f in fields) for r in rows]
    return (("﻿" if bom else "") + eol.join(lines) + eol).encode("utf-8")


def _setup(tmp_path):
    built = _build()
    (tmp_path / "dev_manifest.json").write_text(json.dumps(built["manifest"]), encoding="utf-8")
    ls.write_csv(tmp_path / "dev_sheet.csv", built["sheet"], ls.SHEET_FIELDS)
    return built


def _save(tmp_path, rows, **kw):
    (tmp_path / "dev_sheet.csv").write_bytes(_semicolon_excel(rows, ls.SHEET_FIELDS, **kw))


# ---------------------------------------------------------------- reader

def test_reader_accepts_bom_semicolons_and_windows_line_endings(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r) for r in built["sheet"]]
    rows[0].update(label="supported", unsure="Y", note="fine; really")
    _save(tmp_path, rows)
    back = ls.read_csv(tmp_path / "dev_sheet.csv")
    assert [r["item"] for r in back] == [r["item"] for r in rows]
    assert back[0]["label"] == "supported" and back[0]["note"] == "fine; really"
    assert back[0]["cited_facts"] == rows[0]["cited_facts"].replace("\n", "\n")  # embedded line breaks survive


@pytest.mark.parametrize("delimiter", [",", ";", "\t"])
def test_reader_sniffs_the_delimiter_from_the_header(tmp_path, delimiter):
    path = tmp_path / "x.csv"
    path.write_bytes(f"item{delimiter}label{delimiter}note\r\nI1{delimiter}supported{delimiter}a b\r\n".encode("utf-8"))
    assert ls.read_csv(path) == [{"item": "I1", "label": "supported", "note": "a b"}]


def test_reader_falls_back_to_windows_1252_and_normalizes_headers(tmp_path):
    path = tmp_path / "x.csv"
    path.write_bytes(" Item ;LABEL;Note\r\nI1;supported;señor\r\n".encode("cp1252"))
    assert ls.read_csv(path) == [{"item": "I1", "label": "supported", "note": "señor"}]


def test_labels_are_matched_after_trimming_and_lowercasing_only():
    assert ls.normalize_label(" Supported ") == "supported"
    assert ls.normalize_label("Wrong-Number-Or-Name") == "wrong-number-or-name"
    assert ls.normalize_label("supportd") == "supportd"          # still invalid, never guessed


def test_labels_join_on_item_only_and_ignore_every_other_column(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r) for r in built["sheet"]]
    for r in rows:
        r["label"] = " Supported"
    rows[0]["sentence"] = "Excel changed this ’quote’ and the number 2,5"
    rows[0]["case_group"] = "G99"
    rows[0]["cited_facts"] = ""
    _save(tmp_path, rows)
    joined, summary = ls.join_labels(built["manifest"], ls.read_csv(tmp_path / "dev_sheet.csv"))
    assert summary["labeled"] == len(rows) and all(j["label"] == "supported" for j in joined)
    assert joined[0]["classes"] == built["manifest"]["items"][rows[0]["item"]]["classes"]


def test_a_duplicated_item_is_refused_by_the_join():
    manifest = {"items": {"I1": {"stratum": "B"}}}
    rows = [{"item": "I1", "label": "supported"}, {"item": "I1", "label": "unsupported"}]
    with pytest.raises(ValueError):
        ls.join_labels(manifest, rows)


# ---------------------------------------------------------------- check

def _snapshot(path):
    return {p.name: (p.stat().st_mtime_ns, p.read_bytes()) for p in path.iterdir()}


def test_check_counts_labeled_unlabeled_and_invalid_values_per_column(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r) for r in built["sheet"]]
    rows[0].update(label="supported")
    rows[1].update(label="Unsupported", unsure="Y")
    rows[2].update(label="supportd", unsure="maybe")
    rows[3].update(label="not-a-claim", note="x")
    _save(tmp_path, rows)
    before = _snapshot(tmp_path)
    text, code = ls.cmd_check(tmp_path, "dev")
    assert _snapshot(tmp_path) == before                   # writes nothing
    report = ls.check_report(tmp_path, "dev")["sheet"]
    n = len(rows)
    assert report["rows"] == n and report["missing_ids"] == [] and report["duplicate_ids"] == [] and report["unknown_ids"] == []
    assert report["columns"]["label"] == {"labeled": 3, "unlabeled": n - 4, "invalid": [(rows[2]["item"], "supportd")]}
    assert report["columns"]["unsure"]["invalid"] == [(rows[2]["item"], "maybe")]
    assert report["columns"]["unsure"]["labeled"] == 1          # Y marks; "maybe" is invalid
    assert report["columns"]["note"]["labeled"] == 1
    assert code == 2 and "supportd" in text                     # invalid values: fix them, but ids are fine


def test_check_is_clean_when_everything_is_valid(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r, label="supported") for r in built["sheet"]]
    _save(tmp_path, rows)
    text, code = ls.cmd_check(tmp_path, "dev")
    assert code == 0 and "OK" in text


@pytest.mark.parametrize("damage", ["missing", "duplicate", "altered", "extra"])
def test_check_refuses_when_item_ids_are_missing_duplicated_or_altered(tmp_path, damage):
    built = _setup(tmp_path)
    rows = [dict(r, label="supported") for r in built["sheet"]]
    first = rows[0]["item"]
    if damage == "missing":
        rows = rows[1:]
    elif damage == "duplicate":
        rows.append(dict(rows[1]))
    elif damage == "altered":
        rows[0]["item"] = first.lower()                      # I123456 -> i123456 is a different id
    elif damage == "extra":
        rows.append(dict(rows[0], item="I000001"))
    _save(tmp_path, rows)
    report = ls.check_report(tmp_path, "dev")["sheet"]
    assert {"missing": report["missing_ids"], "duplicate": report["duplicate_ids"],
            "altered": report["unknown_ids"], "extra": report["unknown_ids"]}[damage]
    text, code = ls.cmd_check(tmp_path, "dev")
    assert code == 1 and "REFUSED" in text


def test_check_ignores_but_reports_an_excel_altered_sentence_cell(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r, label="supported") for r in built["sheet"]]
    rows[0]["sentence"] = rows[0]["sentence"].replace(".", ",") + " "
    _save(tmp_path, rows)
    report = ls.check_report(tmp_path, "dev")["sheet"]
    assert report["readonly_cells_changed"] == 1
    text, code = ls.cmd_check(tmp_path, "dev")
    assert code == 0 and "ignored" in text


def test_check_refuses_when_the_label_or_item_column_is_gone(tmp_path):
    built = _setup(tmp_path)
    (tmp_path / "dev_sheet.csv").write_bytes(_semicolon_excel(built["sheet"], ["item", "sentence"]))
    text, code = ls.cmd_check(tmp_path, "dev")
    assert code == 1 and "label" in text


def test_check_covers_the_pairs_and_the_relabel_sheet_when_they_exist(tmp_path):
    built = _setup(tmp_path)
    pairs = ls.build_pairs(_world(), "dev")
    (tmp_path / "dev_pairs_manifest.json").write_text(json.dumps(pairs["manifest"]), encoding="utf-8")
    prow = [dict(r) for r in pairs["sheet"]]
    prow[0]["more_useful"] = "Left"
    prow[1]["more_useful"] = "both"
    (tmp_path / "dev_pairs.csv").write_bytes(_semicolon_excel(prow, ls.PAIR_FIELDS))
    _save(tmp_path, [dict(r, label="supported") for r in built["sheet"]])
    full = ls.check_report(tmp_path, "dev")
    assert full["pairs"]["columns"]["more_useful"] == {"labeled": 1, "unlabeled": len(prow) - 2, "invalid": [(prow[1]["pair"], "both")]}
    assert "relabel" not in full


def test_a_checked_sheet_still_feeds_the_metrics(tmp_path):
    built = _setup(tmp_path)
    _save(tmp_path, [dict(r, label="supported") for r in built["sheet"]])
    report = ls.cmd_metrics(tmp_path, "dev", record=None)
    assert report["labels"]["labeled"] == len(built["sheet"])


def test_main_check_returns_the_exit_code_and_writes_nothing(tmp_path, capsys):
    built = _setup(tmp_path)
    _save(tmp_path, [dict(r, label="supported") for r in built["sheet"]][1:])
    before = _snapshot(tmp_path)
    assert ls.main(["check", "--split", "dev", "--out", str(tmp_path)]) == 1
    assert "REFUSED" in capsys.readouterr().out
    assert _snapshot(tmp_path) == before


def test_relabel_shows_the_original_sentence_even_if_excel_altered_the_sheet(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r, label="supported") for r in built["sheet"]]
    for r in rows:
        r["sentence"] = "ALTERED"
    _save(tmp_path, rows)
    ls.cmd_snapshot(tmp_path, "dev", "2026-11-06")
    assert ls.cmd_relabel(tmp_path, "dev", "2026-11-08") > 0
    shown = ls.read_csv(tmp_path / "dev_relabel.csv")
    assert all(r["sentence"] != "ALTERED" and r["sentence"] for r in shown)


def test_metrics_accept_the_same_pair_answers_check_accepts(tmp_path):
    built = _setup(tmp_path)
    pairs = ls.build_pairs(_world(), "dev")
    (tmp_path / "dev_pairs_manifest.json").write_text(json.dumps(pairs["manifest"]), encoding="utf-8")
    prow = [dict(r) for r in pairs["sheet"]]
    prow[0]["more_useful"] = "Left"
    prow[1]["more_useful"] = " TIE "
    prow[0]["pair"] = prow[0]["pair"] + " "
    (tmp_path / "dev_pairs.csv").write_bytes(_semicolon_excel(prow, ls.PAIR_FIELDS))
    _save(tmp_path, [dict(r, label="supported") for r in built["sheet"]])
    assert ls.cmd_check(tmp_path, "dev")[1] == 0
    u1 = ls.cmd_metrics(tmp_path, "dev", record=None)["u1"]
    assert u1["n"] == 2 and u1["tie"] == 1


def test_a_whitespace_only_cell_is_not_an_answer_for_the_overwrite_guard(tmp_path):
    path = tmp_path / "dev_sheet.csv"
    path.write_bytes(_semicolon_excel([{"item": "I1", "label": "  "}], ["item", "label"]))
    ls.guard_no_answers(path, "label")


def test_reliability_uses_the_same_normalization_as_check(tmp_path):
    built = _setup(tmp_path)
    rows = [dict(r, label="Supported") for r in built["sheet"]]
    rows[0]["item"] = rows[0]["item"] + " "
    _save(tmp_path, rows)
    ls.cmd_snapshot(tmp_path, "dev", "2026-11-06")
    assert ls.cmd_relabel(tmp_path, "dev", "2026-11-08") > 0
    origin = json.loads((tmp_path / "dev_relabel_manifest.json").read_text(encoding="utf-8"))["origin"]
    again = ls.read_csv(tmp_path / "dev_relabel.csv")
    for r in again:
        r["label"] = " supported "
    (tmp_path / "dev_relabel.csv").write_bytes(_semicolon_excel(again, ls.SHEET_FIELDS))
    assert ls.cmd_check(tmp_path, "dev")[1] == 0
    out = ls.cmd_metrics(tmp_path, "dev", record=None)["reliability"]
    assert out["agreement"]["n"] == len(origin) and out["agreement"]["percent"] == 1.0 and out["unanswered"] == 0


def test_reliability_and_snapshot_ignore_invalid_labels_and_refuse_duplicates():
    first = [{"item": "I1", "label": "supported", "unsure": ""}, {"item": "I2", "label": "typo", "unsure": ""}]
    second = [{"item": "R1", "label": "supported"}, {"item": "R2", "label": "supported"}]
    out = ls.reliability(first, second, {"R1": "I1", "R2": "I2"})
    assert out["agreement"]["n"] == 1
    assert ls.snapshot_log({}, first, "2026-11-06") == {"I1": "2026-11-06"}
    with pytest.raises(ValueError):
        ls.reliability(first, second + [{"item": "R1", "label": "supported"}], {"R1": "I1", "R2": "I2"})
    assert ls.reliability(first, [{"item": "R1", "label": "  "}], {"R1": "I1"})["unanswered"] == 1
