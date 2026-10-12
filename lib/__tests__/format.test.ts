import { describe, expect, it } from "vitest";
import { formatFigure, formatStartTime } from "@/lib/format";
import type { Game } from "@/lib/types";

const LIVE: Game = {
  title: "Test game",
  venue: "Yankee Stadium",
  start_time_utc: "2026-07-15T23:05:00Z",
  start_time_local: null,
  timezone: null,
  broadcast_note: null,
  home_team_id: "147",
  away_team_id: "111",
};

describe("formatFigure", () => {
  it.each([["N/A"], [" N/A "], [""], ["  "], [null], [undefined]])("shows %j as a dash", (value) => {
    expect(formatFigure(value)).toBe("—");
  });

  it.each([
    ["3.10", "3.10"],
    ["101.0", "101.0"],
    [0, "0"],
    [110, "110"],
    ["0.00", "0.00"],
  ])("keeps the real figure %j", (value, expected) => {
    expect(formatFigure(value)).toBe(expected);
  });

  it("never turns an unavailable figure into a number", () => {
    for (const value of ["N/A", null, undefined, ""]) {
      expect(formatFigure(value)).not.toMatch(/NaN|0\.0|^0$/);
    }
  });
});

describe("formatStartTime (D33)", () => {
  it.each([
    ["America/New_York", "7:05 PM EDT"],
    ["America/Los_Angeles", "4:05 PM PDT"],
    ["America/Chicago", "6:05 PM CDT"],
    ["America/Phoenix", "4:05 PM MST"],
  ])("converts the UTC instant to the venue zone %s", (timezone, expected) => {
    expect(formatStartTime({ ...LIVE, timezone })).toBe(expected);
  });

  it("shows the instant as UTC when the source gave no zone", () => {
    expect(formatStartTime(LIVE)).toBe("23:05 UTC");
  });

  it.each([["Mars/Olympus"], [""], ["not a zone"]])("falls back to UTC for the unusable zone %j", (timezone) => {
    expect(formatStartTime({ ...LIVE, timezone })).toBe("23:05 UTC");
  });

  it("never uses the zone of the machine that renders it", () => {
    const before = process.env.TZ;
    try {
      for (const machine of ["Asia/Tokyo", "America/Los_Angeles", "UTC"]) {
        process.env.TZ = machine;
        expect(formatStartTime(LIVE)).toBe("23:05 UTC");
        expect(formatStartTime({ ...LIVE, timezone: "America/New_York" })).toBe("7:05 PM EDT");
      }
    } finally {
      if (before === undefined) delete process.env.TZ;
      else process.env.TZ = before;
    }
  });

  it("shows the demo's own pre-formatted time and zone as before", () => {
    const demo: Game = { ...LIVE, start_time_utc: undefined, start_time_local: "7:15 PM", timezone: "America/Los_Angeles" };
    expect(formatStartTime(demo)).toBe("7:15 PM America/Los_Angeles");
  });

  it.each([["garbage"], ["2026-07-15T23:05:00"], [""]])("says the time is unavailable for the bad instant %j, never the demo's", (bad) => {
    expect(formatStartTime({ ...LIVE, start_time_utc: bad, start_time_local: "7:15 PM", timezone: "America/Los_Angeles" })).toBe(
      "Start time not available",
    );
  });

  it("says the time is unavailable when there is nothing to show", () => {
    expect(formatStartTime({ ...LIVE, start_time_utc: null })).toBe("Start time not available");
  });
});
