# Pre-freeze dev pass — run 4 review

**INCOMPLETE: 6 of 10 cases attempted. 0 accepted, 6 rejected, 4 not attempted.** This is not a ten-case result or an estimate for the whole guide. Production keeps the rules writer.

Run: 2026-10-31, 12:08–12:19 UTC (07:08–07:19 America/Bogota).

**Gemini calls: 22/30 run; 127/400 experiment (105 before this run).** Capacity failures: 10/22 (45.5%); average: 22/6 = 3.67 calls per attempted case. Both predicates were true at the sixth case boundary; recorded stop reason is `capacity_stop`. No further cases were attempted.

Models: primary `gemini-3.1-flash-lite` (17 calls, 9 capacity failures); fallback `gemini-3.5-flash` (5 calls, 1 capacity failure). LOW thinking, default temperature, 20-second pacing.

## Frozen inputs

- guide `0.4`: `84a87b387c260fd05c0277b8fb19c9abe867c9cf64920643056805df5aef972c`
- glossary `1.1`: `f7a22da784278170c617cd03c18f27db6a14236620608fe3f8f77c70e6d58b8d`
- prompt `p2.2-3`: `db509483d528e1453349501bffcd1e6aa26bee40e2a19192ec21cbed13e44d3c`
- Packets manifest: `0d906f78d42ab013568be535db1716fd329d72033a002a414b1f29625bdc4a25`

[Complete per-sentence diagnostics, every content attempt, evidence paths, NLI scores and style findings](b1-dev-examples-run4.md). The raw report is unchanged. Its 'shown text' length line measures the final rules fallback for rejected cases; the paired text below gives separate rendered lengths.

## Outcomes and paths

| Case | Outcome | Gemini calls | Attempt delivery paths | Final path |
|---|---|---:|---|---|
| `postseason-849842` | rejected | 2 | primary / primary | rules |
| `postseason-849849` | rejected | 2 | primary / primary | rules |
| `opener-824280` | rejected | 2 | primary / primary | rules |
| `opener-823769` | rejected | 3 | primary_retry / primary | rules |
| `limited-823836` | rejected | 6 | fallback / fallback | rules |
| `limited-825104` | rejected | 7 | fallback_retry / fallback | rules |
| `limited-823863` | not_attempted | 0 | — | not_attempted |
| `veteran-824027` | not_attempted | 0 | — | not_attempted |
| `veteran-823938` | not_attempted | 0 | — | not_attempted |
| `veteran-824803` | not_attempted | 0 | — | not_attempted |

## S1 and NLI diagnostics

Style finding instances across all content attempts (not an official report-rule S1 score): `S-1` 6; `S-2` 5; `S-4` 12; `S-5` 2; `S-7` 6; `W11.expansion` 2; `W11.repeat` 1; `W14.team` 2; `W17.length` 6.

S-1, S-2, S-4, S-5, S-7 and S-8 have code detectors; S-3, S-6 and S-9 have no judge/human assessment in this pass. Their absence from the finding list is not a pass.

NLI: 206 scored sentence records out of 247 diagnostic records across content attempts. Statuses: `{'scored': 206, 'unrenderable': 8, 'not_applicable': 33}`. 125 scores are at least 0.9 and 137 at least 0.5; these are unlabelled scores, not entailment accuracy/recall or gates. Watch records are not applicable. Structurally invalid candidates cannot be scored.

## Full rules and model text side by side

All shown model candidates were rejected. Selection follows the frozen report: fewest failed gate codes, later attempt on a tie. A structure failure stops other gate checks, so its count is not comparable. Every attempt's diagnostics remain in the complete report; raw shape-rejected sentence fields are listed separately below and the complete candidates are cached locally.

### postseason-849842

REJECTED; final path `rules`. Shown model: content attempt 1, `gemini-3.1-flash-lite`, delivery path `primary`, gates `['W1.entity', 'W1.evidence_path']`.

Rendered text length: rules 2279; shown model 1984 characters. [All sentence diagnostics](b1-dev-examples-run4.md#postseason-849842).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Four-seam-Splitter starter against Four-seam-Curveball starter | Kevin Gausman and Nick Pivetta duel in Game 2 of the NL Wild Card Series. |
| Short summary | - Kevin Gausman brings this strength: Solid command supports strike-zone control.<br>- Nick Pivetta brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Kevin Gausman can land the splitter early in counts. | - This is Game 2 of the NL Wild Card Series.<br>- Before first pitch, SD leads 1-0.<br>- Both starters bring specific pitching profiles into this 2026 regular season through Sep 29 matchup. |
| Matchup Summary | This matchup features Four-seam-Splitter starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 2 of the NL Wild Card Series. Before first pitch, SD leads 1-0. | Kevin Gausman starts for Chicago with a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning). Nick Pivetta counters for San Diego with a 2.86 ERA and a 1.01 WHIP. Gausman shows solid command and average swing-and-miss ability, while Pivetta displays above-average swing-and-miss ability. All figures cover the 2026 regular season through Sep 29. |
| Kevin Gausman vs San Diego Padres | Kevin Gausman works off a four-seam-splitter combination. He shows average swing-and-miss ability. He shows solid command. Kevin Gausman has allowed 26 home runs over 750 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.722 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Kevin Gausman needs efficient strikes. | The San Diego lineup enters with a .722 OPS (on-base plus slugging). That group carries a 21.5% K% (strikeout rate) and a 9.4% BB% (walk rate). They draw walks at an above-average rate against right-handed pitchers. |
| Nick Pivetta vs Chicago Cubs | Nick Pivetta works off a four-seam-curveball combination. He shows above-average swing-and-miss ability. Control data for Nick Pivetta is limited (140 batters faced; 170 needed), so no command claim is made. Nick Pivetta has allowed 2 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.757 OPS), so Nick Pivetta cannot live over the middle. They draw walks at an above-average rate, so Nick Pivetta needs efficient strikes. | The Chicago lineup has a .757 OPS. The Chicago group shows a 21.2% K% and a 10.6% BB%. Their offense draws walks at an above-average rate against right-handed pitchers. |
| Arsenal Scout | The main contrast is Four-seam to set up, Splitter to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Gausman uses a four-seam fastball as his primary pitch and uses the splitter as his second most used pitch. Pivetta uses a four-seam fastball as his primary offering and the curveball as his second most used pitch. Gausman&#x27;s four-seam fastball moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. His splitter moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin. Pivetta&#x27;s four-seam fastball moves 3.5 in. sideways and 20.3 in. up compared with a pitch thrown without spin. His curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Kevin Gausman land the splitter early in counts?<br>- Can Nick Pivetta keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Gausman uses his splitter to finish counts.<br>- Watch if Pivetta relies on his four-seam fastball to set up hitters.<br>- Watch whether the Chicago lineup draws walks as they have done at an above-average rate. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Kevin Gausman and Nick Pivetta: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them. | Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. There is not enough data yet to rate his command. |

