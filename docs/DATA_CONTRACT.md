# Data contract — what the published file may say

Normative (decision D34). This contract defines what `public/data/pitchcraft-demo.json`, and every text that describes it, may contain. It does not replace `docs/DECISIONS.md`: where they differ, the decision wins and the difference is reported. QA (`docs/QA_PROTOCOL.md`) verifies compliance with this contract. A rule changes only through a new decision.

- **Annex A:** `docs/data-inventory.md`, the field-by-field inventory of the live payload at HEAD `043db03`. Its findings F1 to F13 (and F14 to F16, added below) are the **known violations** of this contract. Each is closed by the commit named in section 4; until then, the generic checks of P0.15-D3 mark it as a strict `xfail`.
- **Scope of "published":** every field of the JSON file, whether or not a component renders it, and every text that describes the file: agent text, generator text (workflow, metadata, archive labels), frontend text and workflow text.
- **Words used.** A *field* is a path in the file. A *group of figures* is a set of fields that come from one source with one scope (section 2, rule 3). An *unavailable state* is the explicit way a field says "no value": `null` for a scalar, `[]` for a list, `{}` for a map, and the documented sentinel for the few fields that are text by type (`"N/A"` for `season_summary.era`, `whip`, `innings`; `"Not available"` for `primary_pitch` and `putaway_pitch`). The sentinels are listed in the manifest of P0.15-D3; none may be a number.

## 1. Where a value comes from

Every published field is exactly one of:

| Kind | Meaning | Example |
|---|---|---|
| **Source value** | A value the source gave, copied or parsed, not changed in meaning. | `game.start_time_utc` from the schedule's `gameDate`; `season_summary.era` from the MLB API |
| **Documented derivation** | Computed by code from source values, by a rule written in `DECISIONS.md` or in this repository's code and named in the manifest. | `pitching_profile.swing_miss_label` (D24, D25); `putaway_pitch` (D30); `offense_profile.ops_vs_hand` from Savant plate appearances |
| **Label constant** | A constant that asserts nothing about data: a name, a title, a unit. | `metadata.project_name`; the section title "Arsenal Scout" |
| **Unavailable state** | The field says there is no value. | `bio: null`; `charts.strength_profile: []` |

Anything else is a violation, in particular a constant that asserts a fact (a status, a scope, a date, a record, a claim about data).

## 2. The eight rules

### Rule 1. Provenance

*Every published field is a source value, a documented derivation, or an explicit unavailable state. Constants only for labels that assert nothing about data.*

Examples from Annex A:

- `status: "upcoming"` for every live game was a constant asserting a fact (F5).
- `data_confidence.lineup_status: "probable_pitchers"` and `pitch_data_status: "fetched_snapshot"` are constants that assert what the data contains (F5, F1). The second one is written even for a starter with no pitch data.
- `charts.pitch_movement.*.*.family: "Fastball"` for an unmapped pitch is an invented derivation (F6e).
- `family` for a mapped pitch, `teams.*.record: null`, `bio: null` are correct: the first is a derivation from a name map, the others are explicit unavailable states.
- `critic_review.revision_notes` ending with "Avoided claiming official Stuff+." is a constant asserting that a check happened; no check exists (F8).

**Check (P0.15-D3):** a manifest lists every path of a live file with its kind and, for a source value, its source. A leaf outside the manifest, or a constant that is not a label, fails validation.

### Rule 2. Unknown is never zero

*`null` when unknown. `0` only when the source measured zero. A column that cannot be used is unavailable plus a recorded error.*

Examples:

