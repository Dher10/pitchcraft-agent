# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest(s) recorded in this run: `172e12b13e39b8b1a16438ea825ceafd80b96ea4c7f23bf970304ef98ec0b347`; prompt version(s) recorded in this run: `p2.2-6`. Nothing here is published; rules stay live.

S1 code detectors: S-1, S-2, S-4, S-5, S-7, S-8; S-3, S-6 and S-9 require judge/human assessment and are not evaluated here. NLI is score-only unless explicitly recorded as gate; no human-calibrated entailment claim.

Gemini HTTP calls: run 19 of 30, experiment 146 of 400.
Capacity failures (503/429) in this run: 1 of 19 finished calls. By model: `gemini-3.1-flash-lite` 1 of 19.
Run started 2026-11-03 18:52 local (2026-11-03 23:52 UTC), finished 2026-11-03 19:01 local.
Paths: primary 3, primary_retry 1, fallback 0, fallback_retry 0, rules 6, not_attempted 0. LLM coverage 4/10; accepted 4, rejected 6, not attempted 0; not written by the primary model 7/10 (a fallback or rules result is not a primary first-attempt success).


## postseason-849842

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number'], style findings ['W11.expansion', 'W17.length'], tokens {'promptTokenCount': 15475, 'candidatesTokenCount': 861, 'thoughtsTokenCount': 270, 'totalTokenCount': 16606}
  - gate `W1.number` token `2` in: Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series
  - style `W11.expansion` token `put-away pitch` in: Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch.
  - style `W17.length` token `1355` in: (whole report)
  - NLI (score_only) score `0.00015925118350423872`, problem `None`, paths `['series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series
  - NLI (score_only) score `0.9891151189804077`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 2 of the NL Wild Card Series.
  - NLI (score_only) score `0.9904932379722595`, problem `None`, paths `['series.standing']`: Before first pitch, SD leads 1-0.
  - NLI (score_only) score `0.013638418167829514`, problem `None`, paths `['findings.away_starter_strengths', 'findings.home_starter_strengths']`: Both starters enter the game with distinct pitching profiles.
  - NLI (score_only) score `0.9951024055480957`, problem `None`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: This report covers the 2026 regular season through Sep 29.
  - NLI (score_only) score `0.9969844222068787`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9856578707695007`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label']`: He shows solid command.
  - NLI (score_only) score `0.9394745826721191`, problem `None`, paths `['findings.lineup_notes.home', 'glossary.BB%.short', 'teams.home.offense_profile.bb_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand']`: The San Diego Padres lineup draws walks at a 9.4% BB% (walk rate).
  - NLI (score_only) score `0.0013106806436553597`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Nick Pivetta has a 2.86 ERA and a 1.01 WHIP.
  - NLI (score_only) score `0.983370304107666`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label']`: He shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.9887809753417969`, problem `None`, paths `['findings.lineup_notes.away', 'glossary.OPS.short', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The Chicago Cubs lineup has a .757 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9558374285697937`, problem `None`, paths `['glossary.K%.short', 'glossary.BB%.short', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: This lineup has a 21.2% K% (strikeout rate) and a 10.6% BB%.
  - NLI (score_only) score `0.00610681576654315`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch']`: Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch.
  - NLI (score_only) score `0.9539342522621155`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0014560702256858349`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Pivetta uses a Four-seam as his primary pitch and a Curveball as his put-away pitch.
  - NLI (score_only) score `0.9631474614143372`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Curveball.v_break']`: His Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Gausman uses his Splitter to finish plate appearances.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_style', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Pivetta relies on his Curveball in counts against the Chicago Cubs.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home', 'starters.away_starter.pitching_profile.command_label']`: Watch if the Padres lineup generates walks against Gausman.
  - NLI (score_only) score `0.9663813710212708`, problem `None`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through']`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
  - Sentence evidence `['F147', 'F149', 'F181']`: Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series
  - Sentence evidence `['F145', 'F147']`: This is Game 2 of the NL Wild Card Series.
  - Sentence evidence `['F148']`: Before first pitch, SD leads 1-0.
  - Sentence evidence `['F004', 'F007']`: Both starters enter the game with distinct pitching profiles.
  - Sentence evidence `['F024', 'F157']`: This report covers the 2026 regular season through Sep 29.
  - Sentence evidence `['F169', 'F177', 'F013', 'F018']`: Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - Sentence evidence `['F150']`: He shows solid command.
  - Sentence evidence `['F010', 'F011', 'F226', 'F227']`: The San Diego Padres lineup draws walks at a 9.4% BB% (walk rate).
  - Sentence evidence `['F201', 'F209']`: Nick Pivetta has a 2.86 ERA and a 1.01 WHIP.
  - Sentence evidence `['F187']`: He shows above-average swing-and-miss ability.
  - Sentence evidence `['F009', 'F017', 'F221', 'F223']`: The Chicago Cubs lineup has a .757 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F014', 'F011', 'F219', 'F217']`: This lineup has a 21.2% K% (strikeout rate) and a 10.6% BB%.
  - Sentence evidence `['F152', 'F153']`: Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch.
  - Sentence evidence `['F116', 'F117']`: His Four-seam moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F184', 'F185']`: Pivetta uses a Four-seam as his primary pitch and a Curveball as his put-away pitch.
  - Sentence evidence `['F128', 'F129']`: His Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F005', 'F153']`: Watch how often Gausman uses his Splitter to finish plate appearances.
  - Sentence evidence `['F008', 'F185']`: Watch whether Pivetta relies on his Curveball in counts against the Chicago Cubs.
  - Sentence evidence `['F010', 'F150']`: Watch if the Padres lineup generates walks against Gausman.
  - Sentence evidence `['F191', 'F193', 'F199']`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W8.form'], style findings ['S-2', 'W17.length'], tokens {'promptTokenCount': 15567, 'candidatesTokenCount': 933, 'thoughtsTokenCount': 407, 'totalTokenCount': 16907}
  - gate `W1.number` token `two` in: Kevin Gausman faces Nick Pivetta in game two of the NL Wild Card Series
  - gate `W8.form` token `None` in: Pivetta moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin with his curveball.
  - gate `W8.form` token `None` in: Gausman moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin with his splitter.
  - style `S-2` token `That group` in: That group draws walks at a 10.6% BB%.
  - style `W17.length` token `1533` in: (whole report)
  - NLI (score_only) score `0.9808121919631958`, problem `None`, paths `['series.game_number', 'series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Kevin Gausman faces Nick Pivetta in game two of the NL Wild Card Series
  - NLI (score_only) score `0.9891151189804077`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 2 of the NL Wild Card Series.
  - NLI (score_only) score `0.9904932379722595`, problem `None`, paths `['series.standing']`: Before first pitch, SD leads 1-0.
  - NLI (score_only) score `0.7332744002342224`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name']`: Kevin Gausman and Nick Pivetta are the starting pitchers.
  - NLI (score_only) score `0.004520437680184841`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Kevin Gausman and Nick Pivetta bring distinct profiles to this contest in the 2026 regular season through Sep 29.
  - NLI (score_only) score `0.9944304823875427`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Kevin Gausman holds a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.981773316860199`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'teams.home.offense_profile.k_rate_vs_hand', 'glossary.OPS.short', 'glossary.K%.short']`: The San Diego Padres lineup against right-handed pitchers has a .722 OPS (on-base plus slugging) and a 21.5% K% (strikeout rate).
  - NLI (score_only) score `0.9949436783790588`, problem `None`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.BB%.short']`: This lineup has a 9.4% BB% (walk rate).
  - NLI (score_only) score `0.002095588017255068`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Nick Pivetta carries a 2.86 ERA and a 1.01 WHIP.
  - NLI (score_only) score `0.9945371747016907`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.k_rate_number']`: The Chicago Cubs lineup against right-handed pitchers posts a .757 OPS and a 21.2% K%.
  - NLI (score_only) score `0.9948886036872864`, problem `None`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: That group draws walks at a 10.6% BB%.
  - NLI (score_only) score `0.9739784002304077`, problem `None`, paths `['findings.lineup_notes.away']`: Chicago has a strong OPS against this pitcher's hand.
  - NLI (score_only) score `0.9914783835411072`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label', 'findings.away_starter_strengths']`: Kevin Gausman shows solid command and average swing-and-miss ability while using a four-seam to set up and a splitter to finish.
  - NLI (score_only) score `0.9976115226745605`, problem `None`, paths `['findings.home_starter_strengths', 'starters.home_starter.pitching_profile.swing_miss_label']`: Nick Pivetta uses a four-seam to set up and a curveball to finish, showing above-average swing-and-miss ability.
  - NLI (score_only) score `0.6424835920333862`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Curveball.v_break', 'glossary.Break.short']`: Pivetta moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin with his curveball.
  - NLI (score_only) score `0.9232177138328552`, problem `None`, paths `['pitch_movement.away_starter.Splitter.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Splitter.v_break', 'glossary.Break.short']`: Gausman moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin with his splitter.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.1.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Kevin Gausman relies on his splitter.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Nick Pivetta locates his curveball.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home', 'teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch if the San Diego Padres draw walks as they do at an above-average rate.
  - NLI (score_only) score `0.12969620525836945`, problem `None`, paths `['starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.sample.limited.control', 'starters.home_starter.pitching_profile.command_label']`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
  - Sentence evidence `['F145', 'F147', 'F149', 'F181']`: Kevin Gausman faces Nick Pivetta in game two of the NL Wild Card Series
  - Sentence evidence `['F145', 'F147']`: This is Game 2 of the NL Wild Card Series.
  - Sentence evidence `['F148']`: Before first pitch, SD leads 1-0.
  - Sentence evidence `['F001', 'F149', 'F181']`: Kevin Gausman and Nick Pivetta are the starting pitchers.
  - Sentence evidence `['F157', 'F189']`: Kevin Gausman and Nick Pivetta bring distinct profiles to this contest in the 2026 regular season through Sep 29.
  - Sentence evidence `['F169', 'F177', 'F013', 'F018']`: Kevin Gausman holds a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - Sentence evidence `['F230', 'F233', 'F229', 'F017', 'F014']`: The San Diego Padres lineup against right-handed pitchers has a .722 OPS (on-base plus slugging) and a 21.5% K% (strikeout rate).
  - Sentence evidence `['F227', 'F011']`: This lineup has a 9.4% BB% (walk rate).
  - Sentence evidence `['F201', 'F209']`: Nick Pivetta carries a 2.86 ERA and a 1.01 WHIP.
  - Sentence evidence `['F221', 'F223', 'F219', 'F218']`: The Chicago Cubs lineup against right-handed pitchers posts a .757 OPS and a 21.2% K%.
  - Sentence evidence `['F217']`: That group draws walks at a 10.6% BB%.
  - Sentence evidence `['F009']`: Chicago has a strong OPS against this pitcher's hand.
  - Sentence evidence `['F150', 'F155', 'F004']`: Kevin Gausman shows solid command and average swing-and-miss ability while using a four-seam to set up and a splitter to finish.
  - Sentence evidence `['F007', 'F187']`: Nick Pivetta uses a four-seam to set up and a curveball to finish, showing above-average swing-and-miss ability.
  - Sentence evidence `['F128', 'F129', 'F012']`: Pivetta moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin with his curveball.
  - Sentence evidence `['F122', 'F123', 'F012']`: Gausman moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin with his splitter.
  - Sentence evidence `['F035', 'F153']`: Watch how often Kevin Gausman relies on his splitter.
  - Sentence evidence `['F084', 'F185']`: Watch whether Nick Pivetta locates his curveball.
  - Sentence evidence `['F010', 'F227']`: Watch if the San Diego Padres draw walks as they do at an above-average rate.
  - Sentence evidence `['F193', 'F199', 'F191']`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W1.number'], style findings ['W11.expansion', 'W17.length']

**Headline**

Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series

**Short summary**

- This is Game 2 of the NL Wild Card Series.
- Before first pitch, SD leads 1-0.
- Both starters enter the game with distinct pitching profiles.

**Matchup Summary**

This report covers the 2026 regular season through Sep 29.

**Kevin Gausman vs San Diego Padres**

Kevin Gausman carries a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning). He shows solid command. The San Diego Padres lineup draws walks at a 9.4% BB% (walk rate).

**Nick Pivetta vs Chicago Cubs**

Nick Pivetta has a 2.86 ERA and a 1.01 WHIP. He shows above-average swing-and-miss ability. The Chicago Cubs lineup has a .757 OPS (on-base plus slugging) against right-handed pitchers. This lineup has a 21.2% K% (strikeout rate) and a 10.6% BB%.

**Arsenal Scout**

Gausman uses a Four-seam as his primary pitch and a Splitter as his put-away pitch. His Four-seam moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. Pivetta uses a Four-seam as his primary pitch and a Curveball as his put-away pitch. His Curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Gausman uses his Splitter to finish plate appearances.
- Watch whether Pivetta relies on his Curveball in counts against the Chicago Cubs.
- Watch if the Padres lineup generates walks against Gausman.

**Data Confidence Note**

Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.


