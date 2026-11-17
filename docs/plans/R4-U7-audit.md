# R4-U7 audit fixes: Codex audit of PR #6 (head `f3aea88`)

Approved by the owner's message of 2026-11-17 ("merge after fixes"). Fix all five findings on `v2`, red test first for each, one commit per finding or per related pair; add each fix under 2.1.0 in `CHANGELOG.md`; reviewer PASS, the five suites, green CI; update `PR_BODY.md`. Do not touch the PR, tags or `main`.

1. **Blocker, CSP blocks the team filter** without JavaScript (`form-action 'none'`). Owner's decision: `form-action 'self'`, nothing else in the policy; record it in `docs/SECURITY.md`. Red test: the header lacks `form-action 'self'`. Browser proof against the production build with JavaScript off: submitting MIL shows only MIL games, no CSP violation. The repo's browser tooling is Playwright (`scripts/check_security_headers.mjs`, Oct 28), so the proof is an opt-in script, `scripts/check_release_b_browser.mjs`, with no new dependency and no CI change.
2. **Targets under 44 px at 375 px:** series links (`components/home/SeriesBoardView.tsx`) and calendar day links (`components/archive/Calendar.tsx`): at least 44x44, no overlap, no sideways scroll at 375 px. Remove limitation 6 from the PR text.
3. **Footer links and desktop game links** (`components/site/SiteFooter.tsx`, `components/archive/ResultsTable.tsx`): clickable area at least 44 px tall, plain-link look kept.
   For 2 and 3, a measured check at 375, 430 and 1280 px that fails if any interactive element on the release B pages is under 44x44; any exception is asked for before it is kept.
4. **Empty index** crashes `calendarMonth()` (`components/archive/ArchiveView.tsx`, `lib/archiveQuery.ts`): handle it before the mode line and calendar, with an empty-state text from `docs/plans/R4-U.md` section 5 (if none fits, propose one and stop). Red regression test with an empty index.
5. **Game 404 without JavaScript** (`app/game/[gamePk]/page.tsx`, `not-found.tsx`): the heading and links appear only after hydration. Render the not-found content on the server; test the real route with JavaScript off against the production build.

**Owner's decision on item 5 (2026-11-17): option D.** No change to `proxy.ts` or the build in 2.1.0; listed as a known limitation in the PR text and recorded in `docs/STATUS.md` as the first item for 2.1.1 with the findings and two candidate fixes.
