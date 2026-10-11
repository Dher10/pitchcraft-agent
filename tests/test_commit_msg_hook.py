"""Tests for .githooks/commit-msg (decision D21).

Each test runs the real hook with `sh` against a message file inside a throwaway
git repo. Author and committer come from environment variables, so the owner's
git config is never touched. Set COMMIT_MSG_HOOK to run the tests against
another copy of the hook (used for mutation checks).
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = Path(os.environ.get("COMMIT_MSG_HOOK") or REPO_ROOT / ".githooks" / "commit-msg")
OWNER_NAME = "Daniel Herdenez"
OWNER_EMAIL = "edherdenez@gmail.com"

VALID_MESSAGE = (
    "fix: stop demo recent form leaking into live starters\n"
    "\n"
    "Live starters kept recent_form from the demo inputs.\n"
    "\n"
    "pytest 12/12.\n"
)


def _find_sh() -> str:
    found = shutil.which("sh")
    if found:
        return found
    for candidate in (
        r"C:\Program Files\Git\usr\bin\sh.exe",
        r"C:\Program Files\Git\bin\sh.exe",
        r"C:\Program Files (x86)\Git\usr\bin\sh.exe",
    ):
        if Path(candidate).exists():
            return candidate
    pytest.skip("sh not found (install Git for Windows or add sh to PATH)")


@pytest.fixture
def run_hook(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    sh = _find_sh()
    git = shutil.which("git")

    def _tool_path() -> str:
        """The hook uses sed, grep, head, wc, tr, mv and git. On Windows the `sh` found may
        come without them on PATH (QA saw `sed` missing), so Git's own directories go first."""

        sh_dir = Path(sh).parent
        dirs = [str(sh_dir)]
        for relative in ("../usr/bin", "../../usr/bin"):
            candidate = (sh_dir / relative).resolve()
            if candidate.is_dir() and str(candidate) not in dirs:
                dirs.append(str(candidate))
        if git and str(Path(git).parent) not in dirs:
            dirs.append(str(Path(git).parent))
        return os.pathsep.join([*dirs, os.environ.get("PATH", "")])

    def _run(
        message: str,
        author_email: str = OWNER_EMAIL,
        committer_email: str = OWNER_EMAIL,
        env_overrides: dict[str, str] | None = None,
    ):
        msg_file = repo / "COMMIT_EDITMSG"
        msg_file.write_text(message, encoding="utf-8", newline="\n")
        env = {
            **os.environ,
            "PATH": _tool_path(),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": OWNER_NAME,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": OWNER_NAME,
            "GIT_COMMITTER_EMAIL": committer_email,
            **(env_overrides or {}),
        }
        result = subprocess.run(
            [sh, str(HOOK), str(msg_file)],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        return result, msg_file.read_text(encoding="utf-8")

    return _run


def test_accepts_valid_message(run_hook):
    result, _ = run_hook(VALID_MESSAGE)
    assert result.returncode == 0, result.stderr


def test_rejects_subject_without_prefix(run_hook):
    result, _ = run_hook("add stuff to the pipeline\n\nBody explaining why.\n")
    assert result.returncode != 0
    assert "Subject must look like" in result.stderr


def test_rejects_message_without_body(run_hook):
    result, _ = run_hook("fix: stop demo recent form leaking\n")
    assert result.returncode != 0
    assert "body" in result.stderr


def test_rejects_other_author(run_hook):
    result, _ = run_hook(VALID_MESSAGE, author_email="someone@example.com")
    assert result.returncode != 0
    assert OWNER_EMAIL in result.stderr


def test_rejects_other_committer(run_hook):
    result, _ = run_hook(VALID_MESSAGE, committer_email="noreply@anthropic.com")
    assert result.returncode != 0
    assert OWNER_EMAIL in result.stderr


def test_strips_co_authored_by_lines(run_hook):
    message = VALID_MESSAGE + (
        "\nCo-Authored-By: Claude <noreply@anthropic.com>\n"
        "co-authored-by: Someone <someone@example.com>\n"
    )
    result, final_text = run_hook(message)
    assert result.returncode == 0, result.stderr
    assert "co-authored-by" not in final_text.lower()
    assert "noreply@anthropic.com" not in final_text
    assert "stop demo recent form leaking" in final_text


# --- subject rules: lowercase after the colon, no trailing period (QA-10) --------------------------


@pytest.mark.parametrize(
    "subject",
    [
        "fix: accept UPPERCASE SUMMARY.",
        "fix: accept Uppercase in the middle",
        "fix: add the readme.",
        "fix: add the readme...",
        "fix(Pipeline): add thing",
        "feat: ADD thing",
    ],
)
def test_rejects_uppercase_or_a_trailing_period_in_the_subject(run_hook, subject):
    result, _ = run_hook(f"{subject}\n\nBody.\n")

    assert result.returncode != 0, subject
    assert "Subject must look like" in result.stderr


@pytest.mark.parametrize(
    "subject",
    [
        "fix: stop demo recent form leaking into live starters",
        "feat: rate-based labels with limited-sample flags and data scopes",
        "docs: add rate bands, analytics and qa gate decisions (d25-d27)",
        "fix(pipeline): keep `AsOf` out of the snapshot",  # uppercase inside backticks is code
        "test: cover as_of end to end and place phase 0 gaps (d28)",
    ],
)
def test_still_accepts_the_subjects_the_repo_already_uses(run_hook, subject):
    result, _ = run_hook(f"{subject}\n\nBody.\n")

    assert result.returncode == 0, result.stderr


# --- Merge and Revert: only the shapes git writes itself, never free text --------------------------

REVERT_SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.mark.parametrize(
    "message",
    ["Merge arbitrary text\n", "Merge\n", "Merge branch\n", "Revert whatever I like\n", 'Revert "x"\n'],
)
def test_rejects_merge_and_revert_subjects_that_git_did_not_write(run_hook, message):
    result, _ = run_hook(message)

    assert result.returncode != 0, message


@pytest.mark.parametrize(
    "message",
    [
        "Merge branch 'feature' into v2\n",
        "Merge remote-tracking branch 'origin/v2'\n",
        "Merge tag 'v1.0.0-kaggle'\n",
        f'Revert "fix: stop demo form leaking"\n\nThis reverts commit {REVERT_SHA}.\n',
    ],
)
def test_accepts_the_merge_and_revert_messages_git_generates(run_hook, message):
    result, _ = run_hook(message)

    assert result.returncode == 0, result.stderr


def test_a_revert_without_the_reverts_line_is_rejected(run_hook):
    result, _ = run_hook('Revert "fix: stop demo form leaking"\n\nBecause I said so.\n')

    assert result.returncode != 0


def test_a_merge_message_still_needs_the_owner_identity(run_hook):
    result, _ = run_hook("Merge branch 'feature' into v2\n", author_email="someone@example.com")

    assert result.returncode != 0
    assert OWNER_EMAIL in result.stderr


# --- attribution: every tool, not only Claude ---------------------------------------------------------


@pytest.mark.parametrize(
    "trailer",
    [
        "Generated by Codex",
        "generated by codex",
        "Generated with Codex CLI",
        "Generated with [Claude Code](https://claude.com/claude-code)",
        "\U0001F916 Generated with ChatGPT",
        "Generated by GitHub Copilot",
        "Co-authored-by: Codex <codex@openai.com>",
        "Co-authored-by: ChatGPT <noreply@openai.com>",
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "Assisted-by: Claude",
        "Codex-Session: 123",
        "Claude-Session: abc",
        "Signed-off-by: Codex <noreply@openai.com>",
    ],
)
def test_strips_ai_attribution_from_any_tool(run_hook, trailer):
    result, final_text = run_hook(VALID_MESSAGE + f"\n{trailer}\n")

    assert result.returncode == 0, result.stderr
    assert trailer.lower() not in final_text.lower()
    assert "stop demo recent form leaking" in final_text


# The filter must not depend on the locale of the shell that runs `git commit` (QA2-05): under a
# UTF-8 locale the emoji line used to stay in the message. The environment is a test parameter:
# the default of whoever runs the suite, then C and C.UTF-8.
LOCALES = {
    "default": {},
    "C": {"LC_ALL": "C"},
    "C.UTF-8": {"LC_ALL": "C.UTF-8"},
}


@pytest.mark.parametrize("locale", list(LOCALES))
@pytest.mark.parametrize(
    "trailer",
    [
        "\U0001F916 Generated with ChatGPT",
        "\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)",
        "✨ generated by codex",
        "Generated with Codex CLI",
        "Co-Authored-By: Claude <noreply@anthropic.com>",
    ],
)
def test_attribution_is_stripped_in_every_locale(run_hook, trailer, locale):
    result, final_text = run_hook(VALID_MESSAGE + f"\n{trailer}\n", env_overrides=LOCALES[locale])

    assert result.returncode == 0, result.stderr
    assert trailer.lower() not in final_text.lower()
    assert "stop demo recent form leaking" in final_text


@pytest.mark.parametrize("locale", list(LOCALES))
def test_prose_with_accents_and_emoji_survives_in_every_locale(run_hook, locale):
    body = "Corrige el análisis de lanzamientos — niño \U0001F9E2 sin cambios.\n"
    result, final_text = run_hook(
        f"docs: add qa report for phase-0\n\n{body}\n\U0001F916 Generated with ChatGPT\npytest 1/1.\n",
        env_overrides=LOCALES[locale],
    )

    assert result.returncode == 0, result.stderr
    assert body.strip() in final_text
    assert "chatgpt" not in final_text.lower()


def test_keeps_prose_that_only_mentions_a_tool(run_hook):
    body = "Record the independent review run by Codex, and the fix Claude Code suggested.\n"
    result, final_text = run_hook(f"docs: add qa report for phase-0\n\n{body}\npytest 1/1.\n")

    assert result.returncode == 0, result.stderr
    assert body.strip() in final_text


def test_a_message_that_is_only_attribution_after_the_subject_has_no_body(run_hook):
    result, _ = run_hook("fix: stop it\n\nGenerated by Codex\n")

    assert result.returncode != 0
    assert "body" in result.stderr


# --- the test environment itself -----------------------------------------------------------------------


def test_the_hook_runs_with_the_tools_it_uses_even_if_the_process_path_lacks_them(run_hook, monkeypatch):
    # QA found 4 hook tests failing because `sed` was not on PATH on Windows. The fixture
    # now puts the directory of the `sh` it found (and Git's usr/bin) on the hook's PATH.
    monkeypatch.setenv("PATH", os.devnull)
    result, _ = run_hook(VALID_MESSAGE)

    assert result.returncode == 0, result.stderr
