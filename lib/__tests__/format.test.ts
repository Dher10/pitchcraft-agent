import { describe, expect, it } from "vitest";
import { formatFigure } from "@/lib/format";

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
