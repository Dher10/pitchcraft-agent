# External QA of PR #10 (release 2.2.0) — 2026-11-19

Two external checks of PR #10 before the owner's merge on 2026-11-19. This
record summarizes them; it does not replace the report of each tool.

| Check | Target | Result |
| --- | --- | --- |
| Codex audit | `de5577b` | Two findings, fixed or verified in `7c3ce0f` and `7c30a26`. |
| Antigravity QA | Vercel preview at `7c30a26` | 25 checks pass; verdict: ready for production. |

## Codex audit at `de5577b`

1. Filtered totals on the archive. The count for a filtered list must use the
   filtered total, not the archive-wide one. Handled in `7c3ce0f`: the test now
   asserts "Showing 1 to 10 of 13 games, newest first" and "Showing 11 to 13 of
   13 games, newest first" for `team=MIL&per=10`. It failed ("of 40") with the
   archive-wide total passed to `countRange` and passes on the real code (the
   break was not committed).
2. Hostile filter values and the router bootstrap. The bootstrap repeats the
   request URL. Verified in `7c30a26` on the default production build: the
   values are escaped (percent-encoded in JSON strings, `&` as `\u0026`), none
   is raw, no script runs and no CSP violation is logged in Chrome with
   JavaScript on. Recorded in `docs/SECURITY.md` ("Known limitations"), with the
   regression check `check_release_b_browser.mjs inject`, which fails against a
   server that reflects the query raw. `proxy.ts` and the routing are unchanged.
   Redirecting invalid or default filter parameters to their canonical URL is
   proposed for a later release and needs its own decision (see `docs/STATUS.md`).

## Antigravity QA on the Vercel preview at `7c30a26`

- Checks: 25, all pass, at 375, 430 and 1280 px.
- Console: zero errors from the site.
- Verdict: ready for production.
- Limit: it could not turn JavaScript off. That case is covered by the Codex
  audit and by `check_release_b_browser.mjs csp`, which runs with JavaScript
  off.

## Outcome

The owner merged PR #10 on 2026-11-19. Next: tag `v2.2.0` and the GitHub
release from `docs/releases/v2.2.0.md`, then `main` into `v2`.
