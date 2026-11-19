import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import {
  DEFAULT_PER,
  PAGE_SIZES,
  calendarMonth,
  dayHref,
  hrefFor,
  noMatchText,
  pageCount,
  parseArchiveQuery,
  reasonCount,
  selectGames,
  type ArchiveQuery,
} from "@/lib/archiveQuery";

// U4 (docs/plans/R4-U.md): the archive's filters, from the URL and the index alone. Invalid values are ignored and never
// echoed; a game must have every reason picked; counts and links come from one place.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));
const q = (params: Record<string, string | string[] | undefined> = {}) => parseArchiveQuery(params, INDEX);
const pks = (query: ArchiveQuery) => selectGames(INDEX, query).map((row) => row.game_pk);

describe("parsing the URL", () => {
  it("is empty for no parameters", () => {
    expect(q()).toEqual({ team: null, from: null, to: null, reasons: [], page: 1, month: null, per: 20 });
  });

  it("keeps a team that played in the index, in either side of a game", () => {
    expect(q({ team: "MIL" }).team).toBe("MIL");
    expect(q({ team: "TB" }).team).toBe("TB");
  });

  it.each(["mil", "XXX", "", "MIL ", "<script>", "MIL,TB", "Milwaukee Brewers", "../x"])("ignores the team %j", (team) => {
    expect(q({ team }).team).toBeNull();
  });

  it("takes the first value when a parameter is repeated", () => {
    expect(q({ team: ["TB", "MIL"] }).team).toBe("TB");
    expect(q({ from: ["2026-10-23", "2026-10-01"], to: ["2026-10-28"] }).from).toBe("2026-10-23");
  });

  it("keeps a day and a range inside the index, inclusive of both ends", () => {
    expect(q({ from: "2026-10-23", to: "2026-10-28" })).toMatchObject({ from: "2026-10-23", to: "2026-10-28" });
    expect(q({ from: "2026-09-29" }).from).toBe("2026-09-29");
    expect(q({ from: "2026-10-28" }).from).toBe("2026-10-28");
  });

  it.each(["2026-09-28", "2026-10-29", "2026-10-32", "2026-02-30", "10/23/2026", "2026-10-23T10:00", "yesterday", "", "20261023"])(
    "ignores the day %j (outside the index or not a day)",
    (from) => {
      expect(q({ from }).from).toBeNull();
    },
  );

  it("ignores an end before the start, and an end with no start", () => {
    expect(q({ from: "2026-10-23", to: "2026-10-01" }).to).toBeNull();
    expect(q({ to: "2026-10-23" }).to).toBeNull();
    expect(q({ from: "2026-10-23", to: "garbage" })).toMatchObject({ from: "2026-10-23", to: null });
  });

  it("keeps the known reasons, once each, in the index's order, and drops the rest", () => {
    expect(q({ reason: ["world_series", "strikeout_duel", "strikeout_duel", "nonsense"] }).reasons).toEqual([
      "strikeout_duel",
      "world_series",
    ]);
    expect(q({ reason: "veteran_duel" }).reasons).toEqual(["veteran_duel"]);
    expect(q({ reason: ["", "STRIKEOUT_DUEL", "series_clincher "] }).reasons).toEqual([]);
  });

  it.each([["2", 2], ["1", 1]])("reads the page %j", (page, expected) => {
    // The index has 40 games: two pages of 20 by default.
    expect(q({ page }).page).toBe(expected);
  });

  it("ignores a page beyond the last", () => {
    expect(q({ page: "3" }).page).toBe(1);
  });

  it.each(["0", "-1", "1.5", "abc", "", "99999", "1e3", " 2"])("ignores the page %j", (page) => {
    expect(q({ page }).page).toBe(1);
  });

  it("keeps a month of the index and ignores any other", () => {
    expect(q({ month: "2026-09" }).month).toBe("2026-09");
    expect(q({ month: "2026-10" }).month).toBe("2026-10");
    for (const month of ["2026-08", "2026-11", "2026-13", "2025-10", "October", "2026-1", ""]) expect(q({ month }).month, month).toBeNull();
  });
});

