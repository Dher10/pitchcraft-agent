# Plan B results: how accurate are the gates and the NLI score, by the owner's labels

Written for: the owner, and for anyone who reads the case study or the Kaggle writeup later. Computed Nov 6 2026 from the owner's complete labels. **The judge agreement is not here yet** (section 8 is a placeholder until the test judging run finishes).

Sources: protocol `docs/plans/P2-planB-labeling-v2.md` (section 6 defines every metric), decision D64, the B1 run on 40 cases (20 dev, 20 test). Dev and test are reported apart. The test numbers were computed once, after the dev numbers, and nothing here changes a gate.

## 1. In plain language

- **On test, the hard gates reject far more sentences than they should, driven by 2 reports.** On test, 40 sentences were flagged by a hard gate (all of them were taken, none sampled out) and the owner judged 36 of them supported. Only 4 flagged sentences (10.0%, 95% interval 4.0% to 23.1%) were really unsupported. Most of the noise comes from the entity check W1.entity: 19 flagged test sentences, 19 supported, and all 19 sit in just 2 reports.
- **The gates do not make an accepted report safe.** Of the 5 accepted test reports, 3 contained at least one sentence the owner labeled unsupported (60%, interval 23% to 88%). Across the 104 accepted test sentences that count, 3 were errors (2.9%, interval 1.0% to 8.1%). All 3 are "unsupported" (a claim the fact table does not establish), none is a wrong number or name. On dev the same measure was 3 of 3 reports and 10 of 65 sentences (15.4%), but the dev labels turned out unstable (section 5).
- **Most real errors carry no gate flag.** In the test sample, 12 sentences were labeled errors: 4 had a gate flag, 8 did not (3 inside accepted reports, 5 among the clean sentences of rejected reports). This is a count of the sample, not a population rate, and all 12 are "unsupported". I did not check which kind of unsupported claim they are.
- **NLI is not a usable gate yet.** On dev its ranking of supported against error sentences is close to chance (AUROC 0.55). On test it is better (0.73) but rests on only 7 scored error sentences. No threshold is proposed.
- **The model report lost more pairs than it won in U1** (3 wins, 1 tie, 7 losses over 11), with a wide interval and a blinding problem (section 7). I would not read it as a finding about report quality.
- **Overall acceptance** of the model report by the gates: 11 of 40 (27.5%, interval 16.1% to 42.8%).

## 2. Method in short

- **Samples.** Dev: 113 sentences (A accepted 66, B flagged 25, C clean in rejected 22), 6 pairs. Test: 235 sentences (A 105, B 40, C 90), 5 pairs. The test B stratum is supply-limited: every flagged sentence was taken (inclusion probability 1), so the 40 are a census of the flagged sentences of the 20 test cases, not a draw. Seed 20261106.
- **Labels.** One labeler (the owner), four labels, truth judged against the fact table (protocol section 2). An *error* is `wrong-number-or-name` or `unsupported`. `not-a-claim` sentences (dev 2, test 1) are excluded from every rate.
- **Weights and intervals.** Every rate uses inverse inclusion probability weights. Intervals are 95% Wilson intervals on the Kish effective sample size, so a heavily weighted stratum widens them. Intervals treat sentences as independent, which they are not (section 9).
- **Dev and test use different rules.** Dev was labeled under protocol v1 (digest `886bf60f...`), test under v2 (digest `4f627a80...`), which adds hard-case rules 6 (similarity or contrast between starters is unsupported) and 7 ("Watch" lines). The dev labels reflect the owner's practice before those rules were written down.
- **Commands.** `python -m evals.labeling_sheet check --split dev` and `--split test` (both: ids intact, every filled value valid; dev re-label 12 filled, test re-label 24 filled), then `python -m evals.labeling_sheet metrics --split dev` and `--split test`. A few counts the tool does not print (label mix per stratum, re-label transitions, pooled U1, pair lengths, how many W1.entity sentences sit in how many reports) come from a read-only one-off script that calls the same functions; it is not in the repo.
- **"insufficient".** For gate classes: fewer than 5 labeled claim sentences (the raw counts are shown anyway). For recall: fewer than 10 labeled errors, as the protocol says. This 5 is my choice for this report, applied identically to dev and test.

Label mix (owner, unweighted):

| Split | Stratum | supported | wrong-number-or-name | unsupported | not-a-claim |
|---|---|---:|---:|---:|---:|
| dev | A | 55 | 6 | 4 | 1 |
| dev | B | 19 | 3 | 2 | 1 |
| dev | C | 17 | 3 | 2 | 0 |
| test | A | 101 | 0 | 3 | 1 |
| test | B | 36 | 0 | 4 | 0 |
| test | C | 85 | 0 | 5 | 0 |

## 3. Gate precision and harness-rigidity rate per hard-gate class (stratum B)

