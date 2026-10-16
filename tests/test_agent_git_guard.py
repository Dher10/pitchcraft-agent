"""Tests for .claude/hooks/git_guard.py, the PreToolUse hook that enforces the git rules of D35.

`decide(command, git)` takes the command line and a fake `git(*args)`; nothing here touches the real
repository. A few tests run the script itself with the hook input on stdin, to check the exit codes Claude
Code reads (0: let it through, 2: block).
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "git_guard.py"
spec = importlib.util.spec_from_file_location("git_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

OWNER = {"user.name": "Daniel Herdenez", "user.email": "edherdenez@gmail.com"}


class FakeGit:
    """The answers of the repository: current branch, config, tags and whether HEAD is on a remote."""

    def __init__(self, branch="v2", config=None, tags=("v1.0.0-kaggle",), pushed=False):
        self.branch, self.config, self.tags, self.pushed = branch, dict(OWNER if config is None else config), tags, pushed

    def __call__(self, *args: str) -> str:
        if args[:2] == ("branch", "--show-current"):
            return self.branch
        if args[:1] == ("config",):
            if args[1] not in self.config:
                raise subprocess.CalledProcessError(1, "git config")
            return self.config[args[1]]
        if args[:2] == ("tag", "--list"):
            return "\n".join(self.tags)
        if args[:2] == ("branch", "-r"):
            return "origin/v2" if self.pushed else ""
        raise AssertionError(f"unexpected git call {args}")


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(name, raising=False)


def verdict(command, **kwargs):
    return guard.decide(command, FakeGit(**kwargs))


ALLOWED = [
    # what the implementing session does every day
    "git status --short",
    "git diff --stat",
    "git diff main...HEAD",
    "git log --oneline -5",
    "git log main..v2",
    "git show v1.0.0-kaggle --stat",
    "git add -A",
    "git add -A && git commit -q -m 'feat: add a thing'",
    "git commit -m 'fix: keep main page text and a tag v1.0.0-kaggle out of the way'",
    "git push origin v2",
    "git push -u origin v2",
    "git push origin HEAD:v2",
    "git push origin refs/heads/v2",
    "git push origin experiment/pitch-mix",
    "git push",  # the current branch is v2
    "git branch --show-current",
    "git branch -r --contains HEAD",
    "git tag --list",
    "git tag -l 'v1*'",
    "git remote -v",
    "git config user.name",
    "git config user.email edherdenez@gmail.com",
    "git config user.name 'Daniel Herdenez'",
    "git stash push -q -- components/StarterCard.tsx",
    "git stash pop -q",
    "git fetch",
    "git pull --ff-only",
    "git checkout -b experiment/spike",
    "git switch experiment/spike",
    "git rev-parse HEAD",
    "git -C . log -1",
    "git commit -q -F - <<'EOF'\nfeat: say it in the body\n\nA line about main, git push --force and rebase that is only text.\nEOF",
    # redirections are not arguments (the first of these blocked the session's own push)
    "git push origin v2 2>&1 | tail -1",
    "git push origin v2 > out.txt",
    "git push origin v2 >out.txt 2>&1",
    "git push origin v2 &>/dev/null",
    "git log --oneline -3 2>/dev/null",
    "git commit -q -m 'feat: x' 2>&1 | tail -2",
    "git status --short 1>/dev/null",
    "cat file.txt | grep main",
    "python -m pytest -q",
    "npm test",
    "gh run list --branch v2 --limit 1",
]

BLOCKED = [
    # push
    ("git push origin main", "release branch"),
    ("git push origin v2:main", "release branch"),
    ("git push origin main 2>&1 | tail -1", "release branch"),
    ("git push --force origin v2 2>&1", "force"),
    ("git push origin feature/x > out.txt", "only to v2 or experiment"),
    ("git push origin HEAD:main", "release branch"),
    ("git push origin feature/x", "only to v2 or experiment"),
    ("git push origin refs/heads/main", "release branch"),
    ("git push origin v1.0.0-kaggle", "only to v2 or experiment"),
    ("git push origin tag v1.0.0-kaggle", "tag"),
    ("git push origin refs/tags/v9", "tag"),
    ("git push --tags", "can move or delete"),
    ("git push --all", "can move or delete"),
    ("git push --mirror", "can move or delete"),
    ("git push origin --delete v2", "can move or delete"),
    ("git push origin :v2", "deletes"),
    ("git push origin +v2", "force"),
    # force and friends
    ("git push --force origin v2", "force"),
    ("git push -f origin v2", "force"),
    ("git push --force-with-lease origin v2", "force"),
    ("git push --force-with-lease=v2:abc origin v2", "force"),
    ("git checkout -f main", "force"),
    ("git checkout --force v2", "force"),
    ("git branch --force v2 HEAD~3", "force"),
    ("git clean --force -d", "force"),
    ("git worktree add --force ../w v2", "force"),
    ("git branch -f v2 HEAD~3", "force"),
    ("git rebase v2", "rebase"),
    ("git rebase -i HEAD~3", "rebase"),
    ("git pull --rebase", "rebase"),
    ("git reset --hard HEAD~1", "reset --hard"),
    ("git reset --hard", "reset --hard"),
    ("git commit -m 'feat: x' --no-verify", "--no-verify"),
    ("git commit -n -m 'feat: x'", "--no-verify"),
    ("git commit -nm 'feat: x'", "--no-verify"),
    ("git push --no-verify origin v2", "--no-verify"),
    ("git -c core.hooksPath=/dev/null commit -m 'feat: x'", "hooksPath"),
    ("git config core.hooksPath /tmp/none", "hooksPath"),
    # main and tags
    ("git checkout main", "release branch"),
    ("git switch main", "release branch"),
    ("git merge main", "release branch"),
    ("git merge origin/main", "release branch"),
    ("git branch -D main", "release branch"),
    ("git branch -m v2 main", "release branch"),
    ("git fetch origin main", "release branch"),
    ("git pull origin main", "release branch"),
    ("git cherry-pick main", "release branch"),
    ("git update-ref refs/heads/main HEAD", "release branch"),
    ("git checkout v1.0.0-kaggle", "tag"),
    ("git tag v9.9.9", "tags are frozen"),
    ("git tag -d v1.0.0-kaggle", "tags are frozen"),
    ("git tag -f v1.0.0-kaggle HEAD", "force"),
    ("git tag -a v2.0 -m 'release'", "tags are frozen"),
    ("git update-ref refs/tags/v1.0.0-kaggle HEAD", "tag"),
]


@pytest.mark.parametrize("command", ALLOWED)
def test_the_commands_of_a_normal_day_pass(command):
    assert verdict(command) is None, command


@pytest.mark.parametrize("command,why", BLOCKED)
def test_the_dangerous_commands_are_blocked_with_a_reason(command, why):
    reason = verdict(command)

    assert reason is not None and why in reason, (command, reason)


def test_a_command_chain_is_blocked_if_any_part_of_it_is():
    assert verdict("git add -A && git commit -q -m 'feat: x' && git push --force origin v2") is not None
    assert verdict("npm test; git push origin main") is not None
    assert verdict("git push origin v2 | cat") is None


def test_a_here_string_does_not_hide_the_commands_after_it():
    assert verdict("cat <<<hello\ngit push --force origin v2") is not None


# --- the current branch ---------------------------------------------------------------------------------------


def test_a_bare_push_follows_the_current_branch():
    assert verdict("git push", branch="v2") is None
    assert verdict("git push", branch="experiment/spike") is None
    assert "only to v2 or experiment" in verdict("git push", branch="feature/x")
    assert verdict("git push", branch="main") is not None


def test_nothing_is_committed_or_merged_on_main():
    assert "current branch" in verdict("git commit -m 'feat: x'", branch="main")
    assert "current branch" in verdict("git merge v2", branch="main")
    assert verdict("git commit -m 'feat: x'", branch="v2") is None


# --- amend ----------------------------------------------------------------------------------------------------


def test_amend_is_allowed_only_on_a_commit_nobody_has_pushed():
    assert verdict("git commit --amend -m 'feat: x'", pushed=False) is None
    assert "already on a remote" in verdict("git commit --amend -m 'feat: x'", pushed=True)
    assert "already on a remote" in verdict("git commit --amend --no-edit", pushed=True)


def test_amend_fails_closed_when_git_cannot_say():
    def broken(*args):
        raise subprocess.CalledProcessError(128, "git")

    assert guard.decide("git commit --amend -m 'feat: x'", broken) is not None


# --- identity -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command,config",
    [
        ("git commit -m 'feat: x'", {"user.name": "Someone Else", "user.email": "edherdenez@gmail.com"}),
        ("git commit -m 'feat: x'", {"user.name": "Daniel Herdenez", "user.email": "other@example.com"}),
        ("git commit -m 'feat: x'", {}),
        ("git -c user.email=other@example.com commit -m 'feat: x'", OWNER),
        ("GIT_AUTHOR_EMAIL=other@example.com git commit -m 'feat: x'", OWNER),
        ("GIT_COMMITTER_NAME='Someone Else' git commit -m 'feat: x'", OWNER),
        ("git commit --author='Someone Else <other@example.com>' -m 'feat: x'", OWNER),
        ("git commit --author 'Daniel Herdenez <other@example.com>' -m 'feat: x'", OWNER),
        ("git merge --no-ff v2", {"user.name": "Someone Else", "user.email": "edherdenez@gmail.com"}),
        ("git cherry-pick abc123", {"user.name": "Daniel Herdenez", "user.email": "other@example.com"}),
    ],
)
def test_a_commit_that_is_not_the_owners_is_blocked(command, config):
    reason = verdict(command, config=config)

    assert reason is not None and "commits are made as Daniel Herdenez" in reason, (command, reason)


def test_the_owners_identity_passes_however_it_is_given():
    assert verdict("git -c user.name='Daniel Herdenez' -c user.email=edherdenez@gmail.com commit -m 'feat: x'") is None
    assert verdict("GIT_AUTHOR_NAME='Daniel Herdenez' GIT_AUTHOR_EMAIL=edherdenez@gmail.com git commit -m 'feat: x'") is None
    assert verdict("git commit --author='Daniel Herdenez <edherdenez@gmail.com>' -m 'feat: x'") is None


def test_the_identity_of_the_repository_is_not_changed():
    assert "not changed" in verdict("git config user.email other@example.com")
    assert "not changed" in verdict("git config --global user.name 'Someone Else'")


def test_the_process_environment_counts_too(monkeypatch):
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "other@example.com")

    assert verdict("git commit -m 'feat: x'") is not None


# --- the script, as Claude Code runs it ------------------------------------------------------------------------


def run_script(command, tmp_path):
    event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run([sys.executable, str(HOOK)], input=event, capture_output=True, text=True, cwd=tmp_path, env=env)


def test_the_script_exits_2_and_says_why_when_it_blocks(tmp_path):
    result = run_script("git push --force origin v2", tmp_path)

    assert result.returncode == 2
    assert "Blocked by .claude/hooks/git_guard.py" in result.stderr and "force" in result.stderr


def test_the_script_exits_0_for_a_command_that_is_not_git(tmp_path):
    assert run_script("python -m pytest -q", tmp_path).returncode == 0


def test_the_script_lets_through_what_it_cannot_read(tmp_path):
    for stdin in ("", "not json", json.dumps({"tool_input": {}}), json.dumps({"tool_input": {"command": 5}})):
        result = subprocess.run([sys.executable, str(HOOK)], input=stdin, capture_output=True, text=True, cwd=tmp_path)
        assert result.returncode == 0, stdin


def test_the_hook_is_wired_in_the_settings():
    settings = json.loads((HOOK.parents[1] / "settings.json").read_text(encoding="utf-8"))
    entries = settings["hooks"]["PreToolUse"]

    assert any(
        entry["matcher"] == "Bash" and any(h["type"] == "command" and "git_guard.py" in h["command"] for h in entry["hooks"])
        for entry in entries
    )
    assert settings["attribution"] == {"commit": "", "pr": ""}  # what was there stays
