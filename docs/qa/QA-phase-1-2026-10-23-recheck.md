# Phase 1 gate — release 1 focused recheck — 2026-10-23

Verdict: RELEASE 1 CLEARED

Recheck of **QA1-01 through QA1-06** from `docs/qa/QA-phase-1-2026-10-23.md` against the owner-approved `docs/plans/P1-R1fix.md`. Reviewed range: `3027528..cf4a46660535f408fcc66c5626bd4aec5c45cd93` (five commits). This is a focused recheck, not a new full Phase 1 gate. QA1-07 remains deferred to release 2 by the owner.

**All six original probes are FIXED. No new Blocker or High was found in the range. All five requested full checks pass.** One new Low documentation issue is listed below; it does not reopen the original publication probes. This satisfies the requested focused release-1 recheck (protocol severity outcome: PASS). Production release steps R0–R8 remain the owner's steps; this report does not certify deploy-key authentication, Vercel settings, production delivery or Analytics ingestion.

**MLB requests: 0. Savant requests: 0. Workflows triggered: 0.** Product/config/test files changed by this recheck: **0**. Only this report is proposed for the commit. Probes use mocked sources, local fixtures and temporary repositories outside the checkout. Publication pushes are mocked; fixture setup pushes only to disposable local bare repositories. No GitHub operation was performed.

## Verification

The five requested full commands run once each, sequentially, in the owner's default PowerShell terminal on HEAD, with no PATH or locale changes. Expanded access is used for pytest/npm/build because the original gate established sandbox TEMP/process restrictions. Read-only fixture probes are additional targeted checks, not another run of either full suite.

| Command | Observed result |
|---|---|
| `python -m pytest` | Exit 0: **4535 passed, 2 skipped, 2 warnings in 389.00s** |
| `npm test` | Exit 0: **17 files / 261 tests passed**, 13.49s |
| `npx tsc --noEmit` | Exit 0 |
| `npm run lint` | Exit 0 |
| `npm run build` | Exit 0: compiled, type checked, generated pages; routes `/`, `/_not-found`, `/quality` |
| `git diff --check 3027528..HEAD` | Exit 0 |
| `git log --format=fuller 3027528..HEAD` | Five commits; author and committer Daniel Herdenez `<edherdenez@gmail.com>` throughout; conventional subjects and bodies, no attribution trailers |

The two pytest skips are served-file live-only assertions while the committed file is demo. The two warnings are date parsing in the intentional malformed-date cache cases. No contract-finding xfail appears in the run or in the new regression tests.

Scratch probes are retained outside the repo in `$env:TEMP/pitchcraft-phase1-recheck-20261023/`: `original-probes.py`, `footer-probe.cjs`, `publish-probes.py`, and generated `notes.json`. Commands and representative output follow. The initial sandbox attempt of `original-probes.py` stopped on `PermissionError: [WinError 5]` creating a temporary fixture cache; the unchanged command succeeded with expanded access. That failed attempt is not evidence of a product failure. The Python source/series probe replaces socket connection attempts with an assertion in addition to the matrix's mocked sources.

## Original findings on HEAD

| ID | Original severity | Result | Evidence on HEAD |
|---|---|---|---|
| QA1-01 | Blocker | **FIXED** | Live/Final/null Game 1 emits neither the opening sentence nor its claim; Preview retains both. Injected stale claims fail `rule4:analyst.series.opening#game_state`. |
| QA1-02 | High | **FIXED** | Both originally accepted equals-form token options now return the guard's denial; bare/short/normalized variants also denied, ordinary read controls allowed. |
| QA1-03 | High | **FIXED** | Actual served, generated demo, fallback and live disclaimers render both source names and the non-commercial note. |
| QA1-04 | Low | **FIXED** | The original literal URL userinfo command is denied as credentials; token-only userinfo and uploads-host variants are also denied. |
| QA1-05 | Low | **FIXED** | With all four inherited conflicting identity variables, the actual temporary commit has the owner's author and committer identity. |
| QA1-06 | Low | **FIXED** | Real index lock and synthetic add-process failure now return closed failure, restore original bytes and leave a clean index/worktree without pushing. Post-copy status/commit failure controls do likewise. |

### QA1-01 — temporal series claim