- `events` null in every row of a Statcast frame published `batters_faced 0`, `strikeouts 0`, `walks 0`, `home_runs 0` from source `statcast`, and the card showed K "0" (F6b). The code could not tell "no plate appearance completed" from "unusable column". The column is unusable: the counts are `null`, `sample.rates.source` is `"unavailable"`, and an error is recorded.
- The analyst writes "no batters faced on record" and "no pitches on record" when the count is `null`, because it tests `if batters` (F14). A missing count is not a zero count.
- `_usage_pct` returning `None` for a side the starter never faced (P0.14-C) is correct; a real `0%` against a side he did face stays `0%`.
- `pitch_type` null in every row of a populated frame produced a debut with `pitches 0` and no error (F6a). Same class.

**Check:** the manifest names, for every numeric field, the evidence a `0` requires (for a count: the source and that the column was usable). A `0` without its evidence fails; so does an unknown value written as `0`, `"0"` or `"N/A"` text in a numeric field, and so does a guessed default such as a throwing hand.

### Rule 3. Scope

*Each group of figures carries the scope of its source. No scope is stated for a group without figures.*

Groups at HEAD: pitch data (Statcast; `sample.arsenal.scope`, `charts.*`), season rates (ERA, WHIP, innings; MLB API; `scopes.season_rates`), counts (strikeouts, walks, home runs, batters faced; the API or Statcast; `scopes.counts`, `sample.rates.scope`), team offense (Savant; `offense_profile.scope`). Scope is `regular_season` or `regular_and_postseason`, through the cutoff (D29).

Examples:

- ERA from the regular-season API labelled "regular season and postseason" because the counts came from Statcast (QA4-01, closed in P0.15-B).
- `offense_profile.scope` is set while every offense figure is `null`, and the analyst writes "Team offense splits cover the regular season through D" one sentence after "Season offense splits were not available" (F2).
- A starter with no figure in any group has no scope (closed in P0.15-B: "no season figures are available").

**Check:** one table of groups (figure paths, scope path, source rule). A figure without a scope, a scope without a figure, or a scope that disagrees with the source of its group fails. No sentence says "all figures" about a starter whose groups differ.

### Rule 4. Claims

*Every sentence that asserts a fact (agent text, UI text or workflow text) declares the fields that make it true and is emitted only when they do. This applies to JSON nobody renders.*

