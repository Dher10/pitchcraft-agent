# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest `55fb2a171f8e8b5b09c8f24c02e73c27a522f0efd6d8aaecc7b42a5323be46d3`, prompt `p2.2-2`. Nothing here is published; rules stay live.

Gemini HTTP calls: run 55 of 80, experiment 95 of 400.
Capacity failures (503/429) in this run: 35 of 55 finished calls.
Run started 2026-10-30 15:22 local (2026-10-30 20:22 UTC), finished 2026-10-30 15:27 local.
More than a third of the calls failed on capacity; time of day of the run: 2026-10-30 15:22 to 2026-10-30 15:27 local (America/Bogota (UTC-5)).
Paths: primary 0, primary_retry 0, fallback 0, fallback_retry 0, rules 10. LLM coverage 0/10; not written by the primary model 10/10 (a fallback or rules result is not a primary first-attempt success).


## Run 2 summary (read first)

- **Result:** 0 of 10 accepted; all ten ended on the rules report (`checks_failed`). Run 1 (guide 0.2) also ended 0 of 10; the numbers below are new evidence, not a repeat. The run used prompt `p2.2-1`; the next prompt version is `p2.2-2` (see the lineup-note fix below).
- **Gemini calls:** run 55 of the run cap 80; experiment 95 of 400 (40 in run 1). Outcomes of the 55: 20 answered, 33 `http_429`, 2 `http_503`. **All 33 `http_429` and both `http_503` were on the primary `gemini-3.5-flash`**, which answered 3 of its 38 calls; the fallback `gemini-3.1-flash-lite` answered 17 of 17. So 8 of the 10 texts shown below are fallback text, which is not a Gemini primary B1 result (the two primary-model texts shown are `postseason-849842` and `postseason-849849`); each case names the model of the text it shows. Tokens: about 10,950 per answered call (about 7,100 in).
- **Capacity:** 35 of 55 calls (64%) failed on capacity, more than a third. Time of day: 15:22 to 15:27 local (America/Bogota, UTC-5), that is 20:22 to 20:27 UTC, about 11 calls per minute. A 429 is a rate or quota limit, not the overload a 503 means; run 1 (earlier the same day) had 15 `http_503` and 7 `http_429`. The free-tier limits of the primary model are not published, so I cannot say whether this was the per-minute or the daily limit.
- **What the checks found (162 failures over 20 candidates):** `W1.evidence_path` 34, `W11.expansion` 28, `W1.entity` 23, `W1.number` 21, `W1.evidence_value` 12, `W2.comparison` 8, `W8.form` 6, `W10.cause` 5, `W1.no_evidence` 5, `W15.form` 4, `W12.time` 3, `W17.structure` 3, and 2 or fewer each of `W5.label`, `W3.prediction`, `W11.repeat`, `W12.repeat`, `W6.arsenal`, `W17.length`. Many are our rules being rigid or our input being awkward, not the model being wrong; see `docs/writer-guide-0.4-proposal.md`, part A.
- **Harness defect found and fixed after the run (no further call):** the lineup notes were a list, so the natural citation `findings.lineup_notes.home` pointed at no value (15 of the 34 `W1.evidence_path`). It is now one string per side; prompt version `p2.2-2`.
- **What is shown per case:** the model candidate with the fewest failed checks (a later attempt wins a tie), labelled with its attempt number and model. Every phrase quoted in a readability note is checked by code against the text shown; the document cannot be built if a quote is missing.
- **A caution on what is shown:** "fewest failed checks" counts a `W17.structure` failure as one check, so it can prefer a candidate whose other checks never ran (`postseason-849842`, `limited-825104`, `limited-823863`). The heading of each case names the checks of the text shown.
- **Readability verdicts (per case below):** better 5, mixed 3, not better 2. Better: `limited-823836`, `opener-823769`, `opener-824280`, `postseason-849842`, `postseason-849849`. Mixed: `limited-825104`, `limited-823863`, `veteran-824803`. Not better: `veteran-824027`, `veteran-823938`. Common weaknesses of the model text: the scope repeated, stat runs of the same shape, filler sentences, title-case headlines and words such as "utilizes". They are the subject of the guide 0.4 proposals.


## postseason-849842

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.entity', 'W10.cause'], tokens {'candidatesTokenCount': 2164, 'promptTokenCount': 7247, 'totalTokenCount': 9411}
  - `W1.entity` token `Sep` in: Kevin Gausman has a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 29.
  - `W1.entity` token `Sep` in: Nick Pivetta has a 2.86 ERA and a 1.01 WHIP over the 2026 regular season through Sep 29.
  - `W1.entity` token `Sep` in: Kevin Gausman relies on his Four-seam at 50.6% and Splitter at 39.2% over the 2026 regular season through Sep 29.
  - `W10.cause` token `due to` in: Control metrics for Nick Pivetta are limited due to a sample of 140 batters faced compared to the required 170.
