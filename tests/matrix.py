"""The combination matrix and the hard cases of the data contract (PLAN.md P0.15-D3.3b). Not a test module.

Every scenario runs the whole way with sources that are faked at the network edge only: the schedule, the
MLB stats and people endpoints, Statcast and Savant answer from here; `run_live_pipeline`, the snapshot on
disk, `_resolve_live_input`, `build_payload`, `validate_payload` and `check_contract` are the real ones.

The matrix is the product of five conditions (docs/DATA_CONTRACT.md, section 5.3), 72 cases:

    API         complete (a whole line), partial (ERA, WHIP, innings and strikeouts only), absent (the request fails)
                The line is a function of the starter's frame (`stat_line`): both sources describe the same starter,
                as the real ones do (a gap of 0 in 28 real pitchers, tests/test_statcast_vs_api.py). A starter with no
                pitch on record (a debut, or any starter on opening day) has no line: the valid empty answer, so
                "complete" and "partial" collapse into it for him.
    season      regular only, or with postseason rows before the cutoff
    starter     debut (no pitch on record), limited (60 pitches), healthy (1,150 pitches)
    day         normal, or opening day (the cutoff falls before the season, so Statcast is never asked)
    hand        in the Statcast frame, or missing from it and answered by the people endpoint (L)

Only the away starter varies; the home starter is always healthy. The hard cases (`HARD_CASES`) cover the
other side of the pair and the awkward members of ENGINEERING.md section 5.

Outcomes are computed once per process (`outcomes()`), so the tests of the matrix, of the table of known
violations and of the differential test share one run.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from functools import cache
import itertools
import json
from pathlib import Path
import re
import tempfile
from typing import Any
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.contract_checks import Violation, check_contract
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from tests.corpus import published
from tests.live_helpers import failed_checks

SEASON_START, SEASON_END = date(2026, 3, 25), date(2026, 9, 27)
OPENING_DAY, REGULAR_DAY, POSTSEASON_DAY = "2026-03-25", "2026-07-04", "2026-10-10"
POSTSEASON_ROW_DATE = "2026-10-02"

API_KINDS = ("complete", "partial", "absent")
SEASONS = ("regular", "postseason")
STARTERS = ("debut", "limited", "healthy")
DAYS = ("normal", "opening")
HANDS = ("present", "missing")

# What the stats endpoint answers about the plate appearances, in the keys the MLB API uses, is built by
# `stat_line` from the frame. These are the figures that do not come from it.
ERA, WHIP = "3.10", "1.05"
# A gap: the API says the starter faced this many more batters than his frame holds (F21). `gap`: 25 more (against an
# empty frame, the extreme case); `gap_season`: 200 more, a season's worth. Each line stays coherent with itself.
GAPS = {
    "gap": {"batters_faced": 25, "strikeouts": 6, "walks": 2, "home_runs": 1, "outs": 16},
    "gap_season": {"batters_faced": 200, "strikeouts": 70, "walks": 15, "home_runs": 8, "outs": 150},
}

# Pitches by code. Away: 1,150 (sinker, slider, changeup); home: 900 (four-seam, curveball, slider).
HEALTHY_MIX = {
    "away": {"SI": 700, "SL": 300, "CH": 150},
    "home": {"FF": 560, "CU": 240, "SL": 100},
}
LIMITED_MIX = {"away": {"SI": 40, "SL": 20}, "home": {"FF": 40, "CU": 20}}
# A plate appearance ends every fourth pitch, in this order.
EVENT_CYCLE = ("strikeout", "field_out", "walk", "single", "strikeout", "field_out", "home_run", "field_out")
FRAME_COLUMNS = (
    "game_date", "game_type", "pitch_type", "stand", "p_throws",
    "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "events",
)


@dataclass(frozen=True)
class Pitcher:
    """One starter as the sources describe him."""

    pid: int
    name: str
    side: str  # "away" or "home"
    throws: str  # what the Statcast frame says, or what the people endpoint answers when the frame does not
    kind: str = "healthy"  # debut | limited | healthy
    # complete | partial | zeros (BB and HR 0 though his rows show some: the zeros are the API's) | absent (the
    # request fails) | empty (a valid empty answer) | gap, gap_season (the API says he faced 25 / 200 batters more than
    # his frame holds)
    api: str = "complete"
    postseason: bool = False  # the frame has postseason rows before the cutoff
    hand_in_frame: bool = True
    lookup: str | None = None  # what the people endpoint answers; None: his hand; "FAIL": the request fails
    events: str = "ok"  # ok | null (the column exists and is null in every row)
    drop: tuple[str, ...] = ()  # columns missing from the frame
    null_pitch_type: bool = False  # `pitch_type` null in every row
    null_stand: bool = False  # `stand` null in every row
    mix: dict[str, int] | None = None  # pitches by code, instead of the kind's own


@dataclass(frozen=True)
class Scenario:
    """A whole day of the world: the game, both starters and what each source answers."""

    name: str
    game_day: str
    away: Pitcher
    home: Pitcher
    savant: str = "ok"  # ok | blank (a valid empty month for every team)
    away_team: tuple[int, str] = (111, "Boston Red Sox")
    home_team: tuple[int, str] = (147, "New York Yankees")
    # what the schedule says of the game: (abstractGameState, detailedState); (None, None) sends no status at all
    state: tuple[str | None, str | None] = ("Preview", "Scheduled")
    # a postseason game: (gameType, seriesDescription, seriesGameNumber, gamesInSeries, the schedule's standing text after
    # the game before it, or None for no earlier game played); None for a regular-season game (P1.5-b)
    series: tuple[str, str, int, int, str | None] | None = None


@dataclass(frozen=True)
class Case:
    """One cell of the matrix."""

    api: str
    season: str
    starter: str
    day: str
    hand: str

    @property
    def id(self) -> str:
        return "-".join((self.api, self.season, self.starter, self.day, self.hand))

    @property
    def game_day(self) -> str:
        if self.day == "opening":
            return OPENING_DAY
        return POSTSEASON_DAY if self.season == "postseason" else REGULAR_DAY

    @property
    def effective_starter(self) -> str:
        """Opening day has no pitch to count: whatever the starter was, he is a debut."""

        return "debut" if self.day == "opening" else self.starter

    @property
    def effective_postseason(self) -> bool:
        return self.season == "postseason" and self.day == "normal" and self.effective_starter != "debut"

    @property
    def canonical(self) -> tuple:
        """Cells that must give the same payload: what no source can tell apart."""

        debut = self.effective_starter == "debut"
        # a starter with no pitch on record has no line, so the two answers that carry one say the same thing
        api = "empty" if debut and self.api != "absent" else self.api
        return (
            api,
            self.game_day if self.day == "normal" else OPENING_DAY,
            self.effective_starter,
            self.effective_postseason,
            "lookup" if debut else self.hand,
        )


MATRIX: tuple[Case, ...] = tuple(
    Case(*combination) for combination in itertools.product(API_KINDS, SEASONS, STARTERS, DAYS, HANDS)
)


def scenario_of(case: Case) -> Scenario:
    away = Pitcher(
        11, "Away Ace", "away", "L",
        kind=case.starter, api=case.api,
        postseason=case.season == "postseason",
        hand_in_frame=case.hand == "present",
    )
    home = Pitcher(22, "Home Ace", "home", "R", postseason=case.season == "postseason")
    return Scenario(case.id, case.game_day, away, home)


# --- the faked sources -----------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, payload: Any):
        self._body = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False


def mix_of(pitcher: Pitcher) -> dict[str, int]:
    if pitcher.mix is not None:
        return pitcher.mix
    if pitcher.kind == "debut":
        return {}
    return (HEALTHY_MIX if pitcher.kind == "healthy" else LIMITED_MIX)[pitcher.side]


def event_at(index: int) -> str | None:
    """The event that ends the plate appearance of the pitch at `index`, if any (every fourth pitch does)."""

    return EVENT_CYCLE[(index // 4) % len(EVENT_CYCLE)] if index % 4 == 3 else None


def regular_season_events(pitcher: Pitcher) -> list[str]:
    """The plate appearances of the regular season in the frame, as the API counts them (not the postseason's)."""

    late = lambda index: pitcher.postseason and index % 5 == 0  # noqa: E731
    pitches = sum(mix_of(pitcher).values())
    return [event for index in range(pitches) if (event := event_at(index)) and not late(index)]


def stat_line(pitcher: Pitcher, opening: bool = False) -> dict[str, Any] | None:
    """
    What the stats endpoint answers for `pitcher`: a function of his frame, so that both sources describe the same
    starter (tests/test_statcast_vs_api.py measured a gap of 0 in 28 real pitchers). None is the valid empty answer:
    he has no regular-season plate appearance on record (a debut, or opening day, when nothing was played yet).
    """

    if pitcher.api in ("absent", "empty"):  # the request fails / a valid empty answer
        return None
    events = [] if opening else regular_season_events(pitcher)
    gap = GAPS.get(pitcher.api, dict.fromkeys(("batters_faced", "strikeouts", "walks", "home_runs", "outs"), 0))
    if not events and not gap["batters_faced"]:
        return None
    outs = events.count("strikeout") + events.count("field_out") + gap["outs"]
    line = {
        "era": ERA,
        "whip": WHIP,
        "inningsPitched": f"{outs // 3}.{outs % 3}",
        "strikeOuts": events.count("strikeout") + gap["strikeouts"],
        "baseOnBalls": events.count("walk") + gap["walks"],
        "homeRuns": events.count("home_run") + gap["home_runs"],
        "battersFaced": len(events) + gap["batters_faced"],
    }
    if pitcher.api == "partial":
        return {key: line[key] for key in ("era", "whip", "inningsPitched", "strikeOuts")}
    if pitcher.api == "zeros":
        line.update(baseOnBalls=0, homeRuns=0)
    return line


def pitcher_frame(pitcher: Pitcher) -> pd.DataFrame:
    """The Statcast frame of a pitcher. A debut has none: an empty frame, with no columns."""

    codes = [code for code, count in mix_of(pitcher).items() for _ in range(count)]
    if not codes:
        return pd.DataFrame()
    rows = []
    for index, code in enumerate(codes):
        late = pitcher.postseason and index % 5 == 0
        rows.append(
            {
                "game_date": pd.Timestamp(POSTSEASON_ROW_DATE if late else "2026-06-20"),
                "game_type": "D" if late else "R",
                "pitch_type": None if pitcher.null_pitch_type else code,
                "stand": None if pitcher.null_stand else ("L" if index % 2 else "R"),
                "p_throws": pitcher.throws,
                "release_speed": 88.0 + len(code) + (index % 7) * 0.5,
                "pfx_x": 0.3 + 0.01 * (index % 7),
                "pfx_z": 1.0 + 0.01 * (index % 5),
                "plate_x": -0.4 + 0.05 * (index % 9),
                "plate_z": 1.9 + 0.05 * (index % 11),
                "events": None if pitcher.events == "null" else event_at(index),
            }
        )
    frame = pd.DataFrame(rows, columns=list(FRAME_COLUMNS))
    drop = set(pitcher.drop) | (set() if pitcher.hand_in_frame else {"p_throws"})
    return frame.drop(columns=sorted(drop))


def savant_csv(team_code: str, month_start: str, away_code: str, home_code: str) -> str:
    """Plate appearances of one team in a month, against both hands, in the columns Savant sends."""

    top = team_code == away_code
    rows = []
    for index in range(40):
        rows.append(
            {
                "game_date": f"{month_start[:8]}{2 + index % 20:02d}",
                "game_type": "R",
                "game_pk": 1000 + index,
                "home_team": home_code,
                "away_team": away_code,
                "inning_topbot": "Top" if top else "Bot",
                "p_throws": "L" if index % 3 == 0 else "R",
                "stand": "R",
                "batter": index,
                "at_bat_number": index,
                "events": EVENT_CYCLE[index % len(EVENT_CYCLE)],
            }
        )
    return pd.DataFrame(rows).to_csv(index=False)


@dataclass
class Asked:
    """What the pipeline asked of each source, for the tests that check the sources were or were not used."""

    statcast: list[int] = field(default_factory=list)
    savant: list[str] = field(default_factory=list)
    people: list[int] = field(default_factory=list)
    stats: list[int] = field(default_factory=list)


def _status_of(state: tuple[str | None, str | None]) -> dict[str, Any]:
    """The `status` object of a schedule game, as the schedule sends it: nothing at all, or only the parts it has."""

    abstract, detailed = state
    status = {key: value for key, value in (("abstractGameState", abstract), ("detailedState", detailed)) if value is not None}
    return {"status": status} if status else {}


def install_sources(monkeypatch: pytest.MonkeyPatch, scenario: Scenario, tmp: Path) -> Asked:
    pitchers = {scenario.away.pid: scenario.away, scenario.home.pid: scenario.home}
    asked = Asked()
    away_id, away_name = scenario.away_team
    home_id, home_name = scenario.home_team
    schedule = {
        "dates": [
            {
                "games": [
                    {
                        "gamePk": 777001,
                        "officialDate": scenario.game_day,
                        "gameDate": f"{scenario.game_day}T23:05:00Z",
                        **_status_of(scenario.state),
                        "venue": {"name": "Test Park", "timeZone": {"id": "America/New_York"}},
                        "teams": {
                            "away": {
                                "team": {"id": away_id, "name": away_name},
                                "probablePitcher": {"id": scenario.away.pid, "fullName": scenario.away.name},
                            },
                            "home": {
                                "team": {"id": home_id, "name": home_name},
                                "probablePitcher": {"id": scenario.home.pid, "fullName": scenario.home.name},
                            },
                        },
                    }
                ]
            }
        ]
    }

    if scenario.series is not None:
        game_type, description, number, length, standing_text = scenario.series
        today = schedule["dates"][0]["games"][0]
        today.update(gameType=game_type, seriesDescription=description, seriesGameNumber=number, gamesInSeries=length)

    def series_answer(url: str) -> dict[str, Any]:
        """The two standing requests: the game itself, then the games of the window (one played earlier game)."""

        game_type, _, number, _, standing_text = scenario.series
        teams = {side: {"team": {"id": team}} for side, team in (("away", away_id), ("home", home_id))}
        game = {
            "gamePk": 777001,
            "gameType": game_type,
            "officialDate": scenario.game_day,
            "seriesGameNumber": number,
            "status": {"abstractGameState": "Preview", "detailedState": "Scheduled"},
            "teams": teams,
        }
        if "gamePk" in url:
            return {"dates": [{"games": [game]}]}
        if standing_text is None or number < 2:
            return {"dates": []}
        numbers = re.findall(r"(\d)-(\d)", standing_text)
        wins, losses = (int(numbers[0][0]), int(numbers[0][1])) if numbers else (0, 0)
        earlier = {
            "gamePk": 777000,
            "gameType": game_type,
            "officialDate": (date.fromisoformat(scenario.game_day) - timedelta(days=1)).isoformat(),
            "seriesGameNumber": number - 1,
            "status": {"abstractGameState": "Final", "detailedState": "Final"},
            "teams": teams,
            "seriesStatus": {"wins": wins, "losses": losses, "isOver": False, "result": standing_text},
        }
        return {"dates": [{"games": [earlier]}]}

    def urlopen(req: Any, timeout: Any = None) -> FakeResponse:
        url = req.full_url if hasattr(req, "full_url") else req
        if "schedule" in url:
            if scenario.series is not None and "hydrate=seriesStatus" in url:
                return FakeResponse(series_answer(url))
            return FakeResponse(schedule)
        if "/stats?" in url:
            pitcher = pitchers[int(re.search(r"/people/(\d+)/stats", url).group(1))]
            asked.stats.append(pitcher.pid)
            if pitcher.api == "absent":
                raise OSError("MLB stats API unreachable")
            line = None if pitcher.api == "empty" else stat_line(pitcher, opening=scenario.game_day == OPENING_DAY)
            if line is None:
                return FakeResponse({"stats": [{"splits": []}]})
            return FakeResponse({"stats": [{"splits": [{"stat": line}]}]})
        person = re.search(r"/people/(\d+)$", url)
        if person:
            pitcher = pitchers[int(person.group(1))]
            asked.people.append(pitcher.pid)
            if pitcher.lookup == "FAIL":
                raise OSError("MLB people endpoint unreachable")
            return FakeResponse({"people": [{"pitchHand": {"code": pitcher.lookup or pitcher.throws}}]})
        raise AssertionError(f"unexpected URL {url}")

    def statcast(start: str, end: str, player_id: int) -> pd.DataFrame:
        asked.statcast.append(player_id)
        return pitcher_frame(pitchers[player_id])

    away_code = lp.MLB_TEAM_ABBR_BY_ID.get(away_id, "AAA")
    home_code = lp.MLB_TEAM_ABBR_BY_ID.get(home_id, "HHH")

    def savant(url: str, timeout: int = 60) -> str:
        asked.savant.append(url)
        if scenario.savant == "blank":
            return ""
        query = {key: values[0] for key, values in parse_qs(urlparse(url).query).items()}
        return savant_csv(query["team"], query["game_date_gt"], away_code, home_code)

    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp / "processed")
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp / "team_batting")
    monkeypatch.setattr(lp, "PITCHER_HAND_CACHE_DIR", tmp / "pitcher_hand")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_run_warnings", [])
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0, "open_requests": 0})
    monkeypatch.setattr(lp, "_pitcher_hand_run", {"requests": 0})
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27)))
    monkeypatch.setattr(lp.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(lp, "statcast_pitcher", statcast)
    monkeypatch.setattr(lp, "_get_text", savant)
    return asked


# --- running a scenario ----------------------------------------------------------------------------


@dataclass
class Outcome:
    """What a scenario produced, from the run record to the contract."""

    scenario: Scenario
    asked: Asked
    record: dict[str, Any]
    snapshot: dict[str, Any] | None
    status: dict[str, Any]  # the generator's reading of the run: mode, reason
    payload: dict[str, Any] | None  # after a trip through JSON; None if the generator stopped
    blocked: str | None  # the critic's message when it stopped the generator
    failed: list[str]  # publication checks that fail (`validate_payload`)
    violations: list[Violation]  # every violation of the contract, tolerated or not

    @property
    def live(self) -> bool:
        return self.status["mode"] == "fetched_snapshot"

    @property
    def matchup(self) -> dict[str, Any]:
        """The live matchup (`matchup_001`) of a live outcome."""

        assert self.payload is not None and self.live, f"{self.scenario.name} was not published as live"
        return next(m for m in self.payload["matchups"] if m["id"] == "matchup_001")

    def error_sources(self) -> set[str]:
        return {error["source"] for error in self.record["errors"]}


def run_scenario(scenario: Scenario) -> Outcome:
    """The pipeline, the generator, the publication checks and the contract, over faked sources."""

    with pytest.MonkeyPatch.context() as monkeypatch, tempfile.TemporaryDirectory() as directory:
        asked = install_sources(monkeypatch, scenario, Path(directory))
        lp.main_with_args(scenario.game_day, None)
        record = cache_manager.load_processed("live_run")
        snapshot, status = gdj._resolve_live_input()
        monkeypatch.setattr(gdj, "_live", snapshot)
        monkeypatch.setattr(gdj, "_live_status", status)
        payload, blocked, failed, violations = None, None, [], []
        try:
            built = gdj.build_payload()
        except gdj.CriticBlocked as exc:
            blocked = str(exc)
        else:
            payload = published(built)
            failed = failed_checks(built)
            violations = check_contract(payload)
        return Outcome(scenario, asked, record, snapshot, status, payload, blocked, failed, violations)


def fingerprint(outcome: Outcome) -> str:
    """The payload without the clock of the run, to compare cells that must be the same."""

    payload = json.loads(json.dumps(outcome.payload))
    payload["metadata"]["generated_at"] = None
    payload["metadata"]["data_fetched_at"] = None
    run = payload["metadata"]["data_status"].get("live_run")
    if run:
        run["run_at"] = None
    return json.dumps(payload, sort_keys=True)


# --- the hard cases --------------------------------------------------------------------------------


def _world(name: str, away: Pitcher | None = None, home: Pitcher | None = None, **changes: Any) -> Scenario:
    base = Scenario(
        name,
        REGULAR_DAY,
        away or Pitcher(11, "Away Ace", "away", "L"),
        home or Pitcher(22, "Home Ace", "home", "R"),
    )
    return replace(base, **changes)


def _hard_cases() -> dict[str, Scenario]:
    away = Pitcher(11, "Away Ace", "away", "L")
    home = Pitcher(22, "Home Ace", "home", "R")
    debut = {"kind": "debut", "api": "empty"}
    cases = [
        # the pair, from the side the matrix does not vary
        _world("two_debuts", replace(away, **debut), replace(home, **debut)),
        _world("two_limited", replace(away, kind="limited"), replace(home, kind="limited")),
        _world("home_limited_away_healthy", away, replace(home, kind="limited")),
        _world("home_debut_away_healthy", away, replace(home, **debut)),
        # awkward members (ENGINEERING.md section 5)
        _world("api_zeros_are_zeros", replace(away, api="zeros")),
        # F21: the API says he faced more batters than Statcast holds
        _world("statcast_gap", replace(away, kind="debut", api="gap")),  # an empty frame: not a debut, a gap
        _world("statcast_short", replace(away, kind="limited", api="gap")),  # 15 plate appearances against 40
        _world("statcast_short_season", replace(away, api="gap_season")),  # 287 plate appearances against 487
        _world("two_gaps", replace(away, kind="debut", api="gap"), replace(home, kind="debut", api="gap")),  # both sides
        _world("unknown_figures", replace(away, kind="debut", api="gap"), replace(home, events="null", api="absent")),
        _world("no_offense_data", savant="blank"),
        # QA5-01 / probe A: one starter's sixth pitch is the opponent's primary.
        _world("six_type_overlap",
               replace(away, mix={"FF": 400, "SI": 300, "SL": 200, "CH": 150, "CU": 90, "FC": 10}),
               replace(home, mix={"FC": 600, "SL": 300})),
        _world("six_type_overlap_reversed",
               replace(away, mix={"FC": 600, "SL": 300}),
               replace(home, mix={"FF": 400, "SI": 300, "SL": 200, "CH": 150, "CU": 90, "FC": 10})),
        _world("six_type_no_overlap",
               replace(away, mix={"FF": 400, "SI": 300, "SL": 200, "CH": 150, "CU": 90, "FC": 10}),
               replace(home, mix={"FF": 600, "SL": 300})),
        # Three raw codes are one display pitch; conservation sums every alias.
        _world("six_type_alias_overlap",
               replace(away, mix={"FF": 400, "SI": 300, "SL": 200, "CH": 150, "FC": 90, "CU": 5, "KC": 3, "CS": 2}),
               replace(home, mix={"CU": 600, "SL": 300})),
        _world("events_null_in_every_row", replace(away, events="null", api="absent")),
        _world("pitch_type_null_in_every_row", replace(away, null_pitch_type=True)),
        _world("stand_null_in_every_row", replace(away, null_stand=True)),
        _world("unmapped_pitch_code", replace(away, mix={"XX": 120, "SL": 60})),
        _world("unknown_team", away_team=(999, "Brand New Club")),
        _world("hand_lookup_fails", replace(away, **debut, lookup="FAIL")),
        _world("switch_pitcher", replace(away, **debut, lookup="S")),
        # F5: the state of the game, as the real schedule sends it (a postponed game is Final, 2026-10-16)
        _world("live_state_live", state=("Live", "In Progress")),
        _world("live_state_final", state=("Final", "Final")),
        _world("live_state_postponed", state=("Final", "Postponed")),
        _world("live_state_cancelled", state=("Final", "Cancelled")),
        _world("live_state_suspended", state=("Final", "Suspended")),
        _world("live_state_missing", state=(None, None)),
        _world("live_state_unknown", state=("Preview", "Something New")),
        # P1.5-b: a postseason game with its series (the standing text is what the schedule's seriesStatus says)
        _world("series_standing", series=("L", "AL Championship Series", 3, 7, "BOS leads 2-0"), game_day=POSTSEASON_DAY),
        _world("series_tied", series=("D", "NL Division Series", 3, 5, "Series tied 1-1"), game_day=POSTSEASON_DAY),
        _world("series_opening", series=("W", "World Series", 1, 7, None), game_day=POSTSEASON_DAY),
        _world("series_standing_unavailable", series=("L", "AL Championship Series", 3, 7, "BOS lead two nil"), game_day=POSTSEASON_DAY),
    ]
    cases += [
        _world(f"frame_without_{column}", replace(away, drop=(column,)))
        for column in ("stand", "release_speed", "plate_x", "plate_z", "pitch_type")
    ]
    return {scenario.name: scenario for scenario in cases}


HARD_CASES: dict[str, Scenario] = _hard_cases()


# --- all the outcomes, once ------------------------------------------------------------------------


@cache
def matrix_outcome(case: Case) -> Outcome:
    return run_scenario(scenario_of(case))


@cache
def hard_outcome(name: str) -> Outcome:
    return run_scenario(HARD_CASES[name])


def outcomes() -> dict[str, Outcome]:
    """Every outcome of the matrix and of the hard cases, by name."""

    found = {f"matrix:{case.id}": matrix_outcome(case) for case in MATRIX}
    found.update({f"hard:{name}": hard_outcome(name) for name in HARD_CASES})
    return found
