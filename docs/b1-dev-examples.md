# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest `9c85e2e21a9db548f2f57c2c1536d9e998c2ec52f752d7e0d08be0ce8f149b8e`, prompt `p2.2-1`. Nothing here is published; rules stay live.

Gemini HTTP calls: run 40 of 40, experiment 40 of 400.
Paths: primary 0, primary_retry 0, fallback 0, fallback_retry 0, rules 10. LLM coverage 0/10; not written by the primary model 10/10 (a fallback or rules result is not a primary first-attempt success).



## Notes added after the run (read first)

- Run at commit `3fc3a92`, guide 0.2, prompt `p2.2-1`, first live Gemini calls of P2.2. Gemini HTTP calls from the ledger: 40 of the run cap 40 (4 x 10 items) and 40 of the experiment cap 400. Outcomes: 18 answered (`ok`), 15 `http_503`, 7 `http_429`. Models that answered: `gemini-3.5-flash` 10, `gemini-3.1-flash-lite` 8. The cap was reached during the tenth case, which ended on rules with `call_cap_reached`.
- **No model report was accepted: 0 of 10 passed the checks, so every case below ended on the rules report.** Two causes were defects of the harness, not of the model, and are fixed in the commit that adds this document, with no further call: (1) the glossary was shown to the model as a list, so the model cited `glossary.0.definition`, which does not exist (16 `W1.evidence_path`); it is now an object keyed by term, so the path is `glossary.OPS`; (2) the definition check rejected "OPS is On-base plus slugging ..." (capital after "is") and the plain definition forms the model wrote (17 `W11.definition`); both capitalizations are accepted now.
- The other failures are the model's: `W1.entity` 9, `W1.number` 5, `W11.order` 5, `W10.cause` 3, `W1.no_evidence` 3, `W17.length` 2, `W15.form` 2, `W6.arsenal` 2, `W2.comparison` 2, and one each of `W14.starter`, `W14.team`, `W4.topic`, `W5.label`, `W17.structure`, `W1.evidence_value`. The counts are confounded by the two harness defects: a sentence with an invalid glossary path skipped its own content checks, and part of the retry feedback named the harness failures instead of the model's. They are not a clean estimate of the model's failure rate.
- The 40-call run cap was a binding limit here because 22 of 40 calls were 503/429 capacity failures. Nothing was re-run, because the run cap is spent and a re-run needs your decision.

## postseason-849842

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W1.entity', 'W2.comparison', 'W11.definition'], tokens {'promptTokenCount': 6391, 'candidatesTokenCount': 2212, 'totalTokenCount': 8603}
- Content attempt 2: transport path `primary_retry`, transport failures [('gemini-3.5-flash', 1, 'http_503')], model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W1.entity', 'W11.definition'], tokens {'promptTokenCount': 6485, 'candidatesTokenCount': 2923, 'totalTokenCount': 9408}
- Length: rules 2279 characters; shown text 2279 characters.

### Rules text (A)

**Headline**

Four-seam-Splitter starter against Four-seam-Curveball starter

**Short summary**

- Kevin Gausman brings this strength: Solid command supports strike-zone control.
- Nick Pivetta brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Kevin Gausman can land the splitter early in counts.

**Matchup Summary**

This matchup features Four-seam-Splitter starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 2 of the NL Wild Card Series. Before first pitch, SD leads 1-0.

**Kevin Gausman vs San Diego Padres**

Kevin Gausman works off a four-seam-splitter combination. He shows average swing-and-miss ability. He shows solid command. Kevin Gausman has allowed 26 home runs over 750 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.722 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Kevin Gausman needs efficient strikes.

**Nick Pivetta vs Chicago Cubs**

Nick Pivetta works off a four-seam-curveball combination. He shows above-average swing-and-miss ability. Control data for Nick Pivetta is limited (140 batters faced; 170 needed), so no command claim is made. Nick Pivetta has allowed 2 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.757 OPS), so Nick Pivetta cannot live over the middle. They draw walks at an above-average rate, so Nick Pivetta needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Splitter to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Kevin Gausman land the splitter early in counts?
- Can Nick Pivetta keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Kevin Gausman and Nick Pivetta: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W1.entity', 'W11.definition']

**Headline**

Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series.

**Short summary**

- This is Game 2 of the NL Wild Card Series.
- Before first pitch, SD leads 1-0.
- Kevin Gausman starts for CHC, and Nick Pivetta starts for SD.

**Matchup Summary**

This is Game 2 of the NL Wild Card Series. Before first pitch, SD leads 1-0. ERA is Earned run average: earned runs allowed per nine innings. Lower is better. Kevin Gausman has a 4.51 ERA over the 2026 regular season through Sep 29. Nick Pivetta has a 2.86 ERA over the 2026 regular season through Sep 29.

**Kevin Gausman vs San Diego Padres**

swing-and-miss is How often hitters swing and miss against him. command is How well a pitcher puts the ball where he wants it. Kevin Gausman shows Average swing-and-miss ability over the 2026 regular season through Sep 29. Kevin Gausman shows Solid command over the 2026 regular season through Sep 29. BB% is Share of plate appearances that end in a walk. San Diego Padres draws walks at a 9.4% BB% rate against right-handed pitchers over the 2026 regular season through Sep 29.

**Nick Pivetta vs Chicago Cubs**

