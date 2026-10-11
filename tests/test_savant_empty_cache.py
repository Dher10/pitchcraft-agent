"""A valid empty finished month is cached; a failed response is not (QA-09, D23).

D23: each monthly chunk of the team-batting fetch is requested once and cached. An empty
month (off-season, a team with no games in the range) is a valid answer and used to be
re-requested on every run, spending the request budget for nothing. A response that is not
the CSV Savant sends (an error page, a dropped connection) is a failure and must never be
cached as "empty".
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_team_splits_as_of import savant  # noqa: F401  (a fixture)

APRIL = (date(2026, 4, 1), date(2026, 4, 30))


def cache_files() -> list:
    return sorted(lp.TEAM_BATTING_CACHE_DIR.glob("*.csv")) if lp.TEAM_BATTING_CACHE_DIR.exists() else []


@pytest.mark.parametrize("body", ["", "   ", "\n\n"])
def test_an_empty_finished_month_is_requested_once(savant, body):
    urls, state = savant
    state["csv"] = body

    first = lp.fetch_team_batting_statcast("NYY", *APRIL)
    second = lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert len(urls) == 1, "the same finished month was requested again"
    assert len(first) == 0 and len(second) == 0
    assert len(cache_files()) == 1


def test_the_cached_empty_month_has_the_columns_of_every_other_month(savant):
    _, state = savant
    state["csv"] = ""
    lp.fetch_team_batting_statcast("NYY", *APRIL)

    again = lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert list(again.columns) == list(lp.TEAM_BATTING_COLUMNS)
    assert lp.derive_team_splits(again, "NYY", "2026-07-14") == {}


def test_an_empty_month_counts_once_against_the_request_budget(savant):
    _, state = savant
    state["csv"] = ""

    for _ in range(3):
        lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert lp._savant_run["requests"] == 1


def test_an_empty_month_between_full_months_keeps_the_full_ones(savant):
    urls, state = savant
    full = state["csv"]
    state["csv"] = full
    lp.fetch_team_batting_statcast("NYY", date(2026, 3, 1), date(2026, 3, 31))
    state["csv"] = ""
    lp.fetch_team_batting_statcast("NYY", *APRIL)
    state["csv"] = full

    df = lp.fetch_team_batting_statcast("NYY", date(2026, 3, 1), date(2026, 4, 30))

    assert len(urls) == 2  # both months came from the cache the second time
    assert len(df) > 0


def test_a_failed_request_is_not_cached_as_an_empty_month(savant, monkeypatch):
    urls, _ = savant

    def down(url, timeout=60):
        urls.append(url)
        raise OSError("connection reset")

    monkeypatch.setattr(lp, "_get_text", down)

    for _ in range(2):
        with pytest.raises(OSError):
            lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert len(urls) == 2
    assert cache_files() == []


@pytest.mark.parametrize(
    "body",
    ["<html><body>Service unavailable</body></html>", '{"message": "rate limited"}', "Error 503"],
)
def test_a_response_that_is_not_the_csv_is_a_failure_and_is_not_cached(savant, body):
    urls, state = savant
    state["csv"] = body

    for _ in range(2):
        with pytest.raises(ValueError):
            lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert len(urls) == 2
    assert cache_files() == []


def test_an_empty_month_that_is_not_finished_is_not_cached(savant):
    urls, state = savant
    state["csv"] = ""
    today = date.today()
    start = today.replace(day=1)

    lp.fetch_team_batting_statcast("NYY", start, today)
    lp.fetch_team_batting_statcast("NYY", start, today)

    assert len(urls) == 2
    assert cache_files() == []


def test_an_empty_chunk_ending_yesterday_is_cached_under_its_end_date(savant):
    urls, state = savant
    state["csv"] = ""
    yesterday = date.today() - timedelta(days=1)
    start = yesterday - timedelta(days=3)
    if start.month != yesterday.month:
        pytest.skip("the range crosses a month boundary today")

    lp.fetch_team_batting_statcast("NYY", start, yesterday)
    lp.fetch_team_batting_statcast("NYY", start, yesterday)

    assert len(urls) == 1
    assert cache_files()[0].name == f"NYY_{start}_{yesterday}.csv"
