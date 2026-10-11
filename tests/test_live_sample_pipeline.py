"""The live pipeline builds the sample, scopes and labels for each starter (PLAN.md P0.5).

Statcast and the MLB API are mocked; the cache is redirected to tmp_path.
"""

from __future__ import annotations

from datetime import date
import json

import pandas as pd
import pytest

from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp


class FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


API_STATS = {
    "stats": [
        {
            "splits": [
                {
                    "stat": {
                        "era": "3.10",
                        "whip": "1.05",
                        "inningsPitched": "101.0",
                        "strikeOuts": 0,  # a real zero must not fall back to Statcast
                        "baseOnBalls": 20,
                        "homeRuns": 5,
                        "battersFaced": 400,
                    }
                }
            ]
        }
    ]
}
NO_SPLITS = {"stats": [{"splits": []}]}


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(cache_manager, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )
    return tmp_path


def route(monkeypatch, handlers):
    """urlopen -> first handler whose key is in the URL."""

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        for key, payload in handlers:
            if key in url:
                if isinstance(payload, Exception):
                    raise payload
                return FakeResponse(payload)
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)


def frame(extra_rows=(), n_plain=150, game_type="R", game_date="2026-07-01"):
    base = {
        "game_date": pd.Timestamp(game_date),
        "game_type": game_type,
        "pitch_type": "FF",
        "stand": "R",
        "p_throws": "R",
        "release_speed": 94.0,
        "pfx_x": 0.5,
        "pfx_z": 1.1,
        "plate_x": 0.1,
        "plate_z": 2.5,
        "events": None,
    }
    rows = [dict(base) for _ in range(n_plain)]
    rows += [{**base, **extra} for extra in extra_rows]
    return pd.DataFrame(rows)


# 19 completed plate appearances (4 K, 3 BB, 2 HR, 10 outs) plus one truncated PA.
EVENTS = (
    ["strikeout"] * 3
    + ["strikeout_double_play"]
    + ["walk"] * 2
    + ["intent_walk"]
    + ["home_run"] * 2
    + ["field_out"] * 10
    + ["truncated_pa"]
)


def events_frame(**kw):
    return frame(extra_rows=[{"events": e} for e in EVENTS], **kw)


# --- sample from Statcast when the API has nothing ------------------------------------------------


def test_sample_falls_back_to_statcast_events_and_says_so(monkeypatch):
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: events_frame())

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    rates = result["sample"]["rates"]
    assert rates["source"] == "statcast"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (
        19,
        4,
        3,
        2,
    )  # strikeout_double_play and intent_walk count; truncated_pa is not a plate appearance
    assert result["sample"]["arsenal"]["pitches"] == 150 + len(EVENTS)
    assert rates["scope"]["kind"] == "regular_season"
    assert rates["scope"]["through"] == "2026-07-14"
    assert result["sample"]["limited"] == {"arsenal": False, "strikeout": True, "control": True}


# --- sample from the MLB API ------------------------------------------------------------------------


