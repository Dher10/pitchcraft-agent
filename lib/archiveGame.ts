import { promises as fs } from "node:fs";
import path from "node:path";
import { clubNickname } from "@/lib/teams";
import { formatDay, newYorkDay } from "@/lib/format";
import { GAME_COPY } from "@/lib/copy/game";
import type { ArchiveFinalLine, ArchiveGameFile, ArchiveIndex, ArchiveIndexRow, ArchiveStarterCheck } from "@/lib/types";

/**
 * The reader of a game file of archive_version 1.0.0 (D66, R4 4.4). Nothing is presented before the whole envelope is
 * validated: exact keys, types, the score and its winner, the origin and its date, the starter checks and the final lines.
 * A file that fails is refused with one closed code (rule 8), never with the text of the failure. The id is checked before
 * any file is touched, and no path is ever built from anything but that validated id.
 */

const ROUNDS = ["Wild Card Series", "Division Series", "League Championship Series", "World Series"];
const CHECKS = ["started", "did_not_start", "unknown"];
const KEYS = ["archive_version", "game_pk", "season", "date", "round", "series", "teams", "result", "origin", "starters_check",
  "starter_facts", "final_line", "payload"];
const GAME_PK = /^[1-9][0-9]{5,8}$/;
const INNINGS = /^[0-9]{1,2}(?:\.[0-2])?$/;
const INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

// A JSON value read from a file whose shape is checked field by field below: one named alias, not scattered `any`.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Loose = Record<string, any>;

const invalid = (): never => {
  throw new Error("archive_game_invalid");
};
const need = (condition: unknown): void => {
  if (!condition) invalid();
};

function record(value: unknown, keys?: string[]): Loose {
  need(value !== null && typeof value === "object" && !Array.isArray(value));
  const found = value as Loose;
  if (keys) need(Object.keys(found).length === keys.length && keys.every((key) => Object.hasOwn(found, key)));
  return found;
}

const count = (value: unknown): value is number => typeof value === "number" && Number.isSafeInteger(value) && value >= 0;
const text = (value: unknown): value is string => typeof value === "string" && value.trim().length > 0;

function day(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const stamp = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(stamp) && new Date(stamp).toISOString().slice(0, 10) === value;
}

/** Is this string the id of a game (the MLB `gamePk`)? Checked before any file is touched. */
export function isGamePk(id: string): boolean {
  return GAME_PK.test(id);
}

function finalLine(value: unknown): ArchiveFinalLine | null {
  if (value === null) return null;
  const line = record(value, ["innings_pitched", "hits", "earned_runs", "walks", "strikeouts"]);
  need(line.innings_pitched === null || (typeof line.innings_pitched === "string" && INNINGS.test(line.innings_pitched)));
  for (const key of ["hits", "earned_runs", "walks", "strikeouts"]) need(line[key] === null || count(line[key]));
  return line as ArchiveFinalLine;
}

function starter(value: unknown) {
  if (value === null) return null;
  const who = record(value, ["id", "name"]);
  need(count(who.id) && who.id > 0 && text(who.name));
  return who as { id: number; name: string };
}

/** Validate a game file. `expectedPk` is the id of the route: a file that is another game is refused. */
export function parseArchiveGame(value: unknown, expectedPk?: number): ArchiveGameFile {
  try {
    const game = record(value, KEYS);
    need(game.archive_version === "1.0.0" && game.season === 2026);
    need(count(game.game_pk) && GAME_PK.test(String(game.game_pk)));
    if (expectedPk !== undefined) need(game.game_pk === expectedPk);
    need(day(game.date) && game.date.startsWith("2026-"));
    need(ROUNDS.includes(game.round));

    const series = record(game.series, ["series_name", "game_number", "games_in_series", "over", "after"]);
    need(text(series.series_name) && count(series.game_number) && series.game_number >= 1 && series.game_number <= 7);
    need(series.games_in_series === null || [3, 5, 7].includes(series.games_in_series));
    need(typeof series.over === "boolean" && (series.after === null || text(series.after)));

    const teams = record(game.teams, ["away", "home"]);
    for (const side of ["away", "home"]) {
      const team = record(teams[side], ["id", "name"]);
      need(count(team.id) && team.id > 0 && text(team.name));
    }

    const result = record(game.result, ["away_runs", "home_runs", "status", "winner"]);
    need(result.status === "final" && count(result.away_runs) && count(result.home_runs) && result.away_runs !== result.home_runs);
    need(result.winner === (result.away_runs > result.home_runs ? "away" : "home"));

    const origin = record(game.origin, ["as_of", "built_at", "kind", "published_at", "source"]);
    need(origin.kind === "published_live" || origin.kind === "reconstructed");
    need(day(origin.as_of) && origin.as_of === new Date(Date.parse(`${game.date}T00:00:00Z`) - 86400000).toISOString().slice(0, 10));
    need(typeof origin.built_at === "string" && INSTANT.test(origin.built_at));
    need(origin.kind === "published_live" ? typeof origin.published_at === "string" && INSTANT.test(origin.published_at) : origin.published_at === null);
    if (origin.source !== null) {
      const source = record(origin.source, ["commit", "sha256"]);
      need(text(source.commit) && text(source.sha256));
    }

    const checks = record(game.starters_check, ["away", "home", "actual"]);
    const actual = record(checks.actual, ["away", "home"]);
    for (const side of ["away", "home"]) {
      need(CHECKS.includes(checks[side]));
      const who = starter(actual[side]);
      // A starter the box score could not name is `unknown` and has no name; every other check has the pitcher who started.
      need(checks[side] === "unknown" ? who === null : who !== null);
    }

    const lines = record(game.final_line, ["away", "home"]);
    for (const side of ["away", "home"] as const) {
      const line = finalLine(lines[side]);
      // A starter the box score could not name has no line; every other starter's line is a line or null.
      need(checks[side] !== "unknown" || line === null);
    }

    const payload = record(game.payload);
    need(Array.isArray(payload.matchups) && payload.matchups.length === 1);
    record(payload.matchups[0]);
    return game as ArchiveGameFile;
  } catch {
    throw new Error("archive_game_invalid");
  }
}

