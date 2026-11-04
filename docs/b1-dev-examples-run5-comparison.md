# Dev pass, run 5 (fact-ID instrument) review

**Accepted: 4 of 10. Rejected: 6 (all fell back to the rules writer).** Plan A needs 5 or more of 10, so this run is below that line. The decision between Plan A and Plan B is the owner's. No 40-case B1 run was started.

Run time: 2026-11-03 23:52 to 2026-11-04 00:01 UTC (started 2026-11-03 18:52 local on the owner's PC, about 9 minutes). All ten cases were attempted; neither early stop fired.

**Gemini calls: 19/30 run cap; 146/400 experiment cap** (127 before this run). Calls per case: 19/10 = 1.9 (stop: more than 3 per case after the first 5 cases). Capacity failures: 1/19 finished calls (5.3%; stop: more than a third).

Per model: `gemini-3.1-flash-lite` 19 calls, 1 capacity failures; the fallback `gemini-3.5-flash` was not used. Primary `gemini-3.1-flash-lite`, fallback `gemini-3.5-flash`, LOW thinking, default temperature, 20 s pacing, NLI score only.

## Frozen inputs (verified before the run)

- guide `0.7`: `172e12b13e39b8b1a16438ea825ceafd80b96ea4c7f23bf970304ef98ec0b347`
- glossary `1.1`: `f7a22da784278170c617cd03c18f27db6a14236620608fe3f8f77c70e6d58b8d`
- prompt `p2.2-6`: `fc3d476bf3f59bad4a7d645a6e9f81658488097b44c3603e8d6c1956d89c74fd`
- Packets manifest: `0d906f78d42ab013568be535db1716fd329d72033a002a414b1f29625bdc4a25`
- Frozen at commit `0426c02`

Complete raw per-attempt report (every sentence, evidence path, style finding and NLI score): [b1-dev-examples-run5.md](b1-dev-examples-run5.md).

## Outcome per case

| Case | Outcome | Path | Gemini calls | Content attempts | Hard-gate findings (per attempt) |
|---|---|---|---:|---:|---|
| `postseason-849842` | rejected | rules | 2 | 2 | W1.number / W1.number,W8.form |
| `postseason-849849` | rejected | rules | 2 | 2 | W1.number,W10.cause / W15.outcome,W6.unsaid,W13.standing |
| `opener-824280` | ACCEPTED | primary | 1 | 1 | none |
| `opener-823769` | rejected | rules | 2 | 2 | W17.structure / W1.number,W4.topic,W15.outcome,W2.comparison |
| `limited-823836` | ACCEPTED | primary | 1 | 1 | none |
| `limited-825104` | rejected | rules | 2 | 2 | W6.arsenal / W17.structure |
| `limited-823863` | rejected | rules | 2 | 2 | W1.entity,W8.value,W6.unsaid / W7.missing |
| `veteran-824027` | rejected | rules | 2 | 2 | W0.sentence,W12.time / W1.entity |
| `veteran-823938` | ACCEPTED | primary | 2 | 2 | W8.form / none |
| `veteran-824803` | ACCEPTED | primary_retry | 3 | 2 | W1.number,W8.form,W1.entity,W7.missing,W13.series / none |

## Totals

- Accepted: **4/10** (`opener-824280` via primary, `limited-823836` via primary, `veteran-823938` via primary, `veteran-824803` via primary_retry)
- Style (S1 detector) instances across all attempts: `S-1` 4; `S-2` 11; `S-4` 18; `S-5` 4; `S-7` 3; `W11.expansion` 22; `W11.repeat` 3; `W12.scope` 8; `W14.starter` 1; `W14.team` 2; `W17.length` 13. S-3, S-6 and S-9 have no assessment here. S1 style findings are scored, never a rejection by themselves (D52).
- NLI (score only, local CPU): 275 scored sentences; 154 at least 0.9, 181 at least 0.5, median 0.948. These are unlabelled scores, not accuracy.
- Verdicts on the hard-gate findings (one per check per attempt, all attempts including accepted cases' earlier ones): real model error 18; harness rigidity 6; known limitation 4.

**Reading the verdicts.** 'Real model error': the model broke a guide rule or said something unsupported, even when the fact is true. 'Harness rigidity': the sentence is fine for a fan and consistent with the packet, and the check is stricter than the guide needs. 'Known limitation': a documented gap of the lexical gates or a D62 trade-off. These are my judgments, not owner labels.

## postseason-849842

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.number'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.number | 2 | Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series | real model error | headline says Game 2 but cites only the series name; game_number is cited in another sentence, so the fact is true but this sentence is not bound to it |

S1/style findings of this attempt (2; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | put-away pitch | Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch. |
| W17.length | 1355 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.number', 'W8.form'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.number | two | Kevin Gausman faces Nick Pivetta in game two of the NL Wild Card Series | harness rigidity | &#x27;game two&#x27; spelled out; cites series.game_number = 2 correctly. The number word is not mapped to the digit |
| W8.form | None | Pivetta moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin with his curveball. | real model error | movement clause is followed by &#x27;with his curveball/splitter&#x27;, so it is not at the start or end as W8 requires; numbers and directions are right |
| W8.form | None | Gausman moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin with his splitter. | real model error | movement clause is followed by &#x27;with his curveball/splitter&#x27;, so it is not at the start or end as W8 requires; numbers and directions are right |

S1/style findings of this attempt (2; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-2 | That group | That group draws walks at a 10.6% BB%. |
| W17.length | 1533 | (whole report) |

### Rules text beside rejected model text

Model text shown: content attempt 1 (fewest failed gates, later on a tie). Lengths: rules 2279, model 1363 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Splitter starter against Four-seam-Curveball starter | Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series |
| Short summary | - Kevin Gausman brings this strength: Solid command supports strike-zone control.<br>- Nick Pivetta brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Kevin Gausman can land the splitter early in counts. | - This is Game 2 of the NL Wild Card Series.<br>- Before first pitch, SD leads 1-0.<br>- Both starters enter the game with distinct pitching profiles. |
| Matchup Summary | This matchup features Four-seam-Splitter starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 2 of the NL Wild Card Series. Before first pitch, SD leads 1-0. | This report covers the 2026 regular season through Sep 29. |
| Kevin Gausman vs San Diego Padres | Kevin Gausman works off a four-seam-splitter combination. He shows average swing-and-miss ability. He shows solid command. Kevin Gausman has allowed 26 home runs over 750 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.722 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Kevin Gausman needs efficient strikes. | Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning). He shows solid command. The San Diego Padres lineup draws walks at a 9.4% BB% (walk rate). |
| Nick Pivetta vs Chicago Cubs | Nick Pivetta works off a four-seam-curveball combination. He shows above-average swing-and-miss ability. Control data for Nick Pivetta is limited (140 batters faced; 170 needed), so no command claim is made. Nick Pivetta has allowed 2 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.757 OPS), so Nick Pivetta cannot live over the middle. They draw walks at an above-average rate, so Nick Pivetta needs efficient strikes. | Nick Pivetta has a 2.86 ERA and a 1.01 WHIP. He shows above-average swing-and-miss ability. The Chicago Cubs lineup has a .757 OPS (on-base plus slugging) against right-handed pitchers. This lineup has a 21.2% K% (strikeout rate) and a 10.6% BB%. |
| Arsenal Scout | The main contrast is Four-seam to set up, Splitter to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch. His Four-seam moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. Pivetta uses a Four-seam as his primary pitch and a Curveball as his put-away pitch. His Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Kevin Gausman land the splitter early in counts?<br>- Can Nick Pivetta keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Gausman uses his Splitter to finish plate appearances.<br>- Watch whether Pivetta relies on his Curveball in counts against the Chicago Cubs.<br>- Watch if the Padres lineup generates walks against Gausman. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Kevin Gausman and Nick Pivetta: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them. | Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. |

### NLI scores of the shown model attempt (score only; 20 sentence records)

| Score | Sentence |
|---:|---|
| 0.0002 | Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series |
| 0.9891 | This is Game 2 of the NL Wild Card Series. |
| 0.9905 | Before first pitch, SD leads 1-0. |
| 0.0136 | Both starters enter the game with distinct pitching profiles. |
| 0.9951 | This report covers the 2026 regular season through Sep 29. |
| 0.9970 | Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning). |
| 0.9857 | He shows solid command. |
| 0.9395 | The San Diego Padres lineup draws walks at a 9.4% BB% (walk rate). |
| 0.0013 | Nick Pivetta has a 2.86 ERA and a 1.01 WHIP. |
| 0.9834 | He shows above-average swing-and-miss ability. |
| 0.9888 | The Chicago Cubs lineup has a .757 OPS (on-base plus slugging) against right-handed pitchers. |
| 0.9558 | This lineup has a 21.2% K% (strikeout rate) and a 10.6% BB%. |
| 0.0061 | Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch. |
| 0.9539 | His Four-seam moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. |
| 0.0015 | Pivetta uses a Four-seam as his primary pitch and a Curveball as his put-away pitch. |
| 0.9631 | His Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin. |
| not_applicable | Watch how often Gausman uses his Splitter to finish plate appearances. |
| not_applicable | Watch whether Pivetta relies on his Curveball in counts against the Chicago Cubs. |
| not_applicable | Watch if the Padres lineup generates walks against Gausman. |
| 0.9664 | Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. |

## postseason-849849

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.number', 'W10.cause'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.number | 1 | Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28. | real model error | &#x27;Game 1&#x27; not bound to a cited series.game_number (cited in another sentence); true but uncited here |
| W10.cause | due to | Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command. | known limitation | the cited finding says below-average command &#x27;can create deep-count traffic&#x27;; the model hardens it to &#x27;encounters ... due to&#x27;. The cause is in the packet, the wording is stronger; borderline, lexical cause matching |

S1/style findings of this attempt (2; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-1 | 2026 regular season | Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28. |
| S-4 | utilizes | Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch. |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W15.outcome', 'W6.unsaid', 'W13.standing'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W15.outcome | strikeouts | Watch how often Hagen Smith uses his slider to get strikeouts | harness rigidity | &#x27;how often he uses his slider to get strikeouts&#x27; names no predicted outcome; it cites the season strikeout count. Lexical match on &#x27;strikeouts&#x27; |
| W6.unsaid | None | (whole report) | real model error | limited-data starter is never described as limited in a sentence naming him |
| W13.standing | None | (whole report) | real model error | the required series standing statement is missing |

S1/style findings of this attempt (7; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | ERA | Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning) |
| W11.expansion | WHIP | Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning) |
| W11.expansion | OPS | The Houston Astros lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers |
| W11.expansion | K% | That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) |
| W11.expansion | BB% | That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) |
| S-2 | This group | This group has a 24.1% K% and a 9.4% BB% |
| W17.length | 1711 | (whole report) |

