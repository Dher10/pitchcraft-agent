import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";

import NotableUnavailable from "@/components/notable/NotableUnavailable";
import NotableView from "@/components/notable/NotableView";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { parseNotableQuery } from "@/lib/notableQuery";
import type { ArchiveIndex } from "@/lib/types";

// U5 (docs/plans/R4-U.md, 4 and 5.5): the notable page. Reasons are filters, one or more at a time; the rules are on the
// page with their counts; everything comes from the validated index and one table of reasons.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));

function view(params: Record<string, string | string[] | undefined> = {}, index: ArchiveIndex = INDEX) {
  return render(<NotableView index={index} query={parseNotableQuery(params)} />);
}

const text = (node: Element | null) => node?.textContent ?? "";

describe("the page head", () => {
  it("has the title and the sentence that says the reasons narrow the list", () => {
    const { container } = view();

    expect(container.querySelector("h1")?.textContent).toBe("Notable duels of 2026");
    expect(text(container)).toContain(
      "Starting-pitcher matchups of the 2026 postseason, each with the reasons it stands out. Pick one or more reasons to narrow the list.",
    );
  });
});

describe("the reason filter", () => {
  it("has All notable games and the four reasons in the design's order, each with its count", () => {
    const { getByRole } = view();
    const pills = within(getByRole("navigation", { name: "Notable reason" })).getAllByRole("link").map((link) => link.textContent);

    expect(pills).toEqual(["All notable games30", "Strikeout duel15", "Veteran duel12", "Series-ending game11", "World Series game5"]);
  });

  it("marks All notable games as current when nothing is picked, and the picked reasons when some are", () => {
    const none = view();
    const nav = within(none.getByRole("navigation", { name: "Notable reason" }));
    expect(nav.getByRole("link", { name: /All notable games/ }).getAttribute("aria-current")).toBe("true");
    none.unmount();

    const picked = view({ reason: ["strikeout_duel", "world_series"] });
    const pn = within(picked.getByRole("navigation", { name: "Notable reason" }));
    expect(pn.getByRole("link", { name: /Strikeout duel/ }).getAttribute("aria-current")).toBe("true");
    expect(pn.getByRole("link", { name: /World Series game/ }).getAttribute("aria-current")).toBe("true");
    expect(pn.getByRole("link", { name: /Veteran duel/ }).hasAttribute("aria-current")).toBe(false);
    expect(pn.getByRole("link", { name: /All notable games/ }).hasAttribute("aria-current")).toBe(false);
  });

  it("toggles a reason through the URL", () => {
    const { getByRole } = view({ reason: "strikeout_duel" });
    const nav = within(getByRole("navigation", { name: "Notable reason" }));

    expect(nav.getByRole("link", { name: /Strikeout duel/ }).getAttribute("href")).toBe("/notable");
    expect(nav.getByRole("link", { name: /Veteran duel/ }).getAttribute("href")).toBe("/notable?reason=strikeout_duel&reason=veteran_duel");
    expect(nav.getByRole("link", { name: /All notable games/ }).getAttribute("href")).toBe("/notable");
  });

  it("follows the reasons already picked in its counts", () => {
    const { getByRole } = view({ reason: "strikeout_duel" });
    const nav = within(getByRole("navigation", { name: "Notable reason" }));

    expect(nav.getByRole("link", { name: /Strikeout duel/ }).textContent).toBe("Strikeout duel15");
    expect(nav.getByRole("link", { name: /All notable games/ }).textContent).toBe("All notable games30");
  });
});

describe("the count line and Clear", () => {
  it("says how many games are shown, with the reasons, and the order", () => {
    const { container } = view({ reason: "strikeout_duel" });

    expect(text(container.querySelector("[data-count]"))).toContain("Showing 15 of 30 notable games: Strikeout duel. Most reasons first, then newest.");
  });

  it("offers Clear only when a reason is picked", () => {
    const picked = view({ reason: "strikeout_duel" });
    expect(picked.getByRole("link", { name: "Clear" }).getAttribute("href")).toBe("/notable");
    picked.unmount();

    const none = view();
    expect(none.queryByRole("link", { name: "Clear" })).toBeNull();
    expect(text(none.container.querySelector("[data-count]"))).toContain("Showing 30 notable games.");
  });
});

