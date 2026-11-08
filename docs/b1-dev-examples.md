# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest(s) recorded in this run: `906f01cd31ac21f5d6ab0a4ea556c466f778263a13af3e00f10a803d7e580c7e`; prompt version(s) recorded in this run: `p2.2-3`. Nothing here is published; rules stay live.

Gemini HTTP calls: run 10 of 80, experiment 105 of 400.
Capacity failures (503/429) in this run: 8 of 10 finished calls. By model: `gemini-3.1-flash-lite` 2 of 4; `gemini-3.5-flash` 6 of 6.
**The run stopped early** after case `postseason-849849` at 2026-10-30 16:55 local (2026-10-30 21:55 UTC): 8 of 10 finished calls were capacity failures (more than a third). Failing model(s): `gemini-3.1-flash-lite` (2 of 4), `gemini-3.5-flash` (6 of 6). The remaining cases are `not_attempted`.
Run started 2026-10-30 16:52 local (2026-10-30 21:52 UTC), finished 2026-10-30 16:55 local.
More than a third of the calls failed on capacity; time of day of the run: 2026-10-30 16:52 to 2026-10-30 16:55 local (Hora est. Pacífico, Sudamérica).
Paths: primary 0, primary_retry 0, fallback 0, fallback_retry 0, rules 2, not_attempted 8. LLM coverage 0/10; accepted 0, rejected 2, not attempted 8; not written by the primary model 10/10 (a fallback or rules result is not a primary first-attempt success).


## Run 3 summary (final re-run; read first)

- **The run stopped early, as you asked.** After 2 of the 10 cases (10 Gemini calls) 8 calls had failed on capacity (80%, more than a third), so the runner stopped, kept the partial results and recorded the other 8 cases as `not_attempted`. Time: 16:52 to 16:55 local (America/Bogota, UTC-5), that is 21:52 to 21:55 UTC.
- **Which model failed:** the primary `gemini-3.5-flash` failed on 6 of 6 calls, all `http_429`. The fallback `gemini-3.1-flash-lite` answered 2 of its 4 calls and returned `http_503` on the other 2. At the new 20-second pacing the run made about 3 calls a minute, so the primary refusing all 6 points to a daily quota or a per-minute token limit (about 8,000 prompt tokens per call) rather than a per-minute request limit. I cannot confirm that without the AI Studio limits you are reading.
- **Gemini calls:** run 10 of the run cap 80; experiment 105 of 400 (40 + 55 + 10). Outcomes of the 10: 2 answered (both fallback), 6 `http_429`, 2 `http_503`.
- **Accepted versus rejected:** 0 accepted, 2 rejected, 8 not attempted. `postseason-849842` was rejected after two content attempts (attempt 1: output shape, four summary lines instead of three; attempt 2: `W1.number` for a "Game 2" in the headline that cites no game number and for the built date "Sep 29", and `W1.entity` for "Sep": guide 0.4 says to use the scope label and never to build a date, and the prompt says so; the style findings of attempt 2 were `S-2` and `W14.team`). Attempt 1 failed only the shape gate, but `W17.structure` stops the other gate checks, so its other gates were never evaluated; its text carries the same "through Sep 29" and "Game 2" and would very likely have failed `W1.*` too. `postseason-849849` has no model text at all: all four calls of its first attempt failed on capacity.
- **What D52 changed in these results:** none of the rejections was caused by a style rule. The gates that fired are an output-shape failure and a built date. A report failing only style rules would have been accepted (tested; no such report occurred in this run).
- **Readability:** one model text exists to judge (`postseason-849842`, attempt 1, fallback model, from a candidate that failed the output-shape gate and carries the built date): better than the rules text in flow, with the faults listed in its note. The other 9 cases have no model text to judge, so there is no readability verdict for them.
- **What is shown per case:** the model candidate with the fewest failed gate checks (a later attempt wins a tie), labelled with its attempt, model, gate checks and style findings. A `W17.structure` failure stops the other gate checks, so a shape-failed attempt looks better by this count than it is; the heading says so when it applies. Every phrase quoted in a readability note is checked by code against the text shown.
- Run 2 (guide 0.3) is kept as `docs/b1-dev-examples-run2.md` for comparison.


