// R4-A2: mock only fs.promises.readFile. Home, reader, parser, App and table stay real.
import { afterAll, afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, within } from "@testing-library/react";
import { promises as fs } from "fs";
import path from "path";
import Home from "@/app/page";
import { getArchiveItems } from "@/lib/data";
import type { ArchiveIndex, ArchiveItem, PitchCraftData } from "@/lib/types";
import demo from "@/tests/fixtures/served_demo_0.9.0.json";

const dailyPath = path.join(process.cwd(), "public", "data", "pitchcraft-demo.json");
const indexPath = path.join(process.cwd(), "public", "data", "archive", "index-2026.json");
const originalReadFile = fs.readFile;
const readFileMock = vi.spyOn(fs, "readFile");

beforeEach(() => {
  readFileMock.mockReset();
  readFileMock.mockImplementation(originalReadFile);
});
afterEach(() => vi.useRealTimers());
afterAll(() => readFileMock.mockRestore());

const legacyRow: ArchiveItem = {
  id: "legacy_001",
  date: "2026-09-20",
  title: "Boston Red Sox vs New York Yankees",
  status: "upcoming",
  featured: true,
  starter_summary: "Legacy Away vs Legacy Home",
  result_label: null,
  grade_label: null,
};

function dailyFile(archive: ArchiveItem[] = [legacyRow]): PitchCraftData {
  // Read-only import, cloned before editing. No published JSON is written.
  const value = structuredClone(demo) as unknown as PitchCraftData;
  value.featured_matchup_id = null;
  value.matchups = [];
  value.archive = structuredClone(archive);
  return value;
}

function indexFile(): ArchiveIndex {
  // The complete shape emitted by data_pipeline/archive_index.py. Synthetic, not real results.
  return {
    archive_version: "1.0.0",
    season: 2026,
    veteran_min: 5,
    count: 2,
    notable_count: 1,
    games: [{
      game_pk: 849806,
      date: "2026-10-10",
      season: 2026,
      round: "Division Series",
      series: { series_name: "NL Division Series", game_number: 2, games_in_series: 5 },
      away: { id: 158, name: "Milwaukee Brewers", abbreviation: "MIL" },
      home: { id: 119, name: "Los Angeles Dodgers", abbreviation: "LAD" },
      status: "final",
      result: { away_runs: 4, home_runs: 0, winner: "away" },
      starters: { away: "Indexed Away", home: "Indexed Home" },
      report: { origin: "reconstructed", as_of: "2026-10-09", starters_check: { away: "started", home: "started" } },
      notable: ["strikeout_duel"],
    }, {
      game_pk: 849805,
      date: "2026-10-09",
      season: 2026,
      round: "Division Series",
      series: { series_name: "NL Division Series", game_number: 1, games_in_series: 5 },
      away: { id: 158, name: "Milwaukee Brewers", abbreviation: null },
      home: { id: 119, name: "Los Angeles Dodgers", abbreviation: "LAD" },
      status: "final",
      result: { away_runs: 0, home_runs: 2, winner: "home" },
      starters: { away: null, home: "Earlier Home" },
      report: { origin: "published_live", as_of: "2026-10-08", starters_check: { away: "unknown", home: "did_not_start" } },
      notable: [],
    }],
  };
}

function ioError(code?: string): NodeJS.ErrnoException {
  return Object.assign(new Error("internal_test_path_must_not_become_archive_content"), code ? { code } : {});
}

function serve(index: string | Error, daily: PitchCraftData = dailyFile()) {
  readFileMock.mockImplementation(async (file, options) => {
    const target = String(file);
    if (target === dailyPath) return JSON.stringify(daily);
    if (target === indexPath) {
      if (index instanceof Error) throw index;
      return index;
    }
    // Vite/React may read their own modules during rendering. Only the two
    // application data paths are the controlled external boundary here.
    return originalReadFile(file, options);
  });
}

async function renderHome() {
  return render(await Home({ searchParams: Promise.resolve({}) }));
}

function archiveSection(container: HTMLElement): HTMLElement {
  const section = within(container).getByRole("heading", { name: "Archive", level: 2 }).closest("section");
  expect(section).not.toBeNull();
  return section!;
}

function cells(section: HTMLElement): Array<Array<string | null>> {
  return Array.from(section.querySelectorAll("tbody tr"), (row) =>
    Array.from(row.querySelectorAll("td"), (cell) => cell.textContent));
}

describe("the server archive reader", () => {
  it("reads the versioned 2026 index and projects each final score", async () => {
    serve(JSON.stringify(indexFile()));

    const items = await getArchiveItems();

    expect(readFileMock).toHaveBeenCalledWith(indexPath, "utf-8");
    expect(items).toMatchObject([
      { id: "849806", result_label: "MIL 4 - LAD 0", grade_label: null },
      { id: "849805", result_label: "Milwaukee Brewers 0 - LAD 2", grade_label: null },
    ]);
  });

  it("returns null only for ENOENT so the consumer can retain the daily archive", async () => {
    serve(ioError("ENOENT"));
    await expect(getArchiveItems()).resolves.toBeNull();
  });

  it.each(["EACCES", "EISDIR", "EIO", "ENOTDIR", undefined])(
    "fails closed for an existing/unreadable index instead of returning missing: %s",
    async (code) => {
      serve(ioError(code));
      await expect(getArchiveItems()).rejects.toThrow();
    },
  );

  it.each([
    ["invalid JSON", "{ private_broken_payload"],
    ["invalid shape", JSON.stringify({ archive_version: "1.0.0", games: [] })],
    ["unknown version", JSON.stringify({ ...indexFile(), archive_version: "2.0.0" })],
  ])("rejects an existing %s with the closed boundary error", async (_label, text) => {
    serve(text);
    await expect(getArchiveItems()).rejects.toThrowError(/^archive_index_invalid$/);
  });
});

