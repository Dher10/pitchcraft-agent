import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import { FASTBALL, makeMatchup, makeSample, makeStarter, mixRow, withCount, withShare } from "./fixtures";

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

  it("does not say there are no pitches on record when the pitch count is unknown (F14)", () => {
    // Statcast cannot be trusted for him (or the sample is unknown): `pitches` is null, not 0.
    const matchup = debut();
    matchup.starters.away_starter.sample = makeSample(null);

    render(<DetailedAnalysis matchup={matchup} />);
    const away = article("Debut Lefty");

    expect(away.textContent).not.toMatch(/no pitches on record/i);
    expect(within(away).getByText(/pitch data is not available for Debut Lefty/i)).toBeTruthy();
    expect(away.textContent).toContain("Arsenal data limited: pitch count not available (100 needed)");
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
    expect(away.textContent).toContain("Moves 7.8 in. sideways and 16.2 in. up compared with a pitch thrown without spin.");
  });
});

describe("an unknown pitch count is not a count of zero (QA3-05)", () => {
  const caption = (pitches: number | null) => {
    const matchup = makeMatchup({
      away: makeStarter("Count Case", "BOS", { sample: makeSample(pitches) }),
      mix: [mixRow("Four-seam", 100, 100)],
    });
    render(<DetailedAnalysis matchup={matchup} />);
    return article("Count Case").textContent ?? "";
  };

  it("says the pitch count is not available when it is null", () => {
    // QA probe: sample.arsenal.pitches = null was rendered as "0 pitches".
    const text = caption(null);

    expect(text).toContain("Arsenal data limited: pitch count not available (100 needed)");
    expect(text).not.toMatch(/0 pitches/);
  });

  it("keeps a real zero as zero pitches", () => {
    expect(caption(0)).toContain("Arsenal data limited: 0 pitches (100 needed)");
  });

  it("keeps a real count below the threshold", () => {
    expect(caption(40)).toContain("Arsenal data limited: 40 pitches (100 needed)");
  });
});

describe("decisions on the arsenal use raw counts, not the rounded share", () => {
  it("lists a pitch thrown once in 3,000 although its share rounds to 0.0", () => {
    const matchup = makeMatchup({
      mix: [
        withCount(mixRow("Four-seam", 100, 100), "away_starter", 2999, 3000),
        withCount(mixRow("Eephus", 0, 0), "away_starter", 1, 3000),
      ],
      awayMovement: { "Four-seam": FASTBALL },
    });
    render(<DetailedAnalysis matchup={matchup} />);

    expect(pitchButtons(article("Away Ace"))).toEqual(["Four-seam", "Eephus"]);
  });

  it("does not list a pitch with a count of zero", () => {
    const matchup = makeMatchup({
      mix: [mixRow("Four-seam", 100, 100), withCount(mixRow("Slider", 0, 40), "away_starter", 0, 3000)],
    });
    render(<DetailedAnalysis matchup={matchup} />);

    expect(pitchButtons(article("Away Ace"))).toEqual(["Four-seam"]);
  });
});

describe("a hand the data does not give is not guessed", () => {
  const hand = (throws: string) => {
    const matchup = makeMatchup({
      away: makeStarter("Hand Case", "BOS", { throws }),
      mix: [mixRow("Four-seam", 100, 100)],
      awayMovement: {},
    });
    render(<DetailedAnalysis matchup={matchup} />);
    return article("Hand Case").textContent ?? "";
  };

  it("prints LHP for a left-hander and RHP for a right-hander", () => {
    expect(hand("L")).toMatch(/LHP/);
  });

  it("prints no hand when it is unknown", () => {
    // Before: anything that was not "L" became "R".
    expect(hand("")).not.toMatch(/[LR]HP/);
  });
});

describe("an unavailable velocity is not a velocity of zero", () => {
  const withVelocity = (away: number | null) => {
    const matchup = makeMatchup({
      mix: [mixRow("Four-seam", 100, 100)],
      velocity: [{ pitch: "Four-seam", away, home: 93.2 }],
    });
    render(<DetailedAnalysis matchup={matchup} />);
    return article("Away Ace");
  };

  it("draws no velocity meter next to N/A", () => {
    const away = withVelocity(null);

    expect(within(away).getByRole("img", { name: /Four-seam movement trajectory/i })).toBeTruthy();
    expect(within(away).queryByText("Velocity")).toBeNull();
    expect(away.textContent).toContain("N/A");
  });

  it("draws the meter for a real velocity", () => {
    const away = withVelocity(94.1);

    expect(within(away).getByText("Velocity")).toBeTruthy();
  });
});

describe("a side the starter never faced is not 0% (P0.14-C)", () => {
  // He faced only right-handed batters: every share against lefties is null in the data.
  const righties = () =>
    makeMatchup({
      mix: [
        withShare(mixRow("Four-seam", 100, 100), "away_starter", "vs_lhh", null),
        withShare(mixRow("Slider", 0, 0), "away_starter", "vs_lhh", null),
      ],
    });
  const pitchButton = (scope: HTMLElement, pitch: string) =>
    within(scope).getAllByRole("button").find((button) => button.textContent?.startsWith(pitch)) as HTMLElement;

  it("shows a dash and says no left-handed batters were faced", () => {
    render(<DetailedAnalysis matchup={righties()} />);
    const away = article("Away Ace");

    expect(pitchButton(away, "Four-seam").textContent).toContain("—");
    expect(away.textContent).toMatch(/No left-handed batters faced/);
    expect(away.textContent).not.toMatch(/0%/);
    expect(away.textContent).not.toMatch(/null/);
  });

  it("still shows the real share against the side he did face", () => {
    render(<DetailedAnalysis matchup={righties()} />);
    const away = article("Away Ace");

    fireEvent.click(within(away).getByRole("button", { name: "vs RHH" }));

    expect(pitchButton(away, "Four-seam").textContent).toContain("100%");
    expect(away.textContent).not.toMatch(/No right-handed batters faced/);
  });

  it("keeps a real zero as 0%", () => {
    const matchup = makeMatchup({
      mix: [
        withShare(mixRow("Four-seam", 100, 100), "away_starter", "vs_lhh", 100),
        withShare(mixRow("Slider", 30, 0), "away_starter", "vs_lhh", 0),
      ],
    });
    render(<DetailedAnalysis matchup={matchup} />);
    const away = article("Away Ace");

    expect(pitchButton(away, "Slider").textContent).toContain("0%");
    expect(away.textContent).not.toMatch(/No left-handed batters faced/);
  });
});
