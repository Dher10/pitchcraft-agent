# Phase 0 — QA run 6 condition check, 2026-10-21

Verdict: **CONDITIONS MET**

Targeted check under `docs/QA_PROTOCOL.md`, task P0.10, of the three conditions in `docs/qa/QA-phase-0-2026-10-20.md`. This is not a new full Phase 0 QA run. QA6-01, QA6-02 and QA6-03 are **MET**. No new Blocker or High was found in the P0.17 diff or the exercised paths. Phase closure remains the owner's acceptance step.

Reviewed P0.17 commits `04d24e5` through `41ef812`, inclusive: `04d24e5`, `4a64c10`, `e49308c`, `f27a994`, `41ef812`. Git's exclusive-base range `04d24e5..41ef812` omits the plan commit; the inclusive diff was also read using `04d24e5^..41ef812`. HEAD throughout was `41ef812ef762b5da9f7a331a2d4ad4fe6b18c9b5`, branch `v2`.

**MLB / Baseball Savant requests: 0.** Sources were mocked and caches redirected to temporary directories; existing suites use their fixtures/mocks. No session PATH or locale changes. Product files, tests, configuration and handoff documents were unchanged. The working tree was clean before this report. Scratch scripts and the mutation copy are outside the repository, under `$env:TEMP/pitchcraft-qa6-conditions-20261021/`.

## Commands and verification

Default PowerShell terminal, Python 3.14.6, Node v24.16.0. Commands requiring child processes or temporary-directory access were run outside the sandbox after the sandbox restrictions below; the command, PATH, locale and test configuration were unchanged.

| Command | Observed result |
|---|---|
| `python -m pytest` | Exit 0: **3615 passed, 2 skipped, 2 warnings in 261.58s**; 3617 collected. Warnings are the two intentionally malformed-date cache cases at `live_pipeline.py:852`; skips are the existing demo-file checks in `tests/test_served_json.py`. |
| `npm test` | Exit 1: **176 passed, 1 failed**, 12 files passed / 1 failed. `GameCarousel.test.tsx` → `says upcoming for a game that is upcoming` timed out at 5000 ms (reported duration 10484 ms). No assertion mismatch was reported. |
| `npm test -- components/__tests__/GameCarousel.test.tsx` | Exit 0: **5 passed**, 1 file, 2.98s. This focused rerun does not replace the full-suite result above. |
| `npx tsc --noEmit` | Exit 0. |
| `npm run lint` | Exit 0. |
| `npm run build` | Exit 0, Next.js 16.4.0; **4/4** static-generation steps completed. |
| `python "$env:TEMP/pitchcraft-qa6-conditions-20261021/probes.py" C:/Dev/pitchcraft-agent` | Exit 0: **26 Statcast cases, 4 negative API counts, 1 ERA placeholder, 15 guard blocks, 4 allow controls**, plus healthy-game and matcher controls. |
| `python "$env:TEMP/pitchcraft-qa6-conditions-20261021/mutations.py" C:/Dev/pitchcraft-agent` | Exit 0: unmutated label file **118 passed**; all four mutants caught by assertion failures (table below). |
| `python -m pytest tests/test_domain_bounds.py tests/test_source_schemas.py -q -p no:cacheprovider` in the unmodified temporary copy | Exit 0: **355 passed in 19.56s**. |
| Same focused command, temporary copy only, with both fetcher modules replaced by their `4a64c10^` versions | Exit 1: **92 failed, 198 passed, 9 skipped, 5 warnings in 18.48s**. The old schemas generate no count/positive cases; the explicit schema-coverage assertions fail. HEAD's tests detect the pre-fix boundary/placeholder defects. |
| `npm audit --json` | Exit 1: **5 high**, 0 critical, in the existing dev lint chain; no Vite advisory. |
| `npm audit --omit=dev --json` | Exit 0: **0 vulnerabilities**. |
| `git diff --check`; identity, branch, remote, history and status reads | Exit 0; owner identity, `v2`, expected origin; only this report added at completion. |

The first sandboxed pytest attempt stopped during collection: **3367 collected / 2 collection errors**, `PermissionError [WinError 5]` accessing temporary directories. The first sandboxed `npm test` attempt stopped before tests with Vite `spawn EPERM`. Those attempts are not passing suite results. Each full suite then executed once outside the sandbox; only the timed-out frontend file was rerun. Some suite commands overlapped; resource contention is a possible explanation for the timeout, not an established cause.

Other network use was read-only: **7 successful GitHub API requests** (rulesets list, three details, effective rules for two branches, CI list) and **2 npm audit commands**. Two initial sandboxed `gh api` calls failed at the local proxy before reaching GitHub. No GitHub settings were changed.

## QA6-01 — MET

