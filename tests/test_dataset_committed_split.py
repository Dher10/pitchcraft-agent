"""P2.4: the committed split of evals/data/dataset is sealed. These tests read only ids, sides and hashes."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import pytest

from evals import build_dataset as bd

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"


def test_the_committed_split_matches_its_lock():
    bd.verify_split_lock(DATASET)


def test_the_committed_split_is_twenty_and_twenty_with_five_per_side_in_each_stratum():
    cases = json.loads((DATASET / "split.json").read_text(encoding="utf-8"))["cases"]

    assert len(cases) == 40
    for stratum in bd.STRATA:
        assert sorted(c["split"] for c in cases if c["stratum"] == stratum) == ["dev"] * 5 + ["test"] * 5


def test_every_sealed_hash_is_the_hash_of_its_selection_record():
    from evals import collect as co

    sealed = {c["id"]: c["sha256"] for c in json.loads((DATASET / "split.json").read_text(encoding="utf-8"))["cases"]}
    records = json.loads((DATASET / "selection.json").read_text(encoding="utf-8"))["cases"]

    assert sealed == {r["case_id"]: co.case_hash(r) for r in records}


@pytest.mark.parametrize("target", ["split.json", "split.lock"])
def test_changing_the_committed_split_or_its_lock_by_one_byte_is_caught(tmp_path, target):
    shutil.copytree(DATASET, tmp_path / "d")
    path = tmp_path / "d" / target
    data = bytearray(path.read_bytes())
    data[10] = ord("0") if data[10] != ord("0") else ord("1")
    path.write_bytes(bytes(data))

    with pytest.raises(bd.SplitChanged):
        bd.verify_split_lock(tmp_path / "d")
