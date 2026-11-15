"""Guard review regressions: JSON types and failure to persist a source stop."""

import json

import pytest

from data_pipeline import archive_build as ab, archive_finalize as fin, archive_games as ag, archive_index as ix
from tests.test_archive_build import World, day_records
from tests.test_archive_boxscore import box
from tests.test_archive_games import records, schedule_game
from tests.test_archive_guard import (
    DAY, NEXT_DAY, LAST_DAY, PK, NEXT_PK, V, BUILT_AT, seed, read_game,
    write_game, recovered, source_world, break_shape,
)
from tests.test_archive_publish import (
    clean_git_environment, folder, real_payload, world, publish, git, published_game,
)


def change_boolean_to_zero(folder):
    document = read_game(folder)
    limited = document["payload"]["matchups"][0]["starters"]["away_starter"]["sample"]["limited"]
    assert limited["arsenal"] is False
    limited["arsenal"] = 0
    write_game(folder, document)


@pytest.mark.parametrize("restriction", ["date_range", "game_filter"])
def test_restored_published_values_keep_boolean_types_outside_selection(tmp_path, restriction):
    seed(tmp_path)
    change_boolean_to_zero(tmp_path)
    _world, deps = source_world(days={NEXT_DAY: []} if restriction == "date_range" else None)
    result = ab.run([NEXT_DAY] if restriction == "date_range" else [DAY], tmp_path, deps, ab.Ledger(),
                    only=NEXT_PK if restriction == "game_filter" else None)
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert ag.STARTER_UNCONFIRMED in fin.check(tmp_path)


def test_selected_resume_does_not_equate_a_boolean_to_zero(tmp_path):
    seed(tmp_path)
    change_boolean_to_zero(tmp_path)
    (record,) = day_records()
    assert not ab.existing_valid(tmp_path / "games" / f"{PK}.json", PK, record, recovered())


def test_source_object_key_order_does_not_change_values_control(tmp_path):
    seed(tmp_path)
    payload, commit, digest = recovered()
    reordered = dict(reversed(list(payload.items())))
    fake, deps = source_world(sources=[(reordered, commit, digest)])
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["skipped"] == [PK] and result["failed"] == [] and result["stopped"] is None
    assert fake.asked.boxes == [] and fake.asked.builds == []


def test_publication_does_not_equate_a_committed_boolean_to_zero(publish, world, capsys):
    assert publish.main(world.argv()) == 0
    head = world.head()
    change_boolean_to_zero(world.candidate)
    assert fin.build(world.candidate, V, BUILT_AT)["problems"] == []
    assert publish.main(world.argv()) == 1
    assert "failed published_report_changed" in capsys.readouterr().out
    assert world.head() == head and git(world.work, "status", "--porcelain") == ""


def test_index_recomputation_does_not_equate_false_with_a_zero_score(tmp_path):
    document = published_game()
    document["result"]["away_runs"] = 0
    write_game(tmp_path, document)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == []
    path = tmp_path / "index-2026.json"
    index = json.loads(path.read_text())
    index["games"][0]["result"]["away_runs"] = False
    text = ag.compact_json(index)
    path.write_text(text, encoding="utf-8")
    files = {"index-2026.json": text, f"games/{PK}.json": (tmp_path / "games" / f"{PK}.json").read_text(encoding="utf-8")}
    (tmp_path / "manifest.json").write_text(ag.compact_json(ix.build_manifest(files, index, BUILT_AT)), encoding="utf-8")
    assert "index:rows" in fin.check(tmp_path)


