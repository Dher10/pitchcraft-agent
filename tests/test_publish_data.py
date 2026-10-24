"""P1.2-c: `scripts/publish_data.py` commits the day's file to `main` and touches nothing else (docs/plans/P1.md, 4.2).

Everything runs against local repositories in a temporary directory: a bare repository stands for GitHub and a clone of it
for the checkout of the publish job. No test pushes anywhere real. The push over SSH, which only the deploy key on
`main` can prove, is covered by the command line the script builds (the recorded `git push`) and by the pinned host keys.

The rules under test: the work tree must be clean before the file is copied; only `public/data/` and `evals/live/` may
change (D15); the commit is the owner's (D42) with the subject `data: daily update YYYY-MM-DD`; a file that is the same
apart from its timestamps is not committed; the push is never forced and goes to `main` only; `--dry-run` does all of it
in a temporary clone and pushes nothing.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "publish_data.py"
TARGET = "public/data/pitchcraft-demo.json"
OWNER = ("Daniel Herdenez", "edherdenez@gmail.com")
KEY_SENTINEL = "PRIVATE-KEY-SENTINEL-do-not-print"

# GitHub's published SSH key fingerprints, read from docs.github.com ("GitHub's SSH key fingerprints") on 2026-10-22.
# They are copied here on purpose: the script's pinned keys must hash to the ones the documentation lists.
DOCUMENTED_FINGERPRINTS = {
    "ssh-ed25519": "SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU",
    "ecdsa-sha2-nistp256": "SHA256:p2QAMXNIC1TJYWeIOttrVc98/R1BUFWu3/LiyKgUfQM",
    "ssh-rsa": "SHA256:uNiVztksCsDhcc0u9e8BujQXVUpKZIDTMczCvj3tD2s",
}


def load_script():
    spec = importlib.util.spec_from_file_location("publish_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def publish():
    return load_script()


@pytest.fixture(autouse=True)
def clean_git_environment(monkeypatch):
    """The machine's own git configuration (identity, autocrlf, hooks) must not decide what a test sees."""

    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(Path(tempfile.gettempdir()) / "pitchcraft-no-such-gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "GIT_SSH_COMMAND"):
        monkeypatch.delenv(name, raising=False)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def payload(target: str = "2026-07-15", fetched: str = "2026-07-15T15:00:03+00:00", headline: str = "A") -> dict:
    return {
        "metadata": {
            "generated_at": fetched,
            "data_fetched_at": fetched,
            "data_status": {"mode": "fetched_snapshot", "live_run": {"run_at": fetched, "target_date": target}},
        },
        "matchups": [{"id": "matchup_001", "title": headline}],
    }


def text_of(value: dict) -> str:
    return json.dumps(value, indent=2) + chr(10)


class World:
    """A bare repository (GitHub), the checkout of the publish job, and a candidate file."""

    def __init__(self, tmp_path: Path) -> None:
        self.remote = tmp_path / "remote.git"
        self.work = tmp_path / "work"
        self.other = tmp_path / "other"
        self.candidate = tmp_path / "candidate" / "pitchcraft-demo.json"
        subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(self.remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.work)], check=True)
        self.configure(self.work)
        (self.work / "public" / "data").mkdir(parents=True)
        (self.work / "app").mkdir()
        (self.work / TARGET).write_text(text_of(payload("2026-07-14", "2026-07-14T15:00:01+00:00", "OLD")), encoding="utf-8")
        (self.work / "app" / "page.txt").write_text("page" + chr(10), encoding="utf-8")
        git(self.work, "add", "-A")
        git(self.work, "commit", "-q", "-m", "seed")
        git(self.work, "remote", "add", "origin", str(self.remote))
        git(self.work, "push", "-q", "origin", "main")
        self.seed = self.remote_head()
        self.write_candidate(payload())

    @staticmethod
    def configure(repo: Path) -> None:
        git(repo, "config", "user.name", "Someone Else")
        git(repo, "config", "user.email", "someone@example.com")
        git(repo, "config", "core.autocrlf", "false")

    def write_candidate(self, value: dict) -> None:
        self.candidate.parent.mkdir(parents=True, exist_ok=True)
        self.candidate.write_text(text_of(value), encoding="utf-8")

    def remote_head(self) -> str:
        return git(self.remote, "rev-parse", "main")

    def argv(self, *extra: str) -> list[str]:
        return [str(self.candidate), "--repo", str(self.work), "--remote", str(self.remote), *extra]

    def advance_remote(self) -> str:
        """Another writer pushed to `main` after the checkout."""

        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.other)], check=True)
        self.configure(self.other)
        (self.other / "elsewhere.txt").write_text("x" + chr(10), encoding="utf-8")
        git(self.other, "add", "-A")
        git(self.other, "commit", "-q", "-m", "elsewhere")
        git(self.other, "push", "-q", "origin", "main")
        return self.remote_head()


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


# --- a good publication ---------------------------------------------------------------------------------------


def test_a_changed_file_is_committed_and_pushed_to_main(publish, world, capsys):
    assert publish.main(world.argv()) == 0

    assert world.remote_head() != world.seed
    assert git(world.remote, "show", "main:" + TARGET) + chr(10) == world.candidate.read_text(encoding="utf-8")
    assert git(world.remote, "show", "--name-only", "--format=", "main").split() == [TARGET]
    assert "publish: pushed" in capsys.readouterr().out


