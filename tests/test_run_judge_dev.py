import json

from evals import judge_freeze as jf
from evals import run_judge_dev as rjd


def _batch(group, ids):
    facts = [{"id": "F001", "subject": "Ace", "field": "era", "value": "2.5", "scope": "2026 season"}]
    return {"group": group, "fact_table": facts, "glossary": [],
            "items": [{"id": i, "sentence": f"s {i}", "cited_facts": ""} for i in ids], "estimated_tokens": 100}


def _ok(ids, label="supported"):
    return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({"verdicts": [{"id": i, "label": label, "unsure": False} for i in ids]})}}],
            "usage": {"total_tokens": 90}}


def test_a_pass_compares_with_owner_labels_and_keeps_counts_only():
    batches = [_batch("G01", ["a", "b"])]
    owner = {"a": "supported", "b": "unsupported"}
    record = rjd.run_pass(lambda body: (200, {"x-ratelimit-remaining-tokens": 7000}, _ok(["a", "b"])), batches, owner)
    assert record["agreement"] == 0.5 and record["missing"] == 0 and record["labeled"] == 2
    assert record["tokens"]["actual"] == 90 and record["prompt_version"] == jf.PROMPT_VERSION
    assert record["headers"][0]["x-ratelimit-remaining-tokens"] == 7000
    assert "s a" not in json.dumps(record)
    assert "unsupported" not in json.dumps(record["batches"])      # control: batch records carry no labels


def test_a_non_200_status_is_a_transport_failure_then_missing_never_a_pass():
    answers = iter([(200, {}, _ok(["a"])), (429, {}, None), (429, {}, None)])
    record = rjd.run_pass(lambda body: next(answers), [_batch("G01", ["a"]), _batch("G02", ["b"])], {"a": "supported", "b": "supported"})
    assert record["missing"] == 1 and record["attempts"] == 3 and record["agreement"] == 0.5


def test_pacing_continues_between_the_first_batch_and_the_rest():
    waits = []
    ids = iter([["a"], ["b"], ["c"]])
    rjd.run_pass(lambda body: (200, {}, _ok(next(ids))), [_batch("G01", ["a"]), _batch("G02", ["b"]), _batch("G03", ["c"])], {"a": "supported"}, sleep=waits.append)
    assert waits == [jf.PACING_SECONDS, jf.PACING_SECONDS]


def test_only_valid_owner_labels_are_used():
    rows = [{"item": "a", "label": " Supported "}, {"item": "b", "label": ""}, {"item": "c", "label": "nonsense"}]
    assert rjd.owner_labels(rows) == {"a": "supported"}


def test_a_pass_record_is_written_once_and_no_per_sentence_file_exists(tmp_path):
    import pytest

    record = {"pass": 1, "agreement": 0.5}
    rjd.write_record(tmp_path, 1, record)
    assert json.loads((tmp_path / "judge_dev_pass1.json").read_text(encoding="utf-8")) == record
    with pytest.raises(SystemExit):
        rjd.write_record(tmp_path, 1, {"pass": 1, "agreement": 1.0})
    assert json.loads((tmp_path / "judge_dev_pass1.json").read_text(encoding="utf-8")) == record
    assert [p.name for p in tmp_path.iterdir()] == ["judge_dev_pass1.json"]


def test_a_first_batch_that_cannot_be_judged_aborts_the_pass_without_a_record():
    import pytest

    calls = []

    def refuse(body):
        calls.append(1)
        return 429, {}, None

    with pytest.raises(rjd.PassAborted):
        rjd.run_pass(refuse, [_batch("G01", ["a"]), _batch("G02", ["b"])], {"a": "supported", "b": "supported"})
    assert len(calls) == 2           # the declared retry only; the second batch is never sent
