# Content and voice

What PitchCraft writes, where each kind of content goes, and how it sounds. This page is the rule for every new string, in the site and in the reports.

## Who reads

A casual fan, on a phone, who knows the clubs and not the statistics. They came to understand tonight's starters or to see how a game they watched was pitched. Write so that this reader never needs a second tab.

## The four kinds of content

Every sentence and number on the site is one of these. Never blend two in one element.

| Kind | What it is | Where it goes | How it looks |
|---|---|---|---|
| **Figure** | A number from a source: ERA, a final line, a pitch count | StatTile, FinalLine, tables, the series board | Scoreboard numeral, with a label and a scope |
| **Fact** | A sentence that states figures: "1 walk to 28 batters." | CallCheck, QuestionAnswer, the one-sentence summary of a start | Plex Sans, the key figure in bold |
| **Reading** | What the figures mean, by a written rule: "above-average swing-and-miss ability", "Held up" | The report's paragraph before the game; chips for verdicts and reasons | Prose or a chip. Always traceable to a rule and its threshold |
| **Context** | Where the data comes from and when: mode line, origin line, scope captions, attribution | Top of the page, under a rule in the score board, under tiles, the footer | `ink-2` or `ink-3`, small |

Rules that follow:

- **Figures go in tiles and strips, not in paragraphs.** A paragraph may cite one figure to support a reading (".751 OPS"); three figures in a sentence is a table.
- **A reading never appears without the figure behind it nearby.** "Solid command" sits in a card that also shows the walks.
- **A verdict is a reading with a rule.** "Held up" exists only where a rule says what holding up means for that kind of claim. No rule: "Not rated", with the reason.
- **Before and after never mix.** What was written before the game is labeled "Before:" or "We asked:"; what was added after is the fact and the verdict. The origin line says which is which.
- **No opinion, no prediction.** PitchCraft does not say who will win, who is better, or that a start was good or bad. It says what was expected, what happened, and whether the two match.

## Voice

Plain, specific, calm. The tone of a scorer who has watched a lot of baseball and does not need to impress anyone.

- State what the data shows and stop. "He threw a first-pitch strike to 20 of 28 batters."
- Short sentences. One idea each. Active voice. The pitcher is the subject.
- Words before abbreviations: "Strikeouts" where it fits; "K%" with Help where it does not.
- Counts before rates when the sample is one game: "9 swings and misses on 88 pitches", not "10.2% whiff rate".
- Say what is not known: "Not available", "Not rated: a home-run rate needs a far larger sample."
- Baseball's own words are welcome where a fan uses them (first pitch, deep counts, the heart of the plate). Insider shorthand is not (CSW, xwOBA, "stuff").

Never:

- Hype or judgment: dominant, elite, filthy, ace, gem, struggled, disaster, must-watch.
- Prediction or advice: will, should win, expect him to, lock, value, odds.
- Exclamation marks, questions used as headlines, emoji.
- "We think", "it seems", "arguably". If a rule supports it, state it; if not, leave it out.
- Zero or a blank for something unknown.

Examples:

| Instead of | Write |
|---|---|
| Misiorowski was dominant, mowing down the Rays. | Held the Rays to one run over eight innings and struck out 11. |
| Rasmussen struggled with his command. | 88 pitches for 15 outs. He left after the fifth. |
| Elite whiff rate. | 21 swings and misses on 104 pitches. |
| Expect a pitchers' duel tonight. | Both starters strike out batters at an above-average rate. |
| N/A | Not available |

## Claims

Every sentence that asserts something about data is a **catalog claim with a registry condition** (data contract rule 4): it has a key, a fixed wording with slots, and the condition under which it may print. This holds for the report, for chips, for verdicts, for answers, for empty states that name data. A design may restyle a claim; a new sentence needs its entry first. Strings stay in the catalog so Spanish (v2.1) is a second column, not a rewrite.

## Labels, numbers, dates

- Labels: sentence case, Plex Sans 13px. No uppercase, no colon at the end.
- Buttons and links say what happens: "Read the report", "See his page", "Show all 9 starters", "Clear".
- Numbers: ERA and WHIP to two decimals; innings as 8.0, 6.1, 5.2; rates with one decimal and the sign (37.9%); averages without the leading zero (.751).
- Scope goes once, under a group of figures: "2026 regular season", "2026 postseason, before and after this game", "Against right-handed pitching".
- Dates for people in text: "Oct 28, 2026"; with the weekday in a page head: "Wednesday, Oct 28, 2026". ISO only in `datetime` attributes and URLs. Times with the zone: "8:08 PM ET".
- Lists in a sentence use commas, not middle dots: "Game 5, Oct 28, 2026, Tropicana Field".
- Names: full name on first use in a card ("Jacob Misiorowski"), "he" after; last name only in tight table cells.

## Sources and attribution

- **MLB Stats API:** schedules, results, box scores (final lines), season lines, series status, rosters.
- **Baseball Savant (Statcast):** pitch-by-pitch data: pitch types and mix, locations, swings and misses, first-pitch strikes, at-bat endings; team batting splits.
- **Computed by PitchCraft, by published formula or rule:** K%, BB%, the split around the All-Star Game, Game Score, labels and verdicts, notable reasons.

Every page footer carries the attribution to MLB Advanced Media, the statement that the site is independent, free and non-commercial, the no-predictions line, "Team colors are approximate", and the credit "Made by Daniel Herdenez" linking to danielherdenez.com. Every group of figures says its scope; a figure computed by PitchCraft can say how in its Help.

## Glossary (the only source of Help text)

| Term | Definition shown |
|---|---|
| ERA | Earned runs allowed per nine innings. Lower is better. |
| WHIP | Walks plus hits per inning pitched. Lower is better; near 1.00 is very good. |
| K% | The share of batters he struck out. For a starter, 25% or more is above average. |
| BB% | The share of batters he walked. Lower is better. |
| OPS | On-base plus slugging: how well a lineup gets on base and hits for power. Higher is better for hitters. |
| IP | Innings pitched. 6.1 means six innings and one out. |
| Final line | What a starter did in this game: innings, hits, earned runs, walks, strikeouts. |
| Game Score | One number for a start, from a public formula. It starts at 50, adds for outs and strikeouts, and subtracts for hits, walks and runs. 50 is an average start; 75 or more is rare. |
| Swing and miss | A swing where the batter did not touch the ball. |
| First-pitch strike | The first pitch of an at-bat was a strike. It puts the pitcher ahead. |
| Heart of the plate | The middle of the strike zone, where pitches are easiest to hit. |
| Deep count | An at-bat that reaches five or more pitches. |
| The split | Why split here? The All-Star Game marks the middle of the season. Comparing the two halves shows whether a starter improved, tired or changed something. |
| Small sample | Too few innings or batters for a figure to say much. Labels that need more are left out. |
| Rookie | A pitcher who still had rookie status this season under MLB's rules. |
| Winner-take-all | A game in which both clubs are one loss from elimination. |

A definition is one or two sentences: what it is, then how to read it. If a page needs a term that is not here, add it here first.
