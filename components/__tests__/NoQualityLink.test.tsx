import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import ArchiveUnavailable from "@/components/archive/ArchiveUnavailable";
import ArchiveView from "@/components/archive/ArchiveView";
import GameNotFound from "@/components/game/GameNotFound";
import GameView from "@/components/game/GameView";
import HomeOffSeason from "@/components/home/HomeOffSeason";
import NotableUnavailable from "@/components/notable/NotableUnavailable";
import NotableView from "@/components/notable/NotableView";
import PitchCraftApp from "@/components/PitchCraftApp";
import SiteFooter from "@/components/site/SiteFooter";
import SiteHeader from "@/components/site/SiteHeader";
import { parseArchiveGame, matchingRow, seriesNeighbors } from "@/lib/archiveGame";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { parseArchiveQuery } from "@/lib/archiveQuery";
import { parseNotableQuery } from "@/lib/notableQuery";
import type { PitchCraftData } from "@/lib/types";
import demo from "@/tests/fixtures/served_demo_0.9.0.json";

// Release B (owner, 2026-11-15): /quality has no content until P3.2, so no page links to it. The route stays (D26 uses it for
// analytics, its CSP handling and its tests stay); the link comes back with P3.2.

const ROOT = process.cwd();
const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(ROOT, "public/data/archive/index-2026.json"), "utf8")));
const GAME = parseArchiveGame(JSON.parse(readFileSync(path.join(ROOT, "public/data/archive/games/849799.json"), "utf8")), 849799);

function links(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll("a[href]"), (a) => a.getAttribute("href") ?? "");
}

const PAGES: [string, () => ReturnType<typeof render>][] = [
  ["the header, off season", () => render(<SiteHeader season="off_season" />)],
  ["the header, in season", () => render(<SiteHeader season="in_season" />)],
  ["the footer", () => render(<SiteFooter />)],
  ["the home in the off season", () => render(<HomeOffSeason index={INDEX} />)],
  ["the archive", () => render(<ArchiveView index={INDEX} query={parseArchiveQuery({}, INDEX)} />)],
  ["the archive with no match", () => render(<ArchiveView index={INDEX} query={parseArchiveQuery({ team: "NYY", from: "2026-10-23", to: "2026-10-28" }, INDEX)} />)],
  ["the archive, unavailable", () => render(<ArchiveUnavailable />)],
  ["the notable page", () => render(<NotableView index={INDEX} query={parseNotableQuery({})} />)],
  ["the notable page, unavailable", () => render(<NotableUnavailable />)],
  [
    "a game page",
    () => {
      const { previous, next } = seriesNeighbors(INDEX, GAME.game_pk);
      return render(<GameView game={GAME} row={matchingRow(GAME, INDEX)} previous={previous} next={next} />);
    },
  ],
  ["the game not found page", () => render(<GameNotFound />)],
  ["the daily view", () => render(<PitchCraftApp data={structuredClone(demo) as unknown as PitchCraftData} indexedArchive={null} />)],
];

describe("no rendered page links to /quality", () => {
  it.each(PAGES)("%s", (_name, draw) => {
    const { container } = draw();

    expect(links(container).filter((href) => href.startsWith("/quality"))).toEqual([]);
  });

  it("control: the check can fail (a planted link is found)", () => {
    const { container } = render(<a href="/quality">Quality</a>);

    expect(links(container).filter((href) => href.startsWith("/quality"))).toEqual(["/quality"]);
  });
});

describe("no source writes a link to /quality", () => {
  function sources(dir: string): string[] {
    const found: string[] = [];
    for (const entry of readdirSync(path.join(ROOT, dir))) {
      if (["__tests__", "node_modules", ".next"].includes(entry)) continue;
      const rel = `${dir}/${entry}`;
      if (statSync(path.join(ROOT, rel)).isDirectory()) found.push(...sources(rel));
      else if (/\.(tsx?|ts)$/.test(entry)) found.push(rel);
    }
    return found;
  }

  it("keeps the route out of every catalog and component", () => {
    const hits = [...sources("components"), ...sources("lib"), ...sources("app")]
      .filter((file) => file !== "app/quality/page.tsx")
      .filter((file) => /["'`]\/quality["'`/?]/.test(readFileSync(path.join(ROOT, file), "utf8")));

    expect(hits).toEqual([]);
  });
});

describe("the route stays", () => {
  it("is still there for the analytics (D26) and for P3.2", () => {
    expect(existsSync(path.join(ROOT, "app/quality/page.tsx"))).toBe(true);
    expect(readFileSync(path.join(ROOT, "app/quality/page.tsx"), "utf8")).toContain("Quality");
  });
});
