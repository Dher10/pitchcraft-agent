"""P2.4 packets: the as-of season line of a starter comes from his cached game log, never from a request.

`season_line_as_of` replaces `fetch_pitcher_season_stats` for the historical cases. It sums only the regular-season rows
dated strictly before the game date (D29), so a row on the game date or later cannot reach a case. The rows below are
SYNTHETIC but have the fields of the real `gameLog` answer (checked against a cached answer of 2026-10-30).
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from evals import build_packets as bp

GAME_DATE = "2026-07-15"


def row(day, ip, er, hits, walks, strikeouts, homers, faced, game_type="R"):
    return {
        "date": day,
        "gameType": game_type,
        "stat": {
            "inningsPitched": ip,
            "earnedRuns": er,
            "hits": hits,
            "baseOnBalls": walks,
            "strikeOuts": strikeouts,
            "homeRuns": homers,
            "battersFaced": faced,
            "gamesStarted": 1,
        },
    }


def answer(rows, season_line=None):
    blocks = [{"type": {"displayName": "gameLog"}, "splits": rows}]
    year = [{"season": "2025", "gameType": "R", "stat": {"gamesPlayed": 30}}]
    if season_line is not None:
        year.append({"season": "2026", "gameType": "R", "stat": season_line})
    blocks.append({"type": {"displayName": "yearByYear"}, "splits": year})
    return {"stats": blocks}


TWO = [
    row("2026-07-01", "6.0", 2, 5, 1, 7, 1, 24),
    row("2026-07-08", "5.2", 3, 6, 2, 4, 0, 24),
]
EXPECTED = {
    "era": "3.86",  # 27 * 5 earned runs / 35 outs
    "whip": "1.20",  # 3 * (11 hits + 3 walks) / 35 outs
    "innings": "11.2",
    "strikeouts": 11,
    "walks": 3,
    "home_runs_allowed": 1,
    "batters_faced": 48,
}


def test_the_line_is_the_sum_of_the_rows_before_the_game():
    assert bp.season_line_as_of(answer(TWO), GAME_DATE) == EXPECTED


@pytest.mark.parametrize("leak_day", [GAME_DATE, "2026-07-16", "2026-09-30"])
def test_a_row_on_the_game_date_or_later_changes_nothing(leak_day):
    leaked = TWO + [row(leak_day, "9.0", 9, 20, 9, 20, 9, 99)]

    assert bp.season_line_as_of(answer(leaked), GAME_DATE) == EXPECTED


def test_a_row_the_day_before_the_game_counts():
    one_more = TWO + [row("2026-07-14", "1.0", 0, 0, 0, 1, 0, 3)]

    assert bp.season_line_as_of(answer(one_more), GAME_DATE)["batters_faced"] == 51


def test_no_row_before_the_game_is_unavailable_not_zero():
    assert bp.season_line_as_of(answer([]), GAME_DATE) == {}
    assert bp.season_line_as_of(answer([row(GAME_DATE, "6.0", 1, 4, 1, 5, 0, 22)]), GAME_DATE) == {}


def test_rows_that_are_not_regular_season_are_left_out():
    mixed = TWO + [row("2026-07-12", "1.0", 5, 5, 5, 0, 5, 9, game_type="S")]

    assert bp.season_line_as_of(answer(mixed), GAME_DATE) == EXPECTED


def test_a_row_without_a_game_type_makes_the_line_unavailable():
    broken = deepcopy(TWO)
    del broken[1]["gameType"]

    assert bp.season_line_as_of(answer(broken), GAME_DATE) == {}


@pytest.mark.parametrize("field", ["inningsPitched", "earnedRuns", "hits", "baseOnBalls", "strikeOuts", "homeRuns", "battersFaced"])
def test_a_missing_figure_makes_the_whole_line_unavailable_never_a_zero(field):
    broken = deepcopy(TWO)
    del broken[0]["stat"][field]

    assert bp.season_line_as_of(answer(broken), GAME_DATE) == {}


@pytest.mark.parametrize("bad", ["abc", "6.3", "6.", "", None, 6.1, "-1.0"])
def test_an_innings_text_that_is_not_innings_makes_the_line_unavailable(bad):
    broken = deepcopy(TWO)
    broken[0]["stat"]["inningsPitched"] = bad

    assert bp.season_line_as_of(answer(broken), GAME_DATE) == {}


def test_a_negative_or_boolean_count_makes_the_line_unavailable():
    for bad in (-1, True, "3"):
        broken = deepcopy(TWO)
        broken[0]["stat"]["strikeOuts"] = bad
        assert bp.season_line_as_of(answer(broken), GAME_DATE) == {}


def test_no_outs_recorded_gives_the_api_placeholders_for_era_and_whip():
    line = bp.season_line_as_of(answer([row("2026-07-01", "0.0", 2, 3, 1, 0, 0, 4)]), GAME_DATE)

    assert line["innings"] == "0.0"
    assert (line["era"], line["whip"]) == ("-.--", "-.--")
    assert line["batters_faced"] == 4


def test_ratios_round_half_up_like_the_api():
    # 27 * 1 / 24 outs = 1.125 -> 1.13 (round half up); 3 * 3 / 24 = 0.375 -> 0.38
    line = bp.season_line_as_of(answer([row("2026-07-01", "8.0", 1, 2, 1, 6, 0, 28)]), GAME_DATE)

    assert (line["era"], line["whip"]) == ("1.13", "0.38")


def test_rows_may_arrive_in_any_order():
    assert bp.season_line_as_of(answer(list(reversed(TWO))), GAME_DATE) == EXPECTED


def test_a_response_without_a_game_log_is_a_shape_error():
    with pytest.raises(bp.PacketError):
        bp.season_line_as_of({"stats": [{"type": {"displayName": "yearByYear"}, "splits": []}]}, GAME_DATE)


# --- the whole season against the API's own season line ---------------------------------------------------------


def test_the_sum_of_the_whole_season_equals_the_api_season_line():
    api = {"era": "3.86", "whip": "1.20", "inningsPitched": "11.2", "strikeOuts": 11, "baseOnBalls": 3, "homeRuns": 1, "battersFaced": 48}

    assert bp.check_against_year_by_year(answer(TWO, api), 2026) == []


def test_a_difference_from_the_api_season_line_is_named():
    api = {"era": "3.86", "whip": "1.20", "inningsPitched": "11.2", "strikeOuts": 12, "baseOnBalls": 3, "homeRuns": 1, "battersFaced": 48}

    assert bp.check_against_year_by_year(answer(TWO, api), 2026) == ["strikeouts: game log 11, season line 12"]


def test_a_season_without_a_year_by_year_line_is_not_checked_and_says_so():
    assert bp.check_against_year_by_year(answer(TWO), 2026) == ["no 2026 line in yearByYear"]
