"""R4-D6 (code half): finishing and re-checking a candidate folder, and publishing it to `main` and nothing else
(docs/plans/R4.md 4.5; D66, D15, D42).

Everything runs against local repositories in a temporary directory: a bare repository stands for GitHub and a clone of it
for the checkout of the publish job. Nothing is pushed anywhere real; the push over SSH is the one thing only the deploy
key on `main` can prove (the first real run), and it reuses `publish_data._push`, which has its own tests.
"""

from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

import pytest

from data_pipeline import archive_finalize as fin
from data_pipeline import archive_games as ag
from data_pipeline import archive_index as ix
from tests.test_archive_games import PUBLISHED, SOURCE, records, schedule_game

ROOT = Path(__file__).resolve().parents[1]
OWNER = ("Daniel Herdenez", "edherdenez@gmail.com")
V = 5
BUILT_AT = "2026-11-08T12:00:00+00:00"


def load_publish():
    spec = importlib.util.spec_from_file_location("publish_archive", ROOT / "scripts" / "publish_archive.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def real_payload():
    """A payload the pipeline really produced and today's checks accept (the first cell of the matrix)."""

    from tests.matrix import MATRIX, matrix_outcome

    outcome = matrix_outcome(MATRIX[0])
    assert outcome.live and outcome.failed == [] and outcome.violations == []
    return outcome.payload


@pytest.fixture(autouse=True)
def clean_git_environment(monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(Path(tempfile.gettempdir()) / "pitchcraft-no-such-gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_SSH_COMMAND"):
        monkeypatch.delenv(name, raising=False)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def published_game(pk=849805, day="2026-10-23"):
    (record,) = records(schedule_game(pk=pk, day=day))
    origin = ag.published_origin(PUBLISHED, record, SOURCE)
    return ag.build_game_file(record, PUBLISHED, origin, starter_facts={"away": {"id": 607259, "prior_mlb_seasons": 6},
                                                                       "home": {"id": 694819, "prior_mlb_seasons": 7}})


def reconstructed_game(payload, pk=849806, day="2026-07-04"):
    (record,) = records(schedule_game(pk=pk, day=day, game_type="D", series_status={"isOver": True, "result": "NYY wins 3-1"}))
    origin = ag.published_origin(payload, record, None)
    origin["kind"], origin["published_at"] = "reconstructed", None
    return ag.build_game_file(record, payload, origin)


def write_game(folder: Path, document) -> Path:
    path = folder / "games" / f"{document['game_pk']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ag.compact_json(document), encoding="utf-8", newline="\n")
    return path


@pytest.fixture
def folder(tmp_path, real_payload):
    candidate = tmp_path / "candidate"
    write_game(candidate, published_game())
    write_game(candidate, reconstructed_game(real_payload))
    return candidate


def built(folder: Path) -> Path:
    result = fin.build(folder, V, BUILT_AT)
    assert result == {"problems": [], "games": 2}
    return folder


# --- finalize: build ----------------------------------------------------------------------------------------------

def test_build_writes_an_index_and_a_manifest_that_check_accepts(folder):
    built(folder)
    index = json.loads((folder / "index-2026.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert index["count"] == 2 and index["veteran_min"] == V and manifest["built_at"] == BUILT_AT
    assert set(manifest["files"]) == {"index-2026.json", "games/849805.json", "games/849806.json"}
    assert fin.check(folder) == [] and fin.check(folder, V) == []


def test_build_is_deterministic_for_the_same_files_and_instant(folder, tmp_path):
    built(folder)
    first = {p.name: p.read_bytes() for p in folder.glob("*.json")}
    fin.build(folder, V, BUILT_AT)
    assert {p.name: p.read_bytes() for p in folder.glob("*.json")} == first


def test_build_needs_an_approved_v_and_writes_nothing_without_it(folder):
    for bad in (None, 0, 31, "5", True):
        with pytest.raises(ix.ArchiveIndexError):
            fin.build(folder, bad, BUILT_AT)
    assert not list(folder.glob("*.json"))


def test_a_game_that_fails_is_left_out_of_the_index_and_reported(folder, real_payload):
    bad = reconstructed_game(real_payload, pk=849807)
    bad["payload"]["matchups"][0]["status"] = "yesterday"  # today's validate_payload refuses it
    write_game(folder, bad)
    result = fin.build(folder, V, BUILT_AT)
    assert result["games"] == 2 and "game:payload" in result["problems"]
    assert "games/849807.json" not in json.loads((folder / "manifest.json").read_text())["files"]


def test_a_file_named_by_another_game_or_unreadable_is_a_problem(folder):
    (folder / "games" / "849999.json").write_text(ag.compact_json(published_game()), encoding="utf-8")
    (folder / "games" / "849998.json").write_text("{not json", encoding="utf-8")
    problems = fin.build(folder, V, BUILT_AT)["problems"]
    assert "name" in problems and "unreadable" in problems


def test_two_seasons_in_one_folder_are_refused(folder, real_payload):
    other = published_game(pk=849808)
    other["season"], other["date"], other["origin"]["as_of"] = 2025, "2025-10-23", "2025-10-22"
    write_game(folder, other)
    assert "season" in fin.build(folder, V, BUILT_AT)["problems"]


def test_a_bad_v_is_refused_even_when_there_is_nothing_to_index(tmp_path):
    (tmp_path / "games").mkdir()
    with pytest.raises(ix.ArchiveIndexError):
        fin.build(tmp_path, None, BUILT_AT)


def test_an_empty_folder_has_nothing_to_index(tmp_path):
    (tmp_path / "games").mkdir()
    assert "season" in fin.build(tmp_path, V, BUILT_AT)["problems"]


# --- finalize: check ---------------------------------------------------------------------------------------------

def test_a_changed_game_file_is_found_by_check(folder):
    built(folder)
    path = folder / "games" / "849805.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["result"]["away_runs"] = 99
    document["result"]["winner"] = "away"
    path.write_text(ag.compact_json(document), encoding="utf-8")
    problems = fin.check(folder)
    assert "manifest:digest" in problems and "index:rows" in problems


def test_check_finds_each_kind_of_damage(folder):
    built(folder)
    (folder / "games" / "849900.json").write_text(ag.compact_json(published_game(pk=849900)), encoding="utf-8")
    assert "manifest:file_set" in fin.check(folder)
    (folder / "games" / "849900.json").unlink()
    (folder / "games" / "849806.json").unlink()
    problems = fin.check(folder)
    assert "manifest:file_set" in problems and "index:rows" in problems
    assert "index:veteran_min" in fin.check(folder, 9)


@pytest.mark.parametrize("victim", ["manifest.json", "index-2026.json"])
def test_a_missing_manifest_or_index_is_a_problem(folder, victim):
    built(folder)
    (folder / victim).unlink()
    assert fin.check(folder) != []


def test_check_refuses_a_reconstructed_payload_that_todays_checks_refuse_and_a_published_one_without_lineage(folder, real_payload):
    built(folder)
    path = folder / "games" / "849806.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"]["matchups"][0]["status"] = "yesterday"
    path.write_text(ag.compact_json(document), encoding="utf-8")
    assert "game:payload" in fin.check(folder)
    built_again = published_game()
    built_again["payload"]["matchups"].append(deepcopy(built_again["payload"]["matchups"][0]))
    (folder / "games" / "849805.json").write_text(ag.compact_json(built_again), encoding="utf-8")
    assert "game:lineage:matchups" in fin.check(folder)


@pytest.mark.parametrize("stray", ["notes.txt", "games/extra.html", ".hidden", "games/sub/x.json"])
def test_check_finds_a_file_the_manifest_does_not_list(folder, stray):
    built(folder)
    path = folder / stray
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    assert "files:set" in fin.check(folder)


def test_main_exit_codes_and_closed_output(folder, capsys):
    assert fin.main(["build", "--dir", str(folder), "--veteran-min", str(V), "--built-at", BUILT_AT]) == 0
    assert fin.main(["check", "--dir", str(folder)]) == 0
    assert fin.main(["check", "--dir", str(folder), "--veteran-min", "9"]) == 1
    assert fin.main(["check", "--dir", str(folder / "nothing")]) == 2
    assert fin.main(["build", "--dir", str(folder), "--veteran-min", "0"]) == 2
    err = capsys.readouterr().err
    assert "index:veteran_min" in err and "veteran_min_not_set" in err and "Nick Martinez" not in err


def test_finalize_makes_no_request_and_imports_nothing_from_evals():
    source = Path(fin.__file__).read_text(encoding="utf-8")
    for forbidden in ("requests", "urllib", "socket", "import evals", "from evals", ".local", "live_pipeline"):
        assert forbidden not in source, forbidden


# --- publish_archive ------------------------------------------------------------------------------------------------

ARCHIVE = "public/data/archive"


class World:
    def __init__(self, tmp_path: Path, candidate: Path) -> None:
        self.remote = tmp_path / "remote.git"
        self.work = tmp_path / "work"
        self.candidate = candidate
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.work)], check=True)
        for key, value in (("user.name", "Someone Else"), ("user.email", "someone@example.com"), ("core.autocrlf", "false")):
            git(self.work, "config", key, value)
        (self.work / "public" / "data").mkdir(parents=True)
        (self.work / "public" / "data" / "pitchcraft-demo.json").write_text("{}\n", encoding="utf-8")
        (self.work / "app").mkdir()
        (self.work / "app" / "page.txt").write_text("page\n", encoding="utf-8")
        git(self.work, "add", "-A")
        git(self.work, "commit", "-q", "-m", "seed")
        git(self.work, "remote", "add", "origin", str(self.remote))
        git(self.work, "push", "-q", "origin", "main")
        self.seed = self.head()

    def head(self) -> str:
        return git(self.remote, "rev-parse", "main")

    def argv(self, *extra: str) -> list[str]:
        return [str(self.candidate), "--repo", str(self.work), "--remote", str(self.remote), *extra]