### Rules text beside rejected model text

Model text shown: content attempt 1 (fewest failed gates, later on a tie). Lengths: rules 2221, model 1922 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Slider starter against Four-seam-Sweeper starter | Hagen Smith and the Chicago White Sox face AJ Blubaugh and the Houston Astros in the AL Wild Card Series. |
| Short summary | - Hagen Smith brings this strength: Above-average swing-and-miss ability.<br>- AJ Blubaugh brings this strength: Four-seam to set up, Sweeper to finish.<br>- The early what to watch is whether Hagen Smith can land the slider early in counts. | - This is Game 1 of the AL Wild Card Series.<br>- Hagen Smith starts for the Chicago White Sox.<br>- AJ Blubaugh starts for the Houston Astros. |
| Matchup Summary | This matchup features Four-seam-Slider starter against Four-seam-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 1 of the AL Wild Card Series; the series has not started. | Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28. |
| Hagen Smith vs Houston Astros | Hagen Smith works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Hagen Smith is limited (110 batters faced; 170 needed), so no command claim is made. Hagen Smith has allowed 1 home run over 110 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.713 OPS), with no glaring weakness to attack. | Hagen Smith enters with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning). He shows above-average swing-and-miss ability. Control data for Hagen Smith is limited with 110 batters faced, where 170 are needed. The Houston Astros lineup against left-handed pitchers carries a .713 OPS (on-base plus slugging), a 21.0% K% (strikeout rate), and a 7.9% BB% (walk rate). |
| AJ Blubaugh vs Chicago White Sox | AJ Blubaugh works off a four-seam-sweeper combination. He shows average swing-and-miss ability. He shows below-average command. AJ Blubaugh has allowed 13 home runs over 401 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.716 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so AJ Blubaugh needs efficient strikes. | AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP. He has below-average command. The Chicago White Sox lineup against right-handed pitchers shows a .716 OPS, a 24.1% K%, and a 9.4% BB%. That group draws walks at an above-average rate and carries an elevated swing-and-miss risk. |
| Arsenal Scout | The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch. His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin. His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin. AJ Blubaugh relies on his four-seam fastball as his primary pitch and a sweeper as his second most used pitch. His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin. His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Hagen Smith land the slider early in counts?<br>- Can AJ Blubaugh keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Hagen Smith uses his slider to finish.<br>- Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command.<br>- Watch how the lineups handle the different secondary offerings of each pitcher. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Hagen Smith and AJ Blubaugh: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them. | Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28. |

### NLI scores of the shown model attempt (score only; 23 sentence records)

| Score | Sentence |
|---:|---|
| 0.7541 | Hagen Smith and the Chicago White Sox face AJ Blubaugh and the Houston Astros in the AL Wild Card Series. |
| 0.9906 | This is Game 1 of the AL Wild Card Series. |
| unrenderable | Hagen Smith starts for the Chicago White Sox. |
| unrenderable | AJ Blubaugh starts for the Houston Astros. |
| 0.0003 | Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28. |
| 0.9646 | Hagen Smith enters with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning). |
| 0.9846 | He shows above-average swing-and-miss ability. |
| 0.1155 | Control data for Hagen Smith is limited with 110 batters faced, where 170 are needed. |
| 0.9889 | The Houston Astros lineup against left-handed pitchers carries a .713 OPS (on-base plus slugging), a 21.0% K% (strikeout rate), and a 7.9% BB% (walk rate). |
| 0.0032 | AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP. |
| 0.9919 | He has below-average command. |
| 0.9887 | The Chicago White Sox lineup against right-handed pitchers shows a .716 OPS, a 24.1% K%, and a 9.4% BB%. |
| 0.9976 | That group draws walks at an above-average rate and carries an elevated swing-and-miss risk. |
| 0.9568 | Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch. |
| 0.0345 | His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin. |
| 0.9010 | His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin. |
| 0.0524 | AJ Blubaugh relies on his four-seam fastball as his primary pitch and a sweeper as his second most used pitch. |
| 0.0398 | His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin. |
| 0.9548 | His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch how often Hagen Smith uses his slider to finish. |
| not_applicable | Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command. |
| not_applicable | Watch how the lineups handle the different secondary offerings of each pitcher. |
| 0.0028 | Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28. |

## opener-824280

**ACCEPTED**, path `primary`, Gemini calls 1, content attempts 1.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates none.

