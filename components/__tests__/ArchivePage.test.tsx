import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";

import ArchiveUnavailable from "@/components/archive/ArchiveUnavailable";
import ArchiveView from "@/components/archive/ArchiveView";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { parseArchiveQuery } from "@/lib/archiveQuery";
import type { ArchiveIndex } from "@/lib/types";

// U4 (docs/plans/R4-U.md, 4 and 5.4): the archive page. Server rendered from the URL, working without JavaScript; every
// value is validated against the index, and nothing that was not validated is written into the page.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));

function view(params: Record<string, string | string[] | undefined> = {}, index: ArchiveIndex = INDEX) {
  return render(<ArchiveView index={index} query={parseArchiveQuery(params, index)} />);
}

const text = (node: Element | null) => node?.textContent ?? "";

describe("the page head", () => {
  it("has the title, the sentence and the mode line of the archive", () => {
    const { container, getByTestId } = view();

    expect(container.querySelector("h1")?.textContent).toBe("Archive");
    expect(text(container)).toContain("Every 2026 postseason game with a report. Pick a team, a day, or a range of days.");
    expect(getByTestId("mode-line").textContent).toBe("2026 season archive, final results through Oct 28, 2026");
  });
});

describe("the filters", () => {
  it("are a plain GET form to /archive, so they work without JavaScript", () => {
    const { getByRole } = view();
    const form = getByRole("form", { name: "Filter games" }) as HTMLFormElement;

    expect(form.getAttribute("method")?.toLowerCase()).toBe("get");
    expect(form.getAttribute("action")).toBe("/archive");
  });

  it("have a team select of the clubs of the index, matching either side, with All teams first", () => {
    const { getByLabelText } = view();
    const select = getByLabelText("Team") as HTMLSelectElement;
    const options = Array.from(select.options).map((option) => [option.value, option.textContent]);

    expect(select.name).toBe("team");
    expect(options[0]).toEqual(["", "All teams"]);
    expect(options).toContainEqual(["MIL", "Milwaukee Brewers"]);
    expect(options).toContainEqual(["TB", "Tampa Bay Rays"]);
    expect(options).toHaveLength(13);
    expect(select.value).toBe("");
  });

  it("select the club of the URL", () => {
    const { getByLabelText } = view({ team: "MIL" });

    expect((getByLabelText("Team") as HTMLSelectElement).value).toBe("MIL");
  });

  it("carry the other filters in hidden fields, only those that were validated", () => {
    const { container } = view({ from: "2026-10-23", to: "2026-10-28", reason: ["world_series", "nonsense"], month: "2026-10", page: "9" });
    const hidden = Array.from(container.querySelectorAll('form input[type="hidden"]')).map((input) => [
      input.getAttribute("name"),
      input.getAttribute("value"),
    ]);

    expect(hidden).toEqual([
      ["from", "2026-10-23"],
      ["to", "2026-10-28"],
      ["reason", "world_series"],
      ["month", "2026-10"],
    ]);
  });

  it("have a submit button for the team", () => {
    const { getByRole } = view();

    expect(getByRole("button", { name: "Show games" }).getAttribute("type")).toBe("submit");
  });
});

