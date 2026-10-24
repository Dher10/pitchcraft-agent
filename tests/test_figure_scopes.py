"""Every group of figures states the scope of the source that gave it (QA4-01, PLAN.md P0.15-B).

Run 4: the MLB API gave ERA, WHIP and innings (regular season only) but not every count; the counts then
came from Statcast, which includes the postseason. The whole season summary was labelled "regular season
and postseason" and the report said "all pitcher figures cover the regular season and postseason", so
the regular-season ERA was publicly presented as a postseason-inclusive figure. Publication validation
accepted it.

There are three groups, each with its own scope, read from one place (`labels.figure_scopes`):
    pitch data          Statcast: regular season, plus the postseason when such pitches are in the frame
    ERA, WHIP, innings  the MLB API: regular season only
    the four counts     whichever source supplied them: the MLB API (regular season) or Statcast

The analyst, the writer, the critic, the validator and the starter card use those scopes and never say
"all figures" when they differ.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re

import pandas as pd
import pytest

from agents import critic
from agents.language import catalog_for
from data_pipeline import generate_demo_json as gdj
from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline as lp
from tests.live_helpers import debut_starter, failed_checks, hand_snapshot, snapshot_from_starters, use_snapshot
from tests.test_live_sample_pipeline import API_STATS, NO_SPLITS, events_frame, frame, isolated, route  # noqa: F401

REGULAR = {"game_day": "2026-07-15", "cutoff": "2026-07-14"}
POSTSEASON = {"game_day": "2026-10-09", "cutoff": "2026-10-08"}

EVERY_COUNT_BUT_HOME_RUNS = deepcopy(API_STATS)
del EVERY_COUNT_BUT_HOME_RUNS["stats"][0]["splits"][0]["stat"]["homeRuns"]
ONLY_RATES = deepcopy(API_STATS)
for key in ("strikeOuts", "baseOnBalls", "homeRuns", "battersFaced"):
    del ONLY_RATES["stats"][0]["splits"][0]["stat"][key]
API = {
    "complete": API_STATS,
    "missing_home_runs": EVERY_COUNT_BUT_HOME_RUNS,
    "only_rates": ONLY_RATES,
    "absent": NO_SPLITS,
}


def frame_for(season: str):
    if season == "postseason":
        # his regular season (the API line is about it: 19 batters faced) and postseason pitches before the cutoff
        return pd.concat([events_frame(), frame(n_plain=30, game_type="D", game_date="2026-10-05")], ignore_index=True)
    return events_frame()


def rich_postseason_frame():
    """His regular season plus 220 postseason plate appearances (27% strikeouts): enough for the strikeout and control labels."""

    events = ["strikeout"] * 60 + ["walk"] * 10 + ["field_out"] * 150
    return pd.concat(
        [events_frame(), frame(extra_rows=[{"events": e} for e in events], game_type="D", game_date="2026-10-05")],
        ignore_index=True,
    )


def build_payload(monkeypatch, api: str, season: str, statcast=None) -> dict:
    """The real fetchers over a frame and an API answer, then the generator: the whole way."""

    dates = POSTSEASON if season == "postseason" else REGULAR
    route(monkeypatch, [("/stats?", API[api])])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: statcast if statcast is not None else frame_for(season))
    away = lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of=dates["cutoff"])
    home = lp.fetch_pitcher_statcast(22, "Bravo Liveleft", as_of=dates["cutoff"])
    assert away and home and lp._run_errors == []
    use_snapshot(
        monkeypatch,
        snapshot_from_starters(away, home, game_day=dates["game_day"], cutoff=dates["cutoff"]),
    )
    return gdj.build_payload()


def live_starters(payload: dict) -> list[dict]:
    return list(payload["matchups"][0]["starters"].values())


def report_text(payload: dict) -> str:
    return json.dumps(payload["matchups"][0]["report"])


def expected_scopes(api: str, season: str) -> dict[str, str | None]:
    """What each group's kind must be, from the source that gave it."""

    pitch = labels.SCOPE_REGULAR_POSTSEASON if season == "postseason" else labels.SCOPE_REGULAR
    counts = labels.SCOPE_REGULAR if api == "complete" else pitch  # the API gave all four, or Statcast did
    rates = labels.SCOPE_REGULAR if api != "absent" else None
    return {"pitch_data": pitch, "season_rates": rates, "counts": counts}