describe("what is shown", () => {
  it("is every game, newest first, with no filter", () => {
    expect(pks(q())).toEqual(INDEX.games.map((row) => row.game_pk));
  });

  it("filters by team on either side, by day and by range (inclusive)", () => {
    const mil = pks(q({ team: "MIL" }));
    expect(mil.length).toBeGreaterThan(0);
    for (const row of selectGames(INDEX, q({ team: "MIL" }))) expect([row.away.abbreviation, row.home.abbreviation]).toContain("MIL");

    const day = selectGames(INDEX, q({ from: "2026-10-28" }));
    expect(day.length).toBe(1);
    expect(day[0].date).toBe("2026-10-28");

    const range = selectGames(INDEX, q({ from: "2026-10-23", to: "2026-10-28" }));
    expect(range.every((row) => row.date >= "2026-10-23" && row.date <= "2026-10-28")).toBe(true);
    expect(range.length).toBe(5);
  });

  it("requires every reason picked (AND)", () => {
    const duel = selectGames(INDEX, q({ reason: "strikeout_duel" }));
    expect(duel.length).toBe(15);
    const both = selectGames(INDEX, q({ reason: ["strikeout_duel", "series_clincher"] }));
    expect(both.length).toBeGreaterThan(0);
    expect(both.length).toBeLessThan(15);
    for (const row of both) expect(row.notable).toEqual(expect.arrayContaining(["strikeout_duel", "series_clincher"]));
  });

  it("has no game for a combination nobody has, instead of widening it", () => {
    expect(pks(q({ team: "NYY", from: "2026-10-23", to: "2026-10-28" }))).toEqual([]);
  });

  it("combines team, dates and reasons", () => {
    const rows = selectGames(INDEX, q({ team: "MIL", from: "2026-10-23", to: "2026-10-28", reason: "world_series" }));
    expect(rows.length).toBe(5);
  });
});

describe("the count on each reason", () => {
  it("is the published count with no filter", () => {
    expect(reasonCount(INDEX, q(), null)).toBe(40);
    expect(reasonCount(INDEX, q(), "strikeout_duel")).toBe(15);
    expect(reasonCount(INDEX, q(), "veteran_duel")).toBe(12);
    expect(reasonCount(INDEX, q(), "series_clincher")).toBe(11);
    expect(reasonCount(INDEX, q(), "world_series")).toBe(5);
  });

  it("follows the team and the dates, and the reasons already picked", () => {
    const query = q({ from: "2026-10-23", to: "2026-10-28" });
    expect(reasonCount(INDEX, query, null)).toBe(5);
    expect(reasonCount(INDEX, query, "world_series")).toBe(5);
    expect(reasonCount(INDEX, q({ team: "MIL" }), null)).toBe(selectGames(INDEX, q({ team: "MIL" })).length);

    const picked = q({ reason: "strikeout_duel" });
    expect(reasonCount(INDEX, picked, "strikeout_duel")).toBe(15);
    expect(reasonCount(INDEX, picked, "world_series")).toBe(selectGames(INDEX, q({ reason: ["strikeout_duel", "world_series"] })).length);
    // "Any game" is the total without the reasons.
    expect(reasonCount(INDEX, picked, null)).toBe(40);
  });
});

describe("pages", () => {
  it("are 20 games each by default, and the index of 40 games is two pages", () => {
    expect(DEFAULT_PER).toBe(20);
    expect(PAGE_SIZES).toEqual([10, 20, 50, "all"]);
    expect(pageCount(40, 20)).toBe(2);
    expect(pageCount(0, 20)).toBe(1);
    expect(pageCount(20, 20)).toBe(1);
    expect(pageCount(21, 20)).toBe(2);
    expect(pageCount(120, 50)).toBe(3);
    expect(pageCount(40, 10)).toBe(4);
  });

  it("are one page for All, whatever the count", () => {
    expect(pageCount(40, "all")).toBe(1);
    expect(pageCount(5000, "all")).toBe(1);
    expect(pageCount(0, "all")).toBe(1);
  });

  it.each([["10", 10], ["20", 20], ["50", 50], ["all", "all"]])("reads the page size %j", (per, expected) => {
    expect(q({ per }).per).toBe(expected);
  });

  it.each(["", "5", "15", "100", "ALL", "All", "-10", "10.5", "abc", "<script>", "10 ", "0x10"])("ignores the page size %j and falls back to 20", (per) => {
    expect(q({ per }).per).toBe(20);
  });

  it("takes the first value of a repeated per", () => {
    expect(q({ per: ["10", "50"] }).per).toBe(10);
  });

  it("checks the page against the page size", () => {
    expect(q({ per: "10", page: "4" }).page).toBe(4);
    expect(q({ per: "10", page: "5" }).page).toBe(1);
    expect(q({ page: "2" }).page).toBe(2);
    expect(q({ page: "3" }).page).toBe(1);
    expect(q({ per: "50", page: "2" }).page).toBe(1);
    expect(q({ per: "all", page: "2" }).page).toBe(1);
  });
});

