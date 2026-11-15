/**
 * The glossary: the only source of Help text, word for word from docs/design/CONTENT.md ("Glossary"). A test
 * compares the two in both directions. If a page needs a term that is not here, it is added to CONTENT.md first.
 */
export const GLOSSARY = {
  "ERA": "Earned runs allowed per nine innings. Lower is better.",
  "WHIP": "Walks plus hits per inning pitched. Lower is better; near 1.00 is very good.",
  "K%": "The share of batters he struck out. For a starter, 25% or more is above average.",
  "BB%": "The share of batters he walked. Lower is better.",
  "OPS": "On-base plus slugging: how well a lineup gets on base and hits for power. Higher is better for hitters.",
  "IP": "Innings pitched. 6.1 means six innings and one out.",
  "Final line": "What a starter did in this game: innings, hits, earned runs, walks, strikeouts.",
  "Game Score": "One number for a start, from a public formula. It starts at 50, adds for outs and strikeouts, and subtracts for hits, walks and runs. 50 is an average start; 75 or more is rare.",
  "Swing and miss": "A swing where the batter did not touch the ball.",
  "First-pitch strike": "The first pitch of an at-bat was a strike. It puts the pitcher ahead.",
  "Heart of the plate": "The middle of the strike zone, where pitches are easiest to hit.",
  "Deep count": "An at-bat that reaches five or more pitches.",
  "The split": "Why split here? The All-Star Game marks the middle of the season. Comparing the two halves shows whether a starter improved, tired or changed something.",
  "Small sample": "Too few innings or batters for a figure to say much. Labels that need more are left out.",
  "Rookie": "A pitcher who still had rookie status this season under MLB's rules.",
  "Winner-take-all": "A game in which both clubs are one loss from elimination.",
} as const;

export type GlossaryTerm = keyof typeof GLOSSARY;

/** The definition of a term. A term outside the glossary is refused, not improvised. */
export function definitionOf(term: string): string {
  if (!Object.hasOwn(GLOSSARY, term)) throw new Error("not_a_glossary_term");
  return GLOSSARY[term as GlossaryTerm];
}
