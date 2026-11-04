"""D64: the 40-case B1 driver. No provider, no packet content: ids, counts and the stop logic only."""
import json

import pytest

from evals import run_b1 as r
from evals import run_b1_full as f


def test_the_plan_is_ten_reused_ten_new_dev_and_twenty_held_out_in_split_order():
    reused, new_dev, held = f.plan_cases()
    assert (len(reused), len(new_dev), len(held)) == (10, 10, 20)
    assert not set(reused) & set(new_dev) and not set(held) & (set(reused) | set(new_dev))
    assert {f.split_of(c) for c in reused + new_dev} == {"dev"}
    assert {f.split_of(c) for c in held} == {"test"}


def test_counts_expose_only_outcomes_paths_and_attempts():
    items = [{"case_id": "a", "path": "primary", "content_attempts": 1, "report": {"secret": "x"}},
             {"case_id": "b", "path": "rules", "content_attempts": 2},
             {"case_id": "c", "path": "not_attempted", "reason": "capacity_stop"}]
    result = f.counts(items)
    assert result == {"cases": 3, "accepted": 1, "rejected": 1, "not_attempted": 1,
                      "paths": {"not_attempted": 1, "primary": 1, "rules": 1}, "content_attempts": 3}
    assert "secret" not in json.dumps(result)


class _Budget:
    def __init__(self):
        self.rows, self.used_run, self.run = [], 0, "t"


def _fake_run(monkeypatch, calls_per_case, capacity=False):
    budget = _Budget()

    def run_item(case_id, dataset, glossary, provider, budget_, directory, nli=None, **_):
        for k in range(calls_per_case):
            ticket = len(budget_.rows)
            budget_.rows.append({"kind": "reserve", "run": "t", "item": case_id, "model": "m", "seq": ticket})
            budget_.rows.append({"kind": "finish", "run": "t", "code": "http_503" if capacity else "ok", "ticket": ticket})
            budget_.used_run += 1
        return {"case_id": case_id, "path": "rules", "reason": "checks_failed", "content_attempts": 1}

    monkeypatch.setattr(r, "run_item", run_item)
    monkeypatch.setattr(f, "split_of", lambda case_id: "dev")
    return budget


def test_the_average_stop_fires_after_five_cases_above_three_calls_each(monkeypatch):
    budget = _fake_run(monkeypatch, 4)
    items, stop = f.run_cases([f"c{i}" for i in range(8)], None, None, budget, None)
    assert stop["reason"] == "average_call_stop" and stop["cases"] == 5
    assert [i["path"] for i in items].count("not_attempted") == 3


def test_the_capacity_stop_fires_when_more_than_a_third_of_calls_fail(monkeypatch):
    budget = _fake_run(monkeypatch, 5, capacity=True)
    items, stop = f.run_cases([f"c{i}" for i in range(4)], None, None, budget, None)
    assert stop["reason"] == "capacity_stop"
    assert [i["path"] for i in items].count("not_attempted") == 2


def test_no_stop_with_two_calls_per_case_and_no_capacity_failure(monkeypatch):
    budget = _fake_run(monkeypatch, 2)
    items, stop = f.run_cases([f"c{i}" for i in range(10)], None, None, budget, None)
    assert stop is None and all(i["path"] == "rules" for i in items)


def test_the_cap_cannot_exceed_the_decision():
    assert f.RUN_CAP == 100
