"""The manifest of a live payload: where every field comes from (data contract rules 1 and 2, D34).

Every leaf of a live file (an empty list or map counts as a leaf: it is the unavailable state of what it
would hold) must match one entry of `MANIFEST`, and each entry says what kind of field it is:

- `source`: a value the source gave, copied or parsed (a name, an id, a count, a start time);
- `derivation`: computed by a documented rule from other fields; its check recomputes the value and compares;
- `label`: a constant that asserts nothing about data (a title, a unit, the schema version);
- `claim`: a sentence the agents or the generator wrote; rule 4 (`claims_registry`) owns its condition;
- `fact`: a constant that asserts a fact about the data, written fixed without looking at the outcome. It is
  a violation by definition. The entry names the finding (F number) it belongs to; the fix of that
  finding turns the entry into a derivation with its evidence.

A `None` is the unavailable state and is allowed only where the entry says `nullable`. A wrong type, a
leaf with no entry, a placeholder given as a value (`???`), a derivation that does not recompute, and a
number that stands for an unknown or a zero with no evidence are violations.

Violation codes (the place is the pattern of the entry, or the normalized path with `[]` for a list item when
no entry matches): `rule1:unlisted`,
`rule1:null_not_declared`, `rule1:wrong_type`, `rule1:constant_asserts_fact`, `rule1:derivation_mismatch`,
`rule1:placeholder`, `rule1:invented_derivation`, `rule2:zero_without_evidence`,
`rule2:unknown_written_as_value`.

`findings(payload)` returns (code, where, message). Only a live file is asked (rule 6: a demo file is a
demo). Demo matchups and archive rows inside a live file are rule 6's finding (F4) and are not walked.

The limit of the zero check: the payload does not carry the Statcast `events` column, so a zero count
is judged by what must hold around it. A starter hurt on his first pitch has pitches and no batter faced:
the check cannot tell that from an unusable `events` column (F6b) and reports it as a zero without evidence.
This module never imports the critic or the agents (`tests/test_registry_no_critic.py`).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
import re
from typing import Any
from zoneinfo import ZoneInfo

from data_pipeline import labels
from data_pipeline.schema import CRITIC_STATUSES, SCHEMA_VERSION, is_utc_instant

LIVE_MODE = "fetched_snapshot"
LIVE_LEVEL = "fetched_snapshot"
SLOTS = ("away_starter", "home_starter")

SOURCE, DERIVATION, LABEL, CLAIM, FACT = "source", "derivation", "label", "claim", "fact"
KINDS = (SOURCE, DERIVATION, LABEL, CLAIM, FACT)

# The workflow steps whose status is written fixed (F19); the postgame step reads its own result.
FIXED_STATUS_STEPS = ("Data Scout Agent", "Matchup Analyst Agent", "Report Writer Agent", "Critic / Fact-check Agent")
POSTGAME_STEP = "Postgame Grader Agent"
RATES_SOURCES = ("mlb_api", "statcast", "unavailable")
IMPOSSIBLE = "rule1:impossible_figures"
HANDS = ("L", "R", "S")
NUMERIC = (int, float)

Problem = tuple[str, str]  # (violation code without the place, message)


# --- the context of a check ------------------------------------------------------------------------


def _at(node: Any, path: tuple) -> Any:
    for key in path:
        node = node[key]
    return node


@dataclass(frozen=True)
class Ctx:
    """The leaf being judged and the way to its neighbours."""

    root: Mapping[str, Any]
    path: tuple
    value: Any

    @property
    def field(self) -> Any:
        return self.path[-1]

    @property
    def matchup(self) -> Mapping[str, Any]:
        return self.root["matchups"][self.path[1]]

    def around(self, up: int, *keys: Any) -> Any:
        """The node `up` levels above the leaf, then down `keys`."""

        return _at(_at(self.root, self.path[: len(self.path) - up]), keys)

    @property
    def starter(self) -> Mapping[str, Any]:
        return self.matchup["starters"][next(part for part in self.path if part in SLOTS)]

    @property
    def slot(self) -> str:
        return next(part for part in self.path if part in SLOTS)


Check = Callable[[Ctx], "Problem | None"]


@dataclass(frozen=True)
class Entry:
    pattern: str
    kind: str
    origin: str  # the source, the rule or the reason, in words
    types: tuple[type, ...] = ()  # the Python types of the value; empty: any
    nullable: bool = False
    check: Check | None = None
    finding: str | None = None  # for `fact`: the finding of DATA_CONTRACT.md section 4
    check_null: bool = False  # the check also runs on an unavailable value (a null that is allowed only in some cases)

    def __post_init__(self) -> None:
        assert self.kind in KINDS, self.kind
        assert (self.kind == FACT) == (self.finding is not None), self.pattern


# --- checks ----------------------------------------------------------------------------------------

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TEAM_ABBR = re.compile(r"[A-Z]{2,4}")
_OPS = re.compile(r"\d?\.\d{3}")
_PERCENT = re.compile(r"\d+(\.\d)?%")
_DIGITS = re.compile(r"\d+")
_RATE_TEXT = re.compile(r"\d+(\.\d+)?")


def _mismatch(message: str) -> Problem:
    return ("rule1:derivation_mismatch", message)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_instant(value: Any) -> bool:
    if not isinstance(value, str) or "T" not in value:
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return False


def is_date(c: Ctx) -> Problem | None:
    return None if _is_date(c.value) else ("rule1:wrong_type", f"{c.value!r} is not a date")


def is_instant(c: Ctx) -> Problem | None:
    return None if _is_instant(c.value) else ("rule1:wrong_type", f"{c.value!r} is not a timestamp with a zone")


def is_utc(c: Ctx) -> Problem | None:
    return None if is_utc_instant(c.value) else ("rule1:wrong_type", f"{c.value!r} is not a UTC instant")


def is_zone(c: Ctx) -> Problem | None:
    try:
        ZoneInfo(c.value)
    except Exception:  # noqa: BLE001  (an unknown key, a bad path: any failure means it is not a zone)
        return ("rule1:wrong_type", f"{c.value!r} is not a time zone")
    return None


def is_digits(c: Ctx) -> Problem | None:
    return None if isinstance(c.value, str) and _DIGITS.fullmatch(c.value) else ("rule1:wrong_type", f"{c.value!r} is not an id")


def equals(expected: Callable[[Ctx], Any], what: str) -> Check:
    def check(c: Ctx) -> Problem | None:
        want = expected(c)
        return None if c.value == want else _mismatch(f"{what}: expected {want!r}, found {c.value!r}")

    return check


def in_set(allowed: tuple[Any, ...]) -> Check:
    def check(c: Ctx) -> Problem | None:
        return None if c.value in allowed else ("rule1:wrong_type", f"{c.value!r} is not one of {list(allowed)}")

    return check


def matches(pattern: re.Pattern[str], what: str) -> Check:
    def check(c: Ctx) -> Problem | None:
        ok = isinstance(c.value, str) and pattern.fullmatch(c.value)
        return None if ok else ("rule1:wrong_type", f"{c.value!r} is not {what}")

    return check


def is_none(c: Ctx) -> Problem | None:
    return None if c.value is None else ("rule1:unlisted", f"a live file has no source for {c.value!r} yet")


def team_abbreviation(c: Ctx) -> Problem | None:
    """A team abbreviation the source or the maps gave; a team they do not know has none (null), never a placeholder."""

    if isinstance(c.value, str) and _TEAM_ABBR.fullmatch(c.value):
        return None
    return ("rule1:placeholder", f"{c.value!r} stands for a team abbreviation the source did not give (F7)")


def scope_part(c: Ctx) -> Problem | None:
    """`kind`, `through` and `label` of a scope: the label is made from the other two."""

    scope = c.around(1)
    kind, through = scope.get("kind"), scope.get("through")
    if c.field == "kind":
        return None if kind in (labels.SCOPE_REGULAR, labels.SCOPE_REGULAR_POSTSEASON) else _mismatch(f"unknown scope kind {kind!r}")
    if c.field == "through":
        return None if _is_date(through) else ("rule1:wrong_type", f"{through!r} is not a date")
    if kind not in (labels.SCOPE_REGULAR, labels.SCOPE_REGULAR_POSTSEASON) or not _is_date(through):
        return None  # the other two parts report it
    want = labels.make_scope(kind, through)["label"]
    return None if c.value == want else _mismatch(f"label {c.value!r} is not {want!r}")


def season_text(c: Ctx) -> Problem | None:
    """ERA, WHIP and innings are text by type: "N/A" when unknown, otherwise a number written as text."""

    value = c.value
    if value == "N/A" or (isinstance(value, str) and _RATE_TEXT.fullmatch(value)):
        return None
    return ("rule2:unknown_written_as_value", f"{value!r} is neither a number written as text nor the sentinel 'N/A'")


# -- starters ---------------------------------------------------------------------------------------


def _mix_rows(c: Ctx, slot: str) -> list[Mapping[str, Any]]:
    """The cells of the pitch mix for one starter that are real pitches (count above zero), most thrown first."""

    cells = []
    for row in c.matchup["charts"]["pitch_mix"]:
        cell = row[slot]
        if isinstance(cell.get("count"), int) and cell["count"] > 0:
            cells.append({**cell, "pitch": row["pitch"]})
    return sorted(cells, key=lambda cell: (-cell["count"], cell["pitch"]))


def profile_field(c: Ctx) -> Problem | None:
    """
    The pitching profile is computed: the primary pitch is the most thrown, the put-away pitch the second
    one if it is at least 15% of his pitches (D30), the style is made of both, and the labels come from the
    sample (D24, D25). Recompute and compare.
    """

    starter, field = c.starter, c.field
    sample = starter["sample"]
    cells = _mix_rows(c, c.slot)
    if field in ("swing_miss_label", "command_label", "contact_risk_label"):
        profile = {"style_label": None}
        labels.apply_profile_labels(profile, sample)
        want = profile[field]
    else:
        # The same function the pipeline calls (D30, F6e): a role held by a pitch the map does not name is not available.
        total = cells[0]["total"] if cells else 0
        primary, second = labels.profile_pitches({cell["pitch"]: cell["count"] for cell in cells}, total=total)
        if field == "primary_pitch":
            want = primary
        elif field == "putaway_pitch":
            want = second
        else:
            want = f"{primary}-{second} starter" if labels.pitch_named(second) else f"{primary} starter"
            if not labels.pitch_named(primary) or sample["limited"]["arsenal"]:
                want = labels.ARSENAL_LIMITED_STYLE
    return None if c.value == want else _mismatch(f"{field} is computed from the pitch mix and the sample: expected {want!r}, found {c.value!r}")


def limited_flag(c: Ctx) -> Problem | None:
    sample = c.starter["sample"]
    rates, arsenal = sample["rates"], sample["arsenal"]
    want = labels.build_sample(
        pitches=arsenal["pitches"],
        arsenal_scope=arsenal["scope"],
        batters_faced=rates["batters_faced"],
        strikeouts=rates["strikeouts"],
        walks=rates["walks"],
        home_runs=rates["home_runs"],
        rates_source=rates["source"],
        rates_scope=rates["scope"],
    )["limited"][c.field]
    return None if c.value is want else _mismatch(f"limited.{c.field} is {want} for this sample (D24)")


def threshold(c: Ctx) -> Problem | None:
    return None if c.value == labels.THRESHOLDS[c.field] else _mismatch(f"thresholds.{c.field} is {labels.THRESHOLDS[c.field]} (D24)")


def arsenal_pitches(c: Ctx) -> Problem | None:
    thrown = [cell for cell in _mix_rows(c, c.slot)]
    if c.value is None:
        # Unknown (F21: his Statcast answer was incomplete, so none of it is used): there is no pitch of his in the mix
        if thrown:
            return _mismatch("the pitch count is unknown but the pitch mix has pitches thrown by this starter")
        return None
    if c.value < 0:
        return ("rule1:wrong_type", f"{c.value!r} is not a count")
    if c.value == 0 and thrown:
        return ("rule2:zero_without_evidence", "pitches is 0 but the pitch mix has pitches thrown by this starter")
    if c.value > 0 and not thrown:
        return _mismatch(f"{c.value} pitches but no pitch in the mix")
    return None


def rate_count(c: Ctx) -> Problem | None:
    """
    A count of batters faced, strikeouts, walks or home runs. Unknown is null: a source that is
    `unavailable` has no number. A zero is evidence-backed when the source measured it: the MLB API line
    gave it, or Statcast saw the plate appearances (batters faced above zero, or no pitch at all).
    """

    value = c.value
    if value is None:
        return None
    rates = c.around(1)
    source = rates["source"]
    if source == "unavailable":
        return ("rule2:unknown_written_as_value", f"{c.field} is {value!r} but the counts are unavailable")
    if value != 0 or source != "statcast":
        return None
    pitches = c.starter["sample"]["arsenal"]["pitches"]
    if c.field == "batters_faced":
        if pitches:
            return ("rule2:zero_without_evidence", f"0 batters faced from Statcast with {pitches} pitches: no plate appearance was counted (an unusable `events` column reads like this, F6b)")
        return None
    if not rates["batters_faced"]:
        return ("rule2:zero_without_evidence", f"{c.field} is 0 but no plate appearance was counted")
    return None


def summary_count(c: Ctx) -> Problem | None:
    rates = c.starter["sample"]["rates"]
    source_field = {"home_runs_allowed": "home_runs"}.get(c.field, c.field)
    want = rates[source_field]
    return None if c.value == want else _mismatch(f"season_summary.{c.field} is the count of sample.rates.{source_field} ({want!r})")


# -- the pitch mix and the other charts -------------------------------------------------------------


def mix_cell(c: Ctx) -> Problem | None:
    """One starter's cell of a pitch: `count` and `total` are raw, `overall` is their share, `vs_*` a share against one side."""

    cell = c.around(1)
    slot, field, value = c.path[-2], c.field, c.value
    pitches = c.matchup["starters"][slot]["sample"]["arsenal"]["pitches"]
    count, total = cell.get("count"), cell.get("total")
    if field == "total":
        if value == 0 and pitches:
            return ("rule2:zero_without_evidence", f"total is 0 but the starter threw {pitches} pitches")
        return None if not pitches or value in (0, pitches) else _mismatch(f"total is {value} but the sample has {pitches} pitches")
    if field == "count":
        if value == 0 and not total and pitches:
            return ("rule2:zero_without_evidence", "a pitch count of 0 out of no total")
        return None
    if value is None:
        if field == "overall" and total:
            return _mismatch(f"overall is the share count/total ({round(count / total * 100, 1)}), found null: out of {total} pitches there is a share")
        return None
    if not total:
        return ("rule2:zero_without_evidence", f"{field} is {value!r} out of {total!r} pitches: a share of nothing is unknown, not zero")
    if field == "overall":
        want = round(count / total * 100, 1)
        return None if value == want else _mismatch(f"overall is the share count/total ({want}), found {value!r}")
    return None if 0 <= value <= 100 else ("rule1:wrong_type", f"{field} {value!r} is not a percentage")


