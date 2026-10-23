"""P1.2-a (D42): the Statcast pitcher fetch has a request budget, a pause, a timeout and a status check.

`pybaseball.statcast_pitcher` calls `requests.get` with no timeout and no status check. `fetch_pitcher_statcast` now
reaches it only through `_statcast_pitcher_frame`, which counts every request that really leaves the machine (a hit of
pybaseball's own cache sends nothing and costs nothing), refuses the 21st of a run, sleeps SAVANT_PAUSE_SECONDS before
every Savant request but the first of the run (team batting counts too), gives each request a 60 second timeout and
turns a status other than 200 into a recorded `request_failed`. No test makes a real request: the transport under
`requests` is replaced by a canned one, and the real `pybaseball.statcast_pitcher` runs on top of it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import requests
from pybaseball import cache as pybaseball_cache
from requests.adapters import HTTPAdapter

from data_pipeline.fetchers import live_pipeline as lp

ROOT = Path(__file__).resolve().parents[1]
CSV = "game_date,game_type,pitch_type\n2026-07-01,R,FF\n2026-07-01,R,SL\n"


class Transport:
    """What stands in for the network: it records every request that reaches `HTTPAdapter.send`."""

    def __init__(self, status: int = 200, body: str = CSV, error: Exception | None = None):
        self.status, self.body, self.error = status, body, error
        self.calls: list[dict] = []

    def __call__(self, adapter, request, **kwargs):
        self.calls.append({"url": request.url, **kwargs})
        if self.error is not None:
            raise self.error
        response = requests.Response()
        response.status_code = self.status
        response._content = self.body.encode()
        response.headers["content-type"] = "text/csv"
        response.url = request.url
        response.request = request
        return response


@pytest.fixture(autouse=True)
def fresh_run(monkeypatch, tmp_path):
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0, "open_requests": 0})
    monkeypatch.setattr(lp, "_pitcher_statcast_run", {"requests": 0}, raising=False)
    monkeypatch.setattr(lp, "_pitcher_hand_run", {"requests": 0})
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(pybaseball_cache.config, "cache_directory", str(tmp_path / "pybaseball"))
    monkeypatch.setattr(pybaseball_cache.config, "enabled", True)
    sleeps: list[float] = []
    monkeypatch.setattr(lp.time, "sleep", sleeps.append)
    return sleeps


@pytest.fixture
def transport(monkeypatch):
    fake = Transport()
    monkeypatch.setattr(HTTPAdapter, "send", fake)
    return fake


def frame(pitcher_id: int = 1, start: str = "2026-03-26", end: str = "2026-07-14"):
    return lp._statcast_pitcher_frame(start, end, pitcher_id)


def test_the_cap_is_twenty_and_the_hand_lookup_keeps_its_ten():
    assert lp.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN == 20
    assert lp.PITCHER_HAND_MAX_REQUESTS_PER_RUN == 10
    assert lp.SAVANT_MAX_REQUESTS_PER_RUN == 210 and lp.SAVANT_MAX_OPEN_MONTH_REQUESTS_PER_RUN == 10


def test_one_pitcher_is_one_request_and_its_frame_is_returned(transport):
    result = frame(101)

    assert len(transport.calls) == 1 and "pitchers_lookup%5B%5D=101" in transport.calls[0]["url"]
    assert list(result["pitch_type"]) == ["FF", "SL"]
    assert lp._pitcher_statcast_run["requests"] == 1


def test_twenty_requests_pass_and_the_twenty_first_is_refused_without_a_request(transport):
    for pitcher_id in range(1, 21):
        frame(pitcher_id)
    assert len(transport.calls) == 20

    with pytest.raises(lp.PitcherStatcastBudgetExceeded):
        frame(21)

    assert len(transport.calls) == 20


def test_the_refused_request_is_a_recorded_budget_failure_and_the_run_goes_on(monkeypatch, transport):
    monkeypatch.setattr(lp, "season_dates", lambda year: (lp.date(2026, 3, 26), lp.date(2026, 9, 27)))
    lp._pitcher_statcast_run["requests"] = lp.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN

    result = lp.fetch_pitcher_statcast(31, "Capped Starter", as_of="2026-07-14")

    assert result is None and transport.calls == []
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("statcast_pitcher", "budget_spent")]


def test_a_failed_request_still_counts_against_the_cap(monkeypatch):
    monkeypatch.setattr(HTTPAdapter, "send", Transport(error=requests.ConnectionError("down")))

    with pytest.raises(requests.ConnectionError):
        frame(5)

    assert lp._pitcher_statcast_run["requests"] == 1


def test_the_first_request_of_the_run_does_not_wait_and_each_next_one_waits_two_seconds(transport, fresh_run):
    frame(1)
    assert fresh_run == []

    frame(2)
    frame(3)

    assert fresh_run == [lp.SAVANT_PAUSE_SECONDS, lp.SAVANT_PAUSE_SECONDS] and lp.SAVANT_PAUSE_SECONDS == 2.0


def test_a_team_batting_request_made_before_makes_the_first_pitcher_request_wait(transport, fresh_run):
    lp._savant_run.update(requests=1)

    frame(1)

    assert fresh_run == [lp.SAVANT_PAUSE_SECONDS]


def test_a_pitcher_request_made_before_makes_the_next_team_batting_request_wait(monkeypatch, transport, fresh_run):
    monkeypatch.setattr(lp, "_get_text", lambda url, timeout=60: "")
    frame(1)

    lp._savant_get("https://baseballsavant.mlb.com/statcast_search/csv?team=NYY")

    assert fresh_run == [lp.SAVANT_PAUSE_SECONDS]
    assert lp._savant_run["requests"] == 1


def test_a_cache_hit_of_pybaseball_sends_nothing_and_costs_nothing(transport, fresh_run):
    first = frame(7)
    second = frame(7)

    assert len(transport.calls) == 1 and lp._pitcher_statcast_run["requests"] == 1
    assert fresh_run == []
    assert list(first["pitch_type"]) == list(second["pitch_type"])


def test_every_request_gets_a_sixty_second_timeout(transport):
    frame(8)

    assert transport.calls[0]["timeout"] == 60


def test_a_status_other_than_200_is_a_request_failure_and_the_answer_is_not_used(monkeypatch):
    transport = Transport(status=503, body="<html>unavailable</html>")
    monkeypatch.setattr(HTTPAdapter, "send", transport)

    with pytest.raises(lp.SavantRequestFailed) as caught:
        frame(9)

    assert "503" in str(caught.value) and lp.error_code(caught.value) == "request_failed"
    assert "<html>" not in str(caught.value)


def test_a_blocked_savant_is_recorded_as_a_request_failure_by_the_fetcher(monkeypatch):
    monkeypatch.setattr(lp, "season_dates", lambda year: (lp.date(2026, 3, 26), lp.date(2026, 9, 27)))
    monkeypatch.setattr(HTTPAdapter, "send", Transport(status=403, body="Forbidden"))

    result = lp.fetch_pitcher_statcast(41, "Blocked Starter", as_of="2026-07-14")

    assert result is None
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("statcast_pitcher", "request_failed")]


def test_a_timeout_is_a_request_failure(monkeypatch):
    monkeypatch.setattr(HTTPAdapter, "send", Transport(error=requests.ConnectTimeout("slow")))

    with pytest.raises(requests.ConnectTimeout) as caught:
        frame(10)

    assert lp.error_code(caught.value) == "request_failed"


def test_the_transport_is_put_back_after_the_call_even_when_it_fails(monkeypatch):
    fake = Transport(error=requests.ConnectionError("down"))
    monkeypatch.setattr(HTTPAdapter, "send", fake)

    with pytest.raises(requests.ConnectionError):
        frame(11)

    assert HTTPAdapter.send is fake


def test_the_pitcher_budget_is_per_run(monkeypatch):
    monkeypatch.setattr(lp, "build_live_snapshot", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("stop")))
    lp._pitcher_statcast_run["requests"] = 7

    lp.run_live_pipeline("2026-07-15")

    assert lp._pitcher_statcast_run["requests"] == 0


def test_no_other_code_in_the_pipeline_calls_statcast_pitcher_directly():
    callers = []
    for path in sorted((ROOT / "data_pipeline").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            if name == "statcast_pitcher":  # `statcast_pitcher(...)` and `pybaseball.statcast_pitcher(...)`
                callers.append((path.name, node.lineno))
    in_the_guard = [call for call in callers if call[0] == "live_pipeline.py"]

    assert len(callers) == 1 and len(in_the_guard) == 1
