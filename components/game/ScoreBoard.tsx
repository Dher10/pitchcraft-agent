import Chip from "@/components/ui/Chip";
import { InfoIcon } from "@/components/ui/Icons";
import TeamBadge from "@/components/TeamBadge";
import { clubAbbreviation, gameVenue, publishedDay, seriesSentence, sideName } from "@/lib/archiveGame";
import { GAME_COPY } from "@/lib/copy/game";
import { formatDay } from "@/lib/format";
import type { ArchiveGameFile, ArchiveIndexRow } from "@/lib/types";

interface Side {
  key: "away" | "home";
  name: string;
  fullName: string;
  abbreviation: string | null;
  runs: number;
  won: boolean;
}

/** A club beside the score: badge and name, the winner in full strength, the loser dimmer. */
function Club({ side }: { side: Side }) {
  return (
    <div
      data-score-side={side.key}
      data-won={side.won ? "true" : undefined}
      className={`flex flex-col items-center gap-space-2 text-center text-body-sm bp-lg:gap-space-4 bp-lg:font-display bp-lg:text-display-md ${
        side.key === "home" ? "bp-lg:flex-row-reverse bp-lg:justify-end" : "bp-lg:flex-row bp-lg:justify-end"
      } ${side.won ? "font-bold text-on-board" : "font-medium text-on-board-2"}`}
    >
      <TeamBadge abbreviation={side.abbreviation} size={48} onBoard />
      <span className="bp-lg:hidden">{side.name}</span>
      <span className="hidden bp-lg:inline">{side.fullName}</span>
    </div>
  );
}

/**
 * The top of the game page, on the board: round, game number, date and venue; the two clubs around the final score; the
 * series line; the origin line. State, score, series and origin come from the envelope of the game file, never from the
 * embedded payload (which was written before the game).
 */
export default function ScoreBoard({ game, row }: { game: ArchiveGameFile; row: ArchiveIndexRow | null }) {
  const sides = (["away", "home"] as const).map((key) => ({
    key,
    name: sideName(game, row, key),
    fullName: game.teams[key].name,
    abbreviation: clubAbbreviation(game, row, key),
    runs: game.result[`${key}_runs`],
    won: game.result.winner === key,
  }));
  const [away, home] = sides;
  const series = seriesSentence(game);
  const published = publishedDay(game);
  const origin =
    game.origin.kind === "published_live" && published
      ? GAME_COPY.originPublished(formatDay(published))
      : GAME_COPY.originReconstructed(formatDay(game.origin.as_of));

  return (
    <header data-on-board className="rounded-lg bg-board p-space-4 text-on-board bp-lg:rounded-xl bp-lg:p-space-6">
      <div className="flex flex-wrap items-center gap-space-2">
        <Chip variant="round-board">{game.round}</Chip>
        <span className="text-body-sm text-on-board-2">
          {GAME_COPY.head(game.series.game_number, formatDay(game.date), gameVenue(game))}
        </span>
      </div>
      <h1 className="sr-only">{GAME_COPY.hidden(away.name, home.name, game.round, game.series.game_number)}</h1>
      <div className="mt-space-5 mb-space-4 grid grid-cols-[1fr_auto_1fr] items-center gap-space-3">
        <Club side={away} />
        <div
          role="img"
          aria-label={GAME_COPY.scoreName(away.name, away.runs, home.name, home.runs)}
          className="flex items-center gap-space-4 font-display text-score tabular-nums whitespace-nowrap text-signal"
        >
          <span className={away.won ? "" : "font-bold text-on-board-2"}>{away.runs}</span>
          <i aria-hidden="true" className="h-1 w-2.5 rounded-sm bg-on-board-2" />
          <span className={home.won ? "" : "font-bold text-on-board-2"}>{home.runs}</span>
        </div>
        <Club side={home} />
      </div>
      <p className="mb-space-4 text-center text-body-sm">
        <strong>{GAME_COPY.final}</strong>
        {series ? ` ${series}` : null}
      </p>
      <div className="flex items-start gap-space-2 border-t border-board-2 pt-space-3 text-body-sm text-on-board-2">
        <InfoIcon className="mt-0.5 size-4 flex-none" />
        <span>{origin}</span>
      </div>
    </header>
  );
}