### postseason-849849

REJECTED; final path `rules`. Shown model: content attempt 2, `gemini-3.1-flash-lite`, delivery path `primary`, gates `['W1.number', 'W1.entity', 'W10.cause']`.

Rendered text length: rules 2221; shown model 2024 characters. [All sentence diagnostics](b1-dev-examples-run4.md#postseason-849849).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Four-seam-Slider starter against Four-seam-Sweeper starter | Hagen Smith and the Chicago White Sox meet AJ Blubaugh and the Houston Astros in AL Wild Card Series Game 1. |
| Short summary | - Hagen Smith brings this strength: Above-average swing-and-miss ability.<br>- AJ Blubaugh brings this strength: Four-seam to set up, Sweeper to finish.<br>- The early what to watch is whether Hagen Smith can land the slider early in counts. | - This is the first game of the AL Wild Card Series.<br>- Hagen Smith starts for Chicago, and AJ Blubaugh takes the mound for Houston.<br>- All statistics cited cover the 2026 regular season through Sep 28. |
| Matchup Summary | This matchup features Four-seam-Slider starter against Four-seam-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 1 of the AL Wild Card Series; the series has not started. | Chicago and Houston play in this postseason matchup. Hagen Smith is the visiting starter. AJ Blubaugh is the starting pitcher for the home team. |
| Hagen Smith vs Houston Astros | Hagen Smith works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Hagen Smith is limited (110 batters faced; 170 needed), so no command claim is made. Hagen Smith has allowed 1 home run over 110 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.713 OPS), with no glaring weakness to attack. | Hagen Smith shows above-average swing-and-miss ability. There is not enough data yet to rate his command, as he has 110 batters faced and 170 are needed for a read. The Houston lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers. That group carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) in this split. |
| AJ Blubaugh vs Chicago White Sox | AJ Blubaugh works off a four-seam-sweeper combination. He shows average swing-and-miss ability. He shows below-average command. AJ Blubaugh has allowed 13 home runs over 401 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.716 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so AJ Blubaugh needs efficient strikes. | AJ Blubaugh shows below-average command and average swing-and-miss ability. He has a 3.66 ERA (earned run average) and a 1.23 WHIP (walks plus hits per inning). The Chicago lineup has a .716 OPS against right-handed pitchers. Their K% is 24.1% and their BB% is 9.4% in this split. |
| Arsenal Scout | The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Hagen Smith throws a four-seam fastball 48.4% of the time and a slider 30.3% of the time. His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin. The slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin. AJ Blubaugh relies on his four-seam fastball 51.4% of the time and his sweeper 22.9% of the time. His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin. The sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Hagen Smith land the slider early in counts?<br>- Can AJ Blubaugh keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Hagen Smith uses his slider to finish hitters.<br>- Watch whether AJ Blubaugh can control his pitches to avoid traffic.<br>- Watch if Chicago can manage their 24.1% K% against the Houston pitching staff. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Hagen Smith and AJ Blubaugh: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them. | The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28. The command rating for Hagen Smith is missing due to a limited sample. |

### opener-824280

REJECTED; final path `rules`. Shown model: content attempt 2, `gemini-3.1-flash-lite`, delivery path `primary`, gates `['W15.outcome']`.

