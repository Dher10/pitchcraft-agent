import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import DetailedAnalysis from "@/components/DetailedAnalysis";
import MatchupView from "@/components/MatchupView";
import ScoutingReport from "@/components/ScoutingReport";
import { makeMatchup, makeSample, makeStarter, mixRow, withCount, withShare } from "./fixtures";

function panel(name = "Away Ace") {
  return screen.getByRole("heading", { name: `How ${name} attacks` }).closest("article")!;
}
function pitches(node: HTMLElement) {
  return within(node).getAllByRole("button").filter((button) => button.hasAttribute("aria-pressed"));
}
function fixture() {
  const row = (name: string, count: number, left: number | null, right: number | null) =>
    withShare(withShare(withCount(mixRow(name, Math.round(count / 10) / 10, name === "Absent" ? 100 : 0), "away_starter", count, 10000),
      "away_starter", "vs_lhh", left), "away_starter", "vs_rhh", right);
  // 5,000 pitches against each side. Slider is 999 L / 3,000 R; Rare is 1 L / 0 R.
  // All five away pitches are retained; Absent belongs only to the opponent.
  const mix = [row("Zulu", 1500, 20, 10), row("Rare", 1, 0, 0), row("Alpha", 1500, 20, 10),
    row("Slider", 3999, 20, 60), row("Curve", 3000, 40, 20), row("Absent", 0, 0, 0)];
  return makeMatchup({ mix,
    away: makeStarter("Away Ace", "BOS", { sample: makeSample(10000) }),
    home: makeStarter("Home Ace", "NYY"),
    velocity: mix.map((item) => ({ pitch: item.pitch, away: item.pitch === "Absent" ? null : 94.1,
      home: item.pitch === "Absent" ? 93.2 : null })),
    awayMovement: {}, homeMovement: {},
  });
}

describe("F8 published side usage order (owner amendment)", () => {
  it("sorts by side share, overall count, then name; retains a rounded zero and excludes an overall zero", () => {
    render(<DetailedAnalysis matchup={fixture()} />);
    const rows = pitches(panel());
    expect(rows.map((row) => row.textContent)).toEqual(["Curve40%", "Slider20%", "Alpha20%", "Zulu20%", "Rare0%"]);
    expect(rows[0].getAttribute("aria-pressed")).toBe("true");
  });
  it("reorders on hand change and resets the selection to that order's first pitch", () => {
    render(<DetailedAnalysis matchup={fixture()} />);
    fireEvent.click(pitches(panel())[2]);
    fireEvent.click(within(panel()).getByRole("button", { name: "vs RHH" }));
    const rows = pitches(panel());
    expect(rows.map((row) => row.textContent)).toEqual(["Slider60%", "Curve20%", "Alpha10%", "Zulu10%", "Rare0%"]);
    expect(rows[0].getAttribute("aria-pressed")).toBe("true");
  });
  it("breaks equal published shares by overall raw count", () => {
    const matchup = fixture();
    render(<DetailedAnalysis matchup={matchup} />);
    expect(pitches(panel()).slice(1, 4).map((row) => row.textContent)).toEqual(["Slider20%", "Alpha20%", "Zulu20%"]);
  });
});

describe("F10 and F12", () => {
  it("omits the Strength Profile section in live mode", () => {
    render(<DetailedAnalysis matchup={makeMatchup({})} />);
    expect(screen.queryByRole("heading", { name: "Strength Profile" })).toBeNull();
    expect(screen.queryByText("Not available for live data yet.")).toBeNull();
  });
  it("keeps the demo Strength Profile section", () => {
    const matchup = makeMatchup({});
    matchup.data_confidence.level = "demo_cached";
    render(<DetailedAnalysis matchup={matchup} />);
    expect(screen.getByRole("heading", { name: "Strength Profile" })).toBeTruthy();
  });
  it.each([
    ["Away strength line.", "Home strength line."],
    ["Away limited line.", "Home unavailable line."],
  ])("shows both existing writer lines, without the third watch line", (away, home) => {
    const matchup = makeMatchup({});
    matchup.report.short_summary = [away, home, "Watch line."];
    const { container } = render(<MatchupView matchup={matchup} />);
    const header = container.querySelector("header")!;
    expect(header.textContent).toContain(away);
    expect(header.textContent).toContain(home);
    expect(header.textContent).not.toContain("Watch line.");
  });
});

