"""R4 real-run guard: source parser failures stop the entire candidate.

No network or git mutation. Boxscores use the documented MLB shape from the
existing boxscore fixture. Cache fixtures use recovered published source tuples:
the legacy report is deliberately never passed off as a current reconstruction.
"""

from copy import deepcopy
from datetime import date, timedelta
import json
import os
import subprocess

import pytest

from data_pipeline import archive_boxscore as bx, archive_build as ab
from data_pipeline import archive_dryrun as dr, archive_finalize as fin, archive_games as ag
from tests.test_archive_boxscore import PROBABLE, box
from tests.test_archive_build import DAY, World, day_records
from tests.test_archive_games import PUBLISHED, records, schedule_game
from tests.test_archive_publish import load_publish


PK, NEXT_PK = 849805, 849806
NEXT_DAY, LAST_DAY = "2026-10-24", "2026-10-25"
BUILT_AT = "2026-11-08T12:00:00+00:00"
V = 5
LINE_KEYS = (
    ("innings_pitched", "inningsPitched"), ("hits", "hits"),
    ("earned_runs", "earnedRuns"), ("walks", "baseOnBalls"),
    ("strikeouts", "strikeOuts"),
)


def recovered(day=DAY, commit="a"):
    """A historical source, with date changes explicit for synthetic later days."""
    payload = deepcopy(PUBLISHED)
    payload["matchups"][0]["date"] = day
    payload["metadata"]["data_status"]["live_run"].update(
        target_date=day, as_of=(date.fromisoformat(day) - timedelta(days=1)).isoformat(),
    )
    return payload, commit * 40, commit * 64


def source_world(*, raw=None, days=None, sources=None):
    world = World(days=days, boxes={PK: raw if raw is not None else box()})
    return world, world.deps(published=sources or [recovered()])


def game_path(folder, pk=PK):
    return folder / "games" / f"{pk}.json"


def read_game(folder, pk=PK):
    return json.loads(game_path(folder, pk).read_text(encoding="utf-8"))


def seed(folder):
    world, deps = source_world()
    result = ab.run([DAY], folder, deps, ab.Ledger())
    assert result["built"] == [PK] and result["failed"] == []
    assert fin.game_problems(read_game(folder)) == []
    return read_game(folder)


def write_game(folder, document):
    ab.write_atomically(game_path(folder, document["game_pk"]), ag.compact_json(document))


def pitching(raw, side):
    node = raw["teams"][side]
    return node["players"][f"ID{node['pitchers'][0]}"]["stats"]["pitching"]


def break_shape(raw, side, change):
    node = raw["teams"][side]
    pid = node["pitchers"][0]
    if change == "teams_missing":
        raw.pop("teams")
    elif change == "side_missing":
        raw["teams"].pop(side)
    elif change == "pitchers_missing":
        node.pop("pitchers")
    elif change == "pitchers_text":
        node["pitchers"] = str(pid)
    elif change == "pitchers_mapping":
        node["pitchers"] = {"0": pid}
    elif change == "pitcher_text":
        node["pitchers"] = [str(pid)]
    elif change == "pitcher_bool":
        node["pitchers"] = [True]
    elif change == "players_missing":
        node.pop("players")
    elif change == "players_empty":
        node["players"] = {}
    elif change == "person_id":
        node["players"][f"ID{pid}"]["person"]["id"] = 1
    elif change == "name_missing":
        node["players"][f"ID{pid}"]["person"].pop("fullName")
    else:
        raise AssertionError(change)
    return raw


SHAPE_FAILURES = (
    "teams_missing", "side_missing", "pitchers_missing", "pitchers_text",
    "pitchers_mapping", "pitcher_text", "pitcher_bool", "players_missing",
    "players_empty", "person_id", "name_missing",
)


def assert_stopped(result, folder, pk=PK):
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert {"game_pk": pk, "code": ag.STARTER_UNCONFIRMED} in result["failed"]
    assert not game_path(folder, pk).exists()


def assert_blocked(folder):
    # The marker is internal; only the existing closed reason leaves this boundary.
    assert any(ag.STARTER_UNCONFIRMED in label for label in fin.check(folder))


