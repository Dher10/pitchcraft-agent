# Plan B: final judge freeze and the frozen judge on the test sample (owner order, Nov 6 2026)

Scope of this commit: the final `evals/data/writer/judge-freeze.json` (judge-p3 selected by the pre-freeze rule after dev pass 2: 77.9% agreement against 71.7%), the test-judging runner `evals/run_judge_test.py` with `tests/test_run_judge_test.py`, and STATUS.

Runner rules:
- Refuses to run unless `judge-freeze.json` verifies against the code and is committed.
- Judges the test manifest and facts files (strata A, B and C, 235 sentences), one case group per call, frozen spec, 60 s pacing, the declared single identical retry.
- Resumable: `.local/p2-2/labeling/judge_test_state.json` (untracked) holds the judge's label per sentence id, completed batch digests, calls, attempts and tokens, never sentence or response text. A later invocation skips completed batches.
- Abort rule: two consecutive failed batches pause the run (quota stop); the next invocation continues, the failed batches are retried.
- Never reads the owner's test labels or the answered sheet, never prints a verdict or a gate finding: counts only. No metric is computed.
- Never touches `public/data/` or `evals/live/`.
