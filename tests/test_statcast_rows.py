"""Every populated Statcast row is validated before it is filtered (QA4-02, PLAN.md P0.15-C).

Run 4: the required columns existed, but their values were missing in populated rows, and the date
comparison and `isin` filter treated a missing value as "excluded". A frame whose `game_type` was None in
every row became a debut with 0 pitches and no error; one missing `game_date` among valid rows silently
shrank the pitch count. Malformed data became a successful, undercounted sample.

A row that cannot say when it was played and what kind of game it was is a malformed source answer:
a recorded source failure, never an exclusion. What stays legitimate, with no error: a valid empty frame
(a debut), spring training / exhibition / all-star rows, and rows dated after the cutoff.
"""

from __future__ import annotations

import io

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests import test_as_of_end_to_end as e2e
from tests.test_as_of_end_to_end import batting_csv, leaky_sources  # noqa: F401  (fixture)
from tests.test_live_sample_pipeline import API_STATS, events_frame, frame, isolated, route  # noqa: F401

CUTOFF = "2026-07-14"


def assigned(df: pd.DataFrame, column: str, value, rows=None) -> pd.DataFrame:
    """A copy with `column` set to `value` in `rows` (every row when None); the dtype may become object."""

    out = df.copy()
    out[column] = out[column].astype(object)
    out.loc[out.index if rows is None else rows, column] = value
    return out


def pitcher(monkeypatch, df: pd.DataFrame, api=API_STATS):
    route(monkeypatch, [("/stats?", api)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: df)
    return lp.fetch_pitcher_statcast(11, "Row Ace", as_of=CUTOFF)


# --- pitcher frames --------------------------------------------------------------------------------------

MALFORMED = {
    "game_type missing in every row": lambda f: assigned(f, "game_type", None),
    "game_type missing in one row": lambda f: assigned(f, "game_type", None, rows=[3]),
    "game_type unknown": lambda f: assigned(f, "game_type", "X", rows=[0]),
    "game_type in lowercase": lambda f: assigned(f, "game_type", "r", rows=[5]),
    "game_type empty": lambda f: assigned(f, "game_type", "", rows=[2]),
    "game_date missing in one row": lambda f: assigned(f, "game_date", None, rows=[0]),
    "game_date missing in every row": lambda f: assigned(f, "game_date", None),
    "game_date not a date": lambda f: assigned(f, "game_date", "not-a-date", rows=[4]),
    "game_date a number": lambda f: assigned(f, "game_date", 20260701, rows=[1]),
}


@pytest.mark.parametrize("name", list(MALFORMED))
def test_a_malformed_row_is_a_recorded_source_failure_not_an_undercounted_sample(monkeypatch, name):
    result = pitcher(monkeypatch, MALFORMED[name](events_frame()))

    assert result is None
    assert [error["source"] for error in lp._run_errors] == ["statcast_pitcher"]
    message = lp._run_errors[0]["message"]
    assert ("game_type" if "game_type" in name else "game_date") in message
    assert "row" in message


def test_the_qa_probe_one_missing_date_no_longer_drops_one_pitch_silently(monkeypatch):
    # 170 rows, one without a date: it used to publish 169 pitches and no error.
    result = pitcher(monkeypatch, assigned(events_frame(), "game_date", None, rows=[0]))

    assert result is None and len(lp._run_errors) == 1


def test_the_qa_probe_a_game_type_missing_everywhere_is_not_a_debut(leaky_sources, monkeypatch):
    # Through the whole pipeline: it used to end ok with 0 pitches for both starters.
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: assigned(e2e.STATCAST, "game_type", None))

    record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)

    assert snapshot is None
    assert record["status"] == "failed"
    assert {error["source"] for error in record["errors"]} == {"statcast_pitcher"}
    assert all("game_type" in error["message"] for error in record["errors"])


# What stays legitimate: nothing here is an error.


def test_a_valid_empty_frame_is_still_a_debut(monkeypatch):
    route(monkeypatch, [("/stats?", {"stats": [{"splits": []}]}), ("/people/11", {"people": [{"pitchHand": {"code": "R"}}]})])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: pd.DataFrame())

    result = lp.fetch_pitcher_statcast(11, "Row Ace", as_of=CUTOFF)

    assert result["sample"]["arsenal"]["pitches"] == 0 and lp._run_errors == []


@pytest.mark.parametrize("game_type", ["S", "E", "A"])
def test_spring_exhibition_and_all_star_rows_are_excluded_without_an_error(monkeypatch, game_type):
    mixed = pd.concat([events_frame(), frame(n_plain=40, game_type=game_type, game_date="2026-03-10")], ignore_index=True)

    result = pitcher(monkeypatch, mixed)

    assert result["sample"]["arsenal"]["pitches"] == 150 + len(e2e_events()) and lp._run_errors == []