Rendered text length: rules 2330; shown model 2191 characters. [All sentence diagnostics](b1-dev-examples-run4.md#opener-824280).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Four-seam-Splitter starter against Sinker-Slider starter | Trey Yesavage and Brenan Hanifee start in Detroit |
| Short summary | - Trey Yesavage brings this strength: Four-seam to set up, Splitter to finish.<br>- Brenan Hanifee brings this strength: Sinker to set up, Slider to finish.<br>- The early what to watch is whether Trey Yesavage can land the splitter early in counts. | - Trey Yesavage faces off against Brenan Hanifee as Toronto visits Detroit.<br>- Both starters bring early season pitching numbers into this matchup for the 2026 regular season through May 14.<br>- The game takes place at Comerica Park. |
| Matchup Summary | This matchup features Four-seam-Splitter starter against Sinker-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | Trey Yesavage holds a 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning) for the Toronto Blue Jays during the 2026 regular season through May 14. Brenan Hanifee has a 1.08 ERA and a 1.08 WHIP for the Detroit Tigers in that same period. Control and strikeout data for both pitchers remains in a limited sample. |
| Trey Yesavage vs Detroit Tigers | Trey Yesavage works off a four-seam-splitter combination. Strikeout data for Trey Yesavage is limited (57 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Trey Yesavage is limited (57 batters faced; 170 needed), so no command claim is made. Trey Yesavage has allowed 0 home runs over 57 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.725 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Trey Yesavage needs efficient strikes. | Trey Yesavage has a limited sample of 57 batters faced, with 170 needed for a control read and 70 for a strikeout read. The Detroit Tigers lineup against right-handed pitchers carries a .725 OPS (on-base plus slugging) as of the 2026 regular season through May 14. That group has a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split, and it draws walks at an above-average rate. |
| Brenan Hanifee vs Toronto Blue Jays | Brenan Hanifee works off a sinker-slider combination. Strikeout data for Brenan Hanifee is limited (33 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Brenan Hanifee is limited (33 batters faced; 170 needed), so no command claim is made. Brenan Hanifee has allowed 1 home run over 33 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.701 OPS), with no glaring weakness to attack. | Brenan Hanifee has a limited sample of 33 batters faced, with 170 needed for a control read and 70 for a strikeout read. The Toronto Blue Jays lineup against right-handed pitchers has a .701 OPS, an 18.2% K%, and a 7.3% BB% over the 2026 regular season through May 14. |
| Arsenal Scout | The main contrast is Four-seam to set up, Splitter to finish versus Sinker to set up, Slider to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point. | Trey Yesavage uses a four-seam fastball 48.6% of the time, moving 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. His put-away pitch is the splitter, which he throws 36.6% of the time, moving 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin. Brenan Hanifee uses a sinker 58.9% of the time, moving 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin. His put-away pitch is the slider, which he uses 18.8% of the time, moving 1.7 in. sideways and 2.8 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Trey Yesavage land the splitter early in counts?<br>- Can Brenan Hanifee keep the ball low?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Trey Yesavage relies on his four-seam fastball to set up his splitter.<br>- Watch whether Brenan Hanifee uses his sinker effectively to set up his slider.<br>- Watch how the Detroit Tigers lineup manages the strikeout rate against Trey Yesavage. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Trey Yesavage and Brenan Hanifee: all pitcher figures cover the 2026 regular season through May 14. Team offense splits cover the 2026 regular season through May 14. Samples below the minimum are flagged as limited and no claim is made from them. | The data provided for this matchup uses probable pitchers for the 2026 regular season through May 14. |

### opener-823769

REJECTED; final path `rules`. Shown model: content attempt 1, `gemini-3.1-flash-lite`, delivery path `primary_retry`, gates `['W17.structure']`.

Rendered text length: rules 2325; shown model 1709 characters. [All sentence diagnostics](b1-dev-examples-run4.md#opener-823769).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Four-seam-Slider starter against Four-seam-Changeup starter | Ryan Rolison and Brandon Woodruff meet in Milwaukee |
| Short summary | - Ryan Rolison brings this strength: Above-average swing-and-miss ability.<br>- Brandon Woodruff brings this strength: Above-average swing-and-miss ability.<br>- The early what to watch is whether Ryan Rolison can land the slider early in counts. | - Ryan Rolison makes the start for Chicago against Brandon Woodruff of Milwaukee.<br>- Both starters show above-average swing-and-miss ability.<br>- The lineups for both teams draw walks at an above-average rate.<br>- All data in this report covers the 2026 regular season through Jun 27. |
| Matchup Summary | This matchup features Four-seam-Slider starter against Four-seam-Changeup starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning). Brandon Woodruff maintains a 3.0 ERA and a 0.89 WHIP. Woodruff has a lower WHIP than Rolison, while Rolison has a lower ERA than Woodruff. |
| Ryan Rolison vs Milwaukee Brewers | Ryan Rolison works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Ryan Rolison is limited (114 batters faced; 170 needed), so no command claim is made. Ryan Rolison has allowed 3 home runs over 114 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.682 OPS), which gives Ryan Rolison an edge if he gets ahead. They draw walks at an above-average rate, so Ryan Rolison needs efficient strikes. | The Brewers lineup has a .682 OPS (on-base plus slugging) against left-handed pitchers. This group has a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate). Rolison has a limited sample for control: 114 batters faced, and 170 are needed for a read. |
| Brandon Woodruff vs Chicago Cubs | Brandon Woodruff works off a four-seam-changeup combination. He shows above-average swing-and-miss ability. Control data for Brandon Woodruff is limited (140 batters faced; 170 needed), so no command claim is made. Brandon Woodruff has allowed 4 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Brandon Woodruff needs efficient strikes. | Against right-handed pitchers, the Cubs lineup has a .734 OPS. They carry a 21.2% K% and an 11.4% BB%. Woodruff has a limited sample for control: 140 batters faced, and 170 are needed for a read. |
| Arsenal Scout | The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Changeup to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point. | Rolison uses his Four-seam fastball 44.8% of the time and uses his Slider (second most used pitch) 19.9% of the time. His Slider moves 4.4 in. sideways and 2.3 in. down compared with a pitch thrown without spin. Woodruff throws his Four-seam fastball 43.9% of the time and his Changeup (second most used pitch) 19.8% of the time. His Changeup moves 16.1 in. sideways and 8.0 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can Ryan Rolison land the slider early in counts?<br>- Can Brandon Woodruff keep the ball in the zone?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Rolison uses his Slider in counts where he needs a finish.<br>- Watch whether Woodruff executes his Changeup against right-handed hitters effectively.<br>- Watch if the Cubs lineup can generate walks against Woodruff. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Ryan Rolison and Brandon Woodruff: all pitcher figures cover the 2026 regular season through Jun 27. Team offense splits cover the 2026 regular season through Jun 27. Samples below the minimum are flagged as limited and no claim is made from them. | Data confidence reflects that these are the probable pitchers. |

### limited-823836

REJECTED; final path `rules`. Shown model: content attempt 1, `gemini-3.5-flash`, delivery path `fallback`, gates `['W12.time']`.