def test_the_commit_is_the_owners_with_the_subject_of_d42(publish, world):
    git(world.work, "config", "user.name", "Another Person")  # the checkout's own identity must not be used

    assert publish.main(world.argv()) == 0

    fields = git(world.remote, "log", "-1", "--format=%an|%ae|%cn|%ce|%s", "main").split("|")
    assert fields == [OWNER[0], OWNER[1], OWNER[0], OWNER[1], "data: daily update 2026-07-15"]


def test_the_subject_names_the_day_of_the_games_not_the_day_of_the_run(publish, world):
    world.write_candidate(payload(target="2026-09-30", fetched="2026-10-01T15:00:00+00:00"))

    assert publish.main(world.argv()) == 0

    assert git(world.remote, "log", "-1", "--format=%s", "main") == "data: daily update 2026-09-30"


@pytest.mark.parametrize("newline", [chr(10), chr(13) + chr(10)])
def test_the_committed_bytes_are_the_candidates_exactly(publish, world, newline):
    # No newline translation in either direction, and non-ASCII text survives (a team or player name).
    text = json.dumps(payload(headline="Peña"), indent=2, ensure_ascii=False).replace(chr(10), newline) + newline
    world.candidate.write_bytes(text.encode("utf-8"))

    assert publish.main(world.argv()) == 0

    assert (world.work / TARGET).read_bytes() == world.candidate.read_bytes() == text.encode("utf-8")


def test_the_commit_has_no_trailer_and_a_one_line_message(publish, world):
    assert publish.main(world.argv()) == 0

    assert git(world.remote, "log", "-1", "--format=%B", "main").strip() == "data: daily update 2026-07-15"


# --- a file that did not change ---------------------------------------------------------------------------------


def test_a_file_that_differs_only_in_its_timestamps_is_not_committed(publish, world, capsys):
    (world.work / TARGET).write_text(text_of(payload("2026-07-15", "2026-07-15T09:00:00+00:00", "A")), encoding="utf-8")
    git(world.work, "add", "-A")
    git(world.work, "commit", "-q", "-m", "earlier run")
    git(world.work, "push", "-q", "origin", "main")
    before = world.remote_head()
    world.write_candidate(payload("2026-07-15", "2026-07-15T15:00:03+00:00", "A"))

    assert publish.main(world.argv()) == 0

    assert world.remote_head() == before
    assert git(world.work, "status", "--porcelain") == ""
    assert "publish: unchanged" in capsys.readouterr().out


@pytest.mark.parametrize("edit", ["headline", "target_date", "new_key"])
def test_a_file_that_differs_in_anything_else_is_committed(publish, world, edit):
    (world.work / TARGET).write_text(text_of(payload()), encoding="utf-8")
    git(world.work, "add", "-A")
    git(world.work, "commit", "-q", "-m", "same day")
    git(world.work, "push", "-q", "origin", "main")
    before = world.remote_head()
    changed = payload(headline="B" if edit == "headline" else "A", target="2026-07-16" if edit == "target_date" else "2026-07-15")
    if edit == "new_key":
        changed["matchups"][0]["extra"] = 1
    world.write_candidate(changed)

    assert publish.main(world.argv()) == 0

    assert world.remote_head() != before


def test_only_the_three_timestamps_are_ignored(publish):
    base = payload()
    assert publish.same_apart_from_timestamps(text_of(base), text_of(payload(fetched="2030-01-01T00:00:00+00:00")))
    assert not publish.same_apart_from_timestamps(text_of(base), text_of({**base, "generated_on": "x"}))
    other = payload()
    other["matchups"][0]["created_at"] = "2026-07-15T00:00:00+00:00"
    assert not publish.same_apart_from_timestamps(text_of(base), text_of(other))
    assert publish.TIMESTAMP_KEYS == {"generated_at", "data_fetched_at", "run_at"}


@pytest.mark.parametrize("old", ["", "not json", "[1, 2]"])
def test_a_previous_file_that_is_not_a_payload_is_always_replaced(publish, old):
    assert not publish.same_apart_from_timestamps(old, text_of(payload()))


def test_a_target_that_does_not_exist_yet_is_created(publish, world):
    git(world.work, "rm", "-q", TARGET)
    git(world.work, "commit", "-q", "-m", "no file yet")
    git(world.work, "push", "-q", "origin", "main")

    assert publish.main(world.argv()) == 0

    assert git(world.remote, "show", "--name-only", "--format=", "main").split() == [TARGET]


# --- the allowlist (D15) ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path", ["public/data/pitchcraft-demo.json", "public/data/a/b.json", "evals/live/heartbeat.txt", "evals/live/2026/x.json"]
)
def test_paths_under_the_two_published_folders_are_allowed(publish, path):
    assert publish.outside_allowlist([path]) == []


@pytest.mark.parametrize(
    "path",
    [
        "app/page.tsx",
        ".github/workflows/daily.yml",
        "scripts/publish_data.py",
        "public/dataX/x.json",
        "public/data",
        "public/data/",
        "public/datax",
        "public/data/../../app/page.tsx",
        "/public/data/x.json",
        "./public/data/x.json",
        "public" + chr(92) + "data" + chr(92) + "x.json",
        "evals/live2/x.json",
        "evals/lives/x",
        "evals/x/live/y",
        "PUBLIC/DATA/x.json",
        "",
        " public/data/x.json",
    ],
)
def test_every_other_path_is_outside(publish, path):
    assert publish.outside_allowlist(["public/data/ok.json", path]) == [path]


def test_nothing_is_outside_an_empty_list(publish):
    assert publish.outside_allowlist([]) == []