S1/style findings of this attempt (7; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-4 | features | This game features right-handed starters Trey Yesavage and Brenan Hanifee. |
| S-4 | maintain | They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split. |
| S-7 | in this split | They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split. |
| S-7 | in this split | That unit has an 18.2% K% and a 7.3% BB% in this split. |
| S-4 | maintains | Watch whether the Tigers lineup maintains its walk rate against Yesavage. |
| S-5 | matchup | Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup |
| W17.length | 1564 | (whole report) |

### Rules text beside accepted model text

Model text shown: content attempt 1. Lengths: rules 2330, model 1572 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Splitter starter against Sinker-Slider starter | Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup |
| Short summary | - Trey Yesavage brings this strength: Four-seam to set up, Splitter to finish.<br>- Brenan Hanifee brings this strength: Sinker to set up, Slider to finish.<br>- The early what to watch is whether Trey Yesavage can land the splitter early in counts. | - Trey Yesavage has an 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning).<br>- Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.<br>- Data covers the 2026 regular season through May 14. |
| Matchup Summary | This matchup features Four-seam-Splitter starter against Sinker-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | This game features right-handed starters Trey Yesavage and Brenan Hanifee. |
| Trey Yesavage vs Detroit Tigers | Trey Yesavage works off a four-seam-splitter combination. Strikeout data for Trey Yesavage is limited (57 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Trey Yesavage is limited (57 batters faced; 170 needed), so no command claim is made. Trey Yesavage has allowed 0 home runs over 57 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.725 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Trey Yesavage needs efficient strikes. | Trey Yesavage has a limited sample of 57 batters faced, while 170 are needed for a command read and 70 for a strikeout read. The Tigers lineup has a .725 OPS (on-base plus slugging) against right-handed pitchers. They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split. The group draws walks at an above-average rate. |
| Brenan Hanifee vs Toronto Blue Jays | Brenan Hanifee works off a sinker-slider combination. Strikeout data for Brenan Hanifee is limited (33 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Brenan Hanifee is limited (33 batters faced; 170 needed), so no command claim is made. Brenan Hanifee has allowed 1 home run over 33 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.701 OPS), with no glaring weakness to attack. | Brenan Hanifee has a limited sample of 33 batters faced, while 170 are needed for a command read and 70 for a strikeout read. The Blue Jays offense has a .701 OPS against right-handed pitchers. That unit has an 18.2% K% and a 7.3% BB% in this split. |
| Arsenal Scout | The main contrast is Four-seam to set up, Splitter to finish versus Sinker to set up, Slider to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point. | Trey Yesavage uses a Four-seam as his primary pitch and a Splitter as his put-away pitch (second most used pitch). His Four-seam moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. Brenan Hanifee relies on his Sinker as his primary pitch and his Slider as his put-away pitch. His Sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Trey Yesavage land the splitter early in counts?<br>- Can Brenan Hanifee keep the ball low?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Yesavage throws his Splitter to finish plate appearances.<br>- Watch whether the Tigers lineup maintains its walk rate against Yesavage.<br>- Watch if the Blue Jays can contact Hanifee&#x27;s Sinker. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Trey Yesavage and Brenan Hanifee: all pitcher figures cover the 2026 regular season through May 14. Team offense splits cover the 2026 regular season through May 14. Samples below the minimum are flagged as limited and no claim is made from them. | Probable pitchers are listed for this matchup. |

### NLI scores of the shown model attempt (score only; 20 sentence records)

| Score | Sentence |
|---:|---|
| 0.0240 | Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup |
| 0.9899 | Trey Yesavage has an 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning). |
| 0.0014 | Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP. |
| 0.9300 | Data covers the 2026 regular season through May 14. |
| 0.9877 | This game features right-handed starters Trey Yesavage and Brenan Hanifee. |
| 0.1752 | Trey Yesavage has a limited sample of 57 batters faced, while 170 are needed for a command read and 70 for a strikeout read. |
| 0.9823 | The Tigers lineup has a .725 OPS (on-base plus slugging) against right-handed pitchers. |
| 0.2973 | They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split. |
| 0.9943 | The group draws walks at an above-average rate. |
| 0.3771 | Brenan Hanifee has a limited sample of 33 batters faced, while 170 are needed for a command read and 70 for a strikeout read. |
| 0.9866 | The Blue Jays offense has a .701 OPS against right-handed pitchers. |
| 0.9661 | That unit has an 18.2% K% and a 7.3% BB% in this split. |
| 0.9868 | Trey Yesavage uses a Four-seam as his primary pitch and a Splitter as his put-away pitch (second most used pitch). |
| 0.7137 | His Four-seam moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. |
| 0.0021 | Brenan Hanifee relies on his Sinker as his primary pitch and his Slider as his put-away pitch. |
| 0.8656 | His Sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch how often Yesavage throws his Splitter to finish plate appearances. |
| not_applicable | Watch whether the Tigers lineup maintains its walk rate against Yesavage. |
| not_applicable | Watch if the Blue Jays can contact Hanifee&#x27;s Sinker. |
| 0.1118 | Probable pitchers are listed for this matchup. |

## opener-823769

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W17.structure'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W17.structure | None | (whole report) | real model error | output not the required JSON shape; no sentence was evaluated |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.number', 'W4.topic', 'W15.outcome', 'W2.comparison'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.number | two | This duel at American Family Field features two starters with contrasting pitch preferences. | known limitation | &#x27;two starters&#x27; is a trivially true count written as a word with no cited number; spelled counts cannot be bound |
| W4.topic | Family | This duel at American Family Field features two starters with contrasting pitch preferences. | harness rigidity | token &#x27;Family&#x27; comes from the cited venue name &#x27;American Family Field&#x27; and is read as a forbidden topic word |
| W15.outcome | strikeout | Watch whether Ryan Rolison uses his slider often in strikeout counts. | harness rigidity | &#x27;uses his slider often in strikeout counts&#x27; describes a pitch-count situation, not a game outcome; lexical match on &#x27;strikeout&#x27; |
| W2.comparison | below | Control data for both Ryan Rolison and Brandon Woodruff is limited, as both are below the 170 batters faced threshold. | known limitation | &#x27;below the 170 batters faced threshold&#x27; is true and cited, but D62 forbids all comparison wording; accepted trade-off of the code gate |

S1/style findings of this attempt (12; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | ERA | Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27. |
| W11.expansion | WHIP | Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27. |
| W11.expansion | OPS | Ryan Rolison faces a Milwaukee lineup that has a .682 OPS (on-base plus slugging) against left-handed pitchers. |
| W11.expansion | K% | The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate). |
| W11.expansion | BB% | The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate). |
| S-7 | over the same period | Brandon Woodruff carries a 3.00 ERA and a 0.89 WHIP over the same period. |
| S-4 | feature | Both starters feature above-average swing-and-miss ability. |
| S-4 | features | This duel at American Family Field features two starters with contrasting pitch preferences. |
| S-4 | maintain | Watch if the Cubs hitters maintain their plate discipline against the Milwaukee starter. |
| S-2 | This team | This team also draws walks at an above-average rate. |
| W12.scope | None | (whole report) |
| W17.length | 1462 | (whole report) |

### Rules text beside rejected model text