Rendered text length: rules 2196; shown model 1725 characters. [All sentence diagnostics](b1-dev-examples-run4.md#limited-823836).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Four-seam-Changeup starter against Sinker-Sweeper starter | George Klassen faces Tyler Phillips in Miami |
| Short summary | - George Klassen brings this strength: Four-seam to set up, Changeup to finish.<br>- Tyler Phillips brings this strength: Sinker to set up, Sweeper to finish.<br>- The early what to watch is whether George Klassen can land the changeup early in counts. | - George Klassen has limited control and strikeout data.<br>- Tyler Phillips carries a 3.53 ERA (earned run average) for Miami.<br>- This report uses data from the 2026 regular season through Aug 6. |
| Matchup Summary | This matchup features Four-seam-Changeup starter against Sinker-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch. | George Klassen starts for the Angels with a 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning). Tyler Phillips has a 3.53 ERA and a 1.35 WHIP for the Marlins. This report covers the 2026 regular season through Aug 6. |
| George Klassen vs Miami Marlins | George Klassen works off a four-seam-changeup combination. Strikeout data for George Klassen is limited (32 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for George Klassen is limited (32 batters faced; 170 needed), so no command claim is made. George Klassen has allowed 1 home run over 32 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. | George Klassen has limited control data with 32 batters faced when 170 are needed. His strikeout data is also limited with 32 batters faced out of 70 required. Against right-handed pitchers, the Marlins lineup has a .734 OPS (on-base plus slugging). Their K% (strikeout rate) is 21.0% and their BB% (walk rate) is 8.9%. |
| Tyler Phillips vs Los Angeles Angels | Tyler Phillips works off a sinker-sweeper combination. He shows below-average swing-and-miss ability. He shows average command. Tyler Phillips has allowed 11 home runs over 383 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.687 OPS), which gives Tyler Phillips an edge if he gets ahead. They also strike out often, which favors a swing-and-miss approach. | Tyler Phillips shows average command and below-average swing-and-miss ability. Against right-handed pitchers, the Angels lineup posts a .687 OPS. That lineup shows a 24.9% K% and an 8.3% BB%. Los Angeles has elevated swing-and-miss risk. |
| Arsenal Scout | The main contrast is Four-seam to set up, Changeup to finish versus Sinker to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point. | George Klassen relies on a Four-seam fastball at 38.6% and a Changeup at 24.8%. His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. Tyler Phillips throws a Sinker 25.5% of the time and a Sweeper 24.2% of the time. His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin. |
| Three Things to Watch | - Can George Klassen land the changeup early in counts?<br>- Can Tyler Phillips keep the ball low?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often George Klassen relies on his Four-seam pitch.<br>- Watch whether Tyler Phillips throws his put-away pitch (second most used pitch), the Sweeper.<br>- Watch if the Angels manage their 24.9% K% against Tyler Phillips. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. George Klassen and Tyler Phillips: all pitcher figures cover the 2026 regular season through Aug 6. Team offense splits cover the 2026 regular season through Aug 6. Samples below the minimum are flagged as limited and no claim is made from them. | Lineup status is probable pitchers. George Klassen has pitched 4.2 innings this season. Tyler Phillips has completed 89.1 innings. |

### limited-825104

REJECTED; final path `rules`. Shown model: content attempt 2, `gemini-3.5-flash`, delivery path `fallback`, gates `['W1.entity', 'W6.arsenal']`.

