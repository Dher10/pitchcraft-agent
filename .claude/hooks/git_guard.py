"""PreToolUse hook for the Bash and PowerShell tools: the git safety rules of D35 (docs/DECISIONS.md, AGENTS.md "Agency workflow").

Claude Code runs this before every Bash and PowerShell call (`.claude/settings.json` has one matcher for each)
and gives it the call as JSON on stdin (`{"tool_name": "Bash", "tool_input": {"command": "..."}}`). Exit code 0
lets the call through; exit code 2 blocks it and sends the reason (stderr) back to the session. Nothing here
edits anything.

It blocks:
  - a push to any branch other than `v2` or `experiment/*`;
  - any operation on `main` / `master` or on a tag (reading them is allowed: `git log main`, `git tag --list`);
  - `--force`, `--force-with-lease`, a `+refspec`, `rebase`, `reset --hard`, `--no-verify`, `filter-branch`;
  - deleting or renaming `v2` or `main` (`git branch -d/-D/-m`);
  - changing a remote (`git remote add`, `set-url`, `remove`, `rename`, ...);
  - `commit --amend` when HEAD is already on a remote;
  - a commit whose author or committer is not Daniel Herdenez <edherdenez@gmail.com>, and a change of that identity;
  - changing `core.hooksPath` (reading it, `git config --get core.hooksPath`, is allowed: CONTRIBUTING asks for it);
  - git behind a wrapper that carries a string the parser cannot see into (`bash -c`, `sh -c`, `eval`,
    `powershell`/`pwsh -Command`, `cmd /c`, `python -c`, `node -e`, `Invoke-Expression`, ...) whenever the string
    mentions git, and git behind a program name built at run time (`x=git; $x push ...`). The session runs git
    directly instead, where the rules above can read it.

Git options are read the way git reads them: combined short flags (`-fu`) and unambiguous abbreviations (`--forc`).

What it does not see: a script file or a program that runs git on its own, a function or alias a shell
defines, and `gh` / the GitHub API. GitHub rulesets protect `main`, `v2` and the tag `v1.0.0-kaggle` on the server for those cases.

The decision is `decide(command, git)`; `git(*args)` runs git and returns its output (the tests pass a fake).
The parser reads the command the way a shell would, well enough for the commands an agent writes; a command it
cannot read is not blocked on that account (the commit-msg hook and CI are the other lines), but every line of
the rules above is a test in `tests/test_agent_git_guard.py`.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Callable

OWNER_NAME = "Daniel Herdenez"
OWNER_EMAIL = "edherdenez@gmail.com"
ALLOWED_PUSH_BRANCH = re.compile(r"^(v2|experiment/.+)$")
PROTECTED_BRANCHES = ("main", "master")

# Subcommands that only read: naming `main` or a tag in them is fine (`git diff main...HEAD`, `git show v1.0.0`).
READ_ONLY = {
    "status", "diff", "log", "show", "rev-parse", "rev-list", "merge-base", "cat-file", "ls-tree", "ls-files",
    "blame", "shortlog", "describe", "name-rev", "for-each-ref", "show-ref", "ls-remote", "range-diff", "grep",
    "whatchanged", "diff-tree", "diff-index", "count-objects", "check-ignore", "config", "help", "version", "remote",
    "stash", "add",
}
# Subcommands that create commits (their identity must be the owner's).
COMMITTING = {"commit", "merge", "revert", "cherry-pick", "am"}
CONFIG_WRITING_FLAGS = {"--unset", "--unset-all", "--add", "--replace-all", "-e", "--edit", "--rename-section", "--remove-section"}
REMOTE_CHANGING = {"add", "set-url", "remove", "rm", "rename", "set-head", "set-branches", "prune"}
BRANCH_REMOVING_FLAGS = {"-d", "-D", "--delete", "-m", "-M", "--move"}
PUSH_OPTIONS_WITH_VALUE ={"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
TAG_LISTING_FLAGS = {"-l", "--list", "-n", "--contains", "--no-contains", "--points-at", "--sort", "--format", "--merged",
                     "--no-merged", "-v", "--verify", "--column", "--no-column", "-i", "--ignore-case"}

GitRunner = Callable[..., str]
REDIRECTION = re.compile(r"^\d*(>>?|<)")  # `>out`, `2>`, `2>/dev/null`, `<in`: not arguments of the command


def run_git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


# --- reading the command -------------------------------------------------------------------------------------


def strip_heredocs(command: str) -> str:
    """Drop the body of every here-document: it is text for a program (a commit message), not a command."""

    lines, out, terminator = command.split("\n"), [], None
    for line in lines:
        if terminator is not None:
            if line.strip() == terminator or (terminator in ("'@", '"@') and line.startswith(terminator)):
                terminator = None
            continue
        out.append(line)
        match = re.search(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1", line)
        if match:
            terminator = match.group(2)
        elif re.search(r"@['\"]\s*$", line):  # a PowerShell here-string: `@'` ... `'@`
            terminator = line.rstrip()[-1] + "@"
    return "\n".join(out)


def segments(command: str) -> list[list[str]]:
    """The simple commands of a command line, as token lists (split on ; && || | and newlines, outside quotes)."""

    commands: list[list[str]] = []
    for line in strip_heredocs(command).split("\n"):
        try:
            lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            tokens = line.split()
        current: list[str] = []
        skip_target = False
        for token in tokens:
            if token and set(token) <= set(";&|"):
                if current:
                    commands.append(current)
                current = []
                skip_target = False
            elif skip_target:
                skip_target = False  # the file a bare `>` or `2>` writes to
            elif REDIRECTION.match(token):
                skip_target = bool(re.fullmatch(r"\d*(>>?|<)", token))  # `>out.txt` has its target inside; `>` has it next
            else:
                current.append(token)
        if current:
            commands.append(current)
    return commands


# Long options the rules below look for. Git accepts any unambiguous abbreviation (`--forc`, `--no-ver`, `--amen`), so an
# abbreviation of one of these is read as the option itself (the shortest one it could be).
DANGEROUS_LONG = (
    "--force", "--force-with-lease", "--force-if-includes", "--no-verify", "--amend", "--hard", "--mirror", "--delete",
    "--tags", "--follow-tags", "--prune", "--rebase", "--all",
)


def canonical_option(arg: str) -> str:
    name, equals, value = arg.partition("=")
    if name.startswith("--") and len(name) >= 4 and name not in DANGEROUS_LONG:
        candidates = [option for option in DANGEROUS_LONG if option.startswith(name)]
        if candidates:
            return min(candidates, key=len) + equals + value
    return arg


def program_name(token: str) -> str:
    """`C:\\Program Files\\Git\\cmd\\git.exe` -> `git`: the program a command word runs, without directory and extension."""

    name = re.split(r"[\\/]", token)[-1].lower()
    return re.sub(r"\.(exe|cmd|bat|com|ps1)$", "", name)


class Invocation:
    """One `git ...` simple command: its environment, its global options, its subcommand and its arguments."""

    def __init__(self, tokens: list[str]):
        self.env: dict[str, str] = {}
        self.config: dict[str, str] = {}
        self.sub = ""
        self.args: list[str] = []
        index = 0
        while index < len(tokens) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[index]):
            name, _, value = tokens[index].partition("=")
            self.env[name] = value
            index += 1
        if index >= len(tokens) or program_name(tokens[index]) != "git":
            self.is_git = False
            return
        self.is_git = True
        index += 1
        while index < len(tokens) and tokens[index].startswith("-"):
            token = tokens[index]
            if token == "-c" and index + 1 < len(tokens):
                key, _, value = tokens[index + 1].partition("=")
                self.config[key.lower()] = value
                index += 2
            elif token in ("-C", "--git-dir", "--work-tree", "--namespace") and index + 1 < len(tokens):
                index += 2
            else:
                index += 1
        if index < len(tokens):
            self.sub = tokens[index]
            self.args = [canonical_option(arg) for arg in tokens[index + 1 :]]

    def flags(self) -> list[str]:
        """The arguments that are options (they start with `-`), up to a `--`."""

        found = []
        for arg in self.args:
            if arg == "--":
                break
            if arg.startswith("-"):
                found.append(arg)
        return found

    def positional(self, with_value: set[str] | None = None) -> list[str]:
        with_value = with_value or set()
        found, skip = [], False
        for arg in self.args:
            if skip:
                skip = False
            elif arg in with_value:
                skip = True
            elif not arg.startswith("-") or arg == "-":
                found.append(arg)
        return found


# --- the rules -------------------------------------------------------------------------------------------------


def _ref_name(ref: str) -> str:
    for prefix in ("refs/heads/", "refs/remotes/origin/", "remotes/origin/", "origin/"):
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return ref


def _is_protected(ref: str) -> bool:
    return _ref_name(ref) in PROTECTED_BRANCHES


def _tag_names(git: GitRunner) -> set[str]:
    try:
        return {line.strip() for line in git("tag", "--list").splitlines() if line.strip()}
    except Exception:  # noqa: BLE001 - a repository without tags, or git missing: nothing to protect by name
        return set()


def _current_branch(git: GitRunner) -> str:
    try:
        return git("branch", "--show-current")
    except Exception:  # noqa: BLE001
        return ""


def _config_value(inv: Invocation, git: GitRunner, key: str, env_name: str | None = None) -> str | None:
    """The value git would use: the command's `-c`, the environment of the command, the process environment, the config."""

    if key in inv.config:
        return inv.config[key]
    if env_name and env_name in inv.env:
        return inv.env[env_name]
    if env_name and os.environ.get(env_name):
        return os.environ[env_name]
    try:
        return git("config", key) or None
    except Exception:  # noqa: BLE001
        return None


