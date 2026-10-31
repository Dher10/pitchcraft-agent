"""Frozen dev inputs must be verified before loading a key or calling Gemini."""
import json
import pytest

from agents import llm_report_writer as lw
from evals import run_b1


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    # Only metadata (ids/hashes), the glossary and the dev-only guide are copied.
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    for name in ("glossary.json", "packets_manifest.json"):
        (dataset / name).write_bytes((run_b1.DATASET / name).read_bytes())
    guide = tmp_path / "guide.md"
    guide.write_bytes(lw.GUIDE_PATH.read_bytes())
    cases = run_b1.pick_cases()
    monkeypatch.setattr(lw, "GUIDE_PATH", guide)
    monkeypatch.setattr(run_b1, "DATASET", dataset)
    monkeypatch.setattr(run_b1, "WORK", tmp_path / "work")
    monkeypatch.setattr(run_b1, "pick_cases", lambda: cases)
    return dataset, guide, cases


@pytest.mark.parametrize("changed", ["guide", "glossary", "prompt", "packets_manifest"])
def test_each_frozen_input_drift_rejects_main_before_credentials_or_calls(inputs, tmp_path, monkeypatch, capsys, changed):
    from evals import experiment_freeze as freeze
    from evals import local_runner
    dataset, guide, cases = inputs
    record = tmp_path / "freeze.json"
    record.write_text(json.dumps({"run_cap": 30, "inputs": freeze.current_inputs(dataset, cases)}), encoding="utf-8")
    monkeypatch.setattr(freeze, "FREEZE_PATH", record)
    if changed == "prompt":
        monkeypatch.setattr(lw, "PROMPT_VERSION", "changed-prompt")
    else:
        path = guide if changed == "guide" else dataset / ("glossary.json" if changed == "glossary" else "packets_manifest.json")
        path.write_bytes(path.read_bytes() + b"\n ")

    def forbidden(*args, **kwargs):
        pytest.fail("frozen-input drift reached credentials or a provider")
    monkeypatch.setattr(local_runner, "_local_key", forbidden)
    monkeypatch.setattr(run_b1, "make_provider", forbidden)
    assert run_b1.main(["--owner-pc-offline", "--run-cap", "30"]) == 1
    assert "frozen_inputs_changed" in capsys.readouterr().out
    assert not (run_b1.WORK / "calls.jsonl").exists()


def test_unchanged_frozen_inputs_pass_and_only_dev_ids_and_hashes_are_recorded(inputs, tmp_path):
    from evals import experiment_freeze as freeze
    dataset, _, cases = inputs
    snapshot = freeze.current_inputs(dataset, cases)
    record = tmp_path / "freeze.json"
    record.write_text(json.dumps({"run_cap": 30, "inputs": snapshot}), encoding="utf-8")
    assert freeze.verify_frozen(record, dataset, cases)["inputs"] == snapshot
    assert [e["id"] for e in snapshot["dev_cases"]] == cases and len(cases) == 10
    assert all(set(e) == {"id", "packet_sha256", "findings_sha256"} for e in snapshot["dev_cases"])


def test_committed_freeze_matches_the_current_inputs():
    from evals import experiment_freeze as freeze
    record = freeze.verify_frozen(freeze.FREEZE_PATH, run_b1.DATASET, run_b1.pick_cases())
    assert record["inputs"]["prompt"]["version"] == "p2.2-3"


def test_execution_cannot_raise_the_frozen_run_cap(inputs, tmp_path, monkeypatch, capsys):
    from evals import experiment_freeze as freeze, local_runner
    dataset, _, cases = inputs
    record = tmp_path / "freeze.json"
    record.write_text(json.dumps({"run_cap": 30, "inputs": freeze.current_inputs(dataset, cases)}), encoding="utf-8")
    monkeypatch.setattr(freeze, "FREEZE_PATH", record)
    def forbidden(*args, **kwargs):
        pytest.fail("raised cap reached credentials")
    monkeypatch.setattr(local_runner, "_local_key", forbidden)
    assert run_b1.main(["--owner-pc-offline", "--run-cap", "31"]) == 1
    assert "run_cap_exceeds_freeze" in capsys.readouterr().out


@pytest.mark.parametrize("cap", [31, "30", True])
def test_invalid_frozen_cap_is_rejected_before_credentials(inputs, tmp_path, monkeypatch, capsys, cap):
    from evals import experiment_freeze as freeze, local_runner
    dataset, _, cases = inputs
    record = tmp_path / "freeze.json"
    record.write_text(json.dumps({"run_cap": cap, "inputs": freeze.current_inputs(dataset, cases)}), encoding="utf-8")
    monkeypatch.setattr(freeze, "FREEZE_PATH", record)
    def forbidden(*args, **kwargs):
        pytest.fail("invalid freeze record reached credentials")
    monkeypatch.setattr(local_runner, "_local_key", forbidden)
    assert run_b1.main(["--owner-pc-offline", "--run-cap", "30"]) == 1
    assert "frozen_inputs_changed" in capsys.readouterr().out
