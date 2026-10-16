import type { Game } from "@/lib/types";

/** The dash shown wherever a figure is not available. */
export const UNAVAILABLE = "—";

/**
 * A season figure for display. "N/A", an empty string, null and undefined are all
 * "not available" and show as a dash; nothing is ever parsed into a number here.
 */
export function formatFigure(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return UNAVAILABLE;
  const text = String(value).trim();
  return text === "" || text === "N/A" ? UNAVAILABLE : text;
}

/** Only a hand the data gives is shown: anything else (a switch pitcher, a missing value) names no hand. */
export function throwingHand(raw: string | null | undefined): "L" | "R" | null {
  const hand = raw?.toUpperCase().charAt(0);
  return hand === "L" || hand === "R" ? hand : null;
}

export const START_TIME_UNAVAILABLE = "Start time not available";

const UTC_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;

/**
 * The start of a game for display (D33).
 *
 * A live game carries `start_time_utc`: it is shown in the venue's IANA zone when the source gave one
 * ("7:05 PM EDT") and as UTC otherwise ("23:05 UTC"). The zone is always explicit, never the one of the
 * browser or the server that renders it, and never one taken from demo data. A live game whose instant
 * is not a valid UTC instant says the time is not available. A demo game has no instant and shows its
 * own pre-formatted time and zone.
 */
export function formatStartTime(game: Pick<Game, "start_time_utc" | "start_time_local" | "timezone">): string {
  const instant = game.start_time_utc;
  if (instant !== undefined && instant !== null) {
    const date = UTC_INSTANT.test(instant) ? new Date(instant) : null;
    if (date === null || Number.isNaN(date.getTime())) return START_TIME_UNAVAILABLE;
    const zoned = game.timezone ? inZone(date, game.timezone) : null;
    return zoned ?? `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())} UTC`;
  }
  if (game.start_time_local) {
    return game.timezone ? `${game.start_time_local} ${game.timezone}` : game.start_time_local;
  }
  return START_TIME_UNAVAILABLE;
}

function inZone(date: Date, timeZone: string): string | null {
  try {
    return new Intl.DateTimeFormat("en-US", { timeZone, hour: "numeric", minute: "2-digit", timeZoneName: "short" })
      .format(date)
      .replace(/[  ]/g, " ");
  } catch {
    return null; // not a zone this runtime knows: fall back to UTC
  }
}

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export const MODE_LINE_DEMO = "Demo data: live data unavailable";
export const MODE_LINE_FETCH_UNKNOWN = "Live data · fetch time not available";

const ISO_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/;

/** The day of an instant in America/New_York (D29's zone), written YYYY-MM-DD; null when it is not an instant. */
function newYorkDay(instant: string | null | undefined): string | null {
  if (typeof instant !== "string" || !ISO_INSTANT.test(instant)) return null;
  const date = new Date(instant);
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }).format(date);
}

/**
 * The line that says what the page shows (contract rule 6). Live only for `fetched_snapshot`, with the day the data was
 * fetched in New York; every other mode, known or not, is demo data. The date is never the browser's or the server's.
 */
export function formatModeLine(dataMode: string, fetchedAt: string | null | undefined): string {
  if (dataMode !== "fetched_snapshot") return MODE_LINE_DEMO;
  const day = newYorkDay(fetchedAt);
  return day ? `Live data · fetched ${day}` : MODE_LINE_FETCH_UNKNOWN;
}
