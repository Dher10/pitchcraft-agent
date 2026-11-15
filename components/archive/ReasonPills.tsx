import Link from "next/link";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { REASON_LABELS } from "@/lib/notableReasons";
import { REASON_ORDER, hrefFor, reasonCount, type ArchiveQuery } from "@/lib/archiveQuery";
import type { ArchiveIndex } from "@/lib/types";

const PILL = "inline-flex min-h-tap items-center rounded-sm border px-space-4 text-body-sm font-medium whitespace-nowrap no-underline";

/**
 * The reason filter: "Any game" and one pill per reason with its count. A pill toggles its reason through the URL, and
 * a game must have every reason picked, so picking more narrows the list. The current pills carry aria-current.
 */
export default function ReasonPills({ index, query }: { index: ArchiveIndex; query: ArchiveQuery }) {
  const pill = (current: boolean) =>
    `${PILL} ${current ? "border-ink bg-ink font-semibold text-surface hover:text-surface" : "border-line-strong bg-surface text-ink hover:text-ink"}`;
  return (
    <nav aria-label={ARCHIVE_COPY.reasonLabel} className="flex flex-wrap gap-space-2">
      <Link
        href={hrefFor(query, { reasons: [] })}
        prefetch={false}
        aria-current={query.reasons.length === 0 ? "true" : undefined}
        className={pill(query.reasons.length === 0)}
      >
        {ARCHIVE_COPY.anyGame}
        <span className="ml-1.5 tabular-nums opacity-75">{reasonCount(index, query, null)}</span>
      </Link>
      {REASON_ORDER.map((reason) => {
        const picked = query.reasons.includes(reason);
        const reasons = picked ? query.reasons.filter((r) => r !== reason) : [...query.reasons, reason];
        return (
          <Link key={reason} href={hrefFor(query, { reasons })} prefetch={false} aria-current={picked ? "true" : undefined} className={pill(picked)}>
            {REASON_LABELS[reason]}
            <span className="ml-1.5 tabular-nums opacity-75">{reasonCount(index, query, reason)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
