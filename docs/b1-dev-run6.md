# B1 dev examples: model text beside the rules text (owner gate)

Dev split only. Guide digest(s) recorded in this run: `172e12b13e39b8b1a16438ea825ceafd80b96ea4c7f23bf970304ef98ec0b347`; prompt version(s) recorded in this run: `p2.2-6`. Nothing here is published; rules stay live.

S1 code detectors: S-1, S-2, S-4, S-5, S-7, S-8; S-3, S-6 and S-9 require judge/human assessment and are not evaluated here. NLI is score-only unless explicitly recorded as gate; no human-calibrated entailment claim.

Gemini HTTP calls: run 57 of 100, experiment 203 of 400.
Capacity failures (503/429) in this run: 3 of 57 finished calls. By model: `gemini-3.1-flash-lite` 3 of 57.
Run started 2026-11-03 19:21 local (2026-11-04 00:21 UTC), finished 2026-11-03 19:43 local.
Paths: primary 2, primary_retry 0, fallback 0, fallback_retry 0, rules 8, not_attempted 0. LLM coverage 2/10; accepted 2, rejected 8, not attempted 0; not written by the primary model 8/10 (a fallback or rules result is not a primary first-attempt success).


## postseason-849831

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary**; content attempts: 1
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-1', 'S-2', 'S-4', 'W17.length'], tokens {'promptTokenCount': 14328, 'candidatesTokenCount': 1020, 'thoughtsTokenCount': 1863, 'totalTokenCount': 17211}
  - style `S-1` token `2026 regular season` in: Gavin Williams enters the game with a 3.76 ERA and a 1.11 WHIP over the 2026 regular season through Oct 9.
  - style `S-4` token `possess` in: Both pitchers possess above-average swing-and-miss ability for their teams.
  - style `S-2` token `That lineup` in: That lineup has an elevated swing-and-miss risk, a 24.1% K% and a 9.4% BB%.
  - style `W17.length` token `1677` in: (whole report)
  - NLI (score_only) score `0.9393962025642395`, problem `None`, paths `['data_confidence.lineup_status', 'series.game_number', 'series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Sean Burke and Gavin Williams start Game 5 of the AL Division Series
  - NLI (score_only) score `0.9057661890983582`, problem `None`, paths `['series.game_number', 'series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Sean Burke and Gavin Williams face each other in Game 5 of the AL Division Series.
  - NLI (score_only) score `0.0061340355314314365`, problem `None`, paths `['series.standing']`: The series is tied 2-2 heading into this deciding matchup.
  - NLI (score_only) score `0.0014867136487737298`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Both pitchers possess above-average swing-and-miss ability for their teams.
  - NLI (score_only) score `0.995762050151825`, problem `None`, paths `['series.standing', 'series.series_name', 'series.game_number', 'venue']`: This AL Division Series is tied 2-2 heading into Game 5 at Progressive Field.
  - NLI (score_only) score `0.9899837970733643`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Sean Burke carries a 3.34 ERA (earned run average) and a 1.20 WHIP (walks plus hits per inning) over the 2026 regular season through Oct 9.
  - NLI (score_only) score `0.9851689338684082`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9902276992797852`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The Guardians lineup has a .706 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9750184416770935`, problem `None`, paths `['findings.lineup_notes.home', 'teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand', 'glossary.BB%.short', 'glossary.K%.short']`: That group draws walks at an above-average rate, with a 9.1% BB% (walk rate) and a 20.6% K% (strikeout rate).
  - NLI (score_only) score `0.007669773884117603`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Gavin Williams enters the game with a 3.76 ERA and a 1.11 WHIP over the 2026 regular season through Oct 9.
  - NLI (score_only) score `0.9861406087875366`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9884318709373474`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The White Sox offense has a .716 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9789730906486511`, problem `None`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: That lineup has an elevated swing-and-miss risk, a 24.1% K% and a 9.4% BB%.
  - NLI (score_only) score `0.9782524704933167`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Sean Burke uses a four-seam fastball as his primary pitch and a curveball as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.99228435754776`, problem `None`, paths `['velocity_by_pitch.2.away_starter_velocity', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'velocity_by_pitch.0.away_starter_velocity']`: He throws his four-seam at 94.8 mph and his curveball at 79.0 mph.
  - NLI (score_only) score `0.005900372285395861`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Gavin Williams uses a sweeper as his primary pitch and a four-seam fastball as his put-away pitch.
  - NLI (score_only) score `0.9887599945068359`, problem `None`, paths `['velocity_by_pitch.5.home_starter_velocity', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'velocity_by_pitch.2.home_starter_velocity']`: He throws his sweeper at 87.6 mph and his four-seam at 97.7 mph.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.0.away_starter.overall', 'findings.away_style']`: Watch how often Sean Burke uses his four-seam fastball to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.5.home_starter.overall', 'findings.home_style']`: Watch if Gavin Williams relies on his sweeper early in counts.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.1.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how the White Sox lineup handles the curveball from Sean Burke.
  - NLI (score_only) score `0.6263406872749329`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are confirmed for this game.
  - Sentence evidence `['F001', 'F120', 'F122', 'F124', 'F156']`: Sean Burke and Gavin Williams start Game 5 of the AL Division Series
  - Sentence evidence `['F120', 'F122', 'F124', 'F156']`: Sean Burke and Gavin Williams face each other in Game 5 of the AL Division Series.
  - Sentence evidence `['F123']`: The series is tied 2-2 heading into this deciding matchup.
  - Sentence evidence `['F130', 'F162']`: Both pitchers possess above-average swing-and-miss ability for their teams.
  - Sentence evidence `['F123', 'F122', 'F120', 'F227']`: This AL Division Series is tied 2-2 heading into Game 5 at Progressive Field.
  - Sentence evidence `['F144', 'F152', 'F013', 'F018', 'F148']`: Sean Burke carries a 3.34 ERA (earned run average) and a 1.20 WHIP (walks plus hits per inning) over the 2026 regular season through Oct 9.
  - Sentence evidence `['F125', 'F130']`: He shows average command and above-average swing-and-miss ability.
  - Sentence evidence `['F206', 'F208', 'F017']`: The Guardians lineup has a .706 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F010', 'F202', 'F204', 'F011', 'F014']`: That group draws walks at an above-average rate, with a 9.1% BB% (walk rate) and a 20.6% K% (strikeout rate).
  - Sentence evidence `['F176', 'F184', 'F180']`: Gavin Williams enters the game with a 3.76 ERA and a 1.11 WHIP over the 2026 regular season through Oct 9.
  - Sentence evidence `['F157', 'F162']`: He shows average command and above-average swing-and-miss ability.
  - Sentence evidence `['F196', 'F198']`: The White Sox offense has a .716 OPS against right-handed pitchers.
  - Sentence evidence `['F009', 'F194', 'F192']`: That lineup has an elevated swing-and-miss risk, a 24.1% K% and a 9.4% BB%.
  - Sentence evidence `['F127', 'F128', 'F022']`: Sean Burke uses a four-seam fastball as his primary pitch and a curveball as his put-away pitch (second most used pitch).
  - Sentence evidence `['F215', 'F209']`: He throws his four-seam at 94.8 mph and his curveball at 79.0 mph.
  - Sentence evidence `['F159', 'F160']`: Gavin Williams uses a sweeper as his primary pitch and a four-seam fastball as his put-away pitch.
  - Sentence evidence `['F225', 'F216']`: He throws his sweeper at 87.6 mph and his four-seam at 97.7 mph.
  - Sentence evidence `['F024', 'F025', 'F005']`: Watch how often Sean Burke uses his four-seam fastball to set up hitters.
  - Sentence evidence `['F084', 'F085', 'F008']`: Watch if Gavin Williams relies on his sweeper early in counts.
  - Sentence evidence `['F035', 'F036', 'F128']`: Watch how the White Sox lineup handles the curveball from Sean Burke.
  - Sentence evidence `['F001']`: Probable pitchers are confirmed for this game.
- Length: rules 2441 characters; shown text 1686 characters.

### Rules text (A)

**Headline**

Four-seam-Curveball starter against Sweeper-Four-seam starter

**Short summary**

- Sean Burke brings this strength: Above-average swing-and-miss ability.
- Gavin Williams brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Sean Burke can land the curveball early in counts.

**Matchup Summary**

This matchup features Four-seam-Curveball starter against Sweeper-Four-seam starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 5 of the AL Division Series. Before first pitch, series tied 2-2.

**Sean Burke vs Cleveland Guardians**

Sean Burke works off a four-seam-curveball combination. He shows above-average swing-and-miss ability (regular-season rates). He shows average command (regular-season rates). Sean Burke has allowed 19 home runs over 716 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.706 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Sean Burke needs efficient strikes.

**Gavin Williams vs Chicago White Sox**

Gavin Williams works off a sweeper-four-seam combination. He shows above-average swing-and-miss ability (regular-season rates). He shows average command (regular-season rates). Gavin Williams has allowed 28 home runs over 746 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.716 OPS), with no glaring weakness to attack. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Gavin Williams needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Curveball to finish versus Sweeper to set up, Four-seam to finish. The primary pitch contrast is Four-seam against Sweeper, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Sean Burke land the curveball early in counts?
- Can Gavin Williams keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Sean Burke and Gavin Williams: ERA, WHIP, innings and the strikeout, walk and home-run counts cover the 2026 regular season; the pitch mix, velocity and movement cover the 2026 regular season and postseason through Oct 9. They are different samples. Team offense splits cover the 2026 regular season.

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `S-1` `2026 regular season`, `S-4` `possess`, `S-2` `That lineup`, `W17.length` `1677`

**Headline**

Sean Burke and Gavin Williams start Game 5 of the AL Division Series

**Short summary**

- Sean Burke and Gavin Williams face each other in Game 5 of the AL Division Series.
- The series is tied 2-2 heading into this deciding matchup.
- Both pitchers possess above-average swing-and-miss ability for their teams.

**Matchup Summary**

This AL Division Series is tied 2-2 heading into Game 5 at Progressive Field.

**Sean Burke vs Cleveland Guardians**

Sean Burke carries a 3.34 ERA (earned run average) and a 1.20 WHIP (walks plus hits per inning) over the 2026 regular season through Oct 9. He shows average command and above-average swing-and-miss ability. The Guardians lineup has a .706 OPS (on-base plus slugging) against right-handed pitchers. That group draws walks at an above-average rate, with a 9.1% BB% (walk rate) and a 20.6% K% (strikeout rate).

**Gavin Williams vs Chicago White Sox**

Gavin Williams enters the game with a 3.76 ERA and a 1.11 WHIP over the 2026 regular season through Oct 9. He shows average command and above-average swing-and-miss ability. The White Sox offense has a .716 OPS against right-handed pitchers. That lineup has an elevated swing-and-miss risk, a 24.1% K% and a 9.4% BB%.

**Arsenal Scout**

Sean Burke uses a four-seam fastball as his primary pitch and a curveball as his put-away pitch (second most used pitch). He throws his four-seam at 94.8 mph and his curveball at 79.0 mph. Gavin Williams uses a sweeper as his primary pitch and a four-seam fastball as his put-away pitch. He throws his sweeper at 87.6 mph and his four-seam at 97.7 mph.

**Three Things to Watch**

- Watch how often Sean Burke uses his four-seam fastball to set up hitters.
- Watch if Gavin Williams relies on his sweeper early in counts.
- Watch how the White Sox lineup handles the curveball from Sean Burke.

**Data Confidence Note**

Probable pitchers are confirmed for this game.


