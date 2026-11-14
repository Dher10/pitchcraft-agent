# Independent R4 data audit — 2026-11-14

Base `7bbbd27`; audited `197bcac..7bbbd27`, including the identity code at
`197bcac`. Read-only first: three independently scoped audit agents plus the
implementing session's boundary tracing. No MLB/Savant requests, production data
writes, or release. References below are lines at the audited head.

| ID | Rating | Location | Finding and evidence | Fix group |
| --- | --- | --- | --- | --- |
| A1 | blocker | `data_pipeline/archive_games.py:551` | Envelope date/teams/cutoff/live origin are independent of the report. Changing the real fixture's envelope date to Oct 30, away team, or publication time to after first pitch still passes envelope and finalizer. | 1 |
| A2 | blocker | `data_pipeline/archive_finalize.py:82`, `archive_build.py:162`, `scripts/publish_archive.py:79` | Rewritten legacy report text retains the claimed source SHA and passes; resume trusts it and publisher permits overwriting. Compare resumed values and source to recovered committed reports; refuse changed payloads already published. | 1 + 2 |
| A3 | should-fix | `data_pipeline/archive_games.py:575` | Unrelated starter-fact IDs produce veteran tags; `started` with no actual starter passes. Bind facts and confirmation to report IDs. | 1 |
| A4 | blocker | `data_pipeline/archive_build.py:395`, `archive_history.py:214` | `--history-dir` bypasses the resolved protected-path guard and can write raw responses under `public/data/` or `evals/live/`. | 1 |
| A5 | should-fix | `data_pipeline/archive_build.py:101` | Exhausted Savant ledger rejects a zero-request pitcher-cache hit before consulting the cache. Enforce the limit at transport while allowing free reads. | 1 |
| A6 | should-fix | `data_pipeline/archive_build.py:162` | Envelope-only resume accepts `payload={}`; finalization then blocks instead of rebuilding. Reuse full origin-aware validation. | 1 |
| A7 | should-fix | `data_pipeline/archive_history.py:202` | Matching digest does not bind a cached response to the requested pitcher/season URL. A pitcher-11 record copied under pitcher 22 is accepted. | 1 |
| A8 | should-fix | `data_pipeline/archive_build.py:414`, `.github/workflows/archive-backfill.yml:124` | One isolated game failure exits nonzero, skipping publication of all valid neighbors, contrary to D66. Separate fatal run failures from isolated game failures in the CLI. No workflow edit required. | 2 |
| A9 | should-fix | `data_pipeline/archive_finalize.py:129` | Unchanged reruns change only manifest time and create another data commit. Preserve a matching existing manifest. | 2 |
| A10 | should-fix | `scripts/publish_archive.py:99` | Destination symlinks/junctions are followed before the Git allowlist check. A tracked directory link can direct game writes outside the checkout. Analytical finding; reproduce in temporary filesystem before fixing. | 2 |
| A11 | should-fix | `data_pipeline/archive_index.py:289` | Manifest count types are checked but derivations are not: counts 999/999 pass with a sound unchanged index. | 2 |
| G1 | blocker (task 2) | `data_pipeline/archive_build.py:263` | Parser mismatch and rejected final-line fields stop only the dry-run reporter, not real publication. Implement the owner's required run-wide guard separately. | guard |

Checks without additional findings: unique published matching; final-only scores
and postponed/suspended exclusion; pregame pitch and game-log cutoff filtering
(no row on/after the game date), regular-season lineup scope; measured zeros and
nulls; missing labels/limited samples do not make tags; separate HTTP budgets and
ceiling exceptions escape broad catches; candidate extras and hashes; reconstructed
payload validation; dirty checkout/branch/dropped-file checks; owner identity and
nonforced push; manual-only workflow, SHA-pinned actions, read-only token,
deploy key only in the publish environment, private key file and cleanup.

Expected nonpublic writes are candidate output, temporary pipeline files, raw
diagnostics and caches. The publisher's only allowed destination is the archive.
History URL and published-history inputs remain trusted source boundaries; the
raw committed blob hash is never recomputed from compact reserialization.

## Verification and disposition

Group 1: A1, A3-A7 and the resume half of A2 fixed. New regression tests:
16 failed before implementation, one valid-published control passed. Existing
synthetic fixtures corrected where they contradicted report identity. Full
default-terminal checks in order: pytest 6372 passed / 2 skipped, npm 296 passed,
tsc/lint/default Turbopack build exit 0. Independent reviewer PASS, round 1. Group 2 and
G1 remain open. No existing decision changed; no tolerance, skip or xfail added.
