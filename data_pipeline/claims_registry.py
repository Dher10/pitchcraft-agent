"""The registry of claims: what must be true of the payload for each sentence to be written (contract rule 4).

This is the machine form of sections 3.1, 3.2 and 3.5 of `docs/DATA_CONTRACT.md`. Every key of the
catalogs (the agents' and the generator's) either has a rule here (a function of the claim, its
arguments and the payload) or is listed in `ASSERTS_NOTHING`. `tests/test_claims_registry.py` fails if
a key is in neither, if an entry matches no key, or if this module and the contract differ.

A rule returns nothing; it records what is false with `Ctx.require`. Each failure has a reason, and
the violation code is `<key>#<reason>` (see `data_pipeline/contract_checks.py`). The conditions are
written as the contract states them: a sentence written without its condition holding is a violation.
Every violation reported by these checks stops publication (no tolerance since P0.15-D2.5c).
This is not proof of detection completeness: source conservation and frontend phrases also need
their own tests, and the remaining semantic-negative coverage gaps are listed in STATUS.md.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from fnmatch import fnmatchcase
import re
from typing import Any

from agents.language import SUBJECT_SLOTS, Catalog
from data_pipeline import labels
from data_pipeline import series as series_vocab
from data_pipeline import report_facts as facts
from data_pipeline.claims import render_text
from data_pipeline.schema import STATE_OF_STATUS, new_york_day

LIVE_LEVEL = "fetched_snapshot"
FACING = {"away_starter": "home", "home_starter": "away"}  # the lineup a starter faces
SCOPE_GROUPS_OF_FIGURE = {
    "analyst.figure.era": "season_rates",
    "analyst.figure.whip": "season_rates",
    "analyst.figure.innings": "season_rates",
    "analyst.figure.counts": "counts",
    "analyst.figure.pitch_data": "pitch_data",
}
SEASON_GROUPS = ("season_rates", "counts")


@dataclass(frozen=True)
class Fail:
    """One thing that is false: a short reason (part of the violation code) and a message."""

    reason: str
    message: str


class _Abort(Exception):
    """The rest of the rule cannot be evaluated (something it needs is missing)."""


# --- an index of the claims of one list ----------------------------------------------------------


class ClaimIndex:
    """The claims of one list (a matchup's, or the root's): their text, their parents and their locations."""

    def __init__(self, claims: list[dict[str, Any]], catalogs: tuple[Catalog, Catalog]) -> None:
        self.catalogs = catalogs
        self.by_id: dict[str, dict[str, Any]] = {claim["id"]: claim for claim in claims}
        self.parents: dict[str, list[str]] = defaultdict(list)
        self.by_location: dict[str, dict[str, Any]] = {}
        self._texts: dict[str, str | None] = {}
        for claim in claims:
            for ref in _refs(claim["args"].values()):
                self.parents[ref].append(claim["id"])
            if isinstance(claim["location"], str):
                self.by_location[claim["location"]] = claim

    def text(self, claim_id: str) -> str | None:
        if claim_id not in self._texts:
            self._texts[claim_id] = None  # guards a cycle
            claim = self.by_id.get(claim_id)
            if claim is not None:
                args = {name: self.resolve(value) for name, value in claim["args"].items()}
                self._texts[claim_id] = render_text(claim["key"], args, self.catalogs)
        return self._texts[claim_id]

    def resolve(self, value: Any) -> Any:
        if isinstance(value, Mapping) and set(value) == {"claim"}:
            return self.text(value["claim"])
        if isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value

    def ancestors(self, claim_id: str) -> Iterator[dict[str, Any]]:
        """The claims that contain this one, nearest first."""

        seen: set[str] = set()
        queue = list(self.parents.get(claim_id, ()))
        while queue:
            parent = queue.pop(0)
            if parent in seen:
                continue
            seen.add(parent)
            yield self.by_id[parent]
            queue.extend(self.parents.get(parent, ()))

    def descendants(self, claim_id: str) -> Iterator[dict[str, Any]]:
        """The claims this one is made of (itself excluded)."""

        for ref in _refs(self.by_id[claim_id]["args"].values()):
            if ref in self.by_id:
                yield self.by_id[ref]
                yield from self.descendants(ref)


def _refs(values: Any) -> Iterator[str]:
    for value in values:
        if isinstance(value, Mapping) and set(value) == {"claim"}:
            yield value["claim"]
        elif isinstance(value, list):
            yield from _refs(value)


# --- the context a rule sees ---------------------------------------------------------------------


class Ctx:
    """One claim, its arguments and the payload around it."""

    def __init__(
        self,
        payload: Mapping[str, Any],
        matchup: Mapping[str, Any] | None,
        claim: Mapping[str, Any],
        index: ClaimIndex,
        shared: dict[str, Any],
    ) -> None:
        self.payload = payload
        self.matchup = matchup
        self.claim = claim
        self.key: str = claim["key"]
        self.args: Mapping[str, Any] = claim["args"]
        self.index = index
        self.shared = shared
        self.fails: list[Fail] = []

    # --- arguments
    def text(self, name: str) -> Any:
        """The argument, with a reference replaced by the text of the claim it points to."""

        return self.index.resolve(self.args[name])

    def ref(self, name: str) -> Mapping[str, Any]:
        value = self.args.get(name)
        if not (isinstance(value, Mapping) and set(value) == {"claim"}):
            self.fail("argument", f"argument {name!r} is not a reference to a claim")
            raise _Abort
        return self.index.by_id[value["claim"]]

    def count(self, name: str) -> Any:
        """The number inside a counted noun ("3 home runs") given as a reference."""

        return self.ref(name)["args"].get("count")

    # --- verdicts
    def fail(self, reason: str, message: str) -> None:
        self.fails.append(Fail(reason, message))

    def require(self, condition: Any, reason: str, message: str) -> bool:
        if not condition:
            self.fail(reason, message)
        return bool(condition)

    # --- the world of the claim
    @property
    def live(self) -> bool:
        return self.matchup is not None and (self.matchup.get("data_confidence") or {}).get("level") == LIVE_LEVEL

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self.payload.get("metadata") or {}

    @property
    def slot(self) -> str:
        subject = self.claim["subject"]
        if self.matchup is None or subject not in SUBJECT_SLOTS:
            self.fail("subject", "the sentence is about a starter but records none")
            raise _Abort
        return subject

    @property
    def starter(self) -> Mapping[str, Any]:
        return self.matchup["starters"][self.slot]  # type: ignore[index]

    @property
    def other(self) -> Mapping[str, Any]:
        return self.matchup["starters"][other_slot(self.slot)]  # type: ignore[index]

    @property
    def lineup(self) -> Mapping[str, Any]:
        """The offense of the lineup the starter faces."""

        return self.matchup["teams"][FACING[self.slot]]["offense_profile"]  # type: ignore[index]

    @property
    def state(self) -> str | None:
        """The state of the game (Preview, Live, Final), or None when it is not known.

        The published `status` is the schedule's state through one table (`schema.GAME_STATUS`): `upcoming` is Preview,
        `live` is Live, `final` is Final, `null` is unknown (F5, closed in P0.15-D2.5a). A demo matchup declares the same.
        """

        status = (self.matchup or {}).get("status")
        return STATE_OF_STATUS.get(status) if isinstance(status, str) else None

    def who(self) -> list[Mapping[str, Any]]:
        """The starters a scope note is about: the ones named in the `who` of this claim or of its nearest ancestor."""

        for claim in (self.claim, *self.index.ancestors(self.claim["id"])):
            if "who" in claim["args"]:
                text = self.index.resolve(claim["args"]["who"])
                found = [s for s in (self.matchup or {}).get("starters", {}).values() if s["name"] in str(text)]
                if found:
                    return found
        self.fail("who", "the starters the note is about cannot be told from the sentence")
        raise _Abort

    def descendant_keys(self, name: str) -> set[str]:
        value = self.args[name]
        if isinstance(value, Mapping) and "claim" in value:
            claim = self.index.by_id[value["claim"]]
            return {claim["key"], *(d["key"] for d in self.index.descendants(claim["id"]))}
        return set()


def other_slot(slot: str) -> str:
    return SUBJECT_SLOTS[1] if slot == SUBJECT_SLOTS[0] else SUBJECT_SLOTS[0]


# --- reading the data ----------------------------------------------------------------------------


def _sample(starter: Mapping[str, Any]) -> Mapping[str, Any] | None:
    sample = starter.get("sample")
    return sample if isinstance(sample, Mapping) else None


def _unspoken(starter: Mapping[str, Any]) -> bool:
    """True when no sentence may describe his arsenal: a small sample (D24) or a lead pitch with no name (F6e)."""

    return labels.arsenal_unspoken(dict(starter))


def _limited(starter: Mapping[str, Any], dimension: str) -> bool:
    sample = _sample(starter)
    return bool(sample and sample["limited"][dimension])


def _profile(starter: Mapping[str, Any]) -> Mapping[str, Any]:
    return starter["pitching_profile"]


def _label(starter: Mapping[str, Any], name: str) -> str:
    return str(_profile(starter).get(name) or "").lower()


def _percent(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("%", ""))
    except ValueError:
        return None


def _short(pitch: Any) -> str:
    """How a sentence says a pitch: lower case, without the word fastball."""

    return re.sub(r"(?i) fastball$", "", str(pitch).strip()).lower()


def _mix_name(pitch: Any) -> str:
    value = str(pitch).lower()
    for token in (labels.FASTBALL_SUFFIX, "-seam"):
        value = value.replace(token, "")
    return value.strip()


def _mix_row(matchup: Mapping[str, Any], pitch: Any) -> Mapping[str, Any] | None:
    target = _mix_name(pitch)
    return next((row for row in matchup["charts"]["pitch_mix"] if _mix_name(row["pitch"]) == target), None)


def _pitched_slots(matchup: Mapping[str, Any]) -> list[str]:
    """The starters that have pitch data (a counted pitch), in the order away, home."""

    return [slot for slot in SUBJECT_SLOTS if labels.has_pitch_data(matchup["starters"][slot])]


def _split_sides(matchup: Mapping[str, Any]) -> list[str]:
    """The lineups that have a split (an OPS, a K% or a BB%), in the order away, home."""

    return [side for side in ("away", "home") if labels.has_offense_figure(matchup["teams"][side]["offense_profile"])]


def _expected_strengths(starter: Mapping[str, Any]) -> list[str]:
    """The strengths the labels of a starter support, first one first, as keys (or the key prefix of the style)."""

    swing, command = _label(starter, "swing_miss_label"), _label(starter, "command_label")
    found: list[str] = []
    if _sample(starter) is not None:  # a live starter: only labels that cleared their sample
        if "above-average" in swing:
            found.append("analyst.strength.swing_miss")
        if "solid" in command:
            found.append("analyst.strength.command")
        if not _unspoken(starter):
            found.append("analyst.style.")
        return found
    contact = _label(starter, "contact_risk_label")
    recent = str((starter.get("recent_form") or {}).get("label") or "").lower()
    if "above-average" in swing:
        found.append("analyst.strength.swing_miss")
    if "plus" in command or "solid" in command:
        found.append("analyst.strength.command")
    if "low" in contact:
        found.append("analyst.strength.contact")
    if "trending" in recent:
        found.append("analyst.strength.trending")
    found.append("analyst.style.")
    return found


# --- agent phrases: headline, style, reads -------------------------------------------------------


def _summary(c: Ctx) -> None:
    c.require(c.text("label") == c.matchup["report"]["headline"], "label", "the label is not the headline of the report")  # type: ignore[index]


def _label_against(c: Ctx) -> None:
    away, home = (c.matchup["starters"][slot] for slot in SUBJECT_SLOTS)  # type: ignore[index]
    if _unspoken(away) or _unspoken(home):
        expected = (away["name"], home["name"])
    else:
        expected = (_profile(away)["style_label"], _profile(home)["style_label"])
    c.require((c.text("away"), c.text("home")) == expected, "pair", f"expected {expected!r}")


def _style(c: Ctx) -> None:
    starter, profile = c.starter, _profile(c.starter)
    named = labels.pitch_named
    c.require(not _unspoken(starter), "limited_arsenal", "the arsenal is limited or has an unnamed lead pitch")
    c.require(named(profile["primary_pitch"]), "pitch", "the primary pitch is not named")
    c.require(c.text("primary") == profile["primary_pitch"], "pitch", "the primary pitch is not his")
    if c.key.endswith(".pair"):
        c.require(named(profile["putaway_pitch"]), "pitch", "the put-away pitch is not named")
        c.require(c.text("putaway") == profile["putaway_pitch"], "pitch", "the put-away pitch is not his")
    else:
        c.require(not named(profile["putaway_pitch"]), "pitch", "he has a put-away pitch")


def _share(cell: Mapping[str, Any]) -> float | None:
    """The share of a mix cell, or None when it is unknown (a starter who threw nothing has no share, F20)."""

    overall = cell.get("overall")
    return None if overall is None else float(overall)


def _thrown_share(matchup: Mapping[str, Any], slot: str, pitch: Any, minimum: float) -> tuple[bool, bool]:
    """(thrown, at least `minimum` percent), on the raw counts when the row has them."""

    row = _mix_row(matchup, pitch)
    if row is None:
        return False, False
    cell = row[slot]
    count, total = cell.get("count"), cell.get("total")
    if isinstance(count, int) and isinstance(total, int):
        return count > 0, labels.share_at_least(count, total, minimum)
    overall = _share(cell)
    return (overall or 0) > 0, (overall or 0) >= minimum


def _combination(c: Ctx) -> None:
    starter, profile = c.starter, _profile(c.starter)
    c.require(not _unspoken(starter), "limited_arsenal", "the arsenal is limited or has an unnamed lead pitch")
    primary_ok = labels.pitch_named(profile["primary_pitch"]) and c.text("primary") == _short(profile["primary_pitch"])
    c.require(primary_ok, "pitch", "the primary pitch is not his")
    put_ok = labels.pitch_named(profile["putaway_pitch"]) and c.text("putaway") == _short(profile["putaway_pitch"])
    c.require(put_ok, "pitch", "the put-away pitch is not his")
    c.require(c.text("name") == starter["name"], "name", "the sentence is about another starter")
    if put_ok and primary_ok:
        thrown = _thrown_share(c.matchup, c.slot, profile["primary_pitch"], 0)[0]  # type: ignore[arg-type]
        _, enough = _thrown_share(c.matchup, c.slot, profile["putaway_pitch"], labels.PUTAWAY_MIN_USAGE_PCT)  # type: ignore[arg-type]
        c.require(thrown, "thrown", "the primary pitch was not thrown")
        c.require(enough, "putaway_share", "the put-away pitch is under 15% of his pitches")


def _mainly(c: Ctx) -> None:
    starter, profile = c.starter, _profile(c.starter)
    c.require(not _unspoken(starter), "limited_arsenal", "the arsenal is limited or has an unnamed lead pitch")
    c.require(labels.pitch_named(profile["primary_pitch"]), "pitch", "the primary pitch is not named")
    c.require(not labels.pitch_named(profile["putaway_pitch"]), "pitch", "he has a put-away pitch")
    c.require(c.text("primary") == _short(profile["primary_pitch"]), "pitch", "the primary pitch is not his")


def _shows(c: Ctx) -> None:
    starter = c.starter
    label = c.text("label")
    options = []
    for name, dimension in (("swing_miss_label", "strikeout"), ("command_label", "control")):
        value = _profile(starter).get(name)
        if value and not _limited(starter, dimension):
            options.append(value[:1].lower() + value[1:])
    c.require(label in options, "label", f"{label!r} is not a rate label of his that cleared its sample")


def _qualifier(c: Ctx) -> None:
    starter = c.starter
    counts = labels.figure_scopes(starter).get("counts")
    c.require(counts is not None and labels.scopes_differ(starter), "groups_agree", "his groups of figures cover the same games")
    if counts is not None:
        both = c.key.endswith("qualifier_both")
        c.require((counts["kind"] == labels.SCOPE_REGULAR_POSTSEASON) == both, "scope", "the qualifier is not the scope of his counts")


# --- agent phrases: what the data has -----------------------------------------------------------


def _have_pitches(c: Ctx) -> None:
    pitches = ((_sample(c.starter) or {}).get("arsenal") or {}).get("pitches")
    c.require(pitches is not None and c.args["count"] == pitches, "count", "the count is not his pitch count")


def _have_no_pitches(c: Ctx) -> None:
    pitches = ((_sample(c.starter) or {}).get("arsenal") or {}).get("pitches")
    c.require(pitches == 0, "unknown_not_zero", "his pitch count is not a measured zero")


def _have_pitches_unavailable(c: Ctx) -> None:
    pitches = ((_sample(c.starter) or {}).get("arsenal") or {}).get("pitches")
    c.require(pitches is None, "known", "his pitch count is known")


def _have_batters_unavailable(c: Ctx) -> None:
    batters = ((_sample(c.starter) or {}).get("rates") or {}).get("batters_faced")
    c.require(batters is None, "known", "his batters faced is known")


def _have_batters(c: Ctx) -> None:
    batters = ((_sample(c.starter) or {}).get("rates") or {}).get("batters_faced")
    c.require(batters is not None and c.args["count"] == batters, "count", "the count is not his batters faced")


def _have_no_batters(c: Ctx) -> None:
    rates = (_sample(c.starter) or {}).get("rates") or {}
    c.require(
        rates.get("batters_faced") == 0 and rates.get("source") != "unavailable",
        "unknown_not_zero",
        "his batters faced is not a measured zero",
    )


def _data_limited(c: Ctx) -> None:
    starter, dimension = c.starter, c.key.rsplit(".", 1)[1]
    sample = _sample(starter)
    c.require(sample is not None and sample["limited"][dimension], "not_limited", f"his {dimension} data is not limited")
    c.require(c.text("name") == starter["name"], "name", "the sentence is about another starter")
    if sample is not None:
        c.require(c.args["needed"] == sample["thresholds"][dimension], "threshold", "the threshold is not the sample's")


def _data_contact(c: Ctx) -> None:
    rates = (_sample(c.starter) or {}).get("rates") or {}
    c.require(rates.get("home_runs") is not None and (rates.get("batters_faced") or 0) > 0, "unknown", "his home runs or batters faced are unknown")
    c.require(c.count("home_runs") == rates.get("home_runs"), "count", "the home runs are not his")
    c.require(c.args["batters"] == rates.get("batters_faced"), "count", "the batters are not his")


def _data_arsenal_unnamed(c: Ctx) -> None:
    """The sentence says why a starter with enough pitches is not described: his lead pitch has no name (F6e)."""

    c.require(labels.arsenal_unnamed(dict(c.starter)), "named", "his lead pitch is named, or his arsenal is limited")
    c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")


def _data_no_home_runs(c: Ctx) -> None:
    rates = (_sample(c.starter) or {}).get("rates") or {}
    c.require(rates.get("home_runs") is None or not rates.get("batters_faced"), "known", "his home runs are known")


# --- agent phrases: strengths and risks ----------------------------------------------------------


def _strength_swing(c: Ctx) -> None:
    starter = c.starter
    c.require("above-average" in _label(starter, "swing_miss_label"), "label", "his strikeout label is not above average")
    c.require(not _limited(starter, "strikeout"), "limited", "his strikeout data is limited")


def _strength_command(c: Ctx) -> None:
    starter = c.starter
    label = _profile(starter).get("command_label")
    c.require(c.text("label") == label, "label", "the label is not his command label")
    c.require("plus" in str(label).lower() or "solid" in str(label).lower(), "label", "his command is not solid or plus")
    c.require(not _limited(starter, "control"), "limited", "his control data is limited")


def _strength_contact(c: Ctx) -> None:
    c.require("low" in _label(c.starter, "contact_risk_label"), "label", "his contact risk is not low")


def _recent(c: Ctx, word: str) -> None:
    label = str((c.starter.get("recent_form") or {}).get("label") or "").lower()
    c.require(word in label, "label", f"his recent form is not {word}")


def _strength_trending(c: Ctx) -> None:
    _recent(c, "trending")


def _risk_command(c: Ctx) -> None:
    c.require("below-average" in _label(c.starter, "command_label"), "label", "his command is not below average")
    c.require(not _limited(c.starter, "control"), "limited", "his control data is limited")


def _risk_contact(c: Ctx) -> None:
    label = _label(c.starter, "contact_risk_label")
    c.require("elevated" in label or "high" in label, "label", "his contact risk is not elevated")


def _risk_volatile(c: Ctx) -> None:
    _recent(c, "volatile")


def _internal(c: Ctx) -> None:
    c.fail("published", "an internal finding is part of the published text")


# --- agent phrases: the lineup -------------------------------------------------------------------


def _hand_is_his(c: Ctx) -> None:
    throws = c.starter.get("throws")
    expected = f"{throws}HP" if throws in ("L", "R") else None
    c.require(expected is not None and c.text("hand") == expected, "hand", f"the hand {c.text('hand')!r} is not the hand he throws with")


def _offense_no_hand(c: Ctx) -> None:
    throws = c.starter.get("throws")
    c.require(throws not in ("L", "R"), "hand", f"he throws with {throws!r}, a hand the lineup read can name")


def _offense_unavailable(c: Ctx) -> None:
    c.require(_percent(c.lineup.get("ops_vs_hand")) is None, "known", "the lineup's OPS against his hand is known")
    _hand_is_his(c)


def _offense_read(c: Ctx) -> None:
    ops = _percent(c.lineup.get("ops_vs_hand"))
    c.require(c.lineup.get("ops_vs_hand") is not None and c.text("ops") == c.lineup.get("ops_vs_hand"), "ops", "the OPS is not the lineup's")
    _hand_is_his(c)
    if ops is None:
        return
    band = c.key.rsplit(".", 1)[1]
    actual = "strong" if ops >= labels.OFFENSE_OPS_STRONG else "average" if ops >= 0.700 else "weak"
    c.require(band == actual, "band", f"the lineup's OPS {ops} is {actual}, not {band}")
    if "name" in c.args:
        c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")


def _offense_note(c: Ctx) -> None:
    field, minimum = (
        ("k_rate_vs_hand", labels.OFFENSE_K_NOTE_PCT)
        if c.key.endswith("strikeouts")
        else ("bb_rate_vs_hand", labels.OFFENSE_BB_NOTE_PCT)
    )
    rate = _percent(c.lineup.get(field))
    c.require(rate is not None and rate >= minimum, "rate", f"the lineup's {field} is not at least {minimum}")
    if "name" in c.args:
        c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")


# --- agent phrases: scope notes ------------------------------------------------------------------


def _scope_labels(starter: Mapping[str, Any], groups: tuple[str, ...]) -> set[str]:
    scopes = labels.figure_scopes(starter)
    return {scopes[g]["label"] for g in groups if g in scopes}


def _scope_same(c: Ctx) -> None:
    for starter in c.who():
        scopes = labels.figure_scopes(starter)
        c.require(bool(scopes) and not labels.scopes_differ(starter), "groups", f"{starter['name']}'s groups differ or he has none")
        if scopes:
            c.require(c.text("label") == next(iter(scopes.values()))["label"], "label", "the label is not the scope of his figures")


def _scope_none(c: Ctx) -> None:
    for starter in c.who():
        c.require(not labels.figure_scopes(starter), "has_figures", f"{starter['name']} has figures")


def _scope_differ(c: Ctx) -> None:
    for starter in c.who():
        scopes = labels.figure_scopes(starter)
        c.require(labels.scopes_differ(starter), "groups", f"{starter['name']}'s groups cover the same games")
        c.require("pitch_data" in scopes and c.text("arsenal") == scopes.get("pitch_data", {}).get("label"), "label", "the arsenal label is not the scope of his pitch data")


def _scope_groups(c: Ctx) -> None:
    for starter in c.who():
        c.require(labels.scopes_differ(starter), "groups", f"{starter['name']}'s groups cover the same games")


def _scope_part(c: Ctx) -> None:
    """A part of a scope note ("ERA and WHIP cover the regular season through D")."""

    for starter in c.who():
        scopes = labels.figure_scopes(starter)
        if c.key == "analyst.scope.no_season_figures":
            c.require(not any(g in scopes for g in SEASON_GROUPS) and "pitch_data" in scopes, "has_figures", f"{starter['name']} has season figures or no pitch data")
            continue
        groups = {SCOPE_GROUPS_OF_FIGURE[k] for k in c.descendant_keys("figures") if k in SCOPE_GROUPS_OF_FIGURE}
        c.require(bool(groups) and all(g in scopes for g in groups), "figures", f"{starter['name']} lacks a group the sentence names")
        c.require(all(scopes[g]["label"] == c.text("label") for g in groups if g in scopes), "label", "the label is not the scope of the figures")


def _series_sentence(c: Ctx) -> None:
    """
    `analyst.series.standing` and `.opening`: the matchup has this series, and the numbers are the matchup's own.

    The opening sentence says the series has not started, which is true only before the game: it needs the game to be
    known as Preview (QA1-01). The standing sentence needs no state: it is framed "Before first pitch", and the standing is
    the one as of the day before the game (D29), so it is true in every state, an unknown one included.
    """

    series = (c.matchup or {}).get("series")
    if not c.require(isinstance(series, Mapping), "series", "the matchup has no series"):
        return
    c.require(
        c.args["series_name"] == series["series_name"] and series_vocab.series_name(series["series_name"]) is not None,
        "name",
        "the series name is not the matchup's, or is not one the code knows",
    )
    number = series["game_number"]
    length = series["games_in_series"]
    c.require(
        isinstance(number, int)
        and not isinstance(number, bool)
        and 1 <= number <= series_vocab.MAX_GAMES
        and (length is None or number <= length),
        "game_number",
        "no series has a game with this number",
    )
    if c.key.endswith(".opening"):
        c.require(number == 1, "game_number", "the sentence says the series has not started, but this is not game 1")
        _preview(c, "the sentence says the series has not started, and it")
        return
    c.require(c.args["n"] == number and number >= 2, "game_number", "the game number is not the matchup's, or is the first")
    standing = series["standing"]
    c.require(
        standing is not None
        and c.args["result"] == series_vocab.in_sentence(standing)
        and series_vocab.standing(standing, number, series["games_in_series"]) == standing,
        "standing",
        "the standing is not the matchup's, or cannot be true before this game",
    )


def _scope_offense(c: Ctx) -> None:
    label = c.text("label")
    teams = [
        team["offense_profile"]
        for team in c.matchup["teams"].values()  # type: ignore[index]
        if (team["offense_profile"].get("scope") or {}).get("label") == label
    ]
    c.require(bool(teams), "label", "no lineup has this scope")
    for offense in teams:
        has = any(offense.get(f) is not None for f in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand"))
        c.require(has, "no_offense_figure", "the scope is claimed for a lineup with no offense figure")


# --- report writer -------------------------------------------------------------------------------


def _writer_strength(c: Ctx) -> None:
    starter = c.starter
    c.require(c.text("name") == starter["name"], "name", "the sentence is about another starter")
    expected = _expected_strengths(starter)
    key = c.ref("strength")["key"]
    c.require(
        bool(expected) and key.startswith(expected[0]) or (not expected and key == "writer.default_strength"),
        "first",
        f"the strength is {key}, the first the labels support is {expected[:1]}",
    )


def _writer_strength_none(c: Ctx) -> None:
    starter = c.starter
    c.require(_sample(starter) is not None and not _expected_strengths(starter), "has_strength", "the labels support a strength")
    c.require(c.text("name") == starter["name"], "name", "the sentence is about another starter")


def _arsenal_contrast(c: Ctx) -> None:
    starters = [c.matchup["starters"][slot] for slot in SUBJECT_SLOTS]  # type: ignore[index]
    c.require(not any(_unspoken(s) for s in starters), "limited_arsenal", "an arsenal is limited or has an unnamed lead pitch")
    for prefix, starter in zip(("away", "home"), starters):
        c.require(c.text(f"{prefix}_primary") == _profile(starter)["primary_pitch"], "pitch", f"the {prefix} primary pitch is not his")
        c.require(c.ref(f"{prefix}_style")["key"].startswith("analyst.style."), "style", f"the {prefix} style is not a style sentence")


def _arsenal_works_off(c: Ctx) -> None:
    c.require(not _unspoken(c.starter), "limited_arsenal", "his arsenal is limited or has an unnamed lead pitch")
    c.require(c.ref("style")["key"].startswith("analyst.style."), "style", "the style is not a style sentence")
    c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")


def _arsenal_no_contrast(c: Ctx) -> None:
    starters = c.matchup["starters"].values()  # type: ignore[union-attr]
    c.require(any(_limited(s, "arsenal") for s in starters), "no_limit", "no arsenal is limited")


def _arsenal_no_contrast_unnamed(c: Ctx) -> None:
    """The contrast is missing because a starter's lead pitch has no name, and no arsenal is limited (that is the other sentence)."""

    starters = c.matchup["starters"].values()  # type: ignore[union-attr]
    c.require(not any(_limited(s, "arsenal") for s in starters), "limited", "an arsenal is limited: the sentence about too little data is the one")
    c.require(any(labels.arsenal_unnamed(dict(s)) for s in starters), "unnamed", "no starter has a lead pitch without a name")


