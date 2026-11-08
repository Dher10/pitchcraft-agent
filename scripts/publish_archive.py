"""Commit the archive candidate folder to `main` and touch nothing else (docs/plans/R4.md 4.5; D15, D42, D66).

    python scripts/publish_archive.py CANDIDATE_DIR [--repo DIR] [--remote URL] [--key-file PATH] [--dry-run]

`CANDIDATE_DIR` is the folder the backfill built and `python -m data_pipeline.archive_finalize check` accepted. This
script judges it **again** (no network), then publishes it only safely, with the same machinery as `publish_data.py`:

- the work tree of `--repo` must be clean before anything is copied;
- the folder is copied to `public/data/archive/` and every path `git status` then reports must be under `public/data/` or
  `evals/live/` (D15), else the copy is undone and nothing is committed;
- a file the repository already has under `public/data/archive/` and the candidate lacks is a refusal (`dropped_file`): a
  backfill adds and corrects, it never deletes a published game;
- the commit is the owner's, Daniel Herdenez, with the subject `data: archive backfill YYYY` (the season of the index);
- the push is `HEAD:refs/heads/main`, never forced, from the branch `main` only, over SSH with the deploy key;
- `--dry-run` does all of it in a temporary clone and pushes nothing.

Output goes to stdout as `publish: ...` lines; a failure is `publish: failed CODE`, the code one of
`candidate_unreadable` (a folder or file that cannot be read), `candidate_invalid` (a folder that `archive_finalize check`
refuses, including any file the manifest does not list), `dirty_tree`, `not_on_main`, `outside_allowlist`, `dropped_file`, `git_failed`,
`push_rejected`. Exit codes: 0 published, unchanged or dry run done; 1 failed; 2 usage error.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import publish_data as pd  # noqa: E402  (the same allowlist, identity, git helpers and push as the daily job)
from data_pipeline import archive_finalize  # noqa: E402

ARCHIVE_DIR = "public/data/archive"
SUBJECT = "data: archive backfill {season}"
EXIT_OK, EXIT_FAILED, EXIT_USAGE = pd.EXIT_OK, pd.EXIT_FAILED, pd.EXIT_USAGE


def candidate_files(candidate: Path) -> dict[str, bytes]:
    """The files of a candidate folder by relative path, as bytes. A path that escapes the folder is refused."""

    files: dict[str, bytes] = {}
    root = candidate.resolve()
    for path in sorted(candidate.rglob("*")):
        if path.is_dir():
            continue
        resolved = path.resolve()
        relative = resolved.relative_to(root).as_posix() if root in resolved.parents else None
        if relative is None or path.is_symlink() or relative.startswith(".") or "/." in relative:
            raise pd.Failure("candidate_invalid")
        files[relative] = path.read_bytes()
    return files


def _season_of(candidate: Path) -> int:
    names = sorted(p.name for p in candidate.glob("index-*.json"))
    if len(names) != 1:
        raise pd.Failure("candidate_invalid")
    stem = names[0].removeprefix("index-").removesuffix(".json")
    if not (stem.isdigit() and len(stem) == 4):
        raise pd.Failure("candidate_invalid")
    return int(stem)


def _work_in(repo: Path, files: dict[str, bytes], subject: str) -> bool:
    """Copy, check and commit in `repo`. Returns whether a commit was made. Raises `Failure`."""

    base = repo / ARCHIVE_DIR
    existing = {p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()} if base.is_dir() else set()
    if existing - set(files):
        raise pd.Failure("dropped_file")
    before = {name: (base / name).read_bytes() for name in existing}
    changed = [name for name, data in files.items() if before.get(name) != data]
    if not changed:
        return False

    def roll_back() -> None:
        try:
            pd._git(repo, "reset", "-q")
        except (OSError, subprocess.SubprocessError, UnicodeError):
            pass
        for name in files:
            try:
                if name in before:
                    (base / name).write_bytes(before[name])
                else:
                    (base / name).unlink(missing_ok=True)
            except OSError:
                pass

    try:
        for name in changed:
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[name])
        paths = pd.changed_paths(repo)
        outside = pd.outside_allowlist(paths)
        if outside or not paths:
            for path in outside:
                pd.say(f"outside {path}")
            raise pd.Failure("outside_allowlist" if outside else "git_failed")
        for path in sorted(paths):
            pd.say(f"file {path}")
        pd.say("allowlist ok")
        pd._git_ok(repo, "add", "-A")
        result = pd._git(
            repo,
            "-c", f"user.name={pd.IDENTITY_NAME}",
            "-c", f"user.email={pd.IDENTITY_EMAIL}",
            "-c", "commit.gpgsign=false",
            "commit", "-q", "-m", subject,
            env=pd._commit_env(),
        )  # fmt: skip
        if result.returncode != 0:
            raise pd.Failure("git_failed")
    except (pd.Failure, OSError, subprocess.SubprocessError, UnicodeError):
        roll_back()
        raise
    return True


def publish(candidate: Path, repo: Path, remote: str, key_file: Path | None, dry_run: bool) -> None:
    if not candidate.is_dir():
        raise pd.Failure("candidate_unreadable")
    try:
        problems = archive_finalize.check(candidate)
    except (OSError, ValueError):
        raise pd.Failure("candidate_unreadable") from None
    if problems:
        for label in problems:
            pd.say(f"problem {label}")
        raise pd.Failure("candidate_invalid")
    try:
        files = candidate_files(candidate)
        subject = SUBJECT.format(season=_season_of(candidate))
    except OSError:
        raise pd.Failure("candidate_unreadable") from None
    if pd.changed_paths(repo):
        raise pd.Failure("dirty_tree")
    if not dry_run and pd._git_ok(repo, "branch", "--show-current").strip() != pd.BRANCH:
        raise pd.Failure("not_on_main")

    clone: Path | None = None
    try:
        work = repo
        if dry_run:
            clone = Path(tempfile.mkdtemp(prefix="pitchcraft-archive-dry-run-"))
            result = subprocess.run(
                ["git", "clone", "-q", "--no-hardlinks", str(repo), str(clone / "repo")],
                capture_output=True, text=True, env=pd._env(),
            )
            if result.returncode != 0:
                raise pd.Failure("git_failed")
            work = clone / "repo"
        if not _work_in(work, files, subject):
            pd.say("unchanged: every file is the committed one")
            return
        if dry_run:
            pd.say(f'dry-run: would commit "{subject}" and push HEAD to {pd.BRANCH}; nothing pushed')
            return
        pd._push(work, remote, key_file)
        pd.say(f"pushed {pd._git_ok(work, 'rev-parse', '--short', 'HEAD').strip()} to {pd.BRANCH}: {subject}")
    finally:
        if clone is not None:
            pd._remove_tree(clone)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python scripts/publish_archive.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("candidate", type=Path, help="the folder the backfill built and `archive_finalize check` accepted")
    parser.add_argument("--repo", type=Path, default=Path("."), help="the checkout to commit in (default: .)")
    parser.add_argument("--remote", default=pd.DEFAULT_REMOTE, help="where to push (default: this repository over SSH)")
    parser.add_argument("--key-file", type=Path, help="the deploy key; required to push to an SSH remote")
    parser.add_argument("--dry-run", action="store_true", help="do everything in a temporary clone; push nothing")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if not args.dry_run and pd.is_ssh(args.remote):
        if args.key_file is None:
            parser.error("--key-file is required to push to an SSH remote")
        if not args.key_file.is_file():
            parser.error("--key-file does not exist")
    if args.key_file is not None and not args.key_file.is_file():
        parser.error("--key-file does not exist")
    try:
        publish(args.candidate, args.repo.resolve(), args.remote, args.key_file, args.dry_run)
    except pd.Failure as failure:
        pd.say(f"failed {failure.code}")
        return EXIT_FAILED
    except (OSError, subprocess.SubprocessError, UnicodeError):
        pd.say("failed git_failed")
        return EXIT_FAILED
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
