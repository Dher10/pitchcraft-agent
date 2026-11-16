# R4-U: release B, design system v2 and the R4 pages (plan, for the owner's approval)

Task: R4-U (PLAN.md, "UI part, release B"), units U0 to U7. Decision: D67 (2026-11-15). Sources: `docs/design/` (the approved package; `PLAN_UI.md` is its proposal of these units), `docs/plans/R4.md` (sections 4.4, 4.6, 5, 8), `docs/DATA_CONTRACT.md` (rules 1 to 8, registry 3.3, section 7). Where `R4.md` section 5 and this file differ, this file decides; where this file and D67 differ, D67 decides.

**Deadline:** release B in production by **2026-12-06** (case-study screenshots). **Frozen until February 2027:** R4-P, R5 (team and pitcher pages, TeamDirectory, PitchHeatmap), Today in season, the AttackCard, the Spanish version, writer v3, dark theme values. Nothing of these is started here.

## 1. Where we start (verified 2026-11-15)

- `v2` at `71cc253` contains the bot's archive commit `b739dbb` (owner's merge of `main` into `v2`, PR #5); as of `71cc253`, `v2` is 0 commits behind the release branch. That merge also brought the production daily file (schema 0.9.0, `no_games`, 0 matchups) into `v2`; 7 pytest tests that assumed the earlier copy fail, and CI of `71cc253` is red (run 43753721313). Fixing them is outside this plan and waits for the owner. `public/data/archive/` has 40 game files, `index-2026.json` (22.7 KB) and `manifest.json`.
- Index: 40 rows, `archive_version 1.0.0`, `veteran_min` 5, 30 notable. Tags: `strikeout_duel` 15, `veteran_duel` 12, `series_clincher` 11, `world_series` 5. Reasons per game: 0 (10 games), 1 (18), 2 (11), 3 (1). Rounds: Wild Card 9, Division 16, League Championship 10, World Series 5. Dates 2026-09-29 to 2026-10-28 (two months: September and October). Origins: 35 `reconstructed`, 5 `published_live`.
- Game files: 23,849 to 28,853 bytes each. Every one has both starters `started` and both final lines (IP, H, ER, BB, K). None has pitches, runs, the club's hits, Game Score, verdicts or answers. `game.venue` is present in all 40. `game.start_time_local` is null in all 40, and `start_time_utc` is a `T00:00:00Z` placeholder in 18 (the 5 `published_live` and 13 `reconstructed`) and a time in the other 22, which is not verified; so no first-pitch time is shown.
- **Embedded payload traps:** `matchups[0].status` is `"upcoming"` in the 5 `published_live` files (`"final"` in the 35 others); `metadata.last_updated_label` reads "Live data fetched {date}" and the data confidence note says "This report uses a fetched live snapshot with probable pitchers" in all 40; the report text says "Before first pitch, {team} leads {w}-{l}" (or the like) in 29 (all 5 `published_live`, 24 `reconstructed`). The 5 `published_live` payloads are schema 0.9.0 (the rest 0.10.0). The page takes state, score, series and origin from the **envelope** only; report text appears only inside the labelled block 4 of U3.
- The layout already calls `headers()` (CSP nonce), so every page is dynamically rendered; `searchParams` is a Promise (Next 16.4.1, `node_modules/next/dist/docs/01-app/01-getting-started/03-layouts-and-pages.md`).
- CI runs pytest, vitest, `tsc --noEmit`, eslint and `next build`. No size, secret, docs or link check exists. `tsc` includes every `**/*.ts`.

## 2. Rules for every unit

