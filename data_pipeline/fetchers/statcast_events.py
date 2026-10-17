"""Known Statcast event outcomes, shared by pitcher and team derivations.

The values come from the cached public Savant rows and the existing compound-
event fixtures. Unlisted values must remain unknown rather than become outs.
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
    "strikeout_double_play": EventOutcome("strikeout"),
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
    "field_error": EventOutcome("at_bat"),
    "fielders_choice": EventOutcome("at_bat"),
    "fielders_choice_out": EventOutcome("out"),
    "truncated_pa": EventOutcome("non_pa"),
}

COMPLETED_EVENTS = frozenset(code for code, outcome in STATCAST_EVENTS.items() if outcome.kind != "non_pa")
