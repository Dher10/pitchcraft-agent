/**
 * The 30 clubs: nickname, league and division. A closed table of static labels (data contract 3.4); it asserts nothing
 * about data. The key is the abbreviation the MLB Stats API uses today.
 */
export interface Club {
  nickname: string;
  league: "American League" | "National League";
  division: "East" | "Central" | "West";
}

export const CLUBS: Record<string, Club> = {
  BAL: { nickname: "Orioles", league: "American League", division: "East" },
  BOS: { nickname: "Red Sox", league: "American League", division: "East" },
  NYY: { nickname: "Yankees", league: "American League", division: "East" },
  TB: { nickname: "Rays", league: "American League", division: "East" },
  TOR: { nickname: "Blue Jays", league: "American League", division: "East" },
  CWS: { nickname: "White Sox", league: "American League", division: "Central" },
  CLE: { nickname: "Guardians", league: "American League", division: "Central" },
  DET: { nickname: "Tigers", league: "American League", division: "Central" },
  KC: { nickname: "Royals", league: "American League", division: "Central" },
  MIN: { nickname: "Twins", league: "American League", division: "Central" },
  ATH: { nickname: "Athletics", league: "American League", division: "West" },
  HOU: { nickname: "Astros", league: "American League", division: "West" },
  LAA: { nickname: "Angels", league: "American League", division: "West" },
  SEA: { nickname: "Mariners", league: "American League", division: "West" },
  TEX: { nickname: "Rangers", league: "American League", division: "West" },
  ATL: { nickname: "Braves", league: "National League", division: "East" },
  MIA: { nickname: "Marlins", league: "National League", division: "East" },
  NYM: { nickname: "Mets", league: "National League", division: "East" },
  PHI: { nickname: "Phillies", league: "National League", division: "East" },
  WSH: { nickname: "Nationals", league: "National League", division: "East" },
  CHC: { nickname: "Cubs", league: "National League", division: "Central" },
  CIN: { nickname: "Reds", league: "National League", division: "Central" },
  MIL: { nickname: "Brewers", league: "National League", division: "Central" },
  PIT: { nickname: "Pirates", league: "National League", division: "Central" },
  STL: { nickname: "Cardinals", league: "National League", division: "Central" },
  ARI: { nickname: "D-backs", league: "National League", division: "West" },
  COL: { nickname: "Rockies", league: "National League", division: "West" },
  LAD: { nickname: "Dodgers", league: "National League", division: "West" },
  SD: { nickname: "Padres", league: "National League", division: "West" },
  SF: { nickname: "Giants", league: "National League", division: "West" },
};

/** The nickname of a club, or null when the abbreviation is missing or not one of the 30 (never a placeholder). */
export function clubNickname(abbreviation: string | null | undefined): string | null {
  if (!abbreviation) return null;
  return Object.hasOwn(CLUBS, abbreviation) ? CLUBS[abbreviation].nickname : null;
}
