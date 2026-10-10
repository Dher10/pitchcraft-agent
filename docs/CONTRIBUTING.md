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
- **Body (enforced: at least one line):** explain the why, not a list of files. Name the root cause for fixes. Mention anything deliberately left out.
- **Verification line (expected):** end with what was run and its result, e.g. `pytest 24/24, ruff clean, next build green`.
- **Language:** English.

### Example

```
fix: stop demo recent form leaking into live starters

_apply_live_starter overwrote name, pitch mix and season stats with live
data but kept recent_form and bio from the demo inputs, so the Matchup
Analyst could describe a real pitcher's form using another pitcher's demo
label. Live starters now take recent form from real data or mark it as
unavailable.

Covers the "Live starters carry no demo fields" scenario in PLAN.md.

pytest 12/12, next build green.
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
