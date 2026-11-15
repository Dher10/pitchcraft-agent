import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";

import GameNotFound from "@/components/game/GameNotFound";
import GameView from "@/components/game/GameView";
import { parseArchiveIndex } from "@/lib/archiveIndex";
import { gameMetadata, parseArchiveGame, seriesNeighbors } from "@/lib/archiveGame";

// U3 (docs/plans/R4-U.md, 4 and 5.3): the game page after the game, on the 1.0.0 file. State, score, series and origin come
// from the envelope, never from the embedded payload; the report appears only in one block labelled by its origin.

// A JSON value read from a file whose shape is checked field by field below: one named alias, not scattered `any`.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Loose = Record<string, any>;

const ARCHIVE = path.join(process.cwd(), "public/data/archive");
const FILES = readdirSync(path.join(ARCHIVE, "games")).filter((name) => name.endsWith(".json"));
const INDEX = parseArchiveIndex(JSON.parse(readFileSync(path.join(ARCHIVE, "index-2026.json"), "utf8")));
const raw = (pk: string | number) => JSON.parse(readFileSync(path.join(ARCHIVE, "games", `${pk}.json`), "utf8"));
const LIVE = 849799; // World Series game 5, published live
const RECONSTRUCTED = INDEX.games.find((row) => row.report.origin === "reconstructed")!.game_pk;

function view(pk: number | Loose, options: { index?: boolean } = {}) {
  const file = typeof pk === "number" ? raw(pk) : pk;
  const game = parseArchiveGame(file, file.game_pk);
  const row = options.index === false ? null : (INDEX.games.find((r) => r.game_pk === game.game_pk) ?? null);
  const { previous, next } = options.index === false ? { previous: null, next: null } : seriesNeighbors(INDEX, game.game_pk);
  return render(<GameView game={game} row={row} previous={previous} next={next} />);
}

const text = (container: HTMLElement) => container.textContent ?? "";

describe("the score board", () => {
  it("names the game for assistive tech and shows the final score with its accessible name", () => {
    const { container, getByRole } = view(LIVE);

    expect(container.querySelector("h1")?.textContent).toBe("Brewers at Rays, World Series Game 5");
    expect(getByRole("img", { name: "Final score: Brewers 4, Rays 1" })).toBeTruthy();
    expect(text(container)).toContain("Final.");
  });

  it("shows the round, the game number, the date and the venue", () => {
    const { container } = view(LIVE);

    expect(text(container)).toContain("World Series");
    expect(text(container)).toContain("Game 5, Oct 28, 2026, Tropicana Field");
  });

  it("says who won the series, from the envelope's series line", () => {
    const { container } = view(LIVE);

    expect(text(container)).toContain("Brewers win the series 4-1.");
  });

  it("says who leads and when the series is tied, in the closed forms", () => {
    const leads = INDEX.games.find((row) => raw(row.game_pk).series.after.includes("leads"))!;
    const tied = INDEX.games.find((row) => raw(row.game_pk).series.after.startsWith("Series tied"))!;
    const leadsAfter: string = raw(leads.game_pk).series.after;
    const tiedAfter: string = raw(tied.game_pk).series.after;

    const a = view(leads.game_pk);
    expect(text(a.container)).toContain(` lead the series ${leadsAfter.split(" ")[2]}.`);
    a.unmount();

    const b = view(tied.game_pk);
    expect(text(b.container)).toContain(`Series tied ${tiedAfter.split(" ")[2]}.`);
  });

  it("says nothing about the series when the line is not one of the closed forms", () => {
    const file = raw(LIVE);
    file.series.after = "something else";
    const { container } = view(file);

    expect(text(container)).not.toContain("something else");
    expect(text(container)).not.toMatch(/win the series|lead the series|Series tied/);
  });

  it("states the origin of a report published live", () => {
    const { container } = view(LIVE);

    expect(text(container)).toContain(
      "The report was published before the game, on Oct 28, 2026. The final score and the final lines were added after the game, from the box score.",
    );
  });

  it("states the origin of a report rebuilt after the game, and never says published", () => {
    const row = INDEX.games.find((r) => r.game_pk === RECONSTRUCTED)!;
    const { container } = view(RECONSTRUCTED);
    const outsideReportText = stripReportText(container);

    expect(text(container)).toContain(
      `The report was written after the game, from data through ${formatLong(row.report.as_of)}. The final score and the final lines are from the box score.`,
    );
    expect(outsideReportText).not.toMatch(/published/i);
  });

  it("marks the winner and not the loser", () => {
    const { container } = view(LIVE);

    expect(container.querySelector('[data-score-side="away"]')?.getAttribute("data-won")).toBe("true");
    expect(container.querySelector('[data-score-side="home"]')?.hasAttribute("data-won")).toBe(false);
  });

  it("links back to the archive", () => {
    const { getByRole } = view(LIVE);

    expect(getByRole("link", { name: "Back to the archive" }).getAttribute("href")).toBe("/archive");
  });
});