def _confidence_limited(c: Ctx) -> None:
    starters = c.matchup["starters"].values()  # type: ignore[union-attr]
    c.require(any(any((_sample(s) or {}).get("limited", {}).values()) for s in starters), "no_limit", "no dimension is limited")


def _preview(c: Ctx, what: str) -> None:
    c.require(c.state == "Preview", "game_state", f"{what} needs the game to be known as Preview; its state is {c.state!r}")


def _confidence_snapshot(c: Ctx) -> None:
    c.require(c.live, "not_live", "the matchup is not live")


def _item_pitch_data(c: Ctx) -> None:
    """The list names Statcast pitch data only when BOTH starters have a pitch on record."""

    c.require(c.live, "not_live", "the matchup is not live")
    c.require(len(_pitched_slots(c.matchup)) == 2, "pitch_data", "a starter has no pitch data, the list says Statcast pitch data")  # type: ignore[arg-type]


def _item_offense(c: Ctx) -> None:
    """The list names season offense splits only when BOTH lineups have a split."""

    c.require(c.live, "not_live", "the matchup is not live")
    c.require(len(_split_sides(c.matchup)) == 2, "offense", "a lineup has no split, the list says season offense splits")  # type: ignore[arg-type]


def _confidence_lineups(c: Ctx) -> None:
    c.require(c.live, "not_live", "the matchup is not live")
    _preview(c, "'before first pitch'")


