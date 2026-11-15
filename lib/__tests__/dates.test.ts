import { describe, expect, it } from "vitest";
import { formatDay, formatMonthDay } from "@/lib/format";

// Dates for people: "Oct 28, 2026". ISO stays in `datetime` attributes and URLs (docs/design/CONTENT.md).

describe("dates for people", () => {
  it("writes a day as Mon D, YYYY without any time-zone shift", () => {
    expect(formatDay("2026-10-28")).toBe("Oct 28, 2026");
    expect(formatDay("2026-09-29")).toBe("Sep 29, 2026");
    expect(formatDay("2026-01-01")).toBe("Jan 1, 2026");
    expect(formatDay("2026-12-31")).toBe("Dec 31, 2026");
  });

  it("writes a day without the year", () => {
    expect(formatMonthDay("2026-10-28")).toBe("Oct 28");
  });

  it("refuses what is not an ISO day, instead of inventing a date", () => {
    for (const bad of ["", "2026-13-01", "2026-02-30", "10/28/2026", "2026-10-28T10:00:00Z", "Oct 28, 2026"]) {
      expect(() => formatDay(bad), bad).toThrow();
    }
  });
});
