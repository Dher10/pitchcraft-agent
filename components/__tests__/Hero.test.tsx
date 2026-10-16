import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import Hero from "@/components/Hero";

// P0.15-D2.4b (F3, contract 3.3): the hero and the layout describe the product, not the data; the mode line says whether
// the page shows live or demo data. No "Cached Demo" over live data.

const LIVE = { data_mode: "fetched_snapshot", generated_at: "2026-07-04T12:00:00Z" };
const FALLBACK = { data_mode: "demo_fallback", generated_at: "2026-06-28T09:00:00-05:00" };
const DEMO = { data_mode: "demo_cached", generated_at: "2026-06-28T09:00:00-05:00" };

describe("the hero", () => {
  it.each([["live", LIVE], ["fallback", FALLBACK], ["demo", DEMO]])("describes the product neutrally (%s)", (_, metadata) => {
    const { container } = render(<Hero metadata={metadata} />);
    const text = container.textContent ?? "";

    expect(text).toContain("Starter matchups, checked against the data");
    expect(text).toContain(
      "Each report reads the probable starters from public MLB data and says only what that data supports. No predictions, no betting.",
    );
    expect(text).not.toMatch(/cached/i);
  });

  it("shows the live mode line with the day of the fetch", () => {
    const { getByTestId } = render(<Hero metadata={LIVE} />);

    expect(getByTestId("mode-line").textContent).toBe("Live data · fetched 2026-07-04");
    expect(getByTestId("mode-line").getAttribute("data-mode")).toBe("live");
  });

  it.each([["fallback", FALLBACK], ["demo", DEMO]])("shows the demo mode line (%s)", (_, metadata) => {
    const { getByTestId } = render(<Hero metadata={metadata} />);

    expect(getByTestId("mode-line").textContent).toBe("Demo data: live data unavailable");
    expect(getByTestId("mode-line").getAttribute("data-mode")).toBe("demo");
  });
});

describe("the layout", () => {
  const source = readFileSync(path.join(process.cwd(), "app", "layout.tsx"), "utf-8");

  it("describes the product, not the data", () => {
    expect(source).toContain(
      "Starting-pitcher matchup reports for MLB fans, checked against public data. No predictions, no betting.",
    );
    expect(source).not.toMatch(/cached/i);
  });
});