def _confidence_pitch_data(c: Ctx) -> None:
    """
    What is said of missing pitch data: `one` (the one named has it, the other does not) or `none`. The
    consequence is checked on the report: no sentence names a pitch for a starter without pitch data.
    """

    matchup = c.matchup
    c.require(c.live, "not_live", "the matchup is not live")
    pitched = _pitched_slots(matchup)  # type: ignore[arg-type]
    names = {slot: matchup["starters"][slot]["name"] for slot in SUBJECT_SLOTS}  # type: ignore[index]
    part = c.key.rsplit(".", 1)[1]
    c.require(len(pitched) == {"one": 1, "none": 0}[part], "pitch_data", f"the sentence says {part} starter has Statcast pitch data, {len(pitched)} do")
    if part == "one" and len(pitched) == 1:
        c.require(c.text("with_data") == names[pitched[0]], "names", "the starter with pitch data is not the one named")
        c.require(c.text("without_data") == names[other_slot(pitched[0])], "names", "the starter without pitch data is not the one named")
    report = (matchup or {}).get("report")  # type: ignore[union-attr]
    if report is None:
        return
    for slot in SUBJECT_SLOTS:
        if slot in pitched:
            continue
        named = facts.pitches_named_for(matchup, report, slot, _catalog(c))  # type: ignore[arg-type]
        c.require(not named, "arsenal_claims", f"the report names {', '.join(named)} for {names[slot]}, who has no pitch data")