@pytest.fixture
def world(tmp_path, folder):
    built(folder)
    return World(tmp_path, folder)


@pytest.fixture
def publish():
    return load_publish()


def test_the_folder_is_committed_and_pushed_to_main_and_only_under_the_archive(publish, world, capsys):
    assert publish.main(world.argv()) == 0
    files = git(world.remote, "show", "--name-only", "--format=", "main").split()
    assert sorted(files) == sorted(f"{ARCHIVE}/{name}" for name in
                                   ("games/849805.json", "games/849806.json", "index-2026.json", "manifest.json"))
    assert git(world.remote, "log", "-1", "--format=%an|%ae|%cn|%ce|%s|%b", "main") == "|".join([*OWNER, *OWNER, "data: archive backfill 2026", ""])
    assert git(world.remote, "show", f"main:{ARCHIVE}/games/849805.json") == (world.candidate / "games" / "849805.json").read_text(encoding="utf-8").strip()
    assert "publish: pushed" in capsys.readouterr().out


def test_the_checkouts_own_identity_is_not_used(publish, world):
    git(world.work, "config", "user.name", "Another Person")
    assert publish.main(world.argv()) == 0
    assert git(world.remote, "log", "-1", "--format=%an", "main") == OWNER[0]


def test_a_second_publication_of_the_same_folder_commits_nothing(publish, world, capsys):
    assert publish.main(world.argv()) == 0
    git(world.work, "pull", "-q", "origin", "main")
    head = world.head()
    assert publish.main(world.argv()) == 0
    assert world.head() == head and "publish: unchanged" in capsys.readouterr().out


