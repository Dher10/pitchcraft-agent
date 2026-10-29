# PitchCraft Report Writer Eval — Spec v0.5

Owner: Daniel Herdenez · Updated: 2026-10-28
Related: `PRD_v2.md`, `DECISIONS.md` (D2, D8, D17, D24, D44-D47),
revised `plans/P2.md`; `writer-guide.md` is created/approved after real dev packets exist.

The Oct 27 owner kickoff selects D46 providers and the code/local-NLI /
post-publication-judge cascade. This specification describes the target,
not implemented evaluators. Owner approved the plan/SECURITY on Oct 28
with D47 adjustments, then approved nonce/dynamic/style-attribute scope and
the separate local-key route. P2-SEC implements security primitives/headers;
stop before P2.1 for owner key creation/storage. Generated prose is unwired. Schema stays
0.9.0 until separate exact-schema approval. GitHub Models is retired.

## 1. Decision this eval informs

Should PitchCraft publish the LLM writer by default instead of the rules-based writer?

Ship only if all hold on the held-out test set (owner confirmed 2026-10-24):

- Groundedness: ≥95% of reports with zero unsupported claims
- Policy: 100% free of betting, odds or outcome language
- R1 relevance and no outside knowledge: 100% of reports pass both its code
  and judge checks; true-but-unsupported statements fail
- Fan usefulness: LLM wins or ties vs. rules in ≥70% of pairs
- Judge trust: judge–human agreement ≥85% separately for G2, L1, U1, R1, S1 and the bundled policy audit

S1's guide-compliance scores inform B2; there is no separate S1 report
pass-rate ship threshold. The judge-trust target still applies to S1.
Any failed ship gate or missing required evidence keeps rules live, and
the case documents why. With 20 test cases, groundedness needs 19/20,
policy and R1 each need 20/20, and U1 needs 14/20 wins or ties.

Use the first LLM attempt as the primary A/B1/B2 comparison. Report retry
and fallback performance separately; a rules fallback is not an LLM success.

## 2. Systems under test

- **A:** rules-based writer, with the name-split bug fixed and nothing else changed.
- **B1:** LLM writer v1, Gemini via AI Studio; exact ID verified in P2.1.
- **B2:** LLM writer v2, one change chosen from error analysis on B1.

All receive identical stored findings and matchup packet. Pin exact model
IDs and temperature in config, and record prompt, guide, evaluator and
packet versions/digests. No model substitution inside an experiment. Rules fallback attempts
are operational results, never counted as Gemini B1/B2 first-attempt success.

## 3. LLM writer contract

- **Input:** Matchup Analyst findings + packet subset + per-dimension sample flags + language.
- **Output target (D44/D45):** plain-text sentences with evidence, never HTML,
  in a versioned report with sentence-to-evidence claims,
  including sentence text, supporting packet paths and cited values,
  subject and text location. The exact schema and version require separate
  owner approval before implementation; no new schema is chosen here.
- Every factual sentence maps to evidence in the packet, including text in
  unrendered fields. Independent validation checks coverage, paths, values,
  subject, flags, scope/time and semantics. Schema-valid JSON alone is insufficient.
- Existing catalog claims continue for rules/fixed text. No plain-string
  bypass of `claims.py`, independent contract checks or the final validator.
- The owner's hard checkpoint is November 2: if the prose boundary is not
  proven, rules stay live and the experiment is reported offline.
- Before P2.2, the owner approves `docs/writer-guide.md`: casual-fan audience,
  packet-only facts, forbidden topics/phrasing, jargon explained on first
  use, short sentences, concrete things to watch and symmetric treatment
  of the starters. Include 3-5 good/bad pairs from real dev packets, with
  evidence and failure reasons. Build/version the prompt from that guide.
- Never add predictions, betting, outcomes, injuries, personal life, history, awards,
  facts outside the packet even if true, or deception/effectiveness inferred
  from movement alone. Required jargon definitions must themselves have
  packet evidence; do not treat the guide as permission for outside facts.

Python computes everything; the writer never calculates. Intensity words
come only from existing D24/D25 labels and thresholds. No causal words such
as "because" or "due to" without explicit packet cause. The owner-approved
guide requires neutral factual tone, first-use jargon explanations, short
sentences, concrete things to watch and symmetric starters, with 3-5 real-dev
good/bad pairs. Named forbidden topics stay forbidden even if in the packet.

