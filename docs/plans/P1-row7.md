# P1 row 7: P1.5-b the series producer, the sentence and the page line

Plan of record: `docs/plans/P1.md` section 5 (row 7) and section 10 (the approved texts), D43. This file adds what the code needs that the plan leaves open.

Written for: the owner and the reviewer.

## Decisions inside the plan, for the owner to correct

1. **Where the series name, number and length come from.** The day's schedule (`seriesDescription`, `seriesGameNumber`, `gamesInSeries`, `gameType`), no extra request; only the standing needs the two requests of `fetch_series_status`, and none for game 1. They are kept raw and judged by `series.build`, not added to the strict schedule schema, so a malformed series field cannot fail the day.
2. **A name the code does not know gives `series: null`** (the page says nothing about a series); an unknown or impossible standing gives `standing: null` inside the object ("Series standing not available"). The seven names and the standing patterns are fixed from one real answer (2026-10-22, 41 games, `tests/fixtures/mlb_series_2026-10.json`).
3. **A "wins" standing is never the standing before a game** (the series is over; no game follows).
4. **The sentence** is two catalog keys (one template each) of the same registry rule: `analyst.series.standing` for a game after the first with a standing, `analyst.series.opening` for game 1. The text is the owner's (section 10). It is placed at the end of the Matchup Summary body, written by the analyst through `Catalog`, joined by the writer. The page does not render the summary body; the visible series line comes from the structured object.
5. **The page line** is `{series_name} · Game {n} · {standing}`, `{series_name} · Game 1`, or `{series_name} · Game {n} · Series standing not available` (section 10), under the headline in the pregame view; `null` draws nothing.

6. **Numbers no series can have.** Text is matched as ASCII (a digit of another script is not a schedule's). A game number above seven, or beyond the length the same answer states, gives `series: null` (the numbers cannot both be true), not a series with a number nobody can have; the manifest and the registry refuse the same numbers.

## Requests

One real MLB schedule request (the measurement of the vocabulary, D16); the committed fixture is its reduction. Tests make none.