def velocity(c: Ctx) -> Problem | None:
    if c.value is None:
        return None
    return None if c.value > 0 else ("rule2:zero_without_evidence", f"a velocity of {c.value!r} is not a measurement")


def unit_interval(c: Ctx) -> Problem | None:
    return None if 0 <= c.value <= 1 else ("rule1:wrong_type", f"{c.value!r} is not a position in the plot area")


def movement_family(c: Ctx) -> Problem | None:
    """The family of a pitch is read from the name map; a pitch the map does not know has none."""

    name = c.path[-2]
    want = labels.PITCH_FAMILY.get(name)
    if c.value == want:
        return None
    if want is None:
        return ("rule1:invented_derivation", f"{name!r} is not in the pitch family map, yet its family is {c.value!r} (F6e)")
    return _mismatch(f"the family of {name!r} is {want!r}, found {c.value!r}")


# -- teams -------------------------------------------------------------------------------------------


def _team(c: Ctx) -> str:
    return c.path[3]  # matchups[i].teams.<side>....


def _opposing_hand(c: Ctx) -> str:
    """The home lineup faces the away starter and the other way round."""

    slot = "away_starter" if _team(c) == "home" else "home_starter"
    return c.matchup["starters"][slot]["throws"]


def _offense(c: Ctx) -> Mapping[str, Any]:
    return c.matchup["teams"][_team(c)]["offense_profile"]