*Precision* = share of flagged sentences that are errors. *Rigidity* = share of flagged sentences labeled supported (a false alarm). A sentence flagged by two classes counts in both (dev 3, test 1 such sentences). The "wrong / unsupp / supported" column is raw counts.

**Dev** (25 flagged sentences, 13 classes). All classes together: 5 errors in 24 claim sentences, weighted precision 23.6% [10.1%, 45.8%].

| Class | Claims | wrong / unsupp / supported | Precision | Wrong-name share | Rigidity |
|---|---:|---|---|---|---|
| W1.number | 5 | 0 / 0 / 5 | 0.0% [0.0%, 46.5%] | 0.0% [0.0%, 46.5%] | 100.0% [53.5%, 100.0%] |
| W0.sentence | 3 | 0 / 0 / 3 | insufficient | insufficient | insufficient |
| W1.entity | 3 (+1 not-a-claim) | 0 / 0 / 3 | insufficient | insufficient | insufficient |
| W10.cause | 3 | 0 / 0 / 3 | insufficient | insufficient | insufficient |
| W8.form | 3 | 2 / 0 / 1 | insufficient | insufficient | insufficient |
| W12.time | 2 | 0 / 0 / 2 | insufficient | insufficient | insufficient |
| W15.outcome | 2 | 0 / 1 / 1 | insufficient | insufficient | insufficient |
| W1.fact_id | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W1.no_evidence | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W2.comparison | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W4.topic | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W5.label | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W7.missing | 1 (+1 not-a-claim) | 0 / 1 / 0 | insufficient | insufficient | insufficient |
| W8.value | 1 | 1 / 0 / 0 | insufficient | insufficient | insufficient |

**Test** (40 flagged sentences, 10 classes, a census). All classes together: 4 errors in 40 claim sentences, precision 10.0% [4.0%, 23.1%], none a wrong number or name.

| Class | Claims | wrong / unsupp / supported | Precision | Wrong-name share | Rigidity |
|---|---:|---|---|---|---|
| W1.entity | 19 | 0 / 0 / 19 | 0.0% [0.0%, 16.8%] | 0.0% [0.0%, 16.8%] | 100.0% [83.2%, 100.0%] |
| W12.time | 8 | 0 / 2 / 6 | 25.0% [7.1%, 59.1%] | 0.0% [0.0%, 32.4%] | 75.0% [40.9%, 92.9%] |
| W1.number | 3 | 0 / 1 / 2 | insufficient | insufficient | insufficient |
| W15.outcome | 3 | 0 / 1 / 2 | insufficient | insufficient | insufficient |
| W10.cause | 2 | 0 / 0 / 2 | insufficient | insufficient | insufficient |
| W2.comparison | 2 | 0 / 0 / 2 | insufficient | insufficient | insufficient |
| W3.prediction | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W5.label | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W7.missing | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |
| W8.form | 1 | 0 / 0 / 1 | insufficient | insufficient | insufficient |

Reading: only W1.number (dev), W1.entity and W12.time (test) have enough sentences to state a rate, and W1.entity's 19 sentences come from 2 reports (13 from one case, 6 from another), so its evidence is closer to 2 independent observations than 19. On dev, W1.entity flagged 3 supported sentences from 3 reports. Over both splits W1.entity flagged 22 claim sentences and none was an error. W8.form and W8.value are the only classes whose dev flags were mostly right (3 of 4 flagged claim sentences were wrong numbers or names), too few to rate.

## 4. False-accept rate (stratum A)

| | Accepted reports with at least one error sentence | Accepted sentences that are errors |
|---|---|---|
| Dev (3 of the 6 accepted reports, chosen by seed) | 3 of 3: 100% [43.8%, 100%] | 10 of 65: 15.4% [8.6%, 26.1%] (6 wrong-number-or-name, 4 unsupported) |
| Test (all 5 accepted reports) | 3 of 5: 60.0% [23.1%, 88.2%] | 3 of 104: 2.9% [1.0%, 8.1%] (0 wrong-number-or-name, 3 unsupported) |