## postseason-849849

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W10.cause'], style findings ['S-1', 'S-4'], tokens {'promptTokenCount': 14113, 'candidatesTokenCount': 1097, 'thoughtsTokenCount': 1425, 'totalTokenCount': 16635}
  - gate `W1.number` token `1` in: Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28.
  - gate `W10.cause` token `due to` in: Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command.
  - style `S-1` token `2026 regular season` in: Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28.
  - style `S-4` token `utilizes` in: Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch.
  - NLI (score_only) score `0.7540735006332397`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'teams.away.name', 'teams.home.name', 'series.series_name']`: Hagen Smith and the Chicago White Sox face AJ Blubaugh and the Houston Astros in the AL Wild Card Series.
  - NLI (score_only) score `0.9906396865844727`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 1 of the AL Wild Card Series.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team']`: Hagen Smith starts for the Chicago White Sox.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.name', 'starters.home_starter.team']`: AJ Blubaugh starts for the Houston Astros.
  - NLI (score_only) score `0.00030536536360159516`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through']`: Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28.
  - NLI (score_only) score `0.9645508527755737`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Hagen Smith enters with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9846255779266357`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: He shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.11546143144369125`, problem `None`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.sample.limited.control', 'starters.away_starter.pitching_profile.command_label']`: Control data for Hagen Smith is limited with 110 batters faced, where 170 are needed.
  - NLI (score_only) score `0.9889445900917053`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.OPS.short', 'glossary.K%.short', 'glossary.BB%.short']`: The Houston Astros lineup against left-handed pitchers carries a .713 OPS (on-base plus slugging), a 21.0% K% (strikeout rate), and a 7.9% BB% (walk rate).
  - NLI (score_only) score `0.0031625141855329275`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP.
  - NLI (score_only) score `0.9919328093528748`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label']`: He has below-average command.
  - NLI (score_only) score `0.9887080192565918`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: The Chicago White Sox lineup against right-handed pitchers shows a .716 OPS, a 24.1% K%, and a 9.4% BB%.
  - NLI (score_only) score `0.9975706934928894`, problem `None`, paths `['findings.lineup_notes.away']`: That group draws walks at an above-average rate and carries an elevated swing-and-miss risk.
  - NLI (score_only) score `0.9567785859107971`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch.
  - NLI (score_only) score `0.034492626786231995`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9009791016578674`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Slider.v_break']`: His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0523567833006382`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: AJ Blubaugh relies on his four-seam fastball as his primary pitch and a sweeper as his second most used pitch.
  - NLI (score_only) score `0.03978170454502106`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.v_break']`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9548161625862122`, problem `None`, paths `['pitch_movement.home_starter.Sweeper.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sweeper.v_break']`: His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'findings.away_starter_strengths']`: Watch how often Hagen Smith uses his slider to finish.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.command_label', 'findings.home_starter_risks']`: Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch how the lineups handle the different secondary offerings of each pitcher.
  - NLI (score_only) score `0.002801448805257678`, problem `None`, paths `['starters.away_starter.sample.arsenal.pitches', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.pitches', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.away_starter.sample.thresholds.arsenal', 'starters.home_starter.sample.thresholds.arsenal']`: Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28.
  - Sentence evidence `['F121', 'F153', 'F187', 'F197', 'F119']`: Hagen Smith and the Chicago White Sox face AJ Blubaugh and the Houston Astros in the AL Wild Card Series.
  - Sentence evidence `['F117', 'F119']`: This is Game 1 of the AL Wild Card Series.
  - Sentence evidence `['F121', 'F151']`: Hagen Smith starts for the Chicago White Sox.
  - Sentence evidence `['F153', 'F183']`: AJ Blubaugh starts for the Houston Astros.
  - Sentence evidence `['F121', 'F153', 'F146', 'F178']`: Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28.
  - Sentence evidence `['F141', 'F149', 'F013', 'F018']`: Hagen Smith enters with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning).
  - Sentence evidence `['F127']`: He shows above-average swing-and-miss ability.
  - Sentence evidence `['F133', 'F139', 'F131']`: Control data for Hagen Smith is limited with 110 batters faced, where 170 are needed.
  - Sentence evidence `['F203', 'F201', 'F199', 'F017', 'F014', 'F011']`: The Houston Astros lineup against left-handed pitchers carries a .713 OPS (on-base plus slugging), a 21.0% K% (strikeout rate), and a 7.9% BB% (walk rate).
  - Sentence evidence `['F173', 'F181']`: AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP.
  - Sentence evidence `['F154']`: He has below-average command.
  - Sentence evidence `['F193', 'F191', 'F189']`: The Chicago White Sox lineup against right-handed pitchers shows a .716 OPS, a 24.1% K%, and a 9.4% BB%.
  - Sentence evidence `['F009']`: That group draws walks at an above-average rate and carries an elevated swing-and-miss risk.
  - Sentence evidence `['F124', 'F125', 'F022']`: Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch.
  - Sentence evidence `['F097', 'F098']`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F100', 'F101']`: His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F156', 'F157', 'F022']`: AJ Blubaugh relies on his four-seam fastball as his primary pitch and a sweeper as his second most used pitch.
  - Sentence evidence `['F112', 'F113']`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F115', 'F116']`: His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F125', 'F004']`: Watch how often Hagen Smith uses his slider to finish.
  - Sentence evidence `['F154', 'F006']`: Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command.
  - Sentence evidence `['F125', 'F157']`: Watch how the lineups handle the different secondary offerings of each pitcher.
  - Sentence evidence `['F128', 'F160', 'F138', 'F170']`: Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W15.outcome', 'W6.unsaid', 'W13.standing'], style findings ['S-2', 'W11.expansion', 'W17.length'], tokens {'promptTokenCount': 14215, 'candidatesTokenCount': 991, 'thoughtsTokenCount': 1179, 'totalTokenCount': 16385}
  - gate `W15.outcome` token `strikeouts` in: Watch how often Hagen Smith uses his slider to get strikeouts
  - style `W11.expansion` token `ERA` in: Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning)
  - style `W11.expansion` token `WHIP` in: Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning)
  - style `W11.expansion` token `OPS` in: The Houston Astros lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers
  - style `W11.expansion` token `K%` in: That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate)
  - style `W11.expansion` token `BB%` in: That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate)
  - style `S-2` token `This group` in: This group has a 24.1% K% and a 9.4% BB%
  - gate `W6.unsaid` token `None` in: (whole report)
  - gate `W13.standing` token `None` in: (whole report)
  - style `W17.length` token `1711` in: (whole report)
  - NLI (score_only) score `0.909654974937439`, problem `None`, paths `['series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Hagen Smith and AJ Blubaugh start in the AL Wild Card Series
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team']`: Hagen Smith leads the White Sox pitching staff against the Astros
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['series.game_number', 'starters.home_starter.name', 'starters.home_starter.team']`: AJ Blubaugh takes the mound for Houston in this opening game
  - NLI (score_only) score `0.0716085284948349`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: All stats cover the 2026 regular season through 2026-09-28
  - NLI (score_only) score `0.33162063360214233`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning)
  - NLI (score_only) score `0.02041965164244175`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: AJ Blubaugh enters the matchup with a 3.66 ERA and a 1.23 WHIP
  - NLI (score_only) score `0.9921143054962158`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Hagen Smith shows above-average swing-and-miss ability
  - NLI (score_only) score `0.03425973653793335`, problem `None`, paths `['findings.away_starter_strengths', 'findings.away_style']`: He uses a four-seam fastball to set up and a slider to finish
  - NLI (score_only) score `0.9817812442779541`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.vs_pitcher_hand']`: The Houston Astros lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers
  - NLI (score_only) score `0.9856542944908142`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number']`: That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate)
  - NLI (score_only) score `0.9940392971038818`, problem `None`, paths `['findings.home_starter_risks', 'starters.home_starter.pitching_profile.command_label']`: AJ Blubaugh shows below-average command which can create deep-count traffic
  - NLI (score_only) score `0.02257242426276207`, problem `None`, paths `['findings.home_starter_strengths', 'findings.home_style']`: He uses a four-seam fastball to set up and a sweeper to finish
  - NLI (score_only) score `0.9880309700965881`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: The Chicago White Sox lineup has a .716 OPS against right-handed pitchers
  - NLI (score_only) score `0.9757399559020996`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: This group has a 24.1% K% and a 9.4% BB%
  - NLI (score_only) score `0.9885821342468262`, problem `None`, paths `['findings.lineup_notes.away']`: The White Sox have an elevated swing-and-miss risk and draw walks at an above-average rate
  - NLI (score_only) score `0.10253246873617172`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: Smith's four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin
  - NLI (score_only) score `0.8668769598007202`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Slider.v_break']`: His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin
  - NLI (score_only) score `0.8158361911773682`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.v_break']`: Blubaugh's four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin
  - NLI (score_only) score `0.9337329268455505`, problem `None`, paths `['pitch_movement.home_starter.Sweeper.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sweeper.v_break']`: His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'starters.away_starter.season_summary.strikeouts', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Watch how often Hagen Smith uses his slider to get strikeouts
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.primary_pitch']`: Watch if AJ Blubaugh controls his four-seam fastball to avoid deep counts
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away']`: Watch how the White Sox manage their swing-and-miss risk against the Blubaugh delivery
  - NLI (score_only) score `0.9802634119987488`, problem `None`, paths `['data_confidence.lineup_status', 'venue']`: Probable pitchers are listed for this game at Daikin Park
  - Sentence evidence `['F119', 'F121', 'F153']`: Hagen Smith and AJ Blubaugh start in the AL Wild Card Series
  - Sentence evidence `['F121', 'F151']`: Hagen Smith leads the White Sox pitching staff against the Astros
  - Sentence evidence `['F117', 'F153', 'F183']`: AJ Blubaugh takes the mound for Houston in this opening game
  - Sentence evidence `['F129']`: All stats cover the 2026 regular season through 2026-09-28
  - Sentence evidence `['F141', 'F149', 'F129']`: Hagen Smith enters the series with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning)
  - Sentence evidence `['F173', 'F181', 'F161']`: AJ Blubaugh enters the matchup with a 3.66 ERA and a 1.23 WHIP
  - Sentence evidence `['F127']`: Hagen Smith shows above-average swing-and-miss ability
  - Sentence evidence `['F004', 'F005']`: He uses a four-seam fastball to set up and a slider to finish
  - Sentence evidence `['F202', 'F203', 'F205']`: The Houston Astros lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers
  - Sentence evidence `['F200', 'F198']`: That team has a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate)
  - Sentence evidence `['F006', 'F154']`: AJ Blubaugh shows below-average command which can create deep-count traffic
  - Sentence evidence `['F007', 'F008']`: He uses a four-seam fastball to set up and a sweeper to finish
  - Sentence evidence `['F192', 'F193', 'F195']`: The Chicago White Sox lineup has a .716 OPS against right-handed pitchers
  - Sentence evidence `['F190', 'F188']`: This group has a 24.1% K% and a 9.4% BB%
  - Sentence evidence `['F009']`: The White Sox have an elevated swing-and-miss risk and draw walks at an above-average rate
  - Sentence evidence `['F097', 'F098']`: Smith's four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin
  - Sentence evidence `['F100', 'F101']`: His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin
  - Sentence evidence `['F112', 'F113']`: Blubaugh's four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin
  - Sentence evidence `['F115', 'F116']`: His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin
  - Sentence evidence `['F125', 'F147']`: Watch how often Hagen Smith uses his slider to get strikeouts
  - Sentence evidence `['F154', 'F156']`: Watch if AJ Blubaugh controls his four-seam fastball to avoid deep counts
  - Sentence evidence `['F009']`: Watch how the White Sox manage their swing-and-miss risk against the Blubaugh delivery
  - Sentence evidence `['F001', 'F224']`: Probable pitchers are listed for this game at Daikin Park
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W10.cause'], style findings ['S-1', 'S-4']

**Headline**

Hagen Smith and the Chicago White Sox face AJ Blubaugh and the Houston Astros in the AL Wild Card Series.

**Short summary**

- This is Game 1 of the AL Wild Card Series.
- Hagen Smith starts for the Chicago White Sox.
- AJ Blubaugh starts for the Houston Astros.

**Matchup Summary**

Hagen Smith and AJ Blubaugh face off for Game 1, with all statistics covering the 2026 regular season through Sep 28.

**Hagen Smith vs Houston Astros**

Hagen Smith enters with a 1.29 ERA (earned run average) and a 0.96 WHIP (walks plus hits per inning). He shows above-average swing-and-miss ability. Control data for Hagen Smith is limited with 110 batters faced, where 170 are needed. The Houston Astros lineup against left-handed pitchers carries a .713 OPS (on-base plus slugging), a 21.0% K% (strikeout rate), and a 7.9% BB% (walk rate).

**AJ Blubaugh vs Chicago White Sox**

AJ Blubaugh carries a 3.66 ERA and a 1.23 WHIP. He has below-average command. The Chicago White Sox lineup against right-handed pitchers shows a .716 OPS, a 24.1% K%, and a 9.4% BB%. That group draws walks at an above-average rate and carries an elevated swing-and-miss risk.

**Arsenal Scout**

Hagen Smith utilizes a four-seam fastball primary pitch and a slider second most used pitch. His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin. His slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin. AJ Blubaugh relies on his four-seam fastball as his primary pitch and a sweeper as his second most used pitch. His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin. His sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Hagen Smith uses his slider to finish.
- Watch if AJ Blubaugh encounters deep-count traffic due to his below-average command.
- Watch how the lineups handle the different secondary offerings of each pitcher.

**Data Confidence Note**

Both starters have recorded over 100 pitches in the 2026 regular season through Sep 28.