def _has_figures(offense: Mapping[str, Any]) -> bool:
    return any(offense.get(key) is not None for key in ("ops_vs_hand", "k_rate_vs_hand", "bb_rate_vs_hand"))


def offense_text(c: Ctx) -> Problem | None:
    offense = _offense(c)
    if c.field == "summary_label":
        want = f"Real season split vs {_opposing_hand(c)}HP" if _has_figures(offense) else None
    else:  # recent_form
        want = "Season split" if _has_figures(offense) else None
    return None if c.value == want else _mismatch(f"{c.field} follows the figures of the lineup: expected {want!r}, found {c.value!r}")


# -- the rest of the file ----------------------------------------------------------------------------


def _live_ids(c: Ctx) -> set[str]:
    return {m["id"] for m in c.root["matchups"] if (m.get("data_confidence") or {}).get("level") == LIVE_LEVEL}


def featured_is_live(c: Ctx) -> Problem | None:
    return None if c.value in _live_ids(c) else _mismatch(f"featured_matchup_id {c.value!r} is not a live matchup of the file")


def pitch_data_status(c: Ctx) -> str:
    """`fetched_snapshot` when at least one starter has a pitch on record (`sample.arsenal.pitches`), else `unavailable`."""

    pitched = any(labels.has_pitch_data(starter) for starter in c.matchup["starters"].values())
    return "fetched_snapshot" if pitched else "unavailable"


