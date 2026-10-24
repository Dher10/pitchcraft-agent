# PitchCraft Report Writer Eval — Spec v0.3

Owner: Daniel Herdenez · Updated: 2026-10-24
Related: `PRD_v2.md`, `DECISIONS.md` (D2, D8, D9, D17, D24, D44),
approved `plans/P2.md`; `writer-guide.md` is created/approved after real dev packets exist.

This is the approved evaluation specification, not a statement that the
writer or evaluators are implemented. P2.1 is waiting for owner credentials
confirmation and a judge-provider decision: [GitHub Models retired on
July 30, 2026](https://github.blog/changelog/2026-07-30-github-models-is-now-retired/).
D9/D17 are unchanged; no replacement is selected here.

## 1. Decision this eval informs

Should PitchCraft publish the LLM writer by default instead of the rules-based writer?

Ship only if all hold on the held-out test set (owner confirmed 2026-10-24):

- Groundedness: ≥95% of reports with zero unsupported claims
- Policy: 100% free of betting, odds or outcome language
- R1 relevance and no outside knowledge: 100% of reports pass both its code
  and judge checks; true-but-unsupported statements fail
- Fan usefulness: LLM wins or ties vs. rules in ≥70% of pairs
- Judge trust: judge–human agreement ≥85% separately for G2, L1, U1, R1 and S1

S1's guide-compliance scores inform B2; there is no separate S1 report
pass-rate ship threshold. The judge-trust target still applies to S1.
Any failed ship gate or missing required evidence keeps rules live, and
the case documents why. With 20 test cases, groundedness needs 19/20,
policy and R1 each need 20/20, and U1 needs 14/20 wins or ties.

Use the first LLM attempt as the primary A/B1/B2 comparison. Report retry
and fallback performance separately; a rules fallback is not an LLM success.

## 2. Systems under test

- **A:** rules-based writer, with the name-split bug fixed and nothing else changed.
- **B1:** LLM writer v1, Gemini Flash.
- **B2:** LLM writer v2, one change chosen from error analysis on B1.

All receive identical stored findings and matchup packet. Pin exact model
IDs and temperature in config, and record prompt, guide, evaluator and
packet versions/digests. No model substitution inside an experiment.

## 3. LLM writer contract

- **Input:** Matchup Analyst findings + packet subset + per-dimension sample flags + language.
- **Output target (D44):** a versioned report with sentence-to-evidence claims,
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
- Never add predictions, betting, outcomes, injuries, history, awards,
  facts outside the packet even if true, or deception/effectiveness inferred
  from movement alone. Required jargon definitions must themselves have
  packet evidence; do not treat the guide as permission for outside facts.

## 4. Dimensions (binary pass/fail per report)

| Dim | Evaluator | Pass when |
|---|---|---|
| G1 Numeric grounding | Code | Every cited path exists and every number in the text matches the packet within a defined rounding tolerance |
| G2 Semantic grounding | LLM judge | Every qualitative claim follows from its cited data; no uncited factual claim |
| L1 Limited-data honesty | Code + LLM judge | No claims on a dimension flagged as limited; the limitation is stated |
| P1 Policy | Code | No betting, odds, win-probability or outcome-prediction language |
| C1 Coverage | Code | Both starters' available primary and put-away pitches and both available offense reads appear, with honest unavailable/limited states; D30's absent second pitch is not invented |
| F1 Format | Code | Schema valid; length within range set after reading 10 rules-based outputs |
| U1 Fan usefulness | LLM judge, pairwise, order randomized | A casual fan understands the duel and knows what to watch; no unsupported time claim |
| R1 Relevance and no outside knowledge | Code + LLM judge | Every sentence concerns this game, its starters or its lineups and states no fact absent from the packet; true-but-unsupported fails |
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
- Stratified: 10 high-data veterans; 10 limited-sample starters (rookies, returns from IL); 10 openers, bullpen-adjacent or missing-data cases; 10 postseason games.
- Leakage rule: every fetch uses `as_of = game_date − 1`, including series status. The schedule's `seriesStatus` is the standing after each game, so reading the series' last game returns the final result; the standing before first pitch is the one after the previous game of the same series dated on or before `as_of` (`fetch_series_status`, P0.2).
- Split: 20 dev / 20 test, five cases per stratum in each. Inputs and test
  membership frozen before B1 runs; no refetch between A/B1/B2.
- Stored as JSONL in `evals/data/` with fetch date and `as_of` per case.

## 6. Human labels and judge calibration

- The owner labels G2, L1 and R1, each S1 guide rule, and U1 for all 40 A/B1
  cases, blind to system where possible. Keep one-line reasons. U1 retains
  win/tie/loss and derives the binary wins-or-ties result consistently.
- Workload: 80 A/B1 report readings, 240 G2/L1/R1 decisions, 80 times the
  approved number of S1 rules, and 40 U1 pairs. The original 6-8 hours did
  not include R1/S1. Labeling is Nov 4-6; owner confirms hours before Nov 3.
- Budget B2 held-out labels separately: 20 new reports for G2/L1/R1 and
  S1 per rule, plus 20 U1 pairs against fixed A; reuse A's labels.
- Tune judge prompts on dev only. Freeze judge/evaluator versions and B2
  before opening B1 test outputs, human reasons or aggregate results.
  P2.6 exits at dev calibration/version freeze; held-out trust is measured
  in P2.7 after B2 freeze. Sealed test labels cannot influence B2.
- Report held-out agreement, TPR/TNR, confusion matrices and denominators
  separately for G2, L1, U1, R1 and S1; target at least 85% per dimension,
  never a pooled result across dimensions. For S1 the dimension denominator
  is applicable report-rule judgments; also show each rule's agreement and
  the report-level summary agreement. No additional per-rule ship threshold.
- Freeze applicability/tie/abstention rules before B1. Show absent-class
  TPR/TNR as undefined; missing/refusing/quota-limited judgments are
  `not_evaluated`, not passes. Missing required evidence blocks shipping.
- Judge model family differs from writer family.

## 7. Error analysis and iteration

Open-code every B1 failure on dev, group and count, including R1 and S1
rule failures. Pick one change targeting the largest actionable category
(prompt, packet content or contract); S1 informs that choice. Stop for
owner approval of the B2 hypothesis before implementation. Run B2 on the
frozen test set, preserving shared inputs/comparability; report A/B1/B2.

## 8. Online monitoring (production)

- Target daily integration scores G1, P1, C1, F1, code-L1 and code-R1, plus
  G2 by judge. U1 and judged R1/S1 stay offline in this plan; the offline
  R1 ship gate does not create an unapproved daily semantic veto.
- Guardrail (D2): technical/content/code-check failure gets one informed
  retry, then validated rules fallback. Log every attempt. An unsafe fallback
  or failed final integrity validation retains the prior public file.
- D17 still logs unavailable daily G2 as `not_evaluated` and continues
  publishing subject to code gates. It does not waive offline judge trust.
- Append-only log `evals/live/YYYY-MM-DD.jsonl`, one row per report: `game_id`, `writer`, `model`, `prompt_version`, `evaluator_version`, `attempts`, `fallback`, per-dimension result and reason.
- A summary file feeds the site's quality page.
- Weekly human review of 3–5 live reports; disagreements trigger a judge-prompt review; labels join the next offline set.
- Daily pass rates are monitoring signals, not version comparisons.

## 9. Infrastructure ($0)

Writer: Gemini Flash via AI Studio, exact model and $0 quota to confirm.
D9 names GitHub Models as the cross-family judge provider, but that service
is retired; replacement provider, access and exact model need owner approval
before P2.1 can finish. Do not select a paid or same-family substitute.
Offline runs local; daily runs on Actions. Responses are cached by input,
model, guide/prompt/evaluator version; runs resume across days. Public MLB
data only. Provider configuration is swappable without changing a frozen run.

## 10. Non-goals (v2)

Postgame validation of "what to watch", multi-model comparison, latency or cost optimization, changes to Matchup Analyst logic beyond Phase 0 fixes.

## 11. Milestones

- Oct 24: owner approves the P2 plan and additions; P2.1 stops at credentials/
  provider confirmation. No P2.4 before that and P2.1's acceptance checks.
- Oct 27-29 target: P2.1, then D32 analysis and P2.4; conditional on access.
- Before P2.2: real-dev writer guide/examples approved; prompt versioned with it.
- Nov 2: hard claims-boundary checkpoint; otherwise rules live, experiment offline.
- Nov 3 target: A/B1 captured before labels; owner hours confirmed before this date.
- Nov 4-6: expanded owner labels; dev-only judge calibration.
- Nov 8 target: B2 and comparison; Nov 9-10 QA/contingency.
- Nov 11 at 18:00 America/Bogota: evidence freeze and ship/no-ship decision.
- Nov 15: case published; incomplete evidence means rules remain live.
