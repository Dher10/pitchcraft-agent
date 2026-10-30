"""P2.4 packets: the committed packet set of evals/data/dataset is frozen. These tests read ids, sides and hashes only."""

from __future__ import annotations

import json
from pathlib import Path

from evals import build_packets as bp
from evals import request_ledger as rl

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"


def manifest():
    return bp.read_manifest(DATASET)


def test_the_committed_set_verifies_against_its_manifest_and_lock():
    bp.verify_packet_set(DATASET)


def test_the_packet_set_equals_the_sealed_case_ids_exactly():
    sealed = [c["id"] for c in json.loads((DATASET / "split.json").read_text(encoding="utf-8"))["cases"]]

    assert len(sealed) == 40
    assert [e["id"] for e in manifest()["cases"]] == sealed


def test_both_sides_have_twenty_packets_and_twenty_findings():
    cases = manifest()["cases"]

    assert sorted(e["split"] for e in cases).count("dev") == 20 and sorted(e["split"] for e in cases).count("test") == 20
    assert all(len(e["packet_sha256"]) == 64 and len(e["findings_sha256"]) == 64 for e in cases)


def test_the_build_used_no_mlb_lookup_and_stayed_inside_every_ceiling():
    used = manifest()["requests"]

    assert used["mlb"] == 0
    for group, count in used.items():
        assert count <= rl.CEILINGS[group]


def test_every_case_records_its_cached_inputs():
    for entry in manifest()["cases"]:
        assert len(entry["inputs"]["schedule_sha256"]) == 64 and len(entry["inputs"]["history_sha256"]) == 2


def test_the_dev_reader_opens_dev_cases_and_refuses_the_test_side():
    ids = {e["id"]: e["split"] for e in manifest()["cases"]}
    dev = next(i for i, side in ids.items() if side == "dev")
    test = next(i for i, side in ids.items() if side == "test")

    assert bp.load_dev_packet(DATASET, dev)["id"] == dev
    try:
        bp.load_dev_packet(DATASET, test)
    except bp.TestSplitSealed:
        pass
    else:
        raise AssertionError("a test case was opened")
