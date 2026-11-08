import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import ArchiveTable from "@/components/ArchiveTable";
import GameCarousel from "@/components/GameCarousel";
import PitchCraftApp from "@/components/PitchCraftApp";
import type { ArchiveItem, Metadata, PitchCraftData, Series } from "@/lib/types";
import { makeMatchup } from "./fixtures";
import noGamesLive from "@/tests/fixtures/no_games_live.json";

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
  standing: "MIL leads 1-0",
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
    expect(container.textContent).not.toContain("How PitchCraft Works");
    expect(container.textContent).not.toMatch(/pending/i);
    expect(container.textContent).toContain("Archive");
    expect(container.textContent).toContain("For information only.");
    expect(container.textContent).not.toContain("Games");
    expect(container.querySelectorAll("article").length).toBe(0);
  });

  it("ignores a matchup id in the address when there is nothing to select", () => {
    expect(() => render(<PitchCraftApp data={empty} initialSelectedId="matchup_404" />)).not.toThrow();
  });

  it("control: an empty live page without a run makes no no-games assertion", () => {
    const { container } = render(<PitchCraftApp data={empty} />);
    expect(container.textContent).not.toContain("No MLB games scheduled");
  });

  it("shows the no-games date above the archive only for a live no-games record", () => {
    const data = file({
      featured_matchup_id: null, matchups: [], archive: [row()],
      metadata: { ...metadata, data_status: {
        mode: "fetched_snapshot", reason: null,
        live_run: { status: "no_games", target_date: "2026-10-23", as_of: "2026-10-22",
          run_at: "2026-10-23T15:00:01+00:00", games_scheduled: 0, games_live: 0, errors: [], warnings: [] },
      } },
    });
    const { container } = render(<PitchCraftApp data={data} />);
    expect(container.textContent).toContain("No MLB games scheduled on 2026-10-23.");
    expect(container.textContent).toContain("Rays vs Brewers");
    expect(container.textContent!.indexOf("No MLB games")).toBeLessThan(container.textContent!.indexOf("Archive"));
    const hero = container.querySelector("h1")!.closest("section")!;
    expect(hero.nextElementSibling?.textContent).toBe("No MLB games scheduled on 2026-10-23.");
    expect(container.textContent).not.toContain("Away Ace");
    expect(container.textContent).toContain("Live data");
  });

  it("control: a demo empty file makes no no-games assertion", () => {
    const { container } = render(<PitchCraftApp data={file({
      featured_matchup_id: null, matchups: [],
      metadata: { ...(noGamesLive as PitchCraftData).metadata, data_mode: "demo_cached" },
    })} />);
    expect(container.textContent).not.toContain("No MLB games scheduled");
    expect(container.textContent).not.toContain("How PitchCraft Works");
  });

  it("renders the actual fake-schedule → daily → validated artifact without a demo matchup", () => {
    const { container } = render(<PitchCraftApp data={noGamesLive as PitchCraftData} />);
    expect(container.textContent).toContain("No MLB games scheduled on 2026-07-16.");
    expect(container.textContent).toContain("Boston Red Sox vs New York Yankees");
    expect(container.textContent).toContain("MLB Stats API");
    expect(container.textContent).toContain("Baseball Savant");
    expect(container.querySelectorAll("button").length).toBe(0);
    expect(container.textContent).not.toContain("Featured game has not been completed");
    expect(container.textContent).toContain("Live data · fetched 2026-07-16");
    expect(container.textContent).not.toContain("How PitchCraft Works");
    expect(container.textContent).not.toMatch(/pending/i);
    const hero = container.querySelector("h1")!.closest("section")!;
    expect(hero.nextElementSibling?.textContent).toBe("No MLB games scheduled on 2026-07-16.");
  });

  it("control: a file with a matchup still draws the carousel and the matchup", () => {
    // Keep run evidence present so this independently exercises the matchup-count guard.
    const { container } = render(<PitchCraftApp data={file({ metadata: (noGamesLive as PitchCraftData).metadata })} />);

    expect(container.textContent).toContain("Games");
    expect(container.textContent).toContain("Away Ace");
    expect(container.textContent).toContain("How PitchCraft Works");
    expect(container.textContent).not.toContain("No MLB games scheduled");
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
  it("omits an unknown historical source state together with the status column", () => {
    const { container } = render(<ArchiveTable archive={[row({ status: null })]} />);
    expect(container.querySelectorAll("tbody tr td")).toHaveLength(5);
    expect(container.querySelectorAll("tbody tr td")[2].textContent).toBe("A vs B");
  });
  it("shows the page's dash for the result and for the grade, and never 'Pending'", () => {
    const { container } = render(<ArchiveTable archive={[row()]} />);
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[3]).toBe("—");
    expect(cells[4]).toBe("—");
    expect(container.textContent).not.toContain("Pending");
  });

  it("control: a result with no grade yet still says Pending", () => {
    const { container } = render(<ArchiveTable archive={[row({ result_label: "BOS 5 - NYY 3" })]} />);
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[3]).toBe("BOS 5 - NYY 3");
    expect(cells[4]).toBe("Pending");
  });

  it("control: a result and a grade are drawn as they are", () => {
    const { container } = render(
      <ArchiveTable archive={[row({ result_label: "BOS 5 - NYY 3", grade_label: "Starter Duel: A, B" })]} />,
    );
    const cells = Array.from(container.querySelectorAll("tbody tr td")).map((cell) => cell.textContent);

    expect(cells[3]).toBe("BOS 5 - NYY 3");
    expect(cells[4]).toBe("Starter Duel: A, B");
  });
});

describe("a matchup with a series", () => {
  const view = (series: Series | null) => render(<PitchCraftApp data={file({ matchups: [{ ...makeMatchup({}), series }] })} />);

  it("draws the series line under the headline", () => {
    const { container } = view(SERIES);

    expect(container.textContent).toContain("World Series · Game 2 · MIL leads 1-0");
  });

  it("draws nothing about a series for a game that has none", () => {
    const { container } = view(null);

    expect(container.textContent).not.toContain("World Series");
    expect(container.textContent).not.toMatch(/Game \d/);
    expect(container.textContent).not.toContain("Series standing not available");
  });

  it("says the standing is not available for a later game without one", () => {
    const { container } = view({ series_name: "World Series", game_number: 2, games_in_series: 7, standing: null });

    expect(container.textContent).toContain("World Series · Game 2 · Series standing not available");
  });

  it("shows game 1 without a standing and without the not-available words", () => {
    const { container } = view({ series_name: "World Series", game_number: 1, games_in_series: 7, standing: null });

    expect(container.textContent).toContain("World Series · Game 1");
    expect(container.textContent).not.toContain("Series standing not available");
  });

  it("does not disturb the venue and time line of the header", () => {
    const { container } = view(SERIES);

    expect(container.textContent).toContain("Test Park");
  });

  it("accepts a series whose length is unknown", () => {
    expect(() => view({ series_name: "World Series", game_number: 1, games_in_series: null, standing: null })).not.toThrow();
  });
});
