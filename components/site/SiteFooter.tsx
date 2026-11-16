import Link from "next/link";
import { SITE_COPY } from "@/lib/copy/site";

const LINK = "text-on-board underline underline-offset-4 hover:text-signal";

/**
 * The footer of every page, on the board: links, the attribution to MLB Advanced Media, the non-commercial and
 * no-predictions lines, and the author credit as a plain link (owner, 2026-11-15: a credit, never a call to action).
 */
export default function SiteFooter() {
  const copy = SITE_COPY.footer;
  return (
    <footer data-on-board className="bg-board pt-space-5 pb-space-6 text-caption text-on-board">
      <div className="mx-auto max-w-[1184px] px-space-4 bp-lg:px-space-6">
        <nav aria-label={copy.navLabel} className="mb-space-4 flex flex-wrap gap-space-4 text-body-sm">
          <Link href={SITE_COPY.links.howItWorks} className={LINK}>{copy.howItWorks}</Link>
          <a href={SITE_COPY.links.github} className={LINK}>{copy.github}</a>
        </nav>
        <p className="mb-space-2 max-w-[680px] text-on-board-2">{copy.attribution}</p>
        <p className="mb-space-2 max-w-[680px] text-on-board-2">{copy.nonCommercial}</p>
        <p className="mb-space-2 max-w-[680px] text-on-board-2">{copy.noPredictions}</p>
        <p className="mb-0 max-w-[680px] text-on-board-2">
          {copy.madeBy} <a href={SITE_COPY.links.author} className={LINK}>{copy.author}</a>
        </p>
      </div>
    </footer>
  );
}