## opener-824280

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary**; content attempts: 1
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-4', 'S-5', 'S-7', 'W17.length'], tokens {'promptTokenCount': 13316, 'candidatesTokenCount': 947, 'thoughtsTokenCount': 2507, 'totalTokenCount': 16770}
  - style `S-4` token `features` in: This game features right-handed starters Trey Yesavage and Brenan Hanifee.
  - style `S-4` token `maintain` in: They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split.
  - style `S-7` token `in this split` in: They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split.
  - style `S-7` token `in this split` in: That unit has an 18.2% K% and a 7.3% BB% in this split.
  - style `S-4` token `maintains` in: Watch whether the Tigers lineup maintains its walk rate against Yesavage.
  - style `S-5` token `matchup` in: Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup
  - style `W17.length` token `1564` in: (whole report)
  - NLI (score_only) score `0.024038732051849365`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name']`: Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup
  - NLI (score_only) score `0.9899057745933533`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Trey Yesavage has an 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.00135227560531348`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
  - NLI (score_only) score `0.9300380349159241`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Data covers the 2026 regular season through May 14.
  - NLI (score_only) score `0.9876783490180969`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.throws', 'starters.home_starter.throws']`: This game features right-handed starters Trey Yesavage and Brenan Hanifee.
  - NLI (score_only) score `0.1752469539642334`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.limited.strikeout', 'starters.away_starter.sample.thresholds.strikeout', 'starters.away_starter.pitching_profile.swing_miss_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: Trey Yesavage has a limited sample of 57 batters faced, while 170 are needed for a command read and 70 for a strikeout read.
  - NLI (score_only) score `0.9823082685470581`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'glossary.OPS.short']`: The Tigers lineup has a .725 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.2972606122493744`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split.
  - NLI (score_only) score `0.9943217039108276`, problem `None`, paths `['findings.lineup_notes.home']`: The group draws walks at an above-average rate.
  - NLI (score_only) score `0.37706053256988525`, problem `None`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.sample.limited.strikeout', 'starters.home_starter.sample.thresholds.strikeout', 'starters.home_starter.pitching_profile.swing_miss_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through']`: Brenan Hanifee has a limited sample of 33 batters faced, while 170 are needed for a command read and 70 for a strikeout read.
  - NLI (score_only) score `0.9865937232971191`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The Blue Jays offense has a .701 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9660811424255371`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That unit has an 18.2% K% and a 7.3% BB% in this split.
  - NLI (score_only) score `0.9867903590202332`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Trey Yesavage uses a Four-seam as his primary pitch and a Splitter as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.7136785387992859`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0020511019974946976`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Brenan Hanifee relies on his Sinker as his primary pitch and his Slider as his put-away pitch.
  - NLI (score_only) score `0.865646243095398`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sinker.v_break']`: His Sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Yesavage throws his Splitter to finish plate appearances.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch whether the Tigers lineup maintains its walk rate against Yesavage.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.primary_pitch']`: Watch if the Blue Jays can contact Hanifee's Sinker.
  - NLI (score_only) score `0.11176794022321701`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are listed for this matchup.
  - Sentence evidence `['F001', 'F101', 'F133']`: Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup
  - Sentence evidence `['F121', 'F129', 'F013', 'F018']`: Trey Yesavage has an 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning).
  - Sentence evidence `['F153', 'F161']`: Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
  - Sentence evidence `['F109', 'F141']`: Data covers the 2026 regular season through May 14.
  - Sentence evidence `['F101', 'F133', 'F132', 'F164']`: This game features right-handed starters Trey Yesavage and Brenan Hanifee.
  - Sentence evidence `['F111', 'F112', 'F113', 'F119', 'F120']`: Trey Yesavage has a limited sample of 57 batters faced, while 170 are needed for a command read and 70 for a strikeout read.
  - Sentence evidence `['F183', 'F175', 'F017']`: The Tigers lineup has a .725 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F181', 'F179', 'F014', 'F011']`: They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split.
  - Sentence evidence `['F010']`: The group draws walks at an above-average rate.
  - Sentence evidence `['F143', 'F144', 'F145', 'F151', 'F152']`: Brenan Hanifee has a limited sample of 33 batters faced, while 170 are needed for a command read and 70 for a strikeout read.
  - Sentence evidence `['F173', 'F175']`: The Blue Jays offense has a .701 OPS against right-handed pitchers.
  - Sentence evidence `['F171', 'F169']`: That unit has an 18.2% K% and a 7.3% BB% in this split.
  - Sentence evidence `['F104', 'F105', 'F022']`: Trey Yesavage uses a Four-seam as his primary pitch and a Splitter as his put-away pitch (second most used pitch).
  - Sentence evidence `['F080', 'F081']`: His Four-seam moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F136', 'F137']`: Brenan Hanifee relies on his Sinker as his primary pitch and his Slider as his put-away pitch.
  - Sentence evidence `['F095', 'F096']`: His Sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004', 'F105']`: Watch how often Yesavage throws his Splitter to finish plate appearances.
  - Sentence evidence `['F179']`: Watch whether the Tigers lineup maintains its walk rate against Yesavage.
  - Sentence evidence `['F136']`: Watch if the Blue Jays can contact Hanifee's Sinker.
  - Sentence evidence `['F001']`: Probable pitchers are listed for this matchup.
- Length: rules 2330 characters; shown text 1572 characters.

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

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `S-4` `features`, `S-4` `maintain`, `S-7` `in this split`, `S-7` `in this split`, `S-4` `maintains`, `S-5` `matchup`, `W17.length` `1564`

**Headline**

Trey Yesavage faces Brenan Hanifee in Blue Jays and Tigers matchup

**Short summary**

- Trey Yesavage has an 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning).
- Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
- Data covers the 2026 regular season through May 14.

**Matchup Summary**

This game features right-handed starters Trey Yesavage and Brenan Hanifee.

**Trey Yesavage vs Detroit Tigers**

Trey Yesavage has a limited sample of 57 batters faced, while 170 are needed for a command read and 70 for a strikeout read. The Tigers lineup has a .725 OPS (on-base plus slugging) against right-handed pitchers. They maintain a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split. The group draws walks at an above-average rate.

**Brenan Hanifee vs Toronto Blue Jays**

Brenan Hanifee has a limited sample of 33 batters faced, while 170 are needed for a command read and 70 for a strikeout read. The Blue Jays offense has a .701 OPS against right-handed pitchers. That unit has an 18.2% K% and a 7.3% BB% in this split.

**Arsenal Scout**

Trey Yesavage uses a Four-seam as his primary pitch and a Splitter as his put-away pitch (second most used pitch). His Four-seam moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. Brenan Hanifee relies on his Sinker as his primary pitch and his Slider as his put-away pitch. His Sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Yesavage throws his Splitter to finish plate appearances.
- Watch whether the Tigers lineup maintains its walk rate against Yesavage.
- Watch if the Blue Jays can contact Hanifee's Sinker.

**Data Confidence Note**

Probable pitchers are listed for this matchup.


## opener-823769

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 14771, 'candidatesTokenCount': 1249, 'thoughtsTokenCount': 319, 'totalTokenCount': 16339}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W4.topic', 'W15.outcome', 'W2.comparison'], style findings ['S-2', 'S-4', 'S-7', 'W11.expansion', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14800, 'candidatesTokenCount': 1156, 'thoughtsTokenCount': 383, 'totalTokenCount': 16339}
  - gate `W1.number` token `two` in: This duel at American Family Field features two starters with contrasting pitch preferences.
  - gate `W4.topic` token `Family` in: This duel at American Family Field features two starters with contrasting pitch preferences.
  - gate `W15.outcome` token `strikeout` in: Watch whether Ryan Rolison uses his slider often in strikeout counts.
  - gate `W2.comparison` token `below` in: Control data for both Ryan Rolison and Brandon Woodruff is limited, as both are below the 170 batters faced threshold.
  - style `W11.expansion` token `ERA` in: Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27.
  - style `W11.expansion` token `WHIP` in: Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27.
  - style `W11.expansion` token `OPS` in: Ryan Rolison faces a Milwaukee lineup that has a .682 OPS (on-base plus slugging) against left-handed pitchers.
  - style `W11.expansion` token `K%` in: The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate).
  - style `W11.expansion` token `BB%` in: The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate).
  - style `S-7` token `over the same period` in: Brandon Woodruff carries a 3.00 ERA and a 0.89 WHIP over the same period.
  - style `S-4` token `feature` in: Both starters feature above-average swing-and-miss ability.
  - style `S-4` token `features` in: This duel at American Family Field features two starters with contrasting pitch preferences.
  - style `S-4` token `maintain` in: Watch if the Cubs hitters maintain their plate discipline against the Milwaukee starter.
  - style `S-2` token `This team` in: This team also draws walks at an above-average rate.
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1462` in: (whole report)
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'starters.home_starter.name', 'starters.home_starter.team', 'status']`: Ryan Rolison starts for the Cubs against Brandon Woodruff and the Brewers.
  - NLI (score_only) score `0.8591620922088623`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27.
  - NLI (score_only) score `0.09784054011106491`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Brandon Woodruff carries a 3.00 ERA and a 0.89 WHIP over the same period.
  - NLI (score_only) score `0.02023386023938656`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Both starters feature above-average swing-and-miss ability.
  - NLI (score_only) score `0.9509550929069519`, problem `None`, paths `['venue', 'starters.away_starter.pitching_profile.style_label', 'starters.home_starter.pitching_profile.style_label']`: This duel at American Family Field features two starters with contrasting pitch preferences.
  - NLI (score_only) score `0.99181067943573`, problem `None`, paths `['starters.away_starter.name', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand']`: Ryan Rolison faces a Milwaukee lineup that has a .682 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9889531135559082`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number']`: The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate).
  - NLI (score_only) score `0.9954378008842468`, problem `None`, paths `['findings.lineup_notes.home']`: That group draws walks at an above-average rate.
  - NLI (score_only) score `0.9958608746528625`, problem `None`, paths `['starters.home_starter.name', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: Brandon Woodruff meets a Cubs offense with a .734 OPS against right-handed pitchers.
  - NLI (score_only) score `0.8942636251449585`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: The Chicago lineup has a 21.2% K% and an 11.4% BB% in those matchups.
  - NLI (score_only) score `0.03754136711359024`, problem `None`, paths `['findings.lineup_notes.away']`: This team also draws walks at an above-average rate.
  - NLI (score_only) score `0.960527241230011`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Ryan Rolison primarily throws his four-seam fastball and uses his slider as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.0016506222309544683`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Brandon Woodruff relies on his four-seam fastball and uses his changeup as his put-away pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch']`: Watch whether Ryan Rolison uses his slider often in strikeout counts.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch how often Brandon Woodruff sequences his four-seam fastball with his changeup.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch if the Cubs hitters maintain their plate discipline against the Milwaukee starter.
  - NLI (score_only) score `0.9405959248542786`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through', 'starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through']`: Control data for both Ryan Rolison and Brandon Woodruff is limited, as both are below the 170 batters faced threshold.
  - Sentence evidence `['F138', 'F168', 'F170', 'F200', 'F202']`: Ryan Rolison starts for the Cubs against Brandon Woodruff and the Brewers.
  - Sentence evidence `['F158', 'F166', 'F162']`: Ryan Rolison enters with a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) for the 2026 regular season through June 27.
  - Sentence evidence `['F190', 'F198', 'F194']`: Brandon Woodruff carries a 3.00 ERA and a 0.89 WHIP over the same period.
  - Sentence evidence `['F144', 'F176']`: Both starters feature above-average swing-and-miss ability.
  - Sentence evidence `['F244', 'F143', 'F175']`: This duel at American Family Field features two starters with contrasting pitch preferences.
  - Sentence evidence `['F138', 'F220', 'F222']`: Ryan Rolison faces a Milwaukee lineup that has a .682 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F217', 'F215']`: The Brewers lineup shows a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate).
  - Sentence evidence `['F010']`: That group draws walks at an above-average rate.
  - Sentence evidence `['F170', 'F210', 'F212']`: Brandon Woodruff meets a Cubs offense with a .734 OPS against right-handed pitchers.
  - Sentence evidence `['F208', 'F206']`: The Chicago lineup has a 21.2% K% and an 11.4% BB% in those matchups.
  - Sentence evidence `['F009']`: This team also draws walks at an above-average rate.
  - Sentence evidence `['F141', 'F142', 'F022']`: Ryan Rolison primarily throws his four-seam fastball and uses his slider as his put-away pitch (second most used pitch).
  - Sentence evidence `['F173', 'F174']`: Brandon Woodruff relies on his four-seam fastball and uses his changeup as his put-away pitch.
  - Sentence evidence `['F142']`: Watch whether Ryan Rolison uses his slider often in strikeout counts.
  - Sentence evidence `['F173', 'F174']`: Watch how often Brandon Woodruff sequences his four-seam fastball with his changeup.
  - Sentence evidence `['F206']`: Watch if the Cubs hitters maintain their plate discipline against the Milwaukee starter.
  - Sentence evidence `['F148', 'F150', 'F156', 'F180', 'F182', 'F188']`: Control data for both Ryan Rolison and Brandon Woodruff is limited, as both are below the 170 batters faced threshold.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Ryan Rolison faces Brandon Woodruff at American Family Field

**Short summary**

- Ryan Rolison and Brandon Woodruff lead their teams as probable pitchers for this game.
- Rolison for the Chicago Cubs carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) over the 2026 regular season through 2026-06-27.
- Woodruff for the Milwaukee Brewers has a 3.00 ERA and a 0.89 WHIP over the same period.

**Matchup Summary**

This matchup features two pitchers with above-average swing-and-miss ability.

**Ryan Rolison vs Milwaukee Brewers**

The Brewers lineup facing left-handed pitchers like Rolison maintains a .682 OPS (on-base plus slugging), a 21.8% K% (strikeout rate), and a 10.3% BB% (walk rate) through 2026-06-27. This group draws walks at an above-average rate.

**Brandon Woodruff vs Chicago Cubs**

The Cubs lineup facing right-handed pitchers like Woodruff shows a .734 OPS, a 21.2% K%, and an 11.4% BB% through 2026-06-27. The Cubs lineup also draws walks at an above-average rate.

**Arsenal Scout**

Rolison uses a Four-seam as his primary pitch and a Slider as his put-away pitch (second most used pitch). His Four-seam moves 2.0 in. sideways and 15.1 in. up compared with a pitch thrown without spin. Woodruff relies on his Four-seam as his primary pitch and his Changeup as his put-away pitch. His Four-seam moves 4.6 in. sideways and 18.1 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Rolison uses his slider to close out plate appearances.
- Watch whether Woodruff utilizes his changeup to challenge opposing hitters.
- Watch how both teams manage plate discipline given their tendencies to draw walks.

