import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import type { PitchFamily } from "@/lib/types";
import { makeMatchup, makeSample, makeStarter, mixRow } from "./fixtures";

function article(name = "Away Ace") {
  return screen.getByRole("heading", { name: `How ${name} attacks` }).closest("article") as HTMLElement;
}

const measurements = [
  { h_break: 5, v_break: -7, sentence: "Moves 5 in. sideways and 7 in. down compared with a pitch thrown without spin." },
  { h_break: 0, v_break: 0, sentence: "Moves 0 in. sideways and 0 in. up compared with a pitch thrown without spin." },
  { h_break: 12, v_break: 16, sentence: "Moves 12 in. sideways and 16 in. up compared with a pitch thrown without spin." },
  { h_break: -3.25, v_break: -0.5, sentence: "Moves 3.25 in. sideways and 0.5 in. down compared with a pitch thrown without spin." },
];
const families: PitchFamily[] = ["Fastball", "Breaking", "Offspeed"];

describe("QA5-04: only measured movement facts", () => {
  for (const family of families) {
    const pitch = { Fastball: "Four-seam", Breaking: "Slider", Offspeed: "Changeup" }[family];
    for (const velocity of [null, 82, 99]) {
      it.each(measurements)(`${family}, velocity ${velocity}: $sentence`, ({ h_break, v_break, sentence }) => {
        const matchup = makeMatchup({
          mix: [mixRow(pitch, 100, 100)],
          velocity: [{ pitch, away: velocity, home: 94 }],
          awayMovement: { [pitch]: { family, h_break, v_break } },
          homeMovement: { [pitch]: { family, h_break, v_break } },
        });
        for (const starter of Object.values(matchup.starters)) {
          starter.pitching_profile.primary_pitch = pitch;
          starter.pitching_profile.style_label = `${pitch} starter`;
        }
        render(<DetailedAnalysis matchup={matchup} />);
        const away = article();
        expect(within(away).getByText(sentence)).toBeTruthy();
        expect(away.textContent).not.toMatch(/arm.side|glove.side|barrel|hitter.s timing|much slower|more than/i);
        if (velocity === null) {
          expect(away.textContent).toContain("N/A");
          expect(within(away).queryByText("Velocity")).toBeNull();
        }
      });
    }
  }

  for (const hand of ["L", "R", "S", ""]) {
    it.each([5, -5])(`uses the approved sideways fallback for hand '${hand}' and hBreak %s`, (horizontal) => {
      const matchup = makeMatchup({
        away: makeStarter("Hand Case", "BOS", { throws: hand }),
        awayMovement: { "Four-seam": { family: "Fastball", h_break: horizontal, v_break: 16 } },
      });
      matchup.teams.home.offense_profile.vs_pitcher_hand = hand === "L" ? "LHP" : hand === "R" ? "RHP" : null;
      render(<DetailedAnalysis matchup={matchup} />);
      const away = article("Hand Case");
      expect(within(away).getByText("Moves 5 in. sideways and 16 in. up compared with a pitch thrown without spin.")).toBeTruthy();
      expect(away.textContent).not.toMatch(/arm.side|glove.side/);
      // The existing graphic keeps the published sign. It does not turn
      // screen-left/right into arm/glove labels or mirror it for a hand.
      const shape = within(away).getByRole("img", { name: /movement trajectory/ });
      const endX = Number(shape.querySelector('circle[r="7"]')?.getAttribute("cx"));
      expect(horizontal > 0 ? endX > 75 : endX < 75).toBe(true);
    });
  }

  it("control: keeps the unmapped-family sentence unchanged", () => {
    render(<DetailedAnalysis matchup={makeMatchup({
      awayMovement: { "Four-seam": { family: null, h_break: 5, v_break: -7 } },
    })} />);
    expect(within(article()).getByText("This pitch is not in the pitch-family map, so no shape description is given.")).toBeTruthy();
    expect(article().textContent).not.toContain("compared with a pitch thrown without spin");
  });

  it.each([
    { h_break: null, v_break: 5 },
    { h_break: 5, v_break: null },
  ])("control: missing movement has no numeric description ($h_break, $v_break)", (movement) => {
    render(<DetailedAnalysis matchup={makeMatchup({
      awayMovement: { "Four-seam": { family: "Fastball", ...movement } },
    })} />);
    expect(within(article()).getByText("Movement data not available for this pitch.")).toBeTruthy();
    expect(article().textContent).not.toContain("compared with a pitch thrown without spin");
  });

  it("control: a limited sample still suppresses movement descriptions", () => {
    const sample = makeSample(40);
    sample.rates = { ...sample.rates, batters_faced: 10, strikeouts: 2, walks: 1, home_runs: 0 };
    sample.limited = { arsenal: true, strikeout: true, control: true };
    const starter = makeStarter("Thin Sample", "BOS", { sample });
    starter.season_summary = {
      ...starter.season_summary, era: "0.00", whip: "0.33", innings: "3.0",
      strikeouts: 2, walks: 1, home_runs_allowed: 0,
    };
    starter.pitching_profile = {
      ...starter.pitching_profile, style_label: "Arsenal data limited",
      primary_pitch: "Not available", putaway_pitch: "Not available",
    };
    render(<DetailedAnalysis matchup={makeMatchup({
      away: starter,
    })} />);
    expect(within(article("Thin Sample")).getByText(/pitch shapes are not described/)).toBeTruthy();
    expect(article("Thin Sample").textContent).not.toContain("compared with a pitch thrown without spin");
  });
});

