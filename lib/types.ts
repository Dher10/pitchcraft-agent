export type MatchupStatus = "upcoming" | "final" | "demo";
export type CriticCheckStatus = "supported" | "unsupported" | "revised" | "not_present" | "warning";
export type ConfidenceLevel = "live_confirmed" | "partial" | "demo_cached" | "limited";
export type CallResult = "held_up" | "partially_held_up" | "did_not_hold_up" | "unclear";
export type AgentStatus = "completed" | "not_applicable" | "pending";

export interface PitchCraftData {
  metadata: Metadata;
  featured_matchup_id: string;
  matchups: Matchup[];
  archive: ArchiveItem[];
  agent_workflow: AgentWorkflow;
  disclaimers: string[];
}

export interface Metadata {
  project_name: string;
  version: string;
  data_mode: string;
  generated_at: string;
  last_updated_label: string;
  data_sources: string[];
}

export interface Matchup {
  id: string;
  date: string;
  status: MatchupStatus;
  is_featured: boolean;
  game: Game;
  teams: { home: Team; away: Team };
  starters: { away_starter: Starter; home_starter: Starter };
  charts: Charts;
  pitch_locations: PitchLocations;
  report: Report;
  critic_review: CriticReview;
  postgame: Postgame | null;
  data_confidence: DataConfidence;
}

export interface Game {
  title: string;
  venue: string;
  start_time_local: string;
  timezone: string;
  broadcast_note: string;
  home_team_id: string;
  away_team_id: string;
}

export interface Team {
  id: string;
  name: string;
  abbreviation: string;
  record: string;
  offense_profile: OffenseProfile;
}

export interface OffenseProfile {
  summary_label: string;
  vs_pitcher_hand: string;
  ops_vs_hand: string;
  k_rate_vs_hand: string;
  bb_rate_vs_hand: string;
  recent_form: string;
}

export interface StarterBio {
  age: number;
  height: string;
  weight: number;
  bats: string;
  throws: string;
  mlb_service: string;
  accolades: string[];
}

export interface Starter {
  id: string;
  name: string;
  team: string;
  throws: string;
  bio: StarterBio;
  season_summary: SeasonSummary;
  pitching_profile: PitchingProfile;
  recent_form: RecentForm;
}

export interface SeasonSummary {
  era: string;
  whip: string;
  innings: string;
  strikeouts: number;
  walks: number;
  home_runs_allowed: number;
}

export interface PitchingProfile {
  style_label: string;
  primary_pitch: string;
  putaway_pitch: string;
  command_label: string;
  swing_miss_label: string;
  contact_risk_label: string;
}

export interface RecentForm {
  label: string;
  last_three_starts_summary: string;
}

export interface PitchUsage {
  overall: number;
  vs_lhh: number;
  vs_rhh: number;
}

export interface PitchMixRow {
  pitch: string;
  away_starter: PitchUsage;
  home_starter: PitchUsage;
}

export interface VelocityRow {
  pitch: string;
  away_starter_velocity: number | null;
  home_starter_velocity: number | null;
}

export interface StrengthRow {
  dimension: string;
  away_starter: number;
  home_starter: number;
}

export interface Charts {
  pitch_mix: PitchMixRow[];
  velocity_by_pitch: VelocityRow[];
  strength_profile: StrengthRow[];
}

export interface PitchLocation {
  pitch: string;
  x: number;
  y: number;
}

export interface PitchLocationsByHand {
  vs_lhh: PitchLocation[];
  vs_rhh: PitchLocation[];
}

export interface PitchLocations {
  note: string;
  away_starter: PitchLocationsByHand;
  home_starter: PitchLocationsByHand;
}

export interface ReportSection {
  title: string;
  body?: string;
  bullets?: string[];
}

export interface Report {
  headline: string;
  short_summary: string[];
  sections: ReportSection[];
}

export interface CriticCheck {
  claim: string;
  status: CriticCheckStatus;
  evidence: string;
}

export interface CriticReview {
  status: string;
  summary: string;
  checks: CriticCheck[];
  revision_notes: string[];
}

export interface StarterLine {
  name: string;
  innings_pitched: string;
  earned_runs: number;
  strikeouts: number;
  walks: number;
  home_runs_allowed: number;
  pitchcraft_grade: string;
  grade_explanation: string;
  plan_vs_execution: string;
  what_to_watch_next: string;
}

export interface CallCheckItem {
  pregame_note: string;
  result: CallResult;
  postgame_evidence: string;
}

export interface Postgame {
  final_score: { home_team_runs: number; away_team_runs: number; winning_team: string };
  starter_lines: { away_starter: StarterLine; home_starter: StarterLine };
  starter_duel_winner: string;
  call_check: CallCheckItem[];
}

export interface DataConfidence {
  level: ConfidenceLevel;
  lineup_status: string;
  pitch_data_status: string;
  notes: string[];
}

export interface ArchiveItem {
  id: string;
  date: string;
  title: string;
  status: MatchupStatus;
  featured: boolean;
  starter_summary: string;
  result_label: string;
  grade_label: string | null;
}

export interface AgentStep {
  agent: string;
  status: AgentStatus;
  output: string;
}

export interface AgentWorkflow {
  description: string;
  steps: AgentStep[];
}
