# Offline writer instrument replay

estimate of fact-ID behaviour; replay-only unique subject/field suffix normalization

Zero Gemini calls. All original candidate text and capture/ledger hashes preserved. NLI scores are diagnostic.

| Run | Case | Attempt | Strict accepted (0/1) | Estimated accepted (0/1) | Strict reasons | Estimated reasons |
|---|---|---:|---:|---:|---|---|
| 2 | limited-823836 | 1 | 0 | 0 | REPLAY.unmappable, W1.no_evidence, W1.number, W12.time | REPLAY.unmappable, W1.no_evidence, W1.number, W12.time |
| 2 | limited-823836 | 2 | 0 | 0 | W1.entity, W1.number, W10.cause, W12.time, W2.comparison, W8.form | W1.entity, W1.number, W10.cause, W12.time, W2.comparison, W8.form |
| 2 | limited-823863 | 1 | 0 | 0 | REPLAY.unmappable, W10.cause, W5.label | W10.cause, W5.label |
| 2 | limited-823863 | 2 | 0 | 0 | W17.structure | W17.structure |
| 2 | limited-825104 | 1 | 0 | 0 | W17.structure | W17.structure |
| 2 | limited-825104 | 2 | 0 | 0 | W12.time, W6.arsenal | W12.time, W6.arsenal |
| 2 | opener-823769 | 1 | 0 | 0 | REPLAY.unmappable, W1.no_evidence, W1.number, W12.time, W2.comparison | REPLAY.unmappable, W1.no_evidence, W1.number, W12.time, W2.comparison |
| 2 | opener-823769 | 2 | 0 | 0 | REPLAY.unmappable, W12.time, W5.label, W8.form | W12.time, W5.label, W8.form |
| 2 | opener-824280 | 1 | 0 | 0 | REPLAY.unmappable, W1.entity, W1.no_evidence, W1.number, W10.cause, W12.time, W2.comparison | REPLAY.unmappable, W1.entity, W1.no_evidence, W1.number, W10.cause, W12.time, W2.comparison |
| 2 | opener-824280 | 2 | 0 | 0 | REPLAY.unmappable, W1.no_evidence | REPLAY.unmappable, W1.no_evidence |
| 2 | postseason-849842 | 1 | 0 | 0 | W10.cause, W2.comparison | W10.cause, W2.comparison |
| 2 | postseason-849842 | 2 | 0 | 0 | W17.structure | W17.structure |
| 2 | postseason-849849 | 1 | 0 | 0 | REPLAY.unmappable, W1.entity, W1.number, W12.time | W1.entity, W1.number, W12.time |
| 2 | postseason-849849 | 2 | 0 | 0 | REPLAY.unmappable, W1.entity, W2.comparison | REPLAY.unmappable, W1.entity, W2.comparison |
| 2 | veteran-823938 | 1 | 0 | 0 | REPLAY.unmappable, W1.entity, W1.no_evidence, W2.comparison | REPLAY.unmappable, W1.entity, W1.no_evidence, W2.comparison |
| 2 | veteran-823938 | 2 | 0 | 0 | W12.time, W2.comparison, W3.prediction | W12.time, W2.comparison, W3.prediction |
| 2 | veteran-824027 | 1 | 0 | 0 | W1.entity, W1.number, W7.missing | W1.entity, W1.number, W7.missing |
| 2 | veteran-824027 | 2 | 0 | 0 | W1.entity, W12.time | W1.entity, W12.time |
| 2 | veteran-824803 | 1 | 0 | 0 | W1.entity, W12.time | W1.entity, W12.time |
| 2 | veteran-824803 | 2 | 0 | 0 | W1.entity, W1.number, W10.cause, W12.time, W3.prediction, W5.label | W1.entity, W1.number, W10.cause, W12.time, W3.prediction, W5.label |
| 3 | postseason-849842 | 1 | 0 | 0 | W17.structure | W17.structure |
| 3 | postseason-849842 | 2 | 0 | 0 | W1.number, W2.comparison | W1.number, W2.comparison |
| 4 | limited-823836 | 1 | 0 | 0 | W12.time | W12.time |
| 4 | limited-823836 | 2 | 0 | 0 | W12.time, W2.comparison, W6.unsaid | W12.time, W2.comparison, W6.unsaid |
| 4 | limited-825104 | 1 | 0 | 0 | W1.authority, W1.entity, W10.cause, W6.arsenal | W1.authority, W1.entity, W10.cause, W6.arsenal |
| 4 | limited-825104 | 2 | 0 | 0 | W6.arsenal | W6.arsenal |
| 4 | opener-823769 | 1 | 0 | 0 | W17.structure | W17.structure |
| 4 | opener-823769 | 2 | 0 | 0 | REPLAY.unmappable, W1.number, W15.outcome | W15.outcome |
| 4 | opener-824280 | 1 | 0 | 0 | REPLAY.unmappable, W1.number, W6.unsaid | W6.unsaid |
| 4 | opener-824280 | 2 | 0 | 0 | W15.outcome | W15.outcome |
| 4 | postseason-849842 | 1 | 0 | 1 | REPLAY.unmappable | accepted |
| 4 | postseason-849842 | 2 | 0 | 0 | REPLAY.unmappable, W1.number, W2.comparison, W8.form | W1.number, W2.comparison, W8.form |
| 4 | postseason-849849 | 1 | 0 | 0 | W5.intensity | W5.intensity |
| 4 | postseason-849849 | 2 | 1 | 1 | accepted | accepted |

