# Plan B results: how accurate are the gates and the NLI score, by the owner's labels

Written for: the owner, and for anyone who reads the case study or the Kaggle writeup later. Computed Nov 6 2026 from the owner's complete labels. The judge agreement is in section 8.

Sources: protocol `docs/plans/P2-planB-labeling-v2.md` (section 6 defines every metric), decision D64, the B1 run on 40 cases (20 dev, 20 test). Dev and test are reported apart. The test numbers were computed once, after the dev numbers, and nothing here changes a gate.

## 1. In plain language

- **On test, the hard gates reject far more sentences than they should, driven by 2 reports.** On test, 40 sentences were flagged by a hard gate (all of them were taken, none sampled out) and the owner judged 36 of them supported. Only 4 flagged sentences (10.0%, 95% interval 4.0% to 23.1%) were really unsupported. Most of the noise comes from the entity check W1.entity: 19 flagged test sentences, 19 supported, and all 19 sit in just 2 reports.
- **The gates do not make an accepted report safe.** Of the 5 accepted test reports, 3 contained at least one sentence the owner labeled unsupported (60%, interval 23% to 88%). Across the 104 accepted test sentences that count, 3 were errors (2.9%, interval 1.0% to 8.1%). All 3 are "unsupported" (a claim the fact table does not establish), none is a wrong number or name. On dev the same measure as labeled was 3 of 3 reports and 10 of 65 sentences (15.4%), but 6 of those 10 are one boilerplate phrase that the owner's later re-labels and all test labels treat as supported; without it dev reads 2 of 3 reports and 4 of 65 sentences (6.2%) (section 12).
- **Most real errors carry no gate flag.** In the test sample, 12 sentences were labeled errors: 4 had a gate flag, 8 did not (3 inside accepted reports, 5 among the clean sentences of rejected reports). This is a count of the sample, not a population rate, and all 12 are "unsupported". I did not check which kind of unsupported claim they are.
- **NLI is not a usable gate yet.** On dev its ranking of supported against error sentences is close to chance (AUROC 0.55). On test it is better (0.73) but rests on only 7 scored error sentences. No threshold is proposed.
- **The model report lost more pairs than it won in U1** (3 wins, 1 tie, 7 losses over 11), with a wide interval and the blinding limitation of section 7. The owner reads it as a stated-versus-revealed preference: the LLM sentences read better, but whole reports were chosen less often than the longer, more informative rules reports (section 12.1).
- **The judge (judge-p3) agrees with the owner on 79.6% of the 235 test sentences, kappa 0.17**, under the 85% target. It found 5 of the owner's 12 errors and flagged 29 sentences the owner calls supported.
- **Overall acceptance** of the model report by the gates: 11 of 40 (27.5%, interval 16.1% to 42.8%).

## 2. Method in short

- **Samples.** Dev: 113 sentences (A accepted 66, B flagged 25, C clean in rejected 22), 6 pairs. Test: 235 sentences (A 105, B 40, C 90), 5 pairs. The test B stratum is supply-limited: every flagged sentence was taken (inclusion probability 1), so the 40 are a census of the flagged sentences of the 20 test cases, not a draw. Seed 20261106.
- **Labels.** One labeler (the owner), four labels, truth judged against the fact table (protocol section 2). An *error* is `wrong-number-or-name` or `unsupported`. `not-a-claim` sentences (dev 2, test 1) are excluded from every rate.
- **Weights and intervals.** Every rate uses inverse inclusion probability weights. Intervals are 95% Wilson intervals on the Kish effective sample size, so a heavily weighted stratum widens them. Intervals treat sentences as independent, which they are not (section 9).
- **Dev and test use different rules.** Dev was labeled under protocol v1 (digest `886bf60f...`), test under v2 (digest `4f627a80...`), which adds hard-case rules 6 (similarity or contrast between starters is unsupported) and 7 ("Watch" lines). The dev labels reflect the owner's practice before those rules were written down.
- **Commands.** `python -m evals.labeling_sheet check --split dev` and `--split test` (both: ids intact, every filled value valid; dev re-label 12 filled, test re-label 24 filled), then `python -m evals.labeling_sheet metrics --split dev` and `--split test`. A few counts the tool does not print (label mix per stratum, re-label transitions, pooled U1, pair lengths, how many W1.entity sentences sit in how many reports) come from a read-only one-off script that calls the same functions; it is not in the repo.
- **"insufficient".** For gate classes: fewer than 5 labeled claim sentences (the raw counts are shown anyway). For recall: fewer than 10 labeled errors, as the protocol says. This 5 is my choice for this report, applied identically to dev and test.

