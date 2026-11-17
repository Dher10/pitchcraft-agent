import { todayInNewYork } from "@/lib/format";
import type { PitchCraftData } from "@/lib/types";

export type SeasonMode = "in_season" | "off_season";

/**
 * Is the site in season? One fact, one function (docs/plans/R4-U.md, U2). It is in season only when the daily file is a
 * live one, its run targeted today (New York, the zone of a game's official date) and it found at least one game.
 * Every other state is the off season: a demo or fallback file, a stale file, a day without games, a file without a
 * run record. A day without games inside a season reads as off season until Today in season is built (frozen, D67).
 */
export function seasonMode(daily: Pick<PitchCraftData, "metadata">, now: Date = new Date()): SeasonMode {
  const { data_mode, data_status } = daily.metadata;
  if (data_mode !== "fetched_snapshot") return "off_season";
  const run = data_status?.live_run;
  if (!run || run.target_date !== todayInNewYork(now)) return "off_season";
  return run.games_live >= 1 ? "in_season" : "off_season";
}
