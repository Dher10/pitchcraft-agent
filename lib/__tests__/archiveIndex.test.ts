// R4-A2: synthetic fixtures imitate data_pipeline/archive_index.py::index_row/build_index.
// They are schema examples, not production records. Expected projections are literal.
import { describe, expect, it } from "vitest";
import { archiveIndexItems, parseArchiveIndex } from "@/lib/archiveIndex";
import type { ArchiveIndex, ArchiveIndexRow } from "@/lib/types";

function makeRow(): ArchiveIndexRow {
  return {
    game_pk: 849806,
    date: "2026-10-10",
    season: 2026,
    round: "Division Series",
    series: { series_name: "NL Division Series", game_number: 2, games_in_series: 5 },
    away: { id: 158, name: "Milwaukee Brewers", abbreviation: "MIL" },
    home: { id: 119, name: "Los Angeles Dodgers", abbreviation: "LAD" },
    status: "final",
    result: { away_runs: 4, home_runs: 0, winner: "away" },
    starters: { away: "Away Starter", home: "Home Starter" },
    report: {
      origin: "reconstructed",
      as_of: "2026-10-09",
      starters_check: { away: "started", home: "unknown" },
    },
    notable: [],
  };
}

function makeIndex(): ArchiveIndex {
  return {
    archive_version: "1.0.0",
    season: 2026,
    veteran_min: 5,
    count: 1,
    notable_count: 0,
    games: [makeRow()],
  };
}

// Fixture mutations only: this helper does not validate, normalize or derive expected output.
function parentAt(value: unknown, path: string): [Record<string, unknown>, string] {
  const keys = path.split(".");
  const last = keys.pop()!;
  let parent = value;
  for (const key of keys) parent = (parent as Record<string, unknown>)[key];
  return [parent as Record<string, unknown>, last];
}

function changed(path: string, value: unknown): unknown {
  const candidate = makeIndex();
  const [parent, key] = parentAt(candidate, path);
  parent[key] = value;
  return candidate;
}

function expectInvalid(value: unknown) {
  // The boundary must not expose malformed values or internal exception text.
  expect(() => parseArchiveIndex(value)).toThrowError(/^archive_index_invalid$/);
}

describe("the archive index boundary", () => {
  it("control: reads the complete producer shape, including a measured score of zero", () => {
    expect(parseArchiveIndex(makeIndex())).toEqual(makeIndex());
  });

  it("control: accepts a valid empty index without inventing rows", () => {
    const empty = { ...makeIndex(), count: 0, notable_count: 0, games: [] };
    expect(archiveIndexItems(parseArchiveIndex(empty))).toEqual([]);
  });

  it("control: accepts the producer's nullable labels and series facts", () => {
    const value = makeIndex();
    value.games[0].away.abbreviation = null;
    value.games[0].home.abbreviation = null;
    value.games[0].starters = { away: null, home: null };
    value.games[0].series = { series_name: null, game_number: null, games_in_series: null };
    expect(parseArchiveIndex(value)).toEqual(value);
  });

  it("control: accepts closed origin/check/reason values without interpreting them as grades", () => {
    const value = makeIndex();
    value.games[0].round = "World Series";
    value.games[0].series = { series_name: "World Series", game_number: 7, games_in_series: 7 };
    value.games[0].home = { id: 139, name: "Tampa Bay Rays", abbreviation: "TB" };
    value.games[0].date = "2026-10-31";
    value.games[0].report.as_of = "2026-10-30";
    value.games[0].report.origin = "published_live";
    value.games[0].report.starters_check = { away: "did_not_start", home: "unknown" };
    value.games[0].notable = ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"];
    value.notable_count = 1;
    expect(archiveIndexItems(parseArchiveIndex(value))[0].grade_label).toBeNull();
  });

  const mandatoryPaths = [
    "archive_version", "season", "veteran_min", "count", "notable_count", "games",
    "games.0.game_pk", "games.0.date", "games.0.season", "games.0.round", "games.0.series",
    "games.0.series.series_name", "games.0.series.game_number", "games.0.series.games_in_series",
    "games.0.away", "games.0.away.id", "games.0.away.name", "games.0.away.abbreviation",
    "games.0.home", "games.0.home.id", "games.0.home.name", "games.0.home.abbreviation",
    "games.0.status", "games.0.result", "games.0.result.away_runs", "games.0.result.home_runs",
    "games.0.result.winner", "games.0.starters", "games.0.starters.away", "games.0.starters.home",
    "games.0.report", "games.0.report.origin", "games.0.report.as_of", "games.0.report.starters_check",
    "games.0.report.starters_check.away", "games.0.report.starters_check.home", "games.0.notable",
  ];

  it.each(mandatoryPaths)("rejects a missing mandatory field: %s", (path) => {
    const value = makeIndex();
    const [parent, key] = parentAt(value, path);
    delete parent[key];
    expectInvalid(value);
  });

  it.each([
    ["null", null], ["array", []], ["text", "not an index"],
  ])("rejects a non-object document: %s", (_label, value) => {
    expectInvalid(value);
  });

  const invalidValues: Array<[string, unknown]> = [
    ["archive_version", "1.0.1"],
    ["season", 2025],
    ["veteran_min", 0],
    ["veteran_min", 31],
    ["veteran_min", true],
    ["veteran_min", 5.5],
    ["count", true],
    ["count", 1.5],
    ["notable_count", false],
    ["notable_count", 0.5],
    ["games", {}],
    ["games.0", null],
    ["games.0.game_pk", "849806"],
    ["games.0.game_pk", 849806.5],
    ["games.0.game_pk", 0],
    ["games.0.date", "2026-02-30"],
    ["games.0.date", "2026-10-1"],
    ["games.0.season", true],
    ["games.0.season", 2025],
    ["games.0.round", "Postseason"],
    ["games.0.series.series_name", "an unknown series"],
    ["games.0.series.game_number", true],
    ["games.0.series.game_number", 1.5],
    ["games.0.series.games_in_series", 4],
    ["games.0.away", []],
    ["games.0.away.id", 0],
    ["games.0.home.id", true],
    ["games.0.home.name", ""],
    ["games.0.away.abbreviation", ""],
    ["games.0.home.abbreviation", 139],
    ["games.0.status", "live"],
    ["games.0.result", false],
    ["games.0.result.away_runs", true],
    ["games.0.result.home_runs", null],
    ["games.0.result.home_runs", -1],
    ["games.0.result.home_runs", 0.5],
    ["games.0.result.winner", "home"],
    ["games.0.starters.away", "   "],
    ["games.0.starters.home", 0],
    ["games.0.report.origin", "demo"],
    ["games.0.report.as_of", "2026-10-10"],
    ["games.0.report.as_of", "2026-10-08"],
    ["games.0.report.as_of", "2026-02-30"],
    ["games.0.report.starters_check.away", "probably_started"],
    ["games.0.notable", ["a new reason"]],
    ["games.0.notable", ["veteran_duel", "veteran_duel"]],
    ["games.0.notable", ["veteran_duel", "strikeout_duel"]],
  ];

  it.each(invalidValues)("rejects an invalid value at %s: %j", (path, value) => {
    expectInvalid(changed(path, value));
  });

  it("rejects a tied score even when the winner label is otherwise known", () => {
    const value = makeIndex();
    value.games[0].result = { away_runs: 0, home_runs: 0, winner: "away" };
    expectInvalid(value);
  });

  it("rejects a row whose date is outside the index season", () => {
    const value = makeIndex();
    value.games[0].date = "2025-10-10";
    value.games[0].report.as_of = "2025-10-09";
    expectInvalid(value);
  });

  it("rejects count and notable_count that contradict the actual rows", () => {
    expectInvalid(changed("count", 0));
    expectInvalid(changed("notable_count", 1));
  });

  it("rejects duplicate ids even when dates differ", () => {
    const value = makeIndex();
    value.count = 2;
    value.games.push({ ...makeRow(), date: "2026-10-09", report: { ...makeRow().report, as_of: "2026-10-08" } });
    expectInvalid(value);
  });

  it("rejects ascending dates instead of sorting an invalid index into validity", () => {
    const value = makeIndex();
    value.count = 2;
    value.games.push({ ...makeRow(), game_pk: 849807, date: "2026-10-11", report: { ...makeRow().report, as_of: "2026-10-10" } });
    expectInvalid(value);
  });

  it("rejects ascending ids within the same date", () => {
    const value = makeIndex();
    value.count = 2;
    value.games.push({ ...makeRow(), game_pk: 849807 });
    expectInvalid(value);
  });

  it("rejects additional family/row fields, including an invented public grade", () => {
    expectInvalid({ ...makeIndex(), grade: "A" });
    const value = makeIndex();
    Object.assign(value.games[0], { grade: "A" });
    expectInvalid(value);
  });
});

