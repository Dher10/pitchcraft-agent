"""P2.4 collection request ledger: ceilings, resume, hash chain (docs/plans/P2.4.md section 4)."""

from __future__ import annotations

from datetime import date
import json

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from evals import request_ledger as rl
from tests.test_team_splits_as_of import savant  # noqa: F401  (a fixture)


def ledger(tmp_path):
    return rl.RequestLedger(tmp_path / "request_ledger.jsonl")


def test_ceilings_are_the_approved_numbers():
    assert rl.CEILINGS == {
        "savant_closed_month": 210,
        "savant_open_month": 80,
        "pitcher_hand": 80,
        "pitcher_statcast": 160,
        "mlb": 160,
    }
    assert rl.GROUP == {"mlb_schedule": "mlb", "mlb_series": "mlb", "mlb_people": "mlb"} | {
        s: s for s in rl.CEILINGS if s != "mlb"
    }


@pytest.mark.parametrize("source", sorted(rl.GROUP))
def test_every_source_stops_at_its_ceiling_and_the_refusal_writes_nothing(tmp_path, source):
    led = ledger(tmp_path)
    ceiling = rl.CEILINGS[rl.GROUP[source]]
    for _ in range(ceiling):
        led.finish(led.reserve(source, "x"), "ok")
    size = (tmp_path / "request_ledger.jsonl").stat().st_size

    with pytest.raises(rl.CeilingReached) as raised:
        led.reserve(source, "one too many")

    assert raised.value.code == "ceiling_reached"
    assert (tmp_path / "request_ledger.jsonl").stat().st_size == size  # refused before anything was sent or written
    assert led.count(rl.GROUP[source]) == ceiling


def test_the_three_mlb_sources_share_one_ceiling(tmp_path):
    led = ledger(tmp_path)
    for source, n in (("mlb_schedule", 100), ("mlb_people", 40), ("mlb_series", 20)):
        for _ in range(n):
            led.finish(led.reserve(source, "x"), "ok")

    with pytest.raises(rl.CeilingReached):
        led.reserve("mlb_series", "161st")


def test_unknown_source_and_outcome_are_refused(tmp_path):
    led = ledger(tmp_path)
    with pytest.raises(ValueError):
        led.reserve("gemini", "x")
    seq = led.reserve("mlb_people", "x")
    with pytest.raises(ValueError):
        led.finish(seq, "maybe")


def test_counts_survive_a_restart_and_a_crash_before_the_result_still_counts(tmp_path):
    led = ledger(tmp_path)
    led.finish(led.reserve("mlb_people", "a"), "ok")
    led.reserve("mlb_people", "b")  # the process dies here: no result row

    again = ledger(tmp_path)

    assert again.count("mlb") == 2
    assert len(again.pending()) == 1


def test_a_cache_hit_costs_nothing_and_is_not_counted_again(savant, tmp_path):  # noqa: F811
    urls, _ = savant
    led = ledger(tmp_path)
    with rl.counted_savant(led):
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))  # resume: from the cache
    assert len(urls) == 1
    assert led.count("savant_closed_month") == 1
    assert ledger(tmp_path).count("savant_closed_month") == 1


def test_the_request_is_recorded_before_it_is_sent_and_a_failure_is_recorded_too(savant, tmp_path, monkeypatch):  # noqa: F811
    led = ledger(tmp_path)
    seen = []

    def failing(url, timeout=60):
        seen.append(led.count("savant_closed_month"))  # already counted when the wire is touched
        raise OSError("down")

    monkeypatch.setattr(lp, "_get_text", failing)
    with rl.counted_savant(led), pytest.raises(OSError):
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))

    assert seen == [1]
    assert led.pending() == []
    assert json.loads((tmp_path / "request_ledger.jsonl").read_text().splitlines()[-1])["outcome"] == "failed"


