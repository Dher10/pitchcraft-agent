"""QA5-02 c2: check the closed event domain against one saved MLB response.

Only the fixture acquisition requested by the owner used the network. These
tests use the real derivations and pipeline with mocked transport and caches.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.fetchers.statcast_events import COMPLETED_EVENTS, STATCAST_EVENTS
from tests import test_as_of_end_to_end as e2e
from tests.live_helpers import snapshot_from_starters, use_snapshot
from tests.test_as_of_end_to_end import leaky_sources  # noqa: F401
from tests.test_live_sample_pipeline import NO_SPLITS, events_frame, isolated, route  # noqa: F401
from tests.test_statcast_event_domain import published_run
from tests.test_team_splits_as_of import pa_rows


METADATA = json.loads((Path(__file__).parent / "fixtures/mlb_event_types_2026-10-17.json").read_bytes())
# Independently enumerated scoring classes. No catch-all for a new PA code.
PA_CLASSES = {
    "single": ("hit", 1), "double": ("hit", 2),
    "triple": ("hit", 3), "home_run": ("hit", 4),
    "walk": ("walk", 0), "intent_walk": ("walk", 0),
    "strikeout": ("strikeout", 0), "strike_out": ("strikeout", 0),
    "strikeout_double_play": ("strikeout", 0), "strikeout_triple_play": ("strikeout", 0),
    "hit_by_pitch": ("hit_by_pitch", 0),
    "sac_fly": ("sac_fly", 0), "sac_fly_double_play": ("sac_fly", 0),
    "sac_bunt": ("sac_bunt", 0), "sac_bunt_double_play": ("sac_bunt", 0),
    "catcher_interf": ("interference", 0),
    "field_out": ("out", 0), "force_out": ("out", 0),
    "grounded_into_double_play": ("out", 0), "double_play": ("out", 0),
    "triple_play": ("out", 0), "fielders_choice_out": ("out", 0),
    "batter_interference": ("out", 0),
    "field_error": ("at_bat", 0), "fielders_choice": ("at_bat", 0),
    "fan_interference": ("at_bat", 0), "os_ruling_pending_primary": ("at_bat", 0),
}


def test_metadata_codes_are_unique_and_every_pa_has_an_explicit_scoring_class():
    codes = [event["code"] for event in METADATA]
    assert len(codes) == len(set(codes)) == 74
    assert set(PA_CLASSES) == {event["code"] for event in METADATA if event["plateAppearance"]}
    # truncated_pa is a documented Savant-only non-PA value retained from c.
    assert set(STATCAST_EVENTS) == set(codes) | {"truncated_pa"}


@pytest.mark.parametrize("event", METADATA, ids=lambda event: event["code"])
def test_every_metadata_code_has_the_right_pa_status_and_scoring_class(event):
    code = event["code"]
    outcome = STATCAST_EVENTS.get(code)
    assert outcome is not None, code
    expected = PA_CLASSES[code] if event["plateAppearance"] else ("non_pa", 0)
    assert (outcome.kind, outcome.bases) == expected
    assert (code in COMPLETED_EVENTS) == event["plateAppearance"]
    assert (outcome.kind == "hit") == event["hit"]

    # Both numerical readers must honor the metadata; e.g. a runner out
    # contributes no PA, while a triple play contributes exactly one.
    counts = lp._statcast_counts(pd.DataFrame({"events": ["single", code], "game_type": "R"}))
    assert counts["batters_faced"] == 1 + int(event["plateAppearance"])
    assert counts["strikeouts"] == int(expected[0] == "strikeout")
    assert counts["walks"] == int(expected[0] == "walk")
    assert counts["home_runs"] == int(expected[1] == 4)
    line = lp._split_line(pd.Series(["single", code]))
    assert line["plate_appearances"] == counts["batters_faced"]
    assert line["strikeouts"] == counts["strikeouts"] and line["walks"] == counts["walks"]


def month_frame():
    rows = []
    # A 30-day month, 600 completed PA plus intermediate pitch rows. Both
    # pitcher hands occur, and the last day includes inning-ending events.
    daily = [None] * 60 + ["single"] * 2 + ["double"] + ["walk"] * 2 + ["strikeout"] * 4 + ["field_out"] * 11
    for day in range(1, 31):
        rows += pa_rows("NYY", "L" if day % 2 else "R", daily, game_date=f"2026-06-{day:02d}")
    rows += pa_rows("NYY", "R", ["caught_stealing_2b", "pickoff_1b", "triple_play"], game_date="2026-06-30")
    return pd.DataFrame(rows)


def test_realistic_team_month_keeps_figures_with_runner_outs_and_a_triple_play(leaky_sources, monkeypatch):
    source = month_frame()
    monkeypatch.setattr(lp, "fetch_team_batting_statcast", lambda *args, **kwargs: source.copy())
    record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)
    assert snapshot is not None
    assert not any(error["code"] == "unknown_value" for error in record["errors"])
    splits = lp.derive_team_splits(source, "NYY", "2026-06-30")
    assert splits["vl"]["plate_appearances"] == 300
    assert splits["vr"] == {
        "ops": ".471", "avg": ".166", "strikeouts": 60, "walks": 30,
        "plate_appearances": 301, "k_rate": 19.9, "bb_rate": 10.0,
    }
    payload = published_run(monkeypatch, record, snapshot)
    offense = payload["matchups"][0]["teams"]["home"]["offense_profile"]
    assert offense["ops_vs_hand"] is not None
    assert offense["k_rate_vs_hand"] is not None and offense["scope"] is not None


def test_starter_keeps_statcast_counts_with_runner_outs_and_a_triple_play(monkeypatch):
    source = events_frame(n_plain=300)
    extra = source.iloc[:3].copy()
    extra["events"] = ["caught_stealing_2b", "pickoff_1b", "triple_play"]
    source = pd.concat([source, extra], ignore_index=True)
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: source.copy())
    result = lp.fetch_pitcher_statcast(11, "Metadata Starter", as_of="2026-07-03")
    assert result is not None and lp._run_errors == []
    rates = result["sample"]["rates"]
    assert rates["source"] == "statcast" and rates["scope"] is not None
    assert tuple(rates[key] for key in ("batters_faced", "strikeouts", "walks", "home_runs")) == (20, 4, 3, 2)
    assert result["sample"]["arsenal"]["pitches"] == 323
    use_snapshot(monkeypatch, snapshot_from_starters(result, {**result, "name": "Other Starter"}))
    from data_pipeline import generate_demo_json as gdj
    from data_pipeline.validators import validate_payload
    validate_payload(gdj.build_payload())


def test_control_provider_error_remains_unknown_in_both_paths(monkeypatch):
    assert "provider_error" not in {event["code"] for event in METADATA}
    with pytest.raises(lp.UnknownValue, match="provider_error"):
        lp.derive_team_splits(month_frame().assign(events="provider_error"), "NYY", "2026-06-30")
    route(monkeypatch, [("/stats?", NO_SPLITS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *args, **kwargs: events_frame().assign(events="provider_error"))
    result = lp.fetch_pitcher_statcast(11, "Unknown Starter", as_of="2026-07-03")
    assert result is not None and result["sample"]["rates"]["source"] == "unavailable"
    assert lp._run_errors[0]["code"] == "unknown_value"
