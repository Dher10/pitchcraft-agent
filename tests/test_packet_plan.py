"""P2.4 packets: the offline plan of a build (what it would request) and the cached schedule it reads."""

from __future__ import annotations

from datetime import date
import hashlib
import json

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from evals import build_packets as bp
from evals import collect_sources as cs
from evals import request_ledger as rl

SEASON = (date(2026, 3, 25), date(2026, 9, 27))


def digest(response):
    return hashlib.sha256(json.dumps(response, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def game(pk, day, away=111, home=147, status=("Final", "Final")):
    return {
        "gamePk": pk,
        "gameType": "R",
        "officialDate": day,
        "status": {"abstractGameState": status[0], "detailedState": status[1]},
        "teams": {
            "away": {"team": {"id": away}, "probablePitcher": {"id": pk * 10, "fullName": "A"}},
            "home": {"team": {"id": home}, "probablePitcher": {"id": pk * 10 + 1, "fullName": "B"}},
        },
    }


def write_schedule(directory, name, games):
    response = {"dates": [{"date": g["officialDate"], "games": [g]} for g in games]}
    (directory / name).write_text(json.dumps({"url": "u", "fetched_at": 1.0, "sha256": digest(response), "response": response}), encoding="utf-8")


def test_cached_schedule_maps_every_game_to_its_raw_row_file_and_digest(tmp_path):
    write_schedule(tmp_path, "schedule_a_R.json", [game(1, "2026-07-15")])

    found = cs.cached_schedule(tmp_path)

    assert found[1].raw["officialDate"] == "2026-07-15"
    assert found[1].file == "schedule_a_R.json" and len(found[1].sha256) == 64


def test_a_replayed_game_keeps_its_final_row(tmp_path):
    write_schedule(tmp_path, "schedule_a_R.json", [game(1, "2026-07-15", status=("Final", "Final"))])
    write_schedule(tmp_path, "schedule_b_R.json", [game(1, "2026-07-16", status=("Preview", "Scheduled"))])

    assert cs.cached_schedule(tmp_path)[1].raw["officialDate"] == "2026-07-15"


def test_a_schedule_file_that_changed_is_refused(tmp_path):
    write_schedule(tmp_path, "schedule_a_R.json", [game(1, "2026-07-15")])
    path = tmp_path / "schedule_a_R.json"
    path.write_text(path.read_text(encoding="utf-8").replace("2026-07-15", "2026-07-16"), encoding="utf-8")

    with pytest.raises(Exception):
        cs.cached_schedule(tmp_path)


def test_the_plan_counts_only_the_savant_months_not_on_disk_and_sends_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(lp, "_get_json", lambda *a, **k: (_ for _ in ()).throw(AssertionError("request")))
    cache = tmp_path / "team_batting"
    cache.mkdir()
    for code in ("BOS", "NYY"):
        for start, end in lp._month_chunks(SEASON[0], date(2026, 6, 30)):
            (cache / f"{code}_{start}_{end}.csv").write_text("x", encoding="utf-8")  # closed months through June are cached
    schedule = {1: cs.CachedGame(game(1, "2026-07-15"), "f", "s")}
    records = [{"case_id": "veteran-1", "game_pk": 1, "as_of": "2026-07-14", "pitcher_ids": [10, 11]}]
    store = cs.HistoryStore(tmp_path / "history", 2026)

    plan = bp.plan_requests(records, schedule, SEASON, store, team_cache_dir=cache)

    assert plan["savant_open_month"] == 2  # July 1-14 for each of the two teams
    assert plan["savant_closed_month"] == 0
    assert plan["pitcher_statcast"] == 2 and plan["mlb"] == 0
    assert plan["missing_history"] == [10, 11] and plan["missing_games"] == []


def test_a_game_that_is_not_in_the_cached_schedule_is_named(tmp_path):
    records = [{"case_id": "veteran-1", "game_pk": 9, "as_of": "2026-07-14", "pitcher_ids": [10, 11]}]

    plan = bp.plan_requests(records, {}, SEASON, cs.HistoryStore(tmp_path, 2026), team_cache_dir=tmp_path)

    assert plan["missing_games"] == ["veteran-1"]


def test_requests_used_counts_reservations_from_a_row_on(tmp_path):
    ledger = rl.RequestLedger(tmp_path / "l.jsonl")
    ledger.finish(ledger.reserve("mlb_schedule", "x"), "ok")
    since = len(ledger.rows)
    ledger.finish(ledger.reserve("pitcher_statcast", "a"), "ok")
    ledger.finish(ledger.reserve("pitcher_statcast", "b"), "failed")
    ledger.finish(ledger.reserve("savant_open_month", "c"), "ok")

    used = bp.requests_used(ledger, since)

    assert used["pitcher_statcast"] == 2 and used["savant_open_month"] == 1 and used["mlb"] == 0