## postseason-849827

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W6.arsenal'], style findings ['S-2', 'W11.expansion', 'W17.length'], tokens {'promptTokenCount': 12353, 'candidatesTokenCount': 1626, 'thoughtsTokenCount': 2567, 'totalTokenCount': 16546}
  - style `W11.expansion` token `put-away pitch` in: Robert Gasser has a limited arsenal and the findings note no primary or put-away pitch.
  - style `S-2` token `That team` in: That team has a 22.3% K% and a 10.8% BB%.
  - gate `W6.arsenal` token `None` in: (whole report)
  - style `W17.length` token `1830` in: (whole report)
  - NLI (score_only) score `0.030068712309002876`, problem `None`, paths `['series.game_number', 'series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Walker Buehler and Robert Gasser take the mound in Game 4 of the NL Division Series.
  - NLI (score_only) score `0.9887208342552185`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 4 of the NL Division Series.
  - NLI (score_only) score `0.9913642406463623`, problem `None`, paths `['series.standing']`: Before first pitch, MIL leads 2-1.
  - NLI (score_only) score `0.01631653681397438`, problem `None`, paths `['starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: All statistics cover the 2026 regular season through Oct 6.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'starters.home_starter.name', 'starters.home_starter.team']`: Robert Gasser pitches for the Milwaukee Brewers and Walker Buehler starts for the San Diego Padres.
  - NLI (score_only) score `0.991117000579834`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Robert Gasser has a 3.87 ERA (earned run average) and a 1.19 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.973455548286438`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9399105906486511`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through', 'starters.away_starter.sample.thresholds.arsenal']`: His arsenal data is limited with 463 batters faced and 100 needed for a full profile.
  - NLI (score_only) score `0.9920235872268677`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The San Diego Padres lineup has a .705 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9768498539924622`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number', 'glossary.K%.short', 'glossary.BB%.short']`: This group records a 21.7% K% (strikeout rate) and an 8.2% BB% (walk rate).
  - NLI (score_only) score `0.001245590508915484`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Walker Buehler carries a 4.63 ERA and a 1.35 WHIP.
  - NLI (score_only) score `0.9746535420417786`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9844553470611572`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: The Milwaukee Brewers lineup has a .759 OPS against right-handed pitchers.
  - NLI (score_only) score `0.971950352191925`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: That team has a 22.3% K% and a 10.8% BB%.
  - NLI (score_only) score `0.026571298018097878`, problem `None`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Milwaukee Brewers lineup has a strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - NLI (score_only) score `0.9935480952262878`, problem `None`, paths `['starters.home_starter.pitching_profile.style_label']`: Walker Buehler is a cutter-four-seam starter.
  - NLI (score_only) score `0.9937945604324341`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Cutter.h_break', 'pitch_movement.home_starter.Cutter.v_break']`: He uses his cutter 24.4% of the time, moving 4.9 in. sideways and 10.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9939790964126587`, problem `None`, paths `['pitch_mix.1.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Four-seam.h_break', 'pitch_movement.home_starter.Four-seam.v_break']`: He throws his four-seam pitch 20.2% of the time, moving 4.7 in. sideways and 16.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9706565737724304`, problem `None`, paths `['pitch_mix.2.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.3.home_starter.overall', 'pitch_mix.4.home_starter.overall']`: His sinker usage is 19.9%, while he uses his slider 10.6% and his changeup 9.5% of the time.
  - NLI (score_only) score `0.0012442098231986165`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'starters.away_starter.sample.limited.arsenal']`: Robert Gasser has a limited arsenal and the findings note no primary or put-away pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_strengths', 'pitch_mix.0.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.home_starter.pitching_profile.primary_pitch']`: Watch how often Walker Buehler uses his cutter to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'starters.away_starter.name']`: Watch if the San Diego Padres lineup improves its 21.7% K% against Robert Gasser.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.bb_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch whether Milwaukee Brewers batters capitalize on their above-average walk rate.
  - NLI (score_only) score `0.9305961728096008`, problem `None`, paths `['data_confidence.lineup_status']`: Pitcher availability for this game is listed as probable.
  - Sentence evidence `['F094', 'F096', 'F098', 'F130']`: Walker Buehler and Robert Gasser take the mound in Game 4 of the NL Division Series.
  - Sentence evidence `['F094', 'F096']`: This is Game 4 of the NL Division Series.
  - Sentence evidence `['F097']`: Before first pitch, MIL leads 2-1.
  - Sentence evidence `['F112', 'F138', 'F144', 'F154', 'F171']`: All statistics cover the 2026 regular season through Oct 6.
  - Sentence evidence `['F098', 'F128', 'F130', 'F160']`: Robert Gasser pitches for the Milwaukee Brewers and Walker Buehler starts for the San Diego Padres.
  - Sentence evidence `['F118', 'F126', 'F013', 'F018']`: Robert Gasser has a 3.87 ERA (earned run average) and a 1.19 WHIP (walks plus hits per inning).
  - Sentence evidence `['F099', 'F104']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F107', 'F110', 'F115']`: His arsenal data is limited with 463 batters faced and 100 needed for a full profile.
  - Sentence evidence `['F179', 'F180', 'F182', 'F017']`: The San Diego Padres lineup has a .705 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F177', 'F175', 'F014', 'F011']`: This group records a 21.7% K% (strikeout rate) and an 8.2% BB% (walk rate).
  - Sentence evidence `['F150', 'F158']`: Walker Buehler carries a 4.63 ERA and a 1.35 WHIP.
  - Sentence evidence `['F131', 'F136']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F169', 'F170', 'F172']`: The Milwaukee Brewers lineup has a .759 OPS against right-handed pitchers.
  - Sentence evidence `['F167', 'F165']`: That team has a 22.3% K% and a 10.8% BB%.
  - Sentence evidence `['F009', 'F172']`: The Milwaukee Brewers lineup has a strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - Sentence evidence `['F135']`: Walker Buehler is a cutter-four-seam starter.
  - Sentence evidence `['F030', 'F083', 'F084']`: He uses his cutter 24.4% of the time, moving 4.9 in. sideways and 10.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F041', 'F086', 'F087']`: He throws his four-seam pitch 20.2% of the time, moving 4.7 in. sideways and 16.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F052', 'F063', 'F074']`: His sinker usage is 19.9%, while he uses his slider 10.6% and his changeup 9.5% of the time.
  - Sentence evidence `['F101', 'F102', 'F107']`: Robert Gasser has a limited arsenal and the findings note no primary or put-away pitch.
  - Sentence evidence `['F007', 'F029', 'F133']`: Watch how often Walker Buehler uses his cutter to set up hitters.
  - Sentence evidence `['F177', 'F098']`: Watch if the San Diego Padres lineup improves its 21.7% K% against Robert Gasser.
  - Sentence evidence `['F009', 'F165']`: Watch whether Milwaukee Brewers batters capitalize on their above-average walk rate.
  - Sentence evidence `['F001']`: Pitcher availability for this game is listed as probable.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 12467, 'candidatesTokenCount': 1272, 'thoughtsTokenCount': 856, 'totalTokenCount': 14595}
  - gate `W17.structure` token `None` in: (whole report)
- Length: rules 2317 characters; shown text 2317 characters.

### Rules text (A)

**Headline**

Robert Gasser against Walker Buehler

**Short summary**

- Robert Gasser has no claimed strength because the data is limited.
- Walker Buehler brings this strength: Cutter to set up, Four-seam to finish.
- The early what to watch is whether Robert Gasser can stay ahead of hitters early in counts.

**Matchup Summary**

This matchup features Robert Gasser against Walker Buehler. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 4 of the NL Division Series. Before first pitch, MIL leads 2-1.

**Robert Gasser vs San Diego Padres**

Robert Gasser shows average swing-and-miss ability. He shows average command. Robert Gasser's arsenal data is limited (pitch count not available; 100 needed), so this report makes no arsenal claim for him. Robert Gasser has allowed 15 home runs over 463 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against LHP pitching (.705 OPS), with no glaring weakness to attack.

**Walker Buehler vs Milwaukee Brewers**

Walker Buehler works off a cutter-four-seam combination. He shows average swing-and-miss ability. He shows average command. Walker Buehler has allowed 22 home runs over 651 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.759 OPS), so Walker Buehler cannot live over the middle. They draw walks at an above-average rate, so Walker Buehler needs efficient strikes.

**Arsenal Scout**

Robert Gasser's arsenal data is limited (pitch count not available; 100 needed), so this report makes no arsenal claim for him. Walker Buehler works off Cutter to set up, Four-seam to finish. No arsenal contrast is drawn because at least one arsenal has too little data.

**Three Things to Watch**

- Can Robert Gasser stay ahead of hitters early in counts?
- Can Walker Buehler keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers and season offense splits. Statcast pitch data was available for Walker Buehler but not for Robert Gasser, so the pitch read makes no arsenal claims about Robert Gasser. Lineups can still change before first pitch. Robert Gasser and Walker Buehler: all pitcher figures cover the 2026 regular season. Team offense splits cover the 2026 regular season. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Robert Gasser and Walker Buehler pitch in Game 4 of the NL Division Series

**Short summary**

- The Milwaukee Brewers hold a 2-1 lead in the NL Division Series.
- This contest is Game 4 of the 5-game set.
- Robert Gasser and Walker Buehler are the probable starters for this matchup.

**Matchup Summary**

All performance data for these starters and lineups covers the 2026 regular season through 2026-10-06.

**Robert Gasser vs San Diego Padres**

Robert Gasser brings a 3.87 ERA (earned run average) and a 1.19 WHIP (walks plus hits per inning) into the start. He shows average command and average swing-and-miss ability. The San Diego Padres lineup faces him with a .705 OPS (on-base plus slugging) against left-handed pitchers. That group records a 21.7% K% (strikeout rate) and an 8.2% BB% (walk rate) in these splits.

**Walker Buehler vs Milwaukee Brewers**

Walker Buehler enters with a 4.63 ERA and a 1.35 WHIP. He shows average command and average swing-and-miss ability. The Milwaukee Brewers lineup prepares to face right-handed pitching with a .759 OPS. Their offense posts a 22.3% K% and a 10.8% BB% against that handedness. Lineup notes indicate the Milwaukee Brewers have a strong OPS against this pitcher's hand and draw walks at an above-average rate.

**Arsenal Scout**

Arsenal data for Robert Gasser is limited with 463 batters faced, and 100 pitches are required for a report. Walker Buehler relies on a mix led by a cutter at 24.4%, a four-seam at 20.2%, and a sinker at 19.9%. He also includes a slider at 10.6% and a changeup at 9.5% in his primary rotation. His cutter moves 4.9 in. sideways and 10.0 in. up compared with a pitch thrown without spin. The four-seam moves 4.7 in. sideways and 16.0 in. up, while his sinker moves 13.9 in. sideways and 12.7 in. up compared with a pitch thrown without spin. His slider moves 8.2 in. sideways and 2.8 in. up, and the changeup moves 12.4 in. sideways and 3.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch whether Robert Gasser can maintain his average command through the early innings.
- Watch how often Walker Buehler uses his cutter to set up and his four-seam to finish against the Milwaukee Brewers.
- Watch if the Milwaukee Brewers hitters maintain their above-average walk rate against the San Diego Padres bullpen and starter.

**Data Confidence Note**

Data confidence is based on probable pitchers as provided by the game status.


## postseason-849803

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 14682, 'candidatesTokenCount': 1669, 'thoughtsTokenCount': 2949, 'totalTokenCount': 19300}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W8.form'], style findings ['S-2', 'S-4', 'W11.expansion', 'W17.length'], tokens {'promptTokenCount': 14711, 'candidatesTokenCount': 894, 'thoughtsTokenCount': 1258, 'totalTokenCount': 16863}
  - gate `W1.number` token `4` in: Dustin May faces Griffin Jax in Game 4 of the World Series
  - gate `W8.form` token `None` in: Dustin May moves his cutter 1.3 in. sideways and 9.1 in. up compared with a pitch thrown without spin.
  - gate `W8.form` token `None` in: Griffin Jax moves his sweeper 13.0 in. sideways and 1.2 in. down compared with a pitch thrown without spin.
  - style `W11.expansion` token `put-away pitch` in: He uses a four-seam as his put-away pitch.
  - style `S-4` token `maintains` in: Watch if the Milwaukee Brewers lineup maintains its walk rate.
  - style `S-4` token `features` in: This matchup features probable pitchers as listed in the team information.
  - style `S-2` token `That group` in: That group has a 22.3% K% and a 10.8% BB%, and the lineup notes state it has strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - style `W17.length` token `1575` in: (whole report)
  - NLI (score_only) score `0.00014365921379067004`, problem `None`, paths `['series.series_name', 'starters.away_starter.name', 'starters.home_starter.name']`: Dustin May faces Griffin Jax in Game 4 of the World Series
  - NLI (score_only) score `0.9890232086181641`, problem `None`, paths `['series.game_number', 'series.series_name']`: This is Game 4 of the World Series.
  - NLI (score_only) score `0.9914423823356628`, problem `None`, paths `['series.standing']`: Before first pitch, MIL leads 3-0.
  - NLI (score_only) score `0.9960359930992126`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Data for this report is from the 2026 regular season and postseason through 2026-10-26.
  - NLI (score_only) score `0.9863399267196655`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name']`: Dustin May and Griffin Jax are the probable pitchers for their respective teams.
  - NLI (score_only) score `0.9962272644042969`, problem `None`, paths `['glossary.ERA.short', 'glossary.WHIP.short', 'starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip']`: Dustin May carries a 4.70 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9686087369918823`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9783424139022827`, problem `None`, paths `['glossary.OPS.short', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand']`: The Tampa Bay Rays lineup has a .751 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.930018424987793`, problem `None`, paths `['glossary.BB%.short', 'glossary.K%.short', 'glossary.OPS.short', 'findings.lineup_notes.home', 'teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand']`: This group has a 19.1% K% (strikeout rate) and an 8.7% BB% (walk rate), and the lineup notes state it has strong OPS against this pitcher's hand.
  - NLI (score_only) score `0.012386317364871502`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Griffin Jax enters with a 3.53 ERA and a 1.18 WHIP.
  - NLI (score_only) score `0.9823703765869141`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9840272665023804`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The Milwaukee Brewers lineup has a .759 OPS against right-handed pitchers.
  - NLI (score_only) score `0.973415195941925`, problem `None`, paths `['findings.lineup_notes.away', 'teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.k_rate_vs_hand']`: That group has a 22.3% K% and a 10.8% BB%, and the lineup notes state it has strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - NLI (score_only) score `0.992868959903717`, problem `None`, paths `['pitch_movement.away_starter.Cutter.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Cutter.v_break']`: Dustin May moves his cutter 1.3 in. sideways and 9.1 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9933695793151855`, problem `None`, paths `['glossary.put-away pitch.short', 'starters.away_starter.pitching_profile.putaway_pitch']`: He uses a four-seam as his put-away pitch.
  - NLI (score_only) score `0.9888238310813904`, problem `None`, paths `['pitch_movement.home_starter.Sweeper.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sweeper.v_break']`: Griffin Jax moves his sweeper 13.0 in. sideways and 1.2 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `0.004185490310192108`, problem `None`, paths `['starters.home_starter.pitching_profile.putaway_pitch']`: He uses a sinker as his put-away pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Dustin May throws his cutter.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.3.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch whether Griffin Jax relies on his sweeper to finish hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.away.offense_profile.bb_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: Watch if the Milwaukee Brewers lineup maintains its walk rate.
  - NLI (score_only) score `0.7893548607826233`, problem `None`, paths `['data_confidence.lineup_status']`: This matchup features probable pitchers as listed in the team information.
  - Sentence evidence `['F128', 'F130', 'F162']`: Dustin May faces Griffin Jax in Game 4 of the World Series
  - Sentence evidence `['F126', 'F128']`: This is Game 4 of the World Series.
  - Sentence evidence `['F129']`: Before first pitch, MIL leads 3-0.
  - Sentence evidence `['F138']`: Data for this report is from the 2026 regular season and postseason through 2026-10-26.
  - Sentence evidence `['F001', 'F130', 'F162']`: Dustin May and Griffin Jax are the probable pitchers for their respective teams.
  - Sentence evidence `['F013', 'F018', 'F150', 'F158']`: Dustin May carries a 4.70 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning).
  - Sentence evidence `['F131', 'F136']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F017', 'F212', 'F214']`: The Tampa Bay Rays lineup has a .751 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F011', 'F014', 'F017', 'F010', 'F208', 'F210']`: This group has a 19.1% K% (strikeout rate) and an 8.7% BB% (walk rate), and the lineup notes state it has strong OPS against this pitcher's hand.
  - Sentence evidence `['F182', 'F190']`: Griffin Jax enters with a 3.53 ERA and a 1.18 WHIP.
  - Sentence evidence `['F163', 'F168']`: He shows average command and above-average swing-and-miss ability.
  - Sentence evidence `['F202', 'F204']`: The Milwaukee Brewers lineup has a .759 OPS against right-handed pitchers.
  - Sentence evidence `['F009', 'F198', 'F200']`: That group has a 22.3% K% and a 10.8% BB%, and the lineup notes state it has strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - Sentence evidence `['F097', 'F098']`: Dustin May moves his cutter 1.3 in. sideways and 9.1 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F022', 'F134']`: He uses a four-seam as his put-away pitch.
  - Sentence evidence `['F124', 'F125']`: Griffin Jax moves his sweeper 13.0 in. sideways and 1.2 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F166']`: He uses a sinker as his put-away pitch.
  - Sentence evidence `['F024']`: Watch how often Dustin May throws his cutter.
  - Sentence evidence `['F062']`: Watch whether Griffin Jax relies on his sweeper to finish hitters.
  - Sentence evidence `['F198']`: Watch if the Milwaukee Brewers lineup maintains its walk rate.
  - Sentence evidence `['F001']`: This matchup features probable pitchers as listed in the team information.
- Length: rules 2232 characters; shown text 2232 characters.

### Rules text (A)

**Headline**

Cutter-Four-seam starter against Sweeper-Sinker starter

**Short summary**

- Dustin May brings this strength: Cutter to set up, Four-seam to finish.
- Griffin Jax brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Dustin May can land the four-seam early in counts.

**Matchup Summary**

This matchup features Cutter-Four-seam starter against Sweeper-Sinker starter. The scouting note is matchup fit, with each pressure point shaping what to watch. This is Game 4 of the World Series. Before first pitch, MIL leads 3-0.

**Dustin May vs Tampa Bay Rays**

Dustin May works off a cutter-four-seam combination. He shows average swing-and-miss ability (regular-season rates). He shows average command (regular-season rates). Dustin May has allowed 14 home runs over 621 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.751 OPS), so Dustin May cannot live over the middle.

**Griffin Jax vs Milwaukee Brewers**

Griffin Jax works off a sweeper-sinker combination. He shows above-average swing-and-miss ability (regular-season rates). He shows average command (regular-season rates). Griffin Jax has allowed 15 home runs over 459 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.759 OPS), so Griffin Jax cannot live over the middle. They draw walks at an above-average rate, so Griffin Jax needs efficient strikes.

**Arsenal Scout**

The main contrast is Cutter to set up, Four-seam to finish versus Sweeper to set up, Sinker to finish. The primary pitch contrast is Cutter against Sweeper, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Dustin May land the four-seam early in counts?
- Can Griffin Jax keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Dustin May and Griffin Jax: ERA, WHIP, innings and the strikeout, walk and home-run counts cover the 2026 regular season; the pitch mix, velocity and movement cover the 2026 regular season and postseason through Oct 26. They are different samples. Team offense splits cover the 2026 regular season.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

World Series Game 4 features Dustin May and Griffin Jax

**Short summary**

- This is Game 4 of the World Series.
- Before first pitch, MIL leads 3-0.
- Dustin May and Griffin Jax are the probable pitchers.

**Matchup Summary**

The statistics in this report cover the 2026 regular season through Oct 26, with pitching figures and pitch mix including the postseason through that same date.

**Dustin May vs Tampa Bay Rays**

Dustin May is a cutter-four-seam starter for Milwaukee. He shows average command and average swing-and-miss ability. His primary pitch is the cutter and his put-away pitch (second most used pitch) is the four-seam fastball. The Tampa Bay Rays lineup has a .751 OPS (on-base plus slugging) against right-handed pitchers. The team carries a 19.1% K% (strikeout rate) and an 8.7% BB% (walk rate) in this split.

**Griffin Jax vs Milwaukee Brewers**

Griffin Jax is a sweeper-sinker starter for Tampa Bay. He shows average command and above-average swing-and-miss ability. His primary pitch is the sweeper and his put-away pitch is the sinker. The Milwaukee Brewers lineup has a .759 OPS against right-handed pitchers. That group carries a 22.3% K% and a 10.8% BB% in this split.

**Arsenal Scout**