describe("the calendar", () => {
  it("shows the month, the weekdays and a link on each day with games, naming the games", () => {
    const { container, getByRole } = view();

    expect(text(container.querySelector("[data-calendar-title]"))).toBe("October 2026");
    expect(Array.from(container.querySelectorAll("[data-weekday]")).map((cell) => cell.textContent)).toEqual([
      "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
    ]);
    expect(getByRole("link", { name: "October 3, 4 games" }).getAttribute("href")).toBe("/archive?from=2026-10-03&month=2026-10");
    expect(getByRole("link", { name: "October 8, 1 game" })).toBeTruthy();
    expect(container.querySelectorAll("a[data-day]")).toHaveLength(INDEX.games.filter((row) => row.date.startsWith("2026-10")).map((row) => row.date).filter((d, i, a) => a.indexOf(d) === i).length);
  });

  it("leaves a day without games as plain text, not a link", () => {
    const { container } = view();
    const nine = Array.from(container.querySelectorAll("[data-day-plain]")).find((cell) => cell.textContent === "9");

    expect(nine).toBeTruthy();
    expect(nine?.tagName).not.toBe("A");
  });

  it("has a previous month link and a disabled next month with its reason, bounded by the index", () => {
    const { getByRole, container } = view();

    expect(getByRole("link", { name: "Previous month" }).getAttribute("href")).toBe("/archive?month=2026-09");
    const next = container.querySelector('[aria-label="Next month, no games"]') as HTMLElement;
    expect(next.getAttribute("aria-disabled")).toBe("true");
    expect(next.tagName).not.toBe("A");
  });

  it("is September with the other direction disabled when the month says so", () => {
    const { getByRole, container } = view({ month: "2026-09" });

    expect(text(container.querySelector("[data-calendar-title]"))).toBe("September 2026");
    expect(getByRole("link", { name: "Next month" }).getAttribute("href")).toBe("/archive?month=2026-10");
    expect((container.querySelector('[aria-label="Previous month, no games"]') as HTMLElement).getAttribute("aria-disabled")).toBe("true");
  });

  it("marks the start, the end and the days between with words as well as fills, and explains the key", () => {
    const { container } = view({ from: "2026-10-23", to: "2026-10-28" });

    expect(container.querySelector('a[aria-label="October 23, 1 game, start of your range"]')?.getAttribute("data-state")).toBe("end");
    expect(container.querySelector('a[aria-label="October 28, 1 game, end of your range"]')?.getAttribute("data-state")).toBe("end");
    expect(container.querySelector('a[aria-label="October 26, 1 game, in your range"]')?.getAttribute("data-state")).toBe("range");
    expect(text(container.querySelector("[data-calendar-key]"))).toContain("Day with games (number of games)");
    expect(text(container.querySelector("[data-calendar-key]"))).toContain("Start and end of your range");
  });

  it("explains the in-range style in the key with a swatch that has the signal-tint fill and the signal bar, always shown", () => {
    for (const props of [{}, { from: "2026-10-23", to: "2026-10-28" }] as const) {
      const { container, unmount } = view(props);
      const items = [...container.querySelectorAll("[data-calendar-key] > span")];
      expect(items.map((item) => text(item))).toEqual([
        "Day with games (number of games)",
        "Start and end of your range",
        "Days in your range",
      ]);
      const swatch = items[2].querySelector("i") as HTMLElement;
      expect(swatch.getAttribute("aria-hidden")).toBe("true");
      expect(swatch.className).toContain("bg-signal-tint");
      expect(swatch.className).toContain("border-b-signal");
      unmount();
    }
  });

  it("says the selection to assistive tech: the name and aria-current on the start and the end, and on nothing else", () => {
    const { container, getByRole } = view({ from: "2026-10-23", to: "2026-10-28" });

    expect(getByRole("link", { name: "October 23, 1 game, start of your range" }).getAttribute("aria-current")).toBe("date");
    expect(getByRole("link", { name: "October 28, 1 game, end of your range" }).getAttribute("aria-current")).toBe("date");
    expect(container.querySelectorAll('a[aria-current="date"]')).toHaveLength(2);
    expect(getByRole("link", { name: "October 26, 1 game, in your range" }).hasAttribute("aria-current")).toBe(false);
  });

  it("names a single chosen day as selected", () => {
    const { container, getByRole } = view({ from: "2026-10-23" });

    expect(getByRole("link", { name: "October 23, 1 game, selected" }).getAttribute("aria-current")).toBe("date");
    expect(container.querySelectorAll('a[aria-current="date"]')).toHaveLength(1);
  });

  it("has no selection and no aria-current with no day chosen", () => {
    const { container } = view();

    expect(container.querySelector('a[aria-current="date"]')).toBeNull();
    expect(container.querySelector('a[aria-label*="your range"], a[aria-label*="selected"]')).toBeNull();
  });

  it("links the second tap to the end of the range through the URL", () => {
    const { getByRole } = view({ from: "2026-10-23" });

    expect(getByRole("link", { name: "October 28, 1 game" }).getAttribute("href")).toBe("/archive?from=2026-10-23&to=2026-10-28&month=2026-10");
  });
});