**Data Confidence Note**

Control data for both Ryan Rolison and Brandon Woodruff is limited.


## limited-823836

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary**; content attempts: 1
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-1', 'S-2', 'S-4', 'W11.expansion', 'W11.repeat'], tokens {'promptTokenCount': 14552, 'candidatesTokenCount': 928, 'thoughtsTokenCount': 1905, 'totalTokenCount': 17385}
  - style `W11.expansion` token `ERA` in: Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - style `W11.expansion` token `WHIP` in: Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - style `W11.expansion` token `OPS` in: The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - style `W11.repeat` token `OPS` in: The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - style `W11.expansion` token `K%` in: That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate).
  - style `W11.repeat` token `K%` in: This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate).
  - style `W11.expansion` token `BB%` in: That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate).
  - style `W11.repeat` token `BB%` in: This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate).
  - style `S-1` token `2026 regular season through Aug 6` in: The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - style `S-4` token `features` in: This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
  - style `S-2` token `This group` in: This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate).
  - NLI (score_only) score `0.002880386309698224`, problem `None`, paths `['data_confidence.lineup_status', 'venue']`: George Klassen and Tyler Phillips prepare for a matchup at loanDepot park.
  - NLI (score_only) score `0.0006064147455617785`, problem `None`, paths `['data_confidence.lineup_status', 'venue']`: This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
  - NLI (score_only) score `0.9231953620910645`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.008468554355204105`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Phillips holds a 3.53 ERA and a 1.35 WHIP for the same period.
  - NLI (score_only) score `0.0006064147455617785`, problem `None`, paths `['data_confidence.lineup_status', 'venue']`: This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
  - NLI (score_only) score `0.9883233308792114`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.9937917590141296`, problem `None`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.k_rate_vs_hand']`: That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate).
  - NLI (score_only) score `0.9928332567214966`, problem `None`, paths `['findings.lineup_notes.away']`: The team has an elevated swing-and-miss risk.
  - NLI (score_only) score `0.9900602102279663`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.9952974915504456`, problem `None`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand']`: This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate).
  - NLI (score_only) score `0.975699782371521`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: There is limited data for George Klassen: 32 batters faced, while 170 are needed for a command read.
  - NLI (score_only) score `0.0030840602703392506`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.limited.strikeout', 'starters.away_starter.sample.thresholds.strikeout', 'starters.away_starter.pitching_profile.swing_miss_label']`: There is not enough data to rate his command or swing-and-miss ability.
  - NLI (score_only) score `0.02021089382469654`, problem `None`, paths `['starters.away_starter.pitching_profile.style_label', 'findings.away_starter_strengths']`: George Klassen is a Four-seam-Changeup starter who uses his four-seam fastball to set up and his changeup to finish.
  - NLI (score_only) score `0.021423140540719032`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.04104020446538925`, problem `None`, paths `['starters.home_starter.pitching_profile.style_label', 'findings.home_starter_strengths']`: Tyler Phillips is a Sinker-Sweeper starter who uses his sinker to set up and his sweeper to finish.
  - NLI (score_only) score `0.23427410423755646`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sinker.v_break']`: His sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.0.away_starter.overall']`: Watch how often George Klassen uses his four-seam fastball early in the count.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch if Tyler Phillips throws his sweeper to get hitters out.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'starters.home_starter.throws', 'teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch how the Angels lineup manages the swing-and-miss risk against the right-handed starter.
  - NLI (score_only) score `0.7300093173980713`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are listed for this game.
  - Sentence evidence `['F001', 'F241']`: George Klassen and Tyler Phillips prepare for a matchup at loanDepot park.
  - Sentence evidence `['F001', 'F241']`: This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
  - Sentence evidence `['F155', 'F163', 'F143']`: Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
  - Sentence evidence `['F187', 'F195', 'F175']`: Phillips holds a 3.53 ERA and a 1.35 WHIP for the same period.
  - Sentence evidence `['F001', 'F241']`: This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
  - Sentence evidence `['F207', 'F208']`: The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - Sentence evidence `['F203', 'F205']`: That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate).
  - Sentence evidence `['F009']`: The team has an elevated swing-and-miss risk.
  - Sentence evidence `['F217', 'F218']`: The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6.
  - Sentence evidence `['F213', 'F215']`: This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate).
  - Sentence evidence `['F145', 'F147', 'F153']`: There is limited data for George Klassen: 32 batters faced, while 170 are needed for a command read.
  - Sentence evidence `['F145', 'F146']`: There is not enough data to rate his command or swing-and-miss ability.
  - Sentence evidence `['F140', 'F004']`: George Klassen is a Four-seam-Changeup starter who uses his four-seam fastball to set up and his changeup to finish.
  - Sentence evidence `['F108', 'F109']`: His four-seam fastball moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F172', 'F007']`: Tyler Phillips is a Sinker-Sweeper starter who uses his sinker to set up and his sweeper to finish.
  - Sentence evidence `['F123', 'F124']`: His sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F024', 'F025']`: Watch how often George Klassen uses his four-seam fastball early in the count.
  - Sentence evidence `['F084', 'F171']`: Watch if Tyler Phillips throws his sweeper to get hitters out.
  - Sentence evidence `['F009', 'F198', 'F209']`: Watch how the Angels lineup manages the swing-and-miss risk against the right-handed starter.
  - Sentence evidence `['F001']`: Probable pitchers are listed for this game.
- Length: rules 2196 characters; shown text 1809 characters.

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

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `W11.expansion` `ERA`, `W11.expansion` `WHIP`, `W11.expansion` `OPS`, `W11.repeat` `OPS`, `W11.expansion` `K%`, `W11.repeat` `K%`, `W11.expansion` `BB%`, `W11.repeat` `BB%`, `S-1` `2026 regular season through Aug 6`, `S-4` `features`, `S-2` `This group`

**Headline**

George Klassen and Tyler Phillips prepare for a matchup at loanDepot park.

**Short summary**

- This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.
- Klassen enters with an 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning) over the 2026 regular season through Aug 6.
- Phillips holds a 3.53 ERA and a 1.35 WHIP for the same period.

**Matchup Summary**

This matchup features starting pitchers George Klassen and Tyler Phillips in a contest at loanDepot park.

**George Klassen vs Miami Marlins**

The Angels lineup has a .687 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. That group shows a 24.9% K% (strikeout rate) and an 8.3% BB% (walk rate). The team has an elevated swing-and-miss risk.

**Tyler Phillips vs Los Angeles Angels**

The Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. This group carries a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate). There is limited data for George Klassen: 32 batters faced, while 170 are needed for a command read. There is not enough data to rate his command or swing-and-miss ability.

**Arsenal Scout**

George Klassen is a Four-seam-Changeup starter who uses his four-seam fastball to set up and his changeup to finish. His four-seam fastball moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. Tyler Phillips is a Sinker-Sweeper starter who uses his sinker to set up and his sweeper to finish. His sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often George Klassen uses his four-seam fastball early in the count.
- Watch if Tyler Phillips throws his sweeper to get hitters out.
- Watch how the Angels lineup manages the swing-and-miss risk against the right-handed starter.

**Data Confidence Note**

Probable pitchers are listed for this game.


## limited-825104

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W6.arsenal'], style findings ['S-2', 'W12.scope', 'W14.team', 'W17.length'], tokens {'promptTokenCount': 13990, 'candidatesTokenCount': 928, 'thoughtsTokenCount': 1459, 'totalTokenCount': 16377}
  - style `S-2` token `That group` in: That group has a 19.4% K% and a 9.5% BB%.
  - gate `W6.arsenal` token `None` in: (whole report)
  - style `W14.team` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1519` in: (whole report)
  - NLI (score_only) score `0.6355159282684326`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Bryce Elder and Michael Soroka match up in Arizona.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'venue']`: Bryce Elder starts for Atlanta at Chase Field.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.name', 'starters.home_starter.team']`: Michael Soroka pitches for Arizona.
  - NLI (score_only) score `0.0008227683138102293`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Both starters enter the game with stats from the 2026 regular season through April 3.
  - NLI (score_only) score `0.9944977164268494`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: This report covers the 2026 regular season through April 3.
  - NLI (score_only) score `0.9795747399330139`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Bryce Elder has a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.99033522605896`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The Arizona lineup has a .653 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9210413694381714`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group has a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate).
  - NLI (score_only) score `0.01418213825672865`, problem `None`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.sample.limited.control', 'starters.away_starter.pitching_profile.command_label']`: Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a full read.
  - NLI (score_only) score `0.009439322166144848`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Michael Soroka carries a 0.00 ERA and a 1.00 WHIP.
  - NLI (score_only) score `0.9889057874679565`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The Atlanta lineup has a .827 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9732820391654968`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That group has a 19.4% K% and a 9.5% BB%.
  - NLI (score_only) score `0.0812108963727951`, problem `None`, paths `['starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.sample.limited.control', 'starters.home_starter.pitching_profile.command_label']`: Control data for Michael Soroka is limited, with 20 batters faced and 170 required for a complete profile.
  - NLI (score_only) score `0.9875499606132507`, problem `None`, paths `['findings.lineup_notes.away']`: The Atlanta Braves have a strong OPS against this pitcher's hand and draw walks at an above-average rate.
  - NLI (score_only) score `0.208452969789505`, problem `None`, paths `['findings.away_style', 'starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch']`: Bryce Elder uses a Sinker to set up and a Slider to finish.
  - NLI (score_only) score `0.8755736947059631`, problem `None`, paths `['pitch_movement.away_starter.Sinker.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Sinker.v_break']`: His Sinker moves 14.6 in. sideways and 7.6 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.03635253384709358`, problem `None`, paths `['findings.home_style', 'starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Michael Soroka uses a Slurve to set up and a Four-seam to finish.
  - NLI (score_only) score `0.18480685353279114`, problem `None`, paths `['pitch_movement.home_starter.Slurve.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slurve.v_break']`: His Slurve moves 9.6 in. sideways and 6.8 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Bryce Elder relies on his Sinker.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch if Michael Soroka uses his Slurve throughout the game.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch if the Atlanta lineup sustains its walk rate.
  - NLI (score_only) score `0.6574479341506958`, problem `None`, paths `['data_confidence.lineup_status']`: The current pitcher status for this game is probable pitchers.
  - Sentence evidence `['F002', 'F121', 'F153', 'F224']`: Bryce Elder and Michael Soroka match up in Arizona.
  - Sentence evidence `['F121', 'F151', 'F224']`: Bryce Elder starts for Atlanta at Chase Field.
  - Sentence evidence `['F153', 'F183']`: Michael Soroka pitches for Arizona.
  - Sentence evidence `['F129', 'F161']`: Both starters enter the game with stats from the 2026 regular season through April 3.
  - Sentence evidence `['F129']`: This report covers the 2026 regular season through April 3.
  - Sentence evidence `['F141', 'F149', 'F013', 'F018']`: Bryce Elder has a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning).
  - Sentence evidence `['F203', 'F205', 'F017']`: The Arizona lineup has a .653 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F201', 'F199', 'F014', 'F011']`: That group has a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate).
  - Sentence evidence `['F133', 'F139', 'F131']`: Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a full read.
  - Sentence evidence `['F173', 'F181']`: Michael Soroka carries a 0.00 ERA and a 1.00 WHIP.
  - Sentence evidence `['F193', 'F195']`: The Atlanta lineup has a .827 OPS against right-handed pitchers.
  - Sentence evidence `['F191', 'F189']`: That group has a 19.4% K% and a 9.5% BB%.
  - Sentence evidence `['F165', 'F171', 'F163']`: Control data for Michael Soroka is limited, with 20 batters faced and 170 required for a complete profile.
  - Sentence evidence `['F009']`: The Atlanta Braves have a strong OPS against this pitcher's hand and draw walks at an above-average rate.
  - Sentence evidence `['F005', 'F124', 'F125']`: Bryce Elder uses a Sinker to set up and a Slider to finish.
  - Sentence evidence `['F100', 'F101']`: His Sinker moves 14.6 in. sideways and 7.6 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F008', 'F156', 'F157']`: Michael Soroka uses a Slurve to set up and a Four-seam to finish.
  - Sentence evidence `['F118', 'F119']`: His Slurve moves 9.6 in. sideways and 6.8 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F024']`: Watch how often Bryce Elder relies on his Sinker.
  - Sentence evidence `['F084']`: Watch if Michael Soroka uses his Slurve throughout the game.
  - Sentence evidence `['F189']`: Watch if the Atlanta lineup sustains its walk rate.
  - Sentence evidence `['F001']`: The current pitcher status for this game is probable pitchers.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 14085, 'candidatesTokenCount': 826, 'thoughtsTokenCount': 1129, 'totalTokenCount': 16040}
  - gate `W17.structure` token `None` in: (whole report)
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Bryce Elder and Michael Soroka match up at Chase Field

**Short summary**

- Bryce Elder and Michael Soroka start the game for their respective teams.
- Both starters enter the matchup with limited sample sizes in the 2026 regular season through 2026-04-03.
- The Atlanta Braves and Arizona Diamondbacks lineups prepare to face right-handed pitching.
- This is a matchup of starting pitchers.

**Matchup Summary**

Bryce Elder of the Braves and Michael Soroka of the Diamondbacks face off on April 4, 2026.

**Bryce Elder vs Arizona Diamondbacks**

Bryce Elder carries a 0.00 ERA (earned run average) and a 1.00 WHIP (walks plus hits per inning) in the 2026 regular season through 2026-04-03. The Arizona lineup holds a .653 OPS (on-base plus slugging) against right-handed pitchers, with a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate).

