import { describe, expect, it } from "vitest";
import { render, screen, within } from "@testing-library/react";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import GameCarousel from "@/components/GameCarousel";
import MatchupView from "@/components/MatchupView";
import { chartSeries, formatUsage } from "@/components/PitchMixChart";
import PitchTrajectoryCard from "@/components/PitchTrajectoryCard";
import TeamBadge from "@/components/TeamBadge";
import { describePitchMovement } from "@/lib/pitchDescriptions";
import { teamLabel } from "@/lib/teamLabel";
import type { PitchMixRow } from "@/lib/types";
import { FASTBALL, makeMatchup, makeSample, makeStarter, mixRow, withCount } from "./fixtures";

// P0.15-D2.2c: a family, an abbreviation and a share can be null (schema 0.5.0). No producer writes a null
// yet; every reader must already handle it, and never print "null", "NaN" or an invented value.

function unnamedTeams() {
  const matchup = makeMatchup({
    away: makeStarter("Away Ace", "BOS"),
    home: makeStarter("Home Ace", "NYY"),
  });
  matchup.teams.away.abbreviation = null;
  matchup.teams.home.abbreviation = null;
  matchup.starters.away_starter.team = null;
  matchup.starters.home_starter.team = null;
  return matchup;
}

describe("a team with no abbreviation shows its name", () => {
  it("teamLabel is the abbreviation when there is one and the name otherwise", () => {
    expect(teamLabel({ abbreviation: "BOS", name: "Boston Red Sox" })).toBe("BOS");
    expect(teamLabel({ abbreviation: null, name: "Brand New Club" })).toBe("Brand New Club");
  });

  it("the badge has no letters when there is no abbreviation", () => {
    const { container } = render(<TeamBadge abbreviation={null} />);

    expect(container.textContent).toBe("");
  });

  it("the carousel names the team", () => {
    const matchup = unnamedTeams();
    render(
      <GameCarousel matchups={[matchup]} archive={[]} featuredId={matchup.id} selectedId={matchup.id} onSelect={() => {}} />,
    );

    expect(document.body.textContent).toContain("Boston Red Sox");
    expect(document.body.textContent).toContain("New York Yankees");
    expect(document.body.textContent).not.toMatch(/null|undefined/);
  });

  it("the matchup names the team on the starter card and in the scouting title", () => {
    render(<MatchupView matchup={unnamedTeams()} />);

    expect(document.body.textContent).toMatch(/Boston Red Sox\s*·\s*AWAY/);
    expect(document.body.textContent).toMatch(/New York Yankees\s*·\s*HOME/);
    expect(document.body.textContent).toContain("Away Ace vs New York Yankees");
    expect(document.body.textContent).not.toMatch(/null|undefined|\?\?\?/);
  });
});

describe("a pitch share that is null is not a bar (F20)", () => {
  const rows: PitchMixRow[] = [
    {
      pitch: "Four-seam",
      away_starter: { overall: null, vs_lhh: null, vs_rhh: null, count: 0, total: 0 },
      home_starter: { overall: 100, vs_lhh: 100, vs_rhh: 100, count: 90, total: 90 },
    },
  ];

  it("the chart series keeps the null: no 0%, no NaN", () => {
    expect(chartSeries(rows)).toEqual([{ pitch: "Four-seam", away_starter_usage: null, home_starter_usage: 100 }]);
  });

  it("the tooltip says it is not available", () => {
    expect(formatUsage(null)).toBe("not available");
    expect(formatUsage(12.5)).toBe("12.5%");
  });

  it("the detail panel shows no pitch for the starter who threw none", () => {
    const matchup = makeMatchup({
      away: makeStarter("Debut Lefty", "BOS", { throws: "L", sample: makeSample(0) }),
      home: makeStarter("Veteran Righty", "NYY"),
      mix: [rows[0]],
      velocity: [{ pitch: "Four-seam", away: null, home: 94.1 }],
      awayMovement: {},
    });

    render(<DetailedAnalysis matchup={matchup} />);
    const away = screen.getByRole("heading", { name: "How Debut Lefty attacks" }).closest("article") as HTMLElement;

    expect(within(away).queryAllByRole("button").filter((b) => /Four-seam/.test(b.textContent ?? ""))).toEqual([]);
    expect(document.body.textContent).not.toMatch(/NaN|null%/);
  });

  it("a pitch with a null share and no raw counts was not thrown", () => {
    const matchup = makeMatchup({
      away: makeStarter("Away Ace", "BOS", { sample: makeSample(1500) }),
      home: makeStarter("Home Ace", "NYY"),
      mix: [
        withCount(mixRow("Four-seam", 100, 100), "away_starter", 1500, 1500),
        { ...mixRow("Slider", 0, 0), home_starter: { overall: null, vs_lhh: null, vs_rhh: null } },
      ],
    });

    render(<DetailedAnalysis matchup={matchup} />);
    const home = screen.getByRole("heading", { name: "How Home Ace attacks" }).closest("article") as HTMLElement;

    expect(within(home).queryAllByRole("button").filter((b) => /Slider/.test(b.textContent ?? ""))).toEqual([]);
  });
});

describe("a pitch with no family is not given one (F6e)", () => {
  it("the description says the pitch is not in the map", () => {
    const text = describePitchMovement({ family: null, velocity: 90, hBreak: 3, vBreak: 5 });

    expect(text).toMatch(/not in the pitch-family map/i);
    expect(text).not.toMatch(/fastball/i);
  });

  it("the trajectory card shows no family badge", () => {
    render(
      <PitchTrajectoryCard
        pitchName="XX"
        family={null}
        velocity={90}
        usagePct={12}
        hBreak={3}
        vBreak={5}
        throwsHand="R"
        team={null}
        description="x"
      />,
    );

    expect(document.body.textContent).not.toMatch(/Fastball|Breaking|Offspeed|null/);
    expect(screen.queryByTestId("pitch-family")).toBeNull(); // not even an empty coloured pill
  });

  it("control: a pitch with a family keeps its badge", () => {
    render(
      <PitchTrajectoryCard
        pitchName="Slider"
        family="Breaking"
        velocity={86}
        usagePct={30}
        hBreak={-4}
        vBreak={2}
        throwsHand="R"
        team="BOS"
        description="x"
      />,
    );

    expect(screen.getByTestId("pitch-family").textContent).toBe("Breaking");
  });

  it("the detail panel does not infer a family from the name of the pitch", () => {
    const matchup = makeMatchup({
      mix: [mixRow("Unmapped pitch", 100, 0)],
      velocity: [{ pitch: "Unmapped pitch", away: 90, home: null }],
      awayMovement: { "Unmapped pitch": { ...FASTBALL, family: null } },
    });

    render(<DetailedAnalysis matchup={matchup} />);
    const away = screen.getByRole("heading", { name: "How Away Ace attacks" }).closest("article") as HTMLElement;

    expect(away.textContent).not.toMatch(/Fastball|Breaking|Offspeed/);
  });
});
