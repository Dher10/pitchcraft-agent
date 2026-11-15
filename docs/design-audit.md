# Design audit — the current PitchCraft UI

Input for the design track (the owner with Claude Design, D65). **Facts, not proposals**: this file lists what exists, what it looks like and where it is inconsistent or missing, so the new identity and design system start from the real product. Opinions are marked **Observation**. Open questions for the owner are marked **OWNER**.

Taken on 2026-11-07 at `v2` `8a018c1` (the code of release 3). The component inventory was read from the code by a read-only pass and the numbers are counts over `app/` and `components/` (tests excluded); the screenshots were taken from a scratch copy of the app on a local dev server, with real published data files dropped in the copy. **The repository's `public/data/` was not touched.**

## 1. Screenshots

All in `docs/design-audit/screens/`, full page, CSS pixels. The browser viewports were 1280 px (desktop) and 390 px (phone); the saved images are 1265 and 375 px wide because the page scrollbar is not part of the image.

| File | State | Data used |
|---|---|---|
| `01-demo-desktop.png`, `02-demo-mobile.png` | Demo data: "Demo data: live data unavailable" (amber), two demo games, six demo archive rows | the file now in the repo (`demo_cached`) |
| `03-live-game-desktop.png`, `04-live-game-mobile.png` | Live game day: World Series game 5, one game card, full report, critic review, workflow, 4 archive rows | the file the bot published on 2026-10-28 (commit `79dfe01`) |
| `05-no-games-desktop.png`, `06-no-games-mobile.png` | No-games day, which is **what production shows today**: hero, one line, archive of 5 rows | the file the bot published on 2026-10-30 (commit `492e194`) |
| `07-quality-mobile.png` | `/quality`: an empty page | repo |

**Not captured** (can be added when the design track asks): the postgame view of a final game (it exists only in demo data), the expanded "See detailed analysis" panel, a tooltip open, the hand toggle and pitch hover states, a limited-sample starter, a switch pitcher, an unknown team badge, a keyboard focus ring. The component tests contain fixtures for most of them (`components/__tests__/`).

## 2. Routes and page states

Routes today: `/` and `/quality`. No navigation, header, footer links or `<Link>` anywhere; a game has no URL of its own. `/quality` renders `<main aria-label="Quality" />` and nothing else.

`/` is one centered column, `max-w-3xl` (768 px) with `px-4`, on every screen size; there is no layout beyond it on a desktop (see `03`: about a fifth of the width is empty each side).

| State of `/` | Condition | What shows |
|---|---|---|
| Demo | `data_mode` is not `fetched_snapshot` | amber mode line, demo games, strength-profile radar in the detail panel |
| Live game day | `fetched_snapshot` with matchups | green mode line, game cards, selected game, critic review, "How PitchCraft Works", archive, notes |
| No-games day | `fetched_snapshot`, no matchups, run status `no_games` | hero, the line "No MLB games scheduled on {date}.", archive, notes |
| Empty archive | no rows | "Archive" and "No past reports yet"; the Games header still says "0 archived" |
| Selected via `?matchup=` | initial state only | clicking a card changes state but not the URL; an unknown id silently shows the featured game |
| Final game with no postgame object | status `final`, `postgame` null | rendered as a pregame report (automated postgame was cut, D41) |

Observation: in the offseason the production page reads "Live data · fetched 2026-10-30" and "No MLB games scheduled on 2026-10-30" over a five-row table of rows with no result; it looks like a stale live page.

## 3. Components and their states

All sizes are Tailwind arbitrary values unless named. "Dash" is `—`, the page's one way to say a value is unavailable (`UNAVAILABLE` in `lib/format.ts`).

