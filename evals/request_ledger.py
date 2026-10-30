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
from urllib.parse import urlsplit

from requests.adapters import HTTPAdapter

from data_pipeline.fetchers import live_pipeline
from evals.provider_protocol import canonical, digest

# Collection-wide ceilings (owner approval of Oct 29; the MLB ceiling raised from 120 to 160 on Oct 30, and once more to 172 for the selection re-run). The three MLB
# sources share one ceiling.
CEILINGS = {
    "savant_closed_month": 210,
    "savant_open_month": 80,
    "pitcher_hand": 80,
    "pitcher_statcast": 160,
    "mlb": 172,
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
        self.refused = False  # set when a reservation was refused at a ceiling (shows even if a caller swallows the error)
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
            self.refused = True
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


def mlb_source(url):
    """The ledger source of an MLB Stats API request, by what the url asks for."""

    if "hydrate=seriesStatus" in url:
        return "mlb_series"
    if "/people/" in url:
        # A throwing-hand lookup (`people/{id}`) has its own ceiling; the per-pitcher history (`/stats?`) is a lookup.
        return "mlb_people" if "/stats" in urlsplit(url).path else "pitcher_hand"
    if "/schedule" in url:
        return "mlb_schedule"
    raise ValueError(f"no ledger source for the MLB request {url!r}")


@contextmanager
def counted_mlb(ledger):
    """Route every MLB Stats API request of `live_pipeline._get_json` through the ledger, reserved before it is sent.

    A url the ledger has no source for is refused before anything is sent, so no request can go uncounted."""

    real = live_pipeline._get_json

    def counted(url, timeout=8):
        seq = ledger.reserve(mlb_source(url), url)
        try:
            data = real(url, timeout)
        except BaseException:
            ledger.finish(seq, "failed")
            raise
        ledger.finish(seq, "ok")
        return data

    live_pipeline._get_json = counted
    try:
        yield ledger
    finally:
        live_pipeline._get_json = real


@contextmanager
def counted_statcast_pitcher(ledger):
    """Reserve every Statcast pitcher HTTP request in the ledger before it is sent.

    `live_pipeline._counted_pitcher_transport` already counts and paces the requests of one run; this wraps it so each
    request that really leaves the machine is also a reservation in the collection-wide ledger (a hit of pybaseball's
    own cache sends nothing and costs nothing). A request refused at the ceiling is never sent."""

    real = live_pipeline._counted_pitcher_transport

    @contextmanager
    def counted():
        with real():
            inner = HTTPAdapter.send

            def send(adapter, request, **kwargs):
                seq = ledger.reserve("pitcher_statcast", request.url)
                try:
                    response = inner(adapter, request, **kwargs)
                except BaseException:
                    ledger.finish(seq, "failed")
                    raise
                ledger.finish(seq, "ok")
                return response

            HTTPAdapter.send = send
            try:
                yield
            finally:
                HTTPAdapter.send = inner

    live_pipeline._counted_pitcher_transport = counted
    try:
        yield ledger
    finally:
        live_pipeline._counted_pitcher_transport = real
