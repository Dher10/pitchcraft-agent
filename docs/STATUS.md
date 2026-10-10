# PitchCraft v2 — Status / handoff

Updated by whichever agent finishes a task. Keep it short. Newest session on top.

## Current state

- **Phase:** Phase 0 in progress. S0, P0.0, P0.1 (`b73368a`), P0.1b, P0.2 (`d34d49b`), P0.3 (`2a5490d`), P0.3b (`d948cbb`) done; P0.4 analysis written, not approved.
- **Branch:** `v2` (D14). `main` serves v1.
- **Next task:** `PLAN.md` → P0.7 `[auto]`, then P0.8, P0.9 (owner's order). P0.5 is skipped until the owner decides on `docs/thresholds-proposal.md`. Stop before P1.0.
- **Blocked:** nothing.
- **Half-done:** nothing. The first GitHub Actions run of `tests.yml` was green (run 38084965586, job `pytest`, commit `062bf13`), so Python 3.14 on `setup-python` v5.6.0 works. Moving the workflow off Node 20 actions and onto `ubuntu-24.04` is now part of P1.0.
- **Open finding (not in any task yet):** live matchups still inherit the demo `game.broadcast_note` ("Demo matchup for capstone"). Not shown in the UI; belongs with P0.8 (explicit data mode).
- **Committed JSON not regenerated:** `public/data/pitchcraft-demo.json` still holds the old live starter and team fields until the generator is next run.

## Pending Notion sync

Changes made in the repo that the owner still needs mirrored to Notion:

- New `docs/thresholds-proposal.md` (P0.4 analysis: 2026 distribution and threshold options; a proposal, nothing approved).
- D23 (Savant request ceiling: 210 requests, once, cached, 2 s pause) added to `DECISIONS.md`.
- P0.1: live starters now show "Bio not available" and "Recent form not available" instead of demo text. The bio source comes with P1.5.
- New plan task P0.1b (team `offense_profile` never inherits demo values), placed after P0.1. Done: live team offense and record show "not available" instead of demo values; when a team has no split, the report makes no offense claims and the Data Confidence Note says so.
- P1.0 now also covers: checkout and setup-python versions without Node 20 (pinned by SHA) and runner fixed to `ubuntu-24.04`.

Last Notion sync: 2026-10-10, from the initial docs commit.

## Session log

### 2026-10-10 — P0.6 starter names never split (Claude Code, auto lane)

- Root cause: `_watch_observation` in `agents/report_writer.py` split the subject of "Can <name> <action>?" at the first space (or at the third word for names starting with "Pitcher" / "Demo"), so "Can Corbin Burnes land the slider…" became "whether Corbin can Burnes land…" and even "Pitcher A" gave "whether Pitcher A land can the slider".
- Fix: the subject is matched against the full starter names of the packet (longest first); where a name ends is never guessed. An unmatched subject is left as written.
- Tests: `tests/test_report_writer_names.py` (24 cases: 11 name shapes × 2 checks, home starter, unmatched subject). 21 seen failing on the old code, then passing. Local run: 80 passed.
- Gherkin "Pitcher name is never split": covered for the rules writer by these tests. The LLM writer will need the same check in P2.2 (claims are checked against starter names).
- No product behavior change beyond the sentence; nothing to add to Pending Notion sync.

### 2026-10-10 — P0.4 threshold analysis (Claude Code, analysis only)

- Wrote `docs/thresholds-proposal.md`: sources, method, the 2026 distribution of the sample before each of the 4,858 starts, and for each dimension how many starts and pitchers each threshold would flag. Nothing implemented; `DECISIONS.md` untouched; P0.4 left unticked because its acceptance needs the owner's approval and a recorded decision.
- Measured with 27 weekly league-wide requests to the MLB Stats API (no Statcast bulk download). Start count equals the sum of final `gamesStarted`.
- Headline: strikeout at 70 BF flags 20.5% of starts; control at 170 BF flags 41.2%; arsenal at 100 pitches flags 10.7%. Home-run rate needs 1,320 BF and no 2026 starter passed 894, so it cannot be labelled honestly in one season. The 100-pitch arsenal value has no published stabilization source (closest verified: Stuff+ at 72).
- Open owner decisions are listed at the top of the document.

### 2026-10-10 — P0.3b pitcher game_type filter and Savant request budget (Claude Code)

- `fetch_pitcher_statcast` keeps only `R` and postseason (`F`, `D`, `L`, `W`) rows; spring training (`S`), exhibition (`E`) and all-star (`A`) never count, even when dated before `as_of`. Postseason rows count only when dated on or before `as_of`, through the existing date filter. This closes the open finding from P0.3. If the frame has no `game_type` column the filter is skipped.
- Savant team-batting fetch: `_savant_get` sleeps 2 s before every request except the first of the run, counts only real HTTP requests (cache hits are free) and raises `SavantRequestCapExceeded` before request 211 (30 teams x 7 monthly chunks). `fetch_team_splits` re-raises it instead of returning `{}`, so the run stops. The pybaseball pitcher fetch is a different path and is not counted.
- Tests: 7 new (1 in `test_fetchers_as_of.py`, 6 in `test_team_splits_as_of.py`; the new ones seen failing first). Local run: 56 passed.
- D23 (the 210-request ceiling) was approved by the owner and added to `DECISIONS.md` in this commit.
- Not checked, noted for P0.5 / P2.4: pitcher ERA / WHIP / IP come from the MLB API (`stats=season` / `byDateRange`); whether they include postseason games is unknown, so for a postseason case they could differ from the Statcast counts, which now include postseason games before `as_of`.
- No product behavior change; nothing to add to Pending Notion sync.

### 2026-10-10 — P0.3 team splits by date range (Claude Code, auto lane)

- **Finding:** the MLB Stats API cannot give a date-bounded split by pitcher hand. `statSplits&sitCodes=vl,vr` ignores `startDate`/`endDate` (same PA 1963 / 4034 for a window ending 2026-04-05 as for the full season); `byDateRange` honors the dates but returns one total row and ignores `sitCodes` / `opposingPlayerHand`; `byDateRangeAdvanced` and `/stats` with `sitCodes` return nothing.
- **Derived from Statcast instead.** Deviation from the approved plan: `pybaseball.statcast(team=...)` filters by *pitching* team (`player_type=pitcher` is hardcoded in the library), so it returns no batting rows for the team, and it needs one request per day (205 requests, 5.5 min per team). `fetch_team_batting_statcast` asks Savant directly with `player_type=batter&hfGT=R`, one request per calendar month (7 per team-season, never league-wide), sequential, with finished months cached trimmed under `data_cache/raw/team_batting/` (git-ignored). A month that reaches Savant's 25,000-row cap raises instead of truncating silently. `derive_team_splits` counts completed regular-season PAs by the batting team on or before `as_of`; `fetch_team_splits(..., as_of)` uses both (Savant's code for ARI is `AZ`). Without `as_of` the API path is unchanged. This replaces the `{}` that P0.2 returned.
- **Validation (the plan's stop condition), as_of 2026-10-10 vs the API's season splits:** NYY and ARI, both hands, exact match on PA, K, BB, AVG and OPS (e.g. NYY vs RHP: 4034 PA, .714 OPS both). Mid-season check, NYY as_of 2026-07-14: last game date in the data 2026-07-12, 1235 / 2367 PA vs 1963 / 4034 for the full season.
- Tests: 17 new in `tests/test_team_splits_as_of.py` (Savant mocked, cache in tmp_path; 13 failing and 4 erroring first); the P0.2 test that asserted `{}` was removed because the behavior it checked is replaced. Local run: 49 passed.
- Volume (D16): 7 sequential, cached requests per team. The 40-case eval at P2.4 is at most 80 team-seasons; each team-season is cached once, and the same cached months serve any `as_of`.
- No product behavior change (callers still use `as_of=None`); nothing to add to Pending Notion sync.

### 2026-10-10 — P0.2 `as_of` in every fetcher (Claude Code)

- `as_of` is an ISO date, inclusive (data dated on or before it); `None` = today, so current behavior is unchanged. Fetchers in `live_pipeline.py`: `fetch_pitcher_statcast` (end date = `as_of`, plus a `game_date <= as_of` filter), `fetch_pitcher_season_stats` (`byDateRange` Jan 1 → `as_of`; `as_of` must be in `season`), `fetch_team_splits`, and new `fetch_series_status`. Callers (`build_live_snapshot`) are not wired yet; that comes with P0.7 and the eval dataset.
- **Team splits (input for P0.3):** `statSplits&sitCodes=vl,vr` ignores `startDate`/`endDate` (same PA 1963 / 4034 with or without a range ending 2026-06-30), and `byDateRange` drops the vl/vr split. With `as_of` set, `fetch_team_splits` returned `{}` (unavailable) instead of leaking season-to-date numbers; P0.3 replaced that with splits derived from Statcast.
- **Series status:** the schedule's `seriesStatus` is the standing *after each game*, not the final result (checked on the 2026 ALDS/NLDS: game 3 shows "leads 2-1" while the series ended 3-1). This corrects the planning note above ("past series status shows the final result"); that only holds when reading the series' last game. `fetch_series_status` returns the standing after the last earlier game of the same series dated ≤ `as_of` (0-0 for game 1); `{}` outside the postseason.
- Tests: 18 new in `tests/test_fetchers_as_of.py` (network and Statcast mocked; 15 seen failing first, 3 were unchanged-behavior checks). Local run: 33 passed. Real calls with `as_of`: Burnes season stats before his first start → `{}`, through 2026-09-30 → 10.1 IP; Statcast through 2026-09-14 → 7.2 IP (his two starts, 3.0 + 4.2); series standings before games 1, 3 and 4 as expected.
- `requirements-dev.txt` now includes `requirements.txt`: CI only installed pytest and `live_pipeline` imports pybaseball/numpy/pandas.
- Gherkin "As-of cutoff prevents leakage" and "Series status has no leakage": fetcher level covered by the tests above; the end-to-end scenario needs the callers wired (P0.7, P2.4).
- No product behavior change; nothing to add to Pending Notion sync.

### 2026-10-10 — P0.1b live team fields without demo values (Claude Code)

- Root cause: `_apply_offense_split` returned early when a team had no split, leaving the demo template's offense fields (and `record`) on a real team; the analyst then wrote them into the report as facts. Second bug in the same path: a missing field inside a real split became the string `"N/A"`, which the analyst parsed as 0.0 and turned into "has struggled against RHP pitching (N/A OPS)".
- Fix: unavailable is `None`. `_apply_offense_split` resets `summary_label`, `ops_vs_hand`, `k_rate_vs_hand`, `bb_rate_vs_hand`, `recent_form` to `None` and fills only what the split has; team `record` is `None` for live games; `_format_ops` / `_format_pct` return `None`. `matchup_analyst` uses `_optional_rate` (no OPS claim without OPS; K% / BB% notes and pressure points only for real values; removed the unused `_rate_value`). `report_writer._confidence_note` no longer claims offense splits when a team has none. `ScoutingReport` shows "—" and "Offense data not available". `lib/types.ts` allows `null`.
- Tests: 5 new in `tests/test_live_starters_no_demo_fields.py` (no splits, partial split, agents without splits, one missing metric, demo regression). Written first, 4 seen failing on the old code (one showed the "N/A OPS" sentence), then passing. Local run: 15 passed. `tsc --noEmit`, `eslint` on changed files and `npm run build` clean. A split-less live payload also passes `validate_payload` (94 checks) in memory.
- Gherkin "Live starters carry no demo fields": covered for starters (P0.1) and team fields (this task) by automated tests.

### 2026-10-10 — P0.1 live starters without demo fields (Claude Code)

- Root cause: `_apply_live_starter` overwrote only name, hand, `season_summary` and `pitching_profile` on a deep copy of the demo template, so the template's `bio` and `recent_form` stayed under a real pitcher's name.
- Fix: live starters get `bio = None` and `recent_form = None`. `StarterCard` shows "Bio not available" / "Recent form not available". `matchup_analyst._starter_findings` and the `validators.py` bio check accept `None`. `lib/types.ts` updated.
- Tests: `tests/test_live_starters_no_demo_fields.py` (3 tests). Written first and seen failing on the old code (demo recent-form text in the starter and in the findings), then passing. Local run: 10 passed. `tsc --noEmit`, `eslint` on the changed files and `npm run build` clean.
- Gherkin "Live starters carry no demo fields": covered by the automated test above.
- Also closed: confirmed with `gh run view` that run 38084965586 is green.

### 2026-10-10 — P0.0 test infrastructure (Claude Code)

- Added `requirements-dev.txt` (pytest 9.1.1), `pytest.ini`, `tests/` and `.github/workflows/tests.yml` (push to `v2` + manual; `contents: read`; actions pinned by SHA: checkout v4.2.2, setup-python v5.6.0; Python 3.14 as local).
- `tests/test_commit_msg_hook.py` (6 tests): valid message accepted; rejects no-prefix subject, no body, other author, other committer; strips `Co-Authored-By`. Mutation-checked on temporary copies of the hook (via `COMMIT_MSG_HOOK`): each mutation fails exactly its test; the real hook was not modified.
- `tests/test_demo_agents_smoke.py`: five agents over demo data in memory; asserts nothing under `public/data` or `data_cache` changes; does not import `live_pipeline` or `generate_demo_json`.
- Local run: 7 passed. `.gitattributes` already forces LF on `.githooks/*` (verified).
- No product behavior change; nothing to add to Pending Notion sync.

### 2026-10-10 — S0 setup (Claude Code)

- Created `.claude/settings.json` (attribution off, D21). Ran `git config core.hooksPath .githooks`.
- Removed the contradictory git lines from `AGENTS.md` (owner edit); D20 governs.
- Committed as `2147676` and pushed to `v2`. Post-commit check passed: author Daniel Herdenez, no attribution.

### 2026-10-10 — Git workflow (Claude chat)

- Found commit `564b5f7` authored as `Claude <noreply@anthropic.com>` with attribution trailers, made by a cloud session in July. Left in history (rewriting `main` and the tag is riskier than the issue).
- Added `docs/CONTRIBUTING.md`, `.githooks/commit-msg`, `.gitattributes` and `.claude/settings.json`. Decisions D20–D21.

### 2026-10-10 — Audit (Claude chat)

- Full history scan: no secrets in any commit or branch. `.env*` and `*.pem` ignored.
- `npm audit --omit=dev`: 1 critical (next), 4 high, 1 moderate; all fixed by Next 16.4.0. Practical exposure low (static site: no middleware, Server Actions or `next/image`), fixed anyway in P0.9.
- Stray `pitchcraftvisualpolish.bundle` committed in `5a8c5cc`; `pybaseball` unpinned; no test infrastructure.
- Added P0.0, P0.9, P1.0, P1.8, P1.9; reordered P0.4/P0.5; decisions D15–D19.

### 2026-10-10 — Planning (Claude chat)

- Audited v1 code. Findings recorded in `PLAN.md` Phase 0: demo `recent_form`/bio leaking into live starters; count-based labels with duplicated logic; no sample thresholds; season-to-date fetches cause leakage for historical games; Critic does not read report text; name-split bug; silent fallback to demo.
- Verified MLB Stats API: player profile includes birth city/state/country, draft records (year, team, round, school) and MLB debut date; schedule includes series description, game number and series status. Past series status shows the final result, so it needs an `as_of` rebuild for historical cases.
- Created `PRD_v2.md`, `eval-spec.md`, `DECISIONS.md` (D1–D14; D15–D19 added in the audit), `PLAN.md`, this file and the new `AGENTS.md`.