Rendered text length: rules 2494; shown model 1493 characters. [All sentence diagnostics](b1-dev-examples-run4.md#limited-825104).

| Section | Rules text (A) | Rejected model text |
|---|---|---|
| Headline | Bryce Elder against Michael Soroka | Bryce Elder and Michael Soroka meet as Atlanta faces Arizona |
| Short summary | - Bryce Elder has no claimed strength because the data is limited.<br>- Michael Soroka has no claimed strength because the data is limited.<br>- The early what to watch is whether Bryce Elder can stay ahead of hitters early in counts. | - Bryce Elder carries a 0.00 ERA (earned run average) for Atlanta over the 2026 regular season through Apr 3.<br>- Michael Soroka holds a 0.00 ERA for Arizona.<br>- Atlanta has a .827 OPS (on-base plus slugging) against right-handed pitchers. |
| Matchup Summary | This matchup features Bryce Elder against Michael Soroka. The scouting note is matchup fit, with each pressure point shaping what to watch. | Bryce Elder has a 0.00 ERA and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3. Michael Soroka matches that 0.00 ERA and 1.00 WHIP for Arizona. |
| Bryce Elder vs Arizona Diamondbacks | Bryce Elder&#x27;s arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Bryce Elder is limited (23 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Bryce Elder is limited (23 batters faced; 170 needed), so no command claim is made. Bryce Elder has allowed 0 home runs over 23 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.653 OPS), which gives Bryce Elder an edge if he gets ahead. | Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a read. Arizona has a .653 OPS against right-handed pitchers. Their K% (strikeout rate) is 22.8% and their BB% (walk rate) is 8.7%. |
| Michael Soroka vs Atlanta Braves | Michael Soroka&#x27;s arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Michael Soroka is limited (20 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Michael Soroka is limited (20 batters faced; 170 needed), so no command claim is made. Michael Soroka has allowed 0 home runs over 20 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.827 OPS), so Michael Soroka cannot live over the middle. They draw walks at an above-average rate, so Michael Soroka needs efficient strikes. | Control data for Michael Soroka is limited: 20 batters faced, and 170 are needed for a read. Atlanta draws walks at an above-average rate and has strong OPS against this pitcher&#x27;s hand. Their strikeout rate is 19.4% and their walk rate is 9.5%. |
| Arsenal Scout | Bryce Elder&#x27;s arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Michael Soroka&#x27;s arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. No arsenal contrast is drawn because at least one arsenal has too little data. | Bryce Elder relies on a Sinker 34.9% of the time and a Slider 34.9% of the time. Michael Soroka throws a Slurve 48.3% of the time and a Four-seam 33.7% of the time. Both pitchers have limited sample sizes for their full pitch shapes. |
| Three Things to Watch | - Can Bryce Elder stay ahead of hitters early in counts?<br>- Can Michael Soroka work efficiently through the lineup?<br>- Which lineup forces more deep counts by the third inning? | - Watch how often Bryce Elder relies on his Sinker against right-handed hitters.<br>- Watch whether Michael Soroka relies on his Slurve as his primary pitch.<br>- Watch if Atlanta keeps its .827 OPS against right-handed starters. |
| Data Confidence Note | This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Bryce Elder and Michael Soroka: all pitcher figures cover the 2026 regular season through Apr 3. Team offense splits cover the 2026 regular season through Apr 3. Samples below the minimum are flagged as limited and no claim is made from them. | Both starters have limited sample sizes in control and strikeout measures. Probable pitchers are listed for this matchup. |

## Shape-rejected attempt: raw sentence fields

These fields are quoted model output. Other code checks and NLI did not run after the structure gate failed. Supplied citations below have not been verified as support for this attempt.

### opener-823769, content attempt 1

| Sentence field | Model text | Supplied evidence | NLI / other checks |
|---|---|---|---|
| 1 | Ryan Rolison and Brandon Woodruff meet in Milwaukee | [{&quot;path&quot;: &quot;starters.away_starter.name&quot;, &quot;value&quot;: &quot;Ryan Rolison&quot;}, {&quot;path&quot;: &quot;starters.home_starter.name&quot;, &quot;value&quot;: &quot;Brandon Woodruff&quot;}] | Not evaluated: structure gate |
| 2 | Ryan Rolison makes the start for Chicago against Brandon Woodruff of Milwaukee. | [{&quot;path&quot;: &quot;starters.away_starter.name&quot;, &quot;value&quot;: &quot;Ryan Rolison&quot;}, {&quot;path&quot;: &quot;starters.home_starter.name&quot;, &quot;value&quot;: &quot;Brandon Woodruff&quot;}] | Not evaluated: structure gate |
| 3 | Both starters show above-average swing-and-miss ability. | [{&quot;path&quot;: &quot;starters.away_starter.pitching_profile.swing_miss_label&quot;, &quot;value&quot;: &quot;Above-average swing-and-miss ability&quot;}, {&quot;path&quot;: &quot;starters.home_starter.pitching_profile.swing_miss_label&quot;, &quot;value&quot;: &quot;Above-average swing-and-miss ability&quot;}] | Not evaluated: structure gate |
| 4 | The lineups for both teams draw walks at an above-average rate. | [{&quot;path&quot;: &quot;findings.lineup_notes.away&quot;, &quot;value&quot;: &quot;draws walks at an above-average rate&quot;}, {&quot;path&quot;: &quot;findings.lineup_notes.home&quot;, &quot;value&quot;: &quot;draws walks at an above-average rate&quot;}] | Not evaluated: structure gate |
| 5 | All data in this report covers the 2026 regular season through Jun 27. | [{&quot;path&quot;: &quot;starters.away_starter.season_summary.scopes.counts.label&quot;, &quot;value&quot;: &quot;2026 regular season through Jun 27&quot;}] | Not evaluated: structure gate |
| 6 | Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning). | [{&quot;path&quot;: &quot;starters.away_starter.season_summary.era&quot;, &quot;value&quot;: &quot;1.82&quot;}, {&quot;path&quot;: &quot;glossary.ERA.short&quot;, &quot;value&quot;: &quot;earned run average&quot;}, {&quot;path&quot;: &quot;starters.away_starter.season_summary.whip&quot;, &quot;value&quot;: &quot;1.11&quot;}, {&quot;path&quot;: &quot;glossary.WHIP.short&quot;, &quot;value&quot;: &quot;walks plus hits per inning&quot;}] | Not evaluated: structure gate |
| 7 | Brandon Woodruff maintains a 3.0 ERA and a 0.89 WHIP. | [{&quot;path&quot;: &quot;starters.home_starter.season_summary.era_number&quot;, &quot;value&quot;: &quot;3.0&quot;}, {&quot;path&quot;: &quot;starters.home_starter.season_summary.whip_number&quot;, &quot;value&quot;: &quot;0.89&quot;}] | Not evaluated: structure gate |
| 8 | Woodruff has a lower WHIP than Rolison, while Rolison has a lower ERA than Woodruff. | [{&quot;path&quot;: &quot;starters.home_starter.season_summary.whip_number&quot;, &quot;value&quot;: &quot;0.89&quot;}, {&quot;path&quot;: &quot;starters.away_starter.season_summary.whip_number&quot;, &quot;value&quot;: &quot;1.11&quot;}, {&quot;path&quot;: &quot;starters.away_starter.season_summary.era_number&quot;, &quot;value&quot;: &quot;1.82&quot;}, {&quot;path&quot;: &quot;starters.home_starter.season_summary.era_number&quot;, &quot;value&quot;: &quot;3.0&quot;}] | Not evaluated: structure gate |
| 9 | The Brewers lineup has a .682 OPS (on-base plus slugging) against left-handed pitchers. | [{&quot;path&quot;: &quot;teams.home.offense_profile.ops_vs_hand&quot;, &quot;value&quot;: &quot;.682&quot;}, {&quot;path&quot;: &quot;glossary.OPS.short&quot;, &quot;value&quot;: &quot;on-base plus slugging&quot;}] | Not evaluated: structure gate |
| 10 | This group has a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate). | [{&quot;path&quot;: &quot;teams.home.offense_profile.k_rate_vs_hand&quot;, &quot;value&quot;: &quot;21.8%&quot;}, {&quot;path&quot;: &quot;glossary.K%.short&quot;, &quot;value&quot;: &quot;strikeout rate&quot;}, {&quot;path&quot;: &quot;teams.home.offense_profile.bb_rate_vs_hand&quot;, &quot;value&quot;: &quot;10.3%&quot;}, {&quot;path&quot;: &quot;glossary.BB%.short&quot;, &quot;value&quot;: &quot;walk rate&quot;}] | Not evaluated: structure gate |
| 11 | Rolison has a limited sample for control: 114 batters faced, and 170 are needed for a read. | [{&quot;path&quot;: &quot;starters.away_starter.sample.rates.batters_faced&quot;, &quot;value&quot;: &quot;114&quot;}, {&quot;path&quot;: &quot;starters.away_starter.sample.thresholds.control&quot;, &quot;value&quot;: &quot;170&quot;}] | Not evaluated: structure gate |
| 12 | Against right-handed pitchers, the Cubs lineup has a .734 OPS. | [{&quot;path&quot;: &quot;teams.away.offense_profile.ops_vs_hand&quot;, &quot;value&quot;: &quot;.734&quot;}] | Not evaluated: structure gate |
| 13 | They carry a 21.2% K% and an 11.4% BB%. | [{&quot;path&quot;: &quot;teams.away.offense_profile.k_rate_vs_hand&quot;, &quot;value&quot;: &quot;21.2%&quot;}, {&quot;path&quot;: &quot;teams.away.offense_profile.bb_rate_vs_hand&quot;, &quot;value&quot;: &quot;11.4%&quot;}] | Not evaluated: structure gate |
| 14 | Woodruff has a limited sample for control: 140 batters faced, and 170 are needed for a read. | [{&quot;path&quot;: &quot;starters.home_starter.sample.rates.batters_faced&quot;, &quot;value&quot;: &quot;140&quot;}, {&quot;path&quot;: &quot;starters.home_starter.sample.thresholds.control&quot;, &quot;value&quot;: &quot;170&quot;}] | Not evaluated: structure gate |
| 15 | Rolison uses his Four-seam fastball 44.8% of the time and uses his Slider (second most used pitch) 19.9% of the time. | [{&quot;path&quot;: &quot;pitch_mix.0.away_starter.overall&quot;, &quot;value&quot;: &quot;44.8&quot;}, {&quot;path&quot;: &quot;pitch_mix.1.away_starter.overall&quot;, &quot;value&quot;: &quot;19.9&quot;}, {&quot;path&quot;: &quot;glossary.put-away pitch.short&quot;, &quot;value&quot;: &quot;second most used pitch&quot;}] | Not evaluated: structure gate |
| 16 | His Slider moves 4.4 in. sideways and 2.3 in. down compared with a pitch thrown without spin. | [{&quot;path&quot;: &quot;pitch_movement.away_starter.Slider.h_break&quot;, &quot;value&quot;: &quot;-4.4&quot;}, {&quot;path&quot;: &quot;pitch_movement.away_starter.Slider.v_break&quot;, &quot;value&quot;: &quot;-2.3&quot;}] | Not evaluated: structure gate |
| 17 | Woodruff throws his Four-seam fastball 43.9% of the time and his Changeup (second most used pitch) 19.8% of the time. | [{&quot;path&quot;: &quot;pitch_mix.0.home_starter.overall&quot;, &quot;value&quot;: &quot;43.9&quot;}, {&quot;path&quot;: &quot;pitch_mix.5.home_starter.overall&quot;, &quot;value&quot;: &quot;19.8&quot;}] | Not evaluated: structure gate |
| 18 | His Changeup moves 16.1 in. sideways and 8.0 in. up compared with a pitch thrown without spin. | [{&quot;path&quot;: &quot;pitch_movement.home_starter.Changeup.h_break&quot;, &quot;value&quot;: &quot;-16.1&quot;}, {&quot;path&quot;: &quot;pitch_movement.home_starter.Changeup.v_break&quot;, &quot;value&quot;: &quot;8.0&quot;}] | Not evaluated: structure gate |
| 19 | Watch how often Rolison uses his Slider in counts where he needs a finish. | [{&quot;path&quot;: &quot;starters.away_starter.pitching_profile.putaway_pitch&quot;, &quot;value&quot;: &quot;Slider&quot;}] | Not evaluated: structure gate |
| 20 | Watch whether Woodruff executes his Changeup against right-handed hitters effectively. | [{&quot;path&quot;: &quot;starters.home_starter.pitching_profile.putaway_pitch&quot;, &quot;value&quot;: &quot;Changeup&quot;}] | Not evaluated: structure gate |
| 21 | Watch if the Cubs lineup can generate walks against Woodruff. | [{&quot;path&quot;: &quot;findings.lineup_notes.away&quot;, &quot;value&quot;: &quot;draws walks at an above-average rate&quot;}] | Not evaluated: structure gate |
| 22 | Data confidence reflects that these are the probable pitchers. | [{&quot;path&quot;: &quot;data_confidence.lineup_status&quot;, &quot;value&quot;: &quot;probable pitchers&quot;}] | Not evaluated: structure gate |

