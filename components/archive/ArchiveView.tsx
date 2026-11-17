import ArchiveUnavailable from "@/components/archive/ArchiveUnavailable";
import Filters from "@/components/archive/Filters";
import ResultsTable from "@/components/archive/ResultsTable";
import ModeLine from "@/components/ModeLine";
import Button from "@/components/ui/Button";
import EmptyState from "@/components/ui/EmptyState";
import GameRow from "@/components/ui/GameRow";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { PAGE_SIZE, hrefFor, noMatchText, pageCount, selectGames, type ArchiveQuery } from "@/lib/archiveQuery";
import type { ArchiveIndex } from "@/lib/types";

/**
 * The archive page: the filters (team, calendar, reasons), the count, and the results as game rows on a phone and a table
 * from 1024 px, 50 a page. Everything comes from the validated query and the index; with no match the empty state names
 * what was asked.
 */
export default function ArchiveView({ index, query }: { index: ArchiveIndex; query: ArchiveQuery }) {
  // A valid index with no games has no last day and no month: the archive's notice, before the mode line and the calendar.
  if (index.games.length === 0) return <ArchiveUnavailable />;
  const games = selectGames(index, query);
  const pages = pageCount(games.length);
  const shown = games.slice((query.page - 1) * PAGE_SIZE, query.page * PAGE_SIZE);
  const last = index.games.map((row) => row.date).sort().at(-1) as string;
  const none = noMatchText(index, query);

  return (
    <main className="mx-auto max-w-[1184px] px-space-4 pt-space-5 pb-space-7 bp-lg:px-space-6 bp-lg:pt-space-7">
      <section className="mb-space-6 grid gap-space-3">
        <h1 className="m-0 font-display text-display-md text-ink bp-lg:text-display-lg">{ARCHIVE_COPY.title}</h1>
        <p className="m-0 max-w-[640px] text-body-lg text-ink-2">{ARCHIVE_COPY.lede}</p>
        <div>
          <ModeLine archive={{ season: index.season, through: last }} />
        </div>
      </section>
      <div className="grid items-start gap-space-4 bp-lg:grid-cols-[380px_1fr] bp-lg:gap-space-6">
        <Filters index={index} query={query} />
        <div className="grid gap-space-4">
          <p data-count className="m-0 text-body-sm text-ink-2">{ARCHIVE_COPY.count(games.length, index.games.length)}</p>
          {games.length === 0 ? (
            <EmptyState title={none.title} action={<Button href="/archive" variant="secondary">{ARCHIVE_COPY.clearFilters}</Button>}>
              {none.body}
            </EmptyState>
          ) : (
            <>
              <div data-results="rows" className="overflow-hidden rounded-lg border border-line bg-surface bp-lg:hidden">
                {shown.map((game) => (
                  <GameRow key={game.game_pk} game={game} maxReasons={1} />
                ))}
              </div>
              <div data-results="table" className="hidden overflow-hidden rounded-lg border border-line bp-lg:block">
                <ResultsTable games={shown} />
              </div>
              {pages > 1 ? (
                <nav aria-label={ARCHIVE_COPY.pagerLabel} className="flex items-center justify-between gap-space-3">
                  {query.page > 1 ? (
                    <Button href={hrefFor(query, { page: query.page - 1 })} variant="secondary">{ARCHIVE_COPY.previousPage}</Button>
                  ) : (
                    <span />
                  )}
                  <span className="text-body-sm text-ink-2">{ARCHIVE_COPY.page(query.page, pages)}</span>
                  {query.page < pages ? (
                    <Button href={hrefFor(query, { page: query.page + 1 })} variant="secondary">{ARCHIVE_COPY.nextPage}</Button>
                  ) : (
                    <span />
                  )}
                </nav>
              ) : null}
            </>
          )}
        </div>
      </div>
    </main>
  );
}