Command: `python "$env:TEMP/pitchcraft-phase1-recheck-20261023/original-probes.py"`, exit 0 with expanded access. The probe repeats the original `run_scenario(replace(HARD_CASES["series_opening"], name="qa-recheck", state=state))` on HEAD through the real pipeline, generator, critic, validator and contract. It extends this to `{series_opening, series_standing, series_tied}` × `{Preview/Scheduled, Live/In Progress, Final/Final, missing state}`.

```text
series_opening Preview: status=upcoming opening=True  opening_claim=True  failed=[] violations=[]
series_opening Live:    status=live     opening=False opening_claim=False failed=[] violations=[]
series_opening Final:   status=final    opening=False opening_claim=False failed=[] violations=[]
series_opening missing: status=None     opening=False opening_claim=False failed=[] violations=[]
INJECTED_OPENING live  ['rule4:analyst.series.opening#game_state']
INJECTED_OPENING final ['rule4:analyst.series.opening#game_state']
INJECTED_OPENING None  ['rule4:analyst.series.opening#game_state']
```

All 12 generated cells have no blocked critic result, failed publication checks or contract violations. Both later-game cases retain their historically framed sentence in all four states: `Before first pitch, BOS leads 2-0.` / `Before first pitch, series tied 1-1.` The payload keeps MLB's `Series tied 1-1`; only its sentence form is lowercased. The explicit exception in contract rule 4 now matches the approved plan and D29's historical cutoff.

Expected and actual now agree under D34 rules 4/7 and D40. Enforcement: `agents/matchup_analyst.py:130`, `data_pipeline/claims_registry.py:652`, `data_pipeline/series.py:72`. Regression/negative coverage: `tests/test_series_state.py:77`, `:86`, `:97`, `:148`, `:161`, `:174`. Reverting the writer condition would restore the observed false sentence; removing the registry condition would admit the injected claims. Both failure modes have direct assertions.

### QA1-02 and QA1-04 — guard-only string probes

Same Python command, exit 0. Import `.claude/hooks/git_guard.py` and call `decide(command, lambda *args: "")`, exactly as in the original report. The strings below are **not executed** against any CLI login or URL.

```text
'gh auth status --show-token=true' => 'gh auth status --show-token prints the token and is not allowed (P1.0)'
'gh auth status --show-token=True' => same denial
'gh auth status --show-token'      => same denial
'gh auth status --show-token=1'    => same denial
'gh auth status --show-token=false' => same denial
'gh auth status -at'               => same denial
'gh auth status -t=true'           => same denial
'gh auth status --SHOW_TOKEN=True' => same denial
'curl https://user:pw@api.github.com/user' => 'a request to the GitHub API with credentials is not allowed (P1.0)'
'curl -u user:pw https://api.github.com/user' => 'a request to the GitHub API with a body or credentials is not allowed (P1.0)'
'curl https://token@uploads.github.com/repos/example/assets' => credentials denial
```

Controls `gh auth status`, `gh auth status --hostname github.com`, `gh api repos/Dher10/pitchcraft-agent/rulesets` and `curl https://api.github.com/user` each return `None` (allowed). No credential value is read or printed. The QA1-02 secret-display path and QA1-04 literal credential-request gap are closed within the documented shell guard's scope. Enforcement: `.claude/hooks/git_guard.py:512`, `:549`, `:459`, `:626`. Regression coverage: `test_every_spelling_of_the_token_printing_option_is_blocked`, `test_control_the_status_of_gh_without_the_token_option_passes`, `test_a_url_to_the_github_api_with_user_information_is_a_credential_and_is_blocked`, and their URL/read controls in `tests/test_agent_git_guard.py`. These test the actual decision result, not a mocked guard result.

### QA1-03 — render the actual notes

The Python probe builds the real demo/fallback/live payloads using `tests.corpus.build` with mocked inputs and exports only their notes plus the committed served file's notes to temporary `notes.json`. Command: `node "$env:TEMP/pitchcraft-phase1-recheck-20261023/footer-probe.cjs"`, exit 0. As in the original probe, the installed TypeScript compiler transpiles the actual `components/Disclaimer.tsx`; React `renderToStaticMarkup` renders it with those notes.