**Correction (section 12): all 12 dev `wrong-number-or-name` labels are the same sentence template (the gloss "compared with a pitch thrown without spin" after a movement figure), not a wrong number or a wrong name.** The table shows the labels as given.

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

Reading: only W1.number (dev), W1.entity and W12.time (test) have enough sentences to state a rate, and W1.entity's 19 sentences come from 2 reports (13 from one case, 6 from another), so its evidence is closer to 2 independent observations than 19. On dev, W1.entity flagged 3 supported sentences from 3 reports. Over both splits W1.entity flagged 22 claim sentences and none was an error. The 3 dev wrong-number-or-name labels in B (W8.form 2, W8.value 1) are the gloss template of section 12; counting that gloss as supported, as the owner's re-labels and the test labels do, W8.form and W8.value have 0 errors in 4 flagged claim sentences and dev B precision falls to 2 of 24 (5.4% [1.0%, 24.7%]).

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

All 4 dev sentences first labeled wrong-number-or-name that were re-labeled came back supported. They are 4 of the 12 dev sentences that carry the same gloss ("compared with a pitch thrown without spin"), which the owner first marked wrong with the note that the phrase "wasn't necessary"; on re-label the figures were judged right and the sentence supported. The fifth change (supported → unsupported) is "They maintain a 22.3% K% ... and a 9.0% BB% ... in this split", where "maintain" implies an evaluation, which is what hard-case rule 7 later wrote down. So rules 6 and 7 explain at most 1 of the 5 dev changes; the other 4 are a convention change about one gloss phrase (section 12). The unsure flag was never used (0 in both splits), so the unsure share says nothing about confidence. Kappa on test is held down by the label imbalance (21 of the 24 first labels were supported).

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

Judge judge-p3 (`openai/gpt-oss-120b`, temperature 0, reasoning low, frozen spec `evals/data/writer/judge-freeze.json`), judged once on the 235 test sentences (strata A, B and C), 39 batches, 43 calls (47 attempts, the 4 failed attempts were retried or resumed, no batch left unjudged, 0 missing, `unsure` flagged 0 times), 252,837 tokens, in two quota-limited sessions (Nov 6 and Nov 7, resumed from the state file after the abort rule paused it). The judge never saw the owner's labels. Computed with `jf.judge_agreement` against the owner's test labels; unweighted, over the sample as drawn, not stratum-weighted.

| Measure | Value |
|---|---|
| Agreement, all four labels | **187 of 235 = 79.6%** (95% Wilson 74.0% to 84.2%) |
| Cohen's kappa | **0.17** |
| Error versus supported, claim sentences only (not-a-claim excluded) | 188 of 220 = 85.5% |
| By stratum (agreement; kappa) | A 86 of 105 = 81.9% (0.17); B 27 of 40 = 67.5% (0.17); C 74 of 90 = 82.2% (0.15) |
| Target | 85% per judged dimension (`docs/eval-spec.md`); **not met** on the four-label agreement |

Confusion matrix (rows: owner label; columns: judge label; counts):

| Owner \ Judge | supported | wrong-number-or-name | unsupported | not-a-claim | Total |
|---|---:|---:|---:|---:|---:|
| supported | 183 | 8 | 21 | 10 | 222 |
| wrong-number-or-name | 0 | 0 | 0 | 0 | 0 |
| unsupported | 3 | 1 | 4 | 4 | 12 |
| not-a-claim | 0 | 0 | 1 | 0 | 1 |
| Total | 186 | 9 | 26 | 14 | 235 |

