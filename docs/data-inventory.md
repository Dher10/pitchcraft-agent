# Inventory of the published payload (live mode)

Read-only inventory of every field of `public/data/pitchcraft-demo.json` when it is built from a live run. Written to be the input of the data contract. It is **Annex A of `docs/DATA_CONTRACT.md`** (D34): findings F1 to F18 below are the known violations of that contract at HEAD `043db03`, and the contract's section 4 says which commit closes each. The inventory is a snapshot and is not updated as the findings are closed. Nothing in the code was changed to produce it.

- **Code state:** branch `v2`, HEAD `043db03` (P0.15-A, B and C done; D paused).
- **Date:** 2026-10-12.
- **How it was made:** (1) a real live payload was built in memory with the generator and the pipeline's own functions (`build_payload()` over a complete snapshot and over a two-debut snapshot, nothing written to the repo); (2) every producer was read (`live_pipeline.py`, `live_matchup.py`, `generate_demo_json.py`, `labels.py`, the five agents, `messages_en.py`); (3) every component that renders the file was read to say where the fan sees each field; (4) failure behavior was probed in memory (Statcast columns dropped or nulled, API answers empty or malformed, a switch-pitcher hand); (5) the 17 real Savant files already in the local `data_cache` (53,941 rows) were read offline. No request was made to MLB or Savant.
- **Not verified:** real MLB/Savant answers beyond what the schemas and the local cache cover; the completeness of `PITCH_NAME_MAP`; behavior of Next.js hydration (components were read, not run in a browser).

## 0. Reading guide

| Term | Meaning |
|---|---|
| **MLB API** | `statsapi.mlb.com`: schedule (`hydrate=probablePitcher,venue(timezone)`), `people/{id}` (hand), `people/{id}/stats` (season line). Validated by `mlb_schemas.py`. |
| **Statcast** | `pybaseball.statcast_pitcher` pitch rows (regular season, plus postseason up to the cutoff). |
| **Savant** | `baseballsavant.mlb.com` team-batting CSV, one request per month. |
| **derived** | computed from the above by code (`labels.py`, `process_pitcher_statcast`, agents). |
| **constant** | written by code with no source. |
| **catalog text** | an English sentence from `agents/messages_en.py`. |
| **Fan sees** | the component that renders it (read from `components/*.tsx`). "JSON only" = published in the file, rendered by no component. |
| **Unavailable value** | what is published when a figure has no source: `null`, `"N/A"`, `[]` or `{}`, never a measured zero (see F6 for the exceptions found). |

Producer names: `fetch_todays_games`, `fetch_pitcher_hand`, `fetch_pitcher_season_stats`, `fetch_pitcher_statcast` (+ `process_pitcher_statcast`, `_statcast_counts`, `_attach_sample`), `fetch_team_splits` (+ `derive_team_splits`) are in `data_pipeline/fetchers/live_pipeline.py`; `live_matchup.*` is `data_pipeline/live_matchup.py`; `gdj.*` is `data_pipeline/generate_demo_json.py`.

## 1. How the file is produced, and what a failure does to the whole file

1. `run_live_pipeline(target_date)` → a run record (`live_run.json`) and a snapshot (`live_matchup.json`) in `data_cache/processed`.
2. Importing the generator runs `_resolve_live_input()`: the snapshot is used only if the run is `ok`, the snapshot belongs to that run and `_snapshot_unsafe` accepts it. Otherwise the mode is `demo_fallback` (or `demo_cached` if there is no run at all).
3. `build_payload()` starts from `demo_inputs.build_demo_payload()` (6 archive rows, 2 matchups, workflow, disclaimers), replaces the `matchup_001` slot with the first live game, inserts up to 2 more live games after it, replaces `archive[0]`, then runs the five agents over **all** matchups (demo ones included) and rebuilds `agent_workflow`.
4. `main()` writes the file only if the critic found nothing `unsupported` and `validate_payload` passes. Otherwise it exits 1 and **the previous file stays**.
5. The page (`lib/data.ts`, `app/page.tsx`) reads the file on every request.

| What fails | Run-level outcome | What is published |
|---|---|---|
| No `live_run.json` | no run | `demo_cached`, reason "No live run; showing demo data" |
| Run record or snapshot unreadable, snapshot from another run, or `_snapshot_unsafe` | run ignored | `demo_fallback`, reason names the cause. **Any one unsafe game rejects the whole snapshot** (F11). |
| Schedule request fails, answer malformed, or a `gameDate` is not a UTC instant | `[]` + error `mlb_schedule` → run `failed` | `demo_fallback` |
| Schedule valid but no games | run `no_games`, no error | `demo_fallback`, reason "Live run no_games; showing demo data" |
| Games, but none with both probable pitchers | run `no_usable_games`; `skipped_games` in the run record | `demo_fallback` |
| One starter's fetch returns `None` (Statcast error, malformed rows, missing column, hand unknown) | that game is skipped; others continue (5 candidates, at most 3 live games) | the game is absent; if no game survives, as above |
| Team splits fail or Savant budget spent | `{}` for that team + error `savant_team_batting` / budget error; **game kept** | offense fields `null` (section 3.3) |
| Season-stats call fails or is malformed | `{}` + error `mlb_season_stats`; game kept | `"N/A"` figures; counts from Statcast if it has them |
| Critic finds an `unsupported` claim | generator exits 1 | file not written; previous file remains |
| `validate_payload` fails | generator exits 1 | file not written |

### 1b. Per source: missing, empty, malformed

What each source's failure publishes, by field. "Error" is the entry recorded in the run record (`source`); "skipped" means the game is absent from the file.

