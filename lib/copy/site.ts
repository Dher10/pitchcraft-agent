/**
 * The text of the shell: header, footer and the labels shared by the primitives (docs/plans/R4-U.md, 5.1). Strings live in
 * one catalog so the Spanish version (v2.1) is a second column, not a rewrite. Each asserting string is registered in
 * docs/DATA_CONTRACT.md, section 3.3.
 */
export const SITE_COPY = {
  logo: { name: "PitchCraft, home", wordmark: "PITCHCRAFT" },
  nav: {
    label: "Main",
    today: "Today",
    notable: "Notable",
    archive: "Archive",
    todayLocked: "No games in the off season",
  },
  /** Under the header while the season is off: it says why Today is locked. */
  seasonNotice: {
    lead: "Off season.",
    body: "No games today. Today's games and daily reports return when the 2027 season starts.",
  },
  footer: {
    navLabel: "Footer",
    howItWorks: "How PitchCraft works",
    github: "GitHub",
    attribution:
      "Data from the MLB Stats API and Baseball Savant (Statcast), made public by MLB Advanced Media. PitchCraft is an independent fan project and is not affiliated with MLB.",
    nonCommercial: "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features.",
    noPredictions: "For information only: no predictions and no betting advice. Team colors are approximate.",
    madeBy: "Made by",
    author: "Daniel Herdenez",
  },
  links: {
    home: "/",
    notable: "/notable",
    archive: "/archive",
    howItWorks: "/#how-pitchcraft-works",
    github: "https://github.com/Dher10/pitchcraft-agent",
    author: "https://www.danielherdenez.com",
  },
  figure: { unavailable: "Not available" },
  finalLine: {
    label: "Final line",
    notAvailable: "Final line not available",
    fields: {
      innings_pitched: { abbreviation: "IP", name: "Innings pitched" },
      hits: { abbreviation: "H", name: "Hits" },
      earned_runs: { abbreviation: "ER", name: "Earned runs" },
      walks: { abbreviation: "BB", name: "Walks" },
      strikeouts: { abbreviation: "K", name: "Strikeouts" },
    },
  },
  help: { buttonName: (term: string) => `What is ${term}?` },
  /** The archive mode line is this prefix, a space and the date written for people. */
  archiveModeLinePrefix: (season: number) => `${season} season archive, final results through`,
} as const;
