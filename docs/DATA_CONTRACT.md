# Data contract — what the published file may say

Normative (decision D34). This contract defines what `public/data/pitchcraft-demo.json`, and every text that describes it, may contain. It does not replace `docs/DECISIONS.md`: where they differ, the decision wins and the difference is reported. QA (`docs/QA_PROTOCOL.md`) verifies compliance with this contract. A rule changes only through a new decision.

- **Annex A:** `docs/data-inventory.md`, the field-by-field inventory of the live payload at HEAD `043db03`. Its findings F1 to F13 (and F14 to F20, added below) are the **known violations** of this contract. Each is closed by the commit named in section 4; until then, `data_pipeline/known_violations.py` tolerates it and the generic checks of P0.15-D3 report it.
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
- `data_confidence.lineup_status: "probable_pitchers"` and `pitch_data_status: "fetched_snapshot"` are constants that assert what the data contains (F5). `pitch_data_status` was one too (F1) until P0.15-D2.1b: it is now computed, `fetched_snapshot` when at least one starter has pitch data and `unavailable` (the word `sample.rates.source` uses) when none has.
- `charts.pitch_movement.*.*.family: "Fastball"` for an unmapped pitch is an invented derivation (F6e).
- `family` for a mapped pitch, `teams.*.record: null`, `bio: null` are correct: the first is a derivation from a name map, the others are explicit unavailable states.
- `critic_review.revision_notes` ending with "Avoided claiming official Stuff+." is a constant asserting that a check happened; no check exists (F8).

**Check (`data_pipeline/provenance.py`, section 6):** a manifest lists every path of a live file with its kind and, for a source value, its source. A leaf outside the manifest (`rule1:unlisted`), a constant that asserts a fact (`rule1:constant_asserts_fact`), a wrong type, a placeholder given as a value (`rule1:placeholder`), a family invented for a pitch the map does not know (`rule1:invented_derivation`) and a derivation that does not recompute (`rule1:derivation_mismatch`) fail validation.

### Rule 2. Unknown is never zero

*`null` when unknown. `0` only when the source measured zero. A column that cannot be used is unavailable plus a recorded error.*

Examples:

- `events` null in every row of a Statcast frame published `batters_faced 0`, `strikeouts 0`, `walks 0`, `home_runs 0` from source `statcast`, and the card showed K "0" (F6b). The code could not tell "no plate appearance completed" from "unusable column". The column is unusable: the counts are `null`, `sample.rates.source` is `"unavailable"`, and an error is recorded.
- The analyst writes "no batters faced on record" and "no pitches on record" when the count is `null`, because it tests `if batters` (F14). A missing count is not a zero count.
- `_usage_pct` returning `None` for a side the starter never faced (P0.14-C) is correct; a real `0%` against a side he did face stays `0%`.
- `pitch_type` null in every row of a populated frame produced a debut with `pitches 0` and no error (F6a). Same class.
- A starter who threw no pitch has `charts.pitch_mix[].<slot>.overall = 0` for each pitch his opponent threw (F20): a share of zero pitches is unknown, `null`, not 0%. His `count` of 0 out of a `total` of 0 is the measured zero; the share is what cannot be computed.

**Check (`data_pipeline/provenance.py`, section 6):** the manifest names, for every numeric field, the evidence a `0` requires (section 6.3). A `0` without its evidence fails (`rule2:zero_without_evidence`); so does an unknown value written as a number for a source that is `unavailable`, or as `"0"`, `""` or `"N/A"` text in a numeric field (`rule2:unknown_written_as_value`). A guessed default such as a throwing hand is found by the matrix, not by the payload: the hand is a source value and the payload cannot say which source gave it (`tests/test_matrix.py` makes the people endpoint answer the opposite of the guess).

### Rule 3. Scope

*Each group of figures carries the scope of its source. No scope is stated for a group without figures.*

A group has a figure when a value is known, **a measured zero included** (rule 2): a debut's 0 pitches come from a valid Statcast answer, so `sample.arsenal.scope` stays and says which games the zero was measured over. An unknown value (`null`, `"N/A"`, a `sample.rates.source` of `"unavailable"`) is not a figure: the group has no scope in any field that carries one, and the field is `null`. A scope is a field; the sentence that states it (rule 4) follows the same rule.

