"""Schema 0.5.0: a pitch share, a team abbreviation and a pitch family can be null (P0.15-D2.2c).

Nothing writes these nulls yet (F20 is commit d, F6e and F7 commit e). This commit makes every reader ready
first, so that the first producer of a null breaks nothing: `float(None)` is a TypeError, a null abbreviation
was a placeholder in the manifest, and the publication check wanted a number for every share. The tests build
the payloads the producers will write, by hand, and run the real readers over them.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from agents import critic
from agents.language import catalog_for
from data_pipeline import claims_registry as registry
from data_pipeline import generate_demo_json as gdj
from data_pipeline import labels, schema
from data_pipeline import report_facts as facts
from data_pipeline.contract_checks import check_contract
from data_pipeline.schema import SCHEMA_VERSION, snapshot_matches_schema
from tests.corpus import build, published
from tests.live_helpers import failed_checks
from tests.matrix import hard_outcome

SLOTS = ("away_starter", "home_starter")
T = catalog_for("en")


def codes(payload) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


def no_pitch_cells(payload) -> int:
    """The cells of a starter who threw nothing: 0 out of 0, a share that is unknown, not 0%. Returns how many."""

    edited = 0
    for matchup in payload["matchups"]:
        if matchup["data_confidence"]["level"] != "fetched_snapshot":
            continue
        for row in matchup["charts"]["pitch_mix"]:
            for slot in SLOTS:
                if row[slot]["total"] == 0:
                    row[slot]["overall"] = None
                    edited += 1
    return edited


# --- the version -------------------------------------------------------------------------------------------


def test_the_schema_is_0_5_0_and_a_snapshot_of_0_4_0_is_not_read():
    assert SCHEMA_VERSION == "0.6.0"
    assert snapshot_matches_schema("0.6.0") and not snapshot_matches_schema("0.5.0") and not snapshot_matches_schema("0.4.0")


def test_the_demo_file_says_the_schema_it_is_written_under():
    from data_pipeline import demo_inputs

    assert demo_inputs.build_demo_payload()["metadata"]["version"] == schema.SCHEMA_VERSION


# --- a null share (F20 producer, commit d) ------------------------------------------------------------------


@pytest.fixture
def one_debut():
    """A game with a debut (home) and a healthy starter (away): the debut's cells are 0 out of 0."""

    return deepcopy(hard_outcome("home_debut_away_healthy").payload)


def test_a_null_share_out_of_no_pitches_passes_the_publication_check(one_debut):
    assert no_pitch_cells(one_debut) > 0

    assert failed_checks(one_debut) == []


def test_a_null_share_out_of_no_pitches_is_what_the_manifest_wants(one_debut):
    assert no_pitch_cells(one_debut) > 0

    found = codes(one_debut)

    assert not {c for c in found if "overall" in c and c.startswith(("rule2:", "rule1:null_not_declared"))}
    assert not {c for c in found if c.endswith("#unreadable")}


def test_a_null_share_out_of_pitches_is_wrong(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    cell = payload["matchups"][0]["charts"]["pitch_mix"][0]["away_starter"]
    assert cell["total"] > 0
    cell["overall"] = None

    assert any(c.startswith("rule1:derivation_mismatch#") and c.endswith(".overall") for c in codes(payload))
    assert failed_checks(payload) != []


def test_the_readers_of_the_share_take_a_null_as_not_thrown(one_debut):
    matchup = deepcopy(one_debut["matchups"][0])
    for row in matchup["charts"]["pitch_mix"]:
        for slot in SLOTS:
            row[slot] = {"overall": None, "vs_lhh": None, "vs_rhh": None}  # no raw counts: the demo's shape
    pitch = matchup["charts"]["pitch_mix"][0]["pitch"]

    assert critic._was_thrown(None, None) is False
    assert critic._pitch_usage(matchup, "away_starter", pitch) == 0
    assert all(not facts.thrown_by(matchup, slot) for slot in SLOTS)
    assert registry._thrown_share(matchup, "away_starter", pitch, 15) == (False, False)
    assert registry._share({"overall": None}) is None and registry._share({"overall": 12.5}) == 12.5


def test_a_claim_that_cites_a_null_share_fails_its_condition_instead_of_crashing(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    before = codes(payload)
    matchup = payload["matchups"][0]
    primary = matchup["starters"]["away_starter"]["pitching_profile"]["primary_pitch"].lower().replace(" fastball", "")
    for row in matchup["charts"]["pitch_mix"]:
        if row["pitch"].lower().replace(" fastball", "") == primary:
            row["away_starter"]["overall"] = None

    new = codes(payload) - before

    assert "rule4:critic.pitch.supported_primary#usage" in new
    assert not {c for c in new if c.endswith("#unreadable")}


def test_the_critic_runs_over_a_matchup_whose_cells_are_null(one_debut):
    matchup = deepcopy(one_debut["matchups"][0])
    assert no_pitch_cells({"matchups": [matchup]}) > 0
    report = {key: matchup["report"][key] for key in ("headline", "short_summary", "sections")}

    review = critic.run(report, matchup)

    assert review["status"] == "reviewed"


# --- a null abbreviation (F7 producer, commit e) --------------------------------------------------------------


def unnamed_team_payload(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    matchup = payload["matchups"][0]
    matchup["teams"]["away"]["abbreviation"] = None
    matchup["starters"]["away_starter"]["team"] = None
    row = next(row for row in payload["archive"] if row["id"] == matchup["id"])
    row["title"] = f"{matchup['teams']['away']['name']} vs {matchup['teams']['home']['abbreviation']}"
    return payload


def test_a_team_with_no_abbreviation_is_not_a_placeholder_for_the_manifest(monkeypatch):
    found = codes(published(unnamed_team_payload(monkeypatch)))

    assert not {c for c in found if "abbreviation" in c or c.endswith("starters.*.team")}


def test_the_title_of_an_archive_row_uses_the_name_of_a_team_with_no_abbreviation(monkeypatch):
    payload = published(unnamed_team_payload(monkeypatch))
    payload["archive"][0]["title"] = "None vs NYY"  # what an f-string over a null would write

    assert any(c.startswith("rule1:derivation_mismatch#archive[].title") for c in codes(payload))


def test_a_game_may_come_without_an_abbreviation_but_not_without_a_name():
    game = {
        "away_team": "Brand New Club", "home_team": "New York Yankees", "away_team_abbr": None, "home_team_abbr": "NYY",
        "away_team_id": 999, "home_team_id": 147, "away_pitcher_id": 1, "home_pitcher_id": 2,
        "start_time_utc": "2026-07-15T23:05:00Z",
    }

    assert gdj._featured_game_problem(game) is None
    assert gdj._featured_game_problem({**game, "away_team": ""}) == "featured_game.away_team is missing"
    absent = {key: value for key, value in game.items() if key != "away_team_abbr"}
    assert gdj._featured_game_problem(absent) == "featured_game.away_team_abbr is missing"


def test_the_team_label_is_the_abbreviation_or_the_name():
    assert labels.team_label("BOS", "Boston Red Sox") == "BOS"
    assert labels.team_label(None, "Brand New Club") == "Brand New Club"