Before publication, code/schema/contract checks are followed by a pinned
CPU NLI cross-encoder for each generated sentence against the packet's
verified catalog fact sentences, never raw JSON. Calibrate its threshold
on dev HUMAN entailment labels and semantic negatives; pin fact-renderer,
model revision/SHA-256, tokenizer and threshold in the run identity. Missing,
uncalibrated, oversized/truncated or failed NLI evidence rejects the LLM
candidate; one informed retry total, then independently validated rules.
This does not replace the offline G2/R1 judge or guarantee accuracy. Nov 2
proof requires the actual independent publication path, not an unset gate.

## 4. Dimensions (binary pass/fail per report)

| Dim | Evaluator | Pass when |
|---|---|---|
| G1 Numeric grounding | Code | Every cited path exists; numbers match their subject/field within the frozen formatting tolerance, and absent numbers/entities are rejected |
| G2 Semantic grounding | LLM judge | Every qualitative claim follows from its cited data; no uncited factual claim |
| L1 Limited-data honesty | Code + local NLI + LLM judge | No claims on a dimension flagged as limited; the limitation is stated |
| P1 Policy | Code, with bundled judge policy audit | No betting, odds, win-probability or outcome-prediction language; any confirmed violation fails the 100% policy gate |
| C1 Coverage | Code | Both starters' available primary and put-away pitches and both available offense reads appear, with honest unavailable/limited states; D30's absent second pitch is not invented |
| F1 Format | Code | Schema valid; length within range set after the owner reads 10 rules-based dev outputs |
| U1 Fan usefulness | LLM judge, pairwise, order randomized | A casual fan understands the duel and knows what to watch; no unsupported time claim |
| R1 Relevance and no outside knowledge | Code + local NLI + LLM judge | Every sentence concerns this game, its starters or its lineups and states no fact absent from the packet; true-but-unsupported fails |
| S1 Guide compliance | LLM judge, binary per guide rule | Each applicable approved rule passes, including jargon explained on first use and no forbidden phrasing |

Both writers face the same applicable checks. A's claim-extraction pass
supports G1, P1, C1, F1, code-L1 and code-R1; an extraction failure is a
failure or explicit missing evaluation, never silently excluded.

R1 code checks report entities and numbers against the packet's evidence,
documented aliases and G1's formatting/rounding rules. It must reject an
absent player/team, absent number and irrelevant outside entity. It cannot
establish semantic support: a familiar entity can still carry an invented
injury, award or claim. The R1 judge checks relevance and unsupported facts
sentence by sentence; a valid path to an unrelated fact does not pass.
The report passes R1 only if both components pass.

S1 stores a binary result and reason for every applicable guide rule, plus
a report summary (all applicable rules pass). Freeze rule IDs, applicability
and aggregation before B1; retain per-rule scores for B2 error analysis.
Generic jargon/measurement definitions used in prose must be supplied as
explicit, approved packet evidence to A and B alike before packet freeze.

## 5. Dataset

- 40 matchups from the 2026 regular season and postseason.
- Stratified: 10 high-data veterans; 10 positive but limited-sample starters; 10 openers or bullpen-adjacent cases; 10 postseason games.
- Leakage rule: every fetch uses `as_of = game_date − 1`, including series status. The schedule's `seriesStatus` is the standing after each game, so reading the series' last game returns the final result; the standing before first pitch is the one after the previous game of the same series dated on or before `as_of` (`fetch_series_status`, P0.2).
- Split: 20 dev / 20 test, five cases per stratum in each. Inputs and test
  membership frozen before B1 runs; no refetch between A/B1/B2.
- Stored as JSONL in `evals/data/` with fetch date, source/packet/findings digests and `as_of` per case. Mutually exclusive primary strata; record overlapping traits without double counting.
- Debut, zero sample, null pitch data, shortened and postponed games belong
  to the regression suite. Neither that suite nor the 40-case dataset
  provides an accuracy guarantee; do not fabricate missingness or add edge
  cases to an accuracy denominator.
- Recompute D32 lineup-vs-hand quartiles first; changed thresholds need an
  owner superseding decision. Preserve D23/D29/D42 collection caps/pacing.

