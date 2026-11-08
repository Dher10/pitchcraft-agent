# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest(s) recorded in this run: `84a87b387c260fd05c0277b8fb19c9abe867c9cf64920643056805df5aef972c`; prompt version(s) recorded in this run: `p2.2-3`. Nothing here is published; rules stay live.

S1 code detectors: S-1, S-2, S-4, S-5, S-7, S-8; S-3, S-6 and S-9 require judge/human assessment and are not evaluated here. NLI is score-only unless explicitly recorded as gate; no human-calibrated entailment claim.

Gemini HTTP calls: run 22 of 30, experiment 127 of 400.
Capacity failures (503/429) in this run: 10 of 22 finished calls. By model: `gemini-3.1-flash-lite` 9 of 17; `gemini-3.5-flash` 1 of 5.
**The run stopped early** after case `limited-825104` at 2026-10-31 07:19 local (2026-10-31 12:19 UTC): 10 of 22 finished calls were capacity failures (more than a third). Failing model(s): `gemini-3.1-flash-lite` (9 of 17), `gemini-3.5-flash` (1 of 5). The remaining cases are `not_attempted`.
Run started 2026-10-31 07:08 local (2026-10-31 12:08 UTC), finished 2026-10-31 07:19 local.
More than a third of the calls failed on capacity; time of day of the run: 2026-10-31 07:08 to 2026-10-31 07:19 local (Hora est. Pacífico, Sudamérica).
Paths: primary 0, primary_retry 0, fallback 0, fallback_retry 0, rules 6, not_attempted 4. LLM coverage 0/10; accepted 0, rejected 6, not attempted 4; not written by the primary model 10/10 (a fallback or rules result is not a primary first-attempt success).


## postseason-849842

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.entity', 'W1.evidence_path'], style findings ['S-1', 'S-4', 'W14.team'], tokens {'promptTokenCount': 8305, 'candidatesTokenCount': 2159, 'thoughtsTokenCount': 1475, 'totalTokenCount': 11939}
  - gate `W1.entity` token `Sep` in: Both starters bring specific pitching profiles into this 2026 regular season through Sep 29 matchup.
  - gate `W1.entity` token `Sep` in: All figures cover the 2026 regular season through Sep 29.
  - gate `W1.evidence_path` token `starters.home_starter.thresholds.control` in: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
  - style `S-1` token `2026 regular season` in: All figures cover the 2026 regular season through Sep 29.
  - style `S-4` token `displays` in: Gausman shows solid command and average swing-and-miss ability, while Pivetta displays above-average swing-and-miss ability.
  - style `W14.team` token `None` in: (whole report)
  - NLI (score_only) score `0.00688914954662323`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'series.series_name', 'series.game_number']`: Kevin Gausman and Nick Pivetta duel in Game 2 of the NL Wild Card Series.
  - NLI (score_only) score `0.9934658408164978`, problem `None`, paths `['series.series_name', 'series.game_number']`: This is Game 2 of the NL Wild Card Series.
  - NLI (score_only) score `0.9904932379722595`, problem `None`, paths `['series.standing']`: Before first pitch, SD leads 1-0.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Both starters bring specific pitching profiles into this 2026 regular season through Sep 29 matchup.
  - NLI (score_only) score `0.0005573753733187914`, problem `None`, paths `['starters.away_starter.season_summary.era', 'glossary.ERA.short', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short']`: Kevin Gausman starts for Chicago with a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.00039312703302130103`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip']`: Nick Pivetta counters for San Diego with a 2.86 ERA and a 1.01 WHIP.
  - NLI (score_only) score `0.9946816563606262`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Gausman shows solid command and average swing-and-miss ability, while Pivetta displays above-average swing-and-miss ability.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through']`: All figures cover the 2026 regular season through Sep 29.
  - NLI (score_only) score `0.979198694229126`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'glossary.OPS.short']`: The San Diego lineup enters with a .722 OPS (on-base plus slugging).
  - NLI (score_only) score `0.9860963225364685`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_number', 'glossary.BB%.short']`: That group carries a 21.5% K% (strikeout rate) and a 9.4% BB% (walk rate).
  - NLI (score_only) score `0.00024036914692260325`, problem `None`, paths `['findings.lineup_notes.home']`: They draw walks at an above-average rate against right-handed pitchers.
  - NLI (score_only) score `0.9908162355422974`, problem `None`, paths `['teams.away.offense_profile.ops_number']`: The Chicago lineup has a .757 OPS.
  - NLI (score_only) score `0.9894822835922241`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.bb_rate_number']`: The Chicago group shows a 21.2% K% and a 10.6% BB%.
  - NLI (score_only) score `0.00029870576690882444`, problem `None`, paths `['findings.lineup_notes.away']`: Their offense draws walks at an above-average rate against right-handed pitchers.
  - NLI (score_only) score `0.8720522522926331`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Gausman uses a four-seam fastball as his primary pitch and uses the splitter as his second most used pitch.
  - NLI (score_only) score `0.9903212189674377`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Pivetta uses a four-seam fastball as his primary offering and the curveball as his second most used pitch.
  - NLI (score_only) score `0.12450586259365082`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break']`: Gausman's four-seam fastball moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9739060401916504`, problem `None`, paths `['pitch_movement.away_starter.Splitter.h_break', 'pitch_movement.away_starter.Splitter.v_break']`: His splitter moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.03252851590514183`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: Pivetta's four-seam fastball moves 3.5 in. sideways and 20.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9862797260284424`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'pitch_movement.home_starter.Curveball.v_break']`: His curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style']`: Watch how often Gausman uses his splitter to finish counts.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_style']`: Watch if Pivetta relies on his four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away']`: Watch whether the Chicago lineup draws walks as they have done at an above-average rate.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.thresholds.control']`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
  - NLI (score_only) score `0.007607303559780121`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label']`: There is not enough data yet to rate his command.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Kevin Gausman'}, {'path': 'starters.home_starter.name', 'value': 'Nick Pivetta'}, {'path': 'series.series_name', 'value': 'NL Wild Card Series'}, {'path': 'series.game_number', 'value': '2'}]`: Kevin Gausman and Nick Pivetta duel in Game 2 of the NL Wild Card Series.
  - Sentence evidence `[{'path': 'series.series_name', 'value': 'NL Wild Card Series'}, {'path': 'series.game_number', 'value': '2'}]`: This is Game 2 of the NL Wild Card Series.
  - Sentence evidence `[{'path': 'series.standing', 'value': 'SD leads 1-0'}]`: Before first pitch, SD leads 1-0.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season'}, {'path': 'starters.away_starter.sample.arsenal.scope.through', 'value': '2026-09-29'}]`: Both starters bring specific pitching profiles into this 2026 regular season through Sep 29 matchup.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era', 'value': '4.51'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.27'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: Kevin Gausman starts for Chicago with a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning).
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '2.86'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.01'}]`: Nick Pivetta counters for San Diego with a 2.86 ERA and a 1.01 WHIP.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.command_label', 'value': 'Solid command'}, {'path': 'starters.away_starter.pitching_profile.swing_miss_label', 'value': 'Average swing-and-miss ability'}, {'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Gausman shows solid command and average swing-and-miss ability, while Pivetta displays above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season'}, {'path': 'starters.away_starter.season_summary.scopes.season_rates.through', 'value': '2026-09-29'}]`: All figures cover the 2026 regular season through Sep 29.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_number', 'value': '0.722'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: The San Diego lineup enters with a .722 OPS (on-base plus slugging).
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_number', 'value': '21.5'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_number', 'value': '9.4'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: That group carries a 21.5% K% (strikeout rate) and a 9.4% BB% (walk rate).
  - Sentence evidence `[{'path': 'findings.lineup_notes.home', 'value': 'draws walks at an above-average rate'}]`: They draw walks at an above-average rate against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_number', 'value': '0.757'}]`: The Chicago lineup has a .757 OPS.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_number', 'value': '21.2'}, {'path': 'teams.away.offense_profile.bb_rate_number', 'value': '10.6'}]`: The Chicago group shows a 21.2% K% and a 10.6% BB%.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': "has strong OPS against this pitcher's hand; draws walks at an above-average rate"}]`: Their offense draws walks at an above-average rate against right-handed pitchers.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}, {'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Splitter'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}]`: Gausman uses a four-seam fastball as his primary pitch and uses the splitter as his second most used pitch.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}, {'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Curveball'}]`: Pivetta uses a four-seam fastball as his primary offering and the curveball as his second most used pitch.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '-10.6'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '16.9'}]`: Gausman's four-seam fastball moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Splitter.h_break', 'value': '-14.0'}, {'path': 'pitch_movement.away_starter.Splitter.v_break', 'value': '4.3'}]`: His splitter moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Four-seam.h_break', 'value': '-3.5'}, {'path': 'pitch_movement.home_starter.Four-seam.v_break', 'value': '20.3'}]`: Pivetta's four-seam fastball moves 3.5 in. sideways and 20.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Curveball.h_break', 'value': '6.7'}, {'path': 'pitch_movement.home_starter.Curveball.v_break', 'value': '-15.2'}]`: His curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'findings.away_style', 'value': 'Four-seam to set up, Splitter to finish'}]`: Watch how often Gausman uses his splitter to finish counts.
  - Sentence evidence `[{'path': 'findings.home_style', 'value': 'Four-seam to set up, Curveball to finish'}]`: Watch if Pivetta relies on his four-seam fastball to set up hitters.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': "has strong OPS against this pitcher's hand; draws walks at an above-average rate"}]`: Watch whether the Chicago lineup draws walks as they have done at an above-average rate.
  - Sentence evidence `[{'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '140'}, {'path': 'starters.home_starter.thresholds.control', 'value': '170'}]`: Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'null'}]`: There is not enough data yet to rate his command.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W2.comparison', 'W8.form', 'W1.evidence_path'], style findings ['W17.length'], tokens {'promptTokenCount': 8413, 'candidatesTokenCount': 1935, 'thoughtsTokenCount': 1415, 'totalTokenCount': 11763}
  - gate `W1.number` token `09` in: All figures in this report cover the 2026 regular season through 2026-09-29.
  - gate `W1.number` token `29` in: All figures in this report cover the 2026 regular season through 2026-09-29.
  - gate `W2.comparison` token `lower` in: Pivetta has a lower ERA (2.86 vs 4.51) and a lower WHIP (1.01 vs 1.27) than Gausman.
  - gate `W1.number` token `10.4` in: That group shows a 21.2% strikeout rate (K%) and a 10.4% walk rate (BB%).
  - gate `W8.form` token `None` in: Gausman moves his Splitter 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin.
  - gate `W8.form` token `None` in: Pivetta moves his Curveball 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - gate `W1.evidence_path` token `starters.home_starter.thresholds.control` in: There is not enough data yet to rate the control of Nick Pivetta; his sample is limited to 140 batters faced, and 170 are needed.
  - style `W17.length` token `1666` in: (whole report)
  - NLI (score_only) score `0.9390100836753845`, problem `None`, paths `['series.game_number', 'series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series
  - NLI (score_only) score `0.9963757395744324`, problem `None`, paths `['series.game_number', 'series.series_name', 'series.standing']`: This is Game 2 of the NL Wild Card Series, and before first pitch, SD leads 1-0.
  - NLI (score_only) score `0.002131757792085409`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Kevin Gausman and Nick Pivetta lead their teams into the matchup.
  - NLI (score_only) score `0.00036175185232423246`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: All figures in this report cover the 2026 regular season through 2026-09-29.
  - NLI (score_only) score `0.9745251536369324`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Kevin Gausman carries a 4.51 earned run average (ERA) and a 1.27 walks plus hits per inning (WHIP).
  - NLI (score_only) score `0.002304102759808302`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip']`: Nick Pivetta has a 2.86 ERA and a 1.01 WHIP.
  - NLI (score_only) score `0.0034545548260211945`, problem `None`, paths `['starters.home_starter.season_summary.era_number', 'starters.away_starter.season_summary.era_number', 'starters.home_starter.season_summary.whip_number', 'starters.away_starter.season_summary.whip_number']`: Pivetta has a lower ERA (2.86 vs 4.51) and a lower WHIP (1.01 vs 1.27) than Gausman.
  - NLI (score_only) score `0.9944032430648804`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: The Chicago Cubs lineup has a .757 on-base plus slugging (OPS) against right-handed pitchers.
  - NLI (score_only) score `0.9616149067878723`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group shows a 21.2% strikeout rate (K%) and a 10.4% walk rate (BB%).
  - NLI (score_only) score `0.9928041100502014`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand']`: The San Diego Padres lineup has a .722 OPS against right-handed pitchers.
  - NLI (score_only) score `0.987054169178009`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.bb_rate_vs_hand']`: The Padres show a 21.5% K% and a 9.4% BB%.
  - NLI (score_only) score `0.7937975525856018`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.home.offense_profile.ops_number']`: The Chicago Cubs have a higher OPS (.757 vs .722) than the San Diego Padres.
  - NLI (score_only) score `0.6307562589645386`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'pitch_mix.1.away_starter.overall']`: Kevin Gausman uses his Four-seam 50.6% of the time and his Splitter 39.2% of the time.
  - NLI (score_only) score `0.9861587882041931`, problem `None`, paths `['pitch_movement.away_starter.Splitter.h_break', 'pitch_movement.away_starter.Splitter.v_break']`: Gausman moves his Splitter 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9269110560417175`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'pitch_mix.5.home_starter.overall']`: Nick Pivetta uses his Four-seam 52.2% of the time and his Curveball 22.1% of the time.
  - NLI (score_only) score `0.9895040988922119`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'pitch_movement.home_starter.Curveball.v_break']`: Pivetta moves his Curveball 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Gausman uses his Splitter to finish plate appearances.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Pivetta relies on his Curveball to get outs.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.bb_rate_vs_hand']`: Watch if the San Diego Padres walk-rate increases against Gausman.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.thresholds.control']`: There is not enough data yet to rate the control of Nick Pivetta; his sample is limited to 140 batters faced, and 170 are needed.
  - NLI (score_only) score `0.9873573780059814`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label']`: Kevin Gausman shows solid command.
  - NLI (score_only) score `0.9934684038162231`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label']`: Nick Pivetta shows above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'series.game_number', 'value': '2'}, {'path': 'series.series_name', 'value': 'NL Wild Card Series'}, {'path': 'starters.away_starter.name', 'value': 'Kevin Gausman'}, {'path': 'starters.home_starter.name', 'value': 'Nick Pivetta'}]`: Kevin Gausman faces Nick Pivetta in Game 2 of the NL Wild Card Series
  - Sentence evidence `[{'path': 'series.game_number', 'value': '2'}, {'path': 'series.series_name', 'value': 'NL Wild Card Series'}, {'path': 'series.standing', 'value': 'SD leads 1-0'}]`: This is Game 2 of the NL Wild Card Series, and before first pitch, SD leads 1-0.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Kevin Gausman'}, {'path': 'starters.home_starter.name', 'value': 'Nick Pivetta'}]`: Kevin Gausman and Nick Pivetta lead their teams into the matchup.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season'}]`: All figures in this report cover the 2026 regular season through 2026-09-29.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era', 'value': '4.51'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.27'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: Kevin Gausman carries a 4.51 earned run average (ERA) and a 1.27 walks plus hits per inning (WHIP).
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '2.86'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.01'}]`: Nick Pivetta has a 2.86 ERA and a 1.01 WHIP.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era_number', 'value': '2.86'}, {'path': 'starters.away_starter.season_summary.era_number', 'value': '4.51'}, {'path': 'starters.home_starter.season_summary.whip_number', 'value': '1.01'}, {'path': 'starters.away_starter.season_summary.whip_number', 'value': '1.27'}]`: Pivetta has a lower ERA (2.86 vs 4.51) and a lower WHIP (1.01 vs 1.27) than Gausman.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.757'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: The Chicago Cubs lineup has a .757 on-base plus slugging (OPS) against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '21.2%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '10.6%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: That group shows a 21.2% strikeout rate (K%) and a 10.4% walk rate (BB%).
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.722'}]`: The San Diego Padres lineup has a .722 OPS against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.5%'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '9.4%'}]`: The Padres show a 21.5% K% and a 9.4% BB%.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_number', 'value': '0.757'}, {'path': 'teams.home.offense_profile.ops_number', 'value': '0.722'}]`: The Chicago Cubs have a higher OPS (.757 vs .722) than the San Diego Padres.
  - Sentence evidence `[{'path': 'pitch_mix.0.away_starter.overall', 'value': '50.6'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '39.2'}]`: Kevin Gausman uses his Four-seam 50.6% of the time and his Splitter 39.2% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Splitter.h_break', 'value': '-14.0'}, {'path': 'pitch_movement.away_starter.Splitter.v_break', 'value': '4.3'}]`: Gausman moves his Splitter 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_mix.0.home_starter.overall', 'value': '52.2'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '22.1'}]`: Nick Pivetta uses his Four-seam 52.2% of the time and his Curveball 22.1% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Curveball.h_break', 'value': '6.7'}, {'path': 'pitch_movement.home_starter.Curveball.v_break', 'value': '-15.2'}]`: Pivetta moves his Curveball 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Splitter'}]`: Watch how often Gausman uses his Splitter to finish plate appearances.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Curveball'}]`: Watch whether Pivetta relies on his Curveball to get outs.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '9.4%'}]`: Watch if the San Diego Padres walk-rate increases against Gausman.
  - Sentence evidence `[{'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '140'}, {'path': 'starters.home_starter.thresholds.control', 'value': '170'}]`: There is not enough data yet to rate the control of Nick Pivetta; his sample is limited to 140 batters faced, and 170 are needed.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.command_label', 'value': 'Solid command'}]`: Kevin Gausman shows solid command.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Nick Pivetta shows above-average swing-and-miss ability.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W1.entity', 'W1.evidence_path'], style findings ['S-1', 'S-4', 'W14.team']

