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
- [ ] P0.3 [auto] Check whether the MLB Stats API supports team splits by date range. If not, derive them from Statcast with the same cutoff. Record the finding in `STATUS.md`.
- [ ] P0.4 [gated] Measure the real 2026 distribution (pitches, batters faced, walks) and present proposed per-dimension thresholds (D11) to the owner. Do not implement thresholds until the owner approves; record the approved values in `DECISIONS.md`.
- [ ] P0.5 [gated] Rate-based labels (K%, BB%, HR rate) in a single module, using the thresholds approved in P0.4. Remove the duplicated count-based logic in `live_pipeline.py` and `generate_demo_json.py`. Fix the `total_pitches` calculation (currently sums percentages).
- [ ] P0.6 [auto] Fix the name-split bug in `agents/report_writer.py` (`_watch_observation`).
- [ ] P0.7 [auto] Remove the hardcoded season year (2026, `2026-03-20`).
- [ ] P0.8 [auto] Explicit data mode and error log instead of the silent fallback to demo.
- [ ] P0.9 [auto] Hygiene: upgrade Next.js to 16.4.0 (fixes `npm audit` critical/high findings; read `node_modules/next/dist/docs/` first); delete `pitchcraftvisualpolish.bundle` (stray git bundle); pin `pybaseball==2.2.7`; move or delete `test_splits.py`. `npm audit --omit=dev` must report 0 critical and 0 high.

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
    When the daily job runs
    Then it exits successfully without errors
    And the site shows the season archive

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
    When it is fetched for the historical dataset
    Then the series status reflects the standing before first pitch, not the final result
```

## Phase 1 — Automation and signals (target Oct 25, closes v2.0-a)

- [ ] P1.0 Workflow security: least-privilege `permissions` (`contents: write`, `models: read` only where needed); secrets only via GitHub Secrets and never printed; third-party actions pinned by commit SHA; no secrets on pull requests from forks. Also update `actions/checkout` and `actions/setup-python` in `tests.yml` to versions that no longer run on Node 20, pinned by commit SHA, and pin the runner to `ubuntu-24.04` instead of `ubuntu-latest`. The bot commits only `public/data/` and `evals/live/` (D15).
- [ ] P1.1 Test the Statcast fetch from GitHub Actions. If blocked, heavy fetch runs locally and Actions uses the committed cache. Record the result in `DECISIONS.md` via owner approval.
- [ ] P1.2 Daily workflow (cron + manual trigger for testing): today's previews, yesterday's postgame, publish JSON.
- [ ] P1.3 Several real games per day; no demo rows mixed into live mode.
- [ ] P1.4 Origin and limited-data badges in the frontend (D3).
- [ ] P1.5 Postseason layer: series context + draft + debut + birthplace as cited claims (D7). Handle international signings with no draft record.
- [ ] P1.6 Offseason state on the site.
- [ ] P1.7 Daily append-only log under `evals/live/` even while only the rules writer runs (monitoring starts here).
- [ ] P1.8 Keep-alive: verify GitHub's inactivity rule for scheduled workflows and add a heartbeat (e.g. a monthly commit to `evals/live/heartbeat.txt`) so the daily job survives the offseason.
- [ ] P1.9 Data attribution and disclaimer on the site (MLB / Baseball Savant), no monetization of any kind, cached fetches and no bulk downloads (D16).

## Phase 2 — LLM writer and eval (target Nov 8)

- [ ] P2.1 AI Studio API key + test call; GitHub Models access. Keys only in env vars / GitHub secrets.
- [ ] P2.2 LLM writer behind the same interface as the rules writer, with `claims[]`, a versioned prompt and an exact model ID pinned in config. Output is schema-validated before it can reach the public JSON; free-text MLB fields are passed as quoted data, never as instructions. No `dangerouslySetInnerHTML` anywhere in the frontend.
- [ ] P2.3 Guardrail: informed retry and fallback to rules (D2).
- [ ] P2.4 40-case dataset with `as_of`, stratified; test split frozen. Historical case builder raises if `as_of` is None.
- [ ] P2.5 Human labels (G2, L1, U1) — owner task, ~6–8 hours, reserved in the week of Oct 19–25 and finished before Nov 1.
- [ ] P2.6 Code evaluators and judge; calibration on dev. If GitHub Models is unavailable in the daily run, G2 is logged as `not_evaluated` and publishing continues (D17).
- [ ] P2.7 Baseline run A vs. B1; error analysis; one change; B2 run.

## Phase 3 — Publish (target Nov 15)

- [ ] P3.1 v2.0-b decision using the eval rule.
- [ ] P3.2 Quality page on the site.
- [ ] P3.3 Case study on danielherdenez.com and pm-ai-playbook — owner task.
- [ ] P3.4 README, ARCHITECTURE, RUNBOOK, CHANGELOG.

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
