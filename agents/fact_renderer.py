"""Verified fact sentences for the local NLI (docs/SECURITY.md, "Each generated sentence is checked against the packet's verified
catalog fact sentences, never raw JSON").

`render_fact(doc, path)` turns one value of the writer input into one plain English sentence that keeps its subject, measurement,
flag, scope and time. The wording lives in `agents/writer_lexicon.json` ("facts"), not here (D6). A path with no template renders
to None and a sentence that cites it cannot be checked: the NLI stage rejects it (fail closed). The renderer version is part of the
run identity of every NLI result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

from agents import writer_input as wi

FACT_RENDERER_VERSION = "p2.3-2"
_FACTS = json.loads((Path(__file__).with_name("writer_lexicon.json")).read_text(encoding="utf-8"))["en"]["facts"]
_SLOT = r"(?P<slot>away_starter|home_starter)"
_SIDE = r"(?P<side>away|home)"
_STAT_BASE = {"era_number": "era", "whip_number": "whip"}
_OFFENSE_BASE = {"ops_number": "ops_vs_hand", "k_rate_number": "k_rate_vs_hand", "bb_rate_number": "bb_rate_vs_hand"}


def _t(key: str, **fields: Any) -> str:
    """A template filled from the packet. An unknown (None) is never shown as a value: it makes the fact unrenderable."""

    if any(value is None for value in fields.values()):
        raise ValueError("unknown value")
    return _FACTS[key].format(**fields)


def renderer_identity() -> str:
    """Version plus a hash of the fact table and of this source: a calibration is bound to exactly this renderer."""

    digest = hashlib.sha256(json.dumps(_FACTS, sort_keys=True).encode("utf-8"))
    digest.update(Path(__file__).read_bytes())
    return f"{FACT_RENDERER_VERSION}:{digest.hexdigest()[:16]}"


def _hand(code: str | None) -> str:
    return _FACTS["hands"].get(str(code), str(code))


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:]


def _name(doc: dict, slot: str) -> str:
    return doc["starters"][slot]["name"]


def _team(doc: dict, side: str) -> str:
    return doc["teams"][side]["name"]


def _scope(doc: dict, path: str) -> str:
    return wi.scope_label(doc, path) or _FACTS["no_scope"]


def render_fact(doc: dict, path: str) -> str | None:
    """One fact sentence for `path`, or None when the path has no template."""

    index = wi.evidence_index(doc)
    if path not in index:
        return None
    value = index[path]
    parts = path.split(".")
    try:
        sentence = _dispatch(doc, index, path, parts, value)
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    return sentence if sentence is None or len(sentence) <= 300 else None


def _dispatch(doc: dict, index: dict, path: str, parts: list[str], value: Any) -> str | None:
    head = parts[0]
    if head == "starters":
        return _starter(doc, index, path, parts, value)
    if head == "teams":
        return _team_fact(doc, path, parts, value)
    if head == "pitch_mix":
        return _pitch_mix(doc, index, path, parts, value)
    if head == "pitch_movement":
        return _movement(doc, path, parts, value)
    if head == "velocity_by_pitch":
        if parts[2] == "pitch":
            return _t("mix_pitch", value=value)
        slot = parts[2].removesuffix("_velocity")
        pitch = doc["velocity_by_pitch"][int(parts[1])]["pitch"]
        return _t("velocity", name=_name(doc, slot), pitch=pitch, value=value) if value is not None else _t("velocity_null", name=_name(doc, slot), pitch=pitch)
    if head == "findings":
        return _findings(doc, parts, value)
    if head == "glossary" and parts[-1] == "short":
        term = ".".join(parts[1:-1])
        return _t("glossary_short", term=term, value=value) if value else None
    if head == "series":
        return _series(doc, parts, value)
    if path == "venue":
        return _t("venue", value=value) if value else None
    if path == "date":
        return _t("date", value=value)
    if path == "status":
        return _t("status_upcoming") if value == "upcoming" else _t("status_other", value=value)
    if path == "data_confidence.lineup_status":
        return _t("lineup_status", value=value)
    return None


def _starter(doc, index, path, parts, value):
    slot = parts[1]
    name, section = _name(doc, slot), parts[2]
    side = "away" if slot == "away_starter" else "home"
    if section == "name":
        return _t("starter", name=name, team=_team(doc, side), side=_FACTS["side_" + side])
    if section == "throws":
        return _t("throws", name=name, hand=_hand(value))
    if section == "season_summary":
        key = parts[3]
        if key == "scopes":
            return _t("scope", value=value) if parts[-1] == "label" else None
        base = _STAT_BASE.get(key, key)
        shown = index[".".join([*parts[:3], base])] if key in _STAT_BASE else value
        scope = _scope(doc, path)
        return _t("stat_" + base, name=name, value=shown, scope=scope)
    if section == "pitching_profile":
        key = parts[3]
        if key in ("command_label", "swing_miss_label", "contact_risk_label"):
            dim = key.removesuffix("_label")
            return _t("label_" + dim, name=name, label=_lower_first(value)) if value else _t("label_null_" + dim, name=name)
        if key == "primary_pitch":
            return _t("primary_pitch", name=name, value=value)
        if key == "putaway_pitch":
            return _t("putaway_pitch", name=name, value=value) if value else _t("putaway_null", name=name)
        if key == "style_label":
            return _t("style", name=name, value=value)
        return None
    if section == "sample":
        group, key = parts[3], parts[4]
        if key == "scope" or group == "rates" and key == "source":
            return _t("scope", value=value) if parts[-1] == "label" else None
        if group == "rates":
            return _t("rate_" + key, name=name, value=value, scope=_scope(doc, path)) if value is not None else _t("rate_null", name=name)
        if group == "arsenal" and key == "pitches":
            return _t("arsenal_pitches", name=name, value=value, scope=_scope(doc, path))
        if group == "limited":
            return _t("limited_true" if value else "limited_false", name=name, dim=_FACTS["dims"][key])
        if group == "thresholds":
            return _t("threshold", name=name, value=value, dim=_FACTS["dims"][key], unit=_FACTS["units"][key])
    return None


def _team_fact(doc, path, parts, value):
    side, section = parts[1], parts[2]
    team = _team(doc, side)
    if section == "name":
        return _t("team", team=team, side=_FACTS["side_" + side])
    if section == "abbreviation":
        return _t("abbreviation", team=team, value=value)
    if section == "offense_profile":
        key = parts[3]
        if key == "scope":
            return _t("scope", value=value) if parts[-1] == "label" else None
        base = _OFFENSE_BASE.get(key, key)
        profile = doc["teams"][side]["offense_profile"]
        hand = _hand(profile["vs_pitcher_hand"])
        scope = _scope(doc, path)
        if base == "vs_pitcher_hand":
            return _t("split_hand", team=team, hand=hand)
        shown = profile[base] if key in _OFFENSE_BASE else value
        return _t("offense_" + base, team=team, value=shown, hand=hand, scope=scope) if shown is not None else _t("offense_null", team=team)
    return None


def _pitch_mix(doc, index, path, parts, value):
    entry = doc["pitch_mix"][int(parts[1])]
    if parts[2] == "pitch":
        return _t("mix_pitch", value=value)
    slot, key = parts[2], parts[3]
    return _t("mix_" + key, name=_name(doc, slot), pitch=entry["pitch"], value=value)


def _movement(doc, path, parts, value):
    slot, pitch, key = parts[1], parts[2], parts[3]
    name = _name(doc, slot)
    if value is None and key in ("h_break", "v_break"):
        return _t("move_null", name=name, pitch=pitch)
    if key == "family":
        return _t("move_family", name=name, pitch=pitch, value=value)
    if key == "h_break":
        return _t("move_h", name=name, pitch=pitch, value=abs(value))
    if key == "v_break":
        return _t("move_v", name=name, pitch=pitch, value=abs(value), direction=_FACTS["down"] if value < 0 else _FACTS["up"])
    return None


def _findings(doc, parts, value):
    key = parts[1]
    if key == "lineup_notes":
        side = parts[2]
        if value is None:
            return _t("notes_null", team=_team(doc, side))
        return " ".join(_t("lineup_note", team=_team(doc, side), note=note.strip()) for note in value.split(";") if note.strip())
    if key in ("away_style", "home_style"):
        slot = key.replace("_style", "_starter")
        return _t("analyst_style", name=_name(doc, slot), value=value)
    match = re.fullmatch(r"(away_starter|home_starter)_(strengths|risks)", key)
    if match:
        slot, kind = match.groups()
        if value is None:
            return _t("analyst_null_" + kind, name=_name(doc, slot))
        return _t("analyst_" + kind, name=_name(doc, slot), value=value)
    return None


def _series(doc, parts, value):
    key = parts[1]
    if value is None:
        return None
    return {"series_name": lambda: _t("series_name", value=value), "game_number": lambda: _t("series_game", value=value),
            "games_in_series": lambda: _t("series_games", value=value), "standing": lambda: _t("series_standing", value=value)}[key]()


def premise_for(doc: dict, paths: list[str]) -> tuple[str | None, str | None]:
    """(premise, problem): the fact sentences of the cited paths joined in order, each once. problem is None, "unrenderable" or "oversize".

    Never truncates: a premise over 2,400 characters is refused (docs/SECURITY.md: reject oversize inputs rather than truncating evidence)."""

    facts: list[str] = []
    for path in paths:
        fact = render_fact(doc, path)
        if fact is None:
            return None, "unrenderable"
        if fact not in facts:
            facts.append(fact)
    premise = " ".join(facts)
    if not premise:
        return None, "unrenderable"
    if len(premise) > 2400:
        return None, "oversize"
    return premise, None
