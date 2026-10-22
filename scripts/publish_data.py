"""Commit the day's data file to `main` and touch nothing else (docs/plans/P1.md, 4.2; D15, D42).

    python scripts/publish_data.py CANDIDATE [--repo DIR] [--remote URL] [--key-file PATH] [--dry-run]

`CANDIDATE` is a file the daily job built and the publish job re-validated (`python -m data_pipeline.daily --check`).
This script does not judge its contents; it only publishes them, and only safely:

- the work tree of `--repo` must be clean before anything is copied;
- the candidate is copied to `public/data/pitchcraft-demo.json`, and every path `git status` then reports must be under
  `public/data/` or `evals/live/` (D15), else the copy is undone and nothing is committed;
- a candidate that differs from the committed file only in its three timestamps is not committed;
- the commit is the owner's, Daniel Herdenez, with the subject `data: daily update YYYY-MM-DD` (D42), the day being the
  `target_date` of the run;
- the push is `HEAD:refs/heads/main`, never forced, from the branch `main` only, over SSH with the deploy key in
  `--key-file` and GitHub's published host keys (pinned below, `StrictHostKeyChecking=yes`). The script names the key file to
  ssh; it never reads or prints it.

`--dry-run` does all of it in a temporary clone of `--repo`, pushes nothing, and prints the files and the verdict of the
allowlist. The checkout is left as it was.

Output goes to stdout as `publish: ...` lines; a failure is `publish: failed CODE` with the code one of
`candidate_unreadable`, `dirty_tree`, `not_on_main`, `outside_allowlist`, `git_failed`, `push_rejected`.
Exit codes: 0 published, unchanged or dry run done; 1 failed; 2 usage error.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Sequence

TARGET = "public/data/pitchcraft-demo.json"
ALLOWED_PREFIXES = ("public/data/", "evals/live/")
BRANCH = "main"
IDENTITY_NAME = "Daniel Herdenez"
IDENTITY_EMAIL = "edherdenez@gmail.com"
DEFAULT_REMOTE = "git@github.com:Dher10/pitchcraft-agent.git"
# The instants a run stamps on the file. Everything else in the file is content.
TIMESTAMP_KEYS = frozenset({"generated_at", "data_fetched_at", "run_at"})

# GitHub's published SSH host keys, from `GET https://api.github.com/meta` (`ssh_keys`) on 2026-10-22. Their SHA256
# fingerprints equal the ones in docs.github.com ("GitHub's SSH key fingerprints"); a test hashes them against a copy of
# the documented values. If GitHub rotates a key, a push fails closed here: replace the key after reading both sources.
GITHUB_HOST_KEYS = (
    ("ssh-ed25519", "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"),
    (
        "ecdsa-sha2-nistp256",
        "AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBEmKSENjQEezOmxkZMy7opKgwFB9nkt5YRrYMjNuG5N87uRgg6CLrbo5wAdT/y6v0mKV0U2w0WZ2YB/++Tpockg=",
    ),
    (
        "ssh-rsa",
        "AAAAB3NzaC1yc2EAAAADAQABAAABgQCj7ndNxQowgcQnjshcLrqPEiiphnt+VTTvDP6mHBL9j1aNUkY4Ue1gvwnGLVlOhGeYrnZaMgRK6+PKCUXaDbC7qtbW8gIkhL7aGCsOr/C56SJMy/BCZfxd1nWzAOxSDPgVsmerOBYfNqltV9/hWCqBywINIR+5dIg6JTJ72pcEpEjcYgXkE2YEFXV1JHnsKgbLWNlhScqb2UmyRkQyytRLtL+38TGxkxCflmO+5Z8CSSNY7GidjMIZ7Q4zMjA2n1nGrlTDkzwDCsw+wqFPGQA179cnfGWOWRVruj16z6XyvxvjJwbz0wQZ75XK5tKSb7FNyeIEs4TT4jk+S4dhPeAUC5y+bDYirYgM4GC7uEnztnZyaVWQ7B381AK4Qdrwt51ZqExKbQpTUNn+EjqoTwvqNj4kqx5QUCI0ThS/YkOxJCXmPUWZbhjpCg56i+2aB6CmK2JGhn57K5mj0MNdBXA4/WnwH6XoPWJzK5Nyu2zB3nAZp+S5hpQs+p1vN1/wsjk=",
    ),
)

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2


class Failure(Exception):
    """The publication stopped; `code` is the closed label printed as `publish: failed CODE`."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def say(text: str) -> None:
    print(f"publish: {text}", flush=True)


