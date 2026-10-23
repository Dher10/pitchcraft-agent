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


# --- QA6-02: wrapped git, other tools, the rest of the QA list (P0.17-c) ---------------------------------------------

# Every command of the QA run 6 list, as the report printed them, and the ones of the same class.
WRAPPED_AND_INDIRECT = [
    # the QA list
    'bash -c "git push --force origin main"',
    "sh -c 'git push origin main'",
    'eval "git push origin main"',
    'powershell -Command "git push origin main"',
    "cmd /c git push origin main",
    "x=git; $x push origin main",
    "python -c \"import subprocess; subprocess.run(['git','push','origin','main'])\"",
    # the same wrappers, other spellings
    'pwsh -Command "git push origin main"',
    'powershell -NoProfile -Command "& git push --force origin v2"',
    'powershell "git push origin main"',
    "bash -lc 'git reset --hard'",
    "zsh -c 'git push origin main'",
    "cmd /k git push origin main",
    "cmd.exe /c git push origin main",
    "node -e \"require('child_process').execSync('git push origin main')\"",
    "python3 -c \"import os; os.system('git push origin main')\"",
    'perl -e \'system("git push origin main")\'',
    'Invoke-Expression "git push origin main"',
    'iex "git push origin main"',
    "echo main | xargs git checkout",
    "Start-Process git -ArgumentList 'push origin main'",
    "1..3 | ForEach-Object { git push origin main }",
    "Invoke-Command -ScriptBlock { git push origin main }",
    # a program the guard cannot read at all
    "powershell -EncodedCommand ZwBpAHQAIABwAHUAcwBoAA==",
    "pwsh -enc ZwBpAHQAIABwAHUAcwBoAA==",
    # a program name built at run time
    "$x = 'git'; & $x push origin main",
    "g=git; $g push --force origin v2",
]

# git behind words that pass the command along, and inside substitutions: the guard reads them as plain git.
PASSED_ALONG = [
    "env git push origin main",
    "env GIT_AUTHOR_EMAIL=other@example.com git commit -m 'feat: x'",
    "command git push --force origin v2",
    "& git push origin main",
    "& 'C:\\Program Files\\Git\\cmd\\git.exe' push origin main",
    '"C:\\Program Files\\Git\\cmd\\git.exe" push --force origin v2',
    "$out = git push origin main",
    "$out = & git push --force origin v2",
    "x=$(git push origin main)",
    "echo $(git push --force origin v2)",
    "echo `git push origin main`",
    "(git push origin main)",
    "{ git push origin main }",
    "time git reset --hard",
]

NEW_GIT_RULES = [
    ("git filter-branch --all", "filter-branch"),
    ("git filter-branch --env-filter 'true' HEAD", "filter-branch"),
    ("git filter-repo --path docs", "filter-repo"),
    ("git branch -D v2", "v2"),
    ("git branch -d v2", "v2"),
    ("git branch --delete v2", "v2"),
    ("git branch -m v2 old", "v2"),
    ("git branch -d origin/v2", "v2"),
    ("git branch -D main", "release branch"),
    ("git remote add evil https://x.y/z.git", "git remote add"),
    ("git remote set-url origin https://x.y/z.git", "git remote set-url"),
    ("git remote remove origin", "git remote remove"),
    ("git remote rm origin", "git remote rm"),
    ("git remote rename origin up", "git remote rename"),
    ("git config --unset core.hooksPath", "hooksPath"),
    ("git config --global core.hooksPath /x", "hooksPath"),
    ("git config --replace-all core.hooksPath /x", "hooksPath"),
    ("git config --add core.hooksPath /x", "hooksPath"),
]