def _confidence_offense(c: Ctx) -> None:
    """What is said of a missing offense split: `one` (the team named has one, the other does not) or `none`."""

    matchup = c.matchup
    c.require(c.live, "not_live", "the matchup is not live")
    sides = _split_sides(matchup)  # type: ignore[arg-type]
    teams = {side: matchup["teams"][side]["name"] for side in ("away", "home")}  # type: ignore[index]
    part = c.key.rsplit(".", 1)[1]
    c.require(len(sides) == {"one": 1, "none": 0}[part], "offense", f"the sentence says {part} lineup has a season offense split, {len(sides)} do")
    if part == "one" and len(sides) == 1:
        lacking = "home" if sides[0] == "away" else "away"
        c.require(c.text("with_split") == teams[sides[0]], "names", "the lineup with a split is not the one named")
        c.require(c.text("without_split") == teams[lacking], "names", "the lineup without a split is not the one named")


def _confidence_demo(c: Ctx) -> None:
    c.require(not c.live, "live", "a live matchup says it is based on cached demo data")


def _first_watch(c: Ctx) -> Mapping[str, Any]:
    found = [
        claim
        for location, claim in c.index.by_location.items()
        if re.fullmatch(r"report\.sections\[\d+\]\.bullets\[0\]", location)
    ]
    if len(found) != 1:
        c.fail("first_watch", "the first thing to watch cannot be found")
        raise _Abort
    return found[0]


