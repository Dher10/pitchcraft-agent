import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import { FASTBALL, makeMatchup, makeSample, makeStarter, mixRow } from "./fixtures";

function article(name: string): HTMLElement {
  return screen.getByRole("heading", { name: `How ${name} attacks` }).closest("article") as HTMLElement;
}

function pitchButtons(scope: HTMLElement): string[] {
  return within(scope)
    .queryAllByRole("button")
    .map((button) => button.textContent ?? "")
    .filter((text) => !/vs (L|R)HH/.test(text))
    .map((text) => text.replace(/[\d.]+%$/, ""));
}

describe("a debut starter (QA-03)", () => {
  // QA probe: the away starter has no pitches; the opponent throws a four-seam 100% of the time.
  const debut = () =>
    makeMatchup({
      away: makeStarter("Debut Lefty", "BOS", { throws: "L", sample: makeSample(0) }),
      home: makeStarter("Veteran Righty", "NYY"),
      mix: [mixRow("Four-seam", 0, 100)],
      velocity: [{ pitch: "Four-seam", away: null, home: 94.1 }],
      awayMovement: {},
    });

  it("gets no pitch row, trajectory, shape claim or opponent pitch", () => {
    render(<DetailedAnalysis matchup={debut()} />);
    const away = article("Debut Lefty");

    expect(pitchButtons(away)).toEqual([]);
    expect(within(away).queryByRole("img", { name: /movement trajectory/i })).toBeNull();
    expect(away.textContent).not.toMatch(/mostly straight|fastball shape|Break\s*0\.0/i);
    expect(away.textContent).not.toContain("Four-seam");
  });

  it("says plainly that there is nothing to show", () => {
    render(<DetailedAnalysis matchup={debut()} />);
    const away = article("Debut Lefty");

    expect(within(away).getByText(/no pitches on record/i)).toBeTruthy();
    expect(away.textContent).toContain("Arsenal data limited: 0 pitches (100 needed)");
  });

  it("does not change what the opponent shows", () => {
    render(<DetailedAnalysis matchup={debut()} />);
    const home = article("Veteran Righty");

    expect(pitchButtons(home)).toEqual(["Four-seam"]);
    expect(within(home).getByRole("img", { name: /Four-seam movement trajectory/i })).toBeTruthy();
  });
});

describe("each starter shows only his own arsenal", () => {
  const matchup = () =>
    makeMatchup({
      away: makeStarter("Away Ace", "BOS"),
      home: makeStarter("Home Ace", "NYY"),
      mix: [mixRow("Sinker", 0, 55), mixRow("Four-seam", 60, 0), mixRow("Slider", 40, 0), mixRow("Changeup", 0, 45)],
      awayMovement: { "Four-seam": FASTBALL, Slider: { h_break: -3.6, v_break: 0.4, family: "Breaking" } },
      homeMovement: { Sinker: { h_break: 13.2, v_break: 6.5, family: "Fastball" }, Changeup: { h_break: 11.8, v_break: 6.1, family: "Offspeed" } },
    });

  it("lists only the pitches that starter threw", () => {
    render(<DetailedAnalysis matchup={matchup()} />);

    expect(pitchButtons(article("Away Ace"))).toEqual(["Four-seam", "Slider"]);
    expect(pitchButtons(article("Home Ace"))).toEqual(["Sinker", "Changeup"]);
  });

  it("starts on his own first pitch, not the first pitch of the combined list", () => {
    render(<DetailedAnalysis matchup={matchup()} />);

    expect(within(article("Away Ace")).getByRole("img", { name: /Four-seam movement trajectory/i })).toBeTruthy();
    expect(within(article("Home Ace")).getByRole("img", { name: /Sinker movement trajectory/i })).toBeTruthy();
  });

  it("lists velocities only for his own pitches", () => {
    render(<DetailedAnalysis matchup={matchup()} />);

    expect(article("Away Ace").textContent).not.toMatch(/Sinker|Changeup/);
    expect(article("Home Ace").textContent).not.toMatch(/Four-seam|Slider/);
  });
});

describe("a limited arsenal", () => {
  it("states the limitation and describes no pitch shape", () => {
    const matchup = makeMatchup({
      away: makeStarter("Thin Sample", "BOS", { sample: makeSample(40) }),
      mix: [mixRow("Four-seam", 100, 100)],
    });
    render(<DetailedAnalysis matchup={matchup} />);
    const away = article("Thin Sample");

    expect(away.textContent).toContain("Arsenal data limited: 40 pitches (100 needed)");
    expect(within(away).getByText(/shapes are not described/i)).toBeTruthy();
    expect(within(away).queryByRole("img", { name: /movement trajectory/i })).toBeNull();
    expect(away.textContent).not.toMatch(/fastball shape|mostly straight/i);
  });
});

describe("unavailable movement", () => {
  const withMovement = (awayMovement: Parameters<typeof makeMatchup>[0]["awayMovement"]) =>
    makeMatchup({ mix: [mixRow("Four-seam", 100, 100)], awayMovement });

  it("is shown as unavailable, never as a measured 0.0 inch break", () => {
    render(<DetailedAnalysis matchup={withMovement({ "Four-seam": { h_break: null, v_break: null, family: "Fastball" } })} />);
    const away = article("Away Ace");

    expect(within(away).getByText(/movement data not available/i)).toBeTruthy();
    expect(within(away).queryByRole("img", { name: /movement trajectory/i })).toBeNull();
    expect(away.textContent).not.toMatch(/Break|0\.0 in|mostly straight|fastball shape/i);
  });

  it("is also unavailable when the pitch has no movement entry at all", () => {
    render(<DetailedAnalysis matchup={withMovement({})} />);
    const away = article("Away Ace");

    expect(within(away).getByText(/movement data not available/i)).toBeTruthy();
    expect(within(away).queryByRole("img", { name: /movement trajectory/i })).toBeNull();
  });

  it("keeps the velocity and usage of the pitch that has no movement", () => {
    render(<DetailedAnalysis matchup={withMovement({})} />);
    const away = article("Away Ace");

    expect(away.textContent).toContain("94.1 mph");
    expect(away.textContent).toContain("100%");
  });

  it("still draws a real measured zero", () => {
    render(<DetailedAnalysis matchup={withMovement({ "Four-seam": { h_break: 0, v_break: 0, family: "Fastball" } })} />);
    const away = article("Away Ace");

    expect(within(away).getByRole("img", { name: /Four-seam movement trajectory/i })).toBeTruthy();
    expect(away.textContent).toContain("0.0 in");
  });
});

describe("a healthy arsenal is unchanged", () => {
  it("draws the trajectory and describes the shape", () => {
    render(<DetailedAnalysis matchup={makeMatchup({})} />);
    const away = article("Away Ace");

    expect(within(away).getByRole("img", { name: /Four-seam movement trajectory/i })).toBeTruthy();
    expect(away.textContent).toMatch(/Rides through the zone|Runs|Shows a modest fastball shape/);
  });
});
