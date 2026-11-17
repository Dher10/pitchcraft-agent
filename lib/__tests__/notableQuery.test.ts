import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { REASON_ORDER } from "@/lib/archiveQuery";
import {
  NOTABLE_REASONS,
  REASON_DISPLAY_ORDER,
  REASON_LABELS,
  reasonRule,
} from "@/lib/notableReasons";
import { countSentence, notableCount, notableGames, notableHref, parseNotableQuery, ruleCount } from "@/lib/notableQuery";

// U5 (docs/plans/R4-U.md): the notable page's list and its rules from one source, so the pill, the chip, the rule text and
// the count can never disagree. A game must have every reason picked; the order is most reasons first, then newest.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));
const q = (params: Record<string, string | string[] | undefined> = {}) => parseNotableQuery(params);
const withV = (veteran_min: number) => ({ ...INDEX, veteran_min });

describe("one source for the reasons", () => {
  it("has the four reasons in the display order of the design", () => {
    expect(REASON_DISPLAY_ORDER).toEqual(["strikeout_duel", "veteran_duel", "series_clincher", "world_series"]);
    expect(NOTABLE_REASONS.map((reason) => reason.key)).toEqual(REASON_DISPLAY_ORDER);
  });

  it("covers exactly the tags the index can carry", () => {
    expect([...REASON_ORDER].sort()).toEqual([...REASON_DISPLAY_ORDER].sort());
    expect(Object.keys(REASON_LABELS).sort()).toEqual([...REASON_ORDER].sort());
  });

  it("has a label and a rule for every reason, and the label is the one the chips print", () => {
    for (const reason of NOTABLE_REASONS) {
      expect(reason.label.trim().length).toBeGreaterThan(0);
      expect(reasonRule(reason.key, 5).trim().length).toBeGreaterThan(0);
      expect(REASON_LABELS[reason.key]).toBe(reason.label);
    }
  });

  it("writes each rule in plain words, with the veteran threshold from the index", () => {
    expect(reasonRule("strikeout_duel", 5)).toBe(
      "Both starters strike out batters at an above-average rate: a strikeout rate of 25% or more over a full sample, before the game.",
    );
    expect(reasonRule("veteran_duel", 5)).toBe("Both starters had pitched in at least 5 earlier MLB seasons.");
    expect(reasonRule("veteran_duel", 7)).toBe("Both starters had pitched in at least 7 earlier MLB seasons.");
    expect(reasonRule("series_clincher", 5)).toBe("The game decided its series.");
    expect(reasonRule("world_series", 5)).toBe("Every World Series game is on the list.");
  });

  it("counts the games of a rule as the index's tags do", () => {
    for (const reason of REASON_DISPLAY_ORDER) {
      expect(ruleCount(INDEX, reason), reason).toBe(INDEX.games.filter((game) => game.notable.includes(reason)).length);
    }
    expect([ruleCount(INDEX, "strikeout_duel"), ruleCount(INDEX, "veteran_duel"), ruleCount(INDEX, "series_clincher"), ruleCount(INDEX, "world_series")]).toEqual([15, 12, 11, 5]);
  });
});

describe("parsing the URL", () => {
  it("is empty for no parameters", () => {
    expect(q()).toEqual({ reasons: [] });
  });

  it("keeps the known reasons once each, in the index's order, and drops the rest", () => {
    expect(q({ reason: ["world_series", "strikeout_duel", "strikeout_duel", "nonsense"] }).reasons).toEqual(["strikeout_duel", "world_series"]);
    expect(q({ reason: "veteran_duel" }).reasons).toEqual(["veteran_duel"]);
    expect(q({ reason: ["", "STRIKEOUT_DUEL", "series_clincher "] }).reasons).toEqual([]);
    expect(q({ reason: ["<script>", "../x"] }).reasons).toEqual([]);
  });

  it("ignores every other parameter", () => {
    expect(q({ team: "MIL", page: "2", from: "2026-10-01" })).toEqual({ reasons: [] });
  });
});