## postseason-849842

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'candidatesTokenCount': 2040, 'promptTokenCount': 8239, 'thoughtsTokenCount': 1258, 'totalTokenCount': 11537}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429')], model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W1.entity'], style findings ['S-2', 'W14.team'], tokens {'candidatesTokenCount': 2064, 'promptTokenCount': 8268, 'thoughtsTokenCount': 1913, 'totalTokenCount': 12245}
  - gate `W1.number` token `2` in: Kevin Gausman and Nick Pivetta meet in Game 2 of the NL Wild Card Series
  - gate `W1.number` token `29` in: All statistics for this matchup cover the 2026 regular season through Sep 29.
  - gate `W1.entity` token `Sep` in: All statistics for this matchup cover the 2026 regular season through Sep 29.
  - style `S-2` token `the` in: The Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - style `W14.team` token `None` in: (whole report)
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Kevin Gausman and Nick Pivetta meet in the NL Wild Card Series

**Short summary**

- This is Game 2 of the NL Wild Card Series, and before first pitch, SD leads 1-0.
- Kevin Gausman starts for Chicago while Nick Pivetta starts for San Diego.
- Both pitchers bring different styles and arsenals to this matchup.
- All figures in this report cover the 2026 regular season through Sep 29.

**Matchup Summary**

Kevin Gausman carries a 4.51 earned run average (ERA) and 1.27 walks plus hits per inning (WHIP) while Nick Pivetta carries a lower 2.86 ERA and a lower 1.01 WHIP.

**Kevin Gausman vs San Diego Padres**

Kevin Gausman shows solid command and average swing-and-miss ability. The San Diego Padres lineup holds a .722 on-base plus slugging (OPS) against right-handed pitchers. This group draws walks at a 9.4% walk rate (BB%) and carries a 21.5% strikeout rate (K%).

**Nick Pivetta vs Chicago Cubs**

Nick Pivetta shows above-average swing-and-miss ability. Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. The Chicago Cubs lineup has a .757 OPS against right-handed pitchers. That group draws walks at a 10.6% BB% and maintains a 21.2% K%.

**Arsenal Scout**

Kevin Gausman relies on his four-seam fastball and his second most used pitch, the splitter. His four-seam fastball moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. His splitter moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin. Nick Pivetta throws his four-seam fastball and his second most used pitch, the curveball. His four-seam fastball moves 3.5 in. sideways and 20.3 in. up compared with a pitch thrown without spin. His curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Kevin Gausman uses his splitter to finish counts.
- Watch whether Nick Pivetta can maintain his control with his curveball.
- Watch if the Chicago Cubs lineup increases its walks against the San Diego starting pitching.

**Data Confidence Note**

Pitching profiles are based on probable pitchers.

### Readability for a casual fan

Verdict: better than the rules text, with visible flaws. It states the series situation and who starts for which team in plain sentences, and the short forms read naturally ("4.51 earned run average (ERA)"). Flaws: the clause "compared with a pitch thrown without spin" is repeated in all four movement sentences, so the Arsenal Scout paragraph reads like a template; "Both pitchers bring different styles and arsenals to this matchup." is filler; the last watch item ("increases its walks against the San Diego starting pitching") is awkward and implies a result. This is attempt 1: it had four summary lines (an output-shape failure), and because that failure stops the other gate checks, its other gates were not evaluated; it carries the same built date ("through Sep 29") that failed `W1.*` in attempt 2, so it could not have been published either way.


## postseason-849849

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `http_503`); content attempts: 1
- Content attempt 1: transport path `rules`, transport failures [('gemini-3.5-flash', 1, 'http_429'), ('gemini-3.5-flash', 2, 'http_429'), ('gemini-3.1-flash-lite', 1, 'http_503'), ('gemini-3.1-flash-lite', 2, 'http_503')], model `-`, gate checks not reached, style findings none, tokens -
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

### Model text (B1)

No model text: the call never produced a usable answer.

### Readability for a casual fan

No model text exists for this case: all four calls of its first content attempt failed on capacity (two `http_429` on the primary, two `http_503` on the fallback), so there is no readability comparison.


## opener-824280

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## opener-823769

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## limited-823836

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## limited-825104

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## limited-823863

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## veteran-824027

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## veteran-823938

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## veteran-824803

- Outcome: **NOT ATTEMPTED (capacity stop)**
- Path: **not_attempted** (reason: `capacity_stop`); content attempts: 0


## Calibration note: the rules text of veteran-824027 through the word-level checks

Not a defect list. These are the words and shapes the word-level checks flag in the text the rules writer publishes today. Whether each would be a violation depends on citations (a comparison word is allowed when both values are quoted; a sentence-opening question word is a limit of the entity heuristic). The checks that need citations were not run.

- `W1.entity`: 'Can José Soriano', 'Can Kyle Freeland', 'Statcast'
- `W10.cause`: 'because', 'so'
- `W15.question`: '?'
- `W16.internal`: 'fetched', 'snapshot'
- `W2.comparison`: 'larger', 'more', 'versus'