Nick Pivetta shows Above-average swing-and-miss ability over the 2026 regular season through Sep 29. batters faced is The number of hitters a pitcher has pitched to. Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. Chicago Cubs has a .757 OPS against right-handed pitchers over the 2026 regular season through Sep 29.

**Arsenal Scout**

put-away pitch is In this report, the pitch he uses second most (at least 15% of his pitches). Kevin Gausman relies on his Four-seam as his primary pitch and Splitter as his put-away pitch. Nick Pivetta relies on his Four-seam as his primary pitch and Curveball as his put-away pitch. Nick Pivetta throws his Four-seam at 94.0 mph, which is faster than Kevin Gausman at 93.8 mph over the 2026 regular season.

**Three Things to Watch**

- Watch how often Kevin Gausman throws his Splitter.
- Watch whether Nick Pivetta uses his Curveball against Chicago Cubs.
- Watch how San Diego Padres handles Kevin Gausman and his Four-seam.

**Data Confidence Note**

limited sample is Too few pitches or batters faced for a reliable read; the packet says how many are needed. Kevin Gausman has full sample data across all tracked areas over the 2026 regular season through Sep 29. Control data for Nick Pivetta is limited with 140 batters faced out of 170 needed over the 2026 regular season through Sep 29.


## postseason-849849

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.no_evidence', 'W1.evidence_path', 'W1.number', 'W1.entity', 'W11.definition', 'W11.order'], tokens {'promptTokenCount': 6133, 'candidatesTokenCount': 3025, 'thoughtsTokenCount': 550, 'totalTokenCount': 9708}
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W17.structure'], tokens {'promptTokenCount': 6250, 'candidatesTokenCount': 2072, 'thoughtsTokenCount': 1167, 'totalTokenCount': 9489}
- Length: rules 2221 characters; shown text 2221 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Four-seam-Sweeper starter

**Short summary**

- Hagen Smith brings this strength: Above-average swing-and-miss ability.
- AJ Blubaugh brings this strength: Four-seam to set up, Sweeper to finish.
- The early what to watch is whether Hagen Smith can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Four-seam-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 1 of the AL Wild Card Series; the series has not started.

**Hagen Smith vs Houston Astros**

Hagen Smith works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Hagen Smith is limited (110 batters faced; 170 needed), so no command claim is made. Hagen Smith has allowed 1 home run over 110 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.713 OPS), with no glaring weakness to attack.

**AJ Blubaugh vs Chicago White Sox**

AJ Blubaugh works off a four-seam-sweeper combination. He shows average swing-and-miss ability. He shows below-average command. AJ Blubaugh has allowed 13 home runs over 401 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.716 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so AJ Blubaugh needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Hagen Smith land the slider early in counts?
- Can AJ Blubaugh keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Hagen Smith and AJ Blubaugh: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W17.structure']

**Headline**

AL Wild Card Series Game 1: Chicago White Sox at Houston Astros

**Short summary**

- This is Game 1 of the AL Wild Card Series.
- Hagen Smith starts for Chicago, while AJ Blubaugh starts for Houston.
- Both starters use a four-seam fastball to set up their approach.
- The White Sox and Astros lineups face their respective pitchers in this three-game series.

**Matchup Summary**

ERA is earned runs allowed per nine innings; lower is better. WHIP is walks plus hits per inning pitched; lower is better. Hagen Smith enters with a 1.29 ERA and a 0.96 WHIP for the 2026 regular season through Sep 28. AJ Blubaugh enters with a 3.66 ERA and a 1.23 WHIP for the 2026 regular season through Sep 28.

**Hagen Smith vs Houston Astros**

OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for; higher means a stronger lineup. The Houston Astros lineup has a .713 OPS against left-handed pitchers, for the 2026 regular season through Sep 28. Swing-and-miss is how often hitters swing and miss against him. Hagen Smith shows above-average swing-and-miss ability for the 2026 regular season through Sep 28.

**AJ Blubaugh vs Chicago White Sox**

The Chicago White Sox lineup has a .716 OPS against right-handed pitchers, for the 2026 regular season through Sep 28. Command is how well a pitcher puts the ball where he wants it. AJ Blubaugh shows below-average command for the 2026 regular season through Sep 28.

**Arsenal Scout**

Put-away pitch is the pitch he uses second most, at least 15% of his pitches. Hagen Smith uses a slider as his put-away pitch, throwing it 30.3% of the time. AJ Blubaugh uses a sweeper as his put-away pitch, throwing it 22.9% of the time. Break is total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin. The Smith slider moves 5.2 in. sideways and 3.5 in. down. The Blubaugh sweeper moves 11.9 in. sideways and 3.7 in. up.

**Three Things to Watch**

- Watch how often Hagen Smith uses his slider to finish sequences.
- Watch whether AJ Blubaugh encounters deep-count traffic given his below-average command.
- Watch how the Chicago lineup handles the sweeper from AJ Blubaugh.

**Data Confidence Note**

Limited sample is too few pitches or batters faced for a reliable read; the packet says how many are needed. Control data for Hagen Smith is limited: 110 batters faced, and 170 are needed for a read. There is not enough data yet to rate his command.


