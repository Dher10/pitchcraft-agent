"""Rule-based Critic / Fact-check Agent."""

from __future__ import annotations

import re
from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog, catalog_for
from data_pipeline import labels

# How the pitch names of the DATA read (Statcast / the pitch mix), whatever language the
# report is in. The ways a report TEXT says them live in the catalog ("critic.pitch_aliases").
DATA_PITCH_NAMES = {
    "four-seam": ("four-seam",),
    "sinker": ("sinker", "two-seam"),
    "cutter": ("cutter",),
    "slider": ("slider",),
    "sweeper": ("sweeper",),
    "slurve": ("slurve",),
    "curveball": ("curveball",),
    "changeup": ("changeup",),
    "splitter": ("splitter",),
    "knuckleball": ("knuckleball",),
    "forkball": ("forkball",),
    "eephus": ("eephus",),
}
FASTBALL_FAMILY = ("four-seam", "sinker", "cutter")
GENERIC_FASTBALL = "fastball"
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _patterns(names: dict[str, tuple[str, ...]]) -> dict[str, re.Pattern[str]]:
    return {
        pitch: re.compile(r"\b(?:" + "|".join(re.escape(n) for n in forms) + r")s?\b")
        for pitch, forms in names.items()
    }


_DATA_PATTERNS = _patterns(DATA_PITCH_NAMES)
_FASTBALL_WORD = re.compile(r"\bfastballs?\b")


def run(
    report: dict[str, Any],
    matchup_input: dict[str, Any],
    language: str = DEFAULT_LANGUAGE,
) -> dict[str, Any]:
    """Check report claims against structured data and return the critic review, in `language`."""

    t = catalog_for(language)
    checks: list[dict[str, str]] = []
    checks.extend(_pitch_claim_checks(t, report, matchup_input))
    checks.append(_unobserved_pitch_check(t, report, matchup_input))
    checks.append(_command_check(t, report, matchup_input))
    checks.append(_scope_check(t, report, matchup_input))
    checks.append(_language_scan(t, report))

    # The critic reviews; it does not rewrite. A claim it cannot support is reported as
    # "unsupported", and the generator refuses to publish a report that has one.
    notes = [check["evidence"] for check in checks if check["status"] == "warning"]
    notes.extend([t("critic.note.focus"), t("critic.note.stuff_plus")])

    unsupported = sum(1 for check in checks if check["status"] == "unsupported")
    warnings = sum(1 for check in checks if check["status"] == "warning")
    if unsupported:
        summary = t("critic.summary.unsupported", checked=len(checks), unsupported=unsupported)
    elif warnings:
        summary = t("critic.summary.warnings", checked=len(checks), warnings=warnings)
    else:
        summary = t("critic.summary.supported", checked=len(checks))

    return {
        "status": "reviewed",
        "summary": summary,
        "checks": checks,
        "revision_notes": notes,
    }


def _pitch_claim_checks(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    report_text = _report_text(report).lower()
    for slot in ("away_starter", "home_starter"):
        starter = matchup_input["starters"][slot]
        profile = starter["pitching_profile"]
        sample = starter.get("sample")
        if sample and sample["limited"]["arsenal"]:
            checks.append(_limited_arsenal_check(t, starter, sample, report_text))
            continue
        for role, pitch, minimum in (
            ("primary", profile["primary_pitch"], labels.PRIMARY_MIN_USAGE_PCT),
            ("putaway", profile["putaway_pitch"], labels.PUTAWAY_MIN_USAGE_PCT),
        ):
            if labels.pitch_named(pitch):
                checks.append(_pitch_role_check(t, matchup_input, slot, starter, role, pitch, minimum))

    return checks


def _pitch_role_check(
    t: Catalog,
    matchup_input: dict[str, Any],
    slot: str,
    starter: dict[str, Any],
    role: str,
    pitch: str,
    minimum: int,
) -> dict[str, str]:
    usage = _pitch_usage(matchup_input, slot, pitch)
    role_name = t(f"critic.role.{role}")
    claim = t("critic.pitch.claim", name=starter["name"], role=role_name, pitch=_display_pitch(pitch))
    if usage <= 0:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.pitch.absent", pitch=_display_pitch(pitch), name=starter["name"]),
        }
    if usage >= minimum:
        evidence = t(f"critic.pitch.supported_{role}", usage=f"{usage:g}", pitch=_display_pitch(pitch))
        return {"claim": claim, "status": "supported", "evidence": evidence}
    return {
        "claim": claim,
        "status": "warning",
        "evidence": t(
            "critic.pitch.low",
            pitch=_display_pitch(pitch),
            usage=f"{usage:g}",
            name=starter["name"],
            minimum=minimum,
            role=role_name,
        ),
    }


