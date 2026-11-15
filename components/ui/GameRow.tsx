import Link from "next/link";
import Chip from "@/components/ui/Chip";
import TeamBadge from "@/components/TeamBadge";
import { UNAVAILABLE, formatDay } from "@/lib/format";
import { REASON_LABELS } from "@/lib/notableReasons";
import { clubNickname } from "@/lib/teams";
import type { ArchiveIndexRow } from "@/lib/types";

type Side = ArchiveIndexRow["away"];

function nickname(team: Side): string {
  return clubNickname(team.abbreviation) ?? team.name;
}

/**
 * A finished game in any list: date, round and game number; the two sides with badge, team, starter and runs; then its
 * notable reasons (docs/design/COMPONENTS.md, GameRow). The whole row is one link to the game page. The winner is marked
 * three ways, none of them color alone: a bold name, heavier runs and a triangle before the runs.
 */
export default function GameRow({ game, maxReasons }: { game: ArchiveIndexRow; maxReasons?: number }) {
  const sides = [
    { key: "away" as const, team: game.away, runs: game.result.away_runs, starter: game.starters.away },
    { key: "home" as const, team: game.home, runs: game.result.home_runs, starter: game.starters.home },
  ];
  const reasons = maxReasons === undefined ? game.notable : game.notable.slice(0, maxReasons);
  const hidden = game.notable.length - reasons.length;
  const name = `${nickname(game.away)} at ${nickname(game.home)}, ${formatDay(game.date)}, final ${game.result.away_runs}-${game.result.home_runs}`;

  return (
    <Link
      href={`/game/${game.game_pk}`}
      prefetch={false}
      aria-label={name}
      className="relative block min-h-tap border-t border-line p-space-4 text-ink no-underline first:border-t-0 hover:bg-ground hover:text-ink"
    >
      <span className="mb-space-3 flex flex-wrap items-center gap-space-2 text-label text-ink-2">
        <span className="font-medium tabular-nums text-ink">{formatDay(game.date)}</span>
        <Chip variant="round">{game.round}</Chip>
        {game.series.game_number !== null ? <span>{`Game ${game.series.game_number}`}</span> : null}
      </span>
      <span className="grid gap-space-2">
        {sides.map(({ key, team, runs, starter }) => {
          const won = game.result.winner === key;
          return (
            <span key={key} data-side={key} data-winner={won ? "true" : undefined} className="grid min-h-[34px] grid-cols-[34px_1fr_auto] items-center gap-space-3">
              <TeamBadge abbreviation={team.abbreviation} size={34} />
              <span className="min-w-0">
                <span data-team-name className={`block text-body-lg ${won ? "font-bold" : "font-medium"}`}>
                  {nickname(team)}
                </span>
                <span className="block text-label font-normal text-ink-2">{starter ?? UNAVAILABLE}</span>
              </span>
              <span
                data-runs
                className={`min-w-[30px] text-right font-display text-display-md tabular-nums ${
                  won
                    ? "text-ink before:relative before:-top-[3px] before:mr-2 before:inline-block before:border-y-[6px] before:border-l-[8px] before:border-y-transparent before:border-l-stitch before:align-middle before:content-['']"
                    : "text-ink-2"
                }`}
              >
                {runs}
              </span>
            </span>
          );
        })}
      </span>
      {reasons.length > 0 ? (
        <span className="mt-space-3 flex flex-wrap items-center gap-space-2">
          {reasons.map((reason) => (
            <Chip key={reason} variant="reason" wrap data-reason={reason}>
              {REASON_LABELS[reason]}
            </Chip>
          ))}
          {hidden > 0 ? (
            <Chip variant="neutral" data-more-reasons="">
              {`+${hidden}`}
            </Chip>
          ) : null}
        </span>
      ) : null}
    </Link>
  );
}