**Headline**

Kevin Gausman and Nick Pivetta duel in Game 2 of the NL Wild Card Series.

**Short summary**

- This is Game 2 of the NL Wild Card Series.
- Before first pitch, SD leads 1-0.
- Both starters bring specific pitching profiles into this 2026 regular season through Sep 29 matchup.

**Matchup Summary**

Kevin Gausman starts for Chicago with a 4.51 ERA (earned run average) and a 1.27 WHIP (walks plus hits per inning). Nick Pivetta counters for San Diego with a 2.86 ERA and a 1.01 WHIP. Gausman shows solid command and average swing-and-miss ability, while Pivetta displays above-average swing-and-miss ability. All figures cover the 2026 regular season through Sep 29.

**Kevin Gausman vs San Diego Padres**

The San Diego lineup enters with a .722 OPS (on-base plus slugging). That group carries a 21.5% K% (strikeout rate) and a 9.4% BB% (walk rate). They draw walks at an above-average rate against right-handed pitchers.

**Nick Pivetta vs Chicago Cubs**

The Chicago lineup has a .757 OPS. The Chicago group shows a 21.2% K% and a 10.6% BB%. Their offense draws walks at an above-average rate against right-handed pitchers.

**Arsenal Scout**

Gausman uses a four-seam fastball as his primary pitch and uses the splitter as his second most used pitch. Pivetta uses a four-seam fastball as his primary offering and the curveball as his second most used pitch. Gausman's four-seam fastball moves 10.6 in. sideways and 16.9 in. up compared with a pitch thrown without spin. His splitter moves 14.0 in. sideways and 4.3 in. up compared with a pitch thrown without spin. Pivetta's four-seam fastball moves 3.5 in. sideways and 20.3 in. up compared with a pitch thrown without spin. His curveball moves 6.7 in. sideways and 15.2 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Gausman uses his splitter to finish counts.
- Watch if Pivetta relies on his four-seam fastball to set up hitters.
- Watch whether the Chicago lineup draws walks as they have done at an above-average rate.

**Data Confidence Note**

Control data for Nick Pivetta is limited: 140 batters faced, and 170 are needed for a read. There is not enough data yet to rate his command.


## postseason-849849

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.evidence_value', 'W5.intensity', 'W5.label', 'W10.cause'], style findings ['S-4', 'S-7', 'W17.length'], tokens {'promptTokenCount': 8044, 'candidatesTokenCount': 2504, 'thoughtsTokenCount': 367, 'totalTokenCount': 10915}
  - gate `W1.evidence_value` token `starters.away_starter.season_summary.scopes.season_rates.label` in: Hagen Smith carries a 1.29 earned run average (ERA) and a 0.96 walks plus hits per inning (WHIP) over the 2026 regular season through Sep 28.
  - gate `W1.evidence_value` token `starters.home_starter.season_summary.scopes.season_rates.label` in: AJ Blubaugh has a 3.66 ERA and a 1.23 WHIP over the same period.
  - gate `W5.intensity` token `best` in: The Chicago White Sox and the Houston Astros begin their best-of-three series.
  - gate `W5.label` token `command` in: Watch if AJ Blubaugh encounters deep-count traffic due to his command.
  - gate `W10.cause` token `due to` in: Watch if AJ Blubaugh encounters deep-count traffic due to his command.
  - style `S-7` token `over the same period` in: AJ Blubaugh has a 3.66 ERA and a 1.23 WHIP over the same period.
  - style `S-4` token `utilizes` in: AJ Blubaugh utilizes a four-seam fastball and a sweeper.
  - style `W17.length` token `1541` in: (whole report)
  - NLI (score_only) score `0.0019959378987550735`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'series.series_name']`: Hagen Smith and AJ Blubaugh start in the AL Wild Card Series opener
  - NLI (score_only) score `0.9906396865844727`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 1 of the AL Wild Card Series.
  - NLI (score_only) score `0.0004994397750124335`, problem `None`, paths `['starters.away_starter.season_summary.era', 'glossary.ERA.short', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short', 'starters.away_starter.season_summary.scopes.season_rates.label']`: Hagen Smith carries a 1.29 earned run average (ERA) and a 0.96 walks plus hits per inning (WHIP) over the 2026 regular season through Sep 28.
  - NLI (score_only) score `0.9304137229919434`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.season_rates.label']`: AJ Blubaugh has a 3.66 ERA and a 1.23 WHIP over the same period.
  - NLI (score_only) score `0.009673227556049824`, problem `None`, paths `['teams.away.name', 'teams.home.name', 'series.games_in_series']`: The Chicago White Sox and the Houston Astros begin their best-of-three series.
  - NLI (score_only) score `0.9928285479545593`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Hagen Smith shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.9925710558891296`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label']`: AJ Blubaugh shows below-average command.
  - NLI (score_only) score `0.9945074915885925`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: The Houston Astros offense has a .713 on-base plus slugging (OPS) against left-handed pitchers.
  - NLI (score_only) score `0.9665669202804565`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: Their strikeout rate (K%) is 21.0% and their walk rate (BB%) is 7.9%.
  - NLI (score_only) score `0.9923980832099915`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand']`: The Chicago White Sox lineup has a .716 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9857072234153748`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: This group has a 24.1% K% and a 9.4% BB%.
  - NLI (score_only) score `0.9902929067611694`, problem `None`, paths `['findings.lineup_notes.away']`: The Chicago White Sox has elevated swing-and-miss risk and draws walks at an above-average rate.
  - NLI (score_only) score `0.988396942615509`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Hagen Smith relies on a four-seam fastball and a slider as his second most used pitch (put-away pitch).
  - NLI (score_only) score `0.010940219275653362`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.7564705014228821`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: AJ Blubaugh utilizes a four-seam fastball and a sweeper.
  - NLI (score_only) score `0.024559441953897476`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style']`: Watch how often Hagen Smith uses his slider to finish sequences.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks']`: Watch if AJ Blubaugh encounters deep-count traffic due to his command.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away']`: Watch whether the Chicago White Sox can manage the swing-and-miss risk in their lineup.
  - NLI (score_only) score `0.994583785533905`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: Control data for Hagen Smith is limited: 110 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Hagen Smith'}, {'path': 'starters.home_starter.name', 'value': 'AJ Blubaugh'}, {'path': 'series.series_name', 'value': 'AL Wild Card Series'}]`: Hagen Smith and AJ Blubaugh start in the AL Wild Card Series opener
  - Sentence evidence `[{'path': 'series.game_number', 'value': '1'}, {'path': 'series.series_name', 'value': 'AL Wild Card Series'}]`: This is Game 1 of the AL Wild Card Series.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era', 'value': '1.29'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '0.96'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}, {'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Sep 28'}]`: Hagen Smith carries a 1.29 earned run average (ERA) and a 0.96 walks plus hits per inning (WHIP) over the 2026 regular season through Sep 28.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '3.66'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.23'}, {'path': 'starters.home_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Sep 28'}]`: AJ Blubaugh has a 3.66 ERA and a 1.23 WHIP over the same period.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Chicago White Sox'}, {'path': 'teams.home.name', 'value': 'Houston Astros'}, {'path': 'series.games_in_series', 'value': '3'}]`: The Chicago White Sox and the Houston Astros begin their best-of-three series.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Hagen Smith shows above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'Below-average command'}]`: AJ Blubaugh shows below-average command.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.713'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: The Houston Astros offense has a .713 on-base plus slugging (OPS) against left-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.0%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '7.9%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: Their strikeout rate (K%) is 21.0% and their walk rate (BB%) is 7.9%.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.716'}]`: The Chicago White Sox lineup has a .716 OPS against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.1%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '9.4%'}]`: This group has a 24.1% K% and a 9.4% BB%.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': 'has elevated swing-and-miss risk; draws walks at an above-average rate'}]`: The Chicago White Sox has elevated swing-and-miss risk and draws walks at an above-average rate.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}, {'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Slider'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}]`: Hagen Smith relies on a four-seam fastball and a slider as his second most used pitch (put-away pitch).
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '7.9'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '14.0'}]`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}, {'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Sweeper'}]`: AJ Blubaugh utilizes a four-seam fastball and a sweeper.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Four-seam.h_break', 'value': '-10.7'}, {'path': 'pitch_movement.home_starter.Four-seam.v_break', 'value': '17.2'}]`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'findings.away_style', 'value': 'Four-seam to set up, Slider to finish'}]`: Watch how often Hagen Smith uses his slider to finish sequences.
  - Sentence evidence `[{'path': 'findings.home_starter_risks', 'value': 'Below-average command can create deep-count traffic'}]`: Watch if AJ Blubaugh encounters deep-count traffic due to his command.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': 'has elevated swing-and-miss risk; draws walks at an above-average rate'}]`: Watch whether the Chicago White Sox can manage the swing-and-miss risk in their lineup.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '110'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: Control data for Hagen Smith is limited: 110 batters faced, and 170 are needed for a read.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W1.entity', 'W10.cause'], style findings ['S-1', 'S-2', 'S-7'], tokens {'promptTokenCount': 8201, 'candidatesTokenCount': 2012, 'thoughtsTokenCount': 2988, 'totalTokenCount': 13201}
  - gate `W1.number` token `28` in: All statistics cited cover the 2026 regular season through Sep 28.
  - gate `W1.entity` token `Sep` in: All statistics cited cover the 2026 regular season through Sep 28.
  - gate `W1.number` token `28` in: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - gate `W1.entity` token `Sep` in: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - gate `W10.cause` token `due to` in: The command rating for Hagen Smith is missing due to a limited sample.
  - style `S-1` token `2026 regular season` in: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - style `S-7` token `in this split` in: That group carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) in this split.
  - style `S-7` token `in this split` in: Their K% is 24.1% and their BB% is 9.4% in this split.
  - style `S-2` token `the` in: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - NLI (score_only) score `0.9138178825378418`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'series.series_name', 'series.game_number']`: Hagen Smith and the Chicago White Sox meet AJ Blubaugh and the Houston Astros in AL Wild Card Series Game 1.
  - NLI (score_only) score `0.9950267672538757`, problem `None`, paths `['series.series_name', 'series.game_number']`: This is the first game of the AL Wild Card Series.
  - NLI (score_only) score `0.42513418197631836`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Hagen Smith starts for Chicago, and AJ Blubaugh takes the mound for Houston.
  - NLI (score_only) score `0.00014749818365089595`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: All statistics cited cover the 2026 regular season through Sep 28.
  - NLI (score_only) score `0.0011321170022711158`, problem `None`, paths `['series.series_name']`: Chicago and Houston play in this postseason matchup.
  - NLI (score_only) score `0.9881645441055298`, problem `None`, paths `['starters.away_starter.name']`: Hagen Smith is the visiting starter.
  - NLI (score_only) score `0.9858378767967224`, problem `None`, paths `['starters.home_starter.name']`: AJ Blubaugh is the starting pitcher for the home team.
  - NLI (score_only) score `0.9928285479545593`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Hagen Smith shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.05067127197980881`, problem `None`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: There is not enough data yet to rate his command, as he has 110 batters faced and 170 are needed for a read.
  - NLI (score_only) score `0.9963506460189819`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: The Houston lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9457364082336426`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: That group carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) in this split.
  - NLI (score_only) score `0.9058579802513123`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: AJ Blubaugh shows below-average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9889051914215088`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: He has a 3.66 ERA (earned run average) and a 1.23 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9896736145019531`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand']`: The Chicago lineup has a .716 OPS against right-handed pitchers.
  - NLI (score_only) score `0.8627888560295105`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: Their K% is 24.1% and their BB% is 9.4% in this split.
  - NLI (score_only) score `0.018440045416355133`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'pitch_mix.1.away_starter.overall']`: Hagen Smith throws a four-seam fastball 48.4% of the time and a slider 30.3% of the time.
  - NLI (score_only) score `0.010940219275653362`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9005054235458374`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'pitch_movement.away_starter.Slider.v_break']`: The slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `0.04318743944168091`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'pitch_mix.4.home_starter.overall']`: AJ Blubaugh relies on his four-seam fastball 51.4% of the time and his sweeper 22.9% of the time.
  - NLI (score_only) score `0.024559441953897476`, problem `None`, paths `['pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9443068504333496`, problem `None`, paths `['pitch_movement.home_starter.Sweeper.h_break', 'pitch_movement.home_starter.Sweeper.v_break']`: The sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Hagen Smith uses his slider to finish hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks']`: Watch whether AJ Blubaugh can control his pitches to avoid traffic.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.k_rate_vs_hand']`: Watch if Chicago can manage their 24.1% K% against the Houston pitching staff.
  - NLI (score_only) score `0.0001338053261861205`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - NLI (score_only) score `0.01848997175693512`, problem `None`, paths `['starters.away_starter.sample.limited.control']`: The command rating for Hagen Smith is missing due to a limited sample.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Hagen Smith'}, {'path': 'starters.home_starter.name', 'value': 'AJ Blubaugh'}, {'path': 'series.series_name', 'value': 'AL Wild Card Series'}, {'path': 'series.game_number', 'value': '1'}]`: Hagen Smith and the Chicago White Sox meet AJ Blubaugh and the Houston Astros in AL Wild Card Series Game 1.
  - Sentence evidence `[{'path': 'series.series_name', 'value': 'AL Wild Card Series'}, {'path': 'series.game_number', 'value': '1'}]`: This is the first game of the AL Wild Card Series.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Hagen Smith'}, {'path': 'starters.home_starter.name', 'value': 'AJ Blubaugh'}]`: Hagen Smith starts for Chicago, and AJ Blubaugh takes the mound for Houston.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season'}]`: All statistics cited cover the 2026 regular season through Sep 28.
  - Sentence evidence `[{'path': 'series.series_name', 'value': 'AL Wild Card Series'}]`: Chicago and Houston play in this postseason matchup.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Hagen Smith'}]`: Hagen Smith is the visiting starter.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'AJ Blubaugh'}]`: AJ Blubaugh is the starting pitcher for the home team.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Hagen Smith shows above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '110'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: There is not enough data yet to rate his command, as he has 110 batters faced and 170 are needed for a read.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.713'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: The Houston lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.0%'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '7.9%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: That group carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) in this split.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'Below-average command'}, {'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Average swing-and-miss ability'}]`: AJ Blubaugh shows below-average command and average swing-and-miss ability.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '3.66'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.23'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: He has a 3.66 ERA (earned run average) and a 1.23 WHIP (walks plus hits per inning).
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.716'}]`: The Chicago lineup has a .716 OPS against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.1%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '9.4%'}]`: Their K% is 24.1% and their BB% is 9.4% in this split.
  - Sentence evidence `[{'path': 'pitch_mix.0.away_starter.overall', 'value': '48.4'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '30.3'}]`: Hagen Smith throws a four-seam fastball 48.4% of the time and a slider 30.3% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '7.9'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '14.0'}]`: His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Slider.h_break', 'value': '-5.2'}, {'path': 'pitch_movement.away_starter.Slider.v_break', 'value': '-3.5'}]`: The slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_mix.0.home_starter.overall', 'value': '51.4'}, {'path': 'pitch_mix.4.home_starter.overall', 'value': '22.9'}]`: AJ Blubaugh relies on his four-seam fastball 51.4% of the time and his sweeper 22.9% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Four-seam.h_break', 'value': '-10.7'}, {'path': 'pitch_movement.home_starter.Four-seam.v_break', 'value': '17.2'}]`: His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Sweeper.h_break', 'value': '11.9'}, {'path': 'pitch_movement.home_starter.Sweeper.v_break', 'value': '3.7'}]`: The sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Slider'}]`: Watch how often Hagen Smith uses his slider to finish hitters.
  - Sentence evidence `[{'path': 'findings.home_starter_risks', 'value': 'Below-average command can create deep-count traffic'}]`: Watch whether AJ Blubaugh can control his pitches to avoid traffic.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.1%'}]`: Watch if Chicago can manage their 24.1% K% against the Houston pitching staff.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season'}]`: The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}]`: The command rating for Hagen Smith is missing due to a limited sample.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W1.entity', 'W10.cause'], style findings ['S-1', 'S-2', 'S-7']

