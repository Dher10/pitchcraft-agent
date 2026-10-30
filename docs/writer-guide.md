# PitchCraft writer guide (version 0.3, written to the owner's review of 2026-10-30; the short forms of section 5 await approval)

Status: version 0.1 was drafted on Oct 30 from the frozen dev packets only (`evals/data/dataset/packets/dev`, manifest `0d906f78d42ab013568be535db1716fd329d72033a002a414b1f29625bdc4a25`); the owner approved it as version 0.2 the same day with nine changes, all applied below. No test-split packet, finding or output was opened. The guide and the prompt are versioned together; the SHA-256 of this file, recorded in `docs/STATUS.md` and pinned by a test, is the guide digest.

Version 0.3 (owner review of the ten B1 dev examples): a term with a short form gets it in parentheses on first use instead of a definition (W11); a scope is stated once per section (W12); labels may be written in lowercase inside a sentence and a hyphenated intensity word counts as the intensity word (W5); the word checks are denylists (section 6); section 4 adds a pair of natural prose that meets every rule.

**The LLM writer follows W1 to W17 strictly, with no exemptions.** It does not imitate the rules writer's phrasing. The rules writer's catalog sentences (for example "gives X an edge if he gets ahead", "needs efficient strikes", and the "because ... needs a far larger sample" sentence) are judgment phrasing or use a cause word, and they are not allowed for the LLM (the last one is restated without a cause word). That A (rules) and B (LLM) differ in style is the point of the experiment.

Requirements come from `docs/plans/P2.md` ("Writer guide prerequisite"), `docs/eval-spec.md` sections 3 and 4, D44/D45 and `docs/DATA_CONTRACT.md`.

## 1. Who you write for and how

You write the prose of a matchup report for a casual baseball fan: someone who knows the game but not the statistics. They want to understand the duel and know what to watch.

- Plain words, short sentences, one idea per sentence. The hard sentence cap of the validator is 300 characters; aim far below it.
- Plain text only. No HTML, no markdown, no links, no emoji, no invisible characters (D45).
- Neutral and factual about real people. No jokes, nicknames, character judgments or praise or blame beyond what a labeled figure supports.
- Treat both starters, and both lineups, the same way: same kinds of facts, same order, same care with limits.
- Every sentence that states a fact points to its evidence (packet path and the value you cite). A sentence with no evidence states no fact.

## 2. What you receive

The Matchup Analyst's findings and a subset of the packet: the game, the series object (postseason only), both starters (`season_summary`, `pitching_profile`, `sample`), both lineups (`teams.*.offense_profile`), the pitch mix, velocity and movement, and the approved glossary (section 5). Every figure is already computed by Python. Every figure carries its scope (`through` date).

You do not receive, and must not use: anything about this game's result, the news, injuries, history, other seasons, other players, or anything you know from outside the packet, even if it is true.

## 3. Rules

Each rule has a stable ID (S1 scores each one pass or fail per report) and the condition under which it applies.

