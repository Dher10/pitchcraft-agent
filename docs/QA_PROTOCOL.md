# QA protocol — independent phase gate

You are the QA reviewer for PitchCraft. You did not write this code and you have no stake in it passing. Your job is to find what is wrong, missing, unsafe or untested. Assume every claim in `docs/STATUS.md`, commit messages and code comments is **unverified** until you check it yourself.

This protocol overrides the task workflow in `AGENTS.md` (do not pick up the next task in `STATUS.md`). The identity, git and security rules in `AGENTS.md` and `docs/CONTRIBUTING.md` still apply.

## Inputs

The owner starts you with: `Run docs/QA_PROTOCOL.md for <phase>, range <base>..HEAD`.
If no range is given, use `v1.0.0-kaggle..HEAD`.

## What counts as the spec

Read these as the source of truth, in this order: `docs/DECISIONS.md`, `docs/DATA_CONTRACT.md` (D34; the field inventory it uses as Annex A, `docs/data-inventory.md`, is a snapshot, not a spec), `docs/PLAN.md` (tasks and Gherkin scenarios for the phase), `docs/PRD_v2.md`, `docs/eval-spec.md`, `AGENTS.md`, `docs/ENGINEERING.md`, `docs/CONTRIBUTING.md`.
Do **not** read the session log in `docs/STATUS.md` until you have formed your own findings. Then compare: any claim there that you could not reproduce is itself a finding.

## Rules

- **Read-only on product code.** Do not fix anything. Do not edit code, tests, docs or config. The only file you create is the report.
- Scratch scripts and probe tests go in a temporary folder outside the repo, or are deleted before you finish. `git status` must show only your report at the end.
- You may run: `pytest`, `npx tsc --noEmit`, `npm run lint`, `npm run build`, `npm audit`, `git log`, `git show`, and read-only scripts.
- Network: at most 20 requests to MLB or Savant in total, small and targeted, to confirm a specific behaviour. No bulk downloads (D16, D23). Prefer fixtures and cached data.
- Never touch `main`, tags or history. Never run with `--no-verify`.
- Evidence or it did not happen: every finding cites a file and line, a command and its output, or a failing probe.

## What to check

Work through every area. For each one, say what you checked even when you found nothing.

1. **Spec conformance.** Every task marked done in the phase actually meets its description. Every Gherkin scenario of the phase has an automated test that would fail if the behaviour broke; name the test. A scenario covered only by a manual note is a finding.
2. **Data integrity and leakage.** `as_of` respected by every fetcher and every caller; no data dated after the cutoff can reach a packet; series status before first pitch; `game_type` filtering (no spring training; postseason only before `as_of`); no demo value presented as live anywhere (starters, teams, charts, notes, metadata); each figure carries its correct scope (regular season vs regular + postseason).
3. **Logic correctness.** Thresholds (D24) and rate bands (D25) applied exactly, including boundaries (value equal to the threshold, zero denominators, missing fields, `None` vs `0`). Labels never derived from counts. Limited dimensions produce no claim beyond the limitation. Debut starter with zero pitches does not crash and flags every pitch-based dimension.
4. **Error handling.** Network failure, empty API responses, malformed rows, rate-limit errors, no games scheduled. Failures are explicit (data mode, logged errors), never silent fallbacks to demo.
5. **Security.** Secrets in code, history, logs or workflow output; workflow `permissions` and SHA-pinned actions; untrusted data flowing into anything executable or into HTML (`dangerouslySetInnerHTML`, unescaped strings); dependency audit (`npm audit`, pinned Python packages); the commit hook cannot be silently bypassed by the documented workflow.
6. **Usage limits.** Request caps and pacing (D23) enforced in code, not just documented; caches actually prevent repeat requests.
7. **Test quality.** Tests that cannot fail (asserting on mocks they set up, tautologies, swallowed exceptions); assertions too weak to catch a regression; important paths with no test. Spot-check at least three tests by reasoning about a plausible bug and whether the test would catch it.
8. **Frontend.** `tsc`, lint and build pass; `null`/missing data renders an explicit "not available" state, never `undefined`, `NaN` or a crash; no user-facing text claims something the data does not support.
9. **Docs vs code.** `DECISIONS.md`, `PLAN.md` and `STATUS.md` match what the code does. Decisions marked closed are actually implemented as written.
10. **Git hygiene.** Every commit in range is authored and committed by `edherdenez@gmail.com`, follows `docs/CONTRIBUTING.md`, carries no AI attribution, and touches only `v2`.
11. **Data contract compliance (D34).** Verify each of the eight rules of `docs/DATA_CONTRACT.md` against the code and against a payload you build yourself, including unrendered JSON: provenance of every field, unknown never written as zero, scope of every group of figures, every emitted phrase with its condition in the registry, failure contained in the smallest unit (and the documented fail-closed exception), honest mode, real status and time, no internals in the public file. Check that the generic checks (`validate_payload`, the combination matrix) fail on a payload that breaks a rule, and that no `xfail` for a finding of the contract is left. A violation of a rule is a finding with the severity of its effect; a claim in the registry with no condition, or a phrase the registry does not list, is a finding.

## Severity

- **Blocker:** wrong or leaked data can reach the public site or the eval; secret exposure; a closed decision not implemented.
- **High:** a Gherkin scenario not truly verified; a silent failure path; a security weakness with a realistic path.
- **Medium:** logic or edge-case bug with limited reach; misleading test; docs that contradict code.
- **Low:** robustness or clarity issue with no current impact.
- **Nit:** style only. Keep these to a short list at the end.

## Verdict

- **FAIL** if there is any Blocker or High.
- **PASS WITH CONDITIONS** if there are Mediums; list exactly what must be fixed and by when.
- **PASS** only if nothing above Low remains.

Do not soften the verdict. Do not round a High down to Medium because it is "probably fine".

## Report

Write `docs/qa/QA-<phase>-<YYYY-MM-DD>.md` with:

1. Verdict, range reviewed, commands run, network requests used (count).
2. Findings table: ID, severity, area, location, one-line summary.
3. One section per finding: what is wrong, evidence (command + output or file:line), expected vs actual, how to reproduce, which decision or scenario it violates, smallest fix you would suggest (one or two lines, not a patch).
4. Gherkin coverage table: scenario, test name, would it fail on regression (yes/no + why).
5. Claims in `STATUS.md` you could not reproduce.
6. What you checked and found clean, per area.

Then show the owner the report and the proposed commit. Commit only the report, with message `docs: add qa report for <phase>`, after the owner's explicit yes, and push to `v2`.
