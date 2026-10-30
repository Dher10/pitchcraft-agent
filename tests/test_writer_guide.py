"""P2.2: the approved writer guide is pinned by its digest, so a prompt can name exactly the guide it was written with."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "writer-guide.md"
LOCK = ROOT / "evals" / "data" / "writer" / "guide.lock"


def guide_text() -> str:
    return GUIDE.read_bytes().decode("utf-8").replace("\r\n", "\n")


def guide_digest() -> str:
    return hashlib.sha256(guide_text().encode("utf-8")).hexdigest()


def test_the_guide_digest_equals_its_lock():
    assert LOCK.read_text(encoding="utf-8").strip() == guide_digest()


def test_the_guide_is_the_approved_version_and_no_longer_a_draft():
    first = guide_text().splitlines()[0]

    assert "version 0.2" in first and "approved" in first
    assert "DRAFT" not in guide_text()


def test_the_rules_are_w1_to_w17_once_each_in_order():
    ids = re.findall(r"^\| (W\d+) \|", guide_text(), flags=re.M)

    assert ids == [f"W{n}" for n in range(1, 18)]


def test_the_guide_states_the_owner_decisions_that_change_what_the_writer_may_say():
    text = guide_text()

    assert "strictly, with no exemptions" in text
    assert "Watch how" in text and "Watch whether" in text
    assert "within 20% above or below" in text
    assert "same scope" in text


GLOSSARY = ROOT / "evals" / "data" / "dataset" / "glossary.json"
GLOSSARY_LOCK = ROOT / "evals" / "data" / "dataset" / "glossary.lock"


def table_rows() -> list[tuple[str, str]]:
    section = guide_text().split("## 5. Glossary")[1].split("## 6.")[0]
    rows = re.findall(r"^\| (.+?) \| (.+?) \|$", section, flags=re.M)
    return [r for r in rows if r[0] != "Term" and not set(r[0]) <= set("-")]


def test_the_glossary_file_says_what_the_guide_table_says():
    import json

    terms = json.loads(GLOSSARY.read_text(encoding="utf-8"))["terms"]

    assert [(t["term"], t["definition"]) for t in terms] == table_rows()
    assert len(terms) == 13


def test_the_glossary_digest_equals_its_lock():
    assert GLOSSARY_LOCK.read_text(encoding="utf-8").strip() == hashlib.sha256(GLOSSARY.read_bytes()).hexdigest()


def test_the_owner_wording_of_the_changed_definitions():
    rows = dict(table_rows())

    assert rows["put-away pitch"] == "In this report, the pitch he uses second most (at least 15% of his pitches)."
    assert rows["swing-and-miss"] == "How often hitters swing and miss against him."
    assert rows["command"] == "How well a pitcher puts the ball where he wants it."
