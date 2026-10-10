"""As-of team splits derived from Statcast (PLAN.md P0.3).

The MLB Stats API ignores date ranges on team splits by pitcher hand, so with
`as_of` they are derived from Statcast plate appearances. Nothing is fetched here:
the Savant request is mocked and the disk cache points at tmp_path.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp


def pa_rows(team_batting: str, hand: str, events: list, game_date="2026-07-10", **extra):
    """Plate-appearance rows where `team_batting` is NYY (home, bottom) by default."""

    rows = []
    for event in events:
        rows.append(
            {
                "game_date": game_date,
                "game_type": "R",
                "home_team": "NYY",
                "away_team": "BOS",
                "inning_topbot": "Bot" if team_batting == "NYY" else "Top",
                "p_throws": hand,
                "events": event,
                **extra,
            }
        )
    return rows


# vs LHP: single, double, K, BB, out -> PA 5, AB 4, H 2, TB 3
#   avg .500, OBP (2+1)/(4+1) = .600, SLG 3/4 = .750, OPS 1.350
# vs RHP: HR, out, HBP, sac fly -> PA 4, AB 2, H 1, TB 4
#   avg .500, OBP (1+1)/(2+1+1) = .500, SLG 4/2 = 2.000, OPS 2.500
VS_L = ["single", "double", "strikeout", "walk", "field_out"]
VS_R = ["home_run", "field_out", "hit_by_pitch", "sac_fly"]


def frame(rows) -> pd.DataFrame:
    return pd.DataFrame(rows)


def test_derive_computes_rates_per_pitcher_hand():
    df = frame(pa_rows("NYY", "L", VS_L) + pa_rows("NYY", "R", VS_R))

    splits = lp.derive_team_splits(df, "NYY", "2026-07-14")

    assert splits["vl"] == {
        "ops": "1.350",
        "avg": ".500",
        "strikeouts": 1,
        "walks": 1,
        "plate_appearances": 5,
        "k_rate": 20.0,
        "bb_rate": 20.0,
    }
    assert splits["vr"]["ops"] == "2.500"
    assert splits["vr"]["plate_appearances"] == 4
    assert splits["vr"]["strikeouts"] == 0


def test_derive_ignores_the_other_team_batting():
    # Top of the inning with NYY at home is BOS batting.
    df = frame(pa_rows("NYY", "L", VS_L) + pa_rows("BOS", "L", ["home_run"] * 10))

    assert lp.derive_team_splits(df, "NYY", "2026-07-14")["vl"]["plate_appearances"] == 5


def test_derive_batting_team_is_away_in_the_top_half():
    rows = pa_rows("NYY", "L", ["single"], game_date="2026-07-10")
    away_rows = [
        {**r, "home_team": "BOS", "away_team": "NYY", "inning_topbot": "Top"}
        for r in pa_rows("NYY", "L", ["double"])
    ]

    splits = lp.derive_team_splits(frame(rows + away_rows), "NYY", "2026-07-14")

    assert splits["vl"]["plate_appearances"] == 2


def test_derive_drops_rows_after_as_of():
    df = frame(
        pa_rows("NYY", "L", VS_L, game_date="2026-07-14")
        + pa_rows("NYY", "L", ["home_run"] * 7, game_date="2026-07-15")
    )

    splits = lp.derive_team_splits(df, "NYY", "2026-07-14")

    assert splits["vl"]["plate_appearances"] == 5
    assert splits["vl"]["ops"] == "1.350"


def test_derive_only_counts_completed_regular_season_plate_appearances():
    rows = (
        pa_rows("NYY", "L", VS_L)
        + pa_rows("NYY", "L", ["home_run"], game_type="S")  # spring training
        + pa_rows("NYY", "L", ["home_run"], game_type="D")  # postseason
        + pa_rows("NYY", "L", [None, None, "truncated_pa"])  # mid-PA pitches, suspended PA
    )

    splits = lp.derive_team_splits(frame(rows), "NYY", "2026-07-14")

    assert splits["vl"]["plate_appearances"] == 5


def test_derive_omits_a_hand_with_no_plate_appearances():
    splits = lp.derive_team_splits(frame(pa_rows("NYY", "L", VS_L)), "NYY", "2026-07-14")

    assert set(splits) == {"vl"}


def test_derive_returns_empty_without_rows():
    empty = frame(pa_rows("NYY", "L", VS_L, game_date="2026-07-20"))

    assert lp.derive_team_splits(empty, "NYY", "2026-07-14") == {}
    assert lp.derive_team_splits(frame([]), "NYY", "2026-07-14") == {}


# --- Savant fetch -----------------------------------------------------------


def csv_for(rows) -> str:
    # Savant returns many more columns; unused ones must not matter.
    return frame(rows).assign(pitch_type="FF", release_speed=94.0).to_csv(index=False)


@pytest.fixture
def savant(monkeypatch, tmp_path):
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0})
    urls: list[str] = []
    state = {"csv": csv_for(pa_rows("NYY", "L", VS_L)), "sleeps": [], "events": []}

    def fake_get_text(url: str, timeout: int = 60) -> str:
        urls.append(url)
        state["events"].append("request")
        return state["csv"]

    def fake_sleep(seconds: float) -> None:
        state["sleeps"].append(seconds)
        state["events"].append("sleep")

    monkeypatch.setattr(lp, "_get_text", fake_get_text)
    monkeypatch.setattr(lp.time, "sleep", fake_sleep)
    return urls, state


def test_fetch_batting_requests_one_chunk_per_month_from_the_batter_side(savant):
    urls, _ = savant

    lp.fetch_team_batting_statcast("NYY", date(2026, 3, 20), date(2026, 5, 10))

    assert len(urls) == 3
    ranges = [
        (u.split("game_date_gt=")[1].split("&")[0], u.split("game_date_lt=")[1].split("&")[0])
        for u in urls
    ]
    assert ranges == [
        ("2026-03-20", "2026-03-31"),
        ("2026-04-01", "2026-04-30"),
        ("2026-05-01", "2026-05-10"),
    ]
    assert all("player_type=batter" in u and "team=NYY" in u for u in urls)


def test_fetch_batting_refuses_a_truncated_chunk(savant):
    urls, state = savant
    state["csv"] = csv_for(pa_rows("NYY", "L", ["single"] * lp.SAVANT_ROW_CAP))

    with pytest.raises(RuntimeError, match="truncated"):
        lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))


def test_fetch_batting_caches_finished_chunks_but_not_the_current_one(savant):
    urls, _ = savant
    today = date.today()
    first_of_month = today.replace(day=1)
    past_start = date(2026, 4, 1)
    past_end = date(2026, 4, 30)

    lp.fetch_team_batting_statcast("NYY", past_start, past_end)
    lp.fetch_team_batting_statcast("NYY", past_start, past_end)
    assert len(urls) == 1  # second call served from disk

    urls.clear()
    lp.fetch_team_batting_statcast("NYY", first_of_month, today)
    lp.fetch_team_batting_statcast("NYY", first_of_month, today)
    assert len(urls) == 2  # a chunk that includes today is still growing


def test_fetch_batting_waits_two_seconds_between_requests_but_not_before_the_first(savant):
    urls, state = savant

    lp.fetch_team_batting_statcast("NYY", date(2026, 3, 20), date(2026, 5, 10))

    assert lp.SAVANT_PAUSE_SECONDS == 2.0
    assert state["events"] == ["request", "sleep", "request", "sleep", "request"]
    assert state["sleeps"] == [2.0, 2.0]


def test_fetch_batting_cache_hits_make_no_request_and_no_pause(savant):
    urls, state = savant
    lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))
    state["events"].clear()

    lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 4, 30))

    assert state["events"] == []


def test_fetch_batting_aborts_before_exceeding_the_request_cap(savant, monkeypatch):
    urls, _ = savant
    monkeypatch.setattr(lp, "SAVANT_MAX_REQUESTS_PER_RUN", 2)

    with pytest.raises(lp.SavantRequestCapExceeded):
        lp.fetch_team_batting_statcast("NYY", date(2026, 3, 20), date(2026, 5, 10))

    assert len(urls) == 2  # the third request is never made


def test_request_cap_counts_the_whole_run_not_one_call(savant, monkeypatch):
    urls, _ = savant
    monkeypatch.setattr(lp, "SAVANT_MAX_REQUESTS_PER_RUN", 3)
    lp.fetch_team_batting_statcast("NYY", date(2026, 4, 1), date(2026, 5, 31))  # 2 requests

    with pytest.raises(lp.SavantRequestCapExceeded):
        lp.fetch_team_batting_statcast("BOS", date(2026, 4, 1), date(2026, 5, 31))  # 2 more

    assert len(urls) == 3


def test_request_cap_is_210_the_whole_league_once():
    assert lp.SAVANT_MAX_REQUESTS_PER_RUN == 210  # 30 teams x 7 monthly chunks


def test_team_splits_do_not_swallow_the_request_cap(monkeypatch):
    def over_cap(code, start, end):
        raise lp.SavantRequestCapExceeded("cap")

    monkeypatch.setattr(lp, "fetch_team_batting_statcast", over_cap)

    with pytest.raises(lp.SavantRequestCapExceeded):
        lp.fetch_team_splits(147, season=2026, as_of="2026-07-14")


def test_fetch_batting_skips_empty_months(savant):
    _, state = savant
    state["csv"] = ""

    df = lp.fetch_team_batting_statcast("NYY", date(2026, 11, 1), date(2026, 11, 30))

    assert len(df) == 0


# --- fetch_team_splits with as_of -------------------------------------------


def test_team_splits_with_as_of_derive_from_statcast(monkeypatch):
    calls = {}

    def fake_batting(code, start, end):
        calls["args"] = (code, end)
        return frame(pa_rows("NYY", "L", VS_L) + pa_rows("NYY", "R", VS_R))

    monkeypatch.setattr(lp, "fetch_team_batting_statcast", fake_batting)

    splits = lp.fetch_team_splits(147, season=2026, as_of="2026-07-14")

    assert calls["args"] == ("NYY", date(2026, 7, 14))
    assert splits["vl"]["ops"] == "1.350"


def test_team_splits_use_savants_own_code_for_arizona(monkeypatch):
    calls = {}

    def fake_batting(code, start, end):
        calls["code"] = code
        return frame([])

    monkeypatch.setattr(lp, "fetch_team_batting_statcast", fake_batting)

    lp.fetch_team_splits(109, season=2026, as_of="2026-07-14")

    assert calls["code"] == "AZ"


def test_team_splits_with_as_of_return_empty_on_failure(monkeypatch):
    def boom(code, start, end):
        raise OSError("savant down")

    monkeypatch.setattr(lp, "fetch_team_batting_statcast", boom)

    assert lp.fetch_team_splits(147, season=2026, as_of="2026-07-14") == {}


def test_team_splits_with_as_of_return_empty_for_unknown_team(monkeypatch):
    monkeypatch.setattr(
        lp, "fetch_team_batting_statcast", lambda *a: pytest.fail("must not fetch")
    )

    assert lp.fetch_team_splits(999999, season=2026, as_of="2026-07-14") == {}


def test_team_splits_reject_as_of_from_another_season():
    with pytest.raises(ValueError):
        lp.fetch_team_splits(147, season=2026, as_of="2025-07-14")


def test_derived_splits_match_the_shape_of_the_api_splits(monkeypatch):
    monkeypatch.setattr(
        lp,
        "fetch_team_batting_statcast",
        lambda *a: frame(pa_rows("NYY", "L", VS_L)),
    )
    api_keys = {"ops", "avg", "strikeouts", "walks", "plate_appearances", "k_rate", "bb_rate"}

    splits = lp.fetch_team_splits(147, season=2026, as_of="2026-07-14")

    assert set(splits["vl"]) == api_keys