| Component | Purpose | States it renders |
|---|---|---|
| `Hero` | eyebrow "Starter matchups, checked against the data", h1 "PitchCraft Matchup Agent", one paragraph | none of its own; embeds ModeLine |
| `ModeLine` | pill saying live or demo; `data-testid="mode-line"` | live (green): "Live data · fetched {date}" or "Live data · fetch time not available"; demo (amber): "Demo data: live data unavailable" |
| `GameCarousel` | horizontal row of game cards (plain scroll, no arrows, not a carousel widget) and "{n} archived" | selected (blue border and glow), featured ("recommended" chip), plain, hover (lifts); status chip: upcoming, live (amber), final (green, shows the score only when a postgame object exists), demo, or a dash when the status is unknown; date label "Today" or the date |
| `MatchupView` | the game: pregame or postgame mode | pregame (header card, two starter cards, pitch legend, scouting report, "What to watch", detail toggle, critic review); postgame (final score header, starter cards with Game Score and grade, "Starter duel", plan versus execution, call check) |
| `StarterCard` | one starter: name, bio line, hand and style, ERA/WHIP/K tiles, scope caption, zone diagram, recent form | pregame / postgame; "Bio not available"; "Recent form not available"; a dash for unavailable figures; hand omitted for a switch pitcher; team badge with a null team |
| `ScoutingReport` | two cards "{starter} vs {opponent}" with the report text and OPS, K%, BB% tiles | "Offense data not available" |
| `StatTile` | label and mono value, with a tooltip or a `title` | known stat (tooltip) or other (native `title`) |
| `Tooltip` | hover and focus bubble, Escape to dismiss | always above and centered; no collision handling |
| `DetailedAnalysis` | per starter "How {name} attacks": hand toggle, pitch list, trajectory card, zone | arsenal present; row usage unavailable; no batters faced; arsenal limited; movement missing; locations empty; no arsenal (two wordings); strength-profile radar only for demo |
| `PitchTrajectoryCard` | movement drawing, family chip, velocity and break meters | unmapped family; velocity missing |
| `StrengthProfile` | radar chart (Recharts), demo only | "Not available for live data yet." |
| `ZoneDiagram` | strike-zone dots by pitch | empty; unknown pitch colors grey |
| `CriticReviewPanel` | "Claims Checked": each claim with a status chip | supported, warning, unsupported, not present; "Critic Notes" only when there are notes |
| `AgentPipeline` | "How PitchCraft Works": five numbered steps with status chips | completed, not applicable, pending; hidden on a no-games day |
| `CallCheck` | postgame only: each pregame call with a chip | held up, partially, did not hold up, unclear |
| `ArchiveTable` | the archive, five columns: Date, Matchup, Starters, Result, Grade | empty ("No past reports yet"); populated; Result dash when null; Grade dash when there is no result, otherwise "Pending" |
| `Disclaimer` | footer "Notes", text taken from the data file | the four live notes or the demo notes |
| `TeamBadge` | colored circle with the abbreviation, `aria-hidden` | team color; grey circle for a null abbreviation |
| `PitchMixChart`, `VelocityChart` | Recharts bar charts | **not used by any page** (only by one test); dead code |

Observation: the archive row has no team codes, no score and no link, so the table cannot become a game list without new data (see `docs/plans/R4.md` section 4).

## 4. Design tokens actually in use

There is **no token layer**: no custom colors, spacing scale or dark mode in `app/globals.css`. Everything is Tailwind utilities and literals.