ALLOWED_AGAIN = [
    # the documented check (CONTRIBUTING.md), in every form that only reads
    "git config core.hooksPath",
    "git config --get core.hooksPath",
    "git config --local --get core.hooksPath",
    "git config --global --get core.hooksPath",
    "git config --get-all core.hooksPath",
    "git config --show-origin --get core.hooksPath",
    # remotes and branches that are not v2 or main
    "git remote",
    "git remote -v",
    "git remote show origin",
    "git remote get-url origin",
    "git branch -d experiment/spike",
    "git branch -D experiment/spike",
    "git branch -m experiment/a experiment/b",
    "git branch --list",
    # wrappers that do not mention git are ordinary commands
    'bash -c "echo hello"',
    "sh -c 'ls -la'",
    'powershell -Command "Get-Date"',
    'pwsh -NoProfile -Command "Write-Output 1"',
    "cmd /c dir",
    'python -c "print(1)"',
    'python -c "import json; print(json.dumps({\'a\': 1}))"',
    'node -e "console.log(1)"',
    'eval "echo hi"',
    'Invoke-Expression "Get-Date"',
    "1..3 | ForEach-Object { $_ * 2 }",
    # a script, a module or a file that has git in its name is not a string the shell reads
    "python -m pytest tests/test_agent_git_guard.py -q",
    "python .claude/hooks/git_guard.py",
    "bash scripts/run.sh",
    "powershell -File build.ps1",
    "node scripts/git-info.js",
    # PowerShell and shell habits around plain git
    "$out = git status --short",
    "$out = Get-Date",
    "$branch = git branch --show-current",
    "x=$(git rev-parse HEAD)",
    "echo $(git log -1 --oneline)",
    "(git status)",
    "{ git status }",
    "& git status",
    "env GIT_AUTHOR_NAME='Daniel Herdenez' git status",
    "git commit -q -m @'\nfeat: say it in the body\n\nA line about git push --force origin main and rebase that is only text.\n'@",
    "git commit -q -m \"fix: cover $(git log -1 --format=%h)\"",
]


@pytest.mark.parametrize("command", WRAPPED_AND_INDIRECT)
def test_git_behind_a_wrapper_or_a_runtime_name_is_blocked(command):
    reason = verdict(command)

    assert reason is not None and ("cannot be read by the guard" in reason or "hides the command" in reason), (command, reason)


@pytest.mark.parametrize("command", PASSED_ALONG)
def test_git_behind_words_that_pass_it_along_is_read_as_plain_git(command):
    assert verdict(command) is not None, command


@pytest.mark.parametrize("command,why", NEW_GIT_RULES)
def test_the_new_git_rules_block_with_a_reason(command, why):
    reason = verdict(command)

    assert reason is not None and why in reason, (command, reason)


@pytest.mark.parametrize("command", ALLOWED_AGAIN)
def test_ordinary_commands_and_the_documented_reads_still_pass(command):
    assert verdict(command) is None, command


def test_a_program_name_with_a_directory_and_extension_is_still_the_program():
    assert guard.program_name("C:\\Program Files\\Git\\cmd\\git.exe") == "git"
    assert guard.program_name("/usr/bin/git") == "git"
    assert guard.program_name("PowerShell.exe") == "powershell"
    assert guard.program_name("gitk") == "gitk"


def test_a_substitution_does_not_hide_a_second_command_after_it():
    assert verdict("echo $(date) && git push --force origin v2") is not None
    assert verdict("echo $(date) && git push origin v2") is None


def test_the_hook_is_wired_for_both_shell_tools_with_the_same_script():
    settings = json.loads((HOOK.parents[1] / "settings.json").read_text(encoding="utf-8"))
    commands = {
        entry["matcher"]: [h["command"] for h in entry["hooks"] if h["type"] == "command"]
        for entry in settings["hooks"]["PreToolUse"]
    }

    assert set(commands) == {"Bash", "PowerShell"}
    assert commands["Bash"] == commands["PowerShell"] and "git_guard.py" in commands["Bash"][0]


@pytest.mark.parametrize("tool", ["Bash", "PowerShell"])
def test_the_script_blocks_the_same_way_for_the_powershell_tool(tmp_path, tool):
    event = json.dumps({"tool_name": tool, "tool_input": {"command": 'powershell -Command "git push origin main"'}})
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    result = subprocess.run([sys.executable, str(HOOK)], input=event, capture_output=True, text=True, cwd=tmp_path, env=env)

    assert result.returncode == 2 and "Blocked by .claude/hooks/git_guard.py" in result.stderr


# --- reviewer round 1 of P0.17-c: renaming main, abbreviated and combined options, more wrappers ------------------