- **D35 cycle**, one commit per unit: red tests first, seen failing, controls named; implementation; the five suites one by one in the default terminal (`python -m pytest`, `npm test`, `npx tsc --noEmit`, `npm run lint`, `npm run build`); the reviewer subagent (`.claude/agents/reviewer.md`, Sonnet, medium) on the diff with this plan, at most two rounds; commit as Daniel Herdenez, no attribution, whole files; push `v2`; the CI of that commit green before the next unit. Local Windows build: `next build --webpack` when Turbopack panics (QA3-02), stated in the run report.
- **Never** `public/data/`, `evals/live/`, `main`, tags, workflows, `docs/DECISIONS.md`. Each commit is checked with `git diff --name-only <base>..HEAD -- public/data evals/live` printing nothing.
- **Strings.** Every fan-visible string is in this plan (section 5) or comes from it with a slot. A string not listed here stops the unit. Each string that asserts something about data gets its row in `DATA_CONTRACT.md` section 3.3 in the commit that renders it, with a component test of its condition in both directions. Help text only from the glossary of `docs/design/CONTENT.md`, word for word. Strings live in one module per page family (`lib/copy/*.ts`), so v2.1 adds a second column.
- **Data.** Pages read the published files through validated readers; nothing renders from an unvalidated value; unknown is never zero (the dash with "Not available"); a block whose data is not in 1.0.0 is not rendered and leaves no gap, placeholder or "coming soon". The published data replaces every illustrative value of the references (`docs/design/README.md`, "Data in the references"); no illustrative number goes into a fixture.
- **Fixtures.** Real files are read in tests from `public/data/archive/` (read only). Synthetic fixtures for states the real data lacks (`did_not_start`, `unknown`, a null final-line field, a measured 0, a missing index, an invalid index) are built in `components/__tests__/fixtures.ts` and coherent (hits, walks and strikeouts against outs).
- **Visual check.** Each page against `docs/design/reference/screens/` and `reference/html/` at **375, 430 and 1280 px** in a real browser (Playwright, already a dev dependency): no sideways scroll, 44 px targets, the reference's structure, spacing and copy. Screenshots go to the run report, not the repo.
- **Stops** (R4 section 8 and D35): a new decision or schema version; any change to `DECISIONS.md` or `.github/workflows/`; a fan-visible string not in this plan; a finding that changes the scope; CI red twice in a row; two review rounds without PASS; **any place where the data cannot support what the design shows**.

## 3. Check d: the game-after reference against the 1.0.0 file

| Block of `game-after-*.html` | 1.0.0 supports | Release B |
|---|---|---|
| SiteHeader, breadcrumb "Back to the archive", footer | yes | rendered |
| ScoreBoard: round, game number, date, venue, final score, "Final.", series line | yes (`round`, `series`, `date`, `payload…game.venue`, `result`, `series.after`) | rendered |
| ScoreBoard origin line | yes (`origin.kind`, `published_at`, `as_of`); the reference's "…from the box score and pitch data" no | rendered with the B wording (5.3) |
| Why this game is notable | yes, from the game's **index row** (the game file has no tags) | rendered when the row has a tag |
| StarterCard head: club and role, name, hand, style | yes (`starters_check.actual`, payload `throws`, `pitching_profile.style_label`) | rendered |
| One-sentence summary ("Held the Rays to one run…") | no: needs runs; ER only | **not rendered** (5.3, owner question) |
| FinalLine IP, H, ER, BB, K | yes (`final_line`) | rendered, no Pitches cell |
| Tiles Game Score, swings and misses, first-pitch strikes | no | not rendered |
| PitchChart of the game | no | not rendered |
| CallCheck "What we said, and what happened" | no | not rendered |
| Postseason line before and after | no | not rendered |
| QuestionAnswer answers | no | not rendered; the three questions as asked, inside the report block, with no promise of answers |
| How the report was checked: counts before publishing | yes (`critic_review.checks`) | rendered inside the report block |
| How the report was checked: after the game | no | not rendered |
| "Read the report as published" link | no usable target | not rendered (owner, 2026-11-15) |
| Previous and next game of the series | yes (index rows of the same series and team pair) | rendered |

## 4. Units

### U0. Record the decision and the package (docs only) — this commit

D67 appended (D41, D65, D66 marked); `docs/design/` committed with its path fixes and the B game-page order; `D67_DRAFT.md` removed; reviewer frontmatter `model: sonnet`, `effort: medium`; `STATUS.md`, `PLAN.md`, `R4.md` (4.6 note, section 5 pointer, section 8 rows), `README.md` (v2). No code. *Owner: approves this plan.*

### U1. Tokens, fonts, guards