@pytest.mark.parametrize("side", ag.SIDES)
@pytest.mark.parametrize("change", SHAPE_FAILURES)
def test_strict_run_stops_on_each_parser_shape_failure(tmp_path, side, change):
    raw = break_shape(box(), side, change)
    assert dr.classify_side(raw, side, PROBABLE[side]) == "parser_mismatch"
    _world, deps = source_world(raw=raw)
    assert_stopped(ab.run([DAY], tmp_path, deps, ab.Ledger()), tmp_path)


@pytest.mark.parametrize("raw", [None, [], "malformed source", {}, {"message": "private source detail"}])
def test_strict_run_stops_for_missing_or_unreadable_whole_boxscore(tmp_path, raw):
    world = World(boxes={PK: raw})
    assert_stopped(ab.run([DAY], tmp_path, world.deps(published=[recovered()]), ab.Ledger()), tmp_path)


@pytest.mark.parametrize("side", ag.SIDES)
def test_missing_report_probable_cannot_hide_a_parser_mismatch(tmp_path, side):
    payload = deepcopy(PUBLISHED)
    payload["matchups"][0]["starters"][f"{side}_starter"]["id"] = None
    raw = break_shape(box(), side, "players_missing")
    deps = World(boxes={PK: raw}).deps()
    deps.build_report = lambda record: (deepcopy(payload), {})
    assert_stopped(ab.run([DAY], tmp_path, deps, ab.Ledger()), tmp_path)


REJECTED_LINES = (
    ("innings_pitched", "inningsPitched", "6.3"),
    ("innings_pitched", "inningsPitched", 6.1),
    ("hits", "hits", "4"), ("hits", "hits", -1), ("hits", "hits", 4.0),
    ("earned_runs", "earnedRuns", True), ("earned_runs", "earnedRuns", "1"),
    ("walks", "baseOnBalls", "2"), ("walks", "baseOnBalls", -1),
    ("strikeouts", "strikeOuts", "7"), ("strikeouts", "strikeOuts", False),
)


@pytest.mark.parametrize("side", ag.SIDES)
@pytest.mark.parametrize("field,key,value", REJECTED_LINES)
def test_strict_run_stops_for_every_given_but_rejected_final_line_field(tmp_path, side, field, key, value):
    raw = box()
    pitching(raw, side)[key] = value
    assert dr.line_mismatches(raw, side) == [field]
    _world, deps = source_world(raw=raw)
    assert_stopped(ab.run([DAY], tmp_path, deps, ab.Ledger()), tmp_path)


@pytest.mark.parametrize("side", ag.SIDES)
@pytest.mark.parametrize("change", ["stats_missing", "pitching_missing", "pitching_wrong_type"])
def test_strict_run_stops_when_the_starters_entire_stats_block_is_unreadable(tmp_path, side, change):
    raw = box()
    node = raw["teams"][side]
    player = node["players"][f"ID{node['pitchers'][0]}"]
    if change == "stats_missing":
        player.pop("stats")
    elif change == "pitching_missing":
        player["stats"].pop("pitching")
    else:
        player["stats"]["pitching"] = "private malformed stats"
    _world, deps = source_world(raw=raw)
    assert_stopped(ab.run([DAY], tmp_path, deps, ab.Ledger()), tmp_path)


@pytest.mark.parametrize("side", ag.SIDES)
@pytest.mark.parametrize("field,key", LINE_KEYS)
@pytest.mark.parametrize("missing", ["absent", "null"])
def test_absent_or_null_individual_source_field_is_a_legitimate_unavailable_control(tmp_path, side, field, key, missing):
    raw = box()
    if missing == "absent":
        pitching(raw, side).pop(key)
    else:
        pitching(raw, side)[key] = None
    _world, deps = source_world(raw=raw)
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] is None and result["built"] == [PK] and result["failed"] == []
    assert read_game(tmp_path)["final_line"][side][field] is None
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == []


