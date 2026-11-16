import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, within } from "@testing-library/react";

let mockPath = "/";
vi.mock("next/navigation", () => ({ usePathname: () => mockPath }));

import SiteHeader from "@/components/site/SiteHeader";
import SiteFooter from "@/components/site/SiteFooter";
import { SITE_COPY } from "@/lib/copy/site";

// U2 (docs/plans/R4-U.md, 5.1): the header and the footer of every page.

beforeEach(() => {
  mockPath = "/";
});

function nav(container: HTMLElement) {
  return within(container.querySelector('nav[aria-label="Main"]') as HTMLElement);
}

describe("the site header, off season", () => {
  it("shows Today locked, not a link, with the lock and the reason", () => {
    const { container } = render(<SiteHeader season="off_season" />);
    const today = nav(container).getByText("Today").closest("span");

    expect(today).not.toBeNull();
    expect(today?.getAttribute("aria-disabled")).toBe("true");
    expect(today?.getAttribute("title")).toBe("No games in the off season");
    expect(today?.querySelector("svg")).not.toBeNull();
    expect(nav(container).queryByRole("link", { name: "Today" })).toBeNull();
  });

  it("shows the off-season notice under the header, word for word", () => {
    const { getByTestId } = render(<SiteHeader season="off_season" />);

    expect(getByTestId("season-notice").textContent).toBe(
      "Off season. No games today. Today's games and daily reports return when the 2027 season starts.",
    );
  });

  it("has exactly Notable and Archive as links, and no Teams or Pitchers (R5 is frozen)", () => {
    const { container } = render(<SiteHeader season="off_season" />);
    const links = nav(container).getAllByRole("link");

    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["Notable", "/notable"],
      ["Archive", "/archive"],
    ]);
    expect(container.textContent).not.toMatch(/Teams|Pitchers/);
  });
});

describe("the site header, in season", () => {
  it("has Today as the first link, no lock and no notice", () => {
    const { container, queryByTestId } = render(<SiteHeader season="in_season" />);
    const links = nav(container).getAllByRole("link");

    expect(links.map((link) => link.textContent)).toEqual(["Today", "Notable", "Archive"]);
    expect(links[0].getAttribute("href")).toBe("/");
    expect(container.querySelector("[aria-disabled]")).toBeNull();
    expect(queryByTestId("season-notice")).toBeNull();
  });
});

describe("the current item", () => {
  it.each([
    ["/notable", "Notable"],
    ["/archive", "Archive"],
    ["/game/849799", "Archive"],
  ])("marks %s as %s", (pathname, label) => {
    mockPath = pathname;
    const { container } = render(<SiteHeader season="off_season" />);
    const current = container.querySelectorAll('[aria-current="page"]');

    expect(current).toHaveLength(1);
    expect(current[0].textContent).toBe(label);
  });

  it("marks Today on the home in season, and nothing on the home off season (Today is locked)", () => {
    mockPath = "/";
    const inSeason = render(<SiteHeader season="in_season" />);
    expect(inSeason.container.querySelector('[aria-current="page"]')?.textContent).toBe("Today");
    inSeason.unmount();

    const off = render(<SiteHeader season="off_season" />);
    expect(off.container.querySelector('[aria-current="page"]')).toBeNull();
  });

  it("marks nothing on a page that is not in the menu", () => {
    mockPath = "/quality";
    const { container } = render(<SiteHeader season="off_season" />);

    expect(container.querySelector('[aria-current="page"]')).toBeNull();
  });

  it("does not mark a path that only starts like a menu path", () => {
    mockPath = "/archived";
    const { container } = render(<SiteHeader season="off_season" />);

    expect(container.querySelector('[aria-current="page"]')).toBeNull();
  });
});

describe("the logo", () => {
  it("links to the home with an accessible name and the wordmark as text", () => {
    const { getByRole } = render(<SiteHeader season="off_season" />);
    const logo = getByRole("link", { name: "PitchCraft, home" });

    expect(logo.getAttribute("href")).toBe("/");
    expect(logo.textContent).toBe("PITCHCRAFT");
    expect(logo.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("ships the favicon of the design and no old .ico", () => {
    const root = process.cwd();
    const icon = readFileSync(path.join(root, "app/icon.svg"), "utf8");

    expect(icon).toBe(readFileSync(path.join(root, "docs/design/assets/pitchcraft-favicon.svg"), "utf8"));
    expect(icon).not.toMatch(/<script|onload|href=/i);
    expect(existsSync(path.join(root, "app/favicon.ico"))).toBe(false);
  });
});

describe("the site footer", () => {
  it("carries the attribution, the non-commercial line, the no-predictions line and the colors line, word for word", () => {
    const { container } = render(<SiteFooter />);
    const paragraphs = Array.from(container.querySelectorAll("p")).map((p) => p.textContent);

    expect(paragraphs).toEqual([
      "Data from the MLB Stats API and Baseball Savant (Statcast), made public by MLB Advanced Media. PitchCraft is an independent fan project and is not affiliated with MLB.",
      "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features.",
      "For information only: no predictions and no betting advice. Team colors are approximate.",
      "Made by Daniel Herdenez",
    ]);
  });

  it("has its two links, and none to /quality until that page has content (P3.2, owner 2026-11-15)", () => {
    const { getByRole, queryByRole, container } = render(<SiteFooter />);

    expect(getByRole("link", { name: "How PitchCraft works" }).getAttribute("href")).toBe("/#how-pitchcraft-works");
    expect(queryByRole("link", { name: "Quality" })).toBeNull();
    expect(Array.from(container.querySelectorAll("nav a"), (a) => a.getAttribute("href"))).toEqual([
      "/#how-pitchcraft-works",
      "https://github.com/Dher10/pitchcraft-agent",
    ]);
    expect(getByRole("link", { name: "GitHub" }).getAttribute("href")).toBe("https://github.com/Dher10/pitchcraft-agent");
  });

  it("credits the author with a plain link: no tracking, no new tab, not styled as a button (owner, 2026-11-15)", () => {
    const { getByRole } = render(<SiteFooter />);
    const credit = getByRole("link", { name: "Daniel Herdenez" });

    expect(credit.getAttribute("href")).toBe("https://www.danielherdenez.com");
    expect(credit.hasAttribute("target")).toBe(false);
    expect(credit.className).not.toMatch(/bg-|border|px-|rounded/);
  });

  it("is on the board, so its focus ring is signal", () => {
    const { container } = render(<SiteFooter />);

    expect(container.querySelector("footer")?.hasAttribute("data-on-board")).toBe(true);
  });
});

describe("the copy", () => {
  it("keeps every shell string in the catalog", () => {
    expect(SITE_COPY.nav.today).toBe("Today");
    expect(SITE_COPY.nav.notable).toBe("Notable");
    expect(SITE_COPY.nav.archive).toBe("Archive");
    expect(SITE_COPY.seasonNotice.lead).toBe("Off season.");
  });
});
