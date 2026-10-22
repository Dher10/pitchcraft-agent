"""Schema 0.9.0: `matchups[i].series` exists in every matchup and is null until the producer of row 7 (P1.5-a, D43).

Like D37 (schema 0.5.0), this row ships the version, the field and the readers with no producer of a value. What is
pinned here: every built payload says `series: null` for every matchup; the key is required; the manifest lists the
field as nullable and nothing else under it, so an object in a live file is a finding until row 7 adds the entries
with the producer; the live matchup takes the field from its snapshot game; a snapshot of 0.8.0 is not read.
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

OBJECT = {"series_name": "World Series", "game_number": 2, "games_in_series": 7, "standing": "Brewers lead 1-0"}


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


def test_the_manifest_lists_series_as_nullable_and_nothing_under_it():
    patterns = [entry.pattern for entry in provenance.MANIFEST if "series" in entry.pattern]

    assert patterns == [provenance.M + "series"]
    entry = next(entry for entry in provenance.MANIFEST if entry.pattern == provenance.M + "series")
    assert entry.nullable is True


def test_a_null_series_in_a_live_file_raises_no_finding(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))

    assert payload["matchups"][0]["series"] is None
    assert not {code for code in codes(payload) if "series" in code}
    assert failed_checks(payload) == []


def test_an_object_series_in_a_live_file_is_a_finding_until_row_7_lists_its_parts(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    payload["matchups"][0]["series"] = deepcopy(OBJECT)

    found = codes(payload)

    assert any(code.startswith("rule1:unlisted") for code in found), found
    assert failed_checks(payload) != []


@pytest.mark.parametrize("value", ["World Series", 3, True, ["World Series"]])
def test_a_series_that_is_neither_null_nor_an_object_is_the_wrong_type(monkeypatch, value):
    payload = published(build(monkeypatch, "live_complete"))
    payload["matchups"][0]["series"] = value

    assert any(code.startswith("rule1:wrong_type") for code in codes(payload)) or any(
        code.startswith("rule1:unlisted") for code in codes(payload)
    )
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
