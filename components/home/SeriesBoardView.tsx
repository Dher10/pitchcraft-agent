import Link from "next/link";
import TeamBadge from "@/components/TeamBadge";
import { HOME_COPY } from "@/lib/copy/home";
import type { SeriesBoardModel } from "@/lib/home";

/**
 * A postseason series as a line score with games in place of innings, on the board: one row per club, one cell per game with
 * the runs it scored (a link to that game's page), and the wins at the end. The series winner's total is a filled cell and
 * the other an outlined one, so the winner is told by shape as well as by color.
 */
export default function SeriesBoardView({ board }: { board: SeriesBoardModel }) {
  // One column for the club, one for each game played, one for the wins.
  const columns = `minmax(88px,1.4fr) repeat(${board.games.length}, minmax(0,1fr)) minmax(0,1.1fr)`;
  return (
    <div>
      <div
        role="group"
        aria-label={HOME_COPY.boardLabel(board.round)}
        data-on-board
        className="grid gap-space-2 rounded-lg bg-board-2 p-space-3 text-on-board"
      >
        <div className="grid items-center gap-1.5 text-label text-on-board-2" style={{ gridTemplateColumns: columns }}>
          <span />
          {board.games.map((game) => (
            <span key={game.game_pk} className="text-center">{HOME_COPY.gameColumn(game.number)}</span>
          ))}
          <span className="text-center">{HOME_COPY.wins}</span>
        </div>
        {board.rows.map((row) => (
          <div
            key={row.nickname}
            className="grid items-center gap-1.5"
            style={{ gridTemplateColumns: columns }}
          >
            <span className="flex items-center gap-space-2 text-body-sm font-semibold">
              <TeamBadge abbreviation={row.abbreviation} size={24} onBoard />
              <span>{row.nickname}</span>
            </span>
            {row.cells.map((cell) => (
              <Link
                key={cell.game_pk}
                href={`/game/${cell.game_pk}`}
                prefetch={false}
                aria-label={cell.label}
                className={`flex min-h-tap items-center justify-center rounded-md bg-board font-display text-title-md tabular-nums no-underline bp-md:text-title-lg ${
                  cell.won ? "font-extrabold text-signal hover:text-signal" : "font-bold text-on-board-2 hover:text-on-board"
                }`}
              >
                {cell.runs}
              </Link>
            ))}
            <span
              {...(row.seriesWinner ? { "data-series-winner": "true" } : {})}
              className={`flex min-h-tap items-center justify-center rounded-md font-display text-title-md font-extrabold tabular-nums bp-md:text-title-lg ${
                row.seriesWinner ? "bg-signal text-ink" : "border border-on-board-2 text-on-board"
              }`}
            >
              {row.wins}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-space-3 mb-0 text-body-sm text-on-board-2">{board.sentence}</p>
    </div>
  );
}
