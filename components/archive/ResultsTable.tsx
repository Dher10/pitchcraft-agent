import Link from "next/link";
import Chip from "@/components/ui/Chip";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { UNAVAILABLE, formatDay } from "@/lib/format";
import { REASON_LABELS } from "@/lib/notableReasons";
import { clubNickname } from "@/lib/teams";
import type { ArchiveIndexRow } from "@/lib/types";

const name = (team: ArchiveIndexRow["away"]) => clubNickname(team.abbreviation) ?? team.name;

/**
 * The archive on a wide screen: date and round, game and starters, score, notable. The game cell holds the link; the table
 * never scrolls sideways (under 1024 px the same rows are game rows). The notable column is the first reason and "+n".
 */
export default function ResultsTable({ games }: { games: ArchiveIndexRow[] }) {
  return (
    <table className="w-full border-collapse bg-surface text-body-sm">
      <caption className="sr-only">{ARCHIVE_COPY.tableCaption}</caption>
      <thead>
        <tr>
          {[ARCHIVE_COPY.columns.date, ARCHIVE_COPY.columns.game, ARCHIVE_COPY.columns.score, ARCHIVE_COPY.columns.notable].map((heading) => (
            <th key={heading} scope="col" className="bg-surface-sunken px-space-3 py-2.5 text-left text-label font-medium whitespace-nowrap text-ink-2">
              {heading}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {games.map((game) => {
          const [first, ...rest] = game.notable;
          return (
            <tr key={game.game_pk} className="hover:bg-ground">
              <td className="border-t border-line px-space-3 py-space-3 align-middle">
                <span className="block tabular-nums whitespace-nowrap text-ink">{formatDay(game.date)}</span>
                <span className="mt-1 flex flex-wrap items-center gap-space-2">
                  <Chip variant="round">{game.round}</Chip>
                  {game.series.game_number !== null ? <span className="text-ink-2">{ARCHIVE_COPY.gameNumber(game.series.game_number)}</span> : null}
                </span>
              </td>
              <td className="border-t border-line px-space-3 py-space-3 align-middle">
                <Link href={`/game/${game.game_pk}`} prefetch={false} className="inline-flex min-h-tap items-center font-bold text-ink no-underline hover:text-brand hover:underline">
                  {ARCHIVE_COPY.matchup(name(game.away), name(game.home))}
                </Link>
                <div className="text-label text-ink-2">{ARCHIVE_COPY.starters(game.starters.away ?? UNAVAILABLE, game.starters.home ?? UNAVAILABLE)}</div>
              </td>
              <td data-score className="border-t border-line px-space-3 py-space-3 text-right align-middle font-display text-title-lg whitespace-nowrap tabular-nums text-ink-3">
                <span data-winner={game.result.winner === "away" ? "true" : undefined} className={game.result.winner === "away" ? "font-extrabold text-ink" : ""}>
                  {game.result.away_runs}
                </span>
                –
                <span data-winner={game.result.winner === "home" ? "true" : undefined} className={game.result.winner === "home" ? "font-extrabold text-ink" : ""}>
                  {game.result.home_runs}
                </span>
              </td>
              <td className="border-t border-line px-space-3 py-space-3 align-middle">
                {first ? (
                  <span className="inline-flex flex-wrap items-center gap-space-2">
                    <Chip variant="reason" wrap data-reason={first}>{REASON_LABELS[first]}</Chip>
                    {rest.length > 0 ? <Chip variant="neutral">{`+${rest.length}`}</Chip> : null}
                  </span>
                ) : (
                  <span className="text-ink-3">{UNAVAILABLE}</span>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