SWEPT_BLOCKED = [
    ("git branch -m main", "release branch"),
    ("git branch -m main old", "release branch"),
    ("git branch -M main old", "release branch"),
    ("git branch -m v2 main", "release branch"),
    ("git push -fu origin v2", "force"),
    ("git push -uf origin v2", "force"),
    ("git push -vf origin v2", "force"),
    ("git push --forc origin v2", "force"),
    ("git push --force-w origin v2", "force"),
    ("git push -ud origin v2", "can move or delete"),
    ("git push --mirro", "can move or delete"),
    ("git push --del origin v2", "can move or delete"),
    ("git commit --no-ver -m 'feat: x'", "--no-verify"),
    ("git reset --har HEAD~1", "reset --hard"),
    ("git clean -fd", "force"),
    ("git checkout -fb x", "force"),
    ("GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m 'feat: x'", "hooksPath"),
    ("wsl git push origin main", "cannot be read by the guard"),
    ("ssh host git push origin main", "cannot be read by the guard"),
    ("find . -name x -exec git push origin main ;", "cannot be read by the guard"),
]


@pytest.mark.parametrize("command,why", SWEPT_BLOCKED)
def test_combined_and_abbreviated_options_and_the_rest_of_the_sweep_are_blocked(command, why):
    reason = verdict(command)

    assert reason is not None and why in reason, (command, reason)


def test_an_abbreviated_amend_is_blocked_on_a_pushed_commit_and_allowed_on_a_local_one():
    assert "already on a remote" in verdict("git commit --amen -m 'feat: x'", pushed=True)
    assert verdict("git commit --amen -m 'feat: x'", pushed=False) is None


@pytest.mark.parametrize(
    "command",
    [
        "git push -u origin v2",
        "git push -q origin v2",
        "git push -vu origin v2",
        "git push --set-upstream origin v2",
        "git push --dry-run origin v2",
        "git log --all --oneline",
        "git log --alternate-refs",
        "git add --all",
        "git commit --allow-empty -m 'chore: x'",
        "git commit --amend --no-edit",
        "git diff --stat --format=%h",
        "git log --format=%h -3",
        "git status --short --branch",
        "git branch -vv",
        "git branch --format=%(refname:short)",
        "git branch -m experiment/a experiment/b",
        "git clean -n",
        "git checkout -b experiment/spike",
        "GIT_CONFIG_NOSYSTEM=1 git status",
        "find . -name '*.py' -exec python -m pytest {} ;",
        "ssh host ls",
    ],
)
def test_control_options_that_look_like_the_dangerous_ones_still_pass(command):
    assert verdict(command, pushed=False) is None, command


# --- reviewer round 2 of P0.17-c: -m/-c/-C name a branch outside the committing subcommands; pull's rebase spellings --

@pytest.mark.parametrize(
    "command,why",
    [
        ("git switch -c main", "release branch"),
        ("git switch -C main", "release branch"),
        ("git switch -m main", "release branch"),
        ("git checkout -m main", "release branch"),
        ("git checkout -C main", "release branch"),
        ("git checkout -c main", "release branch"),
        ("git reset -m main", "release branch"),
        ("git switch -c v1.0.0-kaggle", "tag"),
        ("git pull -r", "rebase"),
        ("git pull -rv", "rebase"),
        ("git pull --rebase=true", "rebase"),
        ("git pull --rebase=merges", "rebase"),
        ("git pull --reb=true", "rebase"),
    ],
)
def test_a_branch_named_after_a_value_option_and_the_other_pull_rebase_spellings_are_blocked(command, why):
    reason = verdict(command)

    assert reason is not None and why in reason, (command, reason)


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m main",
        "git commit -m 'fix: main page'",
        "git commit -F main.txt",
        "git commit -C HEAD~1 --no-edit",
        "git merge -m main v2",
        "git stash push -m main",
        "git switch -c experiment/spike",
        "git checkout -b experiment/spike",
        "git pull --rebase=false",
        "git pull --no-rebase",
        "git pull --ff-only",
        "git pull -q",
    ],
)
def test_control_messages_and_experiment_branches_still_pass(command):
    assert verdict(command, pushed=False) is None, command


