import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render, within } from "@testing-library/react";

import HomeOffSeason from "@/components/home/HomeOffSeason";
import { parseArchiveIndex } from "@/lib/archiveIndex";

// U6 (docs/plans/R4-U.md, 4 and 5.6): the home in the off season. The season in review on the published archive; it never
// shows a live mode line or a past date as today, and it has no block that needs data the archive does not have.

const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(process.cwd(), "public/data/archive/index-2026.json"), "utf8")));
const text = (node: Element | null) => node?.textContent ?? "";

function home() {
  return render(<HomeOffSeason index={INDEX} />);
}

describe("the hero", () => {
  it("has the archive mode line, the title, the sentence and the two actions", () => {
    const { getByTestId, container, getByRole } = home();

    expect(getByTestId("mode-line").textContent).toBe("2026 season archive, final results through Oct 28, 2026");
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(container.querySelector("h1")?.textContent).toBe("The 2026 postseason, start by start");
    expect(text(container)).toContain("What each starting pitcher was expected to do, and what he did. Only what the data supports.");
    expect(getByRole("link", { name: "See the notable duels" }).getAttribute("href")).toBe("/notable");
    expect(getByRole("link", { name: "Browse all 40 games" }).getAttribute("href")).toBe("/archive");
  });

  it("does not promise what only the after-the-game layer will give", () => {
    const { container } = home();

    expect(text(container)).not.toMatch(/how the report held up|where the pitches|whether each claim held up/i);
  });
});

describe("the series board", () => {
  it("is the World Series line score, a link on every game with a full name", () => {
    const { getByRole, getByLabelText } = home();
    const board = getByLabelText("World Series, game by game");

    expect(within(board).getByRole("link", { name: "Game 1: Brewers 3, Rays 2" }).getAttribute("href")).toMatch(/^\/game\/\d{6,9}$/);
    expect(within(board).getByRole("link", { name: "Game 1: Rays 2, Brewers 3" })).toBeTruthy();
    expect(getByRole("link", { name: "Game 5: Brewers 4, Rays 1" }).getAttribute("href")).toBe("/game/849799");
  });

  it("has the games as columns, the wins at the end, and the club names beside their badges", () => {
    const { getByLabelText } = home();
    const board = getByLabelText("World Series, game by game");

    for (const heading of ["G1", "G2", "G3", "G4", "G5", "Wins"]) expect(text(board)).toContain(heading);
    expect(text(board)).toContain("Brewers");
    expect(text(board)).toContain("Rays");
    expect(board.querySelectorAll("[data-series-winner]")).toHaveLength(1);
    expect(board.querySelector("[data-series-winner]")?.textContent).toBe("4");
  });

  it("says who won the series and invites a click", () => {
    const { container } = home();

    expect(text(container)).toContain("World Series. Brewers win the series 4-1. Pick a game to see how its starters did.");
  });

  it("is left out, with no gap, when the index has no World Series game", () => {
    const index = { ...INDEX, games: INDEX.games.filter((g) => g.round !== "World Series") };
    const { container, queryByLabelText } = render(<HomeOffSeason index={index} />);

    expect(queryByLabelText("World Series, game by game")).toBeNull();
    expect(text(container)).not.toContain("Pick a game to see how its starters did.");
  });
});

describe("the notable duels", () => {
  it("are the top three notable games, most reasons first then newest, with a link to all of them", () => {
    const { getByRole, container } = home();
    const section = container.querySelector("[data-home-notable]") as HTMLElement;
    const rows = Array.from(section.querySelectorAll('a[href^="/game/"]'));

    expect(section.querySelector("h2")?.textContent).toBe("Notable duels of 2026");
    expect(rows).toHaveLength(3);
    expect(rows[0].getAttribute("href")).toBe("/game/849799");
    expect(rows[0].querySelectorAll("[data-reason]")).toHaveLength(3);
    expect(getByRole("link", { name: "All notable duels" }).getAttribute("href")).toBe("/notable");
  });

  it("sit in three columns from the large breakpoint, each game in its own card", () => {
    const { container } = home();
    const list = container.querySelector("[data-home-notable] [data-home-notable-list]") as HTMLElement;

    expect(list.className).toMatch(/bp-lg:grid-cols-3/);
    for (const row of Array.from(list.querySelectorAll('a[href^="/game/"]'))) expect(row.className).toMatch(/bp-lg:rounded-lg/);
  });

  it("are left out when no game in the index is notable", () => {
    const quiet = { ...INDEX, games: INDEX.games.map((g) => ({ ...g, notable: [] })), notable_count: 0 };
    const { container, queryByRole } = render(<HomeOffSeason index={quiet} />);

    expect(container.querySelector("[data-home-notable]")).toBeNull();
    expect(queryByRole("link", { name: "All notable duels" })).toBeNull();
  });
});

describe("how PitchCraft works", () => {
  it("has three cards, the last one saying only what release B shows", () => {
    const { container, queryByRole } = home();
    const section = container.querySelector("#how-pitchcraft-works") as HTMLElement;
    const cards = Array.from(section.querySelectorAll("[data-how-card]"));

    expect(section.querySelector("h2")?.textContent).toBe("How PitchCraft works");
    expect(queryByRole("link", { name: "Quality" })).toBeNull(); // no link to /quality until P3.2 (owner, 2026-11-15)
    expect(cards.map((card) => card.querySelector("h3")?.textContent)).toEqual(["Before the game", "Every claim is checked", "After the game"]);
    expect(text(cards[0])).toContain("A short report on both starters from public MLB data: arsenal, season figures, the lineup each one faces.");
    expect(text(cards[1])).toContain("Each statement is tested against the data before the report is published. No predictions, no betting.");
    expect(text(cards[2])).toContain("The final score and each starter's final line, from the box score.");
  });
});

describe("what the home does not have", () => {
  it("has no team directory (R5 is frozen) and no sentence that sounds live or says today", () => {
    const { container } = home();

    expect(text(container)).not.toMatch(/rotation|American League|National League|Find a team/);
    expect(text(container)).not.toMatch(/live data|today|upcoming|fetched|tonight/i);
    expect(container.querySelector('[data-mode="live"]')).toBeNull();
    expect(container.querySelector('[data-mode="demo"]')).toBeNull();
  });
});