**Michael Soroka vs Atlanta Braves**

Michael Soroka shows a 0.00 ERA and a 1.00 WHIP over his limited sample of games in the same period. The Atlanta offense produces a .827 OPS, a 19.4% K% and a 9.5% BB% against right-handed pitchers.

**Arsenal Scout**

Bryce Elder uses a sinker as his primary pitch and a slider as his put-away pitch, but his arsenal data is limited. Michael Soroka relies on a slurve as his primary pitch and a four-seam fastball as his put-away pitch, with limited arsenal data.

**Three Things to Watch**

- Watch whether Bryce Elder uses his sinker to set up hitters early in counts.
- Watch how Michael Soroka mixes his slurve and four-seam fastball throughout the contest.
- Watch if the Atlanta lineup sustains its OPS against right-handed pitchers.

**Data Confidence Note**

The game features probable pitchers.


## limited-823863

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.entity', 'W8.value', 'W6.unsaid'], style findings ['S-2', 'S-5', 'W12.scope', 'W14.starter', 'W17.length'], tokens {'promptTokenCount': 14494, 'candidatesTokenCount': 960, 'thoughtsTokenCount': 1820, 'totalTokenCount': 17274}
  - gate `W1.entity` token `Eury Perez` in: Tobias Myers and Eury Perez start at loanDepot park
  - gate `W1.entity` token `Eury Perez` in: Eury Perez takes the mound for the Marlins against the visiting New York Mets.
  - gate `W1.entity` token `Eury Perez` in: Tobias Myers and Eury Perez each start this game on 2026-05-22.
  - gate `W1.entity` token `Eury Perez` in: Eury Perez has a 5.33 ERA and a 1.41 WHIP.
  - gate `W8.value` token `None` in: His splitter moves 9.6 in. sideways and 8.4 in. down compared with a pitch thrown without spin.
  - gate `W1.entity` token `Eury Perez` in: Eury Perez uses a four-seam fastball 49.3% of the time and a slider 15.0% of the time.
  - gate `W1.entity` token `Eury Perez` in: Watch if Eury Perez can control his slider with his below-average command.
  - style `S-2` token `That lineup` in: That lineup has a 20.7% K% and an 8.1% BB%.
  - style `S-5` token `Perez` in: Tobias Myers and Eury Perez start at loanDepot park
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W14.starter` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1517` in: (whole report)
  - NLI (score_only) score `0.0022433868143707514`, problem `None`, paths `['date', 'venue']`: Tobias Myers and Eury Perez start at loanDepot park
  - NLI (score_only) score `0.5857741236686707`, problem `None`, paths `['starters.away_starter.name', 'teams.home.name', 'venue']`: Tobias Myers faces the Miami Marlins at loanDepot park.
  - NLI (score_only) score `0.4385729730129242`, problem `None`, paths `['starters.home_starter.name', 'teams.away.name']`: Eury Perez takes the mound for the Marlins against the visiting New York Mets.
  - NLI (score_only) score `0.00924675166606903`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All season figures cover the 2026 regular season through 2026-05-21.
  - NLI (score_only) score `0.4654318690299988`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name']`: Tobias Myers and Eury Perez each start this game on 2026-05-22.
  - NLI (score_only) score `0.9914305806159973`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.innings', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning) over 29.0 innings.
  - NLI (score_only) score `0.9900679588317871`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: He shows average swing-and-miss ability.
  - NLI (score_only) score `0.993750274181366`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The Miami Marlins offense has a .697 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9171276688575745`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group has a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - NLI (score_only) score `0.0007993213948793709`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Eury Perez has a 5.33 ERA and a 1.41 WHIP.
  - NLI (score_only) score `0.889133870601654`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows above-average swing-and-miss ability and below-average command.
  - NLI (score_only) score `0.9870775938034058`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The New York Mets offense has a .659 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9751772284507751`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That lineup has a 20.7% K% and an 8.1% BB%.
  - NLI (score_only) score `0.1808214634656906`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Tobias Myers uses a four-seam fastball 50.1% of the time and a splitter 21.4% of the time.
  - NLI (score_only) score `0.00570359081029892`, problem `None`, paths `['pitch_movement.away_starter.Splitter.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Splitter.v_break', 'glossary.Break.short']`: His splitter moves 9.6 in. sideways and 8.4 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `0.894268810749054`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.2.home_starter.overall']`: Eury Perez uses a four-seam fastball 49.3% of the time and a slider 15.0% of the time.
  - NLI (score_only) score `0.9479268789291382`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break', 'glossary.Break.short']`: His slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths']`: Watch how often Tobias Myers uses his four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks', 'starters.home_starter.pitching_profile.command_label']`: Watch if Eury Perez can control his slider with his below-average command.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: Watch whether the New York Mets offense draws walks against the Miami pitching staff.
  - NLI (score_only) score `0.006804867181926966`, problem `None`, paths `['data_confidence.lineup_status']`: Data confidence for this game is based on probable pitchers.
  - Sentence evidence `['F002', 'F235']`: Tobias Myers and Eury Perez start at loanDepot park
  - Sentence evidence `['F129', 'F205', 'F235']`: Tobias Myers faces the Miami Marlins at loanDepot park.
  - Sentence evidence `['F161', 'F195']`: Eury Perez takes the mound for the Marlins against the visiting New York Mets.
  - Sentence evidence `['F137', 'F169', 'F202', 'F212']`: All season figures cover the 2026 regular season through 2026-05-21.
  - Sentence evidence `['F002', 'F129', 'F161']`: Tobias Myers and Eury Perez each start this game on 2026-05-22.
  - Sentence evidence `['F149', 'F152', 'F157', 'F013', 'F018']`: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning) over 29.0 innings.
  - Sentence evidence `['F135']`: He shows average swing-and-miss ability.
  - Sentence evidence `['F211', 'F203', 'F213', 'F017']`: The Miami Marlins offense has a .697 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F209', 'F207', 'F014', 'F011']`: That group has a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - Sentence evidence `['F181', 'F189']`: Eury Perez has a 5.33 ERA and a 1.41 WHIP.
  - Sentence evidence `['F162', 'F167']`: He shows above-average swing-and-miss ability and below-average command.
  - Sentence evidence `['F201', 'F203']`: The New York Mets offense has a .659 OPS against right-handed pitchers.
  - Sentence evidence `['F199', 'F197']`: That lineup has a 20.7% K% and an 8.1% BB%.
  - Sentence evidence `['F025', 'F036']`: Tobias Myers uses a four-seam fastball 50.1% of the time and a splitter 21.4% of the time.
  - Sentence evidence `['F111', 'F112', 'F012']`: His splitter moves 9.6 in. sideways and 8.4 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F030', 'F052']`: Eury Perez uses a four-seam fastball 49.3% of the time and a slider 15.0% of the time.
  - Sentence evidence `['F123', 'F124', 'F012']`: His slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004']`: Watch how often Tobias Myers uses his four-seam fastball to set up hitters.
  - Sentence evidence `['F006', 'F162']`: Watch if Eury Perez can control his slider with his below-average command.
  - Sentence evidence `['F197', 'F196']`: Watch whether the New York Mets offense draws walks against the Miami pitching staff.
  - Sentence evidence `['F001']`: Data confidence for this game is based on probable pitchers.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W7.missing'], style findings ['S-4', 'W11.expansion', 'W12.scope', 'W14.team', 'W17.length'], tokens {'promptTokenCount': 14646, 'candidatesTokenCount': 988, 'thoughtsTokenCount': 1198, 'totalTokenCount': 16832}
  - gate `W7.missing` token `starters.away_starter.pitching_profile.command_label` in: Watch whether Tobias Myers can maintain his command throughout the game.
  - style `W11.expansion` token `ERA` in: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning).
  - style `W11.expansion` token `WHIP` in: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning).
  - style `W11.expansion` token `OPS` in: The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers.
  - style `W11.expansion` token `K%` in: That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - style `W11.expansion` token `BB%` in: That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - style `S-4` token `maintain` in: Watch whether Tobias Myers can maintain his command throughout the game.
  - style `W14.team` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1607` in: (whole report)
  - NLI (score_only) score `0.0050980630330741405`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Tobias Myers faces Eury Pérez in Miami
  - NLI (score_only) score `0.3033984899520874`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Tobias Myers and Eury Pérez pitch at loanDepot park.
  - NLI (score_only) score `0.009136723354458809`, problem `None`, paths `['findings.away_style', 'findings.home_style']`: The starters bring distinct styles to the mound.
  - NLI (score_only) score `0.07800313830375671`, problem `None`, paths `['teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Both lineups prepare for right-handed starters.
  - NLI (score_only) score `0.007965142838656902`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: These figures cover the 2026 regular season through 2026-05-21.
  - NLI (score_only) score `0.002579980995506048`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip']`: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9900679588317871`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: He shows average swing-and-miss ability.
  - NLI (score_only) score `0.9262128472328186`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: Control data for Myers is limited: 115 batters faced, and 170 are needed for a full reading.
  - NLI (score_only) score `0.983944296836853`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand']`: The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9927847385406494`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number']`: That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - NLI (score_only) score `0.0013421822804957628`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Eury Pérez has a 5.33 ERA and 1.41 WHIP.
  - NLI (score_only) score `0.889133870601654`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows above-average swing-and-miss ability and below-average command.
  - NLI (score_only) score `0.988878607749939`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The New York lineup has a .659 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9721323847770691`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: Those hitters have a 20.7% K% and an 8.1% BB%.
  - NLI (score_only) score `0.7826915383338928`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Myers uses his Four-seam fastball 50.1% of the time.
  - NLI (score_only) score `0.967849850654602`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: It moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.7007609009742737`, problem `None`, paths `['pitch_movement.away_starter.Splitter.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Splitter.v_break']`: His Splitter moves 9.6 in. sideways and 8.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.01724090985953808`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Pérez uses a Four-seam fastball 49.3% of the time.
  - NLI (score_only) score `0.9502846002578735`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.v_break']`: It moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.8688019514083862`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break']`: His Slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label']`: Watch whether Tobias Myers can maintain his command throughout the game.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch how often Eury Pérez throws his Four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks']`: Watch if the New York lineup capitalizes on deep-count traffic created by Eury Pérez.
  - NLI (score_only) score `0.9920420050621033`, problem `None`, paths `['data_confidence.lineup_status', 'date']`: This report uses probable pitchers for the game on 2026-05-22.
  - Sentence evidence `['F001', 'F129', 'F161', 'F235']`: Tobias Myers faces Eury Pérez in Miami
  - Sentence evidence `['F001', 'F129', 'F161', 'F235']`: Tobias Myers and Eury Pérez pitch at loanDepot park.
  - Sentence evidence `['F005', 'F008']`: The starters bring distinct styles to the mound.
  - Sentence evidence `['F203', 'F213']`: Both lineups prepare for right-handed starters.
  - Sentence evidence `['F137', 'F169', 'F202', 'F212']`: These figures cover the 2026 regular season through 2026-05-21.
  - Sentence evidence `['F149', 'F157']`: Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning).
  - Sentence evidence `['F135']`: He shows average swing-and-miss ability.
  - Sentence evidence `['F139', 'F141', 'F147']`: Control data for Myers is limited: 115 batters faced, and 170 are needed for a full reading.
  - Sentence evidence `['F211', 'F213']`: The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F208', 'F206']`: That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - Sentence evidence `['F181', 'F189']`: Eury Pérez has a 5.33 ERA and 1.41 WHIP.
  - Sentence evidence `['F162', 'F167']`: He shows above-average swing-and-miss ability and below-average command.
  - Sentence evidence `['F201', 'F203']`: The New York lineup has a .659 OPS against right-handed pitchers.
  - Sentence evidence `['F198', 'F196']`: Those hitters have a 20.7% K% and an 8.1% BB%.
  - Sentence evidence `['F025']`: Myers uses his Four-seam fastball 50.1% of the time.
  - Sentence evidence `['F105', 'F106']`: It moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F111', 'F112']`: His Splitter moves 9.6 in. sideways and 8.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F030']`: Pérez uses a Four-seam fastball 49.3% of the time.
  - Sentence evidence `['F120', 'F121']`: It moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F123', 'F124']`: His Slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F139']`: Watch whether Tobias Myers can maintain his command throughout the game.
  - Sentence evidence `['F030']`: Watch how often Eury Pérez throws his Four-seam fastball to set up hitters.
  - Sentence evidence `['F006']`: Watch if the New York lineup capitalizes on deep-count traffic created by Eury Pérez.
  - Sentence evidence `['F001', 'F002']`: This report uses probable pitchers for the game on 2026-05-22.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W7.missing'], style findings ['S-4', 'W11.expansion', 'W12.scope', 'W14.team', 'W17.length']

**Headline**

Tobias Myers faces Eury Pérez in Miami

**Short summary**

- Tobias Myers and Eury Pérez pitch at loanDepot park.
- The starters bring distinct styles to the mound.
- Both lineups prepare for right-handed starters.

**Matchup Summary**

These figures cover the 2026 regular season through 2026-05-21.

**Tobias Myers vs Miami Marlins**

Tobias Myers has a 3.41 ERA (earned run average) and a 1.03 WHIP (walks plus hits per inning). He shows average swing-and-miss ability. Control data for Myers is limited: 115 batters faced, and 170 are needed for a full reading. The Miami lineup has a .697 OPS (on-base plus slugging) against right-handed pitchers. That group carries a 20.9% K% (strikeout rate) and an 8.8% BB% (walk rate).

**Eury Pérez vs New York Mets**

Eury Pérez has a 5.33 ERA and 1.41 WHIP. He shows above-average swing-and-miss ability and below-average command. The New York lineup has a .659 OPS against right-handed pitchers. Those hitters have a 20.7% K% and an 8.1% BB%.

