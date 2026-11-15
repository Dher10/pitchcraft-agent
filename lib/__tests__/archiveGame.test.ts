import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { isGamePk, loadArchiveGame, matchingRow, parseArchiveGame, publishedReport, seriesNeighbors } from "@/lib/archiveGame";

// U3 (docs/plans/R4-U.md): the reader of a game file of archive_version 1.0.0. Nothing is presented before the whole
// envelope is validated, and the id is checked before any file is touched.

// A JSON value read from a file whose shape is checked field by field below: one named alias, not scattered `any`.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Loose = Record<string, any>;

const ARCHIVE = path.join(process.cwd(), "public/data/archive");
const FILES = readdirSync(path.join(ARCHIVE, "games")).filter((name) => name.endsWith(".json"));
const raw = (pk: string | number) => JSON.parse(readFileSync(path.join(ARCHIVE, "games", `${pk}.json`), "utf8"));
const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(ARCHIVE, "index-2026.json"), "utf8")));
const GAME = 849799; // World Series game 5, published live

function mutate(edit: (game: Loose) => void, pk = GAME) {
  const game = raw(pk);
  edit(game);
  return game;
}

describe("the real game files", () => {
  it("are 40, and every one is valid", () => {
    expect(FILES).toHaveLength(40);
    for (const name of FILES) {
      const pk = Number(name.replace(".json", ""));
      expect(() => parseArchiveGame(raw(pk), pk), name).not.toThrow();
    }
  });

  it("give the envelope values the page shows", () => {
    const game = parseArchiveGame(raw(GAME), GAME);

    expect(game.round).toBe("World Series");
    expect(game.result).toEqual({ away_runs: 4, home_runs: 1, status: "final", winner: "away" });
    expect(game.series).toMatchObject({ game_number: 5, over: true, after: "MIL wins 4-1" });
    expect(game.origin.kind).toBe("published_live");
    expect(game.final_line.away).toEqual({ innings_pitched: "5.2", hits: 2, earned_runs: 0, walks: 1, strikeouts: 2 });
    expect(game.starters_check.actual.away?.name).toBe("Jacob Misiorowski");
  });

  it("agree with the index row of the same game on the score and the teams", () => {
    for (const row of INDEX.games) {
      const game = parseArchiveGame(raw(row.game_pk), row.game_pk);
      expect(game.result.away_runs, String(row.game_pk)).toBe(row.result.away_runs);
      expect(game.result.home_runs, String(row.game_pk)).toBe(row.result.home_runs);
      expect(game.teams.away.id).toBe(row.away.id);
      expect(game.date).toBe(row.date);
    }
  });
});

