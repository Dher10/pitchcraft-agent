# PitchCraft v2 — Status / handoff

Updated by whichever agent finishes a task. Keep it short. Newest session on top.

## Current state

- **Phase:** Phase 0 not started. Planning closed on 2026-10-10.
- **Branch:** `v2` (D14). `main` serves v1.
- **Next task:** `PLAN.md` → P0.1 (remove demo `recent_form` and bio from live starters). Start in plan mode.
- **Blocked:** nothing.
- **Half-done:** nothing.

## Pending Notion sync

Changes made in the repo that the owner still needs mirrored to Notion:

- (none)

Last Notion sync: 2026-10-10, from the initial docs commit.

## Session log

### 2026-10-10 — Planning (Claude chat)

- Audited v1 code. Findings recorded in `PLAN.md` Phase 0: demo `recent_form`/bio leaking into live starters; count-based labels with duplicated logic; no sample thresholds; season-to-date fetches cause leakage for historical games; Critic does not read report text; name-split bug; silent fallback to demo.
- Verified MLB Stats API: player profile includes birth city/state/country, draft records (year, team, round, school) and MLB debut date; schedule includes series description, game number and series status. Past series status shows the final result, so it needs an `as_of` rebuild for historical cases.
- Created `PRD_v2.md`, `eval-spec.md`, `DECISIONS.md` (D1–D14), `PLAN.md`, this file and the new `AGENTS.md`.
