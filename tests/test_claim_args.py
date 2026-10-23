"""Every argument of a claim is a payload value or a reference to another claim (P0.15-D3.2, rule 4).

`args` of a claim may not hold a piece of text cut out of another sentence: `writer.watch_whether`
used to keep "land the slider early in counts", a slice of the first "Three Things to Watch" bullet,
so the claim could not say where its text came from. A string argument passes only if

- it is a reference (`{"claim": id}`), or
- it is the separator of an `@join` or the empty text (a qualifier that is not written), or
- it equals a value of the payload outside the sentences, in one of the forms listed in
  `ACCEPTED_FORMS` (each form, and its reason, is written in `docs/DATA_CONTRACT.md`, rule 4).

The payloads are the corpus of the contract tests: four generator payloads, the eighteen golden
scenarios and the served file.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

from data_pipeline.claims import MATCHUP_TEXT_PATHS, ROOT_TEXT_PATHS, text_leaves
from tests.corpus import GOLDEN_NAMES, KINDS, build, golden_payload, published, served

FASTBALL = re.compile(r"(?i) fastball$")

# name -> (how a payload value is turned into the form an argument may have, why the form is accepted)
ACCEPTED_FORMS: dict[str, Any] = {
    "as is": lambda value: value,
    "lower case": lambda value: value.lower(),
    "first letter lower case": lambda value: value[:1].lower() + value[1:],
    "without fastball": lambda value: FASTBALL.sub("", value).lower(),
}


def _walk(node: Any, prefix: str, skip: set[str], strings: set[str], numbers: set[str]) -> None:
    if isinstance(node, dict):
        for key, child in node.items():
            if key == "claims":
                continue
            _walk(child, f"{prefix}.{key}" if prefix else str(key), skip, strings, numbers)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            _walk(child, f"{prefix}[{index}]", skip, strings, numbers)
    elif isinstance(node, str):
        if prefix not in skip:
            strings.add(node)
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        numbers.update({str(node), f"{node:g}"})


def payload_values(payload: dict[str, Any]) -> tuple[set[str], set[str]]:
    """(strings, numbers written as text) of the payload outside its sentences and its claims."""

    strings: set[str] = set()
    numbers: set[str] = set()
    root_text = {location for location, _ in text_leaves(payload, ROOT_TEXT_PATHS)}
    for key, child in payload.items():
        if key not in ("claims", "matchups"):
            _walk(child, key, root_text, strings, numbers)
    for matchup in payload.get("matchups", []):
        skip = {location for location, _ in text_leaves(matchup, MATCHUP_TEXT_PATHS)}
        _walk(matchup, "", skip, strings, numbers)
    return strings, numbers


def _allowed(payload: dict[str, Any]) -> set[str]:
    strings, numbers = payload_values(payload)
    return numbers | {form(value) for value in strings for form in ACCEPTED_FORMS.values()}


def _claim_lists(payload: dict[str, Any]):
    yield "claims", payload.get("claims", [])
    for index, matchup in enumerate(payload.get("matchups", [])):
        yield f"matchups[{index}].report.claims", (matchup.get("report") or {}).get("claims", [])


def _strings(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


def unmatched_args(payload: dict[str, Any]) -> list[str]:
    """Where a claim has a text argument that is neither a payload value nor a reference."""

    allowed = _allowed(payload)
    found: list[str] = []
    for where, claims in _claim_lists(payload):
        for claim in claims:
            for name, value in claim["args"].items():
                if claim["key"] == "@join" and name == "sep":
                    continue
                for text in _strings(value):
                    if text != "" and text not in allowed:
                        found.append(f"{where} {claim['id']} {claim['key']} {name}={text[:60]!r}")
    return found


# --- over the corpus -----------------------------------------------------------------------------


@pytest.mark.parametrize("kind", KINDS)
def test_no_argument_of_a_generated_payload_is_a_piece_of_a_sentence(monkeypatch, kind):
    payload = published(build(monkeypatch, kind))

    assert unmatched_args(payload) == []


@pytest.mark.parametrize("name", GOLDEN_NAMES)
def test_no_argument_of_a_golden_scenario_is_a_piece_of_a_sentence(monkeypatch, name):
    payload = published(golden_payload(monkeypatch, name))

    assert unmatched_args(payload) == []


def test_no_argument_of_the_served_file_is_a_piece_of_a_sentence():
    assert unmatched_args(served()) == []


# --- the check itself ----------------------------------------------------------------------------


def _payload(*claims: dict[str, Any], **starter: Any) -> dict[str, Any]:
    return {
        "metadata": {"data_mode": "demo_cached"},
        "claims": [],
        "matchups": [
            {
                "id": "m1",
                "starters": {"away_starter": {"name": "Alpha Livearm", "pitching_profile": starter}},
                "report": {"claims": list(claims)},
            }
        ],
    }


def _claim(key: str, **args: Any) -> dict[str, Any]:
    return {"id": "c1", "key": key, "args": args, "subject": None, "location": None}


@pytest.mark.parametrize(
    "leaf, argument",
    [
        ("Alpha Livearm", "Alpha Livearm"),  # as is: a name, a label, a pitch
        ("Solid command", "solid command"),  # lower case: a label in the middle of a sentence
        ("Solid command", "Solid command"),
        ("Above-average swing-and-miss ability", "above-average swing-and-miss ability"),  # first letter lower
        ("Four-seam Fastball", "four-seam"),  # without fastball: the short name of a pitch
        ("Slider", "slider"),
    ],
)
def test_the_accepted_forms_of_a_payload_value(leaf, argument):
    payload = _payload(_claim("analyst.read.shows", label=argument), primary_pitch=leaf)

    assert unmatched_args(payload) == []


def test_a_number_written_as_text_matches_the_number_of_the_payload():
    payload = _payload(_claim("critic.pitch.supported_primary", usage="71.4"), overall=71.4, whole=12.0)

    assert unmatched_args(payload) == []
    assert unmatched_args(_payload(_claim("critic.pitch.supported_primary", usage="12"), whole=12.0)) == []
    assert unmatched_args(_payload(_claim("critic.pitch.supported_primary", usage="71.5"), overall=71.4)) != []


def test_a_piece_cut_out_of_a_sentence_is_found():
    payload = _payload(_claim("writer.watch_whether", name="Alpha Livearm", action="land the slider early in counts"))
    payload["matchups"][0]["report"]["sections"] = [{"title": "Watch", "bullets": ["Can Alpha Livearm land the slider early in counts?"]}]

    assert unmatched_args(payload) == [
        "matchups[0].report.claims c1 writer.watch_whether action='land the slider early in counts'"
    ]


def test_a_text_that_is_only_in_a_sentence_is_not_a_payload_value():
    payload = _payload(_claim("writer.watch_line", observation="whether Alpha Livearm can land it"))
    payload["matchups"][0]["report"]["headline"] = "The early what to watch is whether Alpha Livearm can land it."

    assert unmatched_args(payload) != []


def test_a_reference_the_separator_of_a_join_and_the_empty_text_pass():
    payload = _payload(
        _claim("writer.watch_whether", name="Alpha Livearm", action={"claim": "c2"}),
        {"id": "c3", "key": "@join", "args": {"sep": "; ", "parts": [{"claim": "c2"}, ""]}, "subject": None, "location": None},
    )

    assert unmatched_args(payload) == []