**Arsenal Scout**

Myers uses his Four-seam fastball 50.1% of the time. It moves 4.6 in. sideways and 20.0 in. up compared with a pitch thrown without spin. His Splitter moves 9.6 in. sideways and 8.4 in. up compared with a pitch thrown without spin. Pérez uses a Four-seam fastball 49.3% of the time. It moves 11.5 in. sideways and 18.0 in. up compared with a pitch thrown without spin. His Slider moves 2.7 in. sideways and 4.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Tobias Myers can maintain his command throughout the game.
- Watch how often Eury Pérez throws his Four-seam fastball to set up hitters.
- Watch if the New York lineup capitalizes on deep-count traffic created by Eury Pérez.

**Data Confidence Note**

This report uses probable pitchers for the game on 2026-05-22.


## veteran-824027

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W0.sentence', 'W12.time'], style findings ['S-1', 'S-5', 'W17.length'], tokens {'promptTokenCount': 15328, 'candidatesTokenCount': 899, 'thoughtsTokenCount': 1634, 'totalTokenCount': 17861}
  - gate `W0.sentence` token `None` in: Kyle Freeland and Jos&eacute; Soriano take the mound for a starting pitching matchup on June 1.
  - gate `W0.sentence` token `None` in: Kyle Freeland and Jos&eacute; Soriano bring distinct pitching profiles to the 2026 regular season through May 31.
  - gate `W0.sentence` token `None` in: Kyle Freeland and Jos&eacute; Soriano lead their respective staffs into the matchup on June 1.
  - gate `W0.sentence` token `None` in: Jos&eacute; Soriano has a 2.65 ERA and a 1.15 WHIP.
  - gate `W0.sentence` token `None` in: Jos&eacute; Soriano uses a Sinker to set up and a Curveball to finish.
  - gate `W0.sentence` token `None` in: Watch whether Jos&eacute; Soriano can manage his command with the Sinker.
  - gate `W12.time` token `Pitching and usage data for both starters is available through the 2026 regular season through May 31.` in: Pitching and usage data for both starters is available through the 2026 regular season through May 31.
  - style `S-1` token `2026 regular season through May 31` in: Pitching and usage data for both starters is available through the 2026 regular season through May 31.
  - style `S-5` token `Jos` in: Kyle Freeland and Jos&eacute; Soriano take the mound for a starting pitching matchup on June 1.
  - style `S-5` token `June` in: Kyle Freeland and Jos&eacute; Soriano take the mound for a starting pitching matchup on June 1.
  - style `W17.length` token `1566` in: (whole report)
  - NLI (score_only) score `0.2548159062862396`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name']`: Kyle Freeland and Jos&eacute; Soriano take the mound for a starting pitching matchup on June 1.
  - NLI (score_only) score `0.000842440640553832`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Kyle Freeland and Jos&eacute; Soriano bring distinct pitching profiles to the 2026 regular season through May 31.
  - NLI (score_only) score `0.9972520470619202`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'glossary.OPS.short']`: The Colorado Rockies lineup produces a .709 OPS (on-base plus slugging).
  - NLI (score_only) score `0.9935810565948486`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: The Los Angeles Angels lineup produces a .712 OPS.
  - NLI (score_only) score `0.03179996833205223`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name']`: Kyle Freeland and Jos&eacute; Soriano lead their respective staffs into the matchup on June 1.
  - NLI (score_only) score `0.9913239479064941`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Kyle Freeland has an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9793742895126343`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows solid command and average swing-and-miss ability.
  - NLI (score_only) score `0.8953003287315369`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: The Los Angeles Angels lineup has a 24.3% K% (strikeout rate) and a 10.4% BB% (walk rate).
  - NLI (score_only) score `0.9960110187530518`, problem `None`, paths `['findings.lineup_notes.home']`: That group carries an elevated swing-and-miss risk and draws walks at an above-average rate.
  - NLI (score_only) score `0.001440173014998436`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Jos&eacute; Soriano has a 2.65 ERA and a 1.15 WHIP.
  - NLI (score_only) score `0.9789835810661316`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows below-average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9389433264732361`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: The Colorado Rockies lineup has a 22.7% K% and an 8.3% BB%.
  - NLI (score_only) score `0.9966890215873718`, problem `None`, paths `['findings.away_style']`: Kyle Freeland uses a Four-seam to set up and a Curveball to finish.
  - NLI (score_only) score `0.9596406817436218`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9931240677833557`, problem `None`, paths `['findings.home_style']`: Jos&eacute; Soriano uses a Sinker to set up and a Curveball to finish.
  - NLI (score_only) score `0.897229790687561`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sinker.v_break']`: His Sinker moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.primary_pitch']`: Watch how often Kyle Freeland throws his Four-seam.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.primary_pitch']`: Watch whether Jos&eacute; Soriano can manage his command with the Sinker.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home']`: Watch how the Los Angeles Angels lineup manages their swing-and-miss risk.
  - NLI (score_only) score `0.0021422530990093946`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Pitching and usage data for both starters is available through the 2026 regular season through May 31.
  - Sentence evidence `['F002', 'F146', 'F178']`: Kyle Freeland and Jos&eacute; Soriano take the mound for a starting pitching matchup on June 1.
  - Sentence evidence `['F154', 'F186']`: Kyle Freeland and Jos&eacute; Soriano bring distinct pitching profiles to the 2026 regular season through May 31.
  - Sentence evidence `['F218', 'F017']`: The Colorado Rockies lineup produces a .709 OPS (on-base plus slugging).
  - Sentence evidence `['F228']`: The Los Angeles Angels lineup produces a .712 OPS.
  - Sentence evidence `['F002', 'F146', 'F178']`: Kyle Freeland and Jos&eacute; Soriano lead their respective staffs into the matchup on June 1.
  - Sentence evidence `['F166', 'F174', 'F013', 'F018']`: Kyle Freeland has an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning).
  - Sentence evidence `['F147', 'F152']`: He shows solid command and average swing-and-miss ability.
  - Sentence evidence `['F226', 'F224', 'F014', 'F011']`: The Los Angeles Angels lineup has a 24.3% K% (strikeout rate) and a 10.4% BB% (walk rate).
  - Sentence evidence `['F010']`: That group carries an elevated swing-and-miss risk and draws walks at an above-average rate.
  - Sentence evidence `['F198', 'F206']`: Jos&eacute; Soriano has a 2.65 ERA and a 1.15 WHIP.
  - Sentence evidence `['F179', 'F184']`: He shows below-average command and above-average swing-and-miss ability.
  - Sentence evidence `['F216', 'F214']`: The Colorado Rockies lineup has a 22.7% K% and an 8.3% BB%.
  - Sentence evidence `['F005']`: Kyle Freeland uses a Four-seam to set up and a Curveball to finish.
  - Sentence evidence `['F122', 'F123']`: His Four-seam moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F008']`: Jos&eacute; Soriano uses a Sinker to set up and a Curveball to finish.
  - Sentence evidence `['F137', 'F138']`: His Sinker moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F149']`: Watch how often Kyle Freeland throws his Four-seam.
  - Sentence evidence `['F179', 'F181']`: Watch whether Jos&eacute; Soriano can manage his command with the Sinker.
  - Sentence evidence `['F010']`: Watch how the Los Angeles Angels lineup manages their swing-and-miss risk.
  - Sentence evidence `['F154', 'F186']`: Pitching and usage data for both starters is available through the 2026 regular season through May 31.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.entity'], style findings ['S-1', 'W17.length'], tokens {'promptTokenCount': 15432, 'candidatesTokenCount': 919, 'thoughtsTokenCount': 1734, 'totalTokenCount': 18085}
  - gate `W1.entity` token `June` in: Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026.
  - gate `W1.entity` token `June` in: Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026.
  - style `S-1` token `2026 regular season through May 31` in: Pitching data for both starters is complete and covers the 2026 regular season through May 31.
  - style `W17.length` token `1631` in: (whole report)
  - NLI (score_only) score `0.150007963180542`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'teams.home.name']`: Kyle Freeland faces the Los Angeles Angels as José Soriano starts for the home team
  - NLI (score_only) score `0.9334991574287415`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name']`: Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026.
  - NLI (score_only) score `0.06305211782455444`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Freeland brings an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) to the mound.
  - NLI (score_only) score `0.0071622030809521675`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Soriano enters with a 2.65 ERA and a 1.15 WHIP, with all stats current for the 2026 regular season through May 31.
  - NLI (score_only) score `0.9862869381904602`, problem `None`, paths `['date', 'starters.away_starter.name', 'starters.home_starter.name']`: Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026.
  - NLI (score_only) score `0.9967898726463318`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9880500435829163`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4%.
  - NLI (score_only) score `0.9200180768966675`, problem `None`, paths `['findings.lineup_notes.home']`: The Angels offense has elevated swing-and-miss risk and draws walks at an above-average rate.
  - NLI (score_only) score `0.9943752288818359`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Rockies offense has a .709 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9895846247673035`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That group shows a 22.7% K% and an 8.3% BB%.
  - NLI (score_only) score `0.9833449721336365`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Soriano shows below-average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9708214402198792`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time.
  - NLI (score_only) score `0.11609041690826416`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9597487449645996`, problem `None`, paths `['pitch_mix.5.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.1.home_starter.overall']`: Soriano uses his sinker 27.8% of the time and his curveball 24.8% of the time.
  - NLI (score_only) score `0.9579907059669495`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sinker.v_break']`: The sinker from Soriano moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths', 'findings.away_style']`: Watch how often Freeland uses his four-seam fastball to set up his curveball.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks', 'starters.home_starter.pitching_profile.command_label']`: Watch if Soriano can manage his command, as below-average command can create deep-count traffic.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.1.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how the Angels lineup handles the curveball from Freeland.
  - NLI (score_only) score `0.0023981102276593447`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Pitching data for both starters is complete and covers the 2026 regular season through May 31.
  - Sentence evidence `['F146', 'F178', 'F222']`: Kyle Freeland faces the Los Angeles Angels as José Soriano starts for the home team
  - Sentence evidence `['F002', 'F146', 'F178']`: Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026.
  - Sentence evidence `['F166', 'F174', 'F013', 'F018']`: Freeland brings an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) to the mound.
  - Sentence evidence `['F198', 'F206', 'F202']`: Soriano enters with a 2.65 ERA and a 1.15 WHIP, with all stats current for the 2026 regular season through May 31.
  - Sentence evidence `['F002', 'F146', 'F178']`: Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026.
  - Sentence evidence `['F228', 'F017']`: The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F226', 'F224', 'F014', 'F011']`: Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4%.
  - Sentence evidence `['F010']`: The Angels offense has elevated swing-and-miss risk and draws walks at an above-average rate.
  - Sentence evidence `['F218']`: The Rockies offense has a .709 OPS against right-handed pitchers.
  - Sentence evidence `['F216', 'F214']`: That group shows a 22.7% K% and an 8.3% BB%.
  - Sentence evidence `['F179', 'F184']`: Soriano shows below-average command and above-average swing-and-miss ability.
  - Sentence evidence `['F025', 'F036']`: Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time.
  - Sentence evidence `['F122', 'F123']`: His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F085', 'F041']`: Soriano uses his sinker 27.8% of the time and his curveball 24.8% of the time.
  - Sentence evidence `['F137', 'F138']`: The sinker from Soriano moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004', 'F005']`: Watch how often Freeland uses his four-seam fastball to set up his curveball.
  - Sentence evidence `['F006', 'F179']`: Watch if Soriano can manage his command, as below-average command can create deep-count traffic.
  - Sentence evidence `['F036', 'F150']`: Watch how the Angels lineup handles the curveball from Freeland.
  - Sentence evidence `['F154', 'F186']`: Pitching data for both starters is complete and covers the 2026 regular season through May 31.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W1.entity'], style findings ['S-1', 'W17.length']

**Headline**

Kyle Freeland faces the Los Angeles Angels as José Soriano starts for the home team

**Short summary**

- Kyle Freeland and José Soriano lead their respective teams in this contest on June 1, 2026.
- Freeland brings an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) to the mound.
- Soriano enters with a 2.65 ERA and a 1.15 WHIP, with all stats current for the 2026 regular season through May 31.

**Matchup Summary**

Freeland and Soriano lead their respective pitching staffs in a game scheduled for June 1, 2026.

**Kyle Freeland vs Los Angeles Angels**

The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers. Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4%. The Angels offense has elevated swing-and-miss risk and draws walks at an above-average rate.

**José Soriano vs Colorado Rockies**

The Rockies offense has a .709 OPS against right-handed pitchers. That group shows a 22.7% K% and an 8.3% BB%. Soriano shows below-average command and above-average swing-and-miss ability.

**Arsenal Scout**

Freeland uses a four-seam fastball 26.4% of the time and a curveball 22.5% of the time. His four-seam fastball moves 5.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin. Soriano uses his sinker 27.8% of the time and his curveball 24.8% of the time. The sinker from Soriano moves 15.2 in. sideways and 2.3 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Freeland uses his four-seam fastball to set up his curveball.
- Watch if Soriano can manage his command, as below-average command can create deep-count traffic.
- Watch how the Angels lineup handles the curveball from Freeland.

**Data Confidence Note**

Pitching data for both starters is complete and covers the 2026 regular season through May 31.


