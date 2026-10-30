"""P2.4 packets: the frozen packet set, its manifest and its seal.

The set must equal the sealed case ids exactly, every file must hash to what the manifest says, the manifest is pinned by
`packets.lock`, and the only way a tool reads a packet is by side: a test-split case id is refused by the dev reader.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from evals import build_packets as bp

SECRET = "TEST-SIDE-CONTENT-THAT-MUST-NEVER-BE-PRINTED"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_dataset(directory: Path) -> list[dict]:
    """A sealed split of four cases (two dev, two test) written the way `write_split` writes it."""

    cases = [
        {"id": "veteran-1", "stratum": "veteran", "split": "dev", "sha256": "a" * 64},
        {"id": "veteran-2", "stratum": "veteran", "split": "test", "sha256": "b" * 64},
        {"id": "limited-3", "stratum": "limited", "split": "dev", "sha256": "c" * 64},
        {"id": "limited-4", "stratum": "limited", "split": "test", "sha256": "d" * 64},
    ]
    text = json.dumps({"version": 1, "seed": "s", "cases": cases}, indent=1, sort_keys=True) + "\n"
    directory.mkdir(parents=True)
    (directory / "split.json").write_bytes(text.encode())
    (directory / "split.lock").write_bytes((sha(text.encode()) + "\n").encode())
    return cases


def built(case_id: str) -> bp.BuiltCase:
    text = SECRET if case_id in ("veteran-2", "limited-4") else "plain"
    return bp.BuiltCase(
        case_id=case_id,
        packet={"id": case_id, "text": text},
        findings={"matchup_headline": f"headline {case_id}"},
        live_game={},
        notes={"unsafe": None, "errors": [], "warnings": []},
    )


INPUTS = {cid: {"schedule": "s" * 64, "history": ["h" * 64, "i" * 64]} for cid in ("veteran-1", "veteran-2", "limited-3", "limited-4")}
REQUESTS = {"pitcher_statcast": 8, "savant_open_month": 6, "pitcher_hand": 0, "mlb": 0}


@pytest.fixture
def dataset(tmp_path):
    directory = tmp_path / "evals" / "data" / "dataset"
    make_dataset(directory)
    return directory


def freeze(directory, cases=("veteran-1", "veteran-2", "limited-3", "limited-4")):
    return bp.freeze(directory, [built(c) for c in cases], INPUTS, REQUESTS)


def test_freeze_writes_each_side_in_its_own_directory(dataset):
    freeze(dataset)

    for case_id, side in (("veteran-1", "dev"), ("limited-3", "dev"), ("veteran-2", "test"), ("limited-4", "test")):
        assert (dataset / "packets" / side / f"{case_id}.json").is_file()
        assert (dataset / "findings" / side / f"{case_id}.json").is_file()
    assert not (dataset / "packets" / "dev" / "veteran-2.json").exists()


def test_the_manifest_hashes_are_the_hashes_of_the_files(dataset):
    freeze(dataset)

    manifest = json.loads((dataset / "packets_manifest.json").read_text(encoding="utf-8"))
    assert [c["id"] for c in manifest["cases"]] == ["veteran-1", "veteran-2", "limited-3", "limited-4"]
    for entry in manifest["cases"]:
        side = entry["split"]
        assert entry["packet_sha256"] == sha((dataset / "packets" / side / f"{entry['id']}.json").read_bytes())
        assert entry["findings_sha256"] == sha((dataset / "findings" / side / f"{entry['id']}.json").read_bytes())
        assert entry["selection_sha256"] in {"a" * 64, "b" * 64, "c" * 64, "d" * 64}
    assert manifest["requests"] == REQUESTS
    assert manifest["split_lock"] == (dataset / "split.lock").read_text(encoding="ascii").strip()


def test_the_lock_is_the_hash_of_the_manifest_and_freeze_returns_it(dataset):
    returned = freeze(dataset)

    assert returned == sha((dataset / "packets_manifest.json").read_bytes())
    assert (dataset / "packets.lock").read_text(encoding="ascii").strip() == returned


def test_the_files_are_canonical_json(dataset):
    freeze(dataset)

    data = (dataset / "packets" / "dev" / "veteran-1.json").read_bytes()
    assert data == bp.canonical({"id": "veteran-1", "text": "plain"})
    assert data.endswith(b"\n")


def test_a_missing_case_stops_the_freeze_and_writes_nothing(dataset):
    with pytest.raises(bp.PacketSetMismatch, match="limited-4"):
        freeze(dataset, cases=("veteran-1", "veteran-2", "limited-3"))

    assert not (dataset / "packets").exists() and not (dataset / "packets_manifest.json").exists()


def test_a_case_outside_the_sealed_split_stops_the_freeze(dataset):
    with pytest.raises(bp.PacketSetMismatch, match="extra-9"):
        bp.freeze(dataset, [built(c) for c in ("veteran-1", "veteran-2", "limited-3", "limited-4", "extra-9")], INPUTS, REQUESTS)


def test_a_duplicate_case_stops_the_freeze(dataset):
    with pytest.raises(bp.PacketSetMismatch):
        freeze(dataset, cases=("veteran-1", "veteran-1", "veteran-2", "limited-3", "limited-4"))


def test_a_frozen_set_is_never_rewritten(dataset):
    freeze(dataset)

    with pytest.raises(bp.PacketSetChanged):
        freeze(dataset)


def test_freeze_checks_the_split_lock_first(dataset):
    data = bytearray((dataset / "split.json").read_bytes())
    data[10] ^= 1
    (dataset / "split.json").write_bytes(bytes(data))

    with pytest.raises(Exception):
        freeze(dataset)
    assert not (dataset / "packets").exists()


@pytest.mark.parametrize("where", [("public", "data"), ("evals", "live")])
def test_freeze_refuses_a_directory_inside_the_published_data(tmp_path, where):
    directory = tmp_path.joinpath(*where) / "dataset"
    make_dataset(directory)

    with pytest.raises(Exception, match="never writes"):
        freeze(directory)


# --- verifying a frozen set --------------------------------------------------------------------------------------


def frozen(dataset):
    freeze(dataset)
    return dataset


def test_a_frozen_set_verifies(dataset):
    bp.verify_packet_set(frozen(dataset))


@pytest.mark.parametrize("path", ["packets/dev/veteran-1.json", "packets/test/limited-4.json", "findings/dev/limited-3.json", "findings/test/veteran-2.json"])
def test_one_changed_byte_in_any_file_is_caught(dataset, path):
    frozen(dataset)
    target = dataset / path
    data = bytearray(target.read_bytes())
    data[3] ^= 1
    target.write_bytes(bytes(data))

    with pytest.raises(bp.PacketSetChanged, match=Path(path).stem):
        bp.verify_packet_set(dataset)


def test_a_deleted_file_is_caught(dataset):
    frozen(dataset)
    (dataset / "packets" / "test" / "veteran-2.json").unlink()

    with pytest.raises(bp.PacketSetChanged):
        bp.verify_packet_set(dataset)


def test_an_extra_file_is_caught(dataset):
    frozen(dataset)
    (dataset / "packets" / "dev" / "veteran-9.json").write_bytes(b"{}\n")

    with pytest.raises(bp.PacketSetMismatch, match="veteran-9"):
        bp.verify_packet_set(dataset)


def test_a_file_moved_to_the_other_side_is_caught(dataset):
    frozen(dataset)
    shutil.move(dataset / "packets" / "test" / "veteran-2.json", dataset / "packets" / "dev" / "veteran-2.json")

    with pytest.raises(bp.PacketSetMismatch):
        bp.verify_packet_set(dataset)


def test_an_edited_manifest_is_caught_by_the_lock(dataset):
    frozen(dataset)
    path = dataset / "packets_manifest.json"
    data = bytearray(path.read_bytes())
    data[5] ^= 1
    path.write_bytes(bytes(data))

    with pytest.raises(bp.PacketSetChanged, match="lock"):
        bp.verify_packet_set(dataset)


def test_a_manifest_for_another_split_is_caught(dataset):
    frozen(dataset)
    split = json.loads((dataset / "split.json").read_text(encoding="utf-8"))
    split["cases"][0]["sha256"] = "e" * 64
    text = json.dumps(split, indent=1, sort_keys=True) + "\n"
    (dataset / "split.json").write_bytes(text.encode())
    (dataset / "split.lock").write_bytes((sha(text.encode()) + "\n").encode())

    with pytest.raises(bp.PacketSetChanged, match="split"):
        bp.verify_packet_set(dataset)


# --- the seal -----------------------------------------------------------------------------------------------------


def test_the_dev_reader_returns_a_dev_packet(dataset):
    frozen(dataset)

    assert bp.load_dev_packet(dataset, "veteran-1") == {"id": "veteran-1", "text": "plain"}
    assert bp.dev_case_ids(dataset) == ["veteran-1", "limited-3"]


@pytest.mark.parametrize("case_id", ["veteran-2", "limited-4"])
def test_the_dev_reader_refuses_a_test_case_even_by_id(dataset, case_id):
    frozen(dataset)

    with pytest.raises(bp.TestSplitSealed):
        bp.load_dev_packet(dataset, case_id)
    with pytest.raises(bp.TestSplitSealed):
        bp.load_dev_findings(dataset, case_id)


def test_the_dev_reader_refuses_an_id_that_is_not_a_case_or_tries_a_path(dataset):
    frozen(dataset)

    for bad in ("nope", "../test/veteran-2", "dev/../../test/veteran-2", ""):
        with pytest.raises(bp.TestSplitSealed):
            bp.load_dev_packet(dataset, bad)


def test_the_summary_has_ids_sides_and_hashes_and_never_content(dataset):
    frozen(dataset)

    text = "\n".join(bp.summary_lines(dataset))

    assert SECRET not in text
    assert "veteran-2" in text and "test" in text
    assert sha((dataset / "packets" / "test" / "veteran-2.json").read_bytes()) in text
