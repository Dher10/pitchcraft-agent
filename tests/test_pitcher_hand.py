"""The throwing hand of a pitcher: where it comes from, and what it costs (QA2-03 sweep).

A Statcast frame without `p_throws` used to make the pitcher right-handed, which picks the
wrong team split and prints the wrong hand. The hand now comes from the MLB people endpoint
when the frame cannot say. That lookup is cached for good (a hand does not change) and counts
against a per-run request budget; a failed or invalid answer is never cached.
"""

from __future__ import annotations

from datetime import date
import json

import pytest

from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import API_STATS, frame, route


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )


def person(code: str) -> dict:
    return {"people": [{"pitchHand": {"code": code}}]}


class Counter:
    """urlopen stub that answers from a table and counts the people requests."""

    def __init__(self, monkeypatch, answers: dict[int, object]):
        self.calls: list[int] = []
        self.answers = answers
        monkeypatch.setattr(lp.urllib.request, "urlopen", self._urlopen)

    def _urlopen(self, req, timeout=None):
        from tests.test_live_sample_pipeline import FakeResponse

        url = req.full_url if hasattr(req, "full_url") else req
        if "/stats?" in url:
            return FakeResponse(API_STATS)
        pitcher_id = int(url.rstrip("/").split("/people/")[1].split("?")[0])
        self.calls.append(pitcher_id)
        answer = self.answers[pitcher_id]
        if isinstance(answer, Exception):
            raise answer
        return FakeResponse(answer)


# --- the frame cannot say the hand ------------------------------------------------------------------


def test_a_frame_without_p_throws_takes_the_hand_from_the_people_endpoint(monkeypatch):
    stub = Counter(monkeypatch, {11: person("L")})
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame().drop(columns=["p_throws"]))

    result = lp.fetch_pitcher_statcast(11, "Lefty", as_of="2026-07-14")

    assert result["throws"] == "L"
    assert stub.calls == [11] and lp._run_errors == []


def test_a_frame_whose_p_throws_is_all_null_takes_the_hand_from_the_people_endpoint(monkeypatch):
    stub = Counter(monkeypatch, {11: person("L")})
    data = frame()
    data["p_throws"] = None
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: data)

    result = lp.fetch_pitcher_statcast(11, "Lefty", as_of="2026-07-14")

    assert result["throws"] == "L" and stub.calls == [11]


def test_a_frame_with_p_throws_makes_no_extra_request(monkeypatch):
    stub = Counter(monkeypatch, {})
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame())

    result = lp.fetch_pitcher_statcast(11, "Righty", as_of="2026-07-14")

    assert result["throws"] == "R" and stub.calls == []


def test_when_nothing_can_say_the_hand_the_pitcher_is_an_error_not_a_right_hander(monkeypatch):
    Counter(monkeypatch, {11: OSError("down")})
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame().drop(columns=["p_throws"]))

    result = lp.fetch_pitcher_statcast(11, "Nobody Knows", as_of="2026-07-14")

    assert result is None
    assert [e["source"] for e in lp._run_errors] == ["mlb_person"]


# --- cache ----------------------------------------------------------------------------------------------


def test_a_hand_is_requested_once_and_then_read_from_the_cache(monkeypatch):
    stub = Counter(monkeypatch, {11: person("L")})

    assert lp.fetch_pitcher_hand(11) == "L"
    assert lp.fetch_pitcher_hand(11) == "L"

    assert stub.calls == [11]
    cached = json.loads((lp.PITCHER_HAND_CACHE_DIR / "11.json").read_text(encoding="utf-8"))
    assert cached["throws"] == "L"


def test_a_cache_hit_survives_a_new_run(monkeypatch):
    stub = Counter(monkeypatch, {11: person("R")})
    lp.fetch_pitcher_hand(11)
    lp._pitcher_hand_run["requests"] = 0  # what the next run starts with

    assert lp.fetch_pitcher_hand(11) == "R"
    assert stub.calls == [11]


def test_a_failed_request_is_not_cached(monkeypatch):
    stub = Counter(monkeypatch, {11: OSError("down")})
    assert lp.fetch_pitcher_hand(11) is None
    stub.answers[11] = person("L")

    assert lp.fetch_pitcher_hand(11) == "L"

    assert stub.calls == [11, 11]


@pytest.mark.parametrize("answer", [person("X"), {"people": []}, {"message": "oops"}, [], None])
def test_an_invalid_answer_is_an_error_and_is_not_cached(monkeypatch, answer):
    stub = Counter(monkeypatch, {11: answer})

    assert lp.fetch_pitcher_hand(11) is None

    assert [e["source"] for e in lp._run_errors] == ["mlb_person"]
    assert not (lp.PITCHER_HAND_CACHE_DIR / "11.json").exists()
    assert stub.calls == [11]


@pytest.mark.parametrize("content", ["not json", "{}", '{"throws": "Q"}', '{"throws": null}'])
def test_a_corrupt_cache_file_is_ignored_and_requested_again(monkeypatch, content):
    stub = Counter(monkeypatch, {11: person("L")})
    lp.PITCHER_HAND_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (lp.PITCHER_HAND_CACHE_DIR / "11.json").write_text(content, encoding="utf-8")

    assert lp.fetch_pitcher_hand(11) == "L"

    assert stub.calls == [11]
    assert lp._run_errors == []


# --- budget -----------------------------------------------------------------------------------------------


def test_the_budget_is_ten_requests_a_run():
    # 5 candidate games x 2 starters: the most one run can ask for, with the cache doing the rest.
    assert lp.PITCHER_HAND_MAX_REQUESTS_PER_RUN == 10


def test_requests_past_the_budget_are_an_error_without_a_call(monkeypatch):
    monkeypatch.setattr(lp, "PITCHER_HAND_MAX_REQUESTS_PER_RUN", 2)
    stub = Counter(monkeypatch, {1: person("L"), 2: person("R"), 3: person("L")})

    assert [lp.fetch_pitcher_hand(pid) for pid in (1, 2, 3)] == ["L", "R", None]

    assert stub.calls == [1, 2]
    assert [e["source"] for e in lp._run_errors] == ["mlb_person"]
    assert "budget" in lp._run_errors[0]["message"]
    assert lp._run_errors[0]["pitcher_id"] == 3


def test_cache_hits_do_not_spend_the_budget(monkeypatch):
    monkeypatch.setattr(lp, "PITCHER_HAND_MAX_REQUESTS_PER_RUN", 1)
    stub = Counter(monkeypatch, {1: person("L")})

    assert [lp.fetch_pitcher_hand(1) for _ in range(5)] == ["L"] * 5

    assert stub.calls == [1] and lp._run_errors == []


def test_a_failed_request_still_spends_the_budget(monkeypatch):
    monkeypatch.setattr(lp, "PITCHER_HAND_MAX_REQUESTS_PER_RUN", 1)
    stub = Counter(monkeypatch, {1: OSError("down"), 2: person("R")})

    assert lp.fetch_pitcher_hand(1) is None
    assert lp.fetch_pitcher_hand(2) is None

    assert stub.calls == [1]


def test_every_run_starts_with_a_fresh_budget(monkeypatch):
    lp._pitcher_hand_run["requests"] = 99
    route(monkeypatch, [("schedule", {"dates": []})])

    lp.run_live_pipeline("2026-07-15")

    assert lp._pitcher_hand_run["requests"] == 0
