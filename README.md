# PitchCraft Matchup Agent

PitchCraft turns MLB starting-pitcher matchups into fan-friendly scouting reports, with a critic that fact-checks every claim against the same structured data the frontend renders.

## Architecture

PitchCraft is a deterministic multi-agent pipeline. The agents are rule-based and reproducible; no LLM is used.

- Data Scout assembles the matchup packet and records data availability.
- Matchup Analyst turns pitcher, offense, chart, and context inputs into matchup findings.
- Report Writer produces the readable scouting report from those findings.
- Critic / Fact-check verifies each claim against the data and flags unsupported betting, odds, or outcome language.
- Postgame Grader adds a starter-performance readout for completed games.

The pipeline writes the JSON payload consumed by the Next.js frontend at `public/data/pitchcraft-demo.json`.

## Postgame Grading

Postgame grading uses the original Bill James Game Score (1988), the industry-standard single-game pitcher metric. PitchCraft's letter grade is a readability layer on top of the numeric Game Score, not a separate official statistic.

## Data Modes

- `demo_cached`: always works without internet and uses deterministic demo inputs.
- `fetched_snapshot`: fetches the real MLB schedule and probable pitchers from the MLB Stats API, then pitch mix, velocity, and zone tendencies from pybaseball Statcast. The processed snapshot is saved locally.

If any live fetch fails, PitchCraft silently falls back to demo data. The public demo runs from a committed JSON snapshot; the local live snapshot under `data_cache/` is intentionally gitignored.

## Run Locally

Install frontend dependencies:

```bash
npm install
```

Start the app:

```bash
npm run dev
```

Open `http://127.0.0.1:3000`.

Build the frontend:

```bash
npm run build
```

Generate JSON from the current inputs:

```bash
python data_pipeline/generate_demo_json.py
```

Optionally refresh live data:

```bash
python -m data_pipeline.fetchers.live_pipeline [YYYY-MM-DD]
python data_pipeline/generate_demo_json.py
```

Delete `data_cache/processed/live_matchup.json` to return to demo data.

## Security & QA

No secrets or API keys are committed. `.env*`, build artifacts, the live snapshot, and all `data_cache/` contents are gitignored.

Reports contain no betting, odds, or win-probability language. The critic explicitly scans for and flags that language while checking report claims against the structured matchup data.

## Limitations

PitchCraft is a capstone demo, not a betting tool. Internal "Stuff" and strength signals are PitchCraft-specific and are not official Stuff+. Live data covers the featured matchup; other archive rows are illustrative demo data.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Recharts
- Python standard library
- pybaseball