- **Scope:** every token of `docs/design/tokens.json` under `@theme` in `app/globals.css` (colors, type scale, fonts, spacing, radius, shadow, breakpoints `bp-md` 720, `bp-lg` 1024, content width 1120 plus 32 px gutters on each side, which is the 1184 of `DESIGN_SYSTEM.md`); Big Shoulders Display via `next/font/local` (file and license copied to `app/fonts/`, `app/fonts/README.md` updated); IBM Plex Mono removed with its two files and `OFL-mono.txt` if no component still uses `font-mono` after the units that replace them (else removed in the last unit that drops it, U6); the focus ring from the tokens; CSP unchanged (same-origin fonts).
- **Files:** `app/globals.css`, `app/layout.tsx`, `app/fonts/*`, `lib/__tests__/designGuards.test.ts` (new).
- **Red-first tests (guards):** fail on (1) text under 12 px (`text-[<12px]`, `text-xs` below the token floor, `font-size` under 12 in CSS); (2) `text-neutral-400` or lighter on light surfaces; (3) a hex literal in `app/` and `components/` outside the **token definitions in `app/globals.css` and `lib/teamColors.ts`** (owner, 2026-11-15); (4) arbitrary `text-[..px]`. Each guard has a positive control (a planted violation string fails) and a negative control (the token file passes). Existing components that break a guard are listed as named exceptions in the test, each removed by the unit that replaces the component; the list may only shrink.
- **Acceptance:** the five suites green; the exceptions list printed in the run report; the home renders unchanged in structure (A2), now on the tokens; the font loads same-origin.
- **New fan-visible strings:** none.

### U2. Shell and primitives

- **Scope:** `SiteHeader` (logo and wordmark; Today, Notable, Archive; `aria-current`; Today locked with the off-season notice when the season is off; phone tabs 44 px, desktop bar 68 px), `SiteFooter` (links, attribution, non-commercial and no-predictions lines, team-colors line, the credit as a plain link), `ModeLine`, `Button`, `Chip` (status, `feat`, `reason`, `round`), `TeamBadge` (24/34/48), `StatTile`, `FinalLine`, `Help` (tap, focus, hover; Escape and tap outside close; `aria-expanded`; text only from the glossary), `EmptyState` and `Notice`, `GameRow`, the logo and the favicon (`app/icon.svg` from `pitchcraft-favicon.svg`; `app/favicon.ico` removed). **The season switch** is one tested function, `lib/season.ts`: `seasonMode(daily, now)` returns `in_season` only when the daily file is live (`fetched_snapshot`) and its `live_run.target_date` is today in America/New_York with at least one game; otherwise `off_season`. A closed nickname table for the 30 clubs (`lib/teams.ts`, static labels, section 3.4).
- **Files:** `components/site/*`, `components/ui/*`, `lib/season.ts`, `lib/teams.ts`, `lib/glossary.ts`, `lib/copy/site.ts`, `app/layout.tsx`, `app/icon.svg`; tests beside them.
- **Red-first tests:** season switch (today with games, today without games, stale live file, demo file, missing `live_run`, the date boundary at 01:30 UTC); header current item and the locked Today (`aria-disabled`, not a link); Help opens on click and focus, closes on Escape and outside tap, text equals the glossary entry; FinalLine shows 0 for a measured 0, the dash for null, "Final line not available" for a null line, never a Pitches cell when pitches are absent; GameRow accessible name and winner marked by weight and the triangle, not color only; footer link to danielherdenez.com has no tracking parameters and is not styled as a button.
- **Acceptance:** shell on every existing page (home, `/quality`); 375/430/1280 checks of header and footer against the references; the guards' exception list shrinks.
- **New fan-visible strings:** 5.1.

### U3. Game page `/game/<gamePk>`

