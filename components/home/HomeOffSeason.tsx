import Link from "next/link";
import SeriesBoardView from "@/components/home/SeriesBoardView";
import ModeLine from "@/components/ModeLine";
import Button from "@/components/ui/Button";
import GameRow from "@/components/ui/GameRow";
import { HOME_COPY } from "@/lib/copy/home";
import { seriesBoard } from "@/lib/home";
import { notableGames } from "@/lib/notableQuery";
import type { ArchiveIndex } from "@/lib/types";

/**
 * The home in the off season: the season in review, on the published archive. A board hero (the archive mode line, the title,
 * two actions and the World Series line score), the top three notable games, and how PitchCraft works. It never shows a live
 * mode line or a past date as today, and it has no block that needs data the 1.0.0 archive does not have.
 */
export default function HomeOffSeason({ index }: { index: ArchiveIndex }) {
  const board = seriesBoard(index);
  const top = notableGames(index, { reasons: [] }).slice(0, 3);
  const last = index.games.map((game) => game.date).sort().at(-1) as string;

  return (
    <main>
      <section data-on-board className="bg-board text-on-board">
        <div className="mx-auto max-w-[1184px] px-space-4 py-space-5 bp-lg:px-space-6 bp-lg:py-space-8">
          <div className={`grid gap-space-5 ${board ? "bp-lg:grid-cols-[minmax(0,1fr)_460px] bp-lg:items-end bp-lg:gap-space-8" : ""}`}>
            <div className="grid content-start gap-space-4">
              <div>
                <ModeLine archive={{ season: index.season, through: last }} onBoard />
              </div>
              <h1 className="m-0 font-display text-display-lg text-on-board bp-lg:text-display-xl">{HOME_COPY.title}</h1>
              <p className="m-0 max-w-[640px] text-body-lg text-on-board-2">{HOME_COPY.lede}</p>
              <div className="flex flex-wrap gap-space-3">
                <Button href="/notable" variant="signal">{HOME_COPY.seeNotable}</Button>
                <Button href="/archive" variant="secondary-board">{HOME_COPY.browse(index.count)}</Button>
              </div>
            </div>
            {board ? <SeriesBoardView board={board} /> : null}
          </div>
        </div>
      </section>
      <div className="mx-auto grid max-w-[1184px] gap-space-6 px-space-4 py-space-6 bp-lg:gap-space-7 bp-lg:px-space-6 bp-lg:py-space-7">
        {top.length > 0 ? (
          <section data-home-notable>
            <div className="mb-space-4 flex items-baseline justify-between gap-space-3">
              <h2 className="m-0 font-display text-title-lg text-ink">{HOME_COPY.notableTitle}</h2>
              <Link href="/notable" prefetch={false} className="inline-flex min-h-tap items-center text-body-sm text-brand underline underline-offset-4">
                {HOME_COPY.allNotable}
              </Link>
            </div>
            {/* One joined list on a phone; from 1024 px three cards across, each game in its own. */}
            <div
              data-home-notable-list
              className="overflow-hidden rounded-lg border border-line bg-surface bp-lg:grid bp-lg:grid-cols-3 bp-lg:gap-space-5 bp-lg:overflow-visible bp-lg:rounded-none bp-lg:border-0 bp-lg:bg-transparent"
            >
              {top.map((game) => (
                <GameRow
                  key={game.game_pk}
                  game={game}
                  maxReasons={3}
                  className="bp-lg:rounded-lg bp-lg:border bp-lg:border-line bp-lg:bg-surface bp-lg:first:border-t"
                />
              ))}
            </div>
          </section>
        ) : null}
        <section id="how-pitchcraft-works">
          <div className="mb-space-4 flex items-baseline justify-between gap-space-3">
            <h2 className="m-0 font-display text-title-lg text-ink">{HOME_COPY.howTitle}</h2>
            <Link href="/quality" prefetch={false} className="inline-flex min-h-tap items-center text-body-sm text-brand underline underline-offset-4">
              {HOME_COPY.quality}
            </Link>
          </div>
          <div className="grid gap-space-4 bp-lg:grid-cols-3 bp-lg:gap-space-5">
            {HOME_COPY.cards.map((card) => (
              <div key={card.title} data-how-card className="rounded-lg border border-line bg-surface p-space-4 bp-lg:p-space-5">
                <h3 className="m-0 text-title-md text-ink">{card.title}</h3>
                <p className="m-0 mt-1.5 text-body-sm text-ink-2">{card.body}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
