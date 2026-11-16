/**
 * The text of the home in the off season (docs/plans/R4-U.md, 5.6). One catalog, so Spanish (v2.1) is a second column. Each
 * sentence that asserts something about data is registered in docs/DATA_CONTRACT.md, section 3.3.
 */
export const HOME_COPY = {
  title: "The 2026 postseason, start by start",
  lede: "What each starting pitcher was expected to do, and what he did. Only what the data supports.",
  seeNotable: "See the notable duels",
  browse: (n: number) => `Browse all ${n} games`,
  boardLabel: (round: string) => `${round}, game by game`,
  gameColumn: (n: number) => `G${n}`,
  wins: "Wins",
  boardWon: (round: string, name: string, wins: number, losses: number) => `${round}. ${name} win the series ${wins}-${losses}. Pick a game to see how its starters did.`,
  notableTitle: "Notable duels of 2026",
  allNotable: "All notable duels",
  howTitle: "How PitchCraft works",
  cards: [
    {
      title: "Before the game",
      body: "A short report on both starters from public MLB data: arsenal, season figures, the lineup each one faces.",
    },
    {
      title: "Every claim is checked",
      body: "Each statement is tested against the data before the report is published. No predictions, no betting.",
    },
    { title: "After the game", body: "The final score and each starter's final line, from the box score." },
  ],
} as const;
