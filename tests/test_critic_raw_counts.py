"""The critic decides on raw pitch counts, never on the rounded share (QA3-03).

QA3-03 probe: 3,000 Four-seams in 10,010 pitches is 29.97%. The chart shows 30.0%, and the critic,
which read the chart, declared the 30% "primary pitch" minimum met. The structured pitch mix now
carries `count` (that pitch) and `total` (the starter's pitches behind the shares); the critic
compares those with `labels.share_at_least`. The chart keeps showing the rounded share. Rows
without counts (the demo, snapshots written before this) keep using the percentage.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents import critic
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_critic_attribution import isolated  # noqa: F401  (fixture)
from tests.test_critic_pitch_names import A, B, matchup as pitch_matchup
from tests.test_live_sample_pipeline import API_STATS, frame, route
from tests.test_live_starters_no_demo_fields import _fake_live_game

ROOT = Path(__file__).resolve().parents[1]
TOTAL = 10_010
PRIMARY_MIN = labels.PRIMARY_MIN_USAGE_PCT


def frame_for(counts: dict[str, int]):
    return frame(
        n_plain=0,
        extra_rows=[{"pitch_type": code} for code, n in counts.items() for _ in range(n)],
    )


def primary_counts(four_seam: int) -> dict[str, int]:
    """Four-seam is the most used pitch with `four_seam` of 10,010 pitches."""

    rest = TOTAL - four_seam
    return {"FF": four_seam, "SL": 2500, "CH": 2000, "CU": 1500, "SI": rest - 6000}


HEALTHY = {"FF": 150, "SL": 50}


def payload_for(monkeypatch, away: dict[str, int], home: dict[str, int] = HEALTHY) -> dict:
    """Both starters through the real fetchers, the real charts and the real generator."""

    route(monkeypatch, [("/stats?", API_STATS), ("/people/", {"people": [{"pitchHand": {"code": "R"}}]})])

    def fetch(pitcher_id: int, name: str, counts: dict[str, int]):
        monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame_for(counts))
        return lp.fetch_pitcher_statcast(pitcher_id, name, as_of="2026-07-14")

    away_data = fetch(11, "Boundary Ace", away)
    home_data = fetch(22, "Home Ace", home)
    template = next(m for m in demo_inputs.build_demo_payload()["matchups"] if m["id"] == "matchup_001")
    live = _fake_live_game(template)
    live.update(
        away_starter=away_data,
        home_starter=home_data,
        combined_charts={
            "pitch_mix": lp._combine_pitch_mix(away_data, home_data),
            "velocity_by_pitch": lp._combine_velocity(away_data, home_data),
        },
    )
    monkeypatch.setattr(
        gdj, "_live", {"fetched_date": "2026-07-15", "as_of": "2026-07-14", "live_games": [live]}
    )
    monkeypatch.setattr(
        gdj, "_live_status", {"mode": "fetched_snapshot", "reason": "Live run ok", "live_run": None}
    )
    return gdj.build_payload()


def live_matchup(payload: dict) -> dict:
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


def primary_check(matchup: dict, name: str = "Boundary Ace") -> dict:
    checks = matchup["critic_review"]["checks"]
    return next(c for c in checks if c["claim"].startswith(f"{name}'s primary pitch"))


# --- the structured mix carries the counts ---------------------------------------------------------


def test_the_pitch_mix_row_carries_the_raw_count_and_the_total():
    result = lp.process_pitcher_statcast(frame_for({"FF": 2126, "SL": 374}), "Counts")

    four_seam, slider = result["pitch_mix"]
    assert (four_seam["away_starter"]["count"], four_seam["away_starter"]["total"]) == (2126, 2500)
    assert (slider["away_starter"]["count"], slider["away_starter"]["total"]) == (374, 2500)
    assert slider["away_starter"]["overall"] == 15.0  # the chart still shows the rounded share


def test_a_pitch_the_other_starter_never_threw_has_count_zero_and_his_own_total(monkeypatch, isolated):
    payload = payload_for(monkeypatch, {"FF": 100, "SL": 50}, {"FF": 120, "CH": 30})

    rows = {r["pitch"]: r for r in live_matchup(payload)["charts"]["pitch_mix"]}
    assert rows["Slider"]["home_starter"] == {
        "overall": 0, "vs_lhh": 0, "vs_rhh": 0, "count": 0, "total": 150
    }
    assert (rows["Slider"]["away_starter"]["count"], rows["Slider"]["away_starter"]["total"]) == (50, 150)


def test_a_starter_with_no_pitches_has_total_zero_in_every_row(monkeypatch, isolated):
    payload = payload_for(monkeypatch, {"FF": 100, "SL": 50}, {})

    for row in live_matchup(payload)["charts"]["pitch_mix"]:
        assert (row["home_starter"]["count"], row["home_starter"]["total"]) == (0, 0)


# --- QA3-03: the 30% boundary ----------------------------------------------------------------------


def test_the_qa_probe_29_97_percent_is_not_a_primary_pitch_even_though_the_chart_says_30(monkeypatch, isolated):
    payload = payload_for(monkeypatch, primary_counts(3000))
    live = live_matchup(payload)

    row = next(r for r in live["charts"]["pitch_mix"] if r["pitch"] == "Four-seam")
    assert row["away_starter"]["overall"] == 30.0  # display
    check = primary_check(live)
    assert check["status"] == "warning"
    assert "3,000 of 10,010" in check["evidence"]
    assert any(check["evidence"] in note for note in live["critic_review"]["revision_notes"])
    assert failed(payload) == []  # a warning does not block publication


@pytest.mark.parametrize("four_seam", [3003, 3004])  # exactly 30.00% and just above
def test_30_percent_exactly_and_above_are_a_primary_pitch(monkeypatch, isolated, four_seam):
    live = live_matchup(payload_for(monkeypatch, primary_counts(four_seam)))

    assert primary_check(live)["status"] == "supported"


def put_away_game(count: int, total: int = 2500) -> dict:
    """The away starter's Slider is his put-away pitch with `count` of `total` pitches (15.0% shown)."""

    game = pitch_matchup(away={"Four-seam": 85.0, "Slider": 15.0}, home={"Four-seam": 70.0, "Slider": 30.0})
    for row in game["charts"]["pitch_mix"]:
        slot = row["away_starter"]
        slot["count"] = count if row["pitch"] == "Slider" else total - count
        slot["total"] = total
    return game


