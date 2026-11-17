import Link from "next/link";
import Logo from "@/components/site/Logo";
import SiteNav from "@/components/site/SiteNav";
import { InfoIcon } from "@/components/ui/Icons";
import { SITE_COPY } from "@/lib/copy/site";
import type { SeasonMode } from "@/lib/season";

/**
 * The header of every page, on the board: the logo and the destinations that exist (Today, Notable, Archive; Teams and
 * Pitchers wait for R5). Off season, Today is locked and a notice under the header says why.
 */
export default function SiteHeader({ season }: { season: SeasonMode }) {
  return (
    <>
      <header data-on-board className="bg-board text-on-board">
        <div className="mx-auto max-w-[1184px] px-space-4 bp-lg:flex bp-lg:items-center bp-lg:justify-between bp-lg:px-space-6">
          <div className="flex min-h-14 items-center bp-lg:min-h-[68px]">
            <Link
              href={SITE_COPY.links.home}
              aria-label={SITE_COPY.logo.name}
              // The wordmark is 26 px (docs/design/COMPONENTS.md, Logo): a logo size, not a text style of the scale.
              style={{ fontSize: 26, lineHeight: "26px", letterSpacing: "0.02em" }}
              className="inline-flex min-h-tap items-center gap-2.5 font-display font-extrabold text-on-board no-underline hover:text-on-board"
            >
              <Logo />
            </Link>
          </div>
          <SiteNav season={season} />
        </div>
      </header>
      {season === "off_season" ? (
        <div data-testid="season-notice" className="border-b border-line bg-signal-tint text-body-sm text-ink">
          <div className="mx-auto flex max-w-[1184px] items-start gap-space-2 px-space-4 py-2.5 bp-lg:px-space-6">
            <InfoIcon className="mt-0.5 size-4 flex-none text-signal-ink" />
            <p className="m-0">
              <strong className="font-semibold">{SITE_COPY.seasonNotice.lead}</strong> {SITE_COPY.seasonNotice.body}
            </p>
          </div>
        </div>
      ) : null}
    </>
  );
}
