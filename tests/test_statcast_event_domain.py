"""QA5-02: an unrecognized event cannot be measured as an out or zero rate.

Sources mirror the existing Statcast/Savant fixtures; all external calls are
mocked. Removing event validation must restore probe C and the no-API labels.
"""

from __future__ import annotations

import pandas as pd
import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import validate_payload
from tests import test_as_of_end_to_end as e2e
from tests.live_helpers import snapshot_from_starters, use_snapshot
from tests.test_as_of_end_to_end import leaky_sources  # noqa: F401
from tests.test_live_sample_pipeline import API_STATS, NO_SPLITS, events_frame, isolated, route  # noqa: F401
from tests.test_team_splits_as_of import pa_rows


def published_run(monkeypatch, record, snapshot):
    cache_manager.save_processed("live_run", record)
    cache_manager.save_processed("live_matchup", snapshot)
    live, status = gdj._resolve_live_input()
    monkeypatch.setattr(gdj, "_live", live)
    monkeypatch.setattr(gdj, "_live_status", status)
    payload = gdj.build_payload()
    validate_payload(payload)
    return payload


@pytest.mark.parametrize("event,code", [(None, "unusable_column"), ("provider_error", "unknown_value")])
def test_probe_c_unusable_team_events_publish_unavailable_offense_and_record_the_error(leaky_sources, monkeypatch, event, code):
    source = pd.DataFrame(pa_rows("NYY", "R", [event] * 200))
    monkeypatch.setattr(lp, "fetch_team_batting_statcast", lambda *args, **kwargs: source.copy())

    record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)

    assert snapshot is not None
    assert any(error["source"] == "savant_team_batting" and error["code"] == code for error in record["errors"])
    payload = published_run(monkeypatch, record, snapshot)
    offense = payload["matchups"][0]["teams"]["home"]["offense_profile"]
    assert offense["ops_vs_hand"] is None
    assert offense["k_rate_vs_hand"] is None and offense["bb_rate_vs_hand"] is None
    assert offense["scope"] is None and offense["summary_label"] is None


@pytest.mark.parametrize("event,code", [(None, "unusable_column"), ("provider_error", "unknown_value")])
@pytest.mark.parametrize("api", [NO_SPLITS, API_STATS], ids=["no-api", "complete-api"])
def test_bad_pitcher_events_disable_statcast_counts_but_keep_sound_figures(monkeypatch, event, code, api):
    source = events_frame(n_plain=300)
    source["events"] = event
    route(monkeypatch, [("/stats?", api)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: source.copy())

    result = lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03")

    assert result is not None and result["sample"]["arsenal"]["pitches"] == 320
    assert result["pitch_mix"] and result["velocity_by_pitch"] and result["movement"]
    assert result["pitch_locations"]["vs_rhh"] and result["throws"] == "R"
    assert [(error["source"], error["code"]) for error in lp._run_errors] == [("statcast_pitcher", code)]
    rates = result["sample"]["rates"]
    if api == NO_SPLITS:
        assert rates["source"] == "unavailable" and rates["scope"] is None
        assert [rates[key] for key in ("batters_faced", "strikeouts", "walks", "home_runs")] == [None] * 4
        assert result["pitching_profile"]["swing_miss_label"] is None
        assert result["pitching_profile"]["command_label"] is None
        assert result["pitching_profile"]["contact_risk_label"] is None
    else:
        assert rates["source"] == "mlb_api"
        assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (19, 0, 2, 1)
    use_snapshot(monkeypatch, snapshot_from_starters(result, {**result, "name": "Bravo Liveleft"}))
    validate_payload(gdj.build_payload())


def test_one_unknown_event_invalidates_the_whole_counts_group_even_among_known_events(monkeypatch):
    source = events_frame()
    source.loc[0, "events"] = "provider_error"
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: source)

    result = lp.fetch_pitcher_statcast(11, "Mixed Events", as_of="2026-07-03")

    assert result is not None and result["sample"]["rates"]["source"] == "unavailable"
    assert result["sample"]["rates"]["batters_faced"] is None
    assert lp._run_errors[0]["code"] == "unknown_value"


