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
    expect(container.querySelector('a[aria-label="October 26, 1 game"]')?.getAttribute("data-state")).toBe("range");
    expect(text(container.querySelector("[data-calendar-key]"))).toContain("Day with games (number of games)");
    expect(text(container.querySelector("[data-calendar-key]"))).toContain("Start and end of your range");
  });

  it("says the selection to assistive tech: the name and aria-current on the start and the end, and on nothing else", () => {
    const { container, getByRole } = view({ from: "2026-10-23", to: "2026-10-28" });

    expect(getByRole("link", { name: "October 23, 1 game, start of your range" }).getAttribute("aria-current")).toBe("date");
    expect(getByRole("link", { name: "October 28, 1 game, end of your range" }).getAttribute("aria-current")).toBe("date");
    expect(container.querySelectorAll('a[aria-current="date"]')).toHaveLength(2);
    expect(getByRole("link", { name: "October 26, 1 game" }).hasAttribute("aria-current")).toBe(false);
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

    expect(pills).toEqual(["Any game40", "Series-ending game11", "Strikeout duel15", "Veteran duel12", "World Series game5"]);
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
  it("says how many games are shown of how many, newest first", () => {
    const { container } = view();

    expect(text(container.querySelector("[data-count]"))).toBe("Showing 40 of 40 games, newest first");
  });

  it("follows the filters", () => {
    const { container } = view({ from: "2026-10-23", to: "2026-10-28" });

    expect(text(container.querySelector("[data-count]"))).toBe("Showing 5 of 40 games, newest first");
  });

  it("writes the chosen range in words and offers Clear, only when something is chosen", () => {
    const chosen = view({ from: "2026-10-23", to: "2026-10-28" });
    expect(chosen.container.textContent).toContain("Oct 23 to Oct 28, 2026");
    expect(chosen.getByRole("link", { name: "Clear" }).getAttribute("href")).toBe("/archive");
    chosen.unmount();

    const oneDay = view({ from: "2026-10-28" });
    expect(oneDay.container.textContent).toContain("Oct 28, 2026");
    oneDay.unmount();

    const none = view();
    expect(none.queryByRole("link", { name: "Clear" })).toBeNull();
  });
});

describe("the results", () => {
  it("are a list of game rows on a phone and a table from the large breakpoint, 40 each", () => {
    const { container } = view();

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

  it("has no pager for 40 games", () => {
    const { queryByRole } = view();

    expect(queryByRole("navigation", { name: "Pages" })).toBeNull();
  });

  it("shows 50 games a page and a pager with Previous and Next, for 120 games", () => {
    const index = manyGames(120);
    const { container, getByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({ page: "2" }, index)} />);

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(50);
    const pager = within(getByRole("navigation", { name: "Pages" }));
    expect(pager.getByRole("link", { name: "Previous page" }).getAttribute("href")).toBe("/archive");
    expect(pager.getByRole("link", { name: "Next page" }).getAttribute("href")).toBe("/archive?page=3");
    expect(text(getByRole("navigation", { name: "Pages" }))).toContain("Page 2 of 3");
  });

  it("shows the last page with what is left, and no Next", () => {
    const index = manyGames(120);
    const { container, queryByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({ page: "3" }, index)} />);

    expect(container.querySelectorAll('[data-results="rows"] a[href^="/game/"]')).toHaveLength(20);
    expect(queryByRole("link", { name: "Next page" })).toBeNull();
  });

  it("links to the next page on the first page", () => {
    const index = manyGames(120);
    const { getByRole } = render(<ArchiveView index={index} query={parseArchiveQuery({}, index)} />);

    expect(getByRole("link", { name: "Next page" }).getAttribute("href")).toBe("/archive?page=2");
    expect(text(getByRole("navigation", { name: "Pages" }))).toContain("Page 1 of 3");
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
    });

    expect(container.innerHTML).not.toMatch(/<script|onerror|onmouseover|javascript:/i);
    expect(text(container.querySelector("[data-count]"))).toBe("Showing 40 of 40 games, newest first");
  });
});

describe("the archive is not available", () => {
  it("is a neutral notice, not an error", () => {
    const { getByRole, container } = render(<ArchiveUnavailable />);

    expect(getByRole("status").textContent).toBe("The archive is not available right now.");
    expect(container.querySelector("h1")?.textContent).toBe("Archive");
  });
});