## veteran-823938

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary**; content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W8.form'], style findings ['S-4', 'W11.expansion', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14136, 'candidatesTokenCount': 1322, 'thoughtsTokenCount': 533, 'totalTokenCount': 15991}
  - gate `W8.form` token `None` in: He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up.
  - gate `W8.form` token `None` in: Eric Lauer uses his Four-seam 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up.
  - gate `W8.form` token `None` in: His Cutter, a put-away pitch, moves 1.8 in. sideways and 8.7 in. up.
  - style `W11.expansion` token `put-away pitch` in: He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up.
  - style `S-4` token `exhibits` in: He exhibits below-average swing-and-miss ability.
  - style `S-4` token `demonstrates` in: He demonstrates below-average swing-and-miss ability.
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1419` in: (whole report)
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.team', 'starters.home_starter.team']`: Nick Martinez and the Tampa Bay Rays face Eric Lauer and the Los Angeles Dodgers.
  - NLI (score_only) score `0.9940547347068787`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Nick Martinez holds a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.010883701965212822`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Eric Lauer enters with a 5.47 ERA and a 1.29 WHIP.
  - NLI (score_only) score `0.9980270266532898`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: The Dodgers offense against right-handed pitchers carries an .806 OPS (on-base plus slugging).
  - NLI (score_only) score `0.019996553659439087`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: These statistics cover the 2026 regular season through June 14.
  - NLI (score_only) score `0.9865958094596863`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label']`: Nick Martinez shows solid command.
  - NLI (score_only) score `0.9976446032524109`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: He exhibits below-average swing-and-miss ability.
  - NLI (score_only) score `0.9640037417411804`, problem `None`, paths `['teams.home.offense_profile.bb_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_number', 'glossary.BB%.short', 'glossary.K%.short']`: The Dodgers lineup draws walks at an 11.0% walk rate (BB%) and records a 20.3% strikeout rate (K%).
  - NLI (score_only) score `0.9919008016586304`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label']`: Eric Lauer shows average command.
  - NLI (score_only) score `0.9972834587097168`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label']`: He demonstrates below-average swing-and-miss ability.
  - NLI (score_only) score `0.9912912845611572`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Tampa Bay Rays lineup has an .685 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9721831679344177`, problem `None`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.k_rate_vs_hand']`: That group has an 8.8% BB% and a 17.7% K%.
  - NLI (score_only) score `0.9841212034225464`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Sinker.h_break', 'pitch_movement.away_starter.Sinker.v_break', 'glossary.Break.short']`: Nick Martinez throws his Sinker 31.4% of the time, which moves 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9897758960723877`, problem `None`, paths `['pitch_movement.away_starter.Changeup.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Changeup.v_break', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up.
  - NLI (score_only) score `0.9910967350006104`, problem `None`, paths `['pitch_mix.3.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: Eric Lauer uses his Four-seam 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up.
  - NLI (score_only) score `0.003012296510860324`, problem `None`, paths `['pitch_movement.home_starter.Cutter.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Cutter.v_break', 'starters.home_starter.pitching_profile.putaway_pitch']`: His Cutter, a put-away pitch, moves 1.8 in. sideways and 8.7 in. up.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.away_starter.pitching_profile.primary_pitch']`: Watch how often Nick Martinez throws his Sinker, his most used pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_strengths', 'pitch_mix.3.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch whether Eric Lauer relies on his Four-seam to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.style_label', 'findings.lineup_notes.home']`: Watch if the Dodgers lineup connects against the Sinker-Changeup style of Nick Martinez.
  - NLI (score_only) score `0.00010899176413659006`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are Nick Martinez and Eric Lauer.
  - Sentence evidence `['F124', 'F156', 'F154', 'F186']`: Nick Martinez and the Tampa Bay Rays face Eric Lauer and the Los Angeles Dodgers.
  - Sentence evidence `['F144', 'F152', 'F013', 'F018']`: Nick Martinez holds a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning).
  - Sentence evidence `['F176', 'F184']`: Eric Lauer enters with a 5.47 ERA and a 1.29 WHIP.
  - Sentence evidence `['F205', 'F206', 'F017']`: The Dodgers offense against right-handed pitchers carries an .806 OPS (on-base plus slugging).
  - Sentence evidence `['F132', 'F170', 'F197', 'F207']`: These statistics cover the 2026 regular season through June 14.
  - Sentence evidence `['F125']`: Nick Martinez shows solid command.
  - Sentence evidence `['F130']`: He exhibits below-average swing-and-miss ability.
  - Sentence evidence `['F201', 'F203', 'F011', 'F014']`: The Dodgers lineup draws walks at an 11.0% walk rate (BB%) and records a 20.3% strikeout rate (K%).
  - Sentence evidence `['F157']`: Eric Lauer shows average command.
  - Sentence evidence `['F162']`: He demonstrates below-average swing-and-miss ability.
  - Sentence evidence `['F196']`: The Tampa Bay Rays lineup has an .685 OPS against left-handed pitchers.
  - Sentence evidence `['F192', 'F194']`: That group has an 8.8% BB% and a 17.7% K%.
  - Sentence evidence `['F025', 'F103', 'F104', 'F012']`: Nick Martinez throws his Sinker 31.4% of the time, which moves 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F091', 'F092', 'F128', 'F022']`: He uses his Changeup as a put-away pitch, moving 12.5 in. sideways and 4.3 in. up.
  - Sentence evidence `['F063', 'F118', 'F119']`: Eric Lauer uses his Four-seam 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up.
  - Sentence evidence `['F115', 'F116', 'F160']`: His Cutter, a put-away pitch, moves 1.8 in. sideways and 8.7 in. up.
  - Sentence evidence `['F025', 'F127']`: Watch how often Nick Martinez throws his Sinker, his most used pitch.
  - Sentence evidence `['F007', 'F063']`: Watch whether Eric Lauer relies on his Four-seam to set up hitters.
  - Sentence evidence `['F129', 'F010']`: Watch if the Dodgers lineup connects against the Sinker-Changeup style of Nick Martinez.
  - Sentence evidence `['F001']`: Probable pitchers are Nick Martinez and Eric Lauer.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-2', 'S-4', 'W12.scope'], tokens {'promptTokenCount': 14300, 'candidatesTokenCount': 914, 'thoughtsTokenCount': 1491, 'totalTokenCount': 16705}
  - style `S-4` token `maintains` in: Watch whether the Dodgers lineup maintains its walk rate against Martinez.
  - style `S-4` token `features` in: The game features probable pitchers for the scheduled date.
  - style `S-2` token `the` in: The game features probable pitchers for the scheduled date.
  - style `S-2` token `That group` in: That group carries a 17.7% K% and an 8.8% BB%.
  - style `W12.scope` token `None` in: (whole report)
  - NLI (score_only) score `0.0012188750552013516`, problem `None`, paths `['data_confidence.lineup_status']`: Nick Martinez and Eric Lauer start for their teams
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'teams.away.name']`: Nick Martinez leads the Rays against the Dodgers.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.name', 'starters.home_starter.team', 'teams.home.name']`: The Dodgers counter with Eric Lauer on the mound.
  - NLI (score_only) score `0.9411816596984863`, problem `None`, paths `['venue']`: These teams meet at UNIQLO Field at Dodger Stadium.
  - NLI (score_only) score `0.9925097227096558`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Figures in this report cover the 2026 regular season through June 14.
  - NLI (score_only) score `0.02400028519332409`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Nick Martinez brings a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning) to the mound.
  - NLI (score_only) score `0.9876145124435425`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows solid command and below-average swing-and-miss ability.
  - NLI (score_only) score `0.9963016510009766`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: The Dodgers lineup has an .806 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.942797839641571`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group has a 20.3% K% (strikeout rate) and an 11.0% BB% (walk rate).
  - NLI (score_only) score `0.9955155253410339`, problem `None`, paths `['findings.lineup_notes.home']`: The Dodgers show strong OPS against this pitcher's hand and draw walks at an above-average rate.
  - NLI (score_only) score `0.004361830651760101`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Eric Lauer enters the game with a 5.47 ERA and a 1.29 WHIP.
  - NLI (score_only) score `0.9917545318603516`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and below-average swing-and-miss ability.
  - NLI (score_only) score `0.993118166923523`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Rays lineup has a .685 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9907863736152649`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That group carries a 17.7% K% and an 8.8% BB%.
  - NLI (score_only) score `0.9748960137367249`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Sinker.h_break', 'pitch_movement.away_starter.Sinker.v_break']`: Martinez uses his sinker 31.4% of the time, moving 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9982624650001526`, problem `None`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'pitch_mix.1.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'glossary.put-away pitch.short']`: His put-away pitch (second most used pitch) is the changeup, which he throws 28.0% of the time.
  - NLI (score_only) score `0.9862972497940063`, problem `None`, paths `['pitch_mix.3.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: Lauer uses his four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9850281476974487`, problem `None`, paths `['starters.home_starter.pitching_profile.putaway_pitch', 'pitch_mix.2.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: His put-away pitch is the cutter, thrown 17.5% of the time.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Nick Martinez throws his sinker to initiate counts.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.putaway_pitch']`: Watch if Eric Lauer relies on his cutter to finish plate appearances.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch whether the Dodgers lineup maintains its walk rate against Martinez.
  - NLI (score_only) score `0.009272536262869835`, problem `None`, paths `['data_confidence.lineup_status']`: The game features probable pitchers for the scheduled date.
  - Sentence evidence `['F001']`: Nick Martinez and Eric Lauer start for their teams
  - Sentence evidence `['F124', 'F154', 'F190']`: Nick Martinez leads the Rays against the Dodgers.
  - Sentence evidence `['F156', 'F186', 'F200']`: The Dodgers counter with Eric Lauer on the mound.
  - Sentence evidence `['F227']`: These teams meet at UNIQLO Field at Dodger Stadium.
  - Sentence evidence `['F132']`: Figures in this report cover the 2026 regular season through June 14.
  - Sentence evidence `['F144', 'F152', 'F013', 'F018']`: Nick Martinez brings a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning) to the mound.
  - Sentence evidence `['F125', 'F130']`: He shows solid command and below-average swing-and-miss ability.
  - Sentence evidence `['F206', 'F017']`: The Dodgers lineup has an .806 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F204', 'F202', 'F014', 'F011']`: That group has a 20.3% K% (strikeout rate) and an 11.0% BB% (walk rate).
  - Sentence evidence `['F010']`: The Dodgers show strong OPS against this pitcher's hand and draw walks at an above-average rate.
  - Sentence evidence `['F176', 'F184']`: Eric Lauer enters the game with a 5.47 ERA and a 1.29 WHIP.
  - Sentence evidence `['F157', 'F162']`: He shows average command and below-average swing-and-miss ability.
  - Sentence evidence `['F196']`: The Rays lineup has a .685 OPS against left-handed pitchers.
  - Sentence evidence `['F194', 'F192']`: That group carries a 17.7% K% and an 8.8% BB%.
  - Sentence evidence `['F025', 'F103', 'F104']`: Martinez uses his sinker 31.4% of the time, moving 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F128', 'F036', 'F022']`: His put-away pitch (second most used pitch) is the changeup, which he throws 28.0% of the time.
  - Sentence evidence `['F063', 'F118', 'F119']`: Lauer uses his four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F160', 'F052']`: His put-away pitch is the cutter, thrown 17.5% of the time.
  - Sentence evidence `['F025']`: Watch how often Nick Martinez throws his sinker to initiate counts.
  - Sentence evidence `['F160']`: Watch if Eric Lauer relies on his cutter to finish plate appearances.
  - Sentence evidence `['F202']`: Watch whether the Dodgers lineup maintains its walk rate against Martinez.
  - Sentence evidence `['F001']`: The game features probable pitchers for the scheduled date.
- Length: rules 1970 characters; shown text 1626 characters.

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

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `S-4` `maintains`, `S-4` `features`, `S-2` `the`, `S-2` `That group`, `W12.scope` `None`

**Headline**

Nick Martinez and Eric Lauer start for their teams

**Short summary**

- Nick Martinez leads the Rays against the Dodgers.
- The Dodgers counter with Eric Lauer on the mound.
- These teams meet at UNIQLO Field at Dodger Stadium.

**Matchup Summary**

Figures in this report cover the 2026 regular season through June 14.

**Nick Martinez vs Los Angeles Dodgers**

Nick Martinez brings a 2.43 ERA (earned run average) and a 1.16 WHIP (walks plus hits per inning) to the mound. He shows solid command and below-average swing-and-miss ability. The Dodgers lineup has an .806 OPS (on-base plus slugging) against right-handed pitchers. That group has a 20.3% K% (strikeout rate) and an 11.0% BB% (walk rate). The Dodgers show strong OPS against this pitcher's hand and draw walks at an above-average rate.

**Eric Lauer vs Tampa Bay Rays**

Eric Lauer enters the game with a 5.47 ERA and a 1.29 WHIP. He shows average command and below-average swing-and-miss ability. The Rays lineup has a .685 OPS against left-handed pitchers. That group carries a 17.7% K% and an 8.8% BB%.

**Arsenal Scout**

Martinez uses his sinker 31.4% of the time, moving 15.2 in. sideways and 12.4 in. up compared with a pitch thrown without spin. His put-away pitch (second most used pitch) is the changeup, which he throws 28.0% of the time. Lauer uses his four-seam fastball 45.5% of the time, moving 9.2 in. sideways and 15.8 in. up compared with a pitch thrown without spin. His put-away pitch is the cutter, thrown 17.5% of the time.

**Three Things to Watch**

- Watch how often Nick Martinez throws his sinker to initiate counts.
- Watch if Eric Lauer relies on his cutter to finish plate appearances.
- Watch whether the Dodgers lineup maintains its walk rate against Martinez.

**Data Confidence Note**

The game features probable pitchers for the scheduled date.


