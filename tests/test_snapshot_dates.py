"""The generator parses the dates of a cached run and snapshot and rejects unsafe ones (QA2-01).

QA2-01 probe: a run and a snapshot that carried the same strings (game 2026-07-15, cutoff
2026-07-20) were accepted, and pitches thrown after the game reached the public payload as
live data. Equal strings do not prove a safe relationship: every date is parsed, each game's
cutoff must be before its official date (D29), and run, snapshot and game must agree.
"""

from __future__ import annotations

from copy import deepcopy
import json
from datetime import date
from unittest.mock import patch

import pytest

from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.schema import SCHEMA_VERSION
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_live_sample_pipeline import API_STATS, FakeResponse, frame
from tests.test_live_starters_no_demo_fields import SLOTS, _fake_live_game
from tests.test_stale_snapshot import RUN_AT, good_run


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])


@pytest.fixture()
def template() -> dict:
    payload = demo_inputs.build_demo_payload()
    return next(m for m in payload["matchups"] if m["id"] == "matchup_001")


def live_game(template, official="2026-07-15", as_of="2026-07-14", through=None) -> dict:
    game = _fake_live_game(template)
    # `_fake_live_game` gives both starters the away starter's profile; the home starter's put-away pitch must
    # be one he throws at least 15% of the time in the mix it is paired with (D30), as the pipeline writes it.
    # The profile is what the pipeline derives from that mix (the manifest recomputes it, rule 1): the most
    # thrown pitch, the second one from 15%, and the style made of both. Likewise the summary counts are the
    # counts of the sample.
    game["away_starter"]["pitching_profile"].update(
        primary_pitch="Four-seam", putaway_pitch="Slider", style_label="Four-seam-Slider starter"
    )
    game["home_starter"]["pitching_profile"].update(
        primary_pitch="Sinker", putaway_pitch="Changeup", style_label="Sinker-Changeup starter"
    )
    for slot in SLOTS:
        game[slot]["season_summary"]["strikeouts"] = game[slot]["sample"]["rates"]["strikeouts"]
    game["featured_game"]["official_date"] = official
    game["as_of"] = as_of
    scope = labels.make_scope(labels.SCOPE_REGULAR, through or as_of)
    for slot in SLOTS:
        game[slot]["sample"]["arsenal"]["scope"] = scope
        game[slot]["sample"]["rates"]["scope"] = scope
        game[slot]["season_summary"]["scopes"] = {"season_rates": scope, "counts": scope}
    return game


def pair(template, *, as_of="2026-07-14", game_as_of=None, official="2026-07-15", through=None):
    game = live_game(template, official=official, as_of=game_as_of or as_of, through=through)
    run = good_run(as_of=as_of)
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "run_at": RUN_AT,
        "fetched_date": "2026-07-15",
        "as_of": as_of,
        "live_games": [game],
    }
    return run, snapshot


def resolve(run, snapshot):
    cache_manager.save_processed("live_run", run)
    cache_manager.save_processed("live_matchup", snapshot)
    return gdj._resolve_live_input()


def drop(path):
    """Mutation: remove the key at `path` of the first game of the snapshot."""

    def mutate(run, snapshot):
        target = snapshot["live_games"][0]
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return mutate


def setvalue(path, value):
    def mutate(run, snapshot):
        target = snapshot["live_games"][0]
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return mutate


# --- the coherent pair is live ----------------------------------------------------------------------


def test_a_coherent_pair_is_live(template):
    snapshot, status = resolve(*pair(template))

    assert snapshot is not None and status["mode"] == "fetched_snapshot"


def test_an_earlier_explicit_cutoff_is_still_live(template):
    snapshot, status = resolve(*pair(template, as_of="2026-07-10"))

    assert snapshot is not None and status["mode"] == "fetched_snapshot"


# --- the unsafe ones are rejected, and the reason says why -------------------------------------------


