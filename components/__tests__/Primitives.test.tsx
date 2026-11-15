import { describe, expect, it } from "vitest";
import { fireEvent, render } from "@testing-library/react";

import Button from "@/components/ui/Button";
import Chip from "@/components/ui/Chip";
import EmptyState from "@/components/ui/EmptyState";
import FinalLine from "@/components/ui/FinalLine";
import GameRow from "@/components/ui/GameRow";
import Help from "@/components/ui/Help";
import Notice from "@/components/ui/Notice";
import ModeLine from "@/components/ModeLine";
import StatTile from "@/components/StatTile";
import TeamBadge from "@/components/TeamBadge";
import { GLOSSARY } from "@/lib/glossary";
import { REASON_LABELS } from "@/lib/notableReasons";
import type { ArchiveIndexRow } from "@/lib/types";

// U2 (docs/plans/R4-U.md): the primitives of the design system. Color never works alone: status, winner and team are each
// carried by a word or a shape as well; an unknown figure is a dash, never a zero.

describe("Chip", () => {
  it.each(["ok", "warn", "bad"] as const)("%s status chips carry an icon and a word", (variant) => {
    const { container } = render(<Chip variant={variant}>Held up</Chip>);

    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    expect(container.textContent).toBe("Held up");
  });

  it("is a span, not a control, and may wrap but never truncates", () => {
    const { container } = render(<Chip variant="reason" wrap>Both starters strike out batters at an above-average rate</Chip>);
    const chip = container.firstElementChild as HTMLElement;

    expect(chip.tagName).toBe("SPAN");
    expect(chip.className).toMatch(/whitespace-normal/);
    expect(chip.className).not.toMatch(/truncate|overflow-hidden/);
  });

  it("has a round variant for the board that does not also carry the light fill", () => {
    const { container } = render(<Chip variant="round-board">World Series</Chip>);
    const classes = (container.firstElementChild as HTMLElement).className;

    expect(classes).toMatch(/bg-board-2/);
    expect(classes).not.toMatch(/bg-brand-tint/);
  });

  it("has at least a 24 px height", () => {
    const { container } = render(<Chip variant="neutral">Final</Chip>);

    expect((container.firstElementChild as HTMLElement).className).toMatch(/min-h-6/);
  });
});

describe("Button", () => {
  it("navigates with a link and submits with a button", () => {
    const link = render(<Button href="/archive">Browse all 40 games</Button>);
    expect(link.getByRole("link", { name: "Browse all 40 games" }).getAttribute("href")).toBe("/archive");
    link.unmount();

    const submit = render(<Button type="submit">Clear filters</Button>);
    expect(submit.getByRole("button", { name: "Clear filters" }).getAttribute("type")).toBe("submit");
  });

  it.each(["primary", "signal", "secondary", "quiet"] as const)("%s is a 44 px target", (variant) => {
    const { container } = render(<Button href="/x" variant={variant}>Go</Button>);

    expect((container.firstElementChild as HTMLElement).className).toMatch(/min-h-tap/);
  });
});

describe("TeamBadge", () => {
  it("shows the abbreviation as decoration; the name is always next to it", () => {
    const { container } = render(<TeamBadge abbreviation="MIL" />);
    const badge = container.firstElementChild as HTMLElement;

    expect(badge.textContent).toBe("MIL");
    expect(badge.getAttribute("aria-hidden")).toBe("true");
    expect(badge.className).toMatch(/font-display/);
  });

  it("uses the team's approximate color, and the fallback token for an unknown club", () => {
    const known = render(<TeamBadge abbreviation="MIL" />);
    expect((known.container.firstElementChild as HTMLElement).style.background).not.toBe("");
    known.unmount();

    const unknown = render(<TeamBadge abbreviation={null} />);
    expect(unknown.container.textContent).toBe("");
  });

  it("has a thin ring on the board so navy clubs stay visible", () => {
    const { container } = render(<TeamBadge abbreviation="TB" onBoard />);

    expect((container.firstElementChild as HTMLElement).className).toMatch(/ring/);
  });
});

