# PitchCraft v2 — Execution plan

Living plan. Agents tick checkboxes and update `STATUS.md` after every task (see `AGENTS.md`).

## Rollout (decision D10)

- **v2.0-a — before Oct 25, 2026:** Phase 0 + daily automation + source signals + postseason layer, with the rules-based writer.
- **v2.0-b — Nov 15, 2026:** LLM writer enabled only if it passes the eval; case study published.
- **v2.1:** Spanish.

**Build order inside v2.0-a:** core first (Phase 0, daily job, badges, offseason state), then the postseason layer. The postseason layer is in scope and worked daily; it is built last only because the core must be live first.

**Hard window:** the postseason layer only has value while there are postseason games. If it is not live before the World Series ends, it waits for the 2027 postseason.

**If v2.0-a slips past Oct 25, cut in this order:** 1) automated postgame, 2) bio facts in the postseason layer. Phase 0, automation, source signals and series context are never cut.

## Setup

- [x] S0 Create `.claude/settings.json` with `{"attribution": {"commit": "", "pr": ""}}` (disables Claude Code attribution, D21). Run `git config core.hooksPath .githooks`, confirm identity per `docs/CONTRIBUTING.md`, and commit all pending docs and config with the new flow. Check with `git log -1 --format='%an <%ae>%n%B'` that the commit is under the owner's name, in format, and without attribution.

## Phase 0 — Data integrity (target Oct 18)

Lanes (D22): `[auto]` = plan approved once, then commit and push without asking; `[gated]` = explicit yes before each commit. Unlabelled = gated.