**Headline**

Hagen Smith and the Chicago White Sox meet AJ Blubaugh and the Houston Astros in AL Wild Card Series Game 1.

**Short summary**

- This is the first game of the AL Wild Card Series.
- Hagen Smith starts for Chicago, and AJ Blubaugh takes the mound for Houston.
- All statistics cited cover the 2026 regular season through Sep 28.

**Matchup Summary**

Chicago and Houston play in this postseason matchup. Hagen Smith is the visiting starter. AJ Blubaugh is the starting pitcher for the home team.

**Hagen Smith vs Houston Astros**

Hagen Smith shows above-average swing-and-miss ability. There is not enough data yet to rate his command, as he has 110 batters faced and 170 are needed for a read. The Houston lineup has a .713 OPS (on-base plus slugging) against left-handed pitchers. That group carries a 21.0% K% (strikeout rate) and a 7.9% BB% (walk rate) in this split.

**AJ Blubaugh vs Chicago White Sox**

AJ Blubaugh shows below-average command and average swing-and-miss ability. He has a 3.66 ERA (earned run average) and a 1.23 WHIP (walks plus hits per inning). The Chicago lineup has a .716 OPS against right-handed pitchers. Their K% is 24.1% and their BB% is 9.4% in this split.

**Arsenal Scout**

Hagen Smith throws a four-seam fastball 48.4% of the time and a slider 30.3% of the time. His four-seam fastball moves 7.9 in. sideways and 14.0 in. up compared with a pitch thrown without spin. The slider moves 5.2 in. sideways and 3.5 in. down compared with a pitch thrown without spin. AJ Blubaugh relies on his four-seam fastball 51.4% of the time and his sweeper 22.9% of the time. His four-seam fastball moves 10.7 in. sideways and 17.2 in. up compared with a pitch thrown without spin. The sweeper moves 11.9 in. sideways and 3.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Hagen Smith uses his slider to finish hitters.
- Watch whether AJ Blubaugh can control his pitches to avoid traffic.
- Watch if Chicago can manage their 24.1% K% against the Houston pitching staff.

**Data Confidence Note**

The data for both starting pitchers and lineups is from the 2026 regular season through Sep 28. The command rating for Hagen Smith is missing due to a limited sample.


