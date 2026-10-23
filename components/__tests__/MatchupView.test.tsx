import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import MatchupView from "@/components/MatchupView";
import GameCarousel from "@/components/GameCarousel";
import type { Matchup } from "@/lib/types";
import { makeMatchup } from "./fixtures";

/** A live game as the generator now writes it: an explicit UTC instant, the venue's zone only if the source gave one. */
function liveMatchup(game: Partial<Matchup["game"]>): Matchup {
  const matchup = makeMatchup({});
  return {
    ...matchup,
    game: {
      ...matchup.game,
      venue: "Yankee Stadium",
      start_time_utc: "2026-07-15T23:05:00Z",
      start_time_local: null,
      timezone: null,
      ...game,
    },
  };
}

function header(): string {
  return screen.getByText(/Yankee Stadium|Venue not available/).textContent ?? "";
}

describe("the game time in the matchup header", () => {
  it("shows the UTC instant as UTC when the source gave no zone, never a zone from the demo", () => {
    render(<MatchupView matchup={liveMatchup({})} />);

    expect(header()).toBe("Yankee Stadium · 23:05 UTC");
    expect(document.body.textContent).not.toMatch(/America\/Los_Angeles|T23:05:00Z/);
  });

  it("converts to the venue zone the source gave", () => {
    render(<MatchupView matchup={liveMatchup({ timezone: "America/New_York" })} />);

    expect(header()).toBe("Yankee Stadium · 7:05 PM EDT");
  });

  it("says the venue is unavailable instead of printing nothing or a demo park", () => {
    render(<MatchupView matchup={liveMatchup({ venue: null })} />);

    expect(header()).toBe("Venue not available · 23:05 UTC");
  });
});

describe("the game time in the carousel", () => {
  it("uses the same rule", () => {
    const matchup = liveMatchup({ timezone: "America/New_York" });
    render(
      <GameCarousel matchups={[matchup]} archive={[]} featuredId={matchup.id} selectedId={matchup.id} onSelect={() => {}} />,
    );

    expect(document.body.textContent).toContain("7:05 PM EDT");
    expect(document.body.textContent).not.toContain("null");
  });
});