The constructors decide this, not the checks: `labels.build_sample` writes `sample.arsenal.scope = null` when the pitch count is unknown and `sample.rates.scope = null` when the counts are unavailable; `live_matchup.build_offense` writes `offense_profile.scope`, `summary_label` and `recent_form` only when the lineup has an OPS, K% or BB% (a split with none of them is no split). These fields are nullable since schema 0.4.0 (P0.15-D2.1a), and a live snapshot is read only if its `schema_version` is exactly the code's (`schema.snapshot_matches_schema`; a missing or different one is rejected). The file says only `data_status.reason = {source: "snapshot", code: "snapshot_schema_mismatch"}` (rule 8); the versions go to the local log. Recorded as D36.

Groups at HEAD: pitch data (Statcast; `sample.arsenal.scope`, `charts.*`), season rates (ERA, WHIP, innings; MLB API; `scopes.season_rates`), counts (strikeouts, walks, home runs, batters faced; the API or Statcast; `scopes.counts`, `sample.rates.scope`), team offense (Savant; `offense_profile.scope`). Scope is `regular_season` or `regular_and_postseason`, through the cutoff (D29).

**Source of the counts** (QA3-02, P0.14-A). The four counts (batters faced, strikeouts, walks, home runs) come from the MLB API line when it gives all four. Otherwise they come from the valid Statcast plate appearances, if the starter has pitches. Otherwise they come from a partial API line, if it has any count. Otherwise they are unavailable (`sample.rates.source` is `"unavailable"`, every count `null`). Sources are never mixed field by field. `sample.rates.source` says which one gave them, and the scope of the group is that of the source: regular season for the API, the scope of the pitch data for Statcast.

Examples:

- ERA from the regular-season API labelled "regular season and postseason" because the counts came from Statcast (QA4-01, closed in P0.15-B).
- `offense_profile.scope` was set while every offense figure was `null`, and the analyst wrote "Team offense splits cover the regular season through D" one sentence after "Season offense splits were not available" (F2, closed in P0.15-D2.1a).
- A starter with no figure in any group has no scope (closed in P0.15-B: "no season figures are available").
- `sample.rates.scope` was set while the counts were unavailable (`sample.rates.source` is `"unavailable"`), though `season_summary.scopes.counts` was `null` (F17, closed in P0.15-D2.1a). `sample.arsenal.scope` with `pitches == 0` is **not** this: the zero was measured.

**Check (`data_pipeline/contract_checks.py`, `GROUPS`):** one table of groups (pitch data, season rates, counts, offense), each with how to tell that it has a figure, every field that carries its scope, and the source rule. A figure without a scope, a scope without a figure, or a scope that disagrees with the source of its group fails (`rule3:<group>#figures_without_scope`, `#scope_without_figures`, `#scope_disagrees_with_source`). Only live matchups are asked. No sentence says "all figures" about a starter whose groups differ.

### Rule 4. Claims

*Every sentence that asserts a fact (agent text, UI text or workflow text) declares the fields that make it true and is emitted only when they do. This applies to JSON nobody renders.*

