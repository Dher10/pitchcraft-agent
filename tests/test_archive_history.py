"""R4-D4: the per-starter history of the archive backfill (D66): the season line as of the day before, prior seasons,
one request per pitcher, a digest-checked disk cache.

The `gameLog` and `yearByYear` answers are SYNTHETIC (the shape the P2.4 collection already read for real, 106 lookups,
checked strictly); no request is made here.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from data_pipeline import archive_history as ah
from data_pipeline.fetchers.mlb_schemas import SourceShapeError


def row(day, ip="5.0", faced=21, started=True, game_type="R", er=2, hits=5, walks=2, k=6, hr=1):
    return {
        "date": day, "gameType": game_type,
        "stat": {"inningsPitched": ip, "battersFaced": faced, "earnedRuns": er, "hits": hits, "baseOnBalls": walks,
                 "strikeOuts": k, "homeRuns": hr, "gamesStarted": 1 if started else 0},
    }


def answer(rows, years=(2022, 2023, 2025), extra_year_rows=()):
    year_splits = [{"season": str(y), "stat": {"gamesPlayed": 20}} for y in years] + list(extra_year_rows)
    return {"stats": [{"type": {"displayName": "gameLog"}, "splits": rows},
                      {"type": {"displayName": "yearByYear"}, "splits": year_splits}]}


ROWS = [row("2026-04-02"), row("2026-04-08", ip="6.1", faced=26, er=1, hits=4, walks=1, k=8, hr=0),
        row("2026-10-04", ip="4.0", faced=18, game_type="D")]


def test_the_line_sums_only_regular_season_rows_before_the_game_date():
    line = ah.season_line_as_of(answer(ROWS), "2026-10-05")
    # 5.0 + 6.1 = 11.1 innings = 34 outs; earned runs 3; the postseason row (2026-10-04) is not a regular-season row
    assert line == {"era": "2.38", "whip": "1.06", "innings": "11.1", "strikeouts": 14, "walks": 3,
                    "home_runs_allowed": 1, "batters_faced": 47}


def test_a_row_on_the_game_date_or_later_is_never_summed():
    base = ah.season_line_as_of(answer(ROWS[:2]), "2026-04-08")
    assert base["batters_faced"] == 21  # the 04-08 row is the game's own day
    leaked = ROWS[:1] + [row("2026-04-08", faced=99), row("2026-04-09", faced=99)]
    assert ah.season_line_as_of(answer(leaked), "2026-04-08")["batters_faced"] == 21


def test_no_row_before_the_date_is_unavailable_not_zero():
    assert ah.season_line_as_of(answer(ROWS), "2026-04-02") == {}
    assert ah.season_line_as_of(answer([]), "2026-10-05") == {}


@pytest.mark.parametrize(
    "bad",
    [lambda r: r["stat"].pop("hits"), lambda r: r["stat"].__setitem__("hits", -1), lambda r: r["stat"].__setitem__("hits", "4"),
     lambda r: r["stat"].__setitem__("inningsPitched", "5.3"), lambda r: r["stat"].__setitem__("inningsPitched", None),
     lambda r: r.pop("gameType"), lambda r: r.pop("date")],
)
def test_a_row_before_the_date_with_a_missing_or_bad_figure_makes_the_whole_line_unavailable(bad):
    rows = deepcopy(ROWS)
    bad(rows[0])
    try:
        line = ah.season_line_as_of(answer(rows), "2026-10-05")
    except SourceShapeError:
        return  # a figure of the wrong type is a malformed answer, also never a number
    assert line == {}


def test_a_bad_row_after_the_date_or_of_another_game_type_does_not_matter():
    rows = deepcopy(ROWS)
    rows[2]["stat"].pop("hits")
    assert ah.season_line_as_of(answer(rows), "2026-04-09")["batters_faced"] == 47  # rows of 04-02 and 04-08
    assert ah.season_line_as_of(answer(rows), "2026-10-05") != {}  # the bad row is a postseason row: only regular-season rows are read


def test_zero_innings_gives_dash_rates_not_a_division_by_zero():
    line = ah.season_line_as_of(answer([row("2026-04-02", ip="0.0", faced=3, er=2, hits=2, walks=1, k=0, hr=0)]), "2026-04-03")
    assert line["era"] == "-.--" and line["whip"] == "-.--" and line["innings"] == "0.0" and line["batters_faced"] == 3


def test_the_answer_must_have_a_game_log():
    with pytest.raises(SourceShapeError):
        ah.season_line_as_of({"stats": [{"type": {"displayName": "yearByYear"}, "splits": []}]}, "2026-10-05")
    for bad in (None, {}, {"stats": None}, {"stats": [{}]}, {"message": "x"}):
        with pytest.raises(SourceShapeError):
            ah.season_line_as_of(bad, "2026-10-05")


def test_prior_seasons_counts_earlier_seasons_with_games_and_not_the_current_one():
    assert ah.prior_seasons(answer(ROWS, years=(2022, 2023, 2025, 2026)), 2026) == 3
    assert ah.prior_seasons(answer(ROWS, years=()), 2026) == 0  # a debut is a real 0: he pitched in no earlier season
    two_clubs = [{"season": "2025", "stat": {"gamesPlayed": 5}}]
    assert ah.prior_seasons(answer(ROWS, years=(2025,), extra_year_rows=two_clubs), 2026) == 1  # one season, two lines
    zero = [{"season": "2024", "stat": {"gamesPlayed": 0}}]
    assert ah.prior_seasons(answer(ROWS, years=(2025,), extra_year_rows=zero), 2026) == 1


def test_an_earlier_season_with_no_games_figure_makes_the_count_unknown_not_smaller():
    """Rule 2: unknown is never a number. A season that says nothing about its games cannot be counted as zero games."""

    silent = {"season": "2024", "stat": {}}
    assert ah.prior_seasons(answer(ROWS, years=(2022, 2023), extra_year_rows=[silent]), 2026) is None
    # a season of the current year or later is not an earlier season and does not matter
    later = {"season": "2026", "stat": {}}
    assert ah.prior_seasons(answer(ROWS, years=(2022, 2023), extra_year_rows=[later]), 2026) == 2
    # and a real rookie is a real 0
    assert ah.prior_seasons(answer(ROWS, years=()), 2026) == 0


def test_the_cache_file_is_written_in_one_step(tmp_path):
    ah.HistoryStore(tmp_path, 2026, Net(answer(ROWS))).response(11)
    assert [p.name for p in tmp_path.iterdir()] == ["11_2026.json"]  # no temporary file left behind


def test_prior_seasons_is_none_when_the_answer_has_no_year_by_year():
    only_log = {"stats": [{"type": {"displayName": "gameLog"}, "splits": ROWS}]}
    assert ah.prior_seasons(only_log, 2026) is None


def test_a_year_line_without_a_season_is_a_malformed_answer():
    bad = answer(ROWS, years=(), extra_year_rows=[{"stat": {"gamesPlayed": 5}}])
    with pytest.raises(SourceShapeError):
        ah.prior_seasons(bad, 2026)


# --- the store ---------------------------------------------------------------------------------------------------


class Net:
    def __init__(self, response):
        self.response, self.urls = response, []

    def __call__(self, url):
        self.urls.append(url)
        if isinstance(self.response, Exception):
            raise self.response
        return deepcopy(self.response)


def test_one_request_serves_every_game_of_a_pitcher_and_is_cached_on_disk(tmp_path):
    net = Net(answer(ROWS))
    store = ah.HistoryStore(tmp_path, 2026, net)
    first = store.season_stats(11, "2026-10-05")
    second = store.season_stats(11, "2026-04-08")
    assert len(net.urls) == 1 and store.lookups == 1
    assert "people/11/stats" in net.urls[0] and "stats=gameLog,yearByYear" in net.urls[0] and "season=2026" in net.urls[0]
    assert first["batters_faced"] == 47 and second["batters_faced"] == 21
    reopened = ah.HistoryStore(tmp_path, 2026, Net(OSError("must not be asked")))
    assert reopened.season_stats(11, "2026-10-05") == first and reopened.lookups == 0
    assert reopened.known(11) and not reopened.known(12)


def test_prior_seasons_comes_from_the_same_single_request(tmp_path):
    net = Net(answer(ROWS))
    store = ah.HistoryStore(tmp_path, 2026, net)
    store.season_stats(11, "2026-10-05")
    assert store.prior_seasons(11) == 3 and len(net.urls) == 1


def test_a_malformed_answer_is_never_cached_and_the_request_is_counted(tmp_path):
    net = Net({"stats": [{"type": {"displayName": "gameLog"}}]})
    store = ah.HistoryStore(tmp_path, 2026, net)
    with pytest.raises(SourceShapeError):
        store.season_stats(11, "2026-10-05")
    assert store.lookups == 1 and not list(tmp_path.glob("*.json"))


def test_a_failed_request_is_counted_and_nothing_is_written(tmp_path):
    store = ah.HistoryStore(tmp_path, 2026, Net(OSError("down")))
    with pytest.raises(OSError):
        store.response(11)
    assert store.lookups == 1 and not list(tmp_path.glob("*.json"))


def test_a_cached_record_that_no_longer_matches_its_digest_is_refused(tmp_path):
    ah.HistoryStore(tmp_path, 2026, Net(answer(ROWS))).response(11)
    path = tmp_path / "11_2026.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["response"]["stats"][0]["splits"][0]["stat"]["battersFaced"] = 99
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(SourceShapeError):
        ah.HistoryStore(tmp_path, 2026, Net(answer(ROWS))).response(11)


@pytest.mark.parametrize("bad", [0, -3, "11", None, True, 1.5])
def test_a_pitcher_id_that_is_not_a_positive_integer_never_reaches_a_url_or_a_path(tmp_path, bad):
    net = Net(answer(ROWS))
    store = ah.HistoryStore(tmp_path, 2026, net)
    with pytest.raises(ValueError):
        store.response(bad)
    assert net.urls == []


def test_the_module_imports_nothing_from_evals():
    from pathlib import Path

    source = Path(ah.__file__).read_text(encoding="utf-8")
    assert "import evals" not in source and "from evals" not in source and ".local" not in source