def test_one_unknown_team_event_is_checked_before_any_filtering():
    source = pd.DataFrame(pa_rows("NYY", "R", ["field_out"]) + pa_rows("BOS", "L", ["provider_error"], game_date="2026-07-20", game_type="S"))
    with pytest.raises(lp.UnknownValue, match="events"):
        lp.derive_team_splits(source, "NYY", "2026-07-14")


def test_split_line_cannot_default_an_unknown_outcome_to_an_out():
    with pytest.raises(lp.UnknownValue, match="events"):
        lp._split_line(pd.Series(["single", "provider_error"]))


def test_control_null_pitches_and_truncated_plate_appearances_do_not_inflate_counts():
    source = events_frame()
    counts = lp._statcast_counts(source)
    assert (counts["batters_faced"], counts["strikeouts"], counts["walks"], counts["home_runs"]) == (19, 4, 3, 2)
    team = pd.DataFrame(pa_rows("NYY", "R", [None, "truncated_pa", "single", "field_out"]))
    assert lp.derive_team_splits(team, "NYY", "2026-07-14")["vr"] == {
        "ops": "1.000", "avg": ".500", "strikeouts": 0, "walks": 0,
        "plate_appearances": 2, "k_rate": 0.0, "bb_rate": 0.0,
    }


def test_control_only_known_non_pa_events_and_empty_answers_are_valid():
    source = pd.DataFrame(pa_rows("NYY", "R", [None, "truncated_pa"]))
    assert lp.derive_team_splits(source, "NYY", "2026-07-14") == {}
    assert lp.derive_team_splits(pd.DataFrame(), "NYY", "2026-07-14") == {}


def test_partial_api_counts_survive_unknown_statcast_events(monkeypatch):
    api = {"stats": [{"splits": [{"stat": {"era": "3.10", "baseOnBalls": 2}}]}]}
    route(monkeypatch, [("/stats?", api)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: events_frame().assign(events="provider_error"))

    result = lp.fetch_pitcher_statcast(11, "Partial API", as_of="2026-07-03")

    assert result is not None
    rates = result["sample"]["rates"]
    assert rates["source"] == "mlb_api" and rates["walks"] == 2
    assert rates["batters_faced"] is None and rates["strikeouts"] is None
    assert result["season_summary"]["era"] == "3.10"
    assert result["pitching_profile"]["command_label"] is None


def test_unknown_pitcher_events_are_checked_before_date_filtering(monkeypatch):
    source = events_frame()
    source.loc[0, "events"] = "provider_error"
    source.loc[0, "game_date"] = source.loc[0, "game_date"].replace(day=20)
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: source)

    result = lp.fetch_pitcher_statcast(11, "Filtered Event", as_of="2026-07-03")

    assert result is not None and result["sample"]["arsenal"]["pitches"] == 169
    assert result["sample"]["rates"]["batters_faced"] is None
    assert lp._run_errors[0]["code"] == "unknown_value"


def test_control_known_completed_events_keep_their_scoring_class_in_both_paths():
    # These are the observed cached event values plus existing compound-event
    # fixtures. 21 PA: 4 hits / 10 bases, 2 BB, 2 K, 1 HBP, 2 SF, 2 SH, 1 CI.
    events = ["single", "double", "triple", "home_run", "walk", "intent_walk",
              "strikeout", "strikeout_double_play", "hit_by_pitch", "sac_fly",
              "sac_fly_double_play", "sac_bunt", "sac_bunt_double_play", "catcher_interf",
              "field_out", "force_out", "grounded_into_double_play", "double_play",
              "field_error", "fielders_choice", "fielders_choice_out"]
    counts = lp._statcast_counts(pd.DataFrame({"events": events, "game_type": "R"}))
    assert (counts["batters_faced"], counts["strikeouts"], counts["walks"], counts["home_runs"]) == (21, 2, 2, 1)
    line = lp.derive_team_splits(pd.DataFrame(pa_rows("NYY", "R", events)), "NYY", "2026-07-14")["vr"]
    assert line == {"ops": "1.158", "avg": ".308", "strikeouts": 2, "walks": 2,
                    "plate_appearances": 21, "k_rate": 9.5, "bb_rate": 9.5}
