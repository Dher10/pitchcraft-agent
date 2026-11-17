import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { homeView, seriesBoard } from "@/lib/home";
import type { ArchiveIndex } from "@/lib/types";

// U6 (docs/plans/R4-U.md): which home the site shows, and the line score of the last series, from the index alone.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));

describe("which home", () => {
  it("is the season in review when it is the off season and the index is there", () => {
    expect(homeView("off_season", INDEX)).toBe("archive_home");
  });

  it("is the daily view in season, whatever the index says (Today in season is frozen, D67)", () => {
    expect(homeView("in_season", INDEX)).toBe("daily_view");
    expect(homeView("in_season", null)).toBe("daily_view");
  });

  it("is the daily view when the index is missing or empty, as the interim home was", () => {
    expect(homeView("off_season", null)).toBe("daily_view");
    expect(homeView("off_season", { ...INDEX, games: [], count: 0, notable_count: 0 })).toBe("daily_view");
  });
});

describe("the series board", () => {
  it("is the World Series, game by game, from the index", () => {
    const board = seriesBoard(INDEX)!;

    expect(board.round).toBe("World Series");
    expect(board.games.map((g) => g.number)).toEqual([1, 2, 3, 4, 5]);
    const [first, second] = board.rows;
    expect(first.nickname).toBe("Brewers");
    expect(second.nickname).toBe("Rays");
    expect(first.cells.map((c) => c.runs)).toEqual([3, 5, 10, 3, 4]);
    expect(second.cells.map((c) => c.runs)).toEqual([2, 4, 1, 4, 1]);
    expect(first.wins).toBe(4);
    expect(second.wins).toBe(1);
  });

  it("links each cell to its game and marks who won it", () => {
    const board = seriesBoard(INDEX)!;
    const g5 = board.games[4];

    expect(g5.game_pk).toBe(849799);
    expect(board.rows[0].cells[4]).toMatchObject({ game_pk: 849799, won: true });
    expect(board.rows[1].cells[4]).toMatchObject({ game_pk: 849799, won: false });
    expect(board.rows[0].cells[3].won).toBe(false);
    expect(board.rows[1].cells[3].won).toBe(true);
    for (const row of board.rows) for (const cell of row.cells) expect(cell.label).toMatch(/^Game \d: \w[\w -]* \d+, \w[\w -]* \d+$/);
    expect(board.rows[0].cells[0].label).toBe("Game 1: Brewers 3, Rays 2");
    expect(board.rows[1].cells[0].label).toBe("Game 1: Rays 2, Brewers 3");
  });

  it("says who won the series, and picks the winner's total", () => {
    const board = seriesBoard(INDEX)!;

    expect(board.sentence).toBe("World Series. Brewers win the series 4-1. Pick a game to see how its starters did.");
    expect(board.rows[0].seriesWinner).toBe(true);
    expect(board.rows[1].seriesWinner).toBe(false);
  });

  it("is absent while the series is not over: only the approved sentence about a won series is written", () => {
    const only = (n: number): ArchiveIndex => ({
      ...INDEX,
      games: INDEX.games.filter((g) => g.round === "World Series").filter((g) => (g.series.game_number ?? 99) <= n),
    });

    expect(seriesBoard(only(3))).toBeNull();
    expect(seriesBoard(only(4))).toBeNull();
    expect(seriesBoard(only(5))).not.toBeNull();
  });

  it("is absent for a tied series and when the number of games in the series is not known", () => {
    const tied: ArchiveIndex = {
      ...INDEX,
      games: INDEX.games
        .filter((g) => g.round === "World Series" && (g.series.game_number ?? 99) <= 2)
        .map((g) => (g.series.game_number === 2 ? { ...g, result: { away_runs: 6, home_runs: 1, winner: "away" as const } } : g)),
    };
    const unknownLength: ArchiveIndex = {
      ...INDEX,
      games: INDEX.games.map((g) => (g.round === "World Series" ? { ...g, series: { ...g.series, games_in_series: null } } : g)),
    };

    expect(seriesBoard(tied)).toBeNull();
    expect(seriesBoard(unknownLength)).toBeNull();
  });

  it("is absent when the index has no World Series game, and for no index", () => {
    expect(seriesBoard({ ...INDEX, games: INDEX.games.filter((g) => g.round !== "World Series") })).toBeNull();
    expect(seriesBoard(null)).toBeNull();
  });

  it("shows a measured zero as 0", () => {
    const shutout: ArchiveIndex = {
      ...INDEX,
      games: INDEX.games.map((g) => (g.game_pk === 849799 ? { ...g, result: { away_runs: 3, home_runs: 0, winner: "away" as const } } : g)),
    };

    expect(seriesBoard(shutout)!.rows[1].cells[4].runs).toBe(0);
  });
});