Dustin May throws his cutter 24.3% of the time and his four-seam fastball 24.2% of the time. The cutter moves 1.3 in. sideways and 9.1 in. up compared with a pitch thrown without spin. The four-seam fastball moves 9.7 in. sideways and 15.2 in. up compared with a pitch thrown without spin. Griffin Jax throws his sweeper 24.5% of the time and his sinker 23.0% of the time. The sweeper moves 13.0 in. sideways and 1.2 in. down compared with a pitch thrown without spin. The sinker moves 16.6 in. sideways and 11.0 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Dustin May turns to his cutter throughout the game.
- Watch whether the Tampa Bay lineup maintains its strikeout rate against Dustin May.
- Watch how the Milwaukee hitters handle the sweeper from Griffin Jax.

**Data Confidence Note**

Data confidence for this matchup is based on probable pitchers.


## opener-824384

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 14719, 'candidatesTokenCount': 938, 'thoughtsTokenCount': 1100, 'totalTokenCount': 16757}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `primary_retry`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503')], model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W6.unsaid'], style findings ['S-1', 'S-2', 'S-4', 'W11.expansion', 'W14.team'], tokens {'promptTokenCount': 14748, 'candidatesTokenCount': 1185, 'thoughtsTokenCount': 259, 'totalTokenCount': 16192}
  - gate `W1.number` token `two` in: This game features two starting pitchers and two lineups looking to execute their established game plans.
  - style `W11.expansion` token `ERA` in: Chris Murphy enters this matchup for Chicago with a 3.94 ERA (earned run average) and a 1.34 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 14.
  - style `W11.expansion` token `WHIP` in: Chris Murphy enters this matchup for Chicago with a 3.94 ERA (earned run average) and a 1.34 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 14.
  - style `S-1` token `2026 regular season through Sep 14` in: Foster Griffin brings a 3.65 ERA and a 1.18 WHIP into the contest for Cleveland covering the same 2026 regular season through Sep 14.
  - style `S-4` token `features` in: This game features two starting pitchers and two lineups looking to execute their established game plans.
  - style `S-4` token `utilizes` in: Chris Murphy utilizes a four-seam fastball and a slider.
  - style `S-4` token `maintains` in: Watch whether Foster Griffin maintains his solid command against the Chicago White Sox lineup.
  - style `S-2` token `That group` in: That group has a 24.6% K% (strikeout rate) and a 9.6% BB% against left-handed pitchers.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W14.team` token `None` in: (whole report)
  - NLI (score_only) score `0.0009426795295439661`, problem `None`, paths `['date', 'venue']`: Chris Murphy and Foster Griffin square off at Progressive Field.
  - NLI (score_only) score `0.0003430983342695981`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip']`: Chris Murphy enters this matchup for Chicago with a 3.94 ERA (earned run average) and a 1.34 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 14.
  - NLI (score_only) score `0.0003056972345802933`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Foster Griffin brings a 3.65 ERA and a 1.18 WHIP into the contest for Cleveland covering the same 2026 regular season through Sep 14.
  - NLI (score_only) score `0.7362278699874878`, problem `None`, paths `['teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Both starters face lineups with distinct offensive profiles against left-handed pitchers.
  - NLI (score_only) score `0.6297138333320618`, problem `None`, paths `['data_confidence.lineup_status', 'findings.away_starter_strengths', 'findings.home_starter_strengths']`: This game features two starting pitchers and two lineups looking to execute their established game plans.
  - NLI (score_only) score `0.23132571578025818`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip']`: Chris Murphy has a 3.94 ERA and a 1.34 WHIP across the 2026 regular season through Sep 14.
  - NLI (score_only) score `0.9969514608383179`, problem `None`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.BB%.short']`: The Cleveland lineup draws walks at a 10.2% BB% (walk rate) against left-handed pitchers.
  - NLI (score_only) score `0.9972456693649292`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: This group carries a .657 OPS (on-base plus slugging) against left-handed pitchers over the 2026 regular season through Sep 14.
  - NLI (score_only) score `0.030943915247917175`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Foster Griffin shows solid command with a 3.65 ERA and a 1.18 WHIP over the 2026 regular season through Sep 14.
  - NLI (score_only) score `0.9960797429084778`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Chicago White Sox lineup carries a .742 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9700092673301697`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'glossary.K%.short', 'teams.away.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: That group has a 24.6% K% (strikeout rate) and a 9.6% BB% against left-handed pitchers.
  - NLI (score_only) score `0.7990668416023254`, problem `None`, paths `['findings.lineup_notes.away']`: The Chicago lineup has an elevated swing-and-miss risk.
  - NLI (score_only) score `0.01009697187691927`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch']`: Chris Murphy utilizes a four-seam fastball and a slider.
  - NLI (score_only) score `0.021724453195929527`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam fastball moves 7.7 in. sideways and 16.2 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0017289280658587813`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Foster Griffin relies on a cutter and a four-seam fastball.
  - NLI (score_only) score `0.9695545434951782`, problem `None`, paths `['pitch_movement.home_starter.Cutter.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Cutter.v_break']`: His cutter moves 4.6 in. sideways and 7.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch how often Chris Murphy employs his slider to finish sequences.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.command_label', 'teams.away.name']`: Watch whether Foster Griffin maintains his solid command against the Chicago White Sox lineup.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'teams.home.name']`: Watch if the Chicago White Sox lineup manages the elevated swing-and-miss risk against the Cleveland pitching.
  - NLI (score_only) score `0.23992951214313507`, problem `None`, paths `['data_confidence.lineup_status']`: The lineup status for this game is listed as probable pitchers.
  - Sentence evidence `['F002', 'F244']`: Chris Murphy and Foster Griffin square off at Progressive Field.
  - Sentence evidence `['F158', 'F166', 'F163']`: Chris Murphy enters this matchup for Chicago with a 3.94 ERA (earned run average) and a 1.34 WHIP (walks plus hits per inning) over the 2026 regular season through Sep 14.
  - Sentence evidence `['F190', 'F198', 'F195']`: Foster Griffin brings a 3.65 ERA and a 1.18 WHIP into the contest for Cleveland covering the same 2026 regular season through Sep 14.
  - Sentence evidence `['F212', 'F222']`: Both starters face lineups with distinct offensive profiles against left-handed pitchers.
  - Sentence evidence `['F001', 'F004', 'F007']`: This game features two starting pitchers and two lineups looking to execute their established game plans.
  - Sentence evidence `['F158', 'F166', 'F163']`: Chris Murphy has a 3.94 ERA and a 1.34 WHIP across the 2026 regular season through Sep 14.
  - Sentence evidence `['F216', 'F011']`: The Cleveland lineup draws walks at a 10.2% BB% (walk rate) against left-handed pitchers.
  - Sentence evidence `['F220', 'F017', 'F221']`: This group carries a .657 OPS (on-base plus slugging) against left-handed pitchers over the 2026 regular season through Sep 14.
  - Sentence evidence `['F171', 'F190', 'F198', 'F195']`: Foster Griffin shows solid command with a 3.65 ERA and a 1.18 WHIP over the 2026 regular season through Sep 14.
  - Sentence evidence `['F210', 'F211']`: The Chicago White Sox lineup carries a .742 OPS against left-handed pitchers.
  - Sentence evidence `['F208', 'F014', 'F206', 'F011']`: That group has a 24.6% K% (strikeout rate) and a 9.6% BB% against left-handed pitchers.
  - Sentence evidence `['F009']`: The Chicago lineup has an elevated swing-and-miss risk.
  - Sentence evidence `['F141', 'F142']`: Chris Murphy utilizes a four-seam fastball and a slider.
  - Sentence evidence `['F108', 'F109']`: His four-seam fastball moves 7.7 in. sideways and 16.2 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F173', 'F174']`: Foster Griffin relies on a cutter and a four-seam fastball.
  - Sentence evidence `['F126', 'F127']`: His cutter moves 4.6 in. sideways and 7.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004', 'F142']`: Watch how often Chris Murphy employs his slider to finish sequences.
  - Sentence evidence `['F171', 'F204']`: Watch whether Foster Griffin maintains his solid command against the Chicago White Sox lineup.
  - Sentence evidence `['F009', 'F214']`: Watch if the Chicago White Sox lineup manages the elevated swing-and-miss risk against the Cleveland pitching.
  - Sentence evidence `['F001']`: The lineup status for this game is listed as probable pitchers.
- Length: rules 2285 characters; shown text 2285 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Cutter-Four-seam starter

**Short summary**

- Chris Murphy brings this strength: Four-seam to set up, Slider to finish.
- Foster Griffin brings this strength: Solid command supports strike-zone control.
- The early what to watch is whether Chris Murphy can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Cutter-Four-seam starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Chris Murphy vs Cleveland Guardians**

Chris Murphy works off a four-seam-slider combination. He shows average swing-and-miss ability. Control data for Chris Murphy is limited (140 batters faced; 170 needed), so no command claim is made. Chris Murphy has allowed 2 home runs over 140 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.657 OPS), which gives Chris Murphy an edge if he gets ahead. They draw walks at an above-average rate, so Chris Murphy needs efficient strikes.

**Foster Griffin vs Chicago White Sox**

Foster Griffin works off a cutter-four-seam combination. He shows average swing-and-miss ability. He shows solid command. Foster Griffin has allowed 23 home runs over 674 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against LHP pitching (.742 OPS), so Foster Griffin cannot live over the middle. They also strike out often, which favors a swing-and-miss approach; They draw walks at an above-average rate, so Foster Griffin needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Cutter to set up, Four-seam to finish. The primary pitch contrast is Four-seam against Cutter, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Chris Murphy land the slider early in counts?
- Can Foster Griffin keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Chris Murphy and Foster Griffin: all pitcher figures cover the 2026 regular season through Sep 14. Team offense splits cover the 2026 regular season through Sep 14. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Chris Murphy and the White Sox face Foster Griffin and the Guardians at Progressive Field.

**Short summary**

- This report covers the 2026 regular season through 2026-09-14.
- Chris Murphy starts for the Chicago White Sox, and Foster Griffin starts for the Cleveland Guardians.
- Both lineups enter the game with offensive statistics against left-handed pitchers.
- Both starters feature distinct pitching profiles and arsenals.

**Matchup Summary**

This report covers the 2026 regular season through 2026-09-14.

**Chris Murphy vs Cleveland Guardians**

Chris Murphy has a 3.94 ERA (earned run average) and a 1.34 WHIP (walks plus hits per inning). He shows average swing-and-miss ability. The Cleveland Guardians lineup has a .657 OPS (on-base plus slugging) against left-handed pitchers. This group draws walks at a 10.2% BB% (walk rate) and has a 22.0% K% (strikeout rate).

**Foster Griffin vs Chicago White Sox**

Foster Griffin has a 3.65 ERA and a 1.18 WHIP. He shows solid command and average swing-and-miss ability. The Chicago White Sox offense has a .742 OPS against left-handed pitchers. They have a 9.6% BB% and a 24.6% K% with an elevated swing-and-miss risk.

**Arsenal Scout**

Murphy throws his four-seam fastball at 96.3 mph and his slider at 89.3 mph. Griffin uses a cutter at 88.5 mph and a four-seam fastball at 91.5 mph.

**Three Things to Watch**

- Watch whether Murphy relies on his four-seam fastball to set up hitters.
- Watch how Griffin uses his cutter to set up and his four-seam fastball to finish.
- Watch if the White Sox lineup manages the swing-and-miss risk against left-handed pitching.

**Data Confidence Note**

All data reflects the 2026 regular season through 2026-09-14.


## opener-823605

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 13907, 'candidatesTokenCount': 1108, 'thoughtsTokenCount': 1347, 'totalTokenCount': 16362}
  - gate `W17.structure` token `None` in: (whole report)
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W5.label', 'W10.cause', 'W6.unsaid'], style findings ['S-4', 'S-7', 'W11.expansion', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 13936, 'candidatesTokenCount': 1223, 'thoughtsTokenCount': 2106, 'totalTokenCount': 17265}
  - gate `W5.label` token `above average swing and miss ability and a four seam cutter starter` in: He shows above-average swing-and-miss ability and a four-seam-cutter starter style.
  - gate `W10.cause` token `due to` in: Watch if Christian Scott experiences deep-count traffic due to his below-average command.
  - style `W11.expansion` token `ERA` in: Steven Cruz enters this start with a 5.08 ERA (earned run average) and a 1.45 WHIP (walks plus hits per inning) for the 2026 regular season through 2026-07-07.
  - style `W11.expansion` token `WHIP` in: Steven Cruz enters this start with a 5.08 ERA (earned run average) and a 1.45 WHIP (walks plus hits per inning) for the 2026 regular season through 2026-07-07.
  - style `W11.expansion` token `OPS` in: The Kansas City Royals lineup faces right-handed pitchers with a .720 OPS (on-base plus slugging) over the 2026 regular season through 2026-07-07.
  - style `W11.expansion` token `K%` in: This group shows a 21.6% K% (strikeout rate) and a 9.3% BB% (walk rate) in that split.
  - style `W11.expansion` token `BB%` in: This group shows a 21.6% K% (strikeout rate) and a 9.3% BB% (walk rate) in that split.
  - style `S-7` token `in this matchup` in: Steven Cruz and Christian Scott start in this matchup between the Kansas City Royals and the New York Mets.
  - style `S-7` token `in that split` in: This group shows a 21.6% K% (strikeout rate) and a 9.3% BB% (walk rate) in that split.
  - style `S-4` token `features` in: Christian Scott features a four-seam fastball 50.2% of the time and a sweeper 22.9% of the time.
  - style `S-4` token `features` in: This game features confirmed probable pitchers for 2026-07-08.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1551` in: (whole report)
  - NLI (score_only) score `0.9736832976341248`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'teams.away.name', 'teams.home.name']`: Steven Cruz and Christian Scott start in this matchup between the Kansas City Royals and the New York Mets.
  - NLI (score_only) score `0.01081071700900793`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Steven Cruz enters this start with a 5.08 ERA (earned run average) and a 1.45 WHIP (walks plus hits per inning) for the 2026 regular season through 2026-07-07.
  - NLI (score_only) score `0.6927240490913391`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Christian Scott carries a 3.49 ERA and a 1.35 WHIP through 2026-07-07.
  - NLI (score_only) score `0.0017383189406245947`, problem `None`, paths `['starters.away_starter.throws', 'starters.home_starter.throws']`: Both pitchers are right-handed starters for their respective teams.
  - NLI (score_only) score `0.941627562046051`, problem `None`, paths `['date', 'teams.away.name', 'teams.home.name']`: The Kansas City Royals meet the New York Mets in this game on 2026-07-08.
  - NLI (score_only) score `0.9969822764396667`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Kansas City Royals lineup faces right-handed pitchers with a .720 OPS (on-base plus slugging) over the 2026 regular season through 2026-07-07.
  - NLI (score_only) score `0.9430344104766846`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: This group shows a 21.6% K% (strikeout rate) and a 9.3% BB% (walk rate) in that split.
  - NLI (score_only) score `0.9944146871566772`, problem `None`, paths `['findings.lineup_notes.away']`: The team draws walks at an above-average rate.
  - NLI (score_only) score `0.9920278191566467`, problem `None`, paths `['teams.home.offense_profile.bb_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.ops_vs_hand']`: Against right-handed pitchers, the New York Mets lineup has a .677 OPS, a 22.0% K%, and an 8.3% BB% through 2026-07-07.
  - NLI (score_only) score `0.012504512444138527`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Steven Cruz uses a four-seam fastball 57.8% of the time and a cutter 24.4% of the time.
  - NLI (score_only) score `0.49953967332839966`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label', 'starters.away_starter.pitching_profile.style_label']`: He shows above-average swing-and-miss ability and a four-seam-cutter starter style.
  - NLI (score_only) score `0.05493713170289993`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.3.home_starter.overall']`: Christian Scott features a four-seam fastball 50.2% of the time and a sweeper 22.9% of the time.
  - NLI (score_only) score `0.9889714121818542`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label', 'starters.home_starter.pitching_profile.command_label']`: He shows above-average swing-and-miss ability and below-average command.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Steven Cruz relies on his four-seam fastball as his primary pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_risks', 'starters.home_starter.pitching_profile.command_label']`: Watch if Christian Scott experiences deep-count traffic due to his below-average command.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.style_label']`: Watch whether the Royals lineup effectively targets the four-seam-sweeper starter style of Christian Scott.
  - NLI (score_only) score `0.9603749513626099`, problem `None`, paths `['data_confidence.lineup_status', 'date']`: This game features confirmed probable pitchers for 2026-07-08.
  - Sentence evidence `['F121', 'F153', 'F187', 'F197']`: Steven Cruz and Christian Scott start in this matchup between the Kansas City Royals and the New York Mets.
  - Sentence evidence `['F141', 'F149', 'F145']`: Steven Cruz enters this start with a 5.08 ERA (earned run average) and a 1.45 WHIP (walks plus hits per inning) for the 2026 regular season through 2026-07-07.
  - Sentence evidence `['F173', 'F181', 'F177']`: Christian Scott carries a 3.49 ERA and a 1.35 WHIP through 2026-07-07.
  - Sentence evidence `['F152', 'F184']`: Both pitchers are right-handed starters for their respective teams.
  - Sentence evidence `['F002', 'F187', 'F197']`: The Kansas City Royals meet the New York Mets in this game on 2026-07-08.
  - Sentence evidence `['F193', 'F194']`: The Kansas City Royals lineup faces right-handed pitchers with a .720 OPS (on-base plus slugging) over the 2026 regular season through 2026-07-07.
  - Sentence evidence `['F191', 'F189']`: This group shows a 21.6% K% (strikeout rate) and a 9.3% BB% (walk rate) in that split.
  - Sentence evidence `['F009']`: The team draws walks at an above-average rate.
  - Sentence evidence `['F199', 'F201', 'F203', 'F204']`: Against right-handed pitchers, the New York Mets lineup has a .677 OPS, a 22.0% K%, and an 8.3% BB% through 2026-07-07.
  - Sentence evidence `['F025', 'F036']`: Steven Cruz uses a four-seam fastball 57.8% of the time and a cutter 24.4% of the time.
  - Sentence evidence `['F127', 'F126']`: He shows above-average swing-and-miss ability and a four-seam-cutter starter style.
  - Sentence evidence `['F030', 'F063']`: Christian Scott features a four-seam fastball 50.2% of the time and a sweeper 22.9% of the time.
  - Sentence evidence `['F159', 'F154']`: He shows above-average swing-and-miss ability and below-average command.
  - Sentence evidence `['F124', 'F025']`: Watch how often Steven Cruz relies on his four-seam fastball as his primary pitch.
  - Sentence evidence `['F006', 'F154']`: Watch if Christian Scott experiences deep-count traffic due to his below-average command.
  - Sentence evidence `['F158']`: Watch whether the Royals lineup effectively targets the four-seam-sweeper starter style of Christian Scott.
  - Sentence evidence `['F001', 'F002']`: This game features confirmed probable pitchers for 2026-07-08.