- Each emitted phrase is recorded as a claim `{id, key, args, subject, location}`. The sentences of a matchup (report, critic review, data confidence notes, postgame) are in `matchups[i].report.claims[]`, with locations relative to the matchup (`report.sections[1].body`); the sentences the generator writes (workflow, data label) are in `claims[]` at the root, with locations from the root. `subject` is the starter the sentence is about (`away_starter`, `home_starter`) or `null`; `location` is `null` for a part of another sentence. `metadata.language` says which catalog the keys belong to.
- `args` are values copied from the payload (a name, a number, a label, a scope) or `{"claim": id}`, a reference to a claim that is part of the sentence (a plural such as "3 home runs" inside a longer sentence). Never an internal (a path, an exception, a function name, an object). Two pseudo keys build sentences out of sentences: `@join` (args `sep` and `parts`) and `@capitalize` (arg `of`); they assert nothing themselves.
- The text of a report is exactly the join of its registered phrases. The validator renders each claim again from its key and args and requires the text of the field to be exactly that; a text field with no claim, a claim for a field that does not exist, a part that no sentence uses, or a sentence edited after the fact fails. Which fields are text is a list in `data_pipeline/claims.py` (`MATCHUP_TEXT_PATHS`, `ROOT_TEXT_PATHS`); the static content of the demo (archive rows, disclaimers, bios) is not agent or generator text and joins the list when it becomes mode-dependent (D2.4).
- Each key has a condition in the registry (section 3). The validator evaluates it on the payload and the args. A phrase whose condition is false fails (`rule4:<key>#<reason>`).
- **A text argument is a payload value, a reference, or one of the forms below.** `tests/test_claim_args.py` fails over the four generated payloads, the fourteen golden scenarios and the served file if a text argument of any claim is none of these: a reference `{"claim": id}`; the separator of an `@join`; the empty text (a qualifier that is not written); or a value of the payload outside the sentences, written in one of these forms. The list is closed: a new form needs its reason written here and a test.
  1. *As is*: a name, a label, a scope or a pitch exactly as the payload has it. The sentence quotes the value.
  2. *Lower case*: `solid command`, `four-seam fastball`. A label or a pitch in the middle of a sentence is written in lower case; the value does not change.
  3. *First letter in lower case*: `above-average swing-and-miss ability`. A rate label ("Above-average swing-and-miss ability") that follows its subject ("He shows …") loses its capital and nothing else.
  4. *Without ` fastball`, then lower case*: `four-seam`, `sinker`. The data says "Four-seam Fastball"; a sentence says the pitch by its short name.
  5. *A number written as text*: the number of the payload as Python writes it (`str(n)`) or without a trailing zero (`12.0` is `12`). The critic writes a share inside a sentence. A figure computed from two payload numbers (a percentage of two counts) or grouped with thousands separators is not a form of a payload value; the condition of its key in the registry checks it against the raw counts (`critic.pitch.low_counts`).
  A piece cut out of another sentence (the action of a question, the names of two starters joined with `", "`) is none of these: it is its own phrase, referenced (`analyst.watch.action.*`, `@join`).