## veteran-824803

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary_retry**; content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W8.form', 'W1.entity', 'W7.missing', 'W13.series'], style findings ['S-2', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14035, 'candidatesTokenCount': 1012, 'thoughtsTokenCount': 2112, 'totalTokenCount': 17159}
  - gate `W1.number` token `two` in: The series opens with a matchup between two starters at Oriole Park at Camden Yards.
  - gate `W8.form` token `None` in: His four-seam fastball moves -9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.
  - gate `W1.entity` token `Matchup Analyst` in: Pitching profiles and lineup notes come from the Matchup Analyst findings.
  - gate `W7.missing` token `findings.home_starter_risks` in: Pitching profiles and lineup notes come from the Matchup Analyst findings.
  - style `S-2` token `That group` in: That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 24.5% K% and a 10.2% BB%.
  - gate `W13.series` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1712` in: (whole report)
  - NLI (score_only) score `0.0002497312380000949`, problem `None`, paths `['data_confidence.lineup_status', 'date', 'starters.away_starter.name', 'starters.home_starter.name']`: Carlos Rodón and Shane Baz start in the series opener
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team']`: Carlos Rodón takes the mound for the New York Yankees.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.name', 'starters.home_starter.team']`: Shane Baz starts for the Baltimore Orioles.
  - NLI (score_only) score `0.02368975430727005`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All figures represent the 2026 regular season through 2026-08-17.
  - NLI (score_only) score `0.02130609005689621`, problem `None`, paths `['venue', 'status']`: The series opens with a matchup between two starters at Oriole Park at Camden Yards.
  - NLI (score_only) score `0.9948849081993103`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Carlos Rodón holds a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9721408486366272`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows below-average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9961231350898743`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: The Baltimore lineup has a .723 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.967464029788971`, problem `None`, paths `['findings.lineup_notes.home', 'teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate).
  - NLI (score_only) score `0.00101161515340209`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Shane Baz carries a 4.00 ERA and a 1.36 WHIP.
  - NLI (score_only) score `0.9697384238243103`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9919048547744751`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The New York lineup has a .713 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9822841286659241`, problem `None`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 24.5% K% and a 10.2% BB%.
  - NLI (score_only) score `0.8303815126419067`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Carlos Rodón uses a four-seam fastball 44.4% of the time and a slider 24.4% of the time.
  - NLI (score_only) score `0.018941475078463554`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9635613560676575`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.4.home_starter.overall']`: Shane Baz uses a four-seam fastball 34.2% of the time and a curveball 32.7% of the time.
  - NLI (score_only) score `0.04802282154560089`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.v_break']`: His four-seam fastball moves -9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths', 'findings.away_style']`: Watch how Carlos Rodón uses his four-seam fastball to set up and his slider to finish.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_strengths', 'findings.home_style']`: Watch how Shane Baz uses his four-seam fastball to set up and his curveball to finish.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'findings.lineup_notes.home']`: Watch if the elevated swing-and-miss risk for both lineups affects plate appearances.
  - NLI (score_only) score `0.0020730735268443823`, problem `None`, paths `['findings.away_starter_risks', 'findings.away_starter_strengths', 'findings.home_starter_risks', 'findings.home_starter_strengths', 'findings.lineup_notes.away', 'findings.lineup_notes.home']`: Pitching profiles and lineup notes come from the Matchup Analyst findings.
  - Sentence evidence `['F001', 'F002', 'F121', 'F153']`: Carlos Rodón and Shane Baz start in the series opener
  - Sentence evidence `['F121', 'F151']`: Carlos Rodón takes the mound for the New York Yankees.
  - Sentence evidence `['F153', 'F183']`: Shane Baz starts for the Baltimore Orioles.
  - Sentence evidence `['F129', 'F161', 'F194', 'F204']`: All figures represent the 2026 regular season through 2026-08-17.
  - Sentence evidence `['F224', 'F185']`: The series opens with a matchup between two starters at Oriole Park at Camden Yards.
  - Sentence evidence `['F141', 'F149', 'F013', 'F018']`: Carlos Rodón holds a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning).
  - Sentence evidence `['F122', 'F127']`: He shows below-average command and above-average swing-and-miss ability.
  - Sentence evidence `['F203', 'F017']`: The Baltimore lineup has a .723 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F010', 'F201', 'F199', 'F014', 'F011']`: That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate).
  - Sentence evidence `['F173', 'F181']`: Shane Baz carries a 4.00 ERA and a 1.36 WHIP.
  - Sentence evidence `['F154', 'F159']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F193']`: The New York lineup has a .713 OPS against right-handed pitchers.
  - Sentence evidence `['F009', 'F191', 'F189']`: That group has an elevated swing-and-miss risk and draws walks at an above-average rate, with a 24.5% K% and a 10.2% BB%.
  - Sentence evidence `['F025', 'F036']`: Carlos Rodón uses a four-seam fastball 44.4% of the time and a slider 24.4% of the time.
  - Sentence evidence `['F097', 'F098']`: His four-seam fastball moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F030', 'F074']`: Shane Baz uses a four-seam fastball 34.2% of the time and a curveball 32.7% of the time.
  - Sentence evidence `['F115', 'F116']`: His four-seam fastball moves -9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004', 'F005']`: Watch how Carlos Rodón uses his four-seam fastball to set up and his slider to finish.
  - Sentence evidence `['F007', 'F008']`: Watch how Shane Baz uses his four-seam fastball to set up and his curveball to finish.
  - Sentence evidence `['F009', 'F010']`: Watch if the elevated swing-and-miss risk for both lineups affects plate appearances.
  - Sentence evidence `['F003', 'F004', 'F006', 'F007', 'F009', 'F010']`: Pitching profiles and lineup notes come from the Matchup Analyst findings.
- Content attempt 2: transport path `primary_retry`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503')], model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-2', 'S-4', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14207, 'candidatesTokenCount': 910, 'thoughtsTokenCount': 1340, 'totalTokenCount': 16457}
  - style `S-4` token `demonstrate` in: The lineups demonstrate distinct tendencies at the plate.
  - style `S-4` token `possesses` in: Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning).
  - style `S-4` token `maintains` in: This unit maintains a 24.5% K% and a 10.2% BB%.
  - style `S-4` token `maintain` in: Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic.
  - style `S-4` token `utilizes` in: Watch how often Shane Baz utilizes his Four-seam.
  - style `S-2` token `the` in: The pitching profiles for both starters are based on at least 100 pitches thrown.
  - style `S-2` token `This offense` in: This offense has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1676` in: (whole report)
  - NLI (score_only) score `0.01548101007938385`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name']`: Carlos Rodón and the New York Yankees visit Shane Baz and the Baltimore Orioles
  - NLI (score_only) score `0.8531615734100342`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Carlos Rodón and Shane Baz represent their teams in this contest.
  - NLI (score_only) score `0.013086733408272266`, problem `None`, paths `['findings.away_style', 'findings.home_style']`: Both starters bring contrasting styles to the mound.
  - NLI (score_only) score `0.9572268724441528`, problem `None`, paths `['findings.lineup_notes.away', 'findings.lineup_notes.home']`: The lineups demonstrate distinct tendencies at the plate.
  - NLI (score_only) score `0.057854410260915756`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: All figures cover the 2026 regular season through August 17.
  - NLI (score_only) score `0.99791020154953`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.00101161515340209`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Shane Baz carries a 4.00 ERA and a 1.36 WHIP.
  - NLI (score_only) score `0.9586890935897827`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: Carlos Rodón shows below-average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9974259734153748`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: The Baltimore Orioles lineup against left-handed pitchers holds a .723 OPS (on-base plus slugging).
  - NLI (score_only) score `0.9544894695281982`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate).
  - NLI (score_only) score `0.9718210697174072`, problem `None`, paths `['findings.lineup_notes.home']`: This offense has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - NLI (score_only) score `0.833733320236206`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Shane Baz shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9973629117012024`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The New York Yankees offense against right-handed pitchers posts a .713 OPS.
  - NLI (score_only) score `0.9912018775939941`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: This unit maintains a 24.5% K% and a 10.2% BB%.
  - NLI (score_only) score `0.9883162379264832`, problem `None`, paths `['findings.lineup_notes.away']`: The group has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - NLI (score_only) score `0.9947957396507263`, problem `None`, paths `['findings.away_style']`: Rodón uses his Four-seam to set up and Slider to finish.
  - NLI (score_only) score `0.8170943856239319`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9842705130577087`, problem `None`, paths `['findings.home_style']`: Baz relies on his Four-seam to set up and Curveball to finish.
  - NLI (score_only) score `0.878239095211029`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.v_break']`: His Four-seam moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_risks']`: Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch how often Shane Baz utilizes his Four-seam.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch if the New York Yankees can capitalize on their walk rate against Shane Baz.
  - NLI (score_only) score `0.0036119294818490744`, problem `None`, paths `['starters.away_starter.sample.thresholds.arsenal', 'starters.home_starter.sample.thresholds.arsenal']`: The pitching profiles for both starters are based on at least 100 pitches thrown.
  - Sentence evidence `['F001', 'F121', 'F153']`: Carlos Rodón and the New York Yankees visit Shane Baz and the Baltimore Orioles
  - Sentence evidence `['F121', 'F153']`: Carlos Rodón and Shane Baz represent their teams in this contest.
  - Sentence evidence `['F005', 'F008']`: Both starters bring contrasting styles to the mound.
  - Sentence evidence `['F009', 'F010']`: The lineups demonstrate distinct tendencies at the plate.
  - Sentence evidence `['F129', 'F161']`: All figures cover the 2026 regular season through August 17.
  - Sentence evidence `['F141', 'F149', 'F013', 'F018']`: Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning).
  - Sentence evidence `['F173', 'F181']`: Shane Baz carries a 4.00 ERA and a 1.36 WHIP.
  - Sentence evidence `['F122', 'F127']`: Carlos Rodón shows below-average command and above-average swing-and-miss ability.
  - Sentence evidence `['F203', 'F017']`: The Baltimore Orioles lineup against left-handed pitchers holds a .723 OPS (on-base plus slugging).
  - Sentence evidence `['F201', 'F199', 'F014', 'F011']`: That group has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate).
  - Sentence evidence `['F010']`: This offense has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - Sentence evidence `['F154', 'F159']`: Shane Baz shows average command and average swing-and-miss ability.
  - Sentence evidence `['F193']`: The New York Yankees offense against right-handed pitchers posts a .713 OPS.
  - Sentence evidence `['F191', 'F189']`: This unit maintains a 24.5% K% and a 10.2% BB%.
  - Sentence evidence `['F009']`: The group has an elevated swing-and-miss risk and draws walks at an above-average rate.
  - Sentence evidence `['F005']`: Rodón uses his Four-seam to set up and Slider to finish.
  - Sentence evidence `['F097', 'F098']`: His Four-seam moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F008']`: Baz relies on his Four-seam to set up and Curveball to finish.
  - Sentence evidence `['F115', 'F116']`: His Four-seam moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F003']`: Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic.
  - Sentence evidence `['F029']`: Watch how often Shane Baz utilizes his Four-seam.
  - Sentence evidence `['F189']`: Watch if the New York Yankees can capitalize on their walk rate against Shane Baz.
  - Sentence evidence `['F138', 'F170']`: The pitching profiles for both starters are based on at least 100 pitches thrown.
- Length: rules 2179 characters; shown text 1687 characters.

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

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `S-4` `demonstrate`, `S-4` `possesses`, `S-4` `maintains`, `S-4` `maintain`, `S-4` `utilizes`, `S-2` `the`, `S-2` `This offense`, `W12.scope` `None`, `W17.length` `1676`

**Headline**

Carlos Rodón and the New York Yankees visit Shane Baz and the Baltimore Orioles

**Short summary**

- Carlos Rodón and Shane Baz represent their teams in this contest.
- Both starters bring contrasting styles to the mound.
- The lineups demonstrate distinct tendencies at the plate.

**Matchup Summary**

All figures cover the 2026 regular season through August 17. Carlos Rodón possesses a 3.30 ERA (earned run average) and a 1.25 WHIP (walks plus hits per inning). Shane Baz carries a 4.00 ERA and a 1.36 WHIP.

**Carlos Rodón vs Baltimore Orioles**

Carlos Rodón shows below-average command and above-average swing-and-miss ability. The Baltimore Orioles lineup against left-handed pitchers holds a .723 OPS (on-base plus slugging). That group has a 25.7% K% (strikeout rate) and a 9.5% BB% (walk rate). This offense has an elevated swing-and-miss risk and draws walks at an above-average rate.

**Shane Baz vs New York Yankees**

Shane Baz shows average command and average swing-and-miss ability. The New York Yankees offense against right-handed pitchers posts a .713 OPS. This unit maintains a 24.5% K% and a 10.2% BB%. The group has an elevated swing-and-miss risk and draws walks at an above-average rate.

**Arsenal Scout**

Rodón uses his Four-seam to set up and Slider to finish. His Four-seam moves 9.2 in. sideways and 18.5 in. up compared with a pitch thrown without spin. Baz relies on his Four-seam to set up and Curveball to finish. His Four-seam moves 9.2 in. sideways and 16.6 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Carlos Rodón can maintain his command to avoid deep-count traffic.
- Watch how often Shane Baz utilizes his Four-seam.
- Watch if the New York Yankees can capitalize on their walk rate against Shane Baz.

**Data Confidence Note**

The pitching profiles for both starters are based on at least 100 pitches thrown.


## Calibration note: the rules text of veteran-824027 through the word-level checks

Not a defect list. These are the words and shapes the word-level checks flag in the text the rules writer publishes today. Whether each would be a violation depends on citations (a comparison word is allowed when both values are quoted; a sentence-opening question word is a limit of the entity heuristic). The checks that need citations were not run.

- `W1.entity`: 'Can José Soriano', 'Can Kyle Freeland', 'Statcast'
- `W10.cause`: 'because', 'so'
- `W15.question`: '?'
- `W16.internal`: 'fetched', 'snapshot'
- `W2.comparison`: 'larger', 'more', 'versus'