## opener-824280

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W11.order', 'W11.definition'], tokens {'promptTokenCount': 5918, 'candidatesTokenCount': 1998, 'totalTokenCount': 7916}
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W10.cause', 'W11.definition'], tokens {'promptTokenCount': 5985, 'candidatesTokenCount': 2307, 'totalTokenCount': 8292}
- Length: rules 2330 characters; shown text 2330 characters.

### Rules text (A)

**Headline**

Four-seam-Splitter starter against Sinker-Slider starter

**Short summary**

- Trey Yesavage brings this strength: Four-seam to set up, Splitter to finish.
- Brenan Hanifee brings this strength: Sinker to set up, Slider to finish.
- The early what to watch is whether Trey Yesavage can land the splitter early in counts.

**Matchup Summary**

This matchup features Four-seam-Splitter starter against Sinker-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Trey Yesavage vs Detroit Tigers**

Trey Yesavage works off a four-seam-splitter combination. Strikeout data for Trey Yesavage is limited (57 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Trey Yesavage is limited (57 batters faced; 170 needed), so no command claim is made. Trey Yesavage has allowed 0 home runs over 57 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.725 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Trey Yesavage needs efficient strikes.

**Brenan Hanifee vs Toronto Blue Jays**

Brenan Hanifee works off a sinker-slider combination. Strikeout data for Brenan Hanifee is limited (33 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Brenan Hanifee is limited (33 batters faced; 170 needed), so no command claim is made. Brenan Hanifee has allowed 1 home run over 33 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.701 OPS), with no glaring weakness to attack.

**Arsenal Scout**

The main contrast is Four-seam to set up, Splitter to finish versus Sinker to set up, Slider to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Trey Yesavage land the splitter early in counts?
- Can Brenan Hanifee keep the ball low?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Trey Yesavage and Brenan Hanifee: all pitcher figures cover the 2026 regular season through May 14. Team offense splits cover the 2026 regular season through May 14. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W10.cause', 'W11.definition']

**Headline**

Trey Yesavage faces Brenan Hanifee in a matchup between Toronto Blue Jays and Detroit Tigers.

**Short summary**

- Trey Yesavage brings a 0.68 ERA over 13.1 innings pitched.
- Brenan Hanifee holds a 1.08 ERA across 8.1 innings pitched.
- Detroit Tigers draws walks at an above-average rate against right-handed pitchers.

**Matchup Summary**

ERA is Earned run average: earned runs allowed per nine innings. Lower is better. WHIP is Walks plus hits per inning pitched. Lower is better. Trey Yesavage has a 0.68 ERA and a 1.35 WHIP for Toronto Blue Jays. Brenan Hanifee posts a 1.08 ERA and a 1.08 WHIP for Detroit Tigers.

**Trey Yesavage vs Detroit Tigers**

OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. batters faced is The number of hitters a pitcher has pitched to. limited sample is Too few pitches or batters faced for a reliable read; the packet says how many are needed. Trey Yesavage has faced 57 batters, which is a limited sample since 170 are needed for control. Detroit Tigers has a .725 OPS against right-handed pitchers over the 2026 regular season through May 14. Detroit Tigers draws walks at an above-average rate.

**Brenan Hanifee vs Toronto Blue Jays**

Brenan Hanifee has faced 33 batters, which is a limited sample where 170 are needed for control. Toronto Blue Jays posts a .701 OPS against right-handed pitchers over the 2026 regular season through May 14.

**Arsenal Scout**

put-away pitch is In this report, the pitch he uses second most (at least 15% of his pitches). Trey Yesavage throws his Four-seam pitch 48.6 percent of the time as his primary pitch. His put-away pitch is the Splitter, used 36.6 percent of the time. Brenan Hanifee relies on his Sinker 58.9 percent of the time as his primary pitch. His put-away pitch is the Slider, used 18.8 percent of the time.

**Three Things to Watch**

- Watch how often Trey Yesavage throws his Four-seam pitch.
- Watch whether Brenan Hanifee uses his Slider as his put-away pitch.
- Watch how Detroit Tigers fares against right-handed pitching.

**Data Confidence Note**

Lineup status is probable pitchers. Trey Yesavage has limited control data with 57 batters faced when 170 are needed. Brenan Hanifee has limited strikeout data with 33 batters faced when 70 are needed.


## opener-823769

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.no_evidence', 'W1.entity', 'W4.topic', 'W1.evidence_path', 'W11.definition', 'W14.team'], tokens {'promptTokenCount': 6334, 'candidatesTokenCount': 2092, 'thoughtsTokenCount': 1764, 'totalTokenCount': 10190}
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W10.cause', 'W11.definition'], tokens {'promptTokenCount': 6441, 'candidatesTokenCount': 3408, 'totalTokenCount': 9849}
- Length: rules 2325 characters; shown text 2325 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Four-seam-Changeup starter

**Short summary**

- Ryan Rolison brings this strength: Above-average swing-and-miss ability.
- Brandon Woodruff brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Ryan Rolison can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Four-seam-Changeup starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Ryan Rolison vs Milwaukee Brewers**

Ryan Rolison works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Ryan Rolison is limited (114 batters faced; 170 needed), so no command claim is made. Ryan Rolison has allowed 3 home runs over 114 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.682 OPS), which gives Ryan Rolison an edge if he gets ahead. They draw walks at an above-average rate, so Ryan Rolison needs efficient strikes.

**Brandon Woodruff vs Chicago Cubs**

