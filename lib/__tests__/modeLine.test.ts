import { describe, expect, it } from "vitest";
import { formatModeLine, MODE_LINE_DEMO, MODE_LINE_FETCH_UNKNOWN } from "@/lib/format";

// P0.15-D2.4b (F3, contract rule 6 and 3.3): the page says whether it shows live or demo data. It says "live" only for
// `fetched_snapshot`; the date is the day of the fetch in America/New_York (D29's zone), never the one of the machine
// that renders it.

describe("the mode line", () => {
  it("says the data is live and when it was fetched, in New York time", () => {
    expect(formatModeLine("fetched_snapshot", "2026-07-04T12:00:00Z")).toBe("Live data · fetched 2026-07-04");
  });

  it("uses the New York date, not the UTC one: 01:30 UTC on the 5th is still the 4th there", () => {
    expect(formatModeLine("fetched_snapshot", "2026-07-05T01:30:00Z")).toBe("Live data · fetched 2026-07-04");
  });

  it("reads an instant written with an offset", () => {
    expect(formatModeLine("fetched_snapshot", "2026-07-04T20:30:00-05:00")).toBe("Live data · fetched 2026-07-04");
  });

  it("says demo data for a fallback and for a plain demo file", () => {
    expect(formatModeLine("demo_fallback", "2026-07-04T12:00:00Z")).toBe(MODE_LINE_DEMO);
    expect(formatModeLine("demo_cached", null)).toBe(MODE_LINE_DEMO);
    expect(MODE_LINE_DEMO).toBe("Demo data: live data unavailable");
  });

  it("never says live for a mode it does not know", () => {
    expect(formatModeLine("something_new", "2026-07-04T12:00:00Z")).toBe(MODE_LINE_DEMO);
    expect(formatModeLine("", "2026-07-04T12:00:00Z")).toBe(MODE_LINE_DEMO);
  });

  it.each([null, undefined, "", "yesterday", "2026-07-04", "2026-07-04T12:00:00", "2026-13-45T12:00:00Z"])(
    "says the fetch time is not available when a live file has %j",
    (instant) => {
      expect(formatModeLine("fetched_snapshot", instant as string | null | undefined)).toBe(MODE_LINE_FETCH_UNKNOWN);
    },
  );
});