function formatLong(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return `${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1]} ${d}, ${y}`;
}

/** The text of the page without the paragraphs of the report itself: what the page says in its own words. */
function stripReportText(container: HTMLElement): string {
  const clone = container.cloneNode(true) as HTMLElement;
  clone.querySelectorAll("[data-report-text]").forEach((node) => node.remove());
  return text(clone);
}

describe("why this game is notable", () => {
  it("shows the reasons of its index row, as catalog labels", () => {
    const { container, getByLabelText } = view(LIVE);
    const section = getByLabelText("Why this game is notable");

    expect(section.textContent).toContain("Why this game is notable");
    expect(Array.from(section.querySelectorAll("[data-reason]")).map((chip) => chip.textContent)).toEqual([
      "Series-ending game",
      "Strikeout duel",
      "World Series game",
    ]);
    expect(container.querySelectorAll("[data-reason]")).toHaveLength(3);
  });

  it("is absent for a game with no tag, and for a page with no index row", () => {
    const quiet = INDEX.games.find((row) => row.notable.length === 0)!;
    const a = view(quiet.game_pk);
    expect(a.container.querySelector('[aria-label="Why this game is notable"]')).toBeNull();
    a.unmount();

    const b = view(LIVE, { index: false });
    expect(b.container.querySelector('[aria-label="Why this game is notable"]')).toBeNull();
  });
});

describe("how the starters did", () => {
  it("shows each starter's head, with the club and role, and his final line from the box score", () => {
    const { container } = view(LIVE);
    const cards = container.querySelectorAll("[data-starter]");

    expect(cards).toHaveLength(2);
    expect(cards[0].textContent).toContain("Brewers, away starter");
    expect(cards[0].textContent).toContain("Jacob Misiorowski");
    expect(cards[1].textContent).toContain("Rays, home starter");
    expect(cards[1].textContent).toContain("Drew Rasmussen");
    const values = (card: Element) => Array.from(card.querySelectorAll("dl dd")).map((dd) => dd.textContent);
    expect(values(cards[0])).toEqual(["5.2", "2", "0", "1", "2"]);
    expect(values(cards[1])).toEqual(["4.0", "2", "1", "0", "4"]);
  });

  it("labels the line and explains it with the glossary's definition of Final line", () => {
    const { container, getAllByRole } = view(LIVE);
    const card = container.querySelector("[data-starter]") as HTMLElement;

    expect(card.textContent).toContain("Final line");
    expect(getAllByRole("button", { name: "What is Final line?" })).toHaveLength(2);
  });

  it("has no pitch count and no summary sentence: 1.0.0 cannot support them", () => {
    const { container } = view(LIVE);

    expect(text(container)).not.toMatch(/Pitches|Game Score|Swings and misses|First-pitch/);
    expect(container.querySelectorAll("[data-starter] p[data-summary]")).toHaveLength(0);
  });

  it("shows the hand and style the report gave when the probable starter started", () => {
    const { container } = view(LIVE);

    expect(container.querySelector("[data-starter]")?.textContent).toContain("Right-handed, four-seam starter");
  });

  it("shows a real 0 as 0 and a missing field as the dash", () => {
    const file = raw(LIVE);
    file.final_line.away.walks = null;
    const { container } = view(file);
    const cell = (label: string) =>
      Array.from(container.querySelectorAll("[data-starter]:first-of-type dl > div")).find((div) => div.textContent?.includes(label))?.querySelector("dd")?.textContent;

    expect(cell("Earned runs")).toBe("0");
    expect(cell("Walks")).toBe("—Not available");
  });

  it("says the probable starter did not start, and shows the pitcher who did", () => {
    const file = raw(LIVE);
    file.starters_check.away = "did_not_start";
    file.starters_check.actual.away = { id: 1, name: "Someone Else" };
    const { container } = view(file);
    const card = container.querySelector("[data-starter]") as HTMLElement;

    expect(card.textContent).toContain("Someone Else");
    expect(card.textContent).toContain("Probable starter Jacob Misiorowski; Someone Else started.");
    // The report's style and hand describe the probable starter, so they are not shown for the one who started.
    expect(card.textContent).not.toContain("four-seam starter");
  });

  it("says the starter is not confirmed when the boxscore could not say, with no name and no line", () => {
    const file = raw(LIVE);
    file.starters_check.away = "unknown";
    file.starters_check.actual.away = null;
    file.final_line.away = null;
    const { container } = view(file);
    const card = container.querySelector("[data-starter]") as HTMLElement;

    expect(card.textContent).toContain("Starter not confirmed");
    expect(card.textContent).toContain("Final line not available");
    expect(card.textContent).not.toContain("Jacob Misiorowski");
  });

  it("says nothing extra when the starter started", () => {
    const { container } = view(LIVE);

    expect(container.querySelector("[data-starter] [role=status]")).toBeNull();
  });
});

