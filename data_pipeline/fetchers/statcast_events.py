"""Known Statcast event outcomes, shared by pitcher and team derivations.

The domain and PA/hit flags come from https://statsapi.mlb.com/api/v1/eventTypes,
saved unchanged in tests/fixtures/mlb_event_types_2026-10-17.json. Tests check
every metadata code against this map, including every non-PA event. There is
no runtime metadata request or catch-all classification for an unlisted code.
An at-bat without a hit (error/fielder's choice) is not necessarily an out.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventOutcome:
    kind: str
    bases: int = 0


STATCAST_EVENTS = {
    "single": EventOutcome("hit", 1),
    "double": EventOutcome("hit", 2),
    "triple": EventOutcome("hit", 3),
    "home_run": EventOutcome("hit", 4),
    "walk": EventOutcome("walk"),
    "intent_walk": EventOutcome("walk"),
    "strikeout": EventOutcome("strikeout"),
    "strike_out": EventOutcome("strikeout"),
    "strikeout_double_play": EventOutcome("strikeout"),
    "strikeout_triple_play": EventOutcome("strikeout"),
    "hit_by_pitch": EventOutcome("hit_by_pitch"),
    "sac_fly": EventOutcome("sac_fly"),
    "sac_fly_double_play": EventOutcome("sac_fly"),
    "sac_bunt": EventOutcome("sac_bunt"),
    "sac_bunt_double_play": EventOutcome("sac_bunt"),
    "catcher_interf": EventOutcome("interference"),
    "field_out": EventOutcome("out"),
    "force_out": EventOutcome("out"),
    "grounded_into_double_play": EventOutcome("out"),
    "double_play": EventOutcome("out"),
    "triple_play": EventOutcome("out"),
    "batter_interference": EventOutcome("out"),
    "field_error": EventOutcome("at_bat"),
    "fielders_choice": EventOutcome("at_bat"),
    "fielders_choice_out": EventOutcome("out"),
    # Metadata marks these as PA, not hits; neither asserts a literal out.
    "fan_interference": EventOutcome("at_bat"),
    "os_ruling_pending_primary": EventOutcome("at_bat"),
    # A Savant-only non-PA value, retained from the existing source fixtures.
    "truncated_pa": EventOutcome("non_pa"),
}

# Every plateAppearance=false code in the saved metadata, including runner
# outs. In particular grounded_into_triple_play is non-PA in that metadata;
# triple_play and strikeout_triple_play above each count exactly one PA.
STATCAST_EVENTS.update({code: EventOutcome("non_pa") for code in (
    "pickoff_1b", "pickoff_2b", "pickoff_3b", "pitcher_step_off",
    "pickoff_error_1b", "pickoff_error_2b", "pickoff_error_3b",
    "batter_timeout", "mound_visit", "no_pitch", "error",
    "grounded_into_triple_play", "fielder_interference", "runner_interference",
    "batter_turn", "ejection", "cs_double_play", "defensive_indiff", "injury",
    "os_ruling_pending_prior", "at_bat_start", "passed_ball", "other_advance",
    "runner_double_play", "runner_placed", "pitching_substitution",
    "offensive_substitution", "defensive_switch", "umpire_substitution",
    "pitcher_switch", "game_advisory", "stolen_base", "stolen_base_2b",
    "stolen_base_3b", "stolen_base_home", "caught_stealing", "caught_stealing_2b",
    "caught_stealing_3b", "caught_stealing_home", "defensive_substitution",
    "pickoff_caught_stealing_2b", "pickoff_caught_stealing_3b",
    "pickoff_caught_stealing_home", "balk", "forced_balk", "wild_pitch", "other_out",
)})

COMPLETED_EVENTS = frozenset(code for code, outcome in STATCAST_EVENTS.items() if outcome.kind != "non_pa")