def test_a_copy_that_would_land_outside_the_folders_is_refused_and_undone(publish, world, monkeypatch, capsys):
    monkeypatch.setattr(publish, "TARGET", "app/data.json")

    assert publish.main(world.argv()) == 1

    assert world.remote_head() == world.seed
    assert not (world.work / "app" / "data.json").exists()
    assert git(world.work, "status", "--porcelain") == ""
    assert "publish: failed outside_allowlist" in capsys.readouterr().out


def test_a_copy_over_a_tracked_file_outside_the_folders_puts_the_old_bytes_back(publish, world, monkeypatch):
    monkeypatch.setattr(publish, "TARGET", "app/page.txt")

    assert publish.main(world.argv()) == 1

    assert (world.work / "app" / "page.txt").read_text(encoding="utf-8") == "page" + chr(10)
    assert git(world.work, "status", "--porcelain") == ""


def test_changed_paths_reads_renames_and_untracked_files(publish, world):
    git(world.work, "mv", "app/page.txt", "app/page2.txt")
    (world.work / "new.txt").write_text("n", encoding="utf-8")
    (world.work / TARGET).write_text("{}", encoding="utf-8")

    assert sorted(publish.changed_paths(world.work)) == ["app/page.txt", "app/page2.txt", "new.txt", TARGET]


# --- a work tree that is not clean ------------------------------------------------------------------------------


@pytest.mark.parametrize("dirt", ["untracked", "modified", "staged"])
def test_a_work_tree_that_is_not_clean_is_refused_before_anything_is_copied(publish, world, capsys, dirt):
    if dirt == "untracked":
        (world.work / "notes.txt").write_text("n", encoding="utf-8")
    elif dirt == "modified":
        (world.work / "app" / "page.txt").write_text("changed", encoding="utf-8")
    else:
        (world.work / "app" / "page.txt").write_text("changed", encoding="utf-8")
        git(world.work, "add", "-A")
    snapshot = git(world.work, "status", "--porcelain")

    assert publish.main(world.argv()) == 1

    assert world.remote_head() == world.seed
    assert git(world.work, "status", "--porcelain") == snapshot
    assert (world.work / TARGET).read_text(encoding="utf-8") != world.candidate.read_text(encoding="utf-8")
    assert "publish: failed dirty_tree" in capsys.readouterr().out


def test_a_file_the_repository_ignores_does_not_count_as_dirt(publish, world):
    (world.work / ".gitignore").write_text("data_cache/" + chr(10) + "__pycache__/" + chr(10), encoding="utf-8")
    git(world.work, "add", "-A")
    git(world.work, "commit", "-q", "-m", "ignore")
    git(world.work, "push", "-q", "origin", "main")
    (world.work / "data_cache").mkdir()
    (world.work / "data_cache" / "x.json").write_text("{}", encoding="utf-8")

    assert publish.main(world.argv()) == 0


# --- a candidate that cannot be published -----------------------------------------------------------------------


def broken_candidates():
    good = payload()
    no_run = {"metadata": {"data_status": {}}}
    return {
        "not json": "not json",
        "empty": "",
        "list": "[]",
        "no live run": json.dumps(no_run),
        "date missing": json.dumps({"metadata": {"data_status": {"live_run": {"target_date": None}}}}),
        "date not a date": json.dumps(payload(target="yesterday")),
        "date with a message in it": json.dumps(payload(target="2026-07-15 Co-Authored-By: x")),
        "date with a newline": json.dumps(payload(target="2026-07-15" + chr(10) + "x")),
        "nan": json.dumps(good).replace('"A"', "NaN"),
    }


@pytest.mark.parametrize("name", list(broken_candidates()))
def test_a_candidate_that_cannot_be_read_is_refused_and_nothing_changes(publish, world, capsys, name):
    world.candidate.write_text(broken_candidates()[name], encoding="utf-8")
    before = (world.work / TARGET).read_bytes()

    assert publish.main(world.argv()) == 1

    assert world.remote_head() == world.seed and (world.work / TARGET).read_bytes() == before
    assert git(world.work, "status", "--porcelain") == ""
    assert "publish: failed candidate_unreadable" in capsys.readouterr().out


def test_a_missing_candidate_is_refused(publish, world, capsys):
    world.candidate.unlink()

    assert publish.main(world.argv()) == 1

    assert "publish: failed candidate_unreadable" in capsys.readouterr().out


# --- the push ---------------------------------------------------------------------------------------------------


def test_a_push_that_the_remote_rejects_is_a_failure_and_never_forced(publish, world, capsys):
    other_head = world.advance_remote()

    assert publish.main(world.argv()) == 1

    assert world.remote_head() == other_head
    assert "publish: failed push_rejected" in capsys.readouterr().out


def test_a_rejected_push_prints_the_refusal_and_not_git_s_advice(publish, world, capsys):
    world.advance_remote()

    assert publish.main(world.argv()) == 1

    shown = capsys.readouterr()
    assert "rejected" in shown.err and "hint:" not in shown.err and "hint:" not in shown.out


def test_a_commit_that_git_refuses_leaves_the_tree_as_it_was(publish, world, capsys):
    hook = world.work / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh" + chr(10) + "exit 1" + chr(10), encoding="utf-8", newline=chr(10))
    hook.chmod(0o755)
    before = (world.work / TARGET).read_bytes()

    assert publish.main(world.argv()) == 1

    assert (world.work / TARGET).read_bytes() == before and git(world.work, "status", "--porcelain") == ""
    assert "publish: failed git_failed" in capsys.readouterr().out and world.remote_head() == world.seed


def test_only_main_is_ever_pushed(publish, world, capsys):
    git(world.work, "checkout", "-q", "-b", "v2")

    assert publish.main(world.argv()) == 1

    assert world.remote_head() == world.seed
    assert "publish: failed not_on_main" in capsys.readouterr().out