Brandon Woodruff works off a four-seam-changeup combination. He shows above-average swing-and-miss ability. Control data for Brandon Woodruff is limited (140 batters faced; 170 needed), so no command claim is made. Brandon Woodruff has allowed 4 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Brandon Woodruff needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Changeup to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Ryan Rolison land the slider early in counts?
- Can Brandon Woodruff keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Ryan Rolison and Brandon Woodruff: all pitcher figures cover the 2026 regular season through Jun 27. Team offense splits cover the 2026 regular season through Jun 27. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W10.cause', 'W11.definition']

**Headline**

Ryan Rolison faces Brandon Woodruff in Milwaukee.

**Short summary**

- Ryan Rolison pitches for the Chicago Cubs against Brandon Woodruff for the Milwaukee Brewers.
- Both starters feature above-average swing-and-miss ability.
- Both lineups draw walks at an above-average rate.

**Matchup Summary**

ERA is Earned run average: earned runs allowed per nine innings. Lower is better. WHIP is Walks plus hits per inning pitched. Lower is better. For the 2026 regular season through Jun 27, Ryan Rolison posted a 1.82 ERA and a 1.11 WHIP over 29.2 innings. Over the same period, Brandon Woodruff posted a 3.00 ERA and a 0.89 WHIP over 36.0 innings.

**Ryan Rolison vs Milwaukee Brewers**

swing-and-miss is How often hitters swing and miss against him. Ryan Rolison has Above-average swing-and-miss ability. OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. The Milwaukee Brewers offense draws walks at an above-average rate and recorded a .682 OPS against left-handed pitchers for the 2026 regular season through Jun 27.

**Brandon Woodruff vs Chicago Cubs**

Brandon Woodruff shows Above-average swing-and-miss ability. The Chicago Cubs offense draws walks at an above-average rate and registered a .734 OPS against right-handed pitchers for the 2026 regular season through Jun 27.

**Arsenal Scout**

put-away pitch is In this report, the pitch he uses second most (at least 15% of his pitches). Ryan Rolison uses a Four-seam as his primary pitch and a Slider as his put-away pitch. His Four-seam averages 94.5 miles per hour and moves 2.0 in. sideways and 15.1 in. up compared with a pitch thrown without spin. Brandon Woodruff uses a Four-seam as his primary pitch and a Changeup as his put-away pitch. His Four-seam averages 92.0 miles per hour, which is slower than the 94.5 miles per hour Four-seam of Ryan Rolison.

**Three Things to Watch**

- Watch how often Ryan Rolison throws his Slider.
- Watch whether Brandon Woodruff relies on his Changeup against the Chicago Cubs lineup.
- Watch how often both lineups draw walks during the game.

**Data Confidence Note**

limited sample is Too few pitches or batters faced for a reliable read; the packet says how many are needed. batters faced is The number of hitters a pitcher has pitched to. command is How well a pitcher puts the ball where he wants it. Control data for Ryan Rolison is a limited sample with 114 batters faced, where 170 are needed for a read, so there is not enough data to rate his command. Control data for Brandon Woodruff is a limited sample with 140 batters faced, where 170 are needed for a read, so there is not enough data to rate his command.


## limited-823836

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.entity', 'W11.definition', 'W17.length'], tokens {'promptTokenCount': 6268, 'candidatesTokenCount': 1443, 'totalTokenCount': 7711}
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.evidence_path', 'W1.number', 'W11.order', 'W11.definition', 'W17.length'], tokens {'promptTokenCount': 6335, 'candidatesTokenCount': 2361, 'thoughtsTokenCount': 1727, 'totalTokenCount': 10423}
- Length: rules 2196 characters; shown text 2196 characters.

### Rules text (A)

**Headline**

Four-seam-Changeup starter against Sinker-Sweeper starter

**Short summary**

- George Klassen brings this strength: Four-seam to set up, Changeup to finish.
- Tyler Phillips brings this strength: Sinker to set up, Sweeper to finish.
- The early what to watch is whether George Klassen can land the changeup early in counts.

**Matchup Summary**

This matchup features Four-seam-Changeup starter against Sinker-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**George Klassen vs Miami Marlins**

George Klassen works off a four-seam-changeup combination. Strikeout data for George Klassen is limited (32 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for George Klassen is limited (32 batters faced; 170 needed), so no command claim is made. George Klassen has allowed 1 home run over 32 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack.

**Tyler Phillips vs Los Angeles Angels**

Tyler Phillips works off a sinker-sweeper combination. He shows below-average swing-and-miss ability. He shows average command. Tyler Phillips has allowed 11 home runs over 383 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.687 OPS), which gives Tyler Phillips an edge if he gets ahead. They also strike out often, which favors a swing-and-miss approach.

**Arsenal Scout**

The main contrast is Four-seam to set up, Changeup to finish versus Sinker to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can George Klassen land the changeup early in counts?
- Can Tyler Phillips keep the ball low?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. George Klassen and Tyler Phillips: all pitcher figures cover the 2026 regular season through Aug 6. Team offense splits cover the 2026 regular season through Aug 6. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W1.number', 'W11.order', 'W11.definition', 'W17.length']

**Headline**

George Klassen and the Los Angeles Angels face Tyler Phillips and the Miami Marlins at loanDepot park.

**Short summary**

