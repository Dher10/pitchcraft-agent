"""Sample thresholds, rate labels and data scopes for live starters (D24, PLAN.md P0.5).

The one place that turns counts into labels. Pure Python, no pandas, so the live
pipeline, the generator and the tests all import it without side effects.

Rules (D24):
- A dimension is limited when its sample is below the threshold. A missing number
  counts as limited, never as zero. A limited dimension gets no label.
- Labels come from rates (strikeouts / batters faced, walks / batters faced), never
  from counts, so the same rate gets the same label whatever the innings.
- Contact risk has no rate label: the report shows the home-run count only.
- Every group of figures carries its scope, because the sources do not cover the
  same games (the MLB API's season stats are regular season only; Statcast
  pitches also include postseason games up to the cutoff).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

# D24: minimum sample per dimension.
THRESHOLDS = {"arsenal": 100, "strikeout": 70, "control": 170}
UNITS = {"arsenal": "pitches", "strikeout": "batters faced", "control": "batters faced"}

# Rate bands: rounded quartiles of 2026 starters with 5+ starts
# (docs/thresholds-proposal.md, "Rate bands").
STRIKEOUT_ABOVE_AVERAGE_PCT = 25.0  # at or above
STRIKEOUT_BELOW_AVERAGE_PCT = 18.0  # below
WALK_SOLID_PCT = 7.0  # at or below
WALK_BELOW_AVERAGE_PCT = 10.0  # at or above

SWING_MISS_ABOVE = "Above-average swing-and-miss ability"
SWING_MISS_AVERAGE = "Average swing-and-miss ability"
SWING_MISS_BELOW = "Below-average swing-and-miss ability"
COMMAND_SOLID = "Solid command"
COMMAND_AVERAGE = "Average command"
COMMAND_BELOW = "Below-average command"

ARSENAL_LIMITED_STYLE = "Arsenal data limited"
PITCH_NOT_AVAILABLE = "Not available"
# Words of the data the agents read, not text they write.
FASTBALL_SUFFIX = " fastball"
LEGACY_PLACEHOLDER_LABEL = "see live data"

# A second pitch is called the put-away pitch only above this share of the mix; the
# critic treats the most-used pitch as the primary one above PRIMARY_MIN_USAGE_PCT.
PUTAWAY_MIN_USAGE_PCT = 15
PRIMARY_MIN_USAGE_PCT = 30

# D32: the lineup notes of the analyst ("strike out often", "draws walks", "hits well") and its
# pressure points use these, at or above, on the figure the fan reads on the card.
OFFENSE_K_NOTE_PCT = 23.0
OFFENSE_BB_NOTE_PCT = 9.0
OFFENSE_OPS_STRONG = 0.750  # "hits well against": OPS against the starter's hand, at or above

SCOPE_REGULAR = "regular_season"
SCOPE_REGULAR_POSTSEASON = "regular_and_postseason"
_SCOPE_TEXT = {
    SCOPE_REGULAR: "regular season",
    SCOPE_REGULAR_POSTSEASON: "regular season and postseason",
}


def make_scope(kind: str, through: str) -> dict[str, str]:
    """Which games a group of figures covers: a kind and the last date included."""

    if kind not in _SCOPE_TEXT:
        raise ValueError(f"unknown scope kind {kind!r}")
    return {"kind": kind, "through": through, "label": f"{_SCOPE_TEXT[kind]} through {through}"}


def is_available(value: Any) -> bool:
    """False for None, an empty string and "N/A": nothing may be computed or claimed from them."""

    return value is not None and str(value).strip() not in ("", "N/A")


def pitch_named(pitch: Any) -> bool:
    """True when a profile names a real pitch (not "Not available" or empty)."""

    return is_available(pitch) and str(pitch).strip().lower() != PITCH_NOT_AVAILABLE.lower()


def share_at_least(count: int, total: int, minimum_pct: float) -> bool:
    """
    True when `count` is at least `minimum_pct` percent of `total`, on the raw counts.

    Cross-multiplied, so a share such as 374 / 2500 = 14.96% is below 15 even though the
    chart rounds it to 15.0. A decision is never taken on a rounded figure.
    """

    return total > 0 and count * 100 >= total * minimum_pct


def profile_pitches(pitch_counts: Mapping[str, int]) -> tuple[str, str]:
    """
    (primary pitch, put-away pitch) from pitch counts, on the counts (D30).

    The primary pitch is the most thrown (ties by name, so the order is stable). The put-away pitch is the
    second most thrown, and only from PUTAWAY_MIN_USAGE_PCT of the pitches: a pitch used less is not a
    weapon, and a starter with one pitch has none. Both are PITCH_NOT_AVAILABLE when there is nothing to
    name. The live pipeline and the test of the demo's derivations both call this function.
    """

    ranked = sorted(pitch_counts, key=lambda pitch: (-pitch_counts[pitch], pitch))
    total = sum(pitch_counts.values())
    top = ranked[0] if ranked else PITCH_NOT_AVAILABLE
    second = (
        ranked[1]
        if len(ranked) > 1 and share_at_least(pitch_counts[ranked[1]], total, PUTAWAY_MIN_USAGE_PCT)
        else PITCH_NOT_AVAILABLE
    )
    return top, second


def _below(value: int | None, threshold: int) -> bool:
    return value is None or value < threshold


def build_sample(
    *,
    pitches: int | None,
    arsenal_scope: dict[str, str],
    batters_faced: int | None,
    strikeouts: int | None,
    walks: int | None,
    home_runs: int | None,
    rates_source: str,
    rates_scope: dict[str, str],
) -> dict[str, Any]:
    """
    The sample behind a starter's labels, with the scope of each group of figures that has a figure.

    A group with no figure has no scope (DATA_CONTRACT rule 3): the pitch count is unknown (`None`), or the
    counts are unavailable. A measured zero is a figure: a debut's 0 pitches come from a valid Statcast
    answer and keep the scope of the games they were measured over.
    """

    return {
        "arsenal": {"pitches": pitches, "scope": arsenal_scope if pitches is not None else None},
        "rates": {
            "batters_faced": batters_faced,
            "strikeouts": strikeouts,
            "walks": walks,
            "home_runs": home_runs,
            "source": rates_source,
            "scope": rates_scope if rates_source != "unavailable" else None,
        },
        "limited": {
            "arsenal": _below(pitches, THRESHOLDS["arsenal"]),
            "strikeout": _below(batters_faced, THRESHOLDS["strikeout"]) or strikeouts is None,
            "control": _below(batters_faced, THRESHOLDS["control"]) or walks is None,
        },
        "thresholds": dict(THRESHOLDS),
    }


def strikeout_label(sample: dict[str, Any]) -> str | None:
    if sample["limited"]["strikeout"]:
        return None
    rates = sample["rates"]
    # Cross-multiplied so a band edge such as 14/200 = 7.0% is not lost to float rounding.
    scaled = rates["strikeouts"] * 100
    batters = rates["batters_faced"]
    if scaled >= STRIKEOUT_ABOVE_AVERAGE_PCT * batters:
        return SWING_MISS_ABOVE
    if scaled < STRIKEOUT_BELOW_AVERAGE_PCT * batters:
        return SWING_MISS_BELOW
    return SWING_MISS_AVERAGE


def control_label(sample: dict[str, Any]) -> str | None:
    if sample["limited"]["control"]:
        return None
    rates = sample["rates"]
    scaled = rates["walks"] * 100
    batters = rates["batters_faced"]
    if scaled <= WALK_SOLID_PCT * batters:
        return COMMAND_SOLID
    if scaled >= WALK_BELOW_AVERAGE_PCT * batters:
        return COMMAND_BELOW
    return COMMAND_AVERAGE


def apply_profile_labels(profile: dict[str, Any], sample: dict[str, Any]) -> None:
    """Set the rate-based labels on a pitching profile (None where limited)."""

    profile["swing_miss_label"] = strikeout_label(sample)
    profile["command_label"] = control_label(sample)
    profile["contact_risk_label"] = None
    if sample["limited"]["arsenal"]:
        profile["style_label"] = ARSENAL_LIMITED_STYLE


# The family of each mapped pitch (the colour and copy of the movement chart). A documented derivation from
# the pitch name (DATA_CONTRACT.md, rule 1): a name this table does not have has no family.
PITCH_FAMILY = {
    "Four-seam": "Fastball",
    "Sinker": "Fastball",
    "Cutter": "Fastball",
    "Slider": "Breaking",
    "Curveball": "Breaking",
    "Sweeper": "Breaking",
    "Slurve": "Breaking",
    "Changeup": "Offspeed",
    "Splitter": "Offspeed",
    "Forkball": "Offspeed",
    "Knuckleball": "Offspeed",
    "Screwball": "Offspeed",
    "Eephus": "Offspeed",
}

SEASON_RATE_FIELDS = ("era", "whip", "innings")


def figure_scopes(starter: dict[str, Any]) -> dict[str, dict[str, str]]:
    """
    The scope of every group of figures a live starter really has (QA4-01), by group:

    - "pitch_data": pitch mix, velocity, movement (Statcast); only when pitches were counted.
    - "season_rates": ERA, WHIP and innings (the MLB API, regular season only); only when one is available.
    - "counts": batters faced, strikeouts, walks, home runs, from whichever source gave them; none if
      the source is "unavailable".

    A group without figures has no scope: it can neither differ from the others nor be claimed.
    The analyst, the writer, the critic, the validator and the card all read the scopes from here.
    A starter without a sample (the demo's) has none.
    """

    sample = starter.get("sample")
    if not isinstance(sample, dict):
        return {}
    summary = starter.get("season_summary") or {}
    scopes = summary.get("scopes") or {}
    found: dict[str, dict[str, str]] = {}
    if sample["arsenal"]["pitches"]:
        found["pitch_data"] = sample["arsenal"]["scope"]
    if scopes.get("season_rates") and any(is_available(summary.get(key)) for key in SEASON_RATE_FIELDS):
        found["season_rates"] = scopes["season_rates"]
    if scopes.get("counts") and sample["rates"]["source"] != "unavailable":
        found["counts"] = scopes["counts"]
    return found


def team_label(abbreviation: str | None, name: str) -> str:
    """How a team is written where there is room for an abbreviation: the abbreviation, or the name when it has none (F7)."""

    return abbreviation or name


def has_pitch_data(starter: dict[str, Any]) -> bool:
    """True when a live starter has a pitch on record (the group `pitch_data` of `figure_scopes`); a zero or an unknown count is none."""

    return "pitch_data" in figure_scopes(starter)


OFFENSE_FIGURES = ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand")


def has_offense_figure(offense: dict[str, Any]) -> bool:
    """True when a lineup has an OPS, a K% or a BB% against the hand it faces: the lineup has a split (and a scope)."""

    return any(offense.get(key) is not None for key in OFFENSE_FIGURES)


def scopes_differ(starter: dict[str, Any]) -> bool:
    """True when the groups of figures a starter has do not all cover the same games."""

    return len({scope["kind"] for scope in figure_scopes(starter).values()}) > 1