Model text shown: content attempt 1 (fewest failed gates, later on a tie). Lengths: rules 2325, model 1574 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Slider starter against Four-seam-Changeup starter | Ryan Rolison faces Brandon Woodruff at American Family Field |
| Short summary | - Ryan Rolison brings this strength: Above-average swing-and-miss ability.<br>- Brandon Woodruff brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Ryan Rolison can land the slider early in counts. | - Ryan Rolison and Brandon Woodruff lead their teams as probable pitchers for this game.<br>- Rolison for the Chicago Cubs carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) over the 2026 regular season through 2026-06-27.<br>- Woodruff for the Milwaukee Brewers has a 3.00 ERA and a 0.89 WHIP over the same period. |
| Matchup Summary | This matchup features Four-seam-Slider starter against Four-seam-Changeup starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | This matchup features two pitchers with above-average swing-and-miss ability. |
| Ryan Rolison vs Milwaukee Brewers | Ryan Rolison works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Ryan Rolison is limited (114 batters faced; 170 needed), so no command claim is made. Ryan Rolison has allowed 3 home runs over 114 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.682 OPS), which gives Ryan Rolison an edge if he gets ahead. They draw walks at an above-average rate, so Ryan Rolison needs efficient strikes. | The Brewers lineup facing left-handed pitchers like Rolison maintains a .682 OPS (on-base plus slugging), a 21.8% K% (strikeout rate), and a 10.3% BB% (walk rate) through 2026-06-27. This group draws walks at an above-average rate. |
| Brandon Woodruff vs Chicago Cubs | Brandon Woodruff works off a four-seam-changeup combination. He shows above-average swing-and-miss ability. Control data for Brandon Woodruff is limited (140 batters faced; 170 needed), so no command claim is made. Brandon Woodruff has allowed 4 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Brandon Woodruff needs efficient strikes. | The Cubs lineup facing right-handed pitchers like Woodruff shows a .734 OPS, a 21.2% K%, and an 11.4% BB% through 2026-06-27. The Cubs lineup also draws walks at an above-average rate. |
| Arsenal Scout | The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Changeup to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Rolison uses a Four-seam as his primary pitch and a Slider as his put-away pitch (second most used pitch). His Four-seam moves 2.0 in. sideways and 15.1 in. up compared with a pitch thrown without spin. Woodruff relies on his Four-seam as his primary pitch and his Changeup as his put-away pitch. His Four-seam moves 4.6 in. sideways and 18.1 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Ryan Rolison land the slider early in counts?<br>- Can Brandon Woodruff keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Rolison uses his slider to close out plate appearances.<br>- Watch whether Woodruff utilizes his changeup to challenge opposing hitters.<br>- Watch how both teams manage plate discipline given their tendencies to draw walks. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Ryan Rolison and Brandon Woodruff: all pitcher figures cover the 2026 regular season through Jun 27. Team offense splits cover the 2026 regular season through Jun 27. Samples below the minimum are flagged as limited and no claim is made from them. | Control data for both Ryan Rolison and Brandon Woodruff is limited. |

### NLI scores of the shown model attempt (score only; 0 sentence records)

| Score | Sentence |
|---:|---|

## limited-823836

**ACCEPTED**, path `primary`, Gemini calls 1, content attempts 1.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates none.

S1/style findings of this attempt (11; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | ERA | Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6. |
| W11.expansion | WHIP | Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6. |
| W11.expansion | OPS | The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. |
| W11.repeat | OPS | The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. |
| W11.expansion | K% | That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate). |
| W11.repeat | K% | This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). |
| W11.expansion | BB% | That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate). |
| W11.repeat | BB% | This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). |
| S-1 | 2026 regular season through Aug 6 | The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. |
| S-4 | features | This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park. |
| S-2 | This group | This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). |

### Rules text beside accepted model text

Model text shown: content attempt 1. Lengths: rules 2196, model 1809 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Changeup starter against Sinker-Sweeper starter | George Klassen and Tyler Phillips prepare for a matchup at loanDepot park. |
| Short summary | - George Klassen brings this strength: Four-seam to set up, Changeup to finish.<br>- Tyler Phillips brings this strength: Sinker to set up, Sweeper to finish.<br>- The early what to watch is whether George Klassen can land the changeup early in counts. | - This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.<br>- Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.<br>- Phillips holds a 3.53 ERA and a 1.35 WHIP for the same period. |
| Matchup Summary | This matchup features Four-seam-Changeup starter against Sinker-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park. |
| George Klassen vs Miami Marlins | George Klassen works off a four-seam-changeup combination. Strikeout data for George Klassen is limited (32 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for George Klassen is limited (32 batters faced; 170 needed), so no command claim is made. George Klassen has allowed 1 home run over 32 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. | The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate). The team has an elevated swing-and-miss risk. |
| Tyler Phillips vs Los Angeles Angels | Tyler Phillips works off a sinker-sweeper combination. He shows below-average swing-and-miss ability. He shows average command. Tyler Phillips has allowed 11 home runs over 383 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.687 OPS), which gives Tyler Phillips an edge if he gets ahead. They also strike out often, which favors a swing-and-miss approach. | The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). There is limited data for George Klassen: 32 batters faced, while 170 are needed for a command read. There is not enough data to rate his command or swing-and-miss ability. |
| Arsenal Scout | The main contrast is Four-seam to set up, Changeup to finish versus Sinker to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point. | George Klassen is a Four-seam-Changeup starter who uses his four-seam fastball to set up and his changeup to finish. His four-seam fastball moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. Tyler Phillips is a Sinker-Sweeper starter who uses his sinker to set up and his sweeper to finish. His sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can George Klassen land the changeup early in counts?<br>- Can Tyler Phillips keep the ball low?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often George Klassen uses his four-seam fastball early in the count.<br>- Watch if Tyler Phillips throws his sweeper to get hitters out.<br>- Watch how the Angels lineup manages the swing-and-miss risk against the right-handed starter. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. George Klassen and Tyler Phillips: all pitcher figures cover the 2026 regular season through Aug 6. Team offense splits cover the 2026 regular season through Aug 6. Samples below the minimum are flagged as limited and no claim is made from them. | Probable pitchers are listed for this game. |

### NLI scores of the shown model attempt (score only; 20 sentence records)

| Score | Sentence |
|---:|---|
| 0.0029 | George Klassen and Tyler Phillips prepare for a matchup at loanDepot park. |
| 0.0006 | This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park. |
| 0.9232 | Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6. |
| 0.0085 | Phillips holds a 3.53 ERA and a 1.35 WHIP for the same period. |
| 0.0006 | This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park. |
| 0.9883 | The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. |
| 0.9938 | That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate). |
| 0.9928 | The team has an elevated swing-and-miss risk. |
| 0.9901 | The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. |
| 0.9953 | This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). |
| 0.9757 | There is limited data for George Klassen: 32 batters faced, while 170 are needed for a command read. |
| 0.0031 | There is not enough data to rate his command or swing-and-miss ability. |
| 0.0202 | George Klassen is a Four-seam-Changeup starter who uses his four-seam fastball to set up and his changeup to finish. |
| 0.0214 | His four-seam fastball moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. |
| 0.0410 | Tyler Phillips is a Sinker-Sweeper starter who uses his sinker to set up and his sweeper to finish. |
| 0.2343 | His sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch how often George Klassen uses his four-seam fastball early in the count. |
| not_applicable | Watch if Tyler Phillips throws his sweeper to get hitters out. |
| not_applicable | Watch how the Angels lineup manages the swing-and-miss risk against the right-handed starter. |
| 0.7300 | Probable pitchers are listed for this game. |

## limited-825104

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W6.arsenal'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W6.arsenal | None | (whole report) | real model error | describes pitches of a starter whose arsenal is limited |