- Length: rules 2147 characters; shown text 2147 characters.

### Rules text (A)

**Headline**

Four-seam-Cutter starter against Four-seam-Sweeper starter

**Short summary**

- Steven Cruz brings this strength: Above-average swing-and-miss ability.
- Christian Scott brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Steven Cruz can land the cutter early in counts.

**Matchup Summary**

This matchup features Four-seam-Cutter starter against Four-seam-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Steven Cruz vs New York Mets**

Steven Cruz works off a four-seam-cutter combination. He shows above-average swing-and-miss ability. Control data for Steven Cruz is limited (124 batters faced; 170 needed), so no command claim is made. Steven Cruz has allowed 8 home runs over 124 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.677 OPS), which gives Steven Cruz an edge if he gets ahead.

**Christian Scott vs Kansas City Royals**

Christian Scott works off a four-seam-sweeper combination. He shows above-average swing-and-miss ability. He shows below-average command. Christian Scott has allowed 7 home runs over 214 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.720 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Christian Scott needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Cutter to finish versus Four-seam to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Steven Cruz land the cutter early in counts?
- Can Christian Scott keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Steven Cruz and Christian Scott: all pitcher figures cover the 2026 regular season through Jul 7. Team offense splits cover the 2026 regular season through Jul 7. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Steven Cruz and Christian Scott face off at Citi Field

**Short summary**

- Steven Cruz faces Christian Scott in a game at Citi Field on July 8, 2026.
- Both starters appear in this matchup during the 2026 regular season through July 7.
- The two right-handed pitchers bring their starting arsenals to this meeting.
- All statistics cover the 2026 regular season through July 7.

**Matchup Summary**

Steven Cruz has a 5.08 ERA (earned run average) and a 1.45 WHIP (walks plus hits per inning). Christian Scott carries a 3.49 ERA and a 1.35 WHIP.

**Steven Cruz vs New York Mets**

Steven Cruz uses a four-seam to set up and a cutter to finish his at-bats. He shows above-average swing-and-miss ability. Control data for Steven Cruz is limited, and there is not enough data yet to rate his command. The New York Mets lineup has a .677 OPS (on-base plus slugging) against right-handed pitchers. This group has a 22.0% K% (strikeout rate) and an 8.3% BB% (walk rate).

**Christian Scott vs Kansas City Royals**

Christian Scott uses a four-seam to set up and a sweeper to finish. He shows below-average command and above-average swing-and-miss ability. The Kansas City Royals lineup has a .720 OPS against right-handed pitchers. That lineup has a 21.6% K% and a 9.3% BB%, and it draws walks at an above-average rate.

**Arsenal Scout**

Steven Cruz throws a four-seam that moves -10.8 in. sideways and 14.9 in. up compared with a pitch thrown without spin. He throws a cutter that moves 1.0 in. sideways and 8.3 in. up compared with a pitch thrown without spin. Christian Scott throws a four-seam that moves -9.5 in. sideways and 15.4 in. up compared with a pitch thrown without spin. He throws a sweeper that moves 17.3 in. sideways and 5.6 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Steven Cruz uses his cutter as a put-away pitch (second most used pitch).
- Watch whether Christian Scott manages his deep-count traffic given his below-average command.
- Watch if the Kansas City Royals capitalize on their ability to draw walks at an above-average rate.

**Data Confidence Note**

Probable pitchers are expected for this game.


