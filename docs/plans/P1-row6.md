# P1 row 6: P1.5-a schema 0.9.0 and the readers

Plan of record: `docs/plans/P1.md` section 5 (row 6) and D43 (approved 2026-10-21). The go-ahead to continue with release 1 is the owner's message of 2026-10-22. This file only adds what the code needs that the plan leaves open. Like D37 (schema 0.5.0), the row ships the version, the readers and the field with **no producer of a value**.

Written for: the owner and the reviewer.

## What changes

1. `schema.SCHEMA_VERSION` is `0.9.0` (comment line as the earlier versions), `demo_inputs` and the served demo file carry it; a snapshot of 0.8.0 is not read (D36).
2. `matchups[i].series` exists in every matchup of every file and is `null`: the demo's matchups carry it; a live matchup takes it from its snapshot game (`live_games[i].series`, `null` until row 7). It is a required key of a matchup (`schema.MATCHUP_REQUIRED_KEYS`) and a nullable entry of the manifest. Its parts have no entry yet, so an object in a live file is `rule1:unlisted` until row 7 adds the entries with the producer.
3. `lib/types.ts`: `Series` (`series_name`, `game_number`, `games_in_series`, `standing`), `Matchup.series: Series | null`, `featured_matchup_id: string | null`, `ArchiveItem.result_label: string | null` (`grade_label` already was).
4. The page is null-safe, and shows no new wording: with no matchup the carousel and the matchup view are not drawn (the sentence for that state is row 9's); `featured_matchup_id` null marks no card featured; an archive row with no result shows the page's dash in both the result and the grade column (a grade is never "Pending" for a report that was never going to be graded); a `series` object is accepted and draws nothing (the series line is row 7's).

## Not here

The producer of `series` (row 7), the sentence and the series line (row 7), `matchups: []` and `featured_matchup_id: null` in a validated file, archive rows in a live file and the changes to contract rule 6 and the F4 row (row 9 changes the behaviour; the contract text changes with it, as D43 says). `validate_payload` and the contract checks keep today's rules for those; only the types and the page are ready.

## Requests

None.
