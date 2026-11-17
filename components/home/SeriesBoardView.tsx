import type { CSSProperties } from "react";
import Link from "next/link";
import TeamBadge from "@/components/TeamBadge";
import { HOME_COPY } from "@/lib/copy/home";
import type { SeriesBoardModel } from "@/lib/home";

/**
 * A postseason series as a line score with games in place of innings, on the board: one row per club, one cell per game with
 * the runs it scored (a link to that game's page), and the wins at the end. The series winner's total is a filled cell and
 * the other an outlined one, so the winner is told by shape as well as by color.
 *
 * On a phone each club takes two lines, the club and its wins, then its games on a row of their own with 1 px gaps, so
 * seven games are at least 44 px wide at 375 px; from 720 px a club is one line, as on the board of the design.
 */
export default function SeriesBoardView({ board }: { board: SeriesBoardModel }) {
  // From 720 px: one column for the club, one for each game played, one for the wins. On a phone: one column per game.
  const columns = {
    "--board-columns": `minmax(88px,1.4fr) repeat(${board.games.length}, minmax(0,1fr)) minmax(0,1.1fr)`,
    "--board-phone-columns": `repeat(${Math.max(board.games.length, 2)}, minmax(0,1fr))`,
  } as CSSProperties;
  const line = "grid grid-cols-(--board-phone-columns) items-center gap-x-px gap-y-1.5 bp-md:grid-cols-(--board-columns) bp-md:gap-1.5";
  // On a phone the club and the wins share the first line (the word "Wins" before the count, since the head row then names
  // only the games); the games fill the second line, under their heads.
  const club = "col-[1/-2] row-start-1 bp-md:col-auto bp-md:row-auto";
  const wins = "col-[-2/-1] row-start-1 bp-md:col-auto bp-md:row-auto";
  return (
    <div>
      <div
        role="group"
        aria-label={HOME_COPY.boardLabel(board.round)}
        data-on-board
        className="grid gap-space-2 rounded-lg bg-board-2 p-space-3 text-on-board"
      >
        <div className={`${line} text-label text-on-board-2`} style={columns}>
          <span className="hidden bp-md:block" />
          {board.games.map((game) => (
            <span key={game.game_pk} className="text-center">{HOME_COPY.gameColumn(game.number)}</span>
          ))}
          <span className="hidden text-center bp-md:block">{HOME_COPY.wins}</span>
        </div>
        {board.rows.map((row) => (
          <div key={row.nickname} className={line} style={columns}>
            <span className={`${club} flex items-center gap-space-2 text-body-sm font-semibold`}>
              <TeamBadge abbreviation={row.abbreviation} size={24} onBoard />
              <span>{row.nickname}</span>
              <span className="ml-auto pr-space-2 text-label font-normal text-on-board-2 bp-md:hidden">{HOME_COPY.wins}</span>
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
              className={`${wins} flex min-h-tap items-center justify-center rounded-md font-display text-title-md font-extrabold tabular-nums bp-md:text-title-lg ${
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