it("F6 anchors both lineup stat groups after unequal prose and scope text", () => {
  const matchup = makeMatchup({});
  const { container } = render(<ScoutingReport awayStarter={matchup.starters.away_starter}
    homeStarter={matchup.starters.home_starter} awayOpponent={matchup.teams.home} homeOpponent={matchup.teams.away}
    awaySection={{ title: "Away", body: "Short." }} homeSection={{ title: "Home", body: "Long text. ".repeat(50) }} />);
  const cards = container.querySelectorAll("article");
  expect(cards).toHaveLength(2);
  for (const card of cards) {
    expect(card.classList.contains("flex")).toBe(true);
    expect(card.classList.contains("flex-col")).toBe(true);
    expect(card.lastElementChild?.tagName).toBe("DL");
    expect(card.lastElementChild?.classList.contains("mt-auto")).toBe(true);
  }
});

const tooltips = {
  LHH: "Left-handed hitters", RHH: "Right-handed hitters",
  ERA: "Earned run average: earned runs allowed per nine innings. Lower is better.",
  WHIP: "Walks plus hits per inning pitched. Lower is better.", K: "Strikeouts.",
  OPS: "On-base plus slugging: how often a lineup reaches base plus how much power it hits for. Higher means a stronger lineup.",
  "K%": "Share of plate appearances that end in a strikeout.",
  "BB%": "Share of plate appearances that end in a walk.",
  Break: "Total movement of the pitch, sideways and up or down, compared with a pitch thrown without spin.",
};

describe("F9 accessible exact tooltips", () => {
  it.each(Object.entries(tooltips))("%s opens on focus, has an aria relationship and dismisses with Escape", (label, text) => {
    const matchup = makeMatchup({});
    render(<><MatchupView matchup={matchup} /><DetailedAnalysis matchup={matchup} /></>);
    const trigger = label === "LHH" || label === "RHH"
      ? screen.getAllByRole("button", { name: `vs ${label}` })[0]
      : screen.getAllByText(label, { exact: true })[0];
    expect(trigger.tagName === "BUTTON" || trigger.tabIndex === 0).toBe(true);
    fireEvent.focus(trigger);
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip.textContent).toBe(text);
    expect(trigger.getAttribute("aria-describedby")).toBe(tooltip.id);
    fireEvent.keyDown(trigger, { key: "Escape" });
    expect(screen.queryByRole("tooltip")).toBeNull();
    fireEvent.blur(trigger);
    fireEvent.mouseEnter(trigger);
    expect(screen.getByRole("tooltip").textContent).toBe(text);
    fireEvent.mouseLeave(trigger);
    expect(screen.queryByRole("tooltip")).toBeNull();
    fireEvent.focus(trigger);
    expect(screen.getByRole("tooltip").textContent).toBe(text);
    fireEvent.blur(trigger);
    expect(screen.queryByRole("tooltip")).toBeNull();
  });
  it("keeps a focused description open after the pointer leaves, until focus leaves", () => {
    render(<MatchupView matchup={makeMatchup({})} />);
    const trigger = screen.getAllByText("ERA", { exact: true })[0];
    fireEvent.focus(trigger);
    fireEvent.mouseEnter(trigger);
    fireEvent.mouseLeave(trigger);
    expect(screen.getByRole("tooltip").textContent).toBe(tooltips.ERA);
    fireEvent.blur(trigger);
    expect(screen.queryByRole("tooltip")).toBeNull();
  });
});
