# Components

Guidelines for the 24 components of the PitchCraft design system. Structure and spacing: `components.css` (classes prefixed `pc-`). A rendered example of each is in `reference/html/` inside the pages that use it.

## Logo

The mark plus the wordmark, once per page, in the header. A home plate holding the strike zone with one cell lit.

- In the header (on `board`): the on-board mark at 30px and PITCHCRAFT in Big Shoulders Display 800 at 26px. It links to the home.
- On light surfaces use the on-light mark with `ink` text.
- The app icon is the on-board mark on a `board` tile.
- Files, colors and rules: `assets/README.md`.

## SiteHeader

The header of every page, on `board`: the logo and five destinations (Today, Notable, Archive, Teams, Pitchers).

- Phone: a 56px logo bar and, under it on `board-2`, five equal tabs, each 44px tall. No hamburger menu.
- Desktop: one 68px bar, logo left, links right.
- The current item has `aria-current="page"`, `signal` text and a 3px `signal` underline.
- **Off season:** Today is not a link. It shows a lock and `on-board-2` text (`aria-disabled`), and a notice on `signal-tint` sits under the header: "Off season. No games today. Today's games and daily reports return when the 2027 season starts." In season the lock and the notice are gone and Today is the first link.
- On a game page the current item is the list the visitor came from: Today before the game, Archive after.
- The consumer provides the current item and whether the season is on.

## TeamDirectory

All 30 clubs by league and division, to reach a team page.

- Two panels (American League, National League), each with three rows (East, Central, West) of five clubs.
- Each club is a link: badge on top, nickname under it, both centered on one axis. The name always has room for two lines, so "Blue Jays" and "White Sox" do not push their badge out of line.
- Phone: the panels stack. Desktop: side by side.
- A club with no page yet is shown at 45% opacity and is not a link.

## ModeLine

One line that says what kind of data the page shows. Every page has it (data contract rule 6), at the top of the hero or page head.

- `archive`: the off season. "2026 season archive, final results through {last game date}".
- `live`: a game day. "Live data, fetched {date}".
- `demo`: "Demo data: live data unavailable" (warn tint, square dot).
- On `board` it sits on `board-2` with a `signal` dot.
- Dates are written for people; ISO stays in `datetime` attributes. Keep `data-testid="mode-line"`.

## Chip

A short fixed phrase with a meaning. Sentence case, 13px, at least 24px tall. A chip is not a button.

| Variant | Use |
|---|---|
| `ok` / `warn` / `bad` / neutral | Status: the critic before the game (Supported, Warning, Unsupported, Not present) and the comparison after it (Held up, Partly held up, Did not hold up, Not rated). Always icon + word. |
| `feat` (solid `signal`) | What a starter did: the strongest notable reasons (10+ strikeouts, 8+ innings, Game Score, no-hitter). |
| `reason` (`signal-tint`) | The other notable reasons: stakes and matchup. |
| `round` | The postseason round. |
| `outline` | Rookie mark. |
| `warn` | Small sample, starter changes. |

- Every chip text is a catalog phrase; a reason prints only when its rule is true.
- A long reason may wrap (`pc-chip--wrap`); never truncate it.
- Three status chips in one row share the width equally (`pc-chips--even`).

## Help

A term with its definition one tap away: a circled question mark after the label, and a small panel on `board` that opens on tap, on keyboard focus and on hover.

- The button is 18px with a 44px hit area and an accessible name ("What is Game Score?"); it exposes `aria-expanded`. Escape or a tap outside closes the panel.
- The panel is at most 260px wide, 13px text, the term in `signal`. It opens under the term, or above it when it would cover figures.
- One or two sentences: what the term is, then how to read it ("50 is an average start; 75 or more is rare").
- Every definition comes from the glossary in the Content section, word for word; never write a definition in a page.
- Use it for abbreviations and for choices the page made (why the season is split at the All-Star Game). Do not use `title` attributes.

## TeamBadge

A circle in the team's approximate color with its abbreviation in Big Shoulders Display 800. Owner decision (2026-11-12): team colors stay.

- Sizes: 24 (tables), 34 (rows, directory), 48 (boards and page heads). On `board` the badge gets a thin ring so navy clubs stay visible.
- The badge is decoration; the team name is always in text next to it. Eight clubs are near-identical navies.
- Team color appears in exactly three places: the badge, the 4px top border of a starter card, and the rule under a team or pitcher page head.
- Colors come from `lib/teamColors.ts`; approximate and unlicensed, and the footer says so.