@pytest.mark.parametrize("persistent", [False, True])
def test_stop_write_failure_preserves_immediate_run_wide_stop(tmp_path, monkeypatch, persistent):
    seed(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == []
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    fake = World(days={NEXT_DAY: next_records, LAST_DAY: []},
                 boxes={NEXT_PK: break_shape(box(), "away", "players_missing")})
    write = ab.write_atomically
    attempts = []
    def fail_stop(path, text):
        if path.name == ab.STOP_FILE:
            attempts.append(path)
            if persistent or len(attempts) == 1:
                raise OSError("private stop-state path")
        return write(path, text)
    monkeypatch.setattr(ab, "write_atomically", fail_stop)
    result = ab.run([NEXT_DAY, LAST_DAY], tmp_path,
                    fake.deps(published=[recovered(), recovered(NEXT_DAY, "b")]), ab.Ledger())
    assert attempts
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert result["failed"] == [{"game_pk": NEXT_PK, "code": ag.STARTER_UNCONFIRMED}]
    assert fake.asked.days == [NEXT_DAY]
    assert ag.STARTER_UNCONFIRMED in fin.check(tmp_path)
    assert "private stop-state path" not in json.dumps(result)


def test_stop_write_failure_does_not_replace_a_ceiling_stop(tmp_path, monkeypatch):
    seed(tmp_path)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == []
    next_records = records(schedule_game(pk=NEXT_PK, day=NEXT_DAY, start="2026-10-25T00:00:00Z"))
    fake = World(days={NEXT_DAY: next_records, LAST_DAY: []})
    deps = fake.deps(published=[recovered(), recovered(NEXT_DAY, "b")])
    deps.fetch_boxscore = lambda pk: (_ for _ in ()).throw(ab.CeilingReached("mlb"))
    write = ab.write_atomically
    def fail_stop(path, text):
        if path.name == ab.STOP_FILE:
            raise OSError("private stop-state path")
        return write(path, text)
    monkeypatch.setattr(ab, "write_atomically", fail_stop)
    result = ab.run([NEXT_DAY, LAST_DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] == ag.CEILING_REACHED
    assert fake.asked.days == [NEXT_DAY]
    assert ag.STARTER_UNCONFIRMED in fin.check(tmp_path)


def test_cached_refresh_write_failure_is_closed_and_keeps_the_latch(tmp_path, monkeypatch):
    document = seed(tmp_path)
    document["final_line"]["away"]["hits"] = None
    write_game(tmp_path, document)
    assert fin.build(tmp_path, V, BUILT_AT)["problems"] == []
    write = ab.write_atomically
    def fail_refresh(path, text):
        if path.parent.name == "games":
            raise OSError("private refreshed game path")
        return write(path, text)
    monkeypatch.setattr(ab, "write_atomically", fail_refresh)
    _fake, deps = source_world()
    result = ab.run([DAY], tmp_path, deps, ab.Ledger())
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert ag.STARTER_UNCONFIRMED in fin.check(tmp_path)
    assert "private refreshed game path" not in json.dumps(result)


def test_linked_stop_state_is_refused_before_reading_it(tmp_path, monkeypatch):
    # Supply link metadata at the filesystem boundary so this also runs on
    # Windows without requiring file-symlink privileges.
    stop = tmp_path / ab.STOP_FILE
    stop.write_text(json.dumps({"game_pks": [PK]}), encoding="utf-8")
    path_type = type(stop)
    is_link, read = path_type.is_symlink, path_type.read_text
    monkeypatch.setattr(path_type, "is_symlink", lambda path: path == stop or is_link(path))
    def refuse_read(path, *args, **kwargs):
        if path == stop:
            pytest.fail("linked stop state reached a file read")
        return read(path, *args, **kwargs)
    monkeypatch.setattr(path_type, "read_text", refuse_read)
    fake, deps = source_world()
    result = ab.run([], tmp_path, deps, ab.Ledger())
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert fake.asked.days == [] and fake.asked.boxes == []


@pytest.mark.parametrize("operation", ["rewrite", "unlink"])
def test_stop_state_cleanup_failure_is_closed(tmp_path, monkeypatch, operation):
    seed(tmp_path)
    stop = tmp_path / ab.STOP_FILE
    stop.write_text(json.dumps({"game_pks": [NEXT_PK if operation == "rewrite" else PK]}), encoding="utf-8")
    if operation == "rewrite":
        write = ab.write_atomically
        def fail_write(path, text):
            if path == stop:
                raise OSError("private stop cleanup")
            return write(path, text)
        monkeypatch.setattr(ab, "write_atomically", fail_write)
    else:
        path_type = type(stop)
        unlink = path_type.unlink
        def fail_unlink(path, *args, **kwargs):
            if path == stop:
                raise OSError("private stop cleanup")
            return unlink(path, *args, **kwargs)
        monkeypatch.setattr(path_type, "unlink", fail_unlink)
    _fake, deps = source_world()
    result = ab.run([], tmp_path, deps, ab.Ledger())
    assert result["stopped"] == ag.STARTER_UNCONFIRMED
    assert ag.STARTER_UNCONFIRMED in fin.check(tmp_path)
    assert "private stop cleanup" not in json.dumps(result)
