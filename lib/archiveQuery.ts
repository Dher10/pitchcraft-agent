import { ARCHIVE_COPY } from "@/lib/copy/archive";
import { formatMonthDay } from "@/lib/format";
import { clubNickname } from "@/lib/teams";
import type { ArchiveIndex, ArchiveIndexRow, ArchiveNotableReason } from "@/lib/types";

/**
 * The archive's filters, from the URL and the index alone (docs/plans/R4-U.md, U4). The URL is the state:
 * `/archive?team=MIL&from=2026-10-23&to=2026-10-28&reason=strikeout_duel&month=2026-10&page=2`. Every value is validated
 * against the index; one that is not valid is ignored and never echoed, and nothing that was not validated is written
 * into a link. A game must have every reason picked.
 */

export const PAGE_SIZE = 50;
export const REASON_ORDER: ArchiveNotableReason[] = ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"];

export interface ArchiveQuery {
  team: string | null;
  from: string | null;
  to: string | null;
  reasons: ArchiveNotableReason[];
  page: number;
  month: string | null;
}

type Params = Record<string, string | string[] | undefined>;

const ISO_DAY = /^\d{4}-\d{2}-\d{2}$/;
const MONTH = /^\d{4}-(0[1-9]|1[0-2])$/;
const PAGE = /^[1-9][0-9]{0,3}$/;

const first = (value: string | string[] | undefined): string | undefined => (Array.isArray(value) ? value[0] : value);
const all = (value: string | string[] | undefined): string[] => (value === undefined ? [] : Array.isArray(value) ? value : [value]);

function isRealDay(value: string): boolean {
  if (!ISO_DAY.test(value)) return false;
  const stamp = Date.parse(`${value}T00:00:00Z`);
  return Number.isFinite(stamp) && new Date(stamp).toISOString().slice(0, 10) === value;
}