## StatTile

One figure with its label. The label is on top, centered, in IBM Plex Sans 13px; the value is a scoreboard numeral (Big Shoulders Display 700, 28px, tabular) centered in the tile, so a row of tiles lines up whatever the label length.

- A row of tiles carries one scope caption under it ("2026 regular season").
- States: value; **featured** (`signal` fill, for the figure a notable reason points at); **unavailable** (the dash with "Not available", never 0 or blank); **limited sample** (`warn-tint`, with the sample stated).
- A term a casual fan may not know gets a Help button after the label (see Help).
- Three tiles per row on a phone, up to six on desktop.
- The consumer provides label, value or null, an optional note, and the state.

## FinalLine

A starter's line in one game, from the box score: IP, H, ER, BB, K and, when known, pitches. A ruled strip of equal cells, like a line of a box score, with scoreboard numerals.

- A cell a notable reason points at (8+ innings, 10+ strikeouts) is filled with `signal`.
- A field the box score does not give shows the dash; a real 0 shows 0. With no line at all: the text "Final line not available".
- It is a `dl`; each abbreviation has its full name for assistive tech.
- Shown only on finished games.

## PitchMix

A starter's arsenal as one stacked bar with a legend.

- Each pitch has a token color and a shape by family: fastballs a circle, breaking pitches a diamond, offspeed a square, anything else a grey ring.
- The legend carries the name and the share; the bar has a text alternative. Largest share first; 2px gaps.
- Unknown: no bar, the text "Pitch mix not available" with the reason.

## AttackCard

"How he attacks": what a starter throws and how each pitch behaves. It is the chart of a starter **before a game**; it answers "what does he throw" and never plots single pitches.

- **Hand switch** (vs left-handed, vs right-handed): two toggle buttons; left-handed first. It changes the usage list and the location chart.
- **Arsenal list:** one row per pitch, most used first for the chosen hand: family shape, name, usage as a scoreboard numeral, and a thin bar in the pitch color. Each row is a button; pressing it selects the pitch.
- **Location chart:** the strike zone from the catcher's view with one mark per pitch at its median location against that hand. The selected pitch gets an ink outline.
- **Pitch detail** for the selected pitch: its movement drawn as a path from release, the name with its family, average speed, and one sentence ("Moves 8.0 in. sideways and 17.0 in. up compared with a pitch thrown without spin.").
- Scope caption: "2026 regular season". A pitch under the minimum sample is left out of the list and named in the caption.
- Phone: list, location chart and detail stacked. Desktop: list and chart side by side, detail under them.
- It uses the page's small client script for the two switches; without JavaScript it shows left-handed hitters and the most used pitch.
- Data: all of it is already in the daily payload (pitch mix by hand, velocity, movement, median locations).

## PitchChart

Where a starter's pitches crossed the plate, from the catcher's view: the strike zone in thirds, home plate under it, one mark per pitch.

- Pitch type: token color and family shape, as in PitchMix.
- **How the at-bat ended**, on the pitch that ended it: a strikeout is a `signal` disc with an ink ring behind the mark; a ground-ball out is a solid ink ring; a fly-ball out is a dashed ink ring. Three kinds of out are told apart by shape, so a ground-ball pitcher reads as clearly as a strikeout pitcher.
- **The legends are the filters.** Each legend entry is a toggle button (`aria-pressed`): pitch types in one group, at-bat endings in another. Within a group the choices add up (four-seam or slider); the two groups combine (four-seam and strikeout). With nothing pressed, every pitch shows.
- **Counts follow the filter.** Each button's number is what it would show under the other group's choice: with Strikeout pressed, Four-seam reads 8, the strikeouts that ended on a four-seam. Under the buttons: "Showing 8 of 104 pitches" and "Show all", which clears both groups.
- Pressing an ending hides the pitches that did not end an at-bat. A pressed button is `ink` with its count in `signal`; a count of 0 stays visible so the reader sees there were none.
- Buttons are 40px tall with 8px gaps. The chart keeps a text alternative with all totals; the "Showing" line is announced when it changes.
- It needs a small client script (the only one on the page); without JavaScript the chart shows every pitch and the buttons are plain legends.
- **One game only.** It is used after a game (the game page) and for a single start on the pitcher page. It is never used for a season: a season of pitches is a PitchHeatmap, and before a game the starter gets an AttackCard.
- Unknown: the text "Pitch locations not available".
- Data: Statcast pitch rows already fetched per starter; the at-bat ending needs the play result of each pitch (owner decision pending).