## opener-824280

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.entity', 'W1.evidence_path', 'W6.unsaid'], style findings ['S-4', 'W17.length'], tokens {'promptTokenCount': 7831, 'candidatesTokenCount': 1672, 'thoughtsTokenCount': 1464, 'totalTokenCount': 10967}
  - gate `W1.entity` token `This` in: The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%).
  - gate `W1.entity` token `The` in: The Detroit Tigers lineup shows a .725 OPS against right-handed pitchers. The group has a 22.3% K% and a 9.0% BB% and draws walks at an above-average rate.
  - gate `W1.entity` token `His` in: Trey Yesavage relies on a four-seam fastball 48.6% of the time and uses a splitter as his second most used pitch at 36.6%. His four-seam fastball moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - gate `W1.entity` token `His` in: Brenan Hanifee uses a sinker for 58.9% of his pitches and a slider as his second most used pitch at 18.8%. His sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - gate `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Trey Yesavage has faced 57 batters and requires 170 for a full read.
  - gate `W1.evidence_path` token `starters.home_starter.thresholds.control` in: Brenan Hanifee has faced 33 batters and requires 170 for a full read.
  - style `S-4` token `maintains` in: Trey Yesavage maintains a 0.68 earned run average (ERA) and a 1.35 walks plus hits per inning (WHIP). Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
  - style `S-4` token `maintains` in: The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%).
  - style `S-4` token `utilizes` in: Watch how often Trey Yesavage utilizes his four-seam fastball to set up hitters.
  - style `S-4` token `maintain` in: Watch if the Detroit hitters can maintain their walk rate against a new starter.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W17.length` token `1581` in: (whole report)
  - NLI (score_only) score `0.11148208379745483`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Trey Yesavage and Brenan Hanifee start in Detroit
  - NLI (score_only) score `0.00022074910521041602`, problem `None`, paths `['starters.away_starter.name', 'teams.away.name']`: Trey Yesavage starts for the Toronto Blue Jays against the Detroit Tigers.
  - NLI (score_only) score `0.9738951921463013`, problem `None`, paths `['starters.home_starter.name', 'teams.home.name']`: Brenan Hanifee takes the mound for the home team.
  - NLI (score_only) score `0.0004033002187497914`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.home_starter.sample.limited.control']`: Both starters enter the game with limited statistical samples.
  - NLI (score_only) score `0.13325916230678558`, problem `None`, paths `['starters.away_starter.season_summary.scopes.season_rates.label']`: All statistics in this report cover the 2026 regular season through May 14.
  - NLI (score_only) score `0.9856560230255127`, problem `None`, paths `['starters.away_starter.season_summary.era_number', 'starters.away_starter.season_summary.whip_number', 'starters.home_starter.season_summary.era_number', 'starters.home_starter.season_summary.whip_number', 'glossary.ERA.short', 'glossary.WHIP.short']`: Trey Yesavage maintains a 0.68 earned run average (ERA) and a 1.35 walks plus hits per inning (WHIP). Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
  - NLI (score_only) score `0.9834741950035095`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.bb_rate_number', 'glossary.OPS.short', 'glossary.K%.short', 'glossary.BB%.short']`: The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%).
  - NLI (score_only) score `0.9961519837379456`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.bb_rate_number', 'findings.lineup_notes.home']`: The Detroit Tigers lineup shows a .725 OPS against right-handed pitchers. The group has a 22.3% K% and a 9.0% BB% and draws walks at an above-average rate.
  - NLI (score_only) score `0.9430438280105591`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'pitch_mix.1.away_starter.overall', 'pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break', 'glossary.put-away pitch.short', 'glossary.Break.short']`: Trey Yesavage relies on a four-seam fastball 48.6% of the time and uses a splitter as his second most used pitch at 36.6%. His four-seam fastball moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.2733587622642517`, problem `None`, paths `['pitch_mix.3.home_starter.overall', 'pitch_mix.2.home_starter.overall', 'pitch_movement.home_starter.Sinker.h_break', 'pitch_movement.home_starter.Sinker.v_break']`: Brenan Hanifee uses a sinker for 58.9% of his pitches and a slider as his second most used pitch at 18.8%. His sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style']`: Watch how often Trey Yesavage utilizes his four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_style']`: Watch whether Brenan Hanifee leans on his sinker to initiate contact.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.bb_rate_number']`: Watch if the Detroit hitters can maintain their walk rate against a new starter.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.thresholds.control']`: Trey Yesavage has faced 57 batters and requires 170 for a full read.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.thresholds.control']`: Brenan Hanifee has faced 33 batters and requires 170 for a full read.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Trey Yesavage'}, {'path': 'starters.home_starter.name', 'value': 'Brenan Hanifee'}]`: Trey Yesavage and Brenan Hanifee start in Detroit
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Trey Yesavage'}, {'path': 'teams.away.name', 'value': 'Toronto Blue Jays'}]`: Trey Yesavage starts for the Toronto Blue Jays against the Detroit Tigers.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Brenan Hanifee'}, {'path': 'teams.home.name', 'value': 'Detroit Tigers'}]`: Brenan Hanifee takes the mound for the home team.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}]`: Both starters enter the game with limited statistical samples.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through May 14'}]`: All statistics in this report cover the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era_number', 'value': '0.68'}, {'path': 'starters.away_starter.season_summary.whip_number', 'value': '1.35'}, {'path': 'starters.home_starter.season_summary.era_number', 'value': '1.08'}, {'path': 'starters.home_starter.season_summary.whip_number', 'value': '1.08'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: Trey Yesavage maintains a 0.68 earned run average (ERA) and a 1.35 walks plus hits per inning (WHIP). Brenan Hanifee carries a 1.08 ERA and a 1.08 WHIP.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_number', 'value': '0.701'}, {'path': 'teams.away.offense_profile.k_rate_number', 'value': '18.2'}, {'path': 'teams.away.offense_profile.bb_rate_number', 'value': '7.3'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: The Toronto lineup records a .701 on-base plus slugging (OPS) when facing right-handed pitchers. This group maintains a 18.2% strikeout rate (K%) and a 7.3% walk rate (BB%).
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_number', 'value': '0.725'}, {'path': 'teams.home.offense_profile.k_rate_number', 'value': '22.3'}, {'path': 'teams.home.offense_profile.bb_rate_number', 'value': '9.0'}, {'path': 'findings.lineup_notes.home', 'value': 'draws walks at an above-average rate'}]`: The Detroit Tigers lineup shows a .725 OPS against right-handed pitchers. The group has a 22.3% K% and a 9.0% BB% and draws walks at an above-average rate.
  - Sentence evidence `[{'path': 'pitch_mix.0.away_starter.overall', 'value': '48.6'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '36.6'}, {'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '-4.8'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '19.9'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}, {'path': 'glossary.Break.short', 'value': 'total movement'}]`: Trey Yesavage relies on a four-seam fastball 48.6% of the time and uses a splitter as his second most used pitch at 36.6%. His four-seam fastball moves 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_mix.3.home_starter.overall', 'value': '58.9'}, {'path': 'pitch_mix.2.home_starter.overall', 'value': '18.8'}, {'path': 'pitch_movement.home_starter.Sinker.h_break', 'value': '-16.2'}, {'path': 'pitch_movement.home_starter.Sinker.v_break', 'value': '3.4'}]`: Brenan Hanifee uses a sinker for 58.9% of his pitches and a slider as his second most used pitch at 18.8%. His sinker moves 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'findings.away_style', 'value': 'Four-seam to set up, Splitter to finish'}]`: Watch how often Trey Yesavage utilizes his four-seam fastball to set up hitters.
  - Sentence evidence `[{'path': 'findings.home_style', 'value': 'Sinker to set up, Slider to finish'}]`: Watch whether Brenan Hanifee leans on his sinker to initiate contact.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.bb_rate_number', 'value': '9.0'}]`: Watch if the Detroit hitters can maintain their walk rate against a new starter.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '57'}, {'path': 'starters.away_starter.thresholds.control', 'value': '170'}]`: Trey Yesavage has faced 57 batters and requires 170 for a full read.
  - Sentence evidence `[{'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '33'}, {'path': 'starters.home_starter.thresholds.control', 'value': '170'}]`: Brenan Hanifee has faced 33 batters and requires 170 for a full read.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W15.outcome'], style findings ['S-1', 'S-7', 'W11.expansion'], tokens {'promptTokenCount': 7945, 'candidatesTokenCount': 2258, 'thoughtsTokenCount': 519, 'totalTokenCount': 10722}
  - gate `W15.outcome` token `strikeout` in: Watch how the Detroit Tigers lineup manages the strikeout rate against Trey Yesavage.
  - style `W11.expansion` token `put-away pitch` in: His put-away pitch is the splitter, which he throws 36.6% of the time, moving 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin.
  - style `S-1` token `2026 regular season through May 14` in: Trey Yesavage holds a 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning) for the Toronto Blue Jays during the 2026 regular season through May 14.
  - style `S-7` token `in this split` in: That group has a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split, and it draws walks at an above-average rate.
  - NLI (score_only) score `0.11148208379745483`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Trey Yesavage and Brenan Hanifee start in Detroit
  - NLI (score_only) score `0.20449702441692352`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Trey Yesavage faces off against Brenan Hanifee as Toronto visits Detroit.
  - NLI (score_only) score `0.0002008520532399416`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: Both starters bring early season pitching numbers into this matchup for the 2026 regular season through May 14.
  - NLI (score_only) score `0.9952791929244995`, problem `None`, paths `['venue']`: The game takes place at Comerica Park.
  - NLI (score_only) score `0.005883451085537672`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.whip', 'starters.away_starter.sample.arsenal.scope.label', 'glossary.ERA.short', 'glossary.WHIP.short']`: Trey Yesavage holds a 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning) for the Toronto Blue Jays during the 2026 regular season through May 14.
  - NLI (score_only) score `0.00022180165979079902`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip', 'starters.home_starter.sample.arsenal.scope.label']`: Brenan Hanifee has a 1.08 ERA and a 1.08 WHIP for the Detroit Tigers in that same period.
  - NLI (score_only) score `0.00047968627768568695`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.home_starter.sample.limited.control']`: Control and strikeout data for both pitchers remains in a limited sample.
  - NLI (score_only) score `0.6209734678268433`, problem `None`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.sample.thresholds.strikeout']`: Trey Yesavage has a limited sample of 57 batters faced, with 170 needed for a control read and 70 for a strikeout read.
  - NLI (score_only) score `0.9980633854866028`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short', 'teams.home.offense_profile.scope.label']`: The Detroit Tigers lineup against right-handed pitchers carries a .725 OPS (on-base plus slugging) as of the 2026 regular season through May 14.
  - NLI (score_only) score `0.9347684979438782`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short', 'findings.lineup_notes.home']`: That group has a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split, and it draws walks at an above-average rate.
  - NLI (score_only) score `0.9355326890945435`, problem `None`, paths `['starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.sample.thresholds.strikeout']`: Brenan Hanifee has a limited sample of 33 batters faced, with 170 needed for a control read and 70 for a strikeout read.
  - NLI (score_only) score `0.9926457405090332`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label']`: The Toronto Blue Jays lineup against right-handed pitchers has a .701 OPS, an 18.2% K%, and a 7.3% BB% over the 2026 regular season through May 14.
  - NLI (score_only) score `0.8051526546478271`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break', 'glossary.Break.short']`: Trey Yesavage uses a four-seam fastball 48.6% of the time, moving 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.07261384278535843`, problem `None`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'pitch_mix.1.away_starter.overall', 'pitch_movement.away_starter.Splitter.h_break', 'pitch_movement.away_starter.Splitter.v_break']`: His put-away pitch is the splitter, which he throws 36.6% of the time, moving 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9795798063278198`, problem `None`, paths `['pitch_mix.3.home_starter.overall', 'pitch_movement.home_starter.Sinker.h_break', 'pitch_movement.home_starter.Sinker.v_break']`: Brenan Hanifee uses a sinker 58.9% of the time, moving 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.28483375906944275`, problem `None`, paths `['starters.home_starter.pitching_profile.putaway_pitch', 'pitch_mix.2.home_starter.overall', 'pitch_movement.home_starter.Slider.h_break', 'pitch_movement.home_starter.Slider.v_break']`: His put-away pitch is the slider, which he uses 18.8% of the time, moving 1.7 in. sideways and 2.8 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style']`: Watch how often Trey Yesavage relies on his four-seam fastball to set up his splitter.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_style']`: Watch whether Brenan Hanifee uses his sinker effectively to set up his slider.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.k_rate_vs_hand']`: Watch how the Detroit Tigers lineup manages the strikeout rate against Trey Yesavage.
  - NLI (score_only) score `0.9708505272865295`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.sample.arsenal.scope.label']`: The data provided for this matchup uses probable pitchers for the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Trey Yesavage'}, {'path': 'starters.home_starter.name', 'value': 'Brenan Hanifee'}]`: Trey Yesavage and Brenan Hanifee start in Detroit
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Trey Yesavage'}, {'path': 'starters.home_starter.name', 'value': 'Brenan Hanifee'}]`: Trey Yesavage faces off against Brenan Hanifee as Toronto visits Detroit.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through May 14'}]`: Both starters bring early season pitching numbers into this matchup for the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'venue', 'value': 'Comerica Park'}]`: The game takes place at Comerica Park.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era', 'value': '0.68'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.35'}, {'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through May 14'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: Trey Yesavage holds a 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning) for the Toronto Blue Jays during the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '1.08'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.08'}, {'path': 'starters.home_starter.sample.arsenal.scope.label', 'value': '2026 regular season through May 14'}]`: Brenan Hanifee has a 1.08 ERA and a 1.08 WHIP for the Detroit Tigers in that same period.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}]`: Control and strikeout data for both pitchers remains in a limited sample.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '57'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}, {'path': 'starters.away_starter.sample.thresholds.strikeout', 'value': '70'}]`: Trey Yesavage has a limited sample of 57 batters faced, with 170 needed for a control read and 70 for a strikeout read.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.725'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}, {'path': 'teams.home.offense_profile.scope.label', 'value': '2026 regular season through May 14'}]`: The Detroit Tigers lineup against right-handed pitchers carries a .725 OPS (on-base plus slugging) as of the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '22.3%'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '9.0%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}, {'path': 'findings.lineup_notes.home', 'value': 'draws walks at an above-average rate'}]`: That group has a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split, and it draws walks at an above-average rate.
  - Sentence evidence `[{'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '33'}, {'path': 'starters.home_starter.sample.thresholds.control', 'value': '170'}, {'path': 'starters.home_starter.sample.thresholds.strikeout', 'value': '70'}]`: Brenan Hanifee has a limited sample of 33 batters faced, with 170 needed for a control read and 70 for a strikeout read.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.701'}, {'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '18.2%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '7.3%'}, {'path': 'teams.away.offense_profile.scope.label', 'value': '2026 regular season through May 14'}]`: The Toronto Blue Jays lineup against right-handed pitchers has a .701 OPS, an 18.2% K%, and a 7.3% BB% over the 2026 regular season through May 14.
  - Sentence evidence `[{'path': 'pitch_mix.0.away_starter.overall', 'value': '48.6'}, {'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '-4.8'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '19.9'}, {'path': 'glossary.Break.short', 'value': 'total movement'}]`: Trey Yesavage uses a four-seam fastball 48.6% of the time, moving 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Splitter'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '36.6'}, {'path': 'pitch_movement.away_starter.Splitter.h_break', 'value': '-11.8'}, {'path': 'pitch_movement.away_starter.Splitter.v_break', 'value': '6.2'}]`: His put-away pitch is the splitter, which he throws 36.6% of the time, moving 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_mix.3.home_starter.overall', 'value': '58.9'}, {'path': 'pitch_movement.home_starter.Sinker.h_break', 'value': '-16.2'}, {'path': 'pitch_movement.home_starter.Sinker.v_break', 'value': '3.4'}]`: Brenan Hanifee uses a sinker 58.9% of the time, moving 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Slider'}, {'path': 'pitch_mix.2.home_starter.overall', 'value': '18.8'}, {'path': 'pitch_movement.home_starter.Slider.h_break', 'value': '1.7'}, {'path': 'pitch_movement.home_starter.Slider.v_break', 'value': '2.8'}]`: His put-away pitch is the slider, which he uses 18.8% of the time, moving 1.7 in. sideways and 2.8 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'findings.away_style', 'value': 'Four-seam to set up, Splitter to finish'}]`: Watch how often Trey Yesavage relies on his four-seam fastball to set up his splitter.
  - Sentence evidence `[{'path': 'findings.home_style', 'value': 'Sinker to set up, Slider to finish'}]`: Watch whether Brenan Hanifee uses his sinker effectively to set up his slider.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '22.3%'}]`: Watch how the Detroit Tigers lineup manages the strikeout rate against Trey Yesavage.
  - Sentence evidence `[{'path': 'data_confidence.lineup_status', 'value': 'probable pitchers'}, {'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through May 14'}]`: The data provided for this matchup uses probable pitchers for the 2026 regular season through May 14.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W15.outcome'], style findings ['S-1', 'S-7', 'W11.expansion']

**Headline**

Trey Yesavage and Brenan Hanifee start in Detroit

**Short summary**

- Trey Yesavage faces off against Brenan Hanifee as Toronto visits Detroit.
- Both starters bring early season pitching numbers into this matchup for the 2026 regular season through May 14.
- The game takes place at Comerica Park.

**Matchup Summary**

Trey Yesavage holds a 0.68 ERA (earned run average) and a 1.35 WHIP (walks plus hits per inning) for the Toronto Blue Jays during the 2026 regular season through May 14. Brenan Hanifee has a 1.08 ERA and a 1.08 WHIP for the Detroit Tigers in that same period. Control and strikeout data for both pitchers remains in a limited sample.

**Trey Yesavage vs Detroit Tigers**

Trey Yesavage has a limited sample of 57 batters faced, with 170 needed for a control read and 70 for a strikeout read. The Detroit Tigers lineup against right-handed pitchers carries a .725 OPS (on-base plus slugging) as of the 2026 regular season through May 14. That group has a 22.3% K% (strikeout rate) and a 9.0% BB% (walk rate) in this split, and it draws walks at an above-average rate.

**Brenan Hanifee vs Toronto Blue Jays**

Brenan Hanifee has a limited sample of 33 batters faced, with 170 needed for a control read and 70 for a strikeout read. The Toronto Blue Jays lineup against right-handed pitchers has a .701 OPS, an 18.2% K%, and a 7.3% BB% over the 2026 regular season through May 14.

**Arsenal Scout**

Trey Yesavage uses a four-seam fastball 48.6% of the time, moving 4.8 in. sideways and 19.9 in. up compared with a pitch thrown without spin. His put-away pitch is the splitter, which he throws 36.6% of the time, moving 11.8 in. sideways and 6.2 in. up compared with a pitch thrown without spin. Brenan Hanifee uses a sinker 58.9% of the time, moving 16.2 in. sideways and 3.4 in. up compared with a pitch thrown without spin. His put-away pitch is the slider, which he uses 18.8% of the time, moving 1.7 in. sideways and 2.8 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Trey Yesavage relies on his four-seam fastball to set up his splitter.
- Watch whether Brenan Hanifee uses his sinker effectively to set up his slider.
- Watch how the Detroit Tigers lineup manages the strikeout rate against Trey Yesavage.

**Data Confidence Note**

The data provided for this matchup uses probable pitchers for the 2026 regular season through May 14.


