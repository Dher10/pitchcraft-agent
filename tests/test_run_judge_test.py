import json

import pytest

from evals import judge_freeze as jf
from evals import run_judge_test as rjt


def _batch(group, ids):
    facts = [{"id": "F001", "subject": "Ace", "field": "era", "value": "2.5", "scope": "2026 season"}]
    return {"group": group, "fact_table": facts, "glossary": [],
            "items": [{"id": i, "sentence": f"s {i}", "cited_facts": ""} for i in ids], "estimated_tokens": 100}


def _ok(ids, label="supported"):
    return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"verdicts": [{"id": i, "label": label, "unsure": False} for i in ids]})}}],
            "usage": {"total_tokens": 90}}


def _answers(*items):
    it = iter(items)
    return lambda body: next(it)


def _state():
    return rjt.new_state("judge-p3", total_batches=3)


def test_every_batch_is_judged_once_and_the_state_keeps_labels_counts_and_tokens():
    batches = [_batch("G01", ["a", "b"]), _batch("G02", ["c"])]
    saved = []
    state = rjt.new_state("judge-p3", 2)
    out = rjt.run(_answers((200, {"r": 1}, _ok(["a", "b"])), (200, {"r": 2}, _ok(["c"], "unsupported"))), batches, state, saved.append)
    assert out["status"] == "complete" and out["batches_done"] == 2 and out["batches_total"] == 2
    assert state["verdicts"] == {"a": "supported", "b": "supported", "c": "unsupported"}
    assert state["tokens"] == 180 and state["calls"] == 2 and len(saved) == 2          # saved after every batch
    assert "s a" not in json.dumps(state)                                                # no sentence text, no response text


def test_a_second_run_resumes_after_the_last_completed_batch_and_does_not_call_it_again():
    batches = [_batch("G01", ["a"]), _batch("G02", ["b"]), _batch("G03", ["c"])]
    state = _state()
    answers = [(200, {}, _ok(["a"])), (429, {}, None), (429, {}, None), (429, {}, None), (429, {}, None)]
    out = rjt.run(_answers(*answers), batches, state, lambda s: None)
    assert out["status"] == "paused" and out["reason"] == "two_consecutive_failed_batches" and out["batches_done"] == 1
    calls = []

    def call(body):
        calls.append(body)
        ids = [s["id"] for s in json.loads(body["messages"][1]["content"].split("\n", 1)[1])["sentences"]] if False else None
        return 200, {}, _ok(["b"] if len(calls) == 1 else ["c"])

    out = rjt.run(call, batches, state, lambda s: None)
    assert out["status"] == "complete" and len(calls) == 2                                # G01 was not repeated
    assert set(state["verdicts"]) == {"a", "b", "c"}


def test_one_failed_batch_is_not_an_abort_and_is_retried_on_the_next_run():
    batches = [_batch("G01", ["a"]), _batch("G02", ["b"])]
    state = rjt.new_state("judge-p3", 2)
    answers = [(429, {}, None), (429, {}, None), (200, {}, _ok(["b"]))]
    out = rjt.run(_answers(*answers), batches, state, lambda s: None)
    assert out["status"] == "incomplete" and out["batches_done"] == 1 and out["failed_batches"] == 1
    assert "a" not in state["verdicts"]                                                  # a missing verdict is never stored as a label
    out = rjt.run(_answers((200, {}, _ok(["a"]))), batches, state, lambda s: None)
    assert out["status"] == "complete" and state["verdicts"]["a"] == "supported"


def test_pacing_waits_between_calls_but_not_before_the_first_nor_for_skipped_batches():
    waits = []
    batches = [_batch("G01", ["a"]), _batch("G02", ["b"]), _batch("G03", ["c"])]
    state = _state()
    rjt.run(_answers((200, {}, _ok(["a"]))), batches[:1], state, lambda s: None, sleep=waits.append)
    assert waits == []
    rjt.run(_answers((200, {}, _ok(["b"])), (200, {}, _ok(["c"]))), batches, state, lambda s: None, sleep=waits.append)
    assert waits == [jf.PACING_SECONDS]                                                  # only between the two new calls


def test_a_state_for_another_judge_version_or_batch_set_is_refused(tmp_path):
    path = tmp_path / "judge_test_state.json"
    rjt.save_state(path, rjt.new_state("judge-p2", 3))
    with pytest.raises(SystemExit):
        rjt.load_state(path, "judge-p3", 3)
    with pytest.raises(SystemExit):
        rjt.load_state(path, "judge-p2", 4)
    assert rjt.load_state(path, "judge-p2", 3)["version"] == "judge-p2"
    assert rjt.load_state(tmp_path / "absent.json", "judge-p3", 3)["verdicts"] == {}


def test_the_runner_never_reads_the_owner_labels():
    import inspect

    source = inspect.getsource(rjt)
    assert "owner_labels" not in source and "test_sheet.csv" not in source           # the sheet with the owner's answers is never opened


def test_a_run_needs_a_verified_and_committed_freeze(tmp_path):
    with pytest.raises(SystemExit):
        rjt.require_freeze(tmp_path / "absent.json", committed=lambda p: True)
    good = tmp_path / "judge-freeze.json"
    good.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        rjt.require_freeze(good, committed=lambda p: True, verify=lambda p: (_ for _ in ()).throw(jf.JudgeFrozenChanged("x")))
    with pytest.raises(SystemExit):
        rjt.require_freeze(good, committed=lambda p: False, verify=lambda p: {"spec": {"prompt_version": "judge-p3"}})
    assert rjt.require_freeze(good, committed=lambda p: True, verify=lambda p: {"spec": {"prompt_version": "judge-p3"}}) == "judge-p3"


def test_the_declared_retry_of_a_batch_is_paced_too():
    waits = []
    rjt.run(_answers((429, {}, None), (200, {}, _ok(["a"]))), [_batch("G01", ["a"])], _state(), lambda s: None, sleep=waits.append)
    assert waits == [jf.PACING_SECONDS]