## PitchHeatmap

Where a starter's pitches go over a **season**: one small map per pitch type. A season is thousands of pitches, so single marks would be a blot; the map shows where each pitch lives.

- Each map is a 5 by 5 grid from the catcher's view: the middle 3 by 3 is the strike zone (ink outline), the outer ring is just off the plate. A cell's fill is the pitch's own color, stronger where more pitches crossed; strength is relative to that pitch's busiest cell.
- It is a count per cell, not a smoothed surface: every shade is a number the data has.
- Under each map: the pitch count. A key reads "Fewer pitches" to "More pitches".
- **Small sample:** a pitch thrown fewer than 50 times is shown pitch by pitch in the same frame ("28 pitches, each one shown"). A pitch thrown fewer than 5 times is not drawn and is named in the caption.
- **Hand switch:** All hitters, vs left-handed, vs right-handed.
- Two maps per row on a phone, three on desktop. Pitches in order of use.
- Each map has a text alternative with the pitch, the count and that darker means more.
- Used on the pitcher page under "Where his pitches go" for the season view; choosing a single start there switches to the PitchChart of that game.
- Data: counts per pitch type, batter hand and cell, computed from the season's pitch rows (plan R5).

## GameRow

A finished game in any list: date, round and game number; the two sides with badge, team, starter and runs; then its notable reasons. The whole row is one link to the game page.