- Content attempt 2: transport path `primary_retry`, transport failures [('gemini-3.5-flash', 1, 'http_429')], model `gemini-3.5-flash`, checks ['W17.structure'], tokens {'candidatesTokenCount': 2237, 'promptTokenCount': 7287, 'totalTokenCount': 9524}
  - `W17.structure` token `None` in: (whole report)
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.5-flash`, checks ['W17.structure']

**Headline**

Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series

**Short summary**

- This is Game 2 of the NL Wild Card Series.
- Before first pitch, SD leads 1-0.
- Kevin Gausman starts for Chicago against Nick Pivetta for San Diego.

**Matchup Summary**

Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 29. Nick Pivetta has a 2.86 ERA and a 1.01 WHIP in that same span. This is Game 2 of the NL Wild Card Series, and SD leads 1-0 before first pitch.

**Kevin Gausman vs San Diego Padres**

Kevin Gausman shows solid command and average swing-and-miss ability over the 2026 regular season through Sep 29. The San Diego Padres offense has a .722 OPS (on-base plus slugging) against right-handed pitchers like him. Their K% (strikeout rate) is 21.5% and their BB% (walk rate) is 9.4% in that matchup. San Diego draws walks at an above-average rate.

**Nick Pivetta vs Chicago Cubs**

Nick Pivetta shows above-average swing-and-miss ability over the 2026 regular season through Sep 29. Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. The Chicago Cubs lineup has a .757 OPS against right-handed pitchers. Their strikeout rate is 21.2% and their walk rate is 10.6% in that split. Chicago has strong OPS against this pitcher's hand and draws walks at an above-average rate.

**Arsenal Scout**

Kevin Gausman relies on his Four-seam as his primary pitch (50.6%) and Splitter as his put-away pitch (second most used pitch) at 39.2%. His Four-seam reaches 93.8 mph velocity and his Splitter reaches 84.0 mph velocity. Nick Pivetta throws his Four-seam at 52.2% and Curveball at 22.1%. His Four-seam averages 94.0 mph, and his Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Kevin Gausman throws his Splitter against San Diego hitters.
- Watch how Nick Pivetta uses his Curveball in key counts.
- Watch whether the Chicago lineup draws walks against Nick Pivetta.

**Data Confidence Note**

The lineup status for this game is listed as probable pitchers.

### Readability for a casual fan

Verdict: better. The model text puts the series situation in the headline and the first lines, says who starts for which team and keeps the figures in sentences, where the rules text uses template lines ("works off a four-seam-splitter combination", "The scouting note is matchup fit"). Weakness: the Game 2 and standing sentence appears twice (summary lines and body) and the scope is repeated in each section.


## postseason-849849

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.number', 'W1.entity', 'W1.evidence_path', 'W11.expansion'], tokens {'candidatesTokenCount': 2453, 'promptTokenCount': 6988, 'thoughtsTokenCount': 1481, 'totalTokenCount': 10922}
  - `W1.number` token `1` in: AL Wild Card Series: Smith and Blubaugh Start Game 1
  - `W1.entity` token `Blubaugh Start Game` in: AL Wild Card Series: Smith and Blubaugh Start Game 1
  - `W1.entity` token `Sep` in: Hagen Smith carries a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning) through the 2026 regular season through Sep 28.
  - `W1.entity` token `Sep` in: Hagen Smith faces a Houston lineup that has a .713 OPS (on-base plus slugging) against left-handed pitchers in the 2026 regular season through Sep 28.
  - `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Control data for Smith is limited: 110 batters faced, and 170 are needed for a read, and there is not enough data yet to rate his command.
  - `W1.entity` token `Sep` in: AJ Blubaugh faces a Chicago White Sox lineup that posts a .716 OPS against right-handed pitchers in the 2026 regular season through Sep 28.
  - `W1.entity` token `Sep` in: Hagen Smith uses a four-seam as his primary pitch, which averages 93.8 mph in the 2026 regular season through Sep 28.
  - `W1.entity` token `Sep` in: This report uses data from the 2026 regular season through Sep 28.
  - `W11.expansion` token `put-away pitch` in: Watch how often AJ Blubaugh relies on his sweeper as a put-away pitch with his below-average command.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.5-flash`, checks ['W1.entity', 'W1.number', 'W2.comparison', 'W1.evidence_value'], tokens {'candidatesTokenCount': 4420, 'promptTokenCount': 7087, 'totalTokenCount': 11507}
  - `W1.entity` token `Hagen Smith Faces AJ Blubaugh` in: Hagen Smith Faces AJ Blubaugh in AL Wild Card Series Game 1
  - `W1.entity` token `Sep` in: Over the 2026 regular season through Sep 28, Smith has pitched 28.0 innings.
  - `W1.entity` token `Sep` in: Hagen Smith shows above-average swing-and-miss ability over the 2026 regular season through Sep 28.
  - `W1.entity` token `Sep` in: AJ Blubaugh demonstrates average swing-and-miss ability and below-average command over the 2026 regular season through Sep 28.
  - `W1.number` token `2026` in: Smith uses the Four-seam as his primary pitch at 48.4% and the Slider as his put-away pitch (second most used pitch) at 30.3% over the 2026 regular season through Sep 28.
  - `W1.number` token `28` in: Smith uses the Four-seam as his primary pitch at 48.4% and the Slider as his put-away pitch (second most used pitch) at 30.3% over the 2026 regular season through Sep 28.
  - `W1.entity` token `Sep` in: Smith uses the Four-seam as his primary pitch at 48.4% and the Slider as his put-away pitch (second most used pitch) at 30.3% over the 2026 regular season through Sep 28.
  - `W2.comparison` token `faster` in: His Four-seam is faster than Smith's Four-seam, reaching 95.8 miles per hour.
  - `W1.evidence_value` token `starters.home_starter.name` in: Watch how the Chicago lineup handles Blubaugh's Four-seam fastball.
  - `W1.entity` token `Sep` in: Data for this report comes from probable pitchers listed for the 2026 regular season through Sep 28.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.5-flash`, checks ['W1.entity', 'W1.number', 'W2.comparison', 'W1.evidence_value']

**Headline**

Hagen Smith Faces AJ Blubaugh in AL Wild Card Series Game 1

**Short summary**

- This is Game 1 of the AL Wild Card Series.
- Hagen Smith brings an ERA (earned run average) of 1.29 and a WHIP (walks plus hits per inning) of 0.96 for Chicago.
- AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP for Houston.

**Matchup Summary**

This match features Hagen Smith for CWS and AJ Blubaugh for HOU in Game 1 of the AL Wild Card Series. Over the 2026 regular season through Sep 28, Smith has pitched 28.0 innings. Over the same period, Blubaugh has thrown 96.0 innings.

**Hagen Smith vs Houston Astros**

Hagen Smith shows above-average swing-and-miss ability over the 2026 regular season through Sep 28. Control data for Smith is limited with 110 batters faced when 170 are needed for a read. The Houston Astros lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers. That offense carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate).

**AJ Blubaugh vs Chicago White Sox**

AJ Blubaugh demonstrates average swing-and-miss ability and below-average command over the 2026 regular season through Sep 28. The Chicago White Sox offense has a .716 OPS, a 24.1% K%, and a 9.4% BB% against right-handed pitchers. Chicago draws walks at an above-average rate and has elevated swing-and-miss risk.

**Arsenal Scout**

Smith uses the Four-seam as his primary pitch at 48.4% and the Slider as his put-away pitch (second most used pitch) at 30.3% over the 2026 regular season through Sep 28. His Four-seam averages 93.8 miles per hour, and his Slider averages 83.1 miles per hour. Blubaugh features a Four-seam primary pitch at 51.4% and a Sweeper put-away pitch at 22.9%. His Four-seam is faster than Smith's Four-seam, reaching 95.8 miles per hour. Blubaugh's Sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Hagen Smith relies on his Slider against right-handed hitters.
- Watch whether AJ Blubaugh utilizes his Sweeper against the White Sox lineup.
- Watch how the Chicago lineup handles Blubaugh's Four-seam fastball.

**Data Confidence Note**

Data for this report comes from probable pitchers listed for the 2026 regular season through Sep 28. Hagen Smith has pitched 28.0 innings across 110 batters faced. AJ Blubaugh has logged 96.0 innings across 401 batters faced.

### Readability for a casual fan

Verdict: better. It opens with the Game 1 framing ("This is Game 1 of the AL Wild Card Series.") and says the limited control read once with its numbers ("Control data for Smith is limited with 110 batters faced when 170 are needed for a read."), where the rules text repeats its limited-data sentences in internal wording. Weaknesses: the scope is stated in five places, the confidence note is awkward ("Data for this report comes from probable pitchers listed for the 2026 regular season through Sep 28."), "utilizes" and a title-case headline.


