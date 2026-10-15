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
SLOTS = ("away_starter", "home_starter")
# Words of the data labels ("Plus command", "Solid command"), not text the agents write.
COMMAND_STRONG_TERMS = ("plus", "solid")
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
    language = _language_scan(t, report)
    checks.append(language)

    # The critic reviews; it does not rewrite. A claim it cannot support is reported as
    # "unsupported", and the generator refuses to publish a report that has one.
    notes = [check["evidence"] for check in checks if check["status"] == "warning"]
    # A note says what a check verified: this one is written only when the betting-language check found nothing.
    if language["status"] == "not_present":
        notes.append(t("critic.note.no_betting"))

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
    owned = _owned_sentences(report, matchup_input)
    for slot in SLOTS:
        starter = matchup_input["starters"][slot]
        profile = starter["pitching_profile"]
        sample = starter.get("sample")
        if sample and sample["limited"]["arsenal"]:
            checks.append(_limited_arsenal_check(t, matchup_input, slot, sample, owned))
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
    with t.subject(slot):
        return _pitch_role_result(t, matchup_input, slot, starter, role, pitch, minimum)


def _pitch_role_result(
    t: Catalog,
    matchup_input: dict[str, Any],
    slot: str,
    starter: dict[str, Any],
    role: str,
    pitch: str,
    minimum: int,
) -> dict[str, str]:
    usage = _pitch_usage(matchup_input, slot, pitch)
    counts = _pitch_counts(matchup_input, slot, pitch)
    role_name = t(f"critic.role.{role}")
    claim = t("critic.pitch.claim", name=starter["name"], role=role_name, pitch=_display_pitch(pitch))
    if not _was_thrown(usage, counts):
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.pitch.absent", pitch=_display_pitch(pitch), name=starter["name"]),
        }
    # The minimum is a decision: it is taken on the raw counts when the mix has them, so a share
    # of 29.97% (drawn as 30.0) is below 30. Rows without counts (the demo, older snapshots)
    # only have the percentage.
    meets = labels.share_at_least(counts[0], counts[1], minimum) if counts else usage >= minimum
    if meets:
        evidence = t(f"critic.pitch.supported_{role}", usage=f"{usage:g}", pitch=_display_pitch(pitch))
        return {"claim": claim, "status": "supported", "evidence": evidence}
    if counts:
        evidence = t(
            "critic.pitch.low_counts",
            pitch=_display_pitch(pitch),
            count=f"{counts[0]:,}",
            total=f"{counts[1]:,}",
            usage=f"{counts[0] / counts[1] * 100:.2f}",
            name=starter["name"],
            minimum=minimum,
            role=role_name,
        )
    else:
        evidence = t(
            "critic.pitch.low",
            pitch=_display_pitch(pitch),
            usage=f"{usage:g}",
            name=starter["name"],
            minimum=minimum,
            role=role_name,
        )
    return {"claim": claim, "status": "warning", "evidence": evidence}


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
        if _was_thrown(row[slot]["overall"], _row_counts(row, slot)):
            thrown |= _canonical_pitches(row["pitch"])
    return thrown


def _named_pitches(t: Catalog, sentence: str) -> set[str]:
    lower = sentence.lower()
    named = {pitch for pitch, pattern in _patterns(t.vocabulary("critic.pitch_aliases")).items() if pattern.search(lower)}
    generic = t("critic.generic_fastball")
    if re.search(r"\b" + re.escape(generic) + r"s?\b", lower):
        named.add(GENERIC_FASTBALL)
    return named


def _without_names(sentence: str, names: list[str]) -> str:
    """The sentence without the starters' names: a pitcher called "Fastball" threw no pitch by it."""

    for name in sorted(names, key=len, reverse=True):
        sentence = sentence.replace(name, " ")
    return sentence


def _supports(thrown: set[str], pitch: str) -> bool:
    if pitch == GENERIC_FASTBALL:
        return bool(thrown & {*FASTBALL_FAMILY, GENERIC_FASTBALL})
    return pitch in thrown