- [x] P0.0 Test infrastructure: add pytest, a `tests/` folder and a GitHub Actions workflow that runs the tests on every push to `v2`. No logic changes before this exists. Includes tests of the `.githooks/commit-msg` hook (rejects subject without prefix, message without body, author/committer other than the owner; strips `Co-Authored-By`) and a smoke test of the five agents over demo data.
- [x] P0.1 Remove demo `recent_form` and bio from live starters (`data_pipeline/generate_demo_json.py`, `_apply_live_starter`). Real source or marked unavailable.
- [x] P0.1b Team `offense_profile` never inherits demo values: when a team has no real split, mark offense fields as unavailable. Extend the "Live starters carry no demo fields" Gherkin coverage to team fields.
- [x] P0.2 [gated] Add `as_of` to every fetcher in `data_pipeline/fetchers/`: Statcast, pitcher season stats, team splits, series status.
- [x] P0.3 [auto] Check whether the MLB Stats API supports team splits by date range. If not, derive them from Statcast with the same cutoff. Record the finding in `STATUS.md`.
- [x] P0.3b [gated] Filter pitcher Statcast by `game_type` (never spring training; postseason only up to `as_of`). Pace and cap the Savant team-batting requests (2 s pause, 210 per run, fails if exceeded).
- [x] P0.4 [gated] Measure the real 2026 distribution (pitches, batters faced, walks) and present proposed per-dimension thresholds (D11) to the owner. Do not implement thresholds until the owner approves; record the approved values in `DECISIONS.md`.
- [x] P0.5 [gated] Rate-based labels (K%, BB%, HR rate) in a single module, using the thresholds approved in P0.4. Remove the duplicated count-based logic in `live_pipeline.py` and `generate_demo_json.py`. Fix the `total_pitches` calculation (currently sums percentages).
- [x] P0.6 [auto] Fix the name-split bug in `agents/report_writer.py` (`_watch_observation`).
- [x] P0.7 [auto] Remove the hardcoded season year (2026, `2026-03-20`).
- [x] P0.8 [auto] Explicit data mode and error log instead of the silent fallback to demo.
- [x] P0.9 [auto] Hygiene: upgrade Next.js to 16.4.0 (fixes `npm audit` critical/high findings; read `node_modules/next/dist/docs/` first); delete `pitchcraftvisualpolish.bundle` (stray git bundle); pin `pybaseball==2.2.7`; move or delete `test_splits.py`. `npm audit --omit=dev` must report 0 critical and 0 high.
- [x] P0.11 [gated] Close the Phase 0 gaps found by the definition-of-done check, before the QA gate: end-to-end `as_of` test (scenario 1), split scenarios 4 and 9 (D28), assign the remaining gaps to P1.0, P1.2 and P1.4, and document the accepted dev-only `npm audit` findings.
- [x] P0.12 [gated] Fix the findings of the first Phase 0 QA gate (`docs/qa/QA-phase-0-2026-10-10.md`), grouped by root cause, one commit per subtask. For every finding: first a test that reproduces the QA probe and fails, then the fix. Tests that lock in the unsafe behavior are deleted (for example `test_build_live_snapshot_without_as_of_keeps_todays_behavior`).
  - [x] P0.12-A Strict input boundary: QA-02 (`as_of` is always the day before the game, including the daily job; needs D29 approved first), QA-05 (mandatory columns and schedule structure; malformed or null is an error, a valid empty frame or schedule is not), QA-06 (stale snapshot protection requires non-empty, matching run identifiers and consistent dates), QA-08 (a partial live summary or profile never inherits demo values).
  - [x] P0.12-B The Critic blocks publication, and CI validates the served JSON: QA-04 (no invented put-away pitch; the critic never reports a revision it did not make, and an unsupported claim stops the publish), QA-01 (a test over `public/data/pitchcraft-demo.json`, the file `lib/data.ts` serves, then regenerate it with the corrected generator).
  - [x] P0.12-C Frontend honesty, and the component test runner brought forward from P1.4: QA-03 (the detail panel only shows the selected starter's own arsenal, a limitation for an empty or limited arsenal, and unavailable movement as unavailable, never as 0.0; also the starter card shows "—" for an unavailable ERA, WHIP or IP, the frontend half of the "N/A is never a number" invariant started in B).
  - [x] P0.12-D Minimal D6: QA-07 (`language` parameter, `en` by default, on every agent that writes text, and the agents' user-facing text in a catalog; no Spanish yet).
  - [x] P0.12-E Medium and tooling: QA-09 (cache a valid empty finished month), QA-10 (commit-msg hook gaps), the hook tests no longer depend on `sed` being on PATH, and `.pytest_cache` is out of the lint.
- [x] P0.13 [gated] Fix the findings of the second Phase 0 QA gate (`docs/qa/QA-phase-0-2026-10-11.md`: one Blocker, two Highs, two Mediums, one Low), one commit per subtask, same method as P0.12: for every finding, first a test that reproduces the QA probe and fails, then the fix. Two rules apply to the whole task. (1) Fix the class of error, not only the probe: sweep the code for other `.get(<mandatory field>, [])` / `or []` that turn an error into emptiness, other checks that scan the whole report instead of the starter's own section or sentence, and other decisions taken on rounded values; the sweep result is listed in the plan the owner approves, and each item is either fixed in the subtask that owns it or recorded in `STATUS.md`. (2) The verification line of every commit comes from `python -m pytest` and `npm test` run in the owner's default terminal, with nothing prepended to the PATH and no locale changed; a variation (another locale, a minimal PATH) may be a test case, never the way the verification is run.
  - [x] P0.13-A Input boundary: QA2-01 (the generator parses the dates of the run, the snapshot and each game and rejects explicitly: the cutoff of every game must be before its official date, and run, snapshot and game must agree; publication validation also checks that no figure's scope ends on or after the matchup date) and QA2-03 (nested envelopes of the schedule games, the pitcher season stats, the series status and the Statcast `events` column: a valid empty answer stays valid, a malformed one or an error envelope is a recorded source failure, never an empty or zero result). Sweep fixes in the same commit: a frame without `p_throws` takes the hand from `fetch_pitcher_hand`, never "R" (the lookup is cached for good and capped at 10 requests per run); a snapshot starter without `throws` is rejected; team-split counts the source omits are `None`, not 0; the unused `mlb_stats_api.py` is deleted.
  - [x] P0.13-B Attribution and rounding: QA2-02 (the limited-arsenal check reads only what is said about that starter, by section and sentence; test: a limited starter and a healthy one sharing Four-seam and Slider publish successfully; `_command_check` attributes its label claims the same way) and QA2-04 (D30 and the pitch ranking compare raw pitch counts before any rounding; tests just below, exactly at and just above 15%). Sweep fixes in the same commit: `report_writer` and the critic stop defaulting a missing `limited`/`sections` to empty; `postgame_grader._what_to_watch_next` no longer treats "Above-average" and "Below-average" as "average"; the K%, BB% and OPS cut-offs of the analyst become one constant each (23.0, 9.0, .750, inclusive), recorded as D32 with the value the fan already sees.
  - [x] P0.13-C Tooling and handoff: QA2-05 (the attribution filter of the commit-msg hook does not depend on the locale; verified in the owner's default Windows terminal, with the locale as a test parameter), QA2-06 (the accepted-risk line of `STATUS.md` states the current audit), and the verification rule added to `docs/CONTRIBUTING.md` as: "verification is run without changing PATH or locale; tests that depend on the environment are parameterized by environment". The emoji attribution test runs for the default locale, `C` and `C.UTF-8` and passes in all three. Also in this commit: the 30-second timeout of the ESLint cold-start test (`lib/__tests__/lint-config.test.ts`) is raised.
- [ ] P0.14 [gated] Fix the findings of the third Phase 0 QA gate (`docs/qa/QA-phase-0-2026-10-11-run-3.md`: two Highs, three Mediums), one commit per subtask, same method as P0.12/P0.13: for every finding first a test that reproduces the QA probe and fails, then the fix; the verification line comes from `python -m pytest` and `npm test` in the owner's default terminal. Structural rule: fix the class of error with one mechanism, not another layer on top of the probe. New rule from P0.14 on (also in `docs/CONTRIBUTING.md`): "An item from a sweep that touches a decision boundary or a user-visible claim is fixed, not recorded." The sweep results are listed in the plan the owner approves.
  - [x] P0.14-A Opening day and source shape: QA3-01 (a cutoff before the season start builds the starter with an empty sample and every pitch-based dimension limited, without asking Statcast; the game is published; the test that locked in `None` is rewritten; end-to-end test pipeline → payload) and QA3-02 (one explicit schema per MLB endpoint we consume, validated whole in the fetcher including the inner objects of every populated element; a failure is a recorded source error; a valid empty list stays valid; optional numeric fields stay `None`; negative tests generated from the schema, one per required field; `_attach_sample` does not prefer an API answer without counts over valid Statcast counts).
  - [x] P0.14-B Critic boundaries: QA3-03 (the structured pitch mix carries raw counts and the total; the critic compares the 30% and 15% minimums on counts; the chart stays rounded) and QA3-04 (every critic check that attributes something to a starter uses `_owned_sentences`; sweep of all of `critic.py` listed in the plan).
  - [x] P0.14-C Frontend honesty, sweep, CI and audit record: QA3-05 ("pitch count not available" for null, "0 pitches" for a real zero) plus the sweep of `?? 0`, `|| 0` and `Number(...)` in `components/` and `lib/` (also: a share against a side the starter never faced is unavailable, not 0%, from `_usage_pct` to the panel); the new sweep rule in `docs/CONTRIBUTING.md`; raw `npm audit` output in `docs/qa/audit-2026-10-11.json`. Separate small CI commit: `runs-on: ubuntu-24.04` in the `pytest` job of `tests.yml` (the `components` job already uses it), nothing else.
- [ ] P0.10 [gated] QA gate for Phase 0 (D27). The owner starts Codex with `Run docs/QA_PROTOCOL.md for Phase 0, range v1.0.0-kaggle..HEAD`; the report goes to `docs/qa/`. Phase 0 closes only on PASS, or on PASS WITH CONDITIONS once the listed conditions are met; any Blocker or High is a FAIL and Phase 0 stays open. Run 1 (2026-10-10): FAIL, six Blockers, one High, three Mediums. Run 2 (2026-10-11): FAIL, one Blocker, two Highs, two Mediums, one Low. Run 3 (2026-10-11): FAIL, two Highs, three Mediums. Run 4 happens after P0.14.

### Phase 0 definition of done

```gherkin
Feature: Phase 0 data integrity

  Scenario: As-of cutoff prevents leakage
    Given a game played on 2026-07-15
    When the pipeline runs with as_of 2026-07-14
    Then no Statcast row, season stat, team split or series status is dated after 2026-07-14

  Scenario: Pitcher name is never split
    Given any generated report
    When the text is checked against the starter names in the packet
    Then every starter name appears complete and unbroken

  Scenario: Limited sample is flagged, not filled
    Given a starter below the arsenal sample threshold
    When the report is generated
    Then the arsenal dimension is flagged as limited
    And the report makes no arsenal claim beyond stating the limitation

  Scenario: No games scheduled
    Given a date with no MLB games
    When the live pipeline runs
    Then it exits successfully without errors
    And the run is recorded as no games
    # "the site shows the season archive" is an acceptance criterion of P1.6 (D28)

  Scenario: Data source failure is explicit
    Given Statcast does not respond
    When the pipeline runs
    Then the data mode records the failure
    And no demo data is presented as live

  Scenario: Debut with zero pitches
    Given a starter with no MLB pitches on record
    When the report is generated
    Then every pitch-based dimension is flagged as limited
    And the pipeline does not crash

  Scenario: Live starters carry no demo fields
    Given a live matchup
    When the packet is built
    Then recent form and bio come from real sources or are marked unavailable
    And no field is inherited from demo inputs

  Scenario: Labels use rates, not counts
    Given two starters with the same walk rate and different innings
    When command labels are derived
    Then both receive the same command label

  Scenario: Series status has no leakage
    Given a postseason game already played
    When its series status is fetched with as_of before first pitch
    Then the series status reflects the standing before first pitch, not the final result
    # "the historical dataset builds every postseason case this way" is an acceptance criterion of P2.4 (D28)
```

## Phase 1 — Automation and signals (target Oct 25, closes v2.0-a)

- [ ] P1.0 Workflow security: least-privilege `permissions` (`contents: write`, `models: read` only where needed); secrets only via GitHub Secrets and never printed; third-party actions pinned by commit SHA; no secrets on pull requests from forks. Also update `actions/checkout` and `actions/setup-python` in `tests.yml` to versions that no longer run on Node 20, pinned by commit SHA, and pin the runner to `ubuntu-24.04` instead of `ubuntu-latest`. The bot commits only `public/data/` and `evals/live/` (D15). Pin pandas and numpy (and any other Python dependency CI installs) in `requirements.txt`; today only `pybaseball` is pinned. CI also runs `npx tsc --noEmit`, `npm run lint` and `next build`.
- [ ] P1.1 Test the Statcast fetch from GitHub Actions. If blocked, heavy fetch runs locally and Actions uses the committed cache. Record the result in `DECISIONS.md` via owner approval.
- [ ] P1.2 Daily workflow (cron + manual trigger for testing): today's previews, yesterday's postgame, publish JSON. Count the pitcher Statcast fetch (`statcast_pitcher`) in a request budget with pacing, like the team-batting fetch (D23). D23's 210 covers only team batting, so the budget for pitcher requests needs its own figure: propose it as a new decision (D23 is not edited). The request-budget decision for pitcher fetches also covers the pitcher-hand lookup (today PITCHER_HAND_MAX_REQUESTS_PER_RUN = 10, a constant).
- [ ] P1.3 Several real games per day; no demo rows mixed into live mode. Review D29's open-month budget (10 requests per run, sized for 5 candidate games) for days of up to 15 games.
- [ ] P1.4 Origin and limited-data badges in the frontend (D3). Includes component tests for the explicit "not available", "—", empty and limited states (the component test runner arrives earlier, in P0.12-C; this task adds the tests for those states).
- [ ] P1.5 Postseason layer: series context + draft + debut + birthplace as cited claims (D7). Handle international signings with no draft record.
- [ ] P1.6 Offseason state on the site. Acceptance criterion (D28): on a date with no MLB games, with a `no_games` run record, the site shows the season archive, not demo content.
- [ ] P1.7 Daily append-only log under `evals/live/` even while only the rules writer runs (monitoring starts here).
- [ ] P1.8 Keep-alive: verify GitHub's inactivity rule for scheduled workflows and add a heartbeat (e.g. a monthly commit to `evals/live/heartbeat.txt`) so the daily job survives the offseason.
- [ ] P1.9 Data attribution and disclaimer on the site (MLB / Baseball Savant), no monetization of any kind, cached fetches and no bulk downloads (D16).
- [ ] P1.10 [auto] Web Analytics (D26): install `@vercel/analytics`, add `<Analytics />` to the root layout (`app/layout.tsx`) and create the `/quality` route (its content is P3.2). Page views only. Read the Next.js docs in `node_modules/next/dist/docs/` first. Clicking Enable in the Vercel dashboard is the owner's step at the merge of v2.0-a into `main`, not before.

## Phase 2 — LLM writer and eval (target Nov 8)

- [ ] P2.1 AI Studio API key + test call; GitHub Models access. Keys only in env vars / GitHub secrets.
- [ ] P2.2 LLM writer behind the same interface as the rules writer, with `claims[]`, a versioned prompt and an exact model ID pinned in config. Output is schema-validated before it can reach the public JSON; free-text MLB fields are passed as quoted data, never as instructions. No `dangerouslySetInnerHTML` anywhere in the frontend.
- [ ] P2.3 Guardrail: informed retry and fallback to rules (D2).
- [ ] P2.4 40-case dataset with `as_of`, stratified; test split frozen. Historical case builder raises if `as_of` is None. Acceptance criterion (D28): every postseason case carries the series status as of `game_date − 1` (the standing before first pitch), never the final result. Before building the dataset (D32): recompute the lineup cut-offs (K% 23.0, BB% 9.0, OPS .750) from the 2026 quartiles of team lineups against each pitcher hand, as D25 did for starters, and record the result as a new decision that supersedes D32 if the values change.
- [ ] P2.5 Human labels (G2, L1, U1) — owner task, ~6–8 hours, reserved in the week of Oct 19–25 and finished before Nov 1.
- [ ] P2.6 Code evaluators and judge; calibration on dev. If GitHub Models is unavailable in the daily run, G2 is logged as `not_evaluated` and publishing continues (D17).
- [ ] P2.7 Baseline run A vs. B1; error analysis; one change; B2 run.

## Phase 3 — Publish (target Nov 15)

- [ ] P3.1 v2.0-b decision using the eval rule.
- [ ] P3.2 Quality page on the site.
- [ ] P3.3 Case study on danielherdenez.com and pm-ai-playbook — owner task.
- [ ] P3.4 README, ARCHITECTURE, RUNBOOK, CHANGELOG.

## v2.1 — Spanish (after v2.0-b)

- [ ] L10N.1 Finish D6 as scoped by D31. Separate a label's identifier from its visible text in `labels.py` (today the English text is also the value that code compares, and that is stored in the JSON); move the generator's texts (data mode and its reasons, confidence note, agent workflow, archive labels, offense split labels) and the frontend copy into catalogs; add the Spanish catalog of the five agents (`agents/messages_es.py`, same keys as `messages_en.py`); the writer and the eval take `language` end to end, and the eval checks Spanish reports (D6).

## Backlog after v2 (not scheduled)

- [ ] Ground-ball rate as the replacement for the contact-risk label (D24 leaves contact risk as a count). It stabilizes at about 70 balls in play (FanGraphs Sample Size); Statcast supplies batted-ball type. Needs its own threshold decision.
- [ ] Carry-over of the previous season for April. D24 uses current-season data only, so early in the season most starters are flagged (April: 26% of starts flagged on arsenal, 58% on strikeout, 100% on control). Needs a decision on how to weight the previous season.
- [ ] Automatic monthly summary of visits per route: the Hobby reporting window is one month (D26), so the numbers should be saved each month (for example into `evals/live/`) before they age out.
- [ ] Per-game routes (for example `/game/<id>`), so that views per game can be measured with page views alone (D26).

## Open questions (owner)

- [ ] Confirm eval success thresholds (`eval-spec.md` section 1).
- [ ] Define what makes postseason report text different (D7).
- [ ] Final badge copy (D3).
- [ ] Report length range for F1, after reading 10 rules-based reports.

## Outside the repo (owner, Notion HQ)

- [ ] HQ — Evidencia y portfolio: replace "eval de feature IA en Veflo" with PitchCraft v2; update AWS status.
- [ ] HQ — Ruta Fase 1 v3.1: reflect the two-step rollout in the eval calendar.
- [ ] HQ — Metas y objetivos: eval goal on PitchCraft, not Veflo; AIF no longer a firm goal.
- [ ] CV and site: no changes until v2 is published.