describe("the reason filter", () => {
  it("has Any game and the four reasons, each with its count", () => {
    const { getByRole } = view();
    const nav = within(getByRole("navigation", { name: "Notable reason" }));
    const pills = nav.getAllByRole("link").map((link) => link.textContent);

    expect(pills).toEqual(["Any game40", "Strikeout duel15", "Veteran duel12", "Series-ending game11", "World Series game5"]);
  });

  it("marks Any game as current when no reason is picked, and a picked reason when it is", () => {
    const none = view();
    expect(within(none.getByRole("navigation", { name: "Notable reason" })).getByRole("link", { name: /Any game/ }).getAttribute("aria-current")).toBe("true");
    none.unmount();

    const picked = view({ reason: "strikeout_duel" });
    const nav = within(picked.getByRole("navigation", { name: "Notable reason" }));
    expect(nav.getByRole("link", { name: /Strikeout duel/ }).getAttribute("aria-current")).toBe("true");
    expect(nav.getByRole("link", { name: /Any game/ }).hasAttribute("aria-current")).toBe(false);
  });

  it("toggles a reason through the URL and keeps the other filters", () => {
    const { getByRole } = view({ team: "MIL", reason: "strikeout_duel" });
    const nav = within(getByRole("navigation", { name: "Notable reason" }));

    expect(nav.getByRole("link", { name: /Strikeout duel/ }).getAttribute("href")).toBe("/archive?team=MIL");
    expect(nav.getByRole("link", { name: /World Series game/ }).getAttribute("href")).toBe("/archive?team=MIL&reason=strikeout_duel&reason=world_series");
    expect(nav.getByRole("link", { name: /Any game/ }).getAttribute("href")).toBe("/archive?team=MIL");
  });

  it("follows the other filters in its counts", () => {
    const { getByRole } = view({ from: "2026-10-23", to: "2026-10-28" });
    const nav = within(getByRole("navigation", { name: "Notable reason" }));

    expect(nav.getByRole("link", { name: /Any game/ }).textContent).toBe("Any game5");
    expect(nav.getByRole("link", { name: /World Series game/ }).textContent).toBe("World Series game5");
    expect(nav.getByRole("link", { name: /Veteran duel/ }).textContent).toMatch(/Veteran duel\d/);
  });
});

describe("the count, the range in words and Clear", () => {
  it("says which games are shown of how many when the list has more than one page, newest first", () => {
    const { container } = view();
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 1 to 20 of 40 games, newest first");
  });

  it("says which games the page shows, on the last page and with another page size", () => {
    expect(text(view({ page: "2" }).container.querySelector("[data-count]"))).toBe("Showing 21 to 40 of 40 games, newest first");
    const ten = view({ per: "10", page: "4" });
    expect(text(ten.container.querySelector("[data-count]"))).toBe("Showing 31 to 40 of 40 games, newest first");
  });

  it("says how many are shown of how many when everything fits on one page", () => {
    expect(text(view({ per: "all" }).container.querySelector("[data-count]"))).toBe("Showing 40 of 40 games, newest first");
    expect(text(view({ per: "50" }).container.querySelector("[data-count]"))).toBe("Showing 40 of 40 games, newest first");
  });

  it("follows the filters", () => {
    const { container } = view({ from: "2026-10-23", to: "2026-10-28" });

    expect(text(container.querySelector("[data-count]"))).toBe("Showing 5 of 40 games, newest first");
  });

  it("uses the filtered count as n when a filter leaves more than one page", () => {
    // MIL plays 13 of the 40 games; the total is the filtered one on both pages, never the archive-wide 40.
    const first = view({ team: "MIL", per: "10" });
    expect(text(first.container.querySelector("[data-count]"))).toBe("Showing 1 to 10 of 13 games, newest first");
    first.unmount();
    const second = view({ team: "MIL", per: "10", page: "2" });
    expect(text(second.container.querySelector("[data-count]"))).toBe("Showing 11 to 13 of 13 games, newest first");
  });

  // Release 2.1.1 (docs/plans/2.1.1.md item 2): the words of the chosen days became the summary with its count of games.
  it("writes the chosen days and their games in words and offers Clear, only when something is chosen", () => {
    const chosen = view({ from: "2026-10-23", to: "2026-10-28" });
    expect(text(chosen.container.querySelector("[data-days-summary]"))).toBe("Oct 23 to Oct 28, 5 games");
    expect(chosen.getByRole("link", { name: "Clear" }).getAttribute("href")).toBe("/archive");
    chosen.unmount();

    const oneDay = view({ from: "2026-10-28" });
    expect(text(oneDay.container.querySelector("[data-days-summary]"))).toBe("Oct 28, 1 game");
    oneDay.unmount();

    const none = view();
    expect(none.queryByRole("link", { name: "Clear" })).toBeNull();
  });
});

