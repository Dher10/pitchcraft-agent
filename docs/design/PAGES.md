# Pages and states

The anatomy of each page, top to bottom, and the states it must handle. Layout details live in the page designs; this is the order and the reason for it.

## Every page

1. **SiteHeader** on the board: logo; Today, Notable, Archive, Teams, Pitchers. Off season: Today locked, and the off-season notice under the header.
2. **Page head:** the title in the display face, one sentence on what the page is, and the ModeLine. On the home and on Today the head is a board band.
3. **Content**, in the order below.
4. **Footer** on the board: links (How PitchCraft works, Quality, GitHub), attribution, the non-commercial and no-predictions lines, the credit.

## The season has two modes

| | In season | Off season |
|---|---|---|
| `/` | Today's games | The season in review |
| Today in the header | first link, current on `/` | locked, with the notice |
| ModeLine | "Live data, fetched {date}" | "{year} season archive, final results through {date}" |

The switch is one fact (is the daily job running and is there a schedule), not a redesign.

## Home, off season

1. Board hero: ModeLine, title, one sentence, two actions (the notable duels; the archive), and the SeriesBoard of the last series.
2. Notable duels: the top three GameRows.
3. TeamDirectory: all 30 clubs by league and division.
4. How PitchCraft works: three cards (before the game, every claim is checked, after the game).

## Today, in season

1. Board head: ModeLine (live), "Today's games", the date and the number of games.
2. One card per game, earliest first: round and venue, first-pitch time, the matchup and series standing, both starters (name, style, three season tiles, one line from the report), how many claims were checked, "Read the report".
3. Yesterday: GameRows with results.
- No games today: the EmptyState, then Yesterday.
- A starter not announced: his side of the card says "Starter not confirmed" and the report covers the other.

## Game page: one page, two states

**Before the game** (reached from Today):
1. ScoreBoard with the first-pitch time and the series standing; origin "Live data, fetched {date}".
2. The starters: two StarterCards in the before state (season tiles, the report's paragraph, the AttackCard, the lineup he faces).
3. What to watch: the questions.
4. How the report was checked: the critic's counts and the claims.

**After the game** (reached from Archive, Notable, a team or a pitcher):
1. ScoreBoard with the final score and the series result; origin naming when the report was published and that the rest was added after.
2. Why this game is notable, when it is.
3. How the starters did: two StarterCards in the after state (summary, FinalLine, tiles, PitchChart of the game with at-bat endings, CallCheck, the line before and after).
4. What we asked before the game: the questions, answered.
5. How the report was checked: counts before publishing and after the game, and a link to the report as published.
6. Previous and next game of the series.

The story order after the game is fixed: the result, what each starter did, whether what we said held up, what it did to his line. Season figures from before the game do not lead the page; they live in the report as published.

**After the game, release B** (owner, 2026-11-15; the 1.0.0 game file has no pitch rows, Game Score, verdicts or answers, so blocks 3 to 5 above are reduced and nothing that needs R4-P is rendered):
1. ScoreBoard: state, final score, series line and origin line, all from the game file's envelope, never from the embedded payload.
2. Why this game is notable: the reasons from the game's index row, when it has any.
3. How the starters did: per starter the head, the one-sentence summary only where a catalog phrase supports it from IP, H, ER, BB and K, the FinalLine without pitches, and the starter notes (`did_not_start`, `unknown`).
4. The report as published, inside one block labelled by its origin ("Published before the game, on {date}" or "Written after the game, from data through {as_of}"): the paragraphs, the lineup tiles, the three questions as asked (no answers and no promise of answers), and the critic's counts before publishing.
5. Previous and next game of the series.

Nothing in the embedded payload that says "upcoming", "live" or "before first pitch" renders outside the labelled block of item 4. The link to the report as published is not rendered.

## Notable duels

1. Page head: what the list is, and that the reasons narrow it.
2. Reason filter: "All notable games" and one pill per reason with its count. Pills toggle; picking several shows games with every reason picked. Server rendered from the URL (`/notable?reason=strikeout_duel&reason=series_clincher`).
3. The count ("Showing 15 of 30 notable games: Strikeout duel") with Clear, then GameRows with all their reasons, most reasons first, then newest.
4. How games are chosen: each rule in plain words with its count. On desktop a side column; on a phone after the list.
- Release B shows the R4 4.6 rules (V = 5). The three-group rules of D67 point 5 replace them only when R4-P ships.
- No match for a combination: the EmptyState with "Clear".

## Archive

1. Page head.
2. Filters: team, the Calendar and the reason filter ("Any game" plus the four reasons). A side column on desktop; above the results on a phone.
3. The count ("Showing 5 of 47 games, newest first").
4. Results: GameRows on a phone, ArchiveTable on desktop; 50 per page.
- No match: the EmptyState naming the filters. Index missing: the neutral Notice.

## Team page

1. Head: breadcrumb (All teams / division), badge, club name, "The rotation, explained", the rule in the team color, one sentence.
2. Starters: the pitch-shape key, then one RotationCard per starter, most innings first; four shown, then "Show all {n} starters".
- Starters only. A starter with a small sample is marked and his tiles are warn tiles.

## Pitcher page

1. Head: breadcrumb (Pitchers / club), badge, name, club and hand, the rule in the team color, one sentence.
2. What to expect from him: the profile as three plain statements, and PitchMix.
3. How {year} is going: six season tiles with the scope and batters faced; then the profile against the season in a CallCheck ("Expected:").
4. Where his pitches go: a view switch. The season (default) shows the PitchHeatmap by pitch, with the hand switch; each start with a report shows the PitchChart of that game.
5. Before and after the All-Star Game: the split, with Help.
6. His starts with a report: date and opponent, the final line, Game Score; each row links to the game page.

Reached from the Pitchers index (search by name, filter by team and hand), from a RotationCard ("See his page"), and from a starter's name on a game page.

## States every page handles

Unknown id: a 404 with the EmptyState and links. A figure unavailable: the dash and "Not available". A whole optional block unavailable: omitted without comment. Small sample: marked where the figures are. Demo data: the demo ModeLine, never mixed with live data. Nothing is ever shown as zero because it is unknown.