S1/style findings of this attempt (4; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-2 | That group | That group has a 19.4% K% and a 9.5% BB%. |
| W14.team | None | (whole report) |
| W12.scope | None | (whole report) |
| W17.length | 1519 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W17.structure'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W17.structure | None | (whole report) | real model error | output not the required JSON shape |

### Rules text beside rejected model text

Model text shown: content attempt 2 (fewest failed gates, later on a tie). Lengths: rules 2494, model 1465 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Bryce Elder against Michael Soroka | Bryce Elder and Michael Soroka match up at Chase Field |
| Short summary | - Bryce Elder has no claimed strength because the data is limited.<br>- Michael Soroka has no claimed strength because the data is limited.<br>- The early what to watch is whether Bryce Elder can stay ahead of hitters early in counts. | - Bryce Elder and Michael Soroka start the game for their respective teams.<br>- Both starters enter the matchup with limited sample sizes in the 2026 regular season through 2026-04-03.<br>- The Atlanta Braves and Arizona Diamondbacks lineups prepare to face right-handed pitching.<br>- This is a matchup of starting pitchers. |
| Matchup Summary | This matchup features Bryce Elder against Michael Soroka. The scouting note is matchup fit, with each pressure point shaping what to watch. | Bryce Elder of the Braves and Michael Soroka of the Diamondbacks face off on April 4, 2026. |
| Bryce Elder vs Arizona Diamondbacks | Bryce Elder&#x27;s arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Bryce Elder is limited (23 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Bryce Elder is limited (23 batters faced; 170 needed), so no command claim is made. Bryce Elder has allowed 0 home runs over 23 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.653 OPS), which gives Bryce Elder an edge if he gets ahead. | Bryce Elder carries a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning) in the 2026 regular season through 2026-04-03. The Arizona lineup holds a .653 OPS (on-base plus slugging) against right-handed pitchers, with a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate). |
| Michael Soroka vs Atlanta Braves | Michael Soroka&#x27;s arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Michael Soroka is limited (20 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Michael Soroka is limited (20 batters faced; 170 needed), so no command claim is made. Michael Soroka has allowed 0 home runs over 20 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.827 OPS), so Michael Soroka cannot live over the middle. They draw walks at an above-average rate, so Michael Soroka needs efficient strikes. | Michael Soroka shows a 0.00 ERA and a 1.00 WHIP over his limited sample of games in the same period. The Atlanta offense produces a .827 OPS, a 19.4% K% and a 9.5% BB% against right-handed pitchers. |
| Arsenal Scout | Bryce Elder&#x27;s arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Michael Soroka&#x27;s arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. No arsenal contrast is drawn because at least one arsenal has too little data. | Bryce Elder uses a sinker as his primary pitch and a slider as his put-away pitch, but his arsenal data is limited. Michael Soroka relies on a slurve as his primary pitch and a four-seam fastball as his put-away pitch, with limited arsenal data. |
| Three Things to Watch | - Can Bryce Elder stay ahead of hitters early in counts?<br>- Can Michael Soroka work efficiently through the lineup?<br>- Which lineup forces more deep counts by the third inning? | - Watch whether Bryce Elder uses his sinker to set up hitters early in counts.<br>- Watch how Michael Soroka mixes his slurve and four-seam fastball throughout the contest.<br>- Watch if the Atlanta lineup sustains its OPS against right-handed pitchers. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Bryce Elder and Michael Soroka: all pitcher figures cover the 2026 regular season through Apr 3. Team offense splits cover the 2026 regular season through Apr 3. Samples below the minimum are flagged as limited and no claim is made from them. | The game features probable pitchers. |

### NLI scores of the shown model attempt (score only; 0 sentence records)

| Score | Sentence |
|---:|---|

## limited-823863

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.entity', 'W8.value', 'W6.unsaid'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.entity | Eury Perez | Tobias Myers and Eury Perez start at loanDepot park | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W1.entity | Eury Perez | Eury Perez takes the mound for the Marlins against the visiting New York Mets. | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W1.entity | Eury Perez | Tobias Myers and Eury Perez each start this game on 2026-05-22. | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W1.entity | Eury Perez | Eury Perez has a 5.33 ERA and a 1.41 WHIP. | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W8.value | None | His splitter moves 9.6 in. sideways and 8.4 in. down compared with a pitch thrown without spin. | harness rigidity | writes &#x27;9.6 in. sideways&#x27; for h_break -9.6 (magnitude, no sign); the W8 template carries the signed value, so this is stricter than the facts require |
| W1.entity | Eury Perez | Eury Perez uses a four-seam fastball 49.3% of the time and a slider 15.0% of the time. | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W1.entity | Eury Perez | Watch if Eury Perez can control his slider with his below-average command. | real model error | name written &#x27;Eury Perez&#x27;; the packet name is &#x27;Eury Pérez&#x27;. The guide requires accents; no wrong person is named |
| W6.unsaid | None | (whole report) | real model error | limited-data starter not said to be limited |

S1/style findings of this attempt (5; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-2 | That lineup | That lineup has a 20.7% K% and an 8.1% BB%. |
| S-5 | Perez | Tobias Myers and Eury Perez start at loanDepot park |
| W14.starter | None | (whole report) |
| W12.scope | None | (whole report) |
| W17.length | 1517 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W7.missing'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W7.missing | starters.away_starter.pitching_profile.command_label | Watch whether Tobias Myers can maintain his command throughout the game. | real model error | talks about Myers&#x27; command although his command label is null (limited sample); the claim has no supporting label |

S1/style findings of this attempt (9; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | ERA | Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning). |
| W11.expansion | WHIP | Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning). |
| W11.expansion | OPS | The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers. |
| W11.expansion | K% | That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate). |
| W11.expansion | BB% | That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate). |
| S-4 | maintain | Watch whether Tobias Myers can maintain his command throughout the game. |
| W14.team | None | (whole report) |
| W12.scope | None | (whole report) |
| W17.length | 1607 | (whole report) |

### Rules text beside rejected model text

Model text shown: content attempt 2 (fewest failed gates, later on a tie). Lengths: rules 2060, model 1619 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Splitter starter against Four-seam-Slider starter | Tobias Myers faces Eury Pérez in Miami |
| Short summary | - Tobias Myers brings this strength: Four-seam to set up, Splitter to finish.<br>- Eury Pérez brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Tobias Myers can land the splitter early in counts. | - Tobias Myers and Eury Pérez pitch at loanDepot park.<br>- The starters bring distinct styles to the mound.<br>- Both lineups prepare for right-handed starters. |
| Matchup Summary | This matchup features Four-seam-Splitter starter against Four-seam-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | These figures cover the 2026 regular season through 2026-05-21. |
| Tobias Myers vs Miami Marlins | Tobias Myers works off a four-seam-splitter combination. He shows average swing-and-miss ability. Control data for Tobias Myers is limited (115 batters faced; 170 needed), so no command claim is made. Tobias Myers has allowed 5 home runs over 115 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.697 OPS), which gives Tobias Myers an edge if he gets ahead. | Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning). He shows average swing-and-miss ability. Control data for Myers is limited: 115 batters faced, and 170 are needed for a full reading. The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers. That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate). |
| Eury Pérez vs New York Mets | Eury Pérez works off a four-seam-slider combination. He shows above-average swing-and-miss ability. He shows below-average command. Eury Pérez has allowed 10 home runs over 230 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.659 OPS), which gives Eury Pérez an edge if he gets ahead. | Eury Pérez has a 5.33 ERA and 1.41 WHIP. He shows above-average swing-and-miss ability and below-average command. The New York lineup has a .659 OPS against right-handed pitchers. Those hitters have a 20.7% K% and an 8.1% BB%. |
| Arsenal Scout | The main contrast is Four-seam to set up, Splitter to finish versus Four-seam to set up, Slider to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Myers uses his Four-seam fastball 50.1% of the time. It moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin. His Splitter moves 9.6 in. sideways and 8.4 in. up compared with a pitch thrown without spin. Pérez uses a Four-seam fastball 49.3% of the time. It moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin. His Slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Tobias Myers land the splitter early in counts?<br>- Can Eury Pérez keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch whether Tobias Myers can maintain his command throughout the game.<br>- Watch how often Eury Pérez throws his Four-seam fastball to set up hitters.<br>- Watch if the New York lineup capitalizes on deep-count traffic created by Eury Pérez. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Tobias Myers and Eury Pérez: all pitcher figures cover the 2026 regular season through May 21. Team offense splits cover the 2026 regular season through May 21. Samples below the minimum are flagged as limited and no claim is made from them. | This report uses probable pitchers for the game on 2026-05-22. |

