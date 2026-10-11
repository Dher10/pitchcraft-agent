import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import StarterCard from "@/components/StarterCard";
import { makeStarter } from "./fixtures";

const UNAVAILABLE = { era: "N/A", whip: "N/A", innings: "N/A", strikeouts: null, walks: null, home_runs_allowed: null };

function tile(label: string): string {
  const term = screen.getByText(label, { selector: "span" }).closest("dt") as HTMLElement;
  return (term.nextElementSibling as HTMLElement).textContent ?? "";
}

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