| Source (producer) | Missing: request fails, exception, `None` | Empty but valid | Malformed |
|---|---|---|---|
| **Schedule** (`fetch_todays_games`) | `[]`, error `mlb_schedule`; run `failed` → `demo_fallback` | a day without games (`dates: []`, or a date with `games: []`): `[]`, no error; run `no_games` → `demo_fallback`. A `dates` entry with no `games` key is malformed | error `mlb_schedule` naming the path (`SourceShapeError`, e.g. `gameDate` not a UTC instant, `teams.away.team.name` missing); same outcome as missing. Optional parts: `venue` / `venue.timeZone` absent → `game.venue` / `game.timezone` `null`; no `probablePitcher` → game not eligible, listed in `skipped_games` |
| **People** (`fetch_pitcher_hand`) | `None`, error `mlb_person`; game skipped | `people: []` is a shape error (see malformed) | error `mlb_person`; unknown code → `None`; not cached; 10 lookups per run, the 11th is `None` + error without a call |
| **Season stats** (`fetch_pitcher_season_stats`) | `{}`, error `mlb_season_stats`; game kept | `splits: []`: `{}`, **no error** → `era/whip/innings` `"N/A"`, `scopes.season_rates` `null`, counts from Statcast if it has them | `{}` + error `mlb_season_stats` (e.g. "stats[0].splits[0].stat is missing"); single figures absent: that figure `"N/A"` / `null` (never 0); an API line without all four counts yields to valid Statcast counts |
| **Statcast pitcher** (`fetch_pitcher_statcast`) | exception or `None`: `None`, error `statcast_pitcher`; game skipped | empty frame (a debut, or a cutoff before opening day): starter with `pitches 0`, `pitch_mix []`, `velocity_by_pitch []`, `pitch_movement {}`, `pitch_locations {vs_lhh: [], vs_rhh: []}`, all dimensions limited; hand from `people`; no error | rows with a missing / unparseable `game_date` or a `game_type` outside `R S E A F D L W`: whole answer rejected, error `statcast_pitcher`, game skipped (QA4-02); columns `stand`, `release_speed`, `plate_x`, `plate_z`, `pitch_type` missing: `KeyError`, error, game skipped; `events` missing: counts `null` + error, game kept; `pfx_x`/`pfx_z` missing: movement `null`, no error; `pitch_type` null everywhere: silent debut (F6a); `events` null everywhere: counts `0` (F6b) |
| **Savant team batting** (`fetch_team_batting_statcast` → `derive_team_splits`) | request error or budget spent (210 closed + 10 open-month per run): splits `{}`, error `savant_team_batting`; game kept; offense `null` | blank month: valid empty month, cached; no rows at all: `{}`, no error | not the CSV (error page, JSON envelope): error, not cached; row cap reached (possible truncation): error; missing / invalid `game_date`, `game_type`, `inning_topbot`, `home_team`, `away_team`, `p_throws` in any row: whole month rejected, error, not cached |
| **Series status** (`fetch_series_status`) | n/a | n/a | n/a. The fetcher exists and is tested, but `build_live_snapshot` never calls it: series standing is **not in the snapshot or the payload** (P1.5). |

When the run is `ok`, `metadata.data_status.live_run` is published with `status`, `run_at`, `target_date`, `as_of`, `games_scheduled`, `games_live` and `errors` (first 20 errors, each `{source, message (≤300 chars), …context such as pitcher_id}`), so raw exception text is in the public file (F10).

## 2. Findings from the inventory

These are places where a published or visible statement does not match the data, or a path is silent. None was changed. Each is referenced from the tables below.

- **F1: "Statcast pitch data" in the confidence note (owner-flagged).** `writer.confidence.live_no_offense` and `live_full` both say the report "uses a fetched live snapshot with probable pitchers and Statcast pitch data". Which one is chosen depends only on whether both teams have `ops_vs_hand` (`_base_confidence_note`); nothing checks that any pitch data exists. A two-debut game (0 pitches, no pitch mix) publishes it (probe, section 3.4). `live_full` also says "season offense splits", true only when both teams have a split for the hand faced. The sentence is in the `Data Confidence Note` section, which **no component renders** today (section 3.4), so it is published in the JSON and in anything that reads the JSON (eval packets, P2), but not on the page. I left this sentence recorded as "seen and left" in STATUS when I fixed the debut scope note in P0.15-B. CONTRIBUTING says an item that touches a user-visible claim is fixed, not recorded; I should not have left it. The fact that today's page does not render the section does not change that it is a false statement in the published data.
- **F2: offense scope claimed when there is no offense data.** `build_offense` always sets `offense_profile.scope`, even when every figure is `null`; the analyst then writes "Team offense splits cover the regular season through D." The debut probe publishes, one sentence after "Season offense splits were not available for this game", the sentence "Team offense splits cover the regular season through 2026-07-03." Same class as the debut scope sentence fixed in B. JSON only (same section).
- **F3: static UI and metadata claims that are wrong in live mode.** `Hero.tsx` always prints "Cached Demo" and "Cached matchup data becomes a readable report…"; `app/layout.tsx` has the description "Cached matchup data becomes a readable report with critic review."; the footer disclaimer "Cached demo data may be used to ensure stable public evaluation." is in the file for every mode; `agent_workflow.steps[0].output` says "Loaded cached data for N matchups."; `metadata.data_sources` always lists "Cached demo snapshots (always available)". And **no component reads `metadata.data_mode`, `data_status`, `last_updated_label` or `generated_at`**: a live page and a `demo_fallback` page look the same except for their content. (Badges are P1.4.)
- **F4: demo matchups and archive rows stay in a live payload.** The live file also contains `matchup_002` ("New York Yankees vs Boston Red Sox", fictional pitchers, final score "BOS 5 - NYY 3", a postgame grade) and archive rows `matchup_002` to `matchup_006` (fictional results and grades; 003 to 006 have no matchup). The carousel and the archive table render them next to the live game, and they count in `agent_workflow` ("2 matchups", warnings, "Graded 2 completed starter(s)"). Known (P1.3); listed because the contract must say what a live file contains.
- **F5: `status` is always "upcoming".** The schedule's status (Preview/Live/Final) is read into the snapshot (`featured_game.status`, `games_today[].status`) but never published. A run after first pitch publishes `status: "upcoming"`, a pregame report and `data_confidence.lineup_status: "probable_pitchers"`.
- **F6: silent or unvalidated paths in the Statcast processing** (probed in memory):
  - (a) `pitch_type` null in every row of a 170-row frame → the starter is built as a debut with 0 pitches and **no error** (same class as QA4-02, in a column the row validation does not cover).
  - (b) `events` null in every row, with the MLB API empty → the Statcast fallback publishes **measured zeros**: `batters_faced 0`, `strikeouts 0`, `walks 0`, `home_runs 0`, source `statcast`; the card shows K "0", not "—". The code cannot tell "no plate appearance completed" from "unusable column".
  - (c) `stand`, `release_speed`, `plate_x`, `plate_z` or `pitch_type` columns missing → `KeyError` inside `process_pitcher_statcast`, recorded as `statcast_pitcher: "KeyError: 'stand'"`, game skipped. Explicit, but those columns are not in the required-columns check.
  - (d) `pfx_x` / `pfx_z` columns missing → movement `h_break`/`v_break` `null`, no error (deliberate, documented in `compute_movement`).
  - (e) A pitch code not in `PITCH_NAME_MAP` (for example `FA`, `PO`, `UN`) is published as the raw code in `pitch_mix[].pitch`; and `compute_movement` gives such a pitch `family: "Fastball"` by default.
  - (f) `stand` null → `vs_lhh`/`vs_rhh` `null` (unavailable, fine); `release_speed` null → no velocity row (fine).
