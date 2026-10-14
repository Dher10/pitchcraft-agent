"""The registry of claims covers the catalog and says what the contract says (P0.15-D3.2, rule 4).

`data_pipeline/claims_registry.py` is the machine form of sections 3.1, 3.2 and 3.5 of
`docs/DATA_CONTRACT.md`: every key of the catalogs either has a condition on the payload or is listed as
asserting nothing. These tests fail if a key is added to a catalog and to neither list, if a pattern
matches no key, or if the code and the document drift apart.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
import re

import pytest

from agents.messages_en import EN_MESSAGES
from data_pipeline import claims_registry as registry
from data_pipeline.generator_texts import GENERATOR_MESSAGES

CONTRACT = Path(__file__).resolve().parents[1] / "docs" / "DATA_CONTRACT.md"
CATALOG_KEYS = sorted({*EN_MESSAGES, *GENERATOR_MESSAGES})
PSEUDO_KEYS = {"@join", "@capitalize"}


def section(heading: str) -> str:
    """The text of a `### ` section of the contract, up to the next heading."""

    text = CONTRACT.read_text(encoding="utf-8")
    start = text.index(f"### {heading}")
    nxt = re.search(r"^#{2,3} ", text[start + 4 :], re.MULTILINE)
    return text[start : start + 4 + nxt.start()] if nxt else text[start:]


def expand(cell: str) -> list[str]:
    """The keys named in the first cell of a table row: `.suffix` replaces the last segment of the key before."""

    keys: list[str] = []
    for token in re.findall(r"`([^`]+)`", cell):
        if token.startswith(".") and keys:
            token = keys[-1].rsplit(".", 1)[0] + token
        keys.append(token)
    return keys


def table_keys(*headings: str) -> set[str]:
    found: set[str] = set()
    for heading in headings:
        for line in section(heading).splitlines():
            if line.startswith("| `"):
                found.update(expand(line.split("|")[1]))
    return found


def matches(pattern: str, key: str) -> bool:
    return fnmatchcase(key, pattern)


def specificity(pattern: str) -> int:
    return len(pattern.rstrip("*")) + (1000 if "*" not in pattern else 0)


# --- the catalogs are covered --------------------------------------------------------------------


@pytest.mark.parametrize("key", CATALOG_KEYS)
def test_every_catalog_key_is_registered_or_asserts_nothing(key):
    kind, pattern = registry.classify(key)

    assert kind in ("rule", "nothing"), f"{key} is neither in the registry nor in the list of keys that assert nothing"
    assert matches(pattern, key)


@pytest.mark.parametrize("key", CATALOG_KEYS)
def test_the_most_specific_entry_of_a_key_is_unique(key):
    patterns = [(p, "rule") for p in registry.RULES if matches(p, key)]
    patterns += [(p, "nothing") for p in registry.ASSERTS_NOTHING if matches(p, key)]
    best = max(specificity(p) for p, _ in patterns)

    assert [kind for p, kind in patterns if specificity(p) == best] and len({p for p, _ in patterns if specificity(p) == best}) == 1


def test_a_key_that_is_in_no_list_is_not_classified():
    assert registry.classify("analyst.never.written") == (None, None)


def test_no_entry_matches_no_key():
    entries = [*registry.RULES, *registry.ASSERTS_NOTHING]
    unused = [p for p in entries if p not in PSEUDO_KEYS and not any(matches(p, key) for key in CATALOG_KEYS)]

    assert unused == []


def test_a_pseudo_key_asserts_nothing():
    for key in PSEUDO_KEYS:
        assert registry.classify(key)[0] == "nothing"


# --- the registry and the document say the same --------------------------------------------------


def test_the_registered_keys_are_the_rows_of_sections_3_1_and_3_2_of_the_contract():
    assert set(registry.RULES) == table_keys("3.1", "3.2")


def test_the_keys_that_assert_nothing_are_the_ones_listed_in_section_3_5_of_the_contract():
    listed = set(re.findall(r"`([^`]+)`", section("3.5")))

    assert set(registry.ASSERTS_NOTHING) == listed


def test_the_table_parser_expands_a_suffix_after_the_key_before_it():
    assert expand("`analyst.style.pair` / `.single`") == ["analyst.style.pair", "analyst.style.single"]
    assert expand("`critic.pitch.claim` + `.supported_primary` / `.low`") == [
        "critic.pitch.claim",
        "critic.pitch.supported_primary",
        "critic.pitch.low",
    ]


def test_every_rule_is_a_function_of_the_context():
    for pattern, rule in registry.RULES.items():
        assert callable(rule), pattern


# --- every rule runs ----------------------------------------------------------------------------


def test_every_rule_the_corpus_reaches_reports_when_its_condition_is_false(monkeypatch):
    """A rule that never reports (it reads nothing, or it was wired to the wrong key) cannot catch anything."""

    from data_pipeline.claims import catalogs_of
    from tests.corpus import KINDS, build, golden_payload, published

    never_reports: set[str] = set()
    reached: set[str] = set()
    for source in (*(("kind", k) for k in KINDS), ("golden", "live_healthy"), ("golden", "demo_final")):
        payload = published(build(monkeypatch, source[1]) if source[0] == "kind" else golden_payload(monkeypatch, source[1]))
        catalogs = catalogs_of(payload)
        lists = [(None, payload["claims"])] + [(m, m["report"]["claims"]) for m in payload["matchups"]]
        for matchup, claims in lists:
            index = registry.ClaimIndex(claims, catalogs)
            for claim in claims:
                kind, pattern = registry.classify(claim["key"])
                if kind != "rule" or pattern in reached:
                    continue
                ctx = registry.Ctx(payload, matchup, claim, index, {})
                monkeypatch.setattr(registry.Ctx, "require", lambda self, condition, reason, message: self.fail(reason, message) or False)
                fails = registry.run_rule(claim["key"], ctx)
                monkeypatch.undo()
                reached.add(pattern)
                if not fails:
                    never_reports.add(pattern)

    assert len(reached) > 40  # the corpus reaches most of the registry
    assert sorted(never_reports) == []