## opener-823769

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary_retry`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503')], model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 8246, 'candidatesTokenCount': 1879, 'thoughtsTokenCount': 1279, 'totalTokenCount': 11404}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W2.comparison', 'W1.evidence_path', 'W15.outcome'], style findings ['S-1', 'S-4', 'S-5', 'S-7'], tokens {'promptTokenCount': 8275, 'candidatesTokenCount': 1915, 'thoughtsTokenCount': 1321, 'totalTokenCount': 11511}
  - gate `W2.comparison` token `versus` in: Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup
  - gate `W1.evidence_path` token `starters.away_starter.thresholds.control` in: Control data for Rolison is limited: 114 batters faced, and 170 are needed for a read.
  - gate `W1.evidence_path` token `starters.home_starter.thresholds.control` in: Control data for Woodruff is limited: 140 batters faced, and 170 are needed for a read.
  - gate `W15.outcome` token `strikeout` in: Watch whether the Milwaukee hitters can control their strikeout rate against a left-handed starter.
  - style `S-1` token `2026 regular season through Jun 27` in: Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) during the 2026 regular season through Jun 27.
  - style `S-4` token `maintains` in: Brandon Woodruff maintains a 3.00 ERA and a 0.89 WHIP over the same period.
  - style `S-7` token `over the same period` in: Brandon Woodruff maintains a 3.00 ERA and a 0.89 WHIP over the same period.
  - style `S-4` token `maintain` in: Their strikeout rate is 21.2% and they maintain an 11.4% walk rate during this stretch.
  - style `S-4` token `possesses` in: Woodruff possesses above-average swing-and-miss ability.
  - style `S-5` token `matchup` in: Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup
  - NLI (score_only) score `0.8178454637527466`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup
  - NLI (score_only) score `0.03545970842242241`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Ryan Rolison takes the mound for the Chicago Cubs against Brandon Woodruff and the Milwaukee Brewers.
  - NLI (score_only) score `0.9971150159835815`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: Data covers the 2026 regular season through Jun 27.
  - NLI (score_only) score `0.0073483726009726524`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.primary_pitch']`: Both pitchers rely on four-seam fastballs to begin their work.
  - NLI (score_only) score `0.9959040284156799`, problem `None`, paths `['starters.away_starter.season_summary.era', 'glossary.ERA.short', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short', 'starters.away_starter.sample.arsenal.scope.label']`: Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) during the 2026 regular season through Jun 27.
  - NLI (score_only) score `0.02180405706167221`, problem `None`, paths `['starters.home_starter.season_summary.era_number', 'starters.home_starter.season_summary.whip_number']`: Brandon Woodruff maintains a 3.00 ERA and a 0.89 WHIP over the same period.
  - NLI (score_only) score `0.9971426129341125`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short', 'teams.home.offense_profile.scope.label']`: The Brewers lineup has a .682 OPS (on-base plus slugging) against left-handed pitchers during the 2026 regular season through Jun 27.
  - NLI (score_only) score `0.9780669212341309`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: This group carries a 21.8% strikeout rate (K%) and draws walks at a 10.3% walk rate (BB%).
  - NLI (score_only) score `0.9967017769813538`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Rolison shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.9974380731582642`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label']`: The Chicago Cubs lineup holds a .734 OPS against right-handed pitchers over the 2026 regular season through Jun 27.
  - NLI (score_only) score `0.9641221761703491`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: Their strikeout rate is 21.2% and they maintain an 11.4% walk rate during this stretch.
  - NLI (score_only) score `0.9986977577209473`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label']`: Woodruff possesses above-average swing-and-miss ability.
  - NLI (score_only) score `0.9950666427612305`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'pitch_mix.1.away_starter.overall', 'glossary.put-away pitch.short']`: Rolison throws a four-seam fastball 44.8% of the time and uses a slider, his second most used pitch (put-away pitch), 19.9% of the time.
  - NLI (score_only) score `0.9786146879196167`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'pitch_movement.away_starter.Slider.v_break']`: His slider moves 4.4 in. sideways and 2.3 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0018547592917457223`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'pitch_mix.5.home_starter.overall']`: Woodruff uses his four-seam fastball 43.9% of the time and relies on a changeup as his second most used pitch 19.8% of the time.
  - NLI (score_only) score `0.9503750801086426`, problem `None`, paths `['pitch_movement.home_starter.Changeup.h_break', 'pitch_movement.home_starter.Changeup.v_break']`: His changeup moves 16.1 in. sideways and 8.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.thresholds.control']`: Control data for Rolison is limited: 114 batters faced, and 170 are needed for a read.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.thresholds.control']`: Control data for Woodruff is limited: 140 batters faced, and 170 are needed for a read.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Rolison uses his slider to finish sequences.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.k_rate_vs_hand']`: Watch whether the Milwaukee hitters can control their strikeout rate against a left-handed starter.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.putaway_pitch']`: Watch how Woodruff spots his changeup during the game.
  - NLI (score_only) score `0.9353285431861877`, problem `None`, paths `['status']`: The current status of this game is upcoming.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Ryan Rolison'}, {'path': 'starters.home_starter.name', 'value': 'Brandon Woodruff'}]`: Ryan Rolison faces Brandon Woodruff in Chicago versus Milwaukee matchup
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Ryan Rolison'}, {'path': 'starters.home_starter.name', 'value': 'Brandon Woodruff'}]`: Ryan Rolison takes the mound for the Chicago Cubs against Brandon Woodruff and the Milwaukee Brewers.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through Jun 27'}]`: Data covers the 2026 regular season through Jun 27.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}, {'path': 'starters.home_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}]`: Both pitchers rely on four-seam fastballs to begin their work.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.era', 'value': '1.82'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.11'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}, {'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through Jun 27'}]`: Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning) during the 2026 regular season through Jun 27.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era_number', 'value': '3.0'}, {'path': 'starters.home_starter.season_summary.whip_number', 'value': '0.89'}]`: Brandon Woodruff maintains a 3.00 ERA and a 0.89 WHIP over the same period.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.682'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}, {'path': 'teams.home.offense_profile.scope.label', 'value': '2026 regular season through Jun 27'}]`: The Brewers lineup has a .682 OPS (on-base plus slugging) against left-handed pitchers during the 2026 regular season through Jun 27.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.8%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '10.3%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: This group carries a 21.8% strikeout rate (K%) and draws walks at a 10.3% walk rate (BB%).
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Rolison shows above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.734'}, {'path': 'teams.away.offense_profile.scope.label', 'value': '2026 regular season through Jun 27'}]`: The Chicago Cubs lineup holds a .734 OPS against right-handed pitchers over the 2026 regular season through Jun 27.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '21.2%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '11.4%'}]`: Their strikeout rate is 21.2% and they maintain an 11.4% walk rate during this stretch.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Above-average swing-and-miss ability'}]`: Woodruff possesses above-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'pitch_mix.0.away_starter.overall', 'value': '44.8'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '19.9'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}]`: Rolison throws a four-seam fastball 44.8% of the time and uses a slider, his second most used pitch (put-away pitch), 19.9% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Slider.h_break', 'value': '-4.4'}, {'path': 'pitch_movement.away_starter.Slider.v_break', 'value': '-2.3'}]`: His slider moves 4.4 in. sideways and 2.3 in. down compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'pitch_mix.0.home_starter.overall', 'value': '43.9'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '19.8'}]`: Woodruff uses his four-seam fastball 43.9% of the time and relies on a changeup as his second most used pitch 19.8% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Changeup.h_break', 'value': '-16.1'}, {'path': 'pitch_movement.home_starter.Changeup.v_break', 'value': '8.0'}]`: His changeup moves 16.1 in. sideways and 8.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '114'}, {'path': 'starters.away_starter.thresholds.control', 'value': '170'}]`: Control data for Rolison is limited: 114 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '140'}, {'path': 'starters.home_starter.thresholds.control', 'value': '170'}]`: Control data for Woodruff is limited: 140 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Slider'}]`: Watch how often Rolison uses his slider to finish sequences.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.8%'}]`: Watch whether the Milwaukee hitters can control their strikeout rate against a left-handed starter.
  - Sentence evidence `[{'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Changeup'}]`: Watch how Woodruff spots his changeup during the game.
  - Sentence evidence `[{'path': 'status', 'value': 'upcoming'}]`: The current status of this game is upcoming.
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

Ryan Rolison and Brandon Woodruff meet in Milwaukee

**Short summary**

- Ryan Rolison makes the start for Chicago against Brandon Woodruff of Milwaukee.
- Both starters show above-average swing-and-miss ability.
- The lineups for both teams draw walks at an above-average rate.
- All data in this report covers the 2026 regular season through Jun 27.

**Matchup Summary**

Ryan Rolison carries a 1.82 ERA (earned run average) and a 1.11 WHIP (walks plus hits per inning). Brandon Woodruff maintains a 3.0 ERA and a 0.89 WHIP. Woodruff has a lower WHIP than Rolison, while Rolison has a lower ERA than Woodruff.

**Ryan Rolison vs Milwaukee Brewers**

The Brewers lineup has a .682 OPS (on-base plus slugging) against left-handed pitchers. This group has a 21.8% K% (strikeout rate) and a 10.3% BB% (walk rate). Rolison has a limited sample for control: 114 batters faced, and 170 are needed for a read.

**Brandon Woodruff vs Chicago Cubs**

Against right-handed pitchers, the Cubs lineup has a .734 OPS. They carry a 21.2% K% and an 11.4% BB%. Woodruff has a limited sample for control: 140 batters faced, and 170 are needed for a read.

**Arsenal Scout**

Rolison uses his Four-seam fastball 44.8% of the time and uses his Slider (second most used pitch) 19.9% of the time. His Slider moves 4.4 in. sideways and 2.3 in. down compared with a pitch thrown without spin. Woodruff throws his Four-seam fastball 43.9% of the time and his Changeup (second most used pitch) 19.8% of the time. His Changeup moves 16.1 in. sideways and 8.0 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Rolison uses his Slider in counts where he needs a finish.
- Watch whether Woodruff executes his Changeup against right-handed hitters effectively.
- Watch if the Cubs lineup can generate walks against Woodruff.

**Data Confidence Note**

Data confidence reflects that these are the probable pitchers.


## limited-823836

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503'), ('gemini-3.1-flash-lite', 2, 'http_503')], model `gemini-3.5-flash`, gate checks ['W12.time'], style findings ['S-1', 'S-2', 'W11.repeat', 'W17.length'], tokens {'promptTokenCount': 8183, 'candidatesTokenCount': 1915, 'totalTokenCount': 10098}
  - gate `W12.time` token `this season` in: George Klassen has pitched 4.2 innings this season.
  - style `W11.repeat` token `ERA` in: George Klassen starts for the Angels with a 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning).
  - style `S-1` token `2026 regular season through Aug 6` in: This report covers the 2026 regular season through Aug 6.
  - style `S-2` token `george` in: George Klassen has pitched 4.2 innings this season.
  - style `S-2` token `tyler` in: Tyler Phillips has completed 89.1 innings.
  - style `W17.length` token `1712` in: (whole report)
  - NLI (score_only) score `0.0036982977762818336`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: George Klassen faces Tyler Phillips in Miami
  - NLI (score_only) score `0.9883227944374084`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.limited.strikeout']`: George Klassen has limited control and strikeout data.
  - NLI (score_only) score `0.0003308072919026017`, problem `None`, paths `['starters.home_starter.season_summary.era', 'glossary.ERA.short']`: Tyler Phillips carries a 3.53 ERA (earned run average) for Miami.
  - NLI (score_only) score `0.9973068237304688`, problem `None`, paths `['starters.away_starter.season_summary.scopes.season_rates.label']`: This report uses data from the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.9937098026275635`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'glossary.ERA.short', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short']`: George Klassen starts for the Angels with a 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.0023145556915551424`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip']`: Tyler Phillips has a 3.53 ERA and a 1.35 WHIP for the Marlins.
  - NLI (score_only) score `0.9935368895530701`, problem `None`, paths `['starters.away_starter.season_summary.scopes.season_rates.label']`: This report covers the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.9956368803977966`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: George Klassen has limited control data with 32 batters faced when 170 are needed.
  - NLI (score_only) score `0.9893761873245239`, problem `None`, paths `['starters.away_starter.sample.limited.strikeout', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.strikeout']`: His strikeout data is also limited with 32 batters faced out of 70 required.
  - NLI (score_only) score `0.9975837469100952`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: Against right-handed pitchers, the Marlins lineup has a .734 OPS (on-base plus slugging).
  - NLI (score_only) score `0.9796660542488098`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: Their K% (strikeout rate) is 21.0% and their BB% (walk rate) is 8.9%.
  - NLI (score_only) score `0.9534416198730469`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Tyler Phillips shows average command and below-average swing-and-miss ability.
  - NLI (score_only) score `0.9982703924179077`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand']`: Against right-handed pitchers, the Angels lineup posts a .687 OPS.
  - NLI (score_only) score `0.991425633430481`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: That lineup shows a 24.9% K% and an 8.3% BB%.
  - NLI (score_only) score `0.9848220944404602`, problem `None`, paths `['findings.lineup_notes.away']`: Los Angeles has elevated swing-and-miss risk.
  - NLI (score_only) score `0.9530181884765625`, problem `None`, paths `['starters.away_starter.name', 'pitch_mix.0.away_starter.overall', 'pitch_mix.1.away_starter.overall']`: George Klassen relies on a Four-seam fastball at 38.6% and a Changeup at 24.8%.
  - NLI (score_only) score `0.863078236579895`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.08270952850580215`, problem `None`, paths `['starters.home_starter.name', 'pitch_mix.4.home_starter.overall', 'pitch_mix.5.home_starter.overall']`: Tyler Phillips throws a Sinker 25.5% of the time and a Sweeper 24.2% of the time.
  - NLI (score_only) score `0.9423604607582092`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'pitch_movement.home_starter.Sinker.v_break']`: His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.name', 'starters.away_starter.pitching_profile.primary_pitch']`: Watch how often George Klassen relies on his Four-seam pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.name', 'glossary.put-away pitch.short', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Tyler Phillips throws his put-away pitch (second most used pitch), the Sweeper.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'starters.home_starter.name']`: Watch if the Angels manage their 24.9% K% against Tyler Phillips.
  - NLI (score_only) score `0.9503222703933716`, problem `None`, paths `['data_confidence.lineup_status']`: Lineup status is probable pitchers.
  - NLI (score_only) score `0.45742902159690857`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.innings']`: George Klassen has pitched 4.2 innings this season.
  - NLI (score_only) score `0.9956113696098328`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.innings']`: Tyler Phillips has completed 89.1 innings.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}]`: George Klassen faces Tyler Phillips in Miami
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.limited.strikeout', 'value': 'true'}]`: George Klassen has limited control and strikeout data.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.era', 'value': '3.53'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}]`: Tyler Phillips carries a 3.53 ERA (earned run average) for Miami.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Aug 6'}]`: This report uses data from the 2026 regular season through Aug 6.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.season_summary.era', 'value': '11.57'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '3.64'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: George Klassen starts for the Angels with a 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning).
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.season_summary.era', 'value': '3.53'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.35'}]`: Tyler Phillips has a 3.53 ERA and a 1.35 WHIP for the Marlins.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Aug 6'}]`: This report covers the 2026 regular season through Aug 6.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '32'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: George Klassen has limited control data with 32 batters faced when 170 are needed.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.strikeout', 'value': 'true'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '32'}, {'path': 'starters.away_starter.sample.thresholds.strikeout', 'value': '70'}]`: His strikeout data is also limited with 32 batters faced out of 70 required.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.734'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: Against right-handed pitchers, the Marlins lineup has a .734 OPS (on-base plus slugging).
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.0%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '8.9%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: Their K% (strikeout rate) is 21.0% and their BB% (walk rate) is 8.9%.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'Average command'}, {'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Below-average swing-and-miss ability'}]`: Tyler Phillips shows average command and below-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.687'}]`: Against right-handed pitchers, the Angels lineup posts a .687 OPS.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.9%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '8.3%'}]`: That lineup shows a 24.9% K% and an 8.3% BB%.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': 'has elevated swing-and-miss risk'}]`: Los Angeles has elevated swing-and-miss risk.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'pitch_mix.0.away_starter.overall', 'value': '38.6'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '24.8'}]`: George Klassen relies on a Four-seam fastball at 38.6% and a Changeup at 24.8%.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '-14.8'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '14.2'}]`: His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'pitch_mix.4.home_starter.overall', 'value': '25.5'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '24.2'}]`: Tyler Phillips throws a Sinker 25.5% of the time and a Sweeper 24.2% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Sinker.h_break', 'value': '-17.3'}, {'path': 'pitch_movement.home_starter.Sinker.v_break', 'value': '8.5'}]`: His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}]`: Watch how often George Klassen relies on his Four-seam pitch.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}, {'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Sweeper'}]`: Watch whether Tyler Phillips throws his put-away pitch (second most used pitch), the Sweeper.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.9%'}, {'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}]`: Watch if the Angels manage their 24.9% K% against Tyler Phillips.
  - Sentence evidence `[{'path': 'data_confidence.lineup_status', 'value': 'probable pitchers'}]`: Lineup status is probable pitchers.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.season_summary.innings', 'value': '4.2'}]`: George Klassen has pitched 4.2 innings this season.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.season_summary.innings', 'value': '89.1'}]`: Tyler Phillips has completed 89.1 innings.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503'), ('gemini-3.1-flash-lite', 2, 'http_503')], model `gemini-3.5-flash`, gate checks ['W2.comparison', 'W12.time', 'W6.unsaid'], style findings ['S-4', 'W17.length'], tokens {'promptTokenCount': 8277, 'candidatesTokenCount': 1942, 'totalTokenCount': 10219}
  - gate `W2.comparison` token `lower` in: Phillips owns a lower WHIP of 1.35.
  - gate `W12.time` token `this season` in: George Klassen thrown 4.2 innings this season.
  - gate `W2.comparison` token `versus` in: The Angels lineup has a .687 OPS versus right-handed pitching.
  - style `S-4` token `features` in: This matchup features right-hander George Klassen against right-hander Tyler Phillips.
  - style `S-4` token `features` in: Tyler Phillips features a Sinker 25.5% of the time and a Sweeper 24.2% of the time.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W17.length` token `1666` in: (whole report)
  - NLI (score_only) score `0.030937032774090767`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'teams.away.name', 'teams.home.name']`: George Klassen faces Tyler Phillips as the Angels play the Marlins.
  - NLI (score_only) score `0.9978581070899963`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'glossary.ERA.short', 'teams.away.name']`: George Klassen carries an 11.57 ERA (earned run average) for the Angels.
  - NLI (score_only) score `0.9969391822814941`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.era', 'teams.home.name']`: Tyler Phillips has a 3.53 ERA for the Marlins.
  - NLI (score_only) score `0.3545101284980774`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label']`: All statistics cover the 2026 regular season through Aug 6.
  - NLI (score_only) score `0.22794024646282196`, problem `None`, paths `['starters.away_starter.throws', 'starters.away_starter.name', 'starters.home_starter.throws', 'starters.home_starter.name']`: This matchup features right-hander George Klassen against right-hander Tyler Phillips.
  - NLI (score_only) score `0.9970076680183411`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short']`: Klassen holds a 3.64 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.004904973320662975`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.whip_number', 'starters.away_starter.season_summary.whip_number']`: Phillips owns a lower WHIP of 1.35.
  - NLI (score_only) score `0.9669045805931091`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.innings']`: George Klassen thrown 4.2 innings this season.
  - NLI (score_only) score `0.9526411890983582`, problem `None`, paths `['starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: Control data for him is limited with 32 batters faced out of 170 needed.
  - NLI (score_only) score `0.9914180040359497`, problem `None`, paths `['teams.home.name', 'teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short']`: Miami has a .734 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9771677851676941`, problem `None`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short', 'teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short']`: Their offense posts an 8.9% BB% (walk rate) and a 21.0% K% (strikeout rate).
  - NLI (score_only) score `0.9534416198730469`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Tyler Phillips shows average command and below-average swing-and-miss ability.
  - NLI (score_only) score `0.9968352913856506`, problem `None`, paths `['starters.home_starter.season_summary.strikeouts', 'glossary.K.short', 'starters.home_starter.season_summary.walks', 'starters.home_starter.season_summary.innings']`: He has recorded 66 K (strikeouts) and 38 walks across 89.1 innings.
  - NLI (score_only) score `0.9953734278678894`, problem `None`, paths `['teams.away.name', 'teams.away.offense_profile.ops_vs_hand']`: The Angels lineup has a .687 OPS versus right-handed pitching.
  - NLI (score_only) score `0.9289144277572632`, problem `None`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.k_rate_vs_hand']`: That offense has elevated swing-and-miss risk with a 24.9% K%.
  - NLI (score_only) score `0.9729375243186951`, problem `None`, paths `['starters.away_starter.name', 'pitch_mix.0.away_starter.overall', 'starters.away_starter.pitching_profile.primary_pitch']`: George Klassen relies on his Four-seam fastball 38.6% of the time as his primary pitch.
  - NLI (score_only) score `0.9975759387016296`, problem `None`, paths `['glossary.put-away pitch.short', 'starters.away_starter.pitching_profile.putaway_pitch', 'pitch_mix.1.away_starter.overall']`: His put-away pitch (second most used pitch) is the Changeup at 24.8%.
  - NLI (score_only) score `0.863078236579895`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9650682806968689`, problem `None`, paths `['starters.home_starter.name', 'pitch_mix.4.home_starter.overall', 'pitch_mix.5.home_starter.overall']`: Tyler Phillips features a Sinker 25.5% of the time and a Sweeper 24.2% of the time.
  - NLI (score_only) score `0.9423604607582092`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'pitch_movement.home_starter.Sinker.v_break']`: His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.name', 'findings.away_starter_strengths']`: Watch how often George Klassen uses his Four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.name', 'starters.home_starter.pitching_profile.primary_pitch']`: Watch whether Tyler Phillips relies on his Sinker against the Angels lineup.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch if the Angels swing-and-miss risk shows up against the Sweeper from Phillips.
  - NLI (score_only) score `0.9398270845413208`, problem `None`, paths `['data_confidence.lineup_status']`: Lineup status is listed as probable pitchers.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'teams.away.name', 'value': 'Los Angeles Angels'}, {'path': 'teams.home.name', 'value': 'Miami Marlins'}]`: George Klassen faces Tyler Phillips as the Angels play the Marlins.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.season_summary.era', 'value': '11.57'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'teams.away.name', 'value': 'Los Angeles Angels'}]`: George Klassen carries an 11.57 ERA (earned run average) for the Angels.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.season_summary.era', 'value': '3.53'}, {'path': 'teams.home.name', 'value': 'Miami Marlins'}]`: Tyler Phillips has a 3.53 ERA for the Marlins.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.arsenal.scope.label', 'value': '2026 regular season through Aug 6'}]`: All statistics cover the 2026 regular season through Aug 6.
  - Sentence evidence `[{'path': 'starters.away_starter.throws', 'value': 'R'}, {'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.home_starter.throws', 'value': 'R'}, {'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}]`: This matchup features right-hander George Klassen against right-hander Tyler Phillips.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '3.64'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}]`: Klassen holds a 3.64 WHIP (walks plus hits per inning).
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.season_summary.whip_number', 'value': '1.35'}, {'path': 'starters.away_starter.season_summary.whip_number', 'value': '3.64'}]`: Phillips owns a lower WHIP of 1.35.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'starters.away_starter.season_summary.innings', 'value': '4.2'}]`: George Klassen thrown 4.2 innings this season.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '32'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: Control data for him is limited with 32 batters faced out of 170 needed.
  - Sentence evidence `[{'path': 'teams.home.name', 'value': 'Miami Marlins'}, {'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.734'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}]`: Miami has a .734 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '8.9%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}, {'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '21.0%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}]`: Their offense posts an 8.9% BB% (walk rate) and a 21.0% K% (strikeout rate).
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'Average command'}, {'path': 'starters.home_starter.pitching_profile.swing_miss_label', 'value': 'Below-average swing-and-miss ability'}]`: Tyler Phillips shows average command and below-average swing-and-miss ability.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.strikeouts', 'value': '66'}, {'path': 'glossary.K.short', 'value': 'strikeouts'}, {'path': 'starters.home_starter.season_summary.walks', 'value': '38'}, {'path': 'starters.home_starter.season_summary.innings', 'value': '89.1'}]`: He has recorded 66 K (strikeouts) and 38 walks across 89.1 innings.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Los Angeles Angels'}, {'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.687'}]`: The Angels lineup has a .687 OPS versus right-handed pitching.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': 'has elevated swing-and-miss risk'}, {'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '24.9%'}]`: That offense has elevated swing-and-miss risk with a 24.9% K%.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'pitch_mix.0.away_starter.overall', 'value': '38.6'}, {'path': 'starters.away_starter.pitching_profile.primary_pitch', 'value': 'Four-seam'}]`: George Klassen relies on his Four-seam fastball 38.6% of the time as his primary pitch.
  - Sentence evidence `[{'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}, {'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Changeup'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '24.8'}]`: His put-away pitch (second most used pitch) is the Changeup at 24.8%.
  - Sentence evidence `[{'path': 'pitch_movement.away_starter.Four-seam.h_break', 'value': '-14.8'}, {'path': 'pitch_movement.away_starter.Four-seam.v_break', 'value': '14.2'}]`: His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'pitch_mix.4.home_starter.overall', 'value': '25.5'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '24.2'}]`: Tyler Phillips features a Sinker 25.5% of the time and a Sweeper 24.2% of the time.
  - Sentence evidence `[{'path': 'pitch_movement.home_starter.Sinker.h_break', 'value': '-17.3'}, {'path': 'pitch_movement.home_starter.Sinker.v_break', 'value': '8.5'}]`: His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'George Klassen'}, {'path': 'findings.away_starter_strengths', 'value': 'Four-seam to set up, Changeup to finish'}]`: Watch how often George Klassen uses his Four-seam fastball to set up hitters.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Tyler Phillips'}, {'path': 'starters.home_starter.pitching_profile.primary_pitch', 'value': 'Sinker'}]`: Watch whether Tyler Phillips relies on his Sinker against the Angels lineup.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': 'has elevated swing-and-miss risk'}, {'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Sweeper'}]`: Watch if the Angels swing-and-miss risk shows up against the Sweeper from Phillips.
  - Sentence evidence `[{'path': 'data_confidence.lineup_status', 'value': 'probable pitchers'}]`: Lineup status is listed as probable pitchers.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.5-flash`, gate checks ['W12.time'], style findings ['S-1', 'S-2', 'W11.repeat', 'W17.length']

