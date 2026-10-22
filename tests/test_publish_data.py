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
