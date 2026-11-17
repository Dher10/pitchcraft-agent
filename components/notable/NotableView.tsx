import Link from "next/link";
import NotablePills from "@/components/notable/NotablePills";
import Rules from "@/components/notable/Rules";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import GameRow from "@/components/ui/GameRow";
import { NOTABLE_COPY } from "@/lib/copy/notable";
import { countSentence, notableGames, notableHref, type NotableQuery } from "@/lib/notableQuery";
import type { ArchiveIndex } from "@/lib/types";

const FIRST = 3;

/**
 * The notable page: the reason filter, the count, the games with all their reasons (most reasons first, then newest; the
 * first three, the rest behind a native "Show all" that needs no JavaScript), and the rules with their counts, in a side
 * column on a wide screen and after the list on a phone.
 */
export default function NotableView({ index, query }: { index: ArchiveIndex; query: NotableQuery }) {
  const games = notableGames(index, query);
  const noneAtAll = index.notable_count === 0;
  const head = games.slice(0, FIRST);
  const rest = games.slice(FIRST);

  return (
    <main className="mx-auto max-w-[1184px] px-space-4 pt-space-5 pb-space-7 bp-lg:px-space-6 bp-lg:pt-space-7">
      <section className="mb-space-6 grid gap-space-3">
        <h1 className="m-0 font-display text-display-md text-ink bp-lg:text-display-lg">{NOTABLE_COPY.title}</h1>
        <p className="m-0 max-w-[640px] text-body-lg text-ink-2">{NOTABLE_COPY.lede}</p>
      </section>
      <div className="grid items-start gap-space-6 bp-lg:grid-cols-[minmax(0,1fr)_400px] bp-lg:gap-space-7">
        <section className="grid gap-space-3">
          <NotablePills index={index} query={query} />
          <p data-count className="m-0 text-body-sm text-ink-2">
            {countSentence(index, query)}
            {query.reasons.length > 0 && games.length > 0 ? (
              <>
                {" "}
                <Link href={notableHref([])} prefetch={false} className="inline-flex min-h-tap min-w-tap items-center justify-center font-semibold text-brand underline underline-offset-4">
                  {NOTABLE_COPY.clear}
                </Link>
              </>
            ) : null}
          </p>
          {games.length === 0 ? (
            noneAtAll ? (
              <EmptyState title={NOTABLE_COPY.noRule} action={<Button href="/archive" variant="secondary">{NOTABLE_COPY.browse(index.count)}</Button>} />
            ) : (
              <EmptyState title={NOTABLE_COPY.noEveryReason} action={<Button href={notableHref([])} variant="secondary">{NOTABLE_COPY.clear}</Button>} />
            )
          ) : (
            <div data-notable-list className="overflow-hidden rounded-lg border border-line bg-surface">
              {head.map((game) => (
                <GameRow key={game.game_pk} game={game} />
              ))}
              {rest.length > 0 ? (
                <details data-show-all className="[&[open]>summary]:hidden">
                  <summary className="flex min-h-tap cursor-pointer list-none items-center justify-center border-t border-line text-body font-semibold text-brand">
                    {NOTABLE_COPY.showAll(games.length)}
                  </summary>
                  {rest.map((game) => (
                    <GameRow key={game.game_pk} game={game} />
                  ))}
                </details>
              ) : null}
            </div>
          )}
        </section>
        <Rules index={index} />
      </div>
    </main>
  );
}
