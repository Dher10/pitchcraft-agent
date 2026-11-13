# R4-D7 dry run — report (Nov 12, 2026)

Command: `docs/plans/R4-D7.md` as approved (3 dates, a clean worktree of `451ee33`, output in `C:\Dev\pitchcraft-r4d7-out`, outside the repository). `public/data/` and `evals/live/` were not touched. Nothing was published.

## What happened

- The three builds ran and ended clean: 6 games built, 0 skipped, 0 failed, none stopped by a ceiling; the three `stderr` files are empty.
- The report step of the approved command failed (exit 2, `UnicodeDecodeError`): the builder's stdout also carries the pipeline's log lines in the Windows code page (for example "Cristopher S\xe1nchez"), and the report read the summary files as strict UTF-8. That is a bug of the report tool, not a STOP and not a data problem. Fixed red-first (a test with such a file failed with the same error, then passed) and the report step re-run on the same output with **no new request**. The report below is that re-run. The fix is in the commit that adds this document.
- The data is correct: the game files hold "Sánchez" (U+00E1), no replacement character; only the console display of the log is garbled.

## Result: exit code 0, nothing stops the work

Requests per source against the ceilings of D66 (added over the three runs; every run starts cold on its own counter, the three share one disk cache):

| Date | Games built | MLB requests | Savant requests |
|---|---|---|---|
| 2026-09-30 (Wild Card) | 4 | 22 | 64 |
| 2026-10-10 (Division Series) | 1 | 6 | 9 |
| 2026-10-24 (World Series, published report) | 1 | 4 | 0 |
| **Total** | **6** | **32 of 319** | **73 of 190** |

## report.txt

```
REQUESTS (added over the runs; a ceiling is the hard limit of D66)
  mlb: 32 of 319
  savant: 73 of 190
  runs: 3; games built 6, skipped 0, failed 0; stopped by: [None, None, None]

STARTERS (probable = the starter the report was written for; actual = first pitcher listed in the boxscore)
  check: {'started': 12}
  why readable or not: {'readable': 12}
  game 849802 away: probable Drew Rasmussen (656876), actual Drew Rasmussen, started, readable
  game 849802 home: probable Logan Henderson (701656), actual Logan Henderson, started, readable
  game 849831 away: probable Sean Burke (680732), actual Sean Burke, started, readable
  game 849831 home: probable Gavin Williams (668909), actual Gavin Williams, started, readable
  game 849841 away: probable Cristopher Sánchez (650911), actual Cristopher Sánchez, started, readable
  game 849841 home: probable Tyler Mahle (641816), actual Tyler Mahle, started, readable
  game 849842 away: probable Kevin Gausman (592332), actual Kevin Gausman, started, readable
  game 849842 home: probable Nick Pivetta (601713), actual Nick Pivetta, started, readable
  game 849846 away: probable Sean Burke (680732), actual Sean Burke, started, readable
  game 849846 home: probable Hunter Brown (686613), actual Hunter Brown, started, readable
  game 849848 away: probable Sonny Gray (543243), actual Sonny Gray, started, readable
  game 849848 home: probable Max Fried (608331), actual Max Fried, started, readable

NOTABLE (6 games; the rules are fixed, nothing is tuned here)
  series_clincher: 4
  strikeout_duel: 3
  world_series: 1
  veteran_duel by V (both starters at least V prior MLB seasons), and games with any reason:
    V=1: veteran_duel 6, any reason 6 (100%)
    V=2: veteran_duel 5, any reason 6 (100%)
    V=3: veteran_duel 3, any reason 6 (100%)
    V=4: veteran_duel 3, any reason 6 (100%)
    V=5: veteran_duel 3, any reason 6 (100%)
    V=6: veteran_duel 2, any reason 5 (83%)
    V=7: veteran_duel 2, any reason 5 (83%)
    V=8: veteran_duel 2, any reason 5 (83%)
    V=9: veteran_duel 2, any reason 5 (83%)
    V=10: veteran_duel 0, any reason 5 (83%)

PRIOR MLB SEASONS (11 distinct starters in these games)
  1 prior seasons: 1
  2 prior seasons: 1
  3 prior seasons: 1
  4 prior seasons: 1
  5 prior seasons: 1
  6 prior seasons: 1
  9 prior seasons: 3
  13 prior seasons: 2
  unknown: 0

nothing stops the work: no parser mismatch, no missing boxscore, no failed game, no ceiling passed
```

## Readings (mine; the decisions are the owner's)

1. **The boxscore parser matched the real answer.** All 12 starter sides are `readable`, all 12 `started` (probable equals actual in 12 of 12), and every final line has its five fields from the boxscore, no null. This is the first real boxscore the code has read; the six real answers are kept in `raw/` and can be recorded as a fixture. The sample has no opener or bullpen game, so "the probable starter did not start" is still seen only in synthetic tests.
2. **The published report matched.** Game 849802 (World Series game 2, 2026-10-24) became `published_live` with its commit lineage, at 4 MLB and 0 Savant requests.
3. **Request cost per game is about 5 MLB requests** (a boxscore, up to two series-status requests, up to two history requests, minus cache hits) **plus about 1 to 2 a day** (schedule; the season calendar once), and 2 Savant pitcher frames per game plus 7 team-batting months per new team (56 for the 8 teams of the Wild Card day). Scaled to the 45 to 53 games of the plan, MLB lands around 260 to 300 against the ceiling of 319 (the plan's planning figure was 245), so **the MLB margin is thinner than planned**; Savant stays under 190 (at most 84 team-batting plus 2 per game). This is a linear estimate from 6 games, not a measurement of the full run.
4. **The notable rules tag almost everything in this sample**: any reason on 6 of 6 games for V up to 5 and on 5 of 6 for V up to 10. The sample is biased (four games 2 of Wild Card series, a Division Series game 5 and a World Series game), so it cannot say whether the plan's check (more than about 40% of the pool is too many) is met. Nothing was tuned. `series_clincher` is 4 of 6 because three Wild Card games ended their series and one Division Series game 5 did.
5. **Prior MLB seasons of the 11 starters seen:** 1, 2, 3, 4, 5, 6, 9, 9, 9, 13, 13, none unknown. The full distribution comes from the workflow's step summary on `main` (`archive_dryrun --census`), as the owner decided.