**Headline**

George Klassen faces Tyler Phillips in Miami

**Short summary**

- George Klassen has limited control and strikeout data.
- Tyler Phillips carries a 3.53 ERA (earned run average) for Miami.
- This report uses data from the 2026 regular season through Aug 6.

**Matchup Summary**

George Klassen starts for the Angels with a 11.57 ERA (earned run average) and a 3.64 WHIP (walks plus hits per inning). Tyler Phillips has a 3.53 ERA and a 1.35 WHIP for the Marlins. This report covers the 2026 regular season through Aug 6.

**George Klassen vs Miami Marlins**

George Klassen has limited control data with 32 batters faced when 170 are needed. His strikeout data is also limited with 32 batters faced out of 70 required. Against right-handed pitchers, the Marlins lineup has a .734 OPS (on-base plus slugging). Their K% (strikeout rate) is 21.0% and their BB% (walk rate) is 8.9%.

**Tyler Phillips vs Los Angeles Angels**

Tyler Phillips shows average command and below-average swing-and-miss ability. Against right-handed pitchers, the Angels lineup posts a .687 OPS. That lineup shows a 24.9% K% and an 8.3% BB%. Los Angeles has elevated swing-and-miss risk.

**Arsenal Scout**

George Klassen relies on a Four-seam fastball at 38.6% and a Changeup at 24.8%. His Four-seam moves 14.8 in. sideways and 14.2 in. up compared with a pitch thrown without spin. Tyler Phillips throws a Sinker 25.5% of the time and a Sweeper 24.2% of the time. His Sinker moves 17.3 in. sideways and 8.5 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often George Klassen relies on his Four-seam pitch.
- Watch whether Tyler Phillips throws his put-away pitch (second most used pitch), the Sweeper.
- Watch if the Angels manage their 24.9% K% against Tyler Phillips.

