import { HOME_COPY } from "@/lib/copy/home";
import { clubNickname } from "@/lib/teams";
import type { SeasonMode } from "@/lib/season";
import type { ArchiveIndex, ArchiveIndexRow } from "@/lib/types";

/**
 * What the home shows (docs/plans/R4-U.md, U6). In the off season, with the index there, it is the season in review; in
 * season, or without the index, it stays the daily view (Today in season is frozen until February 2027, D67).
 */
export type HomeView = "archive_home" | "daily_view";

export function homeView(season: SeasonMode, index: ArchiveIndex | null): HomeView {
  return season === "off_season" && index !== null && index.games.length > 0 ? "archive_home" : "daily_view";
}

export interface SeriesCell {
  game_pk: number;
  number: number;
  runs: number;
  won: boolean;
  /** The accessible name of the cell: the club's own runs first. */
  label: string;
}

export interface SeriesRow {
  abbreviation: string | null;
  nickname: string;
  cells: SeriesCell[];
  wins: number;
  /** This club won the series (the series is over and it has the wins it needed). */
  seriesWinner: boolean;
}

export interface SeriesBoardModel {
  round: string;
  games: { number: number; game_pk: number }[];
  rows: [SeriesRow, SeriesRow];
  sentence: string;
}

type Side = ArchiveIndexRow["away"];
const nick = (team: Side) => clubNickname(team.abbreviation) ?? team.name;

/**
 * The World Series as a line score with games for innings, from the index alone: the runs each club scored in each game that
 * was played, the wins, and who won. `null` when the index has no World Series game or the series is not over (the only
 * sentence the home may write about a series is that a club won it, which needs the length of the series and the wins).
 */
export function seriesBoard(index: ArchiveIndex | null): SeriesBoardModel | null {
  const games = (index?.games ?? [])
    .filter((game) => game.round === "World Series" && game.series.game_number !== null)
    .sort((a, b) => (a.series.game_number as number) - (b.series.game_number as number));
  if (games.length === 0) return null;

  const clubs = [games[0].away, games[0].home] as const;
  const needed = games.map((g) => g.series.games_in_series).find((n): n is number => n !== null);
  const rows = clubs.map((club): SeriesRow => {
    const other = club.id === games[0].away.id ? games[0].home : games[0].away;
    const cells = games.map((game): SeriesCell => {
      const mine = game.away.id === club.id ? game.result.away_runs : game.result.home_runs;
      const theirs = game.away.id === club.id ? game.result.home_runs : game.result.away_runs;
      return {
        game_pk: game.game_pk,
        number: game.series.game_number as number,
        runs: mine,
        won: mine > theirs,
        label: `Game ${game.series.game_number}: ${nick(club)} ${mine}, ${nick(other)} ${theirs}`,
      };
    });
    return { abbreviation: club.abbreviation, nickname: nick(club), cells, wins: cells.filter((c) => c.won).length, seriesWinner: false };
  }) as [SeriesRow, SeriesRow];

  const round = games[0].round;
  // The club ahead is the first row; a tie keeps the away club of game 1 first.
  if (rows[1].wins > rows[0].wins) rows.reverse();
  const [a, b] = rows;
  const leader = a;
  const trailer = b;
  const over = needed !== undefined && leader.wins >= Math.ceil(needed / 2) && leader.wins > trailer.wins;
  if (!over) return null;
  leader.seriesWinner = true;
  const sentence = HOME_COPY.boardWon(round, leader.nickname, leader.wins, trailer.wins);
  return { round, games: games.map((g) => ({ number: g.series.game_number as number, game_pk: g.game_pk })), rows, sentence };
}