describe("the results", () => {
  it("are a list of game rows on a phone and a table from the large breakpoint, 20 each by default", () => {
    const { container } = view();

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(20);
    expect(container.querySelectorAll('[data-results="table"] tbody tr')).toHaveLength(20);
  });

  it("show every game for All, 40 each", () => {
    const { container } = view({ per: "all" });

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(40);
    expect(container.querySelectorAll('[data-results="table"] tbody tr')).toHaveLength(40);
  });

  it("start with the newest game", () => {
    const { container } = view();

    expect(container.querySelector('[data-results="rows"] a[href^="/game/"]')?.getAttribute("href")).toBe(`/game/${INDEX.games[0].game_pk}`);
  });

  it("show at most one reason per row on a phone", () => {
    const { container } = view();

    for (const row of Array.from(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]'))) {
      expect(row.querySelectorAll("[data-reason]").length).toBeLessThanOrEqual(1);
    }
  });

  it("have a table with a caption, scoped headers, and the game cell as the link", () => {
    const { container } = view();
    const table = container.querySelector('[data-results="table"] table') as HTMLElement;

    expect(table.querySelector("caption")?.textContent).toBe("2026 postseason games, newest first");
    expect(Array.from(table.querySelectorAll("thead th")).map((th) => [th.textContent, th.getAttribute("scope")])).toEqual([
      ["Date and round", "col"],
      ["Game and starters", "col"],
      ["Score", "col"],
      ["Notable", "col"],
    ]);
    const first = table.querySelector("tbody tr") as HTMLElement;
    expect(first.querySelector("a")?.getAttribute("href")).toBe(`/game/${INDEX.games[0].game_pk}`);
    expect(text(first)).toContain("Jacob Misiorowski");
  });

  it("shows the notable column as the first reason and +n for the rest, and the dash for none", () => {
    const { container } = view();
    const cells = Array.from(container.querySelectorAll('[data-results="table"] tbody tr')).map((tr) => text(tr.querySelector("td:last-child")));

    expect(cells[0]).toBe("Series-ending game+2");
    expect(cells).toContain("—");
  });

  it("show the score as numerals with the winner marked, and a measured zero as 0", () => {
    const { container } = view();
    const first = container.querySelector('[data-results="table"] tbody tr') as HTMLElement;

    expect(text(first.querySelector("[data-score]"))).toBe("4–1");
    expect(first.querySelector('[data-score] [data-winner="true"]')?.textContent).toBe("4");
  });
});

describe("paging", () => {
  function manyGames(copies: number): ArchiveIndex {
    const games = Array.from({ length: copies }, (_, i) => ({ ...INDEX.games[i % INDEX.games.length], game_pk: 900000 + i }));
    return { ...INDEX, count: games.length, games, notable_count: games.filter((g) => g.notable.length > 0).length };
  }

  it("has no pager when everything fits on one page", () => {
    expect(view({ per: "all" }).queryByRole("navigation", { name: "Pages" })).toBeNull();
    expect(view({ per: "50" }).queryByRole("navigation", { name: "Pages" })).toBeNull();
  });

  it("has a pager for 40 games at 20 a page", () => {
    const { getByRole } = view();
    expect(text(getByRole("navigation", { name: "Pages" }))).toContain("Page 1 of 2");
  });

  it("shows 50 games a page and a pager with Previous and Next, for 120 games", () => {
    const index = manyGames(120);
    const { container, getByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({ per: "50", page: "2" }, index)} />);

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(50);
    const pager = within(getByRole("navigation", { name: "Pages" }));
    expect(pager.getByRole("link", { name: "Previous page" }).getAttribute("href")).toBe("/archive?per=50");
    expect(pager.getByRole("link", { name: "Next page" }).getAttribute("href")).toBe("/archive?per=50&page=3");
    expect(text(getByRole("navigation", { name: "Pages" }))).toContain("Page 2 of 3");
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 51 to 100 of 120 games, newest first");
  });

  it("shows the last page with what is left, and no Next", () => {
    const index = manyGames(120);
    const { container, queryByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({ per: "50", page: "3" }, index)} />);

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(20);
    expect(queryByRole("link", { name: "Next page" })).toBeNull();
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 101 to 120 of 120 games, newest first");
  });

  it("links to the next page on the first page, with no per at the default size", () => {
    const index = manyGames(120);
    const { getByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({}, index)} />);

    expect(getByRole("link", { name: "Next page" }).getAttribute("href")).toBe("/archive?page=2");
    expect(text(getByRole("navigation", { name: "Pages" }))).toContain("Page 1 of 6");
  });

  it("shows all 120 games on one page for All", () => {
    const index = manyGames(120);
    const { container } = render(<ArchiveView index={index} query={parseArchiveQuery({ per: "all" }, index)} />);
    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(120);
  });
});

