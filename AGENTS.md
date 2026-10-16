<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# PitchCraft — instructions for any coding agent

These rules apply to every agent working in this repo (Claude Code, Codex or any other). `CLAUDE.md` imports this file, so there is one set of rules for all tools.

## Read before doing anything

1. `docs/STATUS.md` — where the last session stopped and the exact next task.
2. `docs/PLAN.md` — phases, tasks and acceptance criteria.
3. `docs/DECISIONS.md` — decisions already made. Read the ones related to your task.
4. `docs/PRD_v2.md` and `docs/eval-spec.md` — only the sections your task touches.
5. `docs/DATA_CONTRACT.md` — what the published data and every text that describes it may say (D34). Read it before changing any field, sentence, error or label that reaches the public file or the page.
6. `docs/ENGINEERING.md` — how code is written here (validate at the boundary, decide on raw values, red tests first, invariants, fixtures, fix the class, self-review). Read it before coding.

Exception: an agent that runs `docs/QA_PROTOCOL.md` does not read `docs/STATUS.md` at the start. The protocol's own reading order applies, and STATUS is read only after the agent has formed its own findings.

Do not start coding until you can state, in one sentence, which `PLAN.md` task you are working on.

## Source of truth

- This repo is the source of truth for the product: PRD, eval spec, decisions, plan and status.
- A Notion mirror exists for the owner. Agents never treat Notion as authoritative and never need to read it.
- If anything in the code contradicts `docs/DECISIONS.md`, the decision wins. Report the conflict; do not silently "fix" the decision.

## How to work

