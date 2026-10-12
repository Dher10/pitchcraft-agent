"""No invented pitch, and the Critic stops what it cannot support (QA-04).

QA probe: two starters with only four-seam pitches got a "Slider" put-away pitch, the
writer described a four-seam-slider combination, the critic marked it "revised" and the
unchanged report was published. Now the profile never names a pitch that was not
observed, the critic never claims a revision it did not make, and an unsupported claim
stops the publish.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date
import json

import pytest

from agents import critic, data_scout, matchup_analyst, report_writer
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from data_pipeline import schema
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_live_sample_pipeline import API_STATS, frame, route
from tests.test_live_starters_no_demo_fields import _fake_live_game

NOT_AVAILABLE = "Not available"


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(
        lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27))
    )


def two_pitch_frame(second_count: int):
    return frame(n_plain=150 - second_count, extra_rows=[{"pitch_type": "SL"}] * second_count)


# --- the profile never names a pitch that was not observed ----------------------------------------


def test_a_one_pitch_pitcher_has_no_put_away_pitch():
    result = lp.process_pitcher_statcast(frame(n_plain=150), "One Pitch")

    profile = result["pitching_profile"]
    assert [row["pitch"] for row in result["pitch_mix"]] == ["Four-seam"]
    assert profile["primary_pitch"] == "Four-seam"
    assert profile["putaway_pitch"] == NOT_AVAILABLE
    assert "slider" not in json.dumps(profile).lower()


def test_a_second_pitch_below_the_put_away_minimum_is_not_a_put_away_pitch():
    assert labels.PUTAWAY_MIN_USAGE_PCT == 15
    result = lp.process_pitcher_statcast(two_pitch_frame(10), "Mostly Fastball")  # 6.7%

    assert result["pitching_profile"]["putaway_pitch"] == NOT_AVAILABLE


def test_a_real_second_pitch_is_still_the_put_away_pitch():
    result = lp.process_pitcher_statcast(two_pitch_frame(50), "Two Pitch")  # 33%

    profile = result["pitching_profile"]
    assert (profile["primary_pitch"], profile["putaway_pitch"]) == ("Four-seam", "Slider")
    assert profile["style_label"] == "Four-seam-Slider starter"


def test_no_observed_pitch_means_no_pitch_named_at_all():
    empty = frame(n_plain=3)
    empty["pitch_type"] = None

    result = lp.process_pitcher_statcast(empty, "No Pitches")

    assert result["pitch_mix"] == []
    assert result["pitching_profile"]["primary_pitch"] == NOT_AVAILABLE
    assert result["pitching_profile"]["putaway_pitch"] == NOT_AVAILABLE


# --- the QA end-to-end probe -----------------------------------------------------------------------


def live_payload(monkeypatch):
    """Two starters with 150 four-seams each, through the real fetcher, charts and generator."""

    route(monkeypatch, [("/stats?", API_STATS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: frame(n_plain=150))
    away = lp.fetch_pitcher_statcast(11, "One Pitch", as_of="2026-07-14")
    home = lp.fetch_pitcher_statcast(22, "Also One", as_of="2026-07-14")
    assert away and home

    template = next(
        m for m in demo_inputs.build_demo_payload()["matchups"] if m["id"] == "matchup_001"
    )
    game = _fake_live_game(template)
    game.update(
        away_starter=away,
        home_starter=home,
        combined_charts={
            "pitch_mix": lp._combine_pitch_mix(away, home),
            "velocity_by_pitch": lp._combine_velocity(away, home),
        },
    )
    monkeypatch.setattr(
        gdj, "_live", {"run_at": "2026-07-15T12:00:00+00:00", "fetched_date": "2026-07-15", "as_of": "2026-07-14", "live_games": [game]}
    )
    monkeypatch.setattr(
        gdj, "_live_status", {"mode": "fetched_snapshot", "reason": "Live run ok", "live_run": None}
    )
    return gdj.build_payload()


def report_text(matchup: dict) -> str:
    return json.dumps(matchup["report"]).lower()


def test_the_published_report_names_no_pitch_that_was_not_thrown(monkeypatch):
    payload = live_payload(monkeypatch)

    live = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    assert {row["pitch"] for row in live["charts"]["pitch_mix"]} == {"Four-seam"}
    assert "slider" not in report_text(live)
    assert "slider" not in json.dumps(live["critic_review"]).lower()


def test_that_report_passes_the_critic_without_revisions_or_unsupported_claims(monkeypatch):
    payload = live_payload(monkeypatch)

    live = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    statuses = {check["status"] for check in live["critic_review"]["checks"]}
    assert statuses <= {"supported", "not_present", "warning"}
    assert all(check.passed for check in validate_payload(payload))


def test_the_workflow_does_not_claim_revisions_nobody_made(monkeypatch):
    payload = live_payload(monkeypatch)

    text = json.dumps(payload["agent_workflow"]).lower()
    assert "revised" not in text
    assert "verified" not in text


# --- the critic blocks what it cannot support -------------------------------------------------------


@pytest.fixture()
def template() -> dict:
    payload = demo_inputs.build_demo_payload()
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


def review_for(matchup: dict) -> dict:
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, matchup)
    return critic.run(report, matchup)


def with_invented_putaway(template: dict, pitch: str = "Knuckleball") -> dict:
    matchup = deepcopy(template)
    matchup["starters"]["away_starter"]["pitching_profile"]["putaway_pitch"] = pitch
    return matchup


def test_a_pitch_missing_from_the_mix_is_unsupported(template):
    review = review_for(with_invented_putaway(template))

    unsupported = [c for c in review["checks"] if c["status"] == "unsupported"]
    assert unsupported and any("knuckleball" in c["claim"].lower() for c in unsupported)


def test_the_report_text_naming_an_unobserved_pitch_is_unsupported(template):
    matchup = deepcopy(template)
    packet = data_scout.run(matchup)
    report = report_writer.run(matchup_analyst.run(packet), matchup)
    report["sections"][0]["body"] += " He also leans on a sweeper he has never thrown here."
    mix = {row["pitch"].lower() for row in matchup["charts"]["pitch_mix"]}
    assert "sweeper" not in mix

    review = critic.run(report, matchup)

    assert any(
        c["status"] == "unsupported" and "sweeper" in (c["claim"] + c["evidence"]).lower()
        for c in review["checks"]
    )


def test_a_low_usage_pitch_is_a_warning_not_a_revision(template):
    matchup = deepcopy(template)
    for row in matchup["charts"]["pitch_mix"]:
        if row["pitch"] == "Slider":
            row["away_starter"]["overall"] = 6

    review = review_for(matchup)

    low = [c for c in review["checks"] if "6%" in c["evidence"]]
    assert low and all(c["status"] == "warning" for c in low)
    assert all("revised" not in c["evidence"].lower() for c in review["checks"])


def test_the_critic_never_emits_revised_on_any_demo_matchup():
    for matchup in demo_inputs.build_demo_payload()["matchups"]:
        review = review_for(matchup)
        assert {c["status"] for c in review["checks"]} <= {
            "supported", "unsupported", "not_present", "warning"
        }
        assert "revised" not in review["summary"].lower()


def test_an_unsupported_claim_stops_the_generator_and_the_json_is_not_touched(
    monkeypatch, tmp_path, template
):
    payload = demo_inputs.build_demo_payload()
    payload["matchups"][0] = with_invented_putaway(payload["matchups"][0])
    monkeypatch.setattr(gdj.demo_inputs, "build_demo_payload", lambda: payload)
    out = tmp_path / "pitchcraft-demo.json"
    out.write_text('{"sentinel": true}\n', encoding="utf-8")
    monkeypatch.setattr(gdj, "OUTPUT_PATH", out)

    with pytest.raises(gdj.CriticBlocked):
        gdj.build_payload()
    assert gdj.main() == 1

    assert out.read_text(encoding="utf-8") == '{"sentinel": true}\n'


def test_the_validator_rejects_revised_and_unsupported_critic_checks():
    assert "revised" not in schema.CRITIC_STATUSES
    for status in ("revised", "unsupported"):
        payload = gdj.build_payload()
        payload["matchups"][0]["critic_review"]["checks"][0]["status"] = status

        with pytest.raises(ValidationError):
            validate_payload(payload)


def test_a_clean_payload_still_validates():
    payload = gdj.build_payload()

    assert all(check.passed for check in validate_payload(payload))