class Recorder:
    """Stands in for `subprocess.run`: real for everything but a push to an SSH remote, which it records and accepts."""

    def __init__(self, real) -> None:
        self.real = real
        self.pushes: list[tuple[list[str], dict]] = []

    def __call__(self, args, **kwargs):
        if "push" in args:
            self.pushes.append((list(args), dict(kwargs.get("env") or {})))
            return subprocess.CompletedProcess(args, 0, stdout="", stderr="")
        return self.real(args, **kwargs)


def ssh_publish(publish, world, monkeypatch, tmp_path):
    key = tmp_path / "deploy_key"
    key.write_text(KEY_SENTINEL, encoding="utf-8")
    recorder = Recorder(subprocess.run)
    monkeypatch.setattr(publish.subprocess, "run", recorder)
    code = publish.main(
        [str(world.candidate), "--repo", str(world.work), "--remote", publish.DEFAULT_REMOTE, "--key-file", str(key)]
    )
    return code, recorder, key


def test_the_push_goes_to_main_over_ssh_with_the_key_and_the_pinned_host_keys(publish, world, monkeypatch, tmp_path):
    code, recorder, key = ssh_publish(publish, world, monkeypatch, tmp_path)

    assert code == 0 and len(recorder.pushes) == 1
    args, env = recorder.pushes[0]
    assert args[-2:] == ["git@github.com:Dher10/pitchcraft-agent.git", "HEAD:refs/heads/main"]
    command = env["GIT_SSH_COMMAND"]
    assert str(key) in command or key.as_posix() in command
    for option in ("IdentitiesOnly=yes", "StrictHostKeyChecking=yes", "BatchMode=yes", "UserKnownHostsFile="):
        assert option in command
    assert env.get("GIT_TERMINAL_PROMPT") == "0"


def test_the_push_is_never_forced(publish, world, monkeypatch, tmp_path):
    code, recorder, _ = ssh_publish(publish, world, monkeypatch, tmp_path)

    args, _ = recorder.pushes[0]
    assert code == 0
    assert not [a for a in args if a.startswith("--force") or a == "-f" or a.startswith("+") or a.startswith("--delete")]
    assert "--tags" not in args and "--mirror" not in args and "--all" not in args


def test_the_key_file_is_named_to_ssh_and_never_read_or_printed(publish, world, monkeypatch, tmp_path, capsys):
    code, recorder, _ = ssh_publish(publish, world, monkeypatch, tmp_path)

    args, env = recorder.pushes[0]
    shown = capsys.readouterr()
    assert code == 0
    assert KEY_SENTINEL not in shown.out + shown.err + " ".join(args) + repr(env)


def test_an_ssh_remote_needs_a_key_file_and_nothing_is_touched_without_one(publish, world, capsys):
    before = (world.work / TARGET).read_bytes()

    with pytest.raises(SystemExit) as caught:
        publish.main([str(world.candidate), "--repo", str(world.work), "--remote", publish.DEFAULT_REMOTE])

    assert caught.value.code == 2 and (world.work / TARGET).read_bytes() == before
    assert git(world.work, "status", "--porcelain") == ""


def test_a_key_file_that_does_not_exist_is_a_usage_error(publish, world, tmp_path):
    with pytest.raises(SystemExit) as caught:
        publish.main(world.argv("--key-file", str(tmp_path / "missing")))

    assert caught.value.code == 2 and world.remote_head() == world.seed


def test_the_default_remote_is_this_repository_over_ssh(publish):
    assert publish.DEFAULT_REMOTE == "git@github.com:Dher10/pitchcraft-agent.git"


def test_the_pinned_host_keys_are_the_ones_github_documents(publish):
    lines = publish.known_hosts_text().splitlines()

    assert len(lines) == 3 and all(line.startswith("github.com ") for line in lines)
    found = {}
    for line in lines:
        _, kind, key = line.split(" ")
        digest = base64.b64encode(hashlib.sha256(base64.b64decode(key)).digest()).decode().rstrip("=")
        found[kind] = "SHA256:" + digest
    assert found == DOCUMENTED_FINGERPRINTS


def test_the_ssh_command_refuses_any_host_it_does_not_know(publish, tmp_path):
    command = publish.ssh_command(tmp_path / "key", tmp_path / "known_hosts")

    assert command.startswith("ssh ")
    assert "StrictHostKeyChecking=yes" in command and "StrictHostKeyChecking=no" not in command
    assert "UserKnownHostsFile=" in command and "GlobalKnownHostsFile=" in command
    assert "IdentitiesOnly=yes" in command and "BatchMode=yes" in command


# --- --dry-run --------------------------------------------------------------------------------------------------


def test_dry_run_pushes_nothing_and_leaves_the_checkout_as_it_was(publish, world, capsys):
    head = git(world.work, "rev-parse", "HEAD")
    before = (world.work / TARGET).read_bytes()

    assert publish.main(world.argv("--dry-run")) == 0

    out = capsys.readouterr().out
    assert world.remote_head() == world.seed
    assert git(world.work, "rev-parse", "HEAD") == head and (world.work / TARGET).read_bytes() == before
    assert git(world.work, "status", "--porcelain") == ""
    assert "publish: dry-run" in out and "publish: file " + TARGET in out and "publish: allowlist ok" in out


def test_dry_run_needs_no_key_and_no_ssh(publish, world, monkeypatch):
    recorder = Recorder(subprocess.run)
    monkeypatch.setattr(publish.subprocess, "run", recorder)

    code = publish.main([str(world.candidate), "--repo", str(world.work), "--remote", publish.DEFAULT_REMOTE, "--dry-run"])

    assert code == 0 and recorder.pushes == []


