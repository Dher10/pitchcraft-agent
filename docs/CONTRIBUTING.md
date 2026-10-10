# Contributing — commits, identity and git workflow

Applies to every commit in this repo, whoever writes it: the owner, Claude Code, Codex or any other agent. The `commit-msg` hook in `.githooks/` enforces the parts marked **(enforced)**.

## Identity (enforced)

- Every commit is authored and committed as **Daniel Herdenez `<edherdenez@gmail.com>`**.
- Commits are made only from local tools on the owner's machine (VS Code with Claude Code or Codex, or the terminal). Cloud agents (claude.ai/code, Codex cloud) never commit to this repo: they use their own identity.
- Before the first commit of a session, the agent runs and shows:
  ```
  git config user.name
  git config user.email
  git branch --show-current
  git remote -v
  ```
  and stops if the email is not the owner's or the branch is not `v2`.
- Exception: the GitHub Actions bot commits data under `public/data/` and `evals/live/` on `main` (D15). The hook does not run in CI.

## No AI attribution (enforced)

No `Co-Authored-By`, `Claude-Session`, "Generated with Claude Code" or any other tool trailer. The hook strips them; `.claude/settings.json` also turns them off in Claude Code.

## Message format

```
<type>: <lowercase imperative summary>

<Body. What changed and why. For fixes, the root cause and how it was
confirmed. Wrap around 72 characters. Several short paragraphs are fine.>

<Verification line: tests, lint, type check, build.>
```

- **Type (enforced):** `feat`, `fix`, `docs`, `chore`, `style`, `refactor`, `test`, `perf`, `ci`, `build`. Optional scope: `fix(pipeline): ...`.
- **Subject (enforced):** lowercase after the colon, imperative ("add", "fix", "remove"), no trailing period. Aim for under 72 characters.
- **Body (enforced: at least one line):** keep it short. At most two short paragraphs: (1) what was wrong or why the change is needed, with the root cause for fixes; (2) what changed, plus anything deliberately left pending. No file lists, no task bookkeeping (ticking PLAN.md or STATUS.md is implied).
- **Verification line (expected):** end with what was run and its result, e.g. `pytest 24/24, ruff clean, next build green`.
- **Language:** English.

### Example

```
fix: stop live team offense inheriting demo values

When a team had no real split, _apply_offense_split kept the demo
offense fields and record, and the analyst reported them as facts. A
missing field inside a real split also became "N/A", read as 0.0.

Unavailable offense fields are now None; the analyst skips offense
claims without OPS and the card shows a dash. Pending for P0.8:
game.broadcast_note still inherits demo text.

pytest 15/15, tsc and eslint clean, next build green.
```

## Workflow

- One task from `docs/PLAN.md` = one commit.
- Staging is always complete: `git add -A` or whole files. Never `git add -p` or hand-edited hunks.
- Agents may `git add -A`, `git commit` and `git push origin v2` **only after** showing the owner the changed files and the full message and getting an explicit yes (D20).
- Agents never: touch `main`, merge into `main`, force push, rebase, reset, rewrite history, or create/move/delete tags.
- Merging `v2` into `main` is the release and is done by the owner.

## One-time setup per clone

```
git config core.hooksPath .githooks
```

Check it is active with `git config core.hooksPath` (should print `.githooks`).
