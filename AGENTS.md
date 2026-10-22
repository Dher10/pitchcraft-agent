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

**Git safety is a hook plus server-side rules, and each covers only what is written here.**

- **The hook** (`.claude/hooks/git_guard.py`, wired in `.claude/settings.json` as a PreToolUse hook on the **Bash and PowerShell tools**, tested in `tests/test_agent_git_guard.py`) reads plain `git` commands and `git` inside the wrappers it can see. It blocks: a push to any branch other than `v2` or `experiment/*`; any operation on `main` or on a tag; `--force`, `--force-with-lease`, `rebase`, `reset --hard`, `--no-verify`, `filter-branch`; deleting or renaming `v2` or `main`; `git remote add/set-url/remove/rename`; changing `core.hooksPath` (reading it, `git config --get core.hooksPath`, is allowed); `commit --amend` on something already pushed; a commit whose identity is not Daniel Herdenez <edherdenez@gmail.com>. It also blocks git behind a wrapper whose string it cannot read: `bash -c`, `sh -c`, `eval`, `powershell`/`pwsh -Command`, `cmd /c`, `python -c`, `node -e`, `Invoke-Expression`, `xargs`, `Start-Process`, `ForEach-Object` (whenever the string mentions git, gh or the GitHub API), `powershell -EncodedCommand`, and a command word built at run time (`x=git; $x push`). Run git directly, so the hook can read it.
- **The same hook covers `gh` and the GitHub API (P1.0).** It blocks: `gh api` with any method other than GET (`-X`/`--method`), with `-f`, `-F`, `--field`, `--raw-field` unless the method is an explicit GET, with `--input`, or on `graphql`; every `gh` family or verb that is not on its list of reads (`run list/view/watch/download`, `pr view/list/diff/checks/status`, `issue view/list/status`, `repo view/list`, `workflow list/view`, `auth status`, `cache list`, `api` GET, `status`, `search`; `gh auth status` with `--show-token` or `-t` is blocked: it prints the token), so `gh pr merge/create`, `gh repo delete/edit/deploy-key`, `gh secret`, `gh variable`, `gh ruleset`, `gh workflow run/enable/disable`, `gh run rerun/cancel/delete`, `gh release`, `gh label`, `gh auth token/refresh/logout/setup-git`, `gh extension`, `gh alias` and any `gh` command not yet listed are blocked; and `curl`, `wget`, `Invoke-RestMethod` and `Invoke-WebRequest` (and aliases) against api.github.com or uploads.github.com with a non-GET method, a body or credentials. `gh` and the API behind the wrappers above are blocked like git. Reads stay allowed because the D35 loop needs them (CI runs, a pull request, the rulesets through `gh api` GET).
- **What the hook does not see:** any other tool (an editor, an MCP server, a connector); a script file or a program that runs git on its own; a shell function or alias; a `gh` alias already stored in the owner's gh config, a git alias that runs gh (`git config alias.x '!gh ...'`), a GitHub API request whose URL or method is built at run time, `gh` or `git` inside a PowerShell script block or parentheses (`if (...) { gh pr merge 5 }`, `Write-Host (git push origin main)`), and behind a prefix that takes its own arguments (`timeout 5 gh ...`, `env -u X gh ...`, `sudo -u x gh ...`). A command word built at run time is blocked only when the command line also mentions git, gh or the GitHub API (`$g='gi'+'t'; & $g push` is not seen). The strongest protection against a missed pattern is the read-only token the owner sets as `GH_TOKEN` in the agent's terminal (`docs/plans/P1.md`, G6): `gh` then cannot write at all. It is a guard against an agent breaking the written rules, not a security boundary.
- **GitHub rulesets** protect `main` (no deletion, no force push, and changes only through a pull request with 0 approvals and merge method "Merge" only; there is no "Restrict updates" since 2026-10-21), `v2` (no deletion, no non-fast-forward) and the tag `v1.0.0-kaggle` (no deletion, no update) on the server, whatever the git client; they are only as strong as the admin rights of the token `gh` uses, which can edit them. A release is a pull request `v2` → `main` merged by the owner in the GitHub UI, with no ruleset disabled (D42). The `main` ruleset has no bypass actor today; the deploy key of the daily job (D41) is added as the only one, once, by the owner, before the first daily run (`docs/plans/P1.md`, G7). The daily job's commits use the owner's identity (D42).
- **The other lines** are the `commit-msg` hook (identity, format, no attribution), CI, and the permission prompts of the tool.

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
