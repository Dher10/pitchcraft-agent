"""The provisional NLI calibration harness: dev only, deterministic, and its artifact can never admit anything."""

from __future__ import annotations

from pathlib import Path

import pytest

from agents import nli_admission as na
from agents import writer_input as wi
from evals import build_packets as bp
from evals import nli_calibration as nc

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"
CONTROL = Path(__file__).resolve().parents[1] / "evals" / "data" / "writer" / "positive_control.json"
CASE = "veteran-824027"


@pytest.fixture(scope="module")
def doc():
    return wi.build_writer_input(bp.load_dev_packet(DATASET, CASE), bp.load_dev_findings(DATASET, CASE), wi.load_glossary(DATASET / "glossary.json"))


def test_the_dataset_refuses_a_case_that_is_not_dev():
    sealed = {c["id"]: c["split"] for c in __import__("json").loads((DATASET / "split.json").read_text(encoding="utf-8"))["cases"]}
    test_id = next(i for i, side in sealed.items() if side == "test")

    with pytest.raises(ValueError):
        nc.build_dataset(DATASET, CONTROL, [test_id])


def test_auto_paths_finds_the_values_a_sentence_states(doc):
    paths = nc.auto_paths(doc, "Kyle Freeland has allowed 12 home runs over 202 batters faced.")

    assert "starters.away_starter.sample.rates.batters_faced" in paths and "starters.away_starter.sample.rates.home_runs" in paths


def test_perturbations_change_the_sentence_and_cover_the_kinds_the_plan_names(doc):
    text = "Kyle Freeland has an 8.08 earned run average over the 2026 regular season through May 31, against left-handed hitters, and shows solid command."

    kinds = dict(nc.perturbations(text, doc))

    assert {"quantity", "flip", "scope", "unsupported", "cause"} <= set(kinds) and all(t != text for t in kinds.values())
    assert "8.08" not in kinds["quantity"] and "Jul 31" in kinds["scope"] and "because" in kinds["cause"]
    swapped = dict(nc.perturbations("José Soriano shows below-average command.", doc))
    assert "Kyle Freeland" in swapped["subject"]


def test_the_dataset_has_positives_from_the_control_and_the_rules_writer_and_labelled_negatives():
    pairs = nc.build_dataset(DATASET, CONTROL, ["veteran-824027", "limited-823836"])

    assert {p["source"] for p in pairs} == {"positive_control", "rules_writer"}
    assert sum(p["label"] == 1 for p in pairs) > 20 and sum(p["label"] == 0 for p in pairs) > 20
    assert all(p["premise"] and len(p["premise"]) <= 2400 and len(p["text"]) <= 300 for p in pairs)
    assert pairs == nc.build_dataset(DATASET, CONTROL, ["veteran-824027", "limited-823836"])  # deterministic


def test_scoring_batches_and_a_missing_score_is_none():
    pairs = [{"premise": "p", "text": f"t{i}", "label": i % 2, "kind": "positive" if i % 2 else "quantity", "source": "x"} for i in range(70)]
    sizes = []

    def scorer(cache, batch, python=None, timeout=60):
        sizes.append(len(batch))
        return None if len(sizes) == 2 else [0.9] * len(batch)

    nc.score_pairs(pairs, "c", None, scorer=scorer)

    assert sizes == [32, 32, 6] and sum(p["score"] is None for p in pairs) == 32


def test_the_summary_counts_rates_and_the_negatives_that_were_wrongly_entailed():
    pairs = [{"label": 1, "kind": "positive", "source": "positive_control", "score": s} for s in (0.99, 0.95, 0.4)]
    pairs += [{"label": 0, "kind": "quantity", "source": "x", "score": s} for s in (0.01, 0.95)] + [{"label": 0, "kind": "cause", "source": "x", "score": None}]

    summary = nc.summarize(pairs)

    assert summary["pairs"] == 6 and summary["scored"] == 5 and summary["positives"] == 3 and summary["negatives"] == 2
    row = next(r for r in summary["table"] if r["threshold"] == 0.9)
    assert row["tpr"] == pytest.approx(2 / 3) and row["tnr"] == 0.5
    assert summary["by_kind_of_negative"]["quantity"] == {"n": 2, "wrongly_entailed_at_0.9": 1}
    assert summary["recall_by_source"] == {"positive_control": {"0.5": 0.667, "0.8": 0.667, "0.9": 0.667, "0.95": 0.667, "0.99": 0.333}}


def test_the_artifact_is_synthetic_names_what_is_missing_and_can_never_admit():
    artifact = nc.artifact(nc.summarize([]))

    assert artifact["labels"] == "synthetic" and artifact["human_labels"] == 0 and artifact["admission_allowed"] is False and artifact["threshold"] is None
    assert any("no human entailment labels" in m for m in artifact["missing"]) and any("no accepted B1 model output" in m for m in artifact["missing"])
    assert na.calibration_ok({**artifact, "threshold": 0.9}) is False


def test_the_label_pool_holds_unlabelled_dev_model_sentences_with_premises(tmp_path):
    import json
    import test_positive_control as tpc

    case, doc, candidate = tpc.load()
    items = tmp_path / "items"
    items.mkdir()
    item = {"case_id": case, "attempts": [{"content_attempt": 1, "model": "m", "candidate": candidate}]}
    (items / f"{case}.json").write_text(json.dumps(item), encoding="utf-8")

    pool = nc.label_pool(DATASET, [items])

    assert pool and all(p["label"] is None and p["premise"] and p["source"] == "model" and not p["text"].startswith("Watch") for p in pool)
    assert nc.label_pool(DATASET, [items], cases=["limited-823836"]) == []
