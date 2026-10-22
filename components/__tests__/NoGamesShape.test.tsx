import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import ArchiveTable from "@/components/ArchiveTable";
import GameCarousel from "@/components/GameCarousel";
import PitchCraftApp from "@/components/PitchCraftApp";
import type { ArchiveItem, Metadata, PitchCraftData, Series } from "@/lib/types";
import { makeMatchup } from "./fixtures";

// P1.5-a (schema 0.9.0, D43): the page is ready for a day with no games, for archive rows with no result and for a
// series object, before any producer writes one. No new wording is drawn: the sentence for an empty day and the series
// line are rows 9 and 7. The types are checked by tsc (`featured_matchup_id` and `result_label` are nullable).

const metadata: Metadata = {
  project_name: "PitchCraft",
  version: "0.9.0",
  data_mode: "fetched_snapshot",
  generated_at: "2026-10-23T15:00:03+00:00",
  data_fetched_at: "2026-10-23T15:00:01+00:00",
  last_updated_label: "",
  data_sources: [],
};

const SERIES: Series = {
  series_name: "World Series",
  game_number: 2,
  games_in_series: 7,
  standing: "Brewers lead 1-0",
};

function row(overrides: Partial<ArchiveItem> = {}): ArchiveItem {
  return {
    id: "matchup_001",
    date: "2026-10-22",
    title: "Rays vs Brewers",
    status: "upcoming",
    featured: true,
    starter_summary: "A vs B",
    result_label: null,
    grade_label: null,
    ...overrides,
  };
}

function file(overrides: Partial<PitchCraftData> = {}): PitchCraftData {
  return {
    metadata,
    featured_matchup_id: "matchup_test",
    matchups: [makeMatchup({})],
    archive: [],
    agent_workflow: { description: "How the agents work.", steps: [] },
    disclaimers: ["For information only."],
    ...overrides,
  };
}

describe("a day with no games", () => {
  const empty = file({ featured_matchup_id: null, matchups: [], archive: [row()] });

  it("renders without a matchup, a carousel or a featured id, and keeps the rest of the page", () => {
    const { container } = render(<PitchCraftApp data={empty} />);

    expect(container.textContent).toContain("PitchCraft Matchup Agent");
    expect(container.textContent).toContain("How PitchCraft Works");
    expect(container.textContent).toContain("Archive");
    expect(container.textContent).toContain("For information only.");
    expect(container.textContent).not.toContain("Games");
    expect(container.querySelectorAll("article").length).toBe(0);
  });

  it("ignores a matchup id in the address when there is nothing to select", () => {
    expect(() => render(<PitchCraftApp data={empty} initialSelectedId="matchup_404" />)).not.toThrow();
  });

  it("control: a file with a matchup still draws the carousel and the matchup", () => {
    const { container } = render(<PitchCraftApp data={file()} />);

    expect(container.textContent).toContain("Games");
    expect(container.textContent).toContain("Away Ace");
  });

  it("a null featured id marks no card as featured", () => {
    const { container } = render(
      <GameCarousel matchups={[makeMatchup({})]} archive={[]} featuredId={null} selectedId="matchup_test" onSelect={() => {}} />,
    );

    expect(container.textContent).not.toMatch(/recommended/i);
  });

  it("control: the featured id marks its card", () => {
    const { container } = render(
      <GameCarousel matchups={[makeMatchup({})]} archive={[]} featuredId="matchup_test" selectedId="matchup_test" onSelect={() => {}} />,
    );

    expect(container.textContent).toMatch(/recommended/i);
  });
});

describe("an archive row with no result", () => {
  it("shows the page's dash for the result and for the grade, and never 'Pending'", () => {
    const { container } = render(<ArchiveTable archive={[row()]} />);
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[4]).toBe("—");
    expect(cells[5]).toBe("—");
    expect(container.textContent).not.toContain("Pending");
  });

  it("control: a result with no grade yet still says Pending", () => {
    const { container } = render(<ArchiveTable archive={[row({ result_label: "BOS 5 - NYY 3" })]} />);
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[4]).toBe("BOS 5 - NYY 3");
    expect(cells[5]).toBe("Pending");
  });

  it("control: a result and a grade are drawn as they are", () => {
    const { container } = render(
      <ArchiveTable archive={[row({ result_label: "BOS 5 - NYY 3", grade_label: "Starter Duel: A, B" })]} />,
    );
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[4]).toBe("BOS 5 - NYY 3");
    expect(cells[5]).toBe("Starter Duel: A, B");
  });
});

describe("a matchup with a series", () => {
  it("is accepted by the page and draws nothing about the series yet (the series line is row 7)", () => {
    const without = render(<PitchCraftApp data={file({ matchups: [{ ...makeMatchup({}), series: null }] })} />);
    const withSeries = render(<PitchCraftApp data={file({ matchups: [{ ...makeMatchup({}), series: SERIES }] })} />);

    expect(withSeries.container.textContent).toBe(without.container.textContent);
    expect(withSeries.container.textContent).not.toContain("World Series");
  });

  it("accepts a series whose standing and length are unknown", () => {
    const unknown: Series = { series_name: "World Series", game_number: 1, games_in_series: null, standing: null };

    expect(() => render(<PitchCraftApp data={file({ matchups: [{ ...makeMatchup({}), series: unknown }] })} />)).not.toThrow();
  });
});
