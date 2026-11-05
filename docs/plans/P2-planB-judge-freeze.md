# Plan: protocol v2, owner notes, Groq judge dev calibration and freeze (Nov 4 2026)

Approved by the owner in the Nov 4 instruction (three items). Written for: the owner.

Commit 1 (this file's task, `[gated]` by D35 conditions): protocol v2 file, `PROTOCOL_VERSION`/`PROTOCOL_V1_SHA256`, judge prompt `judge-p2` with rules 5 and 6, red tests, `docs/case-study-notes.md`, STATUS. Full five suites, reviewer, green CI.

Commit 2: `evals/run_judge_dev.py` (owner-PC runner: injected key from the USER variable `PITCHCRAFT_GROQ_API_KEY_LOCAL`, `post_json` with metadata, 60 s pacing, batching by case group from the dev manifest and facts files, up to three passes, per-pass record of counts, agreement and Groq header tokens against the estimate, never response text or per-item labels) and, from the results, `evals/data/writer/judge-freeze.json` with the SHA-256 of the spec. Stops before the FROZEN step for the test outputs.

Limits: dev sample only (113 sentences, 23 calls per pass); at most three passes; a prompt change between passes means a new `PROMPT_VERSION` in code, one commit-visible change per pass; no gate finding is read or compared; test outputs, `public/data/` and `evals/live/` untouched.