Reading, from the counts only:

- The owner labeled 222 of 235 sentences supported (94.5%), so a judge that said "supported" every time would agree on 94.5%; the judge's 79.6% is below that trivial baseline and kappa is low (0.17) for the same reason. Treat the agreement percentage and the kappa together.
- Of the owner's 12 errors the judge flagged 5 as an error (4 unsupported, 1 wrong-number-or-name) and passed 3 as supported (4 more were read as not-a-claim). Of the 35 sentences the judge called an error (9 wrong-number-or-name, 26 unsupported), 5 are errors by the owner's label, 29 are owner-supported (8 + 21) and 1 is owner not-a-claim: judge error precision 5 of 35 = 14.3%, recall 5 of 12 = 41.7%.
- The judge called 9 sentences wrong-number-or-name; the owner found no wrong number or name anywhere in the test sheet (8 of the 9 are owner-supported sentences).
- Dev (judge-p3 on the 113 dev sentences, labels of protocol v1): 77.9% agreement, kappa 0.46, so the test result is similar in percent and lower in kappa.

The judge stays a secondary, score-only result (D17, D64): it never gates or approves a report, and it does not reach the 85% target on this sample.

## 9. Limitations

- **One labeler, who is also the product's designer.** The owner's labels are the ground truth and nothing checks them except the owner's own re-labels (24 test items, 12 dev items). There is no inter-rater agreement. Dev self-agreement is poor and test self-agreement is acceptable, both on very few items.
- **Small samples, clustered.** 20 cases per split, 11 accepted reports in all. Sentences inside a report are correlated (W1.entity: 19 test flags in 2 reports), so the Wilson intervals, which treat sentences as independent, are too narrow, most of all for the per-class rows. Treat them as lower bounds on the uncertainty.
- **Dev and test are not comparable.** Different labeling rules (v1 against v2), dev wrong-number labels that are all one gloss phrase later treated as supported (section 12), a dev accepted stratum of only 3 reports. The gates and prompts were developed looking at the dev outputs, so dev numbers are not clean estimates of future performance. The test split is the clean read, and it holds few errors (12 in 235 sentences), none a wrong number or name.
- **Test stratum B is a census, not a sample**, and recall on test is "insufficient" (9 errors).
- **The sample is stratified, not random.** The raw counts in sections 1 and 5 describe the sample; only the weighted figures estimate rates, and they inherit the wide weights of stratum C.
- **Report-level presence checks (W6, W13, W14, W17) are not labeled**; they are covered by unit tests and the run record.
- **NLI AUROC is unweighted across strata** and the test AUROC rests on 7 error sentences.
- **U1**: blinding, one rater, 11 pairs (section 7).
- **Known limitations of the code gates** (`docs/STATUS.md`): finite word lists and lexical patterns do not prove entailment, so unlisted or implied comparisons can escape W2; capitalization-based entity checks can miss lowercase invented names and packet vocabulary can hide a wrong name; per-measurement owner binding does not cover every ellipsis, pronoun or attachment; W5 style-label detection has known holes; **no gate catches similarity or contrast claims between the starters or lineups**. The results above are consistent with this: most errors that exist carry no flag.
- **Judge**: evaluated in section 8 on the same single-labeler ground truth; the test sheet has only 12 owner errors, so judge recall on errors (5 of 12) is very uncertain, and the agreement is dominated by the 222 supported sentences.

## 10. What the gates catch and miss

*Catch.* The gates' catch of wrong numbers and names cannot be measured: the owner found no real wrong number or name in any of the 348 labeled sentences. On test none was labeled; on dev the 12 `wrong-number-or-name` labels are all the movement-gloss phrase of section 12, which the owner's own re-labels and the test labels count as supported. The number and entity gates therefore have no measured catch here, and no measured miss either.

*Over-reject.* A gate flag is a weak sign of an actual error: on test 36 of 40 flagged sentences were fine. The entity check is the main source (all 19 flagged sentences supported, from 2 reports). This is why only 27.5% of the model reports are accepted, and why a rejection tells little about whether the report text was wrong.

