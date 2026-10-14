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


def live(mp, away=None, home=None, splits=False, edit=None) -> dict[str, Any]:
    """A live-shaped matchup like test_limited_samples.build, optionally with offense splits."""

    template = demo_inputs.build_demo_payload()["matchups"][0]
    game = _fake_live_game(
        template,
        away_team_splits=SPLITS_VR if splits else None,
        home_team_splits=SPLITS_VL if splits else None,
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
        game[slot]["sample"]["rates"]["source"] = "unavailable"  # as `_attach_sample` writes a starter with no counts


def scenarios(mp) -> dict[str, dict[str, Any]]:
    demo = demo_inputs.build_demo_payload()["matchups"]
    return {
        "demo_upcoming": deepcopy(demo[0]),
        "demo_final": deepcopy(demo[1]),
        "live_healthy": live(mp),
        "live_with_offense_splits": live(mp, splits=True),
        "live_limited_arsenal": live(mp, away=sample(pitches=40)),
        "live_debut": live(mp, away=debut_sample()),
        "live_both_limited": live(mp, away=sample(pitches=10), home=debut_sample()),
        "live_scopes_differ": live(mp, away=sample(arsenal_scope=REG_POST), home=sample(arsenal_scope=REG_POST)),
        "live_strong_strikeouts_weak_command": live(mp, away=sample(k=110, bb=50), home=sample(k=60, bb=15)),
        "live_limited_rates_only": live(mp, away=sample(bf=50, k=20, bb=2), home=sample(bf=100, k=10, bb=3)),
        "live_no_putaway_pitch": live(mp, edit=_no_putaway),
        "live_unavailable_era_whip_ip": live(mp, away=sample(arsenal_scope=REG_POST), edit=_unavailable_summary),
        "live_no_home_runs": live(mp, away=sample(hr=None)),
        "live_debut_no_figures": live(mp, away=debut_sample(), home=debut_sample(), edit=_no_figures),
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
