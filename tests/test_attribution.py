"""P1.9: the notes at the foot of the page say where the data comes from and that PitchCraft is free (D16, docs/plans/P1.md section 10).

D16 asks for visible attribution to MLB and Baseball Savant, no monetization of any kind, cached fetches and no bulk
downloads. A live file's notes are a closed set (`config.LIVE_DISCLAIMERS`, checked by the manifest); a demo file keeps its
own. The wording is the owner's (section 10), read against MLB's notice ("individual, non-commercial, non-bulk use",
`http://gdx.mlb.com/components/copyright.txt`, read on 2026-10-23).

One of the live notes says requests are cached, which is not the "cached demo" wording rule 6 forbids over live data
(F3): rule 6 exempts that exact sentence and nothing else.
"""

from __future__ import annotations

from copy import deepcopy
import re

import pytest

from data_pipeline import config, demo_inputs
from data_pipeline.contract_checks import check_contract
from tests.corpus import build, published

ATTRIBUTION = "Data from the MLB Stats API and Baseball Savant (Statcast). Not affiliated with MLB."
NON_COMMERCIAL = "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features."
CACHING = "Requests to the data sources are cached and the data is not downloaded in bulk."
INFORMATION_ONLY = "For information only: no predictions and no betting advice."

DEMO_WORDS = re.compile(r"capstone|demo|judging", re.IGNORECASE)


def rule6(payload) -> set[str]:
    return {violation.code for violation in check_contract(payload) if violation.code.startswith("rule6:")}


# --- the texts -------------------------------------------------------------------------------------------------------


def test_the_live_notes_are_these_four_in_this_order():
    assert config.LIVE_DISCLAIMERS == (ATTRIBUTION, NON_COMMERCIAL, CACHING, INFORMATION_ONLY)


def test_the_named_constants_are_the_approved_sentences():
    assert config.NON_COMMERCIAL_NOTE == NON_COMMERCIAL and config.CACHING_NOTE == CACHING


def test_the_demo_notes_say_it_is_free_and_non_commercial_and_nothing_about_requests():
    notes = demo_inputs.build_demo_payload()["disclaimers"]

    assert NON_COMMERCIAL in notes and CACHING not in notes
    assert notes.count(NON_COMMERCIAL) == 1
    assert "PitchCraft is a capstone demo and not a betting or gambling tool." in notes  # the demo keeps its own notes


@pytest.mark.parametrize("kind", ["live_complete", "live_debuts", "live_errors"])
def test_a_live_file_carries_all_four_notes_and_no_demo_wording(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert payload["disclaimers"] == list(config.LIVE_DISCLAIMERS)
    assert not DEMO_WORDS.search(" ".join(payload["disclaimers"]))
    assert rule6(payload) == set()


@pytest.mark.parametrize("kind", ["demo", "fallback"])
def test_a_demo_or_fallback_file_says_it_is_non_commercial(monkeypatch, kind):
    assert NON_COMMERCIAL in published(build(monkeypatch, kind))["disclaimers"]


def test_no_note_promises_or_suggests_anything_about_money_except_that_there_is_none():
    for note in config.LIVE_DISCLAIMERS:
        assert not re.search(r"\b(buy|subscribe|premium|upgrade|affiliate|odds|bet on|wager)\b", note, re.IGNORECASE), note


# --- rule 6 and the exact exemption -------------------------------------------------------------------------------------


@pytest.fixture
def live(monkeypatch):
    return published(build(monkeypatch, "live_complete"))


def test_the_caching_note_is_not_cached_wording_over_live_data(live):
    assert CACHING in live["disclaimers"] and "rule6:cached_wording" not in rule6(live)


@pytest.mark.parametrize(
    "text",
    [
        "Cached demo data may be used to ensure stable public evaluation.",
        "Cached demo snapshots (always available)",
        CACHING + " Cached demo data may be used.",
        "Requests to the data sources are cached and the data is cached demo data.",
        CACHING.replace("Requests", "Some requests"),
        CACHING.lower(),
        CACHING + " ",
        "This report is based on cached data.",
    ],
)
def test_any_other_cached_wording_in_the_notes_is_still_a_finding(live, text):
    edited = deepcopy(live)
    edited["disclaimers"].append(text)

    assert "rule6:cached_wording" in rule6(edited)


def test_the_exemption_does_not_reach_the_sources(live):
    edited = deepcopy(live)
    edited["metadata"]["data_sources"].append(CACHING)

    assert "rule6:cached_wording" in rule6(edited)


def test_a_note_outside_the_closed_set_is_a_finding_of_the_manifest(live):
    edited = deepcopy(live)
    edited["disclaimers"].append("Premium reports are coming soon.")

    assert any(v.code.startswith("rule1:wrong_type") and "disclaimers" in v.code for v in check_contract(edited))
