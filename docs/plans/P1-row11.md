# P1 row 11: P1.10 Web Analytics (D26)

Plan of record: `docs/plans/P1.md` section 9 (approved 2026-10-21). `[auto]` in `docs/PLAN.md`.

Written for: the owner and the reviewer.

## What changes

1. `@vercel/analytics` 2.0.1 by `npm install --save-exact`, lockfile committed (published 2026-10-02; no dependencies, no install scripts, peer dependencies all optional; `npm audit --omit=dev` stays 0). The Next.js 16 docs in `node_modules/next/dist/docs/` were read for the page and layout conventions; the package's Next.js entry is `@vercel/analytics/next`.
2. `app/layout.tsx` renders `<Analytics />` once, inside the body, with no props: page views only, no custom event, no cookie banner (D26).
3. `app/quality/page.tsx`: a bare `<main aria-label="Quality" />`. It draws no visible text; what it shows is P3.2's, and no wording is added before it.
4. Tests (`components/__tests__/Analytics.test.tsx`, `lib/__tests__/noAdsOrTrackers.test.ts`): the layout renders the component once inside the body; the route exists and draws no text; the layout sends no event and adds no other script; the package is pinned exactly and imported only by the root layout.

## Not here

Enabling Web Analytics in the Vercel dashboard (the owner's step R5, after the merge, D26). Nothing is sent from a branch that Vercel does not serve as production.

## Requests

None.