def put_away_check(game: dict) -> dict:
    review = critic.run({"headline": "h", "short_summary": [], "sections": []}, game)
    return next(c for c in review["checks"] if c["claim"] == f"{A}'s put-away pitch is Slider.")


@pytest.mark.parametrize(
    "count, status", [(374, "warning"), (375, "supported"), (376, "supported")]
)  # 14.96%, 15.00%, 15.04%: the chart shows 15.0 for all three
def test_the_15_percent_put_away_minimum_is_checked_on_counts(count, status):
    check = put_away_check(put_away_game(count))

    assert check["status"] == status, check
    if status == "warning":
        assert "374 of 2,500" in check["evidence"]


# --- rows without counts keep the percentage -------------------------------------------------------


@pytest.mark.parametrize("share, status", [(29.9, "warning"), (30.0, "supported"), (30.1, "supported")])
def test_a_row_without_counts_uses_the_percentage(share, status):
    rest = round((100 - share) / 3, 1)  # three other pitches, each below the Four-seam
    game = pitch_matchup(
        away={"Four-seam": share, "Slider": rest, "Changeup": rest, "Curveball": rest},
        home={"Four-seam": 70.0, "Slider": 30.0},
    )
    review = critic.run({"headline": "h", "short_summary": [], "sections": []}, game)

    primary = next(c for c in review["checks"] if c["claim"] == f"{A}'s primary pitch is Four-seam.")
    assert primary["status"] == status


# --- a pitch thrown under 0.05% of the time was still thrown ---------------------------------------