- Start every task in plan mode (or the tool's equivalent): show the plan and the files you will touch, then wait for approval.
- One task at a time, from `PLAN.md`, in order unless the owner says otherwise.
- Keep changes scoped to the task. No drive-by refactors.
- Python pipeline lives in `agents/` and `data_pipeline/`. Frontend in `app/`, `components/`, `lib/`.
- Use only public MLB data. Never add data from any employer or private source.
- Never hardcode user-facing strings in the agents; language is a parameter (decision D6).
- Never present demo data as live (decision D1 and Phase 0).

## Autonomy lanes (D22)

Each task in `PLAN.md` is labelled `[auto]` or `[gated]`; unlabelled tasks are gated.

- `[gated]`: show the plan, wait for approval, and get an explicit yes before each commit (D20).
- `[auto]`: show the plan and wait for approval once. Then implement, run the tests, commit and push to `v2` without asking, and continue with the next `[auto]` task in order. Report each finished task in `STATUS.md`.
- In the auto lane, stop and ask the owner if: any test fails and the fix is not obvious, CI goes red, the task conflicts with `DECISIONS.md`, or it requires touching `DECISIONS.md`, `.github/workflows/`, secrets or `main`. Stop when the next task is `[gated]`.
- Identity, format, branch and history rules apply in both lanes. The commit-msg hook still runs.

## Agency workflow (D35)

One writer at a time. The owner approves each task plan (`docs/plans/`) and each phase-end QA. Inside an approved plan, D35 replaces the per-commit approval of D20; outside one (no approved plan, or the fallback below) the rules of "Git rules" hold as written.

**The cycle.** Explore and plan in plan mode. The approved plan, with the owner's adjustments, is saved in `docs/plans/<task>.md` and committed with its task (`docs/CONTRIBUTING.md`). Then, for each commit of the plan:

1. Red tests first, seen failing; controls named.
2. Implementation.
3. The full verification, in the default terminal: `python -m pytest`, `npm test`, `npx tsc --noEmit`, `npm run lint`, `npm run build`.
4. The reviewer subagent (`.claude/agents/reviewer.md`): it runs in a clean context, gets the task, the plan and the range of the diff, never your reasoning, and returns PASS or BLOCK with findings.
5. Filter the findings: fix those that affect correctness, the contract or the plan; record in `docs/status-archive.md` why you reject any other. At most two review rounds; without PASS after the second, stop and ask the owner.
6. Commit, push to `v2`, and wait for the CI of that commit to be green before the next commit.

You commit and push without asking only when all three hold: the full verification passes, the reviewer returned PASS, and the CI of the previous commit is green.

**Stop and ask the owner** on: a new decision or a new schema version; any change to `docs/DECISIONS.md` or `.github/workflows/`; fan-visible text that is not in the plan; a finding that changes the scope; CI red twice in a row; two review rounds without PASS.

**Git safety is a hook, not a promise.** `.claude/hooks/git_guard.py`, wired in `.claude/settings.json` (PreToolUse on Bash) and tested in `tests/test_agent_git_guard.py`, blocks: a push to any branch other than `v2` or `experiment/*`; any operation on `main` or on a tag; `--force`, `--force-with-lease`, `rebase`, `reset --hard`, `--no-verify`; `commit --amend` on something already pushed; a commit whose identity is not Daniel Herdenez <edherdenez@gmail.com>.

**Fallback.** If Codex continues a task, it follows the same plan and this file, and every commit needs the owner's yes; the phase-end QA is then done by a fresh session of the other tool. Isolated experiments may use their own branch (`experiment/*`) with their own files, never `main`, and the implementing session integrates them.

**Habits.**

- To read a lot of code, use Explore subagents: they return the conclusion, not the files.
- State a result only with the command that produced it: show the output, and do not report the result of a different command or environment as if it were the default one.
- When you close a task, write in `docs/STATUS.md` a summary of about 10 lines: the commits with their hash, what they closed, what changed for the fan, the table entries and `xfail`s removed, and the next task you propose.

## After EVERY finished task (not at the end of the session)

Sessions can end abruptly when tokens run out. Update the handoff after each task:

1. Tick the task's checkbox in `docs/PLAN.md`.
2. Update `docs/STATUS.md`: what you finished, the next task, anything half-done or blocked.
3. Prepare the commit (see Git rules) and ask the owner for approval before running it (inside an approved plan, D35 applies: see "Agency workflow").
4. If the task changed the product's behavior or an assumption, add a line to the "Pending Notion sync" list in `STATUS.md`.

## Changing a decision

- Never edit or delete an existing decision in `DECISIONS.md`.
- If a task requires changing a decision, stop and ask the owner.
- Once approved: append a new decision, mark the old one as `Superseded by Dxx`, and note it in `STATUS.md`.

## Git rules

Full rules in `docs/CONTRIBUTING.md`. Read it before your first commit.

- Before the first commit of a session, run and show `git config user.name`, `git config user.email`, `git branch --show-current` and `git remote -v`. Stop if the email is not `edherdenez@gmail.com` or the branch is not `v2`.
- You may run `git add -A`, `git commit` and `git push origin v2` only after showing the owner the changed files and the full commit message and getting an explicit yes (D20). Inside an approved plan, D35 replaces this yes with the three conditions of "Agency workflow".
- Never touch `main`, merge into `main`, force push, rebase, reset, rewrite history, or create/move/delete tags. The tag `v1.0.0-kaggle` is frozen. Merging `v2` into `main` is the owner's release step.
- Only the GitHub Actions bot may commit to `main`, and only under `public/data/` and `evals/live/` (D15).
- Commit format: `type: lowercase imperative summary`, a body with what and why (root cause for fixes), and a verification line. No `Co-Authored-By` or any AI attribution. The `commit-msg` hook enforces identity, format and no attribution; never bypass it with `--no-verify`.
- Staging is always complete: `git add -A` or whole files. Never `git add -p`.
- One task = one commit.
- Never commit from a cloud agent session; only from local tools on the owner's machine.

## Security rules

- Never commit secrets. API keys live in env vars locally and in GitHub Secrets in CI; never print them in logs.
- Workflows declare least-privilege `permissions` and pin third-party actions by commit SHA.
- LLM output is schema-validated before it reaches any public file. Free-text data passed to a model is quoted data, never instructions.
- Never use `dangerouslySetInnerHTML` in the frontend.
- Data use stays non-commercial, attributed, cached and non-bulk (D16).

## Definition of done

A task is done only when its acceptance criteria in `PLAN.md` pass. For Phase 0, the Gherkin scenarios in `PLAN.md` are the criteria; each one needs an automated test or a documented manual check in `STATUS.md`.

A change is also done only when it complies with `docs/DATA_CONTRACT.md` (any new or changed field, scope, sentence, error or label follows its rules and its registry of claims) and the self-review of `docs/ENGINEERING.md` was done before the commit was shown.