- **Fonts.** IBM Plex Sans 400/500/600/700 for text, IBM Plex Mono 500/600 for labels, numbers and chips (self-hosted, `app/fonts/`). Mono has no 400 or 700 face, so `font-bold` on a mono element is synthesized (team badges, grade circle).
- **Type sizes.** 8 arbitrary pixel sizes (9, 10, 10.5, 11, 12, 13, 15, 27 px) next to 7 named Tailwind sizes. **29 uses are under 11 px** (9 px: 10 uses, 10 px: 15, 10.5 px: 4), mostly mono uppercase labels and chips. The h1 is 27 px; card headlines are `text-2xl` and `text-3xl`; section titles `text-lg` or `text-xl`. There is no named scale.
- **Text color.** `text-neutral-900` (28 uses), `-400` (25), `-500` (24), `-600` (14), `-700` (5), `-800` (2). `text-neutral-400` (#a3a3a3) is used 25 times on white, `neutral-50` and `neutral-100` for labels, captions, the eyebrow, table headers, dates and the footer notes; that is below the usual 4.5:1 contrast for small text. **Observation**, to be checked with a contrast tool.
- **Status palette.** The same four pairs everywhere: green 100/800 (supported, completed, final), amber 100/800 (warning, live, pending, demo), red 100/800 (unsupported, did not hold up), neutral 100/500 (not present, not applicable). Blue 600/50/100/200/700 for selection, featured, links and toggles.
- **Blues are not one blue.** `blue-600` (featured chip), `blue-700` (active toggle, links, focus), `#2563EB` (radar), `#1d4ed8` (bar charts and the focus outline).
- **Charts.** Away `#1d4ed8` or `#2563EB` versus home `#16a34a`; velocity home `#d97706`. Recharts tooltips and legends use library defaults. No text alternative for a chart.
- **Pitch colors.** A 7-key map in `ZoneDiagram` (Four-seam #D85A30, Sinker #1D9E75, Slider #378ADD, Cutter #5B8DEF, Changeup #EF9F27, Curveball #7F77DD; everything else #9E9E9E). Slider and Cutter are two close blues; Sweeper, Splitter and other pitches fall into one grey. Pitch identity is color-only in the zone diagram; the legend and list carry names.
- **Team colors.** `lib/teamColors.ts`, a 36-entry map by abbreviation (30 clubs plus aliases), fallback #71717a. Used for the badge fill, a 3 px top border on starter cards, a 50/50 stripe on game cards, and the **pitch-family chip** on the trajectory card. Never for text or links. Several clubs are near-identical dark navies (ATL, DET, NYY, MIL, SEA, MIN, CLE, CWS). The file says the colors are approximate, not official or licensed.
- **Radii.** `rounded-xl` 20 uses, `rounded-lg` 14, `rounded-md` 11, `rounded-full` 10, `rounded-sm` 1.
- **Shadows.** Cards are flat with a 1 px `neutral-200` border; `shadow-lg` 2, `shadow-sm` 1, and three custom shadows (two blue glows for selected and featured, one hairline).
- **Spacing.** Page `gap-7`, `px-4 py-10`; card padding `p-4` or `p-3.5`/`p-3`; tile `px-2.5 py-2`. No scale beyond Tailwind's.
- **Tracking.** `tracking-wide` 11, `tracking-widest` 8, and custom `0.12em`, `0.14em`, `0.16em` for the uppercase mono labels.
- **Breakpoints.** `sm:` flips several lists from column to row and fixes the table layout; `md:grid-cols-2` for the two starters; `xl:` a three-pane layout in the detail panel; **no `lg:`**. The page itself never widens.
- **Motion.** Only the card hover (`-translate-y-0.5` and a shadow). No loading, skeleton or transition states exist; every page is rendered on the server.

## 5. Accessibility and usability observations

Listed so the design system can fix them by construction. Each was read from the code; none was tested with a screen reader.

- The "See detailed analysis" toggle has no `aria-expanded`; the "vs LHH / vs RHH" toggle has no `aria-pressed`; the selected game card is shown by border color only (no `aria-current`).
- In the detail panel a pitch row changes the selection on **hover, focus and click**, so moving the mouse across the list changes the selection.
- `title` attributes carry the definitions of IP, ER and BB (not available on touch or by keyboard); the other stats use the custom `Tooltip`, which opens above and centered with no collision handling and no touch behavior beyond focus.
- Team badges are `aria-hidden`; the team is carried by adjacent text only. Charts and the radar have no text equivalent beyond an `aria-label`.
- The archive table scrolls sideways on a phone (`min-w-[600px]`), so the Result and Grade columns are cut off (`04-live-game-mobile.png`, bottom). It has no `<caption>` and no `scope` on headers; rows are not links.
- A single global focus style exists (3 px `#1d4ed8` outline); the tooltip trigger has its own.
- The game selector is a scroll row of buttons with one card in it on most days, which leaves a large empty area (`03`).
- Data-driven copy: the footer notes and the workflow step texts come from the data file, not from the components.

## 6. What the new pages need that the UI does not have

For the pages in `docs/plans/R4.md` and R5 (team pages), the current UI has none of:

- **Routing and navigation**: dynamic routes (`/game/<id>`, `/notable`, `/archive`, `/team/<abbr>`), a header or navigation, links between games, back links, 404 and empty-index states.
- **A result display for the archive**: score, winner, round, series line, team codes and a link on every row (data in `docs/plans/R4.md`).
- **A list pattern that works on a phone**: a card or row pattern instead of a table that scrolls sideways.
- **Filters**: a select, two date inputs, a clear action, a result count and a no-match state; none exists.
- **A "why this is notable" pattern**: reason chips with fixed wording (each a registered claim under the data contract).
- **An origin label** that says whether a report was published before the game or written after it.
- **A team page pattern** (R5): a rotation list, per-starter rows with arsenal and labels, a split before and after the All-Star Game, a rookie mark; `Team.record` exists in the types and is never rendered.
- **A width strategy** for desktop beyond a 768 px column.
- **Offseason home**: what the home page says when there are no games for months.
- **Shared tokens** so that every page and the charts use one palette and one type scale.

## 7. Constraints the design must respect

These come from the data contract and the decisions, not from taste.

- **English only** until v2.1 (D31); copy must be easy to move into a catalog.
- **Every sentence that asserts something about data** is a catalog claim with a registry condition (`docs/DATA_CONTRACT.md`, rule 4). The design may restyle copy but a new sentence needs its condition.
- **Unavailable is shown as unavailable** (a dash or a stated reason), never as zero or a blank (rule 2). **Origin and mode are always visible** (rule 6). **No demo content in live pages.**
- **No predictions, no betting, no ads, no trackers, no cookies** (D5, D16, D26). The CSP allows only same-origin scripts, fonts and images plus data URIs (`proxy.ts`); no external font or image host.
- **Team colors are approximate and unlicensed**; MLB and Statcast attribution stays on every page (P1.9).
- **Static, server-rendered pages** reading JSON files; no database (D65). Vercel Analytics counts page views only (D26).
- Mobile first: the audience is a casual fan on a phone (D5).

## 8. Open questions for the owner (OWNER)

1. Does the design track also cover the `/quality` page (it is empty; its content is task P3.2) or only the pages of R4 and R5?
2. Dark mode: in scope for the identity or not?
3. Team colors: keep the approximate map, restrict it to small marks, or drop them in favor of PitchCraft's own palette? (Licensing is not settled in the code.)
4. Should the identity keep the mono uppercase "label" voice, which accounts for most of the sub-11 px text, or replace it?
5. Which of the not-captured states of section 1 does the design track want screenshots of first?
6. Is a logo or wordmark part of the identity? The site has only the text title and a favicon.