| ID | Rule | Applies |
|---|---|---|
| W1 | Only facts in the packet. Entities (players, teams, pitches) and numbers must appear in the evidence you cite. A true fact that is not in the packet is a failure (R1). | always |
| W2 | You never calculate. Do not add, subtract, average, rank, round, convert or work out any difference, ratio or total. Quote a computed figure as given, or do not use it. The only comparison allowed is a comparison word (more, less, faster, slower, higher, lower) in a sentence that quotes both values, with the same scope (see W9), so code can verify it. No other arithmetic, and no words that state arithmetic (twice, double, half, times). | always |
| W3 | No predictions, outcomes, odds, win probability or betting language, and no "will", "should win", "expected to", "likely to". Things to watch (W15) are statements, not forecasts, and never name an outcome. | always |
| W4 | Forbidden topics stay forbidden even if some field contains them: injuries, personal life, history, awards, contracts, rumors, other seasons. | always |
| W5 | Intensity words ("strong", "weak", "above average", "elite") only as the packet's own labels (`pitching_profile.*_label`, D24/D25) and the lineup notes of the findings (D32/D50). Never a stronger adjective, never a percentile, never a league comparison you invented. A claim about command, swing-and-miss or contact risk is made only with the packet's own label for it (`command_label`, `swing_miss_label`, `contact_risk_label`), never from your own reading of the figures. Labels are compared without regard to case and may be written in lowercase inside a sentence ("shows solid command"); a word joined to an intensity word by a hyphen ("elite-level") counts as that word. | a label is non-null |
| W6 | A dimension flagged limited (`sample.limited.<dimension> == true`) gets no claim. Say it is limited, with the counts the findings give (batters faced and the number needed). A missing label stays missing; do not fill it with a guess. | a limited flag, or a null label |
| W7 | A measured zero stays a measured zero ("threw none of this pitch"). A missing value is "not available", never zero. A pitch whose family is unmapped, or a starter whose arsenal is limited, gets no description of his pitch shapes. | zero, null, unmapped or limited arsenal |
| W8 | Movement says only what was measured: "Moves {h} in. sideways and {v} in. {up\|down} compared with a pitch thrown without spin." Never deception, "nasty", "unhittable", or any effect on hitters inferred from movement. Never arm side or glove side. | movement is shown |
| W9 | Compare two pitches or two starters only when both have a measured value for it, from the same scope, and only with a comparison word of W2 in one sentence that quotes both values and cites both paths. Two values with different scope labels are never compared. | any comparison |
| W10 | No cause words ("because", "due to", "thanks to", "as a result", "since", "so that") unless the packet states that cause. Say what is missing without a cause: "There is not enough data yet to rate his home-run risk." | always |
| W11 | A statistical term that has a short form in the glossary (section 5) gets that short form in parentheses right after its first use in the report, once per report, and the sentence cites `glossary.<term>.short`: "OPS (on-base plus slugging)". Never write a glossary definition into the prose, and never "X is <definition>". A term with no short form (batters faced, swing-and-miss, command, limited sample) needs no explanation. Do not use a statistic the glossary lacks. | a term is used |
| W12 | Say what each group of figures covers, with the scope the packet gives ("2026 regular season through Aug 6"): once per section, or once for both starters when their scope is identical, never in every sentence. No "recently", "lately", "tonight", "today", "this week" or any time claim the evidence does not carry. | always |
| W13 | Series (postseason): state only `series.standing` as the standing before first pitch, the game number and the series name. Never this game's result, a clinching or elimination claim, or anything after first pitch. Game 1 has no prior result: say the series has not started, or say nothing. | `series` is not null |
| W14 | Cover both starters and both lineups: the primary and put-away pitch of each starter when available, and each lineup's read when available. If a read is unavailable or limited, say so in the same place a read would have gone. | always |
| W15 | End with concrete things to watch, written as statements that start with "Watch how" or "Watch whether", tied to packet facts (a pitch, a count, a lineup tendency), for example "Watch how often {pitcher} throws his {pitch}." Never a question, and never name an outcome (no result, no win, no strikeout or hit as something that will or should happen). | always |
| W16 | Do not mention the data fetch, the build, the dataset, case ids, the model, or this guide. The fetch note that packets carry (`data_confidence.notes`) is removed from what you receive and is never used. | always |
| W17 | Length and structure. Write the same sections, in the same order, as the rules writer's report: a headline, three summary lines and six sections (summary; the away starter against the home lineup; the home starter against the away lineup; arsenal; what to watch; confidence). The titles are fixed by code. The total length of your report, counted in characters of all its text, is within 20% above or below the rules writer's report for the same case. | always |

## 4. Examples from real dev packets

