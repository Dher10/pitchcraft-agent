"""A Statcast frame that holds fewer plate appearances than the API line says is incomplete (P0.15-D2.2f, F21).

The API line (batters faced, regular season, opening day to the cutoff) and the plate appearances that end in
a regular-season Statcast row are two counts of the same thing. When Statcast has fewer, the pitch data of the
starter is a piece of what he threw, and a mix, a primary pitch or a put-away pitch made from it is a claim the
data does not support. The correction (contract rule 2, "Malformed or incomplete"): a recorded
`statcast_pitcher` error, no pitch data for that starter (unknown, not 0), the API counts kept.

The tolerance is measured, not assumed: `tests/fixtures/statcast_vs_api_pairs.json` has 28 real pitchers (818
appearances, 9,414 batters faced) and the gap is 0 in every one. The two real pitchers whose cached frame holds
only the games of their second club are incomplete against their aggregate season line (the pipeline reads
`splits[0]`, one club, until F22: these tests prove the rule, not that path).

Controls (they pass before the fix and say what must not change): Statcast with more plate appearances than the
API, a line without batters faced, a measured zero, an unusable `events` column, postseason rows that the API
does not count.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import (  # noqa: F401  (isolated is an autouse fixture)
    API_STATS,
    EVENTS,
    _api_line,
    events_frame,
    frame,
    isolated,
    route,
)

PAIRS = json.loads((Path(__file__).parent / "fixtures" / "statcast_vs_api_pairs.json").read_text(encoding="utf-8"))
CUTOFF = "2026-07-14"
PLATE_APPEARANCES = 19  # `events_frame()`: 19 completed plate appearances and one truncated one
PEOPLE = {"people": [{"pitchHand": {"code": "L"}}]}


def line(batters_faced, strikeouts=4, walks=3, home_runs=2):
    return _api_line(
        era="3.10", whip="1.05", inningsPitched="6.1",
        battersFaced=batters_faced, strikeOuts=strikeouts, baseOnBalls=walks, homeRuns=home_runs,
    )


def fetch(monkeypatch, df, api, as_of=CUTOFF):
    route(monkeypatch, [("/stats?", api), ("/people/", PEOPLE)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: df)
    return lp.fetch_pitcher_statcast(11, "Gap Ace", as_of=as_of)


def statcast_errors() -> list[str]:
    return [error["message"] for error in lp._run_errors if error["source"] == "statcast_pitcher"]


def incomplete_errors() -> list[str]:
    return [message for message in statcast_errors() if "incomplete" in message]


def assert_no_pitch_data(result: dict) -> None:
    assert result["sample"]["arsenal"] == {"pitches": None, "scope": None}  # unknown, not 0
    assert result["pitch_mix"] == [] and result["velocity_by_pitch"] == [] and result["movement"] == {}
    assert result["pitch_locations"] == {"vs_lhh": [], "vs_rhh": []}
    assert result["pitching_profile"]["primary_pitch"] == "Not available"
    assert result["pitching_profile"]["putaway_pitch"] == "Not available"


# --- the measurement: real pairs --------------------------------------------------------------------------------


def test_the_calibration_is_made_of_at_least_25_real_pitchers():
    assert len(PAIRS["pairs"]) >= 25
    assert sum(pair["appearances"] for pair in PAIRS["pairs"]) >= 800
    assert all(pair["statcast_games"] == pair["appearances"] for pair in PAIRS["pairs"])


def test_the_gap_between_the_api_and_statcast_is_zero_in_every_real_pair():
    """The observed maximum gap per appearance, and the tolerance the code derives from it."""

    worst = max(
        (pair["api_batters_faced"] - pair["statcast_plate_appearances"]) / pair["appearances"] for pair in PAIRS["pairs"]
    )

    assert worst <= lp.STATCAST_PA_TOLERANCE == 0
    assert worst <= 1  # the bound the plan set before measuring: more than one per appearance would have stopped the commit


def test_intentional_walks_need_no_tolerance_statcast_writes_a_row_for_them():
    assert all(pair["api_intentional_walks"] == pair["statcast_intent_walks"] for pair in PAIRS["pairs"])
    assert sum(pair["api_intentional_walks"] for pair in PAIRS["pairs"]) > 0  # the pairs do contain some


@pytest.mark.parametrize("pair", PAIRS["pairs"], ids=lambda pair: str(pair["pitcher_id"]))
def test_no_real_complete_frame_is_called_incomplete(pair):
    assert not lp.statcast_is_short(pair["statcast_plate_appearances"], pair["api_batters_faced"])


@pytest.mark.parametrize("pair", PAIRS["pairs"], ids=lambda pair: str(pair["pitcher_id"]))
def test_a_real_frame_that_lost_one_plate_appearance_is_called_incomplete(pair):
    """The check is not vacuous: one plate appearance fewer than the API says is already incomplete."""

    assert lp.statcast_is_short(pair["statcast_plate_appearances"] - 1, pair["api_batters_faced"])


@pytest.mark.parametrize("pair", PAIRS["short_frames"], ids=lambda pair: str(pair["pitcher_id"]))
def test_the_real_frames_that_hold_only_part_of_the_season_are_called_incomplete_against_the_aggregate_line(pair):
    assert pair["appearances"] > pair["statcast_games"]
    assert lp.statcast_is_short(pair["statcast_plate_appearances"], pair["api_batters_faced"])


# --- the rule on a frame ----------------------------------------------------------------------------------------


def test_a_frame_counts_the_plate_appearances_of_the_regular_season_only():
    mixed = pd.concat([events_frame(), events_frame(game_type="D", game_date="2026-10-05")], ignore_index=True)

    assert lp.regular_season_plate_appearances(mixed) == PLATE_APPEARANCES  # the 19 of the postseason are not the API's
    assert lp.regular_season_plate_appearances(events_frame()) == PLATE_APPEARANCES


def test_an_empty_frame_has_no_plate_appearance_and_a_frame_without_events_cannot_say():
    assert lp.regular_season_plate_appearances(pd.DataFrame()) == 0
    assert lp.regular_season_plate_appearances(frame()) is None  # `events` null in every row
    assert lp.regular_season_plate_appearances(frame().drop(columns=["events"])) is None


@pytest.mark.parametrize(
    ("statcast", "api", "short"),
    [(19, 19, False), (19, 20, True), (19, 18, False), (0, 25, True), (0, 0, False), (0, 1, True)],
)
def test_the_rule_at_its_boundaries(statcast, api, short):
    assert lp.statcast_is_short(statcast, api) is short


# --- the correction, through the real fetcher ---------------------------------------------------------------


def test_fewer_plate_appearances_than_the_api_line_leave_the_starter_without_pitch_data(monkeypatch):
    result = fetch(monkeypatch, events_frame(), line(25))

    assert result is not None  # the game is kept: the API counts are real
    assert_no_pitch_data(result)
    assert len(incomplete_errors()) == 1
    message = incomplete_errors()[0]
    assert str(PLATE_APPEARANCES) in message and "25" in message


def test_the_api_counts_are_kept_when_the_pitch_data_is_dropped(monkeypatch):
    result = fetch(monkeypatch, events_frame(), line(25))

    rates = result["sample"]["rates"]
    assert rates["source"] == "mlb_api"
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (25, 4, 3, 2)
    assert rates["scope"]["kind"] == "regular_season"
    assert result["season_summary"]["era"] == "3.10" and result["season_summary"]["strikeouts"] == 4
    assert result["season_summary"]["scopes"]["counts"]["kind"] == "regular_season"
    assert result["sample"]["limited"]["arsenal"] is True  # no pitch count is below the minimum, as for any unknown


def test_the_hand_still_comes_from_the_frame_when_the_pitch_data_is_dropped(monkeypatch):
    result = fetch(monkeypatch, events_frame(), line(25))

    assert result["throws"] == "R"  # `p_throws` of the frame; the people endpoint was not needed


def test_an_empty_frame_next_to_a_line_with_batters_faced_is_a_gap_not_a_debut(monkeypatch):
    """The extreme case: Statcast has nothing for a pitcher the API says faced 25 batters."""

    result = fetch(monkeypatch, pd.DataFrame(), line(25))

    assert result is not None
    assert_no_pitch_data(result)  # not "0 pitches": he threw some
    assert len(incomplete_errors()) == 1
    assert result["throws"] == "L"  # from the people endpoint: the frame has none
    assert result["sample"]["rates"]["batters_faced"] == 25


def test_a_partial_api_line_with_batters_faced_keeps_what_it_has_and_nothing_else(monkeypatch):
    result = fetch(monkeypatch, events_frame(), _api_line(era="3.10", battersFaced=25, strikeOuts=6))

    assert_no_pitch_data(result)
    rates = result["sample"]["rates"]
    assert rates["source"] == "mlb_api"  # Statcast's counts are not mixed in: its frame is the one that is incomplete
    assert (rates["batters_faced"], rates["strikeouts"], rates["walks"], rates["home_runs"]) == (25, 6, None, None)


def test_postseason_plate_appearances_do_not_fill_a_gap_in_the_regular_season(monkeypatch):
    mixed = pd.concat([events_frame(), events_frame(game_type="D", game_date="2026-10-05")], ignore_index=True)

    result = fetch(monkeypatch, mixed, line(25), as_of="2026-10-08")

    assert_no_pitch_data(result)  # 19 regular-season plate appearances against 25, however many the postseason adds
    assert len(incomplete_errors()) == 1


# --- controls: what must not change ------------------------------------------------------------------------------


def test_control_a_frame_with_every_plate_appearance_keeps_its_pitch_data(monkeypatch):
    result = fetch(monkeypatch, events_frame(), line(PLATE_APPEARANCES))

    assert result["sample"]["arsenal"]["pitches"] == 150 + len(EVENTS)
    assert result["pitch_mix"] and incomplete_errors() == []
    assert result["sample"]["rates"]["source"] == "mlb_api"


def test_control_statcast_with_more_plate_appearances_than_the_api_is_not_flagged(monkeypatch):
    """The API is the official line: more rows in Statcast (the postseason is already out) is not a gap."""

    result = fetch(monkeypatch, events_frame(), line(10, strikeouts=2, walks=1, home_runs=1))

    assert result["sample"]["arsenal"]["pitches"] == 150 + len(EVENTS)
    assert incomplete_errors() == []


def test_control_a_line_without_batters_faced_has_nothing_to_compare(monkeypatch):
    result = fetch(monkeypatch, events_frame(), _api_line(era="3.10", whip="1.05", inningsPitched="101.0"))

    assert result["sample"]["arsenal"]["pitches"] == 150 + len(EVENTS)
    assert incomplete_errors() == []


def test_control_a_measured_zero_next_to_an_empty_frame_is_a_debut(monkeypatch):
    result = fetch(monkeypatch, pd.DataFrame(), line(0, 0, 0, 0))

    assert result["sample"]["arsenal"]["pitches"] == 0  # measured over a valid empty answer
    assert result["sample"]["rates"]["batters_faced"] == 0
    assert incomplete_errors() == []


def test_control_no_line_at_all_is_a_debut_as_before(monkeypatch):
    result = fetch(monkeypatch, pd.DataFrame(), {"stats": [{"splits": []}]})

    assert result["sample"]["arsenal"]["pitches"] == 0
    assert incomplete_errors() == []


def test_control_events_that_cannot_be_read_skip_the_comparison_and_keep_their_own_error(monkeypatch):
    result = fetch(monkeypatch, frame(), API_STATS)

    assert result["sample"]["arsenal"]["pitches"] == 150
    assert incomplete_errors() == []
    assert any("events" in message for message in statcast_errors())
