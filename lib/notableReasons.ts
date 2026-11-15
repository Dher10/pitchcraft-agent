import type { ArchiveNotableReason } from "@/lib/types";

/**
 * The short label of each notable reason (D67 point 3; R4 section 4.6). Each is a registered claim: a game prints a
 * label only when its index row carries the tag. U5 adds the rule text and the counts beside these labels, from the
 * same table, so a label and its rule can never disagree.
 */
export const REASON_LABELS: Record<ArchiveNotableReason, string> = {
  series_clincher: "Series-ending game",
  strikeout_duel: "Strikeout duel",
  veteran_duel: "Veteran duel",
  world_series: "World Series game",
};
