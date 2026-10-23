"""QA5-05: validate fetched and cached months identically before using them.

Removing cache validation must prevent recovery, reuse poisoned rows, or write
an invalid fresh answer. Requests/pacing are real budget logic over mocked text.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import isolated  # noqa: F401
from tests.test_team_splits_as_of import savant, pa_rows, VS_L  # noqa: F401


APRIL = (date(2026, 4, 1), date(2026, 4, 30))


def invalid_month(kind):
    source = pd.DataFrame(pa_rows("NYY", "L", VS_L, game_date="2026-04-10"))
    if kind.startswith("missing:"):
        return source.drop(columns=[kind.split(":")[1]]).to_csv(index=False)
    if kind == "bad-date":
        source.loc[0, "game_date"] = "not-a-date"
    elif kind == "unknown-event":
        source.loc[0, "events"] = "provider_error"
    elif kind == "null-events":
        source["events"] = None
    elif kind == "bad-hand":
        source.loc[0, "p_throws"] = "X"
    elif kind == "empty-file":
        return ""
    elif kind == "error-envelope":
        return '{"error": "provider failed"}'
    elif kind == "incomplete-header":
        return "game_date\n"
    return source.to_csv(index=False)


INVALID = [*("missing:" + column for column in lp.TEAM_SPLIT_REQUIRED_COLUMNS),
           "bad-date", "unknown-event", "null-events", "bad-hand", "empty-file", "error-envelope", "incomplete-header"]


def seed(text):
    path = lp.TEAM_BATTING_CACHE_DIR / "NYY_2026-04-01_2026-04-30.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize("kind", [kind for kind in INVALID if kind != "empty-file"])
def test_an_invalid_fresh_month_is_never_cached_and_a_later_answer_can_recover(savant, kind):
    urls, state = savant
    valid = state["csv"]
    state["csv"] = invalid_month(kind)

    with pytest.raises(ValueError):
        lp.fetch_team_batting_statcast("NYY", *APRIL)
    assert list(lp.TEAM_BATTING_CACHE_DIR.glob("*.csv")) == []

    state["csv"] = valid
    recovered = lp.fetch_team_batting_statcast("NYY", *APRIL)
    assert len(urls) == 2
    assert lp.derive_team_splits(recovered, "NYY", "2026-07-14")["vl"]["ops"] == "1.350"


@pytest.mark.parametrize("kind", INVALID)
def test_a_poisoned_cache_is_refetched_and_replaced_only_with_a_valid_month(savant, kind):
    urls, state = savant
    path = seed(invalid_month(kind))

    recovered = lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert len(urls) == 1
    assert lp._savant_run["requests"] == 1
    assert lp.derive_team_splits(recovered, "NYY", "2026-07-14")["vl"]["ops"] == "1.350"
    cached = pd.read_csv(path)
    assert set(lp.TEAM_SPLIT_REQUIRED_COLUMNS) <= set(cached.columns)
    assert cached["events"].tolist() == VS_L
    lp.fetch_team_batting_statcast("NYY", *APRIL)
    assert len(urls) == 1


def test_an_invalid_replacement_leaves_the_previous_cache_bytes_untouched(savant):
    urls, state = savant
    path = seed(invalid_month("unknown-event"))
    previous = path.read_bytes()
    state["csv"] = invalid_month("missing:events")

    with pytest.raises(lp.MissingColumn):
        lp.fetch_team_batting_statcast("NYY", *APRIL)
    assert path.read_bytes() == previous and len(urls) == 1


@pytest.mark.parametrize("open_month", [False, True], ids=["closed-budget", "open-budget"])
def test_cache_recovery_cannot_bypass_the_existing_request_budget(savant, monkeypatch, open_month):
    urls, state = savant
    path = seed(invalid_month("missing:events"))
    previous = path.read_bytes()
    monkeypatch.setattr(lp, "_is_open_chunk", lambda *args: open_month)
    if open_month:
        monkeypatch.setattr(lp, "_savant_run", {"requests": 0, "open_requests": 10})
        exception = lp.SavantOpenMonthBudgetExceeded
    else:
        monkeypatch.setattr(lp, "_savant_run", {"requests": 210, "open_requests": 0})
        exception = lp.SavantRequestCapExceeded

    with pytest.raises(exception):
        lp.fetch_team_batting_statcast("NYY", *APRIL)
    assert urls == [] and path.read_bytes() == previous


def test_control_valid_header_only_month_is_cached_once(savant):
    urls, state = savant
    state["csv"] = pd.DataFrame(columns=lp.TEAM_BATTING_COLUMNS).to_csv(index=False)
    for _ in range(2):
        result = lp.fetch_team_batting_statcast("NYY", *APRIL)
        assert result.empty and set(lp.TEAM_SPLIT_REQUIRED_COLUMNS) <= set(result.columns)
    assert len(urls) == 1


def test_probe_d_a_missing_events_month_is_recorded_and_never_cached(savant):
    urls, state = savant
    state["csv"] = invalid_month("missing:events")

    result = lp.fetch_team_splits(147, as_of="2026-04-30", season_start="2026-04-01")

    assert result == {}
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("savant_team_batting", "missing_column")]
    assert list(lp.TEAM_BATTING_CACHE_DIR.glob("*.csv")) == []


def test_a_cached_month_at_the_row_cap_is_refetched_instead_of_trusted(savant, monkeypatch):
    urls, state = savant
    monkeypatch.setattr(lp, "SAVANT_ROW_CAP", 5)
    seed(pd.DataFrame(pa_rows("NYY", "R", VS_L)).to_csv(index=False))
    state["csv"] = pd.DataFrame(pa_rows("NYY", "R", ["single", "field_out"])).to_csv(index=False)

    recovered = lp.fetch_team_batting_statcast("NYY", *APRIL)

    assert len(urls) == 1 and len(recovered) == 2
    assert lp.derive_team_splits(recovered, "NYY", "2026-07-14")["vr"]["ops"] == "1.000"