# --- the QA probe ---------------------------------------------------------------------------------------


def test_the_qa_probe_partial_api_counts_with_postseason_pitches(monkeypatch):
    payload = build_payload(monkeypatch, "missing_home_runs", "postseason")

    for starter in live_starters(payload):
        summary = starter["season_summary"]
        assert (summary["era"], summary["whip"], summary["innings"]) == ("3.10", "1.05", "6.1")
        assert summary["scopes"]["season_rates"] == labels.make_scope(labels.SCOPE_REGULAR, "2026-10-08")
        assert summary["scopes"]["counts"] == labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-10-08")
        assert starter["sample"]["rates"]["source"] == "statcast"
    text = report_text(payload)
    assert "all pitcher figures" not in text
    assert "different samples" in text
    assert "2026 regular season" in text
    assert "2026 regular season and postseason through Oct 8" in text
    assert failed_checks(payload) == []


# --- every combination of API and season ------------------------------------------------------------------


@pytest.mark.parametrize("season", ["regular", "postseason"])
@pytest.mark.parametrize("api", list(API))
def test_each_group_has_the_scope_of_its_source(monkeypatch, api, season):
    payload = build_payload(monkeypatch, api, season)
    dates = POSTSEASON if season == "postseason" else REGULAR
    expected = expected_scopes(api, season)

    for starter in live_starters(payload):
        groups = labels.figure_scopes(starter)
        assert {name: scope["kind"] for name, scope in groups.items()} == {
            name: kind for name, kind in expected.items() if kind
        }
        assert all(scope["through"] == dates["cutoff"] for scope in groups.values())
        summary = starter["season_summary"]
        assert summary["scopes"]["counts"] == starter["sample"]["rates"]["scope"]
        assert (summary["scopes"]["season_rates"] is None) == (summary["era"] == "N/A")
        assert starter["sample"]["rates"]["source"] == ("mlb_api" if api == "complete" else "statcast")


@pytest.mark.parametrize("season", ["regular", "postseason"])
@pytest.mark.parametrize("api", list(API))
def test_the_report_never_says_all_figures_when_the_groups_differ(monkeypatch, api, season):
    payload = build_payload(monkeypatch, api, season)
    dates = POSTSEASON if season == "postseason" else REGULAR
    kinds = {kind for kind in expected_scopes(api, season).values() if kind}
    text = report_text(payload)

    if len(kinds) > 1:
        assert "all pitcher figures" not in text
        assert "different samples" in text
        for kind in kinds:
            assert labels.make_scope(kind, dates["cutoff"])["label"] in text
    else:
        label = labels.make_scope(kinds.pop(), dates["cutoff"])["label"]
        assert f"all pitcher figures cover the {label}" in text
    assert failed_checks(payload) == []


def test_without_the_api_every_group_is_statcast_and_nothing_needs_qualifying(monkeypatch):
    payload = build_payload(monkeypatch, "absent", "postseason", statcast=rich_postseason_frame())
    text = report_text(payload).lower()

    assert "shows" in text and "rates)" not in text
    assert "all pitcher figures cover the 2026 regular season and postseason through oct 8" in text


@pytest.mark.parametrize("api", ["missing_home_runs", "only_rates"])
def test_a_rate_claim_is_qualified_with_the_scope_of_the_counts_behind_it(monkeypatch, api):
    # The counts came from Statcast, so with postseason pitches they cover the postseason too.
    payload = build_payload(monkeypatch, api, "postseason", statcast=rich_postseason_frame())
    text = report_text(payload).lower()

    assert "shows" in text and "(regular season and postseason rates)" in text
    assert "(regular-season rates)" not in text