- **The condition of a claim about data is evaluated on the payload, never by running the critic again.** A claim about data (`critic.pitch.*`, `critic.names.*`, `critic.limited.*`, `critic.command.*`, `critic.scope.*`, `critic.betting.*`) is checked against the fields it speaks about: `count`/`total` of the pitch mix, `sample`, `scopes`, the labels, and the text of the report read with the words of the catalog (`data_pipeline/report_facts.py`). Running the critic again is only for claims about the process (`critic_review.summary` and the notes), and those read the published `checks`, not the critic: the critic is the only definition of what a check is. `tests/test_registry_no_critic.py` fails if a module that checks the contract imports the critic, or if the contract cannot run over the corpus with every function of the critic made to fail. `tests/test_critic_facts_differential.py` measures what that independence costs: it runs the critic and `report_facts` over every report of the corpus and the matrix, and over reports with injected sentences, and fails if they disagree on who a sentence is about, which pitches it names, or the verdict of the names, limited-arsenal, command, scope or betting check. Its injection layer assumes that how a pitch is named does not depend on the matchup, so its variants rotate over 13 matchups chosen for coverage (every combination of limited arsenal, differing groups and command label of a starter, and every relation of the two pitch sets) instead of crossing with all of them; a test checks that the injected sentences reach every branch of the critic's data checks in those matchups. A sentence that reports a problem the data has (`critic.names.credited`, `.nobody`, `.unsupported`, `critic.limited.unsupported`, `critic.command.wrong_*`, `critic.scope.unsupported`, `.all_claimed`, `critic.betting.unsupported`) is never in a published file: the generator stops on an `unsupported` check (rule 5, exception), so the check reports it (`#published`).
- No agent phrase names a pitch that is not in the mapped set (see rule 8, warnings).
- A text that says a game is upcoming ("upcoming", "tonight", "before first pitch", "today") is emitted only when the source state is `Preview` (and for "today", the game's date is today in its official zone). It never appears for a game whose state is `Live` or `Final`.

Examples:

- "This report uses a fetched live snapshot with probable pitchers and Statcast pitch data" was written for a game of two debuts, with no pitch data (F1, closed in P0.15-D2.1b: the note is now built from parts, one per starter and per lineup). The condition of the Statcast part is that a starter has `sample.arsenal.pitches > 0`; the condition of "season offense splits" is that both teams have a split.
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

- `data_status.live_run.errors` and `data_status.reason` carry a `source` from the fixed set (`mlb_schedule`, `mlb_person`, `mlb_season_stats`, `statcast_pitcher`, `savant_team_batting`, `snapshot`) and a `code` from a closed set defined in `data_pipeline/` (initial set: `request_failed`, `malformed_response`, `malformed_rows`, `missing_column`, `unusable_column`, `budget_spent`, `unknown_value`, `game_rejected`, `snapshot_schema_mismatch`). Exception messages, paths, pitcher ids and file names stay in the local run record (`data_cache/processed/live_run.json`), which is not published.
- A **warning** is recorded the same way, `{source, code}`, in a separate `warnings` list. It never changes the run status. The one warning at HEAD: `statcast_pitcher` / `unmapped_pitch_type`, when a pitch code is not in `PITCH_NAME_MAP`. The pitch keeps its raw code as the source value, `family` is `null`, and no agent phrase names it (F6e).
- At HEAD the file publishes `message` (up to 300 characters of exception text) and the reason of a rejected snapshot as free text (F10).

## 3. Registry of claims

Every key that asserts a fact, with its condition on the payload. `m` = the matchup; `s` = the starter the phrase is about; `o` = his opponent's starter; `team` = the lineup the phrase is about (the opponent of `s`, so `team.offense_profile` is the offense `s` faces). Paths are relative to `m`. "Live" conditions are evaluated on live files; demo-only keys are emitted only in a demo file (rule 6). The machine form is `data_pipeline/claims_registry.py` (P0.15-D3.2); a test fails if the two differ, or if a catalog key is neither here nor in section 3.5.

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
| `analyst.scope.offense` | Team offense splits cover the `{label}`. | `team.offense_profile.scope == {label}` **and** at least one of `ops_vs_hand`, `k_rate_vs_hand`, `bb_rate_vs_hand` is not `null` (the builder writes no scope otherwise; F2, closed in P0.15-D2.1a) |
| `writer.strength` | `s` brings this strength. | `{strength}` is the first item of the strengths derived from labels that cleared their threshold (rows `analyst.strength.*` and `analyst.style.*`) |
| `writer.strength_none` | `s` has no claimed strength because the data is limited. | `s` has a `sample` and no strength was derived |
| `writer.arsenal.contrast` | The main contrast is `{away_style}` versus `{home_style}`; the primary pitches are `{away_primary}` and `{home_primary}`. | Neither arsenal limited; `{*_style}` are `analyst.style.*` sentences (made of the primary and put-away pitch), `{*_primary}` the `primary_pitch`es |
| `writer.arsenal.works_off` | `s` works off `{style}`. | `{style}` is `s`'s `style_label`; `s` arsenal limited is false |
| `writer.arsenal.no_contrast` | No arsenal contrast is drawn because at least one arsenal has too little data. | At least one `sample.limited.arsenal` |
| `writer.confidence.limited` | Samples below the minimum are flagged as limited. | Some `sample.limited.*` is true |
| `writer.confidence.snapshot` + `writer.confidence.item.pitchers` / `.pitch_data` / `.offense` | This report uses a fetched live snapshot with `{items}`: probable pitchers, Statcast pitch data, season offense splits ("A, B, and C" / "A and B" / "A"). | The matchup is live. The list names only what is complete: `item.pitch_data` only if **both** starters have pitch data (`sample.arsenal.pitches > 0`; zero or unknown is none); `item.offense` only if **both** lineups have a split (an OPS, a K% or a BB% is not `null`, as `offense_profile.scope` is set; F2). With everything complete the text is the one of before D2.1b (F1) |
| `writer.confidence.pitch_data.one` / `.none` | Statcast pitch data was available for `{with_data}` but not for `{without_data}`, so the pitch read makes no arsenal claims about `{without_data}` / was not available for either starter, so the pitch read makes no arsenal claims. | `one`: exactly one starter has pitch data, `{with_data}` is his name and `{without_data}` the other's; `none`: neither has it. The consequence is checked on the report: no sentence names a pitch for a starter without pitch data (`report_facts.pitches_named_for`; his arsenal is then limited, and the analyst writes no style, primary or put-away pitch for him) (F1, closed in P0.15-D2.1b) |
| `writer.confidence.offense.one` / `.none` | Season offense splits were available for the `{with_split}` lineup but not for the `{without_split}` lineup, so the lineup read makes no offense claims about the `{without_split}` lineup / were not available for this game, so the lineup read makes no offense claims. | `one`: exactly one lineup has a split, `{with_split}` is its team name and `{without_split}` the other's; `none`: neither has one. The consequence is the rule of `analyst.offense.*` (a read of OPS, strikeouts or walks needs the figure it names), so a lineup without a split has only "not available for this lineup yet" (F1, closed in P0.15-D2.1b) |
| `writer.confidence.lineups` | Lineups can still change before first pitch. | The matchup is live, and the game state is `Preview` (F5, F16). Last of the parts of the note, after what is missing |
| `writer.confidence.demo` | The report is based on cached demo data. | The matchup is not live (`data_confidence.level` is not `fetched_snapshot`); a demo sentence in a live matchup is a violation, and a demo matchup inside a live file is rule 6 (F4) |
| `writer.watch_line`, `writer.watch_whether` | The first thing to watch. | `{name}` and `{action}` are those of the first question of `three_things_to_watch`: the same claim, not a copy of its text |
| `analyst.watch.action.land` | `s` can land the `{putaway}` early (the action of a question). | `putaway_pitch == {putaway}` named, at least 15% of his pitches, `not sample.limited.arsenal` |
| `writer.section.summary` | The game is today ("Today's Matchup Summary"). | The state of the game is known and is `Preview` (F16; a live matchup's published `status` is not yet the schedule's state, F5) |
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
| `scout.final.*`, `scout.demo.*` | Demo notes. | The matchup is a demo one (not live): final for `scout.final.*`, not final for `scout.demo.*` (a demo matchup inside a live file is rule 6, F4) |
| `analyst.demo.*`, `analyst.fallback.*`, `analyst.command_note.*`, `analyst.contact_note.*`, `writer.default_strength` | Demo reads built from demo labels and fallbacks. | A demo matchup and a starter with no `sample` (a live starter always has one, which routes to the live reads) |

The conditions of `critic.names.*`, `critic.limited.*`, `critic.command.*`, `critic.scope.*` and `critic.betting.*` are evaluated on the payload (P0.15-D3.3a), with `data_pipeline/report_facts.py` reading the text of the report: a sentence belongs to the starter it names alone, or, if it names nobody, to the starter in the title of its section (QA3-04). The pitch checks (`critic.pitch.*`) and the summary are checked against the raw counts and the list of checks. `critic.role.*` asserts nothing (section 3.5): the role is a word, and the claim that uses it (`critic.pitch.claim`) is the one with a condition. `analyst.pressure.*` are internal findings: any appearance in the published text is a violation.

### 3.2 Generator text (`data_pipeline/`), registered by the same function

Keys have the form `generator.*`; their text stays in the generator, in English (D31), and each emission records its key and args.

| Key | Asserts | Condition |
|---|---|---|
| `generator.workflow.loaded` | Loaded data for `{count}` matchups. | `{count}` is the number of matchups the file counts: every matchup of a demo file, only the live ones of a live file (F4); the word "cached" only in a demo file (F3) |
| `generator.workflow.identified`, `.generated` | The agents identified findings and wrote reports. | Every matchup the file counts has a `report` |
| `generator.workflow.checked` | The critic checked every claim: none unsupported, `{warnings}` warnings. | `{warnings}` equals the warnings across the matchups the file counts; no `unsupported` |
| `generator.workflow.graded`, `.graded_none` | Graded `{count}` completed starters / the featured game has not been completed. | `{count}` equals the number of `postgame.starter_lines` of the matchups the file counts; `.graded_none` only when that number is 0 |
| `generator.metadata.last_updated.live` | Live data fetched `{date}`. | `data_mode == fetched_snapshot`; `metadata.data_fetched_at` exists and `{date}` is its date (F9: the field does not exist yet) |
| `generator.metadata.last_updated.fallback`, `.demo` | Live data is unavailable and the page shows demo data / the data is a demo. | `data_mode` is `demo_fallback` / `demo_cached` |
| `generator.confidence.live_note` | Live snapshot fetched `{date}` for `{matchup_id}`. | The matchup is live, `{matchup_id}` is its `id`, `{date}` is the date of `metadata.data_fetched_at` (F9) |

Texts of the generator that are not keys yet (they become keys in P0.15-D2.4, with F3): `metadata.data_sources` (each listed source is used: MLB Stats API and Baseball Savant only when the file has fields from them, "Cached demo snapshots" only in demo modes, F3) and the archive's `result_label` ("Pregame report available" only when the game state is `Preview`). Rule 6 already checks the wording of `metadata.data_sources` and `disclaimers` in a live file.

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

`@join` and `@capitalize` (they only combine other sentences), `count.*` (plurals), `analyst.list_and`, `writer.confidence.list_two`, `writer.confidence.list_three` (the list of the first sentence of the note), `analyst.goal.*`, `analyst.read.he`, `analyst.figure.*`, `analyst.figure.list_and`, `analyst.watch.question`, `analyst.watch.action.ahead`, `analyst.watch.action.efficient`, `analyst.watch.action.keep`, `analyst.watch.deep` (questions and the actions they are made of; the land action asserts a put-away pitch and is registered above), `analyst.offense.with_notes` (joins two phrases), `writer.section.*` (titles, except the F16 title), `writer.forbidden_terms`, `writer.required_terms`, `critic.role.*`, `critic.generic_fastball`, `critic.pitch_aliases`, `critic.limited.pitches`, `critic.limited.none`, `critic.command.word`, `critic.command.no_label`, `critic.scope.marker`, `critic.scope.all_marker`, `critic.betting_terms`, `critic.betting.item`, `generator.workflow.description` (describes the product, not the data). (Fragments and vocabularies used by the phrases above.)

## 4. Known violations at HEAD `043db03` and where each is closed

| Id | Rule | Closed in | One line |
|---|---|---|---|
| F1 | 4 | P0.15-D2.1b (done) | Confidence note claims "Statcast pitch data" without checking it |
| F2 | 3, 4 | P0.15-D2.1a (done) | Offense scope stated when no offense figure exists |
| F3 | 6 | P0.15-D2.4 | "Cached Demo" texts and no mode line in a live page |
| F4 | 6 | P0.15-D2.4 | Demo matchups and archive rows inside a live file |
| F5 | 7 | P0.15-D2.5 | `status` is always `upcoming`, in the matchup and in its archive row (with the row's `result_label` and `lineup_status`) |
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
| F17 | 3 | P0.15-D2.1a (done) | `sample.rates.scope` is set while the counts are unavailable (found by the rule 3 check in P0.15-D3.2) |
| F18 | 4 | P0.15-D2.1 | "Can X land the changeup early in counts?" for a put-away pitch under 15% of his pitches: the demo's `matchup_002` (Demo Pitcher C, 12%), where the critic warns about the same pitch (found by the rule 4 check in P0.15-D3.2) |
| F19 | 1 | P0.15-D2.4 | The status of the first four steps of `agent_workflow` (`completed`) is written fixed: no step reads its own result (found by the manifest in P0.15-D3.3b-2, classified with the owner's criterion, section 6.2) |
| F20 | 2 | P0.15-D2.2 | `charts.pitch_mix[].<slot>.overall` is `0` when the starter has no pitch (`total` 0): a share of nothing written as 0% (found by the manifest in P0.15-D3.3b-2 over the debut cells of the matrix) |

F13 is not a violation of a rule but a note on how little of the JSON the page shows; the contract still applies to what is not rendered.

## 5. How this is checked

1. **Tests first** for every fix (`docs/ENGINEERING.md`): reproduce the finding, see it fail, then fix.
2. **Generic checks** (P0.15-D3): `validate_payload` applies rules 1 to 4, 6 and 8 to every field and every recorded phrase of every file, not to the cases someone thought of. One negative test per rule shows that the check fails on a payload that breaks it.
3. **Matrix** (P0.15-D3): 72 combinations, API (complete, partial, absent) × season (regular only, with postseason) × starter (debut, limited, healthy) × day (normal, opening day) × throwing hand (present, missing), each through pipeline → generator → `validate_payload`; per case the game is published or fails with an explicit recorded error, and the contract holds. The cells are defined in `tests/matrix.py`: the away starter varies and the home starter is healthy; "hand missing" means the Statcast frame has no `p_throws` and the people endpoint answers `L` (the opposite of a guessed right hand); on opening day the cutoff is before the season, so every starter is a debut and the cells that no source can tell apart must publish the same file. The hard cases outside the product (two debuts, two limited, the other side of the pair, real API zeros, no Savant data, `events` or `pitch_type` null, an unmapped pitch code, an unknown team, a failed hand lookup, a switch pitcher, a frame without a needed column, a starter without a hand) are in the same module. A finding the payload cannot show (F6a, F6b, F6c, F6e, F7, F11, F15) is an `xfail(strict=True)` labelled with its F until its fix in P0.15-D2.
4. **Frontend phrases** (3.3) are not in the JSON, so `validate_payload` cannot see them: each row of 3.3 has a component test that checks its condition, added in the D2 commit that owns it.
5. **QA gate** (D27): QA checks compliance with this contract as a finding area of its own.

## 6. The manifest of a live file (rules 1 and 2)

`data_pipeline/provenance.py` (P0.15-D3.3b-2). `MANIFEST` is a table of entries `(pattern, kind, origin, types, nullable, check)`. Every leaf of a live file, and every empty list or map (the unavailable state of what it would hold), must match one entry. Demo matchups and archive rows inside a live file are not walked: they are rule 6's finding (F4). A demo file is not asked.

### 6.1 Kinds

| Kind | Meaning | The check |
|---|---|---|
| `source` | A value the source gave. | The type, the format (a date, a UTC instant, a team abbreviation) and the evidence a zero needs. |
| `derivation` | Computed by a documented rule. | The value is recomputed from its inputs and compared: the pitching profile from the pitch mix and the sample (D24, D25, D30), `limited` from the sample, the family from the pitch map, the lineup's hand from the opposing starter, the title of an archive row from the teams. |
| `label` | A constant that asserts nothing about data. | The type, and a closed set where there is one (the schema version, the names of the agents, the thresholds of D24). |
| `claim` | A sentence, or the record of the sentences. | Rule 4 owns the condition. |
| `fact` | A constant that asserts a fact, written fixed without looking at the outcome. | It is a violation by definition, with the finding it belongs to. The fix of that finding turns the entry into a derivation with its evidence. |

A `null` is allowed only where the entry says `nullable`. The codes are `rule1:unlisted`, `rule1:null_not_declared`, `rule1:wrong_type`, `rule1:constant_asserts_fact`, `rule1:derivation_mismatch`, `rule1:placeholder`, `rule1:invented_derivation`, `rule2:zero_without_evidence` and `rule2:unknown_written_as_value`, each followed by `#` and the pattern of the entry. A check that cannot read its neighbours (a malformed sample) fails closed with `rule1:derivation_mismatch`.

### 6.2 Statuses: derivation or constant that asserts a fact

The owner's criterion (2026-10-13): a status is a documented derivation if it is set from the real outcome of the step (the agent ran and finished); it is a constant that asserts a fact if it is written fixed without looking at the outcome. Applied to every status the manifest finds:

| Field | How the code sets it | Classification |
|---|---|---|
| `agent_workflow.steps[4].status` (postgame) | `completed` or `not_applicable` from the number of graded starters | Derivation. The check requires it to agree with the step's own recorded sentence (`generator.workflow.graded` or `.graded_none`). |
| `agent_workflow.steps[0..3].status` | The literal `completed` in `_build_agent_workflow`; nothing reads the result of the step. It is true today only because any failure stops the generator (rule 5, exception). | Constant that asserts a fact: **F19**, closed in P0.15-D2.4. |
| `critic_review.status` | `reviewed`, written by the critic at the end of its own run (owner, 2026-10-14) | Derivation, with evidence: `checks[]` is not empty and every `checks[].status` is in the closed set. Without it, `rule1:constant_asserts_fact#matchups[].critic_review.status`. |
| `critic_review.checks[].status` | The verdict of each check | Derivation (closed set). |
| `matchups[].status`, `archive[].status` | The literal `upcoming` | Constant that asserts a fact: **F5**. The archive row joins the finding. |
| `archive[].result_label` | The literal "Pregame report available" | Constant that asserts a fact: **F5**. |
| `data_confidence.lineup_status` | The literal `probable_pitchers` | Constant that asserts a fact: **F5**. |
| `data_confidence.pitch_data_status` | `fetched_snapshot` when at least one starter has pitch data (`sample.arsenal.pitches > 0`), `unavailable` (the word `sample.rates.source` uses) when none has | Derivation, recomputed from the starters (F1, closed in P0.15-D2.1b). |
| `metadata.data_sources[]` | A list that includes "Cached demo snapshots" in a live file | Constant that asserts a fact: **F3**. |
| `data_confidence.level` | Set only by the constructor of a live matchup, from a snapshot game | Derivation by construction (it is what rule 6 reads to tell a live matchup). |
| `metadata.data_mode`, `data_status.mode` | The generator's reading of the run record | Derivation. |
| `sample.rates.source`, `sample.limited.*`, the rate labels | Which source gave the counts; the minimum samples (D24, D25) | Derivation, recomputed. |

### 6.3 The evidence a zero needs

| Field | A `0` is evidenced by | Otherwise |
|---|---|---|
| `sample.arsenal.pitches` | The pitch mix has no pitch thrown by that starter | `zero_without_evidence` |
| `sample.rates.*` (source `mlb_api`) | The MLB line gave it | Accepted |
| `sample.rates.batters_faced` (source `statcast`) | The starter threw no pitch | `zero_without_evidence` (F6b) |
| `sample.rates.strikeouts`, `walks`, `home_runs` (source `statcast`) | At least one plate appearance was counted | `zero_without_evidence` (F6b) |
| `sample.rates.*` (source `unavailable`) | Not applicable: every count is `null` | `unknown_written_as_value` |
| `charts.pitch_mix[].<slot>.total` | The starter threw no pitch (a total above 0 equals his pitches) | `zero_without_evidence` |
| `charts.pitch_mix[].<slot>.count` | A `total` above 0 (a real zero out of his own total), or no pitch at all | `zero_without_evidence` |
| `charts.pitch_mix[].<slot>.overall`, `vs_lhh`, `vs_rhh` | A `total` above 0: the share is `count / total`; out of nothing it is `null` | `zero_without_evidence` (F20) |
| `charts.velocity_by_pitch[].*` | A velocity is never 0 | `zero_without_evidence` |

`season_summary.strikeouts`, `walks` and `home_runs_allowed` are the counts of `sample.rates` and are checked by equality. `era`, `whip` and `innings` are text by type: a number written as text, or the sentinel `"N/A"`.

### 6.4 The limit of the zero check

The payload does not carry the Statcast `events` column, so a zero count is judged by what must hold around it. A starter hurt on his first pitch has pitches and no batter faced; the payload cannot tell him from a frame whose `events` is unusable (F6b), and the check reports him as a zero without evidence. That is the safe direction: a false alarm stops publication, and the case is extremely rare. A real zero that the MLB API measured is accepted, and so is a Statcast zero that sits next to counted plate appearances. Percent strings of a lineup (`k_rate_vs_hand: "0.0%"`) are not checked for evidence: the payload does not carry the plate appearances behind them.
