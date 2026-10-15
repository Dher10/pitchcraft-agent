"""The 72-case matrix and the hard cases, end to end (PLAN.md P0.15-D3.3b, docs/DATA_CONTRACT.md section 5.3).

Each case runs the real pipeline over faked sources (tests/matrix.py), then the real generator and the
real publication checks. For every case:

- the game is published as live, or the run record and the generator's reason say why it was not;
- publication passes: the only violations of the contract are the ones in `known_violations.py`;
- the published figures are the ones the case's sources give (an oracle written from the case, so a
  fixture that silently collapses into another cell fails here).

Findings that the contract names and today's code still has are `xfail(strict=True)`, labelled with their F
number; the fix of P0.15-D2 removes the mark, and a mark whose test passes fails the run.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import pytest

from agents import data_scout, matchup_analyst, report_writer
from data_pipeline.known_violations import KNOWN_VIOLATIONS
from tests.golden_scenarios import live
from tests.matrix import (
    EVENT_CYCLE,
    MATRIX,
    STAT_LINES,
    Outcome,
    Pitcher,
    fingerprint,
    hard_outcome,
    matrix_outcome,
    mix_of,
)

SLOT_OF = {"away": "away_starter", "home": "home_starter"}


def cutoff_of(game_day: str) -> str:
    return (date.fromisoformat(game_day) - timedelta(days=1)).isoformat()


def expected_starter(pitcher: Pitcher, opening: bool) -> dict:
    """
    What the sources give for `pitcher`, written from the case and not from the pipeline's code.

    The counts come from the MLB line when it has all four, otherwise from Statcast when there are pitches,
    otherwise from a partial line, otherwise they are unavailable (`live_pipeline._attach_sample`, QA3-02).
    """

    pitches = 0 if opening or pitcher.kind == "debut" else sum(mix_of(pitcher).values())
    line = STAT_LINES.get(pitcher.api, {})
    api = {
        "batters_faced": line.get("battersFaced"),
        "strikeouts": line.get("strikeOuts"),
        "walks": line.get("baseOnBalls"),
        "home_runs": line.get("homeRuns"),
    }
    events = [EVENT_CYCLE[(i // 4) % len(EVENT_CYCLE)] for i in range(pitches) if i % 4 == 3]
    statcast = {
        "batters_faced": len(events),
        "strikeouts": events.count("strikeout"),
        "walks": events.count("walk"),
        "home_runs": events.count("home_run"),
    }
    postseason = pitcher.postseason and not opening and pitches > 0
    if all(value is not None for value in api.values()):
        source, numbers = "mlb_api", api
    elif pitches > 0:
        source, numbers = "statcast", statcast
    elif any(value is not None for value in api.values()):
        source, numbers = "mlb_api", api
    else:
        source, numbers = "unavailable", dict.fromkeys(api)
    counts_kind = "regular_and_postseason" if source == "statcast" and postseason else "regular_season"
    limited = {
        "arsenal": pitches < 100,
        "strikeout": numbers["batters_faced"] is None or numbers["batters_faced"] < 70 or numbers["strikeouts"] is None,
        "control": numbers["batters_faced"] is None or numbers["batters_faced"] < 170 or numbers["walks"] is None,
    }
    return {
        "pitches": pitches,
        "arsenal_kind": "regular_and_postseason" if postseason else "regular_season",
        "source": source,
        "numbers": numbers,
        "counts_kind": counts_kind,
        "limited": limited,
        "has_season_rates": "era" in line,
        "era": line.get("era", "N/A"),
    }


def check_starter(outcome: Outcome, side: str, pitcher: Pitcher, opening: bool) -> None:
    starter = outcome.matchup["starters"][SLOT_OF[side]]
    want = expected_starter(pitcher, opening)
    through = cutoff_of(outcome.scenario.game_day)
    sample, summary = starter["sample"], starter["season_summary"]
    where = f"{outcome.scenario.name} {side}"

    assert starter["throws"] == pitcher.throws, where
    assert sample["arsenal"]["pitches"] == want["pitches"], where
    assert sample["arsenal"]["scope"]["kind"] == want["arsenal_kind"], where
    assert sample["arsenal"]["scope"]["through"] == through, where
    assert sample["rates"]["source"] == want["source"], where
    assert {key: sample["rates"][key] for key in want["numbers"]} == want["numbers"], where
    assert sample["rates"]["scope"]["kind"] == want["counts_kind"], where
    assert sample["limited"] == want["limited"], where
    assert summary["era"] == want["era"], where
    assert (summary["scopes"]["season_rates"] is not None) == want["has_season_rates"], where
    if want["source"] == "unavailable":
        assert summary["scopes"]["counts"] is None, where
    else:
        assert summary["scopes"]["counts"]["kind"] == want["counts_kind"], where
        assert summary["strikeouts"] == want["numbers"]["strikeouts"], where


def assert_published_or_explained(outcome: Outcome) -> None:
    """The game is published as live, or the run record and the reason say why it is not."""

    if outcome.live:
        assert outcome.record["status"] == "ok", outcome.scenario.name
        assert outcome.payload is not None, outcome.scenario.name
        return
    assert outcome.status["mode"] == "demo_fallback", outcome.scenario.name
    assert outcome.status["reason"], outcome.scenario.name
    assert outcome.record["errors"] or outcome.record["status"] != "ok", outcome.scenario.name


def assert_contract_holds(outcome: Outcome) -> None:
    """Publication passed, and every violation of the contract is a known one."""

    assert outcome.blocked is None, outcome.blocked
    assert outcome.failed == [], outcome.failed
    unknown = sorted({v.code for v in outcome.violations} - set(KNOWN_VIOLATIONS))
    assert unknown == [], f"{outcome.scenario.name}: violations that are not in known_violations.py: {unknown}"


# --- the matrix ------------------------------------------------------------------------------------


def test_the_matrix_is_the_product_of_the_five_conditions():
    assert len(MATRIX) == 72
    assert len({case.id for case in MATRIX}) == 72


@pytest.mark.parametrize("case", MATRIX, ids=lambda case: case.id)
def test_matrix_the_game_is_published_and_the_contract_holds(case):
    outcome = matrix_outcome(case)

    assert_published_or_explained(outcome)
    assert outcome.live, f"every cell of the matrix has a hand the sources can give, so the game is published: {outcome.status}"
    assert_contract_holds(outcome)


@pytest.mark.parametrize("case", MATRIX, ids=lambda case: case.id)
def test_matrix_the_figures_are_the_ones_the_sources_give(case):
    outcome = matrix_outcome(case)
    opening = case.day == "opening"
    scenario = outcome.scenario

    check_starter(outcome, "away", scenario.away, opening)
    check_starter(outcome, "home", scenario.home, opening)
    assert outcome.record["as_of"] == cutoff_of(case.game_day)
    # the only source error a cell can have is the stats API being down
    assert outcome.error_sources() == ({"mlb_season_stats"} if case.api == "absent" else set())


@pytest.mark.parametrize("case", MATRIX, ids=lambda case: case.id)
def test_matrix_the_throwing_hand_comes_from_a_source_and_is_never_guessed(case):
    outcome = matrix_outcome(case)
    asked_for_away = outcome.scenario.away.pid in outcome.asked.people
    from_lookup = case.hand == "missing" or case.effective_starter == "debut"

    # the away starter throws left, the opposite of a guessed right hand
    assert outcome.matchup["starters"]["away_starter"]["throws"] == "L"
    assert outcome.matchup["teams"]["home"]["offense_profile"]["vs_pitcher_hand"] == "LHP"
    assert asked_for_away == from_lookup


@pytest.mark.parametrize("case", MATRIX, ids=lambda case: case.id)
def test_matrix_the_sources_are_asked_only_what_the_day_allows(case):
    outcome = matrix_outcome(case)
    asked = outcome.asked

    if case.day == "opening":  # the cutoff is before the season: no pitch and no plate appearance can exist
        assert asked.statcast == [] and asked.savant == []
        teams = outcome.matchup["teams"]
        assert teams["home"]["offense_profile"]["ops_vs_hand"] is None
        assert teams["away"]["offense_profile"]["ops_vs_hand"] is None
    else:
        assert sorted(asked.statcast) == [11, 22]
        assert asked.savant
        teams = outcome.matchup["teams"]
        assert teams["home"]["offense_profile"]["ops_vs_hand"] is not None
        assert teams["away"]["offense_profile"]["ops_vs_hand"] is not None


def test_matrix_cells_that_no_source_can_tell_apart_publish_the_same_file():
    classes: dict[tuple, list] = defaultdict(list)
    for case in MATRIX:
        classes[case.canonical].append(case)

    # opening day collapses 36 cells into 3 (one per API state); a debut has no frame, so the hand is
    # always asked of the people endpoint: its 12 normal-day cells become 6
    assert len(classes) == 3 + 6 + 24
    assert max(len(cells) for cells in classes.values()) == 12
    for canonical, cells in classes.items():
        prints = {fingerprint(matrix_outcome(case)) for case in cells}
        assert len(prints) == 1, f"{[case.id for case in cells]} differ although {canonical} is the same world"


# --- the hard cases --------------------------------------------------------------------------------

PUBLISHED_HARD_CASES = [
    "two_debuts",
    "two_limited",
    "home_limited_away_healthy",
    "home_debut_away_healthy",
    "api_zeros_are_zeros",
    "no_offense_data",
]


@pytest.mark.parametrize("name", PUBLISHED_HARD_CASES)
def test_hard_case_is_published_and_the_contract_holds(name):
    outcome = hard_outcome(name)

    assert_published_or_explained(outcome)
    assert outcome.live
    assert_contract_holds(outcome)


def test_hard_two_debuts_have_no_pitch_and_say_so():
    outcome = hard_outcome("two_debuts")
    away, home = (outcome.matchup["starters"][slot] for slot in SLOT_OF.values())

    for starter in (away, home):
        assert starter["sample"]["arsenal"]["pitches"] == 0
        assert starter["sample"]["limited"] == {"arsenal": True, "strikeout": True, "control": True}
        assert starter["sample"]["rates"]["source"] == "unavailable"
    assert outcome.matchup["charts"]["pitch_mix"] == []


def test_hard_the_other_side_of_the_pair_is_the_one_that_is_limited():
    limited = hard_outcome("home_limited_away_healthy").matchup["starters"]
    debut = hard_outcome("home_debut_away_healthy").matchup["starters"]

    assert limited["home_starter"]["sample"]["arsenal"]["pitches"] == 60
    assert limited["home_starter"]["sample"]["limited"]["arsenal"] is True
    assert limited["away_starter"]["sample"]["limited"] == {"arsenal": False, "strikeout": False, "control": False}
    assert debut["home_starter"]["sample"]["arsenal"]["pitches"] == 0
    assert debut["home_starter"]["pitching_profile"]["primary_pitch"] == "Not available"
    assert debut["away_starter"]["sample"]["limited"]["arsenal"] is False


def test_hard_a_measured_zero_from_the_api_stays_zero():
    """Control for rule 2: 0 walks and 0 home runs that the source measured are published as 0, not as unknown."""

    starter = hard_outcome("api_zeros_are_zeros").matchup["starters"]["away_starter"]

    assert starter["sample"]["rates"]["source"] == "mlb_api"
    assert (starter["sample"]["rates"]["walks"], starter["sample"]["rates"]["home_runs"]) == (0, 0)
    assert (starter["season_summary"]["walks"], starter["season_summary"]["home_runs_allowed"]) == (0, 0)


def test_hard_a_blank_month_of_savant_data_leaves_the_offense_unavailable():
    teams = hard_outcome("no_offense_data").matchup["teams"]

    for side in ("home", "away"):
        offense = teams[side]["offense_profile"]
        assert (offense["ops_vs_hand"], offense["k_rate_vs_hand"], offense["bb_rate_vs_hand"]) == (None, None, None)


def test_hard_a_hand_that_no_source_gives_drops_the_game_and_says_why():
    outcome = hard_outcome("hand_lookup_fails")

    assert not outcome.live
    assert outcome.status["mode"] == "demo_fallback"
    assert "mlb_person" in outcome.error_sources()
    assert outcome.record["status"] == "failed"


# --- findings of the contract that today's code still has (xfail until their fix in P0.15-D2) -------


@pytest.mark.xfail(strict=True, reason="F6b: an unusable `events` column is published as measured zeros")
def test_hard_events_unusable_means_unavailable_counts_and_a_recorded_error():
    outcome = hard_outcome("events_null_in_every_row")
    rates = outcome.matchup["starters"]["away_starter"]["sample"]["rates"]

    assert rates["source"] == "unavailable"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (None,) * 4
    assert "statcast_pitcher" in outcome.error_sources()


@pytest.mark.xfail(strict=True, reason="F6a: a populated frame with no usable pitch_type is a silent debut")
def test_hard_pitch_type_unusable_in_a_populated_frame_is_a_recorded_source_error():
    outcome = hard_outcome("pitch_type_null_in_every_row")

    assert "statcast_pitcher" in outcome.error_sources()


@pytest.mark.xfail(strict=True, reason="F6e: a pitch code outside the name map gets the family Fastball")
def test_hard_an_unmapped_pitch_has_no_family():
    movement = hard_outcome("unmapped_pitch_code").matchup["charts"]["pitch_movement"]["away_starter"]

    assert "XX" in movement
    assert movement["XX"]["family"] is None


@pytest.mark.xfail(strict=True, reason="F7: a team the abbreviation maps do not know is published as '???'")
def test_hard_an_unknown_team_has_no_abbreviation_instead_of_question_marks():
    teams = hard_outcome("unknown_team").matchup["teams"]

    assert teams["away"]["name"] == "Brand New Club"
    assert teams["away"]["abbreviation"] != "???"


@pytest.mark.xfail(strict=True, reason="F11: one switch pitcher sends the whole snapshot to the demo fallback")
def test_hard_a_switch_pitcher_is_published_and_no_sentence_names_his_hand():
    outcome = hard_outcome("switch_pitcher")

    assert outcome.live, outcome.status["reason"]
    matchup = outcome.matchup
    assert matchup["starters"]["away_starter"]["throws"] == "S"
    assert matchup["teams"]["home"]["offense_profile"]["ops_vs_hand"] is None  # no split for a hand that is not L or R
    assert "SHP" not in str(matchup["report"])


@pytest.mark.parametrize("column", ["stand", "release_speed", "plate_x", "plate_z", "pitch_type"])
@pytest.mark.xfail(strict=True, reason="F6c: a column the pitch data needs is not in the required-columns check")
def test_hard_a_frame_without_a_needed_column_fails_as_a_missing_required_column(column):
    outcome = hard_outcome(f"frame_without_{column}")
    messages = [e["message"] for e in outcome.record["errors"] if e["source"] == "statcast_pitcher"]

    assert not outcome.live
    assert any("missing required column" in message and column in message for message in messages), messages


@pytest.mark.xfail(strict=True, reason="F15: the analyst falls back to the right hand when the starter has none")
def test_the_analyst_writes_no_hand_when_the_starter_has_none(monkeypatch):
    matchup = live(monkeypatch)
    for team in matchup["teams"].values():
        team["offense_profile"]["vs_pitcher_hand"] = None
    for starter in matchup["starters"].values():
        del starter["throws"]
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    text = str(report_writer.run(findings, matchup))

    assert "RHP" not in text and "LHP" not in text and "SHP" not in text
