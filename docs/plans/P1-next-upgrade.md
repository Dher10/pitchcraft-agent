# P1 scope addition: Next.js 16.4.0 to 16.4.1

Approved by the owner on 2026-10-22 (scope addition to `docs/plans/P1.md`, one commit before row 5).

Written for: the owner and the reviewer.

## Why

16.4.1 is the patch release of the Next.js security update of 2026-10-14: two critical unauthenticated RCE advisories (GHSA-673q-mjm6-r5xr, `use cache` returning typed arrays; GHSA-2464-fhr4-w9xw, Image Optimization API with SVG) and one high (GHSA-p3m5-59mp-jv5r, Server Actions DoS). The release notes list no breaking change and no manual step. The site uses none of the affected features as far as the code shows, but the version is the one the owner chose to run. The build of 16.4.0 also exited 1 intermittently on the advisory lookup (`SecurityFatalError`, STATUS row 3).

## What

- `npm install --save-exact next@16.4.1 eslint-config-next@16.4.1` (the matching version exists). No `next upgrade`, no command suggested by tool output (`npm audit fix --force`, `npm install-scripts approve` were not run).
- `package.json` and `package-lock.json` only. The lockfile diff is the `next` family and its `@next/swc-*` binaries.
- 16.4.2 exists (2026-10-15); the owner approved 16.4.1, so 16.4.1 is what is installed. Reported, not taken.

## Verification (D35)

Full verification in the default terminal; `npm run build` three times, with the exit code of each, to see whether the intermittent `SecurityFatalError` is gone. The audit line of `STATUS.md` is updated.

## Not in scope

Any code change, any change to `.github/workflows/`, the Vitest advisories that appeared after the last audit.