describe("a file that is not valid is refused", () => {
  const BAD: [string, (game: Loose) => void][] = [
    ["another archive version", (g) => (g.archive_version = "1.0.1")],
    ["no version", (g) => delete g.archive_version],
    ["a game_pk that is not the route's", (g) => (g.game_pk = 849800)],
    ["a string game_pk", (g) => (g.game_pk = "849799")],
    ["an unknown key", (g) => (g.extra = 1)],
    ["a missing key", (g) => delete g.final_line],
    ["a status that is not final", (g) => (g.result.status = "live")],
    ["tied runs", (g) => (g.result.home_runs = 4)],
    ["a winner that scored fewer runs", (g) => (g.result.winner = "home")],
    ["negative runs", (g) => (g.result.away_runs = -1)],
    ["fractional runs", (g) => (g.result.away_runs = 4.5)],
    ["a round that is not in the table", (g) => (g.round = "Exhibition")],
    ["a date that is not a day", (g) => (g.date = "2026-10-32")],
    ["an as_of that is not the day before", (g) => (g.origin.as_of = "2026-10-20")],
    ["an unknown origin kind", (g) => (g.origin.kind = "demo")],
    ["a published_live report with no published_at", (g) => (g.origin.published_at = null)],
    ["a reconstructed report with a published_at", (g) => { g.origin.kind = "reconstructed"; }],
    ["an unknown starter check", (g) => (g.starters_check.away = "maybe")],
    ["a started starter with no name", (g) => (g.starters_check.actual.away = null)],
    ["an innings pitched that is not an innings count", (g) => (g.final_line.away.innings_pitched = "5.7")],
    ["a negative hit count", (g) => (g.final_line.away.hits = -2)],
    ["a string strikeout count", (g) => (g.final_line.away.strikeouts = "2")],
    ["an unknown starter with a final line", (g) => { g.starters_check.away = "unknown"; g.starters_check.actual.away = null; }],
    ["a payload with no matchup", (g) => (g.payload.matchups = [])],
    ["a payload with two matchups", (g) => g.payload.matchups.push(g.payload.matchups[0])],
    ["a payload that is not an object", (g) => (g.payload = "x")],
  ];

  it.each(BAD)("%s", (_name, edit) => {
    expect(() => parseArchiveGame(mutate(edit), GAME)).toThrow("archive_game_invalid");
  });

  it("control: the same file untouched is accepted", () => {
    expect(() => parseArchiveGame(mutate(() => undefined), GAME)).not.toThrow();
  });

  it.each([null, undefined, 4, "x", [], true])("a value that is not an object: %s", (value) => {
    expect(() => parseArchiveGame(value, GAME)).toThrow("archive_game_invalid");
  });

  it("keeps a null final-line field as null and a measured zero as 0", () => {
    const game = parseArchiveGame(
      mutate((g) => {
        g.final_line.away.walks = null;
        g.final_line.away.hits = 0;
      }),
      GAME,
    );

    expect(game.final_line.away).toMatchObject({ walks: null, hits: 0 });
  });

  it("accepts an unknown starter: no name and no line", () => {
    const game = parseArchiveGame(
      mutate((g) => {
        g.starters_check.away = "unknown";
        g.starters_check.actual.away = null;
        g.final_line.away = null;
      }),
      GAME,
    );

    expect(game.starters_check.away).toBe("unknown");
    expect(game.final_line.away).toBeNull();
  });
});

describe("the id of the route", () => {
  it.each(["849799", "100000", "123456789"])("%s is a game id", (id) => {
    expect(isGamePk(id)).toBe(true);
  });

  it.each(["", "0", "12345", "1234567890", "0123456", "-849799", "849799.json", "../849799", "849799/x", " 849799", "8.49e5", "abc", "849799\n"])(
    "%j is not",
    (id) => {
      expect(isGamePk(id)).toBe(false);
    },
  );
});

describe("loadArchiveGame", () => {
  it("never touches a file for an id that does not match the pattern", async () => {
    const read = vi.fn();
    for (const id of ["../../package", "12", "849799.json", "..%2f", ""]) {
      expect(await loadArchiveGame(id, read), id).toBeNull();
    }
    expect(read).not.toHaveBeenCalled();
  });

  it("reads games/<id>.json for a valid id and returns the validated file", async () => {
    const read = vi.fn(async () => JSON.stringify(raw(GAME)));
    const game = await loadArchiveGame(String(GAME), read);

    expect(game?.game_pk).toBe(GAME);
    expect(read).toHaveBeenCalledTimes(1);
    expect(String((read.mock.calls[0] as unknown[])[0]).replaceAll("\\", "/")).toMatch(/public\/data\/archive\/games\/849799\.json$/);
  });

  it("returns null for an unknown game (no file), never an error", async () => {
    const read = vi.fn(async () => {
      throw Object.assign(new Error("no such file"), { code: "ENOENT" });
    });

    expect(await loadArchiveGame("999999", read)).toBeNull();
  });

  it("returns null for a file that is not JSON, not valid, or that is another game", async () => {
    expect(await loadArchiveGame(String(GAME), async () => "{not json")).toBeNull();
    expect(await loadArchiveGame(String(GAME), async () => JSON.stringify({ ...raw(GAME), result: {} }))).toBeNull();
    expect(await loadArchiveGame("849802", async () => JSON.stringify(raw(GAME)))).toBeNull();
  });
});