def _watch_whether(c: Ctx) -> None:
    first = _first_watch(c)
    c.require(first["key"] == "analyst.watch.question", "first_watch", "the first thing to watch is not a question")
    for name in ("name", "action"):
        c.require(first["args"].get(name) == c.args.get(name), "first_watch", f"the {name} is not the one of the first thing to watch")


def _watch_line(c: Ctx) -> None:
    c.require(c.ref("observation")["key"] == "writer.watch_whether", "observation", "the observation is not 'whether <starter> can <action>'")


def _watch_land(c: Ctx) -> None:
    starter, profile = c.starter, _profile(c.starter)
    c.require(not _unspoken(starter), "limited_arsenal", "his arsenal is limited or has an unnamed lead pitch")
    named = labels.pitch_named(profile["putaway_pitch"])
    c.require(named and c.text("putaway") == _short(profile["putaway_pitch"]), "pitch", "the put-away pitch is not his")
    if named:
        _, enough = _thrown_share(c.matchup, c.slot, profile["putaway_pitch"], labels.PUTAWAY_MIN_USAGE_PCT)  # type: ignore[arg-type]
        c.require(enough, "putaway_share", "the put-away pitch is under 15% of his pitches")


# --- critic --------------------------------------------------------------------------------------


def _checks(c: Ctx) -> list[Mapping[str, Any]]:
    return c.matchup["critic_review"]["checks"]  # type: ignore[index]


def _critic_summary(c: Ctx) -> None:
    checks = _checks(c)
    warnings = sum(1 for check in checks if check["status"] == "warning")
    unsupported = sum(1 for check in checks if check["status"] == "unsupported")
    c.require(c.args["checked"] == len(checks), "count", "the number checked is not the number of checks")
    if c.key.endswith("unsupported"):
        c.fail("published", "an unsupported claim is published")
    elif c.key.endswith("warnings"):
        c.require(c.args["warnings"] == warnings and warnings > 0 and not unsupported, "count", "the warnings are not the ones of the checks")
    else:
        c.require(not warnings and not unsupported, "count", "the checks have warnings")


def _note_no_betting(c: Ctx) -> None:
    ran = [
        index
        for index in range(len(_checks(c)))
        if (claim := c.index.by_location.get(f"critic_review.checks[{index}].claim")) and claim["key"] == "critic.betting.claim"
    ]
    c.require(
        bool(ran) and all(_checks(c)[i]["status"] == "not_present" for i in ran),
        "check",
        "the betting-language check did not run, or found language",
    )


def _role_pitch(c: Ctx) -> tuple[str, Any, int]:
    role = c.ref("role")["key"].rsplit(".", 1)[1]
    profile = _profile(c.starter)
    if role == "primary":
        return role, profile["primary_pitch"], labels.PRIMARY_MIN_USAGE_PCT
    return role, profile["putaway_pitch"], labels.PUTAWAY_MIN_USAGE_PCT


def _pitch_claim(c: Ctx) -> None:
    _, pitch, _ = _role_pitch(c)
    c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")
    c.require(labels.pitch_named(pitch) and _short(c.text("pitch")) == _short(pitch), "pitch", "the pitch is not his")