### NLI scores of the shown model attempt (score only; 24 sentence records)

| Score | Sentence |
|---:|---|
| 0.0051 | Tobias Myers faces Eury Pérez in Miami |
| 0.3034 | Tobias Myers and Eury Pérez pitch at loanDepot park. |
| 0.0091 | The starters bring distinct styles to the mound. |
| 0.0780 | Both lineups prepare for right-handed starters. |
| 0.0080 | These figures cover the 2026 regular season through 2026-05-21. |
| 0.0026 | Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning). |
| 0.9901 | He shows average swing-and-miss ability. |
| 0.9262 | Control data for Myers is limited: 115 batters faced, and 170 are needed for a full reading. |
| 0.9839 | The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers. |
| 0.9928 | That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate). |
| 0.0013 | Eury Pérez has a 5.33 ERA and 1.41 WHIP. |
| 0.8891 | He shows above-average swing-and-miss ability and below-average command. |
| 0.9889 | The New York lineup has a .659 OPS against right-handed pitchers. |
| 0.9721 | Those hitters have a 20.7% K% and an 8.1% BB%. |
| 0.7827 | Myers uses his Four-seam fastball 50.1% of the time. |
| 0.9678 | It moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin. |
| 0.7008 | His Splitter moves 9.6 in. sideways and 8.4 in. up compared with a pitch thrown without spin. |
| 0.0172 | Pérez uses a Four-seam fastball 49.3% of the time. |
| 0.9503 | It moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin. |
| 0.8688 | His Slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch whether Tobias Myers can maintain his command throughout the game. |
| not_applicable | Watch how often Eury Pérez throws his Four-seam fastball to set up hitters. |
| not_applicable | Watch if the New York lineup capitalizes on deep-count traffic created by Eury Pérez. |
| 0.9920 | This report uses probable pitchers for the game on 2026-05-22. |

## veteran-824027

**REJECTED**, path `rules`, Gemini calls 2, content attempts 2, reason `checks_failed`.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W0.sentence', 'W12.time'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W0.sentence | None | Kyle Freeland and Jos&amp;eacute; Soriano take the mound for a starting pitching matchup on June 1. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W0.sentence | None | Kyle Freeland and Jos&amp;eacute; Soriano bring distinct pitching profiles to the 2026 regular season through May 31. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W0.sentence | None | Kyle Freeland and Jos&amp;eacute; Soriano lead their respective staffs into the matchup on June 1. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W0.sentence | None | Jos&amp;eacute; Soriano has a 2.65 ERA and a 1.15 WHIP. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W0.sentence | None | Jos&amp;eacute; Soriano uses a Sinker to set up and a Curveball to finish. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W0.sentence | None | Watch whether Jos&amp;eacute; Soriano can manage his command with the Sinker. | real model error | model emitted an HTML entity (&#x27;Jos&amp;eacute;&#x27;) instead of the accented letter; the security gate is correct |
| W12.time | Pitching and usage data for both starters is available through the 2026 regular season through May 31. | Pitching and usage data for both starters is available through the 2026 regular season through May 31. | real model error | &#x27;available through the 2026 regular season through May 31&#x27; misuses the scope label as a time claim |

S1/style findings of this attempt (4; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-1 | 2026 regular season through May 31 | Pitching and usage data for both starters is available through the 2026 regular season through May 31. |
| S-5 | Jos | Kyle Freeland and Jos&amp;eacute; Soriano take the mound for a starting pitching matchup on June 1. |
| S-5 | June | Kyle Freeland and Jos&amp;eacute; Soriano take the mound for a starting pitching matchup on June 1. |
| W17.length | 1566 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.entity'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.entity | June | Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026. | harness rigidity | &#x27;June 1, 2026&#x27; is written from the cited date 2026-06-01; the month name is read as an uncited entity |
| W1.entity | June | Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026. | harness rigidity | &#x27;June 1, 2026&#x27; is written from the cited date 2026-06-01; the month name is read as an uncited entity |

S1/style findings of this attempt (2; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-1 | 2026 regular season through May 31 | Pitching data for both starters is complete and covers the 2026 regular season through May 31. |
| W17.length | 1631 | (whole report) |

### Rules text beside rejected model text

Model text shown: content attempt 2 (fewest failed gates, later on a tie). Lengths: rules 2048, model 1638 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Curveball starter against Sinker-Curveball starter | Kyle Freeland faces the Los Angeles Angels as José Soriano starts for the home team |
| Short summary | - Kyle Freeland brings this strength: Solid command supports strike-zone control.<br>- José Soriano brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Kyle Freeland can land the curveball early in counts. | - Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026.<br>- Freeland brings an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) to the mound.<br>- Soriano enters with a 2.65 ERA and a 1.15 WHIP, with all stats current for the 2026 regular season through May 31. |
| Matchup Summary | This matchup features Four-seam-Curveball starter against Sinker-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026. |
| Kyle Freeland vs Los Angeles Angels | Kyle Freeland works off a four-seam-curveball combination. He shows average swing-and-miss ability. He shows solid command. Kyle Freeland has allowed 12 home runs over 202 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.712 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Kyle Freeland needs efficient strikes. | The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers. Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4%. The Angels offense has elevated swing-and-miss risk and draws walks at an above-average rate. |
| José Soriano vs Colorado Rockies | José Soriano works off a sinker-curveball combination. He shows above-average swing-and-miss ability. He shows below-average command. José Soriano has allowed 6 home runs over 289 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.709 OPS), with no glaring weakness to attack. | The Rockies offense has a .709 OPS against right-handed pitchers. That group shows a 22.7% K% and an 8.3% BB%. Soriano shows below-average command and above-average swing-and-miss ability. |
| Arsenal Scout | The main contrast is Four-seam to set up, Curveball to finish versus Sinker to set up, Curveball to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point. | Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time. His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin. Soriano uses his sinker 27.8% of the time and his curveball 24.8% of the time. The sinker from Soriano moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Kyle Freeland land the curveball early in counts?<br>- Can José Soriano keep the ball low?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Freeland uses his four-seam fastball to set up his curveball.<br>- Watch if Soriano can manage his command, as below-average command can create deep-count traffic.<br>- Watch how the Angels lineup handles the curveball from Freeland. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Kyle Freeland and José Soriano: all pitcher figures cover the 2026 regular season through May 31. Team offense splits cover the 2026 regular season through May 31. | Pitching data for both starters is complete and covers the 2026 regular season through May 31. |

### NLI scores of the shown model attempt (score only; 19 sentence records)

| Score | Sentence |
|---:|---|
| 0.1500 | Kyle Freeland faces the Los Angeles Angels as José Soriano starts for the home team |
| 0.9335 | Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026. |
| 0.0631 | Freeland brings an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) to the mound. |
| 0.0072 | Soriano enters with a 2.65 ERA and a 1.15 WHIP, with all stats current for the 2026 regular season through May 31. |
| 0.9863 | Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026. |
| 0.9968 | The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers. |
| 0.9881 | Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4%. |
| 0.9200 | The Angels offense has elevated swing-and-miss risk and draws walks at an above-average rate. |
| 0.9944 | The Rockies offense has a .709 OPS against right-handed pitchers. |
| 0.9896 | That group shows a 22.7% K% and an 8.3% BB%. |
| 0.9833 | Soriano shows below-average command and above-average swing-and-miss ability. |
| 0.9708 | Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time. |
| 0.1161 | His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin. |
| 0.9597 | Soriano uses his sinker 27.8% of the time and his curveball 24.8% of the time. |
| 0.9580 | The sinker from Soriano moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch how often Freeland uses his four-seam fastball to set up his curveball. |
| not_applicable | Watch if Soriano can manage his command, as below-average command can create deep-count traffic. |
| not_applicable | Watch how the Angels lineup handles the curveball from Freeland. |
| 0.0024 | Pitching data for both starters is complete and covers the 2026 regular season through May 31. |

