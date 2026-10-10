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

    def _run(message: str, author_email: str = OWNER_EMAIL, committer_email: str = OWNER_EMAIL):
        msg_file = repo / "COMMIT_EDITMSG"
        msg_file.write_text(message, encoding="utf-8", newline="\n")
        env = {
            **os.environ,
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": OWNER_NAME,
            "GIT_AUTHOR_EMAIL": author_email,
            "GIT_COMMITTER_NAME": OWNER_NAME,
            "GIT_COMMITTER_EMAIL": committer_email,
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
