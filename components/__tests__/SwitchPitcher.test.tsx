import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import MatchupView from "@/components/MatchupView";
import { makeMatchup, makeStarter } from "./fixtures";

// P0.15-D2.3b (schema 0.6.0, D38): the lineup that faces a switch pitcher has no hand to name, so
// `vs_pitcher_hand` is null. The page must not print "vs null", "vs undefined" or a dangling "vs".

function switchMatchup() {
  const matchup = makeMatchup({ away: makeStarter("Away Ace", "BOS"), home: makeStarter("Home Ace", "NYY") });
  matchup.starters.away_starter.throws = "S";
  matchup.teams.home.offense_profile.vs_pitcher_hand = null;
  return matchup;
}

describe("a lineup that faces a switch pitcher", () => {
  it("names no hand and prints no null", () => {
    const { container } = render(<MatchupView matchup={switchMatchup()} />);

    expect(document.body.textContent).not.toMatch(/null|undefined|SHP/);
    const footers = Array.from(container.querySelectorAll("p.font-mono")).map((node) => node.textContent?.trim());
    expect(footers).not.toContain("vs");
  });

  it("names no hand on the card of the switch pitcher", () => {
    // The home starter throws "R" (control below); only the away starter is a switch pitcher.
    const { container } = render(<MatchupView matchup={switchMatchup()} />);

    const cards = Array.from(container.querySelectorAll("article")).filter((card) =>
      card.textContent?.includes("Away Ace"),
    );
    const starterCard = cards.find((card) => card.querySelector("h3")?.textContent === "Away Ace");
    expect(starterCard).toBeDefined();
    expect(starterCard?.textContent).not.toMatch(/[LRS]HP/);
  });

  it("control: a known hand is still named on the lineup that faces it and on its own card", () => {
    const { container } = render(<MatchupView matchup={switchMatchup()} />);

    expect(document.body.textContent).toContain("vs RHP"); // the away lineup faces the home starter's hand
    const homeCard = Array.from(container.querySelectorAll("article")).find(
      (card) => card.querySelector("h3")?.textContent === "Home Ace",
    );
    expect(homeCard?.textContent).toContain("RHP");
  });
});
