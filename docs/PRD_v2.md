# PitchCraft v2 — PRD

Owner: Daniel Herdenez · Status: Draft v0.1 · Date: 2026-10-10
Related: `eval-spec.md`, `DECISIONS.md`, `PLAN.md`

## 1. Summary

PitchCraft turns each day's MLB starting-pitcher matchups into scouting reports a casual fan can understand. Reports are generated and published automatically every day, and every report is checked against the data before it is shown. PitchCraft does not predict outcomes and is not a betting tool. v2 takes it from a manually run capstone to a live, reliable and measurable product.

## 2. Problem

**For the fan.** Someone checking today's games sees a pitcher's name, an ERA and little else that means anything without context. The useful data (arsenal, velocity, movement, opponent splits) exists, but it lives in dashboards built for analysts. Nobody translates "38% four-seam, 27% slider" into "here is what to watch tonight."

**For an AI-written product.** Once a model writes the report, it can invent a number or state something the data does not support. Without a way to measure and control that, the product cannot be published to fans responsibly.

## 3. Goals

**Purpose goals (not commercial).** PitchCraft has no revenue model. It exists as public, verifiable evidence of building and measuring an AI product, and as a showcase of responsible AI practices: source transparency, fact-checking and honest handling of missing data.

**Product goals**

1. A fan without deep baseball knowledge understands the duel and knows what to watch.
2. Every published report has its content verified against the data before it goes live.
3. The system runs every day with no manual intervention.
4. Every report is transparent about its origin and the quality of the data behind it.
5. When the sample is thin, the report says so instead of filling the gap.
6. Bilingual product: English in v2, Spanish in v2.1 (D6).

## 4. Users

**Casual fan (primary).** Follows baseball loosely, knows the basic rules, does not read advanced stats. Pain: loose names and numbers that say nothing; analyst dashboards overwhelm. Needs a plain-language read of today's duel and what to watch.

**Postseason newcomer.** Usually skips the regular season and arrives in October because of the buzz. Knows even less. Pain: wants to know why this game matters and what makes these pitchers interesting. Needs context that pulls them into the story fast.

Scouts and analysts are not users: they already have better tools (D5).

## 5. Use cases

1. **Today's preview.** As a fan, I want today's starter duels explained in plain language, so I understand what is at stake without decoding stats.
2. **What to watch.** As a fan, I want concrete things to watch in each game, so I can follow it with more judgment.
3. **Yesterday's recap.** As a fan, I want to see how yesterday's starters did, so I can close the loop.
4. **Transparency.** As a fan, I want to know whether a report was written by AI or by rules, and whether the data is complete, so I know how much to trust it.
5. **Postseason moment.** As a newcomer, I want context on why this duel matters, so I can get hooked on the game.
6. **Quality page.** As a visitor curious about how the product works, I want to see how report quality is measured, so I can trust it.

## 6. Functional requirements

- **FR1 Data extraction.** Daily schedule and probable starters, each starter's arsenal (pitch mix, velocity, movement), opponent splits vs. pitcher hand, and series context in the postseason. Every fetch uses `as_of = game_date − 1`. Starter fields never fall back to demo values in live mode.
- **FR2 Sample sufficiency.** Each dimension (arsenal, strikeout, control) has its own minimum sample. Below it, the dimension is flagged as limited and the report says so. Labels are rate-based, not count-based. Thresholds: D11.
- **FR3 Report generation.** Two writers behind one interface: rules-based (current, bug-fixed) and LLM. The LLM writer outputs the report schema plus `claims[]`, each citing the data field that supports it. With limited data it writes about what exists and states what is missing.
- **FR4 Verification and guardrail.** Code checks run on every report: numeric grounding, forbidden language, coverage, format. On failure, one informed retry with the error. On second failure, the rules-based report is published. Every attempt is logged (D2).
- **FR5 Source signals.** Each report shows its origin (AI-written / Rules-based) and any limited-data dimensions (D3).
- **FR6 Postgame.** Grade yesterday's starters (Game Score) automatically.
- **FR7 Postseason layer.** In postseason games, add series context and cited biographical facts: draft year and round, MLB debut, birthplace (D7). International signings have no draft record and must be handled.
- **FR8 Automation and offseason.** A daily scheduled job runs the full pipeline and publishes. On days with no games it exits cleanly and the site shows the archive.
- **FR9 Quality page.** Shows offline eval results (the decision) and daily monitoring (operations).

## 7. Out of scope

- Outcome prediction, betting, odds or win probability. Permanent.
- Individual batters or full lineups.
- In-game, pitch-by-pitch coverage.
- Native mobile app.
- Accounts, favorites, personalization.
- Comparing several LLMs against each other.
- Spanish: **deferred to v2.1**, not dropped.
- "Hometown connection" stories (needs geo logic beyond available fields).

## 8. Technical considerations

- **Stack:** Next.js + TypeScript + Tailwind on Vercel (unchanged). Python pipeline and agents.
- **Data:** MLB Stats API (schedule, probable pitchers, player bio, series status) and Statcast via pybaseball.
- **Models:** writer on Gemini (Google AI Studio free tier); judge on a different model family via GitHub Models free tier. Provider swappable by env var. Public MLB data only (D9).
- **Runtime:** GitHub Actions on a daily cron; writes JSON to the repo; Vercel redeploys. No servers, $0.
- **Storage:** append-only JSONL per day for monitoring; no database.
- **i18n:** no user-facing strings hardcoded in agents; language is a parameter for writer and eval.

## 9. Success metrics

**Quality (offline frozen set; decides whether the LLM writer ships).** Proposed thresholds, owner to confirm:

- Groundedness: ≥95% of reports with zero unsupported claims.
- Policy: 0 reports with betting or prediction language.
- Fan usefulness: LLM wins or ties vs. rules in ≥70% of pairs.
- Judge trust: judge–human agreement ≥85% per judged dimension.

**Operations (live, daily).**

- % of days the job completes with no manual intervention.
- % of reports needing a retry or falling back to rules.

This year's live history will be short (a few postseason weeks). Operational metrics carry real weight from the 2027 season on.

## 10. Risks

- Statcast blocks cloud runners → heavy fetch runs locally and Actions uses the cache.
- Free-tier limits change → caching, resumable runs, swappable provider.
- Leakage in historical data (season stats, series status) → `as_of` on every fetch.
- Postseason ends before v2.0-a ships → two-step rollout; cut order in `PLAN.md`.
- Judge self-preference → cross-family judge plus human calibration.

## 11. Rollout

- **v2.0-a (target Oct 25):** Phase 0 fixes, daily automation, rules-based writer, source signals, postseason layer.
- **v2.0-b (target Nov 15):** LLM writer enabled only if it passes the eval; case study published.
- **v2.1:** Spanish.

## 12. Open questions

- What exactly makes a postseason report different in the text (D7).
- Final copy for source badges (D3).
- Final sample thresholds after looking at real distributions (D11).
