# Phase 2 draft plan: LLM writer and eval through the Nov 15 case study

Draft for owner review, 2026-10-24. This file authorizes no implementation,
provider calls, data collection, workflow changes, branch migration or release.
Committing this draft is a separate approval from approving its proposals.
The only file changed by this drafting task is `docs/plans/P2-draft.md`;
no Phase 2 checkbox is completed.

Goal: complete P2.1-P2.7 with credible evidence for P3.1 and publish the P3.3
case study on November 15, whether the decision is to ship the LLM or keep
the rules writer. Phase 2 targets November 8; November 9-10 is contingency,
and November 11 is the final evidence cutoff for the case study.

Architecture proposal: retain the rules writer as the default and fallback.
Add one Gemini Flash writer behind its existing interface, a bounded retry,
an offline comparison on fixed packets, and a cross-family judge. Resolve
the claims-contract conflict before permitting generated prose into a payload.

Stack: existing Python pipeline, pytest, Next.js/TypeScript and Vitest;
Gemini through AI Studio for writing and GitHub Models for judging (D9).
Exact provider model IDs, quotas and supported response formats must be
verified in P2.1; this draft assumes none of their current values.

Sources: [PLAN, Phases 2 and 3](../PLAN.md#phase-2--llm-writer-and-eval-target-nov-8),
[eval spec](../eval-spec.md), [decisions](../DECISIONS.md),
[data contract](../DATA_CONTRACT.md), [PRD](../PRD_v2.md),
[engineering practices](../ENGINEERING.md), [contributing](../CONTRIBUTING.md),
[P1-R2 backlog, item a](P1-R2.md#a-save-the-approved-plan-and-backlog),
[current handoff](../STATUS.md) and
[release-2 QA](../qa/QA-release-2-2026-10-24.md).

## Starting conditions and scope

The PLAN tasks covered are P2.1-P2.7, the LLM writer and its evaluation.
P3.1-P3.4 appear here to reserve the time and inputs they need; their work
requires its own approved scope. All P2 tasks are currently unlabelled and
therefore gated under D22. The P1-R2 d-g autonomy amendment does not extend
to Phase 2. Codex still needs the owner's yes for every commit under D35's
fallback unless the owner explicitly approves a different arrangement.

STATUS still lists release-2 QA as next. The newer committed report
`30f6f4c` records PASS on implementation through `51b24ef`; this draft does
not independently rerun or certify that QA. Before Phase 2 execution, the
owner accepts that report and confirms the release PR, Vercel READY and the
first scheduled bot publication on `main`. Reconcile outstanding P1.0,
P1.2 and P1.5 checkboxes with their evidence; do not infer completion from
the P1-R2 checkbox alone. Keep P1.3 and other unrelated backlog work out.

P1.7, the deferred append-only monitoring log, is a real dependency of the
P2.3/P2.6 daily guardrail and P3.2 quality page. Reserve its narrow completion
inside their approved integration scope. P1.4's writer-origin signal also
needs a narrow integration step: show the actual writer used after fallback.
Neither item expands into a general badge redesign or multi-game project.

English only, with `language` passed end to end (D6/D31). Retain current
sample and pitch-role rules (D24/D25/D30), scopes, honest modes and the
whole-file integrity stop (D34/D42). No automated postgame, bios, Spanish,
new pitch-quality metrics, analyst redesign or comparison of several models.

## Product acceptance: owner feedback F5 and F7

These are the owner's prose and movement feedback, carried together in the
P1-R2 backlog. They are distinct from the historical F5/F7 data-contract
findings, which concern game state and team abbreviations.

- F5, fan-friendly prose: explain the two starters' contrast in words a
  casual fan can follow, explain necessary jargon when first used, reduce
  repetitive labels, and give concrete things to watch. Preserve both
  starters, both available offense reads and each dimension's limitation.
  A shorter report that removes needed qualifications fails honesty.
- F7, movement explanations: describe the available measured horizontal
  and vertical movement in plain words, with the existing no-spin reference.
  Cite the correct starter and pitch. A measured zero remains a measurement;
  missing movement stays unavailable. Suppress pitch descriptions for a
  limited arsenal or unmapped family. Use the approved sideways wording;
  arm-side/glove-side direction has no verified convention in this repo.
  Do not infer deception, effectiveness, intended location, hitter reaction
  or an advantage from break inches alone. Comparisons need measurements
  for both pitches and the same reference; otherwise omit the comparison.

P2.2 gets owner review of ten dev examples across the four strata before
B1 is frozen. Add F5/F7 observations to U1's one-line human reasons and
failure categories; retain the agreed U1 binary and pairwise decision rule.
Include examples with available movement, zero, missing movement and a
limited starter. Do not claim improvement from prose that exists only in
unrendered JSON: verify the text in the existing visible report fields.
Changes to report visibility beyond those fields require another scope approval.

## Decisions required before dependent work

Recommendations below are proposals. Approval to store this draft does not
approve them. Record approved policy changes through new decision entries;
never silently override an existing decision or contract rule.

| Owner decision | Needed by | Proposal and consequence |
|---|---|---|
| Claims representation and prose freedom | Oct 27, before P2.2 | Approve a narrowly scoped extension for LLM prose, with an explicit schema version, sentence-to-evidence mapping, subject, text location and independent validation. Keep catalog claims for rules/generated fixed text. Update D34's rule 4 through a new decision and reconcile the eval spec. This is the largest engineering risk. |
| Claim-contract alternative | Same decision | A catalog-only LLM can select/order approved fan-friendly phrases under the current rule 4. It costs less and preserves deterministic rendering, but tests constrained composition and may not improve F5/F7 enough. Recommend the prose extension only if its boundary can be proven by Nov 2; otherwise keep rules live and document the constrained/offline experiment accurately. No raw-string bypass. |
| Task order and dates | Oct 27 | Approve P2.4 before P2.2 and move P2.5's obsolete Oct 19-25 reservation / before-Nov-1 deadline to Nov 4-6. Amend PLAN and eval milestones in the later approved task, leaving the frozen test protections intact. |
| Thresholds and measurement protocol | Oct 27-28, before dataset/B1 | Confirm the spec's 95% groundedness, 100% policy, 70% U1 wins-or-ties and 85% judge-human agreement per judged dimension. Define G1 rounding tolerance from actual display precision, F1 length after ten A reports, tie handling and denominators. Predeclare first-attempt candidate scores as the primary writer comparison; report retry/fallback results separately. |
| D32 lineup cutoffs | Oct 28, before P2.4 packets | Review the 2026 team-vs-hand quartiles and analysis method. If any of 23.0% K, 9.0% BB, .750 OPS changes, approve a superseding decision before producing findings; freeze the same approved inputs for A/B1/B2. Record unchanged values with the analysis if they stay. |
| Credentials, models and $0 capacity | Oct 27 | Owner creates/configures secrets; approve exact writer/judge IDs after access tests. Verify the judge is a different family, and that both fit a paced, cached, resumable $0 run. No paid fallback or model substitution during an experiment. |
| Writer origin, daily integration and new public fields/copy | Before P2.2/P2.3 integration | Approve exact origin/limited-data copy and claim/schema changes, including snapshot compatibility. Any additional public error code also needs approval. Provider errors and retry internals stay out of the public payload. Approve workflow edits separately before making them. |
| Human review and release | Reserve Oct 27; act Nov 8-14 | Commit the labeling/review hours below, choose the independent phase QA session, accept its result, and make P3.1's ship/no-ship decision. A fallback to rules is a valid outcome, not a reason to relax the thresholds. |
| Task branches and PRs | Optional after Nov 15 | Approve the migration in its own decision and task plan. Until then D14/D20/D35/D41/D42 and the current git guard remain binding. |

The eval spec's `claims[] = {text, evidence: [json_path], value_cited}` is
incompatible with today's published `{id, key, args, subject, location}`.
`data_pipeline/claims.py` also rejects ordinary strings in claimed fields;
the current critic/report-facts vocabulary is built around catalog phrases.
A valid provider JSON response or an approving judge does not resolve this.
The approved design must cover sentence completeness, path ownership,
numbers, subject attribution, limited flags, scope/time wording and the
independent contract checker, while retaining the final publication gate.

## Order, dependencies and task deliverables

Use one writer and one reviewed commit per PLAN task, with the approved
decision records and handoff updates included in that task. A decision
needed by P2.2 must be settled before work proceeds; grouping it in a task's
eventual commit does not defer approval. Suggested order:

`P1 release accepted -> P2.1 -> P2.4 -> P2.2 -> P2.3 -> A/B1 capture ->`
`P2.5 -> P2.6 -> P2.7 -> independent Phase 2 QA -> P3.1-P3.4`.

P2.7's A/B1 capture must precede P2.5, even though the final comparison and
B2 belong to P2.7. This sequencing change needs the owner's approval.
P2.6 calibration depends on dev labels; preparation of its shared code
checks belongs in P2.3 so the guardrail never waits for an offline judge.
The owner can label sealed reports while the agent builds the evaluators;
the agent may see dev labels only until B2 and judge versions are frozen.

### P2.1: establish access and a reproducible configuration

Proposed files: `agents/writer_config.py` (new), the dependency manifest if
an SDK is needed, `.env.example` with names only, and configuration/access
tests. Keep provider clients separate from orchestration.

- [ ] Owner installs the AI Studio key locally and the appropriate GitHub
  Models credential/access; confirm intended daily-run access separately
  from local access. Never display tokens or store them in prompts/results.
- [ ] Verify official provider documentation at execution time. Make one
  small writer call and one cross-family judge call using public/synthetic
  input; record model IDs, response-format support and observed limits.
- [ ] Fix model ID, temperature, prompt version and cache-key inputs.
  Version changes require a new run identity. Persist responses by input
  hash, model/config and prompt version; support quota pauses and resumption.
  Calculate the call budget before authorizing the full experiment. The
  minimum official writer workload is 40 B1 plus 20 held-out B2 generations,
  up to 120 calls if every case uses both allowed attempts. Judge workload
  includes G2/L1 assessments of 100 A/B1/B2 reports and 60 U1 pairs; request
  counts depend on permitted batching. Add explicit allowances for probes,
  ten-example previews, any B2 dev runs and every dev calibration pass.
  Fit that full budget to observed daily limits and the Nov 3/8 deadlines.
- [ ] Exit: both local paths work, daily authentication requirements are
  recorded, mocks cover auth/quota failure without network, and the
  remaining calendar fits the observed quota. No live writer is enabled.

### P2.4: freeze data and shared inputs before writer tuning

Proposed files: `evals/build_dataset.py`, `evals/data/cases.jsonl`,
`evals/data/manifest.json`, a split manifest and dataset/leakage tests;
use `data_pipeline/fetchers/live_pipeline.py` and existing caches. Add a
lineup-threshold analysis document and touch `labels.py` only if approved.

- [ ] Recompute D32's quartiles first. Record population, cutoff, two pitcher
  hands, sample eligibility, rounding and cache provenance; get the owner's
  threshold decision. This is policy calibration on 2026 data: disclose it
  as retrospective calibration, not evidence of a prospective time split.
- [ ] Assign 40 real 2026 matchups to four mutually exclusive primary strata:
  10 high-data veterans, 10 limited-sample starters, 10 openers/bullpen or
  missing-data cases, 10 postseason. Use five of each in dev and five in
  test. Record overlapping traits without double-counting cases. Do not
  fabricate missingness to fill the real-data dataset; use mutations in tests.
- [ ] The historical builder rejects `as_of=None` and requires the explicit
  previous official game day (America/New_York). All fetched stats and
  source rows stop at that cutoff. For all ten postseason cases, show the
  standing before first pitch, not the game/series final result (D28/D29).
  Include a Game 1 control and later-game standing checks.
- [ ] Inventory cached inputs before fetching. D16 permits this 40-case set
  once, cached, non-bulk and attributed. Keep a collection-wide request
  ledger and existing D23/D29/D42 caps/pacing; batching must not evade the
  210 closed-month ceiling, 10 open-month requests, 20 pitcher requests or
  10 hand lookups per run. Prefer up to five games per collection batch.
  Escalate an insufficient budget; do not increase caps. Dataset collection
  is a separately approved activity, never a fourth daily-workflow rehearsal.
- [ ] Save fetch timestamps, `as_of`, source/cache digests, strata, split and
  packet/findings hashes. Freeze test membership and inputs before any B1
  experiment. A, B1 and B2 consume identical stored packets and findings.
  Do not refetch between versions or expose future outcomes to either model.
- [ ] Exit: 40 complete, reproducible cases, 20/20 split, explicit-cutoff
  rejection and postseason leakage tests seen red then green; no test data
  inspected for prompt tuning. Preserve missing data honestly in the packet.

### P2.2: implement the writer and its approved claims boundary

Proposed files: `agents/llm_report_writer.py`, a provider adapter,
`agents/prompts/report_writer_v1.*`, `agents/writer_config.py`, and focused
writer/claim tests. Reuse `agents/report_writer.py` as A/fallback. The approved
contract option may also require `data_pipeline/claims.py`, `schema.py`,
`validators.py`, `claims_registry.py`, `contract_checks.py`, `report_facts.py`,
`provenance.py`, `agents/critic.py`, `lib/types.ts` and the contract registry.
Map the exact coordinated schema/readers change in P2.2's approval plan.

- [ ] Keep the public call shape
  `run(findings, matchup_input, language=DEFAULT_LANGUAGE) -> dict[str, Any]`.
  The packet subset includes per-dimension flags, own/opponent identities,
  scopes and already-published movement evidence needed for F7. No new
  analyst interpretation or metric is added to give B an undisclosed advantage.
- [ ] Treat MLB names and other free text as quoted data. Separate prompt
  instructions from the packet. Reject injected instructions, extra keys,
  malformed output, absent claims and cross-starter evidence. All factual
  sentences, including those in fields not rendered, need valid evidence.
- [ ] Add genuine negative tests for an invented number, valid path with
  wrong value, correct value cited for the other starter, uncited qualitative
  assertion, limited-dimension praise, invalid movement interpretation,
  scope mismatch and stale time language. Passing controls include real
  zero, missing measurement, Game 1 and both starters sharing a pitch name.
- [ ] Review ten dev examples for F5/F7 and fix B1 on dev only. Freeze its
  prompt/model/config before the official A/B1 capture. Keep A's writer
  behavior fixed; use the same agreed packet and format/claim extraction
  rules. Document the existing name-split regression test as a baseline control.
- [ ] Exit: both writers use the same interface, every accepted report
  survives the actual critic/contract/publication path, malicious outputs
  are rejected, and existing visible report fields show the approved prose.
  Rules remain the production default pending P3.1.

### P2.3: put the guardrail before publication

Proposed files: `agents/writer_guardrail.py`, `evals/code_evaluators.py`,
`evals/live_log.py`, writer orchestration in
`data_pipeline/generate_demo_json.py` / `daily.py`, and guardrail/log tests.
Any `.github/workflows/daily.yml` or source-badge change needs explicit
owner approval. The deployed bot owns actual `evals/live/` and public data.

- [ ] Run schema, G1, P1, C1, F1, code-L1 and required contract checks before
  accepting a candidate. A technical/content failure gets one informed
  retry with structured errors (D2), then validated rules fallback. There
  are at most two writer calls. If fallback or final integrity validation
  fails, keep the prior public file and record the failure (D34/D42).
- [ ] Test valid first attempt, malformed/timeout first attempt then success,
  bad content twice then rules, exhausted quota, and unsafe rules fallback.
  Include a two-game run and a no-games day. No-games invokes neither
  writer nor judge; do not create fictional scored-report rows.
- [ ] Complete the narrow P1.7 dependency: append-only rows with game ID,
  actual writer, pinned model, prompt/evaluator versions, attempt outcomes,
  fallback and per-dimension result/reason. Retain failed attempts without
  raw secret/provider error messages. Resume without losing prior evidence
  or duplicating successful work; separate offline files from daily logs.
- [ ] Verify D17: an unavailable daily judge records G2 `not_evaluated`,
  never a pass; code checks still gate publication. A completed semantic
  judgment is retained as monitoring, with no invented runtime veto policy.
  U1 remains offline. Test this before adding any daily credential wiring.
- [ ] Exit: fallback is visible as rules-origin, all attempts are traceable,
  rules default still works without model credentials, and deterministic
  CI tests use no MLB/Savant/provider requests.

### A/B1 capture and P2.5: reserve the owner's labeling time

Proposed artifacts: immutable versioned A/B1 outputs under `evals/runs/`,
blinded labeling packets, `evals/labels/` and a codebook. Keep the identity
key and sealed test labels out of the implementer's tuning material.

- [ ] After dataset, B1 and code-check versions are fixed, generate A/B1 for
  all 40 cases, cached/resumable. Show API failures and generation failures;
  do not replace cases, repeatedly sample for a passing result or score the
  rules fallback as a successful LLM candidate. Report guarded outcomes
  alongside the primary first-attempt comparison.
- [ ] Owner labels G2 and L1 separately for each A and B1 report, plus one
  randomized-order U1 comparison for each pair, with one-line reasons.
  This is 80 report readings, 160 G2/L1 decisions and 40 U1 pairs. Preserve
  win/tie/loss for U1 and derive its binary wins-or-ties result consistently.
- [ ] Dev reasons can guide judge calibration and B2. Seal test outputs,
  labels, errors and aggregate results until the judge and B2 are frozen.
  Owner test labeling must not leak examples or category counts to the
  implementer. The owner may spot leakage and halt a run, never tune on it.
- [ ] Exit: all 40 A/B1 cases labelled; missing labels are explicit and block
  the relevant offline conclusions. Reserve 6-8 owner hours, not agent time.

### P2.6: calibrate evaluators and the cross-family judge

Proposed files: `evals/code_evaluators.py`, `evals/judge.py`,
`evals/prompts/judge_v1.*`, `evals/run.py`, calibration tests and a versioned
calibration report. Integrate the existing P2.3 checks rather than duplicating
their definitions. Daily integration uses the approved P2.3/P1.7 boundary.

- [ ] Score G1, P1, C1, F1 and code-L1 with the same definitions for A and B.
  A's claim-extraction pass must be checked against known catalog evidence;
  extractor failure is reported, not a pass or an excluded report.
- [ ] G2 evaluates qualitative entailment and sentence coverage; L1 respects
  each flag; U1 assesses a casual fan's understanding of the duel and what
  to watch. Randomize pair order, retain the seed, and test order reversal.
  Invalid/refusing/quota-limited judge responses are missing evaluations.
- [ ] Tune only on dev human labels. Freeze judge prompt/model/evaluator
  version before inspecting test results. Report test agreement separately
  for G2, L1 and U1, including per-system counts, TPR/TNR and confusion
  matrices. If a class has no examples, its rate is undefined, not 100%.
  Predeclare handling of ties, abstentions and applicable L1 denominators.
- [ ] Exit: dev calibration is complete, judge/evaluator versions are pinned,
  and the held-out trust protocol is frozen. Held-out trust acceptance is
  measured and reported in P2.7 after B2/judge freeze; test evidence stays
  sealed until then. A missed trust threshold withholds the ship
  recommendation. D17's online availability exception never substitutes
  for offline evidence.

### P2.7: explain B1 errors, make one change, evaluate B2

Proposed artifacts: `evals/reports/error-analysis.md`, `evals/runs/` manifests,
`evals/reports/comparison.*` and one versioned B2 prompt/packet/contract
change with its regression tests. No new model comparison.

- [ ] Open-code every B1 dev failure and count categories, including F5
  jargon/repetition, F7 unsupported movement stories, numbers, limited
  dimensions, attribution, policy and format. Choose one change aimed at
  the largest actionable category; record the hypothesis before B2 runs.
  Do not manufacture a failure if dev is clean; ask the owner how to report
  the absence of the spec's planned iteration.
- [ ] Freeze that single B2 change using dev evidence only. Run B2 once on
  the unchanged test inputs; cache and resume the same run across quota
  pauses. If packet or contract changes would invalidate shared inputs or
  A/B1 comparability, stop for scope approval rather than mutating the set.
- [ ] Owner supplies additional blind B2 test labels for judge trust and U1
  against the fixed A; reserve 2-3 hours beyond P2.5. Reuse A human labels.
  Report A/B1/B2, paired outcomes, stratum counts, failures, retry/fallback
  rates, missing evaluations and exact denominators. Keep B1 test evidence
  sealed until B2/judge freeze, then release all comparisons together.
- [ ] Exit: reproducible comparison and a written ship/no-ship recommendation,
  followed by independent Phase 2 QA under D27. With 20 test cases, 95%
  groundedness means at least 19/20 and 70% U1 means at least 14/20; policy
  requires 20/20. Judge trust is at least 85% in each agreed denominator,
  never a pooled average that hides one weak dimension. Report uncertainty
  and the small sample; the percentages are not population guarantees.

## Calendar: October 27-November 15, 2026

All dates use America/Bogota. Assume one implementing agent/writer with
4-6 focused hours per working day, owner approvals available within one
day, and the owner hours explicitly reserved below. Estimates include
testing/review and one ordinary correction per task; provider waiting and
phase QA can consume contingency. Oct 31-Nov 1 are buffer, not mandatory
full workdays. This is feasible with those reservations, not a promise of
unlimited agent throughput or free-tier capacity.

| Date | Agent / evidence deliverable | Owner reservation and checkpoint |
|---|---|---|
| Tue Oct 27 | 4-5 h: release evidence check, claims/measurement decisions, P2.1 access/config and call-budget preflight. | 1.5-2 h: accept Phase 1 QA/release evidence, credentials, contract/order choices, calendar. Finish release checks if pending; unresolved prerequisites consume buffer. |
| Wed Oct 28 | 5-6 h: D32 quartile analysis, request/cache inventory, P2.4 cutoff and series tests. | 0.5-1 h: threshold approval and dataset sampling review. No dataset build before approval. |
| Thu Oct 29 | 5-6 h: finish/cache 40 cases and freeze 20/20 inputs/manifests; run A and prepare ten dev examples/length counts. | 1 h: approve F1 range, tolerance and ten-report prose/movement rubric. |
| Fri Oct 30 | 5-6 h: P2.2 writer, approved schema/claim boundary and negative controls. | 0.5 h: required schema/copy decisions and commit review. |
| Sat Oct 31-Sun Nov 1 | Up to 4 h total contingency for data/quota/contract problems; no new scope. | No labeling deadline: this draft explicitly moves it. Optional 0.5 h approval availability. |
| Mon Nov 2 | 5-6 h: finish P2.2 real publication-path tests; P2.3 guardrail and log integration. | 0.5 h: review ten B1 dev examples and approved origin text. Hard checkpoint: claims boundary works or stop public-LLM path. |
| Tue Nov 3 | 5-6 h: finish P2.3 checks, freeze B1, capture official A/B1 and blind/seal packets. Begin P2.6 runner/judge preparation without test inspection. | 0.5 h: approve readiness/commits and receive labeling packets. If B1 capture is incomplete, revise labeling slots immediately. |
| Wed Nov 4 | 4-5 h: evaluator negatives and dev judge calibration as labels arrive. | P2.5: 2 h, codebook plus first 10 pairs. |
| Thu Nov 5 | 4-5 h: finish P2.6 judge/calibration on dev; P1.7 monitoring summary boundary. | P2.5: 2-3 h, next 15 pairs. |
| Fri Nov 6 | 4-5 h: freeze evaluators/judge; open-code dev failures and choose the single B2 change. | P2.5: 2-3 h, final 15 pairs; seal test labels. Approve B2 hypothesis from dev evidence. |
| Sat Nov 7 | 3-4 h: implement/test one B2 change, freeze it and start held-out B2 run. | 0.5 h: review single change; no test feedback to the writer. |
| Sun Nov 8 | 3-4 h: finish B2, unseal comparisons after freezes, produce P2.7 report and QA handoff. Phase 2 target. | 2-3 h: additional B2 test labels, judge-trust/U1 review. Offline no-ship remains acceptable. |
| Mon Nov 9 | Independent Phase 2 QA, up to one day; implementer responds only after findings. | 0.5-1 h: review findings and scope any correction. |
| Tue Nov 10 | Contingency: focused correction, full verification and independent recheck. Otherwise prepare P3 evidence/docs. | 0.5 h: accept QA and P3.1 recommendation when ready. |
| Wed Nov 11 | Freeze final evidence at 18:00; P3.1 decision. Incomplete evidence means keep rules and state which P2 items remain open. | 0.5-1 h: ship/no-ship decision and case-study outline. No threshold changes after results. |
| Thu Nov 12 | P3.2 minimal quality page and P3.4 docs, from approved text and fixed result artifacts. | P3.3: 2 h drafting the case on danielherdenez.com and pm-ai-playbook. |
| Fri Nov 13 | Finish P3.2/P3.4 verification/review; owner release PR and deployment evidence if approved. | 1-1.5 h: release/preview checks and final copy approval. Keep LLM disabled if gates are incomplete. |
| Sat Nov 14 | Release/case-study correction buffer; no new writer iteration or model switch. | P3.3: 2-3 h editing, screenshots, citations and preview. |
| Sun Nov 15 | Final links and publication check; report what actually shipped. | P3.3: 1 h publish both destinations and check links. |

Engineering estimate through the P2.7 report: about 47-62 focused hours,
plus independent QA and its correction buffer. P3.2/P3.4 need another
8-12 hours on Nov 11-13. If available capacity is lower, invoke the cuts
below immediately; do not borrow the owner's labeling hours for coding.

Owner workload: P2.5 is 6-8 hours, B2 labels another 2-3, P3.3 drafting and
publishing 5-6, and decisions/release/QA review approximately 7-10 hours.
Reserve roughly 20-27 hours total, with P2.5's blocks protected. The table's
short approval slots share this last allowance; they are not additional
labeling time. Weekly review of 3-5 actual live reports (D8) needs a further
30-45 minutes when there are reports; a no-games day supplies none.

## Slip rules and protected scope

| Trigger | Cut or reschedule | Preserve / effect on Nov 15 |
|---|---|---|
| Oct 27 decisions or release prerequisite still unresolved Oct 29 | Drop branch migration from this window, all optional UI polish and extra provider experiments; use weekend buffer. | Keep credentials, claims decision, real data and owner labeling time. Re-estimate before committing to a public LLM. |
| Dataset or claims boundary not ready by Nov 2 | Keep rules production. Continue an honestly labelled offline or catalog-constrained study only if the owner approves its scope. | Do not bypass the contract or fabricate cases. A reduced pilot is exploratory and does not complete P2.4/P2.7 or justify shipping. |
| A/B1 packets not available Nov 3 | Move P2.5 blocks with explicit owner agreement and spend Nov 9-10 contingency. | Keep 40 cases and 20 held-out tests. If 6-8 hours cannot be reserved, report incomplete human evidence and withhold shipping. |
| Quota delay or untrusted judge by Nov 8 | Resume the identical cached run through Nov 10. No multi-model search; no recalibration on test. | D17 permits daily publication without a judge; it does not establish offline judge trust. Keep rules if required offline evidence remains missing. |
| One B2 change or QA fixes exceed Nov 10 | Stop iteration. Publish A/B1 and any valid B2 evidence, marking unfinished tasks. | Do not call Phase 2 complete or enable an unevaluated B2. Keep Nov 11 evidence freeze and Nov 15 case study. |
| P3 work slips | Use a simple quality table with methodology, decision, artifact links and explicit missing monitoring; shorten the case narrative and documentation polish. | Retain P3.2's honest evidence, essential setup/runbook/architecture notes, both case-study destinations and source attribution. Interactive charts can wait. |

Never cut leakage checks, per-dimension honesty, policy checks, schema and
contract validation, rules fallback, attempt logging, independent QA or
the agreed ship rule. Do not count a retry/fallback as an LLM success or
unavailable monitoring as a pass. Do not mark an unfinished P2 task done
because the case-study deadline arrived.

## Risks and how the plan contains them

| Risk | Response and stop condition |
|---|---|
| Free prose invalidates the old catalog-based safety checks | Make the new claim boundary an owner decision and the Nov 2 stop. Test independent semantic/subject checks; a schema-only check is insufficient. Preserve the final integrity stop. |
| F5/F7 gains require new facts or unsupported baseball explanations | Restrict B to existing measurements/findings, approved definitions and actual visible fields. Label readability and movement errors explicitly; do not manufacture a tactical effect from movement. |
| Dataset fetch cost or historical leakage | Cache inventory, collection ledger, existing caps and explicit previous-day cutoff at the builder boundary. Every postseason case has an auditable standing. A budget/leakage defect blocks the dataset. |
| Human time or judge trust is underestimated | Book P2.5 before coding and budget B2 labels separately. Report agreement by dimension and stratum, absent classes and missing labels. Human work cannot be replaced with judge self-labeling. |
| Test contamination through error analysis or a model change | Freeze inputs before B1, expose dev only, seal B1 test evidence until B2/judge freeze, record the one-change hypothesis and all run digests. A contaminated split cannot decide release. |
| Provider free-tier access changes or differs on Actions | Verify access/quotas in P2.1, use small probes, hash caches and resumable local offline runs. Offline judge unavailability blocks evidence; daily unavailability follows D17. No paid fallback by assumption. |
| Offseason leaves no live LLM reports before Nov 15 | Use the frozen historical study and clearly dated screenshots. Show no-games/archive truthfully. Separate replay integration tests from actual production monitoring and make no live-quality claim without reports. |
| Deferred P1.7/P1.4 integration grows | Limit scope to attempt logs, summaries and truthful writer origin. New schema, fan copy or workflow changes require owner approval; postpone unrelated badge work. |
| Review/CI latency and branch migration consume the deadline | Budget full verification and two review rounds, keep Nov 9-10 for QA, and schedule branch migration after the case study. Stop under existing D35 rules. |

## Proposal: short-lived task branches with PRs into main

Recommend adopting this after the Nov 15 release/case, in a separate approved
workflow task. It gives each change its own reviewed diff against the
deployed code and avoids accumulating another large workshop release.
Doing it before Oct 30 is an alternative only if the owner provides the
additional workflow/security review time; it is the first schedule cut.

This proposal changes D14, D20/D22/D35 and D41/D42's branch/release
instructions, the git guard and CONTRIBUTING/QA wording. It is not
authorized by approval to commit this draft. Keep `v2` as the current
workshop until the new decision, guard tests and PR checks are approved.

1. Owner first merges all accepted `v2` work by the existing `v2 -> main`
   PR process and records the baseline. Leave the protected `v2` and frozen
   tag intact; no deletion, rename, rewrite or force push is needed.
2. A normal task starts from freshly fetched `origin/main` on a branch such
   as `task/p2-3-guardrail`, with one approved task/commit and one writer.
   Open a PR to `main`; owner reviews and merges with **Merge** in GitHub.
   Agents never commit/push directly to `main` or merge PRs. Codex per-commit
   approval remains unless a separate owner amendment changes it.
3. Before using that namespace, approve and test the git guard change to
   allow only the task namespace in addition to existing permitted branches.
   Preserve identity, history/tag protections and the read-only GitHub token.
   Do not evade the guard through another tool. PR creation stays an owner
   UI action unless explicitly authorized in the revised policy.
4. Current `tests.yml` runs on pushes to `v2` only. Add PR-to-main checks
   for all five suites, agree stable required check names, and have the
   owner configure them in the `main` ruleset without removing protections.
   Use offline fixtures; no MLB/provider calls, publishing keys or other
   secrets in untrusted PR jobs. Preserve pinned actions and least privilege;
   avoid running PR code with elevated `pull_request_target` credentials.
5. Keep the daily job and its main-only environment/deploy-key exception
   (D15/D41). The existing push trigger for changes to `daily.yml` on `v2`
   would spend a live rehearsal, and all three D42 rehearsals are spent:
   approve/remove that trigger before any workflow migration push, with no
   additional dry run or dispatch inferred. Keep the scheduled production
   path and bot-only allowlist for `public/data/` and `evals/live/`.
6. Bot commits will advance `main` while a PR is open. Update a task branch
   through an ordinary merge from the current remote base under the new
   approved rules, never rebase/force-push. Recheck the diff, full suites and
   PR checks on the updated head. Resolve data conflicts by retaining the
   bot's latest published files; code PRs do not overwrite runtime data.
7. Each merge deploys, so changes land with the rules writer as default.
   An LLM enablement PR needs completed offline evidence, independent phase
   QA and the owner's ship decision. Plan schema transitions so existing
   published data remains readable or the approved regeneration/fallback
   sequence is explicit; do not expose half a contract change across PRs.

If migration is deferred, execute the approved P2 work on `v2` with current
approvals/review/CI rules and the owner's release PR. This draft's eventual
commit and push also go only to `v2` after the owner's explicit yes.

## Verification and handoff for later execution

Every implementation task begins with observed red tests and named passing
controls, then full verification in the default terminal, sequentially:
`python -m pytest`, `npm test`, `npx tsc --noEmit`, `npm run lint`,
`npm run build`. No PATH/locale changes and no source/provider requests in
tests. Read the relevant installed Next.js guide before any Next.js code.

Use `.claude/agents/reviewer.md` in a clean context, supplying only the task,
approved plan and diff range. Fix correctness/contract/scope findings, record
rejected suggestions with reasons, and stop after two rounds without PASS.
Get the required owner commit approval; push to the authorized branch and
wait for green CI before the next task. Only a fresh independent session
performs the phase-end QA; the implementing session does not certify itself.

Update PLAN, STATUS and its Pending Notion sync after each finished task,
with actual hashes/evidence, remaining work and any removed xfails/table
entries. New decisions, schema, workflows or unplanned fan text require
owner approval. No contract tolerance or skipped contract findings return.
Offline artifacts may be committed after review; actual public data and
daily logs remain the deployed bot's work under the approved release policy.

P3 receives the frozen input/run manifests, A/B1/B2 outputs and labels,
evaluator versions, per-dimension and per-stratum results with denominators,
dev error taxonomy, the one-change rationale, attempt/fallback evidence,
QA report and explicit limitations. P3.2 separates offline version evidence
from daily monitoring and displays an honest empty monitoring state when
necessary. P3.3 explains the fan problem, F5/F7 examples, experiment, result
and ship/no-ship decision with reproducible links. A no-ship case can meet
November 15; missing evidence must remain visible as unfinished work.
