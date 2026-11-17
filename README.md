# PitchCraft

PitchCraft turns MLB starting-pitcher matchups into scouting reports a casual fan can read on a phone, and checks every claim against the same public data the page shows. It does not predict outcomes and is not a betting tool. It is free, non-commercial and independent of MLB.

This is version 2. Version 1 was a Kaggle capstone, kept in the tag `v1.0.0-kaggle`.

## What the site does now

- **In season:** a daily job read the MLB schedule, built a report for the day's featured matchup and published it before first pitch. It ran through the 2026 World Series and is off until the 2027 season.
- **Off season:** the site is the 2026 postseason in review: every postseason game played (40), each with its final score, the starters' final lines from the box score, and the pre-game report, either as it was published before the game or written after it from data through the day before. Games are tagged with fixed, explainable reasons ("notable duels").
- **Next:** release B, a redesign on the design system in `docs/design/` (decision D67). The after-the-game layer, team and pitcher pages and the Spanish version resume in February 2027.

## How a report is built

A pipeline of rule-based steps, written in Python:

- **Data scout:** fetches the schedule, probable pitchers and season lines (MLB Stats API) and pitch data and team batting splits (Baseball Savant / Statcast), with request caps, caching and pacing.
- **Matchup analyst:** turns the data into labeled findings by fixed thresholds (for example, a strikeout rate of 25% or more is "above-average swing-and-miss ability").
- **Report writer:** writes the report from a catalog of phrases. Production uses this rules writer.
- **Critic:** checks each claim of the report against the data and blocks betting or prediction language. A report that fails is not published.

An LLM writer (Gemini) with a separate LLM judge (Groq) was built and evaluated against the owner's sentence labels (Plan B, `docs/results-planB.md`). The evidence did not support turning it on, so it stays off in production (D65).

What the published files may say, and how each claim is checked, is the data contract: `docs/DATA_CONTRACT.md`.

## Data

- `public/data/pitchcraft-demo.json`: the daily file (schema 0.10.0), written only by the daily job.
- `public/data/archive/`: the 2026 postseason archive (`archive_version` 1.0.0): one file per game, an index and a manifest with a SHA-256 per file, written once by a manual workflow.

Both are committed to `main` by the GitHub Actions bot (D15); no person or agent edits them. The site never shows demo data as live: every page says which kind of data it shows.

## Run locally

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:3000`.

Checks, as CI runs them:

```bash
pip install -r requirements-dev.txt
python -m pytest
npm test
npx tsc --noEmit
npm run lint
npm run build
```

On Windows, `next build --webpack` avoids a Turbopack PostCSS panic in the local build (QA3-02).

## Where to read more

- `docs/PRD_v2.md`: what the product is for and who it is for.
- `docs/DECISIONS.md`: every decision, append-only.
- `docs/PLAN.md` and `docs/STATUS.md`: the plan and where work stands.
- `docs/design/`: the design system and page designs.
- `AGENTS.md` and `docs/CONTRIBUTING.md`: how code and commits are made here.

## Data use

Data from the MLB Stats API and Baseball Savant, © MLB Advanced Media, used for a non-commercial project, cached and requested at a low rate, with attribution on every page (D16). Team colors are approximate.

## Stack

Next.js (App Router), TypeScript, Tailwind CSS, Vercel; Python with pandas and pybaseball for the pipeline; GitHub Actions for the scheduled and manual jobs.