- George Klassen starts for the Los Angeles Angels in this upcoming matchup.
- Tyler Phillips takes the mound for the Miami Marlins, carrying a 3.53 ERA.
- The Miami Marlins hold a .734 OPS against right-handed pitchers, compared to the .687 OPS of the Los Angeles Angels against right-handed pitchers.

**Matchup Summary**

ERA is earned run average: earned runs allowed per nine innings. Lower is better. WHIP is walks plus hits per inning pitched. Lower is better. OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. George Klassen has an 11.57 ERA and a 3.64 WHIP over 4.2 innings pitched, measured for the 2026 regular season through Aug 6. Tyler Phillips has a 3.53 ERA and a 1.35 WHIP over 89.1 innings pitched, for the same 2026 regular season through Aug 6.

**George Klassen vs Miami Marlins**

The Los Angeles Angels offense faces Tyler Phillips. K% is share of plate appearances that end in a strikeout. BB% is share of plate appearances that end in a walk. The Los Angeles Angels have a 24.9% K% and an 8.3% BB% against right-handed pitchers, through Aug 6. Tyler Phillips shows average command and below-average swing-and-miss ability.

**Tyler Phillips vs Los Angeles Angels**

The Miami Marlins offense faces George Klassen. Limited sample is too few pitches or batters faced for a reliable read; the packet says how many are needed. Batters faced is the number of hitters a pitcher has pitched to. Control and strikeout data for George Klassen are based on a limited sample of 32 batters faced, while 170 are required for a control read and 70 are required for a strikeout read. The Miami Marlins have a 21.0% K% and an 8.9% BB% against right-handed pitchers, through Aug 6.

**Arsenal Scout**

Break is total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin. George Klassen relies on a four-seam as his primary pitch and a changeup as his put-away pitch. Put-away pitch is in this report, the pitch he uses second most (at least 15% of his pitches). Klassen throws his four-seam at 96.8 mph, while the four-seam of Tyler Phillips averages 96.2 mph. Tyler Phillips uses a sinker as his primary pitch and a sweeper as his put-away pitch. The sweeper of Phillips moves 12.4 in. sideways and 1.1 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often George Klassen utilizes his four-seam to set up at-bats against the Marlins lineup.
- Watch whether Tyler Phillips relies on his sinker to set up hitters early in the count.
- Watch if the Los Angeles Angels lineup can generate contact against the pitching staff of Miami.

**Data Confidence Note**

Data for both pitchers is consistent with the 2026 regular season through Aug 6.