- **F7: `"???"` team abbreviation.** `_team_abbreviation` falls back to `"???"` when the schedule gives no abbreviation and the id/name is not in the two lookup tables. It is published as `teams.*.abbreviation` and `starters.*.team`, and the page shows it.
- **F8: two constant critic notes.** `critic_review.revision_notes` always ends with "Kept the report focused on matchup fit rather than outcome prediction." and "Avoided claiming official Stuff+." (shown as "Critic Notes"). They are not data-driven: the betting-language check supports the first; nothing checks the second.
- **F9: `metadata.generated_at`.** In live mode it is the run time of the live fetch (`run_at`, UTC), not the time the file was generated; in `demo_cached` and `demo_fallback` it is the constant `2026-06-28T09:00:00-05:00`.
- **F10: raw error text in the public file** (`data_status.live_run.errors`, see section 1).
- **F11: all-or-nothing snapshot.** `_snapshot_unsafe` returns the first problem of any game and the whole snapshot is dropped. Example probed: `fetch_pitcher_hand` accepts `L`, `R` and `S`, the generator accepts only `L` and `R`, so one starter with `S` sends the whole page to `demo_fallback` ("game 1: away_starter throws 'S', not L or R").
- **F12: the "Today" label.** `GameCarousel` compares `matchup.date` (the official New York date) with the UTC date of the machine that renders it, so late on an Eastern evening the date shows instead of "Today".
- **F13: what the fan reads of the report is a small part of it.** Only `report.headline`, `short_summary[0]`, the two starter sections' `body` and the `bullets` of "Three Things to Watch" are rendered. `short_summary[1..2]` and the sections "Today's Matchup Summary", "Arsenal Scout" and "Data Confidence Note" are not (section 3.4). `short_summary[0]` is always the away starter's strength line.

