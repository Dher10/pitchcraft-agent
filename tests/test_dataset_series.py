"""P2.4 postseason standing before first pitch, end to end over the real 2026 schedule answer.

Source: tests/fixtures/mlb_series_2026-10.json, one real request (41 postseason games, three rounds finished).
Only the network call is replaced; `fetch_series_status` and the builder run for real (D28: negative tests first).
"""

from __future__ import annotations

from datetime import date, timedelta
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from evals import build_dataset as bd

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "mlb_series_2026-10.json").read_text(encoding="utf-8"))
GAMES = [g for day in FIXTURE["dates"] for g in day["games"]]
BY_PK = {}
for g in GAMES:
    BY_PK.setdefault(g["gamePk"], g)  # 849817 appears twice (postponed, then replayed): the first row is the postponed one

GAME_1, LATER, ENDS_SERIES, ENDS_ALT = 849809, 849813, 849815, 849831


@pytest.fixture(autouse=True)
def schedule(monkeypatch):
    def get_json(url, timeout=8):
        q = parse_qs(urlparse(url).query)
        if "gamePk" in q:
            games = [g for g in GAMES if g["gamePk"] == int(q["gamePk"][0])]
        else:
            team, kind = int(q["teamId"][0]), q["gameType"][0]
            lo, hi = q["startDate"][0], q["endDate"][0]
            games = [
                g
                for g in GAMES
                if g["gameType"] == kind
                and team in (g["teams"]["home"]["team"]["id"], g["teams"]["away"]["team"]["id"])
                and lo <= g["officialDate"] <= hi
            ]
        return {"dates": [{"games": games}] if games else []}

    monkeypatch.setattr(lp, "_get_json", get_json)


def status_for(pk):
    game = next(g for g in GAMES if g["gamePk"] == pk)
    cutoff = bd.check_as_of(game["officialDate"], (date.fromisoformat(game["officialDate"]) - timedelta(days=1)).isoformat())
    return game, bd.case_series(game, lp.fetch_series_status(pk, as_of=cutoff))


def test_game_1_has_no_prior_result():
    game, series = status_for(GAME_1)
    assert series == {"game_number": 1, "games_played": 0, "result": None, "is_over": False}


def test_a_later_game_carries_the_standing_before_it_not_its_own_result():
    game, series = status_for(LATER)  # AL Championship Series game 2: game 1 left CLE ahead 1-0; its own result is "tied 1-1"
    assert series["result"] == "CLE leads 1-0" and series["games_played"] == 1
    assert series["result"] != game["seriesStatus"]["result"]


@pytest.mark.parametrize("pk,before", [(ENDS_SERIES, "TB leads 3-2"), (ENDS_ALT, "Series tied 2-2")])
def test_the_game_that_ended_the_series_leaks_no_final_result(pk, before):
    game, series = status_for(pk)
    assert game["seriesStatus"]["isOver"] is True  # control: this game really ended its series
    assert series["result"] == before and series["is_over"] is False
    assert "wins" not in series["result"]


def test_every_final_postseason_game_of_the_answer_passes_without_leaking():
    checked = 0
    for g in GAMES:
        if g["status"]["detailedState"] != "Final" or g["gamePk"] == 849817 or g["seriesGameNumber"] == 1:
            continue
        _, series = status_for(g["gamePk"])
        assert series["games_played"] == g["seriesGameNumber"] - 1, g["gamePk"]
        checked += 1
    assert checked == 24  # 5 wild card + 12 division + 7 championship games after game 1


@pytest.mark.parametrize(
    "poison",
    [
        {"is_over": True},  # the series was already over: the final result leaked
        {"games_played": 2},  # a result from this game or a later one (game 2 asks for 1 prior game)
        {"result": "CLE wins 4-1"},  # the text of a finished series
        {"game_number": 3},  # an answer about another game
    ],
    ids=["is-over", "games-played", "wins-text", "other-game"],
)
def test_a_poisoned_status_is_refused(poison):
    game = next(g for g in GAMES if g["gamePk"] == LATER)
    clean = lp.fetch_series_status(LATER, as_of="2026-10-12")
    bd.case_series(game, clean)  # control: the real answer passes
    with pytest.raises(bd.LeakageError):
        bd.case_series(game, {**clean, **poison})


def test_an_empty_status_is_refused_not_read_as_game_1(monkeypatch):
    game = next(g for g in GAMES if g["gamePk"] == LATER)
    with pytest.raises(bd.LeakageError):
        bd.case_series(game, {})  # the fetcher's answer for any error: no standing, never "0-0"