The "Good" sentences of pairs 2 and 3 are sentences the rules-based writer actually produced for that dev case (`findings/dev/<case>.json`), quoted unchanged; they comply with the rules and are shown for the facts they carry, not as phrasing to copy. Each pair is an excerpt: a term used in it (batters faced, command, swing-and-miss) is defined once elsewhere in the same report under W11. The "Good" sentences of pairs 1, 4 and 5 are **constructed** from the packet's own fields, because the rules writer's sentence for those facts uses phrasing that W3, W10 or W17 do not allow the LLM. Each "Bad" is not model output: no LLM output existed when this was written, so each was **constructed** as a minimal edit of a good sentence that breaks one rule (owner decision 6 in section 7: constructed examples stay, labeled constructed; real B1 failures may be added in a new guide version after the ten B1 dev examples and before any test-split run).

### Pair 1: a limited sample (W6, W5), `limited-823836`

- Evidence: `starters.away_starter.sample.limited.control = true`, `.limited.strikeout = true`, `.rates.batters_faced = 32`, `.thresholds.control = 170`, `.thresholds.strikeout = 70`; `season_summary.walks = 10`; `pitching_profile.command_label = null`, `.swing_miss_label = null`.
- Good (constructed from these fields): "Control data for George Klassen is limited: 32 batters faced, and 170 are needed for a read. There is not enough data yet to rate his command."
- Bad (constructed): "George Klassen has poor control: he walked 10 batters."
- Why it fails: control is flagged limited and has no label, so any command claim breaks W6 and W5; "poor" is an intensity word that is not a packet label (W5). The count of 10 walks is real, but a count does not license a rating on a limited sample.

### Pair 2: intensity words only from labels, both starters alike (W5, W14), `veteran-824027`

- Evidence: `starters.away_starter.pitching_profile.swing_miss_label = "Average swing-and-miss ability"`, `.command_label = "Solid command"`; `starters.home_starter.pitching_profile.swing_miss_label = "Above-average swing-and-miss ability"`, `.command_label = "Below-average command"`.
- Good: "He shows average swing-and-miss ability. He shows solid command." (Freeland) and "He shows above-average swing-and-miss ability. He shows below-average command." (Soriano)
- Bad (constructed): "Soriano is a strikeout machine, while Freeland just pitches to contact."
- Why it fails: "strikeout machine" is a stronger adjective than the label (W5); "pitches to contact" is a claim no field supports (W1); the two starters are described with different kinds of facts (W14).

### Pair 3: the series standing, nothing after first pitch (W13, W3), `postseason-849842`

- Evidence: `series.series_name = "NL Wild Card Series"`, `series.game_number = 2`, `series.games_in_series = 3`, `series.standing = "SD leads 1-0"`. (The game is Game 2 of a three-game series, so the standing is the only prior result.)
- Good (real rules sentence, `findings/dev/postseason-849842.json`): "This is Game 2 of the NL Wild Card Series. Before first pitch, SD leads 1-0."
- Bad (constructed): "SD can finish the series today, and Chicago must win to stay alive."
- Why it fails: "can finish", "must win" and "stay alive" are outcome and forecast language (W3, W13), and "today" is a time claim the packet does not carry (W12). The standing is true, but the elimination framing is not in the evidence.

### Pair 4: a term gets its short form once (W11, W12), `opener-823164`

- Evidence: `teams.home.offense_profile.ops_vs_hand = ".660"`, `.vs_pitcher_hand = "LHP"`, `.scope.label = "2026 regular season through Sep 26"`; glossary entry OPS (section 5).
- Good (constructed from these fields plus the approved short form): "Against left-handed pitchers this lineup has a .660 OPS (on-base plus slugging) over the 2026 regular season through Sep 26."
- Bad (constructed): "Their elite OPS lately shows they feast on lefties."
- Why it fails: "elite" is not a label (W5); "lately" is a time claim (W12); OPS is used with no short form (W11); "feast" is a claim about outcomes with no evidence (W1).
- Note: the rules writer's sentence for the same facts says "which gives Jack Dreyer an edge if he gets ahead". That is judgment phrasing and is not allowed for the LLM.

### Pair 5: movement states a measurement, not a verdict (W8, W7), `veteran-824027`