# --- P1.0-b: gh and the GitHub REST API (docs/plans/P1.md, 3.2, layer 1) -----------------------------------------------
# Reads stay allowed because the D35 loop needs them (CI runs, a pull request, the rulesets through a GET); every write is
# blocked, and a gh family or verb that is not on the list of reads is blocked until it is added with a test.

GH_READS = [
    "gh run list --branch v2 --limit 3",
    "gh run list --json databaseId,headSha,status,conclusion --jq '.[] | .status'",
    "gh run view 39712693892 --log-failed",
    "gh run watch 39712693892",
    "gh run download 39712693892 -n candidate",
    "gh pr view 5 --json state",
    "gh pr list --state open",
    "gh pr diff 5",
    "gh pr checks 5",
    "gh pr status",
    "gh repo view",
    "gh repo view Dher10/pitchcraft-agent --json name",
    "gh repo list",
    "gh workflow list",
    "gh workflow view tests.yml",
    "gh issue list",
    "gh issue view 3",
    "gh search issues foo",
    "gh status",
    "gh auth status",
    "gh cache list",
    "gh --version",
    "gh",
    "gh -R Dher10/pitchcraft-agent run list",
    "gh --repo Dher10/pitchcraft-agent run list",
    "gh run -R Dher10/pitchcraft-agent list",
    "gh run list -R Dher10/pitchcraft-agent",
    "gh pr -R Dher10/pitchcraft-agent view 5",
    "gh api repos/Dher10/pitchcraft-agent -i",
    "gh api repos/Dher10/pitchcraft-agent -i --jq .name",
    "gh api repos/Dher10/pitchcraft-agent -iq .name",
    "curl -m 10 https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl -fsSL https://api.github.com/repos/Dher10/pitchcraft-agent",
    "gh api repos/Dher10/pitchcraft-agent/rulesets",
    "gh api repos/Dher10/pitchcraft-agent/rulesets/25520388 --jq '{enforcement, bypass_actors}'",
    "gh api repos/Dher10/pitchcraft-agent/rulesets 2>&1 | head -5",
    "gh api -X GET search/issues -f q=repo:Dher10/pitchcraft-agent",
    "gh api --method GET repos/Dher10/pitchcraft-agent",
    "gh api --method=GET repos/Dher10/pitchcraft-agent",
    "gh api -XGET repos/Dher10/pitchcraft-agent",
    "gh api -X get repos/Dher10/pitchcraft-agent",
    "gh api repos/actions/checkout/git/ref/tags/v7.0.1 --jq '.object.sha'",
    "gh api --paginate repos/Dher10/pitchcraft-agent/actions/runs",
    "GH_TOKEN=abc gh run list",
    "& gh run list",
    "& 'C:\\Program Files\\GitHub CLI\\gh.exe' run list",
    "gh run list | Select-Object -First 3",
    "$runs = gh run list --limit 2",
    "git push origin v2 && gh run list --branch v2 --limit 1",
    "for r in a b; do gh api repos/actions/$r/releases/latest --jq '.tag_name'; done",
    # other programs are untouched, and so is a request that is not to the GitHub API
    "curl -s https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl -sS -X GET https://api.github.com/repos/Dher10/pitchcraft-agent/rulesets",
    "curl -sS --request GET https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl -I https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl -X POST https://example.com/hook -d 'a=b'",
    "curl -H 'Authorization: Bearer x' https://example.com/private",
    "wget -q https://api.github.com/repos/Dher10/pitchcraft-agent",
    "wget --post-data=a=b https://example.com/form",
    "Invoke-RestMethod https://api.github.com/repos/Dher10/pitchcraft-agent",
    "Invoke-RestMethod -Uri https://api.github.com/repos/Dher10/pitchcraft-agent -Method Get",
    "Invoke-RestMethod -Method Post -Uri https://example.com/hook -Body 'x'",
    "irm https://api.github.com/repos/Dher10/pitchcraft-agent/rulesets -UseBasicParsing",
    "Invoke-WebRequest https://api.github.com/repos/Dher10/pitchcraft-agent -Method GET",
    'bash -c "echo hello"',
    "python -m pytest tests/test_workflows.py -q",
]