## opener-824280

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.number', 'W1.evidence_path', 'W1.entity', 'W10.cause', 'W11.expansion'], tokens {'candidatesTokenCount': 2937, 'promptTokenCount': 6772, 'thoughtsTokenCount': 2116, 'totalTokenCount': 11825}
  - `W1.number` token `two` in: This matchup in Detroit features two starting pitchers in the early part of the 2026 regular season through May 14.
  - `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Data on Trey Yesavage is limited with 57 batters faced; 170 are required for a full control read and 70 for a strikeout read.
  - `W1.evidence_path` token `starters.away_starter.thresholds.strikeout` in: Data on Trey Yesavage is limited with 57 batters faced; 170 are required for a full control read and 70 for a strikeout read.
  - `W1.evidence_path` token `starters.home_starter.thresholds.control` in: Data on Brenan Hanifee is limited with 33 batters faced; 170 are required for a full control read and 70 for a strikeout read.
  - `W1.evidence_path` token `starters.home_starter.thresholds.strikeout` in: Data on Brenan Hanifee is limited with 33 batters faced; 170 are required for a full control read and 70 for a strikeout read.
  - `W1.evidence_path` token `pitch_mix.3.home_starter.pitch` in: Watch how Brenan Hanifee balances his sinker and slider usage.
  - `W1.evidence_path` token `pitch_mix.2.home_starter.pitch` in: Watch how Brenan Hanifee balances his sinker and slider usage.
  - `W1.entity` token `Statistical` in: Statistical readings for these starters are limited due to a small number of batters faced.
  - `W10.cause` token `due to` in: Statistical readings for these starters are limited due to a small number of batters faced.
  - `W11.expansion` token `ERA` in: Trey Yesavage starts for the Toronto Blue Jays with a 0.68 ERA.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.no_evidence', 'W1.number', 'W1.evidence_path', 'W11.expansion'], tokens {'candidatesTokenCount': 2191, 'promptTokenCount': 6881, 'thoughtsTokenCount': 3143, 'totalTokenCount': 12215}
  - `W1.no_evidence` token `None` in: Both pitchers show specific pitch preferences to handle lineups.
  - `W1.number` token `2026` in: Trey Yesavage has a 0.68 ERA (earned run average) and a 1.35 walks plus hits per inning (WHIP) for the 2026 regular season through May 14.
  - `W1.number` token `14` in: Trey Yesavage has a 0.68 ERA (earned run average) and a 1.35 walks plus hits per inning (WHIP) for the 2026 regular season through May 14.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: This group draws walks at an above-average rate.
  - `W1.number` token `2026` in: Trey Yesavage uses a four-seam fastball at 48.6% and a splitter as his put-away pitch (second most used pitch) at 36.6% for the 2026 regular season through May 14.
  - `W1.number` token `14` in: Trey Yesavage uses a four-seam fastball at 48.6% and a splitter as his put-away pitch (second most used pitch) at 36.6% for the 2026 regular season through May 14.
  - `W1.no_evidence` token `None` in: Watch how often Trey Yesavage throws his four-seam fastball.
  - `W1.no_evidence` token `None` in: Watch how the Detroit lineup approach develops against right-handed pitches.
  - `W1.no_evidence` token `None` in: Watch how often Brenan Hanifee uses his sinker.
  - `W11.expansion` token `ERA` in: Trey Yesavage records a 0.68 earned run average (ERA) for the Toronto Blue Jays.
  - `W11.expansion` token `WHIP` in: Trey Yesavage has a 0.68 ERA (earned run average) and a 1.35 walks plus hits per inning (WHIP) for the 2026 regular season through May 14.
  - `W11.expansion` token `OPS` in: The Detroit offense enters with a .725 on-base plus slugging (OPS) against right-handed pitchers.
  - `W11.expansion` token `K%` in: Their strikeout rate (K%) is 22.3% and their walk rate (BB%) is 9.0% in that split.
  - `W11.expansion` token `BB%` in: Their strikeout rate (K%) is 22.3% and their walk rate (BB%) is 9.0% in that split.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, checks ['W1.no_evidence', 'W1.number', 'W1.evidence_path', 'W11.expansion']

**Headline**

Toronto Blue Jays starter Trey Yesavage faces Detroit Tigers starter Brenan Hanifee

**Short summary**

- Trey Yesavage records a 0.68 earned run average (ERA) for the Toronto Blue Jays.
- Brenan Hanifee brings a 1.08 ERA to the mound for the Detroit Tigers.
- The Detroit offense enters with a .725 on-base plus slugging (OPS) against right-handed pitchers.

**Matchup Summary**

Trey Yesavage starts for the Toronto Blue Jays for the 2026 regular season through May 14. Brenan Hanifee represents the Detroit Tigers in the same period. Both pitchers show specific pitch preferences to handle lineups.

**Trey Yesavage vs Detroit Tigers**

Trey Yesavage has a 0.68 ERA (earned run average) and a 1.35 walks plus hits per inning (WHIP) for the 2026 regular season through May 14. The Detroit Tigers offense carries a .725 OPS (on-base plus slugging) against right-handed pitchers. Their strikeout rate (K%) is 22.3% and their walk rate (BB%) is 9.0% in that split. This group draws walks at an above-average rate.

**Brenan Hanifee vs Toronto Blue Jays**

Brenan Hanifee maintains a 1.08 ERA and a 1.08 WHIP over the 2026 regular season through May 14. The Toronto Blue Jays lineup records a .701 OPS against right-handed pitchers. This offense shows an 18.2% K% and a 7.3% BB% against right-handed pitching.

**Arsenal Scout**

Trey Yesavage uses a four-seam fastball at 48.6% and a splitter as his put-away pitch (second most used pitch) at 36.6% for the 2026 regular season through May 14. The four-seam fastball moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. The splitter moves 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin. Brenan Hanifee features a sinker at 58.9% and a slider as his put-away pitch at 18.8%. The sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin. The slider moves 1.7 in. sideways and 2.8 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Trey Yesavage throws his four-seam fastball.
- Watch how the Detroit lineup approach develops against right-handed pitches.
- Watch how often Brenan Hanifee uses his sinker.

**Data Confidence Note**

Control and strikeout data for Trey Yesavage are limited with 57 batters faced. 170 batters faced are required for a control read and 70 for a strikeout read. Control and strikeout data for Brenan Hanifee are limited with 33 batters faced. 170 batters faced are required for a control read and 70 for a strikeout read.

### Readability for a casual fan

Verdict: better, not yet good. It is easier to follow than the rules text (who pitches for whom, what each lineup does) but the short forms make it clumsy ("1.35 walks plus hits per inning (WHIP)", "a splitter as his put-away pitch (second most used pitch)"), and the figures arrive in dense runs. The rules text is template sentences and the repeated "no ... claim is made" lines.


## opener-823769

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.number', 'W1.no_evidence', 'W1.evidence_path', 'W1.evidence_value', 'W15.form'], tokens {'candidatesTokenCount': 2158, 'promptTokenCount': 7187, 'thoughtsTokenCount': 1860, 'totalTokenCount': 11205}
  - `W1.number` token `two` in: Ryan Rolison takes the mound for Chicago against Brandon Woodruff in a matchup of two starters with above-average swing-and-miss ability.
  - `W1.no_evidence` token `None` in: Both lineups enter this game looking to overcome the starting pitching opposition.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: That group shows a 10.3% BB% (walk rate) and a 21.8% K% (strikeout rate), and the lineup notes indicate it draws walks at an above-average rate.
  - `W1.evidence_path` token `findings.lineup_notes.away` in: That group shows a 11.4% BB% and a 21.2% K%, and the lineup notes indicate it draws walks at an above-average rate.
  - `W1.evidence_path` token `pitch_mix.0.away_starter.pitch` in: Ryan Rolison primarily throws a four-seam fastball at 94.5 mph, which is faster than Brandon Woodruff's four-seam fastball at 92.0 mph.
  - `W1.evidence_value` token `velocity_by_pitch.2.away_starter_velocity` in: Ryan Rolison primarily throws a four-seam fastball at 94.5 mph, which is faster than Brandon Woodruff's four-seam fastball at 92.0 mph.
  - `W1.evidence_value` token `velocity_by_pitch.2.home_starter_velocity` in: Ryan Rolison primarily throws a four-seam fastball at 94.5 mph, which is faster than Brandon Woodruff's four-seam fastball at 92.0 mph.
  - `W15.form` token `Watch if both teams ` in: Watch if both teams maintain their walk rates during the game.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_503'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.evidence_path', 'W8.form'], tokens {'candidatesTokenCount': 2989, 'promptTokenCount': 7292, 'thoughtsTokenCount': 1868, 'totalTokenCount': 12149}
  - `W1.evidence_path` token `findings.lineup_notes.away` in: The Milwaukee Brewers and Chicago Cubs lineups show a shared tendency to work counts for walks.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: The Milwaukee Brewers and Chicago Cubs lineups show a shared tendency to work counts for walks.
  - `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Control data for Ryan Rolison is limited: 114 batters faced, and 170 are needed for a read.
  - `W1.evidence_path` token `starters.home_starter.thresholds.control` in: Control data for Brandon Woodruff is limited: 140 batters faced, and 170 are needed for a read.
  - `W8.form` token `None` in: His four-seam fastball moves 4.6 in. sideways compared with a pitch thrown without spin, and 18.1 in. up.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, checks ['W1.evidence_path', 'W8.form']