def test_the_ceiling_stops_the_real_fetch_with_a_closed_code(savant, tmp_path, monkeypatch):  # noqa: F811
    urls, _ = savant
    led = ledger(tmp_path)
    monkeypatch.setitem(rl.CEILINGS, "savant_closed_month", 1)
    with rl.counted_savant(led):
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))
        with pytest.raises(rl.CeilingReached):
            lp.fetch_team_batting_statcast("BOS", date(2026, 4, 1), date(2026, 4, 30))
    assert len(urls) == 1  # the refused request never reached the wire


def test_open_month_requests_use_their_own_source(savant, tmp_path):  # noqa: F811
    led = ledger(tmp_path)
    with rl.counted_savant(led):
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 20), season_end=date(2026, 9, 27))
    assert led.count("savant_open_month") == 1 and led.count("savant_closed_month") == 0


def rewrite(path, edit):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    edit(rows)
    path.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows))


def filled(tmp_path):
    led = ledger(tmp_path)
    for i in range(3):
        led.finish(led.reserve("mlb_people", f"p{i}"), "ok")
    return tmp_path / "request_ledger.jsonl"


@pytest.mark.parametrize(
    "edit",
    [
        lambda rows: rows[1].update(detail="forged"),
        lambda rows: rows.pop(2),
        lambda rows: rows.reverse(),
        lambda rows: rows[3].update(outcome="failed"),
        lambda rows: rows.append(dict(rows[-1])),
    ],
    ids=["edited-row", "deleted-row", "reordered", "edited-outcome", "duplicated-row"],
)
def test_tampering_with_the_chain_is_detected(tmp_path, edit):
    path = filled(tmp_path)
    ledger(tmp_path)  # control: the untouched file loads
    rewrite(path, edit)
    with pytest.raises(rl.LedgerCorrupt):
        ledger(tmp_path)


def test_a_truncated_last_row_is_detected(tmp_path):
    path = filled(tmp_path)
    path.write_text(path.read_text()[:-20])
    with pytest.raises(rl.LedgerCorrupt):
        ledger(tmp_path)


def test_finish_refuses_an_unknown_or_already_finished_reservation_and_keeps_the_ledger_loadable(tmp_path):
    led = ledger(tmp_path)
    seq = led.reserve("mlb_people", "a")
    led.finish(seq, "ok")
    for bad in (seq, 99, "1", None):
        with pytest.raises(ValueError):
            led.finish(bad, "ok")
    assert ledger(tmp_path).count("mlb") == 1  # still loads


# --- every MLB request goes through the ledger (gate 4a) ----------------------------------------------------


@pytest.mark.parametrize(
    "url, source",
    [
        ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-04-01&endDate=2026-04-30", "mlb_schedule"),
        ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&gamePk=1&hydrate=seriesStatus", "mlb_series"),
        ("https://statsapi.mlb.com/api/v1/people/11/stats?stats=gameLog&group=pitching", "mlb_people"),
        ("https://statsapi.mlb.com/api/v1/people/11", "mlb_people"),
    ],
)
def test_each_mlb_request_is_reserved_before_it_is_sent_under_its_own_source(tmp_path, monkeypatch, url, source):
    led = ledger(tmp_path)
    seen = []

    def fake(u, timeout=8):
        seen.append(led.count("mlb"))  # already reserved when the wire is touched
        return {}

    monkeypatch.setattr(lp, "_get_json", fake)
    with rl.counted_mlb(led):
        lp._get_json(url)

    assert seen == [1] and led.rows[0]["source"] == source and led.rows[1]["outcome"] == "ok"
    assert lp._get_json is fake  # the patch is undone


def test_an_mlb_url_with_no_ledger_source_is_refused_before_it_is_sent(tmp_path, monkeypatch):
    sent = []
    monkeypatch.setattr(lp, "_get_json", lambda u, timeout=8: sent.append(u))
    led = ledger(tmp_path)
    with rl.counted_mlb(led), pytest.raises(ValueError):
        lp._get_json("https://statsapi.mlb.com/api/v1/teams/147/stats?stats=statSplits")

    assert sent == [] and led.rows == []