def test_dry_run_works_on_a_branch_that_is_not_main(publish, world):
    git(world.work, "checkout", "-q", "-b", "v2")

    assert publish.main(world.argv("--dry-run")) == 0


def test_dry_run_says_unchanged_for_a_file_that_would_not_be_committed(publish, world, capsys):
    (world.work / TARGET).write_text(text_of(payload("2026-07-15", "2026-07-15T09:00:00+00:00")), encoding="utf-8")
    git(world.work, "add", "-A")
    git(world.work, "commit", "-q", "-m", "earlier run")

    assert publish.main(world.argv("--dry-run")) == 0

    assert "publish: unchanged" in capsys.readouterr().out


def test_dry_run_reports_a_target_outside_the_folders_and_still_pushes_nothing(publish, world, monkeypatch, capsys):
    monkeypatch.setattr(publish, "TARGET", "app/data.json")

    assert publish.main(world.argv("--dry-run")) == 1

    assert "publish: failed outside_allowlist" in capsys.readouterr().out
    assert not (world.work / "app" / "data.json").exists() and world.remote_head() == world.seed


def test_dry_run_leaves_no_temporary_clone_behind(publish, world, monkeypatch, tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))

    assert publish.main(world.argv("--dry-run")) == 0

    assert list(scratch.iterdir()) == []


def test_dry_run_of_a_dirty_checkout_is_refused_too(publish, world, capsys):
    (world.work / "notes.txt").write_text("n", encoding="utf-8")

    assert publish.main(world.argv("--dry-run")) == 1

    assert "publish: failed dirty_tree" in capsys.readouterr().out


# --- usage and structure ----------------------------------------------------------------------------------------


def test_the_candidate_is_required(publish):
    with pytest.raises(SystemExit) as caught:
        publish.main([])

    assert caught.value.code == 2


def test_no_branch_option_exists_because_main_is_the_only_target(publish, world):
    with pytest.raises(SystemExit) as caught:
        publish.main(world.argv("--branch", "v2"))

    assert caught.value.code == 2


def test_the_published_folders_are_the_ones_of_d15(publish):
    assert publish.ALLOWED_PREFIXES == ("public/data/", "evals/live/") and publish.TARGET == TARGET


def test_the_identity_is_the_owners(publish):
    assert (publish.IDENTITY_NAME, publish.IDENTITY_EMAIL) == OWNER


def test_the_script_runs_as_a_program(world):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *world.argv("--dry-run")], capture_output=True, text=True, timeout=120, cwd=ROOT
    )

    assert result.returncode == 0, result.stderr
    assert "publish: allowlist ok" in result.stdout and world.remote_head() == world.seed


# --- QA1-05: the identity of the commit is the owner's whatever the environment says --------------------------------------

OTHER_IDENTITY = {
    "GIT_AUTHOR_NAME": "Other Author",
    "GIT_AUTHOR_EMAIL": "other@example.com",
    "GIT_COMMITTER_NAME": "Other Committer",
    "GIT_COMMITTER_EMAIL": "committer@example.com",
}


def test_inherited_identity_variables_do_not_change_the_author_or_the_committer(publish, world, monkeypatch):
    for name, value in OTHER_IDENTITY.items():
        monkeypatch.setenv(name, value)

    assert publish.main(world.argv()) == 0

    fields = git(world.remote, "log", "-1", "--format=%an|%ae|%cn|%ce", "main").split("|")
    assert fields == [OWNER[0], OWNER[1], OWNER[0], OWNER[1]]


@pytest.mark.parametrize("name", sorted(OTHER_IDENTITY))
def test_each_inherited_identity_variable_alone_is_overridden(publish, world, monkeypatch, name):
    monkeypatch.setenv(name, "Somebody Else" if name.endswith("NAME") else "somebody@example.com")

    assert publish.main(world.argv()) == 0

    fields = git(world.remote, "log", "-1", "--format=%an|%ae|%cn|%ce", "main").split("|")
    assert fields == [OWNER[0], OWNER[1], OWNER[0], OWNER[1]]


def test_the_commit_environment_names_the_owner_for_author_and_committer(publish):
    env = publish._commit_env()

    assert (env["GIT_AUTHOR_NAME"], env["GIT_AUTHOR_EMAIL"]) == OWNER
    assert (env["GIT_COMMITTER_NAME"], env["GIT_COMMITTER_EMAIL"]) == OWNER


def test_control_a_clean_environment_gives_the_owner_too(publish, world):
    assert publish.main(world.argv()) == 0

    assert git(world.remote, "log", "-1", "--format=%an|%cn", "main") == f"{OWNER[0]}|{OWNER[0]}"


# --- QA1-06: a failure at any step after the copy leaves the tree as it was, and is a closed failure ----------------------

CLOSED_CODES = ("candidate_unreadable", "dirty_tree", "not_on_main", "outside_allowlist", "git_failed", "push_rejected")
OLD_TEXT = text_of(payload("2026-07-14", "2026-07-14T15:00:01+00:00", "OLD"))


def fail_at(publish, monkeypatch, step: str, error: Exception, nth: int = 1) -> dict:
    """Make the `nth` git call that has `step` among its arguments raise `error`, as a process that cannot be started would."""

    real = publish._git
    seen = {"calls": 0, "raised": 0}

    def wrapper(repo, *args, env=None):
        if step in args:
            seen["calls"] += 1
            if seen["calls"] == nth:
                seen["raised"] += 1
                raise error
        return real(repo, *args, env=env)

    monkeypatch.setattr(publish, "_git", wrapper)
    return seen