/** The months of the index, from the first game's to the last game's. */
export function indexMonths(index: ArchiveIndex): string[] {
  const dates = index.games.map((row) => row.date).sort();
  if (dates.length === 0) return [];
  const months: string[] = [];
  let [year, month] = dates[0].slice(0, 7).split("-").map(Number);
  const last = dates[dates.length - 1].slice(0, 7);
  for (;;) {
    const value = `${year}-${String(month).padStart(2, "0")}`;
    months.push(value);
    if (value >= last) break;
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return months;
}

export function pageCount(total: number): number {
  return Math.max(1, Math.ceil(total / PAGE_SIZE));
}

/** Read the URL's parameters against the index. Nothing that is not valid survives. */
export function parseArchiveQuery(params: Params, index: ArchiveIndex): ArchiveQuery {
  const teams = new Set(index.games.flatMap((row) => [row.away.abbreviation, row.home.abbreviation]).filter((t): t is string => t !== null));
  const dates = index.games.map((row) => row.date).sort();
  const inIndex = (day: string) => isRealDay(day) && dates.length > 0 && day >= dates[0] && day <= dates[dates.length - 1];

  const team = first(params.team);
  const from = first(params.from);
  const to = first(params.to);
  const reasons = REASON_ORDER.filter((reason) => all(params.reason).includes(reason));
  const month = first(params.month);

  const query: ArchiveQuery = {
    team: team !== undefined && teams.has(team) ? team : null,
    from: from !== undefined && inIndex(from) ? from : null,
    to: null,
    reasons,
    page: 1,
    month: month !== undefined && MONTH.test(month) && indexMonths(index).includes(month) ? month : null,
  };
  // An end needs a start and may not come before it.
  if (query.from !== null && to !== undefined && inIndex(to) && to >= query.from) query.to = to;

  const page = first(params.page);
  if (page !== undefined && PAGE.test(page) && Number(page) <= pageCount(selectGames(index, query).length)) query.page = Number(page);
  return query;
}

function matches(row: ArchiveIndexRow, query: ArchiveQuery, withReasons: boolean): boolean {
  if (query.team !== null && row.away.abbreviation !== query.team && row.home.abbreviation !== query.team) return false;
  if (query.from !== null && row.date < query.from) return false;
  const end = query.to ?? query.from;
  if (end !== null && row.date > end) return false;
  return !withReasons || query.reasons.every((reason) => row.notable.includes(reason));
}

/** The games that match every filter, newest first as the index has them. */
export function selectGames(index: ArchiveIndex, query: ArchiveQuery): ArchiveIndexRow[] {
  return index.games.filter((row) => matches(row, query, true));
}

/**
 * The count on a reason pill: the games that match the team, the dates and the reasons already picked, and also have this
 * reason. `null` is "Any game": the games that match the team and the dates, without the reasons.
 */
export function reasonCount(index: ArchiveIndex, query: ArchiveQuery, reason: ArchiveNotableReason | null): number {
  if (reason === null) return index.games.filter((row) => matches(row, query, false)).length;
  return index.games.filter((row) => matches(row, query, true) && row.notable.includes(reason)).length;
}

/** The URL of the archive with some filters changed. Fixed parameter order; defaults left out; the page resets unless set. */
export function hrefFor(query: ArchiveQuery, change: Partial<ArchiveQuery>): string {
  const next: ArchiveQuery = { ...query, page: 1, ...change };
  const parts: string[] = [];
  if (next.team !== null) parts.push(`team=${next.team}`);
  if (next.from !== null) parts.push(`from=${next.from}`);
  if (next.to !== null) parts.push(`to=${next.to}`);
  for (const reason of REASON_ORDER) if (next.reasons.includes(reason)) parts.push(`reason=${reason}`);
  if (next.month !== null) parts.push(`month=${next.month}`);
  if (next.page > 1) parts.push(`page=${next.page}`);
  return parts.length === 0 ? "/archive" : `/archive?${parts.join("&")}`;
}

/** The link of a day of the calendar: the first tap picks a day, the second picks the end of the range (a URL remembers the first). */
export function dayHref(query: ArchiveQuery, iso: string): string {
  const month = iso.slice(0, 7);
  if (query.from !== null && query.to === null && iso >= query.from) return hrefFor(query, { to: iso, month });
  return hrefFor(query, { from: iso, to: null, month });
}

export interface CalendarDay {
  iso: string;
  day: number;
  games: number;
  label: string | null;
  href: string | null;
  state: "none" | "range" | "end";
  /** What the chosen days say about this day: the start or the end of a range, or the one day chosen. */
  selection: "start" | "end" | "selected" | null;
  /** Strictly between the start and the end of a range, with or without games (release 2.1.1). */
  inRange: boolean;
}
export type CalendarCell = CalendarDay | { outside: number };

export interface CalendarMonth {
  month: string;
  title: string;
  weekdays: readonly string[];
  cells: CalendarCell[];
  previous: string | null;
  next: string | null;
}

/** The month the calendar shows: the URL's, else the month of the chosen start day, else the month of the last game. */
export function calendarMonth(index: ArchiveIndex, query: ArchiveQuery): CalendarMonth {
  const months = indexMonths(index);
  const month = query.month ?? (query.from !== null ? query.from.slice(0, 7) : months[months.length - 1]);
  const [year, monthNumber] = month.split("-").map(Number);
  const length = new Date(Date.UTC(year, monthNumber, 0)).getUTCDate();
  const lead = new Date(Date.UTC(year, monthNumber - 1, 1)).getUTCDay();
  const previousLength = new Date(Date.UTC(year, monthNumber - 1, 0)).getUTCDate();
  const monthName = ARCHIVE_COPY.months[monthNumber - 1];

  const perDay = new Map<string, number>();
  for (const row of index.games) perDay.set(row.date, (perDay.get(row.date) ?? 0) + 1);
  const end = query.to ?? query.from;

  const cells: CalendarCell[] = [];
  for (let n = lead - 1; n >= 0; n -= 1) cells.push({ outside: previousLength - n });
  for (let day = 1; day <= length; day += 1) {
    const iso = `${month}-${String(day).padStart(2, "0")}`;
    const games = perDay.get(iso) ?? 0;
    const edge = iso === query.from || iso === end;
    const oneDay = query.from !== null && (query.to === null || query.to === query.from);
    const selection = iso === query.from ? (oneDay ? "selected" : "start") : iso === query.to && !oneDay ? "end" : null;
    const between = query.from !== null && end !== null && iso > query.from && iso < end;
    const suffix = selection ? ARCHIVE_COPY.daySelection[selection] : between ? ARCHIVE_COPY.inRange : "";
    const label = games > 0 ? ARCHIVE_COPY.dayLabel(monthName, day, games) + suffix : null;
    cells.push({
      iso,
      day,
      games,
      label,
      href: games > 0 ? dayHref(query, iso) : null,
      state: edge ? "end" : between ? "range" : "none",
      selection,
      inRange: between,
    });
  }
  for (let day = 1; cells.length % 7 !== 0; day += 1) cells.push({ outside: day });

  const at = months.indexOf(month);
  return {
    month,
    title: `${monthName} ${year}`,
    weekdays: ARCHIVE_COPY.weekdays,
    cells,
    previous: at > 0 ? hrefFor(query, { month: months[at - 1], page: 1 }) : null,
    next: at >= 0 && at < months.length - 1 ? hrefFor(query, { month: months[at + 1], page: 1 }) : null,
  };
}

/** What the page says when nothing matches: only what the validated filters support, never a raw value. */
export function noMatchText(index: ArchiveIndex, query: ArchiveQuery): { title: string; body: string } {
  const title = ARCHIVE_COPY.noMatchTitle;
  const tail = ARCHIVE_COPY.tryOther;
  const range = query.from !== null && query.to !== null && query.to !== query.from;
  if (query.team !== null && query.from !== null && query.reasons.length === 0) {
    const row = index.games.find((game) => game.away.abbreviation === query.team || game.home.abbreviation === query.team);
    const name = clubNickname(query.team) ?? (row?.away.abbreviation === query.team ? row.away.name : row?.home.name) ?? query.team;
    const sentence = range
      ? ARCHIVE_COPY.teamDidNotPlayBetween(name, formatMonthDay(query.from), formatMonthDay(query.to as string))
      : ARCHIVE_COPY.teamDidNotPlayOn(name, formatMonthDay(query.from));
    return { title, body: `${sentence} ${tail}` };
  }
  if (query.team === null && query.reasons.length > 0 && range) {
    return { title, body: `${ARCHIVE_COPY.noGameHasEveryReason(formatMonthDay(query.from as string), formatMonthDay(query.to as string))} ${tail}` };
  }
  return { title, body: tail };
}

/**
 * The chosen days in words with their games: "Oct 28, 1 game" or "Oct 23 to Oct 28, 5 games" (release 2.1.1). The count is
 * every index row on those days, whatever the team and the reasons, like the number under each day of the calendar.
 */
export function daysSummary(index: ArchiveIndex, query: ArchiveQuery): string | null {
  const from = query.from;
  if (from === null) return null;
  const to = query.to ?? from;
  const games = index.games.filter((row) => row.date >= from && row.date <= to).length;
  const days = to === from ? formatMonthDay(from) : ARCHIVE_COPY.rangeTo(formatMonthDay(from), formatMonthDay(to));
  return ARCHIVE_COPY.daysSummary(days, games);
}