**Data Confidence Note**

Lineup status is probable pitchers. George Klassen has pitched 4.2 innings this season. Tyler Phillips has completed 89.1 innings.


## limited-825104

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `fallback_retry`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503'), ('gemini-3.1-flash-lite', 2, 'http_503'), ('gemini-3.5-flash', 1, 'http_503')], model `gemini-3.5-flash`, gate checks ['W1.entity', 'W5.label', 'W7.missing', 'W10.cause', 'W6.arsenal'], style findings ['S-2', 'S-4', 'S-5', 'S-7', 'W11.expansion'], tokens {'promptTokenCount': 7971, 'candidatesTokenCount': 2854, 'thoughtsTokenCount': 695, 'totalTokenCount': 11520}
  - gate `W1.entity` token `Phoenix` in: Bryce Elder and Michael Soroka take the mound in Phoenix
  - gate `W1.entity` token `Findings` in: Findings indicate Atlanta has strong OPS against this pitcher's hand; draws walks at an above-average rate.
  - gate `W5.label` token `swing-and-miss` in: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
  - gate `W7.missing` token `starters.away_starter.pitching_profile.command_label` in: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
  - gate `W7.missing` token `starters.home_starter.pitching_profile.command_label` in: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
  - gate `W10.cause` token `due to` in: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
  - style `W11.expansion` token `LHH / RHH` in: Watch how often Bryce Elder throws his Sinker against left-handed and right-handed hitters (shortened as LHH / RHH).
  - style `S-7` token `in this split` in: The Diamondbacks show a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate) in this split.
  - style `S-4` token `maintains` in: Watch if the Atlanta lineup maintains its .827 OPS against right-handed pitching.
  - style `S-2` token `bryce` in: Bryce Elder throws a Sinker at 34.9% overall usage with an average velocity of 91.1 mph.
  - style `S-2` token `michael` in: Michael Soroka throws a Slurve 48.3% of the time at an average speed of 80.9 mph.
  - style `S-5` token `Phoenix` in: Bryce Elder and Michael Soroka take the mound in Phoenix
  - gate `W6.arsenal` token `None` in: (whole report)
  - NLI (score_only) score `0.0008625895134173334`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Bryce Elder and Michael Soroka take the mound in Phoenix
  - NLI (score_only) score `0.9905051589012146`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'glossary.ERA.short', 'starters.away_starter.season_summary.innings', 'teams.away.name']`: Bryce Elder enters with a 0.00 ERA (earned run average) over 6.0 innings for Atlanta.
  - NLI (score_only) score `0.9949706196784973`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.whip', 'glossary.WHIP.short', 'starters.home_starter.season_summary.innings', 'teams.home.name']`: Michael Soroka brings a 1.00 WHIP (walks plus hits per inning) over 5.0 innings for Arizona.
  - NLI (score_only) score `0.0002718214818742126`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.home_starter.sample.limited.arsenal']`: Both starting pitchers enter this matchup with limited sample sizes early in the schedule.
  - NLI (score_only) score `0.9936615228652954`, problem `None`, paths `['starters.away_starter.season_summary.scopes.counts.label']`: This report covers figures from the 2026 regular season through Apr 3.
  - NLI (score_only) score `0.9932937622070312`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.innings', 'teams.away.name']`: Bryce Elder posts a 0.00 ERA and a 1.00 WHIP across 6.0 innings for the Atlanta Braves.
  - NLI (score_only) score `0.9923328161239624`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.innings', 'teams.home.name']`: Michael Soroka registers a 0.00 ERA and a 1.00 WHIP across 5.0 innings for the Arizona Diamondbacks.
  - NLI (score_only) score `0.0005465397262014449`, problem `None`, paths `['starters.away_starter.season_summary.home_runs_allowed', 'starters.home_starter.season_summary.home_runs_allowed']`: Neither starter has allowed a home run over his opening outings.
  - NLI (score_only) score `0.9731051325798035`, problem `None`, paths `['starters.away_starter.name', 'teams.home.name', 'teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short', 'teams.home.offense_profile.vs_pitcher_hand']`: Bryce Elder faces an Arizona lineup holding a .653 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.14792364835739136`, problem `None`, paths `['teams.home.name', 'teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: The Diamondbacks show a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate) in this split.
  - NLI (score_only) score `0.9880024194717407`, problem `None`, paths `['starters.away_starter.name', 'findings.away_style', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Bryce Elder uses a Sinker to set up hitters and a Slider as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.9970096349716187`, problem `None`, paths `['starters.away_starter.season_summary.strikeouts', 'glossary.K.short', 'starters.away_starter.season_summary.walks', 'starters.away_starter.sample.rates.batters_faced']`: He has recorded 5 K (strikeouts) and 1 walk while facing 23 batters.
  - NLI (score_only) score `0.9945230484008789`, problem `None`, paths `['starters.home_starter.name', 'teams.away.name', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: Michael Soroka encounters an Atlanta lineup carrying a .827 OPS against right-handed pitching.
  - NLI (score_only) score `0.9943298101425171`, problem `None`, paths `['teams.away.name', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: The Braves compile a 19.4% K% and a 9.5% BB% against right-handed throwers.
  - NLI (score_only) score `0.9931584000587463`, problem `None`, paths `['findings.lineup_notes.away']`: Findings indicate Atlanta has strong OPS against this pitcher's hand; draws walks at an above-average rate.
  - NLI (score_only) score `0.0037974391598254442`, problem `None`, paths `['starters.home_starter.name', 'findings.home_style', 'starters.home_starter.pitching_profile.putaway_pitch']`: Michael Soroka uses a Slurve to set up batters and a Four-seam fastball to finish plate appearances.
  - NLI (score_only) score `0.9906082153320312`, problem `None`, paths `['starters.home_starter.season_summary.strikeouts', 'starters.home_starter.season_summary.walks', 'starters.home_starter.sample.rates.batters_faced']`: He has logged 10 strikeouts and 1 walk across 20 batters faced.
  - NLI (score_only) score `0.7612158060073853`, problem `None`, paths `['starters.away_starter.name', 'pitch_mix.0.pitch', 'pitch_mix.0.away_starter.overall', 'velocity_by_pitch.3.away_starter_velocity']`: Bryce Elder throws a Sinker at 34.9% overall usage with an average velocity of 91.1 mph.
  - NLI (score_only) score `0.5095605254173279`, problem `None`, paths `['pitch_mix.1.pitch', 'pitch_mix.1.away_starter.overall', 'velocity_by_pitch.4.away_starter_velocity']`: His Slider accounts for 34.9% of his total pitches with a 83.1 mph average speed.
  - NLI (score_only) score `0.26304301619529724`, problem `None`, paths `['starters.home_starter.name', 'pitch_mix.5.pitch', 'pitch_mix.5.home_starter.overall', 'velocity_by_pitch.5.home_starter_velocity']`: Michael Soroka throws a Slurve 48.3% of the time at an average speed of 80.9 mph.
  - NLI (score_only) score `0.9885425567626953`, problem `None`, paths `['pitch_mix.4.pitch', 'pitch_mix.4.home_starter.overall', 'velocity_by_pitch.2.home_starter_velocity']`: His Four-seam fastball represents 33.7% of his mix at 93.8 mph.
  - NLI (score_only) score `0.01575622521340847`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.home_starter.sample.limited.arsenal', 'starters.away_starter.sample.arsenal.pitches', 'starters.home_starter.sample.arsenal.pitches', 'starters.away_starter.sample.thresholds.arsenal']`: Arsenal tracking remains limited for both starters, as Bryce Elder has 83 tracked pitches and Michael Soroka has 89 tracked pitches out of 100 needed.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.name', 'pitch_mix.0.pitch', 'glossary.LHH / RHH.short']`: Watch how often Bryce Elder throws his Sinker against left-handed and right-handed hitters (shortened as LHH / RHH).
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.name', 'pitch_mix.5.pitch', 'pitch_mix.5.home_starter.vs_rhh']`: Watch whether Michael Soroka relies on his Slurve against right-handed batters where his usage reaches 53.7%.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.name', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: Watch if the Atlanta lineup maintains its .827 OPS against right-handed pitching.
  - NLI (score_only) score `0.005275039002299309`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: Control and strikeout readings for Bryce Elder are limited, with 23 batters faced out of 170 required for control evaluation.
  - NLI (score_only) score `0.0023484190460294485`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control']`: Control and strikeout data for Michael Soroka are limited, with 20 batters faced out of 170 needed for control assessment.
  - NLI (score_only) score `0.00020123693684581667`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.command_label']`: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}]`: Bryce Elder and Michael Soroka take the mound in Phoenix
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.season_summary.era', 'value': '0.00'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'starters.away_starter.season_summary.innings', 'value': '6.0'}, {'path': 'teams.away.name', 'value': 'Atlanta Braves'}]`: Bryce Elder enters with a 0.00 ERA (earned run average) over 6.0 innings for Atlanta.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.00'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}, {'path': 'starters.home_starter.season_summary.innings', 'value': '5.0'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}]`: Michael Soroka brings a 1.00 WHIP (walks plus hits per inning) over 5.0 innings for Arizona.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.arsenal', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.arsenal', 'value': 'true'}]`: Both starting pitchers enter this matchup with limited sample sizes early in the schedule.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.scopes.counts.label', 'value': '2026 regular season through Apr 3'}]`: This report covers figures from the 2026 regular season through Apr 3.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.season_summary.era', 'value': '0.00'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.00'}, {'path': 'starters.away_starter.season_summary.innings', 'value': '6.0'}, {'path': 'teams.away.name', 'value': 'Atlanta Braves'}]`: Bryce Elder posts a 0.00 ERA and a 1.00 WHIP across 6.0 innings for the Atlanta Braves.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.season_summary.era', 'value': '0.00'}, {'path': 'starters.home_starter.season_summary.whip', 'value': '1.00'}, {'path': 'starters.home_starter.season_summary.innings', 'value': '5.0'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}]`: Michael Soroka registers a 0.00 ERA and a 1.00 WHIP across 5.0 innings for the Arizona Diamondbacks.
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.home_runs_allowed', 'value': '0'}, {'path': 'starters.home_starter.season_summary.home_runs_allowed', 'value': '0'}]`: Neither starter has allowed a home run over his opening outings.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}, {'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.653'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}, {'path': 'teams.home.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Bryce Elder faces an Arizona lineup holding a .653 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}, {'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '22.8%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '8.7%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: The Diamondbacks show a 22.8% K% (strikeout rate) and an 8.7% BB% (walk rate) in this split.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'findings.away_style', 'value': 'Sinker to set up, Slider to finish'}, {'path': 'starters.away_starter.pitching_profile.putaway_pitch', 'value': 'Slider'}, {'path': 'glossary.put-away pitch.short', 'value': 'second most used pitch'}]`: Bryce Elder uses a Sinker to set up hitters and a Slider as his put-away pitch (second most used pitch).
  - Sentence evidence `[{'path': 'starters.away_starter.season_summary.strikeouts', 'value': '5'}, {'path': 'glossary.K.short', 'value': 'strikeouts'}, {'path': 'starters.away_starter.season_summary.walks', 'value': '1'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '23'}]`: He has recorded 5 K (strikeouts) and 1 walk while facing 23 batters.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.827'}, {'path': 'teams.away.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Michael Soroka encounters an Atlanta lineup carrying a .827 OPS against right-handed pitching.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '19.4%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '9.5%'}]`: The Braves compile a 19.4% K% and a 9.5% BB% against right-handed throwers.
  - Sentence evidence `[{'path': 'findings.lineup_notes.away', 'value': "has strong OPS against this pitcher's hand; draws walks at an above-average rate"}]`: Findings indicate Atlanta has strong OPS against this pitcher's hand; draws walks at an above-average rate.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'findings.home_style', 'value': 'Slurve to set up, Four-seam to finish'}, {'path': 'starters.home_starter.pitching_profile.putaway_pitch', 'value': 'Four-seam'}]`: Michael Soroka uses a Slurve to set up batters and a Four-seam fastball to finish plate appearances.
  - Sentence evidence `[{'path': 'starters.home_starter.season_summary.strikeouts', 'value': '10'}, {'path': 'starters.home_starter.season_summary.walks', 'value': '1'}, {'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '20'}]`: He has logged 10 strikeouts and 1 walk across 20 batters faced.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'pitch_mix.0.pitch', 'value': 'Sinker'}, {'path': 'pitch_mix.0.away_starter.overall', 'value': '34.9'}, {'path': 'velocity_by_pitch.3.away_starter_velocity', 'value': '91.1'}]`: Bryce Elder throws a Sinker at 34.9% overall usage with an average velocity of 91.1 mph.
  - Sentence evidence `[{'path': 'pitch_mix.1.pitch', 'value': 'Slider'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '34.9'}, {'path': 'velocity_by_pitch.4.away_starter_velocity', 'value': '83.1'}]`: His Slider accounts for 34.9% of his total pitches with a 83.1 mph average speed.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'pitch_mix.5.pitch', 'value': 'Slurve'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '48.3'}, {'path': 'velocity_by_pitch.5.home_starter_velocity', 'value': '80.9'}]`: Michael Soroka throws a Slurve 48.3% of the time at an average speed of 80.9 mph.
  - Sentence evidence `[{'path': 'pitch_mix.4.pitch', 'value': 'Four-seam'}, {'path': 'pitch_mix.4.home_starter.overall', 'value': '33.7'}, {'path': 'velocity_by_pitch.2.home_starter_velocity', 'value': '93.8'}]`: His Four-seam fastball represents 33.7% of his mix at 93.8 mph.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.arsenal', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.arsenal', 'value': 'true'}, {'path': 'starters.away_starter.sample.arsenal.pitches', 'value': '83'}, {'path': 'starters.home_starter.sample.arsenal.pitches', 'value': '89'}, {'path': 'starters.away_starter.sample.thresholds.arsenal', 'value': '100'}]`: Arsenal tracking remains limited for both starters, as Bryce Elder has 83 tracked pitches and Michael Soroka has 89 tracked pitches out of 100 needed.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'pitch_mix.0.pitch', 'value': 'Sinker'}, {'path': 'glossary.LHH / RHH.short', 'value': 'left-handed and right-handed hitters'}]`: Watch how often Bryce Elder throws his Sinker against left-handed and right-handed hitters (shortened as LHH / RHH).
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'pitch_mix.5.pitch', 'value': 'Slurve'}, {'path': 'pitch_mix.5.home_starter.vs_rhh', 'value': '53.7'}]`: Watch whether Michael Soroka relies on his Slurve against right-handed batters where his usage reaches 53.7%.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.827'}, {'path': 'teams.away.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Watch if the Atlanta lineup maintains its .827 OPS against right-handed pitching.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '23'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: Control and strikeout readings for Bryce Elder are limited, with 23 batters faced out of 170 required for control evaluation.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '20'}, {'path': 'starters.home_starter.sample.thresholds.control', 'value': '170'}]`: Control and strikeout data for Michael Soroka are limited, with 20 batters faced out of 170 needed for control assessment.
  - Sentence evidence `[{'path': 'starters.away_starter.pitching_profile.command_label', 'value': 'null'}, {'path': 'starters.home_starter.pitching_profile.command_label', 'value': 'null'}]`: Both starters lack official ratings for command and swing-and-miss ability due to small early-season samples.
