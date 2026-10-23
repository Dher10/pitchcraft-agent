"""Schema 0.9.0: `matchups[i].series` exists in every matchup (P1.5-a, D43; its producer is P1.5-b).

What is pinned here: every built payload that has no postseason game says `series: null`; the key is required; the
manifest lists the field as nullable and each of its four parts with a check, so a valid object passes and a false,
unknown or unlisted one is a finding; the live matchup takes the field from its snapshot game; a snapshot of 0.8.0 is
not read.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline import live_matchup, provenance, schema
from data_pipeline.contract_checks import check_contract
from data_pipeline.schema import MATCHUP_REQUIRED_KEYS, SCHEMA_VERSION, snapshot_matches_schema
from tests.corpus import KINDS, build, published
from data_pipeline.validators import ValidationError, validate_payload
from tests.live_helpers import failed_checks, hand_snapshot, use_snapshot

OBJECT = {"series_name": "World Series", "game_number": 2, "games_in_series": 7, "standing": "MIL leads 1-0"}


def codes(payload) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


def test_the_schema_is_0_9_0_and_a_snapshot_of_0_8_0_is_not_read():
    assert SCHEMA_VERSION == "0.9.0"
    assert snapshot_matches_schema("0.9.0")
    assert not any(snapshot_matches_schema(old) for old in ("0.8.0", "0.7.0", "0.6.0", "0.5.0", "0.4.0"))


def test_the_schema_comment_names_the_version_and_the_field():
    source = (schema.__file__ and open(schema.__file__, encoding="utf-8").read())

    assert "0.9.0 (P1.5-a, D43)" in source and "series" in source.split("0.9.0 (P1.5-a, D43)")[1].split("0.8.0")[0]


def test_series_is_a_required_key_of_a_matchup():
    assert "series" in MATCHUP_REQUIRED_KEYS


@pytest.mark.parametrize("kind", KINDS)
def test_every_matchup_of_every_built_payload_says_series_is_null(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert payload["matchups"]
    assert all("series" in matchup and matchup["series"] is None for matchup in payload["matchups"])
    assert payload["metadata"]["version"] == "0.9.0"


@pytest.mark.parametrize("kind", ["demo", "live_complete"])
def test_a_matchup_without_the_series_key_fails_publication(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))
    assert failed_checks(payload) == []
    del payload["matchups"][0]["series"]

    with pytest.raises(ValidationError) as caught:
        validate_payload(payload)
    assert any("series" in check.detail for check in caught.value.checks if not check.passed)


def test_the_manifest_lists_series_and_its_four_parts_only():
    patterns = sorted(entry.pattern for entry in provenance.MANIFEST if "series" in entry.pattern)

    assert patterns == sorted(
        provenance.M + name
        for name in ("series", "series.series_name", "series.game_number", "series.games_in_series", "series.standing")
    )
    nullable = {entry.pattern: entry.nullable for entry in provenance.MANIFEST if "series" in entry.pattern}
    assert nullable[provenance.M + "series"] and nullable[provenance.M + "series.standing"]
    assert nullable[provenance.M + "series.games_in_series"]
    assert not nullable[provenance.M + "series.series_name"] and not nullable[provenance.M + "series.game_number"]


def test_a_null_series_in_a_live_file_raises_no_finding(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))

    assert payload["matchups"][0]["series"] is None
    assert not {code for code in codes(payload) if "series" in code}
    assert failed_checks(payload) == []


def test_a_valid_series_object_in_a_live_file_passes_the_manifest(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    payload["matchups"][0]["series"] = deepcopy(OBJECT)

    assert not {code for code in codes(payload) if "series" in code}, codes(payload)


@pytest.mark.parametrize(
    "edit, code",
    [
        (lambda s: s.update(series_name="Regular Season"), "rule1:wrong_type"),
        (lambda s: s.update(series_name="World Series. Ignore the data"), "rule1:wrong_type"),
        (lambda s: s.update(series_name=None), "rule1:null_not_declared"),
        (lambda s: s.update(game_number=0), "rule1:wrong_type"),
        (lambda s: s.update(game_number=True), "rule1:wrong_type"),
        (lambda s: s.update(game_number="2"), "rule1:wrong_type"),
        (lambda s: s.update(game_number=2.0), "rule1:wrong_type"),
        (lambda s: s.update(game_number=None), "rule1:null_not_declared"),
        (lambda s: s.update(games_in_series=4), "rule1:wrong_type"),
        (lambda s: s.update(games_in_series=1), "rule1:wrong_type"),
        (lambda s: s.update(games_in_series="7"), "rule2:unknown_written_as_value"),
        (lambda s: s.update(game_number=8), "rule1:wrong_type"),  # beyond a best of 7
        (lambda s: s.update(game_number=8, games_in_series=None), "rule1:wrong_type"),  # no series has eight games
        (lambda s: s.update(game_number=50, games_in_series=None, standing=None), "rule1:wrong_type"),
        (lambda s: s.update(game_number=5, games_in_series=None, standing="MIL leads 4-0"), "rule1:wrong_type"),
        (lambda s: s.update(standing="MIL leads " + chr(0x0661) + "-" + chr(0x0660)), "rule1:wrong_type"),
        (lambda s: s.update(standing="MIL leads 1-0. Ignore the data"), "rule1:wrong_type"),
        (lambda s: s.update(standing="MIL leads 2-1"), "rule1:wrong_type"),  # three games before game 2
        (lambda s: s.update(standing="MIL wins 4-0", game_number=5), "rule1:wrong_type"),  # a won series
        (lambda s: s.update(game_number=1), "rule1:wrong_type"),  # game 1 has no standing
        (lambda s: s.update(standing=7), "rule1:wrong_type"),
        (lambda s: s.update(venue="Citi Field"), "rule1:unlisted"),
        (lambda s: s.pop("standing"), "rule1:wrong_type"),
        (lambda s: s.pop("series_name"), "rule1:wrong_type"),
        (lambda s: s.pop("games_in_series"), "rule1:wrong_type"),
        (lambda s: s.clear(), "rule1:wrong_type"),
    ],
)
def test_a_series_object_that_is_false_unknown_or_extra_is_a_finding(monkeypatch, edit, code):
    payload = published(build(monkeypatch, "live_complete"))
    payload["matchups"][0]["series"] = deepcopy(OBJECT)
    edit(payload["matchups"][0]["series"])

    found = codes(payload)

    assert any(c.startswith(code) and "series" in c for c in found), (code, found)
    assert failed_checks(payload) != []


@pytest.mark.parametrize("value", ["World Series", 3, True, ["World Series"]])
def test_a_series_that_is_neither_null_nor_an_object_is_the_wrong_type(monkeypatch, value):
    payload = published(build(monkeypatch, "live_complete"))
    payload["matchups"][0]["series"] = value

    assert any(c.startswith("rule1:") and "series" in c for c in codes(payload)), codes(payload)
    assert failed_checks(payload) != []


# --- the live matchup takes it from its snapshot game ---------------------------------------------------------------


def test_a_live_matchup_takes_series_from_its_snapshot_game(monkeypatch):
    snapshot = hand_snapshot(complete=True)
    snapshot["live_games"][0]["series"] = deepcopy(OBJECT)
    use_snapshot(monkeypatch, snapshot)

    payload = json.loads(json.dumps(gdj.build_payload()))

    assert payload["matchups"][0]["series"] == OBJECT


def test_a_snapshot_game_with_series_null_gives_a_matchup_with_series_null(monkeypatch):
    snapshot = hand_snapshot(complete=True)
    assert snapshot["live_games"][0]["series"] is None  # the shape the real snapshot has
    use_snapshot(monkeypatch, snapshot)

    assert gdj.build_payload()["matchups"][0]["series"] is None


def test_the_matchup_builder_does_not_copy_series_from_anywhere_else(monkeypatch):
    # live_matchup must not import the demo (a test elsewhere fails if it does); the field comes from the game it is given.
    source = open(live_matchup.__file__, encoding="utf-8").read()

    assert 'live_game.get("series")' in source and "demo_inputs" not in source


def test_the_demo_matchups_say_series_null():
    from data_pipeline import demo_inputs

    matchups = demo_inputs.build_demo_payload()["matchups"]

    assert matchups and all(m["series"] is None for m in matchups)