def _unobserved_pitch_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """
    Every pitch the report names must have been thrown in this game's data.

    A sentence belongs to the starter it names alone, or, if it names nobody, to the starter in
    the title of its section (`_owned_sentences`, QA3-04); it is held to that starter's pitches.
    A sentence that names both, or nobody outside a starter's section, is held to the two
    together (free text cannot say whose pitch it is). Aliases count: "two-seam" is a sinker,
    "cut fastball" a cutter, and "fastball" is any fastball-family pitch.
    """

    thrown = {slot: _thrown_by(matchup_input, slot) for slot in SLOTS}
    together = thrown[SLOTS[0]] | thrown[SLOTS[1]]
    names = {slot: matchup_input["starters"][slot]["name"] for slot in SLOTS}

    problems: list[str] = []
    for owner, sentence in _owned_sentences(report, matchup_input):
        allowed = thrown[owner] if owner else together
        for pitch in sorted(_named_pitches(t, _without_names(sentence, list(names.values())))):
            if _supports(allowed, pitch):
                continue
            if owner:
                with t.subject(owner):
                    problems.append(t("critic.names.credited", name=names[owner], pitch=pitch))
            else:
                problems.append(t("critic.names.nobody", pitch=pitch))
    claim = t("critic.names.claim")
    if problems:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.names.unsupported", problems=t.join("; ", list(dict.fromkeys(problems)))),
        }
    return {"claim": claim, "status": "supported", "evidence": t("critic.names.supported")}


def _limited_arsenal_check(
    t: Catalog,
    matchup_input: dict[str, Any],
    slot: str,
    sample: dict[str, Any],
    owned: list[tuple[str | None, str]],
) -> dict[str, str]:
    """
    A limited arsenal must not be described: the report may only state the limitation.

    Only what the report says about this starter counts (QA2-02): the sentences that name
    only him, and the unnamed ones in the section titled with his name. What it says about
    the other starter is that starter's business, even if both throw the same pitch. A
    sentence that names both, or nobody and sits in no starter's section, is held to this
    starter only for a pitch the other one never threw.
    """

    starter = matchup_input["starters"][slot]
    other = SLOTS[1] if slot == SLOTS[0] else SLOTS[0]
    other_thrown = _thrown_by(matchup_input, other)
    names = [matchup_input["starters"][s]["name"] for s in SLOTS]
    profile = starter["pitching_profile"]
    profile_pitches = [
        pitch for pitch in (profile["primary_pitch"], profile["putaway_pitch"]) if labels.pitch_named(pitch)
    ]
    named: list[str] = []

    def add(display: str) -> None:
        if display.lower() not in (item.lower() for item in named):
            named.append(display)

    for owner, sentence in owned:
        if owner == other:
            continue
        text = _without_names(sentence, names)
        for pitch in sorted(_named_pitches(t, text)):
            if owner is None and _supports(other_thrown, pitch):
                continue
            add(pitch.capitalize())
        # The profile's own pitch names count too, even outside the vocabulary of known pitches.
        for pitch in profile_pitches:
            if _display_pitch(pitch).lower() in text.lower() and not (
                owner is None
                and _was_thrown(
                    _pitch_usage(matchup_input, other, pitch), _pitch_counts(matchup_input, other, pitch)
                )
            ):
                add(_display_pitch(pitch))
    pitches = sample["arsenal"]["pitches"]
    with t.subject(slot):
        needed = sample["thresholds"]["arsenal"]
        claim = t("critic.limited.claim", name=starter["name"])
        if pitches is None:  # an unknown count is not "no pitches on record" (F14)
            if named:
                evidence = t("critic.limited.unsupported_unavailable", needed=needed, named=t.join(", ", named))
                return {"claim": claim, "status": "unsupported", "evidence": evidence}
            return {
                "claim": claim,
                "status": "supported",
                "evidence": t("critic.limited.supported_unavailable", needed=needed),
            }
        have = t("critic.limited.pitches", count=pitches) if pitches else t("critic.limited.none")
        if named:
            return {
                "claim": claim,
                "status": "unsupported",
                "evidence": t("critic.limited.unsupported", have=have, needed=needed, named=t.join(", ", named)),
            }
        return {
            "claim": claim,
            "status": "supported",
            "evidence": t("critic.limited.supported", have=have.capitalize(), needed=needed),
        }


