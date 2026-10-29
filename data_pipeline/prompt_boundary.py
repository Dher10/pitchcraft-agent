"""Closed internal projection. This does not extend the publication schema.

Provider adapters must use prepare_request, not accept caller-supplied facts.
The lower-level document validator checks shape/encoding, not factual truth.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

from agents.security_policy import FACT_CAP, ModelRejected, bounded_text, validate_sentence
from data_pipeline.claims import catalogs_of
from data_pipeline.claims_registry import ClaimIndex
from data_pipeline import labels, series
from data_pipeline.validators import validate_payload

FACT_KEYS = frozenset((
    "analyst.read.combination", "analyst.read.mainly", "analyst.read.shows",
    "analyst.data.arsenal", "analyst.data.arsenal_unnamed", "analyst.data.strikeout",
    "analyst.data.control", "analyst.data.contact", "analyst.data.no_home_runs",
    "analyst.offense.unavailable", "analyst.offense.unavailable_no_hand",
    "analyst.offense.strong", "analyst.offense.average", "analyst.offense.weak",
    "analyst.scope.differ", "analyst.scope.groups", "analyst.scope.none",
    "analyst.scope.same", "analyst.scope.offense", "analyst.series.standing", "analyst.series.opening",
))
_INSTRUCTION_DATA = json.loads((Path(__file__).resolve().parents[1] / "agents/security_instructions.json").read_text(encoding="utf-8"))
INSTRUCTIONS = _INSTRUCTION_DATA["en"]


@dataclass(frozen=True)
class Field:
    kind: str
    choices: tuple = ()
    nullable: bool = False


@dataclass(frozen=True)
class Items:
    child: Any
    maximum: int


SCOPE = {"kind": Field("enum", (labels.SCOPE_REGULAR, labels.SCOPE_REGULAR_POSTSEASON)),
         "through": Field("date"), "label": Field("text")}
SAMPLE = {
    "arsenal": {"pitches": Field("count", nullable=True), "scope": SCOPE},
    "rates": {**{key: Field("count", nullable=True) for key in ("batters_faced", "strikeouts", "walks", "home_runs")},
              "source": Field("enum", ("mlb_api", "statcast", "unavailable")), "scope": SCOPE},
    "limited": {key: Field("bool") for key in ("arsenal", "strikeout", "control")},
}
STARTER = {"name": Field("name"), "team": Field("abbreviation", nullable=True),
           "throws": Field("enum", ("L", "R", "S")), "sample": SAMPLE}
SERIES = {"series_name": Field("text"), "standing": Field("text", nullable=True),
          "game_number": Field("series_count"), "games_in_series": Field("series_count", nullable=True)}
SCHEMA = {
    "language": Field("enum", ("en",)), "date": Field("date"),
    "status": Field("enum", ("upcoming", "live", "final"), nullable=True),
    "venue": Field("name", nullable=True), "series": SERIES,
    "starters": {slot: STARTER for slot in ("away_starter", "home_starter")},
    "teams": {slot: {"name": Field("name"), "abbreviation": Field("abbreviation", nullable=True)} for slot in ("away", "home")},
    "facts": Items({"key": Field("enum", tuple(sorted(FACT_KEYS))),
                    "subject": Field("enum", ("away_starter", "home_starter"), nullable=True), "text": Field("fact")}, 100),
    "candidates": Items(Field("candidate"), 100),
}
_NULL_OBJECTS = {"series"} | {f"starters.{slot}.sample.{group}.scope" for slot in ("away_starter", "home_starter") for group in ("arsenal", "rates")}


def _walk(node, spec, path=""):
    if isinstance(spec, dict):
        if node is None and path in _NULL_OBJECTS:
            return
        if type(node) is not dict or set(node) != set(spec):
            raise ModelRejected()
        for key, child in spec.items():
            yield from _walk(node[key], child, f"{path}.{key}" if path else key)
    elif isinstance(spec, Items):
        if type(node) is not list or len(node) > spec.maximum:
            raise ModelRejected()
        for item in node:
            yield from _walk(item, spec.child, path + "[]")
    else:
        yield path, node, spec


def _inventory(spec, path=""):
    if isinstance(spec, dict):
        return [p for key, child in spec.items() for p in _inventory(child, f"{path}.{key}" if path else key)]
    if isinstance(spec, Items):
        return _inventory(spec.child, path + "[]")
    return [path] if spec.kind not in ("count", "series_count", "bool") else []


TEXT_FIELDS = tuple(_inventory(SCHEMA))


def text_field_paths(document):
    return [path for path, value, _ in _walk(document, SCHEMA) if isinstance(value, str)]


def text_locations(document):
    def walk(node, spec, path=""):
        if isinstance(spec, dict) and isinstance(node, dict):
            for key, child in spec.items():
                child_path = f"{path}.{key}" if path else key
                if isinstance(child, Field) and isinstance(node[key], str):
                    yield child_path, node, key
                else:
                    yield from walk(node[key], child, child_path)
        elif isinstance(spec, Items):
            for index, value in enumerate(node):
                if isinstance(spec.child, Field) and isinstance(value, str):
                    yield path + "[]", node, index
                else:
                    yield from walk(value, spec.child, path + "[]")
    return list(walk(document, SCHEMA))


def validate_document(document):
    for _, value, spec in _walk(document, SCHEMA):
        if value is None and spec.nullable:
            continue
        if spec.kind in ("count", "series_count"):
            maximum = 7 if spec.kind == "series_count" else 1_000_000
            minimum = 1 if spec.kind == "series_count" else 0
            if type(value) is not int or not minimum <= value <= maximum:
                raise ModelRejected()
        elif spec.kind == "bool":
            if type(value) is not bool:
                raise ModelRejected()
        else:
            if spec.kind == "enum":
                if type(value) is not str or value not in spec.choices:
                    raise ModelRejected()
                continue
            bounded_text(value, FACT_CAP if spec.kind == "fact" else 300)
            if spec.kind == "date":
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ModelRejected()
                except ValueError:
                    raise ModelRejected() from None
            if spec.kind == "abbreviation" and re.fullmatch(r"[A-Z]{2,4}", value) is None:
                raise ModelRejected()
            if spec.kind == "name" and (len(value) > 100 or not any(c.isalpha() for c in value) or any(
                not (unicodedata.category(c)[0] in "LM" or c in " '-.\u2019") for c in value
            )):
                raise ModelRejected()
    for starter in document["starters"].values():
        for group in ("arsenal", "rates"):
            scope = starter["sample"][group]["scope"]
            if scope is not None and scope != labels.make_scope(scope["kind"], scope["through"]):
                raise ModelRejected()
    value = document["series"]
    if value is not None:
        if series.series_name(value["series_name"]) is None or value["games_in_series"] not in (None, 3, 5, 7):
            raise ModelRejected()
        if value["standing"] is not None and series.standing(value["standing"], value["game_number"], value["games_in_series"]) is None:
            raise ModelRejected()
        if value["game_number"] > (value["games_in_series"] or 7):
            raise ModelRejected()
    return document


def project_payload(payload, matchup_id, language="en"):
    # Validate truth/ownership/coverage before any catalog fragment is exposed.
    try:
        validate_payload(payload)
        if language != "en" or payload["metadata"]["language"] != language:
            raise ModelRejected()
        matchup = next(m for m in payload["matchups"] if m["id"] == matchup_id)
        index = ClaimIndex(matchup["report"]["claims"], catalogs_of(payload))
        facts = [{"key": c["key"], "subject": c["subject"], "text": index.text(c["id"])}
                 for c in matchup["report"]["claims"] if c["key"] in FACT_KEYS]
        doc = {"language": language, "date": matchup["date"], "status": matchup["status"],
               "venue": matchup["game"]["venue"], "series": deepcopy(matchup["series"]),
               "teams": {slot: {key: matchup["teams"][slot][key] for key in ("name", "abbreviation")} for slot in ("away", "home")},
               "starters": {}, "facts": facts, "candidates": []}
        for slot in ("away_starter", "home_starter"):
            starter = matchup["starters"][slot]
            sample = starter["sample"]
            doc["starters"][slot] = {key: starter[key] for key in ("name", "team", "throws")}
            doc["starters"][slot]["sample"] = {key: deepcopy(sample[key]) for key in ("arsenal", "rates", "limited")}
        if not facts:
            raise ModelRejected()
        return validate_document(doc)
    except Exception:
        # Validation errors can contain raw source text; never propagate them.
        raise ModelRejected() from None


def make_messages(document, *, purpose):
    if purpose not in INSTRUCTIONS:
        raise ModelRejected()
    validate_document(document)
    content = json.dumps({"untrusted_data": document}, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    if len(content) > 64_000:
        raise ModelRejected()
    return {"messages": [{"role": "system", "content": _INSTRUCTION_DATA[document["language"]][purpose]}, {"role": "user", "content": content}]}


def prepare_request(payload, matchup_id, *, purpose, candidates=(), language="en"):
    """Required provider entry point: fresh independently validated facts."""
    doc = project_payload(payload, matchup_id, language)
    doc["candidates"] = list(candidates)
    return make_messages(doc, purpose=purpose)