## opener-823164

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W6.unsaid'], style findings ['S-2', 'S-4', 'S-7', 'W11.expansion'], tokens {'promptTokenCount': 13944, 'candidatesTokenCount': 948, 'thoughtsTokenCount': 1241, 'totalTokenCount': 16133}
  - style `W11.expansion` token `ERA` in: Jack Dreyer carries a 3.16 ERA (earned run average) and 1.10 WHIP (walks plus hits per inning) for the 2026 regular season through Sep 26.
  - style `W11.expansion` token `WHIP` in: Jack Dreyer carries a 3.16 ERA (earned run average) and 1.10 WHIP (walks plus hits per inning) for the 2026 regular season through Sep 26.
  - style `W11.expansion` token `OPS` in: The San Francisco Giants lineup produces a .660 OPS (on-base plus slugging) against left-handed pitchers.
  - style `W11.expansion` token `K%` in: That group has a 23.7% K% (strikeout rate) and 6.7% BB% (walk rate).
  - style `W11.expansion` token `BB%` in: That group has a 23.7% K% (strikeout rate) and 6.7% BB% (walk rate).
  - style `S-7` token `in the same period` in: Carson Seymour has a 4.70 ERA and 1.53 WHIP in the same period.
  - style `S-4` token `maintains` in: The group maintains a 20.6% K% and 10.4% BB%.
  - style `S-2` token `the` in: The Slider of Carson Seymour moves 0.1 in. sideways and 6.0 in. down compared with a pitch thrown without spin.
  - style `S-2` token `This lineup` in: This lineup has a strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - gate `W6.unsaid` token `None` in: (whole report)
  - NLI (score_only) score `0.0066599673591554165`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Jack Dreyer faces Carson Seymour at Oracle Park
  - NLI (score_only) score `0.5704447627067566`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Jack Dreyer carries a 3.16 ERA (earned run average) and 1.10 WHIP (walks plus hits per inning) for the 2026 regular season through Sep 26.
  - NLI (score_only) score `0.00693359924480319`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Carson Seymour has a 4.70 ERA and 1.53 WHIP in the same period.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.team', 'teams.home.name', 'status']`: The Los Angeles Dodgers and San Francisco Giants are scheduled for this game.
  - NLI (score_only) score `0.00323044927790761`, problem `None`, paths `['findings.away_style', 'findings.home_style']`: Each starter enters the matchup with a specific approach to his pitch mix.
  - NLI (score_only) score `0.976858377456665`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: Jack Dreyer shows average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9943516254425049`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand']`: The San Francisco Giants lineup produces a .660 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9851489067077637`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number']`: That group has a 23.7% K% (strikeout rate) and 6.7% BB% (walk rate).
  - NLI (score_only) score `0.9912139773368835`, problem `None`, paths `['starters.home_starter.pitching_profile.swing_miss_label']`: Carson Seymour shows below-average swing-and-miss ability.
  - NLI (score_only) score `0.9882966876029968`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The Los Angeles Dodgers lineup has a .766 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9837904572486877`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: The group maintains a 20.6% K% and 10.4% BB%.
  - NLI (score_only) score `0.9898055791854858`, problem `None`, paths `['findings.lineup_notes.away']`: This lineup has a strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - NLI (score_only) score `0.0037391595542430878`, problem `None`, paths `['findings.away_starter_strengths', 'starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch']`: Jack Dreyer uses his Four-seam fastball to set up and his Slider to finish.
  - NLI (score_only) score `0.07158423215150833`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam fastball moves 6.1 in. sideways and 19.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9829401969909668`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Slider.v_break']`: Jack Dreyer's Slider moves 3.0 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9853458404541016`, problem `None`, paths `['findings.home_starter_strengths', 'starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Carson Seymour uses his Sinker to set up and his Slider as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.924433171749115`, problem `None`, paths `['pitch_movement.home_starter.Sinker.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sinker.v_break']`: His Sinker moves 15.6 in. sideways and 4.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.38735976815223694`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break']`: The Slider of Carson Seymour moves 0.1 in. sideways and 6.0 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.count', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Jack Dreyer uses his Four-seam fastball in this game.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.3.home_starter.count', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch whether Carson Seymour relies on his Sinker to set up hitters.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch if the San Francisco Giants reduce their K% against left-handed pitchers.
  - NLI (score_only) score `0.9398270845413208`, problem `None`, paths `['data_confidence.lineup_status']`: Lineup status is listed as probable pitchers.
  - Sentence evidence `['F118', 'F150', 'F221']`: Jack Dreyer faces Carson Seymour at Oracle Park
  - Sentence evidence `['F138', 'F146', 'F142']`: Jack Dreyer carries a 3.16 ERA (earned run average) and 1.10 WHIP (walks plus hits per inning) for the 2026 regular season through Sep 26.
  - Sentence evidence `['F170', 'F178', 'F174']`: Carson Seymour has a 4.70 ERA and 1.53 WHIP in the same period.
  - Sentence evidence `['F148', 'F194', 'F182']`: The Los Angeles Dodgers and San Francisco Giants are scheduled for this game.
  - Sentence evidence `['F005', 'F008']`: Each starter enters the matchup with a specific approach to his pitch mix.
  - Sentence evidence `['F119', 'F124']`: Jack Dreyer shows average command and above-average swing-and-miss ability.
  - Sentence evidence `['F200', 'F202']`: The San Francisco Giants lineup produces a .660 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F197', 'F195']`: That group has a 23.7% K% (strikeout rate) and 6.7% BB% (walk rate).
  - Sentence evidence `['F156']`: Carson Seymour shows below-average swing-and-miss ability.
  - Sentence evidence `['F190', 'F192']`: The Los Angeles Dodgers lineup has a .766 OPS against right-handed pitchers.
  - Sentence evidence `['F187', 'F185']`: The group maintains a 20.6% K% and 10.4% BB%.
  - Sentence evidence `['F009']`: This lineup has a strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - Sentence evidence `['F004', 'F121', 'F122']`: Jack Dreyer uses his Four-seam fastball to set up and his Slider to finish.
  - Sentence evidence `['F094', 'F095']`: His Four-seam fastball moves 6.1 in. sideways and 19.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F097', 'F098']`: Jack Dreyer's Slider moves 3.0 in. sideways and 3.4 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F007', 'F153', 'F154', 'F022']`: Carson Seymour uses his Sinker to set up and his Slider as his put-away pitch (second most used pitch).
  - Sentence evidence `['F109', 'F110']`: His Sinker moves 15.6 in. sideways and 4.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F112', 'F113']`: The Slider of Carson Seymour moves 0.1 in. sideways and 6.0 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F024']`: Watch how often Jack Dreyer uses his Four-seam fastball in this game.
  - Sentence evidence `['F062']`: Watch whether Carson Seymour relies on his Sinker to set up hitters.
  - Sentence evidence `['F197']`: Watch if the San Francisco Giants reduce their K% against left-handed pitchers.
  - Sentence evidence `['F001']`: Lineup status is listed as probable pitchers.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none, tokens {'promptTokenCount': 14099, 'candidatesTokenCount': 949, 'thoughtsTokenCount': 776, 'totalTokenCount': 15824}
  - gate `W17.structure` token `None` in: (whole report)
- Length: rules 2113 characters; shown text 2113 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Sinker-Slider starter

**Short summary**

- Jack Dreyer brings this strength: Above-average swing-and-miss ability.
- Carson Seymour brings this strength: Sinker to set up, Slider to finish.
- The early what to watch is whether Jack Dreyer can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Sinker-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Jack Dreyer vs San Francisco Giants**

Jack Dreyer works off a four-seam-slider combination. He shows above-average swing-and-miss ability. He shows average command. Jack Dreyer has allowed 7 home runs over 254 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.660 OPS), which gives Jack Dreyer an edge if he gets ahead.

**Carson Seymour vs Los Angeles Dodgers**

Carson Seymour works off a sinker-slider combination. He shows below-average swing-and-miss ability. Control data for Carson Seymour is limited (137 batters faced; 170 needed), so no command claim is made. Carson Seymour has allowed 6 home runs over 137 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against RHP pitching (.766 OPS), so Carson Seymour cannot live over the middle. They draw walks at an above-average rate, so Carson Seymour needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Sinker to set up, Slider to finish. The primary pitch contrast is Four-seam against Sinker, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Jack Dreyer land the slider early in counts?
- Can Carson Seymour keep the ball low?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Jack Dreyer and Carson Seymour: all pitcher figures cover the 2026 regular season through Sep 26. Team offense splits cover the 2026 regular season through Sep 26. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W17.structure'], style findings none; a `W17.structure` failure stops the other gate checks, so this attempt's other gates were not evaluated and its count is not comparable

**Headline**

Jack Dreyer and Carson Seymour open the series at Oracle Park

**Short summary**

- Jack Dreyer takes the mound for the Los Angeles Dodgers to face Carson Seymour of the San Francisco Giants.
- This matchup features starters with different primary pitch and put-away pitch combinations.
- All statistics cover the 2026 regular season through Sep 26.
- Both teams enter with distinct offensive profiles against these pitching styles.

**Matchup Summary**

Jack Dreyer has a 3.16 ERA (earned run average) and a 1.10 WHIP (walks plus hits per inning). Carson Seymour has a 4.70 ERA and a 1.53 WHIP.

**Jack Dreyer vs San Francisco Giants**

The Giants lineup has a .660 OPS (on-base plus slugging) against left-handed pitchers. That group has a 23.7% K% (strikeout rate) and a 6.7% BB% (walk rate).

**Carson Seymour vs Los Angeles Dodgers**

The Dodgers lineup has a .766 OPS against right-handed pitchers. This group draws walks at an above-average rate and has a 20.6% K% and a 10.4% BB%. Control data for Carson Seymour is limited, with 137 batters faced against a needed 170.

**Arsenal Scout**

Jack Dreyer uses a Four-seam and a Slider, while Carson Seymour throws a Sinker and a Slider. Dreyer shows above-average swing-and-miss ability and average command. Seymour shows below-average swing-and-miss ability. Dreyer has a Four-seam that moves 6.1 in. sideways and 19.7 in. up compared with a pitch thrown without spin. His Slider moves 3.0 in. sideways and 3.4 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Jack Dreyer relies on his Four-seam and Slider to navigate the order.
- Watch whether the Dodgers exploit the limited control data for Carson Seymour.
- Watch if the Giants can generate offense against the Four-seam and Slider of Jack Dreyer.

**Data Confidence Note**

The probable pitchers status confirms both starters for this game.


## limited-824344

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W6.unsaid'], style findings ['S-2', 'S-4', 'W12.scope'], tokens {'promptTokenCount': 14091, 'candidatesTokenCount': 1026, 'thoughtsTokenCount': 2155, 'totalTokenCount': 17272}
  - style `S-4` token `maintains` in: The Boston Red Sox lineup maintains a .676 OPS against right-handed pitchers.
  - style `S-2` token `the` in: The slider moves 4.4 in. sideways and 4.9 in. up compared with a pitch thrown without spin.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.team', 'starters.home_starter.team', 'starters.away_starter.name', 'starters.home_starter.name']`: Jake Bennett and the Boston Red Sox face Ryan Feltner and the Colorado Rockies
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.home_starter.team']`: Jake Bennett starts for the Boston Red Sox against the Colorado Rockies.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.home_starter.name', 'starters.home_starter.team']`: Ryan Feltner takes the mound for the Colorado Rockies.
  - NLI (score_only) score `0.012589465826749802`, problem `None`, paths `['starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All figures reflect data for the 2026 regular season through 2026-06-21.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.team', 'starters.home_starter.team']`: The Boston Red Sox and the Colorado Rockies meet for a duel between starters Jake Bennett and Ryan Feltner.
  - NLI (score_only) score `0.9970412850379944`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Jake Bennett carries a 4.79 ERA (earned run average) and a 1.26 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9866103529930115`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: He shows below-average swing-and-miss ability.
  - NLI (score_only) score `0.9769983887672424`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: His control data is limited with 85 batters faced, and 170 are needed for a rating.
  - NLI (score_only) score `0.9904781579971313`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The Colorado Rockies lineup has a .683 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9604681730270386`, problem `None`, paths `['findings.lineup_notes.home', 'teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number', 'glossary.K%.short', 'glossary.BB%.short']`: That group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) and has elevated swing-and-miss risk.
  - NLI (score_only) score `0.001748847309499979`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Ryan Feltner has a 5.05 ERA and a 1.29 WHIP.
  - NLI (score_only) score `0.9722414612770081`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9958969354629517`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: The Boston Red Sox lineup maintains a .676 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9522900581359863`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: Their K% is 22.7% and their BB% is 7.6%.
  - NLI (score_only) score `0.9783862233161926`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Jake Bennett uses his four-seam fastball 31.0% of the time and his sinker 29.4% of the time.
  - NLI (score_only) score `0.016919629648327827`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: The four-seam fastball moves 11.2 in. sideways and 12.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.35601115226745605`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.5.home_starter.overall']`: Ryan Feltner uses his four-seam fastball 25.1% of the time and his slider 25.1% of the time.
  - NLI (score_only) score `0.9610182046890259`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break']`: The slider moves 4.4 in. sideways and 4.9 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_starter_strengths']`: Watch how often Jake Bennett relies on his four-seam fastball for his setup.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home']`: Watch whether the Colorado Rockies lineup manages the elevated swing-and-miss risk.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Watch how Ryan Feltner uses his slider as a put-away pitch (second most used pitch).
  - NLI (score_only) score `0.9922466278076172`, problem `None`, paths `['data_confidence.lineup_status', 'date']`: This report uses probable pitchers for the game on 2026-06-22.
  - Sentence evidence `['F154', 'F186', 'F124', 'F156']`: Jake Bennett and the Boston Red Sox face Ryan Feltner and the Colorado Rockies
  - Sentence evidence `['F124', 'F186']`: Jake Bennett starts for the Boston Red Sox against the Colorado Rockies.
  - Sentence evidence `['F156', 'F186']`: Ryan Feltner takes the mound for the Colorado Rockies.
  - Sentence evidence `['F148', 'F180', 'F197', 'F207']`: All figures reflect data for the 2026 regular season through 2026-06-21.
  - Sentence evidence `['F124', 'F156', 'F154', 'F186']`: The Boston Red Sox and the Colorado Rockies meet for a duel between starters Jake Bennett and Ryan Feltner.
  - Sentence evidence `['F144', 'F152', 'F013', 'F018']`: Jake Bennett carries a 4.79 ERA (earned run average) and a 1.26 WHIP (walks plus hits per inning).
  - Sentence evidence `['F130']`: He shows below-average swing-and-miss ability.
  - Sentence evidence `['F134', 'F136', 'F142']`: His control data is limited with 85 batters faced, and 170 are needed for a rating.
  - Sentence evidence `['F205', 'F206', 'F208', 'F017']`: The Colorado Rockies lineup has a .683 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F010', 'F203', 'F201', 'F014', 'F011']`: That group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) and has elevated swing-and-miss risk.
  - Sentence evidence `['F176', 'F184']`: Ryan Feltner has a 5.05 ERA and a 1.29 WHIP.
  - Sentence evidence `['F157', 'F162']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F195', 'F196', 'F198']`: The Boston Red Sox lineup maintains a .676 OPS against right-handed pitchers.
  - Sentence evidence `['F193', 'F191']`: Their K% is 22.7% and their BB% is 7.6%.
  - Sentence evidence `['F025', 'F036']`: Jake Bennett uses his four-seam fastball 31.0% of the time and his sinker 29.4% of the time.
  - Sentence evidence `['F097', 'F098']`: The four-seam fastball moves 11.2 in. sideways and 12.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F030', 'F085']`: Ryan Feltner uses his four-seam fastball 25.1% of the time and his slider 25.1% of the time.
  - Sentence evidence `['F118', 'F119']`: The slider moves 4.4 in. sideways and 4.9 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F004']`: Watch how often Jake Bennett relies on his four-seam fastball for his setup.
  - Sentence evidence `['F010']`: Watch whether the Colorado Rockies lineup manages the elevated swing-and-miss risk.
  - Sentence evidence `['F160', 'F022']`: Watch how Ryan Feltner uses his slider as a put-away pitch (second most used pitch).
  - Sentence evidence `['F001', 'F002']`: This report uses probable pitchers for the game on 2026-06-22.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W10.cause', 'W15.outcome', 'W6.unsaid', 'W13.series'], style findings ['S-7', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14192, 'candidatesTokenCount': 920, 'thoughtsTokenCount': 1444, 'totalTokenCount': 16556}
  - gate `W10.cause` token `because` in: His control data is limited because he has faced 85 batters faced, and 170 are needed for a full read.
  - gate `W15.outcome` token `strikeouts` in: Watch whether the Colorado Rockies lineup can avoid strikeouts against Jake Bennett.
  - style `S-7` token `in that split` in: This group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) in that split.
  - gate `W6.unsaid` token `None` in: (whole report)
  - gate `W13.series` token `None` in: (whole report)
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1580` in: (whole report)
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.team', 'starters.home_starter.team']`: Jake Bennett and Ryan Feltner lead their teams in the series opener.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'starters.home_starter.team']`: Jake Bennett starts for the Boston Red Sox against the Colorado Rockies.
  - NLI (score_only) score `0.9890173673629761`, problem `None`, paths `['starters.home_starter.name', 'venue']`: Ryan Feltner starts for the home team in this game at Coors Field.
  - NLI (score_only) score `0.0037244269624352455`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All statistics cover the 2026 regular season through 2026-06-21.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'starters.home_starter.name', 'starters.home_starter.team']`: The starting pitchers for this game are Jake Bennett for the Boston Red Sox and Ryan Feltner for the Colorado Rockies.
  - NLI (score_only) score `0.9947150349617004`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Jake Bennett holds a 4.79 ERA (earned run average) and a 1.26 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9457030296325684`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: His control data is limited because he has faced 85 batters faced, and 170 are needed for a full read.
  - NLI (score_only) score `0.9959326386451721`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short', 'findings.lineup_notes.home']`: The Colorado Rockies lineup shows a .683 OPS (on-base plus slugging) against left-handed pitchers and has an elevated swing-and-miss risk.
  - NLI (score_only) score `0.25832512974739075`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: This group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) in that split.
  - NLI (score_only) score `0.002866011345759034`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Ryan Feltner carries a 5.05 ERA and a 1.29 WHIP.
  - NLI (score_only) score `0.9722414612770081`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9918647408485413`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Boston Red Sox lineup has a .676 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9715705513954163`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: Those hitters have a 22.7% K% and a 7.6% BB% against right-handed pitchers.
  - NLI (score_only) score `0.0389229953289032`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall', 'starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Jake Bennett uses a four-seam fastball 31.0% of the time to set up and a sinker 29.4% of the time as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.002452013548463583`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.5.home_starter.overall', 'starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Ryan Feltner uses a four-seam fastball 25.1% of the time to set up and a slider 25.1% of the time as his put-away pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Jake Bennett throws his four-seam fastball.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Watch if Ryan Feltner leans on his slider when he gets ahead.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch whether the Colorado Rockies lineup can avoid strikeouts against Jake Bennett.
  - NLI (score_only) score `0.9455296993255615`, problem `None`, paths `['data_confidence.lineup_status']`: The game status is listed as probable pitchers.
  - Sentence evidence `['F124', 'F156', 'F154', 'F186']`: Jake Bennett and Ryan Feltner lead their teams in the series opener.
  - Sentence evidence `['F124', 'F154', 'F186']`: Jake Bennett starts for the Boston Red Sox against the Colorado Rockies.
  - Sentence evidence `['F156', 'F227']`: Ryan Feltner starts for the home team in this game at Coors Field.
  - Sentence evidence `['F132', 'F164', 'F197', 'F207']`: All statistics cover the 2026 regular season through 2026-06-21.
  - Sentence evidence `['F124', 'F154', 'F156', 'F186']`: The starting pitchers for this game are Jake Bennett for the Boston Red Sox and Ryan Feltner for the Colorado Rockies.
  - Sentence evidence `['F144', 'F152', 'F013', 'F018']`: Jake Bennett holds a 4.79 ERA (earned run average) and a 1.26 WHIP (walks plus hits per inning).
  - Sentence evidence `['F134', 'F136', 'F142']`: His control data is limited because he has faced 85 batters faced, and 170 are needed for a full read.
  - Sentence evidence `['F206', 'F017', 'F010']`: The Colorado Rockies lineup shows a .683 OPS (on-base plus slugging) against left-handed pitchers and has an elevated swing-and-miss risk.
  - Sentence evidence `['F204', 'F202', 'F014', 'F011']`: This group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) in that split.
  - Sentence evidence `['F176', 'F184']`: Ryan Feltner carries a 5.05 ERA and a 1.29 WHIP.
  - Sentence evidence `['F157', 'F162']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F196']`: The Boston Red Sox lineup has a .676 OPS against right-handed pitchers.
  - Sentence evidence `['F194', 'F192']`: Those hitters have a 22.7% K% and a 7.6% BB% against right-handed pitchers.
  - Sentence evidence `['F025', 'F036', 'F127', 'F128', 'F022']`: Jake Bennett uses a four-seam fastball 31.0% of the time to set up and a sinker 29.4% of the time as his put-away pitch (second most used pitch).
  - Sentence evidence `['F030', 'F085', 'F159', 'F160']`: Ryan Feltner uses a four-seam fastball 25.1% of the time to set up and a slider 25.1% of the time as his put-away pitch.
  - Sentence evidence `['F025']`: Watch how often Jake Bennett throws his four-seam fastball.
  - Sentence evidence `['F085']`: Watch if Ryan Feltner leans on his slider when he gets ahead.
  - Sentence evidence `['F204']`: Watch whether the Colorado Rockies lineup can avoid strikeouts against Jake Bennett.
  - Sentence evidence `['F001']`: The game status is listed as probable pitchers.
- Length: rules 2117 characters; shown text 2117 characters.

### Rules text (A)

**Headline**

Four-seam-Sinker starter against Four-seam-Slider starter

**Short summary**

- Jake Bennett brings this strength: Four-seam to set up, Sinker to finish.
- Ryan Feltner brings this strength: Four-seam to set up, Slider to finish.
- The early what to watch is whether Jake Bennett can land the sinker early in counts.

**Matchup Summary**

This matchup features Four-seam-Sinker starter against Four-seam-Slider starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Jake Bennett vs Colorado Rockies**

Jake Bennett works off a four-seam-sinker combination. He shows below-average swing-and-miss ability. Control data for Jake Bennett is limited (85 batters faced; 170 needed), so no command claim is made. Jake Bennett has allowed 1 home run over 85 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.683 OPS), which gives Jake Bennett an edge if he gets ahead. They also strike out often, which favors a swing-and-miss approach.

**Ryan Feltner vs Boston Red Sox**

Ryan Feltner works off a four-seam-slider combination. He shows average swing-and-miss ability. He shows average command. Ryan Feltner has allowed 7 home runs over 173 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against RHP pitching (.676 OPS), which gives Ryan Feltner an edge if he gets ahead.

**Arsenal Scout**

The main contrast is Four-seam to set up, Sinker to finish versus Four-seam to set up, Slider to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Jake Bennett land the sinker early in counts?
- Can Ryan Feltner keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Jake Bennett and Ryan Feltner: all pitcher figures cover the 2026 regular season through Jun 21. Team offense splits cover the 2026 regular season through Jun 21. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W6.unsaid'], style findings ['S-2', 'S-4', 'W12.scope']

**Headline**

Jake Bennett and the Boston Red Sox face Ryan Feltner and the Colorado Rockies

**Short summary**

- Jake Bennett starts for the Boston Red Sox against the Colorado Rockies.
- Ryan Feltner takes the mound for the Colorado Rockies.
- All figures reflect data for the 2026 regular season through 2026-06-21.

**Matchup Summary**

The Boston Red Sox and the Colorado Rockies meet for a duel between starters Jake Bennett and Ryan Feltner.

**Jake Bennett vs Colorado Rockies**

Jake Bennett carries a 4.79 ERA (earned run average) and a 1.26 WHIP (walks plus hits per inning). He shows below-average swing-and-miss ability. His control data is limited with 85 batters faced, and 170 are needed for a rating. The Colorado Rockies lineup has a .683 OPS (on-base plus slugging) against left-handed pitchers. That group shows a 26.4% K% (strikeout rate) and a 6.3% BB% (walk rate) and has elevated swing-and-miss risk.

**Ryan Feltner vs Boston Red Sox**

Ryan Feltner has a 5.05 ERA and a 1.29 WHIP. He shows average command and average swing-and-miss ability. The Boston Red Sox lineup maintains a .676 OPS against right-handed pitchers. Their K% is 22.7% and their BB% is 7.6%.

**Arsenal Scout**

Jake Bennett uses his four-seam fastball 31.0% of the time and his sinker 29.4% of the time. The four-seam fastball moves 11.2 in. sideways and 12.5 in. up compared with a pitch thrown without spin. Ryan Feltner uses his four-seam fastball 25.1% of the time and his slider 25.1% of the time. The slider moves 4.4 in. sideways and 4.9 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Jake Bennett relies on his four-seam fastball for his setup.
- Watch whether the Colorado Rockies lineup manages the elevated swing-and-miss risk.
- Watch how Ryan Feltner uses his slider as a put-away pitch (second most used pitch).

**Data Confidence Note**

This report uses probable pitchers for the game on 2026-06-22.


