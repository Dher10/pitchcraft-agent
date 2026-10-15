"""What the report says about the data, read from the payload (contract rule 4, P0.15-D3.3a).

The conditions of the critic's claims about the data are decided here, on the fields of a published
matchup (`charts.pitch_mix`, `starters`, `sample`, the labels) and the text of its `report`, with the words
the catalog gives (`critic.pitch_aliases`, `critic.betting_terms`, the markers). They never run the critic:
the critic is what is being checked, and asking it again would only repeat its answer. This module does not
import it, and `tests/test_registry_no_critic.py` fails if it, or the registry, ever does.

The five questions:

- `pitches_not_thrown`: which pitch the report credits to a starter who did not throw it;
- `pitches_named_for`: which pitch the report names for a starter whose arsenal is limited;
- `command_finding`: what the report claims about command, against the labels;
- `scope_finding` and `says_samples_differ`: whether the report says that the groups of figures cover
  different games, for the starters whose groups do;
- `betting_terms`: which words of outcome or betting language the report uses.

A sentence belongs to the starter it names alone; one that names nobody belongs to the starter in the
title of its section, if the title names exactly one; one that names both is nobody's alone (QA3-04).
"""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from agents.language import SUBJECT_SLOTS, Catalog
from data_pipeline import labels

SLOTS = SUBJECT_SLOTS
GENERIC_FASTBALL = "fastball"
FASTBALL_FAMILY = ("four-seam", "sinker", "cutter")
COMMAND_STRONG_TERMS = ("plus", "solid")  # words of the data labels ("Plus command", "Solid command")
# How the pitch names of the DATA read (the pitch mix), whatever the language of the report.
DATA_PITCH_NAMES: dict[str, tuple[str, ...]] = {
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
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
_ANY_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+")
_FASTBALL_WORD = re.compile(r"\bfastballs?\b")


def _forms(names: Mapping[str, tuple[str, ...]]) -> dict[str, re.Pattern[str]]:
    return {
        pitch: re.compile(r"\b(?:" + "|".join(re.escape(n) for n in forms) + r")s?\b")
        for pitch, forms in names.items()
    }


_DATA_PATTERNS = _forms(DATA_PITCH_NAMES)


# --- the text of the report ----------------------------------------------------------------------


def report_locations(report: Mapping[str, Any]) -> list[tuple[str, str]]:
    """(location, text) of every text the report shows: headline, summary lines, section bodies and bullets."""

    found: list[tuple[str, str]] = []
    if isinstance(report.get("headline"), str):
        found.append(("headline", report["headline"]))
    for index, line in enumerate(report.get("short_summary") or []):
        if isinstance(line, str):
            found.append((f"short_summary[{index}]", line))
    for index, section in enumerate(report.get("sections") or []):
        if not isinstance(section, Mapping):
            continue
        if isinstance(section.get("body"), str) and section["body"]:
            found.append((f"sections[{index}].body", section["body"]))
        for number, bullet in enumerate(section.get("bullets") or []):
            if isinstance(bullet, str):
                found.append((f"sections[{index}].bullets[{number}]", bullet))
    return found


def report_text(report: Mapping[str, Any]) -> str:
    return "\n".join(text for _, text in report_locations(report))


def owned_sentences(matchup: Mapping[str, Any], report: Mapping[str, Any]) -> list[tuple[str | None, str]]:
    """Every sentence of the report with the starter it is about, or None when that cannot be told."""

    names = {slot: matchup["starters"][slot]["name"] for slot in SLOTS}

    def owner(sentence: str, section_owner: str | None) -> str | None:
        mentioned = [slot for slot in SLOTS if names[slot] in sentence]
        if len(mentioned) == 1:
            return mentioned[0]
        return None if mentioned else section_owner

    def split(text: str, section_owner: str | None) -> list[tuple[str | None, str]]:
        return [(owner(sentence, section_owner), sentence) for sentence in _SENTENCE_BREAK.split(text)]

    owned: list[tuple[str | None, str]] = []
    for text in (report.get("headline"), *(report.get("short_summary") or [])):
        if isinstance(text, str):
            owned.extend(split(text, None))
    for section in report.get("sections") or []:
        if not isinstance(section, Mapping):
            continue
        titled = [slot for slot in SLOTS if names[slot] in str(section.get("title"))]
        section_owner = titled[0] if len(titled) == 1 else None
        for text in (section.get("body"), *(section.get("bullets") or [])):
            if isinstance(text, str) and text:
                owned.extend(split(text, section_owner))
    return owned


def _without_names(sentence: str, names: list[str]) -> str:
    """The sentence without the starters' names: a pitcher called "Fastball" threw no pitch by it."""

    for name in sorted(names, key=len, reverse=True):
        sentence = sentence.replace(name, " ")
    return sentence


# --- pitches -------------------------------------------------------------------------------------


def _normalize_pitch(pitch: str) -> str:
    value = pitch.lower()
    for token in (labels.FASTBALL_SUFFIX, "-seam"):
        value = value.replace(token, "")
    return value.strip()


def _mix_row(matchup: Mapping[str, Any], pitch: str) -> Mapping[str, Any] | None:
    target = _normalize_pitch(pitch)
    return next((row for row in matchup["charts"]["pitch_mix"] if _normalize_pitch(row["pitch"]) == target), None)


def _was_thrown(cell: Mapping[str, Any]) -> bool:
    """A pitch counted at least once was thrown, even if its share rounds to 0.0 (raw counts first)."""

    count, total = cell.get("count"), cell.get("total")
    if isinstance(count, int) and isinstance(total, int):
        return count > 0
    return cell["overall"] is not None and float(cell["overall"]) > 0  # a null share was not thrown


def _canonical_pitches(name: str) -> set[str]:
    """The pitches a mix row stands for ("Two-seam" is a sinker)."""

    lower = name.lower()
    found = {pitch for pitch, pattern in _DATA_PATTERNS.items() if pattern.search(lower)}
    if not found and _FASTBALL_WORD.search(lower):
        found.add(GENERIC_FASTBALL)
    return found


def thrown_by(matchup: Mapping[str, Any], slot: str) -> set[str]:
    """The pitches (canonical names) the starter in `slot` threw, from the raw counts of the mix."""

    thrown: set[str] = set()
    for row in matchup["charts"]["pitch_mix"]:
        if _was_thrown(row[slot]):
            thrown |= _canonical_pitches(row["pitch"])
    return thrown


def _named_pitches(catalog: Catalog, sentence: str) -> set[str]:
    lower = sentence.lower()
    named = {pitch for pitch, pattern in _forms(catalog.vocabulary("critic.pitch_aliases")).items() if pattern.search(lower)}
    generic = catalog.render("critic.generic_fastball", {})
    if re.search(r"\b" + re.escape(generic) + r"s?\b", lower):
        named.add(GENERIC_FASTBALL)
    return named


def _supports(thrown: set[str], pitch: str) -> bool:
    if pitch == GENERIC_FASTBALL:
        return bool(thrown & {*FASTBALL_FAMILY, GENERIC_FASTBALL})
    return pitch in thrown


def _names_of(matchup: Mapping[str, Any]) -> list[str]:
    return [matchup["starters"][slot]["name"] for slot in SLOTS]


def pitches_not_thrown(matchup: Mapping[str, Any], report: Mapping[str, Any], catalog: Catalog) -> list[tuple[str | None, str]]:
    """
    (owner, pitch) for every pitch the report names that its owner did not throw.

    The owner is the starter the sentence is held to, or None when it is held to the two together (a
    sentence that names both starters, or nobody outside a starter's section).
    """

    thrown = {slot: thrown_by(matchup, slot) for slot in SLOTS}
    together = thrown[SLOTS[0]] | thrown[SLOTS[1]]
    names = _names_of(matchup)
    problems: list[tuple[str | None, str]] = []
    for owner, sentence in owned_sentences(matchup, report):
        allowed = thrown[owner] if owner else together
        for pitch in sorted(_named_pitches(catalog, _without_names(sentence, names))):
            if not _supports(allowed, pitch):
                problems.append((owner, pitch))
    return list(dict.fromkeys(problems))


def pitches_named_for(matchup: Mapping[str, Any], report: Mapping[str, Any], slot: str, catalog: Catalog) -> list[str]:
    """
    The pitches the report names for the starter in `slot`, whose arsenal is limited.

    Only what the report says about him counts: the sentences that name only him, and the unnamed ones in
    the section titled with his name. A sentence that names both, or nobody and sits in no starter's
    section, is held to him only for a pitch the other starter never threw.
    """

    other = SLOTS[1] if slot == SLOTS[0] else SLOTS[0]
    other_thrown = thrown_by(matchup, other)
    names = _names_of(matchup)
    profile = matchup["starters"][slot]["pitching_profile"]
    profile_pitches = [p for p in (profile["primary_pitch"], profile["putaway_pitch"]) if labels.pitch_named(p)]
    named: list[str] = []

    def add(display: str) -> None:
        if display.lower() not in (item.lower() for item in named):
            named.append(display)

    for owner, sentence in owned_sentences(matchup, report):
        if owner == other:
            continue
        text = _without_names(sentence, names)
        for pitch in sorted(_named_pitches(catalog, text)):
            if owner is None and _supports(other_thrown, pitch):
                continue
            add(pitch.capitalize())
        for pitch in profile_pitches:  # the profile's own pitch names count too, even outside the vocabulary
            display = pitch.replace(labels.FASTBALL_SUFFIX, "")
            row = _mix_row(matchup, pitch)
            other_threw = bool(row) and _was_thrown(row[other])
            if display.lower() in text.lower() and not (owner is None and other_threw):
                add(display)
    return named


# --- command -------------------------------------------------------------------------------------


def command_finding(matchup: Mapping[str, Any], report: Mapping[str, Any], catalog: Catalog) -> tuple[str, str | None]:
    """
    What the report claims about command, as (kind, slot):

    - ("wrong", slot): it says a command the label of that starter does not have;
    - ("below", slot): it says below-average command and the label of that starter is that;
    - ("label", slot): it says a plus or solid command and the label of that starter is that;
    - ("absent", None): it makes no command claim.

    A claim with no starter to attribute it to is supported if some starter has the label.
    """

    owned = owned_sentences(matchup, report)
    said = {slot: " ".join(s for o, s in owned if o == slot).lower() for slot in (*SLOTS, None)}
    word = catalog.render("critic.command.word", {})
    below = labels.COMMAND_BELOW.lower()
    strong_phrases = [f"{term} {word}" for term in COMMAND_STRONG_TERMS]

    def label_of(slot: str) -> str:
        return (matchup["starters"][slot]["pitching_profile"].get("command_label") or "").lower()

    below_average = [slot for slot in SLOTS if below in label_of(slot)]
    plus_or_solid = [slot for slot in SLOTS if any(term in label_of(slot) for term in COMMAND_STRONG_TERMS)]

    for slot in SLOTS:
        if below in said[slot] and slot not in below_average:
            return "wrong", slot
        if slot not in plus_or_solid and any(phrase in said[slot] for phrase in strong_phrases):
            return "wrong", slot

    claimed_below = [slot for slot in SLOTS if below in said[slot]]
    if not claimed_below and below in said[None]:
        claimed_below = below_average
    if claimed_below:
        return "below", claimed_below[0]

    claimed_command = [slot for slot in plus_or_solid if word in said[slot]]
    if not claimed_command and word in said[None]:
        claimed_command = plus_or_solid
    if claimed_command:
        return "label", claimed_command[0]
    return "absent", None


def command_strength(matchup: Mapping[str, Any], slot: str) -> int | None:
    """The 0-100 Command score of the strength profile, or None when there is none (never a zero)."""

    for row in matchup["charts"].get("strength_profile") or []:
        if row.get("dimension") == "Command" and row.get(slot) is not None:
            return int(row[slot])
    return None


# --- scope ---------------------------------------------------------------------------------------


def differing_starters(matchup: Mapping[str, Any]) -> tuple[str, ...]:
    """The names of the starters whose groups of figures do not all cover the same games."""

    return tuple(s["name"] for s in matchup["starters"].values() if labels.scopes_differ(s))


def says_samples_differ(report: Mapping[str, Any], catalog: Catalog) -> bool:
    return catalog.render("critic.scope.marker", {}) in report_text(report).lower()


def scope_finding(matchup: Mapping[str, Any], report: Mapping[str, Any], catalog: Catalog) -> tuple[str, tuple[str, ...]]:
    """
    How the report treats the starters whose groups of figures cover different games, as (kind, names):

    - ("same", ()): no starter's groups differ, nothing to say;
    - ("all_claimed", names): it says all the figures cover one sample about a starter whose groups differ;
    - ("supported", names): it says the figures cover different samples;
    - ("unsupported", names): it does not say so.
    """

    differing = differing_starters(matchup)
    if not differing:
        return "same", ()
    all_marker = catalog.render("critic.scope.all_marker", {})
    sentences = _ANY_SENTENCE_BREAK.split(report_text(report))
    claimed = tuple(
        name for name in differing if any(all_marker in s.lower() and name.lower() in s.lower() for s in sentences)
    )
    if claimed:
        return "all_claimed", claimed
    if says_samples_differ(report, catalog):
        return "supported", differing
    return "unsupported", differing


# --- betting -------------------------------------------------------------------------------------


def betting_terms(report: Mapping[str, Any], catalog: Catalog) -> list[tuple[str, str]]:
    """(term, location) of every word of outcome or betting language in the report."""

    found: list[tuple[str, str]] = []
    for location, text in report_locations(report):
        lower = text.lower()
        for term in catalog.terms("critic.betting_terms"):
            if term in lower:
                found.append((term, location))
    return found
