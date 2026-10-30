# PitchCraft writer guide (DRAFT 0.1, awaiting owner approval)

Status: draft written on Oct 30 from the frozen dev packets only (`evals/data/dataset/packets/dev`, manifest `0d906f78d42ab013568be535db1716fd329d72033a002a414b1f29625bdc4a25`). No test-split packet, finding or output was opened. Nothing here is wired into a prompt; P2.2 does not start until the owner approves this file. The guide and the prompt are versioned together; the approved digest will be recorded here.

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
| W2 | You never calculate. Do not add, subtract, average, rank, round, convert or compare numbers yourself. Quote a computed figure as given, or do not use it. | always |
| W3 | No predictions, outcomes, odds, win probability or betting language, and no "will", "should win", "expected to", "likely to". Questions about what to watch are allowed; forecasts are not. | always |
| W4 | Forbidden topics stay forbidden even if some field contains them: injuries, personal life, history, awards, contracts, rumors, other seasons. | always |
| W5 | Intensity words ("strong", "weak", "above average", "elite") only as the packet's own labels (`pitching_profile.*_label`, D24/D25) and the lineup notes of the findings (D32/D50). Never a stronger adjective, never a percentile, never a league comparison you invented. | a label is non-null |
| W6 | A dimension flagged limited (`sample.limited.<dimension> == true`) gets no claim. Say it is limited, with the counts the findings give (batters faced and the number needed). A missing label stays missing; do not fill it with a guess. | a limited flag, or a null label |
| W7 | A measured zero stays a measured zero ("threw none of this pitch"). A missing value is "not available", never zero. A pitch whose family is unmapped, or a starter whose arsenal is limited, gets no description of his pitch shapes. | zero, null, unmapped or limited arsenal |
| W8 | Movement says only what was measured: "Moves {h} in. sideways and {v} in. {up\|down} compared with a pitch thrown without spin." Never deception, "nasty", "unhittable", or any effect on hitters inferred from movement. Never arm side or glove side. | movement is shown |
| W9 | Compare two pitches or two starters only when both have a measured value for it, from the same scope. | any comparison |
| W10 | No cause words ("because", "due to", "thanks to", "as a result") unless the packet states that cause. | always |
| W11 | A statistical term is explained once, on first use, with its approved glossary definition (section 5), and only then. Do not define a term the glossary lacks; do not use it either. | a term is used |
| W12 | Say what each group of figures covers. Use the scope the packet gives ("2026 regular season through Aug 6"). No "recently", "lately", "tonight", "today", "this week" or any time claim the evidence does not carry. | always |
| W13 | Series (postseason): state only `series.standing` as the standing before first pitch, the game number and the series name. Never this game's result, a clinching or elimination claim, or anything after first pitch. Game 1 has no prior result: say the series has not started, or say nothing. | `series` is not null |
| W14 | Cover both starters and both lineups: the primary and put-away pitch of each starter when available, and each lineup's read when available. If a read is unavailable or limited, say so in the same place a read would have gone. | always |
| W15 | End with concrete things to watch, as questions tied to packet facts (a pitch, a count, a lineup tendency). No outcome in the question. | always |
| W16 | Do not mention the data fetch, the build, the dataset, case ids, the model, or this guide. | always |

## 4. Examples from real dev packets

Each "Good" in pairs 1 to 4 is a sentence the rules-based writer actually produced for that dev case (`findings/dev/<case>.json`), quoted unchanged. The "Good" of pair 5 is not existing output: it is the approved sentence form filled from the packet's own fields, and says so. The terms "batters faced", "swing-and-miss" and "command" in the Good sentences of pairs 1 and 2 are glossary rows still **proposed** (section 5); those Good sentences are real rules text, so they stay as they are, and the rows need your approval before the LLM writer may use them (open point 2). Each "Bad" is not model output: no LLM output exists yet, so I **constructed** it as a minimal edit of the good sentence that breaks exactly one rule. The owner decides whether constructed contrasts are acceptable (open point 1).

### Pair 1: a limited sample (W6, W5), `limited-823836`

- Evidence: `starters.away_starter.sample.limited.control = true`, `.limited.strikeout = true`, `.rates.batters_faced = 32`, `.thresholds.control = 170`, `.thresholds.strikeout = 70`; `season_summary.walks = 10`; `pitching_profile.command_label = null`, `.swing_miss_label = null`.
- Good: "Control data for George Klassen is limited (32 batters faced; 170 needed), so no command claim is made."
- Bad (constructed): "George Klassen has poor control: he walked 10 batters."
- Why it fails: control is flagged limited and has no label, so any command claim breaks W6; "poor" is an intensity word that is not a packet label (W5). The count of 10 walks is real, but a count does not license a rating on a limited sample.

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

### Pair 4: terms are explained once, from approved wording (W11, W12), `opener-823164`

- Evidence: `teams.home.offense_profile.ops_vs_hand = ".660"`, `.vs_pitcher_hand = "LHP"`, `.scope.label = "2026 regular season through Sep 26"`; glossary entry OPS (section 5).
- Good (rules sentence plus the approved definition): "This lineup has struggled against LHP pitching (.660 OPS), which gives Jack Dreyer an edge if he gets ahead." and, at its first use, "OPS is on-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup." The scope sentence follows: "Team offense splits cover the 2026 regular season through Sep 26."
- Bad (constructed): "Their elite OPS lately shows they feast on lefties."
- Why it fails: "elite" is not a label (W5); "lately" is a time claim (W12); OPS is used with no definition (W11); "feast" is a claim about outcomes with no evidence (W1).
- Note for the owner: the good sentence is the rules writer's own and contains "gives ... an edge". I kept it unchanged because it is real, but it is the kind of phrasing W3 may need to treat as a judgment; see open point 4.

