"""Collection request ledger (docs/plans/P2.4.md section 4): a hash-chained, append-only record of every
MLB and Savant request of the dataset collection, written BEFORE the request is sent.

A ceiling is checked against the reservations already on disk, so a crash between "reserved" and "result" can
never undercount. A request answered from a cache never reaches this module and is never counted. Nothing but a
source name and a public description (a URL or a team and date range) is stored: no key, no response body.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import time

from data_pipeline.fetchers import live_pipeline
from evals.provider_protocol import canonical, digest

# Collection-wide ceilings (owner approval of Oct 29). The three MLB sources share one ceiling of 120.
CEILINGS = {
    "savant_closed_month": 210,
    "savant_open_month": 80,
    "pitcher_hand": 80,
    "pitcher_statcast": 160,
    "mlb": 120,
}
GROUP = {
    "mlb_schedule": "mlb",
    "mlb_series": "mlb",
    "mlb_people": "mlb",
    "savant_closed_month": "savant_closed_month",
    "savant_open_month": "savant_open_month",
    "pitcher_hand": "pitcher_hand",
    "pitcher_statcast": "pitcher_statcast",
}
OUTCOMES = ("ok", "failed")
ZERO = "0" * 64
ROW_KEYS = {"seq", "kind", "source", "detail", "at", "outcome", "previous", "digest"}


class CeilingReached(RuntimeError):
    code = "ceiling_reached"


class LedgerCorrupt(ValueError):
    code = "ledger_corrupt"


class RequestLedger:
    def __init__(self, path):
        self.path = Path(path)
        self.rows = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        raw = self.path.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            raise LedgerCorrupt("truncated last row")
        rows, previous, reserved = [], ZERO, {}
        for number, line in enumerate(raw.splitlines()):
            try:
                row = json.loads(line)
            except ValueError:
                raise LedgerCorrupt("unreadable row") from None
            if type(row) is not dict or set(row) != ROW_KEYS:
                raise LedgerCorrupt("unexpected row shape")
            body = {k: v for k, v in row.items() if k != "digest"}
            if row["previous"] != previous or row["digest"] != digest(body) or row["seq"] != number:
                raise LedgerCorrupt("chain broken")
            if row["kind"] == "reserve":
                if row["source"] not in GROUP or row["outcome"] is not None:
                    raise LedgerCorrupt("bad reservation")
                reserved[row["seq"]] = row["source"]
            elif row["kind"] == "result":
                target = row["detail"]
                if type(target) is not int or reserved.get(target) != row["source"] or row["outcome"] not in OUTCOMES:
                    raise LedgerCorrupt("result without its reservation")
                del reserved[target]
            else:
                raise LedgerCorrupt("unknown kind")
            rows.append(row)
            previous = row["digest"]
        return rows

    def _append(self, kind, source, detail, outcome=None):
        row = {
            "seq": len(self.rows),
            "kind": kind,
            "source": source,
            "detail": detail,
            "at": round(time.time(), 3),
            "outcome": outcome,
            "previous": self.rows[-1]["digest"] if self.rows else ZERO,
        }
        row["digest"] = digest(row)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(canonical(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.rows.append(row)
        return row["seq"]

    def count(self, group):
        """Reservations of a ceiling group, including any that never got a result."""

        return sum(1 for r in self.rows if r["kind"] == "reserve" and GROUP[r["source"]] == group)

    def pending(self):
        done = {r["detail"] for r in self.rows if r["kind"] == "result"}
        return [r["seq"] for r in self.rows if r["kind"] == "reserve" and r["seq"] not in done]

    def reserve(self, source, detail):
        if source not in GROUP:
            raise ValueError(f"unknown request source {source!r}")
        group = GROUP[source]
        if self.count(group) >= CEILINGS[group]:
            raise CeilingReached(f"{CEILINGS[group]} {group} requests already made in this collection")
        return self._append("reserve", source, str(detail)[:300])

    def finish(self, seq, outcome):
        if outcome not in OUTCOMES:
            raise ValueError(f"unknown outcome {outcome!r}")
        if type(seq) is not int or seq not in self.pending():
            raise ValueError("finish needs the seq of a reservation that has no result yet")
        reservation = self.rows[seq]
        self._append("result", reservation["source"], seq, outcome)


@contextmanager
def counted_savant(ledger):
    """Route the Savant team-batting requests of `live_pipeline` through the ledger (closed and open months apart)."""

    real = live_pipeline._savant_get

    def counted(url, open_month=False):
        seq = ledger.reserve("savant_open_month" if open_month else "savant_closed_month", url)
        try:
            text = real(url, open_month=open_month)
        except BaseException:
            ledger.finish(seq, "failed")
            raise
        ledger.finish(seq, "ok")
        return text

    live_pipeline._savant_get = counted
    try:
        yield ledger
    finally:
        live_pipeline._savant_get = real
