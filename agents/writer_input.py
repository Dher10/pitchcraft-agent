"""The closed input the LLM writer receives: one projection for A, B1 and B2 (guide W1, W16).

Built from a frozen packet, its findings and the frozen glossary. It keeps the figures, labels and scopes the guide names
and drops everything else: ids, bio, recent form, postgame, pitch locations, times, the fetch note (`data_confidence.notes`).
Findings reach the writer as labels only, never as the rules writer's sentences. Names are NFC-normalized.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unicodedata
from typing import Any

SLOTS = ("away_starter", "home_starter")
SIDES = ("away", "home")
CONFIDENCE_KEYS = ("lineup_status",)  # "level" and "pitch_data_status" are internal enums (fetched_snapshot) the writer must not echo (W16)
STARTER_KEYS = ("name", "team", "throws", "season_summary", "pitching_profile", "sample")
TEAM_KEYS = ("name", "abbreviation", "offense_profile")
OFFENSE_DROPPED = ("recent_form", "summary_label")
FINDING_LISTS = ("away_starter_strengths", "away_starter_risks", "home_starter_strengths", "home_starter_risks")
FINDING_STYLES = ("away_style", "home_style")


class WriterInputError(ValueError):
    """The packet or findings do not have the shape the projection needs."""


def load_glossary(path) -> list[dict]:
    terms = json.loads(Path(path).read_text(encoding="utf-8"))["terms"]
    return [{"term": t["term"], "definition": t["definition"]} for t in terms]


def _nfc(node: Any) -> Any:
    if isinstance(node, str):
        return unicodedata.normalize("NFC", node)
    if isinstance(node, dict):
        return {_nfc(k): _nfc(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_nfc(v) for v in node]
    return node


def _plain(value: Any) -> Any:
    """An enum word with underscores ("probable_pitchers") as plain words."""

    return value.replace("_", " ") if isinstance(value, str) else value


def _drop_internal(node: Any) -> None:
    """Remove the taxonomy keys the writer never needs: a scope's `kind` (its label says it) and a rate's `source`."""

    if isinstance(node, dict):
        if "label" in node and "kind" in node:
            del node["kind"]
        if "batters_faced" in node:
            node.pop("source", None)
        for value in node.values():
            _drop_internal(value)
    elif isinstance(node, list):
        for value in node:
            _drop_internal(value)


def _need(mapping: Any, key: str, where: str) -> Any:
    if not isinstance(mapping, dict) or key not in mapping:
        raise WriterInputError(f"missing {where}.{key}")
    return mapping[key]


def build_writer_input(packet: dict, findings: dict, glossary: list[dict]) -> dict:
    """Return the closed writer input. Inputs are not modified."""

    packet = deepcopy(packet)
    starters, teams = _need(packet, "starters", "packet"), _need(packet, "teams", "packet")
    charts = _need(packet, "charts", "packet")
    confidence = _need(packet, "data_confidence", "packet")
    game = _need(packet, "game", "packet")
    doc: dict[str, Any] = {
        "language": "en",
        "date": _need(packet, "date", "packet"),
        "status": packet.get("status"),
        "venue": game.get("venue") if isinstance(game, dict) else None,
        "series": packet.get("series"),
        "data_confidence": {key: _plain(_need(confidence, key, "data_confidence")) for key in CONFIDENCE_KEYS},
        "teams": {},
        "starters": {},
    }
    for side in SIDES:
        team = _need(teams, side, "teams")
        doc["teams"][side] = {key: _need(team, key, f"teams.{side}") for key in TEAM_KEYS}
        # "recent_form" is a label of the split ("Season split") and invites time claims (W12); "summary_label" is internal.
        doc["teams"][side]["offense_profile"] = {k: v for k, v in doc["teams"][side]["offense_profile"].items() if k not in OFFENSE_DROPPED}
    for slot in SLOTS:
        starter = _need(starters, slot, "starters")
        doc["starters"][slot] = {key: _need(starter, key, f"starters.{slot}") for key in STARTER_KEYS}
    doc["pitch_mix"] = _need(charts, "pitch_mix", "charts")
    doc["pitch_movement"] = _need(charts, "pitch_movement", "charts")
    doc["velocity_by_pitch"] = _need(charts, "velocity_by_pitch", "charts")
    doc["findings"] = _findings(findings, teams)
    doc["glossary"] = [{"term": t["term"], "definition": t["definition"]} for t in glossary]
    _drop_internal(doc)
    return _nfc(doc)


def _findings(findings: dict, teams: dict) -> dict:
    out: dict[str, Any] = {key: list(_need(findings, key, "findings")) for key in FINDING_LISTS}
    for key in FINDING_STYLES:
        out[key] = _need(findings, key, "findings")
    by_team = _need(findings, "lineup_pressure_points_by_team", "findings")
    out["lineup_notes"] = {side: list(by_team.get(str(teams[side]["id"]), [])) for side in SIDES}
    return out


def evidence_index(doc: dict) -> dict[str, Any]:
    """Every scalar of the input by dotted path (list items by position), glossary entries by `glossary.<term>`."""

    index: dict[str, Any] = {}

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                walk(value, f"{path}.{key}" if path else str(key))
        elif isinstance(node, list):
            for position, value in enumerate(node):
                walk(value, f"{path}.{position}")
        else:
            index[path] = node

    for key, value in doc.items():
        if key == "glossary":
            for entry in value:
                index[f"glossary.{entry['term']}"] = entry["definition"]
        else:
            walk(value, key)
    return index


_COUNTS = {"strikeouts", "walks", "home_runs_allowed"}


def _dig(doc: Any, *keys: str) -> Any:
    for key in keys:
        doc = doc[key]
    return doc


def scope_label(doc: dict, path: str) -> str | None:
    """The scope label of the figure at `path`, or None when the path is not a scoped figure.

    The label is read as the string the packet already carries (written by labels.figure_scopes); nothing is derived here."""

    parts = path.split(".")
    try:
        if parts[0] == "starters" and parts[2] == "season_summary" and len(parts) == 4 and parts[3] != "scopes":
            return _dig(doc, "starters", parts[1], "season_summary", "scopes", "counts" if parts[3] in _COUNTS else "season_rates", "label")
        if parts[0] == "starters" and parts[2] == "sample" and parts[3] in ("rates", "arsenal") and len(parts) == 5 and parts[4] != "scope":
            return _dig(doc, "starters", parts[1], "sample", parts[3], "scope", "label")
        if parts[0] == "teams" and parts[2] == "offense_profile" and len(parts) == 4 and parts[3] != "scope":
            return _dig(doc, "teams", parts[1], "offense_profile", "scope", "label")
        if parts[0] == "pitch_movement":
            return _dig(doc, "starters", parts[1], "sample", "arsenal", "scope", "label")
        if parts[0] == "pitch_mix" and len(parts) == 4:
            return _dig(doc, "starters", parts[2], "sample", "arsenal", "scope", "label")
        if parts[0] == "velocity_by_pitch" and len(parts) == 3:
            return _dig(doc, "starters", parts[2].removesuffix("_velocity"), "sample", "arsenal", "scope", "label")
    except (KeyError, IndexError, TypeError):
        return None
    return None