- Content attempt 2: transport path `fallback`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503'), ('gemini-3.1-flash-lite', 2, 'http_503')], model `gemini-3.5-flash`, gate checks ['W1.entity', 'W6.arsenal'], style findings ['S-1', 'W14.team', 'W17.length'], tokens {'promptTokenCount': 8215, 'candidatesTokenCount': 2001, 'totalTokenCount': 10216}
  - gate `W1.entity` token `Probable` in: Probable pitchers are listed for this matchup.
  - style `S-1` token `2026 regular season through Apr 3` in: Bryce Elder has a 0.00 ERA and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3.
  - gate `W6.arsenal` token `None` in: (whole report)
  - style `W14.team` token `None` in: (whole report)
  - style `W17.length` token `1485` in: (whole report)
  - NLI (score_only) score `0.02002560719847679`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'teams.away.name', 'teams.home.name']`: Bryce Elder and Michael Soroka meet as Atlanta faces Arizona
  - NLI (score_only) score `0.9956751465797424`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'glossary.ERA.short', 'teams.away.name', 'starters.away_starter.season_summary.scopes.season_rates.label']`: Bryce Elder carries a 0.00 ERA (earned run average) for Atlanta over the 2026 regular season through Apr 3.
  - NLI (score_only) score `0.9973464012145996`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.era', 'teams.home.name']`: Michael Soroka holds a 0.00 ERA for Arizona.
  - NLI (score_only) score `0.9441870450973511`, problem `None`, paths `['teams.away.name', 'teams.away.offense_profile.ops_vs_hand', 'glossary.OPS.short', 'teams.away.offense_profile.vs_pitcher_hand']`: Atlanta has a .827 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9910542368888855`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.whip', 'glossary.WHIP.short', 'starters.away_starter.season_summary.scopes.season_rates.label']`: Bryce Elder has a 0.00 ERA and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3.
  - NLI (score_only) score `0.40973496437072754`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.season_summary.era_number', 'starters.home_starter.season_summary.whip_number', 'starters.away_starter.season_summary.era_number', 'starters.away_starter.season_summary.whip_number', 'teams.home.name']`: Michael Soroka matches that 0.00 ERA and 1.00 WHIP for Arizona.
  - NLI (score_only) score `0.9913526177406311`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control']`: Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a read.
  - NLI (score_only) score `0.9818319082260132`, problem `None`, paths `['teams.home.name', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.vs_pitcher_hand']`: Arizona has a .653 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9480553269386292`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: Their K% (strikeout rate) is 22.8% and their BB% (walk rate) is 8.7%.
  - NLI (score_only) score `0.9929342269897461`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control']`: Control data for Michael Soroka is limited: 20 batters faced, and 170 are needed for a read.
  - NLI (score_only) score `0.9777588844299316`, problem `None`, paths `['teams.away.name', 'findings.lineup_notes.away']`: Atlanta draws walks at an above-average rate and has strong OPS against this pitcher's hand.
  - NLI (score_only) score `0.9418048858642578`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.bb_rate_vs_hand']`: Their strikeout rate is 19.4% and their walk rate is 9.5%.
  - NLI (score_only) score `0.032442521303892136`, problem `None`, paths `['starters.away_starter.name', 'pitch_mix.0.away_starter.overall', 'pitch_mix.0.pitch', 'pitch_mix.1.away_starter.overall', 'pitch_mix.1.pitch']`: Bryce Elder relies on a Sinker 34.9% of the time and a Slider 34.9% of the time.
  - NLI (score_only) score `0.9735533595085144`, problem `None`, paths `['starters.home_starter.name', 'pitch_mix.5.home_starter.overall', 'pitch_mix.5.pitch', 'pitch_mix.4.home_starter.overall', 'pitch_mix.4.pitch']`: Michael Soroka throws a Slurve 48.3% of the time and a Four-seam 33.7% of the time.
  - NLI (score_only) score `0.000547179311979562`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.home_starter.sample.limited.arsenal']`: Both pitchers have limited sample sizes for their full pitch shapes.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.name', 'pitch_mix.0.pitch', 'pitch_mix.0.away_starter.vs_rhh']`: Watch how often Bryce Elder relies on his Sinker against right-handed hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.name', 'starters.home_starter.pitching_profile.primary_pitch']`: Watch whether Michael Soroka relies on his Slurve as his primary pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.name', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: Watch if Atlanta keeps its .827 OPS against right-handed starters.
  - NLI (score_only) score `0.0007771880482323468`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.limited.strikeout', 'starters.home_starter.sample.limited.control', 'starters.home_starter.sample.limited.strikeout']`: Both starters have limited sample sizes in control and strikeout measures.
  - NLI (score_only) score `0.11176794022321701`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are listed for this matchup.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}]`: Bryce Elder and Michael Soroka meet as Atlanta faces Arizona
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.season_summary.era', 'value': '0.00'}, {'path': 'glossary.ERA.short', 'value': 'earned run average'}, {'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Apr 3'}]`: Bryce Elder carries a 0.00 ERA (earned run average) for Atlanta over the 2026 regular season through Apr 3.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.season_summary.era', 'value': '0.00'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}]`: Michael Soroka holds a 0.00 ERA for Arizona.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.827'}, {'path': 'glossary.OPS.short', 'value': 'on-base plus slugging'}, {'path': 'teams.away.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Atlanta has a .827 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.season_summary.era', 'value': '0.00'}, {'path': 'starters.away_starter.season_summary.whip', 'value': '1.00'}, {'path': 'glossary.WHIP.short', 'value': 'walks plus hits per inning'}, {'path': 'starters.away_starter.season_summary.scopes.season_rates.label', 'value': '2026 regular season through Apr 3'}]`: Bryce Elder has a 0.00 ERA and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.season_summary.era_number', 'value': '0.0'}, {'path': 'starters.home_starter.season_summary.whip_number', 'value': '1.0'}, {'path': 'starters.away_starter.season_summary.era_number', 'value': '0.0'}, {'path': 'starters.away_starter.season_summary.whip_number', 'value': '1.0'}, {'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}]`: Michael Soroka matches that 0.00 ERA and 1.00 WHIP for Arizona.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.rates.batters_faced', 'value': '23'}, {'path': 'starters.away_starter.sample.thresholds.control', 'value': '170'}]`: Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'teams.home.name', 'value': 'Arizona Diamondbacks'}, {'path': 'teams.home.offense_profile.ops_vs_hand', 'value': '.653'}, {'path': 'teams.home.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Arizona has a .653 OPS against right-handed pitchers.
  - Sentence evidence `[{'path': 'teams.home.offense_profile.k_rate_vs_hand', 'value': '22.8%'}, {'path': 'glossary.K%.short', 'value': 'strikeout rate'}, {'path': 'teams.home.offense_profile.bb_rate_vs_hand', 'value': '8.7%'}, {'path': 'glossary.BB%.short', 'value': 'walk rate'}]`: Their K% (strikeout rate) is 22.8% and their BB% (walk rate) is 8.7%.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.rates.batters_faced', 'value': '20'}, {'path': 'starters.home_starter.sample.thresholds.control', 'value': '170'}]`: Control data for Michael Soroka is limited: 20 batters faced, and 170 are needed for a read.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'findings.lineup_notes.away', 'value': "has strong OPS against this pitcher's hand; draws walks at an above-average rate"}]`: Atlanta draws walks at an above-average rate and has strong OPS against this pitcher's hand.
  - Sentence evidence `[{'path': 'teams.away.offense_profile.k_rate_vs_hand', 'value': '19.4%'}, {'path': 'teams.away.offense_profile.bb_rate_vs_hand', 'value': '9.5%'}]`: Their strikeout rate is 19.4% and their walk rate is 9.5%.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'pitch_mix.0.away_starter.overall', 'value': '34.9'}, {'path': 'pitch_mix.0.pitch', 'value': 'Sinker'}, {'path': 'pitch_mix.1.away_starter.overall', 'value': '34.9'}, {'path': 'pitch_mix.1.pitch', 'value': 'Slider'}]`: Bryce Elder relies on a Sinker 34.9% of the time and a Slider 34.9% of the time.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'pitch_mix.5.home_starter.overall', 'value': '48.3'}, {'path': 'pitch_mix.5.pitch', 'value': 'Slurve'}, {'path': 'pitch_mix.4.home_starter.overall', 'value': '33.7'}, {'path': 'pitch_mix.4.pitch', 'value': 'Four-seam'}]`: Michael Soroka throws a Slurve 48.3% of the time and a Four-seam 33.7% of the time.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.arsenal', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.arsenal', 'value': 'true'}]`: Both pitchers have limited sample sizes for their full pitch shapes.
  - Sentence evidence `[{'path': 'starters.away_starter.name', 'value': 'Bryce Elder'}, {'path': 'pitch_mix.0.pitch', 'value': 'Sinker'}, {'path': 'pitch_mix.0.away_starter.vs_rhh', 'value': '55.6'}]`: Watch how often Bryce Elder relies on his Sinker against right-handed hitters.
  - Sentence evidence `[{'path': 'starters.home_starter.name', 'value': 'Michael Soroka'}, {'path': 'starters.home_starter.pitching_profile.primary_pitch', 'value': 'Slurve'}]`: Watch whether Michael Soroka relies on his Slurve as his primary pitch.
  - Sentence evidence `[{'path': 'teams.away.name', 'value': 'Atlanta Braves'}, {'path': 'teams.away.offense_profile.ops_vs_hand', 'value': '.827'}, {'path': 'teams.away.offense_profile.vs_pitcher_hand', 'value': 'RHP'}]`: Watch if Atlanta keeps its .827 OPS against right-handed starters.
  - Sentence evidence `[{'path': 'starters.away_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.away_starter.sample.limited.strikeout', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.control', 'value': 'true'}, {'path': 'starters.home_starter.sample.limited.strikeout', 'value': 'true'}]`: Both starters have limited sample sizes in control and strikeout measures.
  - Sentence evidence `[{'path': 'data_confidence.lineup_status', 'value': 'probable pitchers'}]`: Probable pitchers are listed for this matchup.
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

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.5-flash`, gate checks ['W1.entity', 'W6.arsenal'], style findings ['S-1', 'W14.team', 'W17.length']

**Headline**

Bryce Elder and Michael Soroka meet as Atlanta faces Arizona

**Short summary**

- Bryce Elder carries a 0.00 ERA (earned run average) for Atlanta over the 2026 regular season through Apr 3.
- Michael Soroka holds a 0.00 ERA for Arizona.
- Atlanta has a .827 OPS (on-base plus slugging) against right-handed pitchers.

**Matchup Summary**

Bryce Elder has a 0.00 ERA and a 1.00 WHIP (walks plus hits per inning) over the 2026 regular season through Apr 3. Michael Soroka matches that 0.00 ERA and 1.00 WHIP for Arizona.

**Bryce Elder vs Arizona Diamondbacks**

Control data for Bryce Elder is limited: 23 batters faced, and 170 are needed for a read. Arizona has a .653 OPS against right-handed pitchers. Their K% (strikeout rate) is 22.8% and their BB% (walk rate) is 8.7%.

**Michael Soroka vs Atlanta Braves**

Control data for Michael Soroka is limited: 20 batters faced, and 170 are needed for a read. Atlanta draws walks at an above-average rate and has strong OPS against this pitcher's hand. Their strikeout rate is 19.4% and their walk rate is 9.5%.

**Arsenal Scout**

Bryce Elder relies on a Sinker 34.9% of the time and a Slider 34.9% of the time. Michael Soroka throws a Slurve 48.3% of the time and a Four-seam 33.7% of the time. Both pitchers have limited sample sizes for their full pitch shapes.

**Three Things to Watch**

- Watch how often Bryce Elder relies on his Sinker against right-handed hitters.
- Watch whether Michael Soroka relies on his Slurve as his primary pitch.
- Watch if Atlanta keeps its .827 OPS against right-handed starters.

**Data Confidence Note**

Both starters have limited sample sizes in control and strikeout measures. Probable pitchers are listed for this matchup.


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

