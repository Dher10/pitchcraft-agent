"""R4-D4: the starter check and the final line from one boxscore (D66; docs/plans/R4.md 4.2).

The boxscore answers here are SYNTHETIC, written from the documented shape: no real answer was recorded when the module
was written. The strict reading means the first real answer either matches or leaves the starters `unknown`.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline import archive_boxscore as bx
from data_pipeline import archive_games as ag

PROBABLE = {"away": 607259, "home": 694819}


def player(pid, name, **pitching):
    return {f"ID{pid}": {"person": {"id": pid, "fullName": name}, "stats": {"pitching": pitching}}}


def box(away_pitchers=(607259, 111), home_pitchers=(694819, 222), **lines):
    away = {"inningsPitched": "6.1", "hits": 4, "earnedRuns": 1, "baseOnBalls": 2, "strikeOuts": 7}
    home = {"inningsPitched": "5.2", "hits": 6, "earnedRuns": 3, "baseOnBalls": 1, "strikeOuts": 5}
    away.update(lines.get("away", {}))
    home.update(lines.get("home", {}))
    away_players = {**player(607259, "Nick Martinez", **away), **player(111, "Reliever A", inningsPitched="2.0", hits=0)}
    home_players = {**player(694819, "Jacob Misiorowski", **home), **player(222, "Reliever B", inningsPitched="1.0")}
    if away_pitchers and away_pitchers[0] not in (607259, 111):
        away_players.update(player(away_pitchers[0], "Other Away", inningsPitched="1.0", hits=0, earnedRuns=0, baseOnBalls=0, strikeOuts=0))
    return {"teams": {"away": {"pitchers": list(away_pitchers), "players": away_players},
                      "home": {"pitchers": list(home_pitchers), "players": home_players}}}


def test_the_url_is_built_only_from_a_positive_integer():
    assert bx.boxscore_url(849805).endswith("/game/849805/boxscore")
    for bad in ("849805", 0, -1, None, True, 1.5):
        with pytest.raises(ValueError):
            bx.boxscore_url(bad)


def test_the_first_pitcher_listed_is_the_starter_and_his_line_is_the_source_values():
    check, line = bx.starters_and_lines(box(), PROBABLE)
    assert check == {"away": "started", "home": "started",
                     "actual": {"away": {"id": 607259, "name": "Nick Martinez"}, "home": {"id": 694819, "name": "Jacob Misiorowski"}}}
    assert line["away"] == {"innings_pitched": "6.1", "hits": 4, "earned_runs": 1, "walks": 2, "strikeouts": 7}
    assert line["home"] == {"innings_pitched": "5.2", "hits": 6, "earned_runs": 3, "walks": 1, "strikeouts": 5}


def test_the_line_never_belongs_to_a_reliever():
    _, line = bx.starters_and_lines(box(), PROBABLE)
    assert line["away"]["hits"] == 4 and line["away"]["innings_pitched"] != "2.0"


def test_a_probable_starter_who_did_not_start_is_said_so_and_the_line_is_the_one_who_did():
    check, line = bx.starters_and_lines(box(away_pitchers=(999, 607259)), PROBABLE)
    assert check["away"] == "did_not_start" and check["actual"]["away"] == {"id": 999, "name": "Other Away"}
    assert line["away"] == {"innings_pitched": "1.0", "hits": 0, "earned_runs": 0, "walks": 0, "strikeouts": 0}
    assert check["home"] == "started"


def test_a_real_zero_is_a_zero_and_a_missing_field_is_none_never_zero():
    check, line = bx.starters_and_lines(box(away={"hits": 0, "earnedRuns": 0}), PROBABLE)
    assert line["away"]["hits"] == 0 and line["away"]["earned_runs"] == 0
    data = box()
    del data["teams"]["away"]["players"]["ID607259"]["stats"]["pitching"]["hits"]
    del data["teams"]["away"]["players"]["ID607259"]["stats"]["pitching"]["inningsPitched"]
    _, line = bx.starters_and_lines(data, PROBABLE)
    assert line["away"]["hits"] is None and line["away"]["innings_pitched"] is None and line["away"]["strikeouts"] == 7


@pytest.mark.parametrize("bad", [-1, 2.5, "4", True, None])
def test_a_count_that_is_not_a_count_is_none(bad):
    _, line = bx.starters_and_lines(box(away={"hits": bad}), PROBABLE)
    assert line["away"]["hits"] is None


@pytest.mark.parametrize("bad", ["6.3", "6,1", 6.1, "", "six", "6.1 IP", None])
def test_innings_that_are_not_innings_are_none(bad):
    _, line = bx.starters_and_lines(box(away={"inningsPitched": bad}), PROBABLE)
    assert line["away"]["innings_pitched"] is None


def test_without_a_pitching_block_there_is_no_line_but_the_starter_is_known():
    data = box()
    del data["teams"]["away"]["players"]["ID607259"]["stats"]
    check, line = bx.starters_and_lines(data, PROBABLE)
    assert check["away"] == "started" and line["away"] is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["teams"]["away"].__setitem__("pitchers", []),
        lambda d: d["teams"]["away"].__setitem__("pitchers", [True]),
        lambda d: d["teams"]["away"].__setitem__("pitchers", ["607259"]),
        lambda d: d["teams"]["away"].__setitem__("pitchers", None),
        lambda d: d["teams"]["away"].__setitem__("players", {}),
        lambda d: d["teams"]["away"].__setitem__("players", None),
        lambda d: d["teams"]["away"]["players"]["ID607259"]["person"].__setitem__("id", 5),
        lambda d: d["teams"]["away"]["players"]["ID607259"]["person"].__setitem__("fullName", " "),
        lambda d: d["teams"]["away"]["players"]["ID607259"].__setitem__("person", None),
        lambda d: d["teams"].__delitem__("away"),
    ],
)
def test_an_unreadable_side_is_unknown_never_started(mutate):
    data = box()
    mutate(data)
    check, line = bx.starters_and_lines(data, PROBABLE)
    assert check["away"] == "unknown" and check["actual"]["away"] is None and line["away"] is None
    assert check["home"] == "started"  # the other side is judged on its own


@pytest.mark.parametrize("data", [None, [], "x", {}, {"teams": {}}, {"message": "Internal error"}])
def test_an_unreadable_answer_is_unknown_on_both_sides(data):
    check, line = bx.starters_and_lines(data, PROBABLE)
    assert check == ag.unknown_starters_check() and line == {"away": None, "home": None}


@pytest.mark.parametrize("probable", [{"away": None, "home": 694819}, {"away": "607259", "home": 694819}, {"away": True, "home": 694819}, {}])
def test_an_unknown_probable_starter_is_unknown_not_started(probable):
    check, line = bx.starters_and_lines(box(), probable)
    assert check["away"] == "unknown" and check["actual"]["away"] is None and line["away"] is None


def test_the_result_is_a_valid_envelope_part():
    """What this module returns is exactly what `validate_game_file` accepts."""

    from tests.test_archive_games import PUBLISHED, SOURCE, records, schedule_game

    (record,) = records(schedule_game())
    check, line = bx.starters_and_lines(box(), PROBABLE)
    document = ag.build_game_file(record, PUBLISHED, ag.published_origin(PUBLISHED, record, SOURCE), check, line,
                                  {"away": {"id": 607259, "prior_mlb_seasons": 8}, "home": {"id": 694819, "prior_mlb_seasons": None}})
    assert ag.validate_game_file(document) == []
    document["final_line"]["away"] = dict(line["away"], hits=-1)
    assert ag.validate_game_file(document) != []


def test_nothing_in_the_output_grades_or_derives():
    _, line = bx.starters_and_lines(box(), PROBABLE)
    assert set(line["away"]) == set(ag.FINAL_LINE_FIELDS)


def test_the_input_is_not_modified():
    data = box()
    before = deepcopy(data)
    bx.starters_and_lines(data, PROBABLE)
    assert data == before


def test_the_module_has_no_network_and_no_file_access():
    from pathlib import Path

    source = Path(bx.__file__).read_text(encoding="utf-8")
    for forbidden in ("requests", "urllib", "socket", "open(", "read_text", "write_text", "import evals", "from evals"):
        assert forbidden not in source, forbidden
