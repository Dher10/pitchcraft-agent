"""P1-R2-f: exact approved labels/copy; the season response is read locally, never fetched in tests."""

from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

import pytest

from data_pipeline import generate_demo_json as gdj, labels
from data_pipeline import season_calendar
from data_pipeline.contract_checks import check_contract
from data_pipeline.provenance import findings
from data_pipeline.validators import validate_payload
from tests.corpus import build, published

REFERENCE = Path(__file__).resolve().parents[1] / "data_pipeline/reference/mlb_seasons_2026.json"
END = json.loads(REFERENCE.read_bytes())["seasons"][0]["regularSeasonEndDate"]


@pytest.mark.parametrize("cutoff", [END, (date.fromisoformat(END) + timedelta(days=1)).isoformat(), "2026-10-22"])
def test_complete_regular_season_label_names_the_year_without_a_through_date(cutoff):
    scope = labels.make_scope(labels.SCOPE_REGULAR, cutoff)
    assert scope == {"kind": "regular_season", "through": cutoff, "label": "2026 regular season"}


@pytest.mark.parametrize("kind, cutoff, expected", [
    (labels.SCOPE_REGULAR, "2026-07-14", "2026 regular season through Jul 14"),
    (labels.SCOPE_REGULAR_POSTSEASON, "2026-10-22", "2026 regular season and postseason through Oct 22"),
    (labels.SCOPE_REGULAR, "2027-10-22", "2027 regular season through Oct 22"),
    (labels.SCOPE_REGULAR_POSTSEASON, "2027-07-04", "2027 regular season and postseason through Jul 4"),
])
def test_partial_postseason_and_missing_reference_seasons_keep_the_exact_cutoff(kind, cutoff, expected):
    scope = labels.make_scope(kind, cutoff)
    assert scope["kind"] == kind and scope["through"] == cutoff
    assert scope["label"] == expected


def test_the_season_reference_is_the_unmodified_one_request_response_with_source_and_hash():
    metadata = json.loads(REFERENCE.with_suffix(".source.json").read_bytes())
    assert metadata["source_url"] == "https://statsapi.mlb.com/api/v1/seasons/2026?sportId=1"
    assert metadata["requests"] == 1
    assert hashlib.sha256(REFERENCE.read_bytes()).hexdigest() == metadata["sha256"]
    assert END == "2026-09-27"


@pytest.mark.parametrize("count, expected", [(0, "Loaded data for 0 matchups."),
    (1, "Loaded data for 1 matchup."), (3, "Loaded data for 3 matchups.")])
def test_loaded_workflow_plural_through_the_real_generator(count, expected):
    workflow = gdj._build_agent_workflow([f"matchup_{n}" for n in range(count)], gdj.AgentRun(total_warnings=0, graded_starters=0))
    assert workflow["steps"][0]["output"] == expected


def test_the_registry_rejects_plural_matchups_for_a_single_matchup(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    assert len(payload["matchups"]) == 1
    claim = next(c for c in payload["claims"] if c["key"].startswith("generator.workflow.loaded"))
    claim["key"] = "generator.workflow.loaded"
    payload["agent_workflow"]["steps"][0]["output"] = "Loaded data for 1 matchups."
    assert any(v.code.startswith("rule4:generator.workflow.loaded#count") for v in check_contract(payload))


def test_scope_label_and_offline_validation_share_the_reference(monkeypatch):
    payload = published(build(monkeypatch, "live_complete"))
    assert all(check.passed for check in validate_payload(payload))
    broken = deepcopy(payload)
    scope = broken["matchups"][0]["starters"]["away_starter"]["season_summary"]["scopes"]["season_rates"]
    assert scope is not None
    scope["label"] = "2026 regular season"  # this corpus is a mid-season July game
    assert any(code.startswith("rule1:derivation_mismatch#") for code, _, _ in findings(broken))


def test_control_the_day_before_the_official_end_keeps_its_cutoff():
    cutoff = (date.fromisoformat(END) - timedelta(days=1)).isoformat()
    assert labels.make_scope(labels.SCOPE_REGULAR, cutoff)["label"] == "2026 regular season through Sep 26"


@pytest.fixture
def isolated_calendar(monkeypatch, tmp_path):
    reference = tmp_path / REFERENCE.name
    reference.write_bytes(REFERENCE.read_bytes())
    source = reference.with_suffix(".source.json")
    source.write_bytes(REFERENCE.with_suffix(".source.json").read_bytes())
    monkeypatch.setattr(season_calendar, "REFERENCE_DIR", tmp_path)
    season_calendar._calendar.cache_clear()
    yield reference, source
    season_calendar._calendar.cache_clear()


def test_control_calendar_dates_come_from_the_reference_not_a_code_constant(isolated_calendar):
    reference, source = isolated_calendar
    data = json.loads(reference.read_bytes())
    data["seasons"][0]["regularSeasonEndDate"] = "2026-09-26"
    raw = json.dumps(data).encode()
    reference.write_bytes(raw)
    metadata = json.loads(source.read_bytes())
    metadata["sha256"] = hashlib.sha256(raw).hexdigest()
    source.write_text(json.dumps(metadata), encoding="utf-8")
    assert labels.make_scope(labels.SCOPE_REGULAR, "2026-09-26")["label"] == "2026 regular season"


def test_control_corrupt_reference_fails_closed_instead_of_guessing_a_date(isolated_calendar):
    reference, _ = isolated_calendar
    reference.write_bytes(reference.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum mismatch"):
        labels.make_scope(labels.SCOPE_REGULAR, "2026-10-22")