describe("the page size links", () => {
  const group = (r: ReturnType<typeof view>) => within(r.getByRole("navigation", { name: "Games per page" }));

  it("are a labelled group of four links near the count", () => {
    const r = view();
    expect(text(r.getByRole("navigation", { name: "Games per page" }))).toContain("Games per page");
    expect(group(r).getAllByRole("link").map((a) => [a.textContent, a.getAttribute("href")])).toEqual([
      ["10", "/archive?per=10"],
      ["20", "/archive"],
      ["50", "/archive?per=50"],
      ["All", "/archive?per=all"],
    ]);
  });

  it("mark the current size with aria-current, and only that one", () => {
    for (const [per, name] of [[undefined, "20"], ["10", "10"], ["50", "50"], ["all", "All"], ["bogus", "20"]] as const) {
      const r = view(per === undefined ? {} : { per });
      const current = group(r).getAllByRole("link").filter((a) => a.getAttribute("aria-current") === "true");
      expect(current.map((a) => a.textContent), String(per)).toEqual([name]);
      r.unmount();
    }
  });

  it("keep team, dates, reasons and month, and reset to page 1", () => {
    const r = view({ team: "MIL", from: "2026-10-23", to: "2026-10-28", reason: "world_series", month: "2026-10", per: "10" });
    const base = "/archive?team=MIL&from=2026-10-23&to=2026-10-28&reason=world_series&month=2026-10";
    expect(group(r).getAllByRole("link").map((a) => a.getAttribute("href"))).toEqual([`${base}&per=10`, base, `${base}&per=50`, `${base}&per=all`]);
    r.unmount();
    const second = view({ page: "2" });
    expect(group(second).getAllByRole("link").every((a) => !/page=/.test(a.getAttribute("href") ?? ""))).toBe(true);
  });

  it("keep a 44 by 44 px target on every link", () => {
    for (const a of group(view()).getAllByRole("link")) {
      expect(a.className).toMatch(/min-h-tap/);
      expect(a.className).toMatch(/min-w-tap/);
    }
  });

  it("are not shown when no game matches", () => {
    expect(view({ team: "NYY", from: "2026-10-23", to: "2026-10-28" }).queryByRole("navigation", { name: "Games per page" })).toBeNull();
  });

  it("are carried by the team form, so choosing a team keeps the size", () => {
    const hidden = Array.from(view({ per: "10" }).container.querySelectorAll('form input[type="hidden"]')).map((i) => [i.getAttribute("name"), i.getAttribute("value")]);
    expect(hidden).toContainEqual(["per", "10"]);
    expect(view().container.querySelectorAll('form input[name="per"]')).toHaveLength(0);
  });
});

describe("no match", () => {
  it("is the empty state naming what was asked, with a way back, and no list", () => {
    const { container, getByRole } = view({ team: "NYY", from: "2026-10-23", to: "2026-10-28" });

    expect(container.querySelector("h2")?.textContent).toBe("No games match these filters");
    expect(text(container)).toContain("The Yankees did not play between Oct 23 and Oct 28. Try other days or another team.");
    expect(getByRole("link", { name: "Clear filters" }).getAttribute("href")).toBe("/archive");
    expect(container.querySelector('[data-results="rows"]')).toBeNull();
    expect(container.querySelector('[data-results="table"]')).toBeNull();
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 0 of 40 games, newest first");
  });
});

