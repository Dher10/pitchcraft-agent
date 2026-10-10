# PitchCraft v2 — Status / handoff

Updated by whichever agent finishes a task. Keep it short. Newest session on top.

## Current state

- **Phase:** Phase 0 in progress. S0 and P0.0 done.
- **Branch:** `v2` (D14). `main` serves v1.
- **Next task:** `PLAN.md` → P0.1 (remove demo `recent_form` and bio from live starters). Start in plan mode.
- **Blocked:** nothing.
- **Half-done:** the first GitHub Actions run of `tests.yml` has not been seen yet (check it after the P0.0 push; Python 3.14 on `setup-python` v5.6.0 is unverified).

## Pending Notion sync

Changes made in the repo that the owner still needs mirrored to Notion:

- (none)

Last Notion sync: 2026-10-10, from the initial docs commit.

## Session log

### 2026-10-10 — P0.0 test infrastructure (Claude Code)

- Added `requirements-dev.txt` (pytest 9.1.1), `pytest.ini`, `tests/` and `.github/workflows/tests.yml` (push to `v2` + manual; `contents: read`; actions pinned by SHA: checkout v4.2.2, setup-python v5.6.0; Python 3.14 as local).
- `tests/test_commit_msg_hook.py` (6 tests): valid message accepted; rejects no-prefix subject, no body, other author, other committer; strips `Co-Authored-By`. Mutation-checked on temporary copies of the hook (via `COMMIT_MSG_HOOK`): each mutation fails exactly its test; the real hook was not modified.
- `tests/test_demo_agents_smoke.py`: five agents over demo data in memory; asserts nothing under `public/data` or `data_cache` changes; does not import `live_pipeline` or `generate_demo_json`.
- Local run: 7 passed. `.gitattributes` already forces LF on `.githooks/*` (verified).
- No product behavior change; nothing to add to Pending Notion sync.

### 2026-10-10 — S0 setup (Claude Code)

- Created `.claude/settings.json` (attribution off, D21). Ran `git config core.hooksPath .githooks`.
- Removed the contradictory git lines from `AGENTS.md` (owner edit); D20 governs.
- Committed as `2147676` and pushed to `v2`. Post-commit check passed: author Daniel Herdenez, no attribution.

### 2026-10-10 — Git workflow (Claude chat)

- Found commit `564b5f7` authored as `Claude <noreply@anthropic.com>` with attribution trailers, made by a cloud session in July. Left in history (rewriting `main` and the tag is riskier than the issue).
- Added `docs/CONTRIBUTING.md`, `.githooks/commit-msg`, `.gitattributes` and `.claude/settings.json`. Decisions D20–D21.

### 2026-10-10 — Audit (Claude chat)

- Full history scan: no secrets in any commit or branch. `.env*` and `*.pem` ignored.
- `npm audit --omit=dev`: 1 critical (next), 4 high, 1 moderate; all fixed by Next 16.4.0. Practical exposure low (static site: no middleware, Server Actions or `next/image`), fixed anyway in P0.9.
- Stray `pitchcraftvisualpolish.bundle` committed in `5a8c5cc`; `pybaseball` unpinned; no test infrastructure.
- Added P0.0, P0.9, P1.0, P1.8, P1.9; reordered P0.4/P0.5; decisions D15–D19.

### 2026-10-10 — Planning (Claude chat)

- Audited v1 code. Findings recorded in `PLAN.md` Phase 0: demo `recent_form`/bio leaking into live starters; count-based labels with duplicated logic; no sample thresholds; season-to-date fetches cause leakage for historical games; Critic does not read report text; name-split bug; silent fallback to demo.
- Verified MLB Stats API: player profile includes birth city/state/country, draft records (year, team, round, school) and MLB debut date; schedule includes series description, game number and series status. Past series status shows the final result, so it needs an `as_of` rebuild for historical cases.
- Created `PRD_v2.md`, `eval-spec.md`, `DECISIONS.md` (D1–D14; D15–D19 added in the audit), `PLAN.md`, this file and the new `AGENTS.md`.
