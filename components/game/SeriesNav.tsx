import Link from "next/link";
import { GAME_COPY } from "@/lib/copy/game";
import type { ArchiveIndexRow } from "@/lib/types";

function Step({ row, label, edge, align }: { row: ArchiveIndexRow | null; label: string; edge: string | null; align: "left" | "right" }) {
  if (row === null) {
    // The end of the series is said only when the file says it is the end; a neighbor missing from the index says nothing.
    return (
      <div className={`px-space-4 py-space-3 text-body-sm text-ink-3 ${align === "right" ? "text-right" : ""}`}>{edge}</div>
    );
  }
  return (
    <Link
      href={`/game/${row.game_pk}`}
      prefetch={false}
      className={`block min-h-tap rounded-md border border-line bg-surface px-space-4 py-space-3 no-underline ${align === "right" ? "text-right" : ""}`}
    >
      <span className="block text-label text-ink-2">{label}</span>
      <b className="text-body font-semibold text-ink">{GAME_COPY.nav.game(row.series.game_number ?? 0, row.date)}</b>
    </Link>
  );
}

/** The game before and the game after, in the same series; at the ends it says it is the first or the last. */
export default function SeriesNav({
  previous,
  next,
  first,
  last,
}: {
  previous: ArchiveIndexRow | null;
  next: ArchiveIndexRow | null;
  /** The file says this is game 1 of its series. */
  first: boolean;
  /** The file says the series is over after this game. */
  last: boolean;
}) {
  return (
    <nav aria-label={GAME_COPY.nav.label} className="grid grid-cols-2 gap-space-3">
      <Step row={previous} label={GAME_COPY.nav.previous} edge={first ? GAME_COPY.nav.first : null} align="left" />
      <Step row={next} label={GAME_COPY.nav.next} edge={last ? GAME_COPY.nav.last : null} align="right" />
    </nav>
  );
}
