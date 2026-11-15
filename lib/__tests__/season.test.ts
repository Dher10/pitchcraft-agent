import { describe, expect, it } from "vitest";
import { seasonMode } from "@/lib/season";
import type { PitchCraftData } from "@/lib/types";

// The season switch is one tested function (docs/plans/R4-U.md, U2): the site is in season only when the daily job
// ran for today (New York time) and found at least one game; every other state is the off season.

type Daily = Pick<PitchCraftData, "metadata">;

function daily(overrides: {
  mode?: string;
  live_run?: Partial<NonNullable<NonNullable<PitchCraftData["metadata"]["data_status"]>["live_run"]>> | null;
}): Daily {
  const live_run =
    overrides.live_run === null
      ? null
      : {
          status: "ok",
          run_at: "2026-10-28T15:00:00+00:00",
          target_date: "2026-10-28",
          as_of: "2026-10-27",
          games_scheduled: 1,
          games_live: 1,
          errors: [],
          warnings: [],
          ...overrides.live_run,
        };
  return { metadata: { data_mode: overrides.mode ?? "fetched_snapshot", data_status: { mode: overrides.mode ?? "fetched_snapshot", reason: null, live_run } } } as Daily;
}

const NOON_ON_THE_28TH = new Date("2026-10-28T16:00:00Z");

describe("seasonMode", () => {
  it("is in season for a live file whose run targets today and found a game", () => {
    expect(seasonMode(daily({}), NOON_ON_THE_28TH)).toBe("in_season");
  });

  it("is off season for a live file that targets another day (a stale file)", () => {
    expect(seasonMode(daily({ live_run: { target_date: "2026-10-27" } }), NOON_ON_THE_28TH)).toBe("off_season");
    expect(seasonMode(daily({}), new Date("2026-10-29T16:00:00Z"))).toBe("off_season");
  });

  it("is off season for a no_games run, even for today", () => {
    expect(
      seasonMode(daily({ live_run: { status: "no_games", games_scheduled: 0, games_live: 0 } }), NOON_ON_THE_28TH),
    ).toBe("off_season");
  });

  it("is off season for a demo or fallback file, whatever its run record says", () => {
    for (const mode of ["demo_cached", "demo_fallback", "something_new", ""]) {
      expect(seasonMode(daily({ mode }), NOON_ON_THE_28TH)).toBe("off_season");
    }
  });

  it("is off season when the file has no run record or no target date", () => {
    expect(seasonMode(daily({ live_run: null }), NOON_ON_THE_28TH)).toBe("off_season");
    expect(seasonMode(daily({ live_run: { target_date: null } }), NOON_ON_THE_28TH)).toBe("off_season");
  });

  it("uses the New York date: 01:30 UTC on the 29th is still the 28th there", () => {
    expect(seasonMode(daily({}), new Date("2026-10-29T01:30:00Z"))).toBe("in_season");
    expect(seasonMode(daily({}), new Date("2026-10-29T05:00:00Z"))).toBe("off_season");
  });

  it("is off season when no game was found, even with games scheduled", () => {
    expect(seasonMode(daily({ live_run: { games_scheduled: 2, games_live: 0 } }), NOON_ON_THE_28TH)).toBe("off_season");
  });
});