**Probe B/B2 and E2 reproduced through the real fetchers → two-game snapshot → `build_payload()` → `validate_payload()` → `json.dumps(..., allow_nan=False)`.** The scratch harness uses `events_frame`, `API_STATS` and `FakeResponse` from `tests/test_live_sample_pipeline.py`, and `snapshot_from_starters` / `use_snapshot` from `tests/live_helpers.py`. Only the first game's away starter receives the malformed source cell; three healthy starters provide controls. Each Statcast value below was tried in one row and in every row, with `RuntimeWarning` treated as an error.

| Column / values | Actual result for both row patterns |
|---|---|
| `pfx_x`: `-50`, `9999`, `1e6` | Only movement unavailable: both components `null`. |
| `release_speed`: `9999`, `1e6` | Only velocity unavailable: affected starter's public velocity cells `null`. |
| `plate_x`: `-50`, `9999`, `1e6` | Only locations unavailable: both batter-side lists empty; no clipped bogus point. |
| `1e308` in each of `release_speed`, `pfx_x`, `pfx_z`, `plate_x`, `plate_z` | Only that column's measurement group unavailable. No overflow warning or non-finite output. |

All **26** cases recorded exactly one local `statcast_pitcher/malformed_rows` error naming the column, and published its sanitized `{source, code}` in `metadata.data_status.live_run.errors`. Counts, sample, mix, throwing hand, API season summary and unaffected measurement groups stayed equal to the healthy baseline. The other three starters stayed identical to baseline, and the **other public game equaled its healthy baseline**. Both games were present and validated in every case.

API probes changed one first-starter stat at a time:

```text
strikeOuts=-5, battersFaced=-19, baseOnBalls=-1, homeRuns=-1
  each: mlb_season_stats/malformed_response recorded locally and publicly;
        API line rejected; valid Statcast counts used (K=4, BF=19);
        both games published and validated; other public game unchanged.
era="-.--"
  only ERA becomes "N/A"; WHIP, innings, counts and sample unchanged;
  no error; both games published and validated; other game unchanged.
```

Implementation evidence: `live_pipeline.py:804` has the approved per-column bounds; `:906` disables the whole affected group before aggregation/filtering; `:1533` and `:1660` protect aggregation and movement conversion. `_season_figure` at `:508` handles placeholders. `mlb_schemas.py:89` rejects negative/non-integer counts, used for pitcher counts at `:293`, team counts at `:323`, series counts at `:267`, with positive series game numbers at `:248`.

Regression coverage: `test_domain_bounds.py:82` (each column, one/all rows), `:105` (valid boundaries), `:144` (overflow defence with deliberately widened bounds), `:182` (placeholder variants), `:236` / `:275` (two-game containment), and `test_source_schemas.py:301` (negative counts across schemas). The temporary pre-fix run above supplies independent red evidence; it is not a claim about having witnessed the original implementation session.

## QA6-02 — MET

Loaded `.claude/hooks/git_guard.py` and called `decide(command, fake_git)` directly. The fake supplies branch `v2`, the frozen tag and the owner's identity. **Every command in QA6-02 returned a non-null blocking reason**:

```text
BLOCK  bash -c "git push --force origin main"
BLOCK  sh -c 'git push origin main'
BLOCK  eval "git push origin main"
BLOCK  powershell -Command "git push origin main"
BLOCK  cmd /c git push origin main
BLOCK  x=git; $x push origin main
BLOCK  python -c "import subprocess; subprocess.run(['git','push','origin','main'])"
BLOCK  git filter-branch --all
BLOCK  git branch -D v2
BLOCK  git remote add evil https://x.y/z.git
```

Five added class checks also blocked: `pwsh -Command "git push origin main"`, `node -e "require('child_process').execSync('git push origin main')"`, `git branch -d main`, `git remote set-url origin https://x.y/z.git`, and `git remote remove origin`.

Four controls returned `None` (allowed): `git config --get core.hooksPath`, bare `git config core.hooksPath`, `git status --short`, and `git push origin v2`. The actual read-only `git config --get core.hooksPath` printed **`.githooks`**. Unsafe strings were input data to `decide`, never executed as commands.

`.claude/settings.json:9` / `:18` have separate **Bash** and **PowerShell** matchers with identical hook commands. `AGENTS.md:68` describes the interception and wrappers; `:69` explicitly excludes other tools, scripts/programs, functions/aliases, `gh`/REST and runtime names without a literal `git`; `:70` explains server rules and token-admin limitations. This Codex tool session is not itself intercepted by that Claude hook. The check establishes parser behavior, configuration and documented scope, not live interception of this session.

Read with `gh api repos/Dher10/pitchcraft-agent/rulesets`, then `/rulesets/<id>` and `/rules/branches/main` / `/rules/branches/v2`:

