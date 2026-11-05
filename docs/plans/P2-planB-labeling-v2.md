# P2 Plan B: labeling protocol for the owner, version 2

Status: **Version 2, Nov 4 2026.** Version 1 (`docs/plans/P2-planB-labeling.md`, SHA-256 `886bf60fd0228ff2faa9ac1b726f7b24ca73040bbe07e325bd611175e752ab29`) stays unchanged: the dev sheet was drawn under it. Version 2 adds the two hard-case rules 6 and 7 of section 2 from the owner's dev practice (section 12) and applies from the test sheet on. Its digest is recorded in `docs/STATUS.md` and in every manifest drawn after it. Definitions change only through a new protocol version. Originally drafted Nov 3-4 2026 after D64 and the B1 run on 40 cases (dev 6 of 20 accepted, test 5 of 20 accepted, 11 of 40 in all; counts only, from `evals/data/writer/b1-run-record.json`). No agent has labeled or read any sentence for this purpose.

Written for: the owner, who will do the labeling on Nov 6-7 (about 8 hours) and Nov 8 (about 3 hours).

## 1. What this protocol measures

D64 makes the primary question **gate accuracy**: for each hard gate, and for the score-only NLI, how often is it right about a sentence, judged by the owner's labels. The B1 acceptance rate is only a secondary number.

| Question | Measured by | Needs labels of |
|---|---|---|
| Precision of each sentence-level hard gate: of the sentences it flags, how many are truly wrong? | stratum B | flagged sentences |
| False-positive ("harness rigidity") rate: flagged but supported | stratum B | flagged sentences |
| False-accept rate of the gate set: admitted reports that contain a wrong sentence | stratum A | every sentence of every accepted report |
| Recall of the gate set: wrong sentences in rejected reports that no gate flagged | stratum C (+ B) | unflagged sentences of rejected reports |
| NLI: AUROC, and precision and recall of "supported" at 0.5 and 0.9 | all strata | all labeled sentences with a score |
| Secondary: B1 acceptance rate (dev, test, both) with 95% intervals | run record | none |

Out of sentence-level labeling by design: the report-level presence checks (W6 limited data said, W13 series and standing, W14 coverage, W17 shape and length). They test whether a required statement exists, so unit tests and the run record cover them; their counts are reported, not labeled.

## 2. Label definitions

Every labeled item is one model sentence, shown with the facts it cites and the case's full fact table. The owner picks exactly one label.

| Label | Choose it when |
|---|---|
| **supported** | Every claim in the sentence (numbers, names, teams, dates, scope, labels, pitches, causes) follows from the facts in the case's fact table, with each figure tied to its own owner and scope. Wording may paraphrase. A trivially true count ("two starters") counts as supported. |
| **wrong-number-or-name** | A number, name, team, date, pitch or label in the sentence differs from the fact table (wrong value, wrong owner, wrong scope, misspelled or accent-stripped name, a value from the other starter or team). One wrong item is enough, even if the rest is right. |
| **unsupported** | Nothing in the sentence contradicts the fact table, but it states something the fact table does not give: an invented cause, a prediction, an effect on hitters, an unlisted pitch description, a claim about a starter whose data is limited or missing. |
| **not-a-claim** | The sentence asserts nothing checkable: a headline phrase, a "Watch whether ..." prompt with no factual content of its own, a section lead-in. If it also contains a checkable claim, label that claim instead. |