- **Order** (owner, 2026-11-15; `docs/design/PAGES.md`, "After the game, release B"): (1) ScoreBoard from the envelope; (2) why this game is notable, from the index row; (3) how the starters did: head, FinalLine without pitches, starter notes; (4) the report as published in one block labelled by origin: the paragraphs, the lineup tiles, the three questions as asked, the critic's counts before publishing; (5) previous and next game of the series. Breadcrumb "Back to the archive"; the header's current item is Archive.
- **Reader:** `lib/archiveGame.ts` validates a game file of `archive_version 1.0.0` before any value is presented (envelope keys and types, `game_pk` equal to the route id, `result.status == final`, unequal runs and a matching winner, the starter checks, final-line fields as nonnegative integers or null and IP by the innings pattern) and reads the embedded payload with the existing payload types for both 0.10.0 and the 0.9.0 published files. The id is checked against `^[1-9][0-9]{5,8}$` before any file access; an unknown id, an invalid id, a missing or invalid file give `notFound()` (404 with the EmptyState).
- **Containment of the payload:** only the report block (4) reads report text, lineup tiles and critic checks from the payload. The payload's `status`, `metadata` labels, `data_confidence` notes outside the report's own sections, `archive[]` and `series.standing` are never rendered. A test fails if "upcoming", "live", "Live data", "today" or "before first pitch" appears outside block 4, over all 40 real files; block 4 is the only zone where report text may say them. **Inside block 4**, 24 `reconstructed` reports say "Before first pitch, {team} leads…" under the label "Written after the game, from data through {date}". The sentence describes the series before the game, from data through that date, so it is not false; the report is shown as it was written, and the label says what it is. This is listed for the owner in section 7; if the owner rejects it, U3 stops.
- **Files:** `app/game/[gamePk]/page.tsx`, `app/game/[gamePk]/not-found.tsx`, `components/game/*` (ScoreBoard, StarterResult, ReportAsPublished, SeriesNav), `lib/archiveGame.ts`, `lib/copy/game.ts`, `docs/DATA_CONTRACT.md` 3.3 rows; tests.
- **Red-first tests:** each state of R4 5.2 (published_live, reconstructed, did_not_start with the "Probable starter … started" note, unknown, a null final-line field, a measured 0); 404 for invalid, unknown and malformed ids with no file read for an invalid one; no "today" or "upcoming" on a finished game; a reconstructed report never says "published"; reasons render only for tags in the row; previous/next follow the series of the same team pair and are absent at the ends; page title and description per game.
- **Acceptance:** every one of the 40 real files renders without error; game 849799 matches `game-after-phone.png` and `game-after-desktop.png` for the rendered blocks at 375/430/1280; phone one column, desktop starter cards side by side from `bp-md`.
- **New fan-visible strings:** 5.3.

### U4. Archive `/archive`

- **Scope:** filters (team select of the clubs in the index, matching either side; the Calendar as links, a day or a two-tap range remembered through the URL, bounded months September and October 2026, disabled arrows beyond the index; the reason filter "Any game" plus the four reasons, AND across reasons, a count per pill); the count line; GameRow under `bp-lg`, ArchiveTable from `bp-lg`; 50 per page with previous and next; all server rendered from `?team=&from=&to=&reason=&page=&month=` (`month` is the month the calendar shows, `YYYY-MM`, bounded by the index like the other values and ignored and never echoed when invalid; owner, 2026-11-15) working without JavaScript; invalid values ignored and never echoed; no-match EmptyState naming the filters; index missing: the neutral Notice.
- **Data:** the index alone (`lib/archiveIndex.ts`, extended with pure query functions in `lib/archiveQuery.ts`).
- **Files:** `app/archive/page.tsx`, `components/archive/*` (Filters, Calendar, ReasonFilter, ArchiveTable restyled), `lib/archiveQuery.ts`, `lib/copy/archive.ts`, 3.3 rows; tests.
- **Red-first tests:** query parsing (unknown team, bad date, reversed range, out-of-season date, repeated and unknown reasons, bad page) ignored, never echoed; AND semantics and pill counts on the real index (Strikeout duel 15, Veteran duel 12, Series-ending 11, World Series 5, Any 40); range inclusive; team on either side; the two-tap URL; month bounds; the no-match sentence names exactly what was asked; index-missing Notice; the table has a caption and scoped headers and never scrolls sideways.
- **Acceptance:** `archive-phone.png`, `archive-desktop.png`, `archive-no-match-phone.png` at 375/430/1280 with real data.
- **New fan-visible strings:** 5.4.

### U5. Notable `/notable`