# --- the allowlist -----------------------------------------------------------------------------------------------


def outside_allowlist(paths: Iterable[str]) -> list[str]:
    """The paths that are not a file under `public/data/` or `evals/live/` (D15). Strict: no `..`, no leading `/` or `./`."""

    outside = []
    for path in paths:
        parts = path.split("/")
        ok = (
            path == path.strip()
            and "\\" not in path
            and not path.startswith(("/", "./"))
            and all(part not in ("", ".", "..") for part in parts)
            and any(path.startswith(prefix) and len(path) > len(prefix) for prefix in ALLOWED_PREFIXES)
        )
        if not ok:
            outside.append(path)
    return outside


# --- the file ------------------------------------------------------------------------------------------------------


def _reject_constant(name: str) -> None:
    raise ValueError(f"{name} is not a JSON value")


def _strip_timestamps(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _strip_timestamps(item) for key, item in value.items() if key not in TIMESTAMP_KEYS}
    if isinstance(value, list):
        return [_strip_timestamps(item) for item in value]
    return value


def same_apart_from_timestamps(old_text: str, new_text: str) -> bool:
    """True when both are JSON objects equal once the three timestamps are removed. Anything unreadable is a change."""

    try:
        old = json.loads(old_text, parse_constant=_reject_constant)
        new = json.loads(new_text, parse_constant=_reject_constant)
    except ValueError:
        return False
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False
    return _strip_timestamps(old) == _strip_timestamps(new)


def target_date_of(text: str) -> str:
    """The `target_date` of the run that built the candidate, as an ISO date; `Failure` for anything else."""

    try:
        payload = json.loads(text, parse_constant=_reject_constant)
        value = payload["metadata"]["data_status"]["live_run"]["target_date"]
        if isinstance(value, str) and date.fromisoformat(value).isoformat() == value:
            return value
    except (ValueError, KeyError, TypeError):
        pass
    raise Failure("candidate_unreadable")


# --- git -----------------------------------------------------------------------------------------------------------


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env.update(extra or {})
    return env


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=_env(env))


def _git_ok(repo: Path, *args: str) -> str:
    result = _git(repo, *args)
    if result.returncode != 0:
        raise Failure("git_failed")
    return result.stdout