GH_WRITES = [
    # gh api: any method but GET, any field or body that turns the call into a POST, graphql
    ("gh api -X DELETE repos/Dher10/pitchcraft-agent/rulesets/25520388", "DELETE"),
    ("gh api -X PUT repos/Dher10/pitchcraft-agent/topics", "PUT"),
    ("gh api -X PATCH repos/Dher10/pitchcraft-agent -f name=x", "PATCH"),
    ("gh api --method DELETE repos/Dher10/pitchcraft-agent/rulesets/1", "DELETE"),
    ("gh api --method=PUT repos/Dher10/pitchcraft-agent/topics", "PUT"),
    ("gh api -XPOST repos/Dher10/pitchcraft-agent/dispatches", "POST"),
    ("gh api -X=DELETE repos/Dher10/pitchcraft-agent/rulesets/1", "DELETE"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets -f name=x", "POST"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets -F enabled=true", "POST"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets --field name=x", "POST"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets --raw-field name=x", "POST"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets -fname=x", "POST"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets --input body.json", "--input"),
    ("gh api repos/Dher10/pitchcraft-agent/rulesets --input=body.json", "--input"),
    ("gh api -X GET repos/Dher10/pitchcraft-agent/rulesets --input body.json", "--input"),
    ("gh api graphql -f query='{ viewer { login } }'", "graphql"),
    ("gh api /graphql -f query='mutation { x }'", "graphql"),
    # the families and verbs that write
    ("gh repo delete Dher10/pitchcraft-agent --yes", "gh repo delete"),
    ("gh repo edit --visibility private", "gh repo edit"),
    ("gh repo rename x", "gh repo rename"),
    ("gh repo archive Dher10/pitchcraft-agent", "gh repo archive"),
    ("gh repo create x", "gh repo create"),
    ("gh repo fork", "gh repo fork"),
    ("gh repo deploy-key add key.pub", "gh repo deploy-key"),
    ("gh repo deploy-key delete 1", "gh repo deploy-key"),
    ("gh secret set DATA_DEPLOY_KEY", "gh secret"),
    ("gh secret list", "gh secret"),
    ("gh variable set X --body y", "gh variable"),
    ("gh ruleset list", "gh ruleset"),
    ("gh ruleset view 25520388", "gh ruleset"),
    ("gh workflow run daily.yml", "gh workflow run"),
    ("gh workflow enable daily.yml", "gh workflow enable"),
    ("gh workflow disable daily.yml", "gh workflow disable"),
    ("gh run rerun 1", "gh run rerun"),
    ("gh run cancel 1", "gh run cancel"),
    ("gh run delete 1", "gh run delete"),
    ("gh pr merge 5 --merge", "gh pr merge"),
    ("gh pr close 5", "gh pr close"),
    ("gh pr reopen 5", "gh pr reopen"),
    ("gh pr edit 5 --title x", "gh pr edit"),
    ("gh pr create --base main --head v2", "gh pr create"),
    ("gh pr comment 5 --body x", "gh pr comment"),
    ("gh pr checkout 5", "gh pr checkout"),
    ("gh pr -R Dher10/pitchcraft-agent merge 5", "gh pr merge"),
    ("gh pr -R view merge 5", "gh pr merge"),  # -R takes `view` as its value: the verb is merge
    ("gh pr --repo view merge 5", "gh pr merge"),
    ("gh run -R view rerun 1", "gh run rerun"),
    ("gh issue close 3", "gh issue close"),
    ("gh release create v9", "gh release is not on the list"),
    ("gh release delete v1.0.0-kaggle", "gh release is not on the list"),
    ("gh label create x", "gh label is not on the list"),
    ("gh auth token", "gh auth token"),
    ("gh auth refresh", "gh auth refresh"),
    ("gh auth logout", "gh auth logout"),
    ("gh auth setup-git", "gh auth setup-git"),
    ("gh extension install x/y", "gh extension is not on the list"),
    ("gh alias set x 'api -X DELETE'", "gh alias is not on the list"),
    ("gh cache delete 1", "gh cache delete"),
    ("gh gist create f", "gh gist is not on the list"),
    ("gh codespace delete", "gh codespace is not on the list"),
    ("gh config set editor vim", "gh config is not on the list"),
    ("gh project delete 1", "gh project is not on the list"),
    ("gh -R Dher10/pitchcraft-agent secret list", "gh secret"),
    ("gh auth status --show-token", "show-token"),
    ("gh auth status -t", "show-token"),
    ("gh auth status -ht github.com", "show-token"),
    ("gh api repos/Dher10/pitchcraft-agent -iX DELETE", "DELETE"),  # pflag reads `-iX DELETE` as `-i -X DELETE`
    ("gh api repos/Dher10/pitchcraft-agent -hX DELETE", "DELETE"),
    ("gh api repos/Dher10/pitchcraft-agent -iXDELETE", "DELETE"),
    ("gh api repos/Dher10/pitchcraft-agent -ifa=b", "POST"),
    ("GH_TOKEN=abc gh repo delete x", "gh repo delete"),
    ("& gh repo delete x", "gh repo delete"),
    ("& 'C:\\Program Files\\GitHub CLI\\gh.exe' pr merge 5", "gh pr merge"),
    ("gh run list && gh pr merge 5", "gh pr merge"),
    ("echo $(gh pr merge 5)", "gh pr merge"),
    # a request to the GitHub API that writes, carries a body or carries credentials
    ("curl -X DELETE https://api.github.com/repos/Dher10/pitchcraft-agent/rulesets/1", "non-GET"),
    ("curl -XPOST https://api.github.com/repos/Dher10/pitchcraft-agent/dispatches", "non-GET"),
    ("curl --request PATCH https://api.github.com/repos/Dher10/pitchcraft-agent", "non-GET"),
    ("curl --request=PUT https://api.github.com/repos/Dher10/pitchcraft-agent/topics", "non-GET"),
    ("curl -d '{}' https://api.github.com/repos/Dher10/pitchcraft-agent/dispatches", "body or credentials"),
    ("curl --data-binary @f https://api.github.com/repos/Dher10/pitchcraft-agent", "body or credentials"),
    ("curl --json '{}' https://api.github.com/repos/Dher10/pitchcraft-agent", "body or credentials"),
    ("curl -F file=@f https://api.github.com/repos/Dher10/pitchcraft-agent", "body or credentials"),
    ("curl -T f https://uploads.github.com/repos/Dher10/pitchcraft-agent/releases/1/assets", "body or credentials"),
    ("curl -u user:pw https://api.github.com/user", "body or credentials"),
    ("curl -H 'Authorization: Bearer abc' https://api.github.com/user", "credentials"),
    ("curl -H 'authorization: token abc' https://api.github.com/user", "credentials"),
    ("curl -H 'Accept: x' -H \"Authorization: $TOKEN\" https://api.github.com/user", "credentials"),
    ("wget --method=DELETE https://api.github.com/repos/Dher10/pitchcraft-agent", "non-GET"),
    ("wget --post-data=x https://api.github.com/repos/Dher10/pitchcraft-agent", "non-GET"),
    ("wget --header='Authorization: token abc' https://api.github.com/user", "credentials"),
    ("Invoke-RestMethod https://api.github.com/repos/Dher10/pitchcraft-agent/rulesets/1 -Method Delete", "non-GET"),
    ("Invoke-RestMethod -Uri https://api.github.com/repos/Dher10/pitchcraft-agent/dispatches -Method Post -Body '{}'", "non-GET"),
    ("Invoke-RestMethod -Uri https://api.github.com/repos/Dher10/pitchcraft-agent -Body '{}'", "non-GET"),
    ("Invoke-RestMethod -Uri https://api.github.com/repos/Dher10/pitchcraft-agent -Meth Put", "non-GET"),
    ("Invoke-RestMethod -Uri https://api.github.com/repos/Dher10/pitchcraft-agent -Headers @{Authorization='token abc'}", "credentials"),
    ("irm https://api.github.com/user -Headers @{ authorization = \"Bearer $t\" }", "credentials"),
    ("Invoke-WebRequest https://api.github.com/user -Credential $c", "non-GET"),
    ("Invoke-WebRequest https://api.github.com/repos/Dher10/pitchcraft-agent -InFile f.json -Method Put", "non-GET"),
    ("iwr https://api.github.com/user -Authentication Bearer -Token $t", "credentials"),
    ("curl https://api.github.com/user -H 'X-Token: ghp_abcdefghijklmnop'", "credentials"),
    ("Invoke-RestMethod https://api.github.com/repos/Dher10/pitchcraft-agent -CustomMethod DELETE", "non-GET"),  # PowerShell 7.4
    ("wget -Uri https://api.github.com/repos/Dher10/pitchcraft-agent -Method Delete", "non-GET"),  # an alias of Invoke-WebRequest in 5.1
    ("curl -Method Delete https://api.github.com/repos/Dher10/pitchcraft-agent", "non-GET"),
    ("curl -method delete https://api.github.com/repos/Dher10/pitchcraft-agent", "non-GET"),
]