def _command_evidence(t: Catalog, matchup_input: dict[str, Any], slot: str) -> str:
    """Evidence for a command claim: the strength profile when there is one, else the walk rate."""

    strength = _strength_value(matchup_input, "Command", slot)
    if strength is not None:
        return t("critic.command.strength", value=strength)
    starter = matchup_input["starters"][slot]
    sample = starter.get("sample")
    counts = labels.figure_scopes(starter).get("counts")
    if sample and sample["rates"]["batters_faced"] and counts:
        rates = sample["rates"]
        return t(
            "critic.command.walks",
            walks=rates["walks"],
            batters=rates["batters_faced"],
            scope=counts["label"],
        )
    return t("critic.command.none")


def _scope_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """Pitch data and season figures must not be presented as one sample when they differ."""

    claim = t("critic.scope.claim")
    differing = [
        starter["name"]
        for starter in matchup_input["starters"].values()
        if labels.scopes_differ(starter)
    ]
    if not differing:
        return {"claim": claim, "status": "not_present", "evidence": t("critic.scope.same")}
    # "All figures cover one sample" about a starter whose groups cover different games is false,
    # whether or not the report also says somewhere that they differ.
    all_marker = t("critic.scope.all_marker")
    claimed = [
        name
        for name in differing
        if any(
            all_marker in sentence.lower() and name.lower() in sentence.lower()
            for sentence in re.split(r"(?<=[.!?])\s+", _report_text(report))
        )
    ]
    if claimed:
        return {
            "claim": claim,
            "status": "unsupported",
            "evidence": t("critic.scope.all_claimed", who=t.join(", ", claimed)),
        }
    if t("critic.scope.marker") in _report_text(report).lower():
        return {
            "claim": claim,
            "status": "supported",
            "evidence": t("critic.scope.supported", who=t.join(", ", differing)),
        }
    return {
        "claim": claim,
        "status": "unsupported",
        "evidence": t("critic.scope.unsupported", who=t.join(", ", differing)),
    }


def _command_check(t: Catalog, report: dict[str, Any], matchup_input: dict[str, Any]) -> dict[str, str]:
    """
    A command claim must match the label of the starter it is about (QA2-02 sweep).

    "Below-average command" said about a starter whose label is not that, or "solid
    command" about one who is not solid, is unsupported even if the other starter has the
    label. A claim with no starter to attribute it to is supported if some starter has it.
    """

    owned = _owned_sentences(report, matchup_input)
    said = {slot: " ".join(s for o, s in owned if o == slot).lower() for slot in (*SLOTS, None)}
    word = t("critic.command.word")
    below = labels.COMMAND_BELOW.lower()
    strong_phrases = [f"{term} {word}" for term in COMMAND_STRONG_TERMS]

    def command_label(slot: str) -> str:
        return (matchup_input["starters"][slot]["pitching_profile"].get("command_label") or "").lower()

    below_average = [slot for slot in SLOTS if below in command_label(slot)]
    plus_or_solid = [
        slot for slot in SLOTS if any(term in command_label(slot) for term in COMMAND_STRONG_TERMS)
    ]

    for slot in SLOTS:
        wording = None
        if below in said[slot] and slot not in below_average:
            wording = below
        elif slot not in plus_or_solid:
            wording = next((phrase for phrase in strong_phrases if phrase in said[slot]), None)
        if wording:
            starter = matchup_input["starters"][slot]
            with t.subject(slot):
                label = starter["pitching_profile"].get("command_label") or t("critic.command.no_label")
                return {
                    "claim": t("critic.command.wrong_claim", name=starter["name"]),
                    "status": "unsupported",
                    "evidence": t(
                        "critic.command.wrong_evidence", name=starter["name"], wording=wording, label=label
                    ),
                }

    claimed_below = [slot for slot in SLOTS if below in said[slot]]
    if not claimed_below and below in said[None]:
        claimed_below = below_average
    if claimed_below:
        slot = claimed_below[0]
        starter = matchup_input["starters"][slot]
        with t.subject(slot):
            return {
                "claim": t("critic.command.below_claim", name=starter["name"]),
                "status": "supported",
                "evidence": _command_evidence(t, matchup_input, slot),
            }

    claimed_command = [slot for slot in plus_or_solid if word in said[slot]]
    if not claimed_command and word in said[None]:
        claimed_command = plus_or_solid
    if claimed_command:
        slot = claimed_command[0]
        starter = matchup_input["starters"][slot]
        with t.subject(slot):
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
            "evidence": t("critic.betting.unsupported", flagged=t.join(", ", flagged)),
        }

    return {"claim": claim, "status": "not_present", "evidence": t("critic.betting.absent")}