- Evidence: `charts.pitch_movement.home_starter.Curveball = {family: "Breaking", h_break: 12.5, v_break: -6.5}`; the arsenal of José Soriano is not limited (`sample.limited.arsenal = false`).
- Good (constructed from the approved form "Moves {h} in. sideways and {v} in. {up|down} compared with a pitch thrown without spin." filled with the packet values): "Moves 12.5 in. sideways and 6.5 in. down compared with a pitch thrown without spin."
- Bad (constructed): "His curveball dives away from right-handed hitters and fools them."
- Why it fails: "away from right-handed hitters" uses an unverified side convention (W8); "fools them" infers deception and an effect on hitters from movement alone (W8, W1). No hitter-side result is in the packet.

### Pair 6: natural prose that meets every rule (W1 to W17), `veteran-824027`

- Note: this case is also one of the ten B1 dev examples. The prose cannot be copied, because every number must be a value cited from that case's own data; only its style is shared.
- Evidence: the cited paths of each sentence in the away starter section of the hand-written ideal report kept with the project files (ERA, WHIP, labels, the OPS, K% and BB% of the home lineup, its lineup notes).
- Good (hand-written for this guide, constructed from the packet, not model output): "Kyle Freeland carries an 8.08 ERA (earned run average) and a 1.75 WHIP (walks plus hits per inning) over the 2026 regular season through May 31. He shows solid command and average swing-and-miss ability. The Angels lineup has a .712 OPS (on-base plus slugging) against left-handed pitchers like him. Their K% (strikeout rate) is 24.3% and their BB% (walk rate) is 10.4% in that matchup. That group draws walks at an above-average rate and carries an elevated swing-and-miss risk."
- Why it works: each short form appears once, in parentheses, where the term first appears (W11); the scope appears once in the section (W12); labels are lowercase inside sentences (W5); every number is a cited value (W1, W2); sentences vary in length and opening.
- Bad (constructed): "Kyle Freeland has an 8.08 ERA. ERA is earned run average: earned runs allowed per nine innings. Lower is better. Over the 2026 regular season through May 31 he has a 1.75 WHIP over the 2026 regular season through May 31."
- Why it fails: the definition is written into the prose and the scope is repeated (W11, W12).

## 5. Glossary (the meanings behind the terms; the short forms are what you write)

The glossary is frozen in its own file, `evals/data/dataset/glossary.json` (version 1.1), with its own SHA-256 (`glossary.lock`), and the identical file is given to A, B1 and B2. A test checks that the file and this table say the same. Entity checks compare names after Unicode NFC normalization. The meanings are given to you so you understand each term; you do not write them into the prose. On the first use of a term that has a short form, write the term followed by the short form in parentheses, once per report. The first eight rows' meanings already ship to fans as tooltips (`components/Tooltip.tsx`, `docs/DATA_CONTRACT.md` 3.3); the short forms are proposed in version 1.1 and await the owner's approval.

| Term | Short form | Meaning |
|---|---|---|
| ERA | earned run average | Earned run average: earned runs allowed per nine innings. Lower is better. |
| WHIP | walks plus hits per inning | Walks plus hits per inning pitched. Lower is better. |
| K | strikeouts | Strikeouts. |
| OPS | on-base plus slugging | On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. |
| K% | strikeout rate | Share of plate appearances that end in a strikeout. |
| BB% | walk rate | Share of plate appearances that end in a walk. |
| Break | total movement | Total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin. |
| LHH / RHH | left-handed and right-handed hitters | Left-handed hitters / right-handed hitters. |
| batters faced | (none) | The number of hitters a pitcher has pitched to. |
| swing-and-miss | (none) | How often hitters swing and miss against him. |
| command | (none) | How well a pitcher puts the ball where he wants it. |
| put-away pitch | second most used pitch | In this report, the pitch he uses second most (at least 15% of his pitches). |
| limited sample | (none) | Too few pitches or batters faced for a reliable read; the packet says how many are needed. |