def _pitch_evidence(c: Ctx) -> None:
    starter, slot = c.starter, c.slot
    key = c.key.rsplit(".", 1)[1]
    role = "primary" if key.endswith("primary") else "putaway" if key.endswith("putaway") else None
    if role is None:
        role = c.ref("role")["key"].rsplit(".", 1)[1]
    profile = _profile(starter)
    pitch = profile["primary_pitch"] if role == "primary" else profile["putaway_pitch"]
    minimum = labels.PRIMARY_MIN_USAGE_PCT if role == "primary" else labels.PUTAWAY_MIN_USAGE_PCT
    c.require(labels.pitch_named(pitch) and _short(c.text("pitch")) == _short(pitch), "pitch", "the pitch is not his")
    row = _mix_row(c.matchup, pitch) if labels.pitch_named(pitch) else None  # type: ignore[arg-type]
    if row is None:
        c.fail("mix", "the pitch is not in the pitch mix")
        return
    cell = row[slot]
    count, total = cell.get("count"), cell.get("total")
    counted = isinstance(count, int) and isinstance(total, int)
    shown = _share(cell)
    meets = labels.share_at_least(count, total, minimum) if counted else (shown or 0) >= minimum
    if key.startswith("supported"):
        c.require(shown is not None and float(c.text("usage")) == shown, "usage", "the usage is not the mix's")
        c.require(meets, "minimum", f"the pitch is under {minimum}% of his pitches")
        return
    c.require(not meets, "minimum", f"the pitch reaches {minimum}%, the sentence says it does not")
    c.require(c.args["minimum"] == minimum, "minimum", "the minimum is not the role's")
    if key == "low_counts":
        c.require(counted, "counts", "the mix row has no raw counts")
        if counted:
            shown = (str(c.text("count")).replace(",", ""), str(c.text("total")).replace(",", ""))
            c.require(shown == (str(count), str(total)), "counts", "the counts are not the mix's")
    else:
        c.require(not counted, "counts", "the mix row has raw counts, the sentence should use them")
        c.require(shown is not None and float(c.text("usage")) == shown, "usage", "the usage is not the mix's")


def _pitch_absent(c: Ctx) -> None:
    row = _mix_row(c.matchup, c.text("pitch"))  # type: ignore[arg-type]
    thrown = bool(row) and _thrown_share(c.matchup, c.slot, c.text("pitch"), 0)[0]  # type: ignore[arg-type]
    c.require(not thrown, "thrown", "the pitch is in his pitch mix")


def _catalog(c: Ctx) -> Any:
    return c.index.catalogs[0]


def _report(c: Ctx) -> Mapping[str, Any]:
    return c.matchup["report"]  # type: ignore[index]


def _problem_published(c: Ctx) -> None:
    """A sentence that reports a problem the data has is never in a published file (the generator stops)."""

    c.fail("published", "a sentence that reports an unsupported claim is in a published file")


def _names(c: Ctx) -> None:
    problems = facts.pitches_not_thrown(c.matchup, _report(c), _catalog(c))  # type: ignore[arg-type]
    shown = ", ".join(pitch for _, pitch in problems)
    c.require(not problems, "thrown", f"the report names {shown}, which the starter it is credited to did not throw")


def _limited_claim(c: Ctx) -> None:
    c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")
    c.require(_limited(c.starter, "arsenal"), "not_limited", "his arsenal is not limited")


def _limited_supported(c: Ctx) -> None:
    sample = _sample(c.starter)
    if sample is None or not _limited(c.starter, "arsenal"):
        c.fail("not_limited", "his arsenal is not limited")
        return
    pitches = sample["arsenal"]["pitches"]
    have = c.ref("have")
    if have["key"] == "@capitalize":  # the evidence starts a sentence with it
        have = c.index.by_id[have["args"]["of"]["claim"]]
    if have["key"] == "critic.limited.pitches":
        c.require(pitches and have["args"].get("count") == pitches, "count", "the count of pitches is not the sample's")
    else:
        c.require(pitches == 0, "count", "he has pitches on record, or the count is unknown, and the sentence says none")
    c.require(c.args["needed"] == sample["thresholds"]["arsenal"], "needed", "the minimum is not the sample's threshold")
    named = facts.pitches_named_for(c.matchup, _report(c), c.slot, _catalog(c))  # type: ignore[arg-type]
    c.require(not named, "named", f"the report names {', '.join(named)} for him")


def _limited_supported_unavailable(c: Ctx) -> None:
    sample = _sample(c.starter)
    if sample is None or not _limited(c.starter, "arsenal"):
        c.fail("not_limited", "his arsenal is not limited")
        return
    c.require(sample["arsenal"]["pitches"] is None, "count", "his pitch count is known, and the sentence says it is not available")
    c.require(c.args["needed"] == sample["thresholds"]["arsenal"], "needed", "the minimum is not the sample's threshold")
    named = facts.pitches_named_for(c.matchup, _report(c), c.slot, _catalog(c))  # type: ignore[arg-type]
    c.require(not named, "named", f"the report names {', '.join(named)} for him")


def _command(c: Ctx) -> None:
    kind = c.key.rsplit(".", 1)[1]
    if kind in ("wrong_claim", "wrong_evidence"):
        _problem_published(c)
    elif kind in ("absent_claim", "absent_evidence"):
        found, _ = facts.command_finding(c.matchup, _report(c), _catalog(c))  # type: ignore[arg-type]
        c.require(found == "absent", "claim_made", "the report makes a command claim")
    elif kind == "below_claim":
        c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")
        c.require(labels.COMMAND_BELOW.lower() in _label(c.starter, "command_label"), "label", "his command label is not below average")
    elif kind == "label_claim":
        c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")
        label = _label(c.starter, "command_label")
        c.require(any(term in label for term in facts.COMMAND_STRONG_TERMS), "label", "his command label is not plus or solid")
    elif kind == "strength":
        score = facts.command_strength(c.matchup, c.slot)  # type: ignore[arg-type]
        c.require(score is not None and c.args["value"] == score, "value", "the strength profile has no such Command score")
    elif kind == "walks":
        rates = (_sample(c.starter) or {}).get("rates") or {}
        counts = labels.figure_scopes(c.starter).get("counts")  # type: ignore[arg-type]
        c.require(rates.get("walks") is not None and c.args["walks"] == rates.get("walks"), "walks", "the walks are not the sample's")
        c.require(bool(rates.get("batters_faced")) and c.args["batters"] == rates.get("batters_faced"), "batters", "the batters faced are not the sample's")
        c.require(counts is not None and c.args["scope"] == counts["label"], "scope", "the scope is not the scope of the counts")
    elif kind == "none":
        rates = (_sample(c.starter) or {}).get("rates") or {}
        has_sample = bool(rates.get("batters_faced")) and labels.figure_scopes(c.starter).get("counts") is not None  # type: ignore[arg-type]
        c.require(
            facts.command_strength(c.matchup, c.slot) is None and not has_sample,  # type: ignore[arg-type]
            "available",
            "a Command score or a walk-rate sample is available",
        )
    else:
        c.fail("key", f"no condition is written for {c.key}")


def _scope_claim(c: Ctx) -> None:
    kind, _ = facts.scope_finding(c.matchup, _report(c), _catalog(c))  # type: ignore[arg-type]
    c.require(kind != "all_claimed", "all_claimed", "the report says all the figures cover one sample about a starter whose groups differ")
    c.require(kind != "unsupported", "unsaid", "the report does not say the figures cover different samples, and for some starter they do")


def _critic_scope_same(c: Ctx) -> None:
    c.require(not facts.differing_starters(c.matchup), "differs", "the groups of figures of some starter cover different games")  # type: ignore[arg-type]


def _scope_supported(c: Ctx) -> None:
    differing = set(facts.differing_starters(c.matchup))  # type: ignore[arg-type]
    named = {s["name"] for s in c.who()}
    c.require(named == differing and bool(differing), "who", "the starters named are not the ones whose groups differ")
    c.require(facts.says_samples_differ(_report(c), _catalog(c)), "marker", "the report does not say the figures cover different samples")


def _betting(c: Ctx) -> None:
    found = facts.betting_terms(_report(c), _catalog(c))
    c.require(not found, "language", f"the report uses outcome or betting language: {', '.join(term for term, _ in found)}")


# --- postgame grader -----------------------------------------------------------------------------


def _final(c: Ctx) -> Mapping[str, Any]:
    if c.state != "Final" or not isinstance(c.matchup.get("postgame"), Mapping):  # type: ignore[union-attr]
        c.fail("game_state", "a completed start is described for a game that is not final or has no box score")
        raise _Abort
    return c.matchup["postgame"]["starter_lines"][c.slot]  # type: ignore[index]