Rules for hard cases:
1. If a sentence is both wrong and unsupported, use **wrong-number-or-name** when a value is wrong, otherwise **unsupported**.
2. A sentence that is true but cites the wrong fact is still **supported** (citation quality is a gate question, not a truth question). Write "citation" in the note.
3. Judge against the fact table, never against baseball knowledge or the real game. If unsure, choose **unsupported** and write "unsure".
4. **Truth against the fact table, not policy (amendment 1).** A comparison, cause or statement that is correct according to the fact table is **supported**, even if a gate forbids it by policy (D62). **unsupported** means the fact table does not establish it. Policy violations are measured from the gate findings, never from your labels.
5. Do not look at gate findings, NLI scores or the accepted/rejected status. The sheets do not show them.
6. **Similarity or contrast between the starters or lineups (v2).** A judgment that the two starters or the two lineups are alike or different ("similar profiles", "contrasting", "opposite") is **unsupported** unless the fact table states it explicitly.
7. **"Watch ..." lines (v2).** A "Watch ..." line is **not-a-claim** only if it asserts and evaluates nothing. If it implies an evaluation the facts do not establish ("maintain its walk rate", "keep being strong"), it is **unsupported**.

Two optional notes help the analysis: `note` (free text, one line) and `unsure` (Y/blank). Neither is required.

## 3. Sample (stratified, drawn by code with a recorded seed)

The unit is a sentence of a model candidate, from any content attempt. The run-5 dev reports average 20 sentences per candidate (range 16-24, 18 candidates), which sets the sizes below. Report-level findings (no sentence) are not in the frame.

Each sentence goes to exactly one stratum, by priority B, then A, then C.

| Stratum | Contents | Dev (practice) | Test |
|---|---|---:|---:|
| **A** accepted | every sentence of every accepted report: the 5 accepted test reports (about 100 sentences at the dev average of 20.4; test sentences are not counted before the FROZEN step), and 3 of the 6 accepted dev reports (chosen by the seed, about 60). If the test total exceeds 130, whole reports are dropped at random until it does not | about 60 | about 100 (max 130) |
| **B** flagged | the sentence a hard gate flagged, by class (W0, W1.entity, W1.number, W2, W4, W5, W7, W8, W10, W12, W15, any other sentence-level class). Round-robin over the classes, one sentence at a time from each (random order inside the class) until the quota or the supply runs out; every sentence of a class with fewer than the per-class share is taken | 25 | 150 |
| **C** clean in rejected | sentences of rejected candidates that no gate flagged, balanced over four NLI bands: below 0.1, 0.1 to 0.5, 0.5 to 0.9, 0.9 or more (score-less sentences go in a fifth stratum of at most 10) | 20 | 90 (about 20 per band plus the fifth) |
| Total | | about 105 | about 340 (max 370) |

- Seed: `20261106`, recorded in the sheet manifest with the SHA-256 of every B1 output file the sample was drawn from. The inclusion probability of every item (sampled count over stratum size) is stored, so every rate is estimated with the sampling weights and a 95% interval, never with raw counts.
- The dev set is drawn first and labeled first, for practice. Test is drawn from the sealed outputs only after the FROZEN step in section 8.
- Sizes are fixed now, not after seeing the results. If a stratum has fewer sentences than its quota, all are taken and the shortfall is not moved to another stratum.

## 4. Time budget (11 hours total)

At about 1 minute per sentence once warm, and 1.5 for the first dev items:

| Block | When | Items | Time |
|---|---|---:|---:|
| Read the definitions, label the 3 pilot items together with the notes | Nov 6 | 5 | 20 min |
| Dev practice, all dev items | Nov 6 | about 105 | 2 h |
| Blind pairwise sheet U1, dev pairs (section 11) | Nov 6 | 6 pairs | about 20 min |
| Test stratum A (the false-accept question) | Nov 6-7 | about 100 | about 1.7 h |
| Test stratum B | Nov 7 | 150 | about 2.5 h |
| Test stratum C | Nov 8 | 90 | about 1.5 h |
| Re-label a random 10% of items labeled on earlier days (Nov 6-7), blind (self-agreement) | Nov 8 | about 35 | 35 min |
| Blind pairwise sheet U1, test pairs, drawn only after the FROZEN step (section 11) | Nov 8 | 5 pairs | about 25 min |
| Slack, breaks, the notes | | | about 2.5 h |

