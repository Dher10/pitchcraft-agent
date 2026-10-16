"""The table of violations the code has today matches the corpus exactly (P0.15-D3.2, D3.3b).

`known_violations.KNOWN_VIOLATIONS` maps a violation code to the findings (F numbers) of
`docs/DATA_CONTRACT.md` it belongs to. `validate_payload` tolerates exactly those codes, so the generator
keeps publishing as it does today while the fixes land one class at a time (P0.15-D2.1 to D2.5). The table
must match in both directions on the payloads of the tests (the corpus, the 72 cases of the matrix and the
hard cases of `tests/matrix.py`): a violation that is not in it is a new
violation and fails publication; an entry that no longer occurs must be deleted. The last fix deletes
the module (the guard test of that commit makes sure nothing replaces it).
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

import pytest

from data_pipeline.contract_checks import check_contract
from data_pipeline.known_violations import KNOWN_VIOLATIONS
from tests.corpus import GOLDEN_NAMES, KINDS, build, golden_payload, published, served
from tests.live_helpers import failed_checks
from tests.matrix import outcomes

CONTRACT = Path(__file__).resolve().parents[1] / "docs" / "DATA_CONTRACT.md"


def corpus(monkeypatch):
    """(name, payload) of every payload the contract tests run over."""

    for kind in KINDS:
        yield kind, published(build(monkeypatch, kind))
    for name in GOLDEN_NAMES:
        yield f"golden:{name}", published(golden_payload(monkeypatch, name))
    yield "served", served()


@pytest.fixture(scope="module")
def observed():
    """code -> the payloads that have it."""

    found: dict[str, set[str]] = {}
    with pytest.MonkeyPatch.context() as monkeypatch:
        for name, payload in corpus(monkeypatch):
            for violation in check_contract(payload):
                found.setdefault(violation.code, set()).add(name)
    for name, outcome in outcomes().items():
        for violation in outcome.violations:
            found.setdefault(violation.code, set()).add(name)
    return found


def test_a_violation_that_is_not_in_the_table_is_new(observed):
    assert sorted(set(observed) - set(KNOWN_VIOLATIONS)) == []


def test_an_entry_that_no_longer_occurs_is_deleted(observed):
    assert sorted(set(KNOWN_VIOLATIONS) - set(observed)) == []


def test_every_entry_names_findings_the_contract_lists():
    section4 = CONTRACT.read_text(encoding="utf-8").split("## 4. Known violations")[1].split("## 5.")[0]
    listed = set(re.findall(r"^\| (F\d+)", section4, re.MULTILINE))
    for code, findings in KNOWN_VIOLATIONS.items():
        assert findings and all(re.fullmatch(r"F\d+", f) for f in findings), code
        assert set(findings) <= listed, (code, findings)


def test_the_table_is_ordered_by_code_so_a_diff_shows_what_changed():
    assert list(KNOWN_VIOLATIONS) == sorted(KNOWN_VIOLATIONS)


# --- what validate_payload does with them ---------------------------------------------------------


def test_every_payload_of_the_generator_still_validates_with_its_known_violations(monkeypatch):
    for kind in KINDS:
        assert failed_checks(build(monkeypatch, kind)) == [], kind


def test_a_new_violation_fails_publication(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    payload["matchups"][0]["starters"]["away_starter"]["sample"]["rates"]["home_runs"] += 1  # the claim says the old count

    failed = failed_checks(payload)

    assert any(description.startswith("contract: rule4:analyst.data.contact#count") for description in failed), failed


def test_a_violation_is_tolerated_only_when_it_is_in_the_table(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    assert failed_checks(payload) == []

    monkeypatch.delitem(KNOWN_VIOLATIONS, "rule4:writer.confidence.lineups#game_state")
    # `validate_payload` reads the table when it runs, so the same payload now fails on that code
    failed = failed_checks(payload)

    assert any("rule4:writer.confidence.lineups#game_state" in description for description in failed), failed


def test_the_known_violations_that_were_tolerated_are_recorded_as_a_passing_check(monkeypatch):
    from data_pipeline.validators import validate_payload

    checks = validate_payload(build(monkeypatch, "live_debuts"))
    tolerated = [c for c in checks if c.description.startswith("contract:") and c.passed]

    assert len(tolerated) == 1
    assert "known" in tolerated[0].description


def test_a_payload_the_checks_cannot_read_fails_instead_of_passing(monkeypatch):
    payload = deepcopy(build(monkeypatch, "demo"))
    payload["metadata"] = "not an object"

    assert any("contract" in description or "metadata" in description for description in failed_checks(payload))