def _grader_explanation(c: Ctx) -> None:
    line = _final(c)
    score = line["game_score"]
    band = "standout" if score >= 68 else "solid" if score >= 56 else "mixed" if score >= 45 else "rough" if score >= 35 else "difficult"
    c.require(c.args["score"] == score, "figure", "the Game Score is not the line's")
    c.require(c.key.rsplit(".", 1)[1] == band, "band", f"the Game Score {score} is {band}")


def _grader_plan(c: Ctx) -> None:
    line, profile = _final(c), _profile(c.starter)
    c.require(c.text("primary") == str(profile["primary_pitch"]).lower(), "pitch", "the primary pitch is not his")
    c.require(c.text("putaway") == str(profile["putaway_pitch"]).lower(), "pitch", "the put-away pitch is not his")
    walks, runs = int(line["walks"]), int(line["earned_runs"])
    actual = "matched" if walks <= 1 and runs <= 2 else "walks" if walks >= 3 else "partial"
    c.require(c.key.rsplit(".", 1)[1] == actual, "band", f"the line is {actual}")
    for name, value in (("walks", walks), ("earned_runs", runs), ("hits", int(line["hits_allowed"]))):
        if name in c.args:
            c.require(c.count(name) == value, "figure", f"the {name} are not the line's")


def _grader_next(c: Ctx) -> None:
    line, profile = _final(c), _profile(c.starter)
    walks, hits, runs, strikeouts = (int(line[f]) for f in ("walks", "hits_allowed", "earned_runs", "strikeouts"))
    if walks >= 3:
        actual = "walks"
    elif hits >= 7:
        actual = "hits"
    elif runs >= 4:
        actual = "runs"
    elif strikeouts <= 3 and _label(c.starter, "swing_miss_label").startswith("average"):
        actual = "chase"
    else:
        actual = "default"
    c.require(c.key.rsplit(".", 1)[1] == actual, "band", f"the line calls for {actual}")
    if "putaway" in c.args:
        c.require(c.text("putaway") == str(profile["putaway_pitch"]).lower(), "pitch", "the put-away pitch is not his")


def _grader_call(c: Ctx) -> None:
    line = _final(c)
    kind = c.key.split(".")[2]
    if "name" in c.args:
        c.require(c.text("name") == c.starter["name"], "name", "the sentence is about another starter")
    expected = {
        "command": {"walks": int(line["walks"])},
        "walk_risk": {"batters": int(line["walks"])},
        "swing_miss": {"strikeouts": int(line["strikeouts"])},
    }[kind]
    for name, value in expected.items():
        if name in c.args:
            c.require(c.count(name) == value, "figure", f"the {name} are not the line's")
    if "innings" in c.args:
        c.require(c.args["innings"] == line["innings_pitched"], "figure", "the innings are not the line's")
    if "score" in c.args:
        c.require(c.args["score"] == line["game_score"], "figure", "the Game Score is not the line's")


def _scout_note(c: Ctx) -> None:
    final = (c.matchup or {}).get("status") == "final"
    c.require(not c.live, "live", "a live matchup carries a demo note")
    c.require(final == c.key.startswith("scout.final."), "status", "the note is for a game in another state")


def _demo_starter(c: Ctx) -> None:
    c.require(not c.live and _sample(c.starter) is None, "live", "a live starter is read with a demo sentence")


def _demo_matchup(c: Ctx) -> None:
    c.require(not c.live, "live", "a live matchup carries a demo sentence")


# --- generator text ------------------------------------------------------------------------------


def _live_file(c: Ctx) -> bool:
    return c.metadata.get("data_mode") == LIVE_LEVEL


def _counted(c: Ctx) -> list[Mapping[str, Any]]:
    """The matchups the workflow counts: every matchup of a demo file, only the live ones of a live file."""

    matchups = c.payload.get("matchups") or []
    if not _live_file(c):
        return list(matchups)
    return [m for m in matchups if (m.get("data_confidence") or {}).get("level") == LIVE_LEVEL]


def _wf_loaded(c: Ctx) -> None:
    c.require(c.args["count"] == len(_counted(c)), "count", "the count is not the number of matchups the file counts")
    c.require((c.args["count"] == 1) == (c.claim["key"] == "generator.workflow.loaded.one"),
              "count", "the grammatical number is not the number of matchups")
    text = c.index.text(c.claim["id"]) or ""
    c.require(not _live_file(c) or "cached" not in text.lower(), "cached", "a live file says it loaded cached data")


def _wf_done(c: Ctx) -> None:
    c.require(bool(_counted(c)) and all(isinstance(m.get("report"), Mapping) for m in _counted(c)), "report", "no report was produced")


def _wf_checked(c: Ctx) -> None:
    c.require(bool(_counted(c)), "report", "there was no report to check")
    warnings = sum(1 for m in _counted(c) for check in m["critic_review"]["checks"] if check["status"] == "warning")
    c.require(c.args["warnings"] == warnings, "count", "the warnings are not the ones of the matchups the file counts")


def _graded_count(c: Ctx) -> int:
    return sum(len((m.get("postgame") or {}).get("starter_lines") or {}) for m in _counted(c))


def _wf_graded(c: Ctx) -> None:
    c.require(c.args["count"] == _graded_count(c), "count", "the number graded is not the number of box-score lines")


def _wf_graded_none(c: Ctx) -> None:
    c.require(bool(_counted(c)), "report", "there is no featured game")
    c.require(_graded_count(c) == 0, "count", "a completed game was graded")


def _fetched_date(c: Ctx) -> str | None:
    """The day of `metadata.data_fetched_at` in America/New_York (D39), or None when it is not an instant."""

    return new_york_day(c.metadata.get("data_fetched_at"))


def _label_live(c: Ctx) -> None:
    c.require(_live_file(c), "mode", "the file is not a live one")
    c.require(_fetched_date(c) is not None and c.args["date"] == _fetched_date(c), "fetched_at", "the date is not the day of metadata.data_fetched_at")


def _label_fallback(c: Ctx) -> None:
    c.require(c.metadata.get("data_mode") == "demo_fallback", "mode", "the file is not a fallback one")


def _label_demo(c: Ctx) -> None:
    c.require(c.metadata.get("data_mode") == "demo_cached", "mode", "the file is not a demo one")


def _confidence_note(c: Ctx) -> None:
    c.require(c.live, "not_live", "the matchup is not live")
    c.require(c.args["matchup_id"] == c.matchup["id"], "matchup", "the id is not the matchup's")  # type: ignore[index]
    c.require(_fetched_date(c) is not None and c.args["date"] == _fetched_date(c), "fetched_at", "the date is not the day of metadata.data_fetched_at")


# --- the registry --------------------------------------------------------------------------------

Rule = Callable[[Ctx], None]

