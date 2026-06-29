# Data source modes for PitchCraft
DATA_MODE_DEMO = "demo_cached"  # always works, no internet needed
DATA_MODE_SNAPSHOT = "fetched_snapshot"  # fetched once, saved locally
DATA_MODE_LIVE = "live_partial"  # fetched at runtime (optional)

# Source labels for JSON metadata
SOURCE_LABELS = [
    "MLB public schedule/probable pitchers (optional)",
    "Baseball Savant / Statcast-style pitch data (optional)",
    "Cached demo snapshots (always available)",
]

# Active mode for this run - default to demo
ACTIVE_MODE = DATA_MODE_DEMO
