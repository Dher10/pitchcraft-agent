import type { Matchup, PitchLocation, PitchMixRow, PitchMovement, Sample, Starter } from "@/lib/types";

/** Self-contained matchups for component tests: they do not read public/data, which the bot rewrites. */

const SCOPE = { kind: "regular_season", through: "2026-07-14", label: "2026 regular season through Jul 14" } as const;

export function makeSample(pitches: number | null, limitedArsenal = pitches === null || pitches < 100): Sample {
  const limited = pitches === 0;
  return {
    arsenal: { pitches, scope: pitches === null ? null : SCOPE },
    rates: {
      batters_faced: limited ? null : 400,
      strikeouts: limited ? null : 90,
      walks: limited ? null : 30,
      home_runs: limited ? null : 10,
      source: limited ? "unavailable" : "mlb_api",
      scope: limited ? null : SCOPE,
    },
    limited: { arsenal: limitedArsenal, strikeout: limited, control: limited },
    thresholds: { arsenal: 100, strikeout: 70, control: 170 },
  };
}

export function makeStarter(name: string, team: string, overrides: Partial<Starter> = {}): Starter {
  return {
    id: name,
    name,
    team,
    throws: "R",
    bio: null,
    season_summary: {
      era: "3.10",
      whip: "1.05",
      innings: "101.0",
      strikeouts: 110,
      walks: 30,
      home_runs_allowed: 10,
      scopes: { season_rates: SCOPE, counts: SCOPE },
    },
    pitching_profile: {
      style_label: "Four-seam starter",
      primary_pitch: "Four-seam",
      putaway_pitch: "Not available",
      command_label: null,
      swing_miss_label: null,
      contact_risk_label: null,
    },
    recent_form: null,
    sample: makeSample(1500),
    ...overrides,
  };
}

export function mixRow(pitch: string, away: number, home: number): PitchMixRow {
  const usage = (value: number) => ({ overall: value, vs_lhh: value, vs_rhh: value });
  return { pitch, away_starter: usage(away), home_starter: usage(home) };
}

/** The same row with the share against one side replaced (null: that side was never faced). */
export function withShare(
  row: PitchMixRow,
  side: "away_starter" | "home_starter",
  hand: "vs_lhh" | "vs_rhh",
  value: number | null,
): PitchMixRow {
  return { ...row, [side]: { ...row[side], [hand]: value } };
}

/** The same row with the raw counts a live mix carries: `count` of `total` pitches for one starter. */
export function withCount(row: PitchMixRow, side: "away_starter" | "home_starter", count: number, total: number): PitchMixRow {
  return { ...row, [side]: { ...row[side], count, total } };
}

export const FASTBALL: PitchMovement = { h_break: 7.8, v_break: 16.2, family: "Fastball" };

export function makeMatchup(options: {
  away?: Starter;
  home?: Starter;
  mix?: PitchMixRow[];
  velocity?: { pitch: string; away: number | null; home: number | null }[];
  awayMovement?: Record<string, PitchMovement>;
  homeMovement?: Record<string, PitchMovement>;
  awayLocations?: PitchLocation[];
  homeLocations?: PitchLocation[];
}): Matchup {
  const away = options.away ?? makeStarter("Away Ace", "BOS");
  const home = options.home ?? makeStarter("Home Ace", "NYY");
  const mix = options.mix ?? [mixRow("Four-seam", 100, 100)];
  const byHand = (locations: PitchLocation[] = []) => ({ vs_lhh: locations, vs_rhh: locations });
  const team = (id: string, name: string, abbreviation: string) => ({
    id,
    name,
    abbreviation,
    record: null,
    offense_profile: {
      summary_label: null,
      vs_pitcher_hand: "RHP",
      ops_vs_hand: null,
      k_rate_vs_hand: null,
      bb_rate_vs_hand: null,
      recent_form: null,
    },
  });
  return {
    id: "matchup_test",
    date: "2026-07-15",
    status: "upcoming",
    is_featured: true,
    series: null,
    game: {
      title: "Test game",
      venue: "Test Park",
      start_time_local: "7:05 PM",
      timezone: "America/New_York",
      broadcast_note: null,
      home_team_id: "147",
      away_team_id: "111",
    },
    teams: { home: team("147", "New York Yankees", "NYY"), away: team("111", "Boston Red Sox", "BOS") },
    starters: { away_starter: away, home_starter: home },
    charts: {
      pitch_mix: mix,
      velocity_by_pitch: (options.velocity ?? mix.map((row) => ({ pitch: row.pitch, away: 94.1, home: 93.2 }))).map(
        (row) => ({ pitch: row.pitch, away_starter_velocity: row.away, home_starter_velocity: row.home }),
      ),
      strength_profile: [],
      pitch_movement: {
        away_starter: options.awayMovement ?? { "Four-seam": FASTBALL },
        home_starter: options.homeMovement ?? { "Four-seam": FASTBALL },
      },
    },
    pitch_locations: {
      note: "",
      away_starter: byHand(options.awayLocations),
      home_starter: byHand(options.homeLocations),
    },
    report: { headline: "", short_summary: [], sections: [] },
    critic_review: { status: "reviewed", summary: "", checks: [], revision_notes: [] },
    postgame: null,
    data_confidence: { level: "fetched_snapshot", lineup_status: "", pitch_data_status: "", notes: [] },
  };
}