## limited-825104

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary_retry`, transport failures [('gemini-3.5-flash', 1, 'http_503')], model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W11.definition', 'W6.arsenal'], tokens {'promptTokenCount': 6064, 'candidatesTokenCount': 4379, 'thoughtsTokenCount': 44, 'totalTokenCount': 10487}
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W1.entity', 'W11.definition', 'W6.arsenal'], tokens {'promptTokenCount': 6136, 'candidatesTokenCount': 4163, 'thoughtsTokenCount': 958, 'totalTokenCount': 11257}
- Length: rules 2494 characters; shown text 2494 characters.

### Rules text (A)

**Headline**

Bryce Elder against Michael Soroka

**Short summary**

- Bryce Elder has no claimed strength because the data is limited.
- Michael Soroka has no claimed strength because the data is limited.
- The early what to watch is whether Bryce Elder can stay ahead of hitters early in counts.

**Matchup Summary**

This matchup features Bryce Elder against Michael Soroka. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Bryce Elder vs Arizona Diamondbacks**

Bryce Elder's arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Bryce Elder is limited (23 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Bryce Elder is limited (23 batters faced; 170 needed), so no command claim is made. Bryce Elder has allowed 0 home runs over 23 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.653 OPS), which gives Bryce Elder an edge if he gets ahead.

**Michael Soroka vs Atlanta Braves**

Michael Soroka's arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. Strikeout data for Michael Soroka is limited (20 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Michael Soroka is limited (20 batters faced; 170 needed), so no command claim is made. Michael Soroka has allowed 0 home runs over 20 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.827 OPS), so Michael Soroka cannot live over the middle. They draw walks at an above-average rate, so Michael Soroka needs efficient strikes.

**Arsenal Scout**

Bryce Elder's arsenal data is limited (83 pitches; 100 needed), so this report makes no arsenal claim for him. Michael Soroka's arsenal data is limited (89 pitches; 100 needed), so this report makes no arsenal claim for him. No arsenal contrast is drawn because at least one arsenal has too little data.

**Three Things to Watch**

- Can Bryce Elder stay ahead of hitters early in counts?
- Can Michael Soroka work efficiently through the lineup?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Bryce Elder and Michael Soroka: all pitcher figures cover the 2026 regular season through Apr 3. Team offense splits cover the 2026 regular season through Apr 3. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W1.entity', 'W11.definition', 'W6.arsenal']

**Headline**

Bryce Elder and Michael Soroka start as Atlanta Braves visit Arizona Diamondbacks at Chase Field.

**Short summary**

- Bryce Elder takes the mound for Atlanta Braves against Arizona Diamondbacks.
- Michael Soroka starts for Arizona Diamondbacks against Atlanta Braves.
- Both starters enter with limited sample sizes across control, strikeout, and arsenal metrics.

**Matchup Summary**

ERA is Earned run average: earned runs allowed per nine innings. Lower is better. WHIP is Walks plus hits per inning pitched. Lower is better. Bryce Elder has a 0.00 ERA and a 1.00 WHIP across 6.0 innings over the 2026 regular season through Apr 3. Michael Soroka has a 0.00 ERA and a 1.00 WHIP across 5.0 innings over the 2026 regular season through Apr 3.

**Bryce Elder vs Arizona Diamondbacks**

batters faced is The number of hitters a pitcher has pitched to. Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a read. Strikeout data for Bryce Elder is limited: 23 batters faced, and 70 are needed for a read. OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. Against right-handed pitchers, the Arizona Diamondbacks lineup has a .653 OPS over the 2026 regular season through Apr 3.

**Michael Soroka vs Atlanta Braves**

Control data for Michael Soroka is limited: 20 batters faced, and 170 are needed for a read. Strikeout data for Michael Soroka is limited: 20 batters faced, and 70 are needed for a read. Against right-handed pitchers, the Atlanta Braves lineup has a .827 OPS over the 2026 regular season through Apr 3.

**Arsenal Scout**

put-away pitch is In this report, the pitch he uses second most (at least 15% of his pitches). The primary pitch for Bryce Elder is his Sinker, and his put-away pitch is his Slider. The primary pitch for Michael Soroka is his Slurve, and his put-away pitch is his Four-seam. Arsenal data for Bryce Elder is limited: 83 pitches thrown, and 100 are needed for a full sample. Arsenal data for Michael Soroka is limited: 89 pitches thrown, and 100 are needed for a full sample.

**Three Things to Watch**

- Watch how often Bryce Elder relies on his Sinker against right-handed hitters.
- Watch whether Michael Soroka uses his Slurve against left-handed hitters.
- Watch how often Bryce Elder throws his Slider in two-strike counts.

**Data Confidence Note**

limited sample is Too few pitches or batters faced for a reliable read; the packet says how many are needed. Bryce Elder has a limited sample for control, strikeout, and arsenal metrics over the 2026 regular season through Apr 3. Michael Soroka has a limited sample for control, strikeout, and arsenal metrics over the 2026 regular season through Apr 3.


## limited-823863

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W11.definition'], tokens {'promptTokenCount': 6221, 'candidatesTokenCount': 2047, 'totalTokenCount': 8268}
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.number', 'W1.evidence_path', 'W15.form', 'W11.definition', 'W14.starter'], tokens {'promptTokenCount': 6274, 'candidatesTokenCount': 2689, 'thoughtsTokenCount': 1612, 'totalTokenCount': 10575}
- Length: rules 2060 characters; shown text 2060 characters.

### Rules text (A)

**Headline**

Four-seam-Splitter starter against Four-seam-Slider starter

**Short summary**

- Tobias Myers brings this strength: Four-seam to set up, Splitter to finish.
- Eury Pérez brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Tobias Myers can land the splitter early in counts.

**Matchup Summary**

This matchup features Four-seam-Splitter starter against Four-seam-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Tobias Myers vs Miami Marlins**

Tobias Myers works off a four-seam-splitter combination. He shows average swing-and-miss ability. Control data for Tobias Myers is limited (115 batters faced; 170 needed), so no command claim is made. Tobias Myers has allowed 5 home runs over 115 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.697 OPS), which gives Tobias Myers an edge if he gets ahead.

**Eury Pérez vs New York Mets**

Eury Pérez works off a four-seam-slider combination. He shows above-average swing-and-miss ability. He shows below-average command. Eury Pérez has allowed 10 home runs over 230 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.659 OPS), which gives Eury Pérez an edge if he gets ahead.

**Arsenal Scout**

The main contrast is Four-seam to set up, Splitter to finish versus Four-seam to set up, Slider to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Tobias Myers land the splitter early in counts?
- Can Eury Pérez keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Tobias Myers and Eury Pérez: all pitcher figures cover the 2026 regular season through May 21. Team offense splits cover the 2026 regular season through May 21. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.entity', 'W1.number', 'W1.evidence_path', 'W15.form', 'W11.definition', 'W14.starter']

**Headline**

Tobias Myers and the New York Mets visit Eury Perez and the Miami Marlins

**Short summary**

- Tobias Myers holds a 3.41 ERA through the 2026 regular season through May 21.
- Eury Perez carries a 5.33 ERA over the same period.
- The game features two right-handed starting pitchers at loanDepot park.

**Matchup Summary**

ERA is Earned run average: earned runs allowed per nine innings. Lower is better. Tobias Myers has a 3.41 ERA and 1.03 WHIP. WHIP is Walks plus hits per inning pitched. Lower is better. Eury Perez has a 5.33 ERA and 1.41 WHIP through the 2026 regular season through May 21.

**Tobias Myers vs Miami Marlins**

Tobias Myers faces the Miami Marlins. The Marlins lineup has a .697 OPS against right-handed pitchers. OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. limited sample is Too few pitches or batters faced for a reliable read; the packet says how many are needed. Control data for Tobias Myers is a limited sample: 115 batters faced, and 170 are needed for a read.

**Eury Pérez vs New York Mets**

Eury Perez faces the New York Mets. The Mets lineup has a .659 OPS against right-handed pitchers. swing-and-miss is How often hitters swing and miss against him. Perez shows above-average swing-and-miss ability. command is How well a pitcher puts the ball where he wants it. Perez shows below-average command.

**Arsenal Scout**

Tobias Myers throws a four-seam fastball at 92.6 mph and a splitter at 79.8 mph. Eury Perez throws a four-seam fastball at 98.1 mph and a slider at 87.6 mph. Break is Total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin. The four-seam fastball of Myers moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin. The four-seam fastball of Perez moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Tobias Myers uses his four-seam fastball as his primary pitch.
- Watch how often Eury Perez throws his slider as a put-away pitch.
- Watch if the Miami Marlins offense can generate offense against the control of Tobias Myers.

**Data Confidence Note**

Both starters are confirmed for this game.


## veteran-824027

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.no_evidence', 'W1.evidence_path', 'W5.label', 'W10.cause', 'W11.definition'], tokens {'promptTokenCount': 6425, 'candidatesTokenCount': 2294, 'totalTokenCount': 8719}
- Content attempt 2: transport path `fallback_retry`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429'), ('gemini-3.1-flash-lite', 1, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W2.comparison', 'W1.evidence_path', 'W1.number', 'W1.evidence_value', 'W11.order', 'W11.definition'], tokens {'promptTokenCount': 6547, 'candidatesTokenCount': 1765, 'thoughtsTokenCount': 2731, 'totalTokenCount': 11043}
- Length: rules 2048 characters; shown text 2048 characters.

### Rules text (A)

**Headline**

Four-seam-Curveball starter against Sinker-Curveball starter

**Short summary**

- Kyle Freeland brings this strength: Solid command supports strike-zone control.
- José Soriano brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Kyle Freeland can land the curveball early in counts.

**Matchup Summary**

This matchup features Four-seam-Curveball starter against Sinker-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Kyle Freeland vs Los Angeles Angels**

Kyle Freeland works off a four-seam-curveball combination. He shows average swing-and-miss ability. He shows solid command. Kyle Freeland has allowed 12 home runs over 202 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.712 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Kyle Freeland needs efficient strikes.

**José Soriano vs Colorado Rockies**

José Soriano works off a sinker-curveball combination. He shows above-average swing-and-miss ability. He shows below-average command. José Soriano has allowed 6 home runs over 289 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.709 OPS), with no glaring weakness to attack.

**Arsenal Scout**

The main contrast is Four-seam to set up, Curveball to finish versus Sinker to set up, Curveball to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Kyle Freeland land the curveball early in counts?
- Can José Soriano keep the ball low?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Kyle Freeland and José Soriano: all pitcher figures cover the 2026 regular season through May 31. Team offense splits cover the 2026 regular season through May 31.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.entity', 'W2.comparison', 'W1.evidence_path', 'W1.number', 'W1.evidence_value', 'W11.order', 'W11.definition']

**Headline**

Pitching Matchup: Kyle Freeland versus Jose Soriano

**Short summary**

- Kyle Freeland starts for Colorado at Angel Stadium.
- Jose Soriano takes the mound for Los Angeles.
- Both teams evaluate their pitchers' performance through May 31 of the 2026 season.

**Matchup Summary**

Kyle Freeland of the Colorado Rockies has a 8.08 ERA and a 1.75 WHIP in 42.1 innings. Jose Soriano of the Los Angeles Angels has a 2.65 ERA and a 1.15 WHIP in 71.1 innings. ERA is earned run average: earned runs allowed per nine innings. Lower is better. WHIP is walks plus hits per inning pitched. Lower is better.

**Kyle Freeland vs Los Angeles Angels**

Freeland has solid command. He shows average swing-and-miss ability. The Los Angeles lineup has a .712 OPS against left-handed pitchers, 2026 regular season through May 31. OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. The Angels draw walks at an above-average rate against left-handed pitchers.

**José Soriano vs Colorado Rockies**

Soriano has below-average command. He shows above-average swing-and-miss ability. The Colorado lineup has a .709 OPS against right-handed pitchers, 2026 regular season through May 31.

**Arsenal Scout**

Command is how well a pitcher puts the ball where he wants it. Freeland throws his four-seam fastball 26.4% of the time, averaging 91.3 mph. His put-away pitch is his curveball, thrown 22.5% of the time at 82.1 mph. Soriano throws his sinker 27.8% of the time, averaging 96.7 mph. His put-away pitch is his curveball, thrown 24.8% of the time at 85.6 mph. Break is total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Kyle Freeland uses his four-seam fastball to set up his curveball.
- Watch how often Jose Soriano uses his sinker in the strike zone.
- Watch whether the Los Angeles lineup can exploit the pitch counts of Colorado.

**Data Confidence Note**

Data for both starters covers the 2026 regular season through May 31.


## veteran-823938

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_503')], model `gemini-3.1-flash-lite`, checks ['W1.number', 'W1.evidence_path', 'W15.form', 'W11.order', 'W11.definition'], tokens {'promptTokenCount': 6220, 'candidatesTokenCount': 2100, 'thoughtsTokenCount': 481, 'totalTokenCount': 8801}
- Content attempt 2: transport path `primary_retry`, transport failures [('gemini-3.5-flash', 1, 'http_429')], model `gemini-3.5-flash`, checks ['W1.evidence_path', 'W11.definition'], tokens {'promptTokenCount': 6327, 'candidatesTokenCount': 1998, 'thoughtsTokenCount': 875, 'totalTokenCount': 9200}
- Length: rules 1970 characters; shown text 1970 characters.

### Rules text (A)

**Headline**

Sinker-Changeup starter against Four-seam-Cutter starter

**Short summary**

- Nick Martinez brings this strength: Solid command supports strike-zone control.
- Eric Lauer brings this strength: Four-seam to set up, Cutter to finish.
- The early what to watch is whether Nick Martinez can land the changeup early in counts.

**Matchup Summary**

This matchup features Sinker-Changeup starter against Four-seam-Cutter starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Nick Martinez vs Los Angeles Dodgers**

Nick Martinez works off a sinker-changeup combination. He shows below-average swing-and-miss ability. He shows solid command. Nick Martinez has allowed 6 home runs over 318 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.806 OPS), so Nick Martinez cannot live over the middle. They draw walks at an above-average rate, so Nick Martinez needs efficient strikes.

**Eric Lauer vs Tampa Bay Rays**

Eric Lauer works off a four-seam-cutter combination. He shows below-average swing-and-miss ability. He shows average command. Eric Lauer has allowed 15 home runs over 224 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.685 OPS), which gives Eric Lauer an edge if he gets ahead.

**Arsenal Scout**

The main contrast is Sinker to set up, Changeup to finish versus Four-seam to set up, Cutter to finish. The primary pitch contrast is Sinker against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Nick Martinez land the changeup early in counts?
- Can Eric Lauer keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Nick Martinez and Eric Lauer: all pitcher figures cover the 2026 regular season through Jun 14. Team offense splits cover the 2026 regular season through Jun 14.

### Model text (B1) (rejected; the last candidate, not published)

Failed checks: ['W1.evidence_path', 'W11.definition']

**Headline**

Nick Martinez faces Eric Lauer as Tampa Bay Rays play Los Angeles Dodgers.

**Short summary**

- Nick Martinez starts for Tampa Bay Rays.
- Eric Lauer starts for Los Angeles Dodgers.
- The game is at UNIQLO Field at Dodger Stadium.

**Matchup Summary**

ERA is Earned run average: earned runs allowed per nine innings. Lower is better. Nick Martinez has a 2.43 ERA over the 2026 regular season through Jun 14. Eric Lauer has a 5.47 ERA over the 2026 regular season through Jun 14.

**Nick Martinez vs Los Angeles Dodgers**

command is How well a pitcher puts the ball where he wants it. Nick Martinez shows Solid command. swing-and-miss is How often hitters swing and miss against him. Nick Martinez shows Below-average swing-and-miss ability. OPS is On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. Los Angeles Dodgers has a .806 OPS against right-handed pitchers over the 2026 regular season through Jun 14.

**Eric Lauer vs Tampa Bay Rays**

Eric Lauer shows Average command. Eric Lauer shows Below-average swing-and-miss ability. Tampa Bay Rays has a .685 OPS against left-handed pitchers over the 2026 regular season through Jun 14.

**Arsenal Scout**

put-away pitch is In this report, the pitch he uses second most (at least 15% of his pitches). Nick Martinez throws a Sinker as his primary pitch and a Changeup as his put-away pitch. Eric Lauer throws a Four-seam as his primary pitch and a Cutter as his put-away pitch. Nick Martinez throws a Sinker at 92.5 mph and a Four-seam at 92.7 mph. Eric Lauer throws a Four-seam at 90.7 mph and a Cutter at 86.8 mph.

**Three Things to Watch**

- Watch how often Nick Martinez throws his Sinker.
- Watch whether Eric Lauer uses his Cutter against Tampa Bay Rays hitters.
- Watch how often Eric Lauer relies on his Four-seam pitch.

**Data Confidence Note**

Lineups are listed as probable pitchers. Nick Martinez has faced 318 batters faced over the 2026 regular season through Jun 14. Eric Lauer has faced 224 batters faced over the 2026 regular season through Jun 14.


## veteran-824803

- Path: **rules** (reason: `call_cap_reached`); content attempts: 1
- Content attempt 1: transport path `rules`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429'), ('gemini-3.1-flash-lite', 1, 'call_cap_reached')], model `-`, checks not reached, tokens -
- Length: rules 2179 characters; shown text 2179 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Four-seam-Curveball starter

**Short summary**

- Carlos Rodón brings this strength: Above-average swing-and-miss ability.
- Shane Baz brings this strength: Four-seam to set up, Curveball to finish.
- The early what to watch is whether Carlos Rodón can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Carlos Rodón vs Baltimore Orioles**

Carlos Rodón works off a four-seam-slider combination. He shows above-average swing-and-miss ability. He shows below-average command. Carlos Rodón has allowed 3 home runs over 194 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.723 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Carlos Rodón needs efficient strikes.

**Shane Baz vs New York Yankees**

Shane Baz works off a four-seam-curveball combination. He shows average swing-and-miss ability. He shows average command. Shane Baz has allowed 10 home runs over 598 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.713 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Shane Baz needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Carlos Rodón land the slider early in counts?
- Can Shane Baz keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Carlos Rodón and Shane Baz: all pitcher figures cover the 2026 regular season through Aug 17. Team offense splits cover the 2026 regular season through Aug 17.

### Model text (B1) (rejected; the last candidate, not published)

No model text: the call never produced a usable answer.