RULES: dict[str, Rule] = {
    # 3.1 agent phrases
    "analyst.summary": _summary,
    "analyst.label.against": _label_against,
    "analyst.style.pair": _style,
    "analyst.style.single": _style,
    "analyst.read.combination": _combination,
    "analyst.read.mainly": _mainly,
    "analyst.read.shows": _shows,
    "analyst.read.qualifier": _qualifier,
    "analyst.read.qualifier_both": _qualifier,
    "analyst.have.pitches": _have_pitches,
    "analyst.have.no_pitches": _have_no_pitches,
    "analyst.have.batters": _have_batters,
    "analyst.have.pitches_unavailable": _have_pitches_unavailable,
    "analyst.have.batters_unavailable": _have_batters_unavailable,
    "analyst.have.no_batters": _have_no_batters,
    "analyst.data.arsenal": _data_limited,
    "analyst.data.arsenal_unnamed": _data_arsenal_unnamed,
    "analyst.data.strikeout": _data_limited,
    "analyst.data.control": _data_limited,
    "analyst.data.contact": _data_contact,
    "analyst.data.no_home_runs": _data_no_home_runs,
    "analyst.strength.swing_miss": _strength_swing,
    "analyst.strength.command": _strength_command,
    "analyst.strength.contact": _strength_contact,
    "analyst.strength.trending": _strength_trending,
    "analyst.risk.command": _risk_command,
    "analyst.risk.contact": _risk_contact,
    "analyst.risk.volatile": _risk_volatile,
    "analyst.offense.unavailable": _offense_unavailable,
    "analyst.offense.unavailable_no_hand": _offense_no_hand,
    "analyst.offense.strong": _offense_read,
    "analyst.offense.average": _offense_read,
    "analyst.offense.weak": _offense_read,
    "analyst.offense.note_strikeouts": _offense_note,
    "analyst.offense.note_walks": _offense_note,
    "analyst.pressure.ops": _internal,
    "analyst.pressure.strikeouts": _internal,
    "analyst.pressure.walks": _internal,
    "analyst.scope.season_figures": _scope_part,
    "analyst.scope.no_season_figures": _scope_part,
    "analyst.scope.differ": _scope_differ,
    "analyst.scope.groups": _scope_groups,
    "analyst.scope.group_part": _scope_part,
    "analyst.scope.same": _scope_same,
    "analyst.scope.none": _scope_none,
    "analyst.scope.offense": _scope_offense,
    "analyst.series.standing": _series_sentence,
    "analyst.series.opening": _series_sentence,
    "analyst.watch.action.land": _watch_land,
    "writer.strength": _writer_strength,
    "writer.strength_none": _writer_strength_none,
    "writer.arsenal.contrast": _arsenal_contrast,
    "writer.arsenal.works_off": _arsenal_works_off,
    "writer.arsenal.no_contrast": _arsenal_no_contrast,
    "writer.arsenal.no_contrast_unnamed": _arsenal_no_contrast_unnamed,
    "writer.confidence.limited": _confidence_limited,
    "writer.confidence.snapshot": _confidence_snapshot,
    "writer.confidence.item.pitchers": _confidence_snapshot,
    "writer.confidence.item.pitch_data": _item_pitch_data,
    "writer.confidence.item.offense": _item_offense,
    "writer.confidence.pitch_data.one": _confidence_pitch_data,
    "writer.confidence.pitch_data.none": _confidence_pitch_data,
    "writer.confidence.offense.one": _confidence_offense,
    "writer.confidence.offense.none": _confidence_offense,
    "writer.confidence.lineups": _confidence_lineups,
    "writer.confidence.demo": _confidence_demo,
    "writer.watch_line": _watch_line,
    "writer.watch_whether": _watch_whether,
    "writer.default_strength": _demo_matchup,
    # critic
    "critic.summary.supported": _critic_summary,
    "critic.summary.warnings": _critic_summary,
    "critic.summary.unsupported": _critic_summary,
    "critic.note.no_betting": _note_no_betting,
    "critic.pitch.claim": _pitch_claim,
    "critic.pitch.supported_primary": _pitch_evidence,
    "critic.pitch.supported_putaway": _pitch_evidence,
    "critic.pitch.low": _pitch_evidence,
    "critic.pitch.low_counts": _pitch_evidence,
    "critic.pitch.absent": _pitch_absent,
    "critic.names.claim": _names,
    "critic.names.supported": _names,
    "critic.names.credited": _problem_published,
    "critic.names.nobody": _problem_published,
    "critic.names.unsupported": _problem_published,
    "critic.limited.claim": _limited_claim,
    "critic.limited.supported": _limited_supported,
    "critic.limited.unsupported": _problem_published,
    "critic.limited.supported_unavailable": _limited_supported_unavailable,
    "critic.limited.unsupported_unavailable": _problem_published,
    "critic.command.*": _command,
    "critic.scope.claim": _scope_claim,
    "critic.scope.same": _critic_scope_same,
    "critic.scope.supported": _scope_supported,
    "critic.scope.unsupported": _problem_published,
    "critic.scope.all_claimed": _problem_published,
    "critic.betting.claim": _betting,
    "critic.betting.absent": _betting,
    "critic.betting.unsupported": _problem_published,
    # postgame grader and demo notes
    "grader.explanation.*": _grader_explanation,
    "grader.plan.*": _grader_plan,
    "grader.next.*": _grader_next,
    "grader.call.*": _grader_call,
    "scout.final.*": _scout_note,
    "scout.demo.*": _scout_note,
    "analyst.demo.*": _demo_starter,
    "analyst.fallback.*": _demo_starter,
    "analyst.command_note.*": _demo_starter,
    "analyst.contact_note.*": _demo_starter,
    # 3.2 generator text
    "generator.workflow.loaded": _wf_loaded,
    "generator.workflow.loaded.one": _wf_loaded,
    "generator.workflow.identified": _wf_done,
    "generator.workflow.generated": _wf_done,
    "generator.workflow.checked": _wf_checked,
    "generator.workflow.graded": _wf_graded,
    "generator.workflow.graded_none": _wf_graded_none,
    "generator.metadata.last_updated.live": _label_live,
    "generator.metadata.last_updated.fallback": _label_fallback,
    "generator.metadata.last_updated.demo": _label_demo,
    "generator.confidence.live_note": _confidence_note,
}

ASSERTS_NOTHING: tuple[str, ...] = (
    "@join",
    "@capitalize",
    "count.*",
    "analyst.list_and",
    "writer.confidence.list_two",
    "writer.confidence.list_three",
    "analyst.goal.*",
    "analyst.read.he",
    "analyst.figure.*",
    "analyst.figure.list_and",
    "analyst.watch.question",
    "analyst.watch.action.ahead",
    "analyst.watch.action.efficient",
    "analyst.watch.action.keep",
    "analyst.watch.deep",
    "analyst.offense.with_notes",
    "writer.section.*",
    "writer.forbidden_terms",
    "writer.required_terms",
    "critic.role.*",
    "critic.generic_fastball",
    "critic.pitch_aliases",
    "critic.limited.pitches",
    "critic.limited.none",
    "critic.command.word",
    "critic.command.no_label",
    "critic.scope.marker",
    "critic.scope.all_marker",
    "critic.betting_terms",
    "critic.betting.item",
    "generator.workflow.description",
)


def specificity(pattern: str) -> int:
    """An exact key beats a pattern; a longer prefix beats a shorter one."""

    return len(pattern.rstrip("*")) + (0 if "*" in pattern else 1000)


def classify(key: str) -> tuple[str | None, str | None]:
    """("rule" | "nothing", the most specific pattern that matches `key`), or (None, None)."""

    found = [(specificity(p), "rule", p) for p in RULES if fnmatchcase(key, p)]
    found += [(specificity(p), "nothing", p) for p in ASSERTS_NOTHING if fnmatchcase(key, p)]
    if not found:
        return None, None
    _, kind, pattern = max(found)
    return kind, pattern


def run_rule(key: str, ctx: Ctx) -> list[Fail]:
    """The failures of the rule of `key` on `ctx`; none for a key that asserts nothing."""

    kind, pattern = classify(key)
    if kind != "rule":
        return []
    try:
        RULES[pattern](ctx)  # type: ignore[index]
    except _Abort:
        pass
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
        ctx.fail("unreadable", f"the payload does not have what the rule reads: {type(exc).__name__}: {exc}")
    return ctx.fails
