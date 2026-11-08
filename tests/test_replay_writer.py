"""D60: the estimated suffix normalization exists only in offline replay."""
import ast
from pathlib import Path

from evals import replay_writer as replay
from agents import fact_table as ft
from test_fact_table import document


def test_strict_and_estimate_are_separate_and_ambiguity_fails():
    table = ft.build_fact_table(document())
    wrong = "starters.away_starter.thresholds.control"
    assert replay.map_path(wrong, table, estimated=False) is None
    result = replay.map_path(wrong, table, estimated=True)
    assert result == table.id_for_path("starters.away_starter.sample.thresholds.control")
    assert replay.map_path("season_summary.era", table, estimated=True) is None
    assert replay.map_path("starters.away_starter.nonsense.era_number", table, estimated=True) == table.id_for_path("starters.away_starter.season_summary.era_number")


def test_harness_never_imports_replay_or_normalization():
    root = Path(__file__).resolve().parents[1]
    for file in [*(root / "agents").glob("*.py"), root / "evals/run_b1.py"]:
        tree = ast.parse(file.read_text(encoding="utf-8"))
        imports = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        assert not any("replay_writer" in n for n in imports), file
    table = ft.build_fact_table(document())
    assert table.id_for_path("starters.away_starter.thresholds.control") is None


def test_numeric_twin_lineage_is_declared_only_for_run_two():
    table = ft.build_fact_table(document())
    path = "starters.away_starter.season_summary.era"
    assert replay.map_path(path, table, run=2) == table.id_for_path(path + "_number")
    assert replay.map_path(path, table, run=4) == table.id_for_path(path)
    assert replay.map_path("starters.away_starter.season_summary.innings", table, run=2) == table.id_for_path("starters.away_starter.season_summary.innings")


def test_estimate_never_changes_valid_paths_values_or_guesses_a_subject():
    table = ft.build_fact_table(document())
    for path in ("venue", "teams.away.offense_profile.bb_rate_vs_hand", "starters.home_starter.name"):
        assert replay.map_path(path, table, estimated=True) == replay.map_path(path, table, estimated=False)
    assert replay.map_path("starters.unknown.thresholds.control", table, estimated=True) is None
    assert replay.map_path("pitch_mix.99.away_starter.overall", table, estimated=True) is None


def test_reason_counts_exclude_mapping_and_separate_affected_sentences():
    from agents import writer_checks as wc
    candidate = {"headline": {"text": "missing fact"}, "summary_lines": [], "sections": {k: [] for k in wc.SECTION_KEYS}}
    rows = [{"original_candidate": candidate, "estimated": {"unmappable": [{"sentence_index": 0}], "gate_findings": [
        {"check": "REPLAY.unmappable", "sentence": 0}, {"check": "W1.number", "sentence": "missing fact"},
        {"check": "W1.authority", "sentence": "independent fact"}, {"check": "W1.authority", "sentence": "another independent fact"}]}}]
    assert replay.rejection_counts(rows, "estimated") == [
        {"check": "W1.authority", "findings": 2, "candidates": 1}, {"check": "W1.number", "findings": 1, "candidates": 1}]
    assert replay.rejection_counts(rows, "estimated", mapped_only=True) == [{"check": "W1.authority", "findings": 2, "candidates": 1}]


def test_missing_original_citations_are_unmappable_and_excluded_from_mapped_counts():
    import json
    from agents import writer_checks as wc
    record = json.loads((replay.ROOT / "evals/data/writer/instrument-replay.json").read_text(encoding="utf-8"))
    row = next(r for r in record["candidates"] if (r["run"],r["case"],r["attempt"]) == (2,"opener-824280",2))
    candidate = row["original_candidate"]
    empty = {i for i,s in enumerate(wc._all_sentences(candidate)) if not s["evidence"]}
    assert len(empty) == 4
    doc = document(row["case"])
    for estimated in (False, True):
        checked = replay.recheck(candidate, doc, wc.report_length(candidate), run=2, estimated=estimated)
        assert not checked["mapping_complete"] and not checked["accepted"]
        missing = [m for m in checked["unmappable"] if m["reason"] == "missing_citation"]
        assert {m["sentence_index"] for m in missing} == empty
        texts = {wc._all_sentences(candidate)[i]["text"] for i in empty}
        clean = replay.rejection_counts([{"original_candidate":candidate,"estimated":checked}], "estimated", mapped_only=True)
        expected = sum(f["check"] != "REPLAY.unmappable" and f["sentence"] not in texts for f in checked["gate_findings"])
        assert sum(r["findings"] for r in clean) == expected
        assert all(f["sentence"] in empty for f in checked["gate_findings"] if f["check"] == "REPLAY.unmappable" and f["token"] is None)


def test_saved_replay_covers_all_candidates_and_preserves_real_errors():
    import json
    from collections import Counter
    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / "evals/data/writer/instrument-replay.json").read_text(encoding="utf-8"))
    assert record["instrument"]["guide_sha256"] == replay.lw.guide_sha256()
    assert all(replay.sha(root / name) == digest for name, digest in record["instrument"]["sources"].items())
    rows = record["candidates"]
    assert Counter(r["run"] for r in rows) == {2: 20, 3: 2, 4: 12}
    assert len(record["transport_only"]) == 1 and record["gemini_calls"] == 0 and record["sources_unchanged"]
    for mode in ("strict", "estimated"):
        assert sum(not r[mode]["accepted"] for r in rows) == record["totals"][mode]["rejected"]
        assert sum(any(f["check"] == "W17.structure" for f in r[mode]["gate_findings"]) for r in rows) == 5
        for row in rows:
            result = row[mode]
            assert result["accepted"] == (not result["gate_findings"])
            if result["candidate_fact_ids"] is not None:
                from agents import writer_checks as wc
                assert [s["text"] for s in wc._all_sentences(row["original_candidate"])] == [s["text"] for s in wc._all_sentences(result["candidate_fact_ids"])]
        wrong = next(r for r in rows if (r["run"],r["case"],r["attempt"]) == (4,"postseason-849842",2))
        official = next(r for r in rows if (r["run"],r["case"],r["attempt"]) == (4,"limited-825104",1))
        assert any(f["check"] == "W1.number" and f["token"] == "10.4" for f in wrong[mode]["gate_findings"])
        assert any(f["check"] == "W1.authority" for f in official[mode]["gate_findings"])