describe("links", () => {
  it("write the same URL for the same filters, in a fixed order, with defaults left out", () => {
    const query = q({ team: "MIL", from: "2026-10-23", to: "2026-10-28", reason: ["world_series", "strikeout_duel"] });
    expect(hrefFor(query, {})).toBe("/archive?team=MIL&from=2026-10-23&to=2026-10-28&reason=strikeout_duel&reason=world_series");
    expect(hrefFor(q(), {})).toBe("/archive");
  });

  it("change one thing at a time and reset the page", () => {
    const query = q({ team: "MIL", reason: "strikeout_duel" });
    expect(hrefFor(query, { team: null })).toBe("/archive?reason=strikeout_duel");
    expect(hrefFor(query, { reasons: [] })).toBe("/archive?team=MIL");
    expect(hrefFor({ ...query, page: 2 }, { team: "TB" })).toBe("/archive?team=TB&reason=strikeout_duel");
    expect(hrefFor(query, { page: 2 })).toBe("/archive?team=MIL&reason=strikeout_duel&page=2");
    expect(hrefFor(query, { month: "2026-09" })).toBe("/archive?team=MIL&reason=strikeout_duel&month=2026-09");
  });

  it("write per only when it is not the default, after month and before page", () => {
    const query = q({ team: "MIL", per: "10" });
    expect(hrefFor(query, {})).toBe("/archive?team=MIL&per=10");
    expect(hrefFor(query, { page: 2 })).toBe("/archive?team=MIL&per=10&page=2");
    expect(hrefFor(q({ team: "MIL", per: "all", month: "2026-10" }), {})).toBe("/archive?team=MIL&month=2026-10&per=all");
    expect(hrefFor(q({ per: "20" }), {})).toBe("/archive");
    expect(hrefFor(q({ per: "bogus" }), {})).toBe("/archive");
  });

  it("change the page size, keep the filters and go back to page 1", () => {
    const query = q({ team: "MIL", from: "2026-10-23", reason: "world_series", month: "2026-10", per: "10" });
    expect(hrefFor(query, { per: 50 })).toBe("/archive?team=MIL&from=2026-10-23&reason=world_series&month=2026-10&per=50");
    expect(hrefFor(query, { per: 20 })).toBe("/archive?team=MIL&from=2026-10-23&reason=world_series&month=2026-10");
    expect(hrefFor({ ...query, page: 3 }, { per: "all" })).toBe("/archive?team=MIL&from=2026-10-23&reason=world_series&month=2026-10&per=all");
  });

  it("keep per on the links of the other filters", () => {
    expect(hrefFor(q({ per: "50" }), { team: "TB" })).toBe("/archive?team=TB&per=50");
    expect(dayHref(q({ per: "10" }), "2026-10-23")).toBe("/archive?from=2026-10-23&month=2026-10&per=10");
  });

  it("never carry a value that was not validated", () => {
    const query = q({ team: "<script>", from: "x", reason: "evil", page: "-3", month: "nope", per: "<b>" });
    expect(hrefFor(query, {})).toBe("/archive");
  });
});

