"""D29: the pipeline decides the cutoff, and it is always the day before the game (QA-02).

    as_of = officialDate - 1, in historical runs and in the daily job. The game date
    is the official MLB date (America/New_York), never the runner's UTC clock.

The leaky sources are the ones of test_as_of_end_to_end.py: they return post-cutoff
rows and "future" season numbers for any range, so a run that forgets the cutoff
shows it in the snapshot.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_as_of_end_to_end import (  # noqa: F401  (leaky_sources is a fixture)
    CUTOFF,
    GAME_DAY,
    SCHEDULE,
    leaky_sources,
)


def test_a_dated_run_without_as_of_stops_at_the_day_before_the_game(leaky_sources):
    record, snapshot = lp.run_live_pipeline(GAME_DAY)

    assert record["status"] == "ok" and record["errors"] == []
    assert record["as_of"] == CUTOFF and snapshot["as_of"] == CUTOFF
    starter = snapshot["away_starter"]
    assert starter["sample"]["arsenal"]["pitches"] == 150
    assert starter["season_summary"]["era"] == "3.10"
    assert {row["pitch"] for row in starter["pitch_mix"]} == {"Four-seam", "Slider"}
    assert snapshot["away_team_splits"]["vr"]["plate_appearances"] == 20


def test_a_dated_run_without_as_of_never_asks_a_source_past_the_cutoff(leaky_sources):
    api_urls, savant_urls = leaky_sources

    lp.run_live_pipeline(GAME_DAY)

    stats_urls = [u for u in api_urls if "/stats?" in u]
    assert stats_urls and all(f"endDate={CUTOFF}" in u for u in stats_urls)
    assert savant_urls
    assert all(
        parse_qs(urlparse(u).query)["game_date_lt"][0] <= CUTOFF for u in savant_urls
    )


def _freeze_clock(monkeypatch, utc_now: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return utc_now.astimezone(tz) if tz else utc_now.replace(tzinfo=None)

    monkeypatch.setattr(lp, "datetime", FrozenDateTime)


def test_a_run_without_a_date_uses_the_official_date_in_new_york_not_utc(
    leaky_sources, monkeypatch
):
    api_urls, _ = leaky_sources
    # 02:30 UTC on 07-16 is still 22:30 on 07-15 in New York.
    _freeze_clock(monkeypatch, datetime(2026, 7, 16, 2, 30, tzinfo=timezone.utc))

    record, snapshot = lp.run_live_pipeline()

    assert any("schedule" in u and "date=2026-07-15" in u for u in api_urls)
    assert record["target_date"] == GAME_DAY
    assert record["as_of"] == CUTOFF and snapshot["as_of"] == CUTOFF


def test_a_night_game_that_starts_the_next_day_in_utc_keeps_its_official_date(
    leaky_sources, monkeypatch
):
    game = SCHEDULE["dates"][0]["games"][0]
    monkeypatch.setitem(game, "gameDate", "2026-07-16T02:10:00Z")  # 22:10 ET on the 15th
    monkeypatch.setitem(game, "officialDate", GAME_DAY)

    record, snapshot = lp.run_live_pipeline(GAME_DAY)

    assert snapshot["as_of"] == CUTOFF
    assert snapshot["away_starter"]["sample"]["arsenal"]["pitches"] == 150
    assert snapshot["away_starter"]["season_summary"]["era"] == "3.10"


def test_the_official_date_of_the_game_decides_the_cutoff_not_the_requested_date(
    leaky_sources, monkeypatch
):
    game = SCHEDULE["dates"][0]["games"][0]
    monkeypatch.setitem(game, "officialDate", GAME_DAY)

    record, snapshot = lp.run_live_pipeline("2026-07-16")  # the API answered with the 15th

    assert snapshot["as_of"] == CUTOFF


@pytest.mark.parametrize("as_of", [GAME_DAY, "2026-07-16", "2026-10-10"])
def test_an_as_of_on_or_after_the_game_date_is_rejected(leaky_sources, as_of):
    record, snapshot = lp.run_live_pipeline(GAME_DAY, as_of=as_of)

    assert snapshot is None
    assert record["status"] == "failed"
    assert record["errors"] and "as_of" in record["errors"][0]["message"]


def test_an_earlier_explicit_as_of_is_still_allowed(leaky_sources):
    record, snapshot = lp.run_live_pipeline(GAME_DAY, as_of="2026-07-12")

    assert record["status"] == "ok"
    assert snapshot["as_of"] == "2026-07-12"


def test_resolve_as_of_is_the_day_before_the_game():
    assert lp.resolve_as_of("2026-07-15") == date(2026, 7, 14)
    assert lp.resolve_as_of(date(2026, 3, 1)) == date(2026, 2, 28)
    assert lp.resolve_as_of("2026-07-15", "2026-07-14") == date(2026, 7, 14)
    with pytest.raises(ValueError):
        lp.resolve_as_of("2026-07-15", "2026-07-15")
    with pytest.raises(ValueError):
        lp.resolve_as_of(None)


# --- D29 open-month budget --------------------------------------------------------------------


@pytest.fixture
def savant(monkeypatch, tmp_path):
    requests: list[str] = []
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0})
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )

    def fake_get(url, timeout=60):
        requests.append(url)
        return pd.DataFrame(columns=list(lp.TEAM_BATTING_COLUMNS)).to_csv(index=False)

    monkeypatch.setattr(lp, "_get_text", fake_get)
    return requests


def test_the_month_that_holds_as_of_has_its_own_budget_of_ten_requests(savant):
    teams = ["BOS", "NYY", "TOR", "BAL", "TB", "CLE", "DET", "KC", "MIN", "CWS", "HOU"]
    outcomes = {}
    for team in teams:
        outcomes[team] = lp.fetch_team_splits(
            {"BOS": 111, "NYY": 147, "TOR": 141, "BAL": 110, "TB": 139, "CLE": 114,
             "DET": 116, "KC": 118, "MIN": 142, "CWS": 145, "HOU": 117}[team],
            as_of="2026-07-14",
        )

    july = [u for u in savant if "game_date_gt=2026-07-01" in u]
    assert len(july) == 10
    assert [e["source"] for e in lp._run_errors] == ["savant_team_batting"]
    assert "open-month" in lp._run_errors[0]["message"]
    assert lp._run_errors[0]["team_id"] == 117  # the eleventh team: unavailable, not uncut
    assert outcomes["HOU"] == {}


def test_closed_months_do_not_use_the_open_month_budget(savant):
    for team_id in (111, 147, 141, 110, 139, 114, 116, 118, 142, 145, 117, 121):
        lp.fetch_team_splits(team_id, as_of="2026-09-30")  # season over: every month is closed

    assert lp._run_errors == []
    assert lp._savant_run.get("open_requests", 0) == 0


def test_repeating_a_run_the_same_day_costs_no_request(savant):
    lp.fetch_team_splits(147, as_of="2026-07-14")
    first = len(savant)

    lp.fetch_team_splits(147, as_of="2026-07-14")

    assert first > 0 and len(savant) == first


def test_a_new_run_starts_with_a_fresh_budget(leaky_sources):
    lp._savant_run.update(requests=209, open_requests=10)

    record, snapshot = lp.run_live_pipeline(GAME_DAY)

    assert record["status"] == "ok" and record["errors"] == []