describe("the index row of a game", () => {
  it("is the row of the same game when it agrees with the file", () => {
    expect(matchingRow(parseArchiveGame(raw(GAME), GAME), INDEX)?.game_pk).toBe(GAME);
  });

  it("is not used when the date, the clubs or the score differ, or when there is no index", () => {
    const game = parseArchiveGame(raw(GAME), GAME);
    const row = INDEX.games.find((r) => r.game_pk === GAME)!;
    const withRow = (change: Partial<typeof row>) => ({ ...INDEX, games: INDEX.games.map((r) => (r === row ? { ...row, ...change } : r)) });

    expect(matchingRow(game, withRow({ date: "2026-10-27" }))).toBeNull();
    expect(matchingRow(game, withRow({ result: { ...row.result, away_runs: 9 } }))).toBeNull();
    expect(matchingRow(game, withRow({ away: { ...row.away, id: 1 } }))).toBeNull();
    expect(matchingRow(game, null)).toBeNull();
    expect(matchingRow(parseArchiveGame(raw(849802), 849802), { ...INDEX, games: [] })).toBeNull();
  });
});

describe("the neighbors of a game in its series", () => {
  it("finds game 4 before game 5 of the World Series, and nothing after the last game", () => {
    const { previous, next } = seriesNeighbors(INDEX, GAME);

    expect(previous?.game_pk).toBe(INDEX.games.find((row) => row.series.series_name === "World Series" && row.series.game_number === 4)?.game_pk);
    expect(next).toBeNull();
  });

  it("finds nothing before game 1 and the game after it", () => {
    const first = INDEX.games.find((row) => row.series.series_name === "World Series" && row.series.game_number === 1)!;
    const { previous, next } = seriesNeighbors(INDEX, first.game_pk);

    expect(previous).toBeNull();
    expect(next?.series.game_number).toBe(2);
  });

  it("keeps two series of the same round apart (same series name, other clubs)", () => {
    for (const row of INDEX.games) {
      const { previous, next } = seriesNeighbors(INDEX, row.game_pk);
      const pair = (r: typeof row) => [r.away.id, r.home.id].sort().join("-");
      for (const other of [previous, next]) {
        if (other) {
          expect(pair(other), String(row.game_pk)).toBe(pair(row));
          expect(other.series.series_name).toBe(row.series.series_name);
        }
      }
      if (previous) expect(previous.series.game_number).toBe((row.series.game_number ?? 0) - 1);
      if (next) expect(next.series.game_number).toBe((row.series.game_number ?? 0) + 1);
    }
  });

  it("finds no neighbor for a game that is not in the index", () => {
    expect(seriesNeighbors(INDEX, 111111)).toEqual({ previous: null, next: null });
  });
});

describe("the report as published", () => {
  it("reads the sections, the three questions as asked, the lineups and the critic's counts", () => {
    const report = publishedReport(parseArchiveGame(raw(GAME), GAME));

    expect(report.sections.length).toBeGreaterThanOrEqual(5);
    expect(report.sections[0].title).toBe("Matchup Summary");
    expect(report.questions).toHaveLength(3);
    expect(report.questions.every((q) => q.endsWith("?"))).toBe(true);
    expect(report.critic).toEqual({ checked: 7, unsupported: 0, warnings: 1 });
    expect(report.lineups.away?.ops).toBe(".759");
  });

  it("counts the critic's checks of every real file the way the critic's own summary does", () => {
    for (const name of FILES) {
      const pk = Number(name.replace(".json", ""));
      const file = raw(pk);
      const report = publishedReport(parseArchiveGame(file, pk));
      const summary: string = file.payload.matchups[0].critic_review.summary;
      const checked = Number(/checked (\d+) claims/.exec(summary)?.[1]);
      const warnings = /(none|\d+) with a warning/.exec(summary)?.[1];

      expect(report.critic?.checked, name).toBe(checked);
      expect(report.critic?.unsupported, name).toBe(0);
      expect(report.critic?.warnings, name).toBe(warnings === undefined || warnings === "none" ? 0 : Number(warnings));
    }
  });

  it("leaves out a block it cannot read instead of inventing it", () => {
    const game = parseArchiveGame(
      mutate((g) => {
        g.payload.matchups[0].critic_review.checks = "x";
        g.payload.matchups[0].report.sections = [{ title: "Matchup Summary", body: "A sentence." }];
      }),
      GAME,
    );
    const report = publishedReport(game);

    expect(report.critic).toBeNull();
    expect(report.questions).toEqual([]);
    expect(report.sections).toEqual([{ title: "Matchup Summary", body: "A sentence." }]);
  });
});