def critic_review_status(c: Ctx) -> Problem | None:
    """
    The critic writes `reviewed` at the end of its own run, so the status is a derivation (owner, 2026-10-14) -
    but only with its evidence: checks that ran, each with a status of the closed set. Without it the word
    is a constant asserting that a review happened.
    """

    checks = c.around(1).get("checks")
    ok = isinstance(checks, list) and checks and all(isinstance(k, Mapping) and k.get("status") in CRITIC_STATUSES for k in checks)
    if c.value == "reviewed" and ok:
        return None
    return ("rule1:constant_asserts_fact", f"status {c.value!r} with no checks that ran and a known status each")


def step_status(c: Ctx) -> Problem | None:
    step = c.around(1)
    if step.get("agent") in FIXED_STATUS_STEPS:
        return ("rule1:constant_asserts_fact", f"the status of {step.get('agent')!r} is written fixed ({c.value!r}), not read from the result of the step (F19)")
    graded = any(
        claim.get("key") == "generator.workflow.graded" and claim.get("location") == f"agent_workflow.steps[{c.path[2]}].output"
        for claim in c.root.get("claims") or []
    )
    want = "completed" if graded else "not_applicable"
    return None if c.value == want else _mismatch(f"the postgame step is {want!r} by what it reports, found {c.value!r}")


def archive_title(c: Ctx) -> Problem | None:
    matchup = next(m for m in c.root["matchups"] if m["id"] == c.around(1)["id"])
    teams = matchup["teams"]
    want = " vs ".join(labels.team_label(teams[side]["abbreviation"], teams[side]["name"]) for side in ("away", "home"))
    return None if c.value == want else _mismatch(f"the title is made of the teams: expected {want!r}")


def archive_starters(c: Ctx) -> Problem | None:
    matchup = next(m for m in c.root["matchups"] if m["id"] == c.around(1)["id"])
    names = [matchup["starters"][slot]["name"] for slot in SLOTS]
    want = f"{names[0]} vs {names[1]}"
    return None if c.value == want else _mismatch(f"the summary is made of the starters: expected {want!r}")


def game_title(c: Ctx) -> Problem | None:
    teams = c.matchup["teams"]
    want = f"{teams['away']['name']} vs {teams['home']['name']}"
    return None if c.value == want else _mismatch(f"the title is made of the teams: expected {want!r}")


def team_id_matches(c: Ctx) -> Problem | None:
    side = "away" if c.field == "away_team_id" else "home"
    want = c.matchup["teams"][side]["id"]
    return None if c.value == want else _mismatch(f"{c.field} is the id of teams.{side} ({want!r})")


def starter_team(c: Ctx) -> Problem | None:
    side = "away" if c.slot == "away_starter" else "home"
    want = c.matchup["teams"][side]["abbreviation"]
    return None if c.value == want else _mismatch(f"the team of the starter is teams.{side}.abbreviation ({want!r})")


