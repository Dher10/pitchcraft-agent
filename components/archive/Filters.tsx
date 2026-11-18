import Link from "next/link";
import Button from "@/components/ui/Button";
import { ChevronDownIcon } from "@/components/ui/Icons";
import Calendar from "@/components/archive/Calendar";
import ReasonPills from "@/components/archive/ReasonPills";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { calendarMonth, daysSummary, type ArchiveQuery } from "@/lib/archiveQuery";
import type { ArchiveIndex } from "@/lib/types";

/** The clubs of the index, by name, once each. Their names are the index's own. */
function clubs(index: ArchiveIndex): { abbreviation: string; name: string }[] {
  const seen = new Map<string, string>();
  for (const row of index.games) {
    for (const team of [row.away, row.home]) if (team.abbreviation !== null) seen.set(team.abbreviation, team.name);
  }
  return [...seen].map(([abbreviation, name]) => ({ abbreviation, name })).sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * The archive's filters as one plain GET form: the team select (submitted with the button), the calendar and the reason
 * pills (links), and the other filters carried in hidden fields. Only validated values are written into the form.
 */
export default function Filters({ index, query }: { index: ArchiveIndex; query: ArchiveQuery }) {
  const words = daysSummary(index, query);
  const active = query.team !== null || query.from !== null || query.reasons.length > 0;
  return (
    <form method="get" action="/archive" aria-label={ARCHIVE_COPY.filtersLabel} className="grid gap-space-4 rounded-lg border border-line bg-surface p-space-4">
      <div className="grid gap-space-1">
        <label htmlFor="archive-team" className="text-label text-ink-2">{ARCHIVE_COPY.team}</label>
        <div className="relative">
          <select
            id="archive-team"
            name="team"
            defaultValue={query.team ?? ""}
            className="min-h-tap w-full appearance-none rounded-sm border border-line-strong bg-surface px-space-3 pr-10 text-body text-ink"
          >
            <option value="">{ARCHIVE_COPY.allTeams}</option>
            {clubs(index).map((club) => (
              <option key={club.abbreviation} value={club.abbreviation}>{club.name}</option>
            ))}
          </select>
          <ChevronDownIcon className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-ink-2" />
        </div>
        {query.from !== null ? <input type="hidden" name="from" value={query.from} /> : null}
        {query.to !== null ? <input type="hidden" name="to" value={query.to} /> : null}
        {query.reasons.map((reason) => (
          <input key={reason} type="hidden" name="reason" value={reason} />
        ))}
        {query.month !== null ? <input type="hidden" name="month" value={query.month} /> : null}
        <div className="mt-space-1">
          <Button type="submit" variant="secondary">{ARCHIVE_COPY.apply}</Button>
        </div>
      </div>
      <div className="grid gap-space-1">
        <span className="text-label text-ink-2">{ARCHIVE_COPY.dates}</span>
        <Calendar calendar={calendarMonth(index, query)} />
      </div>
      <div className="grid gap-space-1">
        <span className="text-label text-ink-2">{ARCHIVE_COPY.reasonLabel}</span>
        <ReasonPills index={index} query={query} />
      </div>
      {active ? (
        <div className="flex items-center gap-space-2">
          <span className="flex-1 text-body-sm">{words ? <strong data-days-summary className="font-semibold">{words}</strong> : null}</span>
          <Link
            href="/archive"
            prefetch={false}
            className="inline-flex min-h-tap items-center rounded-sm px-space-2 text-body font-semibold text-brand underline underline-offset-4"
          >
            {ARCHIVE_COPY.clear}
          </Link>
        </div>
      ) : null}
    </form>
  );
}
