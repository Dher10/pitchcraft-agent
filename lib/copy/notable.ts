/**
 * The text of the notable page (docs/plans/R4-U.md, 5.5). One catalog, so the Spanish release adds a second column. Each sentence
 * that asserts something about data is registered in docs/DATA_CONTRACT.md, section 3.3.
 */
export const NOTABLE_COPY = {
  title: "Notable duels of 2026",
  lede: "Starting-pitcher matchups of the 2026 postseason, each with the reasons it stands out. Pick one or more reasons to narrow the list.",
  reasonLabel: "Notable reason",
  all: "All notable games",
  clear: "Clear",
  showAll: (n: number) => `Show all ${n}`,
  orderTail: "Most reasons first, then newest.",
  countPicked: (shown: number, total: number, labels: string) => `Showing ${shown} of ${total} notable games: ${labels}.`,
  countAll: (total: number) => `Showing ${total} notable games.`,
  rulesTitle: "How games are chosen",
  rulesIntro: (qualify: number, total: number) =>
    `A game is here when at least one of these is true. Fixed rules, computed from the data before the list was built; who won is not one of them. ${qualify} of the ${total} postseason games qualify, so pick a reason to narrow the list.`,
  gamesWord: (n: number) => (n === 1 ? "game" : "games"),
  noEveryReason: "No games have every reason picked.",
  noRule: "No game met a rule",
  browse: (n: number) => `Browse all ${n} games`,
} as const;
