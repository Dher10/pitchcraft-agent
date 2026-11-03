"""D58: code-owned, per-input fact IDs. No fuzzy or legacy path repair here.

The compact provider representation has named columns; source paths remain
private. Resolution expands only declared scope/limitation bindings.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from agents import writer_input as wi

VERSION = "fact-ids-v1"
_TEXT = json.loads(Path(__file__).with_name("writer_lexicon.json").read_text(encoding="utf-8"))["en"]["instrument"]


class UnknownFact(ValueError):
    """A provider supplied something other than a member of this fact table."""


def value_text(value):
    return "null" if value is None else "true" if value is True else "false" if value is False else str(value)


def scope_path(path):
    parts = path.split(".")
    if parts[0] == "starters" and len(parts) > 3:
        base = ".".join(parts[:2])
        if parts[2] == "season_summary":
            if parts[3] == "scopes":
                return ".".join(parts[:5])
            group = "counts" if parts[3] in wi._COUNTS else "season_rates"
            return f"{base}.season_summary.scopes.{group}"
        if parts[2] == "sample" and parts[3] in ("rates", "arsenal"):
            return f"{base}.sample.{parts[3]}.scope"
    if parts[0] == "teams" and len(parts) > 2 and parts[2] == "offense_profile":
        return ".".join(parts[:3]) + ".scope"
    if parts[0] == "pitch_movement" and len(parts) > 1:
        return f"starters.{parts[1]}.sample.arsenal.scope"
    if parts[0] == "pitch_mix" and len(parts) > 3:
        return f"starters.{parts[2]}.sample.arsenal.scope"
    if parts[0] == "velocity_by_pitch" and len(parts) > 2 and parts[2] != "pitch":
        return f"starters.{parts[2].removesuffix('_velocity')}.sample.arsenal.scope"
    return None


def scope_text(doc, path):
    index = wi.evidence_index(doc)
    base = scope_path(path)
    label, through = index.get(f"{base}.label"), index.get(f"{base}.through")
    if label is None:
        return None
    joiner = _TEXT["scope_joiner"]
    return str(label) if through is None or str(through) in str(label) else f"{str(label).split(joiner)[0]}{joiner}{through}"


def subject_field(doc, path):
    """Stable semantic subject and qualified field; used by the replay suffix estimate too."""
    parts = path.split(".")
    if parts[0] in ("starters", "teams") and len(parts) > 2:
        owner = parts[1]
        return doc[parts[0]][owner]["name"], ".".join(parts[2:])
    if parts[0] == "findings" and len(parts) > 1:
        if parts[1] == "lineup_notes" and len(parts) > 2:
            return doc["teams"][parts[2]]["name"], "lineup_notes"
        match = re.match(r"(away|home)(?:_starter)?_(.*)", parts[1])
        if match:
            side, field = match.groups()
            return doc["starters"][side + "_starter"]["name"], "findings." + field
    if parts[0] == "pitch_movement" and len(parts) > 3:
        return doc["starters"][parts[1]]["name"], ".".join(parts[2:])
    if parts[0] in ("pitch_mix", "velocity_by_pitch") and len(parts) > 2:
        try:
            pitch = doc[parts[0]][int(parts[1])]["pitch"]
            owner = parts[2].removesuffix("_velocity")
            if owner in wi.SLOTS:
                return doc["starters"][owner]["name"], f"{parts[0]}.{pitch}." + ".".join(parts[3:] or ["velocity"])
        except (KeyError, IndexError, ValueError, TypeError):
            pass
    return "game", path


def limitation_paths(doc, slot, dim):
    """Minimal declared label-rule proof, only when every condition is true."""
    labels = {"control": "command_label", "strikeout": "swing_miss_label"}
    if dim not in labels:
        return []
    prefix = f"starters.{slot}."
    paths = [prefix + f"sample.limited.{dim}", prefix + "sample.rates.batters_faced",
             prefix + f"sample.thresholds.{dim}", prefix + "pitching_profile." + labels[dim]]
    index = wi.evidence_index(doc)
    flag, count, threshold, label = (index.get(p) for p in paths)
    if flag is True and type(count) in (int, float) and type(threshold) in (int, float) and count < threshold and label is None and all(p in index for p in paths):
        return paths
    return []


@dataclass
class FactTable:
    rows: list[dict]
    bindings: dict[str, list[dict]]
    by_path: dict[str, str]
    identity: str
    doc: dict

    def id_for_path(self, path):
        return self.by_path.get(path)

    def visible(self):
        columns = ["id", "subject", "field", "value", "scope"]
        return {"protocol": VERSION, "columns": columns, "facts": [[row[c] for c in columns] for row in self.rows]}


def build_fact_table(doc):
    index = wi.evidence_index(doc)
    rows, bindings, by_path = [], {}, {}
    for path in sorted(index):
        # Aliases identify permissible spellings, not additional baseball facts.
        # Definitions are forbidden prose; short forms remain citable.
        if path == "language" or path.startswith("aliases.") or path.endswith(".meaning"):
            continue
        scope = scope_path(path)
        is_scope = scope and path.startswith(scope + ".")
        if is_scope and path != scope + ".label":
            continue
        fact_id = f"F{len(rows) + 1:03d}"
        subject, field = subject_field(doc, path)
        value = index[path]
        paths = [path]
        if is_scope:
            paths = [p for p in index if p.startswith(scope + ".")]
            value = scope_text(doc, path)
            field = field.removesuffix(".label")
        match = re.fullmatch(r"starters\.(away_starter|home_starter)\.(?:sample\.limited\.(control|strikeout)|pitching_profile\.(command|swing_miss)_label)", path)
        if match:
            slot, dim, label = match.groups()
            dim = dim or {"command": "control", "swing_miss": "strikeout"}[label]
            paths = list(dict.fromkeys([path, *limitation_paths(doc, slot, dim)]))
        # Scope is part of a scoped value, never an unrelated uncited row.
        if scope and not is_scope:
            paths = list(dict.fromkeys([*paths, *(p for p in index if p.startswith(scope + "."))]))
        rows.append({"id": fact_id, "subject": subject, "field": field, "value": value, "scope": scope_text(doc, path)})
        bindings[fact_id] = [{"path": p, "value": value_text(index[p])} for p in paths]
        by_path[path] = fact_id
        if is_scope:
            for p in paths:
                by_path[p] = fact_id
    identity = hashlib.sha256(json.dumps({"version": VERSION, "rows": rows, "bindings": bindings}, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
    return FactTable(rows, bindings, by_path, identity, doc)


def resolve_fact_ids(ids, table):
    if not isinstance(ids, list) or any(type(i) is not str or i not in table.bindings for i in ids):
        raise UnknownFact()
    result = []
    for fact_id in ids:
        for evidence in table.bindings[fact_id]:
            if evidence not in result:
                result.append(deepcopy(evidence))
    return result


def resolve_candidate(candidate, doc):
    """Return trusted internal evidence or explicit ID/structure findings; never guess."""
    from agents import writer_checks as wc
    table = build_fact_table(doc)
    result = deepcopy(candidate)
    try:
        sentences = wc._all_sentences(result)
        if not all(isinstance(s, dict) and set(s) == {"text", "evidence"} and type(s["text"]) is str and isinstance(s["evidence"], list) and len(s["evidence"]) <= wc.MAX_EVIDENCE for s in sentences):
            raise TypeError()
        errors = []
        for s in sentences:
            try:
                s["evidence"] = resolve_fact_ids(s["evidence"], table)
            except UnknownFact:
                errors.append({"check": "W1.fact_id", "sentence": s["text"], "token": str(s["evidence"])})
                s["evidence"] = []
        # Expanded code-owned closures can exceed the provider's six-ID limit.
        if not wc._structure_ok(result, expanded=True):
            raise TypeError()
        return result, errors
    except (KeyError, TypeError, IndexError):
        return None, [{"check": "W17.structure", "sentence": None, "token": None}]