describe("the report as published", () => {
  it("is one block with its origin label: published live", () => {
    const { container } = view(LIVE);
    const block = container.querySelector("[data-report-block]") as HTMLElement;

    expect(block.querySelector("h2")?.textContent).toBe("The report");
    expect(block.textContent).toContain("Published before the game, on Oct 28, 2026");
  });

  it("is one block with its origin label: written after the game", () => {
    const row = INDEX.games.find((r) => r.game_pk === RECONSTRUCTED)!;
    const { container } = view(RECONSTRUCTED);
    const block = container.querySelector("[data-report-block]") as HTMLElement;

    expect(block.textContent).toContain(`Written after the game, from data through ${formatLong(row.report.as_of)}`);
    expect(block.textContent).not.toContain("Published before the game");
  });

  it("shows the report's own paragraphs, its lineup tiles and the three questions as asked", () => {
    const file = raw(LIVE);
    const sections = file.payload.matchups[0].report.sections;
    const { container } = view(LIVE);
    const block = container.querySelector("[data-report-block]") as HTMLElement;

    expect(block.textContent).toContain(sections[0].body);
    const questions = Array.from(block.querySelectorAll("[data-question]")).map((q) => q.textContent);
    expect(questions).toEqual(sections.find((s: Loose) => s.bullets).bullets.map((q: string) => `We asked: ${q}`));
    expect(block.querySelectorAll("[data-lineup]")).toHaveLength(2);
    expect(block.querySelector("[data-lineup]")?.textContent).toContain(".759");
  });

  it("does not answer the questions, and does not promise answers", () => {
    const { container } = view(LIVE);
    const block = text(container.querySelector("[data-report-block]") as HTMLElement);

    expect(block).not.toMatch(/answer|Yes\.|Partly\.|Held up|Did not hold up|Each question gets/i);
  });

  it("counts the critic's checks made before publishing, and nothing made after the game", () => {
    const { container } = view(LIVE);
    const block = text(container.querySelector("[data-report-block]") as HTMLElement);

    expect(block).toContain("Before publishing, 7 claims in the report were tested against the data: none unsupported, 1 with a warning.");
    expect(block).not.toMatch(/After the game, \d/);
  });

  it("does not link to the report as published", () => {
    const { container } = view(LIVE);

    expect(text(container)).not.toMatch(/Read the report as published/);
    expect(Array.from(container.querySelectorAll("a")).map((a) => a.getAttribute("href")).join(" ")).not.toMatch(/github|commit/);
  });
});

