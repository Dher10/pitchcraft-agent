import { formatMonthDay } from "@/lib/format";

/**
 * The text of the game page (docs/plans/R4-U.md, 5.3). One catalog, so the Spanish release adds a second column. A sentence that
 * asserts something about data is registered in docs/DATA_CONTRACT.md, section 3.3, with the condition that prints it.
 */
export const GAME_COPY = {
  back: "Back to the archive",
  notableLabel: "Why this game is notable",
  startersTitle: "How the starters did",
  final: "Final.",
  hidden: (away: string, home: string, round: string, game: number) => `${away} at ${home}, ${round} Game ${game}`,
  scoreName: (away: string, awayRuns: number, home: string, homeRuns: number) => `Final score: ${away} ${awayRuns}, ${home} ${homeRuns}`,
  head: (game: number, date: string, venue: string | null) => (venue ? `Game ${game}, ${date}, ${venue}` : `Game ${game}, ${date}`),
  seriesWon: (name: string, wins: number, losses: number) => `${name} win the series ${wins}-${losses}.`,
  seriesLed: (name: string, wins: number, losses: number) => `${name} lead the series ${wins}-${losses}.`,
  seriesTied: (wins: number, losses: number) => `Series tied ${wins}-${losses}.`,
  originPublished: (date: string) =>
    `The report was published before the game, on ${date}. The final score and the final lines were added after the game, from the box score.`,
  originReconstructed: (asOf: string) =>
    `The report was written after the game, from data through ${asOf}. The final score and the final lines are from the box score.`,
  roleAway: (name: string) => `${name}, away starter`,
  roleHome: (name: string) => `${name}, home starter`,
  hand: { L: "Left-handed", R: "Right-handed" },
  handAndStyle: (hand: string | null, style: string | null) =>
    [hand, style ? style.toLowerCase() : null].filter((part): part is string => part !== null).join(", "),
  probableDidNotStart: (probable: string, actual: string) => `Probable starter ${probable}; ${actual} started.`,
  starterNotConfirmed: "Starter not confirmed",
  report: {
    title: "The report",
    published: (date: string) => `Published before the game, on ${date}`,
    written: (asOf: string) => `Written after the game, from data through ${asOf}`,
    weAsked: "We asked:",
    critic: (checked: number, unsupported: string, warnings: string) =>
      `Before publishing, ${checked} claims in the report were tested against the data: ${unsupported} unsupported, ${warnings} with a warning.`,
    none: "none",
    lineupCaption: (hand: string | null, scope: string | null) => [hand ? `vs ${hand}` : null, scope].filter(Boolean).join(", "),
  },
  nav: {
    label: "Games of this series",
    previous: "Previous game",
    next: "Next game",
    first: "First game of the series",
    last: "Last game of the series",
    game: (game: number, isoDate: string) => `Game ${game}, ${formatMonthDay(isoDate)}`,
  },
  notFound: { title: "We could not find that game", archive: "Back to the archive", notable: "Notable duels of 2026" },
  pageTitle: (away: string, home: string, round: string, game: number, date: string) => `${away} at ${home}, ${round} Game ${game}, ${date}`,
  pageDescription: (away: string, awayRuns: number, home: string, homeRuns: number) =>
    `Final score: ${away} ${awayRuns}, ${home} ${homeRuns}. How the starters did and the report for the game.`,
} as const;