That is about 9 h of the 11, so there are about 2 h of slack; if the pace is slower, spend the slack before cutting anything. If the pace is slower, the order of the blocks is the order of value: A first, then B, then C; the re-label block is the first to cut. A stratum left unfinished is reported as unlabeled and its metrics are not published.

## 5. Sheet format

Built by a script on the owner's PC (a later task, `evals/labeling_sheet.py`), written under `.local/p2-2/labeling/` and never committed. Test sheets exist only after the FROZEN step.

One CSV per split (`dev_sheet.csv`, `test_sheet.csv`), opened in Excel or Google Sheets, UTF-8:

| Column | Content |
|---|---|
| `item` | opaque id (random, no case or gate information) |
| `case_group` | G01 ... G20: items are grouped by case so the fact table is read once; groups and the items inside them are shuffled |
| `sentence` | the model sentence as shown to a fan |
| `cited_facts` | the facts the sentence cites, as `F012 | subject | field | value | scope` lines |
| `label` | one of the four labels (data validation list) |
| `unsure` | Y or blank |
| `note` | free text |

A second file per split, `facts_<group>.csv`, holds the case's complete enumerated fact table (the same table the writer received) and the glossary, for rule 3. The sheets omit the gate findings, NLI score, stratum, candidate acceptance, attempt number and model. A `manifest.json` (kept apart from the sheets) records for each `item` its stratum, case, attempt, gate findings, NLI score, inclusion probability and the output hash; the analysis joins on `item` only after the labels are complete.

## 6. Metrics computed from the labels

Let an *error* be a label of wrong-number-or-name or unsupported. not-a-claim items are excluded from every rate and counted separately.