*Miss.* Errors that are not wrong numbers or names, meaning claims the fact table does not support, mostly pass. In the test sample 8 of 12 errors had no flag, and 3 of the 5 accepted reports contained one. The text of a code-accepted report is therefore not a guarantee of truth. Known examples of what no gate covers: similarity or contrast between the starters, and evaluative "Watch" lines (protocol rules 6 and 7).

*What this supports.* Keeping the rules writer in production (D64: the LLM text is score only and does not publish) is consistent with the evidence. It does not support relaxing the entity check on this sample alone (2 reports), and it does not support using NLI as a gate (dev AUROC 0.55).

## 11. Reproduce

`python -m evals.labeling_sheet check --split dev`, `... check --split test`, `... metrics --split dev`, `... metrics --split test`. They read the untracked `.local/p2-2/labeling/` files, so they run on the owner's PC only. No file under `public/data/` or `evals/live/` was read or changed.

## 12. Follow-ups of Nov 7 (owner questions; no label was changed)

The hash, content and sensitivity figures of this section come from read-only one-off scripts that call the same `evals.labeling_sheet` functions; they are not in the repo (only the orientation test is).

### 12.1 U1 integrity: the mapping and the computation are correct; your recollection and the saved data disagree

Check run on the saved `dev_pairs.csv` and `test_pairs.csv` (the files you filled), the stored pairs manifests and the B1 outputs, without printing any report text:

- The stored manifests equal the manifests regenerated from the B1 outputs with the same seed, and the saved sheet text equals the regenerated text, for all 11 pairs.
- For every pair the accepted B1 attempt (checks empty, run record: 6 dev and 5 test accepted) exists, and all of its resolved sentences (20 to 23 per report) appear in the side recorded as "model" and in none of the side recorded as "rules".
- The SHA-256 of the rendered model report and of the rendered rules report each equal the SHA-256 of the corresponding side in the saved sheet (whitespace-normalized); hash prefixes below.
- Independent content check: the rules-writer template phrase "brings this strength" occurs twice on the side recorded as "rules" and nowhere on the side recorded as "model", in all 11 pairs.
- The win/loss computation (`u1_summary`) was recomputed independently from the raw saved choice and the manifest and gave the same totals (3 / 1 / 7). It reads `left`/`right` as the columns of the saved sheet.

| Pair | Case | Model side | Your saved choice | Outcome | Hash model / rules (SHA-256 prefix) |
|---|---|---|---|---|---|
| P103434 | veteran-824803 | right | tie | tie | eb079fe0 / 7b65049d |
| P810778 | opener-824280 | right | left | loss | 255bdc88 / 0ba37135 |
| P363860 | veteran-823938 | left | right | loss | e5a8b935 / 60ce9bed |
| P439026 | veteran-823940 | left | right | loss | 5844b0c1 / 5911e20a |
| P943895 | postseason-849831 | right | left | loss | c044e7a9 / ca912c11 |
| P694780 | limited-823836 | right | left | loss | 21ef8a8b / f69db022 |
| P499663 | opener-822954 | right | left | loss | b3bf10a8 / 4dd71f7b |
| P348241 | postseason-849851 | left | left | win | 94c776f6 / f4f93da3 |
| P565743 | veteran-823979 | left | left | win | 66318fb9 / 8add0ad5 |
| P980308 | postseason-849830 | left | left | win | 686154c9 / 53b74d38 |
| P790885 | veteran-823012 | left | right | loss | 839e37b3 / 341eeea6 |

**There is no bug, and the owner confirmed the result (Nov 7).** The result stands: 3 wins, 1 tie, 7 losses. The owner states having checked the filled files and found no orientation issue (columns pair, left, right, more_useful, note). The owner's reading is a stated-versus-revealed preference: the general impression from sentence labeling was that the LLM prose reads better, but comparing whole reports the rules report was chosen in 7 of 10 non-tie pairs; the rules reports are about 25% longer and carry more information. Both can hold: the LLM writes better sentences but says less. The earlier recollection recorded before the data (that the elaborate prose was chosen almost always) was therefore not borne out. Regression test added: `test_u1_orientation_survives_the_csv_round_trip_end_to_end` (an owner who always picks the model side scores only wins, the opposite owner only losses, through a CSV round trip); it fails when the orientation in `u1_summary` is flipped (verified by a one-off mutation).

