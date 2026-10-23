"""A postponed or cancelled game is never a game that was played (P1 task c, D40, rule 7).

The schedule sends a game that was not played as `abstractGameState` "Final" and the truth in `detailedState`
("Postponed", "Cancelled"; measured on 2026-10-16 over 208 games). D40 made `schema.GAME_STATUS` the one table that reads
the pair. Two readers still took "Final" alone: `fetch_series_status`, which counted a postponed game in the standing of
a series, and `games_today[].status` of the snapshot. Both now go through the table.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

import pytest

from data_pipeline.fetchers import live_pipeline as lp
from tests.test_fetchers_as_of import _GAMES, _game_entry, install_urlopen, query, stub_season_dates  # noqa: F401

GAME_3 = 103
NOT_PLAYED = [("Final", "Postponed"), ("Final", "Cancelled")]


def router(overrides: dict[int, dict]):
    """The series schedule of tests.test_fetchers_as_of, with some entries changed."""

    def entry(pk: int) -> dict:
        game = _game_entry(pk)
        game.update(overrides.get(pk, {}))
        return game

    def route(url: str) -> dict:
        if "gamePk" in query(url):
            return {"dates": [{"games": [entry(int(query(url)["gamePk"]))]}]}
        return {"dates": [{"games": [entry(pk) for pk in sorted(_GAMES)]}]}

    return route


def state(abstract: str, detailed: str | None) -> dict:
    status = {"abstractGameState": abstract}
    if detailed is not None:
        status["detailedState"] = detailed
    return {"status": status}


@pytest.fixture(autouse=True)
def fresh_run_errors(monkeypatch):
    monkeypatch.setattr(lp, "_run_errors", [])


# --- the standing of a series ------------------------------------------------------------------------------------------


@pytest.mark.parametrize("abstract, detailed", NOT_PLAYED)
def test_a_postponed_or_cancelled_game_is_not_in_the_standing(monkeypatch, abstract, detailed):
    # Game 2 (10-04) was not played; game 1 was. Before game 3 the standing is the one after game 1.
    install_urlopen(monkeypatch, router({102: state(abstract, detailed)}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert (result["games_played"], result["source_game_pk"]) == (1, 101)
    assert result["result"] == "LAD leads 1-0"
    assert lp._run_errors == []


@pytest.mark.parametrize("abstract, detailed", NOT_PLAYED)
def test_a_series_whose_only_earlier_game_was_not_played_is_zero_zero(monkeypatch, abstract, detailed):
    install_urlopen(monkeypatch, router({101: state(abstract, detailed)}))

    result = lp.fetch_series_status(102, as_of="2026-10-03")

    assert result["games_played"] == 0
    assert (result["wins"], result["losses"]) == (0, 0)
    assert result["source_game_pk"] is None


@pytest.mark.parametrize("detailed", ["Final", "Game Over", "Completed Early"])
def test_a_game_that_ended_still_counts(monkeypatch, detailed):
    # Control: the three pairs of the table that mean "final" are counted.
    install_urlopen(monkeypatch, router({102: state("Final", detailed)}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert (result["games_played"], result["source_game_pk"]) == (2, 102)


@pytest.mark.parametrize("abstract, detailed", [("Live", "In Progress"), ("Preview", "Scheduled")])
def test_a_game_that_has_not_ended_never_counts(monkeypatch, abstract, detailed):
    install_urlopen(monkeypatch, router({102: state(abstract, detailed)}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert result["source_game_pk"] == 101


@pytest.mark.parametrize("abstract, detailed", [("Final", "Suspended"), ("Final", "Completed Early: Rain"), ("Final", "Some New State")])
def test_a_state_the_table_does_not_know_is_a_failed_source_not_a_game_that_was_not_played(monkeypatch, abstract, detailed):
    # Skipping it would give the standing of an earlier game as if this one had not been played; counting it would
    # trust a state nobody has measured. Neither is a value, so the standing is unavailable.
    install_urlopen(monkeypatch, router({102: state(abstract, detailed)}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert result == {}
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("mlb_series_status", "malformed_response")]


def test_an_unknown_state_of_a_game_outside_the_series_or_after_the_cutoff_is_not_read(monkeypatch):
    # Control: only the earlier games of this series are classified; game 4 (10-07) is after the cutoff.
    install_urlopen(monkeypatch, router({104: state("Final", "Some New State")}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert result["source_game_pk"] == 102 and lp._run_errors == []


def test_a_series_game_without_its_detailed_state_is_a_failed_source_not_a_played_game(monkeypatch):
    # The source always sends `detailedState`. Without it the pair is unknown: the answer is refused whole, because
    # a standing built by guessing which entries were played could be wrong.
    install_urlopen(monkeypatch, router({102: state("Final", None)}))

    result = lp.fetch_series_status(GAME_3, as_of="2026-10-05")

    assert result == {}
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("mlb_series_status", "malformed_response")]


# --- the games of the day ------------------------------------------------------------------------------------------------


def snapshot_status(monkeypatch, abstract: str | None, detailed: str | None) -> str | None:
    game = {
        "game_pk": 1,
        "official_date": "2026-07-15",
        "away_team": "Boston Red Sox",
        "away_team_id": 111,
        "away_team_abbr": "BOS",
        "home_team": "New York Yankees",
        "home_team_id": 147,
        "home_team_abbr": "NYY",
        "away_pitcher_name": "Away Ace",
        "away_pitcher_id": 11,
        "home_pitcher_name": "Home Ace",
        "home_pitcher_id": 22,
        "venue": "Yankee Stadium",
        "start_time_utc": "2026-07-15T23:05:00Z",
        "status": abstract,
        "detailed_state": detailed,
    }
    starter = {
        "pitch_mix": [
            {"pitch": "Four-seam", "away_starter": {"overall": 50, "vs_lhh": 50, "vs_rhh": 50, "count": 50, "total": 100}}
        ],
        "velocity_by_pitch": [{"pitch": "Four-seam", "away_starter_velocity": 94.0}],
    }
    monkeypatch.setattr(lp, "fetch_todays_games", lambda target: [game])
    monkeypatch.setattr(lp, "fetch_pitcher_statcast", lambda pid, name, **kw: {"name": name, **deepcopy(starter)})
    monkeypatch.setattr(lp, "fetch_team_splits", lambda tid, **kw: {})

    snapshot = lp.build_live_snapshot("2026-07-15", as_of="2026-07-14")

    return snapshot["games_today"][0]["status"]


@pytest.mark.parametrize("abstract, detailed", NOT_PLAYED)
def test_a_postponed_or_cancelled_game_of_the_day_is_not_final(monkeypatch, abstract, detailed):
    assert snapshot_status(monkeypatch, abstract, detailed) is None


@pytest.mark.parametrize(
    "abstract, detailed, status",
    [
        ("Final", "Final", "final"),
        ("Final", "Game Over", "final"),
        ("Live", "In Progress", "live"),
        ("Preview", "Scheduled", "upcoming"),
        (None, None, None),
    ],
)
def test_the_status_of_a_game_of_the_day_is_the_one_of_the_table(monkeypatch, abstract, detailed, status):
    assert snapshot_status(monkeypatch, abstract, detailed) == status


# --- the class: no reader takes "Final" alone ------------------------------------------------------------------------------


def test_no_fetcher_compares_a_schedule_state_with_final():
    # `schema.GAME_STATUS` is the one reader of the schedule's states (D40). A comparison with the literal "Final"
    # anywhere else in the fetchers is the same mistake as the two readers above (the registry compares the published
    # state of a payload, not the schedule's).
    root = Path(__file__).resolve().parent.parent / "data_pipeline" / "fetchers"
    comparison = re.compile(r"""(==|!=|\bin\b)\s*[(\[{]?\s*["']Final["']|["']Final["']\s*(==|!=)""")
    offenders = [
        f"{path.relative_to(root)}:{number}: {line.strip()}"
        for path in sorted(root.rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if comparison.search(line) and not line.lstrip().startswith("#")
    ]
    assert offenders == []