# --- the manifest ----------------------------------------------------------------------------------

M = "matchups[]."


def _source(pattern: str, origin: str, types: tuple[type, ...] = (), nullable: bool = False, check: Check | None = None) -> Entry:
    return Entry(pattern, SOURCE, origin, types, nullable, check)


def _derived(pattern: str, origin: str, types: tuple[type, ...] = (), nullable: bool = False, check: Check | None = None) -> Entry:
    return Entry(pattern, DERIVATION, origin, types, nullable, check)


def _label(pattern: str, origin: str, types: tuple[type, ...] = (str,), check: Check | None = None) -> Entry:
    return Entry(pattern, LABEL, origin, types, False, check)


def _claim(pattern: str) -> Entry:
    return Entry(pattern, CLAIM, "a recorded phrase; rule 4 owns its condition", (str,), False, None)


def _record(pattern: str) -> Entry:
    """The record of the phrases (`claims`): ids, keys, arguments of any type, `null` for no subject or place."""

    return Entry(pattern, CLAIM, "the record of the recorded phrases; rule 4 verifies it", (), True, None)


def _fact(pattern: str, finding: str, origin: str) -> Entry:
    return Entry(pattern, FACT, origin, (), True, None, finding)


STR = (str,)
SCOPE_PARTS = ("kind", "through", "label")


def _scope_entries(prefix: str, origin: str, nullable_parent: bool = False) -> list[Entry]:
    entries = [_derived(f"{prefix}.{part}", origin, STR, False, scope_part) for part in SCOPE_PARTS]
    if nullable_parent:
        entries.append(_derived(prefix, origin, (), True))
    return entries