def _push_problem(inv: Invocation, git: GitRunner) -> str | None:
    flags = inv.flags()
    for flag in flags:
        if flag == "--force" or flag.startswith("--force-with-lease") or flag == "--force-if-includes" or re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", flag):
            return "a force push is never allowed (D35)"
        if re.fullmatch(r"-[a-zA-Z]*d[a-zA-Z]*", flag):
            return "git push -d can move or delete refs beyond v2 (D35)"
        if flag in ("--all", "--mirror", "--tags", "--follow-tags", "--delete", "-d", "--prune"):
            return f"git push {flag} can move or delete refs beyond v2 (D35)"
    positional = inv.positional(PUSH_OPTIONS_WITH_VALUE)
    refspecs = positional[1:]
    if "tag" in refspecs[:1]:
        return "pushing a tag is not allowed: tags are frozen (D35)"
    destinations: list[tuple[str, str]] = []
    for refspec in refspecs:
        if refspec.startswith("+"):
            return "a +refspec is a force push (D35)"
        if refspec.startswith(":"):
            return "pushing an empty source deletes a remote ref (D35)"
        source, _, destination = refspec.partition(":")
        destinations.append((source, destination or source))
    if not destinations:  # `git push` or `git push origin`: the current branch
        branch = _current_branch(git)
        destinations.append((branch, branch))
    for source, destination in destinations:
        if source == "HEAD" and destination == "HEAD":
            destination = _current_branch(git)
        destination = _ref_name(destination)
        if destination.startswith(("refs/tags/", "tags/")):
            return "pushing a tag is not allowed: tags are frozen (D35)"
        if _is_protected(destination):
            return f"{destination!r} is the release branch: only the owner touches it (D35)"
        if not ALLOWED_PUSH_BRANCH.match(destination):
            return f"git push is allowed only to v2 or experiment/*, not to {destination or '(no branch)'!r} (D35)"
    return None