## limited-823715

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W6.unsaid'], style findings ['S-1', 'S-2', 'W11.expansion', 'W17.length'], tokens {'promptTokenCount': 13586, 'candidatesTokenCount': 1488, 'thoughtsTokenCount': 1450, 'totalTokenCount': 16524}
  - style `W11.expansion` token `ERA` in: Dylan Cease carries a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - style `W11.expansion` token `WHIP` in: Dylan Cease carries a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - style `S-1` token `2026 regular season through May 1` in: All pitching and hitting figures in this report are from the 2026 regular season through May 1.
  - style `S-2` token `the` in: The data in this report is based on stats from the 2026 regular season through May 1.
  - gate `W6.unsaid` token `None` in: (whole report)
  - style `W17.length` token `1800` in: (whole report)
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.away_starter.team', 'starters.home_starter.name', 'starters.home_starter.team']`: Dylan Cease starts for Toronto against Connor Prielipp and the Minnesota Twins
  - NLI (score_only) score `0.5697012543678284`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Dylan Cease carries a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - NLI (score_only) score `0.008156634867191315`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP through the same period.
  - NLI (score_only) score `0.9563743472099304`, problem `None`, paths `['teams.away.name', 'teams.home.name', 'venue']`: The Toronto Blue Jays face the Minnesota Twins at Target Field.
  - NLI (score_only) score `0.0019951947033405304`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All pitching and hitting figures in this report are from the 2026 regular season through May 1.
  - NLI (score_only) score `0.9941565990447998`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Dylan Cease shows above-average swing-and-miss ability.
  - NLI (score_only) score `0.9879416823387146`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.vs_pitcher_hand', 'glossary.OPS.short']`: The Minnesota Twins lineup has a .707 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9527586102485657`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_number', 'glossary.K%.short', 'glossary.BB%.short']`: Their K% (strikeout rate) is 23.8% and their BB% (walk rate) is 10.1%.
  - NLI (score_only) score `0.987300455570221`, problem `None`, paths `['findings.lineup_notes.home']`: The Minnesota lineup draws walks at an above-average rate.
  - NLI (score_only) score `0.9919244647026062`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: The Toronto Blue Jays have a .632 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9505285024642944`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: Their K% is 16.2% and their BB% is 9.8%.
  - NLI (score_only) score `0.9930872321128845`, problem `None`, paths `['findings.lineup_notes.away']`: Toronto draws walks at an above-average rate.
  - NLI (score_only) score `0.9174368977546692`, problem `None`, paths `['starters.home_starter.sample.limited.strikeout', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.strikeout', 'starters.home_starter.pitching_profile.swing_miss_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through', 'starters.home_starter.sample.rates.strikeouts']`: Connor Prielipp has a limited sample for strikeout data with 11 strikeouts in 36 batters faced, and 70 are needed for a read.
  - NLI (score_only) score `0.9693147540092468`, problem `None`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through']`: His control data is also limited as he has faced 36 batters and 170 are needed for a read.
  - NLI (score_only) score `0.0008785890531726182`, problem `None`, paths `['starters.away_starter.pitching_profile.style_label', 'starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch']`: Dylan Cease is a Four-seam-Slider starter who uses his Four-seam fastball to set up and his Slider to finish.
  - NLI (score_only) score `0.07265850156545639`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His Four-seam fastball moves 3.7 in. sideways and 19.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.001376026077196002`, problem `None`, paths `['starters.home_starter.pitching_profile.style_label', 'starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Connor Prielipp is a Slider-Four-seam starter who uses his Slider to set up and his Four-seam fastball to finish.
  - NLI (score_only) score `0.11576636880636215`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break']`: His Slider moves 2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style']`: Watch how Dylan Cease uses his Four-seam fastball early in the count.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.primary_pitch']`: Watch whether Connor Prielipp uses his Slider as a primary pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'findings.lineup_notes.home']`: Watch how often both teams draw walks given their above-average rates.
  - NLI (score_only) score `0.8890603184700012`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The data in this report is based on stats from the 2026 regular season through May 1.
  - Sentence evidence `['F110', 'F140', 'F142', 'F172']`: Dylan Cease starts for Toronto against Connor Prielipp and the Minnesota Twins
  - Sentence evidence `['F130', 'F138', 'F134']`: Dylan Cease carries a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - Sentence evidence `['F162', 'F170', 'F166']`: Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP through the same period.
  - Sentence evidence `['F176', 'F186', 'F210']`: The Toronto Blue Jays face the Minnesota Twins at Target Field.
  - Sentence evidence `['F118', 'F183', 'F193']`: All pitching and hitting figures in this report are from the 2026 regular season through May 1.
  - Sentence evidence `['F116']`: Dylan Cease shows above-average swing-and-miss ability.
  - Sentence evidence `['F191', 'F192', 'F194', 'F017']`: The Minnesota Twins lineup has a .707 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F189', 'F187', 'F014', 'F011']`: Their K% (strikeout rate) is 23.8% and their BB% (walk rate) is 10.1%.
  - Sentence evidence `['F010']`: The Minnesota lineup draws walks at an above-average rate.
  - Sentence evidence `['F181', 'F182', 'F184']`: The Toronto Blue Jays have a .632 OPS against left-handed pitchers.
  - Sentence evidence `['F179', 'F177']`: Their K% is 16.2% and their BB% is 9.8%.
  - Sentence evidence `['F009']`: Toronto draws walks at an above-average rate.
  - Sentence evidence `['F153', 'F154', 'F157', 'F161']`: Connor Prielipp has a limited sample for strikeout data with 11 strikeouts in 36 batters faced, and 70 are needed for a read.
  - Sentence evidence `['F152', 'F154', 'F160']`: His control data is also limited as he has faced 36 batters and 170 are needed for a read.
  - Sentence evidence `['F115', 'F113', 'F114']`: Dylan Cease is a Four-seam-Slider starter who uses his Four-seam fastball to set up and his Slider to finish.
  - Sentence evidence `['F086', 'F087']`: His Four-seam fastball moves 3.7 in. sideways and 19.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F147', 'F145', 'F146']`: Connor Prielipp is a Slider-Four-seam starter who uses his Slider to set up and his Four-seam fastball to finish.
  - Sentence evidence `['F107', 'F108']`: His Slider moves 2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F005']`: Watch how Dylan Cease uses his Four-seam fastball early in the count.
  - Sentence evidence `['F145']`: Watch whether Connor Prielipp uses his Slider as a primary pitch.
  - Sentence evidence `['F009', 'F010']`: Watch how often both teams draw walks given their above-average rates.
  - Sentence evidence `['F118', 'F183']`: The data in this report is based on stats from the 2026 regular season through May 1.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W1.number', 'W8.form'], style findings ['S-2', 'S-4', 'S-7'], tokens {'promptTokenCount': 13720, 'candidatesTokenCount': 1138, 'thoughtsTokenCount': 2618, 'totalTokenCount': 17476}
  - gate `W1.number` token `two` in: The matchup features two starters looking to settle into the rotation.
  - gate `W8.form` token `None` in: His slider moves -2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.
  - style `S-7` token `over the same period` in: Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP over the same period.
  - style `S-4` token `features` in: The matchup features two starters looking to settle into the rotation.
  - style `S-4` token `maintains` in: That group maintains a 23.8% K% (strikeout rate) and a 10.1% BB% (walk rate).
  - style `S-7` token `in the same period` in: Connor Prielipp has thrown 166 pitches in the same period.
  - style `S-4` token `maintain` in: Watch if the lineups maintain their walk rates against these pitchers.
  - style `S-2` token `the` in: The Blue Jays draw walks at an above-average rate.
  - NLI (score_only) score `0.022563770413398743`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Dylan Cease faces Connor Prielipp at Target Field
  - NLI (score_only) score `0.9658539891242981`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: Dylan Cease enters with a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - NLI (score_only) score `0.0021136105060577393`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP over the same period.
  - NLI (score_only) score `0.005385137628763914`, problem `None`, paths `['data_confidence.lineup_status']`: Both teams look to capitalize on their respective offensive profiles against the opposing starter.
  - NLI (score_only) score `0.00043842141167260706`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: The matchup features two starters looking to settle into the rotation.
  - NLI (score_only) score `0.021327896043658257`, problem `None`, paths `['starters.away_starter.name', 'starters.away_starter.throws', 'teams.home.name']`: Dylan Cease is a right-handed pitcher facing the Minnesota Twins lineup.
  - NLI (score_only) score `0.9789420366287231`, problem `None`, paths `['teams.home.offense_profile.ops_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.ops_vs_hand', 'glossary.OPS.short', 'teams.home.offense_profile.vs_pitcher_hand']`: The Minnesota Twins lineup has a .707 OPS (on-base plus slugging) against right-handed pitchers.
  - NLI (score_only) score `0.9281569123268127`, problem `None`, paths `['teams.home.offense_profile.k_rate_number', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.k_rate_vs_hand', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_number', 'glossary.BB%.short']`: That group maintains a 23.8% K% (strikeout rate) and a 10.1% BB% (walk rate).
  - NLI (score_only) score `0.9962653517723083`, problem `None`, paths `['findings.lineup_notes.home']`: The Twins draw walks at an above-average rate.
  - NLI (score_only) score `0.04763123393058777`, problem `None`, paths `['starters.home_starter.name', 'starters.home_starter.throws', 'teams.away.name']`: Connor Prielipp is a left-handed pitcher facing the Toronto Blue Jays lineup.
  - NLI (score_only) score `0.989288330078125`, problem `None`, paths `['teams.away.offense_profile.ops_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.vs_pitcher_hand']`: The Toronto Blue Jays lineup has a .632 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9513438940048218`, problem `None`, paths `['teams.away.offense_profile.k_rate_number', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_number']`: They show a 16.2% K% and a 9.8% BB%.
  - NLI (score_only) score `0.9964194297790527`, problem `None`, paths `['findings.lineup_notes.away']`: The Blue Jays draw walks at an above-average rate.
  - NLI (score_only) score `0.9858086109161377`, problem `None`, paths `['starters.away_starter.sample.arsenal.pitches', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Dylan Cease has a 2026 regular season sample of 602 total pitches through May 1.
  - NLI (score_only) score `0.8319259285926819`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: He uses a four-seam fastball 36.9% of the time and a slider 28.4% of the time.
  - NLI (score_only) score `0.9461290240287781`, problem `None`, paths `['pitch_movement.away_starter.Slider.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Slider.v_break']`: His slider moves 0.6 in. sideways and 3.5 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.9914382696151733`, problem `None`, paths `['starters.home_starter.sample.arsenal.pitches', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Connor Prielipp has thrown 166 pitches in the same period.
  - NLI (score_only) score `0.0018325067358091474`, problem `None`, paths `['pitch_mix.1.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.0.home_starter.overall']`: He uses his slider 47.0% of the time and his four-seam fastball 28.3% of the time.
  - NLI (score_only) score `0.008213820867240429`, problem `None`, paths `['pitch_movement.home_starter.Slider.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Slider.v_break']`: His slider moves -2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.away_style', 'starters.away_starter.pitching_profile.putaway_pitch']`: Watch whether Dylan Cease uses his slider to finish sequences.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_strengths', 'findings.home_style']`: Watch how often Connor Prielipp relies on his slider to set up his four-seam fastball.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.away', 'findings.lineup_notes.home']`: Watch if the lineups maintain their walk rates against these pitchers.
  - NLI (score_only) score `0.9850162267684937`, problem `None`, paths `['starters.away_starter.sample.limited.control', 'starters.away_starter.sample.rates.batters_faced', 'starters.away_starter.sample.thresholds.control', 'starters.away_starter.pitching_profile.command_label', 'starters.away_starter.sample.rates.scope.label', 'starters.away_starter.sample.rates.scope.through']`: Control data for Dylan Cease is limited as he has faced 138 batters and needs 170.
  - NLI (score_only) score `0.035655826330184937`, problem `None`, paths `['starters.home_starter.sample.limited.control', 'starters.home_starter.sample.rates.batters_faced', 'starters.home_starter.sample.thresholds.control', 'starters.home_starter.pitching_profile.command_label', 'starters.home_starter.sample.limited.strikeout', 'starters.home_starter.sample.thresholds.strikeout', 'starters.home_starter.pitching_profile.swing_miss_label', 'starters.home_starter.sample.rates.scope.label', 'starters.home_starter.sample.rates.scope.through']`: Control data for Connor Prielipp is limited with 36 batters faced against a threshold of 170, and his strikeout data is limited with 36 batters faced against a threshold of 70.
  - NLI (score_only) score `0.9941565990447998`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label']`: Dylan Cease shows above-average swing-and-miss ability.
  - Sentence evidence `['F110', 'F142', 'F210']`: Dylan Cease faces Connor Prielipp at Target Field
  - Sentence evidence `['F130', 'F138', 'F013', 'F018', 'F124']`: Dylan Cease enters with a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
  - Sentence evidence `['F162', 'F170']`: Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP over the same period.
  - Sentence evidence `['F001']`: Both teams look to capitalize on their respective offensive profiles against the opposing starter.
  - Sentence evidence `['F118', 'F150']`: The matchup features two starters looking to settle into the rotation.
  - Sentence evidence `['F110', 'F141', 'F186']`: Dylan Cease is a right-handed pitcher facing the Minnesota Twins lineup.
  - Sentence evidence `['F191', 'F192', 'F017', 'F194']`: The Minnesota Twins lineup has a .707 OPS (on-base plus slugging) against right-handed pitchers.
  - Sentence evidence `['F189', 'F190', 'F014', 'F187', 'F011']`: That group maintains a 23.8% K% (strikeout rate) and a 10.1% BB% (walk rate).
  - Sentence evidence `['F010']`: The Twins draw walks at an above-average rate.
  - Sentence evidence `['F142', 'F173', 'F176']`: Connor Prielipp is a left-handed pitcher facing the Toronto Blue Jays lineup.
  - Sentence evidence `['F181', 'F182', 'F184']`: The Toronto Blue Jays lineup has a .632 OPS against left-handed pitchers.
  - Sentence evidence `['F179', 'F177']`: They show a 16.2% K% and a 9.8% BB%.
  - Sentence evidence `['F009']`: The Blue Jays draw walks at an above-average rate.
  - Sentence evidence `['F117', 'F118']`: Dylan Cease has a 2026 regular season sample of 602 total pitches through May 1.
  - Sentence evidence `['F025', 'F036']`: He uses a four-seam fastball 36.9% of the time and a slider 28.4% of the time.
  - Sentence evidence `['F092', 'F093']`: His slider moves 0.6 in. sideways and 3.5 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F149', 'F150']`: Connor Prielipp has thrown 166 pitches in the same period.
  - Sentence evidence `['F041', 'F030']`: He uses his slider 47.0% of the time and his four-seam fastball 28.3% of the time.
  - Sentence evidence `['F107', 'F108']`: His slider moves -2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F005', 'F114']`: Watch whether Dylan Cease uses his slider to finish sequences.
  - Sentence evidence `['F007', 'F008']`: Watch how often Connor Prielipp relies on his slider to set up his four-seam fastball.
  - Sentence evidence `['F009', 'F010']`: Watch if the lineups maintain their walk rates against these pitchers.
  - Sentence evidence `['F120', 'F122', 'F128']`: Control data for Dylan Cease is limited as he has faced 138 batters and needs 170.
  - Sentence evidence `['F152', 'F153', 'F154', 'F160', 'F161']`: Control data for Connor Prielipp is limited with 36 batters faced against a threshold of 170, and his strikeout data is limited with 36 batters faced against a threshold of 70.
  - Sentence evidence `['F116']`: Dylan Cease shows above-average swing-and-miss ability.
- Length: rules 2365 characters; shown text 2365 characters.

### Rules text (A)

**Headline**

Four-seam-Slider starter against Slider-Four-seam starter

**Short summary**

- Dylan Cease brings this strength: Above-average swing-and-miss ability.
- Connor Prielipp brings this strength: Slider to set up, Four-seam to finish.
- The early what to watch is whether Dylan Cease can land the slider early in counts.

**Matchup Summary**

This matchup features Four-seam-Slider starter against Slider-Four-seam starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Dylan Cease vs Minnesota Twins**

Dylan Cease works off a four-seam-slider combination. He shows above-average swing-and-miss ability. Control data for Dylan Cease is limited (138 batters faced; 170 needed), so no command claim is made. Dylan Cease has allowed 0 home runs over 138 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.707 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Dylan Cease needs efficient strikes.

**Connor Prielipp vs Toronto Blue Jays**

