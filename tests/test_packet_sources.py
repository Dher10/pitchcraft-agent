"""P2.4 packets: the seams that keep a packet build inside the ledger and off the network.

- `HistoryStore.cached_response` reads the cached game log and never asks for it.
- `fetch_pitcher_statcast(season_stats=...)` does not make the season-stats request.
- `request_ledger`: a hand lookup is a `pitcher_hand` request (its own ceiling), and every Statcast pitcher HTTP
  request is reserved in the ledger before it is sent.
"""

from __future__ import annotations

from datetime import date
import json
import hashlib

import pytest
import requests
from pybaseball import cache as pybaseball_cache
from requests.adapters import HTTPAdapter

from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.fetchers.mlb_schemas import SourceShapeError
from evals import collect_sources as cs
from evals import request_ledger as rl
from tests.test_as_of_end_to_end import CUTOFF, STATCAST


def digest(response):
    return hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_history(directory, pitcher_id, response, season=2026):
    record = {"url": "u", "fetched_at": 1.0, "sha256": digest(response), "response": response}
    (directory / f"{pitcher_id}_{season}.json").write_text(json.dumps(record), encoding="utf-8")


RESPONSE = {"stats": [{"type": {"displayName": "gameLog"}, "splits": []}]}


@pytest.fixture
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a request was made")

    monkeypatch.setattr(lp, "_get_json", refuse)


# --- HistoryStore.cached_response -------------------------------------------------------------------------------


def test_cached_response_returns_the_stored_answer_without_a_request(tmp_path, no_network):
    write_history(tmp_path, 11, RESPONSE)
    store = cs.HistoryStore(tmp_path, 2026)

    assert store.cached_response(11) == RESPONSE
    assert store.lookups == 0


def test_cached_response_of_a_missing_pitcher_raises_and_never_fetches(tmp_path, no_network):
    store = cs.HistoryStore(tmp_path, 2026)

    with pytest.raises(cs.HistoryMissing):
        store.cached_response(99)
    assert store.lookups == 0


def test_cached_response_checks_the_digest(tmp_path, no_network):
    write_history(tmp_path, 11, RESPONSE)
    path = tmp_path / "11_2026.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["response"]["stats"][0]["splits"].append({"date": "2026-07-01"})
    path.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(SourceShapeError):
        cs.HistoryStore(tmp_path, 2026).cached_response(11)


def test_the_digest_of_a_cached_answer_is_available_for_the_manifest(tmp_path):
    write_history(tmp_path, 11, RESPONSE)

    assert cs.HistoryStore(tmp_path, 2026).cached_digest(11) == digest(RESPONSE)


# --- fetch_pitcher_statcast(season_stats=...) --------------------------------------------------------------------


@pytest.fixture
def statcast_world(monkeypatch, tmp_path):
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_run_warnings", [])
    monkeypatch.setattr(lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27)))
    monkeypatch.setattr(lp, "_statcast_pitcher_frame", lambda start, end, pitcher_id: STATCAST.copy())


def test_given_season_stats_the_season_stats_request_is_not_made(statcast_world, monkeypatch, no_network):
    monkeypatch.setattr(lp, "fetch_pitcher_season_stats", lambda *a, **k: pytest.fail("the season-stats request was made"))
    line = {"era": "3.10", "whip": "1.05", "innings": "9.1", "strikeouts": 9, "walks": 3, "home_runs_allowed": 2, "batters_faced": 37}

    starter = lp.fetch_pitcher_statcast(11, "Away Ace", as_of=CUTOFF, season_stats=line)

    assert starter["season_summary"]["era"] == "3.10"
    assert starter["sample"]["rates"]["batters_faced"] == 37


def test_an_empty_given_line_is_used_as_is_and_not_replaced_by_a_request(statcast_world, monkeypatch, no_network):
    monkeypatch.setattr(lp, "fetch_pitcher_season_stats", lambda *a, **k: pytest.fail("the season-stats request was made"))

    starter = lp.fetch_pitcher_statcast(11, "Away Ace", as_of=CUTOFF, season_stats={})

    assert starter is not None
    assert starter["season_summary"]["era"] == "N/A"


def test_without_season_stats_the_request_is_still_made(statcast_world, monkeypatch):
    asked = []
    monkeypatch.setattr(lp, "fetch_pitcher_season_stats", lambda *a, **k: asked.append(k) or {})

    lp.fetch_pitcher_statcast(11, "Away Ace", as_of=CUTOFF)

    assert asked == [{"as_of": CUTOFF}]


# --- the ledger -------------------------------------------------------------------------------------------------


