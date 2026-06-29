"""Deterministic demo inputs for the PitchCraft v0.2.0 JSON."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

METADATA: Any = {
  "project_name": "PitchCraft Matchup Agent",
  "version": "0.2.0",
  "data_mode": "cached_demo",
  "generated_at": "2026-06-28T09:00:00-05:00",
  "last_updated_label": "Demo data generated for capstone submission",
  "data_sources": [
    "MLB public schedule/probable pitchers",
    "Baseball Savant / Statcast-style pitch data",
    "Cached demo snapshots"
  ]
}

FEATURED_MATCHUP_ID: Any = "matchup_001"

MATCHUPS: Any = [
  {
    "id": "matchup_001",
    "date": "2026-06-28",
    "status": "upcoming",
    "is_featured": True,
    "game": {
      "title": "San Francisco Giants vs Los Angeles Dodgers",
      "venue": "Oracle Park",
      "start_time_local": "7:15 PM",
      "timezone": "America/Los_Angeles",
      "broadcast_note": "Demo matchup for capstone",
      "home_team_id": "sf",
      "away_team_id": "lad"
    },
    "teams": {
      "home": {
        "id": "sf",
        "name": "San Francisco Giants",
        "abbreviation": "SF",
        "record": "45-39",
        "offense_profile": {
          "summary_label": "Balanced offense with moderate swing-and-miss risk",
          "vs_pitcher_hand": "RHP",
          "ops_vs_hand": ".721",
          "k_rate_vs_hand": "22.8%",
          "bb_rate_vs_hand": "8.7%",
          "recent_form": "Stable"
        }
      },
      "away": {
        "id": "lad",
        "name": "Los Angeles Dodgers",
        "abbreviation": "LAD",
        "record": "51-33",
        "offense_profile": {
          "summary_label": "Power-heavy offense with strong fastball damage potential",
          "vs_pitcher_hand": "LHP",
          "ops_vs_hand": ".768",
          "k_rate_vs_hand": "20.5%",
          "bb_rate_vs_hand": "9.4%",
          "recent_form": "Hot"
        }
      }
    },
    "starters": {
      "away_starter": {
        "id": "pitcher_a",
        "name": "Demo Pitcher A",
        "team": "LAD",
        "throws": "RHP",
        "bio": {
          "age": 27,
          "height": "6-3",
          "weight": 215,
          "bats": "R",
          "throws": "R",
          "mlb_service": "5 yrs",
          "accolades": [
            "2x All-Star"
          ]
        },
        "season_summary": {
          "era": "3.42",
          "whip": "1.16",
          "innings": "92.1",
          "strikeouts": 97,
          "walks": 28,
          "home_runs_allowed": 11
        },
        "pitching_profile": {
          "style_label": "Power fastball-slider starter",
          "primary_pitch": "Four-seam fastball",
          "putaway_pitch": "Slider",
          "command_label": "Average command",
          "swing_miss_label": "Above-average swing-and-miss",
          "contact_risk_label": "Moderate contact risk"
        },
        "recent_form": {
          "label": "Trending stable",
          "last_three_starts_summary": "Has worked into the sixth inning in two of his last three starts."
        }
      },
      "home_starter": {
        "id": "pitcher_b",
        "name": "Demo Pitcher B",
        "team": "SF",
        "throws": "LHP",
        "bio": {
          "age": 31,
          "height": "6-1",
          "weight": 200,
          "bats": "L",
          "throws": "L",
          "mlb_service": "9 yrs",
          "accolades": [
            "2023 All-Star"
          ]
        },
        "season_summary": {
          "era": "3.88",
          "whip": "1.24",
          "innings": "86.0",
          "strikeouts": 81,
          "walks": 31,
          "home_runs_allowed": 9
        },
        "pitching_profile": {
          "style_label": "Command-oriented sinker-changeup starter",
          "primary_pitch": "Sinker",
          "putaway_pitch": "Changeup",
          "command_label": "Solid command",
          "swing_miss_label": "Average swing-and-miss",
          "contact_risk_label": "Low-to-moderate contact risk"
        },
        "recent_form": {
          "label": "Slight volatility",
          "last_three_starts_summary": "Has limited hard contact, but walk totals have increased recently."
        }
      }
    },
    "charts": {
      "pitch_mix": [
        {
          "pitch": "Four-seam",
          "away_starter": {
            "overall": 42,
            "vs_lhh": 38,
            "vs_rhh": 45
          },
          "home_starter": {
            "overall": 18,
            "vs_lhh": 15,
            "vs_rhh": 20
          }
        },
        {
          "pitch": "Slider",
          "away_starter": {
            "overall": 28,
            "vs_lhh": 20,
            "vs_rhh": 34
          },
          "home_starter": {
            "overall": 12,
            "vs_lhh": 18,
            "vs_rhh": 9
          }
        },
        {
          "pitch": "Sinker",
          "away_starter": {
            "overall": 8,
            "vs_lhh": 10,
            "vs_rhh": 6
          },
          "home_starter": {
            "overall": 39,
            "vs_lhh": 44,
            "vs_rhh": 36
          }
        },
        {
          "pitch": "Changeup",
          "away_starter": {
            "overall": 10,
            "vs_lhh": 20,
            "vs_rhh": 3
          },
          "home_starter": {
            "overall": 24,
            "vs_lhh": 12,
            "vs_rhh": 30
          }
        },
        {
          "pitch": "Curveball",
          "away_starter": {
            "overall": 12,
            "vs_lhh": 12,
            "vs_rhh": 12
          },
          "home_starter": {
            "overall": 7,
            "vs_lhh": 11,
            "vs_rhh": 5
          }
        }
      ],
      "velocity_by_pitch": [
        {
          "pitch": "Four-seam",
          "away_starter_velocity": 95.4,
          "home_starter_velocity": None
        },
        {
          "pitch": "Slider",
          "away_starter_velocity": 86.7,
          "home_starter_velocity": 82.1
        },
        {
          "pitch": "Sinker",
          "away_starter_velocity": 93.1,
          "home_starter_velocity": 91.8
        },
        {
          "pitch": "Changeup",
          "away_starter_velocity": 84.8,
          "home_starter_velocity": 83.5
        },
        {
          "pitch": "Curveball",
          "away_starter_velocity": 79.2,
          "home_starter_velocity": 76.9
        }
      ],
      "strength_profile": [
        {
          "dimension": "Stuff",
          "away_starter": 78,
          "home_starter": 66
        },
        {
          "dimension": "Command",
          "away_starter": 63,
          "home_starter": 74
        },
        {
          "dimension": "Whiff",
          "away_starter": 80,
          "home_starter": 62
        },
        {
          "dimension": "Contact Risk",
          "away_starter": 58,
          "home_starter": 70
        },
        {
          "dimension": "Recent Form",
          "away_starter": 72,
          "home_starter": 61
        }
      ]
    },
    "pitch_locations": {
      "note": "x,y are 0-1 within the plot area. The strike zone is drawn by the frontend at a fixed inset (~0.25-0.75). 0,0 is top-left (up and inside to a RHB).",
      "away_starter": {
        "vs_lhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.18
          },
          {
            "pitch": "Changeup",
            "x": 0.72,
            "y": 0.7
          },
          {
            "pitch": "Slider",
            "x": 0.3,
            "y": 0.74
          }
        ],
        "vs_rhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.18
          },
          {
            "pitch": "Slider",
            "x": 0.74,
            "y": 0.72
          },
          {
            "pitch": "Curveball",
            "x": 0.46,
            "y": 0.8
          }
        ]
      },
      "home_starter": {
        "vs_lhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.2
          },
          {
            "pitch": "Sinker",
            "x": 0.5,
            "y": 0.74
          },
          {
            "pitch": "Slider",
            "x": 0.3,
            "y": 0.72
          }
        ],
        "vs_rhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.2
          },
          {
            "pitch": "Sinker",
            "x": 0.5,
            "y": 0.74
          },
          {
            "pitch": "Changeup",
            "x": 0.7,
            "y": 0.7
          }
        ]
      }
    },
    "report": {
      "headline": "A contrast of power stuff vs command and contact management",
      "short_summary": [
        "The Dodgers starter brings more swing-and-miss upside with a fastball-slider foundation.",
        "The Giants starter has a softer velocity profile but may match up well if he keeps the ball on the ground.",
        "The key early signal is whether each starter can avoid fastball counts with runners on base."
      ],
      "sections": [
        {
          "title": "Today's Matchup Summary",
          "body": "This matchup features two different starter profiles: one built around power and swing-and-miss, the other around command, movement, and contact control."
        },
        {
          "title": "Pitcher A vs Team B",
          "body": "Pitcher A's fastball-slider combination gives him a clear bat-missing path, but the opposing lineup can pressure him if they force him into predictable fastball counts."
        },
        {
          "title": "Pitcher B vs Team A",
          "body": "Pitcher B needs to keep the ball down and use the changeup to disrupt timing. His margin for error is smaller against a lineup with strong fastball damage potential."
        },
        {
          "title": "Arsenal Scout",
          "body": "The main contrast is velocity and shape. Pitcher A leans on a harder fastball and slider, while Pitcher B uses sinker-changeup sequencing to manage contact."
        },
        {
          "title": "Three Things to Watch",
          "bullets": [
            "Can Pitcher A land the slider early in counts?",
            "Can Pitcher B keep the ball below the middle of the zone?",
            "Which lineup forces more deep counts by the third inning?"
          ]
        },
        {
          "title": "Data Confidence Note",
          "body": "This report is based on cached demo data for the capstone. Live lineup confirmation is not required for this version."
        }
      ]
    },
    "critic_review": {
      "status": "reviewed",
      "summary": "The critic checked the report for unsupported claims and betting language.",
      "checks": [
        {
          "claim": "Pitcher A relies heavily on the fastball-slider combination.",
          "status": "supported",
          "evidence": "Pitch mix shows 42% four-seam usage and 28% slider usage."
        },
        {
          "claim": "Pitcher B has stronger command.",
          "status": "supported",
          "evidence": "Command signal is higher for Pitcher B in the strength profile (74 vs 63)."
        },
        {
          "claim": "Pitcher A's changeup is his main weapon.",
          "status": "revised",
          "evidence": "Changeup usage is only 10%. Revised to name the slider as the primary put-away pitch."
        },
        {
          "claim": "The report predicts the winner.",
          "status": "not_present",
          "evidence": "No win prediction or betting language found."
        }
      ],
      "revision_notes": [
        "Corrected the put-away pitch claim for Pitcher A from changeup to slider.",
        "Kept the report focused on matchup fit rather than outcome prediction.",
        "Avoided claiming official Stuff+."
      ]
    },
    "postgame": None,
    "data_confidence": {
      "level": "demo_cached",
      "lineup_status": "not_required_for_demo",
      "pitch_data_status": "cached",
      "notes": [
        "This demo uses cached data to guarantee stable judging.",
        "Live data integration can be added after the capstone."
      ]
    }
  },
  {
    "id": "matchup_002",
    "date": "2026-06-26",
    "status": "final",
    "is_featured": False,
    "game": {
      "title": "New York Yankees vs Boston Red Sox",
      "venue": "Fenway Park",
      "start_time_local": "7:10 PM",
      "timezone": "America/New_York",
      "broadcast_note": "Demo matchup for capstone",
      "home_team_id": "bos",
      "away_team_id": "nyy"
    },
    "teams": {
      "home": {
        "id": "bos",
        "name": "Boston Red Sox",
        "abbreviation": "BOS",
        "record": "44-40",
        "offense_profile": {
          "summary_label": "Aggressive offense that punishes pitches over the plate",
          "vs_pitcher_hand": "RHP",
          "ops_vs_hand": ".744",
          "k_rate_vs_hand": "21.6%",
          "bb_rate_vs_hand": "8.1%",
          "recent_form": "Hot"
        }
      },
      "away": {
        "id": "nyy",
        "name": "New York Yankees",
        "abbreviation": "NYY",
        "record": "49-35",
        "offense_profile": {
          "summary_label": "Patient offense with high walk rate and pull-side power",
          "vs_pitcher_hand": "LHP",
          "ops_vs_hand": ".756",
          "k_rate_vs_hand": "19.8%",
          "bb_rate_vs_hand": "10.2%",
          "recent_form": "Stable"
        }
      }
    },
    "starters": {
      "away_starter": {
        "id": "pitcher_c",
        "name": "Demo Pitcher C",
        "team": "NYY",
        "throws": "RHP",
        "bio": {
          "age": 24,
          "height": "6-5",
          "weight": 230,
          "bats": "R",
          "throws": "R",
          "mlb_service": "3 yrs",
          "accolades": []
        },
        "season_summary": {
          "era": "4.05",
          "whip": "1.29",
          "innings": "88.2",
          "strikeouts": 90,
          "walks": 34,
          "home_runs_allowed": 14
        },
        "pitching_profile": {
          "style_label": "High-velocity fastball-curveball starter",
          "primary_pitch": "Four-seam fastball",
          "putaway_pitch": "Curveball",
          "command_label": "Below-average command",
          "swing_miss_label": "Above-average swing-and-miss",
          "contact_risk_label": "Elevated contact risk"
        },
        "recent_form": {
          "label": "Volatile",
          "last_three_starts_summary": "Has alternated between strong outings and short starts driven by walks."
        }
      },
      "home_starter": {
        "id": "pitcher_d",
        "name": "Demo Pitcher D",
        "team": "BOS",
        "throws": "LHP",
        "bio": {
          "age": 29,
          "height": "6-2",
          "weight": 205,
          "bats": "L",
          "throws": "L",
          "mlb_service": "7 yrs",
          "accolades": [
            "3x All-Star"
          ]
        },
        "season_summary": {
          "era": "3.31",
          "whip": "1.11",
          "innings": "95.0",
          "strikeouts": 88,
          "walks": 22,
          "home_runs_allowed": 8
        },
        "pitching_profile": {
          "style_label": "Command-first cutter-changeup starter",
          "primary_pitch": "Cutter",
          "putaway_pitch": "Changeup",
          "command_label": "Plus command",
          "swing_miss_label": "Average swing-and-miss",
          "contact_risk_label": "Low contact risk"
        },
        "recent_form": {
          "label": "Trending up",
          "last_three_starts_summary": "Has completed at least six innings in each of his last three starts."
        }
      }
    },
    "charts": {
      "pitch_mix": [
        {
          "pitch": "Four-seam",
          "away_starter": {
            "overall": 48,
            "vs_lhh": 44,
            "vs_rhh": 52
          },
          "home_starter": {
            "overall": 14,
            "vs_lhh": 12,
            "vs_rhh": 16
          }
        },
        {
          "pitch": "Cutter",
          "away_starter": {
            "overall": 6,
            "vs_lhh": 7,
            "vs_rhh": 5
          },
          "home_starter": {
            "overall": 41,
            "vs_lhh": 47,
            "vs_rhh": 36
          }
        },
        {
          "pitch": "Curveball",
          "away_starter": {
            "overall": 26,
            "vs_lhh": 22,
            "vs_rhh": 30
          },
          "home_starter": {
            "overall": 9,
            "vs_lhh": 11,
            "vs_rhh": 7
          }
        },
        {
          "pitch": "Changeup",
          "away_starter": {
            "overall": 12,
            "vs_lhh": 19,
            "vs_rhh": 5
          },
          "home_starter": {
            "overall": 30,
            "vs_lhh": 22,
            "vs_rhh": 37
          }
        },
        {
          "pitch": "Sinker",
          "away_starter": {
            "overall": 8,
            "vs_lhh": 8,
            "vs_rhh": 8
          },
          "home_starter": {
            "overall": 6,
            "vs_lhh": 8,
            "vs_rhh": 4
          }
        }
      ],
      "velocity_by_pitch": [
        {
          "pitch": "Four-seam",
          "away_starter_velocity": 96.8,
          "home_starter_velocity": 92
        },
        {
          "pitch": "Cutter",
          "away_starter_velocity": 89.5,
          "home_starter_velocity": 88.3
        },
        {
          "pitch": "Curveball",
          "away_starter_velocity": 80.1,
          "home_starter_velocity": 77.4
        },
        {
          "pitch": "Changeup",
          "away_starter_velocity": 87.2,
          "home_starter_velocity": 82.6
        },
        {
          "pitch": "Sinker",
          "away_starter_velocity": 94,
          "home_starter_velocity": 90.7
        }
      ],
      "strength_profile": [
        {
          "dimension": "Stuff",
          "away_starter": 82,
          "home_starter": 64
        },
        {
          "dimension": "Command",
          "away_starter": 52,
          "home_starter": 81
        },
        {
          "dimension": "Whiff",
          "away_starter": 76,
          "home_starter": 60
        },
        {
          "dimension": "Contact Risk",
          "away_starter": 71,
          "home_starter": 48
        },
        {
          "dimension": "Recent Form",
          "away_starter": 58,
          "home_starter": 77
        }
      ]
    },
    "pitch_locations": {
      "note": "x,y are 0-1 within the plot area. The strike zone is drawn by the frontend at a fixed inset (~0.25-0.75).",
      "away_starter": {
        "vs_lhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.16
          },
          {
            "pitch": "Changeup",
            "x": 0.72,
            "y": 0.7
          },
          {
            "pitch": "Curveball",
            "x": 0.46,
            "y": 0.8
          }
        ],
        "vs_rhh": [
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.16
          },
          {
            "pitch": "Curveball",
            "x": 0.48,
            "y": 0.82
          },
          {
            "pitch": "Cutter",
            "x": 0.6,
            "y": 0.5
          }
        ]
      },
      "home_starter": {
        "vs_lhh": [
          {
            "pitch": "Cutter",
            "x": 0.6,
            "y": 0.5
          },
          {
            "pitch": "Changeup",
            "x": 0.5,
            "y": 0.72
          },
          {
            "pitch": "Curveball",
            "x": 0.45,
            "y": 0.78
          }
        ],
        "vs_rhh": [
          {
            "pitch": "Cutter",
            "x": 0.32,
            "y": 0.45
          },
          {
            "pitch": "Changeup",
            "x": 0.72,
            "y": 0.7
          },
          {
            "pitch": "Four-seam",
            "x": 0.5,
            "y": 0.2
          }
        ]
      }
    },
    "report": {
      "headline": "Raw velocity vs precision at Fenway",
      "short_summary": [
        "The Yankees starter has the louder arsenal but a wider command range.",
        "The Red Sox starter relies on the cutter and changeup to keep hitters off balance.",
        "Walk avoidance was the swing factor in this matchup."
      ],
      "sections": [
        {
          "title": "Today's Matchup Summary",
          "body": "A high-velocity arm faces a command-first lefty. The story is whether power can outrun the walk risk against a patient lineup."
        },
        {
          "title": "Pitcher C vs Team B",
          "body": "Pitcher C can miss bats with the fastball-curveball pairing, but the Red Sox punish anything left over the plate when counts get long."
        },
        {
          "title": "Pitcher D vs Team A",
          "body": "Pitcher D needs the cutter to stay on the edges. Against a patient Yankees lineup, limiting free passes is the difference between five and seven innings."
        },
        {
          "title": "Three Things to Watch",
          "bullets": [
            "Can Pitcher C hold his walk rate under control early?",
            "Can Pitcher D land the cutter to both sides of the plate?",
            "Which bullpen gets exposed first if a starter exits early?"
          ]
        }
      ]
    },
    "critic_review": {
      "status": "reviewed",
      "summary": "The critic checked the report for unsupported claims and betting language.",
      "checks": [
        {
          "claim": "Pitcher C carries elevated walk risk.",
          "status": "supported",
          "evidence": "Command signal is 52 and season walk total is 34 in 88.2 innings."
        },
        {
          "claim": "Pitcher D limits hard contact.",
          "status": "supported",
          "evidence": "Contact Risk signal is the lowest in the matchup at 48."
        },
        {
          "claim": "This game is a lock for Boston.",
          "status": "revised",
          "evidence": "Betting-style certainty removed. Revised to describe matchup fit only."
        }
      ],
      "revision_notes": [
        "Removed outcome-certainty language flagged as betting-style.",
        "Kept the analysis focused on command and contact management."
      ]
    },
    "postgame": {
      "final_score": {
        "home_team_runs": 5,
        "away_team_runs": 3,
        "winning_team": "BOS"
      },
      "starter_lines": {
        "away_starter": {
          "name": "Demo Pitcher C",
          "innings_pitched": "4.2",
          "earned_runs": 4,
          "strikeouts": 5,
          "walks": 4,
          "home_runs_allowed": 1,
          "pitchcraft_grade": "C",
          "grade_explanation": "Flashed swing-and-misses but lost efficiency because of walks and one damaging mistake.",
          "plan_vs_execution": "The plan was to climb the ladder with the fastball and finish with the curveball. He fell behind too often and had to come back over the heart of the plate.",
          "what_to_watch_next": "Whether he can throw a first-pitch strike more consistently in his next outing."
        },
        "home_starter": {
          "name": "Demo Pitcher D",
          "innings_pitched": "6.2",
          "earned_runs": 2,
          "strikeouts": 6,
          "walks": 1,
          "home_runs_allowed": 0,
          "pitchcraft_grade": "A-",
          "grade_explanation": "Controlled contact, limited walks, and worked deep enough to give the team a strong start.",
          "plan_vs_execution": "Wanted to work the cutter to both edges and bury the changeup against righties. He executed it almost exactly.",
          "what_to_watch_next": "Whether he keeps the walk rate this low against deeper, more patient lineups."
        }
      },
      "starter_duel_winner": "Demo Pitcher D",
      "call_check": [
        {
          "pregame_note": "Pitcher D needed to limit walks against a patient lineup.",
          "result": "held_up",
          "postgame_evidence": "Issued only one walk over 6.2 innings."
        },
        {
          "pregame_note": "Pitcher C carried elevated walk risk.",
          "result": "held_up",
          "postgame_evidence": "Walked four and exited before completing the fifth inning."
        },
        {
          "pregame_note": "Pitcher C had swing-and-miss upside.",
          "result": "partially_held_up",
          "postgame_evidence": "Recorded five strikeouts but could not work efficiently."
        }
      ]
    },
    "data_confidence": {
      "level": "demo_cached",
      "lineup_status": "final",
      "pitch_data_status": "cached",
      "notes": [
        "Completed demo game used to show the postgame grading flow.",
        "Grades are PitchCraft-specific and explainable, not official metrics."
      ]
    }
  }
]

ARCHIVE: Any = [
  {
    "id": "matchup_001",
    "date": "2026-06-28",
    "title": "Giants vs Dodgers",
    "status": "upcoming",
    "featured": True,
    "starter_summary": "Demo Pitcher A vs Demo Pitcher B",
    "result_label": "Pregame report available",
    "grade_label": None
  },
  {
    "id": "matchup_002",
    "date": "2026-06-26",
    "title": "Yankees vs Red Sox",
    "status": "final",
    "featured": False,
    "starter_summary": "Demo Pitcher C vs Demo Pitcher D",
    "result_label": "BOS 5 - NYY 3",
    "grade_label": "Starter Duel: Demo Pitcher D, A-"
  },
  {
    "id": "matchup_003",
    "date": "2026-06-25",
    "title": "Astros vs Mariners",
    "status": "final",
    "featured": False,
    "starter_summary": "Demo Pitcher E vs Demo Pitcher F",
    "result_label": "SEA 3 - HOU 1",
    "grade_label": "Starter Duel: Demo Pitcher F, A"
  },
  {
    "id": "matchup_004",
    "date": "2026-06-24",
    "title": "Braves vs Phillies",
    "status": "final",
    "featured": False,
    "starter_summary": "Demo Pitcher G vs Demo Pitcher H",
    "result_label": "ATL 6 - PHI 4",
    "grade_label": "Starter Duel: Demo Pitcher G, B+"
  },
  {
    "id": "matchup_005",
    "date": "2026-06-23",
    "title": "Padres vs Cubs",
    "status": "final",
    "featured": False,
    "starter_summary": "Demo Pitcher I vs Demo Pitcher J",
    "result_label": "SD 2 - CHC 0",
    "grade_label": "Starter Duel: Demo Pitcher I, A-"
  },
  {
    "id": "matchup_006",
    "date": "2026-06-22",
    "title": "Orioles vs Rays",
    "status": "final",
    "featured": False,
    "starter_summary": "Demo Pitcher K vs Demo Pitcher L",
    "result_label": "TB 4 - BAL 3",
    "grade_label": "Starter Duel: Demo Pitcher L, B"
  }
]

AGENT_WORKFLOW: Any = {
  "description": "PitchCraft uses a multi-agent workflow to convert matchup data into a fan-facing scouting report.",
  "steps": [
    {
      "agent": "Data Scout Agent",
      "status": "completed",
      "output": "Loaded cached matchup, pitcher, and chart data."
    },
    {
      "agent": "Matchup Analyst Agent",
      "status": "completed",
      "output": "Identified pitcher strengths, risks, and lineup pressure points."
    },
    {
      "agent": "Report Writer Agent",
      "status": "completed",
      "output": "Generated fan-friendly scouting report."
    },
    {
      "agent": "Critic / Fact-check Agent",
      "status": "completed",
      "output": "Verified claims and removed unsupported language."
    },
    {
      "agent": "Postgame Grader Agent",
      "status": "not_applicable",
      "output": "Featured game has not been completed."
    }
  ]
}

DISCLAIMERS: Any = [
  "PitchCraft is a capstone demo and not a betting or gambling tool.",
  "The analysis explains matchup fit and what to watch, not guaranteed outcomes.",
  "Cached demo data may be used to ensure stable public evaluation.",
  "Any internal Stuff or Strength signals are PitchCraft-specific and are not official Stuff+ metrics."
]

def build_demo_payload() -> dict[str, Any]:
  """Return a fresh v0.2.0 demo payload assembled from structured constants."""
  return deepcopy({
    "metadata": METADATA,
    "featured_matchup_id": FEATURED_MATCHUP_ID,
    "matchups": MATCHUPS,
    "archive": ARCHIVE,
    "agent_workflow": AGENT_WORKFLOW,
    "disclaimers": DISCLAIMERS,
  })