### Pair 5: movement states a measurement, not a verdict (W8, W7), `veteran-824027`

- Evidence: `charts.pitch_movement.home_starter.Curveball = {family: "Breaking", h_break: 12.5, v_break: -6.5}`; the arsenal of José Soriano is not limited (`sample.limited.arsenal = false`).
- Good (constructed from the approved form "Moves {h} in. sideways and {v} in. {up|down} compared with a pitch thrown without spin." filled with the packet values): "Moves 12.5 in. sideways and 6.5 in. down compared with a pitch thrown without spin."
- Bad (constructed): "His curveball dives away from right-handed hitters and fools them."
- Why it fails: "away from right-handed hitters" uses an unverified side convention (W8); "fools them" infers deception and an effect on hitters from movement alone (W8, W1). No hitter-side result is in the packet.

## 5. Glossary (the only definitions you may use)

Definitions are evidence too: they must be supplied to A and B alike, frozen with their own digest before B1 (plan P2.4 section 6), and approved by the owner. The first rows already ship to fans as tooltips (`components/Tooltip.tsx`, `docs/DATA_CONTRACT.md` 3.3) and need no new approval. The rest are **proposed** and are not usable until approved.

| Term | Definition | Status |
|---|---|---|
| ERA | Earned run average: earned runs allowed per nine innings. Lower is better. | approved (tooltip) |
| WHIP | Walks plus hits per inning pitched. Lower is better. | approved (tooltip) |
| K | Strikeouts. | approved (tooltip) |
| OPS | On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup. | approved (tooltip) |
| K% | Share of plate appearances that end in a strikeout. | approved (tooltip) |
| BB% | Share of plate appearances that end in a walk. | approved (tooltip) |
| Break | Total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin. | approved (tooltip) |
| LHH / RHH | Left-handed hitters / right-handed hitters. | approved (tooltip) |
| batters faced | The number of hitters a pitcher has pitched to. | proposed |
| swing-and-miss | A hitter swings and does not touch the ball. | proposed |
| command | How well a pitcher throws where he intends. In this report it is only the label given in the packet (`command_label`). | proposed |
| put-away pitch | The pitch a starter uses second most (at least 15% of his pitches); the packet names it. | proposed (D30) |
| limited sample | Too few pitches or batters faced for a reliable read; the packet says how many are needed. | proposed |

## 6. How a report is checked (so you know what fails)

Code checks every cited path, value, entity and number (G1, R1); a local text-entailment model checks each sentence against the packet's fact sentences; a judge scores G2, L1, U1, R1 and, rule by rule, this guide (S1). A sentence the checks cannot trace to evidence is rejected, and after one informed retry the rules writer's text is published instead. Schema-valid output alone proves nothing.

## 7. Open points for the owner

1. **Constructed "bad" examples.** The plan says never invent examples, but no model output exists yet, so each "bad" is a constructed minimal edit of a real sentence, labeled as such. If you prefer only real failures, the guide can ship with the good sentences and the rule table, and the bad examples can be replaced by real B1 failures after the ten B1 dev examples.
2. **Glossary is outside the frozen packets.** The eval spec asks for jargon definitions "as explicit, approved packet evidence ... before packet freeze". The packets were frozen without a glossary. Proposal: freeze the glossary as its own file with its own digest, attached identically to A, B1 and B2 (plan section 6 already lists it as a separate frozen item). Needs your yes, and your approval of the proposed rows (the Good sentences of pairs 1 and 2 already use three of them). Also, names carry accents in the data ("José"); the entity check must compare them as written.
3. **A packet artifact.** Every packet carries `data_confidence.notes = ["Live snapshot fetched 2026-10-30 for <case id>."]`. It is a build artifact (the fetch day and a case id), later than the game date. W16 tells the writer never to use it; if you would rather it be removed from the packets, that is a re-freeze (new hash), which I did not do.
4. **Rules-writer phrasing.** The rules sentence "which gives {pitcher} an edge if he gets ahead" (pair 4) and "so {pitcher} needs efficient strikes" lean toward judgment. They are D32 catalog text. The guide does not change them; tell me if the LLM writer should avoid such phrasing, which would make A and B differ in style by design. The real sentence "no contact-risk rating is given because a home-run rate needs a far larger sample" (in most dev findings) contains "because", which W10 would reject from the LLM writer; it is D-catalog text, so say whether W10 should exempt this one sentence or the writer should restate it differently.
5. **Postseason season lines.** The as-of season line in postseason packets is the regular season only (the game-log source is regular season), which the scope label says ("2026 regular season"). Earlier postseason starts of that October are not in it. I have not checked whether the daily job's own `byDateRange` call matches this for a postseason game; the guide should not claim more than the scope label says.
6. **Opener stratum.** The "opener" cases are starters with short recent outings (opener-like); the schedule opener flag was not read. The guide therefore says nothing about "openers" or "bullpen games": the packets do not establish them.