## Local evidence records

Run metadata: `.local/p2-2/run-info-4.json`; durable shared ledger: `.local/p2-2/calls.jsonl`; audit: `.local/p2-2/run4-audit.json`.

- `.local\p2-2\items-4\postseason-849842.json` — SHA-256 `d2597b36c7d03022949762f2467442c8c017d21fbedc1d7c1b80e816a4ed8ccf`
- `.local\p2-2\items-4\postseason-849849.json` — SHA-256 `93135594f0323b26d6ab25947e15cfb69682ee58a664486d6c319d6a5ecdd8e3`
- `.local\p2-2\items-4\opener-824280.json` — SHA-256 `3a121bb21062e18b779bc6e4589facc7aeb42ef37ad48944ca8285008dbbd040`
- `.local\p2-2\items-4\opener-823769.json` — SHA-256 `3bb1266df17ccdb55a35ee3e6d873f630ab98b8ff0763abb61fc4733d38a6688`
- `.local\p2-2\items-4\limited-823836.json` — SHA-256 `d197dd32c0b3b40e5027bb5287cf2659d1ff3b6a3eefa977e6376cb683dbc2f9`
- `.local\p2-2\items-4\limited-825104.json` — SHA-256 `85a1ad5d8cbb906b547155bb15d0937bf2df8a0ea90f0f8fc457835a848f219d`