Connor Prielipp works off a slider-four-seam combination. Strikeout data for Connor Prielipp is limited (36 batters faced; 70 needed), so no swing-and-miss claim is made. Control data for Connor Prielipp is limited (36 batters faced; 170 needed), so no command claim is made. Connor Prielipp has allowed 0 home runs over 36 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.632 OPS), which gives Connor Prielipp an edge if he gets ahead. They draw walks at an above-average rate, so Connor Prielipp needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Slider to finish versus Slider to set up, Four-seam to finish. The primary pitch contrast is Four-seam against Slider, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Dylan Cease land the slider early in counts?
- Can Connor Prielipp keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Dylan Cease and Connor Prielipp: all pitcher figures cover the 2026 regular season through May 1. Team offense splits cover the 2026 regular season through May 1. Samples below the minimum are flagged as limited and no claim is made from them.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 1 of 2, model `gemini-3.1-flash-lite`, gate checks ['W6.unsaid'], style findings ['S-1', 'S-2', 'W11.expansion', 'W17.length']

**Headline**

Dylan Cease starts for Toronto against Connor Prielipp and the Minnesota Twins

**Short summary**

- Dylan Cease carries a 2.87 ERA (earned run average) and a 1.37 WHIP (walks plus hits per inning) for the 2026 regular season through May 1.
- Connor Prielipp holds a 4.00 ERA and a 0.89 WHIP through the same period.
- The Toronto Blue Jays face the Minnesota Twins at Target Field.

**Matchup Summary**

All pitching and hitting figures in this report are from the 2026 regular season through May 1.

**Dylan Cease vs Minnesota Twins**

Dylan Cease shows above-average swing-and-miss ability. The Minnesota Twins lineup has a .707 OPS (on-base plus slugging) against right-handed pitchers. Their K% (strikeout rate) is 23.8% and their BB% (walk rate) is 10.1%. The Minnesota lineup draws walks at an above-average rate.

**Connor Prielipp vs Toronto Blue Jays**

The Toronto Blue Jays have a .632 OPS against left-handed pitchers. Their K% is 16.2% and their BB% is 9.8%. Toronto draws walks at an above-average rate. Connor Prielipp has a limited sample for strikeout data with 11 strikeouts in 36 batters faced, and 70 are needed for a read. His control data is also limited as he has faced 36 batters and 170 are needed for a read.

**Arsenal Scout**

Dylan Cease is a Four-seam-Slider starter who uses his Four-seam fastball to set up and his Slider to finish. His Four-seam fastball moves 3.7 in. sideways and 19.0 in. up compared with a pitch thrown without spin. Connor Prielipp is a Slider-Four-seam starter who uses his Slider to set up and his Four-seam fastball to finish. His Slider moves 2.4 in. sideways and 1.0 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how Dylan Cease uses his Four-seam fastball early in the count.
- Watch whether Connor Prielipp uses his Slider as a primary pitch.
- Watch how often both teams draw walks given their above-average rates.

**Data Confidence Note**

The data in this report is based on stats from the 2026 regular season through May 1.


## veteran-823940

- Outcome: **ACCEPTED (model text; style findings below)**
- Path: **primary**; content attempts: 1
- Content attempt 1: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks [], style findings ['S-2', 'S-4', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 14944, 'candidatesTokenCount': 1428, 'thoughtsTokenCount': 511, 'totalTokenCount': 16883}
  - style `S-4` token `features` in: This matchup features Shane McClanahan of the Rays and Shohei Ohtani of the Dodgers.
  - style `S-2` token `That group` in: That group draws walks at an above-average rate.
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1662` in: (whole report)
  - NLI (score_only) score `0.002819723915308714`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name']`: Shane McClanahan and Shohei Ohtani duel at the mound
  - NLI (score_only) score `None`, problem `unrenderable`, paths `['starters.away_starter.name', 'starters.home_starter.name', 'starters.away_starter.team', 'starters.home_starter.team']`: This matchup features Shane McClanahan of the Rays and Shohei Ohtani of the Dodgers.
  - NLI (score_only) score `0.004078151658177376`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: All statistics cover the 2026 regular season through 2026-06-16.
  - NLI (score_only) score `0.9949906468391418`, problem `None`, paths `['venue']`: The game takes place at UNIQLO Field at Dodger Stadium.
  - NLI (score_only) score `0.005542024038732052`, problem `None`, paths `['data_confidence.lineup_status']`: Both starters enter the game with similar roles as their team's starting pitchers.
  - NLI (score_only) score `0.9970530271530151`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Shane McClanahan carries a 3.23 ERA (earned run average) and a 1.17 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.9789364337921143`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label', 'starters.away_starter.pitching_profile.swing_miss_label']`: He shows average command and average swing-and-miss ability.
  - NLI (score_only) score `0.9968865513801575`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short']`: The Dodgers lineup has a .737 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9864548444747925`, problem `None`, paths `['findings.lineup_notes.home']`: That group has strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - NLI (score_only) score `0.9793683290481567`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.K%.short', 'glossary.BB%.short']`: Their K% (strikeout rate) is 20.6% and their BB% (walk rate) is 9.5%.
  - NLI (score_only) score `0.0012952893739566207`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Shohei Ohtani carries a 1.06 ERA and a 0.84 WHIP.
  - NLI (score_only) score `0.9857045412063599`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: He shows average command and above-average swing-and-miss ability.
  - NLI (score_only) score `0.9927533268928528`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The Rays lineup has a .734 OPS against right-handed pitchers.
  - NLI (score_only) score `0.9950201511383057`, problem `None`, paths `['findings.lineup_notes.away']`: That group draws walks at an above-average rate.
  - NLI (score_only) score `0.953014075756073`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: Their K% is 19.6% and their BB% is 10.1%.
  - NLI (score_only) score `0.9806466102600098`, problem `None`, paths `['starters.away_starter.pitching_profile.primary_pitch', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Shane McClanahan uses a four-seam as his primary pitch and a changeup as his put-away pitch (second most used pitch).
  - NLI (score_only) score `0.9574328064918518`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: His four-seam moves 9.1 in. sideways and 16.3 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.0021807265002280474`, problem `None`, paths `['starters.home_starter.pitching_profile.primary_pitch', 'starters.home_starter.pitching_profile.putaway_pitch']`: Shohei Ohtani uses a four-seam as his primary pitch and a sweeper as his put-away pitch.
  - NLI (score_only) score `0.9318801164627075`, problem `None`, paths `['pitch_movement.home_starter.Sweeper.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Sweeper.v_break']`: His sweeper moves 15.1 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.primary_pitch']`: Watch how often Shane McClanahan throws his four-seam.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Shohei Ohtani relies on his sweeper in two-strike counts.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home']`: Watch if the Dodgers lineup manages to walk against Shane McClanahan.
  - NLI (score_only) score `0.00047496260958723724`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.home_starter.sample.limited.arsenal']`: Data for both pitchers is based on a full sample of pitches.
  - Sentence evidence `['F001', 'F132', 'F164']`: Shane McClanahan and Shohei Ohtani duel at the mound
  - Sentence evidence `['F132', 'F164', 'F162', 'F194']`: This matchup features Shane McClanahan of the Rays and Shohei Ohtani of the Dodgers.
  - Sentence evidence `['F140', 'F172', 'F205', 'F215']`: All statistics cover the 2026 regular season through 2026-06-16.
  - Sentence evidence `['F238']`: The game takes place at UNIQLO Field at Dodger Stadium.
  - Sentence evidence `['F001']`: Both starters enter the game with similar roles as their team's starting pitchers.
  - Sentence evidence `['F152', 'F160', 'F013', 'F018']`: Shane McClanahan carries a 3.23 ERA (earned run average) and a 1.17 WHIP (walks plus hits per inning).
  - Sentence evidence `['F133', 'F138']`: He shows average command and average swing-and-miss ability.
  - Sentence evidence `['F214', 'F017']`: The Dodgers lineup has a .737 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F010']`: That group has strong OPS against this pitcher's hand and draws walks at an above-average rate.
  - Sentence evidence `['F212', 'F210', 'F014', 'F011']`: Their K% (strikeout rate) is 20.6% and their BB% (walk rate) is 9.5%.
  - Sentence evidence `['F184', 'F192']`: Shohei Ohtani carries a 1.06 ERA and a 0.84 WHIP.
  - Sentence evidence `['F165', 'F170']`: He shows average command and above-average swing-and-miss ability.
  - Sentence evidence `['F204']`: The Rays lineup has a .734 OPS against right-handed pitchers.
  - Sentence evidence `['F009']`: That group draws walks at an above-average rate.
  - Sentence evidence `['F202', 'F200']`: Their K% is 19.6% and their BB% is 10.1%.
  - Sentence evidence `['F135', 'F136', 'F022']`: Shane McClanahan uses a four-seam as his primary pitch and a changeup as his put-away pitch (second most used pitch).
  - Sentence evidence `['F108', 'F109']`: His four-seam moves 9.1 in. sideways and 16.3 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F167', 'F168']`: Shohei Ohtani uses a four-seam as his primary pitch and a sweeper as his put-away pitch.
  - Sentence evidence `['F129', 'F130']`: His sweeper moves 15.1 in. sideways and 3.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F135']`: Watch how often Shane McClanahan throws his four-seam.
  - Sentence evidence `['F168']`: Watch whether Shohei Ohtani relies on his sweeper in two-strike counts.
  - Sentence evidence `['F010']`: Watch if the Dodgers lineup manages to walk against Shane McClanahan.
  - Sentence evidence `['F141', 'F173']`: Data for both pitchers is based on a full sample of pitches.
- Length: rules 2095 characters; shown text 1673 characters.

### Rules text (A)

**Headline**

Four-seam-Changeup starter against Four-seam-Sweeper starter

**Short summary**

- Shane McClanahan brings this strength: Four-seam to set up, Changeup to finish.
- Shohei Ohtani brings this strength: Above-average swing-and-miss ability.
- The early what to watch is whether Shane McClanahan can land the changeup early in counts.

**Matchup Summary**

This matchup features Four-seam-Changeup starter against Four-seam-Sweeper starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Shane McClanahan vs Los Angeles Dodgers**

Shane McClanahan works off a four-seam-changeup combination. He shows average swing-and-miss ability. He shows average command. Shane McClanahan has allowed 3 home runs over 268 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against LHP pitching (.737 OPS), so Shane McClanahan cannot live over the middle. They draw walks at an above-average rate, so Shane McClanahan needs efficient strikes.

**Shohei Ohtani vs Tampa Bay Rays**

Shohei Ohtani works off a four-seam-sweeper combination. He shows above-average swing-and-miss ability. He shows average command. Shohei Ohtani has allowed 3 home runs over 262 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup is roughly average against RHP pitching (.734 OPS), with no glaring weakness to attack. They draw walks at an above-average rate, so Shohei Ohtani needs efficient strikes.

**Arsenal Scout**

The main contrast is Four-seam to set up, Changeup to finish versus Four-seam to set up, Sweeper to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Shane McClanahan land the changeup early in counts?
- Can Shohei Ohtani keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Shane McClanahan and Shohei Ohtani: all pitcher figures cover the 2026 regular season through Jun 16. Team offense splits cover the 2026 regular season through Jun 16.

### Model text (B1): accepted

Style findings recorded for S1 (never a reason to reject): `S-4` `features`, `S-2` `That group`, `W12.scope` `None`, `W17.length` `1662`

**Headline**

Shane McClanahan and Shohei Ohtani duel at the mound

**Short summary**

- This matchup features Shane McClanahan of the Rays and Shohei Ohtani of the Dodgers.
- All statistics cover the 2026 regular season through 2026-06-16.
- The game takes place at UNIQLO Field at Dodger Stadium.

**Matchup Summary**

Both starters enter the game with similar roles as their team's starting pitchers.

**Shane McClanahan vs Los Angeles Dodgers**

Shane McClanahan carries a 3.23 ERA (earned run average) and a 1.17 WHIP (walks plus hits per inning). He shows average command and average swing-and-miss ability. The Dodgers lineup has a .737 OPS (on-base plus slugging) against left-handed pitchers. That group has strong OPS against this pitcher's hand and draws walks at an above-average rate. Their K% (strikeout rate) is 20.6% and their BB% (walk rate) is 9.5%.

**Shohei Ohtani vs Tampa Bay Rays**

Shohei Ohtani carries a 1.06 ERA and a 0.84 WHIP. He shows average command and above-average swing-and-miss ability. The Rays lineup has a .734 OPS against right-handed pitchers. That group draws walks at an above-average rate. Their K% is 19.6% and their BB% is 10.1%.

**Arsenal Scout**

Shane McClanahan uses a four-seam as his primary pitch and a changeup as his put-away pitch (second most used pitch). His four-seam moves 9.1 in. sideways and 16.3 in. up compared with a pitch thrown without spin. Shohei Ohtani uses a four-seam as his primary pitch and a sweeper as his put-away pitch. His sweeper moves 15.1 in. sideways and 3.7 in. up compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Shane McClanahan throws his four-seam.
- Watch whether Shohei Ohtani relies on his sweeper in two-strike counts.
- Watch if the Dodgers lineup manages to walk against Shane McClanahan.

**Data Confidence Note**

Data for both pitchers is based on a full sample of pitches.


## veteran-822840

- Outcome: **REJECTED (the rules report is used)**
- Path: **rules** (reason: `checks_failed`); content attempts: 2
- Content attempt 1: transport path `primary_retry`, transport failures [('gemini-3.1-flash-lite', 1, 'http_503')], model `gemini-3.1-flash-lite`, gate checks ['W1.fact_id', 'W1.entity', 'W1.no_evidence', 'W1.number', 'W12.time'], style findings ['S-1', 'S-4', 'S-5', 'W11.expansion', 'W17.length'], tokens {'promptTokenCount': 14866, 'candidatesTokenCount': 1220, 'thoughtsTokenCount': 242, 'totalTokenCount': 16328}
  - gate `W1.fact_id` token `['F217', 'F219', 'F10']` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - gate `W1.entity` token `Arlington` in: Sean Manaea and MacKenzie Gore face off in Arlington
  - gate `W1.no_evidence` token `None` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - gate `W1.number` token `.766` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - gate `W12.time` token `The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - style `W11.expansion` token `ERA` in: Sean Manaea has a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning) in the 2026 regular season through Sep 21.
  - style `W11.expansion` token `WHIP` in: Sean Manaea has a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning) in the 2026 regular season through Sep 21.
  - style `W11.expansion` token `OPS` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - style `W11.expansion` token `K%` in: That group has a 23.7% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - style `W11.expansion` token `BB%` in: That group has a 23.7% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - style `W11.expansion` token `put-away pitch` in: Watch how often Sean Manaea uses his Sweeper as a put-away pitch (second most used pitch).
  - style `S-1` token `2026 regular season through Sep 21` in: Sean Manaea has a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning) in the 2026 regular season through Sep 21.
  - style `S-4` token `maintains` in: Watch if the Texas Rangers lineup maintains its OPS against left-handed pitchers.
  - style `S-5` token `Arlington` in: Sean Manaea and MacKenzie Gore face off in Arlington
  - style `W17.length` token `1490` in: (whole report)
  - NLI (score_only) score `0.0025722754653543234`, problem `None`, paths `['data_confidence.lineup_status', 'starters.away_starter.name', 'starters.home_starter.name', 'venue']`: Sean Manaea and MacKenzie Gore face off in Arlington
  - NLI (score_only) score `0.9460958242416382`, problem `None`, paths `['starters.away_starter.pitching_profile.style_label', 'starters.home_starter.pitching_profile.style_label']`: Sean Manaea and MacKenzie Gore both carry similar pitching profiles into the game.
  - NLI (score_only) score `0.03507769852876663`, problem `None`, paths `['teams.away.offense_profile.vs_pitcher_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.home.offense_profile.vs_pitcher_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Both teams are preparing their lineups to face left-handed starters.
  - NLI (score_only) score `0.8211377859115601`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: Data covers the 2026 regular season through Sep 21.
  - NLI (score_only) score `0.47398099303245544`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'starters.away_starter.season_summary.scopes.counts.label', 'starters.away_starter.season_summary.scopes.counts.through']`: Sean Manaea has a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning) in the 2026 regular season through Sep 21.
  - NLI (score_only) score `0.006142475176602602`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip', 'starters.home_starter.season_summary.scopes.counts.label', 'starters.home_starter.season_summary.scopes.counts.through']`: MacKenzie Gore enters with a 4.67 ERA and a 1.35 WHIP for that same period.
  - NLI (score_only) score `None`, problem `unrenderable`, paths `[]`: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - NLI (score_only) score `0.9886018633842468`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'teams.home.offense_profile.bb_rate_vs_hand']`: That group has a 23.7% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - NLI (score_only) score `0.9890024662017822`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.vs_pitcher_hand']`: The New York Mets offense shows a .682 OPS against left-handed starters.
  - NLI (score_only) score `0.8633919358253479`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: They carry a 23.1% K% and an 8.5% BB% in those situations.
  - NLI (score_only) score `0.015413707122206688`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_mix.1.away_starter.overall']`: Sean Manaea uses a Four-seam fastball 38.0% of the time and a Sweeper 30.8% of the time.
  - NLI (score_only) score `0.00371853681281209`, problem `None`, paths `['pitch_movement.away_starter.Four-seam.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Four-seam.v_break']`: He throws a Four-seam fastball that moves 13.3 in. sideways and 10.7 in. up compared with a pitch thrown without spin.
  - NLI (score_only) score `0.8508689403533936`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_mix.5.home_starter.overall']`: MacKenzie Gore relies on his Four-seam fastball at a 47.4% rate and his Curveball at an 18.0% rate.
  - NLI (score_only) score `0.43995413184165955`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Curveball.v_break']`: His Curveball moves 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['starters.away_starter.pitching_profile.putaway_pitch', 'pitch_mix.1.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Watch how often Sean Manaea uses his Sweeper as a put-away pitch (second most used pitch).
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.home_starter_strengths', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether MacKenzie Gore executes his plan of using a Four-seam fastball to set up and a Curveball to finish.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch if the Texas Rangers lineup maintains its OPS against left-handed pitchers.
  - NLI (score_only) score `0.004294548649340868`, problem `None`, paths `['starters.away_starter.sample.limited.arsenal', 'starters.home_starter.sample.limited.arsenal']`: Data for both starting pitchers is not limited.
  - Sentence evidence `['F001', 'F135', 'F167', 'F241']`: Sean Manaea and MacKenzie Gore face off in Arlington
  - Sentence evidence `['F140', 'F172']`: Sean Manaea and MacKenzie Gore both carry similar pitching profiles into the game.
  - Sentence evidence `['F209', 'F219']`: Both teams are preparing their lineups to face left-handed starters.
  - Sentence evidence `['F143', 'F175']`: Data covers the 2026 regular season through Sep 21.
  - Sentence evidence `['F155', 'F163', 'F159']`: Sean Manaea has a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning) in the 2026 regular season through Sep 21.
  - Sentence evidence `['F187', 'F195', 'F191']`: MacKenzie Gore enters with a 4.67 ERA and a 1.35 WHIP for that same period.
  - Sentence evidence `['F217', 'F219', 'F10']`: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers.
  - Sentence evidence `['F215', 'F213']`: That group has a 23.7% K% (strikeout rate) and an 8.8% BB% (walk rate).
  - Sentence evidence `['F207', 'F209']`: The New York Mets offense shows a .682 OPS against left-handed starters.
  - Sentence evidence `['F205', 'F203']`: They carry a 23.1% K% and an 8.5% BB% in those situations.
  - Sentence evidence `['F025', 'F036']`: Sean Manaea uses a Four-seam fastball 38.0% of the time and a Sweeper 30.8% of the time.
  - Sentence evidence `['F108', 'F109']`: He throws a Four-seam fastball that moves 13.3 in. sideways and 10.7 in. up compared with a pitch thrown without spin.
  - Sentence evidence `['F030', 'F085']`: MacKenzie Gore relies on his Four-seam fastball at a 47.4% rate and his Curveball at an 18.0% rate.
  - Sentence evidence `['F120', 'F121']`: His Curveball moves 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F139', 'F036']`: Watch how often Sean Manaea uses his Sweeper as a put-away pitch (second most used pitch).
  - Sentence evidence `['F007', 'F171']`: Watch whether MacKenzie Gore executes his plan of using a Four-seam fastball to set up and a Curveball to finish.
  - Sentence evidence `['F217']`: Watch if the Texas Rangers lineup maintains its OPS against left-handed pitchers.
  - Sentence evidence `['F144', 'F176']`: Data for both starting pitchers is not limited.
