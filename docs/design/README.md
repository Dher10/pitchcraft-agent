# PitchCraft design package (v2, "the scoreboard")

Approved by the owner on 2026-11-14. This folder is the source of truth for the look, the components, the copy rules and the page anatomy of PitchCraft. It was produced in the planning chat (Claude Design) and exported here so any agent can build from the repo alone.

## Read in this order

1. `DESIGN_SYSTEM.md`: the idea, color, type, spacing, layout, iconography, accessibility, implementation notes.
2. `CONTENT.md`: the four kinds of content (figure, fact, reading, context), voice, number and date formats, sources, and the glossary that feeds every Help text.
3. `PAGES.md`: the anatomy of each page and its states (in season or off season, before or after the game).
4. `COMPONENTS.md`: guidelines for the 24 components.
5. `PLAN_UI.md`: the work units, their order, acceptance criteria and what each one needs from the data. The plan the units run on is `docs/plans/R4-U.md`.
6. D67 in `docs/DECISIONS.md` (approved 2026-11-15): what release B ships, what is frozen until February 2027, and the after-the-game layer recorded for R4-P.

## Files

| Path | What |
|---|---|
| `tokens.json` | Every token: colors, type scale and fonts, spacing, radius, shadow, layout. The values to put under `@theme`. |
| `components.css` | Reference CSS for all components (classes `pc-*`), written against the tokens. **Reference only: port it, do not ship it as a global stylesheet.** |
| `assets/` | The logo: mark on light, mark on board, favicon, and direction B kept as the alternate. Rules in `assets/README.md`. |
| `fonts/` | Big Shoulders Display (variable, latin, 36 KB) and its license (SIL OFL 1.1). Copy to `app/fonts/` and register it in `app/fonts/README.md`. |
| `reference/html/` | The 20 designed screens as static HTML that opens from disk (`reference.css` beside them). The markup shows structure, class names and real copy. The pitch chart filter and the switches (batter hand, pitch, view) there are a working plain script: it is the behavior spec. |
| `reference/screens/` | The same 20 screens as PNG, phone at 390 px and desktop at 1280 px. |

## Data in the references

Real, from the published archive (`public/data/archive/index-2026.json`, 2026-11-15): every game, date, round, club, starter and final score in the home, notable, archive and today lists; the series board; the counts (40 games, 30 notable; strikeout duel 15, veteran duel 12, series-ending 11, World Series 5); the games per day in the calendar. Real from the Oct 28 report and Savant: the Game 5 pre-game text, claims and questions, both starters' season lines, both lineups' splits, Misiorowski's 2026 innings, mix, usage by batter hand, pitch counts and average speeds.

Illustrative: every in-game figure (final lines with pitches, Game Score, swings and misses, first-pitch strikes), pitch locations and at-bat endings, verdicts and answers (all R4-P), pitch movement and median locations, heat-map distributions, the first-pitch time, and the team and pitcher pages beyond the figures named (R5). Never copy an illustrative number into a fixture as if it were data.

## Scope of release B

Release B builds the shell and the pages that run on the published archive: home (off season), `/game/<gamePk>`, `/archive`, `/notable`. The reference screens also show what comes later; `PLAN_UI.md` says which blocks are frozen until February 2027 (R4-P, R5, Today in season) and how each page behaves without them.

## What is not here

Dark theme values; the `/quality` page content (it takes the card, Chip and table styles as they are); the pitchers index on desktop (derive it from the archive desktop layout: filters left, list right).

## Where the live versions are

The design system and the page canvas live as private artifacts in the owner's claude.ai account. This folder is the export; if the two ever differ, the owner decides and this folder is updated.