## Gate audit of all 12 rejected candidates

Owner-requested audit (Oct 31). Counts use saved check_detail entries filtered by the frozen hard-gate classification. Each distinct recorded sentence/token finding counts once; a candidate can contribute several. The second count is affected candidates out of 12. Rankings use finding count, then check id; style and NLI diagnostics are excluded. The structure-rejected candidate contributes one structure finding; other gates were not evaluated for it. Invalid evidence paths/values also stop the remaining checks for that sentence. These are recorded findings, not an exhaustive count of every possible error.

Total: **47 findings**, **32 candidate/check incidences**, **15 check ids**, **12 rejected candidates**.

| Failed gate id | Findings | Affected candidates / 12 |
|---|---:|---:|
| `W1.entity` | 11 | 5 |
| `W1.evidence_path` | 6 | 4 |
| `W1.number` | 5 | 2 |
| `W2.comparison` | 4 | 3 |
| `W10.cause` | 3 | 3 |
| `W1.evidence_value` | 2 | 1 |
| `W12.time` | 2 | 2 |
| `W15.outcome` | 2 | 2 |
| `W5.label` | 2 | 2 |
| `W6.arsenal` | 2 | 2 |
| `W6.unsaid` | 2 | 2 |
| `W7.missing` | 2 | 1 |
| `W8.form` | 2 | 1 |
| `W17.structure` | 1 | 1 |
| `W5.intensity` | 1 | 1 |

### Verdict definitions

Verdicts below concern the named failed check; they do not accept a sentence's other claims or the whole candidate. They are interpretive dev-packet audits, not owner entailment labels, NLI calibration or a change to a frozen gate.

The requested wrong-fact/rigidity binary needs one qualification: a true value paired with a nonexistent or incomplete citation is a **model citation error**. It is neither an invented numeric fact nor a harness false positive. These cases remain model errors under the evidence contract and are identified explicitly.

### W1.entity: three examples

1. **limited-825104, attempt 2** — offending token/value: `Probable`.

> Probable pitchers are listed for this matchup.

   **Verdict:** Harness rigidity: 'Probable' is an ordinary sentence opener. The cited lineup_status is exactly 'probable pitchers'.

   Packet support: `data_confidence.lineup_status` = `"probable pitchers"`.

2. **limited-825104, attempt 1** — offending token/value: `Findings`.

> Findings indicate Atlanta has strong OPS against this pitcher's hand; draws walks at an above-average rate.

   **Verdict:** Harness rigidity: 'Findings' is a common noun, not an invented entity. The cited Atlanta lineup finding supplies the strong-OPS and walk-rate claims.

   Packet support: `teams.away.name` = `"Atlanta Braves"`; `findings.lineup_notes.away` = `"has strong OPS against this pitcher's hand; draws walks at an above-average rate"`.

3. **opener-824280, attempt 1** — offending token/value: `This`.

> The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%).

   **Verdict:** Harness rigidity: all three Toronto rates and the RHP scope match the packet. 'This' opens the second sentence inside one model field; the entity heuristic recognizes openers only at the field's start.

   Packet support: `teams.away.offense_profile.ops_number` = `0.701`; `teams.away.offense_profile.k_rate_number` = `18.2`; `teams.away.offense_profile.bb_rate_number` = `7.3`; `teams.away.offense_profile.vs_pitcher_hand` = `"RHP"`.

### W1.evidence_path: three examples

1. **opener-823769, attempt 2** — offending token/value: `starters.away_starter.thresholds.control`.

> Control data for Rolison is limited: 114 batters faced, and 170 are needed for a read.

   **Verdict:** Model error — citation, not an invented numeric fact: 114 and 170 are real packet values, but the supplied threshold path does not exist. The valid threshold path includes '.sample.'. The evidence-path gate correctly enforces the contract.

   Packet support: `starters.away_starter.sample.rates.batters_faced` = `114`; `starters.away_starter.sample.thresholds.control` = `170`; `starters.away_starter.sample.limited.control` = `true`.

2. **opener-823769, attempt 2** — offending token/value: `starters.home_starter.thresholds.control`.

> Control data for Woodruff is limited: 140 batters faced, and 170 are needed for a read.

   **Verdict:** Model error — citation: the sentence's 140/170 values are supported, but the model omitted '.sample.' from its threshold pointer. This is a correct evidence-contract rejection, not a factual hallucination or harness false positive.

   Packet support: `starters.home_starter.sample.rates.batters_faced` = `140`; `starters.home_starter.sample.thresholds.control` = `170`; `starters.home_starter.sample.limited.control` = `true`.

3. **postseason-849842, attempt 1** — offending token/value: `starters.home_starter.thresholds.control`.

> Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.

   **Verdict:** Model error — citation: Pivetta has 140 batters faced and a 170 control threshold, but the claimed threshold pointer is nonexistent. The correct path is starters.home_starter.sample.thresholds.control.

   Packet support: `starters.home_starter.sample.rates.batters_faced` = `140`; `starters.home_starter.sample.thresholds.control` = `170`; `starters.home_starter.sample.limited.control` = `true`.

### W1.number: three examples

1. **postseason-849842, attempt 2** — offending token/value: `09`.