def changed_paths(repo: Path) -> list[str]:
    """Every path `git status` reports (staged, unstaged, untracked; both sides of a rename). Ignored files are not dirt."""

    output = _git_ok(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = output.split("\0")
    paths: list[str] = []
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        paths.append(path)
        if "R" in status or "C" in status:
            if index < len(entries) and entries[index]:
                paths.append(entries[index])
            index += 1
    return paths


def known_hosts_text() -> str:
    return "".join(f"github.com {kind} {key}\n" for kind, key in GITHUB_HOST_KEYS)


def ssh_command(key_file: Path, known_hosts: Path) -> str:
    """The `GIT_SSH_COMMAND`: this key only, GitHub's pinned host keys only, no prompt, no other known_hosts."""

    options = (
        "IdentitiesOnly=yes",
        "StrictHostKeyChecking=yes",
        "BatchMode=yes",
        f"UserKnownHostsFile={shlex.quote(known_hosts.as_posix())}",
        "GlobalKnownHostsFile=/dev/null",
    )
    return "ssh -i " + shlex.quote(key_file.as_posix()) + "".join(f" -o {option}" for option in options)


def is_ssh(remote: str) -> bool:
    return remote.startswith(("git@", "ssh://"))


def _remove_tree(path: Path) -> None:
    def make_writable(function, target, error):  # git's object files are read-only on Windows
        os.chmod(target, stat.S_IWRITE)
        function(target)

    shutil.rmtree(path, onexc=make_writable)


# --- the publication ----------------------------------------------------------------------------------------------


def _work_in(repo: Path, candidate_bytes: bytes, subject: str) -> bool:
    """Copy, check and commit in `repo`. Returns whether a commit was made. Raises `Failure`."""

    old_bytes: bytes | None = None
    target = repo / TARGET
    if target.exists():
        old_bytes = target.read_bytes()
        if same_apart_from_timestamps(old_bytes.decode("utf-8", errors="replace"), candidate_bytes.decode("utf-8")):
            return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(candidate_bytes)
    paths = changed_paths(repo)
    outside = outside_allowlist(paths)
    if outside or not paths:
        if old_bytes is None:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(old_bytes)
        for path in outside:
            say(f"outside {path}")
        raise Failure("outside_allowlist" if outside else "git_failed")
    for path in sorted(paths):
        say(f"file {path}")
    say("allowlist ok")
    _git_ok(repo, "add", "-A")
    result = _git(
        repo,
        "-c", f"user.name={IDENTITY_NAME}",
        "-c", f"user.email={IDENTITY_EMAIL}",
        "-c", "commit.gpgsign=false",
        "commit", "-q", "-m", subject,
    )  # fmt: skip
    if result.returncode != 0:
        _git(repo, "reset", "-q")
        if old_bytes is None:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(old_bytes)
        raise Failure("git_failed")
    return True


def _push(repo: Path, remote: str, key_file: Path | None) -> None:
    scratch: Path | None = None
    env: dict[str, str] = {}
    try:
        if is_ssh(remote):
            assert key_file is not None
            scratch = Path(tempfile.mkdtemp(prefix="pitchcraft-hosts-"))
            known_hosts = scratch / "known_hosts"
            known_hosts.write_text(known_hosts_text(), encoding="utf-8", newline="\n")
            env["GIT_SSH_COMMAND"] = ssh_command(key_file, known_hosts)
        result = subprocess.run(
            ["git", "-C", str(repo), "push", remote, f"HEAD:refs/heads/{BRANCH}"],
            capture_output=True,
            text=True,
            env=_env(env),
        )
    finally:
        if scratch is not None:
            _remove_tree(scratch)
    if result.returncode != 0:
        # Only the refusal itself (`To ...`, ` ! [rejected]`, `remote: ...`, ssh's own error); never git's advice.
        for line in result.stderr.splitlines():
            if not line.startswith(("hint:", "Hint:", "error: failed to push")):
                print(line, file=sys.stderr)
        raise Failure("push_rejected")


def publish(candidate: Path, repo: Path, remote: str, key_file: Path | None, dry_run: bool) -> None:
    try:
        candidate_bytes = candidate.read_bytes()  # published byte for byte: no newline translation
        target_date = target_date_of(candidate_bytes.decode("utf-8"))
    except (OSError, ValueError):
        raise Failure("candidate_unreadable") from None
    subject = f"data: daily update {target_date}"
    if changed_paths(repo):
        raise Failure("dirty_tree")
    if not dry_run and _git_ok(repo, "branch", "--show-current").strip() != BRANCH:
        raise Failure("not_on_main")

    clone: Path | None = None
    try:
        work = repo
        if dry_run:
            clone = Path(tempfile.mkdtemp(prefix="pitchcraft-dry-run-"))
            result = subprocess.run(
                ["git", "clone", "-q", "--no-hardlinks", str(repo), str(clone / "repo")],
                capture_output=True,
                text=True,
                env=_env(),
            )
            if result.returncode != 0:
                raise Failure("git_failed")
            work = clone / "repo"
        committed = _work_in(work, candidate_bytes, subject)
        if not committed:
            say("unchanged: the file differs from the committed one only in its timestamps")
            return
        if dry_run:
            say(f'dry-run: would commit "{subject}" and push HEAD to {BRANCH}; nothing pushed')
            return
        _push(work, remote, key_file)
        say(f"pushed {_git_ok(work, 'rev-parse', '--short', 'HEAD').strip()} to {BRANCH}: {subject}")
    finally:
        if clone is not None:
            _remove_tree(clone)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python scripts/publish_data.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("candidate", type=Path, help="the validated file the daily job built")
    parser.add_argument("--repo", type=Path, default=Path("."), help="the checkout to commit in (default: .)")
    parser.add_argument("--remote", default=DEFAULT_REMOTE, help="where to push (default: this repository over SSH)")
    parser.add_argument("--key-file", type=Path, help="the deploy key; required to push to an SSH remote")
    parser.add_argument("--dry-run", action="store_true", help="do everything in a temporary clone; push nothing")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.dry_run and is_ssh(args.remote):
        if args.key_file is None:
            parser.error("--key-file is required to push to an SSH remote")
        if not args.key_file.is_file():
            parser.error("--key-file does not exist")
    if args.key_file is not None and not args.key_file.is_file():
        parser.error("--key-file does not exist")
    try:
        publish(args.candidate, args.repo.resolve(), args.remote, args.key_file, args.dry_run)
    except Failure as failure:
        say(f"failed {failure.code}")
        return EXIT_FAILED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
