"""Limited samples are flagged, not filled; scopes are never mixed (PLAN.md P0.5).

Phase 0 Gherkin: "Limited sample is flagged, not filled" and "Debut with zero
pitches". The agents run in memory over a live-shaped matchup; nothing is fetched.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from agents import critic, data_scout, matchup_analyst, report_writer
from agents.language import catalog_for
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from data_pipeline.validators import validate_payload
from tests.test_live_starters_no_demo_fields import _fake_live_game

REG = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-04")
REG_POST = labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-07-04")

AWAY_PRIMARY, AWAY_PUTAWAY = "Zephyr-seam", "Quasar slider"
HOME_PRIMARY, HOME_PUTAWAY = "Nimbus sinker", "Vortex changeup"


def sample(
    pitches=1500,
    bf=400,
    k=90,
    bb=30,
    hr=10,
    arsenal_scope=REG,
    rates_scope=REG,
):
    return labels.build_sample(
        pitches=pitches,
        arsenal_scope=arsenal_scope,
        batters_faced=bf,
        strikeouts=k,
        walks=bb,
        home_runs=hr,
        rates_source="mlb_api",
        rates_scope=rates_scope,
    )


def build(monkeypatch, away=None, home=None):
    """A live-shaped matchup whose starters carry the given samples."""

    template = demo_inputs.build_demo_payload()["matchups"][0]
    live_game = _fake_live_game(template)
    for slot, given, primary, putaway in (
        ("away_starter", away, AWAY_PRIMARY, AWAY_PUTAWAY),
        ("home_starter", home, HOME_PRIMARY, HOME_PUTAWAY),
    ):
        starter = live_game[slot]
        smp = given or sample()
        starter["sample"] = smp
        starter["pitching_profile"].update(primary_pitch=primary, putaway_pitch=putaway)
        labels.apply_profile_labels(starter["pitching_profile"], smp)
        starter["season_summary"]["scope"] = smp["rates"]["scope"]
    # The profile names these pitches, so the game's pitch mix must contain them.
    zero = {"overall": 0, "vs_lhh": 0, "vs_rhh": 0}
    live_game["combined_charts"]["pitch_mix"] = [
        {"pitch": AWAY_PRIMARY, "away_starter": {"overall": 60, "vs_lhh": 60, "vs_rhh": 60}, "home_starter": zero},
        {"pitch": AWAY_PUTAWAY, "away_starter": {"overall": 30, "vs_lhh": 30, "vs_rhh": 30}, "home_starter": zero},
        {"pitch": HOME_PRIMARY, "away_starter": zero, "home_starter": {"overall": 60, "vs_lhh": 60, "vs_rhh": 60}},
        {"pitch": HOME_PUTAWAY, "away_starter": zero, "home_starter": {"overall": 30, "vs_lhh": 30, "vs_rhh": 30}},
    ]
    monkeypatch.setattr(
        gdj, "_live", {"fetched_date": "2026-07-04", "live_games": [live_game]}
    )
    return gdj._apply_live_game_to_matchup(deepcopy(template), live_game, "matchup_001", True)


def run_agents(matchup):
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, matchup)
    review = critic.run(report, matchup)
    return findings, report, review


def text_of(report) -> str:
    parts = [report["headline"], *report["short_summary"]]
    for section in report["sections"]:
        parts.append(section.get("body", ""))
        parts.extend(section.get("bullets", []))
    return "\n".join(parts)


# --- Gherkin: limited sample is flagged, not filled -----------------------------------


def test_healthy_samples_still_produce_the_claims(monkeypatch):
    _, report, _ = run_agents(build(monkeypatch))
    text = text_of(report)

    assert AWAY_PRIMARY in text and HOME_PRIMARY in text
    assert "limited" not in text.lower().replace("data confidence", "")


def test_limited_arsenal_makes_no_arsenal_claim_beyond_the_limitation(monkeypatch):
    matchup = build(monkeypatch, away=sample(pitches=40))

    findings, report, review = run_agents(matchup)
    text = text_of(report)

    assert "40 pitches" in text and "100" in text
    assert "no arsenal claim" in text
    # none of the away starter's pitch names or style appears anywhere
    # (the analyst writes pitch names in lower case, so compare case-insensitively)
    lowered = text.lower()
    assert AWAY_PRIMARY.lower() not in lowered and AWAY_PUTAWAY.lower() not in lowered
    assert AWAY_PRIMARY.lower() not in "\n".join(findings["three_things_to_watch"]).lower()
    assert AWAY_PRIMARY.lower() not in findings["away_vs_home_offense"].lower()
    assert matchup["starters"]["away_starter"]["pitching_profile"]["style_label"] == (
        "Arsenal data limited"
    )
    # the healthy starter is unaffected
    assert HOME_PRIMARY in text


def test_limited_arsenal_headline_does_not_use_the_style_label(monkeypatch):
    matchup = build(monkeypatch, away=sample(pitches=40))

    findings, report, _ = run_agents(matchup)

    assert "Arsenal data limited" not in report["headline"]
    assert matchup["starters"]["away_starter"]["name"] in report["headline"]


def test_critic_records_the_limitation_instead_of_checking_usage(monkeypatch):
    matchup = build(monkeypatch, away=sample(pitches=40))

    _, _, review = run_agents(matchup)
    claims = [c["claim"] for c in review["checks"]]
    away = matchup["starters"]["away_starter"]["name"]

    assert not any(c.startswith(f"{away}'s primary pitch") for c in claims)
    limited = next(c for c in review["checks"] if f"{away}'s arsenal is limited" in c["claim"])
    assert limited["status"] == "supported"
    assert "40 pitches" in limited["evidence"]


def test_critic_flags_a_report_that_names_a_limited_pitch(monkeypatch):
    matchup = build(monkeypatch, away=sample(pitches=40))
    _, report, _ = run_agents(matchup)
    report["sections"][0]["body"] += f" His {AWAY_PRIMARY} is the key."

    review = critic.run(report, matchup)

    away = matchup["starters"]["away_starter"]["name"]
    check = next(c for c in review["checks"] if f"{away}'s arsenal is limited" in c["claim"])
    assert check["status"] == "unsupported"


def test_limited_strikeout_sample_makes_no_swing_and_miss_claim(monkeypatch):
    matchup = build(monkeypatch, away=sample(bf=50, k=20, bb=5))

    findings, report, _ = run_agents(matchup)
    text = text_of(report).lower()

    assert matchup["starters"]["away_starter"]["pitching_profile"]["swing_miss_label"] is None
    assert "50 batters faced" in text and "70 needed" in text
    assert not any("swing-and-miss" in item.lower() for item in findings["away_starter_strengths"])


def test_limited_control_sample_makes_no_command_claim(monkeypatch):
    matchup = build(monkeypatch, away=sample(bf=120, k=30, bb=30))  # 25% walks, but 120 BF

    findings, report, review = run_agents(matchup)
    text = text_of(report).lower()

    assert matchup["starters"]["away_starter"]["pitching_profile"]["command_label"] is None
    assert "120 batters faced" in text and "170 needed" in text
    assert "below-average command" not in text
    assert not any("Below-average command" in r for r in findings["away_starter_risks"])
    assert all(c["claim"] != "Test Away carries below-average command risk." for c in review["checks"])


def test_contact_risk_is_a_count_never_a_label(monkeypatch):
    matchup = build(monkeypatch, away=sample(bf=640, hr=12))

    findings, report, _ = run_agents(matchup)
    text = text_of(report)

    assert "12 home runs" in text and "640 batters faced" in text
    for slot in ("away_starter", "home_starter"):
        assert matchup["starters"][slot]["pitching_profile"]["contact_risk_label"] is None
    lowered = text.lower()
    assert "contact risk can turn" not in lowered
    assert "limit hard contact" not in lowered and "disrupt timing" not in lowered


# --- Gherkin: debut with zero pitches --------------------------------------------------------


def debut_sample(**kw):
    return labels.build_sample(
        pitches=0,
        arsenal_scope=REG,
        batters_faced=None,
        strikeouts=None,
        walks=None,
        home_runs=None,
        rates_source="mlb_api",
        rates_scope=REG,
        **kw,
    )


def test_a_debut_flags_every_dimension_and_the_report_is_still_written(monkeypatch):
    matchup = build(monkeypatch, away=debut_sample())

    findings, report, review = run_agents(matchup)
    text = text_of(report)
    profile = matchup["starters"]["away_starter"]["pitching_profile"]

    assert matchup["starters"]["away_starter"]["sample"]["limited"] == {
        "arsenal": True,
        "strikeout": True,
        "control": True,
    }
    assert profile["swing_miss_label"] is None and profile["command_label"] is None
    assert "no pitches on record" in text
    assert AWAY_PRIMARY.lower() not in text.lower()
    assert review["checks"]


def test_a_debut_payload_still_validates(monkeypatch):
    matchup = build(monkeypatch, away=debut_sample())
    payload = demo_inputs.build_demo_payload()
    # The fixture's figures run through 2026-07-04; the game is the next day (D29).
    matchup["date"] = "2026-07-05"
    payload["matchups"][0] = matchup
    payload["featured_matchup_id"] = matchup["id"]
    monkeypatch.setattr(gdj, "_live_status", {"mode": "demo_cached", "reason": "", "live_run": None})

    gdj._run_agents(payload["matchups"])

    assert all(c.passed for c in validate_payload(payload))


def test_both_starters_limited_still_gives_a_report(monkeypatch):
    matchup = build(monkeypatch, away=debut_sample(), home=sample(pitches=10, bf=5, k=1, bb=1))

    _, report, _ = run_agents(matchup)

    assert "brings this strength" not in text_of(report)
    assert report["sections"]


def test_an_old_snapshot_without_a_sample_is_limited_everywhere(monkeypatch):
    template = demo_inputs.build_demo_payload()["matchups"][0]
    live_game = _fake_live_game(template)
    del live_game["away_starter"]["sample"]
    monkeypatch.setattr(gdj, "_live", {"fetched_date": "2026-07-04", "live_games": [live_game]})

    matchup = gdj._apply_live_game_to_matchup(deepcopy(template), live_game, "matchup_001", True)
    run_agents(matchup)

    limited = matchup["starters"]["away_starter"]["sample"]["limited"]
    assert limited == {"arsenal": True, "strikeout": True, "control": True}


# --- scopes: never presented as one sample ------------------------------------------------------


def test_every_group_of_figures_in_the_packet_carries_its_scope(monkeypatch):
    matchup = build(monkeypatch)

    for slot in ("away_starter", "home_starter"):
        starter = matchup["starters"][slot]
        assert starter["season_summary"]["scope"]["label"].startswith("regular season")
        assert starter["sample"]["arsenal"]["scope"]["through"] == "2026-07-04"
        assert starter["sample"]["rates"]["scope"]["kind"] in ("regular_season", "regular_and_postseason")
    for side in ("home", "away"):
        offense_scope = matchup["teams"][side]["offense_profile"]["scope"]
        assert offense_scope == labels.make_scope(labels.SCOPE_REGULAR, "2026-07-04")


def test_different_scopes_are_called_different_samples_in_the_report(monkeypatch):
    mixed = sample(arsenal_scope=REG_POST, rates_scope=REG)
    matchup = build(monkeypatch, away=mixed)

    findings, report, review = run_agents(matchup)
    note = next(s for s in report["sections"] if s["title"] == "Data Confidence Note")["body"]
    away = matchup["starters"]["away_starter"]["name"]

    assert "different samples" in note
    assert f"{away}: ERA, WHIP" in note
    assert "regular season through 2026-07-04" in note
    assert "regular season and postseason through 2026-07-04" in note
    scope_check = next(c for c in review["checks"] if "one sample" in c["claim"])
    assert scope_check["status"] == "supported"


def test_rate_claims_are_qualified_when_the_scopes_differ(monkeypatch):
    mixed = sample(arsenal_scope=REG_POST, rates_scope=REG, bf=200, k=50)
    matchup = build(monkeypatch, away=mixed)

    findings, report, _ = run_agents(matchup)

    assert "regular-season rates" in findings["away_vs_home_offense"]


def test_same_scopes_are_stated_once_without_the_warning(monkeypatch):
    matchup = build(monkeypatch)

    _, report, review = run_agents(matchup)
    note = next(s for s in report["sections"] if s["title"] == "Data Confidence Note")["body"]

    assert "different samples" not in note
    assert "all pitcher figures cover the regular season through 2026-07-04" in note
    scope_check = next(c for c in review["checks"] if "one sample" in c["claim"])
    assert scope_check["status"] == "not_present"


def test_critic_flags_a_report_that_hides_different_scopes(monkeypatch):
    mixed = sample(arsenal_scope=REG_POST, rates_scope=REG)
    matchup = build(monkeypatch, away=mixed)
    _, report, _ = run_agents(matchup)
    for section in report["sections"]:
        if section["title"] == "Data Confidence Note":
            section["body"] = "This report uses a fetched live snapshot."

    review = critic.run(report, matchup)

    scope_check = next(c for c in review["checks"] if "one sample" in c["claim"])
    assert scope_check["status"] == "unsupported"


def test_live_matchups_do_not_keep_the_demo_strength_profile(monkeypatch):
    matchup = build(monkeypatch)

    assert matchup["charts"]["strength_profile"] == []
    _, _, review = run_agents(matchup)
    assert all("strength profile" not in c["evidence"] for c in review["checks"])


def test_a_sample_without_its_limited_flags_is_an_error_not_a_healthy_sample(monkeypatch):
    # The writer used .get("limited", {}), so a malformed sample read as "nothing is limited".
    matchup = build(monkeypatch)
    del matchup["starters"]["away_starter"]["sample"]["limited"]

    with pytest.raises(KeyError):
        report_writer._confidence_note(catalog_for("en"), matchup, {"scope_notes": []})