- **F14: an unknown count is written as "no ... on record".** Found while building the registry of claims, not in the first pass. `matchup_analyst._data_notes` builds `have_batters` with `... if batters else t("analyst.have.no_batters")` and `have` with `... if pitches else t("analyst.have.no_pitches")`, so a `null` count (a Statcast frame without `events`, F6b's neighbour) reads "Strikeout data for X is limited (no batters faced on record; 70 needed)". A `null` is unknown; "no batters faced" asserts a measured zero.
- **F15: the analyst guesses a throwing hand.** `matchup_analyst._offense_read` takes `offense.get("vs_pitcher_hand") or _throws_label(starter.get("throws", "R"))` and `_throws_label` defaults to `"R"`. Unreachable for L/R today (snapshots are validated), but a switch pitcher (hand `S`, F11) would read "SHP" and a missing hand "RHP".
- **F16: time claims with no condition.** The section title "Today's Matchup Summary" (`writer.section.summary`) and the sentence "Lineups can still change before first pitch" (`writer.confidence.live_*`) assert that the game is today and that first pitch has not happened. The file can be read days later and the game may be `Live` or `Final` (F5).
- **F17: a scope for counts that are unavailable.** Found by the rule 3 check (P0.15-D3.2), not in the first pass. `_attach_sample` writes `season_summary.scopes.counts = null` when the counts are unavailable but keeps `sample.rates.scope` set (section 3.4 says "always set, even when source is `unavailable`"). Same class as F2. `sample.arsenal.scope` with 0 pitches is not part of it: the zero is measured.
- **F18: a put-away pitch under 15% in a sentence.** Found by the rule 4 check (P0.15-D3.2). The demo's `matchup_002` gives Demo Pitcher C a put-away pitch (Changeup) at 12% of his pitches; the analyst writes "Can Demo Pitcher C land the changeup early in counts?" while D30 says a second pitch is a put-away pitch only from 15%, and the critic warns about the same pitch. The live profile never names such a pitch, so only the demo data shows it.
- **F19: workflow steps with a fixed status.** Found by the manifest (P0.15-D3.3b-2). `_build_agent_workflow` writes `status: "completed"` for the Data Scout, Analyst, Writer and Critic steps without reading the result of any of them; only the postgame step reads its result (`completed` or `not_applicable` from the graded count). It is true today only because a failure stops the generator.
- **F20: a share of no pitches written as 0%.** Found by the manifest over the debut cells of the matrix (P0.15-D3.3b-2). `_combine_pitch_mix.not_thrown` writes `overall: 0` for each pitch the opponent threw even when the starter has no pitch (`total` 0); `vs_lhh` and `vs_rhh` are already `null` there.

## 3. Field inventory

Columns: **Path** · **Producer ← source** · **Scope** · **If the source is missing, empty or malformed, what is published** · **Fan sees** · **Agent text that asserts something about it**. `[i]` is an array index; `{slot}` is `away_starter` or `home_starter`; `{side}` is `home` or `away`. "Scope" is `labels.make_scope(kind, through)`: `regular_season` or `regular_and_postseason`, `through` = the cutoff (the day before the official date, D29).

### 3.1 Top level and `metadata`

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `metadata.project_name` | `demo_inputs.METADATA` ← constant "PitchCraft Matchup Agent" | n/a | n/a | No (`layout.tsx` has its own title) | none |
| `metadata.version` | constant "0.2.0" (= `SCHEMA_VERSION`, checked by the validator) | n/a | n/a | No | none |
| `metadata.data_mode` | `gdj.build_payload` ← `_resolve_live_input()`: `fetched_snapshot` \| `demo_fallback` \| `demo_cached` (`live_partial` is defined and unused) | n/a | decided by the run-level table in section 1 | **No** (F3) | none |
| `metadata.generated_at` | live: snapshot `run_at` (UTC, `datetime.now(utc)` in the pipeline); other modes: demo constant (F9) | n/a | a snapshot without `run_at` is rejected by `_snapshot_mismatch`; a test build without it raises `KeyError` | No | none |
| `metadata.last_updated_label` | live: "Live data fetched {fetched_date}"; fallback: "Live data unavailable; showing demo data"; demo: constant "Demo data generated for capstone submission" (all in `gdj`/`demo_inputs`, not in the catalog) | n/a | n/a | **No** | none |
| `metadata.data_sources[i]` | `config.SOURCE_LABELS`, three constant strings, same in every mode | n/a | n/a | No | none (F3: lists "Cached demo snapshots") |
| `metadata.data_status.mode` | = `data_mode` | n/a | n/a | No | none |
| `metadata.data_status.reason` | `gdj._status` strings: "Live run ok", "No live run; showing demo data", "Live run {status}; showing demo data", "Live snapshot rejected ({why}); showing demo data", … | n/a | n/a | No | none |
| `metadata.data_status.live_run` | run record summary (`_run_summary`): `status`, `run_at`, `target_date`, `as_of`, `games_scheduled`, `games_live`, `errors[:20]` | n/a | `null` when there is no run record | No | none (F10) |
| `featured_matchup_id` | `demo_inputs.FEATURED_MATCHUP_ID` ← constant "matchup_001" | n/a | n/a | Yes: default selected matchup and carousel highlight (`PitchCraftApp`, `GameCarousel`) | none |

### 3.2 `matchups[i]` header and `game` (live matchups: `matchup_001`, then `matchup_live_2`, `matchup_live_3`)

All built by `live_matchup.build_matchup` from the snapshot; nothing is copied from the demo (P0.15-A).

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `id` | `gdj._apply_live_snapshot`: "matchup_001" for the first game, "matchup_live_{n}" for the next | n/a | n/a | Selection and `?matchup=` link (`PitchCraftApp`) | none |
| `date` | snapshot `fetched_date` = the run's target date (the official New York date) | n/a | required: a snapshot without it is rejected | Carousel date badge, "Today" rule (F12); archive date | none |
| `status` | constant "upcoming" (F5) | n/a | n/a | Carousel badge ("recommended" for the featured one, else the status); `MatchupView` picks pregame/postgame | none |
| `is_featured` | constant (first live game `true`, others `false`) | n/a | n/a | No (the carousel uses `featured_matchup_id`) | none |
| `game.title` | `"{away_team} vs {home_team}"` ← schedule `teams.*.team.name` (required) | n/a | game without a team name is rejected by `_game_unsafe` | No | none |
| `game.venue` | `fetch_todays_games` ← schedule `venue.name` (optional) | n/a | `null` | `MatchupView` header: venue, or "Venue not available" | none |
| `game.start_time_utc` | `fetch_todays_games` ← schedule `gameDate`, must be `YYYY-MM-DDTHH:MM:SSZ` | n/a | anything else: schedule fetch fails (`mlb_schedule`), run `failed` | Header and carousel via `formatStartTime` (D33) | none |
| `game.start_time_local` | constant `null` for live games (demo games keep a pre-formatted text) | n/a | n/a | not used for live | none |
| `game.timezone` | `fetch_todays_games` ← schedule `venue.timeZone.id` (optional) | n/a | `null` → shown as UTC | Header and carousel: converts to this zone, else "HH:MM UTC" | none |
| `game.broadcast_note` | constant `null` (no source) | n/a | n/a | No | none |
| `game.home_team_id`, `game.away_team_id` | schedule `teams.*.team.id` → str | n/a | required | No | none |

### 3.3 `matchups[i].teams.{side}`

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `id` | schedule team id → str | n/a | required | No | none |
| `name` | schedule `team.name` | n/a | required | No (only in `game.title` and report section titles) | section titles "X vs {team name}" (not rendered) |
| `abbreviation` | `_team_abbreviation`: schedule `abbreviation` if sent, else `MLB_TEAM_ABBR_BY_ID`, else `..._BY_NAME`, else `"???"` (F7) | n/a | `"???"` | Badges, labels, carousel "BOS @ NYY", team colors | none |
| `record` | constant `null` (no source) | n/a | n/a | No | none |
| `offense_profile.vs_pitcher_hand` | `build_offense`: `"{hand}HP"` of the opposing starter's hand | n/a | follows the starter's hand | `ScoutingReport`: "vs LHP" | every offense sentence: "…against LHP pitching…" |
| `offense_profile.ops_vs_hand` | `fetch_team_splits` → `derive_team_splits` ← Savant team-batting CSV (regular-season plate appearances through the cutoff, split by the pitcher's hand; OPS computed from `events`), formatted ".801" | `offense_profile.scope`: `regular_season` | Savant error, budget spent, malformed rows (QA4-02 rule) or no PA against that hand → `null`; error `savant_team_batting` recorded; game kept | `ScoutingReport` OPS tile ("—" if null) | "This lineup hits well against {hand} pitching ({ops} OPS), so {name} cannot live over the middle." (≥ .750, D32); "…roughly average… with no glaring weakness to attack." (≥ .700); "…has struggled… gives {name} an edge if he gets ahead."; or "Season offense data against {hand} pitching is not available for this lineup yet." |
| `offense_profile.k_rate_vs_hand` | same split: strikeouts / PA × 100, one decimal, "19.4%" | `regular_season` | `null` | K% tile | "They also strike out often, which favors a swing-and-miss approach" (≥ 23.0, D32) |
| `offense_profile.bb_rate_vs_hand` | same: walks / PA × 100, "10.6%" | `regular_season` | `null` | BB% tile | "They draw walks at an above-average rate, so {name} needs efficient strikes" (≥ 9.0, D32) |
| `offense_profile.summary_label` | "Real season split vs {hand}HP" when a split exists | n/a | `null` | `ScoutingReport` text fallback if the starter's section is missing; else "Offense data not available" | none |
| `offense_profile.recent_form` | constant "Season split" when a split exists (it is not a form measure) | n/a | `null` | `ScoutingReport` footer "vs LHP · Season split" | none |
| `offense_profile.scope` | `labels.make_scope(regular_season, through)`, always set | `regular_season` | set even when every figure above is `null` (F2) | No | "Team offense splits cover the regular season through D." (F2) |

Pressure points (`lineup_pressure_points`) are computed by the analyst from these figures; they are internal findings and are not published.

### 3.4 `matchups[i].starters.{slot}`

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `id` | schedule `probablePitcher.id` → str | n/a | no probable pitcher: the game is not eligible (`pick_featured_games`), listed in `skipped_games` | No | none |
| `name` | schedule `probablePitcher.fullName` (never split, P0.6) | n/a | as above | `StarterCard` title, detail panel, section titles | every sentence names him |
| `team` | `_team_abbreviation` of his team (F7) | n/a | `"???"` | `StarterCard` "BOS · AWAY", badge | none |
| `throws` | `process_pitcher_statcast`: first non-null `p_throws`; else `fetch_pitcher_hand` ← MLB `people/{id}` `pitchHand.code` (cached for good, ≤10 lookups per run) | n/a | unknown → fetch returns `None`, error `mlb_person`, game skipped; `S` from the lookup → whole snapshot rejected (F11) | "RHP"/"LHP" in `StarterCard` and the detail panel; picks which offense split is used | "{hand} pitching" in offense sentences |
| `bio` | constant `null` (no source yet, P1.5) | n/a | n/a | "Bio not available" | none |
| `recent_form` | constant `null` | n/a | n/a | "Recent form not available" | none |
| `season_summary.era`, `.whip` | `fetch_pitcher_season_stats` ← MLB `people/{id}/stats?stats=byDateRange&startDate={year}-01-01&endDate={cutoff}`; strings as the API sends ("3.10") | `scopes.season_rates`: `regular_season` (the API leaves out the postseason) | empty answer: `"N/A"` (no error); malformed: `"N/A"` + error `mlb_season_stats`; field absent: `"N/A"` | `StarterCard` ERA and WHIP tiles ("—" for N/A); caption "ERA and WHIP: {scope}" (or merged) | scope note only: "ERA, WHIP and innings cover the regular season through D" (never the values; "N/A" never appears in agent text) |
| `season_summary.innings` | same call, `inningsPitched` | `season_rates` | `"N/A"` | No | scope note only |
| `season_summary.strikeouts`, `.walks`, `.home_runs_allowed` | `_attach_sample` picks one source: the MLB API line **only if it has all four counts** (or some, when Statcast has none); else Statcast events (`_statcast_counts`); else `null` | `scopes.counts` = the chosen source's scope: API → `regular_season`; Statcast → the pitch data's scope | none available: `null` ×3, `sample.rates.source = "unavailable"`, `scopes.counts = null`; Statcast with `events` all null: **measured zeros** (F6b) | `StarterCard` K tile ("—" if null); caption "K: {scope}" | "{name} has allowed {home_runs} home runs over {batters} batters faced; no contact-risk rating is given…" (needs HR and BF); strikeout and control labels come from K/BF and BB/BF |
| `season_summary.scopes.season_rates` | `_attach_sample`: `regular_season` if ERA/WHIP/innings available, else `null` | itself | `null` | caption (see above) | scope note |
| `season_summary.scopes.counts` | `_attach_sample`: the counts' source scope, `null` if source "unavailable" | itself | `null` | caption | scope note; critic `Pitch data and season figures are not presented as one sample` |
| `pitching_profile.style_label` | `process_pitcher_statcast`: "{top}-{second} starter" / "{top} starter" from the pitch mix; "Arsenal data limited" if the arsenal is limited or empty (`labels.ARSENAL_LIMITED_STYLE`) | n/a | "Arsenal data limited" | `StarterCard` subtitle | headline "Sinker-Slider starter against…", "Arsenal Scout" sentence |
| `pitching_profile.primary_pitch` | most-thrown pitch by raw count | n/a | "Not available" (no pitches) | No directly; `PitchLegend` uses `charts.pitch_mix` | "{name} works off a sinker-slider combination."; critic "X's primary pitch is Y." (needs ≥30% of the mix, else warning) |
| `pitching_profile.putaway_pitch` | second pitch by raw count, **only if ≥15% of the mix** (D30), else "Not available" | n/a | "Not available" | No | "works off a {primary}-{putaway} combination" / "works mainly off a {primary}"; "Can {name} land the {putaway} early in counts?"; critic put-away claim |
| `pitching_profile.swing_miss_label` | `labels.strikeout_label` from K/BF rates (≥70 BF, D24; bands D25) | rates source scope | `null` if BF < 70 or K unknown | No directly | "He shows above-average swing-and-miss ability (…rates)." (qualifier names the counts' scope when groups differ); "Above-average swing-and-miss ability" in `short_summary` |
| `pitching_profile.command_label` | `labels.control_label` from BB/BF (≥170 BF) | rates source scope | `null` | No directly | "He shows solid / below-average command."; critic command check |
| `pitching_profile.contact_risk_label` | constant `null` (D24: count only) | n/a | n/a | No | the home-run-count sentence above |
| `sample.arsenal.pitches` | `_attach_sample`: Statcast rows with a `pitch_type`, after the date and game-type filters | `sample.arsenal.scope`: `regular_season`, or `regular_and_postseason` if a postseason row is in the frame | 0 for an empty frame / debut / pitch_type null everywhere (F6a); Statcast failure → no starter | `DetailedAnalysis`: "Arsenal data limited: {N} pitches (100 needed)" or "pitch count not available" or "Pitch data: {scope}" | "Arsenal data is limited ({N} pitches; 100 needed), so this report makes no arsenal claim for him." |
| `sample.arsenal.scope` | `labels.make_scope` | as above | always set | "Pitch data: {label}" | scope note; critic scope check |
| `sample.rates.batters_faced`, `.strikeouts`, `.walks`, `.home_runs` | the chosen source (see season_summary counts) | `sample.rates.scope` | `null` | No | limited-data sentences "Strikeout data for {name} is limited ({N} batters faced; 70 needed), so no swing-and-miss claim is made."; "…Control data… 170…" |
| `sample.rates.source` | `"mlb_api"` \| `"statcast"` \| `"unavailable"` | n/a | `"unavailable"` | No | none |
| `sample.rates.scope` | = `season_summary.scopes.counts` (kept for the sample; validator checks equality) | itself | always set, even when source is "unavailable" | No | none |
| `sample.limited.{arsenal,strikeout,control}` | `labels.build_sample` (thresholds D24: 100, 70, 170) | n/a | `true` when below the threshold or the figure is `null` | Suppresses chart/shape text in the detail panel; "Samples below the minimum…" is a report sentence | "Samples below the minimum are flagged as limited and no claim is made from them." |
| `sample.thresholds` | constant `{arsenal: 100, strikeout: 70, control: 170}` | n/a | n/a | "(100 needed)" in the panel | "100 needed", "70 needed", "170 needed" |

### 3.5 `matchups[i].charts` and `pitch_locations`

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `charts.pitch_mix[i].pitch` | `process_pitcher_statcast`: top 5 pitch names by raw count per starter, `PITCH_NAME_MAP` names; union of both starters (`_combine_pitch_mix`) | pitch data scope | `[]` for two debuts; unmapped code published raw (F6e) | `PitchLegend`, detail-panel rows | critic: "The report names only pitches that appear in the pitch mix." |
| `charts.pitch_mix[i].{slot}.overall` | pitches of that name / his total × 100, one decimal; `0` for a pitch he never threw | pitch data | all-zero row for the other starter's pitches | detail-panel usage bar and %, trajectory card | "Pitch mix shows 60.9% Sinker usage." (critic evidence) |
| `…{slot}.vs_lhh`, `.vs_rhh` | share among that side's pitches (`stand`); `null` when that side was never faced (never 0%) | pitch data | `null` | detail panel toggle: dash and "No left-handed batters faced." | none |
| `…{slot}.count`, `.total` | raw counts behind the shares (`total` = his total, also on rows of pitches he never threw) | pitch data | present on every live row (validator checks count ≤ total = sample pitches) | No | critic uses them for the 30% / 15% minimums ("X is 3,000 of 10,010 pitches (29.97%)…") |
| `charts.velocity_by_pitch[i].pitch` | same pitch union | pitch data | `[]` | detail panel | none |
| `…{slot}_velocity` | mean `release_speed`, one decimal; `null` for the other starter or when all speeds are null | pitch data | row omitted if NaN; `null` | trajectory card (meter hidden when "N/A") | none |
| `charts.strength_profile` | constant `[]` (no live source) | n/a | n/a | `StrengthProfile`: "Not available for live data yet." | none |
| `charts.pitch_movement.{slot}.{pitch}.h_break`, `.v_break` | median `pfx_x` / `pfx_z` × 12 inches, ≥3 observations | pitch data | `null` (missing columns, all null, <3 rows; no error) | trajectory card: "Movement data not available for this pitch" | none |
| `…{pitch}.family` | `compute_movement` name map; default "Fastball" for an unmapped name (F6e) | n/a | "Fastball" | pitch description text (`lib/pitchDescriptions.ts`) | none |
| `pitch_locations.note` | constant owned by `live_matchup` (what the 0–1 numbers mean) | n/a | n/a | No | none |
| `pitch_locations.{slot}.{vs_lhh,vs_rhh}[i].{pitch,x,y}` | median `plate_x` / `plate_z` per pitch and batter side, ≥5 pitches, normalized to 0–1 and clipped | pitch data | `[]` | `ZoneDiagram` in `StarterCard` (vs RHH only) and in the detail panel (toggle) | none |

### 3.6 `matchups[i].report`, `critic_review`, `postgame`, `data_confidence`

Report text comes from `matchup_analyst` → `report_writer` (sentences in `messages_en.py`). Which parts the page renders: **`headline`, `short_summary[0]`, the `body` of the two starter sections ("{name} vs {team}") and the `bullets` of "Three Things to Watch"**. Everything else below is JSON only (F13).

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `report.headline` | analyst `_matchup_label`: "{away style} against {home style}", or the two names if either arsenal is limited | n/a | names only | `MatchupView` header, carousel card | "Sinker-Slider starter against Four-seam-Curveball starter" |
| `report.short_summary[0]` | writer `_strength_line` (away starter): "{name} brings this strength: {first strength}." or "{name} has no claimed strength because the data is limited." | n/a | the "no claimed strength" sentence for a starter with a sample and no strengths | **Yes**, the highlighted line under the headline | "Alpha Livearm brings this strength: Above-average swing-and-miss ability." |
| `report.short_summary[1]` | same for the home starter | n/a | same | No | same pattern |
| `report.short_summary[2]` | "The early what to watch is whether {name} can {action}." | n/a | n/a | No | the first "watch" item |
| `report.sections[0]` "Today's Matchup Summary" `.body` | catalog `analyst.summary` | n/a | n/a | No | "This matchup features {label}. The scouting note is matchup fit, with each pressure point shaping what to watch." |
| `report.sections[1]` "{away} vs {home team}" `.body` | analyst `_live_pitcher_read` + `_offense_read` | per-claim scopes | limited sentences when the sample is below threshold (3.4); offense unavailable sentence (3.3) | **Yes**, `ScoutingReport` card | the sentences quoted in 3.3 and 3.4, including the rate qualifier "(regular-season rates)" / "(regular season and postseason rates)" when the groups differ |
| `report.sections[2]` "{home} vs {away team}" `.body` | same for the other starter | per-claim | same | **Yes** | same |
| `report.sections[3]` "Arsenal Scout" `.body` | writer `_arsenal_scout`: contrast sentence, or the limitation sentences + "No arsenal contrast is drawn because at least one arsenal has too little data." | n/a | limited arsenals → limitation text | No | "The main contrast is {style} versus {style}. The primary pitch contrast is {pitch} against {pitch}, a scouting note for matchup fit and each pressure point." |
| `report.sections[4]` "Three Things to Watch" `.bullets` | analyst `three_things_to_watch` (catalog `analyst.watch.*`) | n/a | neutral questions for a limited arsenal | **Yes**, "What to watch" | "Can {name} land the {putaway} early in counts?", "Can {name} keep the ball low / in the zone?", "Which lineup forces more deep counts by the third inning?" |
| `report.sections[5]` "Data Confidence Note" `.body` | writer `_confidence_note`: base sentence + scope notes + limited sentence | see below | see below | **No** | see below |
| ↳ base sentence | `writer.confidence.live_full` / `live_no_offense` chosen by whether both teams have `ops_vs_hand` | n/a | n/a | No | "This report uses a fetched live snapshot with probable pitchers, Statcast pitch data, and season offense splits…" / "…with probable pitchers and Statcast pitch data. Season offense splits were not available for this game, so the lineup read makes no offense claims. Lineups can still change before first pitch." (**F1**) |
| ↳ scope notes | analyst `scope_notes` (`labels.figure_scopes`) | per group | per starter: "all pitcher figures cover…" (all groups agree), a two- or three-scope sentence ending "They are different samples.", or "{names}: no season figures are available." | No | quoted in 3.4; team: "Team offense splits cover the regular season through D." (**F2**) |
| ↳ limited sentence | "Samples below the minimum are flagged as limited and no claim is made from them." when any dimension is limited | n/a | n/a | No | the sentence |
| `critic_review.status` | constant "reviewed" | n/a | n/a | No | none |
| `critic_review.summary` | `critic.run`: "The critic checked {n} claims and found them supported by the data." / "…none unsupported, {w} with a warning." | n/a | an `unsupported` check stops the publication | **Yes**, `CriticReviewPanel` | the sentence |
| `critic_review.checks[i].claim`, `.status`, `.evidence` | `critic.run`: pitch role claims (primary / put-away) with usage evidence; limited-arsenal claim; "The report names only pitches that appear in the pitch mix."; command claim; "Pitch data and season figures are not presented as one sample."; "The report predicts the winner." | evidence quotes the counts' scope for walks | statuses `supported`, `not_present`, `warning`; `unsupported` blocks | **Yes** | the claims and evidence, e.g. "38 walks in 380 batters faced (regular season through D)." |
| `critic_review.revision_notes[i]` | warnings' evidence, then two constants (F8) | n/a | n/a | **Yes**, "Critic Notes" | "Kept the report focused on matchup fit rather than outcome prediction." "Avoided claiming official Stuff+." |
| `postgame` | constant `null` for live (pregame) matchups | n/a | n/a | not rendered (pregame mode) | none |
| `data_confidence.level` | `live_matchup.confidence_note`: "fetched_snapshot" | n/a | n/a | No | none |
| `data_confidence.lineup_status` | constant "probable_pitchers" (F5) | n/a | n/a | No | none |
| `data_confidence.pitch_data_status` | constant "fetched_snapshot", even for starters with no pitch data | n/a | n/a | No | none (same family as F1) |
| `data_confidence.notes[i]` | "Live snapshot fetched {date} for {matchup id}." | n/a | n/a | No | none |

### 3.7 `archive[i]`, `agent_workflow`, `disclaimers`

| Path | Producer ← source | Scope | If missing / empty / malformed | Fan sees | Agent text |
|---|---|---|---|---|---|
| `archive[0].{id,date,title,status,featured,starter_summary,result_label,grade_label}` | `live_matchup.archive_row`: id "matchup_001", `date` = target date, `title` "{away abbr} vs {home abbr}", `status` "upcoming", `featured` true, `starter_summary` "{name} vs {name}", `result_label` "Pregame report available" (constant), `grade_label` `null` | n/a | n/a | `ArchiveTable` (grade shows "Pending") | none |
| `archive[1..5].*` | `demo_inputs.ARCHIVE` constants (matchups 002–006, fictional pitchers and results); `grade_label` of 002 rewritten by `_update_archive_postgame_labels` from the demo postgame | n/a | n/a | `ArchiveTable` (F4) | "Starter Duel: Demo Pitcher D, B" |
| `agent_workflow.description` | constant | n/a | n/a | `AgentPipeline` | "PitchCraft uses a multi-agent workflow to convert matchup data into a fan-facing scouting report." |
| `agent_workflow.steps[0].output` | `gdj._build_agent_workflow` | n/a | n/a | Yes | "Loaded cached data for {N} matchups." (N counts demo matchups; F3, F4) |
| `agent_workflow.steps[1..2].output` | constants | n/a | n/a | Yes | "Identified pitcher strengths, risks, and lineup pressure points." / "Generated fan-friendly scouting report." |
| `agent_workflow.steps[3].output` | `_build_agent_workflow` with the warning count of **all** matchups | n/a | n/a | Yes | "Checked every claim against the data: none unsupported, {w} warning(s) across all matchups." |
| `agent_workflow.steps[4].{status,output}` | graded starters of the demo final matchups | n/a | `not_applicable` / "Featured game has not been completed." when none | Yes | "Graded {n} completed starter(s) with Bill James Game Score." |
| `agent_workflow.steps[*].agent`, `.status` | constants / computed | n/a | n/a | Yes | none |
| `disclaimers[0..3]` | `demo_inputs.DISCLAIMERS` constants | n/a | n/a | `Disclaimer` footer | "Cached demo data may be used to ensure stable public evaluation." (F3) and three others |

### 3.8 Demo matchups that remain in a live payload (F4)

`matchups[1]` (`matchup_002`, status `final`) and its `postgame` are `demo_inputs` constants processed by the same agents: `game.*` (real team names, fictional pitchers "Demo Pitcher C/D"), `starters.*` with `bio`, `recent_form`, scoreless-source `season_summary` and no `sample`, full `charts` and `pitch_locations`, `postgame.final_score` (5–3), `starter_lines.*` (Game Score, grade, explanation, plan vs execution, what to watch), `call_check[]`. Their `data_confidence.level` is `demo_cached`. The carousel and the archive render them; `matchup.id` lets the page open them. They are not live and carry no scope.

### 3.9 Static text of the page that is not in the payload but makes claims about it

| Where | Text | Wrong or right in live mode |
|---|---|---|
| `components/Hero.tsx` | "Cached Demo"; "Cached matchup data becomes a readable report, then a critic checks the claims against the same data." | wrong (F3) |
| `app/layout.tsx` metadata | "Cached matchup data becomes a readable report with critic review." | wrong (F3) |
| `components/StrengthProfile.tsx` | "Not available for live data yet." | right |
| `components/MatchupView.tsx` / `StarterCard.tsx` / `DetailedAnalysis.tsx` | "Venue not available", "Bio not available", "Recent form not available", "Offense data not available", "Arsenal data limited: …", "Movement data not available for this pitch", "No left-handed batters faced." | right (unavailable states) |

## 4. Fields that are published and rendered by nothing

`metadata.*` (all), `data_confidence.*`, `critic_review.status`, `matchups[i].is_featured`, `game.title`, `game.broadcast_note`, `game.start_time_local` (live), `game.*_team_id`, `teams.*.id`, `teams.*.name`, `teams.*.record`, `teams.*.offense_profile.scope`, `starters.*.id`, `starters.*.bio` and `recent_form` (their "not available" text is a UI constant), `pitching_profile.primary_pitch` / `putaway_pitch` / `command_label` / `swing_miss_label` / `contact_risk_label` (used by agents; the card shows only `style_label`), `sample.rates.*`, `sample.limited.strikeout`, `sample.limited.control`, `sample.thresholds.strikeout/control`, `pitch_mix[].*.count/total`, `pitch_locations.note`, `season_summary.innings/walks/home_runs_allowed`, `report.short_summary[1..2]` and report sections 0, 3 and 5. (`featured_matchup_id` is used for selection and `agent_workflow` is rendered, so they are not in this list.) `components/PitchMixChart.tsx` and `VelocityChart.tsx` are not imported by any component.

## 5. Sentences that assert something about a field (index for the contract)

Every catalog sentence that states a fact, with the field(s) that must make it true. Sentences about the process (critic notes, workflow) are in section 3.7.

| Sentence (key) | Must be true of |
|---|---|
| "{name} works off a {primary}-{putaway} combination." (`analyst.read.combination`) | `pitching_profile.primary_pitch`, `putaway_pitch` (named, ≥15% for put-away), `sample.limited.arsenal = false` |
| "{subject} shows {label}{qualifier}." (`analyst.read.shows`) | `swing_miss_label` / `command_label` (rate sample met); qualifier = scope kind of `scopes.counts` when the groups differ |
| "{name}'s arsenal data is limited ({have}; 100 needed), so this report makes no arsenal claim for him." | `sample.arsenal.pitches`, `thresholds.arsenal` |
| "Strikeout / Control data for {name} is limited ({have}; 70 / 170 needed)…" | `sample.rates.batters_faced`, thresholds |
| "{name} has allowed {HR} home runs over {BF} batters faced; no contact-risk rating is given because a home-run rate needs a far larger sample." | `sample.rates.home_runs`, `batters_faced` |
| "Home runs allowed are not available for {name}." | `sample.rates.home_runs = null` or `batters_faced` empty |
| "This lineup hits well / is roughly average / has struggled against {hand} pitching ({ops} OPS)…" | `offense_profile.ops_vs_hand`, `vs_pitcher_hand` |
| "Season offense data against {hand} pitching is not available for this lineup yet." | `ops_vs_hand = null` |
| "They also strike out often…" / "They draw walks at an above-average rate…" | `k_rate_vs_hand` ≥ 23.0 / `bb_rate_vs_hand` ≥ 9.0 |
| "{who}: all pitcher figures cover the {label}." | all groups with figures share one scope kind |
| "{who}: {figures} cover the {label}; the pitch mix, velocity and movement cover the {label}. They are different samples." / "{who}: {figures} cover {label}; {figures} cover {label}. They are different samples." | `figure_scopes(starter)` |
| "{who}: no season figures are available." | the starter has no figure in any group |
| "Team offense splits cover the {label}." | `offense_profile.scope` **and, as written today, nothing else (F2)** |
| "This report uses a fetched live snapshot with probable pitchers[, Statcast pitch data][, and season offense splits]." | probable pitchers (true), **pitch data (not checked, F1)**, offense splits (checked via `ops_vs_hand`) |
| "Samples below the minimum are flagged as limited and no claim is made from them." | any `sample.limited.* = true` |
| "{name} brings this strength: {strength}." / "{name} has no claimed strength because the data is limited." | strengths from labels that cleared the threshold / absence of any |
| "The early what to watch is whether {name} can {action}." | the first watch item |
| Critic: "{name}'s primary / put-away pitch is {pitch}." with "Pitch mix shows {u}% {pitch} usage." | `pitch_mix[].count/total` vs 30% / 15% minimums |
| Critic: "{walks} walks in {batters} batters faced ({scope})." | `sample.rates.walks`, `batters_faced`, `scopes.counts` |
| Critic: "Each starter's figures cover the same games." | `labels.scopes_differ` false for both |
| Workflow: "Loaded cached data for {N} matchups.", "Checked every claim against the data: none unsupported, {w} warning(s) across all matchups.", "Graded {n} completed starter(s)…" | counts of the payload's matchups, including demo ones (F3, F4) |

## 6. What this inventory does not settle

- The inventory describes what the code does today; it does not say what the contract should require. Items F1 to F16 are inputs for that, not decisions; the contract (`docs/DATA_CONTRACT.md`) is where the requirements are written.
- `data_cache/raw/team_batting` (17 files, 53,941 rows) shows no missing value in `game_date`, `game_type`, `inning_topbot`, `home_team`, `away_team` or `p_throws` and only game type `R`; there is no real pitcher Statcast frame in the local cache, so the pitcher-frame claims rest on the schema checks and the in-memory probes above.
- A live run with games in progress or finished, a postseason slate, a doubleheader, a suspended game and a probable pitcher change before first pitch were not exercised.
