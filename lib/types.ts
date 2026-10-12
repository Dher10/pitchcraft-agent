export type MatchupStatus = "upcoming" | "final" | "demo";
export type CriticCheckStatus = "supported" | "unsupported" | "not_present" | "warning";
export type ConfidenceLevel = "live_confirmed" | "fetched_snapshot" | "partial" | "demo_cached" | "limited";
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
  data_status?: DataStatus;
}

export interface LiveRunSummary {
  status: string;
  run_at: string;
  target_date: string | null;
  as_of: string | null;
  games_scheduled: number;
  games_live: number;
  errors: { source: string; message: string }[];
}

export interface DataStatus {
  mode: string;
  reason: string;
  live_run: LiveRunSummary | null;
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
  /** Null when the schedule did not name the venue (live data). */
  venue: string | null;
  /**
   * Live games (D33): the schedule's UTC instant, YYYY-MM-DDTHH:MM:SSZ. Absent in the demo, whose
   * times are written pre-formatted in `start_time_local`.
   */
  start_time_utc?: string | null;
  /** Demo games only; null for a live game. */
  start_time_local: string | null;
  /** The venue's IANA zone when the source gave one (live), the demo's own zone otherwise; null if unknown. */
  timezone: string | null;
  broadcast_note: string | null;
  home_team_id: string;
  away_team_id: string;
}

export interface Team {
  id: string;
  name: string;
  abbreviation: string;
  record: string | null;
  offense_profile: OffenseProfile;
}

export interface OffenseProfile {
  summary_label: string | null;
  vs_pitcher_hand: string;
  ops_vs_hand: string | null;
  k_rate_vs_hand: string | null;
  bb_rate_vs_hand: string | null;
  recent_form: string | null;
  scope?: DataScope | null;
}

/** Which games a group of figures covers (live data only). */
export interface DataScope {
  kind: "regular_season" | "regular_and_postseason";
  through: string;
  label: string;
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
  bio: StarterBio | null;
  season_summary: SeasonSummary;
  pitching_profile: PitchingProfile;
  recent_form: RecentForm | null;
  sample?: Sample;
}

/** The sample behind a live starter's labels (D24). Absent for demo starters. */
export interface Sample {
  arsenal: { pitches: number | null; scope: DataScope };
  rates: {
    batters_faced: number | null;
    strikeouts: number | null;
    walks: number | null;
    home_runs: number | null;
    source: "mlb_api" | "statcast" | "unavailable";
    scope: DataScope;
  };
  limited: { arsenal: boolean; strikeout: boolean; control: boolean };
  thresholds: { arsenal: number; strikeout: number; control: number };
}

export interface SeasonSummary {
  era: string;
  whip: string;
  innings: string;
  strikeouts: number | null;
  walks: number | null;
  home_runs_allowed: number | null;
  scope?: DataScope;
}

export interface PitchingProfile {
  style_label: string;
  primary_pitch: string;
  putaway_pitch: string;
  command_label: string | null;
  swing_miss_label: string | null;
  contact_risk_label: string | null;
}

export interface RecentForm {
  label: string;
  last_three_starts_summary: string;
}

export interface PitchUsage {
  overall: number;
  // null: the starter never faced that side, so there is no share (not 0%).
  vs_lhh: number | null;
  vs_rhh: number | null;
  // Raw pitches behind the rounded shares (live data only; the demo has none): `count` of this
  // pitch out of the starter's `total`. Decisions use these, the chart shows the rounded share.
  count?: number;
  total?: number;
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

export type PitchFamily = "Fastball" | "Breaking" | "Offspeed";

export interface PitchMovement {
  /** Inches; null when the movement was not measured (never 0 for "unknown"). */
  h_break: number | null;
  v_break: number | null;
  family: PitchFamily;
}

export interface Charts {
  pitch_mix: PitchMixRow[];
  velocity_by_pitch: VelocityRow[];
  strength_profile: StrengthRow[];
  pitch_movement: {
    away_starter: Record<string, PitchMovement>;
    home_starter: Record<string, PitchMovement>;
  };
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
  hits_allowed: number;
  earned_runs: number;
  unearned_runs: number;
  strikeouts: number;
  walks: number;
  home_runs_allowed: number;
  game_score: number;
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