- Content attempt 2: transport path `primary`, transport failures none, model `gemini-3.1-flash-lite`, gate checks ['W8.form'], style findings ['W11.expansion', 'W12.scope', 'W17.length'], tokens {'promptTokenCount': 15088, 'candidatesTokenCount': 797, 'thoughtsTokenCount': 2978, 'totalTokenCount': 18863}
  - gate `W8.form` token `None` in: Manaea moves his Sweeper 12.5 in. sideways and 1.3 in. up compared with a pitch thrown without spin (Break: total movement).
  - gate `W8.form` token `None` in: Gore moves his Curveball 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.
  - style `W11.expansion` token `Break` in: Manaea moves his Sweeper 12.5 in. sideways and 1.3 in. up compared with a pitch thrown without spin (Break: total movement).
  - style `W11.expansion` token `LHH / RHH` in: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers (LHH / RHH).
  - style `W12.scope` token `None` in: (whole report)
  - style `W17.length` token `1315` in: (whole report)
  - NLI (score_only) score `0.3318973183631897`, problem `None`, paths `['starters.away_starter.name', 'starters.home_starter.name']`: Sean Manaea starts for the New York Mets against MacKenzie Gore of the Texas Rangers.
  - NLI (score_only) score `0.9701353311538696`, problem `None`, paths `['starters.away_starter.season_summary.era', 'starters.away_starter.season_summary.scopes.season_rates.label', 'starters.away_starter.season_summary.scopes.season_rates.through', 'starters.away_starter.season_summary.whip', 'glossary.ERA.short', 'glossary.WHIP.short']`: Manaea enters with a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning).
  - NLI (score_only) score `0.0008823432144708931`, problem `None`, paths `['starters.home_starter.season_summary.era', 'starters.home_starter.season_summary.scopes.season_rates.label', 'starters.home_starter.season_summary.scopes.season_rates.through', 'starters.home_starter.season_summary.whip']`: Gore has a 4.67 ERA and a 1.35 WHIP.
  - NLI (score_only) score `0.011779743246734142`, problem `None`, paths `['starters.away_starter.pitching_profile.swing_miss_label', 'starters.home_starter.pitching_profile.swing_miss_label']`: Both pitchers show average swing-and-miss ability.
  - NLI (score_only) score `0.9957029223442078`, problem `None`, paths `['starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: This report uses data from the 2026 regular season through 2026-09-21.
  - NLI (score_only) score `0.9392926096916199`, problem `None`, paths `['pitch_mix.0.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through']`: Sean Manaea uses his Four-seam fastball 38.0% of the time.
  - NLI (score_only) score `0.9653850197792053`, problem `None`, paths `['starters.away_starter.pitching_profile.command_label']`: He shows solid command.
  - NLI (score_only) score `0.9938908815383911`, problem `None`, paths `['teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.OPS.short', 'glossary.LHH / RHH.short']`: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers (LHH / RHH).
  - NLI (score_only) score `0.9309554696083069`, problem `None`, paths `['teams.home.offense_profile.k_rate_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through', 'glossary.K%.short', 'teams.home.offense_profile.bb_rate_vs_hand', 'glossary.BB%.short']`: The Texas offense has a 23.7% strikeout rate (K%) and an 8.8% walk rate (BB%).
  - NLI (score_only) score `0.1296408772468567`, problem `None`, paths `['pitch_mix.0.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through']`: MacKenzie Gore uses his Four-seam fastball 47.4% of the time.
  - NLI (score_only) score `0.9071234464645386`, problem `None`, paths `['starters.home_starter.pitching_profile.command_label']`: He shows average command.
  - NLI (score_only) score `0.9915464520454407`, problem `None`, paths `['teams.away.offense_profile.ops_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through']`: The New York Mets lineup has a .682 OPS against left-handed pitchers.
  - NLI (score_only) score `0.9931949377059937`, problem `None`, paths `['teams.away.offense_profile.k_rate_vs_hand', 'teams.away.offense_profile.scope.label', 'teams.away.offense_profile.scope.through', 'teams.away.offense_profile.bb_rate_vs_hand']`: This group carries a 23.1% K% and an 8.5% BB%.
  - NLI (score_only) score `0.9874740839004517`, problem `None`, paths `['pitch_movement.away_starter.Sweeper.h_break', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'pitch_movement.away_starter.Sweeper.v_break', 'glossary.Break.short']`: Manaea moves his Sweeper 12.5 in. sideways and 1.3 in. up compared with a pitch thrown without spin (Break: total movement).
  - NLI (score_only) score `0.9736234545707703`, problem `None`, paths `['pitch_movement.home_starter.Curveball.h_break', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'pitch_movement.home_starter.Curveball.v_break']`: Gore moves his Curveball 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.1.away_starter.overall', 'starters.away_starter.sample.arsenal.scope.label', 'starters.away_starter.sample.arsenal.scope.through', 'starters.away_starter.pitching_profile.putaway_pitch', 'glossary.put-away pitch.short']`: Watch how often Manaea throws his Sweeper as his put-away pitch (second most used pitch).
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['pitch_mix.5.home_starter.overall', 'starters.home_starter.sample.arsenal.scope.label', 'starters.home_starter.sample.arsenal.scope.through', 'starters.home_starter.pitching_profile.putaway_pitch']`: Watch whether Gore relies on his Curveball as his put-away pitch.
  - NLI (score_only) score `None`, problem `not_applicable`, paths `['findings.lineup_notes.home', 'teams.home.offense_profile.ops_vs_hand', 'teams.home.offense_profile.scope.label', 'teams.home.offense_profile.scope.through']`: Watch if the Texas Rangers lineup exploits its strong OPS against left-handed pitchers.
  - NLI (score_only) score `0.6263406872749329`, problem `None`, paths `['data_confidence.lineup_status']`: Probable pitchers are confirmed for this game.
  - Sentence evidence `['F135', 'F167']`: Sean Manaea starts for the New York Mets against MacKenzie Gore of the Texas Rangers.
  - Sentence evidence `['F155', 'F163', 'F013', 'F018']`: Manaea enters with a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning).
  - Sentence evidence `['F187', 'F195']`: Gore has a 4.67 ERA and a 1.35 WHIP.
  - Sentence evidence `['F141', 'F173']`: Both pitchers show average swing-and-miss ability.
  - Sentence evidence `['F143']`: This report uses data from the 2026 regular season through 2026-09-21.
  - Sentence evidence `['F025']`: Sean Manaea uses his Four-seam fastball 38.0% of the time.
  - Sentence evidence `['F136']`: He shows solid command.
  - Sentence evidence `['F217', 'F017', 'F016']`: The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers (LHH / RHH).
  - Sentence evidence `['F215', 'F014', 'F213', 'F011']`: The Texas offense has a 23.7% strikeout rate (K%) and an 8.8% walk rate (BB%).
  - Sentence evidence `['F030']`: MacKenzie Gore uses his Four-seam fastball 47.4% of the time.
  - Sentence evidence `['F168']`: He shows average command.
  - Sentence evidence `['F207']`: The New York Mets lineup has a .682 OPS against left-handed pitchers.
  - Sentence evidence `['F205', 'F203']`: This group carries a 23.1% K% and an 8.5% BB%.
  - Sentence evidence `['F114', 'F115', 'F012']`: Manaea moves his Sweeper 12.5 in. sideways and 1.3 in. up compared with a pitch thrown without spin (Break: total movement).
  - Sentence evidence `['F120', 'F121']`: Gore moves his Curveball 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.
  - Sentence evidence `['F036', 'F139', 'F022']`: Watch how often Manaea throws his Sweeper as his put-away pitch (second most used pitch).
  - Sentence evidence `['F085', 'F171']`: Watch whether Gore relies on his Curveball as his put-away pitch.
  - Sentence evidence `['F010', 'F217']`: Watch if the Texas Rangers lineup exploits its strong OPS against left-handed pitchers.
  - Sentence evidence `['F001']`: Probable pitchers are confirmed for this game.
- Length: rules 1909 characters; shown text 1909 characters.

### Rules text (A)

**Headline**

Four-seam-Sweeper starter against Four-seam-Curveball starter

**Short summary**

- Sean Manaea brings this strength: Solid command supports strike-zone control.
- MacKenzie Gore brings this strength: Four-seam to set up, Curveball to finish.
- The early what to watch is whether Sean Manaea can land the sweeper early in counts.

**Matchup Summary**

This matchup features Four-seam-Sweeper starter against Four-seam-Curveball starter. The scouting note is matchup fit, with each pressure point shaping what to watch.

**Sean Manaea vs Texas Rangers**

Sean Manaea works off a four-seam-sweeper combination. He shows average swing-and-miss ability. He shows solid command. Sean Manaea has allowed 23 home runs over 601 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup hits well against LHP pitching (.766 OPS), so Sean Manaea cannot live over the middle.

**MacKenzie Gore vs New York Mets**

MacKenzie Gore works off a four-seam-curveball combination. He shows average swing-and-miss ability. He shows average command. MacKenzie Gore has allowed 19 home runs over 720 batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample. This lineup has struggled against LHP pitching (.682 OPS), which gives MacKenzie Gore an edge if he gets ahead.

**Arsenal Scout**

The main contrast is Four-seam to set up, Sweeper to finish versus Four-seam to set up, Curveball to finish. The primary pitch contrast is Four-seam against Four-seam, a scouting note for matchup fit and each pressure point.

**Three Things to Watch**

- Can Sean Manaea land the sweeper early in counts?
- Can MacKenzie Gore keep the ball in the zone?
- Which lineup forces more deep counts by the third inning?

**Data Confidence Note**

This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits. Lineups can still change before first pitch. Sean Manaea and MacKenzie Gore: all pitcher figures cover the 2026 regular season through Sep 21. Team offense splits cover the 2026 regular season through Sep 21.

### Model text (B1): rejected, not published. Shown: the attempt with the fewest failed gate checks, content attempt 2 of 2, model `gemini-3.1-flash-lite`, gate checks ['W8.form'], style findings ['W11.expansion', 'W12.scope', 'W17.length']

**Headline**

Sean Manaea starts for the New York Mets against MacKenzie Gore of the Texas Rangers.

**Short summary**

- Manaea enters with a 4.74 ERA (earned run average) and a 1.32 WHIP (walks plus hits per inning).
- Gore has a 4.67 ERA and a 1.35 WHIP.
- Both pitchers show average swing-and-miss ability.

**Matchup Summary**

This report uses data from the 2026 regular season through 2026-09-21.

**Sean Manaea vs Texas Rangers**

Sean Manaea uses his Four-seam fastball 38.0% of the time. He shows solid command. The Texas Rangers lineup has a .766 OPS (on-base plus slugging) against left-handed pitchers (LHH / RHH). The Texas offense has a 23.7% strikeout rate (K%) and an 8.8% walk rate (BB%).

**MacKenzie Gore vs New York Mets**

MacKenzie Gore uses his Four-seam fastball 47.4% of the time. He shows average command. The New York Mets lineup has a .682 OPS against left-handed pitchers. This group carries a 23.1% K% and an 8.5% BB%.

**Arsenal Scout**

Manaea moves his Sweeper 12.5 in. sideways and 1.3 in. up compared with a pitch thrown without spin (Break: total movement). Gore moves his Curveball 3.4 in. sideways and 11.8 in. down compared with a pitch thrown without spin.

**Three Things to Watch**

- Watch how often Manaea throws his Sweeper as his put-away pitch (second most used pitch).
- Watch whether Gore relies on his Curveball as his put-away pitch.
- Watch if the Texas Rangers lineup exploits its strong OPS against left-handed pitchers.

**Data Confidence Note**

Probable pitchers are confirmed for this game.


## Calibration note: the rules text of veteran-824027 through the word-level checks

Not a defect list. These are the words and shapes the word-level checks flag in the text the rules writer publishes today. Whether each would be a violation depends on citations (a comparison word is allowed when both values are quoted; a sentence-opening question word is a limit of the entity heuristic). The checks that need citations were not run.

- `W1.entity`: 'Can José Soriano', 'Can Kyle Freeland', 'Statcast'
- `W10.cause`: 'because', 'so'
- `W15.question`: '?'
- `W16.internal`: 'fetched', 'snapshot'
- `W2.comparison`: 'larger', 'more', 'versus'