type Read = (file: string) => Promise<string>;
const readUtf8: Read = (file) => fs.readFile(file, "utf-8");

/**
 * The validated game for the id of a route, or `null` when it is not there: an id that does not match the pattern (no
 * file is touched), no such file, a file that is not JSON or not valid, or a file that is another game. Never an error.
 */
export async function loadArchiveGame(id: string, read: Read = readUtf8): Promise<ArchiveGameFile | null> {
  if (!isGamePk(id)) return null;
  try {
    const file = path.join(process.cwd(), "public", "data", "archive", "games", `${id}.json`);
    return parseArchiveGame(JSON.parse(await read(file)), Number(id));
  } catch {
    return null;
  }
}

/** The index row of a game, only when it agrees with the game file on the date, the clubs and the score (else it is not used). */
export function matchingRow(game: ArchiveGameFile, index: ArchiveIndex | null): ArchiveIndexRow | null {
  const row = index?.games.find((candidate) => candidate.game_pk === game.game_pk) ?? null;
  if (row === null) return null;
  const agrees =
    row.date === game.date &&
    row.away.id === game.teams.away.id &&
    row.home.id === game.teams.home.id &&
    row.result.away_runs === game.result.away_runs &&
    row.result.home_runs === game.result.home_runs;
  return agrees ? row : null;
}

/** The games before and after a game in its own series: same series name, same two clubs, the game numbers around it. */
export function seriesNeighbors(index: ArchiveIndex, gamePk: number): { previous: ArchiveIndexRow | null; next: ArchiveIndexRow | null } {
  const row = index.games.find((game) => game.game_pk === gamePk);
  if (!row || row.series.series_name === null || row.series.game_number === null) return { previous: null, next: null };
  const pair = (game: ArchiveIndexRow) => [game.away.id, game.home.id].sort((a, b) => a - b).join("-");
  const same = index.games.filter(
    (game) => game.series.series_name === row.series.series_name && game.round === row.round && pair(game) === pair(row),
  );
  const at = (n: number) => same.find((game) => game.series.game_number === n) ?? null;
  return { previous: at(row.series.game_number - 1), next: at(row.series.game_number + 1) };
}

// ---------------------------------------------------------------------------------------------------------------
// What the page reads from the embedded payload. Only the report block uses these; each reader leaves out what it cannot
// read, instead of inventing it (a whole optional block unavailable is omitted without comment).
// ---------------------------------------------------------------------------------------------------------------

export interface ReportSection {
  title: string;
  body?: string;
  bullets?: string[];
}

export interface Lineup {
  ops: string | null;
  k_rate: string | null;
  bb_rate: string | null;
  vs_hand: string | null;
  scope: string | null;
}

export interface PublishedReport {
  sections: ReportSection[];
  questions: string[];
  lineups: { away: Lineup | null; home: Lineup | null };
  critic: { checked: number; unsupported: number; warnings: number } | null;
}

function matchup(game: ArchiveGameFile): Loose {
  return (game.payload.matchups as Loose[])[0];
}

const stringOrNull = (value: unknown): string | null => (typeof value === "string" && value.trim() !== "" ? value : null);