MANIFEST: tuple[Entry, ...] = tuple(
    [
        # -- the file
        _label("featured_matchup_id", "the id of the featured slot", STR, featured_is_live),
        _label("metadata.project_name", "the name of the product"),
        _label("metadata.version", "the schema version", STR, equals(lambda c: SCHEMA_VERSION, "the schema version")),
        _label("metadata.language", "the catalog the keys of the claims belong to"),
        _derived("metadata.data_mode", "the generator's reading of the live run", STR, False, equals(lambda c: LIVE_MODE, "a live file")),
        _source("metadata.generated_at", "the time of the live run (F9: the fetch and the build are not told apart yet)", STR, False, is_instant),
        _claim("metadata.last_updated_label"),
        _fact("metadata.data_sources[]", "F3", "names the sources the file uses; a live file lists 'Cached demo snapshots'"),
        _derived("metadata.data_status.mode", "the generator's reading of the live run", STR, False, equals(lambda c: LIVE_MODE, "a live file")),
        _source("metadata.data_status.reason", "the run record; rule 8 judges its shape", (str, dict)),
        _source("metadata.data_status.live_run.**", "the run record; rule 8 judges its shape", (), True),
        _label("disclaimers[]", "a disclaimer; rule 6 judges its wording in a live file"),
        _record("claims[].**"),
        _claim("agent_workflow.description"),
        _label("agent_workflow.steps[].agent", "the name of an agent", STR, in_set((*FIXED_STATUS_STEPS, POSTGAME_STEP))),
        _derived("agent_workflow.steps[].status", "the postgame step reads its result; the other four are written fixed (F19)", STR, False, step_status),
        _claim("agent_workflow.steps[].output"),
        # -- the archive (live rows)
        _label("archive[].id", "the id of the matchup", STR),
        _source("archive[].date", "the official date of the game", STR, False, is_date),
        _derived("archive[].title", "the abbreviations of the two teams", STR, False, archive_title),
        _fact("archive[].status", "F5", "the state of the game written as `upcoming` without reading the schedule"),
        _label("archive[].featured", "whether the row is the featured one", (bool,)),
        _derived("archive[].starter_summary", "the names of the two starters", STR, False, archive_starters),
        _fact("archive[].result_label", "F5", "'Pregame report available' is written for any game, whatever its state"),
        _source("archive[].grade_label", "the postgame; none exists for a pregame row", (), True, is_none),
        # -- the matchup
        _label(M + "id", "the id of the matchup", STR),
        _source(M + "date", "the official date of the game (schedule `officialDate`)", STR, False, is_date),
        _fact(M + "status", "F5", "written as `upcoming` without reading the schedule's `abstractGameState`"),
        _label(M + "is_featured", "whether the matchup is the featured one", (bool,)),
        _derived(M + "game.title", "the names of the two teams", STR, False, game_title),
        _source(M + "game.venue", "schedule venue name", STR, True),
        _source(M + "game.start_time_utc", "schedule `gameDate`", STR, False, is_utc),
        _source(M + "game.start_time_local", "no live source: the page converts the UTC instant (D33)", (), True, is_none),
        _source(M + "game.timezone", "schedule venue time zone", STR, True, is_zone),
        _source(M + "game.broadcast_note", "no live source", (), True, is_none),
        _derived(M + "game.home_team_id", "the id of teams.home", STR, False, team_id_matches),
        _derived(M + "game.away_team_id", "the id of teams.away", STR, False, team_id_matches),
        _source(M + "teams.*.id", "schedule team id", STR, False, is_digits),
        _source(M + "teams.*.name", "schedule team name", STR),
        _source(M + "teams.*.abbreviation", "schedule team abbreviation, or the id and name maps; none for a team they do not know", STR, True, team_abbreviation),
        _source(M + "teams.*.record", "no live source", (), True, is_none),
        _derived(M + "teams.*.offense_profile.summary_label", "present iff the lineup has a figure", STR, True, offense_text),
        _derived(M + "teams.*.offense_profile.vs_pitcher_hand", "the hand of the starter this lineup faces", STR, False, equals(lambda c: f"{_opposing_hand(c)}HP", "the hand of the opposing starter")),
        _source(M + "teams.*.offense_profile.ops_vs_hand", "Savant plate appearances against that hand", STR, True, matches(_OPS, "an OPS")),
        _source(M + "teams.*.offense_profile.k_rate_vs_hand", "Savant plate appearances against that hand", STR, True, matches(_PERCENT, "a percentage")),
        _source(M + "teams.*.offense_profile.bb_rate_vs_hand", "Savant plate appearances against that hand", STR, True, matches(_PERCENT, "a percentage")),
        _derived(M + "teams.*.offense_profile.recent_form", "present iff the lineup has a figure", STR, True, offense_text),
        *_scope_entries(M + "teams.*.offense_profile.scope", "the cutoff of the run (D29); null when the lineup has no figure", True),
        # -- the starters
        _source(M + "starters.*.id", "schedule probable pitcher id", STR, False, is_digits),
        _source(M + "starters.*.name", "schedule probable pitcher name", STR),
        _derived(M + "starters.*.team", "the abbreviation of his team; none when his team has none", STR, True, starter_team),
        _source(M + "starters.*.throws", "the Statcast frame, or the MLB people endpoint; never guessed", STR, False, in_set(HANDS)),
        _source(M + "starters.*.bio", "no live source yet (P1.5)", (), True, is_none),
        _source(M + "starters.*.recent_form", "no live source yet", (), True, is_none),
        _source(M + "starters.*.season_summary.era", "MLB API season line", STR, False, season_text),
        _source(M + "starters.*.season_summary.whip", "MLB API season line", STR, False, season_text),
        _source(M + "starters.*.season_summary.innings", "MLB API season line", STR, False, season_text),
        _derived(M + "starters.*.season_summary.strikeouts", "the count of sample.rates", (int,), True, summary_count),
        _derived(M + "starters.*.season_summary.walks", "the count of sample.rates", (int,), True, summary_count),
        _derived(M + "starters.*.season_summary.home_runs_allowed", "the count of sample.rates.home_runs", (int,), True, summary_count),
        *_scope_entries(M + "starters.*.season_summary.scopes.season_rates", "the scope of the MLB API line", True),
        *_scope_entries(M + "starters.*.season_summary.scopes.counts", "the scope of the source of the counts", True),
        _derived(M + "starters.*.pitching_profile.primary_pitch", "the most thrown pitch of the mix", STR, False, profile_field),
        _derived(M + "starters.*.pitching_profile.putaway_pitch", "the second pitch if it is 15% or more (D30)", STR, False, profile_field),
        _derived(M + "starters.*.pitching_profile.style_label", "the primary and put-away pitch, or limited", STR, False, profile_field),
        _derived(M + "starters.*.pitching_profile.swing_miss_label", "strikeout rate band (D24, D25)", STR, True, profile_field),
        _derived(M + "starters.*.pitching_profile.command_label", "walk rate band (D24, D25)", STR, True, profile_field),
        _derived(M + "starters.*.pitching_profile.contact_risk_label", "no live rate label (D24)", STR, True, profile_field),
        replace(_source(M + "starters.*.sample.arsenal.pitches", "the Statcast pitch rows up to the cutoff; null when the answer was incomplete (F21)", (int,), True, arsenal_pitches), check_null=True),
        *_scope_entries(M + "starters.*.sample.arsenal.scope", "the games the Statcast rows cover; null when the pitch count is unknown", True),
        _source(M + "starters.*.sample.rates.batters_faced", "the MLB API line, or the Statcast plate appearances", (int,), True, rate_count),
        _source(M + "starters.*.sample.rates.strikeouts", "the MLB API line, or the Statcast plate appearances", (int,), True, rate_count),
        _source(M + "starters.*.sample.rates.walks", "the MLB API line, or the Statcast plate appearances", (int,), True, rate_count),
        _source(M + "starters.*.sample.rates.home_runs", "the MLB API line, or the Statcast plate appearances", (int,), True, rate_count),
        _derived(M + "starters.*.sample.rates.source", "which source gave the counts", STR, False, in_set(RATES_SOURCES)),
        *_scope_entries(M + "starters.*.sample.rates.scope", "the scope of the source of the counts; null when they are unavailable", True),
        _derived(M + "starters.*.sample.limited.*", "below the minimum sample (D24)", (bool,), False, limited_flag),
        _label(M + "starters.*.sample.thresholds.*", "the minimum samples of D24", (int,), threshold),
        # -- the charts
        _source(M + "charts.pitch_mix", "Statcast pitches of both starters (empty: nobody threw one)"),
        _source(M + "charts.pitch_mix[].pitch", "Statcast `pitch_type` through the name map", STR),
        _source(M + "charts.pitch_mix[].*.count", "Statcast pitch rows", (int,), False, mix_cell),
        _source(M + "charts.pitch_mix[].*.total", "Statcast pitch rows", (int,), False, mix_cell),
        replace(_derived(M + "charts.pitch_mix[].*.overall", "count / total; null out of no pitches", NUMERIC, True, mix_cell), check_null=True),
        _derived(M + "charts.pitch_mix[].*.vs_lhh", "share against left-handed batters; unknown if he faced none", NUMERIC, True, mix_cell),
        _derived(M + "charts.pitch_mix[].*.vs_rhh", "share against right-handed batters; unknown if he faced none", NUMERIC, True, mix_cell),
        _source(M + "charts.velocity_by_pitch", "Statcast release speed (empty: no pitch)"),
        _source(M + "charts.velocity_by_pitch[].pitch", "Statcast `pitch_type` through the name map", STR),
        _source(M + "charts.velocity_by_pitch[].*", "mean release speed; none for the starter who did not throw it", NUMERIC, True, velocity),
        _source(M + "charts.strength_profile", "no live source for the 0-100 scores: always empty"),
        _source(M + "charts.pitch_movement.*", "Statcast movement (empty: no pitch)"),
        _source(M + "charts.pitch_movement.*.*.h_break", "Statcast `pfx_x`, median; none under three observations", NUMERIC, True),
        _source(M + "charts.pitch_movement.*.*.v_break", "Statcast `pfx_z`, median; none under three observations", NUMERIC, True),
        _derived(M + "charts.pitch_movement.*.*.family", "the pitch family map", STR, True, movement_family),
        _label(M + "pitch_locations.note", "describes the coordinate system, nothing about a game"),
        _source(M + "pitch_locations.*.*", "Statcast plate location (empty: too few pitches)"),
        _source(M + "pitch_locations.*.*[].pitch", "Statcast `pitch_type` through the name map", STR),
        _source(M + "pitch_locations.*.*[].x", "median Statcast `plate_x`, normalized", NUMERIC, False, unit_interval),
        _source(M + "pitch_locations.*.*[].y", "median Statcast `plate_z`, normalized", NUMERIC, False, unit_interval),
        # -- the sentences and the state of the report
        _source(M + "postgame", "no live postgame until P1.2", (), True, is_none),
        _derived(M + "data_confidence.level", "set only for a matchup built from a snapshot game", STR, False, equals(lambda c: LIVE_LEVEL, "a live matchup")),
        _fact(M + "data_confidence.lineup_status", "F5", "written as `probable_pitchers` without reading the schedule"),
        _derived(M + "data_confidence.pitch_data_status", "`fetched_snapshot` when at least one starter has pitch data, else `unavailable`", STR, False, equals(pitch_data_status, "the status of the starters' pitch data")),
        _claim(M + "data_confidence.notes[]"),
        _record(M + "report.claims[].**"),
        _claim(M + "report.**"),
        _claim(M + "critic_review.summary"),
        _derived(M + "critic_review.status", "written by the critic at the end of its run; needs checks that ran", STR, False, critic_review_status),
        _claim(M + "critic_review.checks[].claim"),
        _claim(M + "critic_review.checks[].evidence"),
        _derived(M + "critic_review.checks[].status", "the verdict of the check", STR, False, in_set(CRITIC_STATUSES)),
        _claim(M + "critic_review.revision_notes[]"),
    ]
)


