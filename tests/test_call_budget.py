"""P2.2: the hard Gemini call cap (plan P2.4 section 5): counted before the request is sent, durable, resumable."""

from __future__ import annotations

import json

import pytest

from agents import call_budget as cb
from agents import writer_policy as wp
from agents.model_transport import ProviderResponse


def budget(tmp_path, run_cap=8, experiment_cap=400, run="r1"):
    return cb.CallBudget(tmp_path / "calls.jsonl", run=run, run_cap=run_cap, experiment_cap=experiment_cap)


def test_the_caps_are_the_approved_numbers():
    assert cb.EXPERIMENT_CAP == 400 and cb.CALLS_PER_ITEM == 4
    assert cb.run_cap_for(40) == 160


def test_a_call_is_counted_before_it_is_sent_and_a_crash_does_not_undercount(tmp_path):
    b = budget(tmp_path)
    b.reserve("item-1", "gemini-3.5-flash")  # never finished: the process "crashed" after sending

    assert budget(tmp_path).used_run == 1 and budget(tmp_path).used_experiment == 1


def test_the_run_cap_stops_the_next_reservation(tmp_path):
    b = budget(tmp_path, run_cap=2)
    b.reserve("a", "m")
    b.reserve("a", "m")

    with pytest.raises(cb.CapReached) as stopped:
        b.reserve("b", "m")
    assert stopped.value.args == ("call_cap_reached",)
    assert b.used_run == 2


def test_the_cap_before_the_first_item_allows_no_call(tmp_path):
    b = budget(tmp_path, run_cap=0)

    with pytest.raises(cb.CapReached):
        b.reserve("a", "m")
    assert b.used_run == 0


def test_the_experiment_cap_counts_every_run_in_the_ledger(tmp_path):
    for run in ("r1", "r2"):
        b = budget(tmp_path, run=run, run_cap=10, experiment_cap=3)
        for _ in range(2 if run == "r1" else 1):
            b.reserve("a", "m")

    with pytest.raises(cb.CapReached):
        budget(tmp_path, run="r3", run_cap=10, experiment_cap=3).reserve("a", "m")


def test_resume_keeps_the_count_of_the_same_run(tmp_path):
    first = budget(tmp_path, run_cap=3)
    first.reserve("a", "m")
    first.reserve("a", "m")

    again = budget(tmp_path, run_cap=3)
    again.reserve("b", "m")

    with pytest.raises(cb.CapReached):
        again.reserve("b", "m")


def test_the_worst_case_is_eight_calls_for_one_item_and_the_run_cap_allows_it(tmp_path):
    b = budget(tmp_path, run_cap=cb.run_cap_for(2))
    for _ in range(8):
        b.reserve("only-item", "m")

    assert b.used_run == 8 and b.remaining_run == 0


def test_a_tampered_ledger_is_refused(tmp_path):
    b = budget(tmp_path)
    b.reserve("a", "m")
    b.reserve("a", "m")
    path = tmp_path / "calls.jsonl"
    rows = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join([rows[1]]) + "\n", encoding="utf-8")  # the first row was removed

    with pytest.raises(cb.BudgetCorrupt):
        budget(tmp_path)


def test_a_finish_row_records_only_a_closed_code(tmp_path):
    b = budget(tmp_path)
    ticket = b.reserve("a", "m")
    b.finish(ticket, "http_503")

    rows = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["kind"] == "finish" and rows[-1]["code"] == "http_503"
    with pytest.raises(cb.BudgetCorrupt):
        b.finish(ticket, "the key was sk-secret")


def test_a_guarded_call_reserves_first_and_the_cascade_ends_on_rules_with_the_cap_code(tmp_path):
    sent = []

    def call(model, timeout):
        sent.append(model)
        return ProviderResponse(503, {}, None)

    b = budget(tmp_path, run_cap=3)
    outcome = wp.write_with_policy(b.guard("item", call), sleep=lambda s: None)

    assert outcome.path == "rules" and len(sent) == 3
    assert outcome.attempts[-1]["code"] == "call_cap_reached"
    assert b.used_run == 3


def test_a_cap_reached_before_the_first_call_sends_nothing(tmp_path):
    sent = []
    b = budget(tmp_path, run_cap=0)

    outcome = wp.write_with_policy(b.guard("item", lambda m, t: sent.append(m)), sleep=lambda s: None)

    assert sent == [] and outcome.path == "rules" and outcome.attempts == ({"model": "gemini-3.5-flash", "try": 1, "code": "call_cap_reached"},)


def test_an_unreadable_partial_row_and_a_negative_cap_are_refused(tmp_path):
    b = budget(tmp_path)
    b.reserve("a", "m")
    with (tmp_path / "calls.jsonl").open("a", encoding="utf-8") as handle:
        handle.write('{"kind":"reserve","ru')

    with pytest.raises(cb.BudgetCorrupt):
        budget(tmp_path)
    with pytest.raises(cb.BudgetCorrupt):
        cb.CallBudget(tmp_path / "other.jsonl", run="r", run_cap=1, experiment_cap=-1)
