# PitchCraft Report Writer Eval — Spec v0.2

Owner: Daniel Herdenez · Date: 2026-10-10
Related: `PRD_v2.md`, `DECISIONS.md` (D2, D8, D9, D11)

## 1. Decision this eval informs

Should PitchCraft publish the LLM writer by default instead of the rules-based writer?

Ship only if all hold on the held-out test set (thresholds proposed, owner to confirm):

- Groundedness: ≥95% of reports with zero unsupported claims
- Policy: 100% free of betting, odds or outcome language
- Fan usefulness: LLM wins or ties vs. rules in ≥70% of pairs
- Judge trust: judge–human agreement ≥85% per judged dimension

If the LLM loses on groundedness, rules stay and the case documents why.

## 2. Systems under test

- **A:** rules-based writer, with the name-split bug fixed and nothing else changed.
- **B1:** LLM writer v1, Gemini Flash.
- **B2:** LLM writer v2, one change chosen from error analysis on B1.

All receive identical findings and matchup packet.

## 3. LLM writer contract

- **Input:** Matchup Analyst findings + packet subset + per-dimension sample flags + language.
- **Output:** current report schema plus `claims[]`: `{ text, evidence: [json_path], value_cited }`.
- Every factual sentence maps to at least one claim. Fixed temperature; prompt versioned in the repo.

## 4. Dimensions (binary pass/fail per report)

| Dim | Evaluator | Pass when |
|---|---|---|
| G1 Numeric grounding | Code | Every cited path exists and every number in the text matches the packet within a defined rounding tolerance |
| G2 Semantic grounding | LLM judge | Every qualitative claim follows from its cited data; no uncited factual claim |
| L1 Limited-data honesty | Code + LLM judge | No claims on a dimension flagged as limited; the limitation is stated |
| P1 Policy | Code | No betting, odds, win-probability or outcome-prediction language |
| C1 Coverage | Code | Both starters' primary and put-away pitch and both offense reads appear (unless flagged limited) |
| F1 Format | Code | Schema valid; length within range set after reading 10 rules-based outputs |
| U1 Fan usefulness | LLM judge, pairwise, order randomized | A casual fan understands the duel and knows what to watch tonight |

The rules-based writer is scored on G1, P1, C1 and F1 through a claim-extraction pass so both systems face the same checks.

## 5. Dataset

- 40 matchups from the 2026 regular season and postseason.
- Stratified: 10 high-data veterans; 10 limited-sample starters (rookies, returns from IL); 10 openers, bullpen-adjacent or missing-data cases; 10 postseason games.
- Leakage rule: every fetch uses `as_of = game_date − 1`, including series status (the API returns final results for past series).
- Split: 20 dev / 20 test. Test frozen before B1 runs.
- Stored as JSONL in `evals/data/` with fetch date and `as_of` per case.

## 6. Human labels and judge calibration

- The owner labels G2, L1 and U1 for all 40 cases (A and B1), blind to system where possible. Each label: pass/fail + one-line reason.
- Judge prompts are tuned on dev only. Report agreement, TPR and TNR on test.
- Judge model family differs from writer family.

## 7. Error analysis and iteration

Open-code every B1 failure on dev, group into categories, count. Pick one change targeting the largest category (prompt, packet content or contract). Run B2 on the frozen test set. Report A vs. B1 vs. B2.

## 8. Online monitoring (production)

- Every daily run scores each report with G1, P1, C1, F1 and the code part of L1, plus G2 by judge. U1 stays offline (pairwise needs both writers).
- Guardrail (D2): an LLM report failing G1 or P1 gets one informed retry; a second failure publishes the rules-based report. All attempts logged.
- Append-only log `evals/live/YYYY-MM-DD.jsonl`, one row per report: `game_id`, `writer`, `model`, `prompt_version`, `evaluator_version`, `attempts`, `fallback`, per-dimension result and reason.
- A summary file feeds the site's quality page.
- Weekly human review of 3–5 live reports; disagreements trigger a judge-prompt review; labels join the next offline set.
- Daily pass rates are monitoring signals, not version comparisons.

## 9. Infrastructure ($0)

Writer: Gemini Flash (AI Studio free tier). Judge: GitHub Models free tier. Offline runs local; daily runs on GitHub Actions. Responses cached by hash; runs resumable across days to fit free quotas. Public MLB data only. Provider swappable by env var.

## 10. Non-goals (v2)

Postgame validation of "what to watch", multi-model comparison, latency or cost optimization, changes to Matchup Analyst logic beyond Phase 0 fixes.

## 11. Milestones

- Oct 18: Phase 0 done
- Oct 25: v2.0-a live; dataset frozen; baseline run (A vs. B1)
- Nov 8: judge calibrated, error analysis, B2 run
- Nov 15: v2.0-b decision and case published