GH_BEHIND_WRAPPERS = [
    'bash -c "gh api -X DELETE repos/Dher10/pitchcraft-agent/rulesets/1"',
    "sh -c 'gh pr merge 5'",
    'powershell -Command "gh repo delete Dher10/pitchcraft-agent"',
    'pwsh -NoProfile -Command "Invoke-RestMethod https://api.github.com/user -Method Delete"',
    'eval "gh pr merge 5"',
    "cmd /c gh pr merge 5",
    'python -c "import os; os.system(\'gh repo delete x\')"',
    "node -e \"require('child_process').execSync('gh pr merge 5')\"",
    'python -c "import requests; requests.delete(\'https://api.github.com/repos/x/y\')"',
    "xargs gh pr merge",
    "ssh host gh pr merge 5",
    "x=gh; $x pr merge 5",
]


@pytest.mark.parametrize("command", GH_READS)
def test_the_reads_of_gh_and_of_other_programs_pass(command):
    assert verdict(command) is None, command


@pytest.mark.parametrize("command,why", GH_WRITES)
def test_every_write_through_gh_or_to_the_github_api_is_blocked_with_a_reason(command, why):
    reason = verdict(command)

    assert reason is not None and why in reason and "(P1.0)" in reason, (command, reason)


@pytest.mark.parametrize("command", GH_BEHIND_WRAPPERS)
def test_gh_and_the_github_api_behind_a_wrapper_are_blocked_as_git_is(command):
    reason = verdict(command)

    assert reason is not None and "cannot be read by the guard" in reason, (command, reason)