describe("the real Home/App archive integration", () => {
  it("shows the season in review, not the interim table, in the off season with the index there (R4-U6)", async () => {
    serve(JSON.stringify(indexFile()));

    const { container } = await renderHome();

    expect(container.querySelector("h1")?.textContent).toBe("The 2026 postseason, start by start");
    expect(container.textContent).toContain("Browse all 2 games");
    expect(container.querySelector("table")).toBeNull();
    expect(container.querySelector('[data-mode="live"]')).toBeNull();
    expect(container.textContent).not.toContain("Boston Red Sox");
    expect(readFileMock).toHaveBeenCalledWith(indexPath, "utf-8");
  });

  it("keeps the daily view in season: every indexed final score, Grade hidden, rows unlinked (the interim home, R4-A2)", async () => {
    // A live day in season (clock fixed) is not the off season, so the daily view and its interim table stay.
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date("2026-10-28T16:00:00Z"));
    const live = dailyFile();
    live.metadata.data_mode = "fetched_snapshot";
    live.metadata.data_status = {
      mode: "fetched_snapshot",
      reason: null,
      live_run: {
        status: "ok", run_at: "2026-10-28T15:00:00+00:00", target_date: "2026-10-28", as_of: "2026-10-27",
        games_scheduled: 1, games_live: 1, errors: [], warnings: [],
      },
    };
    serve(JSON.stringify(indexFile()), live);

    const { container } = await renderHome();
    const section = archiveSection(container);

    expect(readFileMock).toHaveBeenCalledWith(dailyPath, "utf-8");
    expect(readFileMock).toHaveBeenCalledWith(indexPath, "utf-8");
    expect(Array.from(section.querySelectorAll("th"), (cell) => cell.textContent)).toEqual([
      "Date", "Matchup", "Starters", "Result",
    ]);
    expect(cells(section)).toEqual([
      ["2026-10-10", "Milwaukee Brewers vs Los Angeles Dodgers", "Indexed Away vs Indexed Home", "MIL 4 - LAD 0"],
      ["2026-10-09", "Milwaukee Brewers vs Los Angeles Dodgers", "— vs Earlier Home", "Milwaukee Brewers 0 - LAD 2"],
    ]);
    expect(section.textContent).not.toContain("Boston Red Sox");
    expect(section.textContent).not.toContain("Pending");
    expect(section.querySelectorAll("a")).toHaveLength(0);
    expect(section.querySelectorAll("button")).toHaveLength(0);
    expect(section.textContent).not.toMatch(/featured|recommended/i);
    expect(container.querySelector("h1")?.textContent).not.toBe("The 2026 postseason, start by start");
  });

  it("keeps an existing empty index empty instead of falling back to nonempty daily rows", async () => {
    serve(JSON.stringify({ ...indexFile(), count: 0, notable_count: 0, games: [] }));

    await expect(getArchiveItems()).resolves.toEqual([]);
    const { container } = await renderHome();
    const section = archiveSection(container);

    expect(section.textContent).toContain("No past reports yet");
    expect(section.querySelector("table")).toBeNull();
    expect(section.textContent).not.toContain("Boston Red Sox");
  });

  it("control: a missing index preserves the exact legacy five-column and dash behavior", async () => {
    serve(ioError("ENOENT"));

    const { container } = await renderHome();
    const section = archiveSection(container);

    expect(Array.from(section.querySelectorAll("th"), (cell) => cell.textContent)).toEqual([
      "Date", "Matchup", "Starters", "Result", "Grade",
    ]);
    expect(cells(section)).toEqual([
      ["2026-09-20", "Boston Red Sox vs New York Yankees", "Legacy Away vs Legacy Home", "—", "—"],
    ]);
    expect(section.textContent).not.toContain("Pending");
    expect(section.querySelectorAll("a")).toHaveLength(0);
  });

  it("control: missing-index fallback retains Pending for a legacy result with no grade", async () => {
    serve(ioError("ENOENT"), dailyFile([{ ...legacyRow, result_label: "BOS 5 - NYY 3" }]));

    const { container } = await renderHome();

    expect(cells(archiveSection(container))).toEqual([
      ["2026-09-20", "Boston Red Sox vs New York Yankees", "Legacy Away vs Legacy Home", "BOS 5 - NYY 3", "Pending"],
    ]);
  });

  it.each([
    ["malformed JSON", "{"],
    ["invalid complete row", JSON.stringify({ ...indexFile(), games: [null, null] })],
    ["unsupported version", JSON.stringify({ ...indexFile(), archive_version: "2.0.0" })],
  ])("fails Home closed for an existing %s instead of rendering the daily fallback", async (_label, text) => {
    serve(text);
    await expect(Home({ searchParams: Promise.resolve({}) })).rejects.toThrowError(/^archive_index_invalid$/);
  });

  it("fails Home closed for a filesystem failure instead of rendering daily rows", async () => {
    serve(ioError("EACCES"));
    await expect(Home({ searchParams: Promise.resolve({}) })).rejects.toThrow();
  });
});