| Ruleset | Target | Active rules | Bypass actors |
|---|---|---|---|
| [main, 25520388](https://github.com/Dher10/pitchcraft-agent/rules/25520388) | `refs/heads/main` | `deletion`, `non_fast_forward`, `update` | `[]` |
| [v2, 25520406](https://github.com/Dher10/pitchcraft-agent/rules/25520406) | `refs/heads/v2` | `deletion`, `non_fast_forward` | `[]` |
| [tags, 25520422](https://github.com/Dher10/pitchcraft-agent/rules/25520422) | `refs/tags/v1.0.0-kaggle` | `deletion`, `update` | `[]` |

All three report `enforcement: active` and `current_user_can_bypass: never`. Effective branch-rule endpoints confirm the listed main/v2 rules. The no-bypass release/bot consequence and the administrator's ability to edit rulesets are already documented, not silently assumed away.

## QA6-03 — MET

Copied the repository to a temporary folder, excluding Git metadata, installed/generated files and runtime caches. In separate Python processes, ran `python -m pytest tests/test_labels.py -q -p no:cacheprovider` with one exact replacement in `data_pipeline/labels.py` at a time. Removed the copy's label bytecode between runs. Unmodified control: **118 passed**. All mutants failed assertions in the rate-property tests, not collection/import errors.

| QA6 mutant | Exact replacement condition | Result on the entire label test file |
|---|---|---|
| Walk Solid | `scaled <= WALK_SOLID_PCT * batters` → `rates["walks"] <= 14` | Exit 1: **9 failed, 109 passed** |
| Strikeout Above | `scaled >= STRIKEOUT_ABOVE_AVERAGE_PCT * batters` → `rates["strikeouts"] >= 50` | Exit 1: **27 failed, 91 passed** |
| Strikeout Below | `scaled < STRIKEOUT_BELOW_AVERAGE_PCT * batters` → `rates["strikeouts"] < 36` | Exit 1: **13 failed, 105 passed** |
| Walk Below | `scaled >= WALK_BELOW_AVERAGE_PCT * batters` → `rates["walks"] >= 20` | Exit 1: **14 failed, 104 passed** |

`tests/test_labels.py:204` covers strikeout bands at **100, 200, 600, 1000 BF**; `:206` covers walk bands at **200, 600, 1000, 2000 BF**. The omitted walk label at 100 is correct under D24's 170-BF minimum, explicitly checked at `:292`. Both band edges and average bands are tested with expected labels (`:240`, `:246`), plus one-label-per-rate assertions (`:251`, `:258`) and tenth-point edges. This meets the original condition without weakening D24 to force a command label at 100 BF.

## Diff review, status comparison and remaining observations

P0.17's production changes are confined to source validation/aggregation, the local guard/configuration, and the Vite dev dependency (8.3.1 → 8.3.5). No decision, workflow, schema version, served JSON, app/component or agent-text file changed. The altered boundary paths preserve scopes, cutoffs, valid measurements and sanitized public errors in the probes. All five commits have author/committer `Daniel Herdenez <edherdenez@gmail.com>`, formatted subjects/bodies and verification lines. HEAD is contained by local `v2` and `origin/v2`.

`gh run list --branch v2 --limit 6 --json headSha,status,conclusion,url` reports **completed/success** for all five exact P0.17 SHAs, including [HEAD's CI](https://github.com/Dher10/pitchcraft-agent/actions/runs/39594711753). CI success is separate evidence; it does not replace this session's npm result.

After forming findings, read `STATUS.md` and the P0.17 entries of `status-archive.md`. The three functional condition claims reproduce. The archived mutant count **12** for Walk Below refers to new tests only; the archive explicitly records **14** for the whole file, matching this check. The historical claim `npm test 177 passed` was **not reproduced in this session's full run** (176 passed / 1 timeout); the isolated file passed. Historical approvals and original red runs were not independently witnessed; the archive records owner authorization of the third guard-review round.

Short list below High; none changes this condition verdict:

- **Low — verification timing:** `components/__tests__/GameCarousel.test.tsx:25` timed out once in the full run and passed in isolation. Attribution to P0.17 or contention is unproven; retain the failure in the record.
- **Existing accepted follow-ups:** guard bypasses/false positives listed in `AGENTS.md:69` and the archive; main has no bypass actor for release/D15 automation; the payload manifest still checks velocity positivity rather than source bounds. The source-boundary condition is met; this is not a claim of universal enforcement across arbitrary tools or edited snapshots.
- **Existing QA6 residuals:** runtime source-conservation/projection gating (QA6-04), triple-play metadata/tolerance (QA6-06), and five dev-only lint-chain audit highs remain follow-ups. They were not recertified as part of a full phase review. Vite's QA6-05 advisory is absent; production audit is zero.

Only this report is proposed for commit. No PLAN/STATUS checkbox or phase-closure claim is changed by this targeted review.

## Proposed commit — awaiting owner approval

```text
docs: add qa report for phase-0

Record the targeted QA6 condition check for P0.17 at 41ef812.
All three conditions are met; no new Blocker or High was found.

Verification: pytest 3615 passed, 2 skipped; npm test 176 passed,
1 timeout (isolated file 5 passed); tsc, lint and build exit 0;
four label mutants caught; zero MLB/Savant requests.
```