describe("StatTile", () => {
  it("shows a figure with its label, and a real zero as 0", () => {
    const { container } = render(<dl><StatTile label="Walks" value={0} /></dl>);

    expect(container.querySelector("dt")?.textContent).toBe("Walks");
    expect(container.querySelector("dd")?.textContent).toBe("0");
  });

  it("shows an unavailable figure as the dash with Not available, never as zero or blank", () => {
    const { container } = render(<dl><StatTile label="ERA" value={null} /></dl>);

    expect(container.querySelector("dd")?.textContent).toBe("—");
    expect(container.textContent).toContain("Not available");
    expect(container.textContent).not.toMatch(/\b0\b/);
  });

  it("marks a limited sample with its note, and a featured tile", () => {
    const limited = render(<dl><StatTile label="ERA" value="2.25" state="limited" note="12 batters faced" /></dl>);
    expect(limited.container.textContent).toContain("12 batters faced");
    expect(limited.container.firstElementChild?.innerHTML).toMatch(/bg-warn-tint/);
    limited.unmount();

    const featured = render(<dl><StatTile label="Strikeouts" value={11} state="featured" /></dl>);
    expect(featured.container.firstElementChild?.innerHTML).toMatch(/bg-signal/);
  });

  it("puts a Help button after the label of a term from the glossary", () => {
    const { getByRole } = render(<dl><StatTile label="WHIP" value="1.02" help="WHIP" /></dl>);

    expect(getByRole("button", { name: "What is WHIP?" })).toBeTruthy();
  });
});

describe("FinalLine", () => {
  const line = { innings_pitched: "8.0", hits: 3, earned_runs: 1, walks: 1, strikeouts: 11 };

  it("is a definition list of IP, H, ER, BB and K, each with its full name for assistive tech", () => {
    const { container } = render(<FinalLine line={line} />);
    const cells = Array.from(container.querySelectorAll("dl > div")).map((cell) => [
      cell.querySelector("dt")?.textContent,
      cell.querySelector("dd")?.textContent,
    ]);

    expect(cells).toEqual([
      ["IPInnings pitched", "8.0"],
      ["HHits", "3"],
      ["EREarned runs", "1"],
      ["BBWalks", "1"],
      ["KStrikeouts", "11"],
    ]);
    expect(container.querySelector("dl")?.getAttribute("aria-label")).toBe("Final line");
  });

  it("never shows a Pitches cell: the 1.0.0 files have no pitch count", () => {
    const { container } = render(<FinalLine line={line} />);

    expect(container.textContent).not.toMatch(/Pitches/);
    expect(container.querySelectorAll("dl > div")).toHaveLength(5);
  });

  it("shows a real 0 as 0 and a field the box score does not give as the dash", () => {
    const { container } = render(<FinalLine line={{ ...line, hits: 0, walks: null }} />);
    const values = Array.from(container.querySelectorAll("dd")).map((dd) => dd.textContent);

    expect(values).toEqual(["8.0", "0", "1", "—Not available", "11"]);
    const walks = container.querySelectorAll("dd")[3];
    expect(walks.querySelector('[aria-hidden="true"]')?.textContent).toBe("—");
    expect(walks.querySelector(".sr-only")?.textContent).toBe("Not available");
  });

  it("says Final line not available when there is no line at all", () => {
    const { container } = render(<FinalLine line={null} />);

    expect(container.textContent).toBe("Final line not available");
    expect(container.querySelector("dl")).toBeNull();
  });

  it("fills the cell a notable reason points at", () => {
    const { container } = render(<FinalLine line={line} featured={["strikeouts"]} />);
    const filled = Array.from(container.querySelectorAll("dl > div")).filter((cell) => /bg-signal/.test(cell.className));

    expect(filled).toHaveLength(1);
    expect(filled[0].querySelector("dd")?.textContent).toBe("11");
  });
});

