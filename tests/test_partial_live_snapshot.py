"""A live starter built from a partial snapshot inherits nothing from the demo (QA-08).

Every field the snapshot does not supply is unavailable (None), never the demo
template's value, and the scope never makes an unavailable number look measured.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline import demo_inputs
from data_pipeline import generate_demo_json as gdj
from tests.test_live_starters_no_demo_fields import _fake_live_game

SUMMARY_FIELDS = ("era", "whip", "innings", "strikeouts", "walks", "home_runs_allowed")
UNAVAILABLE = ("N/A", None)  # strings show "N/A", counts are None (the card shows a dash)


@pytest.fixture()
def template() -> dict:
    payload = demo_inputs.build_demo_payload()
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


@pytest.fixture(autouse=True)
def live(monkeypatch):
    monkeypatch.setattr(gdj, "_live", {"run_at": "2026-07-04T12:00:00+00:00", "fetched_date": "2026-07-04", "as_of": "2026-07-03"})


def apply(template: dict, live_starter: dict) -> dict:
    return gdj.live_matchup.build_starter(live_starter, "TAW", 111, gdj._live_through())


def live_starter(template: dict, **overrides) -> dict:
    starter = deepcopy(_fake_live_game(template)["away_starter"])
    starter.update(overrides)
    return starter


def demo_values(template: dict) -> set:
    demo = template["starters"]["away_starter"]
    return {str(demo["season_summary"][k]) for k in SUMMARY_FIELDS}


def test_the_qa_probe_a_summary_with_only_era_keeps_no_demo_numbers(template):
    result = apply(template, live_starter(template, season_summary={"era": "3.10"}))

    summary = result["season_summary"]
    assert summary["era"] == "3.10"
    for field in SUMMARY_FIELDS[1:]:
        assert summary[field] in UNAVAILABLE, f"{field} was inherited from the demo template"


def test_an_empty_summary_is_entirely_unavailable(template):
    result = apply(template, live_starter(template, season_summary={}))

    assert all(result["season_summary"][field] in UNAVAILABLE for field in SUMMARY_FIELDS)
    assert not demo_values(template) & {str(v) for v in result["season_summary"].values()}


def test_a_missing_summary_is_entirely_unavailable(template):
    starter = live_starter(template)
    del starter["season_summary"]

    result = apply(template, starter)

    assert all(result["season_summary"][field] in UNAVAILABLE for field in SUMMARY_FIELDS)


def test_a_partial_pitching_profile_does_not_keep_demo_pitches(template):
    demo_profile = template["starters"]["away_starter"]["pitching_profile"]
    result = apply(template, live_starter(template, pitching_profile={"style_label": "Fastball starter"}))

    profile = result["pitching_profile"]
    assert profile["style_label"] == "Fastball starter"
    assert profile["primary_pitch"] != demo_profile["primary_pitch"]
    assert profile["putaway_pitch"] != demo_profile["putaway_pitch"]
    assert profile["primary_pitch"] == "Not available" and profile["putaway_pitch"] == "Not available"


def test_a_missing_pitching_profile_has_no_demo_labels(template):
    starter = live_starter(template)
    del starter["pitching_profile"]

    result = apply(template, starter)

    profile = result["pitching_profile"]
    assert profile["primary_pitch"] == "Not available"
    assert profile["style_label"] != template["starters"]["away_starter"]["pitching_profile"]["style_label"]


def test_a_complete_snapshot_still_fills_every_field(template):
    result = apply(template, live_starter(template))

    summary = result["season_summary"]
    assert (summary["era"], summary["whip"], summary["innings"]) == ("3.10", "1.05", "101.0")
    assert (summary["strikeouts"], summary["walks"], summary["home_runs_allowed"]) == (110, 30, 10)
    assert summary["scopes"]["counts"]["kind"] == "regular_season"
    assert summary["scopes"]["season_rates"]["kind"] == "regular_season"
