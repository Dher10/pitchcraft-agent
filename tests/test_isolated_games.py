"""One bad game never takes down the page, and a switch pitcher is published (P0.15-D2.3b, F11; schema 0.6.0, D38).

At HEAD `_snapshot_unsafe` returned one reason for the whole snapshot: a single game with a starter whose hand the
generator did not accept (`S`, which `fetch_pitcher_hand` does accept) sent every game to the demo fallback. Rule 5: an
error is contained in the smallest unit. The run-level checks (schema, run identity, cutoff, game day) are whole; the
checks of a game drop that game, with a recorded `{source: "snapshot", code: "game_rejected"}`, and the others are
published. A switch pitcher is published: the lineup he faces has no split (a lineup has one only against L or R),
so `vs_pitcher_hand` is `null`; before, `build_offense` read the right-handed split for him under the label "SHP".

Controls (they pass before the fix): a snapshot with every game safe, a snapshot whose only game is unsafe, a run-level
failure with two games, a known hand reading its own split.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline import labels
from data_pipeline.live_matchup import build_offense
from data_pipeline.schema import SCHEMA_VERSION, snapshot_matches_schema
from tests.test_snapshot_dates import isolated, live_game, pair, resolve, template  # noqa: F401

SCOPE = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")
SPLITS = {
    "vl": {"ops": ".655", "avg": ".231", "k_rate": 20.0, "bb_rate": 6.4},
    "vr": {"ops": ".801", "avg": ".270", "k_rate": 24.5, "bb_rate": 10.2},
}
TARGET, CUTOFF = date(2026, 7, 15), date(2026, 7, 14)


# --- the schema ---------------------------------------------------------------------------------------------


def test_the_schema_is_0_6_0_and_a_snapshot_of_0_5_0_is_not_read():
    assert SCHEMA_VERSION == "0.9.0"
    assert snapshot_matches_schema("0.9.0") and not snapshot_matches_schema("0.8.0") and not snapshot_matches_schema("0.7.0") and not snapshot_matches_schema("0.6.0") and not snapshot_matches_schema("0.5.0")


# --- a switch pitcher: the lineup he faces ---------------------------------------------------------------------


@pytest.mark.parametrize("hand", ["S", "", None, "X"])
def test_a_lineup_facing_a_hand_that_is_not_l_or_r_has_no_split_and_no_label(hand):
    offense = build_offense(hand, SPLITS, SCOPE)  # the right-handed split exists and must not be read for him

    assert offense["vs_pitcher_hand"] is None
    assert (offense["ops_vs_hand"], offense["k_rate_vs_hand"], offense["bb_rate_vs_hand"]) == (None, None, None)
    assert offense["summary_label"] is None and offense["recent_form"] is None and offense["scope"] is None


@pytest.mark.parametrize(("hand", "ops"), [("L", ".655"), ("R", ".801")])
def test_control_a_known_hand_reads_its_own_split(hand, ops):
    offense = build_offense(hand, SPLITS, SCOPE)

    assert offense["vs_pitcher_hand"] == f"{hand}HP" and offense["ops_vs_hand"] == ops
    assert offense["scope"] == SCOPE


# --- a switch pitcher: the game ---------------------------------------------------------------------------------


def test_the_generator_accepts_a_game_whose_starter_is_a_switch_pitcher(template):  # noqa: F811
    game = live_game(template)
    game["home_starter"]["throws"] = "S"

    assert gdj._game_unsafe(game, TARGET, CUTOFF) is None


@pytest.mark.parametrize("hand", ["X", "", None])
def test_control_a_hand_that_is_not_l_r_or_s_is_still_unsafe(template, hand):  # noqa: F811
    game = live_game(template)
    game["home_starter"]["throws"] = hand

    assert "throws" in gdj._game_unsafe(game, TARGET, CUTOFF)


# --- one unsafe game is dropped, the others are published ------------------------------------------------------


def two_games(template, bad_first: bool):  # noqa: F811
    run, snapshot = pair(template)
    good = snapshot["live_games"][0]
    bad = deepcopy(good)
    bad["featured_game"]["game_pk"] = 2
    bad["home_starter"]["throws"] = "X"
    snapshot["live_games"] = [bad, good] if bad_first else [good, bad]
    return run, snapshot, good


@pytest.mark.parametrize("bad_first", [False, True])
def test_an_unsafe_game_is_dropped_and_the_safe_one_is_published(template, bad_first):  # noqa: F811
    run, snapshot, good = two_games(template, bad_first)

    live, status = resolve(run, snapshot)

    assert status["mode"] == "fetched_snapshot"
    assert live is not None and live["live_games"] == [good]


@pytest.mark.parametrize("bad_first", [False, True])
def test_the_dropped_game_is_a_recorded_error_with_its_place(template, bad_first, capsys):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first)

    _, status = resolve(run, snapshot)

    rejected = [e for e in status["live_run"]["errors"] if e.get("code") == "game_rejected"]
    assert rejected == [{"source": "snapshot", "code": "game_rejected"}]  # rule 8: the place goes to the log
    logged = capsys.readouterr().out
    assert f"game {1 if bad_first else 2}" in logged and "throws" in logged


def test_the_page_is_built_from_the_game_that_is_left(template, monkeypatch):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=True)
    live, status = resolve(run, snapshot)
    monkeypatch.setattr(gdj, "_live", live)
    monkeypatch.setattr(gdj, "_live_status", status)

    payload = gdj.build_payload()

    live_ids = [m["id"] for m in payload["matchups"] if m["data_confidence"]["level"] == "fetched_snapshot"]
    assert live_ids == ["matchup_001"]


def test_control_a_snapshot_with_every_game_safe_records_nothing(template):  # noqa: F811
    run, snapshot = pair(template)

    live, status = resolve(run, snapshot)

    assert live is not None
    assert not [e for e in status["live_run"]["errors"] if e.get("code") == "game_rejected"]


def test_control_the_only_game_unsafe_is_the_fallback_with_its_reason(template, capsys):  # noqa: F811
    run, snapshot = pair(template)
    snapshot["live_games"][0]["home_starter"]["throws"] = "X"

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"
    assert status["reason"] == {"source": "snapshot", "code": "game_rejected"}
    logged = capsys.readouterr().out
    assert "game 1" in logged and "throws" in logged


def test_control_every_game_unsafe_is_the_fallback(template):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=False)
    snapshot["live_games"][0]["away_starter"]["throws"] = "X"

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"


def test_control_a_run_level_failure_rejects_the_whole_snapshot_even_with_safe_games(template, capsys):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=False)
    snapshot["live_games"][0]["as_of"] = "2026-07-13"  # not the run's cutoff: the game is dropped, the other is safe
    snapshot["as_of"] = "2026-07-20"  # the snapshot's own cutoff is after the game day: whole
    run["as_of"] = "2026-07-20"

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"
    assert status["reason"] == {"source": "snapshot", "code": "snapshot_mismatch"}
    assert "2026-07-20" in capsys.readouterr().out


# --- the manifest: a lineup facing a switch pitcher (rule 1) ----------------------------------------------------

LABEL = "rule1:derivation_mismatch#matchups[].teams.*.offense_profile.vs_pitcher_hand"


def switch_payload():
    from tests.matrix import hard_outcome

    outcome = hard_outcome("switch_pitcher")
    assert outcome.live
    return deepcopy(outcome.payload)


def codes_of(payload) -> set[str]:
    from data_pipeline.contract_checks import check_contract

    return {violation.code for violation in check_contract(payload)}


def test_the_switch_pitcher_payload_the_pipeline_writes_breaks_no_rule_of_the_manifest():
    assert LABEL not in codes_of(switch_payload())


def test_the_manifest_rejects_a_hand_label_for_a_hand_with_no_split():
    payload = switch_payload()
    payload["matchups"][0]["teams"]["home"]["offense_profile"]["vs_pitcher_hand"] = "SHP"

    assert LABEL in codes_of(payload)


def test_the_manifest_rejects_figures_against_a_hand_the_lineup_has_no_split_against():
    payload = switch_payload()
    offense = payload["matchups"][0]["teams"]["home"]["offense_profile"]
    offense["ops_vs_hand"] = ".801"  # the right-handed split, as it used to be read for him

    assert LABEL in codes_of(payload)


def test_control_the_manifest_still_wants_the_label_when_the_hand_is_known():
    payload = switch_payload()
    payload["matchups"][0]["teams"]["away"]["offense_profile"]["vs_pitcher_hand"] = None  # it faces the home starter, R

    assert LABEL in codes_of(payload)