describe("QA5-06: measured median locations and unavailable arrays", () => {
  for (const side of ["away_starter", "home_starter"] as const) {
    for (const hand of ["vs_lhh", "vs_rhh"] as const) {
      const hitters = hand === "vs_lhh" ? "left" : "right";
      it.each([false, true])(`${side}, ${hand}, populated %s`, (populated) => {
        const matchup = makeMatchup({});
        matchup.pitch_locations[side][hand] = populated ? [{ pitch: "Four-seam", x: 0.25, y: 0.75 }] : [];
        render(<DetailedAnalysis matchup={matchup} />);
        const scope = article(side === "away_starter" ? "Away Ace" : "Home Ace");
        if (hand === "vs_rhh") fireEvent.click(within(scope).getByRole("button", { name: "vs RHH" }));
        if (populated) {
          expect(within(scope).getByText(`Median location against ${hitters}-handed hitters.`)).toBeTruthy();
          expect(within(scope).getByRole("img", { name: "Pitch location strike zone" })).toBeTruthy();
          expect(scope.textContent).not.toContain("Location data not available");
        } else {
          expect(within(scope).getByText(`Location data not available against ${hitters}-handed hitters.`)).toBeTruthy();
          expect(within(scope).queryByRole("img", { name: "Pitch location strike zone" })).toBeNull();
          expect(scope.textContent).not.toContain("Median location");
        }
        expect(scope.textContent).not.toContain("Target locations");
      });
    }

    it(`${side} changes between populated and empty when the selected hand changes`, () => {
      const matchup = makeMatchup({});
      matchup.pitch_locations[side] = { vs_lhh: [{ pitch: "Four-seam", x: 0.3, y: 0.7 }], vs_rhh: [] };
      render(<DetailedAnalysis matchup={matchup} />);
      const scope = article(side === "away_starter" ? "Away Ace" : "Home Ace");
      expect(within(scope).getByText("Median location against left-handed hitters.")).toBeTruthy();
      fireEvent.click(within(scope).getByRole("button", { name: "vs RHH" }));
      expect(within(scope).getByText("Location data not available against right-handed hitters.")).toBeTruthy();
      expect(within(scope).queryByRole("img", { name: "Pitch location strike zone" })).toBeNull();
      fireEvent.click(within(scope).getByRole("button", { name: "vs LHH" }));
      expect(within(scope).getByText("Median location against left-handed hitters.")).toBeTruthy();
      expect(within(scope).getByRole("img", { name: "Pitch location strike zone" })).toBeTruthy();
    });
  }
});
