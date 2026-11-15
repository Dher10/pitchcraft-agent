import Link from "next/link";
import ReportAsPublished from "@/components/game/ReportAsPublished";
import ScoreBoard from "@/components/game/ScoreBoard";
import SeriesNav from "@/components/game/SeriesNav";
import StarterResult from "@/components/game/StarterResult";
import Chip from "@/components/ui/Chip";
import { GAME_COPY } from "@/lib/copy/game";
import { REASON_LABELS } from "@/lib/notableReasons";
import type { ArchiveGameFile, ArchiveIndexRow } from "@/lib/types";

interface GameViewProps {
  game: ArchiveGameFile;
  /** The game's row of the index: its reasons and its clubs' abbreviations. Absent when the index has none for it. */
  row: ArchiveIndexRow | null;
  previous: ArchiveIndexRow | null;
  next: ArchiveIndexRow | null;
}

/**
 * The game page after the game, on the 1.0.0 file, in the owner's order (2026-11-15): the score board, why the game is
 * notable, how the starters did, the report as published in one block, the neighbors in the series. Blocks the 1.0.0 file
 * cannot support (pitches, Game Score, verdicts, answers) are not rendered and leave no gap.
 */
export default function GameView({ game, row, previous, next }: GameViewProps) {
  const reasons = row?.notable ?? [];
  return (
    <main className="mx-auto max-w-[1184px] px-space-4 pb-space-7 bp-lg:px-space-6">
      <nav aria-label="Breadcrumb" className="flex min-h-tap items-center text-body-sm">
        <Link href="/archive" prefetch={false} className="inline-flex min-h-tap items-center text-brand underline underline-offset-4">
          {GAME_COPY.back}
        </Link>
      </nav>
      <div className="grid gap-space-6 bp-lg:gap-space-7">
        <ScoreBoard game={game} row={row} />
        {reasons.length > 0 ? (
          <section aria-label={GAME_COPY.notableLabel}>
            <div className="mb-space-2 text-label text-ink-2">{GAME_COPY.notableLabel}</div>
            <div className="flex flex-wrap gap-space-2">
              {reasons.map((reason) => (
                <Chip key={reason} variant="reason" wrap data-reason={reason}>
                  {REASON_LABELS[reason]}
                </Chip>
              ))}
            </div>
          </section>
        ) : null}
        <section>
          <h2 className="m-0 mb-space-4 font-display text-title-lg text-ink">{GAME_COPY.startersTitle}</h2>
          <div className="grid gap-space-4 bp-md:grid-cols-2 bp-lg:gap-space-5">
            <StarterResult game={game} row={row} side="away" />
            <StarterResult game={game} row={row} side="home" />
          </div>
        </section>
        <ReportAsPublished game={game} row={row} />
        {row ? <SeriesNav previous={previous} next={next} first={game.series.game_number === 1} last={game.series.over} /> : null}
      </div>
    </main>
  );
}
