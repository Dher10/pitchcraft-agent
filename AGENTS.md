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

## After EVERY finished task (not at the end of the session)

Sessions can end abruptly when tokens run out. Update the handoff after each task:

1. Tick the task's checkbox in `docs/PLAN.md`.
2. Update `docs/STATUS.md`: what you finished, the next task, anything half-done or blocked.
3. Propose a commit message (see below). The owner runs git.
4. If the task changed the product's behavior or an assumption, add a line to the "Pending Notion sync" list in `STATUS.md`.

## Changing a decision

- Never edit or delete an existing decision in `DECISIONS.md`.
- If a task requires changing a decision, stop and ask the owner.
- Once approved: append a new decision, mark the old one as `Superseded by Dxx`, and note it in `STATUS.md`.

## Git rules (the owner runs all git commands)

- All v2 work happens on branch `v2`. Never work on or merge into `main` (D14). The tag `v1.0.0-kaggle` is frozen.

- Do not run `git commit`, `git push` or any history-changing command. Propose the commands; the owner runs them in PowerShell.
- Staging is always complete: `git add -A` or whole files. Never `git add -p`, never manual hunk editing.
- Commit messages: imperative mood, prefix (`fix:`, `feat:`, `chore:`, `docs:`, `test:`), extended body explaining why.
- No `Co-Authored-By` lines.
- One commit per task.

## Definition of done

A task is done only when its acceptance criteria in `PLAN.md` pass. For Phase 0, the Gherkin scenarios in `PLAN.md` are the criteria; each one needs an automated test or a documented manual check in `STATUS.md`.