describe("the list", () => {
  it("is the 30 notable games: every game with at least one reason, and no other", () => {
    const games = notableGames(INDEX, q());
    expect(games).toHaveLength(INDEX.notable_count);
    expect(games).toHaveLength(30);
    for (const game of games) expect(game.notable.length).toBeGreaterThan(0);
    expect(new Set(games.map((g) => g.game_pk)).size).toBe(30);
  });

  it("puts the games with the most reasons first, then the newest", () => {
    const games = notableGames(INDEX, q());

    for (let i = 1; i < games.length; i += 1) {
      const a = games[i - 1];
      const b = games[i];
      expect(a.notable.length >= b.notable.length, `${a.game_pk} before ${b.game_pk}`).toBe(true);
      if (a.notable.length === b.notable.length) {
        expect(a.date > b.date || (a.date === b.date && a.game_pk > b.game_pk), `${a.game_pk} before ${b.game_pk}`).toBe(true);
      }
    }
    expect(games[0].notable).toHaveLength(3);
  });

  it("requires every reason picked (AND)", () => {
    expect(notableGames(INDEX, q({ reason: "strikeout_duel" }))).toHaveLength(15);
    const both = notableGames(INDEX, q({ reason: ["strikeout_duel", "world_series"] }));
    expect(both.length).toBeGreaterThan(0);
    expect(both.length).toBeLessThan(15);
    for (const game of both) expect(game.notable).toEqual(expect.arrayContaining(["strikeout_duel", "world_series"]));
  });

  it("is empty for a combination no game has, instead of widening it", () => {
    const none = notableGames(INDEX, q({ reason: ["veteran_duel", "series_clincher", "strikeout_duel", "world_series"] }));
    expect(none).toEqual([]);
  });
});

describe("the count on each pill", () => {
  it("is the published count with nothing picked", () => {
    expect(notableCount(INDEX, q(), null)).toBe(30);
    expect(notableCount(INDEX, q(), "strikeout_duel")).toBe(15);
    expect(notableCount(INDEX, q(), "veteran_duel")).toBe(12);
    expect(notableCount(INDEX, q(), "series_clincher")).toBe(11);
    expect(notableCount(INDEX, q(), "world_series")).toBe(5);
  });

  it("is the size of the list you get by picking it, given the reasons already picked", () => {
    const picked = q({ reason: "strikeout_duel" });
    for (const reason of REASON_DISPLAY_ORDER) {
      const next = parseNotableQuery({ reason: [...picked.reasons, reason] });
      expect(notableCount(INDEX, picked, reason), reason).toBe(notableGames(INDEX, next).length);
    }
    expect(notableCount(INDEX, picked, null)).toBe(30);
  });
});

describe("links", () => {
  it("write the reasons in a fixed order and leave the default out", () => {
    expect(notableHref([])).toBe("/notable");
    expect(notableHref(["world_series", "strikeout_duel"])).toBe("/notable?reason=strikeout_duel&reason=world_series");
  });
});

describe("every link the notable page can make", () => {
  it("stays on /notable with validated characters", () => {
    const links: string[] = [notableHref([])];
    for (const a of REASON_DISPLAY_ORDER) {
      links.push(notableHref([a]));
      for (const b of REASON_DISPLAY_ORDER) links.push(notableHref([a, b]));
    }
    links.push(notableHref(parseNotableQuery({ reason: ["<script>", "x"] }).reasons));
    expect(links.length).toBeGreaterThan(20);
    for (const link of links) expect(link, link).toMatch(/^\/notable(\?[A-Za-z0-9_=&-]+)?$/);
  });
});

describe("the count line", () => {
  it("says how many of the notable games are shown and which reasons narrow them", () => {
    expect(countSentence(INDEX, q({ reason: "strikeout_duel" }))).toBe("Showing 15 of 30 notable games: Strikeout duel. Most reasons first, then newest.");
    expect(countSentence(INDEX, q({ reason: ["world_series", "strikeout_duel"] }))).toMatch(/^Showing \d+ of 30 notable games: Strikeout duel, World Series game\. Most reasons first, then newest\.$/);
  });

  it("says how many games there are when nothing is picked", () => {
    expect(countSentence(INDEX, q())).toBe("Showing 30 notable games. Most reasons first, then newest.");
  });

  it("shows a zero as 0", () => {
    expect(countSentence(INDEX, q({ reason: ["veteran_duel", "series_clincher", "strikeout_duel", "world_series"] }))).toMatch(/^Showing 0 of 30 notable games: /);
  });
});

describe("the veteran rule follows the threshold the index was built with", () => {
  it("prints the index's number", () => {
    expect(reasonRule("veteran_duel", withV(5).veteran_min)).toContain("at least 5 earlier");
    expect(reasonRule("veteran_duel", withV(8).veteran_min)).toContain("at least 8 earlier");
  });
});