def test_api_numbers_win_and_a_real_zero_is_kept(monkeypatch):
    route(monkeypatch, [("/stats?", API_STATS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: events_frame())

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    rates = result["sample"]["rates"]
    assert rates["source"] == "mlb_api"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (
        400,
        0,
        20,
        5,
    )
    assert result["season_summary"]["strikeouts"] == 0
    assert result["season_summary"]["era"] == "3.10"
    # 0 strikeouts in 400 BF is a real rate: below-average swing-and-miss, not "no data"
    assert result["pitching_profile"]["swing_miss_label"] == "Below-average swing-and-miss ability"


def test_season_summary_carries_the_scope_of_the_api_figures(monkeypatch):
    route(monkeypatch, [("/stats?", API_STATS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: events_frame())

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-07-14")

    assert result["season_summary"]["scope"] == {
        "kind": "regular_season",
        "through": "2026-07-14",
        "label": "regular season through 2026-07-14",
    }


# --- scopes: postseason pitches are in the arsenal, not in the API stats ----------------------------


def test_postseason_pitches_make_the_arsenal_scope_different_from_the_api_rates(monkeypatch):
    route(monkeypatch, [("/stats?", API_STATS)])
    mixed = pd.concat(
        [events_frame(), frame(n_plain=30, game_type="D", game_date="2026-10-05")],
        ignore_index=True,
    )
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: mixed)

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-10-08")

    sample = result["sample"]
    assert sample["arsenal"]["scope"]["kind"] == "regular_and_postseason"
    assert sample["arsenal"]["scope"]["through"] == "2026-10-08"
    assert sample["rates"]["scope"]["kind"] == "regular_season"
    assert result["season_summary"]["scope"]["kind"] == "regular_season"


def test_postseason_pitches_after_as_of_do_not_change_the_scope(monkeypatch):
    route(monkeypatch, [("/stats?", API_STATS)])
    mixed = pd.concat(
        [events_frame(), frame(n_plain=30, game_type="D", game_date="2026-10-05")],
        ignore_index=True,
    )
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: mixed)

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-10-01")

    assert result["sample"]["arsenal"]["scope"]["kind"] == "regular_season"


def test_statcast_fallback_counts_inherit_the_postseason_scope(monkeypatch):
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    mixed = pd.concat(
        [events_frame(), frame(n_plain=30, game_type="D", game_date="2026-10-05")],
        ignore_index=True,
    )
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: mixed)

    result = lp.fetch_pitcher_statcast(11, "Test Pitcher", as_of="2026-10-08")

    sample = result["sample"]
    assert sample["rates"]["source"] == "statcast"
    assert sample["rates"]["scope"]["kind"] == "regular_and_postseason"


def test_a_pitcher_with_no_season_stats_is_not_an_error(monkeypatch):
    # The API answers {"stats": []} for someone with no pitching this season
    # (a debut): that is "no data", not a failed request.
    route(monkeypatch, [("/stats?", {"stats": []})])

    assert lp.fetch_pitcher_season_stats(22, as_of="2026-07-14") == {}

    assert lp._run_errors == []


# --- Gherkin: debut with zero pitches ----------------------------------------------------------------


EMPTY = pd.DataFrame(
    columns=["game_date", "game_type", "pitch_type", "stand", "p_throws", "events"]
)
PERSON_LEFTY = {"people": [{"id": 22, "pitchHand": {"code": "L"}}]}


def test_a_debut_becomes_a_starter_with_every_dimension_limited(monkeypatch):
    route(monkeypatch, [("/stats?", NO_SPLITS), ("/people/", PERSON_LEFTY)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: EMPTY)

    result = lp.fetch_pitcher_statcast(22, "Debut Lefty", as_of="2026-07-14")

    assert result is not None
    assert result["throws"] == "L"
    assert result["pitch_mix"] == [] and result["velocity_by_pitch"] == []
    assert result["sample"]["arsenal"]["pitches"] == 0
    assert result["sample"]["limited"] == {"arsenal": True, "strikeout": True, "control": True}
    assert result["pitching_profile"]["swing_miss_label"] is None
    assert result["pitching_profile"]["command_label"] is None
    assert result["pitching_profile"]["contact_risk_label"] is None
    assert result["pitching_profile"]["style_label"] == "Arsenal data limited"
    assert result["season_summary"]["strikeouts"] is None  # unknown, not zero
    assert lp._run_errors == []


def test_a_debut_whose_hand_cannot_be_fetched_fails_with_a_recorded_error(monkeypatch):
    route(monkeypatch, [("/stats?", NO_SPLITS), ("/people/", OSError("people down"))])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: EMPTY)

    assert lp.fetch_pitcher_statcast(22, "Debut Lefty", as_of="2026-07-14") is None

    assert [e["source"] for e in lp._run_errors] == ["mlb_person"]


def test_rows_without_a_usable_pitch_type_are_treated_as_no_pitches(monkeypatch):
    route(monkeypatch, [("/stats?", NO_SPLITS), ("/people/", PERSON_LEFTY)])
    blank = frame(n_plain=5)
    blank["pitch_type"] = None
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: blank)

    result = lp.fetch_pitcher_statcast(22, "Debut Lefty", as_of="2026-07-14")

    assert result["sample"]["arsenal"]["pitches"] == 0


SCHEDULE = {
    "dates": [
        {
            "games": [
                {
                    "gamePk": 1,
                    "gameDate": "2026-07-15T23:05:00Z",
                    "status": {"abstractGameState": "Preview"},
                    "venue": {"name": "Yankee Stadium"},
                    "teams": {
                        "away": {
                            "team": {"id": 111, "name": "Boston Red Sox"},
                            "probablePitcher": {"id": 11, "fullName": "Veteran Righty"},
                        },
                        "home": {
                            "team": {"id": 147, "name": "New York Yankees"},
                            "probablePitcher": {"id": 22, "fullName": "Debut Lefty"},
                        },
                    },
                }
            ]
        }
    ]
}


def test_a_game_with_a_debut_starter_is_shown_not_skipped(monkeypatch, isolated):
    route(
        monkeypatch,
        [
            ("schedule", SCHEDULE),
            ("teams/", {"stats": []}),
            ("/people/22/stats", NO_SPLITS),
            ("/people/11/stats", API_STATS),
            ("/people/22", PERSON_LEFTY),
        ],
    )
    monkeypatch.setattr(
        lp,
        "statcast_pitcher",
        lambda start, end, player_id: events_frame() if player_id == 11 else EMPTY,
    )

    exit_code = lp.main_with_args("2026-07-15", "2026-07-14")  # also exercises the summary prints

    assert exit_code == 0
    run = json.loads((isolated / "processed" / "live_run.json").read_text())
    assert run["status"] == "ok" and run["games_live"] == 1 and run["skipped_games"] == []
    snapshot = json.loads((isolated / "processed" / "live_matchup.json").read_text())
    assert snapshot["home_starter"]["sample"]["limited"]["arsenal"] is True
    assert snapshot["away_starter"]["sample"]["limited"]["arsenal"] is False


# --- the old count-based logic is gone -------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "derive_swing_miss_label",
        "derive_command_label",
        "derive_contact_risk_label",
        "update_pitching_profile_labels",
    ],
)
def test_count_based_label_functions_no_longer_exist(name):
    assert not hasattr(lp, name)


def test_the_generator_has_no_count_based_labels_either():
    from data_pipeline import generate_demo_json as gdj

    for name in ("_derive_swing_miss_label", "_derive_command_label", "_derive_contact_risk_label", "_sanitize_pitching_profile"):
        assert not hasattr(gdj, name)