def _identity_problem(inv: Invocation, git: GitRunner) -> str | None:
    values = {
        "author name": _config_value(inv, git, "user.name", "GIT_AUTHOR_NAME"),
        "author email": _config_value(inv, git, "user.email", "GIT_AUTHOR_EMAIL"),
        "committer name": _config_value(inv, git, "user.name", "GIT_COMMITTER_NAME"),
        "committer email": _config_value(inv, git, "user.email", "GIT_COMMITTER_EMAIL"),
    }
    for index, arg in enumerate(inv.args):  # --author="Name <email>"
        given = arg.split("=", 1)[1] if arg.startswith("--author=") else inv.args[index + 1] if arg == "--author" and index + 1 < len(inv.args) else None
        if given is not None:
            match = re.fullmatch(r"\s*(.*?)\s*<(.*)>\s*", given)
            values["author name"], values["author email"] = (match.group(1), match.group(2)) if match else (given, None)
    for what, value in values.items():
        expected = OWNER_NAME if "name" in what else OWNER_EMAIL
        if value != expected:
            return f"the {what} is {value!r}; commits are made as {OWNER_NAME} <{OWNER_EMAIL}> (D35)"
    return None


def _pushed(git: GitRunner) -> bool | None:
    try:
        return bool(git("branch", "-r", "--contains", "HEAD").strip())
    except Exception:  # noqa: BLE001
        return None


