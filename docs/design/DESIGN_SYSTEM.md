# PitchCraft

Starter matchups, checked against the data. PitchCraft reads public MLB data and tells a casual fan, on a phone, what to expect from the two starting pitchers of a game and, after it, what they did and whether the report held up. It says only what the data supports: no predictions, no betting, no ads.

This is the design system of the site: identity, tokens, components, and the rules for what is written, where, and in what voice. Version 2, "the scoreboard", approved in direction by the owner on 2026-11-13. It replaces version 1 of 2026-11-12 (chalk ground, serif, clay accent), which the owner found flat.

**Read in this order:** this page (identity and foundations), then **Content and voice** (what to write and where figures, facts and analysis go), then **Pages and states** (the anatomy of each page), then a component's own guidelines before using it.

## The idea

**A scoreboard a fan can read.** Every page opens with a dark green band, like the board over the outfield wall: the header, the hero, the score of a game. On the board, figures are yellow, the way a hand-operated scoreboard lights the number that matters. Below the board the page is light and calm, and every featured number, on any surface, is a scoreboard numeral in the same condensed face.

Three rules follow from the product's promise and are visible in every component:

1. **A figure is never alone.** It has a label a fan can read, a scope ("2026 regular season"), a definition one tap away when the term is jargon, and, when it is missing, a dash with the reason. Never zero, never blank.
2. **A report says where it comes from and when.** Every page carries a mode line; every game carries an origin line; what was written before the game and what was added after it are never mixed.
3. **Color never works alone.** Status, winner, pitch type, at-bat ending and team are each carried by a word or a shape as well.

## Visual foundations

### Color

| Role | Token | Notes |
|---|---|---|
| The board | `board` #0E3B2C, `board-2` | header, home hero, score of a game, footer; raised cells |
| On the board | `on-board`, `on-board-2` | text; secondary text and the losing side |
| Signal | `signal` #FFC93C, `signal-tint`, `signal-ink` | figures and the current item on the board; the primary button on the board; featured tiles and chips on light surfaces. A fill on light surfaces, never text |
| Stitch | `stitch` #D7382C | the winner's marker and the lit cell of the on-board logo. A small mark only; never text, never a status |
| Ground and surfaces | `ground` #F1F4EF, `surface`, `surface-sunken` | the page; cards; tiles and table headers |
| Lines | `line`, `line-strong` | decorative; control borders (3:1) |
| Text | `ink`, `ink-2`, `ink-3` | 14.8:1, 8.5:1, 5.6:1 on ground. `ink-3` is the floor on light surfaces |
| Brand | `brand` #177245, `brand-strong`, `brand-tint` | links, the primary button on light surfaces, selection, round chips |
| Status | `ok`, `warn`, `bad` + tints | always icon + word |
| Pitches | `pitch-*` (9) | color + shape by family |
| Focus | `focus` | 3px ink ring on light surfaces; `signal` on the board |

How much of each: the board is the top of every page and the footer, never a card in the middle of a list. Signal is the rarest fill on light surfaces: one featured tile or cell per card, the featured chips, the answer box. If everything is yellow, nothing is the number that matters.

All text pairs were computed: every text token is at least 4.5:1 on the surfaces its usage note names; `signal` on `board` is 8.1:1; pitch colors are at least 3:1 on `surface` as marks.

**Team colors stay** (owner decision, 2026-11-12) in three places: the badge, the 4px top border of a starter card, and the rule under a team or pitcher page head. Approximate and unlicensed; the footer says so; the name is always next to the color.

### Type

| Family | Use |
|---|---|
| **Big Shoulders Display** 700/800 (variable, OFL, self-hosted, 36 KB) | page titles, names of starters and clubs in heads, the wordmark, and **every featured number**: scores, tiles, final lines, the series board, team abbreviations |
| **IBM Plex Sans** 400/500/600/700 (already self-hosted) | everything a fan reads: body, labels, chips, navigation, tables |

No third family: IBM Plex Mono and Fraunces are retired. Figures in running text and tables use the tabular figures of Plex Sans. Labels are sentence case, never uppercase (the wordmark is the only capitals). **12px is the smallest text.** The scale is in `tokens.json`: display-xl 72, display-lg 48, display-md 36, title-lg 28, score 88, stat 28, badge 14; title-md 17, body-lg 17, body 16, body-sm 14, label 13, caption 12.

Big Shoulders Display is one new file (`big-shoulders-display-latin-wght-normal.woff2`, from `@fontsource-variable/big-shoulders-display@5.3.0`), loaded with `next/font/local` like the Plex files, so the CSP (same-origin fonts only) is unchanged.

### Space, shape, depth

- **Spacing:** 4, 8, 12, 16, 24, 32, 48, 64. Card padding 16 on a phone, 24 on desktop. Sections 32 apart on a phone, 48 on desktop.
- **Radius by rank:** 6 (chips, tiles, inputs, buttons, calendar days), 10 (notices, cells of the series board), 14 (cards), 22 (the score board of a game on desktop), full (badges and dots).
- **Depth:** flat. Cards are `surface` with a 1px `line`. The only shadow is `shadow-pop`, for the Help panel.
- **Motion:** none beyond the browser's own; pages are server rendered, so there are no loading states.

