export interface TeamColor {
  bg: string;
  ink: string;
}

// Approximate primary brand colors, used only as a subtle accent (card top-rule,
// badge fill). Not official/licensed team marks — see app disclaimers.
const TEAM_COLORS: Record<string, TeamColor> = {
  ARI: { bg: "#A71930", ink: "#ffffff" },
  ATL: { bg: "#13274F", ink: "#ffffff" },
  BAL: { bg: "#DF4601", ink: "#ffffff" },
  BOS: { bg: "#BD3039", ink: "#ffffff" },
  CHC: { bg: "#0E3386", ink: "#ffffff" },
  CWS: { bg: "#27251F", ink: "#ffffff" },
  CIN: { bg: "#C6011F", ink: "#ffffff" },
  CLE: { bg: "#00385D", ink: "#ffffff" },
  COL: { bg: "#333366", ink: "#ffffff" },
  DET: { bg: "#0C2340", ink: "#ffffff" },
  HOU: { bg: "#EB6E1F", ink: "#0C2340" },
  KC: { bg: "#004687", ink: "#ffffff" },
  KCR: { bg: "#004687", ink: "#ffffff" },
  LAA: { bg: "#BA0021", ink: "#ffffff" },
  LAD: { bg: "#005A9C", ink: "#ffffff" },
  MIA: { bg: "#00A3E0", ink: "#ffffff" },
  MIL: { bg: "#12284B", ink: "#ffffff" },
  MIN: { bg: "#002B5C", ink: "#ffffff" },
  NYM: { bg: "#002D72", ink: "#ffffff" },
  NYY: { bg: "#0C2340", ink: "#ffffff" },
  OAK: { bg: "#003831", ink: "#EFB21E" },
  ATH: { bg: "#003831", ink: "#EFB21E" },
  PHI: { bg: "#E81828", ink: "#ffffff" },
  PIT: { bg: "#FDB827", ink: "#27251F" },
  SD: { bg: "#2F241D", ink: "#ffffff" },
  SDP: { bg: "#2F241D", ink: "#ffffff" },
  SF: { bg: "#FD5A1E", ink: "#000000" },
  SFG: { bg: "#FD5A1E", ink: "#000000" },
  SEA: { bg: "#0C2C56", ink: "#ffffff" },
  STL: { bg: "#C41E3A", ink: "#ffffff" },
  TB: { bg: "#092C5C", ink: "#ffffff" },
  TBR: { bg: "#092C5C", ink: "#ffffff" },
  TEX: { bg: "#003278", ink: "#ffffff" },
  TOR: { bg: "#134A8E", ink: "#ffffff" },
  WSH: { bg: "#AB0003", ink: "#ffffff" },
  WSN: { bg: "#AB0003", ink: "#ffffff" },
};

const FALLBACK_TEAM_COLOR: TeamColor = { bg: "#71717a", ink: "#ffffff" };

export function getTeamColor(abbreviation: string | undefined | null): TeamColor {
  if (!abbreviation) return FALLBACK_TEAM_COLOR;
  return TEAM_COLORS[abbreviation.toUpperCase()] ?? FALLBACK_TEAM_COLOR;
}
