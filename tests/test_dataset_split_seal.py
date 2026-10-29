"""P2.4 sealed split: ids and hashes only, a pinned lock, and no dev tool reads test outputs (plan section 3)."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path

import pytest

from evals import build_dataset as bd
from evals import seal
from tests.test_dataset_selection import COLLECTION, pool

REPO = Path(__file__).resolve().parents[1]


def made(tmp_path):
    sel = bd.select(pool(), COLLECTION)
    hashes = {c.case_id: hashlib.sha256(c.case_id.encode()).hexdigest() for s in bd.STRATA for c in sel.cases[s]}
    bd.write_split(tmp_path, sel, hashes)
    return sel, hashes


def test_the_split_file_holds_case_ids_and_hashes_only(tmp_path):
    made(tmp_path)
    record = json.loads((tmp_path / "split.json").read_text(encoding="utf-8"))

    assert set(record) == {"version", "seed", "cases"}
    assert len(record["cases"]) == 40
    assert all(set(c) == {"id", "stratum", "split", "sha256"} for c in record["cases"])
    text = (tmp_path / "split.json").read_text(encoding="utf-8")
    for forbidden in ("pitcher", "game_pk", "official_date", "traits", "starter"):
        assert forbidden not in text


def test_the_lock_pins_the_split_and_any_change_fails(tmp_path):
    made(tmp_path)
    bd.verify_split_lock(tmp_path)  # control: untouched

    path = tmp_path / "split.json"
    original = path.read_bytes()
    record = json.loads(original)
    record["cases"][0]["split"] = "test" if record["cases"][0]["split"] == "dev" else "dev"  # move one case across
    path.write_text(json.dumps(record, indent=1), encoding="utf-8")
    with pytest.raises(bd.SplitChanged):
        bd.verify_split_lock(tmp_path)

    path.write_bytes(original)
    bd.verify_split_lock(tmp_path)  # restoring the bytes passes again

    (tmp_path / "split.lock").unlink()
    with pytest.raises(bd.SplitChanged):
        bd.verify_split_lock(tmp_path)  # a split with no lock is not sealed


def test_a_lock_without_a_split_fails_too(tmp_path):
    (tmp_path / "split.lock").write_text("0" * 64 + "\n", encoding="utf-8")
    with pytest.raises(bd.SplitChanged):
        bd.verify_split_lock(tmp_path)


def test_write_split_refuses_to_overwrite_a_sealed_split(tmp_path):
    sel, hashes = made(tmp_path)
    with pytest.raises(bd.SplitChanged):
        bd.write_split(tmp_path, sel, hashes)


def test_the_committed_split_is_unchanged():
    """The one that fails if the committed split is edited after its commit (owner amendment 5)."""

    data = REPO / "evals" / "data"
    if (data / "split.json").exists() or (data / "split.lock").exists():
        bd.verify_split_lock(data)


# --- sealing --------------------------------------------------------------------------------------------


def outputs(tmp_path):
    for name in ("dev", "test"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "case-1.json").write_text(json.dumps({"finding": name}), encoding="utf-8")
    return tmp_path


def test_dev_tools_and_reports_cannot_open_test_outputs(tmp_path):
    root = outputs(tmp_path)
    assert seal.read_outputs(root, "dev", purpose="dev_tool") == {"case-1.json": {"finding": "dev"}}  # control
    for purpose in ("dev_tool", "report", "label"):
        with pytest.raises(seal.Sealed):
            seal.read_outputs(root, "test", purpose=purpose)
    with pytest.raises(ValueError):
        seal.read_outputs(root, "test", purpose="anything else")  # unknown purposes are not a way around it


def test_test_outputs_are_visible_as_hashes_only_and_open_only_after_the_freeze(tmp_path):
    root = outputs(tmp_path)
    digests = seal.hashes(root, "test")
    assert digests == {"case-1.json": hashlib.sha256((root / "test" / "case-1.json").read_bytes()).hexdigest()}
    with pytest.raises(seal.Sealed):
        seal.read_outputs(root, "test", purpose="evaluation")  # not frozen yet
    (root / "FROZEN").write_text(seal.freeze_line(root), encoding="utf-8")
    assert seal.read_outputs(root, "test", purpose="evaluation") == {"case-1.json": {"finding": "test"}}
    (root / "test" / "case-1.json").write_text('{"finding": "edited"}', encoding="utf-8")
    with pytest.raises(seal.Sealed):  # a frozen set that changed is sealed again
        seal.read_outputs(root, "test", purpose="evaluation")


def test_nothing_else_in_the_repo_opens_a_test_output_directory():
    """Static guard: only evals/seal.py builds the path of the test outputs."""

    offenders = []
    for folder in ("evals", "agents", "scripts", "data_pipeline"):
        for path in (REPO / folder).rglob("*.py"):
            if path.name == "seal.py":
                continue
            text = path.read_text(encoding="utf-8")
            if "outputs/test" in text.replace("\\", "/") or '"test" /' in text or "/ \"test\"" in text:
                offenders.append(str(path.relative_to(REPO)))
    assert offenders == []
