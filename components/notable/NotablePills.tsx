import Link from "next/link";
import { NOTABLE_COPY } from "@/lib/copy/notable";
import { notableCount, notableHref, type NotableQuery } from "@/lib/notableQuery";
import { NOTABLE_REASONS } from "@/lib/notableReasons";
import type { ArchiveIndex } from "@/lib/types";

const PILL = "inline-flex min-h-tap items-center rounded-sm border px-space-4 text-body-sm font-medium whitespace-nowrap no-underline";

/**
 * The reason filter of the notable page: "All notable games" and one pill per reason with its count. A pill toggles its reason
 * through the URL; picking several shows the games that have every reason picked. The current pills carry aria-current.
 */
export default function NotablePills({ index, query }: { index: ArchiveIndex; query: NotableQuery }) {
  const look = (current: boolean) =>
    `${PILL} ${current ? "border-ink bg-ink font-semibold text-surface hover:text-surface" : "border-line-strong bg-surface text-ink hover:text-ink"}`;
  return (
    <nav aria-label={NOTABLE_COPY.reasonLabel} className="flex flex-wrap gap-space-2">
      <Link
        href={notableHref([])}
        prefetch={false}
        aria-current={query.reasons.length === 0 ? "true" : undefined}
        className={look(query.reasons.length === 0)}
      >
        {NOTABLE_COPY.all}
        <span className="ml-1.5 tabular-nums opacity-75">{notableCount(index, query, null)}</span>
      </Link>
      {NOTABLE_REASONS.map((reason) => {
        const picked = query.reasons.includes(reason.key);
        const next = picked ? query.reasons.filter((r) => r !== reason.key) : [...query.reasons, reason.key];
        return (
          <Link key={reason.key} href={notableHref(next)} prefetch={false} aria-current={picked ? "true" : undefined} className={look(picked)}>
            {reason.label}
            <span className="ml-1.5 tabular-nums opacity-75">{notableCount(index, query, reason.key)}</span>
          </Link>
        );
      })}
    </nav>
  );
}
