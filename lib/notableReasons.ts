import type { ArchiveNotableReason } from "@/lib/types";

/**
 * The notable reasons, in one table (D67 point 3; R4 section 4.6): the short label a chip and a pill print, and the rule in
 * plain words that the notable page explains. The label, the rule and the count on the page all come from here and from the
 * index's own tags, so a chip, a pill and a rule can never disagree. A game prints a reason only when its index row carries
 * the tag. The order is the design's (strikeout duel, veteran duel, series-ending game, World Series game).
 */
export interface NotableReason {
  key: ArchiveNotableReason;
  label: string;
  /** The rule in plain words; `veteranMin` is the threshold the index was built with (D66, R4-D7). */
  rule: (veteranMin: number) => string;
}

export const NOTABLE_REASONS: readonly NotableReason[] = [
  {
    key: "strikeout_duel",
    label: "Strikeout duel",
    rule: () => "Both starters strike out batters at an above-average rate: a strikeout rate of 25% or more over a full sample, before the game.",
  },
  {
    key: "veteran_duel",
    label: "Veteran duel",
    rule: (veteranMin) => `Both starters had pitched in at least ${veteranMin} earlier MLB seasons.`,
  },
  { key: "series_clincher", label: "Series-ending game", rule: () => "The game decided its series." },
  { key: "world_series", label: "World Series game", rule: () => "Every World Series game is on the list." },
];

export const REASON_DISPLAY_ORDER: ArchiveNotableReason[] = NOTABLE_REASONS.map((reason) => reason.key);

export const REASON_LABELS = Object.fromEntries(NOTABLE_REASONS.map((reason) => [reason.key, reason.label])) as Record<
  ArchiveNotableReason,
  string
>;

export function reasonRule(key: ArchiveNotableReason, veteranMin: number): string {
  const reason = NOTABLE_REASONS.find((candidate) => candidate.key === key);
  if (!reason) throw new Error("not_a_notable_reason");
  return reason.rule(veteranMin);
}
