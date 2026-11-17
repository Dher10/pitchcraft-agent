import Link from "next/link";
import { ChevronLeftIcon, ChevronRightIcon } from "@/components/ui/Icons";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import type { CalendarMonth } from "@/lib/archiveQuery";

const ARROW = "inline-flex size-11 items-center justify-center rounded-sm border text-ink no-underline";

/**
 * A month of the archive: each day with games is a link (the day, and under it the number of games), so it works without
 * JavaScript and the URL is shareable. The first tap picks a day and the second the end of a range; the URL remembers the
 * first. A range is marked by words in the key and by fills; a day without games is plain text.
 */
export default function Calendar({ calendar }: { calendar: CalendarMonth }) {
  return (
    <div>
      <div className="mb-space-2 flex items-center justify-between">
        {calendar.previous ? (
          <Link href={calendar.previous} prefetch={false} aria-label={ARCHIVE_COPY.previousMonth} className={`${ARROW} border-line-strong bg-surface`}>
            <ChevronLeftIcon className="size-4" />
          </Link>
        ) : (
          <span aria-disabled="true" aria-label={ARCHIVE_COPY.previousMonthNone} className={`${ARROW} border-line text-ink-3`}>
            <ChevronLeftIcon className="size-4" />
          </span>
        )}
        <b data-calendar-title className="font-display text-title-lg font-bold">{calendar.title}</b>
        {calendar.next ? (
          <Link href={calendar.next} prefetch={false} aria-label={ARCHIVE_COPY.nextMonth} className={`${ARROW} border-line-strong bg-surface`}>
            <ChevronRightIcon className="size-4" />
          </Link>
        ) : (
          <span aria-disabled="true" aria-label={ARCHIVE_COPY.nextMonthNone} className={`${ARROW} border-line text-ink-3`}>
            <ChevronRightIcon className="size-4" />
          </span>
        )}
      </div>
      {/* On a phone the grid runs 8 px into the card padding on each side, so seven days are at least 44 px wide at 375 px. */}
      <div className="-mx-space-2 grid grid-cols-7 gap-0.5 bp-md:mx-0">
        {calendar.weekdays.map((weekday) => (
          <div key={weekday} data-weekday className="py-1 text-center text-caption text-ink-3">{weekday}</div>
        ))}
        {calendar.cells.map((cell, index) => {
          if ("outside" in cell) {
            return (
              <div key={`o${index}`} data-day-outside className="flex h-[46px] items-center justify-center text-body-sm font-medium text-ink-3">
                {cell.outside}
              </div>
            );
          }
          if (cell.href === null) {
            return (
              <div key={cell.iso} data-day-plain className="flex h-[46px] items-center justify-center text-body-sm font-medium tabular-nums text-ink-3">
                {cell.day}
              </div>
            );
          }
          const fill =
            cell.state === "end" ? "bg-board text-on-board hover:text-on-board" : cell.state === "range" ? "bg-brand-tint text-ink" : "bg-surface-sunken text-ink hover:bg-brand-tint";
          return (
            <Link
              key={cell.iso}
              href={cell.href}
              prefetch={false}
              data-day=""
              data-state={cell.state}
              aria-label={cell.label ?? undefined}
              aria-current={cell.selection ? "date" : undefined}
              className={`flex h-[46px] flex-col items-center justify-center gap-0.5 rounded-sm text-body-sm font-semibold tabular-nums no-underline ${fill}`}
            >
              {cell.day}
              <small className={`text-caption font-medium ${cell.state === "end" ? "text-signal" : "text-ink-2"}`}>{cell.games}</small>
            </Link>
          );
        })}
      </div>
      <div data-calendar-key className="mt-space-2 flex flex-wrap gap-x-space-4 gap-y-space-1 text-caption text-ink-2">
        <span className="inline-flex items-center gap-1.5">
          <i aria-hidden="true" className="inline-block size-3 rounded-[3px] bg-surface-sunken" />
          {ARCHIVE_COPY.keyDay}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <i aria-hidden="true" className="inline-block size-3 rounded-[3px] bg-board" />
          {ARCHIVE_COPY.keyRange}
        </span>
      </div>
    </div>
  );
}
