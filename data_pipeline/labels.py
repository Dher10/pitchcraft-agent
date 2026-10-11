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

# A second pitch is called the put-away pitch only above this share of the mix; the
# critic treats the most-used pitch as the primary one above PRIMARY_MIN_USAGE_PCT.
PUTAWAY_MIN_USAGE_PCT = 15
PRIMARY_MIN_USAGE_PCT = 30

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
    """The sample behind a starter's labels, with the scope of each group of figures."""

    return {
        "arsenal": {"pitches": pitches, "scope": arsenal_scope},
        "rates": {
            "batters_faced": batters_faced,
            "strikeouts": strikeouts,
            "walks": walks,
            "home_runs": home_runs,
            "source": rates_source,
            "scope": rates_scope,
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


def scopes_differ(sample: dict[str, Any]) -> bool:
    """True when the pitch data and the season rates do not cover the same games."""

    return sample["arsenal"]["scope"]["kind"] != sample["rates"]["scope"]["kind"]
