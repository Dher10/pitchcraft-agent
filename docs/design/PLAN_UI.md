# Plan: release B (design system v2 + R4 UI)

Status: proposal from the planning chat, 2026-11-15, turned into `docs/plans/R4-U.md` under D35/D36; that file is the plan the units run on. It follows `docs/plans/R4.md`; where the two differ, D67 decides.

## Where we start

- Release A is in production (PR #4, merge `95abcd2`); the bot published the archive (`b739dbb`): 40 postseason games, `archive_version 1.0.0`, 30 notable with V = 5. The interim home (A2, `b74a0e7`) reads the index and shows final scores.
- The data contract the UI consumes does not change in release B: `games/<gamePk>.json`, `index-2026.json`, `manifest.json`, the closed codes, the starter's final line from the box score, no grade.
- The owner's replan of 2026-11-14 freezes R4-P, R5, the Spanish version and the writer v3 until February 2027. The PitchCraft case study is published by 2026-12-20, so release B should be in production with screenshots by **2026-12-06** at the latest.

## Scope

| In release B | Frozen until February 2027 |
|---|---|
| Tokens, fonts, guards; header, footer, primitives | R4-P: final line with pitches, Game Score, in-game counts, the game's PitchChart, CallCheck, answers, new notable rules |
| `/game/<gamePk>` after the game, on the 1.0.0 file | R5: `/team/<abbr>`, `/pitcher/<id>`, `/pitchers`, TeamDirectory, PitchHeatmap |
| `/archive` with team, calendar and reason filters | Today in season (the views are designed; verified before the daily job restarts) |
| `/notable` with reasons as filters | The AttackCard on the pre-game page (it belongs to Today in season) |
| Home, off season | Dark theme |

The header shows Today (locked, off season), Notable and Archive. Teams and Pitchers appear only when R5 ships.

## Rules for every unit

- Red first: write the failing test, see it fail, then the code.
- No new fan-visible sentence without its catalog entry and registry condition. The wording comes from `CONTENT.md` and the reference HTML; list each new string in the unit's run report.
- Nothing under `public/data/` or `evals/live/`; never `main`, tags, workflows or force-push.
- Phone first: 375 and 430 px with no sideways scroll and 44 px targets; then 1280 px.
- Compare each page with `reference/screens/` and `reference/html/`: they are the target for structure, spacing and copy; the published data replaces any illustrative value.
- A block whose data does not exist in 1.0.0 is not rendered and leaves no gap, placeholder or "coming soon".
- Stops as in R4 section 8, plus: any place where the data cannot support what the design shows. Report it; do not invent or hide.

## Units

**U0. Record the decision and the package (docs only).** Verify D67 against the repo (see the prompt), owner approves the text, append it, commit `docs/design/`, update `STATUS.md`, `PLAN.md` (roadmap: release B, the freeze) and the R4 plan's section 5 pointer. Also update the repo `README.md`, which still describes v1 ("no LLM is used"). *Owner: approves the D67 text.*

**U1. Tokens, fonts, guards.** Tokens from `tokens.json` under `@theme` in `app/globals.css`; Big Shoulders Display via `next/font/local` (file and license to `app/fonts/`, its README updated); IBM Plex Mono removed if nothing else needs it. Tests that fail on text under 12 px, `text-neutral-400` and lighter on light surfaces, hex literals in `app/` and `components/` outside `lib/teamColors.ts`, and arbitrary `text-[..px]`. Old components listed as exceptions that later units remove. CSP unchanged.

**U2. Shell and primitives.** SiteHeader (Today locked with the off-season notice when the season is off; Notable; Archive; `aria-current`), footer with attribution and "Made by Daniel Herdenez" linking to danielherdenez.com, ModeLine, Button, Chip, TeamBadge, StatTile, FinalLine, Help (tap, focus, hover; Escape closes; text only from the glossary in `CONTENT.md`), EmptyState and Notice, logo and favicon. The season switch is one tested function.

**U3. Game page.** `/game/<gamePk>` from the game file, in this order (owner, 2026-11-15; `PAGES.md`, "After the game, release B"): (1) ScoreBoard (state, final score, series line, origin line for `published_live` and `reconstructed`), all from the envelope, never from the embedded payload; (2) why the game is notable (the tags of its index row); (3) how the starters did: per starter the head, a one-sentence summary only where a catalog phrase supports it from IP, H, ER, BB and K, FinalLine without pitches, starter notes for `did_not_start` and `unknown`; (4) the report as published, in one block labelled by origin ("Published before the game, on {date}" or "Written after the game, from data through {as_of}"): paragraphs, lineup tiles, the three questions as asked (no answers, no promise of answers), the critic's counts before publishing; (5) previous and next game of the series; 404 for unknown or invalid ids. Nothing from the payload that says "upcoming", "live" or "before first pitch" renders outside block 4; no link to the report as published. Blocks that need R4-P are not rendered. Acceptance: every state in R4 5.2; no "today" or "upcoming" on a finished game; a `reconstructed` report never says "published".

**U4. Archive.** `/archive`: GameRow on a phone, ArchiveTable from `bp-lg`; team select; the Calendar as links; the reason filter ("Any game" plus the four reasons); all server rendered from the URL (`?team=&from=&to=&reason=&page=`), working without JavaScript, the two-tap range through the URL; counts; 50 per page; no-match and index-missing states. Invalid query values ignored and never echoed; month navigation bounded by the index.

**U5. Notable.** `/notable` with the reason filter (one or more reasons; a game must have every reason picked; counts on each pill), the count line with Clear, GameRows with all reasons (most reasons first, then newest), and "How games are chosen" with each R4 4.6 rule and its count. The card text and the computed tags come from one source, so they can never disagree. Short labels ("Strikeout duel", "Veteran duel", "Series-ending game", "World Series game") are new catalog strings.

**U6. Home, off season.** Board hero with the ModeLine, the SeriesBoard of the World Series, the top three notable games (most reasons, then newest), and "How PitchCraft works". It replaces A2. Acceptance: with the daily job off and the index present, the home never shows a live ModeLine or a past date as "today"; without the index it falls back as A2 does.

**U7. Release B.** PR `v2` to `main` with the run reports and screenshots; external QA by the owner (Codex audits the PR, Antigravity); the owner merges. Then capture the screenshots for the case study (phone and desktop of the home, a game, notable, archive).

Order: U0, U1, U2, then U3 to U6 (they can run in parallel once U2 is in), U7.

## Models and effort (D36 roles)

| Work | Tool | Model, effort |
|---|---|---|
| Orchestrator: read the unit, delegate, judge, report | Claude Code | Opus, medium |
| U0 (docs) | writer | Sonnet, low |
| U1 to U6 | writer / reviewer | Sonnet, medium / the reviewer subagent (`.claude/agents/reviewer.md`, Sonnet, medium; D35) |
| U3 (many states) | writer | Sonnet, medium; Opus medium only after a repeated BLOCK |
| U7 | Codex audits the release PR only | medium |

## After February 2027 (not in release B)

- **R4-P:** `docs/plans/R4-P.md` first (data and request budget for the game's pitch rows, the `postgame` block and the new `archive_version`, pre-registered verdict and answer rules, notable v2), then build. Owner approves the plan, the budget, the thresholds after a dry run, and the release.
- **R5:** `docs/plans/R5.md` (team and pitcher pages, pitchers index, TeamDirectory, PitchHeatmap counts and minimum samples, Today in season with the AttackCard, readiness for restarting the daily job).
