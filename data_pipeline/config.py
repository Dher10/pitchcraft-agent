# Data source modes for PitchCraft
DATA_MODE_DEMO = "demo_cached"  # always works, no internet needed
DATA_MODE_SNAPSHOT = "fetched_snapshot"  # fetched once, saved locally
DATA_MODE_LIVE = "live_partial"  # fetched at runtime (optional)
# A live run was attempted but failed or found no usable games. The published
# content is demo data and says so; it is never presented as live.
DATA_MODE_FALLBACK = "demo_fallback"

# Source labels for JSON metadata
SOURCE_LABELS = [
    "MLB public schedule/probable pitchers (optional)",
    "Baseball Savant / Statcast-style pitch data (optional)",
    "Cached demo snapshots (always available)",
]

# What a live file says about its data (rule 6, F3): the sources it uses and, in the footer, where the data comes from.
# A live file never lists a demo source and never says "cached" or "demo"; the demo's own texts stay in `demo_inputs`.
LIVE_SOURCE_LABELS = (
    "MLB Stats API (schedule, probable pitchers, season statistics)",
    "Baseball Savant / Statcast (pitch data, team batting splits)",
)
LIVE_DISCLAIMERS = (
    "Data from the MLB Stats API and Baseball Savant (Statcast). Not affiliated with MLB.",
    "For information only: no predictions and no betting advice.",
)

# Active mode for this run - default to demo
ACTIVE_MODE = DATA_MODE_DEMO