@pytest.mark.parametrize("side", ag.SIDES)
def test_measured_zero_final_line_is_preserved_control(tmp_path, side):
    raw = box()
    pitching(raw, side).update(inningsPitched="0.0", hits=0, earnedRuns=0, baseOnBalls=0, strikeOuts=0)
    _world, deps = source_world(raw=raw)
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] is None and result["failed"] == []
    assert read_game(tmp_path)["final_line"][side] == {
        "innings_pitched": "0.0", "hits": 0, "earned_runs": 0, "walks": 0, "strikeouts": 0,
    }


def test_changed_actual_starter_is_readable_and_retains_the_actual_line_control(tmp_path):
    _world, deps = source_world(raw=box(away_pitchers=(999, 607259)))
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    document = read_game(tmp_path)
    assert result["stopped"] is None and result["failed"] == []
    assert document["starters_check"]["away"] == "did_not_start"
    assert document["starters_check"]["actual"]["away"] == {"id": 999, "name": "Other Away"}
    assert document["final_line"]["away"]["innings_pitched"] == "1.0"


@pytest.mark.parametrize("side", ag.SIDES)
def test_mlb_explicitly_listing_no_pitcher_is_not_a_parser_stop_control(tmp_path, side):
    raw = box()
    raw["teams"][side]["pitchers"] = []
    _world, deps = source_world(raw=raw)
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] is None and result["failed"] == []
    assert read_game(tmp_path)["starters_check"][side] == "unknown"


@pytest.mark.parametrize("side", ag.SIDES)
def test_shared_diagnostics_preserve_the_dryrun_public_api(side):
    # Moving these judgments into the parser must leave the report's API intact.
    raw = break_shape(box(), side, "players_missing")
    assert bx.classify_side(raw, side, PROBABLE[side]) == dr.classify_side(raw, side, PROBABLE[side]) == "parser_mismatch"
    raw = box()
    pitching(raw, side)["hits"] = "4"
    assert bx.line_mismatches(raw, side) == dr.line_mismatches(raw, side) == ["hits"]


@pytest.mark.parametrize("with_raw_dir", [False, True])
def test_default_cli_is_strict_even_when_raw_recording_is_enabled(tmp_path, monkeypatch, capsys, with_raw_dir):
    raw = break_shape(box(), "home", "players_missing")
    _world, deps = source_world(raw=raw)
    monkeypatch.setattr(ab, "real_dependencies", lambda *args: deps)
    argv = ["--out", str(tmp_path), "--start", DAY, "--end", DAY]
    if with_raw_dir:
        argv += ["--raw-dir", str(tmp_path / "raw")]
    assert ab.main(argv) == 1
    output = capsys.readouterr()
    assert '"stopped": "starter_unconfirmed"' in output.out
    assert '"code": "starter_unconfirmed"' in output.out
    assert not game_path(tmp_path).exists()
    assert "Traceback" not in output.err


def test_explicit_diagnostic_run_keeps_the_raw_evidence_and_incomplete_game(tmp_path):
    raw = break_shape(box(), "away", "players_missing")
    _world, deps = source_world(raw=raw)
    deps.save_boxscore = lambda pk, data: ab.write_raw_boxscore(tmp_path / "raw", pk, data)
    result = ab.run([DAY], tmp_path, deps, ab.Ledger(), diagnostic=True)
    assert result["stopped"] is None and result["built"] == [PK]
    assert read_game(tmp_path)["starters_check"]["away"] == "unknown"
    assert json.loads((tmp_path / "raw" / f"{PK}.json").read_text()) == raw
    assert dr.stop_reasons(dr.starter_rows([read_game(tmp_path)], {PK: raw}))


def test_cli_dry_run_explicitly_selects_diagnostic_behavior(tmp_path, monkeypatch, capsys):
    raw = break_shape(box(), "away", "players_missing")
    _world, deps = source_world(raw=raw)
    monkeypatch.setattr(ab, "real_dependencies", lambda *args: deps)
    assert ab.main(["--out", str(tmp_path), "--start", DAY, "--end", DAY, "--dry-run"]) == 0
    assert read_game(tmp_path)["starters_check"]["away"] == "unknown"
    assert '"stopped": null' in capsys.readouterr().out


