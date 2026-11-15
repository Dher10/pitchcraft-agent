import { REASON_ORDER } from "@/lib/archiveQuery";
import { NOTABLE_COPY } from "@/lib/copy/notable";
import { REASON_DISPLAY_ORDER, REASON_LABELS } from "@/lib/notableReasons";
import type { ArchiveIndex, ArchiveIndexRow, ArchiveNotableReason } from "@/lib/types";

/**
 * The notable page's list, from the URL and the index alone (docs/plans/R4-U.md, U5): `/notable?reason=strikeout_duel&reason=...`.
 * The list is the games with at least one reason; picking reasons narrows it, and a game must have every reason picked.
 * Most reasons first, then the newest. A value that is not a known reason is ignored and never echoed.
 */

export interface NotableQuery {
  reasons: ArchiveNotableReason[];
}

type Params = Record<string, string | string[] | undefined>;

/** Read the URL: the known reasons, once each, in the index's order. Every other parameter is ignored. */
export function parseNotableQuery(params: Params): NotableQuery {
  const raw = params.reason === undefined ? [] : Array.isArray(params.reason) ? params.reason : [params.reason];
  return { reasons: REASON_ORDER.filter((reason) => raw.includes(reason)) };
}

/** The notable games that have every reason picked: most reasons first, then the newest. */
export function notableGames(index: ArchiveIndex, query: NotableQuery): ArchiveIndexRow[] {
  return index.games
    .filter((game) => game.notable.length > 0 && query.reasons.every((reason) => game.notable.includes(reason)))
    .sort((a, b) => b.notable.length - a.notable.length || (a.date < b.date ? 1 : a.date > b.date ? -1 : b.game_pk - a.game_pk));
}

/**
 * The count on a pill: the size of the list you get by picking that reason, given the reasons already picked. `null` is
 * "All notable games": every game with at least one reason, whatever is picked.
 */
export function notableCount(index: ArchiveIndex, query: NotableQuery, reason: ArchiveNotableReason | null): number {
  if (reason === null) return index.games.filter((game) => game.notable.length > 0).length;
  return index.games.filter((game) => query.reasons.every((picked) => game.notable.includes(picked)) && game.notable.includes(reason)).length;
}

/** The games that carry a reason, for the rule's own count on the page. */
export function ruleCount(index: ArchiveIndex, reason: ArchiveNotableReason): number {
  return index.games.filter((game) => game.notable.includes(reason)).length;
}

/** The URL of the notable page for some reasons: a fixed order, only known reasons. */
export function notableHref(reasons: ArchiveNotableReason[]): string {
  const picked = REASON_ORDER.filter((reason) => reasons.includes(reason));
  return picked.length === 0 ? "/notable" : `/notable?${picked.map((reason) => `reason=${reason}`).join("&")}`;
}

/** The count line: how many notable games are shown, which reasons narrow them, and the order. */
export function countSentence(index: ArchiveIndex, query: NotableQuery): string {
  const total = notableCount(index, query, null);
  const head =
    query.reasons.length === 0
      ? NOTABLE_COPY.countAll(total)
      : NOTABLE_COPY.countPicked(
          notableGames(index, query).length,
          total,
          REASON_DISPLAY_ORDER.filter((reason) => query.reasons.includes(reason))
            .map((reason) => REASON_LABELS[reason])
            .join(", "),
        );
  return `${head} ${NOTABLE_COPY.orderTail}`;
}
