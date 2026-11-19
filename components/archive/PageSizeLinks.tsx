import Link from "next/link";
import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { PAGE_SIZES, hrefFor, type ArchiveQuery } from "@/lib/archiveQuery";

/**
 * "Games per page: 10 · 20 · 50 · All" as plain links (release 2.2.0). The current size is marked with aria-current and
 * styled as selected; every link keeps the filters and goes back to page 1. Links need no JavaScript and no form.
 */
export default function PageSizeLinks({ query }: { query: ArchiveQuery }) {
  return (
    <nav aria-label={ARCHIVE_COPY.perPageLabel} className="flex flex-wrap items-center gap-x-space-1 text-body-sm text-ink-2">
      <span className="mr-space-1">{ARCHIVE_COPY.perPageLabel}</span>
      {PAGE_SIZES.map((size) => {
        const current = size === query.per;
        return (
          <Link
            key={size}
            href={hrefFor(query, { per: size })}
            prefetch={false}
            aria-current={current ? "true" : undefined}
            className={`inline-flex min-h-tap min-w-tap items-center justify-center rounded-sm border px-space-2 text-body font-semibold no-underline ${
              current ? "border-brand bg-brand text-on-brand" : "border-line-strong bg-surface text-ink hover:border-ink-2 hover:bg-surface-sunken"
            }`}
          >
            {size === "all" ? ARCHIVE_COPY.perPageAll : size}
          </Link>
        );
      })}
    </nav>
  );
}