```text
RENDER {"mode":"demo","MLB":true,"Savant":true,"nonCommercial":true}
RENDER {"mode":"fallback","MLB":true,"Savant":true,"nonCommercial":true}
RENDER {"mode":"live_complete","MLB":true,"Savant":true,"nonCommercial":true}
RENDER {"mode":"served","MLB":true,"Savant":true,"nonCommercial":true}
```

The served demo and generated demo/fallback carry exactly the approved attribution sentence. Live notes retain their live attribution and do not acquire the demo sentence. This meets D16/P1.9's both-mode attribution requirement. Enforcement: `data_pipeline/demo_inputs.py:967`; served note at `public/data/pitchcraft-demo.json:2422`. Regression coverage: `tests/test_attribution.py:69`, `:87`, and actual served-page rendering in `components/__tests__/Attribution.test.tsx:106`. Generated-note checks and the served-file render address the old gap; the newly typed demo-note page cases alone would not prove generator behavior.

### QA1-05 — conflicting inherited identities

Command: `python "$env:TEMP/pitchcraft-phase1-recheck-20261023/publish-probes.py"`, exit 0 with expanded access. Use the publication tests' disposable `World` repository, patch `_push`, and set `GIT_AUTHOR_NAME=Other Author`, `GIT_AUTHOR_EMAIL=other@example.com`, `GIT_COMMITTER_NAME=Other Committer`, `GIT_COMMITTER_EMAIL=committer@example.com` only around `publish_data.main`. Inspect the resulting fixture commit with `git log -1 --format=%an|%ae|%cn|%ce`.

```text
IDENTITY_EXIT 0
IDENTITY_ACTUAL Daniel Herdenez|edherdenez@gmail.com|Daniel Herdenez|edherdenez@gmail.com
IDENTITY_PUSH_MOCK_CALLS 1
```

The local bare fixture remote remains at its seed because publication push is mocked. D21/D42's identity now holds under the original challenging environment. `_commit_env()` explicitly supplies all four variables to the commit process (`scripts/publish_data.py:156`, `:282`). `tests/test_publish_data.py:636` checks the real committed identity collectively; `:647` checks each conflicting variable separately. These assertions would catch a missing override, rather than merely inspecting an intended command.

### QA1-06 — post-copy failure and closed diagnostics

Same publication probe command, exit 0. Repeat the original real `.git/index.lock` and injected `OSError("synthetic process creation failure")` on the add subprocess path, with `_push` mocked. Also inject a post-copy status failure and commit-process startup failure.

```text
ADD_LOCK         exit=1 restored=True status='' push_calls=0 remote_same=True stderr=''
PROCESS_ADD      exit=1 restored=True status='' push_calls=0 remote_same=True stderr=''
POST_COPY_STATUS exit=1 restored=True status='' push_calls=0 remote_same=True stderr=''
PROCESS_COMMIT   exit=1 restored=True status='' push_calls=0 remote_same=True stderr=''
```

Each prints `publish: failed git_failed`; no exception text or traceback escapes. For the lock probe, restoration and clean status are observed even before removing the synthetic lock. The shared rollback covers copy/status/allowlist/add/commit, and the outer handler closes operational exceptions (`scripts/publish_data.py:246`, `:288`, `:384`). Regression tests include `tests/test_publish_data.py:707`, `:718`, `:736`, `:771`, `:790`, plus push/clone exception handling. Expected and actual agree for both original probes; public data and the fixture remote are untouched on failure. Cleanup when rollback itself fails has the limitation below.

## New Blocker/High review and lower-severity list

**New Blockers: 0. New Highs: 0. New Mediums: 0.** Inspected all changed source, test and contract hunks in the five-commit range, including related unchanged readers and publication control flow. A separate clean-context read-only Explore review of publication corroborated the identity/rollback assessment; it ran no suites and wrote no files. Final verdict uses the reproduced probes and verification, not implementer claims.