describe("Help", () => {
  const term = "IP";

  it("is a labeled button, closed at first", () => {
    const { getByRole, queryByRole } = render(<Help term={term} />);
    const button = getByRole("button", { name: "What is IP?" });

    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(queryByRole("tooltip")).toBeNull();
  });

  it("opens on tap with the glossary definition word for word, and closes on a second tap", () => {
    const { getByRole, queryByRole } = render(<Help term={term} />);
    const button = getByRole("button", { name: "What is IP?" });

    fireEvent.click(button);
    expect(button.getAttribute("aria-expanded")).toBe("true");
    expect(getByRole("tooltip").textContent).toBe(`${term}${GLOSSARY[term]}`);

    fireEvent.click(button);
    expect(queryByRole("tooltip")).toBeNull();
  });

  it("opens on keyboard focus and hover, and closes on blur and leave", () => {
    const { getByRole, queryByRole } = render(<Help term={term} />);
    const button = getByRole("button", { name: "What is IP?" });

    fireEvent.focus(button);
    expect(getByRole("tooltip")).toBeTruthy();
    fireEvent.blur(button);
    expect(queryByRole("tooltip")).toBeNull();

    fireEvent.mouseEnter(button.parentElement as HTMLElement);
    expect(getByRole("tooltip")).toBeTruthy();
    fireEvent.mouseLeave(button.parentElement as HTMLElement);
    expect(queryByRole("tooltip")).toBeNull();
  });

  it("closes on Escape and on a tap outside", () => {
    const { getByRole, queryByRole } = render(<Help term={term} />);
    const button = getByRole("button", { name: "What is IP?" });

    fireEvent.click(button);
    fireEvent.keyDown(button, { key: "Escape" });
    expect(queryByRole("tooltip")).toBeNull();

    fireEvent.click(button);
    expect(getByRole("tooltip")).toBeTruthy();
    fireEvent.pointerDown(document.body);
    expect(queryByRole("tooltip")).toBeNull();
  });

  it("has a 44 px hit area", () => {
    const { getByRole } = render(<Help term={term} />);

    expect(getByRole("button", { name: "What is IP?" }).className).toMatch(/after:-inset/);
  });

  it("refuses a term that is not in the glossary", () => {
    // @ts-expect-error a term outside the glossary is a type error as well
    expect(() => render(<Help term="xwOBA" />)).toThrow();
  });
});

