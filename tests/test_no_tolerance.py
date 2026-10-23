"""Nothing tolerates a violation of the data contract any more (P0.15-D2.5c, the end of the temporary table).

From P0.15-D3.2 to D2.5 `data_pipeline/known_violations.py` listed the violations the code still had, and
`validate_payload` let exactly those through while the fixes landed one class at a time. The last fix deletes both. This
guard fails if a mechanism of tolerance comes back: the module, a table of violation codes, an import of it, an `xfail` or
a skip for a finding of the contract, or a `validate_payload` that lets a violation through.
"""

from __future__ import annotations

import ast
import importlib
import json
from pathlib import Path
import re

import pytest

from tests.corpus import build, published
from tests.live_helpers import failed_checks

ROOT = Path(__file__).resolve().parents[1]
THIS = Path(__file__).resolve()


def sources(*folders: str):
    for folder in folders:
        for path in sorted((ROOT / folder).rglob("*.py")):
            if "__pycache__" not in path.parts and path.resolve() != THIS:
                yield path


def test_the_module_of_the_table_does_not_exist():
    assert not (ROOT / "data_pipeline" / "known_violations.py").exists()
    with pytest.raises(ImportError):
        importlib.import_module("data_pipeline.known_violations")


def test_no_source_names_the_table():
    found = [
        str(path.relative_to(ROOT))
        for path in sources("data_pipeline", "agents", "tests", "scripts", ".claude/hooks")
        if re.search(r"known_violations|KNOWN_VIOLATIONS", path.read_text(encoding="utf-8"))
    ]

    assert found == []


def test_no_test_is_an_xfail_and_none_is_skipped_for_a_finding_of_the_contract():
    offenders = []
    for path in sources("tests"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            name = node.attr if isinstance(node, ast.Attribute) else node.id if isinstance(node, ast.Name) else None
            if name == "xfail":
                offenders.append(f"{path.name}:{node.lineno} xfail")
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in ("skip", "skipif"):
                text = " ".join(ast.unparse(arg) for arg in [*node.args, *(k.value for k in node.keywords)])
                if re.search(r"\bF\d{1,2}\b", text):
                    offenders.append(f"{path.name}:{node.lineno} skip for a finding")

    assert offenders == []


def test_the_publication_check_has_no_allowance_for_a_violation():
    source = (ROOT / "data_pipeline" / "validators.py").read_text(encoding="utf-8")

    assert not re.search(r"tolerat|known violation|except the known", source, re.IGNORECASE)


def test_a_payload_with_one_violation_stops_publication(monkeypatch):
    payload = build(monkeypatch, "live_complete")
    assert failed_checks(payload) == []  # control: the generated file has none
    payload["matchups"][0]["status"] = "live"  # a game in progress with the sentence "before first pitch": rule 4

    failed = failed_checks(payload)

    assert any(d.startswith("contract: rule4:writer.confidence.lineups#game_state") for d in failed), failed


def test_the_passing_check_says_the_rules_hold_without_an_exception(monkeypatch):
    from data_pipeline.validators import validate_payload

    descriptions = [c.description for c in validate_payload(build(monkeypatch, "live_complete")) if c.description.startswith("contract:")]

    assert descriptions == ["contract: rules 3, 4, 6 and 8 hold"]


def test_every_published_payload_of_the_generator_has_no_violation_at_all(monkeypatch):
    from data_pipeline.contract_checks import check_contract

    for kind in ("demo", "fallback", "live_complete", "live_debuts", "live_errors"):
        assert [v.code for v in check_contract(published(build(monkeypatch, kind)))] == [], kind
        assert failed_checks(build(monkeypatch, kind)) == [], kind
    served = json.loads((ROOT / "public" / "data" / "pitchcraft-demo.json").read_text(encoding="utf-8"))
    assert [v.code for v in check_contract(served)] == []


def test_a_claim_whose_figure_is_not_the_payloads_stops_publication(monkeypatch):
    """Kept from the table's own test: a sentence that says a count the data does not have is not published."""

    payload = build(monkeypatch, "live_complete")
    payload["matchups"][0]["starters"]["away_starter"]["sample"]["rates"]["home_runs"] += 1  # the claim says the old count

    failed = failed_checks(payload)

    assert any(description.startswith("contract: rule4:analyst.data.contact#count") for description in failed), failed


@pytest.mark.parametrize(
    "edit, code",
    [
        (lambda p: p["metadata"].update(data_fetched_at=None), "contract: rule6:data_fetched_at"),
        (lambda p: p["metadata"]["data_status"].update(reason="a free sentence"), "contract: rule8:reason"),
        (lambda p: p["matchups"][0]["game"].update(weather="sunny"), "contract: rule1:unlisted#matchups[].game.weather"),
    ],
    ids=["rule 6", "rule 8", "rule 1"],
)
def test_a_violation_of_any_other_rule_stops_publication_too(monkeypatch, edit, code):
    """The first guard test uses one code; a tolerance under another name would let these through."""

    payload = build(monkeypatch, "live_complete")
    assert failed_checks(payload) == []  # control
    edit(payload)

    assert any(d.startswith(code) for d in failed_checks(payload)), failed_checks(payload)