@pytest.mark.parametrize(
    "kwargs, mutate, reason",
    [
        ({"as_of": "2026-07-20"}, None, "2026-07-20"),  # the QA2-01 probe
        ({"as_of": "2026-07-16"}, None, "2026-07-16"),
        ({"as_of": "2026-07-15"}, None, "2026-07-15"),  # the game day itself
        ({"as_of": "2026-13-45"}, None, "2026-13-45"),  # not a date
        ({"as_of": "20260714"}, None, "20260714"),  # not the ISO shape
        ({"as_of": "yesterday"}, None, "yesterday"),
        ({"official": "2026-07-16"}, None, "2026-07-16"),  # a game of another day than the run
        ({"game_as_of": "2026-07-13"}, None, "2026-07-13"),  # the game's cutoff is not the run's
        ({"game_as_of": "2026-07-15"}, None, "2026-07-15"),
        ({"through": "2026-07-15"}, None, "2026-07-15"),  # a figure that runs through game day
        ({"through": "2026-07-20"}, None, "2026-07-20"),
        ({}, drop(("featured_game", "official_date")), "official date"),
        ({}, drop(("as_of",)), "cutoff"),
        ({}, setvalue(("featured_game", "official_date"), "soon"), "soon"),
        ({}, drop(("away_starter", "throws")), "throws"),
        ({}, setvalue(("home_starter", "throws"), "X"), "throws"),
        ({}, setvalue(("away_starter", "sample", "arsenal", "scope", "through"), "x"), "x"),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_an_unsafe_run_and_snapshot_is_not_live(template, kwargs, mutate, reason, capsys):
    run, snapshot = pair(template, **kwargs)
    if mutate:
        mutate(run, snapshot)

    live, status = resolve(run, snapshot)

    assert live is None
    assert status["mode"] == "demo_fallback"
    assert status["reason"] in (  # rule 8: a code; what was wrong stays in the log
        {"source": "snapshot", "code": "snapshot_mismatch"},
        {"source": "snapshot", "code": "game_rejected"},
    )
    assert reason in capsys.readouterr().out


SCHEMA_MISMATCH = {"source": "snapshot", "code": "snapshot_schema_mismatch"}


@pytest.mark.parametrize(
    "version",
    [None, "0.3.0", "0.2.0", "0.4.0", "0.5.0", "0.6.1", "1.0.0", "0.6", "v0.6.0", "garbage", "", 4, " 0.6.0"],
    ids=repr,
)
def test_a_snapshot_whose_schema_is_not_exactly_the_codes_is_not_live(template, version):
    """Equality, not "older than": a snapshot written by newer code is as unreadable as an older one."""

    run, snapshot = pair(template)
    if version is None:
        del snapshot["schema_version"]
    else:
        snapshot["schema_version"] = version

    live, status = resolve(run, snapshot)

    assert live is None
    assert status["mode"] == "demo_fallback"
    assert status["reason"] == SCHEMA_MISMATCH


def test_a_snapshot_without_schema_version_is_not_live(template):
    run, snapshot = pair(template)
    del snapshot["schema_version"]

    live, status = resolve(run, snapshot)

    assert live is None and status["reason"] == SCHEMA_MISMATCH


def test_a_snapshot_with_the_schema_of_the_code_is_live(template):
    live, status = resolve(*pair(template))

    assert live is not None and status["mode"] == "fetched_snapshot"


def test_the_published_reason_is_a_source_and_a_code_and_the_detail_stays_in_the_log(template, monkeypatch, capsys):
    """Rule 8: nothing of the rejection reaches the served file but `{source, code}`; the detail is local."""

    from data_pipeline import contract_checks

    run, snapshot = pair(template)
    snapshot["schema_version"] = "0.3.0"
    live, status = resolve(run, snapshot)
    logged = capsys.readouterr().out

    monkeypatch.setattr(gdj, "_live", live)
    monkeypatch.setattr(gdj, "_live_status", status)
    payload = json.loads(json.dumps(gdj.build_payload()))
    published = json.dumps(payload["metadata"]["data_status"])

    assert payload["metadata"]["data_status"]["reason"] == SCHEMA_MISMATCH
    assert "0.3.0" not in published and "P0.15" not in published and "before" not in published
    assert [v for v in contract_checks._rule8(payload) if v.where.endswith("reason")] == []
    assert "0.3.0" in logged and "P0.15-D2.1" in logged  # the detail, for whoever reads the log


def test_a_snapshot_without_games_is_not_live(template):
    run, snapshot = pair(template)
    snapshot["live_games"] = []

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"


def test_a_run_whose_cutoff_is_not_before_its_game_date_is_not_live(template):
    run, snapshot = pair(template)
    run["target_date"] = "2026-07-14"
    snapshot["fetched_date"] = "2026-07-14"
    snapshot["live_games"][0]["featured_game"]["official_date"] = "2026-07-14"

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"


# --- the QA2-01 probe, end to end, with the real fetcher and the real resolver -------------------------


def late_pitcher_game(template, monkeypatch):
    """A pitcher fetched with a late cutoff (what a leaky cache would hold), as QA built it."""

    monkeypatch.setattr(lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27)))
    with patch.object(lp.urllib.request, "urlopen", return_value=FakeResponse(API_STATS)), patch.object(
        lp, "statcast_pitcher", return_value=frame(game_date="2026-07-20")
    ):
        late = lp.fetch_pitcher_statcast(11, "Late Data", as_of="2026-07-20")
    other = deepcopy(late)
    other["name"] = "Other Late Data"
    game = live_game(template, as_of="2026-07-20")
    game.update(
        away_starter=late,
        home_starter=other,
        combined_charts={
            "pitch_mix": lp._combine_pitch_mix(late, other),
            "velocity_by_pitch": lp._combine_velocity(late, other),
        },
    )
    return game