describe("Notice and EmptyState", () => {
  it("a notice is a status region with its tone's icon and the text", () => {
    const { getByRole } = render(<Notice tone="warn">Probable starter A; B started.</Notice>);
    const notice = getByRole("status");

    expect(notice.textContent).toBe("Probable starter A; B started.");
    expect(notice.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("an empty state says what is missing, offers one way forward, and draws the plate, dashed", () => {
    const { container, getByRole } = render(
      <EmptyState title="No games match these filters" action={<Button href="/archive" variant="secondary">Clear filters</Button>}>
        The Mariners did not play between Oct 23 and Oct 28.
      </EmptyState>,
    );

    expect(container.querySelector("h2")?.textContent).toBe("No games match these filters");
    expect(container.textContent).toContain("The Mariners did not play between Oct 23 and Oct 28.");
    expect(getByRole("link", { name: "Clear filters" }).getAttribute("href")).toBe("/archive");
    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    expect(container.firstElementChild?.className).toMatch(/border-dashed/);
  });
});

describe("ModeLine", () => {
  it("says live data with a comma, and the day of the fetch", () => {
    const { getByTestId } = render(<ModeLine dataMode="fetched_snapshot" fetchedAt="2026-07-04T12:00:00Z" />);

    expect(getByTestId("mode-line").textContent).toBe("Live data, fetched 2026-07-04");
    expect(getByTestId("mode-line").getAttribute("data-mode")).toBe("live");
  });

  it("says demo data with the warn style and a square dot, never live", () => {
    const { getByTestId } = render(<ModeLine dataMode="demo_cached" fetchedAt={null} />);

    expect(getByTestId("mode-line").textContent).toBe("Demo data: live data unavailable");
    expect(getByTestId("mode-line").getAttribute("data-mode")).toBe("demo");
  });

  it("says what the archive is in the off season, with the date written for people", () => {
    const { getByTestId } = render(<ModeLine archive={{ season: 2026, through: "2026-10-28" }} />);

    expect(getByTestId("mode-line").textContent).toBe("2026 season archive, final results through Oct 28, 2026");
    expect(getByTestId("mode-line").getAttribute("data-mode")).toBe("archive");
  });

  it("keeps the ISO date in a time element", () => {
    const { container } = render(<ModeLine archive={{ season: 2026, through: "2026-10-28" }} />);

    expect(container.querySelector("time")?.getAttribute("datetime")).toBe("2026-10-28");
  });
});

const GAME: ArchiveIndexRow = {
  game_pk: 849799,
  date: "2026-10-28",
  season: 2026,
  round: "World Series",
  series: { series_name: "World Series", game_number: 5, games_in_series: 7 },
  away: { id: 158, name: "Milwaukee Brewers", abbreviation: "MIL" },
  home: { id: 139, name: "Tampa Bay Rays", abbreviation: "TB" },
  status: "final",
  result: { away_runs: 4, home_runs: 1, winner: "away" },
  starters: { away: "Jacob Misiorowski", home: "Drew Rasmussen" },
  report: { origin: "published_live", as_of: "2026-10-27", starters_check: { away: "started", home: "started" } },
  notable: ["series_clincher", "strikeout_duel", "world_series"],
};

describe("GameRow", () => {
  it("is one link to the game page with the full accessible name", () => {
    const { getByRole } = render(<GameRow game={GAME} />);
    const link = getByRole("link", { name: "Brewers at Rays, Oct 28, 2026, final 4-1" });

    expect(link.getAttribute("href")).toBe("/game/849799");
  });

  it("lists the away side first, then the home side, with the starters and the runs", () => {
    const { container } = render(<GameRow game={GAME} />);
    const sides = Array.from(container.querySelectorAll("[data-side]"));

    expect(sides.map((side) => side.getAttribute("data-side"))).toEqual(["away", "home"]);
    expect(sides[0].textContent).toContain("Brewers");
    expect(sides[0].textContent).toContain("Jacob Misiorowski");
    expect(sides[0].textContent).toContain("4");
    expect(sides[1].textContent).toContain("Rays");
    expect(sides[1].textContent).toContain("Drew Rasmussen");
    expect(sides[1].textContent).toContain("1");
  });

  it("marks the winner by shape and weight, not by color alone, and only the winner", () => {
    const { container } = render(<GameRow game={GAME} />);
    const [away, home] = Array.from(container.querySelectorAll("[data-side]"));

    expect(away.getAttribute("data-winner")).toBe("true");
    expect(home.hasAttribute("data-winner")).toBe(false);
    expect(away.querySelector("[data-runs]")?.className).toMatch(/before:border-l-stitch|before:/);
    expect(away.querySelector("[data-team-name]")?.className).toMatch(/font-bold/);
  });

  it("marks the home side when it won", () => {
    const home = { ...GAME, result: { away_runs: 2, home_runs: 3, winner: "home" as const } };
    const { container } = render(<GameRow game={home} />);

    expect(container.querySelector('[data-side="home"]')?.getAttribute("data-winner")).toBe("true");
    expect(container.querySelector('[data-side="away"]')?.hasAttribute("data-winner")).toBe(false);
  });

  it("shows a measured 0 as 0", () => {
    const shutout = { ...GAME, result: { away_runs: 3, home_runs: 0, winner: "away" as const } };
    const { container } = render(<GameRow game={shutout} />);

    expect(container.querySelector('[data-side="home"] [data-runs]')?.textContent).toBe("0");
  });

  it("shows a starter the index does not name as the dash, not a guessed name", () => {
    const { container } = render(<GameRow game={{ ...GAME, starters: { away: null, home: "Drew Rasmussen" } }} />);

    expect(container.querySelector('[data-side="away"]')?.textContent).toContain("—");
  });

  it("shows the round, the game number and the date written for people", () => {
    const { container } = render(<GameRow game={GAME} />);

    expect(container.textContent).toContain("Oct 28, 2026");
    expect(container.textContent).toContain("World Series");
    expect(container.textContent).toContain("Game 5");
  });

  it("shows the reasons of the row as catalog labels, and only those", () => {
    const { container } = render(<GameRow game={GAME} />);
    const chips = Array.from(container.querySelectorAll("[data-reason]")).map((chip) => chip.textContent);

    expect(chips).toEqual([REASON_LABELS.series_clincher, REASON_LABELS.strikeout_duel, REASON_LABELS.world_series]);
    expect(REASON_LABELS).toEqual({
      series_clincher: "Series-ending game",
      strikeout_duel: "Strikeout duel",
      veteran_duel: "Veteran duel",
      world_series: "World Series game",
    });
  });

  it("shows no reason chips for a game without a tag", () => {
    const { container } = render(<GameRow game={{ ...GAME, notable: [] }} />);

    expect(container.querySelector("[data-reason]")).toBeNull();
  });

  it("limits the reasons shown and counts the rest", () => {
    const { container } = render(<GameRow game={GAME} maxReasons={1} />);

    expect(Array.from(container.querySelectorAll("[data-reason]")).map((chip) => chip.textContent)).toEqual(["Series-ending game"]);
    expect(container.querySelector("[data-more-reasons]")?.textContent).toBe("+2");
  });

  it("names the club by its nickname, and by its full name when the nickname is unknown", () => {
    const unknown = { ...GAME, home: { id: 1, name: "Expansion City", abbreviation: null } };
    const { getByRole } = render(<GameRow game={unknown} />);

    expect(getByRole("link", { name: "Brewers at Expansion City, Oct 28, 2026, final 4-1" })).toBeTruthy();
  });

  it("the whole row is the target and is at least 44 px tall", () => {
    const { getByRole } = render(<GameRow game={GAME} />);

    expect(getByRole("link").className).toMatch(/block/);
    expect(getByRole("link").className).toMatch(/min-h-tap/);
  });
});