describe("the two-tap range", () => {
  it("first tap picks a day", () => {
    expect(dayHref(q(), "2026-10-23")).toBe("/archive?from=2026-10-23&month=2026-10");
  });

  it("second tap on a later day ends the range", () => {
    expect(dayHref(q({ from: "2026-10-23" }), "2026-10-28")).toBe("/archive?from=2026-10-23&to=2026-10-28&month=2026-10");
  });

  it("a second tap on the same day makes it a one-day range", () => {
    expect(dayHref(q({ from: "2026-10-23" }), "2026-10-23")).toBe("/archive?from=2026-10-23&to=2026-10-23&month=2026-10");
  });

  it("a tap before the start, or after a finished range, starts again", () => {
    expect(dayHref(q({ from: "2026-10-23" }), "2026-10-10")).toBe("/archive?from=2026-10-10&month=2026-10");
    expect(dayHref(q({ from: "2026-10-23", to: "2026-10-28" }), "2026-10-07")).toBe("/archive?from=2026-10-07&month=2026-10");
  });

  it("keeps the team and the reasons, and shows the month of the tapped day", () => {
    expect(dayHref(q({ team: "MIL", reason: "world_series" }), "2026-09-29")).toBe(
      "/archive?team=MIL&from=2026-09-29&reason=world_series&month=2026-09",
    );
  });

  it("works across months: the start in September, the end in October", () => {
    expect(dayHref(q({ from: "2026-09-30" }), "2026-10-05")).toBe("/archive?from=2026-09-30&to=2026-10-05&month=2026-10");
  });
});

describe("the calendar", () => {
  it("shows the month of the last game by default, with the games of each day", () => {
    const cal = calendarMonth(INDEX, q());

    expect(cal.title).toBe("October 2026");
    expect(cal.month).toBe("2026-10");
    const days = cal.cells.filter((cell) => "iso" in cell);
    expect(days).toHaveLength(31);
    const oct3 = days.find((cell) => "iso" in cell && cell.iso === "2026-10-03");
    expect(oct3).toMatchObject({ games: 4, label: "October 3, 4 games" });
    expect(days.find((cell) => "iso" in cell && cell.iso === "2026-10-09")).toMatchObject({ games: 0, href: null });
    expect(days.find((cell) => "iso" in cell && cell.iso === "2026-10-08")).toMatchObject({ label: "October 8, 1 game" });
    const total = days.reduce((sum, cell) => sum + ("games" in cell ? cell.games : 0), 0);
    expect(total).toBe(INDEX.games.filter((row) => row.date.startsWith("2026-10")).length);
  });

  it("starts the grid on Sunday with the days of the neighboring months as plain numbers", () => {
    const cal = calendarMonth(INDEX, q());

    expect(cal.cells.length % 7).toBe(0);
    expect(cal.weekdays).toEqual(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]);
    // 1 October 2026 is a Thursday: four leading days (27 to 30 September).
    expect(cal.cells.slice(0, 4).map((cell) => ("outside" in cell ? cell.outside : null))).toEqual([27, 28, 29, 30]);
  });

  it("is bounded by the index: September has the previous month's link disabled and the next enabled", () => {
    const sept = calendarMonth(INDEX, q({ month: "2026-09" }));
    expect(sept.title).toBe("September 2026");
    expect(sept.previous).toBeNull();
    expect(sept.next).toBe("/archive?month=2026-10");

    const oct = calendarMonth(INDEX, q());
    expect(oct.next).toBeNull();
    expect(oct.previous).toBe("/archive?month=2026-09");
  });

  it("opens on the month of the start day when there is one", () => {
    expect(calendarMonth(INDEX, q({ from: "2026-09-30" })).month).toBe("2026-09");
  });

  it("marks the start and the end of the range and the days between", () => {
    const cal = calendarMonth(INDEX, q({ from: "2026-10-23", to: "2026-10-28" }));
    const state = (iso: string) => cal.cells.find((cell) => "iso" in cell && cell.iso === iso);

    expect(state("2026-10-23")).toMatchObject({ state: "end" });
    expect(state("2026-10-28")).toMatchObject({ state: "end" });
    expect(state("2026-10-24")).toMatchObject({ state: "range" });
    expect(state("2026-10-26")).toMatchObject({ state: "range" });
    expect(state("2026-10-22")).toMatchObject({ state: "none" });
  });

  it("names the start and the end of a range in the day's accessible name", () => {
    const cal = calendarMonth(INDEX, q({ from: "2026-10-23", to: "2026-10-28" }));
    const day = (iso: string) => cal.cells.find((cell) => "iso" in cell && cell.iso === iso) as { label: string | null; selection: string | null };

    expect(day("2026-10-23")).toMatchObject({ label: "October 23, 1 game, start of your range", selection: "start" });
    expect(day("2026-10-28")).toMatchObject({ label: "October 28, 1 game, end of your range", selection: "end" });
    expect(day("2026-10-26")).toMatchObject({ label: "October 26, 1 game, in your range", selection: null, inRange: true });
    expect(day("2026-10-24")).toMatchObject({ label: "October 24, 1 game, in your range", selection: null, inRange: true });
    expect(day("2026-10-22")).toMatchObject({ label: null, selection: null, inRange: false });
  });

  it("names a single chosen day as selected, whether the end is missing or the same day", () => {
    for (const query of [q({ from: "2026-10-23" }), q({ from: "2026-10-23", to: "2026-10-23" })]) {
      const day = calendarMonth(INDEX, query).cells.find((cell) => "iso" in cell && cell.iso === "2026-10-23") as { label: string; selection: string };
      expect(day).toMatchObject({ label: "October 23, 1 game, selected", selection: "selected" });
    }
  });

  it("uses the plural of games in a selected day too", () => {
    const day = calendarMonth(INDEX, q({ from: "2026-10-03", to: "2026-10-07" })).cells.find((cell) => "iso" in cell && cell.iso === "2026-10-03") as { label: string };

    expect(day.label).toBe("October 3, 4 games, start of your range");
  });

  it("marks a single chosen day as a start", () => {
    const cal = calendarMonth(INDEX, q({ from: "2026-10-23" }));

    expect(cal.cells.find((cell) => "iso" in cell && cell.iso === "2026-10-23")).toMatchObject({ state: "end" });
  });

  it("links each day with games through the two-tap rule, and a day without games to nothing", () => {
    const cal = calendarMonth(INDEX, q({ from: "2026-10-23" }));
    const day = (iso: string) => cal.cells.find((cell) => "iso" in cell && cell.iso === iso) as { href: string | null };

    expect(day("2026-10-28").href).toBe("/archive?from=2026-10-23&to=2026-10-28&month=2026-10");
    expect(day("2026-10-25").href).toBeNull();
  });
});