@pytest.mark.parametrize("side", ag.SIDES)
@pytest.mark.parametrize("incomplete", ["starter_unknown", "line_missing", *ag.FINAL_LINE_FIELDS])
def test_resume_rechecks_every_incomplete_cached_boxscore_part_only(tmp_path, side, incomplete):
    document = seed(tmp_path)
    if incomplete == "starter_unknown":
        document["starters_check"][side] = "unknown"
        document["starters_check"]["actual"][side] = None
        document["final_line"][side] = None
    elif incomplete == "line_missing":
        document["final_line"][side] = None
    else:
        document["final_line"][side][incomplete] = None
    write_game(tmp_path, document)
    assert fin.game_problems(document) == []  # incomplete is valid, never a reason to rebuild the report
    world, deps = source_world()
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    refreshed = read_game(tmp_path)
    assert result["stopped"] is None and result["failed"] == []
    assert world.asked.boxes == [PK]
    assert world.asked.builds == [] and world.asked.history == []
    assert refreshed["starters_check"][side] == "started"
    assert all(value is not None for value in refreshed["final_line"][side].values())
    assert {k: v for k, v in refreshed.items() if k not in ("starters_check", "final_line")} == {
        k: v for k, v in document.items() if k not in ("starters_check", "final_line")
    }


@pytest.mark.parametrize("restriction", ["date_range", "game_filter"])
def test_restored_incomplete_candidate_is_rechecked_outside_requested_selection(tmp_path, restriction):
    document = seed(tmp_path)
    document["final_line"]["home"]["walks"] = None
    write_game(tmp_path, document)
    world, deps = source_world(days={NEXT_DAY: []} if restriction == "date_range" else None)
    result = ab.run([NEXT_DAY] if restriction == "date_range" else [DAY], tmp_path, deps, ab.Ledger(),
                    only=NEXT_PK if restriction == "game_filter" else None)
    assert result["stopped"] is None and result["failed"] == []
    assert read_game(tmp_path)["final_line"]["home"]["walks"] == 1
    assert world.asked.boxes == [PK] and world.asked.builds == [] and world.asked.history == []


def test_diagnostic_candidate_cannot_bypass_a_later_strict_run(tmp_path):
    raw = break_shape(box(), "home", "players_missing")
    _world, deps = source_world(raw=raw)
    ab.run([DAY], tmp_path, deps, ab.Ledger(), diagnostic=True)
    world, strict = source_world(raw=raw)
    result = ab.run([DAY], tmp_path, strict, ab.Ledger())
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert world.asked.boxes == [PK] and world.asked.builds == [] and world.asked.history == []
    assert_blocked(tmp_path)


def partial_stop(folder):
    """A good day followed by a bad boxscore; each source has a unique date."""
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    raw = break_shape(box(), "away", "players_missing")
    world = World(days={DAY: day_records(), NEXT_DAY: next_records, LAST_DAY: []}, boxes={PK: box(), NEXT_PK: raw})
    deps = world.deps(published=[recovered(), recovered(NEXT_DAY, "b")])
    result = ab.run([DAY, NEXT_DAY, LAST_DAY], folder, deps, ab.Ledger())
    return world, result


def test_stop_after_a_good_game_is_run_wide_and_retains_prior_partial_files(tmp_path):
    world, result = partial_stop(tmp_path)
    assert result["built"] == [PK]
    assert_stopped(result, tmp_path, NEXT_PK)
    assert world.asked.days == [DAY, NEXT_DAY]
    assert fin.game_problems(read_game(tmp_path)) == []
    assert fin.build(tmp_path, V, BUILT_AT)["problems"]
    assert not (tmp_path / "manifest.json").exists() and not (tmp_path / "index-2026.json").exists()
    assert_blocked(tmp_path)


