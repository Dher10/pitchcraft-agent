"""D51: the file names the cutoff set its band claims were written with (schema 0.10.0, `metadata.label_cutoffs`).

D50 moved the lineup cutoffs. The daily file on main is written by the bot and is judged by the code of a later
branch, so every judgement of a cutoff-dependent claim reads the set named in the file; a file without the field
is a 0.9.0 file and is judged with D32. The sets live in one table keyed by decision id (`labels.CUTOFF_SETS`).
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from data_pipeline import archive, demo_inputs, generate_demo_json as gdj, labels, schema
from data_pipeline.claims import verify_claims
from data_pipeline.contract_checks import check_contract
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_no_games_archive import previous, seed  # noqa: F401  (fixtures and helper of the archive tests)
from tests.test_daily import no_network, sources  # noqa: F401

SERVED = Path(__file__).resolve().parents[1] / "public" / "data" / "pitchcraft-demo.json"


def stale_served() -> dict:
    """The v2 copy of the served file: schema 0.9.0, written under D32, no `label_cutoffs`."""

    return json.loads(SERVED.read_text(encoding="utf-8"))


def validation_error(payload) -> str | None:
    try:
        validate_payload(payload)
    except ValidationError as exc:
        return str(exc)
    return None


# --- the table ------------------------------------------------------------------------------------------


def test_the_cutoff_sets_live_in_one_table_keyed_by_decision_id():
    assert labels.CUTOFF_SETS == {
        "D32": {"k": 23.0, "bb": 9.0, "ops": 0.750},
        "D50": {"k": 24.0, "bb": 9.0, "ops": 0.735},
    }
    assert labels.CURRENT_CUTOFFS == "D50" and labels.HISTORICAL_CUTOFFS == "D32"


def test_the_constants_the_agents_read_are_the_current_row():
    row = labels.CUTOFF_SETS[labels.CURRENT_CUTOFFS]
    assert (labels.OFFENSE_K_NOTE_PCT, labels.OFFENSE_BB_NOTE_PCT, labels.OFFENSE_OPS_STRONG) == (row["k"], row["bb"], row["ops"])


@pytest.mark.parametrize(
    "metadata, expected",
    [({}, "D32"), ({"label_cutoffs": "D32"}, "D32"), ({"label_cutoffs": "D50"}, "D50")],
)
def test_a_file_is_judged_with_the_set_it_names_and_a_file_without_the_field_with_d32(metadata, expected):
    assert labels.cutoffs_for(metadata) == labels.CUTOFF_SETS[expected]


@pytest.mark.parametrize("named", ["D99", "d50", "", None, 50, ["D50"], {"D50": 1}])
def test_an_unknown_or_malformed_cutoff_id_fails_closed(named):
    with pytest.raises(labels.UnknownCutoffs):
        labels.cutoffs_for({"label_cutoffs": named})


# --- the stale v2 file and the D50 stamp -----------------------------------------------------------------


def test_the_stale_v2_served_file_has_no_field_and_passes_under_d32():
    payload = stale_served()
    assert payload["metadata"]["version"] == "0.9.0" and "label_cutoffs" not in payload["metadata"]  # control: it is the stale file

    assert validation_error(payload) is None
    assert verify_claims(payload) == []


def test_the_stale_file_is_really_a_d32_only_file():
    # control for the next test: the .744 lineup is "average" only because D32 judges it
    ops = [m["teams"][side]["offense_profile"]["ops_vs_hand"] for m in stale_served()["matchups"] for side in ("home", "away")]
    assert ".744" in ops


def test_a_d50_stamped_file_with_744_ops_labeled_average_fails():
    payload = stale_served()
    payload["metadata"]["version"] = "0.10.0"
    payload["metadata"]["label_cutoffs"] = "D50"

    error = validation_error(payload)

    assert error is not None and "0.744 is strong, not average" in error
    assert any("0.744 is strong, not average" in v.message for v in check_contract(payload))


def test_the_same_claims_stamped_d32_still_pass():
    payload = stale_served()
    payload["metadata"]["version"] = "0.10.0"
    payload["metadata"]["label_cutoffs"] = "D32"

    assert validation_error(payload) is None


def test_an_unknown_cutoff_id_fails_the_validator_and_the_claims_check():
    payload = stale_served()
    payload["metadata"]["version"] = "0.10.0"
    payload["metadata"]["label_cutoffs"] = "D99"

    assert "label_cutoffs" in (validation_error(payload) or "")
    assert any("label_cutoffs" in p for p in verify_claims(payload))


def test_the_new_version_requires_the_field_and_the_old_one_has_none():
    current = gdj.build_payload()
    assert validation_error(current) is None  # control: the generator's file passes

    missing = deepcopy(current)
    del missing["metadata"]["label_cutoffs"]
    assert "label_cutoffs" in (validation_error(missing) or "")

    old = stale_served()
    old["metadata"]["label_cutoffs"] = "D32"  # 0.9.0 has no such field
    assert "label_cutoffs" in (validation_error(old) or "")


def test_the_generator_stamps_the_current_set_and_the_new_version():
    payload = gdj.build_payload()

    assert payload["metadata"]["version"] == schema.SCHEMA_VERSION == "0.10.0"
    assert payload["metadata"]["label_cutoffs"] == labels.CURRENT_CUTOFFS == "D50"
    assert demo_inputs.build_demo_payload()["metadata"]["label_cutoffs"] == "D50"


def test_only_the_stale_version_is_also_readable():
    assert schema.READABLE_VERSIONS == ("0.9.0", "0.10.0")
    assert schema.snapshot_matches_schema("0.10.0") and not schema.snapshot_matches_schema("0.9.0")  # a snapshot is exact


# --- the daily job after the release ---------------------------------------------------------------------


def test_a_published_0_9_0_live_file_is_still_a_valid_archive_source(sources, previous):  # noqa: F811
    seeded = seed(sources, previous)
    assert seeded["metadata"]["version"] == "0.10.0"  # control: a fresh file carries the new version

    old = deepcopy(seeded)  # what main holds before the release: the same file written by 0.9.0 code
    old["metadata"]["version"] = "0.9.0"
    del old["metadata"]["label_cutoffs"]
    assert validation_error(old) is None
    rows = archive.carry_forward(old, "2026-07-16")

    assert [r["id"] for r in rows] == ["2026-07-15:matchup_001"]


def test_an_unknown_version_is_still_refused_as_an_archive_source(sources, previous):  # noqa: F811
    old = deepcopy(seed(sources, previous))
    old["metadata"]["version"] = "0.8.0"

    with pytest.raises(archive.ArchiveError):
        archive.carry_forward(old, "2026-07-16")
