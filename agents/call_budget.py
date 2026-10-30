"""The hard Gemini call cap (plan P2.4 section 5): every HTTP request is counted before it is sent.

A durable hash-chained ledger keeps one `reserve` row before each request and one `finish` row with a closed code after it, so
a crash cannot undercount. The run cap is 4 x the items of the run; the experiment cap counts every run in the ledger.
Nothing here reads a key, a body or an error message.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from agents.writer_policy import CODES, CapReached

CALLS_PER_ITEM = 4  # run cap per item (the worst case is 8 calls; the cap stops a runaway, it does not allow all items 8)
EXPERIMENT_CAP = 400
CAP_CODE = "call_cap_reached"
FINISH_CODES = (*CODES, "ok", "unusable_response")
_ZERO = "0" * 64


class BudgetCorrupt(ValueError):
    pass


def run_cap_for(items: int) -> int:
    return CALLS_PER_ITEM * items


def _digest(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class CallBudget:
    def __init__(self, path, *, run: str, run_cap: int, experiment_cap: int = EXPERIMENT_CAP):
        if type(run) is not str or not run or type(run_cap) is not int or run_cap < 0 or type(experiment_cap) is not int or experiment_cap < 0:
            raise BudgetCorrupt("bad budget arguments")
        self.path, self.run, self.run_cap, self.experiment_cap = Path(path), run, run_cap, experiment_cap
        self.rows: list[dict] = []
        self._load()

    # --- state -------------------------------------------------------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        previous = _ZERO
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                raise BudgetCorrupt("unreadable row") from None
            body = {k: v for k, v in row.items() if k != "digest"}
            if row.get("previous") != previous or _digest(body) != row.get("digest"):
                raise BudgetCorrupt("hash chain broken")
            self.rows.append(row)
            previous = row["digest"]

    @property
    def used_experiment(self) -> int:
        return sum(1 for r in self.rows if r["kind"] == "reserve")

    @property
    def used_run(self) -> int:
        return sum(1 for r in self.rows if r["kind"] == "reserve" and r["run"] == self.run)

    @property
    def remaining_run(self) -> int:
        return max(0, min(self.run_cap - self.used_run, self.experiment_cap - self.used_experiment))

    # --- writing -----------------------------------------------------------------------------------------------------
    def _append(self, **fields) -> dict:
        row = {**fields, "previous": self.rows[-1]["digest"] if self.rows else _ZERO}
        row["digest"] = _digest(row)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.rows.append(row)
        return row

    def reserve(self, item: str, model: str) -> int:
        """Count one HTTP request before it is sent. Raises CapReached (and writes nothing) at either cap."""

        if self.remaining_run <= 0:
            raise CapReached()
        row = self._append(kind="reserve", run=self.run, item=item, model=model, seq=len(self.rows))
        return row["seq"]

    def finish(self, ticket: int, code: str) -> None:
        if code not in FINISH_CODES or type(ticket) is not int:
            raise BudgetCorrupt("not a closed code")
        self._append(kind="finish", run=self.run, ticket=ticket, code=code)

    def guard(self, item: str, call):
        """Wrap `call(model, timeout)` so each request is reserved first and its outcome is recorded."""

        def guarded(model, timeout):
            ticket = self.reserve(item, model)
            try:
                response = call(model, timeout)
            except Exception as error:
                self.finish(ticket, "timeout" if type(error).__name__ == "ConnectionTimeout" else "connection_failed" if type(error).__name__ == "ConnectionFailed" else "malformed_response")
                raise
            status = getattr(response, "status", None)
            self.finish(ticket, "ok" if status == 200 else f"http_{status}" if status in (429, 503) else "http_4xx" if type(status) is int and 400 <= status < 500 else "http_5xx")
            return response

        return guarded