Totals: {"estimated": {"accepted": 2, "missing_citation_sentences": 5, "rejected": 32, "structure_rejected": 5, "unmappable_citations": 26}, "strict": {"accepted": 1, "missing_citation_sentences": 5, "rejected": 33, "structure_rejected": 5, "unmappable_citations": 42}}

Every candidate's unchanged text, per-sentence gates, S1 findings, NLI scores, old citations, resolved bindings and unmappable reasons are in [the replay record](../evals/data/writer/instrument-replay.json).

Strict leaves nonexistent/ambiguous paths rejected. The estimate normalizes a nonexistent path only when exactly one valid path ends in the same field suffix for the explicit same subject. Dimension fields keep their parent (thresholds.control differs from limited.control); other fields use the terminal name. Equal values never resolve ambiguity. The experiment and production harness do not import this tool.

Declared run-2 lineage maps finding-list items to their joined finding and formatted ERA/WHIP/lineup rates to numeric twins. It never converts innings notation. Valid paths resolve to actual code-owned values; supplied-value discrepancies are recorded, never copied into facts. No prose is changed. The five original structure rejects are counted separately from unmappable citation occurrences.

Empty original citation lists are explicitly unmappable in both modes (missing_citation). Missing-citation sentences are counted separately from nonexistent/ambiguous path occurrences and are excluded from the fully-mapped-text subset.

Real-error controls still fail in BOTH modes: run 4 postseason-849842 attempt 2 retains W1.number for 10.4% BB% versus the actual 10.6%; run 4 limited-825104 attempt 1 retains W1.authority for unverified official ratings. The cause alone has a separate fully evidenced must-pass regression; the original official sentence is never accepted.

NLI score coverage (score-only; no threshold or calibration claim):

- strict: 551 scored, 87 Watch/not applicable, 15 unrenderable, 0 unavailable.
- estimated: 551 scored, 87 Watch/not applicable, 15 unrenderable, 0 unavailable.

There are 34 candidates in 18 captures / 35 attempt records. The extra run-3 attempt is transport-only. All five malformed candidates stay rejected. Run-2 prompt metadata is p2.2-1; saved metadata takes precedence over its old report header. Experiment calls remain 127/400; this replay spends 0 calls, and no dev pass or forty-case B1 was started.

## Rejection reasons excluding unmappable paths

Counts below exclude REPLAY.unmappable and cover all 34 candidates. Findings are distinct recorded gate findings; a candidate can contribute more than one. The last column additionally excludes findings on sentences with any missing citation or remaining unmappable path, to avoid treating mapping-induced number/evidence failures as independent factual errors. Report-level checks and the five original structure failures remain. S1 and NLI are diagnostics, not rejection reasons.

| Check ID | Strict findings | Strict candidates | Estimated findings | Estimated candidates | Estimated findings on fully mapped text |
|---|---:|---:|---:|---:|---:|
| W1.authority | 1 | 1 | 1 | 1 | 1 |
| W1.entity | 18 | 10 | 18 | 10 | 17 |
| W1.no_evidence | 8 | 5 | 8 | 5 | 0 |
| W1.number | 27 | 11 | 17 | 9 | 11 |
| W10.cause | 6 | 6 | 6 | 6 | 6 |
| W12.time | 18 | 13 | 18 | 13 | 17 |
| W15.outcome | 2 | 2 | 2 | 2 | 2 |
| W17.structure | 5 | 5 | 5 | 5 | 5 |
| W2.comparison | 15 | 10 | 15 | 10 | 13 |
| W3.prediction | 2 | 2 | 2 | 2 | 2 |
| W5.intensity | 1 | 1 | 1 | 1 | 1 |
| W5.label | 3 | 3 | 3 | 3 | 3 |
| W6.arsenal | 3 | 3 | 3 | 3 | 3 |
| W6.unsaid | 2 | 2 | 2 | 2 | 2 |
| W7.missing | 1 | 1 | 1 | 1 | 1 |
| W8.form | 6 | 3 | 6 | 3 | 6 |