## 6. Human labels and judge calibration

- The owner labels G2, L1 and R1, each S1 guide rule, policy audit, and U1 for all 40 A/B1
  cases, blind to system where possible. Keep one-line reasons. U1 retains
  win/tie/loss and derives the binary wins-or-ties result consistently.
- Workload: 80 A/B1 report readings, 240 G2/L1/R1 decisions, 80 times the
  approved number of S1 rules, and 40 U1 pairs. The original 6-8 hours did
  not include R1/S1. Policy audit and dev sentence/premise NLI labels add
  work; reuse guide-policy labels only with an explicit frozen rubric mapping.
  Labeling is Nov 4-6; owner confirms hours before Nov 3 using a timed dev
  sample. Early dev NLI labels needed for Nov 2 require a separate owner
  reservation; later labels do not move that hard checkpoint.
- Budget B2 held-out labels separately: 20 new reports for G2/L1/R1 and
  S1 per rule, plus 20 U1 pairs against fixed A and policy audit; reuse A's labels.
- Tune judge prompts on dev only. Freeze judge/evaluator versions and B2
  before opening B1 test outputs, human reasons or aggregate results.
  P2.6 exits at dev calibration/version freeze; held-out trust is measured
  in P2.7 after B2 freeze. Sealed test labels cannot influence B2.
- Report held-out agreement, TPR/TNR, confusion matrices and denominators
  separately for G2, L1, U1, R1, S1 and the bundled policy audit; target at least 85% per dimension,
  never a pooled result across dimensions. For S1 the dimension denominator
  is applicable report-rule judgments; also show each rule's agreement and
  the report-level summary agreement. No additional per-rule ship threshold.
- Freeze applicability/tie/abstention rules before B1. Show absent-class
  TPR/TNR as undefined; missing/refusing/quota-limited judgments are
  `not_evaluated`, not passes. Missing required evidence blocks shipping.
- Judge model family differs from writer family. One bundled call per report
  returns separate G2, L1, R1, S1 rule and policy verdicts; U1 uses separate
  pairwise calls. Dev uses BOTH presentation orders and measures position
  bias; test uses ONE randomized order per pair. Record seed, PRNG/version
  and case/version-to-order manifest before calls; reuse it on resume, never
  select order after seeing results. Calibrate the
  bundled protocol, not separate-dimension calls assumed equivalent.
- Freeze provider/route, exact model/fingerprint and disclosed quantization,
  temperature/thinking, prompts/schema/guide/evaluator versions and canonical
  requests before test inspection. Same frozen judge for official A/B1/B2.
  Cloudflare fallback only before freeze; no switch to rescue held-out
  evidence. Material drift/unavailability stops or needs a separately
  approved run. Apply the research frozen-judge rule.
- Include separate human-agreement evidence for the bundled policy audit;
  target >=85% for every judged dimension, never pool it away. Report policy
  agreement separately from P1's 100% report-level ship gate. S1 retains
  its applicable report-rule denominator and no extra style pass-rate gate.

## 7. Error analysis and iteration

Open-code every B1 failure on dev, group and count, including R1 and S1
rule failures. Pick one change targeting the largest actionable category
(prompt, packet content or contract); S1 informs that choice. Stop for
owner approval of the B2 hypothesis before implementation. Run B2 on the
frozen test set, preserving shared inputs/comparability; report A/B1/B2.

## 8. Publication cascade and online monitoring

- Before publication: schema/contract, G1 numbers/entities, code R1/L1,
  policy word list, C1/F1, then local CPU sentence-to-catalog-facts NLI.
  Technical/content/NLI failure gets one informed Gemini retry total,
  then validated rules. At most two Gemini calls; no other writer provider. Unsafe
  fallback/final integrity failure keeps the previous file (D34/D42).
- After publication: ONE Groq call per report covers G2 residue, L1, R1,
  S1 per rule and policy. U1 remains offline. Remote verdicts never gate or
  undo publication (D17); invalid/refusing/unavailable dimensions are
  not_evaluated, never passes. A no-games day calls neither model.