Per accepted test report, errors / labeled sentences (one not-a-claim sentence is in each split's total, so these sum to 105 and 66, not 104 and 65): 0/20, 0/20, 1/21, 1/21, 1/23. Dev: 3/20, 2/23, 5/23. By construction no sentence in A carries a gate flag, so every error in A is a miss of the gate set.

## 5. Gate-set recall (strata B and C, weighted)

Recall = weighted share of labeled errors that carry a hard-gate flag. Per protocol, published only with at least 10 labeled errors, and per class only with 10 errors of its own.

| Split | Labeled errors in B and C | Recall of the gate set | Per class |
|---|---:|---|---|
| Dev | 10 (5 flagged in B, 5 clean in C) | 10.1% [0.8%, 62.4%], effective n 3.3 | all insufficient |
| Test | 9 (4 flagged in B, 5 clean in C) | insufficient (9 < 10) | all insufficient |

The dev figure is dominated by the 5 clean-sentence errors, each of which stands for about 40 sentences (inclusion probability as low as 0.024), which is why the interval is so wide. For orientation only, unweighted and not a protocol metric: test 4 of 9 errors carried a flag; dev 5 of 10. Recall here covers rejected candidates only. The errors inside accepted reports (section 4) are additional misses.

## 6. NLI (score only, never a gate)

Scored sentences exclude not-a-claim: dev 93 (78 supported, 15 error), test 195 (188 supported, 7 error). AUROC compares the score of supported against error sentences and is unweighted across strata. Thresholds are the protocol's fixed 0.5 and 0.9, identical on both splits. **No threshold was chosen or proposed**: dev AUROC is near chance, so there was nothing to tune on dev and carry to test.

| | AUROC | Precision of "supported" at 0.5 | Recall at 0.5 | Precision at 0.9 | Recall at 0.9 |
|---|---|---|---|---|---|
| Dev | 0.548 | 80.1% [51.6%, 93.8%] | 62.6% [40.7%, 80.3%] | 81.8% [49.2%, 95.4%] | 55.2% [34.1%, 74.6%] |
| Test | 0.728 | 98.8% [90.1%, 99.9%] | 69.5% [58.8%, 78.5%] | 100% [90.0%, 100%] | 60.2% [49.3%, 70.1%] |

The test precision is high mostly because 96% of the scored test sentences are supported (a score of 0.5 on a pile that is almost all supported looks good by default). There are only 7 scored errors on test, so the AUROC has no usable interval; I did not compute one.

Gate-by-NLI cross-table (counts of labeled, scored sentences with NLI at or above the threshold; supported / error):

| | Dev nli ≥ 0.5 | Dev nli ≥ 0.9 | Test nli ≥ 0.5 | Test nli ≥ 0.9 |
|---|---|---|---|---|
| No gate flag | 48 (39 / 9) | 37 (33 / 4) | 94 (92 / 2) | 70 (70 / 0) |
| Gate flagged | 6 (5 / 1) | 5 (4 / 1) | 13 (13 / 0) | 10 (10 / 0) |

Reading: where the gates and the owner disagree (a flagged sentence the owner calls supported), NLI sides with the owner on test (13 of 13 flagged sentences with score ≥ 0.5 are supported). On dev, NLI at 0.9 still let 4 errors through among 37 unflagged sentences.

## 7. Owner reliability, U1 and acceptance

**Self-agreement** (re-label of about 10% of items labeled on earlier days, blind):

| Split | Items | Agreement | Cohen's kappa | Changes |
|---|---:|---|---:|---|
| Dev | 12 | 58.3% [32.0%, 80.7%] | −0.07 | 4 wrong-number-or-name → supported, 1 supported → unsupported, 7 unchanged |
| Test | 24 | 91.7% [74.2%, 97.7%] | 0.70 | 2 supported → unsupported, 22 unchanged |

All 4 dev sentences first labeled wrong-number-or-name that were re-labeled came back supported, so the dev wrong-number labels (6 in A, 3 in B, 3 in C) are not stable, and the dev false-accept figure above partly depends on them. The unsure flag was never used (0 in both splits), so the unsure share says nothing about confidence. Kappa on test is held down by the label imbalance (21 of the 24 first labels were supported). I did not inspect the re-labeled sentences, so I cannot say whether the dev shift comes from learning during practice, the new hard-case rules or noise.

**U1 (blind pairwise: model report against rules report, "more useful for a casual fan")**:

| Split | Win | Tie | Loss | Win rate [95% Wilson] |
|---|---:|---:|---:|---|
| Dev | 0 | 1 | 5 | 0% [0%, 39.0%] |
| Test | 3 | 0 | 2 | 60% [23.1%, 88.2%] |
| All 11 | 3 | 1 | 7 | 27.3% [9.7%, 56.6%]; loss 63.6% [35.4%, 84.8%] |

Excluding the tie, 3 wins against 7 losses has an exact two-sided sign test p of 0.34, so the data do not separate the two reports. The two splits point in opposite directions. This differs from the owner's qualitative note (`docs/case-study-notes.md`, "the LLM text is clearly more readable"); I have not reconciled the two and did not read the pair notes.

**Blinding limitation (read the U1 numbers with this).** The owner reported being able to identify the LLM report by its style. The sides are also not matched in form: on the pair sheets the rules report averages about 2,370 characters (dev) and 2,260 (test) against about 1,850 and 1,750 for the model report, so length alone separates them. The owner also labeled every sentence of the accepted model reports in stratum A (test: all 5; dev: 3 of 6), so the model text was already known, possibly before the pair sheet was answered (I did not check the order). There is one rater, who built the product. The pair result is a secondary, biased-by-design signal.

**B1 acceptance rate** (the gates' verdict on the run, not the owner's):

| | Accepted | Cases | Rate | 95% Wilson |
|---|---:|---:|---:|---|
| Dev | 6 | 20 | 30.0% | [14.5%, 51.9%] |
| Test | 5 | 20 | 25.0% | [11.2%, 46.9%] |
| All | 11 | 40 | 27.5% | [16.1%, 42.8%] |

## 8. Judge vs owner (test)

**Pending.** The test judging run (judge-p3, strata A, B and C, 235 sentences, 39 batches) is paused after batch 11 by the Groq daily token limit and resumes after 03:45 UTC Nov 7. This section will hold agreement, kappa and the confusion matrix of the judge against the owner's test labels. Dev judge results (judge-p3: 77.9% agreement, kappa 0.46, below the 85% target) are in `docs/STATUS.md`.

## 9. Limitations

- **One labeler, who is also the product's designer.** The owner's labels are the ground truth and nothing checks them except the owner's own re-labels (24 test items, 12 dev items). There is no inter-rater agreement. Dev self-agreement is poor and test self-agreement is acceptable, both on very few items.
- **Small samples, clustered.** 20 cases per split, 11 accepted reports in all. Sentences inside a report are correlated (W1.entity: 19 test flags in 2 reports), so the Wilson intervals, which treat sentences as independent, are too narrow, most of all for the per-class rows. Treat them as lower bounds on the uncertainty.
- **Dev and test are not comparable.** Different labeling rules (v1 against v2), unstable dev wrong-number labels, a dev accepted stratum of only 3 reports. The gates and prompts were developed looking at the dev outputs, so dev numbers are not clean estimates of future performance. The test split is the clean read, and it holds few errors (12 in 235 sentences), none a wrong number or name.
- **Test stratum B is a census, not a sample**, and recall on test is "insufficient" (9 errors).
- **The sample is stratified, not random.** The raw counts in sections 1 and 5 describe the sample; only the weighted figures estimate rates, and they inherit the wide weights of stratum C.
- **Report-level presence checks (W6, W13, W14, W17) are not labeled**; they are covered by unit tests and the run record.
- **NLI AUROC is unweighted across strata** and the test AUROC rests on 7 error sentences.
- **U1**: blinding, one rater, 11 pairs (section 7).
- **Known limitations of the code gates** (`docs/STATUS.md`): finite word lists and lexical patterns do not prove entailment, so unlisted or implied comparisons can escape W2; capitalization-based entity checks can miss lowercase invented names and packet vocabulary can hide a wrong name; per-measurement owner binding does not cover every ellipsis, pronoun or attachment; W5 style-label detection has known holes; **no gate catches similarity or contrast claims between the starters or lineups**. The results above are consistent with this: most errors that exist carry no flag.
- **Judge**: not evaluated here; on dev it agreed with the owner 77.9% of the time, under the 85% target, so it stays a secondary result.

## 10. What the gates catch and miss

*Catch.* The gates' catch of wrong numbers and names cannot be measured on test, because none occurred: the owner found no wrong number or name in any of the 235 test sentences, flagged or not, so the zero may be the writer's doing and not the gates'. On dev, wrong numbers and names did occur (12 in 113 sentences, though their labels proved unstable): 3 sat in the flagged stratum, each with a form or value (W8) flag, and 6 passed the gates inside accepted reports, with 3 more among unflagged clean sentences. The evidence for a protective effect of the number and entity gates is therefore absent on test and negative on dev.

*Over-reject.* A gate flag is a weak sign of an actual error: on test 36 of 40 flagged sentences were fine. The entity check is the main source (all 19 flagged sentences supported, from 2 reports). This is why only 27.5% of the model reports are accepted, and why a rejection tells little about whether the report text was wrong.

*Miss.* Errors that are not wrong numbers or names, meaning claims the fact table does not support, mostly pass. In the test sample 8 of 12 errors had no flag, and 3 of the 5 accepted reports contained one. The text of a code-accepted report is therefore not a guarantee of truth. Known examples of what no gate covers: similarity or contrast between the starters, and evaluative "Watch" lines (protocol rules 6 and 7).

*What this supports.* Keeping the rules writer in production (D64: the LLM text is score only and does not publish) is consistent with the evidence. It does not support relaxing the entity check on this sample alone (2 reports), and it does not support using NLI as a gate (dev AUROC 0.55).

## 11. Reproduce

`python -m evals.labeling_sheet check --split dev`, `... check --split test`, `... metrics --split dev`, `... metrics --split test`. They read the untracked `.local/p2-2/labeling/` files, so they run on the owner's PC only. No file under `public/data/` or `evals/live/` was read or changed.