def _canonical_pitches(name: str) -> set[str]:
    """The pitches a mix row of the data stands for ("Two-seam" is a sinker)."""

    lower = name.lower()
    found = {pitch for pitch, pattern in _DATA_PATTERNS.items() if pattern.search(lower)}
    if not found and _FASTBALL_WORD.search(lower):
        found.add(GENERIC_FASTBALL)
    return found


def _thrown_by(matchup_input: dict[str, Any], slot: str) -> set[str]:
    thrown: set[str] = set()
    for row in matchup_input["charts"]["pitch_mix"]:
        if row[slot]["overall"] > 0:
            thrown |= _canonical_pitches(row["pitch"])
    return thrown


def _named_pitches(t: Catalog, sentence: str) -> set[str]:
    lower = sentence.lower()
    named = {pitch for pitch, pattern in _patterns(t.vocabulary("critic.pitch_aliases")).items() if pattern.search(lower)}
    generic = t("critic.generic_fastball")
    if re.search(r"\b" + re.escape(generic) + r"s?\b", lower):
        named.add(GENERIC_FASTBALL)
    return named


def _supports(thrown: set[str], pitch: str) -> bool:
    if pitch == GENERIC_FASTBALL:
        return bool(thrown & {*FASTBALL_FAMILY, GENERIC_FASTBALL})
    return pitch in thrown


def _unobserved_pitch_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """
    Every pitch the report names must have been thrown in this game's data.

    A sentence that names exactly one starter is held to that starter's pitches; a
    sentence that names both, or neither, to the two together (free text cannot say
    whose pitch it is). Aliases count: "two-seam" is a sinker, "cut fastball" a
    cutter, and "fastball" is any fastball-family pitch.
    """

    slots = ("away_starter", "home_starter")
    thrown = {slot: _thrown_by(matchup_input, slot) for slot in slots}
    together = thrown["away_starter"] | thrown["home_starter"]
    names = {slot: matchup_input["starters"][slot]["name"] for slot in slots}

    problems: list[str] = []
    for _, text in _report_locations(report):
        for sentence in _SENTENCE_BREAK.split(text):
            mentioned = [slot for slot in slots if names[slot] in sentence]
            allowed = thrown[mentioned[0]] if len(mentioned) == 1 else together
            for pitch in sorted(_named_pitches(t, sentence)):
                if _supports(allowed, pitch):
                    continue
                if len(mentioned) == 1:
                    problems.append(t("critic.names.credited", name=names[mentioned[0]], pitch=pitch))
                else:
                    problems.append(t("critic.names.nobody", pitch=pitch))
    claim = t("critic.names.claim")
    if problems:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.names.unsupported", problems="; ".join(dict.fromkeys(problems))),
        }
    return {"claim": claim, "status": "supported", "evidence": t("critic.names.supported")}


def _limited_arsenal_check(
    t: Catalog, starter: dict[str, Any], sample: dict[str, Any], report_text: str
) -> dict[str, str]:
    """A limited arsenal must not be described: the report may only state the limitation."""

    profile = starter["pitching_profile"]
    named = [
        _display_pitch(pitch)
        for pitch in (profile["primary_pitch"], profile["putaway_pitch"])
        if labels.pitch_named(pitch) and _display_pitch(pitch).lower() in report_text
    ]
    pitches = sample["arsenal"]["pitches"]
    have = t("critic.limited.pitches", count=pitches) if pitches else t("critic.limited.none")
    needed = sample["thresholds"]["arsenal"]
    claim = t("critic.limited.claim", name=starter["name"])
    if named:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.limited.unsupported", have=have, needed=needed, named=", ".join(named)),
        }
    return {
        "claim": claim,
        "status": "supported",
        "evidence": t("critic.limited.supported", have=have.capitalize(), needed=needed),
    }