def _problem(inv: Invocation, git: GitRunner) -> str | None:
    sub, args, flags = inv.sub, inv.args, inv.flags()

    # whatever the subcommand
    if any(f == "--force" or f.startswith("--force-with-lease") or f == "--force-if-includes" for f in flags):
        return "--force and --force-with-lease are never allowed (D35)"
    if any(re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", f) for f in flags) and sub in ("push", "checkout", "switch", "branch", "clean", "tag", "reset", "worktree"):
        return f"git {sub} -f is a force and is never allowed (D35)"
    if "--no-verify" in args or (sub == "commit" and any(re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", f) for f in flags)):
        return "--no-verify skips the hooks and is never allowed (D35)"
    if any("hookspath" in value.lower() for name, value in inv.env.items() if name.upper().startswith("GIT_CONFIG")):
        return "overriding core.hooksPath through the environment skips the hooks (D35)"
    if "core.hookspath" in inv.config:
        return "overriding core.hooksPath skips the hooks (D35)"
    pull_rebase = sub == "pull" and any(re.fullmatch(r"-[a-zA-Z]*r[a-zA-Z]*", f) for f in flags)
    if sub == "rebase" or pull_rebase or any(a == "--rebase" or (a.startswith("--rebase=") and a != "--rebase=false") for a in args):
        return "rebase rewrites history and is never allowed (D35)"
    if sub in ("filter-branch", "filter-repo"):
        return f"git {sub} rewrites history and is never allowed (D35)"
    if sub == "reset" and "--hard" in args:
        return "reset --hard is never allowed (D35)"

    if sub == "push":
        return _push_problem(inv, git)

    if sub == "commit" and "--amend" in args:
        pushed = _pushed(git)
        if pushed is None or pushed:
            return "commit --amend on a commit that is already on a remote rewrites history (D35)"

    if sub == "config":
        positional = inv.positional()
        if len(positional) >= 2 and positional[0].lower() in ("user.name", "user.email"):
            expected = OWNER_NAME if positional[0].lower() == "user.name" else OWNER_EMAIL
            if positional[1] != expected:
                return f"the git identity is {OWNER_NAME} <{OWNER_EMAIL}> and is not changed (D35)"
        if positional and positional[0].lower() == "core.hookspath":
            # `git config core.hooksPath` and `git config --get core.hooksPath` read it (CONTRIBUTING asks for that check)
            if len(positional) >= 2 or any(flag in CONFIG_WRITING_FLAGS for flag in flags):
                return "core.hooksPath is not changed (D35)"
        return None

    if sub == "remote":
        action = (inv.positional() or [""])[0]
        if action in REMOTE_CHANGING:
            return f"git remote {action} changes where the work is sent and is not allowed (D35)"
        return None

    if sub == "branch" and any(flag in BRANCH_REMOVING_FLAGS for flag in flags):
        names = {_ref_name(arg) for arg in inv.positional()}
        if names & set(PROTECTED_BRANCHES):  # `-m` takes a branch here, not a message: positional(), not positional_and_refs()
            return f"{sorted(names & set(PROTECTED_BRANCHES))[0]!r} is the release branch: it is not deleted or renamed (D35)"
        if "v2" in names:
            return "'v2' cannot be deleted or renamed (D35)"

    if sub == "tag":
        positional = inv.positional()
        if any(flag in ("-d", "--delete", "-f", "--force", "-a", "-s", "-m") for flag in flags):
            return "tags are frozen: creating, moving or deleting a tag is not allowed (D35)"
        listing = bool({"-l", "--list", "--contains", "--no-contains", "--points-at", "--merged", "--no-merged"} & set(flags))
        if positional and not listing:  # `git tag v9` creates one; `git tag -l 'v1*'` lists with a pattern
            return "tags are frozen: creating, moving or deleting a tag is not allowed (D35)"
        if flags and not set(flags) <= TAG_LISTING_FLAGS:
            return "tags are frozen (D35)"
        return None

    if sub in COMMITTING:
        problem = _identity_problem(inv, git)
        if problem:
            return problem

    if sub in READ_ONLY:
        return None

    # a mutating subcommand: it must not name main, master or a tag (a commit names no ref: its message is text)
    tags = _tag_names(git)
    for arg in (positional_and_refs(inv) if sub != "commit" else []):
        if _is_protected(arg):
            return f"{arg!r} is the release branch: only the owner touches it (D35)"
        if arg in tags or arg.startswith(("refs/tags/", "tags/")):
            return f"{arg!r} is a tag: tags are frozen (D35)"
    if sub in COMMITTING | {"pull", "cherry-pick", "revert", "am", "reset", "commit", "merge"}:
        if _is_protected(_current_branch(git)):
            return f"the current branch is {_current_branch(git)!r}: nothing is committed or merged there (D35)"
    return None


# The subcommands whose `-m`, `-c`, `-C`, `-F` take a message, a commit or a file; for the others they take a ref.
MESSAGE_SUBCOMMANDS = {"commit", "merge", "revert", "cherry-pick", "am", "tag", "stash", "notes"}
VALUE_OPTIONS = {"-m", "--message", "-F", "--file", "-C", "-c", "--author", "--date", "--reuse-message"}


def positional_and_refs(inv: Invocation) -> list[str]:
    """Every argument that could be a ref, including the two sides of `a..b`, `a...b` and `a:b` (not the value of -m and the like)."""

    found: list[str] = []
    skip = False
    for arg in inv.args:
        if skip:
            skip = False
            continue
        if arg in VALUE_OPTIONS and inv.sub in MESSAGE_SUBCOMMANDS:  # `-c` and `-m` name a branch for switch, checkout, branch, reset
            skip = True
            continue
        if arg.startswith("-") and arg != "-":
            continue
        for piece in re.split(r"\.\.\.?|:", arg):
            if piece:
                found.append(piece)
    return found


# --- git behind a wrapper ----------------------------------------------------------------------------------------

# Words that only pass the command along: `env git push`, `& git push`, `{ git push }`, `time git push`.
TRANSPARENT = {"env", "command", "exec", "nohup", "time", "sudo", "builtin", "nice", "&", "{", "}", "(", ")", "!", "then", "do", "else"}
MENTIONS_GIT = re.compile(r"(?<![A-Za-z0-9_])git(?![A-Za-z0-9_])", re.IGNORECASE)
POSIX_SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "csh", "tcsh", "busybox", "wsl"}
POWERSHELLS = {"powershell", "pwsh", "powershell_ise"}
# program -> the flags that make its next argument code (`-c`, `-e`); a script file or `-m module` is not a string it reads
INTERPRETER_CODE_FLAGS = {
    "python": {"-c"}, "python3": {"-c"}, "py": {"-c"}, "pypy": {"-c"}, "pypy3": {"-c"},
    "node": {"-e", "--eval", "-p", "--print"}, "nodejs": {"-e", "--eval", "-p", "--print"}, "bun": {"-e", "--eval", "-p", "--print"},
    "deno": {"eval"}, "perl": {"-e", "-E"}, "ruby": {"-e"}, "php": {"-r"},
}
# Programs that run what they are given whatever the flags: any mention of git in them is a wrapper.
ALWAYS_WRAPPERS = {
    "eval", "iex", "invoke-expression", "invoke-command", "icm", "start-process", "saps", "start-job", "sajb",
    "foreach-object", "foreach", "%", "where-object", "xargs", "ssh", "wsl", "watch",
}


def _strip_prefixes(tokens: list[str]) -> list[str]:
    """The command a segment runs, after the words that only pass it along and a PowerShell `$result =`."""

    index = 0
    while index < len(tokens):
        token = tokens[index].lower()
        previous = tokens[index - 1].lower() if index else ""
        if token in TRANSPARENT or (token.startswith("-") and previous in ("env", "sudo", "nice", "time")):
            index += 1
        elif token.startswith("$") and tokens[index + 1 : index + 2] in (["="], ["+="]):  # `$out = git push ...`
            index += 2
        elif len(token) > 1 and token[0] in "({" and token.lstrip("({"):  # `(git status)`, `{git push}`
            tokens = [*tokens[:index], tokens[index].lstrip("({"), *tokens[index + 1 :]]
        else:
            break
    rest = tokens[index:]
    while rest and rest[-1] in (")", "}"):
        rest = rest[:-1]
    if len(rest) > 1 and rest[-1].endswith((")", "}")) and index < len(tokens):
        rest[-1] = rest[-1].rstrip(")}") or rest[-1]
    return rest


def _substitutions(tokens: list[str]) -> list[list[str]]:
    """The commands inside `$(...)` and backticks of a segment, quoted or not: the shell runs them, so the guard reads them too."""

    found: list[list[str]] = []
    for index, token in enumerate(tokens):
        for marker, closer in (("$(", ")"), ("`", "`")):
            if marker in token:
                text = " ".join([token.split(marker, 1)[1], *tokens[index + 1 :]]).split(closer)[0]
                found.extend(segments(text))
    return found


def _wrapper_problem(tokens: list[str], command: str) -> str | None:
    """A program that carries a string the parser cannot read, with git in it; or a program name built at run time."""

    rest = _strip_prefixes(tokens)
    while rest and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", rest[0]):
        rest = rest[1:]
    if not rest:
        return None
    program, args = program_name(rest[0]), rest[1:]
    flags = [arg.lower() for arg in args]
    carries_git = any(MENTIONS_GIT.search(arg) for arg in args)
    wrapped = None
    if program in POSIX_SHELLS and carries_git and any(re.fullmatch(r"-[a-z]*c[a-z]*", flag) for flag in flags):
        wrapped = f"{program} -c"
    elif program == "cmd" and carries_git and any(flag in ("/c", "/k", "/r") for flag in flags):
        wrapped = "cmd /c"
    elif program in POWERSHELLS:
        if any(re.fullmatch(r"-e(c|nc|ncodedcommand)?", flag) for flag in flags):
            return f"{program} -EncodedCommand hides the command from the guard (D35)"
        if carries_git and "-file" not in flags:
            wrapped = f"{program} -Command"
    elif program in INTERPRETER_CODE_FLAGS and carries_git and set(flags) & INTERPRETER_CODE_FLAGS[program]:
        wrapped = f"{program} {sorted(set(flags) & INTERPRETER_CODE_FLAGS[program])[0]}"
    elif program in ALWAYS_WRAPPERS and carries_git:
        wrapped = program
    elif program == "find" and carries_git and set(flags) & {"-exec", "-execdir", "-ok", "-okdir"}:
        wrapped = "find -exec"
    if wrapped:
        return f"git inside {wrapped} cannot be read by the guard: run git directly (D35)"
    if re.search(r"^\$|\$\(|`", rest[0]) and rest[1:2] != ["="] and MENTIONS_GIT.search(command):
        return "a command word built at run time next to git cannot be read by the guard: run git directly (D35)"
    return None


def decide(command: str, git: GitRunner = run_git) -> str | None:
    """None if the command may run, else the reason it is blocked."""

    pending = segments(command)
    while pending:
        tokens = pending.pop(0)
        pending.extend(_substitutions(tokens))
        wrapped = _wrapper_problem(tokens, command)
        if wrapped:
            return wrapped
        inv = Invocation(_strip_prefixes(tokens))
        if not inv.is_git or not inv.sub:
            continue
        problem = _problem(inv, git)
        if problem:
            return problem
    return None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    command = (event.get("tool_input") or {}).get("command") if isinstance(event, dict) else None
    if not isinstance(command, str):
        return 0
    reason = decide(command)
    if reason:
        print(f"Blocked by .claude/hooks/git_guard.py: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
