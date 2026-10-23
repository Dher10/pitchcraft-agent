import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import GameCarousel from "@/components/GameCarousel";
import { UNAVAILABLE } from "@/lib/format";
import type { Matchup } from "@/lib/types";
import { makeMatchup } from "./fixtures";

// P0.15-D2.5a (F5, contract rule 7, schema 0.8.0): the badge says the state the schedule gave. A game whose state the
// schedule did not give, or that was not played to its end, has `null`: the badge shows the page's dash for an
// unavailable figure (no new wording) and never guesses "upcoming".

function badge(status: Matchup["status"]): string {
  const matchup: Matchup = { ...makeMatchup({}), status, is_featured: false };
  const { container } = render(
    <GameCarousel matchups={[matchup]} archive={[]} featuredId="other" selectedId={matchup.id} onSelect={() => {}} />,
  );
  return container.querySelector("button span.uppercase")?.textContent ?? "";
}

describe("the status badge of a game", () => {
  it.each([
    ["upcoming", "upcoming"],
    ["live", "live"],
    ["final", "final"],
  ] as const)("says %s for a game that is %s", (status, text) => {
    expect(badge(status)).toBe(text);
  });

  it("shows the dash of an unavailable figure when the matchup has no status, and never upcoming", () => {
    expect(badge(null)).toBe(UNAVAILABLE);
    expect(UNAVAILABLE).toBe("—");
    expect(badge(null)).not.toMatch(/upcoming/);
  });

  it("control: the featured game is still called recommended", () => {
    const matchup: Matchup = { ...makeMatchup({}), status: null, is_featured: true };
    const { container } = render(
      <GameCarousel matchups={[matchup]} archive={[]} featuredId={matchup.id} selectedId={matchup.id} onSelect={() => {}} />,
    );

    expect(container.textContent).toContain("recommended");
  });
});