Backlog (owner decision pending): the term "put-away" does not match its common meaning (the pitch thrown with two strikes). Rename it, or compute true two-strike usage, later; `docs/STATUS.md` lists it.

## 6. How a report is checked (so you know what fails)

Code checks every cited path, value, entity (a canonical name or an alias built from the packet, after NFC normalization) and number (G1, R1), and the short-form, scope, comparison, cause-word, time-word, question and length rules (W2, W9, W10, W11, W12, W15, W17); a local text-entailment model checks each sentence against the packet's fact sentences; a judge scores G2, L1, U1, R1 and, rule by rule, this guide (S1). A sentence the checks cannot trace to evidence is rejected, and after one informed retry the rules writer's text is published instead. Schema-valid output alone proves nothing. The word checks (W2, W3, W4, W5, W10, W12, W15) are denylists: a sentence can pass them and still be wrong or awkward, which is why the entailment model and the judge are later layers and why the owner reads examples. Failed checks are reported per sentence with the check and the offending token. Limits of the entity check, disclosed: it sees capitalized names only (a lowercase "dodgers" is invisible to it); a capitalized word that appears in a non-name string of the packet (a month in a scope label, a label, a pitch name) is accepted on its own; a city alias is accepted whenever the opponent is from another city, though the city may name two teams in the league; sentence-opening words are accepted from a closed list of plain English openers.

## 7. Owner decisions on version 0.1 (2026-10-30)

1. **Rules-writer phrasing.** The LLM follows W1 to W17 strictly, without exemptions, and does not imitate the rules writer. Applied in the status paragraph and in pair 4.
2. **W2/W9 conflict.** Comparison words only when both values are quoted in one sentence with the same scope; no other arithmetic. Applied in W2 and W9.
3. **W3/W15 conflict.** Things to watch are "Watch how/whether ..." statements, never questions, never an outcome. Applied in W3 and W15.
4. **Length and structure.** Same sections as the rules writer; total length within 20% of its report for the same case. Added as W17.
5. **Glossary.** The wording of section 5, in its own frozen file with its own digest, identical for A, B1 and B2; NFC for entity checks. The "put-away" naming question is a backlog item in `docs/STATUS.md`.
6. **Constructed bad examples** stay, labeled constructed. Real failures may be added in a new guide version after the ten B1 dev examples, before any test-split run.
7. **The fetch note in the packets** (`data_confidence.notes`: "Live snapshot fetched ... for <case id>"). The packets are not re-frozen; the writer-input projection of P2.2 removes the field, identically for A, B1 and B2, and its tests prove it.
8. **Postseason season lines.** Checked read-only, with no request: the daily job's season line comes from `fetch_pitcher_season_stats` (`stats=byDateRange`), whose docstring records that both `stats=season` and `byDateRange` leave out postseason games (checked on 2026-10-10: 12.2 postseason IP did not appear in a 162.2 IP line). The daily job and the packets therefore share the regular-season-only scope, and the scope label says so. They do not differ, so there is no backlog item.
9. **Opener stratum.** Unchanged: the "opener" cases are starters with short recent outings; the schedule opener flag was not read. The guide says nothing about openers or bullpen games.

## 8. Owner decisions for version 0.3 (2026-10-30, review of the ten B1 dev examples)

1. **Short forms replace inline definitions.** Glossary 1.1 adds a short form per term (section 5); the prose never carries a definition (W11).
2. **Scope once per section** (W12). **Labels** may be lowercase inside a sentence and a hyphenated intensity word counts (W5).
3. **Entity aliases** are built per case from the packet only: a starter's last name; a team's nickname, its city when the other team does not share it, and its abbreviation. The entity check accepts the canonical names and these aliases, and nothing else.
4. **Word checks are denylists** with the entailment model and the judge as later layers (section 6).
5. **Natural prose.** Pair 6 shows what meets every rule and still reads like a person wrote it; style rules beyond the checks are proposed for version 0.4 after the re-run.
