"""D58: provider citations are IDs; only code may bind them to evidence."""
from copy import deepcopy
from pathlib import Path

import pytest

from agents import fact_table as ft, writer_input as wi, llm_report_writer as lw
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals/data/dataset"


def document(case="postseason-849842"):
    return wi.build_writer_input(bp.load_dev_packet(DATASET, case), bp.load_dev_findings(DATASET, case),
                                 wi.load_glossary(DATASET / "glossary.json"))


def test_deterministic_closed_table_with_complete_scope():
    doc = document()
    table = ft.build_fact_table(doc)
    assert table == ft.build_fact_table(deepcopy(doc))
    assert all(set(row) == {"id", "subject", "field", "value", "scope"} for row in table.rows)
    path = "starters.away_starter.sample.arsenal.scope.label"
    fact_id = table.id_for_path(path)
    row = next(r for r in table.rows if r["id"] == fact_id)
    assert "2026-09-29" in str(row["value"])
    assert any(e["path"].endswith(".through") for e in ft.resolve_fact_ids([fact_id], table))


@pytest.mark.parametrize("bad", [["F9999"], [{"path": "venue", "value": "invented"}], ["F001", 1]])
def test_unknown_or_legacy_citations_never_resolve(bad):
    with pytest.raises(ft.UnknownFact):
        ft.resolve_fact_ids(bad, ft.build_fact_table(document()))


def test_limit_fact_dependency_closure_is_conditional_and_same_owner():
    doc = document("postseason-849849")
    path = "starters.away_starter.sample.limited.control"
    table = ft.build_fact_table(doc)
    proof = ft.resolve_fact_ids([table.id_for_path(path)], table)
    assert {e["path"] for e in proof} >= {path, "starters.away_starter.sample.thresholds.control",
        "starters.away_starter.sample.rates.batters_faced", "starters.away_starter.pitching_profile.command_label"}
    assert all("home_starter" not in e["path"] for e in proof)
    doc["starters"]["away_starter"]["sample"]["rates"]["batters_faced"] = 170
    table = ft.build_fact_table(doc)
    assert len(ft.resolve_fact_ids([table.id_for_path(path)], table)) == 1


def test_all_dev_request_tables_fit_without_dropping_facts():
    for case in bp.dev_case_ids(DATASET):
        doc = document(case)
        table = ft.build_fact_table(doc)
        data = lw.build_body(doc, 3000)["contents"][0]["parts"][0]["text"]
        import json
        visible = json.loads(data)["DATA"]
        assert visible["columns"] == ["id", "subject", "field", "value", "scope"]
        assert len(visible["facts"]) == len(table.rows)
        assert "path" not in lw.SCHEMA["properties"]["headline"]["properties"]["evidence"]["items"]


def test_fact_id_premise_is_rendered_bound_evidence_with_cutoff_and_cause():
    from agents import fact_renderer as fr
    doc = document("postseason-849849")
    table = ft.build_fact_table(doc)
    scope = table.id_for_path("starters.away_starter.sample.arsenal.scope.label")
    limited = table.id_for_path("starters.away_starter.sample.limited.control")
    evidence = ft.resolve_fact_ids([scope, limited], table)
    premise, problem = fr.premise_for(doc, [e["path"] for e in evidence])
    assert problem is None
    assert "2026-09-28" in premise and "Hagen Smith" in premise
    assert "110" in premise and "170" in premise and "because" in premise
    assert "{" not in premise and "F001" not in premise and "starters." not in premise


def test_provider_cannot_revert_to_paths_even_when_the_path_is_valid():
    doc = document()
    from agents import writer_checks as wc
    s = {"text": "The starters are listed.", "evidence": [{"path": "data_confidence.lineup_status", "value": "probable pitchers"}]}
    c = {"headline": s, "summary_lines": [s,s,s], "sections": {key: [s,s,s] if key == "watch" else [s] for key in wc.SECTION_KEYS}}
    _, detail = ft.resolve_candidate(c, doc)
    assert any(f["check"] == "W1.fact_id" for f in detail)