# --- matching and walking --------------------------------------------------------------------------


def _compile(pattern: str) -> re.Pattern[str]:
    parts = []
    for token in re.split(r"(\.\*\*|\*)", pattern):  # `.**`: the field itself or anything below it
        if token == ".**":
            parts.append(r"(?:[.\[].*)?")
        elif token == "*":
            parts.append(r"[^.\[\]]+")
        else:
            parts.append(re.escape(token))
    return re.compile("".join(parts))


_COMPILED = [(entry, _compile(entry.pattern)) for entry in MANIFEST]


def normalize(path: tuple) -> str:
    text = ""
    for part in path:
        text += "[]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text


def entry_for(normalized: str) -> Entry | None:
    return next((entry for entry, regex in _COMPILED if regex.fullmatch(normalized)), None)


def _leaves(node: Any, path: tuple = ()):
    if isinstance(node, Mapping) and node:
        for key, child in node.items():
            yield from _leaves(child, (*path, key))
    elif isinstance(node, list) and node:
        for index, child in enumerate(node):
            yield from _leaves(child, (*path, index))
    else:
        yield path, node  # a scalar, None, or an empty list or map


def _where(path: tuple) -> str:
    return "".join(f"[{part}]" if isinstance(part, int) else (f".{part}" if i else str(part)) for i, part in enumerate(path))


def _is_live_matchup(matchup: Any) -> bool:
    return isinstance(matchup, Mapping) and (matchup.get("data_confidence") or {}).get("level") == LIVE_LEVEL


def _in_scope(payload: Mapping[str, Any], path: tuple) -> bool:
    """Demo matchups and archive rows of a live file are rule 6's finding, not walked here."""

    if path and path[0] == "matchups":
        return _is_live_matchup(payload["matchups"][path[1]])
    if path and path[0] == "archive":
        live = {m.get("id") for m in payload["matchups"] if _is_live_matchup(m)}
        return payload["archive"][path[1]].get("id") in live
    return True