- Append-only `evals/live/YYYY-MM-DD.jsonl`: game ID, actual writer/model,
  guide/prompt/evaluator/NLI identity, attempts/fallback and safe per-dimension
  outcome/reason/usage. No keys, raw internal prompts or provider errors in
  public logs/artifacts; closed codes require approval before implementation.
  Daily files are bot-owned; v2 tests use fixtures, never edit actual logs.
- Summary feeds the quality page; weekly human review of 3-5 actual reports
  investigates disagreements without changing a frozen experiment. Daily
  rates are monitoring signals, not version comparisons.

## 9. Infrastructure and capacity ($0, no card, no trial)

D46/D47: Gemini via AI Studio is the sole model writer, then rules;
exact writer IDs verified in P2.1. Groq Free openai/gpt-oss-120b for BOTH
judge uses; Cloudflare @cf/zai-org/glm-4.7-flash only before judge freeze.
GitHub Models is retired. Free entitlement/quotas remain to verify; no paid
or trial substitute is authorized.

Production keys remain in main-only pitchcraft-llm-main, separate from the
deploy key. Separate local keys/Windows USER variables and an explicit
owner-PC offline runner are approved in plans/P2.md; owner key setup and
confirmation are required before P2.1. No production key export, .env or workflow change. Tests replay
fixtures and make no source/provider requests.

`plans/P2.md` holds the revised ledger: official 100 report calls + 80 U1
(40 dev two-order, 20 B1 test one-order, 20 B2 test one-order), plus three
dev passes (240 calls) = 420; exact final-dev reuse reduces new calls to
340. At assumed 5,500/report and 6,000/U1: 2.41M/1.95M tokens, at least
13/10 quota-days at 200K; with 20% attempts 2.892M/2.34M, 15/12 days.
Conservative B2-dev-inclusive envelope: 480/400 calls, 2.76M/2.30M tokens,
14/12 days; with allowance 17/14. From Nov 1 monitoring reserves ZERO tokens:
full 200K/day is available offline. Through Oct 31 debit actual monitoring
reports (5,500 each); do not carry a permanent 55K reserve into offseason.
Separate local/production keys may share quotas; never double the budget.

These are planning caps/lower bounds, not measured usage or calendar
promises. P2.1 establishes quota/usage measurement on synthetic probes;
full A measurements follow P2.4 and B1 measurements follow first B1, before the full
judge queue, including reasoning, failures and probes. Cache by complete canonical request/model/settings/guide/prompt/
schema/evaluator identity; only complete identical responses are reusable.
Judge A as soon as P2.4 exists, BEFORE B1; add B1 when available. Calibrate only on dev labels, seal
test evidence, pace/resume across quota days. Do not cut gates or switch a
frozen judge to meet a date. No source/provider requests in tests.

## 10. Non-goals (v2)

Postgame validation of "what to watch", multi-model comparison, latency or cost optimization, changes to Matchup Analyst logic beyond Phase 0 fixes.

## 11. Milestones (America/Bogota)

- Oct 27 kickoff: P1-R3, then plan/decisions/security docs; stop for owner
  approval and key/main-only-environment setup. No Phase 2 implementation.
- Oct 28: approval/D47/inventory recorded; stop at P2-SEC rendering scope
  and local-route proposals approved; implement P2-SEC, then STOP before
  P2.1 for owner key setup. No P2.1 calls in P2-SEC.
- After P2-SEC and owner key-setup confirmation: P2.1 -> P2.4 -> immediate A judging
  -> approved real-dev guide -> P2.2 -> P2.3 -> B1 capture/judging.
- From Nov 1: zero daily monitoring reserve, full shared 200K/day offline.
  Required 10/13 quota-days starting Nov 1 end no earlier than Nov 10/13
  without prior valid reuse; allowance/dependencies may extend past cutoff.
- Nov 2: hard claims-boundary proof checkpoint; otherwise rules live,
  experiment offline. No uncalibrated NLI or raw-string bypass.
- Before Nov 3: confirm expanded owner hours and A/B1 readiness.
- Nov 4-6: owner labels; dev-only NLI/judge calibration and frozen versions.
- Nov 8 target: B2/comparison; Nov 9-10 independent Antigravity QA/contingency.
- Nov 11 at 18:00: final evidence freeze; missing gates mean no ship.
- Nov 15: honest case study; branch/PR migration gets its own later task.
