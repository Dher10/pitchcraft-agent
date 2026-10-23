"""QA6-01: a finite value the sensor cannot have is not a measurement (P0.17-b).

QA run 6 probe B2 put one finite number in a Statcast column and the file published it (`pfx_x` 9999 as a
119,988 in. break; `release_speed` 1e6 as a velocity), and a 1e308 overflowed a mean to `inf` and stopped every
game. Probe E2 did the same with the MLB API: a negative count was published and a placeholder ERA ("-.--", what
a real 0-inning debut returns) stopped the whole file. The same containment as QA5-03 applies: the bad group is
unavailable plus one recorded `malformed_rows`; the game and every other group are published.

Named controls (they pass before the fix): values exactly on a bound, null cells, real placeholders of a debut.
"""

from __future__ import annotations

from copy import deepcopy
import json
import warnings

import pytest

from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import validate_payload
from tests.live_helpers import snapshot_from_starters, use_snapshot
from tests.test_live_sample_pipeline import API_STATS, events_frame, isolated, route  # noqa: F401
from tests.test_nonfinite_numbers import MEASUREMENTS, fetch_pair

# (column, a value the sensor cannot produce, why). One row per side of every bound and a gross value.
OUT_OF_BOUNDS = [
    ("release_speed", 30.0, "the lower bound is exclusive"),
    ("release_speed", 0.0, "zero is not a velocity"),
    ("release_speed", -94.0, "negative"),
    ("release_speed", 110.5, "above the fastest pitch"),
    ("release_speed", 9999.0, "QA6 probe B2"),
    ("release_speed", 1e308, "overflows a mean"),
    ("pfx_x", 3.5, "above 3 ft"),
    ("pfx_x", -3.5, "below -3 ft"),
    ("pfx_x", 9999.0, "QA6 probe B2"),
    ("pfx_x", 1e308, "overflows a median's arithmetic"),
    ("pfx_z", 3.5, "above 3 ft"),
    ("pfx_z", -3.5, "below -3 ft"),
    ("pfx_z", -50.0, "QA6 probe B2"),
    ("pfx_z", 1e308, "overflows"),
    ("plate_x", 5.5, "right of any plate"),
    ("plate_x", -5.5, "left of any plate"),
    ("plate_x", 9999.0, "QA6 probe B2: clipped to the chart edge"),
    ("plate_x", 1e308, "overflows"),
    ("plate_z", -3.5, "under the ground"),
    ("plate_z", 10.5, "above any ball in play"),
    ("plate_z", 9999.0, "QA6 probe B2"),
    ("plate_z", 1e308, "overflows"),
]

# The same columns, exactly on the edge of what is allowed: valid, no error.
ON_THE_EDGE = [
    ("release_speed", 30.1),
    ("release_speed", 110.0),
    ("pfx_x", 3.0),
    ("pfx_x", -3.0),
    ("pfx_z", 3.0),
    ("pfx_z", -3.0),
    ("plate_x", 5.0),
    ("plate_x", -5.0),
    ("plate_z", -3.0),
    ("plate_z", 10.0),
]


def assert_only_the_group_of(away, home, column):
    affected = MEASUREMENTS[column]
    for group in set(MEASUREMENTS.values()) - {affected}:
        assert away[group] == home[group], group
    if affected == "velocity_by_pitch":
        assert away[affected] == []
    elif affected == "movement":
        assert all(m["h_break"] is None and m["v_break"] is None for m in away[affected].values())
    else:
        assert away[affected] == {"vs_lhh": [], "vs_rhh": []}


@pytest.mark.parametrize(("column", "value", "why"), OUT_OF_BOUNDS, ids=[f"{c}={v}" for c, v, _ in OUT_OF_BOUNDS])
@pytest.mark.parametrize("rows", ["all", "one"])
def test_a_value_outside_the_physical_bounds_disables_only_its_group_and_keeps_the_game(monkeypatch, column, value, why, rows):
    source = events_frame()
    source.loc[source.index if rows == "all" else [0], column] = value

    away, home = fetch_pair(monkeypatch, source)

    assert away is not None and home is not None
    assert away["sample"]["arsenal"]["pitches"] == 170
    assert away["sample"]["rates"]["batters_faced"] == 19
    assert away["season_summary"]["era"] == "3.10"
    assert away["pitch_mix"] == home["pitch_mix"]
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("statcast_pitcher", "malformed_rows")]
    assert column in lp._run_errors[0]["message"]
    assert_only_the_group_of(away, home, column)

    use_snapshot(monkeypatch, snapshot_from_starters(away, home))
    payload = gdj.build_payload()
    assert len(payload["matchups"]) == 1
    validate_payload(payload)
    json.dumps(payload, allow_nan=False)