### Layout

- **Phone (375 to 430):** one column, 16px gutters, nothing scrolls sideways, every target 44px tall.
- **Tablet (from 720, `bp-md`):** starter cards side by side; lists of cards in two or three columns.
- **Desktop (from 1024, `bp-lg`):** content up to 1184px with 32px gutters; lists gain a side column (criteria, filters, the check of the report). Prose never runs wider than 640px.

### Three charts for three moments

| Moment | Chart | Why |
|---|---|---|
| Before a game | **AttackCard**: the arsenal with usage, each pitch's movement and speed, median location by batter hand | The fan wants to know what he throws. No single pitches. |
| After a game | **PitchChart**: every pitch of that game, with filters and at-bat endings | About a hundred pitches: each mark reads and tells the game. |
| A season (pitcher page) | **PitchHeatmap**: one map per pitch type, by batter hand | Thousands of pitches: a map shows where each pitch lives. |

## Iconography

Small line icons drawn inline at 12 to 18px, stroke 1.4 to 1.8, round caps, `currentColor`: check, warning triangle, cross, dash, star (rookie), clock (origin), info, help (circled question mark), lock (Today, off season), chevrons, calendar arrows, arrow (before to after). No icon library, no emoji. An icon always sits next to its word, except the Help button, which has an accessible name. The empty-state symbol is the logo's plate, dashed.

## Components

Twenty-four, each with a live preview and guidelines: Logo, SiteHeader, TeamDirectory, ModeLine, Chip, Help, TeamBadge, StatTile, FinalLine, PitchMix, AttackCard, PitchChart, PitchHeatmap, GameRow, SeriesBoard, ArchiveTable, RotationCard, ScoreBoard, StarterCard, CallCheck, QuestionAnswer, Calendar (with the filters), Button, EmptyState (with Notice). Their reference CSS is `components.css` in this folder (classes prefixed `pc-`), written against the tokens; previews are plain HTML, not React.

Where the existing code goes: `Hero` becomes the board hero; `GameCarousel` and the home archive become GameRow lists; `ArchiveTable` becomes GameRow on a phone and ArchiveTable on desktop; `StatTile`, `StarterCard`, `TeamBadge`, `ModeLine` are restyled; `CriticReviewPanel` becomes the "How the report was checked" card; `CallCheck` becomes the after-the-game comparison; the "How he attacks" block (`PitchZoneCard` and the pitch list) becomes AttackCard; `Tooltip` becomes Help; `PitchMixChart` and `VelocityChart` (dead code) are deleted; `StrengthProfile` and `AgentPipeline` stay demo-only.

## Accessibility, by construction

Contrast as above; 12px floor; 44px targets; one focus style; winner, status, pitch, at-bat ending and team identifiable without color; lists of games are links with full accessible names; tables have captions and scoped headers; definitions open on tap and focus, not only hover; toggles expose `aria-expanded`; the current nav item has `aria-current`; no sideways scroll at 375px.

## Constraints the system respects

From the data contract and decisions D5, D16, D26, D31, D65: English only until v2.1; unavailable shown as unavailable; origin and mode always visible; no demo content in live pages; no predictions, betting, ads, trackers or cookies; same-origin fonts and images; static, server-rendered pages; MLB and Statcast attribution on every page.

## Decisions recorded in D67 (2026-11-15)

The full text is D67 in `docs/DECISIONS.md`. In short:

1. Release B ships this design system on the published archive (`archive_version 1.0.0`) and changes no data. It runs under D66(5) and R4 4.6: no Game Score, verdicts or answers yet.
2. Frozen until February 2027: R4-P, R5, the Spanish version, writer v3, Today in season, the AttackCard and dark theme values (the token structure is ready).
3. Recorded now, effective only when R4-P ships: after-the-game facts and Game Score (reversing D66(5) and D41's cut of automated postgame), verdicts and answers by written rules, and the new notable rules (replacing R4 4.6 and OQ5).
4. Pitch locations and at-bat endings per game need the pitch rows of the game itself (the report's frames stop at `as_of`), and Game Score and the new notable rules need box-score fields the 1.0.0 files do not keep (runs, club hits, pitches). Both are new fetches with their own request budget, a new block in the archive file and a new `archive_version`.
5. `/pitcher/<id>` and `/pitchers` join `/team/<abbr>` in R5.

## Implementation notes (Tailwind v4, Next.js)

- Put the tokens in `app/globals.css` under `@theme`, so utilities like `bg-board text-on-board font-display rounded-lg` exist and arbitrary values can be banned by lint.
- Add a test that fails on text under 12px, on `text-neutral-400`, and on any hex literal in `app/` and `components/` outside `lib/teamColors.ts`.
- `components.css` is the reference for structure and spacing; port it to components, do not ship it as a global stylesheet.
- Component primitives (dialogs, popovers for Help, selects) may come from a headless library such as the one behind shadcn/ui; the look comes from these tokens, not from a preset theme.