def test_a_hand_lookup_is_a_pitcher_hand_request_not_an_mlb_lookup():
    assert rl.mlb_source("https://statsapi.mlb.com/api/v1/people/123") == "pitcher_hand"
    assert rl.GROUP["pitcher_hand"] == "pitcher_hand"


def test_the_history_lookup_stays_an_mlb_lookup():
    url = "https://statsapi.mlb.com/api/v1/people/123/stats?stats=gameLog,yearByYear&group=pitching&season=2026&sportId=1"

    assert rl.mlb_source(url) == "mlb_people"


class Transport:
    def __init__(self, ledger, error=None):
        self.ledger, self.error, self.reserved_at_send = ledger, error, []

    def __call__(self, adapter, request, **kwargs):
        self.reserved_at_send.append(self.ledger.count("pitcher_statcast"))
        if self.error:
            raise self.error
        response = requests.Response()
        response.status_code = 200
        response._content = b"game_date,game_type,pitch_type\n2026-07-01,R,FF\n"
        response.headers["content-type"] = "text/csv"
        response.url = request.url
        response.request = request
        return response


@pytest.fixture
def statcast_wire(monkeypatch, tmp_path):
    monkeypatch.setattr(lp, "_pitcher_statcast_run", {"requests": 0}, raising=False)
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0, "open_requests": 0})
    monkeypatch.setattr(pybaseball_cache.config, "cache_directory", str(tmp_path / "pybaseball"))
    monkeypatch.setattr(pybaseball_cache.config, "enabled", True)
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    ledger = rl.RequestLedger(tmp_path / "ledger.jsonl")
    transport = Transport(ledger)
    monkeypatch.setattr(HTTPAdapter, "send", transport)
    return ledger, transport


def test_every_statcast_pitcher_request_is_reserved_before_it_is_sent(statcast_wire):
    ledger, transport = statcast_wire

    with rl.counted_statcast_pitcher(ledger):
        lp._statcast_pitcher_frame("2026-03-26", "2026-07-14", 101)

    assert transport.reserved_at_send == [1]  # already in the ledger when the request left
    assert ledger.count("pitcher_statcast") == 1
    assert ledger.pending() == []
    assert ledger.rows[-1]["outcome"] == "ok"


def test_a_failed_statcast_request_is_counted_and_marked_failed(statcast_wire, monkeypatch):
    ledger, _ = statcast_wire
    monkeypatch.setattr(HTTPAdapter, "send", Transport(ledger, error=requests.ConnectionError("down")))

    with rl.counted_statcast_pitcher(ledger):
        with pytest.raises(Exception):
            lp._statcast_pitcher_frame("2026-03-26", "2026-07-14", 102)

    assert ledger.count("pitcher_statcast") == 1
    assert ledger.rows[-1]["outcome"] == "failed"


def test_at_the_ceiling_the_statcast_request_is_refused_before_it_is_sent(statcast_wire, monkeypatch):
    ledger, transport = statcast_wire
    monkeypatch.setitem(rl.CEILINGS, "pitcher_statcast", 1)

    with rl.counted_statcast_pitcher(ledger):
        lp._statcast_pitcher_frame("2026-03-26", "2026-07-14", 103)
        with pytest.raises(rl.CeilingReached):
            lp._statcast_pitcher_frame("2026-03-26", "2026-07-14", 104)

    assert len(transport.reserved_at_send) == 1
    assert ledger.refused is True


def test_the_patched_transport_is_restored(statcast_wire):
    ledger, _ = statcast_wire
    before = lp._counted_pitcher_transport
    send = HTTPAdapter.send

    with rl.counted_statcast_pitcher(ledger):
        assert lp._counted_pitcher_transport is not before

    assert lp._counted_pitcher_transport is before
    assert HTTPAdapter.send is send


def test_reset_run_budgets_zeroes_the_four_counters(monkeypatch):
    monkeypatch.setattr(lp, "_savant_run", {"requests": 9, "open_requests": 4})
    monkeypatch.setattr(lp, "_pitcher_hand_run", {"requests": 3})
    monkeypatch.setattr(lp, "_pitcher_statcast_run", {"requests": 7})
    monkeypatch.setattr(lp, "_run_errors", [{"x": 1}])
    monkeypatch.setattr(lp, "_run_warnings", [{"y": 1}])

    lp.reset_run_budgets()

    assert lp._savant_run == {"requests": 0, "open_requests": 0}
    assert lp._pitcher_hand_run == {"requests": 0}
    assert lp._pitcher_statcast_run == {"requests": 0}
    assert lp._run_errors == [] and lp._run_warnings == []