def _command_evidence(t: Catalog, matchup_input: dict[str, Any], slot: str) -> str:
    """Evidence for a command claim: the strength profile when there is one, else the walk rate."""

    if matchup_input["charts"].get("strength_profile"):
        return t("critic.command.strength", value=_strength_value(matchup_input, "Command", slot))
    sample = matchup_input["starters"][slot].get("sample")
    if sample and sample["rates"]["batters_faced"]:
        rates = sample["rates"]
        return t(
            "critic.command.walks",
            walks=rates["walks"],
            batters=rates["batters_faced"],
            scope=rates["scope"]["label"],
        )
    return t("critic.command.none")


def _scope_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """Pitch data and season figures must not be presented as one sample when they differ."""

    claim = t("critic.scope.claim")
    differing = [
        starter["name"]
        for starter in matchup_input["starters"].values()
        if starter.get("sample") and labels.scopes_differ(starter["sample"])
    ]
    if not differing:
        return {"claim": claim, "status": "not_present", "evidence": t("critic.scope.same")}
    if t("critic.scope.marker") in _report_text(report).lower():
        return {
            "claim": claim,
            "status": "supported",
            "evidence": t("critic.scope.supported", who=", ".join(differing)),
        }
    return {
        "claim": claim,
        "status": "unsupported",
        "evidence": t("critic.scope.unsupported", who=", ".join(differing)),
    }


def _command_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    report_text = _report_text(report).lower()

    def command_label(slot: str) -> str:
        return (matchup_input["starters"][slot]["pitching_profile"].get("command_label") or "").lower()

    below = labels.COMMAND_BELOW.lower()
    below_average = [
        slot
        for slot in ("away_starter", "home_starter")
        if below in command_label(slot)
    ]
    plus_or_solid = [
        slot
        for slot in ("away_starter", "home_starter")
        if any(term in command_label(slot) for term in ("plus", "solid"))
    ]

    if below in report_text and below_average:
        slot = below_average[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": t("critic.command.below_claim", name=starter["name"]),
            "status": "supported",
            "evidence": _command_evidence(t, matchup_input, slot),
        }

    if t("critic.command.word") in report_text and plus_or_solid:
        slot = plus_or_solid[0]
        starter = matchup_input["starters"][slot]
        return {
            "claim": t("critic.command.label_claim", name=starter["name"]),
            "status": "supported",
            "evidence": _command_evidence(t, matchup_input, slot),
        }

    return {
        "claim": t("critic.command.absent_claim"),
        "status": "not_present",
        "evidence": t("critic.command.absent_evidence"),
    }


def _language_scan(t: Catalog, report: dict[str, Any]) -> dict[str, str]:
    locations = _report_locations(report)
    flagged: list[str] = []
    for location, text in locations:
        lower_text = text.lower()
        for term in t.terms("critic.betting_terms"):
            if term in lower_text:
                flagged.append(t("critic.betting.item", term=term, location=location))

    claim = t("critic.betting.claim")
    if flagged:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.betting.unsupported", flagged=", ".join(flagged)),
        }

    return {"claim": claim, "status": "not_present", "evidence": t("critic.betting.absent")}


def _pitch_usage(matchup_input: dict[str, Any], slot: str, pitch: str) -> float:
    target = _normalize_pitch(pitch)
    for row in matchup_input["charts"]["pitch_mix"]:
        if _normalize_pitch(row["pitch"]) == target:
            return float(row[slot]["overall"])
    return 0


def _normalize_pitch(pitch: str) -> str:
    value = pitch.lower()
    for token in (labels.FASTBALL_SUFFIX, "-seam"):
        value = value.replace(token, "")
    return value.strip()


def _display_pitch(pitch: str) -> str:
    return pitch.replace(labels.FASTBALL_SUFFIX, "")


def _strength_value(matchup_input: dict[str, Any], dimension: str, slot: str) -> int:
    for row in matchup_input["charts"]["strength_profile"]:
        if row["dimension"] == dimension:
            return int(row[slot])
    return 0


def _report_text(report: dict[str, Any]) -> str:
    return "\n".join(text for _, text in _report_locations(report))


def _report_locations(report: dict[str, Any]) -> list[tuple[str, str]]:
    locations: list[tuple[str, str]] = [("headline", report.get("headline", ""))]
    for index, summary in enumerate(report.get("short_summary", [])):
        locations.append((f"short_summary[{index}]", summary))
    for index, section in enumerate(report.get("sections", [])):
        if section.get("body"):
            locations.append((f"sections[{index}].body", section["body"]))
        for bullet_index, bullet in enumerate(section.get("bullets", [])):
            locations.append((f"sections[{index}].bullets[{bullet_index}]", bullet))
    return locations
