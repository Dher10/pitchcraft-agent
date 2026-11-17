# R4-V: app versioning before the release B merge (D68)

Approved by the owner's message of 2026-11-17. PR #6 (`v2` to `main`) is open; this commit updates it. Agents create no tags and do not touch the PR.

1. `docs/DECISIONS.md`: D68. SemVer adapted to a product (MAJOR when the product changes shape, MINOR for new pages, features or a visual identity change, PATCH for fixes). Every merge of code into `main` is a release with a tag `vX.Y.Z` that the owner creates; bot data commits carry no version; `schema_version` and `archive_version` stay independent. The tags `v1.0.0-kaggle` and `v2.0-a` stay as history. Release B is v2.1.0. Supersedes the release names of D10 and D65 (`v2.0-b`; `v2.1` for Spanish). `PLAN.md`, `STATUS.md`, `PRD_v2.md` and the plans use the new names.
2. Red test first: `lib/__tests__/version.test.ts` fails unless `package.json` (and the lock, twice) carry the version of the newest `CHANGELOG.md` entry. Seen failing, then both files set to 2.1.0.
3. `CHANGELOG.md` (Keep a Changelog): 2.1.0 (Unreleased until the owner merges), 2.0-a, 1.0.0, from facts in the repo only.
4. `docs/releases/v2.1.0.md`: public release notes, title "v2.1.0 — Offseason experience", same shape as the v2.0-a release.
5. Outside the repo: `C:\Dev\release-b-screenshots\PR_BODY.md` regenerated as public text with "Version: 2.1.0"; owner-only material in `OWNER_NOTES.md`.
6. Reviewer PASS, the five suites one by one, commit and push to `v2`, wait for green CI.

**Note on scope.** The owner's message lists PRs #2, #3, #4 and #6 for v2.1.0. The tag `v2.0-a` is the merge commit of PR #2 (`6c40f58`), so #2 is in 2.0-a; 2.1.0 covers #3, #4 and #6 (and #5, the sync merge of `main` into `v2`).