@pytest.mark.parametrize(("column", "value"), ON_THE_EDGE, ids=[f"{c}={v}" for c, v in ON_THE_EDGE])
def test_control_a_value_exactly_on_a_bound_is_a_measurement(monkeypatch, column, value):
    source = events_frame()
    source[column] = value

    away, home = fetch_pair(monkeypatch, source)

    assert away is not None and lp._run_errors == []
    group = away[MEASUREMENTS[column]]
    assert group, "the group of an in-bounds column is published"
    if column == "release_speed":
        assert away["velocity_by_pitch"][0]["away_starter_velocity"] == value
    elif column.startswith("pfx_"):
        axis = "h_break" if column == "pfx_x" else "v_break"
        assert away["movement"]["Four-seam"][axis] == round(value * 12, 1)
    else:
        assert len(away["pitch_locations"]["vs_rhh"]) == 1
    use_snapshot(monkeypatch, snapshot_from_starters(away, home))
    validate_payload(gdj.build_payload())


@pytest.mark.parametrize("column", MEASUREMENTS)
def test_control_a_null_cell_is_still_just_absent(monkeypatch, column):
    source = events_frame()
    source.loc[[0], column] = None

    away, _ = fetch_pair(monkeypatch, source)

    assert away is not None and lp._run_errors == []


def test_the_bounds_are_one_table_covering_every_measurement_column():
    assert set(lp.PITCH_VALUE_BOUNDS) == set(MEASUREMENTS)
    for column, (low, high, _inclusive) in lp.PITCH_VALUE_BOUNDS.items():
        assert low < high, column


# --- the aggregation does not trust the table to be enough ----------------------------------------------------


def test_a_mean_or_median_that_is_not_finite_is_unavailable_never_inf(monkeypatch):
    """Widen the bounds on purpose: the arithmetic must stay safe on its own (defence in depth)."""

    for column in MEASUREMENTS:
        monkeypatch.setitem(lp.PITCH_VALUE_BOUNDS, column, (-1e309, 1e309, True))
    source = events_frame()
    for column in MEASUREMENTS:
        source[column] = 1.7e308  # a finite number whose sum overflows

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        data = lp.process_pitcher_statcast(source, "Alpha Livearm")

    assert data["velocity_by_pitch"] == []
    assert all(m["h_break"] is None and m["v_break"] is None for m in data["movement"].values())
    assert data["pitch_locations"] == {"vs_lhh": [], "vs_rhh": []}
    json.dumps(data, allow_nan=False)


# --- the MLB API: counts and placeholders ----------------------------------------------------------------------

PLACEHOLDERS = ["-.--", ".---", "-", "--", "N/A", "n/a", "abc", "", "inf", "nan", "-1.00", "1,5"]
SEASON_TEXT = {"era": "era", "whip": "whip", "inningsPitched": "innings"}


def api_line(**stat):
    line = deepcopy(API_STATS)
    line["stats"][0]["splits"][0]["stat"].update(stat)
    return line


def fetch_api_line(monkeypatch, line):
    route(monkeypatch, [("/stats?", line)])
    return lp.fetch_pitcher_season_stats(11, as_of="2026-07-14")


@pytest.mark.parametrize("placeholder", PLACEHOLDERS)
@pytest.mark.parametrize("field", SEASON_TEXT)
def test_a_placeholder_season_stat_is_that_stat_unavailable_and_not_a_failure(monkeypatch, field, placeholder):
    result = fetch_api_line(monkeypatch, api_line(**{field: placeholder}))

    assert result[SEASON_TEXT[field]] == "N/A"
    for other_field, key in SEASON_TEXT.items():
        if other_field != field:
            assert result[key] != "N/A", key
    assert result["strikeouts"] == 0 and result["walks"] == 2 and result["batters_faced"] == 19
    assert lp._run_errors == []


@pytest.mark.parametrize("value", ["0.00", "3.10", "9.00", "27.50", "101.0", "6.1", "0", "12"])
def test_control_a_real_season_figure_is_kept_as_text(monkeypatch, value):
    result = fetch_api_line(monkeypatch, api_line(era=value, whip=value, inningsPitched=value))

    assert (result["era"], result["whip"], result["innings"]) == (value, value, value)