## veteran-823938

**ACCEPTED**, path `primary`, Gemini calls 2, content attempts 2.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W8.form'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W8.form | None | He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up. | real model error | movement sentences lack the required &#x27;compared with a pitch thrown without spin&#x27; clause; values are correct |
| W8.form | None | Eric Lauer uses his Four-seam 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up. | real model error | movement sentences lack the required &#x27;compared with a pitch thrown without spin&#x27; clause; values are correct |
| W8.form | None | His Cutter, a put-away pitch, moves 1.8 in. sideways and 8.7 in. up. | real model error | movement sentences lack the required &#x27;compared with a pitch thrown without spin&#x27; clause; values are correct |

S1/style findings of this attempt (5; scored only):

| Check | Token | Sentence |
|---|---|---|
| W11.expansion | put-away pitch | He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up. |
| S-4 | exhibits | He exhibits below-average swing-and-miss ability. |
| S-4 | demonstrates | He demonstrates below-average swing-and-miss ability. |
| W12.scope | None | (whole report) |
| W17.length | 1419 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates none.

S1/style findings of this attempt (5; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-4 | maintains | Watch whether the Dodgers lineup maintains its walk rate against Martinez. |
| S-4 | features | The game features probable pitchers for the scheduled date. |
| S-2 | the | The game features probable pitchers for the scheduled date. |
| S-2 | That group | That group carries a 17.7% K% and an 8.8% BB%. |
| W12.scope | None | (whole report) |

### Rules text beside accepted model text

Model text shown: content attempt 2. Lengths: rules 1970, model 1626 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Sinker-Changeup starter against Four-seam-Cutter starter | Nick Martinez and Eric Lauer start for their teams |
| Short summary | - Nick Martinez brings this strength: Solid command supports strike-zone control.<br>- Eric Lauer brings this strength: Four-seam to set up, Cutter to finish.<br>- The early what to watch is whether Nick Martinez can land the changeup early in counts. | - Nick Martinez leads the Rays against the Dodgers.<br>- The Dodgers counter with Eric Lauer on the mound.<br>- These teams meet at UNIQLO Field at Dodger Stadium. |
| Matchup Summary | This matchup features Sinker-Changeup starter against Four-seam-Cutter starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | Figures in this report cover the 2026 regular season through June 14. |
| Nick Martinez vs Los Angeles Dodgers | Nick Martinez works off a sinker-changeup combination. He shows below-average swing-and-miss ability. He shows solid command. Nick Martinez has allowed 6 home runs over 318 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.806 OPS), so Nick Martinez cannot live over the middle. They draw walks at an above-average rate, so Nick Martinez needs efficient strikes. | Nick Martinez brings a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning) to the mound. He shows solid command and below-average swing-and-miss ability. The Dodgers lineup has an .806 OPS (on-base plus slugging) against right-handed pitchers. That group has a 20.3% K% (strikeout rate) and an 11.0% BB% (walk rate). The Dodgers show strong OPS against this pitcher&#x27;s hand and draw walks at an above-average rate. |
| Eric Lauer vs Tampa Bay Rays | Eric Lauer works off a four-seam-cutter combination. He shows below-average swing-and-miss ability. He shows average command. Eric Lauer has allowed 15 home runs over 224 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.685 OPS), which gives Eric Lauer an edge if he gets ahead. | Eric Lauer enters the game with a 5.47 ERA and a 1.29 WHIP. He shows average command and below-average swing-and-miss ability. The Rays lineup has a .685 OPS against left-handed pitchers. That group carries a 17.7% K% and an 8.8% BB%. |
| Arsenal Scout | The main contrast is Sinker to set up, Changeup to finish versus Four-seam to set up, Cutter to finish. The primary pitch contrast is Sinker against Four-seam, a scouting note for matchup fit and each pressure point. | Martinez uses his sinker 31.4% of the time, moving 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin. His put-away pitch (second most used pitch) is the changeup, which he throws 28.0% of the time. Lauer uses his four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin. His put-away pitch is the cutter, thrown 17.5% of the time. |
| Three Things to Watch | - Can Nick Martinez land the changeup early in counts?<br>- Can Eric Lauer keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Nick Martinez throws his sinker to initiate counts.<br>- Watch if Eric Lauer relies on his cutter to finish plate appearances.<br>- Watch whether the Dodgers lineup maintains its walk rate against Martinez. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Nick Martinez and Eric Lauer: all pitcher figures cover the 2026 regular season through Jun 14. Team offense splits cover the 2026 regular season through Jun 14. | The game features probable pitchers for the scheduled date. |

### NLI scores of the shown model attempt (score only; 22 sentence records)

| Score | Sentence |
|---:|---|
| 0.0012 | Nick Martinez and Eric Lauer start for their teams |
| unrenderable | Nick Martinez leads the Rays against the Dodgers. |
| unrenderable | The Dodgers counter with Eric Lauer on the mound. |
| 0.9412 | These teams meet at UNIQLO Field at Dodger Stadium. |
| 0.9925 | Figures in this report cover the 2026 regular season through June 14. |
| 0.0240 | Nick Martinez brings a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning) to the mound. |
| 0.9876 | He shows solid command and below-average swing-and-miss ability. |
| 0.9963 | The Dodgers lineup has an .806 OPS (on-base plus slugging) against right-handed pitchers. |
| 0.9428 | That group has a 20.3% K% (strikeout rate) and an 11.0% BB% (walk rate). |
| 0.9955 | The Dodgers show strong OPS against this pitcher&#x27;s hand and draw walks at an above-average rate. |
| 0.0044 | Eric Lauer enters the game with a 5.47 ERA and a 1.29 WHIP. |
| 0.9918 | He shows average command and below-average swing-and-miss ability. |
| 0.9931 | The Rays lineup has a .685 OPS against left-handed pitchers. |
| 0.9908 | That group carries a 17.7% K% and an 8.8% BB%. |
| 0.9749 | Martinez uses his sinker 31.4% of the time, moving 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin. |
| 0.9983 | His put-away pitch (second most used pitch) is the changeup, which he throws 28.0% of the time. |
| 0.9863 | Lauer uses his four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin. |
| 0.9850 | His put-away pitch is the cutter, thrown 17.5% of the time. |
| not_applicable | Watch how often Nick Martinez throws his sinker to initiate counts. |
| not_applicable | Watch if Eric Lauer relies on his cutter to finish plate appearances. |
| not_applicable | Watch whether the Dodgers lineup maintains its walk rate against Martinez. |
| 0.0093 | The game features probable pitchers for the scheduled date. |

## veteran-824803

**ACCEPTED**, path `primary_retry`, Gemini calls 3, content attempts 2.

### Gate findings per attempt

**Attempt 1** (`gemini-3.1-flash-lite`, delivery `primary`): hard gates ['W1.number', 'W8.form', 'W1.entity', 'W7.missing', 'W13.series'].

