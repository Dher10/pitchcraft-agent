# Plan B: results of the owner labels (owner order, Nov 6 2026)

Scope of this commit: `docs/results-planB.md` (all Plan B metrics except the judge agreement, dev and test apart, per protocol v2 section 6) and the STATUS entry. No code, gate, threshold, decision or workflow changes. Docs only.

Method:
- Run `python -m evals.labeling_sheet check --split dev|test`, then `metrics --split dev|test` (existing, tested code). Test numbers are produced once, after the dev numbers, and are not used to change a gate.
- Counts the tool does not print (label mix per stratum, re-label transitions, pooled U1, pair lengths, clusters of W1.entity sentences by report) come from a read-only one-off script that calls the same functions; the report says so.
- "insufficient" for a gate class means fewer than 5 labeled claim sentences (the raw counts are always shown); recall follows the protocol rule (at least 10 labeled errors).
- The placeholder section "Judge vs owner (test)" stays pending until the test judging run finishes (resume after 03:45 UTC Nov 7, from batch 12, with the abort rule).

Out of scope: the judge run (second commit), any change to `public/data/` or `evals/live/`.
