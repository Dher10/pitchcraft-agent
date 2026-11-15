import type { ArchiveIndex, ArchiveItem } from "./types";
import { UNAVAILABLE } from "./format";
import { teamLabel } from "./teamLabel";

const ROUNDS = ["Wild Card Series", "Division Series", "League Championship Series", "World Series"];
const SERIES = ["AL Wild Card Series", "NL Wild Card Series", "AL Division Series", "NL Division Series",
  "AL Championship Series", "NL Championship Series", "World Series"];
const REASONS = ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"];
const CHECKS = ["started", "did_not_start", "unknown"];

function requireValue(condition: unknown): asserts condition {
  if (!condition) throw new Error("archive_index_invalid");
}

function object(value: unknown, keys: string[]): Record<string, unknown> {
  requireValue(value !== null && typeof value === "object" && !Array.isArray(value));
  const record = value as Record<string, unknown>;
  requireValue(Object.keys(record).length === keys.length && keys.every((key) => Object.hasOwn(record, key)));
  return record;
}

function count(value: unknown): value is number {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
}

function text(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function choice(value: unknown, values: string[]): value is string {
  return typeof value === "string" && values.includes(value);
}

function day(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const stamp = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(stamp) && new Date(stamp).toISOString().slice(0, 10) === value;
}

/** Validate the whole versioned index before any row becomes presentation data. */
export function parseArchiveIndex(value: unknown): ArchiveIndex {
  const index = object(value, ["archive_version", "season", "veteran_min", "count", "notable_count", "games"]);
  requireValue(index.archive_version === "1.0.0" && index.season === 2026);
  requireValue(count(index.veteran_min) && index.veteran_min >= 1 && index.veteran_min <= 30);
  requireValue(count(index.count) && count(index.notable_count) && Array.isArray(index.games));
  requireValue(index.count === index.games.length);
  const ids = new Set<number>();
  let previous: { date: string; pk: number } | null = null;
  let notableCount = 0;
  for (const item of index.games) {
    const row = object(item, ["game_pk", "date", "season", "round", "series", "away", "home", "status",
      "result", "starters", "report", "notable"]);
    requireValue(count(row.game_pk) && /^[1-9][0-9]{5,8}$/.test(String(row.game_pk)) && !ids.has(row.game_pk));
    ids.add(row.game_pk);
    requireValue(day(row.date) && row.season === 2026 && row.date.startsWith("2026-"));
    requireValue(previous === null || row.date < previous.date || (row.date === previous.date && row.game_pk < previous.pk));
    previous = { date: row.date, pk: row.game_pk };
    requireValue(choice(row.round, ROUNDS) && row.status === "final");
    const series = object(row.series, ["series_name", "game_number", "games_in_series"]);
    requireValue(series.series_name === null || choice(series.series_name, SERIES));
    requireValue(series.game_number === null || (count(series.game_number) && series.game_number >= 1 && series.game_number <= 7));
    requireValue(series.games_in_series === null || (typeof series.games_in_series === "number" && [3, 5, 7].includes(series.games_in_series)));
    if (typeof series.game_number === "number" && typeof series.games_in_series === "number") {
      requireValue(series.game_number <= series.games_in_series);
    }
    for (const side of ["away", "home"]) {
      const team = object(row[side], ["id", "name", "abbreviation"]);
      requireValue(count(team.id) && team.id > 0 && text(team.name));
      requireValue(team.abbreviation === null || text(team.abbreviation));
    }
    const result = object(row.result, ["away_runs", "home_runs", "winner"]);
    requireValue(count(result.away_runs) && count(result.home_runs) && result.away_runs !== result.home_runs);
    requireValue(result.winner === (result.away_runs > result.home_runs ? "away" : "home"));
    const starters = object(row.starters, ["away", "home"]);
    requireValue([starters.away, starters.home].every((name) => name === null || text(name)));
    const report = object(row.report, ["origin", "as_of", "starters_check"]);
    requireValue(choice(report.origin, ["published_live", "reconstructed"]));
    const cutoff = new Date(Date.parse(`${row.date}T00:00:00Z`) - 86400000).toISOString().slice(0, 10);
    requireValue(report.as_of === cutoff);
    const checks = object(report.starters_check, ["away", "home"]);
    requireValue(choice(checks.away, CHECKS) && choice(checks.home, CHECKS));
    requireValue(Array.isArray(row.notable));
    let lastReason = -1;
    for (const reason of row.notable) {
      requireValue(choice(reason, REASONS));
      const position = REASONS.indexOf(reason);
      requireValue(position > lastReason);
      lastReason = position;
    }
    if (row.notable.length > 0) notableCount += 1;
  }
  requireValue(index.notable_count === notableCount);
  return value as ArchiveIndex;
}

/** The approved A2 score phrase; grades are absent from archive version 1.0.0. */
export function archiveIndexItems(index: ArchiveIndex): ArchiveItem[] {
  return index.games.map((row) => ({
    id: String(row.game_pk), date: row.date,
    title: `${row.away.name} vs ${row.home.name}`,
    status: "final", featured: false,
    starter_summary: `${row.starters.away ?? UNAVAILABLE} vs ${row.starters.home ?? UNAVAILABLE}`,
    result_label: `${teamLabel(row.away)} ${row.result.away_runs} - ${teamLabel(row.home)} ${row.result.home_runs}`,
    grade_label: null,
  }));
}