describe("every link the archive can make", () => {
  it("stays on /archive and carries only validated characters", () => {
    const queries = [q(), q({ team: "MIL" }), q({ from: "2026-10-23", to: "2026-10-28", reason: ["world_series"] }), q({ month: "2026-09" })];
    const links: string[] = [];
    for (const query of queries) {
      const month = calendarMonth(INDEX, query);
      links.push(...[month.previous, month.next].filter((l): l is string => l !== null));
      for (const cell of month.cells) if ("href" in cell && cell.href) links.push(cell.href);
      for (const reason of ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"] as const) {
        links.push(hrefFor(query, { reasons: [reason] }));
      }
      links.push(hrefFor(query, { page: 2 }), hrefFor(query, { team: "TB" }));
    }
    expect(links.length).toBeGreaterThan(80);
    for (const link of links) expect(link, link).toMatch(/^\/archive(\?[A-Za-z0-9_=&-]+)?$/);
  });
});

describe("the sentence for no match", () => {
  it("names the team and the days that were asked", () => {
    expect(noMatchText(INDEX, q({ team: "NYY", from: "2026-10-23", to: "2026-10-28" }))).toEqual({
      title: "No games match these filters",
      body: "The Yankees did not play between Oct 23 and Oct 28. Try other days or another team.",
    });
    expect(noMatchText(INDEX, q({ team: "NYY", from: "2026-10-23" })).body).toBe(
      "The Yankees did not play on Oct 23. Try other days or another team.",
    );
  });

  it("names the days when every reason picked has no game in them", () => {
    expect(noMatchText(INDEX, q({ from: "2026-10-23", to: "2026-10-28", reason: ["veteran_duel", "series_clincher", "strikeout_duel"] })).body).toBe(
      "No game between Oct 23 and Oct 28 has every reason picked. Try other days or another team.",
    );
  });

  it("says only what it can for any other combination", () => {
    expect(noMatchText(INDEX, q({ team: "NYY", reason: "world_series" }))).toEqual({
      title: "No games match these filters",
      body: "Try other days or another team.",
    });
  });

  it("never prints a value that was not validated", () => {
    const text = noMatchText(INDEX, q({ team: "<b>x</b>", from: "<script>" }));
    expect(JSON.stringify(text)).not.toMatch(/script|<b>/);
  });
});