- **Scope:** page head; reason pills ("All notable games" and the four reasons, each with its count; toggles as links; several picked means every reason picked); the count line with Clear; GameRows with all reasons, most reasons first, then newest; "How games are chosen": each R4 4.6 rule in plain words with its count, V read from the index (`veteran_min`); desktop side column, phone after the list; no-match EmptyState with Clear. Server rendered from `?reason=…` (repeatable), invalid values ignored.
- **One source:** the reason labels, the rule sentences and the tag keys come from one table (`lib/notableReasons.ts`), so the pill, the chip and the rule text can never disagree; a test fails if a tag key has no label or rule, or if the rule text and the computed tags disagree on the real index.
- **Files:** `app/notable/page.tsx`, `components/notable/*`, `lib/notableReasons.ts`, `lib/copy/notable.ts`, 3.3 rows; tests.
- **Red-first tests:** counts 30/15/12/11/5 on the real index; AND of two reasons; order; Clear; V in the veteran sentence equals `veteran_min`; empty state; index missing.
- **Acceptance:** `notable-phone.png`, `notable-desktop.png` at 375/430/1280.
- **New fan-visible strings:** 5.5.

### U6. Home, off season

- **Scope:** board hero with the ModeLine ("2026 season archive, final results through {last date}"), title, one sentence, two actions, the SeriesBoard of the World Series (runs per game and wins from the index; each cell a link; the result sentence); the top three notable GameRows (most reasons, then newest) and "All notable duels"; "How PitchCraft works" (three cards). It replaces A2. In season (by `seasonMode`) the home keeps today's daily view unchanged (Today in season is frozen). No TeamDirectory (R5). Without the index it falls back as A2 does. Dead code removed: `PitchMixChart`, `VelocityChart`, the old `Hero` and `GameCarousel` paths no longer reached; IBM Plex Mono if unused.
- **Files:** `app/page.tsx`, `components/home/*`, `lib/copy/home.ts`, 3.3 rows; removal of dead components; tests.
- **Red-first tests:** with the daily job off and the index present, no live ModeLine and no past date shown as "today"; SeriesBoard runs and wins equal the index (MIL 4-1); the top three order; the missing-index fallback; demo data never beside live data.
- **Acceptance:** `home-offseason-phone.png`, `home-offseason-desktop.png` at 375/430/1280, minus TeamDirectory; the guards' exception list is empty.
- **New fan-visible strings:** 5.6.

### U7. Release B

The PR `v2` → `main` with the run report of each unit (strings added, tests, screenshots at 375/430/1280 of the home, a game, notable, archive, no-match) and the Vercel preview checks (a game page reads its JSON in the function, R4 risk R3). Then **stop**: Codex audits the PR (only here), the owner runs the external QA (Antigravity) and merges. After the merge: the case-study screenshots and the monthly visits-per-route export (OQ11).

**Order:** U1, U2, then U3, U4, U5, U6 in that order (one writer at a time, D35), then U7. Target: U1 and U2 by 2026-11-22, U3 to U6 by 2026-12-01, the PR by 2026-12-02, leaving the owner four days for QA and merge.

## 5. Fan-visible strings

Exact text, slots in braces. "Ref" means word for word from the reference HTML or `CONTENT.md`; **"B"** marks a text changed for release B because the reference asserts something the 1.0.0 data cannot support, or a text the references do not give: those need the owner's yes with this plan.

### 5.1 Shell (U2)

- Nav: "Today", "Notable", "Archive" (ref). Teams and Pitchers are not rendered (R5).
- Locked Today: `title` "No games in the off season"; notice "Off season. No games today. Today's games and daily reports return when the 2027 season starts." (ref).
- ModeLine: off season "{year} season archive, final results through {Mon D, YYYY}" (ref; date = last date of the index); demo "Demo data: live data unavailable" (existing). The live form "Live data, fetched {date}" replaces "Live data · fetched {date}" only on pages that show live data (existing condition, CONTENT.md: commas, not middle dots).
- Footer: "How PitchCraft works" (link to the home section), "GitHub" (no "Quality" link: the `quality` page has no content until P3.2, so no page links to it in release B; the route stays for the analytics, D26; owner, 2026-11-15); "Data from the MLB Stats API and Baseball Savant (Statcast), made public by MLB Advanced Media. PitchCraft is an independent fan project and is not affiliated with MLB."; "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features."; "For information only: no predictions and no betting advice. Team colors are approximate."; "Made by Daniel Herdenez" (all ref).
- Logo: accessible name "PitchCraft, home"; wordmark "PITCHCRAFT" (ref).
- FinalLine: "Final line", "IP", "H", "ER", "BB", "K" with full names for assistive tech ("Innings pitched", "Hits", "Earned runs", "Walks", "Strikeouts"); "Final line not available"; "Not available" (ref, CONTENT.md).
- Help: the glossary entries of `CONTENT.md` used in B: ERA, WHIP, K%, BB%, OPS, IP, Final line, Small sample, word for word, with the button names "What is {term}?". **B:** they replace the existing tooltip texts of 3.3 (ERA, WHIP, K, OPS, K%, BB%) where those components are restyled; the existing lineup K% and BB% tooltips ("Share of plate appearances that end in a strikeout/walk.") stay for the lineup tiles, because the glossary's K% defines a starter's rate.
- EmptyState 404: "We could not find that game" (ref) with links "Back to the archive", "Notable duels of 2026".