function lineup(team: unknown): Lineup | null {
  if (team === null || typeof team !== "object") return null;
  const profile = (team as Loose).offense_profile;
  if (profile === null || typeof profile !== "object") return null;
  const scope = profile.scope && typeof profile.scope === "object" ? stringOrNull(profile.scope.label) : null;
  return {
    ops: stringOrNull(profile.ops_vs_hand),
    k_rate: stringOrNull(profile.k_rate_vs_hand),
    bb_rate: stringOrNull(profile.bb_rate_vs_hand),
    vs_hand: stringOrNull(profile.vs_pitcher_hand),
    scope,
  };
}

/** The report as it was written: its sections, the questions it asked, the lineups it described and the critic's counts. */
export function publishedReport(game: ArchiveGameFile): PublishedReport {
  const m = matchup(game);
  const sections: ReportSection[] = [];
  for (const section of Array.isArray(m.report?.sections) ? m.report.sections : []) {
    if (section === null || typeof section !== "object" || !text(section.title)) continue;
    const entry: ReportSection = { title: section.title };
    if (typeof section.body === "string" && section.body.trim() !== "") entry.body = section.body;
    if (Array.isArray(section.bullets) && section.bullets.every((bullet: unknown) => typeof bullet === "string")) entry.bullets = section.bullets;
    if (entry.body !== undefined || entry.bullets !== undefined) sections.push(entry);
  }
  const questions = sections.flatMap((section) => section.bullets ?? []).filter((bullet) => bullet.trim().endsWith("?"));

  const checks = m.critic_review?.checks;
  let critic: PublishedReport["critic"] = null;
  if (Array.isArray(checks) && checks.every((check: Loose) => check && typeof check === "object" && typeof check.status === "string")) {
    critic = {
      checked: checks.length,
      unsupported: checks.filter((check: Loose) => check.status === "unsupported").length,
      warnings: checks.filter((check: Loose) => check.status === "warning").length,
    };
  }
  return { sections, questions, lineups: { away: lineup(m.teams?.away), home: lineup(m.teams?.home) }, critic };
}

/** The venue the schedule named, or `null` (then the line simply has none). */
export function gameVenue(game: ArchiveGameFile): string | null {
  return stringOrNull(matchup(game).game?.venue);
}

/** The probable starter the report was about, with the hand and style label the report gave him. */
export function reportStarter(game: ArchiveGameFile, side: "away" | "home") {
  const starter = matchup(game).starters?.[`${side}_starter`];
  const hand = typeof starter?.throws === "string" ? starter.throws.toUpperCase().charAt(0) : "";
  return {
    name: stringOrNull(starter?.name),
    hand: hand === "L" || hand === "R" ? (hand as "L" | "R") : null,
    style: stringOrNull(starter?.pitching_profile?.style_label),
    team: stringOrNull(matchup(game).teams?.[side]?.abbreviation),
  };
}

/** The abbreviation of a club of this game, from the index row when there is one, else from the report. */
export function clubAbbreviation(game: ArchiveGameFile, row: ArchiveIndexRow | null, side: "away" | "home"): string | null {
  return row?.[side].abbreviation ?? reportStarter(game, side).team;
}

/** The nickname the page uses for a side, or the full name when the club is not in the closed table. */
export function sideName(game: ArchiveGameFile, row: ArchiveIndexRow | null, side: "away" | "home"): string {
  return clubNickname(clubAbbreviation(game, row, side)) ?? game.teams[side].name;
}

/** The day the report was published, in New York (the zone of a game's official date). */
export function publishedDay(game: ArchiveGameFile): string | null {
  return game.origin.published_at ? newYorkDay(game.origin.published_at) : null;
}

/**
 * The sentence about the series, from the envelope's series line and in the closed forms only ("MIL wins 4-1", "MIL leads
 * 3-1", "Series tied 2-2"); a line that is not one of them, or a club that is not in the table, says nothing.
 */
export function seriesSentence(game: ArchiveGameFile): string | null {
  const after = game.series.after;
  if (after === null) return null;
  const tied = /^Series tied (\d)-(\d)$/.exec(after);
  if (tied) return GAME_COPY.seriesTied(Number(tied[1]), Number(tied[2]));
  const lead = /^([A-Z]{2,3}) (wins|leads) (\d)-(\d)$/.exec(after);
  const name = lead ? clubNickname(lead[1]) : null;
  if (!lead || name === null) return null;
  return lead[2] === "wins" ? GAME_COPY.seriesWon(name, Number(lead[3]), Number(lead[4])) : GAME_COPY.seriesLed(name, Number(lead[3]), Number(lead[4]));
}

export function gameMetadata(game: ArchiveGameFile, row: ArchiveIndexRow | null = null): { title: string; description: string } {
  const away = sideName(game, row, "away");
  const home = sideName(game, row, "home");
  return {
    title: GAME_COPY.pageTitle(away, home, game.round, game.series.game_number, formatDay(game.date)),
    description: GAME_COPY.pageDescription(away, game.result.away_runs, home, game.result.home_runs),
  };
}

export type { ArchiveStarterCheck };