def _mix_row(matchup_input: dict[str, Any], pitch: str) -> dict[str, Any] | None:
    target = _normalize_pitch(pitch)
    for row in matchup_input["charts"]["pitch_mix"]:
        if _normalize_pitch(row["pitch"]) == target:
            return row
    return None


def _pitch_usage(matchup_input: dict[str, Any], slot: str, pitch: str) -> float:
    """The rounded share the chart shows (display only; decisions use `_pitch_counts`)."""

    row = _mix_row(matchup_input, pitch)
    return float(row[slot]["overall"]) if row else 0


def _row_counts(row: dict[str, Any], slot: str) -> tuple[int, int] | None:
    """(count, total) of a mix row for a starter, or None when the row has no raw counts."""

    count, total = row[slot].get("count"), row[slot].get("total")
    if isinstance(count, int) and isinstance(total, int):
        return count, total
    return None


def _pitch_counts(matchup_input: dict[str, Any], slot: str, pitch: str) -> tuple[int, int] | None:
    row = _mix_row(matchup_input, pitch)
    return _row_counts(row, slot) if row else None


def _was_thrown(usage: float, counts: tuple[int, int] | None) -> bool:
    """A pitch counted at least once was thrown, even if its share rounds to 0.0."""

    return counts[0] > 0 if counts else usage > 0


def _normalize_pitch(pitch: str) -> str:
    value = pitch.lower()
    for token in (labels.FASTBALL_SUFFIX, "-seam"):
        value = value.replace(token, "")
    return value.strip()


def _display_pitch(pitch: str) -> str:
    return pitch.replace(labels.FASTBALL_SUFFIX, "")


def _strength_value(matchup_input: dict[str, Any], dimension: str, slot: str) -> int | None:
    """The 0-100 score, or None when there is no such dimension (never a score of zero)."""

    for row in matchup_input["charts"].get("strength_profile") or []:
        if row["dimension"] == dimension and row.get(slot) is not None:
            return int(row[slot])
    return None


def _report_text(report: dict[str, Any]) -> str:
    return "\n".join(text for _, text in _report_locations(report))


def _report_locations(report: dict[str, Any]) -> list[tuple[str, str]]:
    # The text fields are mandatory: a report that lost them must fail, not pass every text check.
    locations: list[tuple[str, str]] = [("headline", report["headline"])]
    for index, summary in enumerate(report["short_summary"]):
        locations.append((f"short_summary[{index}]", summary))
    for index, section in enumerate(report["sections"]):
        if section.get("body"):
            locations.append((f"sections[{index}].body", section["body"]))
        for bullet_index, bullet in enumerate(section.get("bullets", [])):
            locations.append((f"sections[{index}].bullets[{bullet_index}]", bullet))
    return locations


def _owned_sentences(report: dict[str, Any], matchup_input: dict[str, Any]) -> list[tuple[str | None, str]]:
    """
    Every sentence of the report with the starter it is about, or None when that cannot be told.

    A sentence that names exactly one starter is about him. One that names nobody is about the
    starter in the title of its section, if the title names exactly one. One that names both is
    nobody's alone.
    """

    names = {slot: matchup_input["starters"][slot]["name"] for slot in SLOTS}

    def owner(sentence: str, section_owner: str | None) -> str | None:
        mentioned = [slot for slot in SLOTS if names[slot] in sentence]
        if len(mentioned) == 1:
            return mentioned[0]
        return None if mentioned else section_owner

    def split(text: str, section_owner: str | None) -> list[tuple[str | None, str]]:
        return [(owner(sentence, section_owner), sentence) for sentence in _SENTENCE_BREAK.split(text)]

    owned: list[tuple[str | None, str]] = []
    for text in (report["headline"], *report["short_summary"]):
        owned.extend(split(text, None))
    for section in report["sections"]:
        titled = [slot for slot in SLOTS if names[slot] in section["title"]]
        section_owner = titled[0] if len(titled) == 1 else None
        for text in (section.get("body"), *section.get("bullets", [])):
            if text:
                owned.extend(split(text, section_owner))
    return owned
