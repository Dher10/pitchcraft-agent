"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LockIcon } from "@/components/ui/Icons";
import { SITE_COPY } from "@/lib/copy/site";
import type { SeasonMode } from "@/lib/season";

type Item = "today" | "notable" | "archive";

/** The item of the menu a path belongs to: a game page belongs to the Archive (after the game), `/quality` to none. */
function currentItem(pathname: string | null): Item | null {
  if (pathname === "/") return "today";
  if (pathname === "/notable" || pathname?.startsWith("/notable/")) return "notable";
  if (pathname === "/archive" || pathname?.startsWith("/archive/") || pathname?.startsWith("/game/")) return "archive";
  return null;
}

const ITEM =
  "flex min-h-tap flex-1 items-center justify-center gap-1 border-b-[3px] border-transparent px-1 text-label whitespace-nowrap text-on-board no-underline hover:text-signal bp-lg:min-h-[68px] bp-lg:flex-none bp-lg:px-0 bp-lg:text-body-sm";
const CURRENT = "border-signal font-semibold text-signal";

export default function SiteNav({ season }: { season: SeasonMode }) {
  const current = currentItem(usePathname());
  const link = (item: Item, href: string, text: string) => (
    <Link
      key={item}
      href={href}
      prefetch={false}
      aria-current={current === item ? "page" : undefined}
      className={`${ITEM} ${current === item ? CURRENT : ""}`}
    >
      {text}
    </Link>
  );
  return (
    <nav
      aria-label={SITE_COPY.nav.label}
      className="-mx-space-4 flex bg-board-2 px-space-2 bp-lg:mx-0 bp-lg:gap-space-5 bp-lg:bg-transparent bp-lg:px-0"
    >
      {season === "in_season" ? (
        link("today", SITE_COPY.links.home, SITE_COPY.nav.today)
      ) : (
        <span aria-disabled="true" title={SITE_COPY.nav.todayLocked} className={`${ITEM} cursor-not-allowed text-on-board-2 hover:text-on-board-2`}>
          <LockIcon className="size-3" />
          {SITE_COPY.nav.today}
        </span>
      )}
      {link("notable", SITE_COPY.links.notable, SITE_COPY.nav.notable)}
      {link("archive", SITE_COPY.links.archive, SITE_COPY.nav.archive)}
    </nav>
  );
}