**Headline**

Ryan Rolison and Brandon Woodruff face off in Milwaukee

**Short summary**

- Ryan Rolison leads the Chicago Cubs against Brandon Woodruff of the Milwaukee Brewers.
- Both starters exhibit above-average swing-and-miss ability.
- Each lineup enters this matchup drawing walks at an above-average rate.

**Matchup Summary**

Ryan Rolison and Brandon Woodruff face off in this pitching duel over the 2026 regular season through Jun 27. Both pitchers possess above-average swing-and-miss ability according to their profiles. The Milwaukee Brewers and Chicago Cubs lineups show a shared tendency to work counts for walks.

**Ryan Rolison vs Milwaukee Brewers**

Ryan Rolison brings a 1.82 ERA (earned run average) and 1.11 WHIP (walks plus hits per inning) into this game over the 2026 regular season through Jun 27. Milwaukee faces him with a .682 OPS (on-base plus slugging). That lineup has a 21.8% K% (strikeout rate) and 10.3% BB% (walk rate) against left-handed pitchers. Control data for Ryan Rolison is limited: 114 batters faced, and 170 are needed for a read.

**Brandon Woodruff vs Chicago Cubs**

Brandon Woodruff carries a 3.00 ERA and 0.89 WHIP over the 2026 regular season through Jun 27. The Chicago lineup features a .734 OPS against right-handed pitchers. Their stats include a 21.2% K% and 11.4% BB%. Control data for Brandon Woodruff is limited: 140 batters faced, and 170 are needed for a read.

**Arsenal Scout**

Ryan Rolison uses a four-seam fastball 44.8% of the time and a slider 19.9% of the time over the 2026 regular season through Jun 27. His four-seam fastball moves 2.0 in. sideways and 15.1 in. up compared with a pitch thrown without spin. Brandon Woodruff relies on a four-seam fastball 43.9% of the time and a changeup 19.8% of the time. His four-seam fastball moves 4.6 in. sideways compared with a pitch thrown without spin, and 18.1 in. up.

**Three Things to Watch**

- Watch whether Ryan Rolison can maintain his control with his limited data sample.
- Watch how Brandon Woodruff utilizes his changeup against the Chicago Cubs.
- Watch how the lineups handle the above-average swing-and-miss ability of each starter.

**Data Confidence Note**

The lineup status is based on probable pitchers.

### Readability for a casual fan

Verdict: better, clearly. The rules text contains the empty line "The primary pitch contrast is Four-seam against Four-seam"; the model text names the teams, the duel and what each lineup tends to do. Weak spots: "possess" wording, a repeated scope phrase and a watch item that restates a label.