def test_a_pitch_that_rounds_to_zero_percent_was_still_thrown():
    game = pitch_matchup(away={"Four-seam": 100.0, "Eephus": 0.0}, home={"Four-seam": 100.0})
    for row in game["charts"]["pitch_mix"]:
        row["away_starter"].update(count=1 if row["pitch"] == "Eephus" else 2999, total=3000)
        row["home_starter"].update(count=3000 if row["pitch"] == "Four-seam" else 0, total=3000)
    report = {"headline": "h", "short_summary": [], "sections": [
        {"title": "t", "body": f"{A} threw an eephus once in a while."}]}

    review = critic.run(report, game)

    names = next(c for c in review["checks"] if c["claim"] == "The report names only pitches that appear in the pitch mix.")
    assert names["status"] == "supported", names


def test_a_pitch_with_count_zero_was_not_thrown_even_if_the_share_field_says_otherwise():
    game = pitch_matchup(away={"Four-seam": 100.0}, home={"Four-seam": 100.0, "Slider": 12.0})
    for row in game["charts"]["pitch_mix"]:
        for slot in ("away_starter", "home_starter"):
            row[slot].update(count=0 if (slot, row["pitch"]) == ("home_starter", "Slider") else 100, total=100)
    report = {"headline": "h", "short_summary": [], "sections": [
        {"title": "t", "body": f"{B} has a slider."}]}

    review = critic.run(report, game)

    names = next(c for c in review["checks"] if c["claim"] == "The report names only pitches that appear in the pitch mix.")
    assert names["status"] == "unsupported"


# --- publication needs the counts of a live matchup ------------------------------------------------


def failed(payload: dict) -> list[str]:
    """The names of the checks publication validation fails (it raises when there are any)."""

    try:
        validate_payload(payload)
    except ValidationError as error:
        return [check.description for check in error.checks if not check.passed]
    return []


def test_a_live_matchup_with_consistent_counts_validates(monkeypatch, isolated):
    assert failed(payload_for(monkeypatch, primary_counts(3003))) == []


@pytest.mark.parametrize("missing", ["count", "total"])
def test_a_live_pitch_mix_row_without_its_count_or_total_fails_publication(monkeypatch, isolated, missing):
    payload = payload_for(monkeypatch, primary_counts(3003))
    del live_matchup(payload)["charts"]["pitch_mix"][0]["away_starter"][missing]

    assert failed(payload), "a live row without counts was accepted"


def test_counts_that_disagree_with_the_sample_fail_publication(monkeypatch, isolated):
    payload = payload_for(monkeypatch, primary_counts(3003))
    live = live_matchup(payload)
    for row in live["charts"]["pitch_mix"]:
        row["away_starter"]["total"] = 9_999

    assert failed(payload)


def test_a_count_larger_than_its_total_fails_publication(monkeypatch, isolated):
    payload = payload_for(monkeypatch, primary_counts(3003))
    live_matchup(payload)["charts"]["pitch_mix"][0]["away_starter"]["count"] = TOTAL + 1

    assert failed(payload)


def test_demo_rows_without_counts_still_validate():
    payload = json.loads((ROOT / "public" / "data" / "pitchcraft-demo.json").read_text(encoding="utf-8"))
    assert "count" not in json.dumps(payload["matchups"][0]["charts"]["pitch_mix"])
    assert failed(payload) == []


# --- a missing strength dimension is not a score of zero -------------------------------------------


def test_a_missing_command_dimension_never_prints_a_zero_score():
    game = pitch_matchup(away={"Four-seam": 70.0, "Slider": 30.0}, home={"Four-seam": 70.0, "Slider": 30.0})
    game["starters"]["away_starter"]["pitching_profile"]["command_label"] = "Plus command"
    game["charts"]["strength_profile"] = [{"dimension": "Velocity", "away_starter": 80, "home_starter": 70}]
    report = {"headline": "h", "short_summary": [], "sections": [
        {"title": "t", "body": f"{A} has plus command."}]}

    review = critic.run(report, game)

    check = next(c for c in review["checks"] if c["claim"] == f"{A}'s command label is supported.")
    assert check["evidence"] == "No walk-rate sample is available."  # not "Command signal is 0"
