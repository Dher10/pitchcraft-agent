"""Matchups that exercise every branch of the text-writing agents, and their outputs.

Used by test_agents_en_golden.py (the English output must not change when the text moves
to a catalog, P0.12-D) and by test_agents_language.py (the same matchups run under a
pseudo-language). Not a test module.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from tests.live_helpers import summary_scopes
from tests.test_live_sample_pipeline import frame  # noqa: F401  (kept for scenario helpers)
from tests.test_live_starters_no_demo_fields import _fake_live_game
from tests.test_limited_samples import (
    REG,
    AWAY_PRIMARY,
    AWAY_PUTAWAY,
    HOME_PRIMARY,
    HOME_PUTAWAY,
    REG_POST,
    debut_sample,
    sample,
)

SPLITS_VR = {"vr": {"ops": ".801", "avg": ".270", "strikeouts": 300, "walks": 150,
                    "plate_appearances": 1500, "k_rate": 24.5, "bb_rate": 10.2}}
SPLITS_VL = {"vl": {"ops": ".655", "avg": ".231", "strikeouts": 280, "walks": 90,
                    "plate_appearances": 1400, "k_rate": 20.0, "bb_rate": 6.4}}


def measured_zero_sample() -> dict[str, Any]:
    """An API line that measured zero batters faced: a figure, with its scope (rule 2, rule 3)."""

    return labels.build_sample(
        pitches=0, arsenal_scope=REG, batters_faced=0, strikeouts=0, walks=0, home_runs=0,
        rates_source="mlb_api", rates_scope=REG,
    )


def live(mp, away=None, home=None, splits=None, edit=None) -> dict[str, Any]:
    """
    A live-shaped matchup like test_limited_samples.build, optionally with offense splits.

    `splits` is "both", "away" or "home": the lineups that get a split. The away starter throws R and the
    home starter L, so the home lineup is read against "vr" and the away lineup against "vl" (the pipeline
    reads the key of the hand it faces, tests/test_offense_reads_opposing_hand.py).
    """

    template = demo_inputs.build_demo_payload()["matchups"][0]
    game = _fake_live_game(
        template,
        away_team_splits=SPLITS_VL if splits in ("both", "away") else None,
        home_team_splits=SPLITS_VR if splits in ("both", "home") else None,
    )
    zero = {"overall": 0, "vs_lhh": 0, "vs_rhh": 0}
    for slot, given, primary, putaway in (
        ("away_starter", away, AWAY_PRIMARY, AWAY_PUTAWAY),
        ("home_starter", home, HOME_PRIMARY, HOME_PUTAWAY),
    ):
        starter = game[slot]
        smp = given or sample()
        starter["sample"] = smp
        starter["pitching_profile"].update(primary_pitch=primary, putaway_pitch=putaway)
        labels.apply_profile_labels(starter["pitching_profile"], smp)
        starter["season_summary"].pop("scope", None)
        starter["season_summary"]["scopes"] = summary_scopes(smp)
    game["combined_charts"]["pitch_mix"] = [
        {"pitch": AWAY_PRIMARY, "away_starter": {"overall": 60, "vs_lhh": 60, "vs_rhh": 60}, "home_starter": zero},
        {"pitch": AWAY_PUTAWAY, "away_starter": {"overall": 30, "vs_lhh": 30, "vs_rhh": 30}, "home_starter": zero},
        {"pitch": HOME_PRIMARY, "away_starter": zero, "home_starter": {"overall": 60, "vs_lhh": 60, "vs_rhh": 60}},
        {"pitch": HOME_PUTAWAY, "away_starter": zero, "home_starter": {"overall": 30, "vs_lhh": 30, "vs_rhh": 30}},
    ]
    if edit:
        edit(game)
    mp.setattr(gdj, "_live", {"run_at": "2026-07-04T12:00:00+00:00", "fetched_date": "2026-07-04", "live_games": [game]})
    return gdj._build_live_matchup(game, "matchup_001", True)


def _no_putaway(game: dict[str, Any]) -> None:
    game["away_starter"]["pitching_profile"]["putaway_pitch"] = labels.PITCH_NOT_AVAILABLE
    game["away_starter"]["pitching_profile"]["style_label"] = f"{AWAY_PRIMARY} starter"


def _unavailable_summary(game: dict[str, Any]) -> None:
    """ERA, WHIP and innings are unavailable, so (as `_attach_sample` writes it) their group has no scope."""

    for slot in ("away_starter", "home_starter"):
        for key in ("era", "whip", "innings"):
            game[slot]["season_summary"][key] = "N/A"
        game[slot]["season_summary"]["scopes"]["season_rates"] = None


def _no_figures(game: dict[str, Any]) -> None:
    """A real debut: no ERA, WHIP, innings or counts, so there is no figure for a scope to cover."""

    for slot in ("away_starter", "home_starter"):
        game[slot]["season_summary"].update(
            era="N/A", whip="N/A", innings="N/A", strikeouts=None, walks=None, home_runs_allowed=None,
            scopes={"season_rates": None, "counts": None},
        )
        # as `_attach_sample` writes a starter with no counts: unavailable, and a group with no figure has no scope
        game[slot]["sample"]["rates"]["source"] = "unavailable"
        game[slot]["sample"]["rates"]["scope"] = None


def _measured_zero_counts(game: dict[str, Any]) -> None:
    """The away starter has a line of zero batters faced from the API: a measured zero, not an unknown."""

    summary = game["away_starter"]["season_summary"]
    summary.update(era="N/A", whip="N/A", innings="0.0", strikeouts=0, walks=0, home_runs_allowed=0)


def from_the_pipeline(mp, hard_case: str) -> dict[str, Any]:
    """
    A live matchup built from what the real pipeline wrote for a hard case of the matrix: the golden file shows only
    states the pipeline produces, so a state it does produce is taken from its output, not typed by hand.
    """

    from tests.matrix import hard_outcome  # not at the top: the matrix imports the corpus, which imports this module

    # the pipeline stamps the real time of its run; the golden file must not depend on the clock (the note says the fetch day)
    base = hard_outcome(hard_case).snapshot
    snapshot = {**base, "run_at": f"{base['fetched_date']}T12:00:00+00:00"}  # noon UTC of the game's own day
    mp.setattr(gdj, "_live", snapshot)
    return gdj._build_live_matchup(snapshot["live_games"][0], "matchup_001", True)


def scenarios(mp) -> dict[str, dict[str, Any]]:
    demo = demo_inputs.build_demo_payload()["matchups"]
    return {
        "demo_upcoming": deepcopy(demo[0]),
        "demo_final": deepcopy(demo[1]),
        "live_healthy": live(mp),
        "live_with_offense_splits": live(mp, splits="both"),
        "live_one_offense_split": live(mp, splits="home"),
        "live_limited_arsenal": from_the_pipeline(mp, "statcast_short_season"),
        "live_debut": live(mp, away=debut_sample()),
        "live_both_limited": live(
            mp, away=sample(pitches=10, bf=3, k=1, bb=0, hr=0), home=sample(pitches=40, bf=10, k=3, bb=1, hr=1)
        ),
        "live_scopes_differ": live(mp, away=sample(arsenal_scope=REG_POST), home=sample(arsenal_scope=REG_POST)),
        "live_strong_strikeouts_weak_command": live(mp, away=sample(k=110, bb=50), home=sample(k=60, bb=15)),
        "live_limited_rates_only": live(
            mp, away=sample(pitches=200, bf=51, k=20, bb=2), home=sample(pitches=400, bf=100, k=10, bb=3)
        ),
        "live_no_putaway_pitch": live(mp, edit=_no_putaway),
        "live_unavailable_era_whip_ip": live(mp, away=sample(arsenal_scope=REG_POST), edit=_unavailable_summary),
        "live_no_home_runs": live(mp, away=sample(hr=None)),
        "live_debut_no_figures": live(mp, away=debut_sample(), home=debut_sample(), edit=_no_figures),
        "live_measured_zero_counts": live(mp, away=measured_zero_sample(), edit=_measured_zero_counts),
        "live_unknown_figures": from_the_pipeline(mp, "unknown_figures"),
        "live_unnamed_lead_pitch": from_the_pipeline(mp, "unmapped_pitch_code"),
        "live_switch_pitcher": from_the_pipeline(mp, "switch_pitcher"),
        # P1.5-b: a postseason game, as the pipeline builds it from the real vocabulary of the schedule
        "live_series_standing": from_the_pipeline(mp, "series_standing"),
        "live_series_opening": from_the_pipeline(mp, "series_opening"),
        "live_series_standing_unavailable": from_the_pipeline(mp, "series_standing_unavailable"),
    }


def agent_outputs(matchup: dict[str, Any], **language: str) -> dict[str, Any]:
    """Run the five agents; `language`, when given, is passed to every one of them."""

    packet = data_scout.run(matchup, **language)
    findings = matchup_analyst.run(packet, **language)
    report = report_writer.run(findings, matchup, **language)
    out = {
        "packet_confidence": packet["data_confidence"],
        "findings": findings,
        "report": report,
        "critic": critic.run(report, matchup, **language),
    }
    if matchup["status"] == "final":
        out["postgame"] = postgame_grader.run(matchup, **language)
    return out