## limited-823836

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.evidence_path', 'W1.number', 'W15.form'], tokens {'candidatesTokenCount': 1770, 'promptTokenCount': 7124, 'thoughtsTokenCount': 1480, 'totalTokenCount': 10374}
  - `W1.evidence_path` token `season_summary.era` in: George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - `W1.evidence_path` token `season_summary.whip` in: George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - `W1.evidence_path` token `season_summary.scopes.counts.label` in: George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - `W1.evidence_path` token `season_summary.era` in: Tyler Phillips carries a 3.53 ERA and a 1.35 WHIP through the same period.
  - `W1.evidence_path` token `season_summary.whip` in: Tyler Phillips carries a 3.53 ERA and a 1.35 WHIP through the same period.
  - `W1.evidence_path` token `season_summary.scopes.season_rates.label` in: Tyler Phillips carries a 3.53 ERA and a 1.35 WHIP through the same period.
  - `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Control and strikeout data for George Klassen are limited: 32 batters faced, where 170 are needed for a control read and 70 are needed for a strikeout read.
  - `W1.evidence_path` token `starters.away_starter.thresholds.strikeout` in: Control and strikeout data for George Klassen are limited: 32 batters faced, where 170 are needed for a control read and 70 are needed for a strikeout read.
  - `W1.evidence_path` token `findings.lineup_notes.away` in: The group carries an elevated swing-and-miss risk.
  - `W1.number` token `6` in: George Klassen uses his Four-seam fastball 38.6% of the time and his Changeup 24.8% of the time, measured through Aug 6, 2026.
  - `W1.number` token `2026` in: George Klassen uses his Four-seam fastball 38.6% of the time and his Changeup 24.8% of the time, measured through Aug 6, 2026.
  - `W15.form` token `Watch if Tyler Phill` in: Watch if Tyler Phillips uses his Sinker to control the zone against the Los Angeles lineup.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.number', 'W2.comparison', 'W10.cause', 'W12.time', 'W8.form', 'W1.evidence_path'], tokens {'candidatesTokenCount': 2195, 'promptTokenCount': 7195, 'thoughtsTokenCount': 2365, 'totalTokenCount': 11755}
  - `W1.entity` token `A Right-Handed Pitching Duel` in: A Right-Handed Pitching Duel in Miami
  - `W1.number` token `7` in: George Klassen and Tyler Phillips prepare for their start on Aug 7, 2026, over the 2026 regular season through Aug 6.
  - `W1.number` token `two` in: The two right-handers look to set the tempo against their opposing lineups.
  - `W1.number` token `2026` in: George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) during the 2026 regular season through Aug 6.
  - `W1.number` token `6` in: George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) during the 2026 regular season through Aug 6.
  - `W2.comparison` token `fewer` in: He has faced 32 batters so far, but because he has faced fewer than the 170 batters required for a control reading and the 70 required for a strikeout reading, his command and strikeout data remain limited.
  - `W10.cause` token `so` in: He has faced 32 batters so far, but because he has faced fewer than the 170 batters required for a control reading and the 70 required for a strikeout reading, his command and strikeout data remain limited.
  - `W12.time` token `so far` in: He has faced 32 batters so far, but because he has faced fewer than the 170 batters required for a control reading and the 70 required for a strikeout reading, his command and strikeout data remain limited.
  - `W1.number` token `2026` in: The Miami Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the same 2026 regular season period.
  - `W12.time` token `this season` in: The Los Angeles Angels offense produces a .687 OPS when facing right-handed pitchers this season.
  - `W8.form` token `None` in: Klassen throws a four-seam fastball 38.6% of the time, moving 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - `W8.form` token `None` in: He uses his changeup 24.8% of the time as his second most used pitch (second most used pitch), moving 14.9 in. sideways and 4.7 in. up.
  - `W8.form` token `None` in: Phillips relies on his sinker 25.5% of the time, moving 17.3 in. sideways and 8.5 in. up.
  - `W8.form` token `None` in: He uses his sweeper 24.2% of the time, moving 12.4 in. sideways and 1.1 in. up.
  - `W1.evidence_path` token `findings.lineup_notes.away` in: Watch how the Angels hitters adjust their approach given their elevated swing-and-miss risk.
  - `W1.number` token `1` in: The stats for Tyler Phillips reflect a full season of work over 1,422 pitches.
  - `W1.number` token `422` in: The stats for Tyler Phillips reflect a full season of work over 1,422 pitches.
  - `W12.time` token `currently` in: Data for George Klassen is currently limited with only 145 pitches recorded for the 2026 season through Aug 6.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, checks ['W1.evidence_path', 'W1.number', 'W15.form']

**Headline**

George Klassen faces Tyler Phillips in Miami

**Short summary**

- George Klassen starts for the Angels.
- Tyler Phillips takes the mound for the Marlins.
- Both starters are right-handed pitchers.

**Matchup Summary**

George Klassen has an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6. Tyler Phillips carries a 3.53 ERA and a 1.35 WHIP through the same period. Phillips shows average command and below-average swing-and-miss ability. Control and strikeout data for George Klassen are limited: 32 batters faced, where 170 are needed for a control read and 70 are needed for a strikeout read.

**George Klassen vs Miami Marlins**

The Miami Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. This group posts a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate) in that matchup.

**Tyler Phillips vs Los Angeles Angels**

The Los Angeles Angels lineup has a .687 OPS against right-handed pitchers over the 2026 regular season through Aug 6. That lineup records a 24.9% K% and an 8.3% BB% against right-handed pitchers. The group carries an elevated swing-and-miss risk.

**Arsenal Scout**

George Klassen uses his Four-seam fastball 38.6% of the time and his Changeup 24.8% of the time, measured through Aug 6, 2026. His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. Tyler Phillips relies on his Sinker 25.5% of the time and his Sweeper 24.2% of the time. The Phillips Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often George Klassen utilizes his Four-seam fastball to set up his Changeup.
- Watch whether the Marlins lineup can handle the pitchers.
- Watch if Tyler Phillips uses his Sinker to control the zone against the Los Angeles lineup.

**Data Confidence Note**

The lineup status is confirmed as probable pitchers.

### Readability for a casual fan

Verdict: better. The limited-data situation is said once with its counts (32 batters faced, 170 and 70 needed) where the rules text says it three times in the same stiff form, and the opening tells the fan who starts for whom. Weaknesses: a paragraph of ERA, WHIP, OPS, K% and BB% in a row, "utilizes", the scope in four places and a vague watch item ("whether the Marlins lineup can handle the pitchers").


## limited-825104

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W17.structure'], tokens {'candidatesTokenCount': 2362, 'promptTokenCount': 6916, 'thoughtsTokenCount': 1321, 'totalTokenCount': 10599}
  - `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W15.form', 'W11.expansion', 'W6.arsenal', 'W17.length'], tokens {'candidatesTokenCount': 1626, 'promptTokenCount': 6945, 'thoughtsTokenCount': 1070, 'totalTokenCount': 9641}
  - `W15.form` token `Watch the approach o` in: Watch the approach of the Atlanta Braves hitters against right-handed pitching.
  - `W11.expansion` token `ERA` in: Bryce Elder enters with a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3.
  - `W11.expansion` token `WHIP` in: Bryce Elder enters with a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3.
  - `W11.expansion` token `OPS` in: Atlanta features an offense with an .827 OPS against right-handed pitching.
  - `W11.expansion` token `K%` in: The Atlanta Braves lineup shows a .827 OPS, a 19.4% K% (strikeout rate), and a 9.5% BB% (walk rate) against right-handed pitchers over this timeframe.
  - `W11.expansion` token `BB%` in: The Atlanta Braves lineup shows a .827 OPS, a 19.4% K% (strikeout rate), and a 9.5% BB% (walk rate) against right-handed pitchers over this timeframe.
  - `W6.arsenal` token `None` in: (whole report)
  - `W17.length` token `1759` in: (whole report)
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, checks ['W17.structure']

**Headline**

Bryce Elder and the Braves face Michael Soroka and the Diamondbacks

**Short summary**

- Bryce Elder starts for the Atlanta Braves against Michael Soroka for the Arizona Diamondbacks.
- Both starters carry limited data for command and strikeout metrics for the 2026 regular season through Apr 3.
- This matchup at Chase Field features the Braves offense against a Diamondbacks pitching staff in the early regular season.
- The 2026 regular season through Apr 3 is the scope for these statistics.

**Matchup Summary**

Bryce Elder and Michael Soroka both hold a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning) for the 2026 regular season through Apr 3. Data for both pitchers regarding command and strikeout ability is limited. Elder has faced 23 batters, and Soroka has faced 20 batters, with 170 and 70 respectively needed for a read on control and strikeouts.

**Bryce Elder vs Arizona Diamondbacks**

Bryce Elder throws for the Braves at Chase Field for the 2026 regular season through Apr 3. The Diamondbacks offense has a .653 OPS (on-base plus slugging) against right-handed pitchers. This group carries a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate) in this same matchup.

**Michael Soroka vs Atlanta Braves**

Michael Soroka starts for the Diamondbacks over the 2026 regular season through Apr 3. The Braves lineup has an .827 OPS against right-handed pitchers. They have a 19.4% K% and a 9.5% BB% in these encounters.

**Arsenal Scout**

Bryce Elder uses a sinker as his primary pitch and a slider as his second most used pitch (second most used pitch) for the 2026 regular season through Apr 3. His sinker averages 91.1 mph, and his slider averages 83.1 mph. The sinker moves 14.6 in. sideways and 7.6 in. up compared with a pitch thrown without spin. Michael Soroka relies on a slurve as his primary pitch and a four-seam fastball as his second most used pitch. The slurve averages 80.9 mph, while the four-seam fastball averages 93.8 mph. The slurve moves 9.6 in. sideways and 6.8 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Bryce Elder utilizes his sinker compared to his slider as the game progresses.
- Watch whether Michael Soroka leans on his slurve against the Braves lineup in this matchup.
- Watch if the Braves offense continues its pattern of drawing walks at a 9.5% BB% against right-handed pitching.

**Data Confidence Note**

Data for Bryce Elder is limited with 83 pitches thrown, short of the 100 needed for the 2026 regular season through Apr 3. Data for Michael Soroka is limited with 89 pitches thrown, short of the 100 needed. The pitching style and pitch mix for both starters are based on these limited samples.