def test_the_qa_probe_a_matching_pair_with_a_late_cutoff_never_reaches_a_payload(
    template, monkeypatch
):
    game = late_pitcher_game(template, monkeypatch)
    run = good_run(as_of="2026-07-20")
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "run_at": RUN_AT,
        "fetched_date": "2026-07-15",
        "as_of": "2026-07-20",
        "live_games": [game],
    }

    live, status = resolve(run, snapshot)

    assert live is None and status["mode"] == "demo_fallback"
    payload = None
    with patch.object(gdj, "_live", live), patch.object(gdj, "_live_status", status):
        payload = gdj.build_payload()
    assert payload["metadata"]["data_mode"] == "demo_fallback"
    assert all(check.passed for check in validate_payload(payload))


def test_publication_validation_rejects_a_late_scope_even_if_the_resolver_were_bypassed(
    template, monkeypatch
):
    game = late_pitcher_game(template, monkeypatch)
    live = {"run_at": "2026-07-15T12:00:00+00:00", "fetched_date": "2026-07-15", "as_of": "2026-07-20", "live_games": [game]}
    status = {"mode": "fetched_snapshot", "reason": None, "live_run": None}

    with patch.object(gdj, "_live", live), patch.object(gdj, "_live_status", status):
        payload = gdj.build_payload()

    with pytest.raises(ValidationError) as caught:
        validate_payload(payload)
    failed = [check for check in caught.value.checks if not check.passed]
    assert any("cutoff" in check.description for check in failed)


def test_a_payload_with_a_safe_scope_still_validates(template, monkeypatch):
    game = live_game(template)
    live = {"run_at": "2026-07-15T12:00:00+00:00", "fetched_date": "2026-07-15", "as_of": "2026-07-14", "live_games": [game]}
    status = {"mode": "fetched_snapshot", "reason": None, "live_run": None}

    with patch.object(gdj, "_live", live), patch.object(gdj, "_live_status", status):
        payload = gdj.build_payload()

    assert all(check.passed for check in validate_payload(payload))