@pytest.mark.parametrize(
    "command",
    [
        "git commit -q -m 'fix: gh pr merge and curl -X DELETE https://api.github.com are only text'",
        "git commit -q -F - <<'EOF'\nfeat: say it\n\ngh api -X DELETE x is only text here.\nEOF",
        "echo gh pr merge",
        "grep -n 'gh api' docs/plans/P1.md",
        "python -m pytest tests/test_agent_git_guard.py -q",
    ],
)
def test_text_that_names_gh_without_running_it_passes(command):
    assert verdict(command) is None, command


def test_the_hook_script_blocks_gh_for_both_shell_tools(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    for tool in ("Bash", "PowerShell"):
        event = json.dumps({"tool_name": tool, "tool_input": {"command": "gh api -X DELETE repos/Dher10/pitchcraft-agent/rulesets/1"}})

        result = subprocess.run([sys.executable, str(HOOK)], input=event, capture_output=True, text=True, cwd=tmp_path, env=env)

        assert result.returncode == 2 and "Blocked by .claude/hooks/git_guard.py" in result.stderr, tool


# --- QA1-02: every spelling of the option that prints the token (P1-R1fix) -----------------------------------------------
#
# `gh auth status --show-token=true` is a valid spelling of the same flag (pflag reads a boolean with `=value`; the CLI
# parses it with strconv.ParseBool), and `-t=true` is the short form. The guard normalizes the option before it judges:
# the name (case, `_` for `-`), the `=value` of any kind, a cluster of short flags. Any value is blocked, `false` included,
# because the guard cannot know what a future version does with a value it does not recognize.

SHOW_TOKEN_SPELLINGS = [
    "gh auth status --show-token",
    *(f"gh auth status --show-token={value}" for value in ("true", "True", "TRUE", "1", "t", "T", "false", "False", "FALSE", "0", "f", "F", "", "yes", "garbage")),
    "gh auth status --SHOW-TOKEN",
    "gh auth status --Show-Token=true",
    "gh auth status --show_token",
    "gh auth status --show_token=true",
    "gh auth status -t",
    "gh auth status -t=true",
    "gh auth status -t=false",
    "gh auth status -th github.com",
    "gh auth status -ht github.com",
    "gh auth status -at",
    "gh auth status --hostname github.com --show-token=true",
    "gh auth status --show-token=true --hostname github.com",
    "gh --show-token=true auth status",
    "gh auth --show-token=1 status",
    "gh -R Dher10/pitchcraft-agent auth status --show-token=True",
    "GH_TOKEN=abc gh auth status --show-token=true",
    "& gh auth status --show-token=true",
    "gh auth status --show-token=true | Select-Object -First 3",
    "$out = gh auth status --show-token=1",
]

SHOW_TOKEN_CONTROLS = [
    "gh auth status",
    "gh auth status --hostname github.com",
    "gh auth status -h github.com",
    "gh auth status --active",
    "gh auth status --hostname=github.com",
    "gh -R Dher10/pitchcraft-agent auth status",
    "gh run list --limit 3",
    "gh api repos/Dher10/pitchcraft-agent/rulesets --jq '.[].name'",
]


@pytest.mark.parametrize("command", SHOW_TOKEN_SPELLINGS)
def test_every_spelling_of_the_token_printing_option_is_blocked(command):
    reason = verdict(command)

    assert reason is not None and "show-token" in reason, (command, reason)


@pytest.mark.parametrize("command", SHOW_TOKEN_CONTROLS)
def test_control_the_status_of_gh_without_the_token_option_passes(command):
    assert verdict(command) is None, command


@pytest.mark.parametrize(
    "command",
    [
        "bash -c 'gh auth status --show-token=true'",
        'powershell -Command "gh auth status --show-token=1"',
        "env gh auth status --show-token=true",
    ],
)
def test_the_token_option_behind_a_wrapper_is_blocked_too(command):
    assert verdict(command) is not None, command


# --- QA1-04: credentials in the user information of a URL to the GitHub API ----------------------------------------------

USERINFO = [
    "curl https://user:pw@api.github.com/user",
    "curl https://token@api.github.com/user",
    "curl user:pw@api.github.com/user",
    "curl -s https://Dher10:ghp_abcdefghijklmnop@api.github.com/user",
    "curl -sS -X GET https://user:pw@api.github.com/repos/Dher10/pitchcraft-agent",
    "curl https://user:pw@uploads.github.com/repos/Dher10/pitchcraft-agent/releases/1/assets",
    "curl https://user%40mail:pw@api.github.com/user",
    "wget https://user:pw@api.github.com/user",
    "Invoke-RestMethod https://user:pw@api.github.com/user",
    "irm https://user:pw@api.github.com/user",
    "Invoke-WebRequest -Uri https://user:pw@api.github.com/user -Method Get",
    "iwr https://token@api.github.com/user",
    "http https://user:pw@api.github.com/user",
    "curl 'https://user:pw@api.github.com/user'",
    "curl https://user:pw@@api.github.com/user",  # an @ inside the user information
    "curl https://user:@@api.github.com/user",
    "curl https://user:p@ss@api.github.com/user",
]

USERINFO_CONTROLS = [
    "curl https://api.github.com/user",
    "curl -s https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl -sS https://api.github.com/repos/Dher10/pitchcraft-agent/rulesets?per_page=1",
    "curl https://api.github.com/search/issues?q=user@example.com",
    "wget -q https://api.github.com/repos/Dher10/pitchcraft-agent",
    "Invoke-RestMethod https://api.github.com/repos/Dher10/pitchcraft-agent",
    "curl https://user:pw@example.com/private",  # not the GitHub API: out of the guard's scope
    "git clone git@github.com:Dher10/pitchcraft-agent.git x",
]


@pytest.mark.parametrize("command", USERINFO)
def test_a_url_to_the_github_api_with_user_information_is_a_credential_and_is_blocked(command):
    reason = verdict(command)

    assert reason is not None and "credentials" in reason, (command, reason)


@pytest.mark.parametrize("command", USERINFO_CONTROLS)
def test_control_a_url_without_user_information_passes(command):
    assert verdict(command) is None, command