def test_a_correction_commits_only_the_files_that_changed(publish, world, real_payload):
    assert publish.main(world.argv()) == 0
    git(world.work, "pull", "-q", "origin", "main")
    write_game(world.candidate, reconstructed_game(real_payload, pk=849810, day="2026-07-05"))
    fin.build(world.candidate, V, BUILT_AT)
    assert publish.main(world.argv()) == 0
    changed = git(world.remote, "show", "--name-only", "--format=", "main").split()
    assert sorted(changed) == sorted(f"{ARCHIVE}/{n}" for n in ("games/849810.json", "index-2026.json", "manifest.json"))


def test_a_candidate_that_lacks_a_published_game_is_refused_a_backfill_never_deletes(publish, world, capsys):
    assert publish.main(world.argv()) == 0
    git(world.work, "pull", "-q", "origin", "main")
    head = world.head()
    (world.candidate / "games" / "849806.json").unlink()
    fin.build(world.candidate, V, BUILT_AT)
    assert publish.main(world.argv()) == 1
    assert "failed dropped_file" in capsys.readouterr().out and world.head() == head
    assert git(world.work, "status", "--porcelain") == ""


def test_dry_run_does_everything_in_a_clone_and_pushes_nothing(publish, world, capsys):
    assert publish.main(world.argv("--dry-run")) == 0
    out = capsys.readouterr().out
    assert "dry-run: would commit" in out and "allowlist ok" in out
    assert world.head() == world.seed and git(world.work, "status", "--porcelain") == ""
    assert not (world.work / ARCHIVE).exists()