def e2e_events() -> list:
    from tests.test_live_sample_pipeline import EVENTS

    return EVENTS


def test_rows_after_the_cutoff_are_excluded_without_an_error(monkeypatch):
    mixed = pd.concat([events_frame(), frame(n_plain=40, game_date="2026-07-20")], ignore_index=True)

    result = pitcher(monkeypatch, mixed)

    assert result["sample"]["arsenal"]["pitches"] == 150 + len(e2e_events()) and lp._run_errors == []


@pytest.mark.parametrize("game_type", ["F", "D", "L", "W"])
def test_postseason_rows_up_to_the_cutoff_are_kept(monkeypatch, game_type):
    # postseason rows only: he has no regular-season line (the API's is regular season), so there is nothing missing
    result = pitcher(monkeypatch, events_frame(n_plain=120, game_type=game_type, game_date="2026-07-10"), api={"stats": [{"splits": []}]})

    assert result["sample"]["arsenal"]["pitches"] == 120 + len(e2e_events())
    assert result["sample"]["arsenal"]["scope"]["kind"] == "regular_and_postseason" and lp._run_errors == []


def test_dates_written_as_text_are_accepted(monkeypatch):
    text_dates = assigned(events_frame(), "game_date", "2026-07-01")

    result = pitcher(monkeypatch, text_dates)

    assert result["sample"]["arsenal"]["pitches"] == 170 and lp._run_errors == []


# --- team batting frames ----------------------------------------------------------------------------------------


def batting(month: str = "2026-07-01", team: str = "NYY") -> pd.DataFrame:
    return pd.read_csv(io.StringIO(batting_csv(team, month)))


TEAM_MALFORMED = {
    "game_type missing in every row": lambda f: assigned(f, "game_type", None),
    "game_type missing in one row": lambda f: assigned(f, "game_type", None, rows=[7]),
    "game_type unknown": lambda f: assigned(f, "game_type", "Z", rows=[0]),
    "game_date missing in one row": lambda f: assigned(f, "game_date", None, rows=[0]),
    "game_date not a date": lambda f: assigned(f, "game_date", "someday", rows=[30]),
    # The columns that decide whether a row is this team's plate appearance and against which hand:
    # a missing value would drop the row from the split without a word.
    "inning_topbot missing in one row": lambda f: assigned(f, "inning_topbot", None, rows=[2]),
    "inning_topbot unknown": lambda f: assigned(f, "inning_topbot", "Middle", rows=[2]),
    "home_team missing in one row": lambda f: assigned(f, "home_team", None, rows=[4]),
    "away_team empty in one row": lambda f: assigned(f, "away_team", "", rows=[4]),
    "p_throws missing in one row": lambda f: assigned(f, "p_throws", None, rows=[6]),
    "p_throws unknown": lambda f: assigned(f, "p_throws", "S", rows=[6]),
}


@pytest.mark.parametrize("name", list(TEAM_MALFORMED))
def test_a_malformed_team_batting_row_is_an_error_not_a_smaller_split(name):
    with pytest.raises(ValueError, match="team batting.*row"):
        lp.derive_team_splits(TEAM_MALFORMED[name](batting()), "NYY", CUTOFF)


def test_valid_team_batting_rows_still_give_the_split():
    splits = lp.derive_team_splits(batting(), "NYY", CUTOFF)

    assert splits["vr"]["plate_appearances"] == 20


def test_team_batting_spring_training_and_later_dates_are_excluded_without_an_error():
    rows = batting()
    spring = rows.copy()
    spring["game_type"] = "S"
    spring["game_date"] = "2026-03-10"
    mixed = pd.concat([rows, spring], ignore_index=True)

    splits = lp.derive_team_splits(mixed, "NYY", CUTOFF)  # the 50 home runs of July 20 are after the cutoff

    assert splits["vr"]["plate_appearances"] == 20


def test_an_empty_team_batting_frame_is_still_no_splits():
    assert lp.derive_team_splits(pd.DataFrame(), "NYY", CUTOFF) == {}


def test_an_invalid_month_is_a_recorded_failure_and_is_not_cached(leaky_sources, monkeypatch):
    bad = assigned(batting(), "game_date", None, rows=[0]).to_csv(index=False)
    monkeypatch.setattr(lp, "_get_text", lambda url, timeout=60: bad if "game_date_gt=2026-07" in url else "")

    splits = lp.fetch_team_splits(147, as_of=CUTOFF)

    assert splits == {}
    assert [error["source"] for error in lp._run_errors] == ["savant_team_batting"]
    assert "game_date" in lp._run_errors[0]["message"]
    assert not [path for path in lp.TEAM_BATTING_CACHE_DIR.glob("*2026-07*.csv")], "the invalid month was cached"
