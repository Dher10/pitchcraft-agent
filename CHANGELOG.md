# Changelog

All notable changes to PitchCraft are recorded here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versioning rule is decision D68 in `docs/DECISIONS.md`: MAJOR when the product changes shape, MINOR for new pages, new features or a change of visual identity, PATCH for fixes with no new feature. Every merge of code into `main` is a release with a tag `vX.Y.Z`.

## [2.2.0] - 2026-11-19

A page size choice on the archive, and a site icon at the address browsers ask for.

### Added
- `/archive` lets you choose how many games each page shows: 10, 20, 50 or All, with a row of links, "Games per page", that works without JavaScript. The default is 20 (it was a fixed 50). The choice is the `per` parameter of the address (`10`, `20`, `50` or `all`; any other value is ignored and never printed); changing it keeps the team, days, reasons and month and goes back to the first page, and the pager, the calendar and the team form keep it. When the list has more than one page the count reads "Showing 21 to 40 of 40 games, newest first".

### Fixed
- `/favicon.ico` returned "not found". It now returns the site icon, the mark of `app/icon.svg` in 16 and 32 pixels.

## [2.1.1] - 2026-11-18

Fixes after release 2.1.0: the game 404 without JavaScript and a clearer range on the archive calendar.

### Fixed
- An unknown or invalid game URL (`/game/<id>`) now shows its heading, "We could not find that game", and the links back to the archive and the notable games with JavaScript disabled, still with status 404. Before, the page body was empty without JavaScript.
- The archive calendar shows a chosen range more clearly: the days between the start and the end are filled and underlined in the signal color (a day without games keeps only the line), each day with games between the start and the end has ", in your range" added to its accessible name, a line above the calendar explains the two taps, and a line right under the calendar, beside "Clear", names the chosen days and how many games the list shows for them with the team and reason filters picked. The key under the calendar has a third item, "Days in your range", with a swatch in the same fill and line.

### Security
- soupsieve updated from 3.0.4 to 4.1.1, which fixes GHSA-mmhr-3c5m-f64f (CVE-2026-126190, high, polynomial-time denial of service in the descendant combinator). It is a transitive dependency of the data pipeline through pybaseball and beautifulsoup4, and the pipeline is not known to reach the affected code.
- A picomatch advisory (GHSA-fc5q-39xc-vjpf) reported during this release was withdrawn by GitHub on 2026-11-18.

## [2.1.0] - 2026-11-17

Offseason experience: a new visual identity and the pages that read the published 2026 archive. Covers pull requests #3, #4 and #6.

### Added
- `/game/<gamePk>`: one page per game after it was played, with the final score, why it is notable, each starter's final line from the box score, and the report as it was published (or written after the game), labelled by its origin. An unknown or invalid id is a 404.
- `/archive`: team select, a calendar of day links with a two-tap range, reason filters with counts, game rows on a phone and a table from 1024 px, 50 per page. Rendered on the server from the URL, so it works without JavaScript.
- `/notable`: the 30 notable games of the 2026 postseason archive, with the reasons as filters and a "How games are chosen" section that lists each rule and its count.
- Archive data pipeline (`archive_version` 1.0.0): final results, one file per game, notable duels and the final starter line from the box score, under a request ceiling (MLB 319, Baseball Savant 190). It runs from a manual workflow only; the published archive has 40 games.
- Evaluation code, data and results of the writer experiment (Plan B) in `docs/results-planB.md`.

### Changed
- New visual identity (design system v2, `docs/design/`): scoreboard look, Big Shoulders Display, one header and footer on every page, light theme.
- `/` in the off season is the season in review: the World Series line score, the top three notable games and how PitchCraft works. In season, or without the archive index, the daily view is unchanged.
- The live mode line now reads "Live data, fetched {date}".
- Schema 0.10.0 adds `label_cutoffs`; it is backward compatible with the published 0.9.0 file.
- Archive table and empty-day layout fixes.

### Fixed
- The archive's team filter works without JavaScript: the Content Security Policy now allows same-origin form submissions (`form-action 'self'`).
- The archive view shows its "not available" notice for a valid archive index with no games, instead of failing while building the calendar (the `/archive` page already guarded this case).
- Every link and button on the release pages is a target of at least 44 by 44 px at 375, 430 and 1280 px: the series board on a phone puts each club's games on their own row, the calendar days are wider on a phone, and the footer links, the logo, the archive table's game links and the notable page's "Clear" link are taller or wider, with the same look.

### Security
- Nonce-based Content Security Policy and security headers.
- Next.js updated from 16.4.1 to 16.4.6, which includes the fix (16.4.5) for GHSA-mfr8-8qww-v76h (moderate, information disclosure across root params through `unstable_cache()` with `use cache`). The app uses neither, so it was not reachable; the update clears the advisory. `eslint-config-next` moves with it.
- The LLM writer cannot run in production; production stays rules-only.

### Not included
- The after-the-game layer (pitches, Game Score, verdicts, answers), team and pitcher pages, Today in season and the Spanish version.

## [2.0-a] - 2026-10-24

Verified daily matchup reports. Covers pull requests #1 and #2 (tag `v2.0-a`).

### Added
- A written data contract of eight rules, enforced when files are published: every published figure carries its source and scope, unknown is never shown as zero, and a failure in one game never invents data.
- A daily GitHub Actions job that publishes the day's games, with a capped and cached request budget for MLB and Baseball Savant data.
- Postseason series context in the reports.
- A live archive of past reports and a no-games state for off days and the offseason.
- A rules-based report writer; every claim is checked against the same data the page shows.
- Six independent QA gates in Phase 0 and two release gates in Phase 1, run by a different AI tool than the one that wrote the code (reports in `docs/qa/`).

### Security
- Pinned third-party actions, least-privilege workflows, a deploy key that can only be used from `main`, branch rulesets and a git guard for coding agents.

## [1.0.0] - 2026-07-04

The Kaggle AI Agents Intensive capstone (tag `v1.0.0-kaggle`, frozen on this date and protected).

### Added
- A deterministic five-agent pipeline in Python with no LLM: Data Scout, Matchup Analyst, Report Writer, Critic / Fact-check and Postgame Grader.
- A Next.js frontend that renders the generated JSON: games carousel, starter cards, lineup splits by pitcher hand, pitch mix, velocity, movement and zone charts, and the critic's review.
- Two data modes: `demo_cached` (offline, deterministic) and `fetched_snapshot` (MLB Stats API schedule and probable pitchers, Statcast pitch data).

### Known limitations
- A failed live fetch fell back to demo data without saying so.
- Live matchups could inherit fields from demo inputs.
- There was no automated test suite or CI.