def assert_untouched(world, capsys, code: str) -> None:
    shown = capsys.readouterr()
    assert f"publish: failed {code}" in shown.out, shown
    assert "Traceback" not in shown.err and "Traceback" not in shown.out
    assert (world.work / TARGET).read_text(encoding="utf-8") == OLD_TEXT
    assert git(world.work, "status", "--porcelain") == ""
    assert world.remote_head() == world.seed


@pytest.mark.parametrize(
    "step, nth",
    [("status", 2), ("add", 1), ("commit", 1)],  # status 1 is the clean-tree check before the copy
)
@pytest.mark.parametrize("error", [OSError("synthetic process failure"), FileNotFoundError("git"), PermissionError("denied")])
def test_a_process_that_cannot_be_started_after_the_copy_is_git_failed_and_the_tree_is_put_back(
    publish, world, monkeypatch, capsys, step, nth, error
):
    seen = fail_at(publish, monkeypatch, step, error, nth)

    assert publish.main(world.argv()) == 1

    assert seen["raised"] == 1
    assert_untouched(world, capsys, "git_failed")


def test_a_failing_status_after_the_copy_puts_the_tree_back(publish, world, monkeypatch, capsys):
    real = publish.changed_paths
    calls = {"n": 0}

    def second_call_fails(repo):
        calls["n"] += 1
        if calls["n"] == 2:
            raise publish.Failure("git_failed")
        return real(repo)

    monkeypatch.setattr(publish, "changed_paths", second_call_fails)

    assert publish.main(world.argv()) == 1

    assert calls["n"] == 2
    assert_untouched(world, capsys, "git_failed")


def test_a_git_add_that_fails_for_real_puts_the_tree_back(publish, world, capsys):
    lock = world.work / ".git" / "index.lock"
    lock.write_text("", encoding="utf-8")  # git add cannot take the lock

    assert publish.main(world.argv()) == 1

    lock.unlink()
    assert_untouched(world, capsys, "git_failed")


def test_a_commit_that_fails_for_real_and_a_reset_that_cannot_run_still_end_in_the_closed_failure(publish, world, monkeypatch, capsys):
    hook = world.work / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh" + chr(10) + "exit 1" + chr(10), encoding="utf-8", newline=chr(10))
    hook.chmod(0o755)
    fail_at(publish, monkeypatch, "reset", OSError("synthetic"))

    assert publish.main(world.argv()) == 1

    hook.unlink()
    git(world.work, "reset", "-q")  # the reset the script could not run: the index still holds the staged copy
    shown = capsys.readouterr()
    assert "publish: failed git_failed" in shown.out and "Traceback" not in shown.err
    assert (world.work / TARGET).read_text(encoding="utf-8") == OLD_TEXT and git(world.work, "status", "--porcelain") == ""


def test_a_reset_whose_output_cannot_be_decoded_does_not_stop_the_file_from_being_put_back(publish, world, monkeypatch, capsys):
    fail_at(publish, monkeypatch, "reset", UnicodeDecodeError("utf-8", bytes([255]), 0, 1, "invalid start byte"))
    monkeypatch.setattr(publish, "TARGET", "app/page.txt")  # outside the allowlist: the rollback runs, the code stays outside_allowlist

    assert publish.main(world.argv()) == 1

    assert (world.work / "app" / "page.txt").read_text(encoding="utf-8") == "page" + chr(10)
    assert "publish: failed outside_allowlist" in capsys.readouterr().out


def test_a_write_that_fails_halfway_puts_the_old_bytes_back(publish, world, monkeypatch, capsys):
    real = publish.Path.write_bytes
    calls = {"n": 0}

    def write_then_fail(path, data):
        written = real(path, data)
        if path.as_posix().endswith(TARGET):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("disk full")
        return written

    monkeypatch.setattr(publish.Path, "write_bytes", write_then_fail)

    assert publish.main(world.argv()) == 1

    assert_untouched(world, capsys, "git_failed")


def test_a_target_that_does_not_exist_yet_is_removed_when_the_commit_fails(publish, world, monkeypatch, capsys):
    git(world.work, "rm", "-q", TARGET)
    git(world.work, "commit", "-q", "-m", "remove the file")
    removed = git(world.work, "rev-parse", "HEAD")
    git(world.work, "push", "-q", "origin", "main")
    seed = world.remote_head()
    fail_at(publish, monkeypatch, "commit", OSError("synthetic"))

    assert publish.main(world.argv()) == 1

    assert not (world.work / TARGET).exists() and git(world.work, "status", "--porcelain") == ""
    assert git(world.work, "rev-parse", "HEAD") == removed and world.remote_head() == seed
    assert "publish: failed git_failed" in capsys.readouterr().out


@pytest.mark.parametrize("step", ["branch", "status"])
def test_a_process_that_cannot_be_started_before_the_copy_is_a_closed_failure_too(publish, world, monkeypatch, capsys, step):
    fail_at(publish, monkeypatch, step, OSError("synthetic"))

    assert publish.main(world.argv()) == 1

    assert_untouched(world, capsys, "git_failed")


def test_a_push_that_cannot_be_started_is_a_closed_failure_and_nothing_is_pushed(publish, world, monkeypatch, capsys):
    real = publish.subprocess.run

    def run(command, *args, **kwargs):
        if "push" in command:
            raise OSError("synthetic")
        return real(command, *args, **kwargs)

    monkeypatch.setattr(publish.subprocess, "run", run)

    assert publish.main(world.argv()) == 1

    shown = capsys.readouterr()
    assert "publish: failed git_failed" in shown.out and "Traceback" not in shown.err
    assert world.remote_head() == world.seed