- Each emitted phrase is recorded as a claim `{id, key, args, subject, location}`. The sentences of a matchup (report, critic review, data confidence notes, postgame) are in `matchups[i].report.claims[]`, with locations relative to the matchup (`report.sections[1].body`); the sentences the generator writes (workflow, data label) are in `claims[]` at the root, with locations from the root. `subject` is the starter the sentence is about (`away_starter`, `home_starter`) or `null`; `location` is `null` for a part of another sentence. `metadata.language` says which catalog the keys belong to.
- `args` are values copied from the payload (a name, a number, a label, a scope) or `{"claim": id}`, a reference to a claim that is part of the sentence (a plural such as "3 home runs" inside a longer sentence). Never an internal (a path, an exception, a function name, an object). Two pseudo keys build sentences out of sentences: `@join` (args `sep` and `parts`) and `@capitalize` (arg `of`); they assert nothing themselves.
- The text of a report is exactly the join of its registered phrases. The validator renders each claim again from its key and args and requires the text of the field to be exactly that; a text field with no claim, a claim for a field that does not exist, a part that no sentence uses, or a sentence edited after the fact fails. Which fields are text is a list in `data_pipeline/claims.py` (`MATCHUP_TEXT_PATHS`, `ROOT_TEXT_PATHS`); the static content of the demo (archive rows, disclaimers, bios) is not agent or generator text and joins the list when it becomes mode-dependent (D2.4).
- Each key has a condition in the registry (section 3). The validator evaluates it on the payload and the args. A phrase whose condition is false fails.
- No agent phrase names a pitch that is not in the mapped set (see rule 8, warnings).
- A text that says a game is upcoming ("upcoming", "tonight", "before first pitch", "today") is emitted only when the source state is `Preview` (and for "today", the game's date is today in its official zone). It never appears for a game whose state is `Live` or `Final`.

Examples:

- "This report uses a fetched live snapshot with probable pitchers and Statcast pitch data" was written for a game of two debuts, with no pitch data (F1). The condition of the Statcast part is that a starter has `sample.arsenal.pitches > 0`; the condition of "season offense splits" is that both teams have a split.
- "Lineups can still change before first pitch" for a game already in progress (F5, F16).
- "Today's Matchup Summary" asserts a date that the file cannot guarantee (F16).
- "Kept the report focused on matchup fit rather than outcome prediction." is supported by the betting-language check; the check's result is its condition (F8).

### Rule 5. Isolated failure

*An error is contained in the smallest unit: a field, a dimension, a game. One bad game never takes down the page.*

- A bad field is its unavailable state plus a recorded error (rule 2). A bad dimension is flagged `limited` (D1, D24). A bad game is dropped from the file with a recorded reason and the other games are published.
- At HEAD one unsafe game rejects the whole snapshot (F11): `fetch_pitcher_hand` accepts `S`, the generator accepts only `L` and `R`, so one switch pitcher sends the page to `demo_fallback`. A starter whose hand is `S` is published; the offense split by hand is unavailable for the opposing team, and no sentence about his hand is written.

**Explicit exception (integrity gate, fails closed).** `critic_review` with an `unsupported` check, and `validate_payload`, still stop the whole file: the generator exits 1, nothing is written and the previous file stays (P0.12-B). The reason is that a claim the data does not back up must not be published; stopping is the safe direction. This is not an isolated failure and is recorded as an exception. Whether to drop only the affected game is reviewed in P1.2.

### Rule 6. Honest mode

*The page states whether it shows live or demo data. A live file contains only live content.*

- `metadata.data_mode` is `fetched_snapshot` (live), `demo_fallback` (a live run failed or found no games) or `demo_cached` (no run). The page shows a visible line: "Live data · fetched {date}" or "Demo data: live data unavailable" (and a demo-labelled text for `demo_cached`).
- In a live file every matchup is a live matchup (`data_confidence.level == "fetched_snapshot"`), every archive row comes from a live run, and the workflow counts only them. The archive table shows only real live rows and, if there are none, "No past reports yet".
- Texts that describe the data source ("Cached demo", "cached matchup data", "Cached demo data may be used…") appear only in a demo file. In a live file the equivalent text is neutral.
- `metadata.data_fetched_at` is the time of the live fetch, `null` in a demo file. `metadata.generated_at` is the time the file was built, always real. They are never the same field (F9).

Examples: F3 (the Hero says "Cached Demo" over live data), F4 (`matchup_002`, "BOS 5 - NYY 3" and a postgame grade next to a live game), F9.

### Rule 7. Real state and time

*Game status comes from the source. "Today" is computed in the game's official zone.*

- The published `status` is derived from the schedule's `abstractGameState` (`Preview`, `Live`, `Final`). If the schedule does not give it, the status is unavailable, never `upcoming` by default (F5).
- A live or final game keeps the pregame report (the cutoff is the day before, D29) and shows its real status. The postgame stays `null` until the daily postgame exists (P1.2); no text promises one.
- The official date of a game is `officialDate` (America/New_York, D29). "Today" on the page is the current date in that zone, not the UTC date of the machine that renders it (F12).
- A start time is a UTC instant shown in the venue's zone when the schedule gives one, otherwise as UTC (D33).

### Rule 8. No internals in the public file

*Errors are published as `{source, code}`, never raw messages.*

- `data_status.live_run.errors` and `data_status.reason` carry a `source` from the fixed set (`mlb_schedule`, `mlb_person`, `mlb_season_stats`, `statcast_pitcher`, `savant_team_batting`, `snapshot`) and a `code` from a closed set defined in `data_pipeline/` (initial set: `request_failed`, `malformed_response`, `malformed_rows`, `missing_column`, `unusable_column`, `budget_spent`, `unknown_value`, `game_rejected`). Exception messages, paths, pitcher ids and file names stay in the local run record (`data_cache/processed/live_run.json`), which is not published.
- A **warning** is recorded the same way, `{source, code}`, in a separate `warnings` list. It never changes the run status. The one warning at HEAD: `statcast_pitcher` / `unmapped_pitch_type`, when a pitch code is not in `PITCH_NAME_MAP`. The pitch keeps its raw code as the source value, `family` is `null`, and no agent phrase names it (F6e).
- At HEAD the file publishes `message` (up to 300 characters of exception text) and the reason of a rejected snapshot as free text (F10).

## 3. Registry of claims

Every key that asserts a fact, with its condition on the payload. `m` = the matchup; `s` = the starter the phrase is about; `o` = his opponent's starter; `team` = the lineup the phrase is about (the opponent of `s`, so `team.offense_profile` is the offense `s` faces). Paths are relative to `m`. "Live" conditions are evaluated on live files; demo-only keys are emitted only in a demo file (rule 6). The machine form is `data_pipeline/claims_registry.py` (P0.15-D3); a test fails if the two differ, or if a catalog key is neither here nor in section 3.5.

### 3.1 Agent phrases (`agents/messages_en.py`)

| Key | Asserts | Condition |
|---|---|---|
| `analyst.summary` | The matchup features `{label}`. | `{label}` equals `report.headline`; `headline` is built from both `style_label`s when neither arsenal is limited, else from both names |
| `analyst.label.against` | `{away}` against `{home}`. | Same: `style_label`s if `not sample.limited.arsenal` for both starters, else names |
| `analyst.style.pair` / `.single` | The style description. | `pitching_profile.primary_pitch` and (for `pair`) `putaway_pitch` are named pitches, not `"Not available"`, and `not sample.limited.arsenal`; `single` when `putaway_pitch == "Not available"` |
| `analyst.read.combination` | `s` works off a primary-putaway combination. | `primary_pitch` and `putaway_pitch` named, both thrown (`count > 0`), `not sample.limited.arsenal`; the putaway pitch is at least 15% of his pitches (D30) |
| `analyst.read.mainly` | `s` works mainly off a primary pitch. | `primary_pitch` named, `putaway_pitch == "Not available"`, `not sample.limited.arsenal` |
| `analyst.read.shows` | `s` shows `{label}`. | `{label}` is `swing_miss_label` (requires `not sample.limited.strikeout`) or `command_label` (requires `not sample.limited.control`) |
| `analyst.read.qualifier` / `.qualifier_both` | The rates are from the regular season (or regular season and postseason). | `scopes.counts` is `regular_season` (or `regular_and_postseason`) and the groups of `s` differ |
| `analyst.have.pitches` | `s` has `{count}` pitches. | `{count} == sample.arsenal.pitches`, which is not `null` |
| `analyst.have.no_pitches` | `s` has no pitches on record. | `sample.arsenal.pitches == 0`, measured (F14: today also written for `null`) |
| `analyst.have.batters` | `s` faced `{count}` batters. | `{count} == sample.rates.batters_faced`, which is not `null` |
| `analyst.have.no_batters` | `s` has no batters faced on record. | `sample.rates.batters_faced == 0`, measured, with `sample.rates.source != "unavailable"` (F14: today also written for `null`) |
| `analyst.data.arsenal` | `s`'s arsenal data is limited, with the count and threshold, and no arsenal claim follows. | `sample.limited.arsenal`, `{needed} == sample.thresholds.arsenal`; no other phrase about `s` names a pitch or an arsenal fact |
| `analyst.data.strikeout` / `.control` | Strikeout (control) data is limited, with count and threshold. | `sample.limited.strikeout` (`.control`), `{needed} == sample.thresholds.strikeout` (`.control`) |
| `analyst.data.contact` | `s` allowed `{home_runs}` over `{batters}` batters faced. | `sample.rates.home_runs` and `batters_faced` are not `null`, `batters_faced > 0`, and equal the arguments |
| `analyst.data.no_home_runs` | Home runs allowed are not available for `s`. | `sample.rates.home_runs is null` or `batters_faced` is `null` or `0` |
| `analyst.strength.swing_miss` | Above-average swing-and-miss ability. | `swing_miss_label == "Above-average swing-and-miss ability"` and `not sample.limited.strikeout` |
| `analyst.strength.command` | `{label}` supports strike-zone control. | `command_label == {label}`, `{label}` is a solid or plus label, `not sample.limited.control` |
| `analyst.strength.contact` | Low contact-risk profile. | `contact_risk_label` is a low label (never in live: D24 leaves it `null`) |
| `analyst.strength.trending` | Recent form is trending the right way. | `s.recent_form` is not `null` and its label says trending (never in live) |
| `analyst.risk.command` | Below-average command can create deep-count traffic. | `command_label` is a below-average label and `not sample.limited.control` |
| `analyst.risk.contact` | Contact risk can turn missed spots into damage. | `contact_risk_label` is an elevated or high label (never in live) |
| `analyst.risk.volatile` | Recent form has been volatile. | `s.recent_form` label says volatile (never in live) |
| `analyst.offense.unavailable` | Offense data against `{hand}` is not available. | `team.offense_profile.ops_vs_hand is null` |
| `analyst.offense.strong` | The lineup hits well against `{hand}` (`{ops}` OPS). | `ops_vs_hand` not `null`, equals `{ops}`, is at least `.750` (D32); `{hand}` matches `s.throws` |
| `analyst.offense.average` | Roughly average against `{hand}`. | `ops_vs_hand` not `null`, `.700 <= ops < .750`; `{hand}` matches `s.throws` |
| `analyst.offense.weak` | The lineup has struggled against `{hand}`. | `ops_vs_hand` not `null`, `ops < .700`; `{hand}` matches `s.throws` |
| `analyst.offense.note_strikeouts` | The lineup strikes out often. | `k_rate_vs_hand` not `null`, at least `23.0` (D32) |
| `analyst.offense.note_walks` | The lineup draws walks at an above-average rate. | `bb_rate_vs_hand` not `null`, at least `9.0` (D32) |
| `analyst.pressure.ops` / `.strikeouts` / `.walks` | Internal findings (not published). | Same conditions as `offense.strong`, `note_strikeouts`, `note_walks` |
| `analyst.scope.season_figures` | `{figures}` cover the `{label}`. | Each listed figure is available (`era`/`whip`/`innings` not `"N/A"`; counts not `null`), and `{label}` is the scope of that group |
| `analyst.scope.no_season_figures` | No season figures are available. | `scopes.season_rates is null` and `scopes.counts is null`, and pitch data exists |
| `analyst.scope.differ` / `.groups` / `.group_part` | The groups cover different samples. | At least two groups with figures; their scope kinds differ; each `{label}` is that group's scope |
| `analyst.scope.same` | All pitcher figures cover `{label}`. | At least one group has figures; every group that has figures has the same scope kind `{label}` |
| `analyst.scope.none` | No season figures are available for `s`. | No group has figures (no pitches, no ERA/WHIP/innings, no counts) |
| `analyst.scope.offense` | Team offense splits cover the `{label}`. | `team.offense_profile.scope == {label}` **and** at least one of `ops_vs_hand`, `k_rate_vs_hand`, `bb_rate_vs_hand` is not `null` (F2: today the second part is not checked) |
| `writer.strength` | `s` brings this strength. | `{strength}` is the first item of the strengths derived from labels that cleared their threshold (rows `analyst.strength.*` and `analyst.style.*`) |
| `writer.strength_none` | `s` has no claimed strength because the data is limited. | `s` has a `sample` and no strength was derived |
| `writer.arsenal.contrast` | The main contrast is `{away_style}` versus `{home_style}`; the primary pitches are `{away_primary}` and `{home_primary}`. | Neither arsenal limited; `{*_style}` are the `style_label`s, `{*_primary}` the `primary_pitch`es |
| `writer.arsenal.works_off` | `s` works off `{style}`. | `{style}` is `s`'s `style_label`; `s` arsenal limited is false |
| `writer.arsenal.no_contrast` | No arsenal contrast is drawn because at least one arsenal has too little data. | At least one `sample.limited.arsenal` |
| `writer.confidence.limited` | Samples below the minimum are flagged as limited. | Some `sample.limited.*` is true |
| `writer.confidence.live_full` | The report uses a live snapshot with probable pitchers, Statcast pitch data and season offense splits. | Game state is `Preview`; **some starter has `sample.arsenal.pitches > 0`; both teams have `ops_vs_hand`** (F1: today the pitch-data part is not checked) |
| `writer.confidence.live_no_offense` | Live snapshot with probable pitchers and Statcast pitch data; offense splits not available; lineups can change before first pitch. | Game state is `Preview`; **some starter has `sample.arsenal.pitches > 0`**; some team lacks `ops_vs_hand` (F1) |
| `writer.confidence.demo` | The report is based on cached demo data. | `data_mode` is `demo_cached` or `demo_fallback` |
| `writer.watch_line`, `writer.watch_whether` | The first thing to watch. | Equals the first of `three_things_to_watch` |
| `analyst.watch.land` | Can `s` land the `{putaway}` early? | `putaway_pitch == {putaway}` named, at least 15% of his pitches, `not sample.limited.arsenal` |
| `critic.summary.supported` / `.warnings` / `.unsupported` | The critic checked `{checked}` claims, none unsupported, `{warnings}` warnings. | `{checked} == len(checks)`; counts equal the statuses in `checks`; `unsupported` never published (the generator stops) |
| `critic.note.focus` | The report is focused on matchup fit, not outcome prediction. | The check `critic.betting.claim` ran and has status `not_present` (F8) |
| `critic.note.stuff_plus` | Avoided claiming official Stuff+. | **No condition can be stated; removed in D2.1** (F8) |
| `critic.pitch.claim` + `.supported_primary` / `.supported_putaway` / `.low` / `.low_counts` | `s`'s primary (put-away) pitch is `{pitch}`, with usage. | `{pitch} == primary_pitch` (`putaway_pitch`); `{count}`/`{total}` are `pitch_mix[].s.count`/`total`; `supported` needs `count/total >= 30%` (`15%`), else a warning |
| `critic.pitch.absent` | `{pitch}` is not in `s`'s pitch mix. | `pitch_mix[].s.count == 0` or the pitch is missing from the mix |
| `critic.names.claim` / `.supported` / `.credited` / `.nobody` / `.unsupported` | The report names only pitches thrown by the starter it credits. | Every pitch named in `s`'s own sentences has `pitch_mix[].s.count > 0` |
| `critic.limited.claim` / `.supported` / `.unsupported` | `s`'s arsenal is limited and the report names no pitch for him. | `sample.limited.arsenal`; no pitch named in `s`'s own sentences |
| `critic.command.*` | The report's command claim about `s` matches his label. | `command_label` for `s` (or "not available"); `walks`/`batters` equal `sample.rates`; `{scope}` equals `scopes.counts` |
| `critic.scope.claim` / `.same` / `.supported` / `.unsupported` / `.all_claimed` | The report says the figures cover different samples, when they do. | `labels.scopes_differ(s)` matches what the report says; "all pitcher figures cover" never about a starter whose groups differ |
| `critic.betting.claim` / `.absent` / `.unsupported` | The report does not predict the winner. | No term of `critic.betting_terms` in any report text |
| `grader.explanation.*`, `grader.plan.*`, `grader.next.*`, `grader.call.*` | Facts about a completed start (Game Score band, walks, hits, earned runs, strikeouts, innings). | `m.postgame` is not `null` and the figure comes from `postgame.starter_lines.s` (box score from the source); never emitted for `Preview` or `Live` games; at HEAD `postgame` is `null` for live files, so none is emitted |
| `scout.final.*`, `scout.demo.*` | Demo notes. | Demo files only (rule 6) |
| `analyst.demo.*`, `analyst.fallback.*`, `analyst.command_note.*`, `analyst.contact_note.*`, `writer.default_strength` | Demo reads built from demo labels and fallbacks. | Demo files only (a live starter always has `sample`, which routes to the live reads) |

### 3.2 Generator text (`data_pipeline/`), registered by the same function

Keys have the form `generator.*`; their text stays in the generator, in English (D31), and each emission records its key and args.

| Key | Asserts | Condition |
|---|---|---|
| `generator.workflow.loaded` | Loaded data for `{N}` matchups. | `{N} == len(matchups)`; the word "cached" only when `data_mode` is a demo mode (F3, F4) |
| `generator.workflow.identified`, `.generated` | The agents identified findings and wrote reports. | Every matchup has a `report` |
| `generator.workflow.checked` | The critic checked every claim: none unsupported, `{w}` warnings. | `{w}` equals the warnings across the matchups of the file; no `unsupported` |
| `generator.workflow.graded` | Graded `{n}` completed starters. | `{n}` equals the number of `postgame.starter_lines` in the file; otherwise the step is `not_applicable` |
| `generator.metadata.last_updated` | Live data fetched `{date}`. | `data_mode == fetched_snapshot`, `{date}` is the date of `data_fetched_at` |
| `generator.metadata.data_sources` | Each listed source was used. | MLB Stats API and Baseball Savant listed only when the file has fields from them; "Cached demo snapshots" only in demo modes (F3) |
| `generator.confidence.note` | Live snapshot fetched `{date}` for `{id}`. | `{date}` equals the date of `data_fetched_at`; `{id}` is the matchup's `id` |
| `generator.archive.result_label` | Pregame report available. | Game state is `Preview` (for other states the label follows the state) |

### 3.3 Frontend text

| Text | Asserts | Condition |
|---|---|---|
| Mode line "Live data · fetched {date}" | The page shows live data. | `data_mode == fetched_snapshot`; `{date}` from `data_fetched_at` |
| Mode line "Demo data: live data unavailable" | The page shows demo data because live data failed. | `data_mode == demo_fallback` |
| Mode line for `demo_cached` | The page shows demo data. | `data_mode == demo_cached` |
| Hero, layout description, footer disclaimer | Describe the data source. | Neutral text in a live file; "cached demo" wording only in a demo file (F3) |
| Carousel badge "Today" | The game's date is today. | `matchup.date` equals the current date in America/New_York (F12) |
| Status badge | The game's state. | Equals the published `status` |
| Start time "7:05 PM EDT" / "23:05 UTC" | The game starts then. | `start_time_utc` valid; zone is `game.timezone` or UTC (D33) |
| Starter card captions "ERA, WHIP and K: {scope}" | The scope of the group. | The group has figures and `scopes.*` equals `{scope}` (rule 3) |
| "Pitch data: {scope}" | The scope of the pitch data. | `sample.arsenal.scope` equals `{scope}` and `pitches > 0` |
| "No past reports yet" | The archive has no live rows. | A live file with `archive == []` |
| Unavailable texts: "Bio not available", "Recent form not available", "Venue not available", "Offense data not available", "Start time not available", "Movement data not available for this pitch", "No left-handed batters faced.", "Not available for live data yet.", "Arsenal data limited: …" | The value is unavailable. | Emitted if and only if the field is in its unavailable state (both directions) |

### 3.4 Static labels that assert nothing about data

Section titles other than "Today's Matchup Summary", team names, pitch names, column headers, units. A label that carries a time word ("Today's") is not static: it is registered above and fixed in D2.5 (F16).

### 3.5 Catalog entries that assert nothing

`@join` and `@capitalize` (they only combine other sentences), `count.*` (plurals), `analyst.list_and`, `analyst.goal.*`, `analyst.read.he`, `analyst.figure.*`, `analyst.figure.list_and`, `analyst.watch.ahead`, `analyst.watch.efficient`, `analyst.watch.keep`, `analyst.watch.deep` (questions), `analyst.offense.with_notes` (joins two phrases), `writer.watch_prefix`, `writer.section.*` (titles, except the F16 title), `writer.forbidden_terms`, `writer.required_terms`, `critic.role.*`, `critic.generic_fastball`, `critic.pitch_aliases`, `critic.limited.pitches`, `critic.limited.none`, `critic.command.word`, `critic.command.no_label`, `critic.scope.marker`, `critic.scope.all_marker`, `critic.betting_terms`, `critic.betting.item`. (Fragments and vocabularies used by the phrases above.)

## 4. Known violations at HEAD `043db03` and where each is closed

| Id | Rule | Closed in | One line |
|---|---|---|---|
| F1 | 4 | P0.15-D2.1 | Confidence note claims "Statcast pitch data" without checking it |
| F2 | 3, 4 | P0.15-D2.1 | Offense scope stated when no offense figure exists |
| F3 | 6 | P0.15-D2.4 | "Cached Demo" texts and no mode line in a live page |
| F4 | 6 | P0.15-D2.4 | Demo matchups and archive rows inside a live file |
| F5 | 7 | P0.15-D2.5 | `status` is always `upcoming` |
| F6 a, b, c, e | 1, 2, 8 | P0.15-D2.2 | Silent debut, measured zeros from an unusable `events`, columns outside the required check, invented family |
| F7 | 1, 2 | P0.15-D2.2 | `"???"` team abbreviation |
| F8 | 1, 4 | P0.15-D2.1 | Two constant critic notes |
| F9 | 6 | P0.15-D2.4 | `generated_at` is the fetch time, or a demo constant |
| F10 | 8 | P0.15-D2.3 | Raw exception text in the public file |
| F11 | 5 | P0.15-D2.3 | One unsafe game (or hand `S`) rejects the whole snapshot |
| F12 | 7 | P0.15-D2.5 | "Today" compared with the UTC date |
| F13 | — | not touched | What the page renders of the report is a small part of it |
| F14 | 2, 4 | P0.15-D2.2 | "no batters (pitches) faced on record" written for a `null` count (`agents/matchup_analyst.py`) |
| F15 | 2 | P0.15-D2.3 | The analyst falls back to the right hand (`starter.get("throws", "R")`, `_throws_label`); with hand `S` it would write "SHP" |
| F16 | 4, 7 | P0.15-D2.5 | "Today's Matchup Summary" and "before first pitch" are time claims with no condition |

F13 is not a violation of a rule but a note on how little of the JSON the page shows; the contract still applies to what is not rendered.

## 5. How this is checked

1. **Tests first** for every fix (`docs/ENGINEERING.md`): reproduce the finding, see it fail, then fix.
2. **Generic checks** (P0.15-D3): `validate_payload` applies rules 1 to 4, 6 and 8 to every field and every recorded phrase of every file, not to the cases someone thought of. One negative test per rule shows that the check fails on a payload that breaks it.
3. **Matrix** (P0.15-D3): 72 combinations, API (complete, partial, absent) × season (regular only, with postseason) × starter (debut, limited, healthy) × day (normal, opening day) × throwing hand (present, missing), each through pipeline → generator → `validate_payload`; per case the game is published or fails with an explicit recorded error, and the contract holds.
4. **Frontend phrases** (3.3) are not in the JSON, so `validate_payload` cannot see them: each row of 3.3 has a component test that checks its condition, added in the D2 commit that owns it.
5. **QA gate** (D27): QA checks compliance with this contract as a finding area of its own.
