/**
 * How a team is written where there is room for an abbreviation: the abbreviation, or the team's name when the
 * sources do not give one (an unknown team has `abbreviation: null`; it is never shown as a placeholder).
 */
export interface LabeledTeam {
  abbreviation: string | null;
  name: string;
}

export function teamLabel(team: LabeledTeam): string {
  return team.abbreviation ?? team.name;
}