def _type_problem(entry: Entry, value: Any) -> Problem | None:
    if value is None:
        return None
    if not entry.types:
        return None
    is_bool = isinstance(value, bool)
    if isinstance(value, entry.types) and (not is_bool or bool in entry.types):
        return None
    if isinstance(value, str) and any(t in entry.types for t in NUMERIC) and str not in entry.types:
        return ("rule2:unknown_written_as_value", f"{value!r} is text in a numeric field")
    return ("rule1:wrong_type", f"{value!r} is a {type(value).__name__}, expected {', '.join(t.__name__ for t in entry.types)}")


def _count(value: Any) -> int | None:
    """A figure as a whole number, or None when it is unknown (or not a number: the manifest reports that)."""

    return value if isinstance(value, int) and not isinstance(value, bool) else None


def impossible_figures(payload: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """
    (code, place, message) for every starter whose figures cannot be true together (F21, rule 1).

    A home run is a batter faced; a strikeout, a walk and a home run are different plate appearances; and every
    batter faced took a typed pitch. A starter that breaks one is published with figures from two different
    samples. Only a starter with a `sample` (what a live run measures) has figures to compare, and a figure that
    is unknown (`None`) is not compared. The one tolerance, documented in the contract (6.5): an intentional walk
    is a batter with no typed pitch, so `batters_faced <= pitches` could fail only for a sample smaller than one
    pitch per batter.
    """

    found: list[tuple[str, str, str]] = []
    for position, matchup in enumerate(payload.get("matchups") or []):
        starters = matchup.get("starters") if isinstance(matchup, Mapping) else None
        if not isinstance(starters, Mapping):
            continue
        label = matchup.get("id") or f"matchups[{position}]"
        for slot in SLOTS:
            starter = starters.get(slot)
            sample = starter.get("sample") if isinstance(starter, Mapping) else None
            if not isinstance(sample, Mapping):
                continue
            rates, arsenal = sample.get("rates") or {}, sample.get("arsenal") or {}
            batters = _count(rates.get("batters_faced"))
            home_runs, strikeouts, walks = (_count(rates.get(key)) for key in ("home_runs", "strikeouts", "walks"))
            pitches = _count(arsenal.get("pitches"))
            where = f"{label} {slot}.sample"
            if batters is not None and home_runs is not None and home_runs > batters:
                found.append((
                    f"{IMPOSSIBLE}#home_runs_over_batters_faced", where,
                    f"{home_runs} home runs against {batters} batters faced",
                ))
            outcomes = [value for value in (strikeouts, walks, home_runs) if value is not None]
            if batters is not None and len(outcomes) == 3 and sum(outcomes) > batters:
                found.append((
                    f"{IMPOSSIBLE}#outcomes_over_batters_faced", where,
                    f"{strikeouts} strikeouts, {walks} walks and {home_runs} home runs are {sum(outcomes)} "
                    f"plate appearances, against {batters} batters faced",
                ))
            if batters is not None and pitches is not None and batters > pitches:
                found.append((
                    f"{IMPOSSIBLE}#batters_faced_over_pitches", where,
                    f"{batters} batters faced against {pitches} pitches",
                ))
    return found


def findings(payload: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """(code, place, message) for every violation of rules 1 and 2 in a live payload."""

    if (payload.get("metadata") or {}).get("data_mode") != LIVE_MODE:
        return []
    found: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(code: str, place: str, where: str, message: str) -> None:
        key = (f"{code}#{place}", where)
        if key not in seen:
            seen.add(key)
            found.append((key[0], where, message))

    for path, value in _leaves(payload):
        if not _in_scope(payload, path):
            continue
        normalized, where = normalize(path), _where(path)
        entry = entry_for(normalized)
        if entry is None:
            add("rule1:unlisted", normalized, where, f"no entry of the manifest says where {where} comes from")
            continue
        if entry.kind == FACT:
            add("rule1:constant_asserts_fact", entry.pattern, where, f"{entry.origin} ({entry.finding})")
            continue
        if value is None:
            if not entry.nullable:
                add("rule1:null_not_declared", entry.pattern, where, "the field is unavailable but its entry does not allow it")
            elif entry.check_null and entry.check is not None:
                try:
                    null_problem = entry.check(Ctx(payload, path, value))
                except (AttributeError, IndexError, KeyError, StopIteration, TypeError, ValueError) as exc:
                    null_problem = _mismatch(f"cannot be checked against its neighbours ({type(exc).__name__}: {exc})")
                if null_problem is not None:
                    add(null_problem[0], entry.pattern, where, null_problem[1])
            continue
        problem = _type_problem(entry, value)
        if problem is None and entry.check is not None:
            try:
                problem = entry.check(Ctx(payload, path, value))
            except (AttributeError, IndexError, KeyError, StopIteration, TypeError, ValueError) as exc:
                # What the check reads is malformed (its own leaf says so): fail closed, never skip.
                problem = _mismatch(f"cannot be checked against its neighbours ({type(exc).__name__}: {exc})")
        if problem is not None:
            add(problem[0], entry.pattern, where, problem[1])
    found += impossible_figures(payload)
    return found