1. **Gate precision, per class**: error rate among the sentences the class flagged (stratum B, weighted). Also the wrong-number-or-name share, to tell whether the class catches the error it names.
2. **Harness-rigidity rate, per class**: share of flagged sentences labeled supported. This replaces my run-5 verdicts with measured ones.
3. **False-accept rate** (strata A): the share of accepted reports with at least one error sentence, and the share of accepted sentences that are errors.
4. **Gate-set recall**: among labeled errors in strata B and C, the weighted share that a hard gate flagged. Per class recall is reported only when the labeled errors of that kind number at least 10; otherwise it is "insufficient".
5. **NLI**: AUROC of the score against supported vs error; precision and recall of "supported" at 0.5 and 0.9; the gate-by-NLI cross-table (does NLI separate the sentences the gates disagree with the owner on). The threshold, if any is proposed, is chosen on dev labels only and then reported unchanged on test.
6. **Owner reliability**: self-agreement on the re-labeled 10% (drawn only from items labeled on earlier days, never from the same session) (percent and Cohen's kappa) and the share marked unsure. These bound how good any rate can be.
7. **Secondary**: B1 acceptance rate for dev (20), test (20) and all 40, with Wilson intervals.

Everything is reported by split. Test numbers are produced once, after the dev numbers and the judge freeze are written, and are not used to change a gate in this task.

## 7. What the Groq judge must still do under Plan B (minimum scope)

Judge: Groq Free `openai/gpt-oss-120b` (D46). No Groq call is made by this draft.

1. **Only one job:** give a four-label verdict, on the same definitions, for the sentences in the owner's labeled sample, so that judge-versus-owner agreement can be measured. It judges nothing else.
2. **Dropped under Plan B** (deferred, not deleted; each needs an owner decision to revive): the after-publication Groq call per report (G2, L1, R1, S1 per rule, policy), the ordered U1 pairwise comparisons, and everything for B2. The owner has no hours for their labels, so their judge scores could not be calibrated. S1 stays as detector counts only.
3. **Frozen before any test sentence is seen by it:** judge prompt text, output schema, model id and parameters, the invalid-response rule (a missing or invalid verdict is "missing", never a pass, never silently retried beyond one declared retry), and the batching rule, all recorded in a freeze file with their SHA-256, committed before the FROZEN step of section 8.
4. **Calibration on dev only:** up to three passes over the dev sample, with the dev labels; the prompt that scores best on dev is the one frozen. Test is judged once.
5. **Rough size** (assumption, to be measured in the first dev pass): about 105 dev sentences per pass and up to 370 test sentences. At roughly 1,400 tokens per sentence, one test pass is about 520K tokens, which is under three quota-days at 200K per day, or fewer with batching of 8-10 sentences per call (a batching rule must itself be frozen). The Groq limits are the ones in `docs/plans/P2.md`; they are to be confirmed against the account headers before the freeze.
6. The judge's verdicts are scores. They never gate or approve a report (D17); the owner's labels decide every conclusion.

## 8. Order of work and the seal

1. Owner approves this protocol (or edits it); I record the approved version.
2. Task: build `evals/labeling_sheet.py` with tests (the sampler, the seed, the stratum rules, the blind sheet, the manifest, the metrics), red tests first. No test sentence is read by anyone.
3. Task: draw and write the dev sheet; the owner starts the dev practice.
4. Task: judge prompt, schema and parameters frozen with dev calibration; freeze file committed.
5. The FROZEN file for the B1 test outputs is written by running the sheet script on the owner's PC (`seal.freeze_line`), the first time anyone opens those outputs. The test sheet is then drawn and labeled; the judge runs on the test sample once.
6. Metrics are computed by the script from the labels; the report states per split what was and was not labeled.

## 9. Decisions this protocol asked the owner to confirm

1. The four labels and their rules (section 2), including rule 2 (a true sentence with a wrong citation is supported).
2. Stratum sizes (section 3) and the 11-hour budget (section 4), in particular that stratum A labels every sentence of every accepted test report (5 reports).
3. Dropping the after-publication judge, U1 and S1 judging under Plan B (section 7, item 2).
4. That the sheets hide gate findings and NLI scores from the owner while labeling.

## 10. Owner approval and amendments (Nov 3 2026, version 1)

Approved as written, with the four labels (rule 2 included), the stratum sizes, the 11-hour budget, dropping the after-publication judge, U1 judge comparisons, S1 judging and B2, and blind sheets. Amendments, all applied above:

1. Labels judge truth against the fact table, not policy (hard-case rule 4); "a comparison" removed from the unsupported examples.
2. The step that compared the owner's dev labels with an agent findings table is removed; the labels stay independent of any agent verdict.
3. A minimal U1 block is added (section 11).
4. The self-agreement re-label sample is drawn only from items labeled on earlier days (Nov 6-7).

## 11. U1 blind pairwise block (amendment 3)

About 45 minutes in all, from the slack. The pairs are the 11 accepted B1 reports (6 dev, 5 test), each shown beside the rules report of the same case, in random left/right order, with no source labels. For each pair the owner chooses which report is more useful for a casual fan (`left`, `right` or `tie`) and may add a note. Dev pairs are drawn with the dev sheet; test pairs are drawn only after the FROZEN step. The win, tie and loss rate of the model report against the rules report is reported with a Wilson interval and is a **secondary** result; no judge is involved. Files: `dev_pairs.csv` and `test_pairs.csv`, with the left/right assignment only in the manifest.

## 12. Version 2 amendments (Nov 4 2026, owner)

From the owner's dev practice, applied before the test sheet is drawn:

1. Hard-case rule 6: a similarity or contrast judgment between the two starters or lineups is unsupported unless the fact table states it explicitly.
2. Hard-case rule 7: a "Watch ..." line is not-a-claim only if it asserts and evaluates nothing; if it implies an evaluation the facts do not establish, it is unsupported.
3. The judge prompt carries both rules (prompt version `judge-p2`). Dev labels were made before these rules were written down; they reflect the owner's practice, which the rules record.