def test_an_invalid_candidate_is_refused_and_nothing_is_copied(publish, world, capsys):
    path = world.candidate / "games" / "849805.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"away_runs":3', '"away_runs":4'), encoding="utf-8")
    assert publish.main(world.argv()) == 1
    assert "failed candidate_invalid" in capsys.readouterr().out
    assert world.head() == world.seed and not (world.work / ARCHIVE).exists()


def test_a_dirty_tree_and_a_branch_other_than_main_are_refused(publish, world, capsys):
    (world.work / "app" / "page.txt").write_text("edited\n", encoding="utf-8")
    assert publish.main(world.argv()) == 1 and "failed dirty_tree" in capsys.readouterr().out
    git(world.work, "checkout", "-q", "--", "app/page.txt")
    git(world.work, "checkout", "-q", "-b", "other")
    assert publish.main(world.argv()) == 1 and "failed not_on_main" in capsys.readouterr().out
    assert world.head() == world.seed


@pytest.mark.parametrize("stray", [".secret", "notes.txt", "games/extra.html", "games/.hidden", "games/sub/849805.json", "other/x.json"])
def test_a_hidden_or_stray_file_in_the_candidate_is_refused_and_nothing_is_published(publish, world, stray):
    path = world.candidate / stray
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    assert publish.main(world.argv()) == 1
    assert world.head() == world.seed and not (world.work / ARCHIVE).exists()


def test_a_missing_directory_and_a_missing_key_are_refused(publish, world, tmp_path, capsys):
    assert publish.main([str(tmp_path / "nothing"), "--repo", str(world.work), "--remote", str(world.remote)]) == 1
    assert "failed candidate_unreadable" in capsys.readouterr().out
    with pytest.raises(SystemExit):
        publish.main([str(world.candidate), "--repo", str(world.work), "--key-file", str(tmp_path / "no-key")])


def test_a_path_outside_public_data_is_refused_by_the_allowlist_and_rolled_back(publish, world, capsys):
    """Control for D15: if the destination were ever moved out of `public/data/`, nothing would be committed."""

    publish.ARCHIVE_DIR = "app/archive"
    assert publish.main(world.argv()) == 1
    assert "failed outside_allowlist" in capsys.readouterr().out
    assert world.head() == world.seed and git(world.work, "status", "--porcelain") == ""
    assert not (world.work / "app" / "archive").exists() or not any((world.work / "app" / "archive").rglob("*.json"))


def test_the_publisher_names_no_path_outside_the_archive(publish):
    source = Path(publish.__file__).read_text(encoding="utf-8")
    assert source.count('"public/data/archive"') == 1
    assert publish.ARCHIVE_DIR == "public/data/archive"
