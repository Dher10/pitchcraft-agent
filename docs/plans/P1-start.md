# P1-start — opening of Phase 1 (owner's message, 2026-10-21)

Approved by the owner sending it. D35 applies: commit and push without asking when the full verification passes, the reviewer returns PASS and the previous CI is green. The message pre-approves the `DECISIONS.md` and workflow changes listed below, nothing else. No QA is run in this session.

## a. Docs: close Phase 0 and record D41

Tick P0.10 in `docs/PLAN.md` (Phase 0 closed: run 6 PASS WITH CONDITIONS, conditions met in `docs/qa/QA-phase-0-2026-10-21-conditions.md`). Add D41 to `docs/DECISIONS.md` (2026-10-21, owner):

- Scope of v2.0-a applies D18's cut order: no automated postgame in P1.2; P1.5 is series context only (no draft, debut or birthplace). P1.3, P1.4 and P1.7 move after the release; P1.6 and P1.8 are built during the World Series and must be live before its last possible game (Oct 31). No fixed target game: the site shows whatever the schedule has on the day it goes live.
- Release model: `v2` is the workshop, `main` is what Vercel publishes; the owner merges `v2` into `main` when the Phase 1 gate passes. The Kaggle version stays in the protected tag `v1.0.0-kaggle`.
- D15's bot writes to `main` through a write deploy key, added as the only bypass of the `main` ruleset, whose private key lives only as a secret of a GitHub environment restricted to the `main` branch. No admin bypass.
- Phase 1 gate: Codex runs `QA_PROTOCOL` focused on the range since Phase 0 closed (`794b063..HEAD`); any Blocker or High is a FAIL.

Mark D18 "Closed; applied by D41".

## b. P1.1 probe

A workflow `.github/workflows/statcast-probe.yml` that runs on push to `v2` only when that file changes (`workflow_dispatch` needs the file on the default branch, so it cannot be triggered from `v2` otherwise). `permissions: contents: read`; actions pinned by SHA; `ubuntu-24.04`. It makes exactly one small Baseball Savant request (one pitcher, a few days of the 2026 postseason) and one MLB Stats API schedule request, prints HTTP status, row count and elapsed time, never prints bodies or secrets, commits nothing. Report the run result with its link. If Savant is blocked, stop: the owner chose the fallback (fetch on the owner's PC, Actions builds from the committed cache), which needs its own plan.

## c. The "Final" bug

`fetch_series_status` and `games_today` treat `abstractGameState` "Final" as a finished game, but postponed and cancelled games also arrive as "Final" (D40). Use the same `GAME_STATUS` mapping as D40; a postponed or cancelled game never counts as played in a series standing. Red tests first (a series with a postponed game, a `games_today` with a cancelled one), sweep for other readers of `abstractGameState`.

## d. Plan for the rest of the reduced Phase 1

Draft `docs/plans/P1.md`: P1.0 (including what covers `gh` and the REST API); P1.2 daily job without postgame, with a dry-run mode testable on `v2` and real publishing only from `main` through the environment deploy key; P1.5 series context; P1.9 attribution; P1.6; P1.8; P1.10 at release; the release steps the owner runs (disable the `main` ruleset, merge, re-enable, enable Analytics). Include the exact GitHub steps the owner must do for the deploy key and environment, but do not generate or store any key. Commit the plan as docs and stop: the owner approves it before any of it is built.

## Report at the end

Commits, CI links, the probe result, and anything recorded instead of fixed.