### 12.2 The 8 unflagged test errors and the 3 accepted-report errors, by kind

I read the 12 test sentences labeled as errors and your notes. All 8 unflagged errors fall in the two kinds that hard-case rules 6 and 7 name; none is an invented cause or a wrong number.

| Kind | Unflagged (8) | Of which in accepted reports (3) | Paraphrase |
|---|---:|---:|---|
| Similarity or contrast judgment between the starters | 4 | 1 | "Both starters have distinct (different) pitching profiles", resting only on two style labels; in the accepted case "each starter features a distinct primary pitch", while both cited primary pitches are the same Four-seam |
| "Watch" line with an evaluation or an unlisted detail | 4 | 2 | "Watch if the pitcher locates his fastball", "whether the lineup can manage the strike zone" (evaluation); "how a pitcher uses his sinker early in counts", "how often he throws his slider" (the facts give a count, not a usage share or a count-by-count split) |
| Invented cause | 0 | 0 | |
| Other | 0 | 0 | |

The 4 flagged test errors are one "Watch" line (a lineup strikeout rate with no benchmark) and three sentences about the scope wording or a framing the facts do not give ("two starters looking to settle in", "both teams look for offensive production", "different approaches"); the last one is also a contrast judgment, caught by a time-scope rule by coincidence. Consequence: **no code gate covers the kinds that account for all 8 misses**, which is the known limitation recorded in `docs/STATUS.md`, now measured: on test, every unflagged error was a similarity/contrast or "Watch" sentence.

### 12.3 Why the dev self-agreement moved, and a template problem in the dev labels (the sensitivity table is a separate analysis; the as-labeled dev numbers stay official, owner decision Nov 7)

Of the 5 dev sentences whose label changed on re-label, 4 are the same template and one is a "Watch"/evaluation case:

- All 12 dev sentences labeled `wrong-number-or-name` carry the movement gloss "compared with a pitch thrown without spin" after the two movement figures (e.g. "moves 9.1 in. sideways and 16.3 in. up compared with a pitch thrown without spin"). Your note on each says the phrase "wasn't necessary". No dev sentence is labeled wrong-number-or-name for any other reason. On re-label, the 4 re-labeled ones came back supported. In the test sheet the same gloss appears in 18 sentences and all 18 are labeled supported. The labeling convention for this phrase therefore changed between dev (first pass) and re-label and test.
- The one other change (supported → unsupported) is a "maintain a ... K% and a ... BB%" sentence, an implied evaluation: the rule-7 kind. Rules 6 and 7 explain 1 of the 5 changes, not the shift as a whole.

Sensitivity, labels untouched: treating the 12 gloss sentences as supported in the dev metrics (an analysis, not a relabel; the metric code and the dev manifest are unchanged) gives:

| Dev measure | As labeled | Gloss counted as supported |
|---|---|---|
| Accepted reports with an error | 3 of 3 | 2 of 3 [20.8%, 93.9%] |
| Accepted sentences that are errors | 10 of 65, 15.4% | 4 of 65, 6.2% [2.4%, 14.8%] |
| Flagged sentences (B) that are errors | 5 of 24, 23.6% | 2 of 24, 5.4% [1.0%, 24.7%] |
| W8.form / W8.value precision | 2 of 3 / 1 of 1 | 0 of 3 / 0 of 1 |
| Labeled errors in B and C | 10 (recall 10.1%) | 4 (recall insufficient) |
| NLI AUROC; precision at 0.5 | 0.548; 80.1% | 0.493; 86.7% |

With this reading dev and test tell the same story: the errors are unsupported claims (contrast and "Watch" sentences), the gates flag very little of them, and NLI does not separate supported from error sentences. Only you can decide which reading of the gloss is the intended label; the as-labeled numbers above stay the official dev numbers until you say otherwise.