> All figures in this report cover the 2026 regular season through 2026-09-29.

   **Verdict:** Model error — missing date citation: this field generated two findings, '09' and '29'. The 2026-09-29 cutoff exists in the packet's .through values, but the sentence cites only the label '2026 regular season', which does not supply the month/day. The date is not invented; the supplied citation is incomplete. This does not certify the broad 'all figures' wording.

   Packet support: `starters.away_starter.sample.arsenal.scope.label` = `"2026 regular season"`; `starters.away_starter.sample.arsenal.scope.through` = `"2026-09-29"`.

2. **postseason-849842, attempt 2** — offending token/value: `10.4`.

> That group shows a 21.2% strikeout rate (K%) and a 10.4% walk rate (BB%).

   **Verdict:** Model error — wrong fact: the sentence says 10.4% BB%, while its cited Chicago value and the packet both say 10.6%.

   Packet support: `teams.away.offense_profile.k_rate_vs_hand` = `"21.2%"`; `teams.away.offense_profile.bb_rate_vs_hand` = `"10.6%"`.

3. **postseason-849849, attempt 2** — offending token/value: `28`.

> All statistics cited cover the 2026 regular season through Sep 28.

   **Verdict:** Model error — missing date citation: the packet cutoff is 2026-09-28, but this sentence cites only the year/season label and omits a .through path. Its month/day are true elsewhere in the packet, not supplied by the cited value. The separate 'Sep' entity finding is a different issue.

   Packet support: `starters.away_starter.sample.arsenal.scope.label` = `"2026 regular season"`; `starters.away_starter.sample.arsenal.scope.through` = `"2026-09-28"`.

### W2.comparison: three examples

1. **limited-823836, attempt 2** — offending token/value: `versus`.

> The Angels lineup has a .687 OPS versus right-handed pitching.

   **Verdict:** Harness rigidity: 'versus right-handed pitching' states the supplied batting-split scope, not a numerical comparison requiring two values. The OPS is .687 and the split is RHP.

   Packet support: `teams.away.name` = `"Los Angeles Angels"`; `teams.away.offense_profile.ops_vs_hand` = `".687"`; `teams.away.offense_profile.vs_pitcher_hand` = `"RHP"`.

2. **opener-823769, attempt 2** — offending token/value: `versus`.

> Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup

   **Verdict:** Harness rigidity for this check: Chicago versus Milwaukee names the matchup, not a numerical comparison. Both starter names and team city aliases are in the packet. This verdict is about W2.comparison, not completeness of the supplied team-name citations.

   Packet support: `starters.away_starter.name` = `"Ryan Rolison"`; `starters.home_starter.name` = `"Brandon Woodruff"`; `teams.away.name` = `"Chicago Cubs"`; `teams.home.name` = `"Milwaukee Brewers"`.

3. **postseason-849842, attempt 2** — offending token/value: `lower`.

> Pivetta has a lower ERA (2.86 vs 4.51) and a lower WHIP (1.01 vs 1.27) than Gausman.

   **Verdict:** Harness rigidity: both comparisons are true (2.86 < 4.51; 1.01 < 1.27), with all four correct numeric values cited. The checker requires exactly two numeric citations, so it rejects two valid comparisons in one sentence.

   Packet support: `starters.home_starter.season_summary.era_number` = `2.86`; `starters.away_starter.season_summary.era_number` = `4.51`; `starters.home_starter.season_summary.whip_number` = `1.01`; `starters.away_starter.season_summary.whip_number` = `1.27`.

### W10.cause: three examples

1. **limited-825104, attempt 1** — offending token/value: `due to`.

> Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.

   **Verdict:** Harness rigidity for the causal check: both control and strikeout dimensions are limited (23/20 BF against minima 170/70), and all four labels are null; the small-sample explanation follows the documented thresholds. 'Official' is unverified wording, and the cited null command labels alone do not cover every subclaim. This verdict does not endorse that word or the whole candidate.

   Packet support: `starters.away_starter.sample.rates.batters_faced` = `23`; `starters.home_starter.sample.rates.batters_faced` = `20`; `starters.away_starter.sample.thresholds.control` = `170`; `starters.away_starter.sample.thresholds.strikeout` = `70`; `starters.away_starter.sample.limited.control` = `true`; `starters.away_starter.sample.limited.strikeout` = `true`; `starters.home_starter.sample.limited.control` = `true`; `starters.home_starter.sample.limited.strikeout` = `true`; `starters.away_starter.pitching_profile.command_label` = `null`; `starters.home_starter.pitching_profile.command_label` = `null`; `starters.away_starter.pitching_profile.swing_miss_label` = `null`; `starters.home_starter.pitching_profile.swing_miss_label` = `null`.

2. **postseason-849849, attempt 1** — offending token/value: `due to`.

> Watch if AJ Blubaugh encounters deep-count traffic due to his command.

   **Verdict:** Harness rigidity: the sentence cites the packet finding 'Below-average command can create deep-count traffic'. The causal relationship is explicitly provided; it was not invented by this candidate. The blanket 'due to' check rejects it anyway.

   Packet support: `findings.home_starter_risks` = `"Below-average command can create deep-count traffic"`.

3. **postseason-849849, attempt 2** — offending token/value: `due to`.

> The command rating for Hagen Smith is missing due to a limited sample.

   **Verdict:** Harness rigidity: Hagen Smith's command label is null, limited.control is true, and 110 BF is below the 170 threshold. The stated reason is the packet's documented limitation; the blanket causal-word check has no exception for it.

   Packet support: `starters.away_starter.pitching_profile.command_label` = `null`; `starters.away_starter.sample.limited.control` = `true`; `starters.away_starter.sample.rates.batters_faced` = `110`; `starters.away_starter.sample.thresholds.control` = `170`.

Audit evidence: `.local/p2-2/run4-gate-analysis.json` holds all 47 findings and the exact supplied/actual citation values for these 15 examples. No cached candidate, frozen input, gate implementation or label pool was changed. No provider/model call made.