# --- publication validation -----------------------------------------------------------------------------------


@pytest.fixture()
def probe_payload(monkeypatch) -> dict:
    payload = build_payload(monkeypatch, "missing_home_runs", "postseason")
    assert failed_checks(payload) == []
    return payload


def starter_of(payload: dict) -> dict:
    return payload["matchups"][0]["starters"]["away_starter"]


def scope_failures(payload: dict) -> list[str]:
    return [failure for failure in failed_checks(payload) if "scope" in failure]


def test_a_counts_scope_that_claims_the_postseason_for_api_counts_is_rejected(monkeypatch):
    payload = build_payload(monkeypatch, "complete", "postseason")
    assert failed_checks(payload) == []
    starter = starter_of(payload)
    wrong = labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-10-08")

    starter["season_summary"]["scopes"]["counts"] = wrong
    starter["sample"]["rates"]["scope"] = wrong

    assert scope_failures(payload)


def test_a_rates_scope_that_claims_the_postseason_is_rejected(probe_payload):
    starter_of(probe_payload)["season_summary"]["scopes"]["season_rates"] = labels.make_scope(
        labels.SCOPE_REGULAR_POSTSEASON, "2026-10-08"
    )

    assert scope_failures(probe_payload)


def test_a_counts_scope_that_calls_statcast_counts_regular_season_is_rejected(probe_payload):
    starter = starter_of(probe_payload)
    regular = labels.make_scope(labels.SCOPE_REGULAR, "2026-10-08")
    starter["season_summary"]["scopes"]["counts"] = regular
    starter["sample"]["rates"]["scope"] = regular

    assert scope_failures(probe_payload)


def test_a_summary_scope_that_differs_from_the_sample_scope_is_rejected(probe_payload):
    starter_of(probe_payload)["season_summary"]["scopes"]["counts"] = labels.make_scope(
        labels.SCOPE_REGULAR, "2026-10-08"
    )

    assert scope_failures(probe_payload)


@pytest.mark.parametrize("missing", ["season_rates", "counts"])
def test_a_figure_group_without_its_scope_is_rejected(probe_payload, missing):
    starter_of(probe_payload)["season_summary"]["scopes"][missing] = None

    assert scope_failures(probe_payload)


def test_a_summary_without_scopes_is_rejected(probe_payload):
    del starter_of(probe_payload)["season_summary"]["scopes"]

    assert scope_failures(probe_payload)


def test_an_unavailable_group_must_not_carry_a_scope(monkeypatch):
    payload = build_payload(monkeypatch, "absent", "regular")
    assert failed_checks(payload) == []
    starter_of(payload)["season_summary"]["scopes"]["season_rates"] = labels.make_scope(
        labels.SCOPE_REGULAR, "2026-07-14"
    )

    assert scope_failures(payload)


# --- the critic ---------------------------------------------------------------------------------------------


def scope_check(report: dict, matchup: dict) -> dict:
    t = catalog_for("en")
    checks = critic.run(report, matchup)["checks"]
    return next(check for check in checks if check["claim"] == t("critic.scope.claim"))


def test_a_report_that_says_all_figures_for_a_starter_whose_groups_differ_is_unsupported(probe_payload):
    matchup = probe_payload["matchups"][0]
    report = deepcopy(matchup["report"])
    report["sections"][-1]["body"] = (
        "Alpha Livearm: all pitcher figures cover the 2026 regular season and postseason through Oct 8."
    )

    check = scope_check(report, matchup)

    assert check["status"] == "unsupported"
    assert "Alpha Livearm" in check["evidence"]


def test_the_real_report_for_the_probe_is_supported(probe_payload):
    matchup = probe_payload["matchups"][0]

    assert scope_check(matchup["report"], matchup)["status"] == "supported"


# --- the one place the scopes are read -----------------------------------------------------------------------------


