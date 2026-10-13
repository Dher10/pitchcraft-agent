"""The sentences the generator itself writes (workflow, data label, live confidence note).

Like the agents' sentences, each one has a key and is written through a `Catalog`, so it is a
`Phrase` that the claims check can record (contract rule 4, `docs/DATA_CONTRACT.md` section 3.2).
They stay in English and outside the agents' catalog until v2.1 (decision D31); the only change is
that they are now keyed templates instead of f-strings.
"""

from __future__ import annotations

from typing import Any

from agents.language import DEFAULT_LANGUAGE, Catalog

GENERATOR_MESSAGES: dict[str, Any] = {
    "generator.workflow.description": (
        "PitchCraft uses a multi-agent workflow to convert matchup data into a fan-facing scouting report."
    ),
    "generator.workflow.loaded": "Loaded cached data for {count} matchups.",
    "generator.workflow.identified": "Identified pitcher strengths, risks, and lineup pressure points.",
    "generator.workflow.generated": "Generated fan-friendly scouting report.",
    "generator.workflow.checked": (
        "Checked every claim against the data: none unsupported, {warnings} warning(s) across all matchups."
    ),
    "generator.workflow.graded": "Graded {count} completed starter(s) with Bill James Game Score.",
    "generator.workflow.graded_none": "Featured game has not been completed.",
    "generator.metadata.last_updated.live": "Live data fetched {date}",
    "generator.metadata.last_updated.fallback": "Live data unavailable; showing demo data",
    "generator.metadata.last_updated.demo": "Demo data generated for capstone submission",
    "generator.confidence.live_note": "Live snapshot fetched {date} for {matchup_id}.",
}

GENERATOR_PREFIX = "generator."


def generator_catalog() -> Catalog:
    """The catalog of the generator's sentences (English only, see the module docstring)."""

    return Catalog(DEFAULT_LANGUAGE, GENERATOR_MESSAGES)