- Away side first, home second.
- The winner is marked three ways: bold name, `ink` runs at weight 800 (the loser's are `ink-2`) and a `stitch` triangle before the runs.
- Runs are scoreboard numerals, right-aligned so they line up down the list.
- Reasons: featured first, then the rest; at most three on the home, one in the archive, all on the notable page.
- Rows share one rounded container and are separated by a line.
- The link's accessible name: "{away} at {home}, {date}, final {runs}-{runs}".

## SeriesBoard

A postseason series as a line score with games in place of innings: one row per club, one cell per game with the runs it scored, and the wins at the end.

- It lives on `board`. The winning side's runs are `signal`; the series winner's total is a `signal` cell, the other an outlined cell.
- Each cell is a link to that game's page, with a full accessible name.
- Under it, one sentence with the result ("Brewers win the series 4-1").
- Used in the home hero for the last series of the season; on a team page for that club's series.

## ArchiveTable

The archive on desktop: date and round, game and starters, score, notable. Under `bp-lg` the same rows render as GameRow; the table never scrolls sideways.

- A `caption` and `scope="col"` on every header. The game cell holds the link.
- Score in scoreboard numerals, away then home, the winner's runs in `ink` at weight 800.
- Notable: the first reason and "+n" for the rest; the dash when none.
- Header row on `surface-sunken`; no stripes.

## RotationCard

One starter on a team page: a separate card per starter, with the 4px top border in the team color.

- Blocks: name with marks (Rookie, Small sample), hand and style, "See his page" and the number of reports; four season tiles with one scope caption; the split before and after the All-Star Game; PitchMix.
- Phone: stacked. Desktop: three columns in one card.
- The split's header has a Help button that says why the season is split there.
- A half with no starts reads "No starts" across the row, not zeros.
- Cards are 16px apart; starters with the most innings first.

## ScoreBoard

The top of a game page, on `board`: round, game number, date and venue; the two clubs around the center; the series line; the origin line.

- **After the game:** the final score in `signal` scoreboard numerals (72px on a phone, 104px on desktop); the loser's runs and name are `on-board-2`. "Final." is written out.
- **Before the game:** the first-pitch time in the center, both clubs at full strength, and the series standing.
- **Origin line**, always present under a rule: before the game "Live data, fetched {date}. Written before the game..."; after it "The report was published before the game, on {date}. What happened was added after the final out." For a report rebuilt later: "Written after the game, from data through {as_of}."
- Phone: badge over nickname. Desktop: full club names in the display face beside the badges.

## StarterCard

One starter on a game page. It has two states that share the head (club and role, name in the display face, hand and style in words, badge) and the 4px top border in the team color.

**After the game ("How the starters did"), top to bottom:**
1. One sentence on the start, a catalog phrase built from the line.
2. FinalLine.
3. Three tiles: Game Score, swings and misses, first-pitch strikes.
4. PitchChart of this game with at-bat endings.
5. "What we said, and what happened" (CallCheck).
6. His postseason (or season) line before and after this game: three tiles with the old value, an arrow and the new one.

**Before the game ("The starters"):** season tiles with one scope caption, the report's paragraph on him, the AttackCard (what he throws and how it moves), and the lineup he faces (three tiles). No cloud of pitches before a game.

- Other states: bio unavailable (line omitted); a figure unavailable (dash and reason in its tile); small sample (warn tiles); probable starter did not start (warn notice naming who started; the card is the pitcher who started); starter not confirmed (neutral notice).
- Two cards side by side from `bp-md`; stacked on a phone, away first.

## CallCheck

"What we said, and what happened": each claim the report made before the game, next to the fact from the game and a verdict.

- One row per claim: the claim in `ink-2` after "Before:", then the fact with its key figure in bold, then the chip, vertically centered on the fact.
- Verdicts: Held up, Partly held up, Did not hold up, Not rated. Each comes from a written rule for that kind of claim (threshold and sample), never from judgment. A claim with no rule is "Not rated" and says why.
- The fact is always a count the reader can check ("1 walk to 28 batters"), not an adjective.
- On the pitcher page the same pattern compares the profile with the season: the first line reads "Expected:".
- The verdict rules need an owner decision before they ship.

## QuestionAnswer

"What we asked before the game": each What-to-watch question of the report, answered after the game with one figure and one sentence.

- The question in `ink-2` after "We asked:"; the figure in a `signal` box, vertically centered on the answer; the answer starts with its verdict in bold ("Yes.", "Partly.", "The Brewers.").
- Before the game the same list shows the questions alone, with the line "Each question gets its answer here after the game."
- A question the data cannot answer says so: "Not answered: {reason}". Never drop a question that was asked.
- Each answer is a computed fact with a registry condition.

## Filters and Calendar

The archive filters: a team select and a month calendar for one day or a range of days.

- Calendar: seven columns, cells 46px tall. A day with games is a link on `surface-sunken` showing the day and, under it, the number of games; a day without games is plain `ink-3` text. The start and end of the range are `board` cells with a `signal` count; days between them are `brand-tint`.
- Month arrows are 44px; an arrow with no games beyond it is disabled. The key under the grid explains both fills.
- First tap picks a day, second tap picks the end of a range, "Clear" resets. Under the grid, the chosen range in words.
- It works as links (`/archive?team=MIL&from=...&to=...`), so it needs no JavaScript and the URL is shareable; the two-tap range uses the URL to remember the first day.
- Desktop: the form is a 380px left column and the results fill the rest. Phone: the form is always open above the results.
- No match: the EmptyState, naming what was asked ("The Mariners did not play between Oct 23 and Oct 28").

## Button

- Primary: `brand` fill on light surfaces, `signal` fill with ink text on `board`. One per view.
- Secondary: `surface` with a `line-strong` border; on `board`, transparent with an `on-board-2` border.
- Quiet: underlined `brand` text, for clearing or going back.
- 44px tall, 15px 600, `radius-sm`. Navigation is an `a`; only form submits are `button`.
- A label says what happens, in the page's words: "Read the report", "See his page", "Show all 9 starters".

## EmptyState and Notice

What a page shows when there is nothing, or less than usual, to show: say what is missing in one plain sentence, say why if the data knows, and offer one way forward.

| Situation | Pattern | Text |
|---|---|---|
| In season, no games today | EmptyState, then yesterday's results | "No games today" |
| Off season | not an empty state: the home is a season review; Today is locked in the header | |
| Filters match nothing | EmptyState naming what was asked | "No games match these filters" |
| No notable game in a round | EmptyState | "No game met a rule" |
| Index missing | Notice, neutral | "The archive is not available right now." |
| Unknown game, team or pitcher | 404 with the EmptyState and links | "We could not find that game" |
| Small sample | Notice or warn tiles, where the figures are | states the sample |
| Probable starter changed | Notice, warn, in the StarterCard | names who started |

- The empty symbol is the logo's plate, dashed, with no zone.
- Never a spinner or skeleton (pages are server rendered), never zero for unknown, never internal error text.

