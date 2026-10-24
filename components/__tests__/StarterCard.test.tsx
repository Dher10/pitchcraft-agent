import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import StarterCard from "@/components/StarterCard";
import type { SeasonSummary } from "@/lib/types";
import { makeStarter } from "./fixtures";

const UNAVAILABLE = { era: "N/A", whip: "N/A", innings: "N/A", strikeouts: null, walks: null, home_runs_allowed: null };

function tile(label: string): string {
  const term = screen.getByText(label, { selector: "span" }).closest("dt") as HTMLElement;
  return (term.nextElementSibling as HTMLElement).textContent ?? "";
}

const REGULAR = { kind: "regular_season", through: "2026-10-08", label: "2026 regular season" } as const;
const BOTH = { kind: "regular_and_postseason", through: "2026-10-08", label: "2026 regular season and postseason through Oct 8" } as const;
const FIGURES = { era: "3.10", whip: "1.05", innings: "101.0", strikeouts: 4, walks: 3, home_runs_allowed: 2 };

function captions(scopes: NonNullable<SeasonSummary["scopes"]>): string[] {
  const summary = { ...FIGURES, scopes };
  render(<StarterCard starter={makeStarter("Away Ace", "BOS", { season_summary: summary })} side="away" mode="pregame" />);
  return Array.from(document.querySelectorAll("p"))
    .map((p) => p.textContent ?? "")
    .filter((text) => /^(ERA, WHIP and K|ERA and WHIP|K): /.test(text));
}

describe("StarterCard scope captions (QA4-01)", () => {
  it("states one caption when ERA, WHIP and K cover the same games", () => {
    expect(captions({ season_rates: REGULAR, counts: REGULAR })).toEqual(["ERA, WHIP and K: 2026 regular season"]);
  });

  it("states each group's own scope when they differ, never one scope for all", () => {
    const lines = captions({ season_rates: REGULAR, counts: BOTH });

    expect(lines).toEqual([
      "ERA and WHIP: 2026 regular season",
      "K: 2026 regular season and postseason through Oct 8",
    ]);
    expect(lines.join(" ")).not.toContain("ERA, WHIP and K");
  });

  it("names only the figures that have a scope", () => {
    expect(captions({ season_rates: REGULAR, counts: null })).toEqual(["ERA and WHIP: 2026 regular season"]);
  });

  it("names only K when the counts are the only group with a scope", () => {
    expect(captions({ season_rates: null, counts: BOTH })).toEqual(["K: 2026 regular season and postseason through Oct 8"]);
  });

  it("states nothing when no group has a scope", () => {
    expect(captions({ season_rates: null, counts: null })).toEqual([]);
  });
});

describe("StarterCard season figures", () => {
  it("shows a dash for an unavailable ERA, WHIP and K, never the string N/A", () => {
    render(<StarterCard starter={makeStarter("Away Ace", "BOS", { season_summary: UNAVAILABLE })} side="away" mode="pregame" />);

    expect([tile("ERA"), tile("WHIP"), tile("K")]).toEqual(["—", "—", "—"]);
    expect(document.body.textContent).not.toMatch(/N\/A|NaN|undefined|null/);
  });

  it("shows the real figures when they exist", () => {
    render(<StarterCard starter={makeStarter("Away Ace", "BOS")} side="away" mode="pregame" />);

    expect([tile("ERA"), tile("WHIP"), tile("K")]).toEqual(["3.10", "1.05", "110"]);
  });

  it("shows a real zero strikeout count as 0, not as a dash", () => {
    const summary = { ...UNAVAILABLE, era: "0.00", whip: "0.00", strikeouts: 0 };
    render(<StarterCard starter={makeStarter("Away Ace", "BOS", { season_summary: summary })} side="away" mode="pregame" />);

    expect([tile("ERA"), tile("K")]).toEqual(["0.00", "0"]);
  });

  it("shows a dash for each unavailable figure on its own", () => {
    const summary = { ...UNAVAILABLE, era: "3.10", strikeouts: 12 };
    render(<StarterCard starter={makeStarter("Away Ace", "BOS", { season_summary: summary })} side="away" mode="pregame" />);

    expect([tile("ERA"), tile("WHIP"), tile("K")]).toEqual(["3.10", "—", "12"]);
  });
});