describe("a hostile URL", () => {
  it("is ignored and never written into the page", () => {
    const { container } = view({
      team: '"><script>alert(1)</script>',
      from: "javascript:alert(1)",
      reason: ["<img src=x onerror=alert(1)>"],
      page: "<b>",
      month: "' onmouseover='x",
      per: "<i>bogus</i>",
    });

    expect(container.innerHTML).not.toMatch(/<script|onerror|onmouseover|javascript:|bogus/i);
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 1 to 20 of 40 games, newest first");
  });
});

describe("the archive is not available", () => {
  it("is a neutral notice, not an error", () => {
    const { getByRole, container } = render(<ArchiveUnavailable />);

    expect(getByRole("status").textContent).toBe("The archive is not available right now.");
    expect(container.querySelector("h1")?.textContent).toBe("Archive");
  });
});

// Codex audit of PR #6 (2026-11-17): a valid index with zero games crashed calendarMonth(). The view handles it before the
// mode line and the calendar are built, with the archive's own notice (docs/plans/R4-U.md 5.4, "index missing").
describe("a valid index with no games", () => {
  const empty = parseArchiveIndex({ ...JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")), count: 0, notable_count: 0, games: [] });

  it("is a valid index, so the view can receive it", () => {
    expect(empty).not.toBeNull();
    expect(empty?.games).toEqual([]);
  });

  it("renders the archive's notice instead of the filters, the mode line and the calendar", () => {
    const { container, getByRole, queryByRole, queryByTestId } = render(<ArchiveView index={empty!} query={parseArchiveQuery({}, empty!)} />);

    expect(container.querySelector("h1")?.textContent).toBe("Archive");
    expect(getByRole("status").textContent).toBe("The archive is not available right now.");
    expect(queryByRole("form", { name: "Filter games" })).toBeNull();
    expect(queryByTestId("mode-line")).toBeNull();
    expect(container.querySelector("[data-calendar-title]")).toBeNull();
    expect(text(container)).not.toMatch(/undefined|NaN/);
  });

  it("ignores any filter in the URL", () => {
    const { getByRole } = render(<ArchiveView index={empty!} query={parseArchiveQuery({ team: "MIL", from: "2026-10-01", month: "2026-10" }, empty!)} />);

    expect(getByRole("status").textContent).toBe("The archive is not available right now.");
  });
});

// Release 2.1.1, item 2 (docs/plans/2.1.1.md; owner's feedback: the range was hard to read). Oct 23 to Oct 28 holds five
// games and one day without games (Oct 25), so every kind of day of a range is in it.
describe("the range on the calendar (2.1.1)", () => {
  const RANGE = { from: "2026-10-23", to: "2026-10-28" };
  const plain = (container: HTMLElement, day: number) =>
    [...container.querySelectorAll("[data-day-plain]")].find((node) => text(node).trim() === String(day)) as HTMLElement;

  it("tells how the calendar works, above the grid", () => {
    const { container } = view();
    const help = container.querySelector("[data-calendar-help]");

    expect(text(help)).toBe("Tap a day to see its games. Tap a second day to see every game in between.");
    expect(help!.compareDocumentPosition(container.querySelector("[data-weekday]")!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("fills the days with games strictly inside the range with signal-tint and a 3 px signal bar", () => {
    const { container } = view(RANGE);
    for (const day of [24, 26, 27]) {
      const link = container.querySelector(`a[aria-label^="October ${day}, "]`) as HTMLElement;
      expect(link.getAttribute("data-state"), `Oct ${day}`).toBe("range");
      expect(link.className, `Oct ${day}`).toContain("bg-signal-tint");
      expect(link.className, `Oct ${day}`).toContain("border-b-[3px]");
      expect(link.className, `Oct ${day}`).toContain("border-b-signal");
    }
  });

  it("gives a day without games inside the range the bar only", () => {
    const { container } = view(RANGE);
    const day = plain(container, 25);

    expect(day.getAttribute("data-in-range")).toBe("");
    expect(day.className).toContain("border-b-[3px]");
    expect(day.className).toContain("border-b-signal");
    expect(day.className).not.toContain("bg-signal-tint");
  });

  it("leaves the start, the end and the days outside the range as they were (controls)", () => {
    const { container } = view(RANGE);
    for (const label of ["October 23, 1 game, start of your range", "October 28, 1 game, end of your range"]) {
      const link = container.querySelector(`a[aria-label="${label}"]`) as HTMLElement;
      expect(link.className).toContain("bg-board");
      expect(link.className).not.toContain("border-b-signal");
    }
    const outside = container.querySelector('a[aria-label="October 19, 1 game"]') as HTMLElement;
    expect(outside.className).not.toMatch(/signal/);
    expect(plain(container, 22).hasAttribute("data-in-range")).toBe(false);
    expect(plain(container, 22).className).not.toContain("border-b-signal");
  });

  it("adds \", in your range\" to the name of a day inside the range, and to nothing else", () => {
    const { container, getByRole } = view(RANGE);

    for (const day of [24, 26, 27]) expect(getByRole("link", { name: `October ${day}, 1 game, in your range` })).toBeTruthy();
    expect(container.querySelectorAll('a[aria-label$=", in your range"]')).toHaveLength(3);
    expect(getByRole("link", { name: "October 23, 1 game, start of your range" })).toBeTruthy();
    expect(getByRole("link", { name: "October 28, 1 game, end of your range" })).toBeTruthy();
    expect(container.querySelectorAll('a[aria-current="date"]')).toHaveLength(2);
  });

  it("names a day inside a range with a team picked the same way: the calendar counts every game", () => {
    const { container } = view({ ...RANGE, team: "NYY" });

    expect(container.querySelectorAll('a[aria-label$=", in your range"]')).toHaveLength(3);
    expect(container.querySelector('a[aria-label="October 26, 1 game, in your range"]')).not.toBeNull();
  });

  // Owner's decision (2.1.1): the summary follows the team and reason filters, so it always says the number the list shows.
  // Oct 3 to Oct 8 holds 15 games; 4 have the Dodgers, 2 of those are strikeout duels.
  it.each([
    [{}, "Oct 3 to Oct 8, 15 games", 15],
    [{ team: "LAD" }, "Oct 3 to Oct 8, 4 games", 4],
    [{ team: "LAD", reason: "strikeout_duel" }, "Oct 3 to Oct 8, 2 games", 2],
  ])("says the same number of games as the list, with filters %o", (filters, summary, shown) => {
    const { container } = view({ from: "2026-10-03", to: "2026-10-08", ...filters });

    expect(text(container.querySelector("[data-days-summary]"))).toBe(summary);
    expect(text(container.querySelector("[data-count]"))).toBe(`Showing ${shown} of 40 games, newest first`);
  });

  it("says no games, like the list, when the team did not play on those days", () => {
    const { container } = view({ ...RANGE, team: "NYY" });

    expect(text(container.querySelector("[data-days-summary]"))).toBe("Oct 23 to Oct 28, 0 games");
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 0 of 40 games, newest first");
  });

  it("sits directly under the calendar grid, with Clear on the same row, before the reason filter", () => {
    const { container, getByRole } = view(RANGE);
    const row = container.querySelector("[data-days-row]") as HTMLElement;
    const grid = container.querySelector("[data-calendar-grid]") as HTMLElement;

    expect(grid.nextElementSibling).toBe(row);
    expect(row.contains(container.querySelector("[data-days-summary]"))).toBe(true);
    expect(row.contains(getByRole("link", { name: "Clear" }))).toBe(true);
    const reasons = container.querySelector('nav[aria-label="Notable reason"]') as HTMLElement;
    expect(row.compareDocumentPosition(reasons) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("counts a range that crosses months, and says nothing with no day chosen", () => {
    const across = view({ from: "2026-09-30", to: "2026-10-03" });
    expect(text(across.container.querySelector("[data-days-summary]"))).toBe("Sep 30 to Oct 3, 9 games");
    across.unmount();

    const none = view({ team: "MIL" });
    expect(none.container.querySelector("[data-days-summary]")).toBeNull();
  });
});