def a_starter(*, pitches=1500, source="mlb_api", era="3.10", scopes=None) -> dict:
    regular = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")
    sample = labels.build_sample(
        pitches=pitches, arsenal_scope=regular, batters_faced=400, strikeouts=90, walks=30, home_runs=10,
        rates_source=source, rates_scope=regular,
    )
    unavailable = era == "N/A"
    return {
        "sample": sample,
        "season_summary": {
            "era": era,
            "whip": "N/A" if unavailable else "1.05",
            "innings": "N/A" if unavailable else "101.0",
            "strikeouts": 90,
            "walks": 30,
            "home_runs_allowed": 10,
            "scopes": scopes if scopes is not None else {"season_rates": regular, "counts": regular},
        },
    }


def test_figure_scopes_lists_only_groups_that_have_figures():
    regular = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")

    assert set(labels.figure_scopes(a_starter())) == {"pitch_data", "season_rates", "counts"}
    assert "pitch_data" not in labels.figure_scopes(a_starter(pitches=0))
    no_rates = a_starter(era="N/A", scopes={"season_rates": None, "counts": regular})
    assert "season_rates" not in labels.figure_scopes(no_rates)
    assert "counts" not in labels.figure_scopes(a_starter(source="unavailable"))
    assert labels.figure_scopes({}) == {}  # a demo starter has no sample: nothing to say


def test_scopes_differ_only_when_a_group_with_figures_has_another_kind():
    both = labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-07-14")
    regular = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")

    assert not labels.scopes_differ(a_starter())
    assert labels.scopes_differ(a_starter(scopes={"season_rates": regular, "counts": both}))
    # A group without figures never makes the others "differ".
    assert not labels.scopes_differ(a_starter(pitches=0, scopes={"season_rates": regular, "counts": regular}))


def test_agents_read_scopes_only_through_labels():
    root = Path(__file__).resolve().parents[1] / "agents"
    direct = re.compile(r"""\[["'](?:scope|scopes)["']\]|\.get\(["']scopes?["']""")
    offenders = [
        f"{path.name}:{number}"
        for path in sorted(root.glob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if direct.search(line) and "offense" not in line
    ]
    assert offenders == [], f"scopes read outside labels.figure_scopes: {offenders}"


# --- a starter with no figures claims no scope ----------------------------------------------------------------------


def confidence_note(payload: dict) -> str:
    sections = payload["matchups"][0]["report"]["sections"]
    return next(section["body"] for section in sections if section["title"] == "Data Confidence Note")


def test_two_debuts_claim_no_scope_and_say_there_are_no_season_figures(monkeypatch):
    # Both starters have no pitch, no ERA, no count: there is nothing for a scope to cover.
    use_snapshot(monkeypatch, hand_snapshot(complete=False))

    payload = gdj.build_payload()

    note = confidence_note(payload)
    assert "Alpha Livearm and Bravo Liveleft: no season figures are available." in note
    assert "all pitcher figures" not in note
    assert not any(labels.figure_scopes(starter) for starter in live_starters(payload))
    assert failed_checks(payload) == []


def test_a_debut_next_to_a_starter_with_figures_each_get_their_own_note(monkeypatch):
    route(monkeypatch, [("/stats?", API["complete"])])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, **k: events_frame())
    away = lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03")
    home = debut_starter("Bravo Liveleft", "R")
    use_snapshot(monkeypatch, snapshot_from_starters(away, home))

    payload = gdj.build_payload()

    note = confidence_note(payload)
    assert "Bravo Liveleft: no season figures are available." in note
    assert "Alpha Livearm: all pitcher figures cover the 2026 regular season through Jul 3." in note
    assert "Bravo Liveleft: all pitcher figures" not in note
    assert failed_checks(payload) == []


def test_a_starter_with_figures_is_never_told_he_has_none(monkeypatch):
    payload = build_payload(monkeypatch, "complete", "regular")

    assert "no season figures are available" not in confidence_note(payload)