def test_a_dry_run_whose_clone_cannot_be_made_is_a_closed_failure_and_leaves_no_clone(publish, world, monkeypatch, capsys, tmp_path):
    real = publish.subprocess.run

    def run(command, *args, **kwargs):
        if "clone" in command:
            raise OSError("synthetic")
        return real(command, *args, **kwargs)

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(publish.subprocess, "run", run)
    monkeypatch.setattr(publish.tempfile, "tempdir", str(scratch))

    assert publish.main(world.argv("--dry-run")) == 1

    assert "publish: failed git_failed" in capsys.readouterr().out
    assert list(scratch.iterdir()) == []
    assert git(world.work, "status", "--porcelain") == ""


def test_a_dry_run_that_fails_in_the_clone_leaves_the_checkout_and_the_clone_clean(publish, world, monkeypatch, capsys, tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(publish.tempfile, "tempdir", str(scratch))
    fail_at(publish, monkeypatch, "add", OSError("synthetic"))

    assert publish.main(world.argv("--dry-run")) == 1

    assert "publish: failed git_failed" in capsys.readouterr().out
    assert list(scratch.iterdir()) == []
    assert (world.work / TARGET).read_text(encoding="utf-8") == OLD_TEXT
    assert git(world.work, "status", "--porcelain") == ""


def test_an_exception_message_is_never_printed(publish, world, monkeypatch, capsys):
    fail_at(publish, monkeypatch, "add", OSError("SECRET-LOOKING-MESSAGE /home/runner/key"), 1)

    assert publish.main(world.argv()) == 1

    shown = capsys.readouterr()
    assert "SECRET-LOOKING-MESSAGE" not in shown.out + shown.err


def test_every_failure_the_script_raises_is_one_of_the_closed_codes():
    import re

    codes = set(re.findall(r'Failure\("([a-z_]+)"\)', SCRIPT.read_text(encoding="utf-8")))

    assert codes and codes <= set(CLOSED_CODES), codes


# --- P1.8: heartbeat; every repository and push here is local -----------------------------------------------

HEARTBEAT = "evals/live/heartbeat.txt"
HEARTBEAT_NOW = datetime(2026, 11, 30, 15, tzinfo=timezone.utc)


@pytest.fixture
def heartbeat_clock(publish, monkeypatch):
    monkeypatch.setattr(publish, "utc_now", lambda: HEARTBEAT_NOW, raising=False)
    monkeypatch.setenv("GIT_AUTHOR_DATE", HEARTBEAT_NOW.isoformat())
    monkeypatch.setenv("GIT_COMMITTER_DATE", HEARTBEAT_NOW.isoformat())


def dated_commit(world, monkeypatch, when, subject="data: daily update 2026-10-30", owner=OWNER):
    """An actual historical commit; the author is the owner because the deployed bot uses D42's identity."""
    with monkeypatch.context() as clock:
        clock.setenv("GIT_AUTHOR_DATE", when.isoformat())
        clock.setenv("GIT_COMMITTER_DATE", when.isoformat())
        clock.setenv("GIT_AUTHOR_NAME", owner[0])
        clock.setenv("GIT_AUTHOR_EMAIL", owner[1])
        clock.setenv("GIT_COMMITTER_NAME", owner[0])
        clock.setenv("GIT_COMMITTER_EMAIL", owner[1])
        git(world.work, "add", "-A")
        git(world.work, "commit", "--allow-empty", "-q", "-m", subject)
    git(world.work, "push", "-q", "origin", "main")
    return world.remote_head()


def same_candidate_as_committed(world):
    world.candidate.write_bytes((world.work / TARGET).read_bytes())


@pytest.mark.parametrize("seconds", [1, 24 * 60 * 60])
def test_old_bot_commit_gets_one_utc_heartbeat_even_without_a_data_change(
    publish, world, monkeypatch, heartbeat_clock, seconds
):
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=30, seconds=seconds))
    same_candidate_as_committed(world)
    old_data = (world.work / TARGET).read_bytes()

    assert publish.main(world.argv()) == 0

    assert world.remote_head() != before
    assert git(world.remote, "show", "main:" + HEARTBEAT) == "2026-11-30"
    assert (world.work / HEARTBEAT).read_bytes() == b"2026-11-30\n"
    assert git(world.remote, "show", "--name-only", "--format=", "main").split() == [HEARTBEAT]
    assert (world.work / TARGET).read_bytes() == old_data
    first = world.remote_head()
    assert publish.main(world.argv()) == 0
    assert world.remote_head() == first


@pytest.mark.parametrize("age", [timedelta(days=1), timedelta(days=30), timedelta(days=30, seconds=-1)])
def test_recent_and_exactly_thirty_day_bot_commits_are_controls(
    publish, world, monkeypatch, heartbeat_clock, age
):
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - age)
    same_candidate_as_committed(world)

    assert publish.main(world.argv()) == 0

    assert world.remote_head() == before
    assert not (world.work / HEARTBEAT).exists()


@pytest.mark.parametrize("changed", [False, True])
def test_a_recent_human_commit_cannot_hide_an_old_bot_commit(
    publish, world, monkeypatch, heartbeat_clock, changed
):
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(hours=1), subject="docs: update notes")
    if not changed:
        same_candidate_as_committed(world)

    assert publish.main(world.argv()) == 0

    assert world.remote_head() != before
    assert git(world.remote, "show", "main:" + HEARTBEAT) == "2026-11-30"
    paths = git(world.remote, "show", "--name-only", "--format=", "main").split()
    assert set(paths) == ({TARGET, HEARTBEAT} if changed else {HEARTBEAT})
    fields = git(world.remote, "log", "-1", "--format=%an|%ae|%cn|%ce|%s", "main").split("|")
    expected_date = "2026-07-15" if changed else "2026-07-14"
    assert fields == [*OWNER, *OWNER, f"data: daily update {expected_date}"]