describe("the archive index projection", () => {
  it("projects final source scores into existing archive items without adding a grade", () => {
    expect(archiveIndexItems(parseArchiveIndex(makeIndex()))).toEqual([{
      id: "849806",
      date: "2026-10-10",
      title: "Milwaukee Brewers vs Los Angeles Dodgers",
      status: "final",
      featured: false,
      starter_summary: "Away Starter vs Home Starter",
      result_label: "MIL 4 - LAD 0",
      grade_label: null,
    }]);
  });

  it.each([
    [null, "ZZZ", "Milwaukee Brewers 4 - ZZZ 0"],
    ["ZZZ", null, "ZZZ 4 - Los Angeles Dodgers 0"],
  ] as const)("uses team-name fallback on either side and preserves unknown nonnull labels: %j / %j", (away, home, expected) => {
    const value = makeIndex();
    value.games[0].away.abbreviation = away;
    value.games[0].home.abbreviation = home;
    expect(archiveIndexItems(parseArchiveIndex(value))[0]).toMatchObject({
      title: "Milwaukee Brewers vs Los Angeles Dodgers",
      result_label: expected,
    });
  });

  it.each([
    [null, "Home Starter", "— vs Home Starter"],
    ["Away Starter", null, "Away Starter vs —"],
    [null, null, "— vs —"],
  ] as const)("shows unavailable starter names without guessing: %j / %j", (away, home, expected) => {
    const value = makeIndex();
    value.games[0].starters = { away, home };
    expect(archiveIndexItems(parseArchiveIndex(value))[0].starter_summary).toBe(expected);
  });

  it("keeps newest-first rows and their distinct scores without mutating the parsed index", () => {
    const value = makeIndex();
    value.count = 2;
    value.games.push({
      ...makeRow(), game_pk: 849805,
      result: { away_runs: 0, home_runs: 2, winner: "home" },
    });
    const parsed = parseArchiveIndex(value);
    const before = structuredClone(parsed);
    expect(archiveIndexItems(parsed).map((item) => [item.id, item.result_label])).toEqual([
      ["849806", "MIL 4 - LAD 0"],
      ["849805", "MIL 0 - LAD 2"],
    ]);
    expect(parsed).toEqual(before);
  });
});
