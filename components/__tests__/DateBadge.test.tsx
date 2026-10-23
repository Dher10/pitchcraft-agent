import { afterEach, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
import GameCarousel from "@/components/GameCarousel";
import type { Matchup } from "@/lib/types";
import { makeMatchup } from "./fixtures";

// P0.15-D2.5b (F12, contract 3.3, rule 7): the badge says "Today" when the game's date is today in America/New_York, not
// when it is the UTC date of the machine that renders the page (the old code compared with `toISOString()`).

function badge(date: string, today?: string): string {
  const matchup: Matchup = { ...makeMatchup({}), date, is_featured: false };
  const { container } = render(
    <GameCarousel matchups={[matchup]} archive={[]} featuredId="other" selectedId={matchup.id} onSelect={() => {}} today={today} />,
  );
  return container.querySelector("button span.text-neutral-400")?.textContent ?? "";
}

afterEach(() => {
  vi.useRealTimers();
});

describe("the date badge of a game", () => {
  it("says Today for the date given as today, and the date for any other", () => {
    expect(badge("2026-07-04", "2026-07-04")).toBe("Today");
    expect(badge("2026-07-05", "2026-07-04")).toBe("2026-07-05");
    expect(badge("2026-07-03", "2026-07-04")).toBe("2026-07-03");
  });

  it("reads the clock in New York: at 01:30 UTC on the 5th the 4th is still today and the 5th is not", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-05T01:30:00Z"));

    expect(badge("2026-07-04")).toBe("Today");
    expect(badge("2026-07-05")).toBe("2026-07-05"); // the UTC date: the old code said Today here
  });

  it("reads winter time in winter: at 04:30 UTC on January 5th the 4th is still today", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-05T04:30:00Z"));

    expect(badge("2026-01-04")).toBe("Today");
    expect(badge("2026-01-05")).toBe("2026-01-05");
  });

  it("control: in the middle of the day both zones agree", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-05T16:00:00Z"));

    expect(badge("2026-07-05")).toBe("Today");
    expect(badge("2026-07-04")).toBe("2026-07-04");
  });
});