### 5.2 Notable reasons (shared by U3 to U6)

Short labels (ref): "Strikeout duel", "Veteran duel", "Series-ending game", "World Series game". Round chips: "Wild Card Series", "Division Series", "League Championship Series", "World Series" (the index's closed table).

### 5.3 Game page (U3)

- Breadcrumb "Back to the archive" (ref). Hidden `h1` "{Away nickname} at {Home nickname}, {round} Game {n}" (ref).
- Head line "Game {n}, {Mon D, YYYY}, {venue}" (ref); "Final." (ref); score accessible name "Final score: {away} {r}, {home} {r}" (ref); series line from `series.after` with nicknames: "{nickname} win the series {w}-{l}." / "{nickname} lead the series {w}-{l}." / "Series tied {w}-{w}." (**B**: the reference shows only the first; the closed set is built from `series.after`/`series.over`).
- ScoreBoard origin line (**B**, replaces the reference's "…Everything marked as what happened was added after the final out, from the box score and pitch data."): published_live "The report was published before the game, on {Mon D, YYYY}. The final score and the final lines were added after the game, from the box score." / reconstructed "The report was written after the game, from data through {Mon D, YYYY}. The final score and the final lines are from the box score."
- "Why this game is notable" (ref) with the reason chips.
- "How the starters did" (ref); head "{Nickname}, away starter" / "{Nickname}, home starter" (ref); "{Right|Left}-handed, {style label lowercased}" (ref, from the report's labels).
- Starter notes (R4 5.5): "Probable starter {name}; {name} started." / "Starter not confirmed".
- **One-sentence summary: not rendered in B** (proposal). A sentence from IP, H, ER, BB and K alone would repeat the FinalLine as prose, which `CONTENT.md` rules out ("three figures in a sentence is a table"), and the reference's sentences need runs, which 1.0.0 does not have.
- Report block title "The report" with its origin label (owner, 2026-11-15): "Published before the game, on {Mon D, YYYY}" / "Written after the game, from data through {Mon D, YYYY}". Inside: the report's own section titles and text as published; "What to watch" questions as asked, under "We asked:" (ref); the check line **B**: "Before publishing, {n} claims in the report were tested against the data: {u} unsupported, {w} with a warning." with "none" for 0 (ref form, before-publishing half only).
- Series nav: "Previous game", "Next game", "Game {n}, {Mon D}", "First game of the series", "Last game of the series" (ref and its mirror).

### 5.4 Archive (U4)

Title "Archive"; "Every 2026 postseason game with a report. Pick a team, a day, or a range of days." (ref); "Filter games", "Team", "All teams", "Dates", "Previous month", "Next month", "Next month, no games", "Previous month, no games", "{Month YYYY}", weekday heads "Sun" to "Sat", day name "{Month D}, {n} game|games" with ", start of your range", ", end of your range" or, for one chosen day, ", selected" added to the name of the day it describes (and `aria-current="date"` on those links; owner, 2026-11-15), key "Day with games (number of games)", "Start and end of your range", "Notable reason", "Any game", range "{Mon D} to {Mon D, YYYY}" and the single day "{Mon D, YYYY}", "Clear", count "Showing {n} of {N} games, newest first", no-match "No games match these filters" with the sentence built from what was asked ("The {nickname} did not play between {Mon D} and {Mon D}." / "The {nickname} did not play on {Mon D}." / "No game between {Mon D} and {Mon D} has every reason picked." **B** for the last), "Try other days or another team." and "Clear filters" (ref); paging "Previous page", "Next page", "Page {p} of {P}" (**B**, not in the reference: 40 games fit one page); table caption "2026 postseason games, newest first" (**B**); the submit button "Show games" of the team select; the pager's accessible label "Pages"; the table headings "Date and round", "Game and starters", "Score", "Notable"; the table phrases "Game {n}", "{away} at {home}" and "{starter} and {starter}" (all approved by the owner, 2026-11-15); index missing "The archive is not available right now." (ref).

### 5.5 Notable (U5)

Title "Notable duels of 2026"; "Starting-pitcher matchups of the 2026 postseason, each with the reasons it stands out. Pick one or more reasons to narrow the list." (ref); "All notable games"; count "Showing {n} of {N} notable games: {labels}. Most reasons first, then newest." and with nothing picked "Showing {N} notable games. Most reasons first, then newest." (**B** for the second); "Clear"; "Show all {n}" (ref); "How games are chosen"; "A game is here when at least one of these is true. Fixed rules, computed from the data before the list was built; who won is not one of them. {N} of the {T} postseason games qualify, so pick a reason to narrow the list." (ref with slots); rules: "Both starters strike out batters at an above-average rate: a strikeout rate of 25% or more over a full sample, before the game."; "Both starters had pitched in at least {V} earlier MLB seasons." (**B**: the reference's "at least five earlier MLB seasons" with V as a numeral from the index and "pitched in", which is what `prior_mlb_seasons` counts); "The game decided its series."; "Every World Series game is on the list." (ref); "{n} games" per rule; no match "No game met a rule" / "No games have every reason picked." (**B** for the second) with "Clear".

### 5.6 Home (U6)

- Title "The 2026 postseason, start by start" (ref).
- Sentence (**B**, replaces "What each starting pitcher was expected to do, what he did, and how the report held up. Only what the data supports.", whose last clause needs R4-P): "What each starting pitcher was expected to do, and what he did. Only what the data supports."
- Actions "See the notable duels", "Browse all {N} games" (ref, N from the index).
- SeriesBoard: accessible name "{round}, game by game"; "G{n}", "Wins"; cell names "Game {n}: {nickname} {r}, {nickname} {r}"; "{round}. {nickname} win the series {w}-{l}. Pick a game to see how its starters did." (ref).
- "Notable duels of 2026", "All notable duels" (ref).
- "How PitchCraft works" with "Before the game: A short report on both starters from public MLB data: arsenal, season figures, the lineup each one faces." and "Every claim is checked: Each statement is tested against the data before the report is published. No predictions, no betting." (ref) and (**B**, replaces "The final line, where the pitches went, and whether each claim held up.") "After the game: The final score and each starter's final line, from the box score."

## 6. Risks

| Risk | Mitigation |
|---|---|
| The 0.9.0 published payloads differ from the 0.10.0 types | U3 reads all 40 real files in a test before any component work; a field the type does not have is a finding, not a cast |
| Payload text that sounds live leaks outside the report block | The containment test over all 40 files (U3) |
| A guard flags many existing components at once | Named exceptions that only shrink; the last unit leaves none |
| Calendar links multiply page views (D26, OQ6 accepted) | Plain links, no prefetch storm: `prefetch={false}` on calendar cells; measured in the preview |
| Deadline | The order above with dates; a unit that slips is reported at once with what moves |
| Windows Turbopack build panic | `next build --webpack` locally, stated in each run report; CI builds on Linux |

## 7. Approvals

| Step | Needs the owner |
|---|---|
| U0 | this plan, including every **B** string of section 5, the summary sentence left out of U3, and the 24 reconstructed reports shown with their "Before first pitch, …" sentence under the "Written after the game" label (U3) |
| U1 to U6 | none beyond this plan (D35); a stop of section 2 brings the unit back |
| U7 | the external QA and the merge |

Reminder for the owner before U1 starts: switch this session to Sonnet, effort Medium (D36 roles, `docs/design/PLAN_UI.md`).