### Readability for a casual fan

Verdict: mixed. The scene setting is plainer than the rules text, but the limited data is not stated more briefly: the shown text says it in the short summary ("Both starters carry limited data for command and strikeout metrics for the 2026 regular season through Apr 3."), again in the Matchup Summary ("Data for both pitchers regarding command and strikeout ability is limited.") and in the confidence note ("Data for Bryce Elder is limited with 83 pitches thrown, short of the 100 needed"), where the rules text repeats it in each field. It also has a time claim ("continues its pattern of drawing walks"), a scope repeated in every section and the same sentence shape in both lineup sections.


## limited-823863

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W5.label', 'W1.evidence_path', 'W2.comparison', 'W1.number', 'W10.cause', 'W11.expansion'], tokens {'candidatesTokenCount': 3299, 'promptTokenCount': 7077, 'thoughtsTokenCount': 1486, 'totalTokenCount': 11862}
  - `W5.label` token `command` in: Eury Pérez takes the mound for Miami, looking to command his fastball and slider mix.
  - `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Control data for Tobias Myers is limited: 115 batters faced, and 170 are needed for a read.
  - `W2.comparison` token `versus` in: That lineup records a 20.7% K% and an 8.1% BB% versus right-handed pitching.
  - `W1.number` token `2026` in: Tobias Myers utilizes a four-seam fastball 50.1% of the time and a splitter 21.4% of the time during the 2026 regular season through May 21.
  - `W1.number` token `21` in: Tobias Myers utilizes a four-seam fastball 50.1% of the time and a splitter 21.4% of the time during the 2026 regular season through May 21.
  - `W5.label` token `command` in: Watch how Eury Pérez manages base traffic, as his below-average command can lead to deep counts.
  - `W10.cause` token `lead to` in: Watch how Eury Pérez manages base traffic, as his below-average command can lead to deep counts.
  - `W11.expansion` token `ERA` in: The visiting starter Myers arrives with a 3.41 earned run average (ERA) and a 1.03 walks plus hits per inning (WHIP).
  - `W11.expansion` token `WHIP` in: The visiting starter Myers arrives with a 3.41 earned run average (ERA) and a 1.03 walks plus hits per inning (WHIP).
  - `W11.expansion` token `OPS` in: Against right-handed pitchers, the Marlins have a .697 on-base plus slugging (OPS) during the 2026 regular season through May 21.
  - `W11.expansion` token `K%` in: The Miami offense carries a 20.9% strikeout rate (K%) and an 8.8% walk rate (BB%) in this matchup.
  - `W11.expansion` token `BB%` in: The Miami offense carries a 20.9% strikeout rate (K%) and an 8.8% walk rate (BB%) in this matchup.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W17.structure'], tokens {'candidatesTokenCount': 2155, 'promptTokenCount': 7222, 'thoughtsTokenCount': 1168, 'totalTokenCount': 10545}
  - `W17.structure` token `None` in: (whole report)
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, checks ['W17.structure']

**Headline**

Tobias Myers and Eury Perez Start at loanDepot Park

**Short summary**

- Tobias Myers takes the mound for the New York Mets against the Miami Marlins.
- Eury Perez starts for Miami in this right-handed pitching matchup.
- Both teams look to adjust to the specific arsenal styles of their opponents.
- Both starters use a four-seam fastball as their primary pitch.

**Matchup Summary**

Tobias Myers enters with a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning) for the 2026 regular season through May 21. Eury Perez carries a 5.33 ERA and a 1.41 WHIP over the 2026 regular season through May 21. Myers features average swing-and-miss ability. Perez displays above-average swing-and-miss ability and below-average command.

**Tobias Myers vs Miami Marlins**

The Miami lineup faces Tobias Myers in the 2026 regular season through May 21. They have a .697 OPS (on-base plus slugging) against right-handed pitchers. This group maintains a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate) in such matchups.

**Eury Pérez vs New York Mets**

The New York Mets lineup squares off against Eury Perez over the 2026 regular season through May 21. They record a .659 OPS against right-handed pitchers. The Mets show a 20.7% K% and an 8.1% BB% in these encounters.

**Arsenal Scout**

Tobias Myers relies on a four-seam fastball at 92.6 mph and a splitter at 79.8 mph for the 2026 regular season through May 21. His four-seam fastball moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin. Eury Perez uses a four-seam fastball at 98.1 mph and a slider at 87.6 mph in the same scope. His slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Tobias Myers can maintain control, as his data for batters faced is limited with 115 and 170 needed for a read.
- Watch how often Eury Perez utilizes his slider, as his below-average command can create deep-count traffic.
- Watch how the hitters for the Mets and Marlins perform against the four-seam fastballs each starter uses as their primary pitch.

**Data Confidence Note**

There is not enough data yet to rate the command of Tobias Myers. Control data for Tobias Myers is limited to 115 batters faced.

### Readability for a casual fan

Verdict: mixed. Smoother than the rules text, and it names where the game is played, but it adds filler ("Both teams look to adjust to the specific arsenal styles of their opponents") that says nothing, a title-case headline and velocity figures that are listed, not explained. The rules text is accurate and hard to read.


## veteran-824027

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.evidence_value', 'W1.entity', 'W1.evidence_path', 'W15.form', 'W12.repeat'], tokens {'candidatesTokenCount': 2243, 'promptTokenCount': 7280, 'thoughtsTokenCount': 1802, 'totalTokenCount': 11325}
  - `W1.evidence_value` token `starters.home_starter.name` in: Kyle Freeland and Jose Soriano Lead Their Teams in Upcoming Angel Stadium Duel
  - `W1.evidence_value` token `starters.home_starter.name` in: Kyle Freeland starts for Colorado against Jose Soriano and the Angels.
  - `W1.entity` token `Jose Soriano` in: Jose Soriano holds a 2.65 ERA and a 1.15 WHIP over the 2026 regular season through May 31.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: This group carries an elevated swing-and-miss risk and draws walks at an above-average rate, with a 24.3% K% (strikeout rate) and a 10.4% BB% (walk rate).
  - `W1.evidence_value` token `velocity_by_pitch.5.home_starter_velocity` in: Jose Soriano utilizes his sinker at 96.7 mph to begin sequences, while his curveball, thrown at 85.6 mph, serves as his second most used pitch.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: Watch whether Freeland uses his solid command to contain the Angels' propensity for drawing walks.
  - `W15.form` token `Watch if the Rockies` in: Watch if the Rockies hitters can navigate Soriano, who shows above-average swing-and-miss ability.
  - `W12.repeat` token `2026 regular season through May 31` in: Jose Soriano holds a 2.65 ERA and a 1.15 WHIP over the 2026 regular season through May 31.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.evidence_value', 'W1.entity', 'W1.evidence_path', 'W11.expansion'], tokens {'candidatesTokenCount': 1647, 'promptTokenCount': 7385, 'thoughtsTokenCount': 820, 'totalTokenCount': 9852}
  - `W1.evidence_value` token `starters.home_starter.name` in: Kyle Freeland and Jose Soriano start in Anaheim
  - `W1.entity` token `Jose Soriano` in: Jose Soriano provides above-average swing-and-miss ability for the Angels.
  - `W1.entity` token `Jose Soriano` in: Jose Soriano carries a 2.65 ERA and a 1.15 WHIP over the same period.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: The lineup notes show this group draws walks at an above-average rate and has an elevated swing-and-miss risk.
  - `W1.evidence_value` token `pitch_mix.0.away_starter.overall` in: Kyle Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time for the 2026 regular season through May 31.
  - `W1.evidence_value` token `pitch_mix.1.away_starter.overall` in: Kyle Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time for the 2026 regular season through May 31.
  - `W1.evidence_value` token `pitch_mix.5.home_starter.overall` in: Jose Soriano relies on a sinker 27.8% of the time and a curveball 24.8% of the time.
  - `W1.evidence_value` token `pitch_mix.1.home_starter.overall` in: Jose Soriano relies on a sinker 27.8% of the time and a curveball 24.8% of the time.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: Watch whether the Angels lineup takes advantage of their above-average walk rate against Freeland.
  - `W11.expansion` token `ERA` in: Kyle Freeland enters this game with an 8.08 earned run average (ERA) and a 1.75 walks plus hits per inning (WHIP) for the 2026 regular season through May 31.
  - `W11.expansion` token `WHIP` in: Kyle Freeland enters this game with an 8.08 earned run average (ERA) and a 1.75 walks plus hits per inning (WHIP) for the 2026 regular season through May 31.
  - `W11.expansion` token `OPS` in: The Angels lineup has a .712 on-base plus slugging (OPS) against left-handed and right-handed hitters (LHH / RHH) like Freeland, according to data from the 2026 regular season through May 31.
  - `W11.expansion` token `K%` in: This group carries a 24.3% strikeout rate (K%) and a 10.4% walk rate (BB%) in this matchup.
  - `W11.expansion` token `BB%` in: This group carries a 24.3% strikeout rate (K%) and a 10.4% walk rate (BB%) in this matchup.
  - `W11.expansion` token `LHH / RHH` in: The Angels lineup has a .712 on-base plus slugging (OPS) against left-handed and right-handed hitters (LHH / RHH) like Freeland, according to data from the 2026 regular season through May 31.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, checks ['W1.evidence_value', 'W1.entity', 'W1.evidence_path', 'W11.expansion']

**Headline**

Kyle Freeland and Jose Soriano start in Anaheim

**Short summary**

- Kyle Freeland brings solid command to the mound for Colorado.
- Jose Soriano provides above-average swing-and-miss ability for the Angels.
- Both starters enter the matchup with distinct pitching profiles.

**Matchup Summary**

Kyle Freeland enters this game with an 8.08 earned run average (ERA) and a 1.75 walks plus hits per inning (WHIP) for the 2026 regular season through May 31. Jose Soriano carries a 2.65 ERA and a 1.15 WHIP over the same period.

**Kyle Freeland vs Los Angeles Angels**

The Angels lineup has a .712 on-base plus slugging (OPS) against left-handed and right-handed hitters (LHH / RHH) like Freeland, according to data from the 2026 regular season through May 31. This group carries a 24.3% strikeout rate (K%) and a 10.4% walk rate (BB%) in this matchup. The lineup notes show this group draws walks at an above-average rate and has an elevated swing-and-miss risk.

**José Soriano vs Colorado Rockies**

The Rockies lineup has a .709 OPS against right-handed pitchers for the 2026 regular season through May 31. Their K% is 22.7% and their BB% is 8.3% in this split.

**Arsenal Scout**

Kyle Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time for the 2026 regular season through May 31. His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin. Jose Soriano relies on a sinker 27.8% of the time and a curveball 24.8% of the time. His sinker moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Freeland uses his four-seam fastball to establish control early.
- Watch how often Soriano induces swings and misses with his curveball.
- Watch whether the Angels lineup takes advantage of their above-average walk rate against Freeland.

**Data Confidence Note**

This report covers the probable pitchers for the upcoming game.

### Readability for a casual fan

Verdict: not better. The model text is fluent but contains an error a fan would notice ("against left-handed and right-handed hitters (LHH / RHH) like Freeland" misuses a glossary term), a place name that is not in the data ("Anaheim"), a lost accent in the starter's name and the filler line "Both starters enter the matchup with distinct pitching profiles". The rules text is stiff but correct. The hand-written positive control for this case reads better than both.


## veteran-823938

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W2.comparison', 'W1.evidence_value'], tokens {'candidatesTokenCount': 2783, 'promptTokenCount': 7075, 'thoughtsTokenCount': 1933, 'totalTokenCount': 11791}
  - `W1.entity` token `Nick Martinez Faces Eric Lauer` in: Nick Martinez Faces Eric Lauer in Los Angeles
  - `W2.comparison` token `lower` in: Nick Martinez faces the Dodgers with a lower ERA than Eric Lauer.
  - `W2.comparison` token `lower` in: Martinez holds a lower WHIP than the 1.29 WHIP of Lauer during the 2026 regular season through Jun 14.
  - `W2.comparison` token `higher` in: The Dodgers offense has a .806 OPS (on-base plus slugging) against right-handed pitchers, which is higher than the .685 OPS that the Rays produce against left-handed pitchers.
  - `W1.evidence_value` token `pitch_movement.away_starter.Sinker.h_break` in: His sinker moves 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W3.prediction', 'W2.comparison', 'W8.form', 'W11.repeat'], tokens {'candidatesTokenCount': 1970, 'promptTokenCount': 7148, 'thoughtsTokenCount': 2340, 'totalTokenCount': 11458}
  - `W3.prediction` token `will` in: Nick Martinez and Eric Lauer will start this game for their respective teams.
  - `W2.comparison` token `lower` in: Nick Martinez has a lower 2.43 ERA (earned run average) than Eric Lauer, who holds a 5.47 ERA.
  - `W2.comparison` token `lower` in: Martinez has a lower 1.16 WHIP (walks plus hits per inning) than the 1.29 WHIP posted by Lauer.
  - `W8.form` token `None` in: Eric Lauer uses his Four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin.
  - `W11.repeat` token `ERA` in: Nick Martinez has a lower 2.43 ERA (earned run average) than Eric Lauer, who holds a 5.47 ERA.
  - `W11.repeat` token `OPS` in: The Dodgers lineup has a .806 OPS (on-base plus slugging) against right-handed pitchers, along with a 20.3% K% (strikeout rate) and 11.0% BB% (walk rate).
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W2.comparison', 'W1.evidence_value']

**Headline**

Nick Martinez Faces Eric Lauer in Los Angeles

**Short summary**

- Nick Martinez leads the Tampa Bay Rays against the Los Angeles Dodgers at UNIQLO Field at Dodger Stadium.
- Martinez enters the 2026 regular season through Jun 14 with a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning).
- Eric Lauer starts for the Dodgers with a 5.47 ERA and a 1.29 WHIP over the same period.

**Matchup Summary**

Nick Martinez faces the Dodgers with a lower ERA than Eric Lauer. Martinez holds a lower WHIP than the 1.29 WHIP of Lauer during the 2026 regular season through Jun 14.

**Nick Martinez vs Los Angeles Dodgers**

Nick Martinez displays solid command and below-average swing-and-miss ability for the 2026 regular season through Jun 14. The Dodgers offense has a .806 OPS (on-base plus slugging) against right-handed pitchers, which is higher than the .685 OPS that the Rays produce against left-handed pitchers. The Dodgers group draws walks at an 11.0% BB% (walk rate) and carries a 20.3% K% (strikeout rate).

**Eric Lauer vs Tampa Bay Rays**

Eric Lauer carries an average command label and below-average swing-and-miss ability during the 2026 regular season through Jun 14. The Rays lineup faces him with an 8.8% BB% and a 17.7% K% in the same period.

**Arsenal Scout**

Nick Martinez relies on his sinker as a primary pitch (31.4% usage) and his changeup as his second most used pitch (28.0% usage) over the 2026 regular season through Jun 14. His sinker moves 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin. Eric Lauer throws his four-seam as his primary pitch (45.5% usage) and his cutter as his second most used pitch (17.5% usage) during the same period. Lauer's four-seam moves 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how Martinez uses his sinker to set up hitters.
- Watch whether Lauer manages his cutter usage to neutralize the Rays.
- Watch how the Dodgers approach the sinker of Martinez.

**Data Confidence Note**

The probable pitcher status for this matchup is based on the lineup notes for the 2026 regular season through Jun 14.

### Readability for a casual fan

Verdict: not better. Smoother than the rules text but riskier. It compares one lineup's OPS against right-handed pitchers with the other lineup's OPS against left-handed pitchers (a misleading comparison the check caught), writes "average command label" (an internal word) and its confidence note makes no sense ("based on the lineup notes").


## veteran-824803

- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.evidence_path', 'W12.repeat'], tokens {'candidatesTokenCount': 2246, 'promptTokenCount': 7078, 'thoughtsTokenCount': 1518, 'totalTokenCount': 10842}
  - `W1.entity` token `Shane Baz Matchup` in: Carlos Rodón and Shane Baz Matchup at Oriole Park
  - `W1.evidence_path` token `findings.lineup_notes.away` in: Both lineups present elevated swing-and-miss risk in this matchup.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: Both lineups present elevated swing-and-miss risk in this matchup.
  - `W1.evidence_path` token `findings.lineup_notes.home` in: The Baltimore offense has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - `W1.evidence_path` token `findings.lineup_notes.away` in: This lineup also presents an elevated swing-and-miss risk and draws walks at an above-average rate.
  - `W12.repeat` token `2026 regular season through Aug 17` in: Shane Baz relies on his four-seam fastball at a 34.2% rate and his curveball at 32.7% for the 2026 regular season through Aug 17.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.number', 'W3.prediction', 'W10.cause', 'W11.expansion'], tokens {'candidatesTokenCount': 2118, 'promptTokenCount': 7143, 'thoughtsTokenCount': 948, 'totalTokenCount': 10209}
  - `W1.entity` token `Shane Baz Matchup Preview` in: Carlos Rodón and Shane Baz Matchup Preview
  - `W1.number` token `two` in: The New York Yankees and Baltimore Orioles prepare for a contest featuring two starters with distinct stylistic profiles.
  - `W3.prediction` token `might` in: Watch whether Carlos Rodón can maintain his command, as his below-average rating might lead to elevated traffic.
  - `W10.cause` token `lead to` in: Watch whether Carlos Rodón can maintain his command, as his below-average rating might lead to elevated traffic.
  - `W11.expansion` token `ERA` in: Carlos Rodón brings a 3.30 earned run average (ERA) and 1.25 walks plus hits per inning (WHIP) into his outing.
  - `W11.expansion` token `WHIP` in: Carlos Rodón brings a 3.30 earned run average (ERA) and 1.25 walks plus hits per inning (WHIP) into his outing.
  - `W11.expansion` token `OPS` in: The Baltimore lineup faces Carlos Rodón with a .723 on-base plus slugging (OPS) against left-handed pitchers during the 2026 regular season through Aug 17.
  - `W11.expansion` token `K%` in: This group carries a 25.7% strikeout rate (K%) and a 9.5% walk rate (BB%) in that matchup.
  - `W11.expansion` token `BB%` in: This group carries a 25.7% strikeout rate (K%) and a 9.5% walk rate (BB%) in that matchup.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, checks ['W1.entity', 'W1.evidence_path', 'W12.repeat']

**Headline**

Carlos Rodón and Shane Baz Matchup at Oriole Park

**Short summary**

- Carlos Rodón delivers above-average swing-and-miss ability for the New York Yankees.
- Shane Baz leads the Baltimore Orioles pitching staff with a primary four-seam fastball and curveball mix.
- Both lineups present elevated swing-and-miss risk in this matchup.

**Matchup Summary**

Carlos Rodón carries a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning) for the 2026 regular season through Aug 17. Shane Baz has a 4.00 ERA and a 1.36 WHIP over the same period. Rodón shows below-average command and above-average swing-and-miss ability. Baz shows average command and average swing-and-miss ability.

**Carlos Rodón vs Baltimore Orioles**

The Baltimore Orioles lineup has a .723 OPS (on-base plus slugging) against left-handed pitchers for the 2026 regular season through Aug 17. Against that group, the team has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate). The Baltimore offense has an elevated swing-and-miss risk and draws walks at an above-average rate.

**Shane Baz vs New York Yankees**

The New York Yankees lineup hits against right-handed pitchers with a .713 OPS through the 2026 regular season through Aug 17. In this matchup, the team has a 24.5% K% and a 10.2% BB%. This lineup also presents an elevated swing-and-miss risk and draws walks at an above-average rate.

**Arsenal Scout**

Carlos Rodón uses his four-seam fastball 44.4% of the time and his slider 24.4% of the time for the 2026 regular season through Aug 17. His four-seam fastball moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin. Shane Baz relies on his four-seam fastball at a 34.2% rate and his curveball at 32.7% for the 2026 regular season through Aug 17. His four-seam fastball moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin. The curveball for Baz moves 5.1 in. sideways and 10.4 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Rodón relies on his slider to finish off batters.
- Watch whether the Baltimore Orioles can capitalize on the below-average command of Rodón.
- Watch how the New York Yankees hitters adjust to the curveball from Baz.

**Data Confidence Note**

Both pitchers are established starters with sufficient data for these profiles.

### Readability for a casual fan

Verdict: mixed. A fan would read it faster than the rules text and trust it less: it pads with unsupported lines ("Both pitchers are established starters with sufficient data", "Shane Baz leads the Baltimore Orioles pitching staff"), repeats the same lineup sentence in both sections and repeats the scope.


## Calibration note: the rules text of veteran-824027 through the word-level checks

Not a defect list. These are the words and shapes the word-level checks flag in the text the rules writer publishes today. Whether each would be a violation depends on citations (a comparison word is allowed when both values are quoted; a sentence-opening question word is a limit of the entity heuristic). The checks that need citations were not run.

- `W1.entity`: 'Can José Soriano', 'Can Kyle Freeland', 'Statcast'
- `W10.cause`: 'because', 'so'
- `W15.question`: '?'
- `W16.internal`: 'fetched', 'snapshot'
- `W2.comparison`: 'larger', 'more', 'versus'