- **R1-RC-01 — Low, cleanup documentation overstates its guarantee.** `scripts/publish_data.py:22` says a failure after copying puts the worktree and index back. Actual rollback at `:249`–`:259` intentionally suppresses reset/restore failures. Additional fixture probe: inject an `OSError` on both commit and rollback reset after a real successful add. Output: `CLEANUP_ALSO_FAILS exit=1 restored=True status='MM public/data/pitchcraft-demo.json' push_calls=0 remote_same=True`, closed `git_failed`, empty stderr. The existing test at `tests/test_publish_data.py:746` manually resets the fixture afterward, so it does not establish unconditional index restoration. This is a limited documentation/cleanup limitation in a disposable checkout, not a public-data or remote mutation. Smallest follow-up: describe rollback as best effort when cleanup itself fails; optionally emit a distinct closed cleanup diagnostic. The original QA1-06 probes are fixed.
- **QA1-07 — existing Low, deferred to release 2 by the owner.** Dependency manifests/lockfile are unchanged in this range. No new audit was requested or run; the original two moderate dev-package advisories are not claimed patched. The inherited one-argument branch-rename guard limitation also remains outside this range; no rename was executed.

## Focused coverage and records

No Phase 1-specific Gherkin block was added by this range. The retained Phase 0 scenarios are run by the full suite; this recheck does not repeat the original gate's complete scenario mapping or external configuration audit.

| Relevant acceptance | Concrete regression coverage | Would fail on the reported regression? |
|---|---|---|
| Honest series wording in four states, with historically framed standing retained | `tests/test_series_state.py` product and negative-condition tests | Yes: assert sentence and claim presence/absence, successful publication, exact status and rejection of stale opening claims |
| Token-display spellings/userinfo denied, ordinary reads allowed | Named guard tests above | Yes: invoke actual guard decisions for unsafe strings and controls |
| Attribution in demo, fallback, live and served page | Python generated-note tests plus `Attribution.test.tsx` served-page test | Yes: removing the demo source sentence fails generated notes and the actual served render |
| Owner identity despite inherited values | `tests/test_publish_data.py:636`, `:647` | Yes: inspect actual fixture commit author and committer |
| Closed operational failures and rollback at post-copy boundaries | `tests/test_publish_data.py:707`, `:718`, `:736`, `:771` | Yes: inspect exit, diagnostic, original bytes, clean status and unchanged fixture remote |

Protocol areas in scope: spec and docs match the approved P1-R1fix conditions; state honesty and contract checks were exercised with generated payloads and false-condition mutations; publication failure/security paths were probed; test assertions were inspected for realistic regressions; footer rendering was checked with actual generated/served notes; range identity/history was read. No new fetcher, numerical threshold, budget/cache implementation, schema, workflow or dependency change appears in the range. Those unchanged areas receive suite regression coverage here, not a fresh full audit. The source-diff secret-pattern scan found **0 candidates** for private-key headers and common GitHub/Google key literals; this is a limited pattern scan, not proof of secret absence.

Read STATUS and the latest archive entry only after forming the findings. The stated QA1-01 through QA1-06 behavior is reproducible, qualified by R1-RC-01's best-effort cleanup boundary. Historical red-first counts, reviewer rounds, approvals and CI results were not reenacted or independently re-queried. G5 and bypass-actor wording now cites the prior read-only observations; the current server state was not re-read. The recorded Google Fonts build dependency predates this range. Release-2 archive/no-games/heartbeat functionality remains excluded; a no-games daily failure retaining the previous file is still expected under D42 until release 2.

## Proposed report-only commit

Preflight: `git config user.name` → `Daniel Herdenez`; `git config user.email` → `edherdenez@gmail.com`; `git branch --show-current` → `v2`; `git remote -v` → `https://github.com/Dher10/pitchcraft-agent.git` (fetch/push); `git config --get core.hooksPath` → `.githooks`.

Final checkout check: `git status --short` shows only the untracked report; `git diff --quiet` and `git diff --cached --quiet` both exit 0 (no tracked or staged changes). HEAD remains `cf4a46660535f408fcc66c5626bd4aec5c45cd93`. No product file was changed. Only `docs/qa/QA-phase-1-2026-10-23-recheck.md` is proposed; nothing staged, committed or pushed.

```text
docs: add qa report for phase 1

Record the focused release 1 recheck for 3027528..cf4a466.
Reproduce QA1-01 through QA1-06 as fixed; record the low cleanup
documentation limitation and the owner-deferred QA1-07.

Verification: pytest 4535 passed, 2 skipped; npm test 261 passed;
tsc, lint and build pass. Verdict: RELEASE 1 CLEARED.
```

Commit requires the owner's explicit yes under `docs/QA_PROTOCOL.md` and the user's request. No commit or push is authorized by the report itself.