describe("the games of the series", () => {
  it("links to the previous game and says it is the last of the series", () => {
    const { container, getByRole } = view(LIVE);
    const nav = container.querySelector('nav[aria-label="Games of this series"]') as HTMLElement;
    const previous = INDEX.games.find((row) => row.series.series_name === "World Series" && row.series.game_number === 4)!;

    expect(getByRole("link", { name: /Previous game/ }).getAttribute("href")).toBe(`/game/${previous.game_pk}`);
    expect(nav.textContent).toContain("Game 4, Oct 27");
    expect(nav.textContent).toContain("Last game of the series");
    expect(nav.textContent).not.toContain("Next game");
  });

  it("links to the next game and says it is the first of the series", () => {
    const first = INDEX.games.find((row) => row.series.series_name === "World Series" && row.series.game_number === 1)!;
    const { container, getByRole } = view(first.game_pk);
    const nav = container.querySelector('nav[aria-label="Games of this series"]') as HTMLElement;

    expect(getByRole("link", { name: /Next game/ }).getAttribute("href")).toMatch(/^\/game\/\d{6,9}$/);
    expect(nav.textContent).toContain("First game of the series");
    expect(nav.textContent).toContain("Game 2,");
  });

  it("says nothing about the end of the series when the file does not say it is the end", () => {
    const file = raw(LIVE);
    file.series.over = false;
    const game = parseArchiveGame(file, LIVE);
    const { container } = render(<GameView game={game} row={INDEX.games.find((r) => r.game_pk === LIVE) ?? null} previous={null} next={null} />);
    const nav = container.querySelector('nav[aria-label="Games of this series"]') as HTMLElement;

    expect(nav.textContent).not.toContain("Last game of the series");
    expect(nav.textContent).not.toContain("First game of the series");
  });

  it("is absent when the page has no index to find the series in", () => {
    const { container } = view(LIVE, { index: false });

    expect(container.querySelector('nav[aria-label="Games of this series"]')).toBeNull();
  });
});

describe("what the embedded payload says about the game before it was played stays inside the report block", () => {
  const FORBIDDEN = /upcoming|\blive\b|live data|today|before first pitch|fetched/i;

  it.each(FILES.map((name) => [name]))("%s: nothing outside block 4 sounds live or upcoming", (name) => {
    const pk = Number(name.replace(".json", ""));
    const { container } = view(pk);
    const clone = container.cloneNode(true) as HTMLElement;
    clone.querySelector("[data-report-block]")?.remove();

    expect(text(clone), name).not.toMatch(FORBIDDEN);
  });

  it.each(FILES.map((name) => [name]))("%s: the page's own words never say published unless the report was", (name) => {
    const pk = Number(name.replace(".json", ""));
    const kind = raw(pk).origin.kind;
    const { container } = view(pk);
    const own = stripReportText(container);

    if (kind === "reconstructed") expect(own, name).not.toMatch(/published/i);
    else expect(own, name).toMatch(/published before the game/i);
  });

  it("the block itself carries the report's own sentences, even those that say before first pitch", () => {
    const withSentence = FILES.map((name) => Number(name.replace(".json", ""))).find((pk) =>
      /before first pitch/i.test(JSON.stringify(raw(pk).payload.matchups[0].report)),
    )!;
    const { container } = view(withSentence);

    expect(text(container.querySelector("[data-report-block]") as HTMLElement)).toMatch(/before first pitch/i);
  });
});

describe("every one of the 40 real files renders", () => {
  it.each(FILES.map((name) => [name]))("%s", (name) => {
    const pk = Number(name.replace(".json", ""));
    const { container } = view(pk);

    expect(container.querySelector("h1")).not.toBeNull();
    expect(container.querySelectorAll("[data-starter]")).toHaveLength(2);
    expect(container.querySelector("[data-report-block]")).not.toBeNull();
  });
});

describe("the page title and description", () => {
  it("names the game, the round and the date, and states the score", () => {
    const meta = gameMetadata(parseArchiveGame(raw(LIVE), LIVE));

    expect(meta.title).toBe("Brewers at Rays, World Series Game 5, Oct 28, 2026");
    expect(meta.description).toBe("Final score: Brewers 4, Rays 1. How the starters did and the report for the game.");
  });
});

describe("the page title and description never say published (rule 7), for either origin", () => {
  it.each(FILES.map((name) => [name]))("%s", (name) => {
    const pk = Number(name.replace(".json", ""));
    const meta = gameMetadata(parseArchiveGame(raw(pk), pk), INDEX.games.find((r) => r.game_pk === pk) ?? null);

    expect(`${meta.title} ${meta.description}`, name).not.toMatch(/published|live|upcoming|today/i);
  });
});

describe("the page for a game that is not there", () => {
  it("is an empty state with the way back, not a blank page", () => {
    const { container, getByRole } = render(<GameNotFound />);

    expect(container.querySelector("h2")?.textContent).toBe("We could not find that game");
    expect(getByRole("link", { name: "Back to the archive" }).getAttribute("href")).toBe("/archive");
    expect(getByRole("link", { name: "Notable duels of 2026" }).getAttribute("href")).toBe("/notable");
  });
});