| Check | Offending token | Sentence | Verdict | Why |
|---|---|---|---|---|
| W1.number | two | The series opens with a matchup between two starters at Oriole Park at Camden Yards. | known limitation | &#x27;two starters&#x27; spelled-out count, same as opener-823769 |
| W8.form | None | His four-seam fastball moves -9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin. | real model error | writes &#x27;-9.2 in. sideways&#x27; (a signed number) so the movement pattern does not match; values are right |
| W1.entity | Matchup Analyst | Pitching profiles and lineup notes come from the Matchup Analyst findings. | real model error | names the internal &#x27;Matchup Analyst&#x27; agent in the report |
| W7.missing | findings.home_starter_risks | Pitching profiles and lineup notes come from the Matchup Analyst findings. | real model error | cites a null finding (home starter risks) as the source of pitching profiles |
| W13.series | None | (whole report) | real model error | the required series statement is missing |

S1/style findings of this attempt (3; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-2 | That group | That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 24.5% K% and a 10.2% BB%. |
| W12.scope | None | (whole report) |
| W17.length | 1712 | (whole report) |

**Attempt 2** (`gemini-3.1-flash-lite`, delivery `primary_retry`): hard gates none.

S1/style findings of this attempt (9; scored only):

| Check | Token | Sentence |
|---|---|---|
| S-4 | demonstrate | The lineups demonstrate distinct tendencies at the plate. |
| S-4 | possesses | Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning). |
| S-4 | maintains | This unit maintains a 24.5% K% and a 10.2% BB%. |
| S-4 | maintain | Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic. |
| S-4 | utilizes | Watch how often Shane Baz utilizes his Four-seam. |
| S-2 | the | The pitching profiles for both starters are based on at least 100 pitches thrown. |
| S-2 | This offense | This offense has an elevated swing-and-miss risk and draws walks at an above-average rate. |
| W12.scope | None | (whole report) |
| W17.length | 1676 | (whole report) |

### Rules text beside accepted model text

Model text shown: content attempt 2. Lengths: rules 2179, model 1687 characters.

| Section | Rules text | Model text |
|---|---|---|
| Headline | Four-seam-Slider starter against Four-seam-Curveball starter | Carlos Rodón and the New York Yankees visit Shane Baz and the Baltimore Orioles |
| Short summary | - Carlos Rodón brings this strength: Above-average swing-and-miss ability.<br>- Shane Baz brings this strength: Four-seam to set up, Curveball to finish.<br>- The early what to watch is whether Carlos Rodón can land the slider early in counts. | - Carlos Rodón and Shane Baz represent their teams in this contest.<br>- Both starters bring contrasting styles to the mound.<br>- The lineups demonstrate distinct tendencies at the plate. |
| Matchup Summary | This matchup features Four-seam-Slider starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | All figures cover the 2026 regular season through August 17. Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning). Shane Baz carries a 4.00 ERA and a 1.36 WHIP. |
| Carlos Rodón vs Baltimore Orioles | Carlos Rodón works off a four-seam-slider combination. He shows above-average swing-and-miss ability. He shows below-average command. Carlos Rodón has allowed 3 home runs over 194 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.723 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Carlos Rodón needs efficient strikes. | Carlos Rodón shows below-average command and above-average swing-and-miss ability. The Baltimore Orioles lineup against left-handed pitchers holds a .723 OPS (on-base plus slugging). That group has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate). This offense has an elevated swing-and-miss risk and draws walks at an above-average rate. |
| Shane Baz vs New York Yankees | Shane Baz works off a four-seam-curveball combination. He shows average swing-and-miss ability. He shows average command. Shane Baz has allowed 10 home runs over 598 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.713 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Shane Baz needs efficient strikes. | Shane Baz shows average command and average swing-and-miss ability. The New York Yankees offense against right-handed pitchers posts a .713 OPS. This unit maintains a 24.5% K% and a 10.2% BB%. The group has an elevated swing-and-miss risk and draws walks at an above-average rate. |
| Arsenal Scout | The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Rodón uses his Four-seam to set up and Slider to finish. His Four-seam moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin. Baz relies on his Four-seam to set up and Curveball to finish. His Four-seam moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Carlos Rodón land the slider early in counts?<br>- Can Shane Baz keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic.<br>- Watch how often Shane Baz utilizes his Four-seam.<br>- Watch if the New York Yankees can capitalize on their walk rate against Shane Baz. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Carlos Rodón and Shane Baz: all pitcher figures cover the 2026 regular season through Aug 17. Team offense splits cover the 2026 regular season through Aug 17. | The pitching profiles for both starters are based on at least 100 pitches thrown. |

### NLI scores of the shown model attempt (score only; 23 sentence records)

| Score | Sentence |
|---:|---|
| 0.0155 | Carlos Rodón and the New York Yankees visit Shane Baz and the Baltimore Orioles |
| 0.8532 | Carlos Rodón and Shane Baz represent their teams in this contest. |
| 0.0131 | Both starters bring contrasting styles to the mound. |
| 0.9572 | The lineups demonstrate distinct tendencies at the plate. |
| 0.0579 | All figures cover the 2026 regular season through August 17. |
| 0.9979 | Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning). |
| 0.0010 | Shane Baz carries a 4.00 ERA and a 1.36 WHIP. |
| 0.9587 | Carlos Rodón shows below-average command and above-average swing-and-miss ability. |
| 0.9974 | The Baltimore Orioles lineup against left-handed pitchers holds a .723 OPS (on-base plus slugging). |
| 0.9545 | That group has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate). |
| 0.9718 | This offense has an elevated swing-and-miss risk and draws walks at an above-average rate. |
| 0.8337 | Shane Baz shows average command and average swing-and-miss ability. |
| 0.9974 | The New York Yankees offense against right-handed pitchers posts a .713 OPS. |
| 0.9912 | This unit maintains a 24.5% K% and a 10.2% BB%. |
| 0.9883 | The group has an elevated swing-and-miss risk and draws walks at an above-average rate. |
| 0.9948 | Rodón uses his Four-seam to set up and Slider to finish. |
| 0.8171 | His Four-seam moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin. |
| 0.9843 | Baz relies on his Four-seam to set up and Curveball to finish. |
| 0.8782 | His Four-seam moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin. |
| not_applicable | Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic. |
| not_applicable | Watch how often Shane Baz utilizes his Four-seam. |
| not_applicable | Watch if the New York Yankees can capitalize on their walk rate against Shane Baz. |
| 0.0036 | The pitching profiles for both starters are based on at least 100 pitches thrown. |

## Local evidence records

Run metadata `.local/p2-2/run-info-5.json`, ledger `.local/p2-2/calls.jsonl`, items `.local/p2-2/items-5/` (untracked). SHA-256 of the item files:

- `postseason-849842.json` `6fc72b0620dafbb4236afd38ab75278af3d9087d68292d554ea4a0307d62fd6e`
- `postseason-849849.json` `ddc13f675315b416fe576c6d17d62228d5c3597c7e8a6f0661bf111f7c66987a`
- `opener-824280.json` `4775288530093f4788481b0261be3a02dded37b1165b0a6e0ffae0c70b6b6975`
- `opener-823769.json` `c8c46525201808662a6475f8802f5e8c0ae3e84612cf781ae246c097961f32d4`
- `limited-823836.json` `cd4d39af00ae2fe3fb80125ed7003e2b73bdf60dda285425de67788eb35ec5c1`
- `limited-825104.json` `e42bcd12d769a165a6cc4f3ada83ecaa06d18f06d0c538d2208c6b7096f7598f`
- `limited-823863.json` `0adfcb7091286d0b38a91622b5fb895d5446db68f0b5fa767841ecee37ed6d08`
- `veteran-824027.json` `34e138d53486b54d386a92663f7bb5c6e7cab6902eff945ea3afc445dab8bd3d`
- `veteran-823938.json` `36788d9692ed360baba6b133ebcc374066501b806b72c99ef1245a31fbfda975`
- `veteran-824803.json` `88dfe5691394e29dc33291eb9eb0f999fde9aab28a79f125a7df72a363138754`