def test_the_debut_shape_reaches_the_payload_with_every_season_figure_unavailable(monkeypatch):
    """A 0-inning debut: the API answers placeholders. Probe E2 stopped the file here."""

    line = api_line(era="-.--", whip="-.--", inningsPitched="0.0", strikeOuts=0, baseOnBalls=0, homeRuns=0, battersFaced=3)
    route(monkeypatch, [("/stats?", line)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, player_id: events_frame())
    away = lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03")
    home = lp.fetch_pitcher_statcast(22, "Bravo Liveleft", as_of="2026-07-03")

    assert away["season_summary"]["era"] == "N/A" and away["season_summary"]["whip"] == "N/A"
    use_snapshot(monkeypatch, snapshot_from_starters(away, home))
    payload = gdj.build_payload()
    assert len(payload["matchups"]) == 1
    validate_payload(payload)


def two_game_snapshot(first, second, monkeypatch):
    """A snapshot of two games built from starters the real fetchers made; `second` is renamed so the games differ."""

    one = snapshot_from_starters(*first)
    other = snapshot_from_starters(*second)
    game = other["live_games"][0]
    featured = game["featured_game"]
    featured.update(
        game_pk=777002, away_team="Second Away Club", away_team_id=903, away_team_abbr="SAW",
        home_team="Second Home Club", home_team_id=904, home_team_abbr="SHM",
        away_pitcher_name="Charlie Thirdarm", away_pitcher_id=333,
        home_pitcher_name="Delta Fourthleft", home_pitcher_id=444,
    )
    game["away_starter"]["name"], game["home_starter"]["name"] = "Charlie Thirdarm", "Delta Fourthleft"
    one["live_games"].append(game)
    use_snapshot(monkeypatch, one)
    return one


@pytest.mark.parametrize("column", MEASUREMENTS)
def test_one_bad_statcast_cell_leaves_the_other_game_published_whole(monkeypatch, column):
    bad = events_frame()
    bad.loc[[0], column] = 9999.0
    frames = {11: bad, 22: events_frame(), 33: events_frame(), 44: events_frame()}
    route(monkeypatch, [("/stats?", API_STATS)])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, player_id: frames[player_id].copy())
    first = (
        lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03"),
        lp.fetch_pitcher_statcast(22, "Bravo Liveleft", as_of="2026-07-03"),
    )
    second = (
        lp.fetch_pitcher_statcast(33, "Charlie Thirdarm", as_of="2026-07-03"),
        lp.fetch_pitcher_statcast(44, "Delta Fourthleft", as_of="2026-07-03"),
    )
    two_game_snapshot(first, second, monkeypatch)

    payload = gdj.build_payload()

    assert len(payload["matchups"]) == 2
    validate_payload(payload)
    json.dumps(payload, allow_nan=False)
    assert_only_the_group_of(first[0], first[1], column)
    for group in set(MEASUREMENTS.values()):
        assert second[0][group] == second[1][group]
    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("statcast_pitcher", "malformed_rows")]


@pytest.mark.parametrize(
    ("bad_line", "rates_source"),
    [
        (api_line(era="-.--"), "mlb_api"),
        (api_line(whip="-.--", inningsPitched=".---"), "mlb_api"),
        # a negative count fails the API line as a source; Statcast counts are the documented fallback
        (api_line(strikeOuts=-5), "statcast"),
        (api_line(battersFaced=-19), "statcast"),
        (api_line(baseOnBalls=-1, homeRuns=-1), "statcast"),
    ],
    ids=["era-placeholder", "whip-and-innings-placeholders", "negative-strikeouts", "negative-batters-faced", "negative-walks-and-homers"],
)
def test_one_bad_api_cell_leaves_the_other_game_published_whole(monkeypatch, bad_line, rates_source):
    lines = {11: bad_line, 22: API_STATS, 33: API_STATS, 44: API_STATS}
    route(monkeypatch, [(f"people/{pid}/stats", line) for pid, line in lines.items()])
    monkeypatch.setattr(lp, "statcast_pitcher", lambda *a, player_id: events_frame())
    first = (
        lp.fetch_pitcher_statcast(11, "Alpha Livearm", as_of="2026-07-03"),
        lp.fetch_pitcher_statcast(22, "Bravo Liveleft", as_of="2026-07-03"),
    )
    second = (
        lp.fetch_pitcher_statcast(33, "Charlie Thirdarm", as_of="2026-07-03"),
        lp.fetch_pitcher_statcast(44, "Delta Fourthleft", as_of="2026-07-03"),
    )
    two_game_snapshot(first, second, monkeypatch)

    payload = gdj.build_payload()

    assert len(payload["matchups"]) == 2
    validate_payload(payload)
    json.dumps(payload, allow_nan=False)
    assert second[0]["season_summary"]["era"] == "3.10"
    assert second[0]["sample"]["rates"]["source"] == "mlb_api"
    assert first[0]["sample"]["rates"]["source"] == rates_source  # the bad cell costs its own line, nothing else