def stopped_with_old_manifest(folder):
    seed(folder)
    assert fin.build(folder, V, BUILT_AT)["problems"] == [] and fin.check(folder) == []
    old_manifest = (folder / "manifest.json").read_bytes()
    old_index = (folder / "index-2026.json").read_bytes()
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    raw = break_shape(box(), "away", "players_missing")
    world = World(days={NEXT_DAY: next_records}, boxes={NEXT_PK: raw})
    # Real wiring supplies all recovered reports, including complete older caches.
    ab.run([NEXT_DAY], folder, world.deps(published=[recovered(), recovered(NEXT_DAY, "b")]), ab.Ledger())
    return old_manifest, old_index


def test_old_valid_manifest_is_blocked_after_a_stopped_game_wrote_no_file(tmp_path):
    before_manifest, before_index = stopped_with_old_manifest(tmp_path)
    assert not game_path(tmp_path, NEXT_PK).exists()
    assert_blocked(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"]
    assert (tmp_path / "manifest.json").read_bytes() == before_manifest
    assert (tmp_path / "index-2026.json").read_bytes() == before_index


def test_publisher_refuses_the_entire_stopped_candidate_before_git_or_copy(tmp_path, monkeypatch, capsys):
    stopped_with_old_manifest(tmp_path)
    assert not game_path(tmp_path, NEXT_PK).exists()  # refusal must survive with only the previously valid files
    publish = load_publish()
    def unexpected(*args, **kwargs):
        pytest.fail("stopped candidate reached git or the publication copy")
    monkeypatch.setattr(publish.pd, "changed_paths", unexpected)
    monkeypatch.setattr(publish, "_work_in", unexpected)
    assert publish.main([str(tmp_path), "--repo", str(tmp_path / "untouched"), "--remote", "local-unused"]) == 1
    assert "failed candidate_invalid" in capsys.readouterr().out
    assert not (tmp_path / "untouched").exists()


@pytest.mark.parametrize("rerun", ["unrelated_day", "only_good_game", "fetch_failed", "ceiling"])
def test_stop_marker_cannot_be_cleared_without_successfully_recovering_missing_stopped_id(tmp_path, rerun):
    stopped_with_old_manifest(tmp_path)
    if rerun in ("unrelated_day", "only_good_game"):
        world, deps = source_world(days={LAST_DAY: []} if rerun == "unrelated_day" else None)
        ab.run([LAST_DAY] if rerun == "unrelated_day" else [DAY], tmp_path, deps, ab.Ledger(),
               only=PK if rerun == "only_good_game" else None)
    else:
        next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
        world = World(days={NEXT_DAY: next_records}, boxes={NEXT_PK: None})
        deps = world.deps(published=[recovered(NEXT_DAY, "b")])
        if rerun == "ceiling":
            deps.fetch_boxscore = lambda pk: (_ for _ in ()).throw(ab.CeilingReached("mlb"))
        ab.run([NEXT_DAY], tmp_path, deps, ab.Ledger())
    assert_blocked(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"]


def test_cached_incomplete_recheck_failure_also_keeps_the_stop(tmp_path):
    document = seed(tmp_path)
    document["final_line"]["away"]["hits"] = None
    write_game(tmp_path, document)
    raw = break_shape(box(), "away", "players_missing")
    _world, deps = source_world(raw=raw)
    ab.run([DAY], tmp_path, deps, ab.Ledger())
    _world, deps = source_world()
    deps.fetch_boxscore = lambda pk: (_ for _ in ()).throw(OSError("private source failure"))
    ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert_blocked(tmp_path)


@pytest.mark.parametrize("failure", ["request_failed", "ceiling"])
def test_first_failed_cached_recheck_blocks_an_old_manifest_without_an_existing_marker(tmp_path, failure):
    document = seed(tmp_path)
    document["final_line"]["home"]["strikeouts"] = None
    write_game(tmp_path, document)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == [] and fin.check(tmp_path) == []
    before = (tmp_path / "manifest.json").read_bytes()
    _world, deps = source_world()
    def fail(pk):
        if failure == "ceiling":
            raise ab.CeilingReached("mlb")
        raise OSError("private source failure")
    deps.fetch_boxscore = fail
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] == (ag.CEILING_REACHED if failure == "ceiling" else ag.STARTER_UNCONFIRMED)
    assert_blocked(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"]
    assert (tmp_path / "manifest.json").read_bytes() == before


def test_successful_strict_recovery_of_previously_stopped_id_clears_publication_block(tmp_path):
    stopped_with_old_manifest(tmp_path)
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    world = World(days={NEXT_DAY: next_records}, boxes={NEXT_PK: box()})
    deps = world.deps(published=[recovered(), recovered(NEXT_DAY, "b")])
    result = ab.run([NEXT_DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] is None and result["built"] == [NEXT_PK] and result["failed"] == []
    assert fin.build(tmp_path, V, BUILT_AT) == {"problems": [], "games": 2}
    assert fin.check(tmp_path) == []
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert set(manifest["files"]) == {"games/849805.json", "games/849806.json", "index-2026.json"}
    assert set(load_publish().candidate_files(tmp_path)) == {*manifest["files"], "manifest.json"}


def test_complete_valid_published_cache_costs_no_extra_boxscore_report_or_history_control(tmp_path):
    seed(tmp_path)
    before = game_path(tmp_path).read_bytes()
    world, deps = source_world()
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["skipped"] == [PK] and result["built"] == [] and result["failed"] == []
    assert world.asked.boxes == [] and world.asked.builds == [] and world.asked.history == []
    assert game_path(tmp_path).read_bytes() == before


@pytest.mark.parametrize("restriction", ["date_range", "game_filter"])
def test_changed_complete_published_cache_is_refused_outside_requested_selection(tmp_path, restriction):
    document = seed(tmp_path)
    document["payload"]["matchups"][0]["report"]["headline"] = "rewritten historical report"
    write_game(tmp_path, document)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == [] and fin.check(tmp_path) == []
    _world, deps = source_world(days={NEXT_DAY: []} if restriction == "date_range" else None)
    result = ab.run([NEXT_DAY] if restriction == "date_range" else [DAY], tmp_path, deps, ab.Ledger(),
                    only=NEXT_PK if restriction == "game_filter" else None)
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert_blocked(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"]


def test_linked_games_directory_is_refused_before_any_requests_or_external_writes(tmp_path):
    candidate, outside = tmp_path / "candidate", tmp_path / "outside"
    candidate.mkdir()
    outside.mkdir()
    link = candidate / "games"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, check=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    world, deps = source_world()
    result = ab.run([DAY], candidate, deps, ab.Ledger())
    assert list(outside.iterdir()) == []
    assert result["stopped"] == ag.GAME_NOT_FOUND
    assert result["failed"] == [{"game_pk": None, "code": ag.GAME_NOT_FOUND}]
    assert world.asked.days == [] and world.asked.boxes == [] and world.asked.builds == [] and world.asked.history == []


def test_confirmed_cache_recovery_does_not_turn_an_isolated_game_failure_into_a_run_stop(tmp_path):
    document = seed(tmp_path)
    document["final_line"]["away"]["hits"] = None
    write_game(tmp_path, document)
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    world = World(days={NEXT_DAY: next_records}, boxes={PK: box()},
                  fail={NEXT_PK: ag.ArchiveError(ag.GAME_NOT_FOUND)})
    result = ab.run([NEXT_DAY], tmp_path, world.deps(published=[recovered()]), ab.Ledger())
    assert result["failed"] == [{"game_pk": NEXT_PK, "code": ag.GAME_NOT_FOUND}]
    assert result["stopped"] is None
    assert fin.build(tmp_path, V, BUILT_AT) == {"problems": [], "games": 1}
    assert fin.check(tmp_path) == []


def test_raw_evidence_save_failure_cannot_hide_a_source_parser_stop(tmp_path):
    raw = break_shape(box(), "away", "players_missing")
    _world, deps = source_world(raw=raw)
    def fail_save(pk, data):
        raise OSError("private diagnostic path")
    deps.save_boxscore = fail_save
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert_stopped(result, tmp_path)
    assert_blocked(tmp_path)
    assert "private diagnostic path" not in json.dumps(result)