describe("the games", () => {
  it("are the 30 notable ones, each a link to its game page, most reasons first", () => {
    const { container } = view();
    const rows = Array.from(container.querySelectorAll('[data-notable-list] a[href^="/game/"]'));

    expect(rows).toHaveLength(30);
    expect(rows[0].getAttribute("href")).toBe("/game/849799");
    expect(rows[0].querySelectorAll("[data-reason]")).toHaveLength(3);
    for (const row of rows) expect(row.querySelectorAll("[data-reason]").length).toBeGreaterThan(0);
  });

  it("show every reason of a game, not only the first", () => {
    const { container } = view();
    const first = container.querySelector('[data-notable-list] a[href="/game/849799"]') as HTMLElement;

    expect(Array.from(first.querySelectorAll("[data-reason]")).map((chip) => chip.textContent)).toEqual([
      "Series-ending game",
      "Strikeout duel",
      "World Series game",
    ]);
    expect(first.querySelector("[data-more-reasons]")).toBeNull();
  });

  it("show the first three and the rest behind Show all, which works without JavaScript", () => {
    const { container } = view({ reason: "strikeout_duel" });
    const details = container.querySelector("details[data-show-all]") as HTMLDetailsElement;

    expect(details.querySelector("summary")?.textContent).toBe("Show all 15");
    expect(container.querySelectorAll('[data-notable-list] > a[href^="/game/"]')).toHaveLength(3);
    expect(details.querySelectorAll('a[href^="/game/"]')).toHaveLength(12);
    expect(details.open).toBe(false);
  });

  it("have no Show all when there are three or fewer", () => {
    const { container } = view({ reason: ["world_series", "strikeout_duel", "series_clincher"] });
    const shown = container.querySelectorAll('[data-notable-list] a[href^="/game/"]').length;

    expect(shown).toBeGreaterThan(0);
    expect(shown).toBeLessThanOrEqual(3);
    expect(container.querySelector("details[data-show-all]")).toBeNull();
  });

  it("follow the reasons picked: every game has every reason", () => {
    const { container } = view({ reason: ["strikeout_duel", "world_series"] });
    const rows = Array.from(container.querySelectorAll('[data-notable-list] a[href^="/game/"]'));

    expect(rows.length).toBeGreaterThan(0);
    for (const row of rows) {
      const labels = Array.from(row.querySelectorAll("[data-reason]")).map((chip) => chip.getAttribute("data-reason"));
      expect(labels).toEqual(expect.arrayContaining(["strikeout_duel", "world_series"]));
    }
  });
});

describe("how games are chosen", () => {
  it("explains the rule of each reason in plain words, with its count", () => {
    const { getByLabelText } = view();
    const card = getByLabelText("How games are chosen");

    expect(card.querySelector("h2")?.textContent).toBe("How games are chosen");
    expect(text(card)).toContain(
      "A game is here when at least one of these is true. Fixed rules, computed from the data before the list was built; who won is not one of them. 30 of the 40 postseason games qualify, so pick a reason to narrow the list.",
    );
    const items = Array.from(card.querySelectorAll("li")).map((li) => text(li));
    expect(items).toEqual([
      "Strikeout duel15 gamesBoth starters strike out batters at an above-average rate: a strikeout rate of 25% or more over a full sample, before the game.",
      "Veteran duel12 gamesBoth starters had pitched in at least 5 earlier MLB seasons.",
      "Series-ending game11 gamesThe game decided its series.",
      "World Series game5 gamesEvery World Series game is on the list.",
    ]);
  });

  it("does not change with the reasons picked: it describes the rules, not the list", () => {
    const { getByLabelText } = view({ reason: "world_series" });

    expect(text(getByLabelText("How games are chosen"))).toContain("Strikeout duel15 games");
  });

  it("says 1 game, not 1 games", () => {
    const one: ArchiveIndex = {
      ...INDEX,
      games: INDEX.games.map((game, i) => ({ ...game, notable: i === 0 ? ["world_series" as const] : [] })),
      notable_count: 1,
    };
    const { getByLabelText } = view({}, one);

    expect(text(getByLabelText("How games are chosen"))).toContain("World Series game1 game");
    expect(text(getByLabelText("How games are chosen"))).not.toContain("1 games");
  });

  it("is placed after the list in the page order, so a phone reads the list first", () => {
    const { container } = view();
    const list = container.querySelector("[data-notable-list]") as Element;
    const card = container.querySelector('aside[aria-label="How games are chosen"]') as Element;

    expect(list.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe("no match", () => {
  it("says no game has every reason picked, with a way back", () => {
    const { container, getByRole } = view({ reason: ["veteran_duel", "series_clincher", "strikeout_duel", "world_series"] });

    expect(container.querySelector("h2")?.textContent).toBe("No games have every reason picked.");
    expect(getByRole("link", { name: "Clear" }).getAttribute("href")).toBe("/notable");
    expect(container.querySelector("[data-notable-list]")).toBeNull();
    expect(text(container.querySelector("[data-count]"))).toContain("Showing 0 of 30 notable games");
  });

  it("says no game met a rule when the index has no notable game at all", () => {
    const quiet: ArchiveIndex = { ...INDEX, games: INDEX.games.map((game) => ({ ...game, notable: [] })), notable_count: 0 };
    const { container, getByRole } = view({}, quiet);

    expect(container.querySelector("h2")?.textContent).toBe("No game met a rule");
    expect(getByRole("link", { name: "Browse all 40 games" }).getAttribute("href")).toBe("/archive");
  });
});

describe("a hostile URL", () => {
  it("is ignored and never written into the page", () => {
    const { container } = view({ reason: ['"><script>alert(1)</script>', "<img src=x onerror=alert(1)>"], page: "<b>" });

    expect(container.innerHTML).not.toMatch(/<script|onerror|<b>/i);
    expect(text(container.querySelector("[data-count]"))).toContain("Showing 30 notable games");
  });
});

describe("the archive is not available", () => {
  it("is a neutral notice under the title, not an error", () => {
    const { getByRole, container } = render(<NotableUnavailable />);

    expect(getByRole("status").textContent).toBe("The archive is not available right now.");
    expect(container.querySelector("h1")?.textContent).toBe("Notable duels of 2026");
  });
});