def test_timestamp_only_data_is_preserved_when_only_the_heartbeat_is_due(
    publish, world, monkeypatch, heartbeat_clock
):
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    old_data = (world.work / TARGET).read_bytes()
    world.write_candidate(payload("2026-07-14", "2026-11-30T15:00:00+00:00", "OLD"))

    assert publish.main(world.argv()) == 0

    assert git(world.remote, "show", "--name-only", "--format=", "main").split() == [HEARTBEAT]
    assert (world.work / TARGET).read_bytes() == old_data


@pytest.mark.parametrize(
    "owner, subject",
    [(OWNER, "docs: revise the plan"), (("Other", "other@example.com"), "data: daily update 2026-11-29"),
     (OWNER, "data: daily update invalid"), (OWNER, "data: daily update 2026-02-30")],
)
def test_only_the_bot_identity_and_exact_valid_daily_subject_reset_its_clock(
    publish, world, monkeypatch, heartbeat_clock, owner, subject
):
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(hours=1), subject=subject, owner=owner)
    same_candidate_as_committed(world)

    assert publish.main(world.argv()) == 0

    assert git(world.remote, "show", "main:" + HEARTBEAT) == "2026-11-30"


@pytest.mark.parametrize("old_heartbeat", [None, b"2026-10-30\n"])
@pytest.mark.parametrize("step", ["add", "commit"])
def test_failed_heartbeat_commit_restores_both_files_and_the_index(
    publish, world, monkeypatch, heartbeat_clock, old_heartbeat, step, capsys
):
    if old_heartbeat is not None:
        target = world.work / HEARTBEAT
        target.parent.mkdir(parents=True)
        target.write_bytes(old_heartbeat)
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    old_data = (world.work / TARGET).read_bytes()
    seen = fail_at(publish, monkeypatch, step, OSError("synthetic heartbeat failure"))

    assert publish.main(world.argv()) == 1

    assert seen["raised"] == 1
    assert world.remote_head() == before
    assert (world.work / TARGET).read_bytes() == old_data
    heartbeat = world.work / HEARTBEAT
    assert (heartbeat.read_bytes() if heartbeat.exists() else None) == old_heartbeat
    assert git(world.work, "status", "--porcelain") == ""
    assert "publish: failed git_failed" in capsys.readouterr().out


def test_heartbeat_write_failure_is_rolled_back_too(publish, world, monkeypatch, heartbeat_clock):
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    old_data = (world.work / TARGET).read_bytes()
    real_write = Path.write_bytes
    failed = []

    def write_then_fail(path, data):
        result = real_write(path, data)
        if path.as_posix().endswith(HEARTBEAT) and not failed:
            failed.append(True)
            raise OSError("disk full")
        return result

    monkeypatch.setattr(Path, "write_bytes", write_then_fail)

    assert publish.main(world.argv()) == 1

    assert failed == [True]
    assert (world.work / TARGET).read_bytes() == old_data
    assert not (world.work / HEARTBEAT).exists()
    assert git(world.work, "status", "--porcelain") == ""
    assert world.remote_head() == before


def test_heartbeat_dry_run_uses_only_the_temporary_clone(
    publish, world, monkeypatch, heartbeat_clock, capsys, tmp_path
):
    before = dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    same_candidate_as_committed(world)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(scratch))

    assert publish.main(world.argv("--dry-run")) == 0

    shown = capsys.readouterr().out
    assert "publish: file " + HEARTBEAT in shown
    assert "publish: allowlist ok" in shown and "nothing pushed" in shown
    assert not (world.work / HEARTBEAT).exists()
    assert world.remote_head() == before == git(world.work, "rev-parse", "HEAD")
    assert git(world.work, "status", "--porcelain") == ""
    assert list(scratch.iterdir()) == []


@pytest.mark.parametrize("dry_run", [False, True])
def test_shallow_history_finds_the_bot_behind_a_human_commit(
    publish, world, monkeypatch, heartbeat_clock, tmp_path, dry_run, capsys
):
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(days=31))
    dated_commit(world, monkeypatch, HEARTBEAT_NOW - timedelta(hours=1), subject="docs: update notes")
    shallow = tmp_path / "shallow"
    subprocess.run(["git", "clone", "-q", "--depth=1", world.remote.as_uri(), str(shallow)], check=True)
    World.configure(shallow)
    world.work = shallow
    same_candidate_as_committed(world)
    assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"

    before = world.remote_head()
    assert publish.main(world.argv(*(["--dry-run"] if dry_run else []))) == 0

    if dry_run:
        assert "publish: file " + HEARTBEAT in capsys.readouterr().out
        assert git(shallow, "rev-parse", "--is-shallow-repository") == "true"
        assert world.remote_head() == before
        assert not (shallow / HEARTBEAT).exists()
    else:
        assert git(world.remote, "show", "main:" + HEARTBEAT) == "2026-11-30"


def test_missing_bot_in_complete_history_is_a_control(publish, world, heartbeat_clock):
    same_candidate_as_committed(world)

    assert publish.main(world.argv()) == 0

    assert world.remote_head() == world.seed
    assert not (world.work / HEARTBEAT).exists()
