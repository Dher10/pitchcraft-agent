"""P2.2: the writer-input projection. One function feeds A, B1 and B2; it removes what the writer must never see."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unicodedata

import pytest

from agents import writer_input as wi
from evals import build_packets as bp

DATASET = Path(__file__).resolve().parents[1] / "evals" / "data" / "dataset"
CASE = "veteran-824027"  # a dev case; the test split is never opened


@pytest.fixture(scope="module")
def parts():
    return bp.load_dev_packet(DATASET, CASE), bp.load_dev_findings(DATASET, CASE), wi.load_glossary(DATASET / "glossary.json")


def build(parts):
    packet, findings, glossary = parts
    return wi.build_writer_input(deepcopy(packet), deepcopy(findings), glossary)


def keys_anywhere(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from keys_anywhere(value)
    elif isinstance(node, list):
        for item in node:
            yield from keys_anywhere(item)


def test_the_fetch_note_and_the_internal_enums_are_removed_and_the_lineup_status_stays(parts):
    doc = build(parts)

    assert "notes" not in doc["data_confidence"]
    assert doc["data_confidence"] == {"lineup_status": "probable pitchers"}
    assert "fetched 2026" not in json.dumps(doc) and CASE not in json.dumps(doc)


def test_nothing_the_guide_forbids_reaches_the_writer(parts):
    names = set(keys_anywhere(build(parts)))

    assert not names & {"id", "bio", "recent_form", "record", "postgame", "pitch_locations", "availability", "is_featured", "start_time_utc", "notes", "away_team_id", "home_team_id"}


def test_the_figures_the_guide_names_are_present(parts):
    doc = build(parts)

    assert doc["starters"]["away_starter"]["pitching_profile"]["command_label"] == "Solid command"
    assert doc["starters"]["home_starter"]["sample"]["rates"]["batters_faced"] == 289
    assert doc["teams"]["away"]["offense_profile"]["ops_vs_hand"] == ".709"
    assert doc["pitch_movement"]["home_starter"]["Curveball"]["h_break"] == 12.5
    assert doc["series"] is None and doc["date"] == "2026-06-01"


def test_the_findings_reach_the_writer_as_labels_only_never_as_sentences(parts):
    findings = build(parts)["findings"]

    assert findings["away_starter_strengths"] == ["Solid command supports strike-zone control", "Four-seam to set up, Curveball to finish"]
    assert findings["lineup_notes"]["home"] == ["has elevated swing-and-miss risk", "draws walks at an above-average rate"]
    assert findings["lineup_notes"]["away"] == []
    text = json.dumps(findings)
    assert "needs efficient strikes" not in text and "far larger sample" not in text and "Can " not in text


def test_the_glossary_is_the_frozen_file_whole_and_in_order(parts):
    terms = json.loads((DATASET / "glossary.json").read_text(encoding="utf-8"))["terms"]

    assert build(parts)["glossary"] == {x["term"]: x["definition"] for x in terms}
    assert list(build(parts)["glossary"]) == [x["term"] for x in terms]


def test_names_are_nfc_even_when_the_source_is_not(parts):
    packet, findings, glossary = deepcopy(parts[0]), parts[1], parts[2]
    packet["starters"]["home_starter"]["name"] = unicodedata.normalize("NFD", "José Soriano")

    doc = wi.build_writer_input(packet, findings, glossary)

    name = doc["starters"]["home_starter"]["name"]
    assert name == unicodedata.normalize("NFC", name) == "José Soriano"


def test_the_projection_is_deterministic_and_does_not_mutate_its_inputs(parts):
    packet, findings, glossary = parts
    before = json.dumps([packet, findings], sort_keys=True)

    assert json.dumps(wi.build_writer_input(packet, findings, glossary), sort_keys=True) == json.dumps(build(parts), sort_keys=True)
    assert json.dumps([packet, findings], sort_keys=True) == before


def test_a_packet_without_a_starter_is_refused(parts):
    packet = deepcopy(parts[0])
    del packet["starters"]["home_starter"]

    with pytest.raises(wi.WriterInputError):
        wi.build_writer_input(packet, parts[1], parts[2])


def test_the_evidence_index_has_every_scalar_by_dotted_path_and_keeps_nulls(parts):
    index = wi.evidence_index(build(parts))

    assert index["starters.away_starter.pitching_profile.command_label"] == "Solid command"
    assert index["starters.home_starter.sample.rates.batters_faced"] == 289
    assert index["starters.home_starter.pitching_profile.contact_risk_label"] is None
    assert index["pitch_movement.home_starter.Curveball.v_break"] == -6.5
    assert index["glossary.OPS"].startswith("On-base plus slugging")
    assert any(path.startswith("pitch_mix.") for path in index)


def test_scope_is_found_for_figures_and_absent_for_the_rest(parts):
    doc = build(parts)
    label = "2026 regular season through May 31"

    assert wi.scope_label(doc, "starters.away_starter.season_summary.era") == label
    assert wi.scope_label(doc, "starters.away_starter.sample.rates.walks") == label
    assert wi.scope_label(doc, "teams.home.offense_profile.ops_vs_hand") == label
    assert wi.scope_label(doc, "pitch_movement.home_starter.Curveball.h_break") == label
    assert wi.scope_label(doc, "starters.away_starter.name") is None
    assert wi.scope_label(doc, "no.such.path") is None


def test_no_string_the_writer_receives_has_an_underscore_or_an_internal_enum(parts):
    strings = [v for v in wi.evidence_index(build(parts)).values() if isinstance(v, str)]

    assert strings and not [v for v in strings if "_" in v]
    assert "fetched" not in json.dumps(build(parts)) and "mlb_api" not in json.dumps(build(parts))
