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
| A6 | should-fix | `data_pipeline/archive_build.py:162,306` | Envelope-only resume accepts `payload={}`; a failed rebuild can also leave the rejected old file in the candidate. Reuse full validation and remove a rejected candidate before rebuilding. | 1 + 2 |
| A7 | should-fix | `data_pipeline/archive_history.py:202` | Matching digest does not bind a cached response to the requested pitcher/season URL. A pitcher-11 record copied under pitcher 22 is accepted. | 1 |
| A8 | should-fix | `data_pipeline/archive_build.py:414`, `.github/workflows/archive-backfill.yml:124` | One isolated game failure exits nonzero, skipping publication of all valid neighbors, contrary to D66. Separate fatal run failures from isolated game failures in the CLI. No workflow edit required. | 2 |
| A9 | should-fix | `data_pipeline/archive_finalize.py:129` | Unchanged reruns change only manifest time and create another data commit. Preserve a matching existing manifest. | 2 |
| A10 | should-fix | `scripts/publish_archive.py:99` | Destination symlinks/junctions are followed before the Git allowlist check. A tracked directory link can direct game writes outside the checkout. Analytical finding; reproduce in temporary filesystem before fixing. | 2 |
| A11 | should-fix | `data_pipeline/archive_index.py:289` | Manifest count types are checked but derivations are not: counts 999/999 pass with a sound unchanged index. | 2 |
| A12 | blocker | `data_pipeline/archive_build.py:87`, `data_pipeline/fetchers/live_pipeline.py:236,444` | Logical calls are charged, but urllib follows redirects. A real opener with fake transport made two sends for a 302 → 200 at ledger usage 1 / ceiling 1, for both MLB and Savant. Refuse redirects within archive enforcement. No real network used. | 2 |
| A13 | should-fix | `data_pipeline/archive_finalize.py:100` | Finalizer build lacks the builder's protected-directory guard and can write directly beneath bot-owned paths. Guard before inspecting/writing candidates. | 2 |
| A14 | should-fix | `data_pipeline/archive_build.py:399` | CLI accepts years and dates outside the approved 2026 postseason; D66 requires a new decision for later seasons. Refuse outside 2026-09-28..2026-10-31 before requests. | 2 |
| A15 | blocker | `data_pipeline/archive_build.py:139,306` (audited head) | A safe `--out` can contain a `games` directory junction; atomic writes then follow its parent outside the candidate, including potentially bot-owned paths. A real temporary Windows junction reproduced an escaped `outside/849805.json` before the fix. Reject linked/escaped game directories before any request or write, and in both finalizer actions. | guard follow-up |
| G1 | blocker (task 2) | `data_pipeline/archive_build.py:263` | Parser mismatch and rejected final-line fields stop only the dry-run reporter, not real publication. Implement the owner's required run-wide guard separately. | guard |

Checks without additional findings: unique published matching; final-only scores
and postponed/suspended exclusion; pregame pitch and game-log cutoff filtering
(no row on/after the game date), regular-season lineup scope; measured zeros and
nulls; missing labels/limited samples do not make tags; separate HTTP budgets and
ceiling exceptions escape broad catches (redirect gap A12 above); candidate extras and hashes; reconstructed
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

Group 2: 13 new tests seen failing before implementation; focused archive checks
then 171 passed. Fixed A2 publication half, A6 stale-file half, A8-A14. Destination
escape reproduced with a real Windows junction in a temporary repository. The
workflow deletes the previous manifest, so both finalizer preservation and
publisher timestamp-only comparison are covered. Reconstructed reports already
published are also immutable in their payload. Full default commands in order:
pytest 6385 passed / 2 skipped, npm 296 passed, tsc/lint/default build exit 0.
Independent review: no findings, round 1, closure documents checked before commit.
All A1-A14 have fixes; G1 is the next separate task.

Guard follow-up (initial verification, superseded by the review fixes below): A15 found by the nested-directory sweep and seen
red before its fix. G1 shares the dry-run source judgment, stops strict builds
with `starter_unconfirmed`, and latches the whole candidate until strict recovery.
The preflight binds every restored published payload to recovered source values,
including complete files outside the selected dates (A2 closure). Controls retain
missing/null individual fields, actual zeros, changed starters, and explicit MLB
empty pitcher lists. Red evidence: main matrix 89 failed / 26 controls passed;
five additional cache/containment cases failed in isolated red runs; two further
regressions (cache recovery plus an ordinary game failure, and raw-evidence write
failure) failed before their corrections. Guard matrix then **122 passed**;
focused archive checks **318 passed** before the final evidence-save regression.
Full default verification: pytest **6507 passed / 2 skipped**, npm **296 passed**,
tsc/lint/default build **exit 0**. Round 1 review BLOCK, resolved below. No production data
touched. Audit fix commits: group 1 `6d2c293`, group 2 `d0c256e`, guard/A15 in this
commit. All A1-A15 and G1 have fixes.

### Guard review follow-ups (round 1, against the uncommitted guard)

| ID | Rating | Location at review | Finding and fix |
| --- | --- | --- | --- |
| R1 | blocker | `archive_build.py:310`, `scripts/publish_archive.py:97` | Python equality accepted a changed JSON boolean as a numeric zero. Reproduced through nonselected/selected resume, publication and index recomputation. Shared JSON-type-aware equality now covers source matching, derived indices/manifests, duplicate records and published payloads; key order remains immaterial. |
| R2 | blocker | `archive_build.py:288` | A stop-state write failure could be caught as an ordinary game error, allowing later requests; persistent failure could escape as an OSError. Reproduced transient/persistent writes, ceiling propagation and cached refresh/cleanup errors. Recording failure now stops immediately with a closed reason, retaining a fail-closed malformed sentinel when possible; linked state is refused before reads. |

Review reds: 7 failed / one key-order control passed; ceiling propagation,
cached-refresh I/O, and three stop-state link/cleanup cases also seen red before
their corrections. Focused archive checks then **570 passed**. Review round 1
BLOCK is accepted, with the reviewer's initially stated CLI-zero scenario
withdrawn/corrected to continued requests and persistent unhandled I/O. The
previous 6507/296 full run is superseded by fresh sequential checks: pytest
**6520 passed / 2 skipped**, npm **296 passed**, tsc/lint/default build **exit 0**.
All A1-A15, G1, R1 and R2 have fixes. Round 2 has no remaining findings; final
closure documents checked before commit. No findings were rejected.
