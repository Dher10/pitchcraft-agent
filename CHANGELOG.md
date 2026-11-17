# Changelog

All notable changes to PitchCraft are recorded here, newest first. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the versioning rule is decision D68 in `docs/DECISIONS.md`: MAJOR when the product changes shape, MINOR for new pages, new features or a change of visual identity, PATCH for fixes with no new feature. Every merge of code into `main` is a release with a tag `vX.Y.Z`.

Note on dates: the newest entry says "Unreleased" until the owner merges its pull request into `main` and creates the tag; the date is filled in then. `package.json` carries the version of the newest entry (a test checks it). The daily data commits of the GitHub Actions bot carry no version. `schema_version` and `archive_version` in the published files are contract versions of the data and are independent of the app version.

## [2.1.0] - Unreleased

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
