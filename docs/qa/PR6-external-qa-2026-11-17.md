# External QA of PR #6 (release 2.1.0) — 2026-11-17

Two external checks of PR #6 before the owner's merge on 2026-11-17. This record
summarizes them; it does not replace the reports of each tool.

| Check | Target | Result |
| --- | --- | --- |
| Codex audit | `f3aea88` | Five findings. Four fixed in PR #6; one deferred to 2.1.1 (`/game/<id>` 404 without JavaScript, recorded in `docs/STATUS.md` and `docs/plans/R4-U7-audit.md`). |
| Codex verification | `e2d16c1` | Verdict: merge. |
| Antigravity QA | Vercel preview of PR #6 | 8 checks pass at 375, 430 and 1280 px, with and without JavaScript. Verdict: ready for production. |

The four fixed findings are in three commits, `d553201`, `80aba6d` and `8cb1180` (one commit each or per pair; the mapping per finding is in `docs/STATUS.md`).
The deferred finding is recorded as a known limitation in `e2d16c1`.

Outcome: the owner merges PR #6 on 2026-11-17; `CHANGELOG.md` dates 2.1.0 the same day.
