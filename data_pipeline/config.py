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
# D16: visible attribution, no monetization of any kind, cached fetches and no bulk downloads (P1.9; the wording is the
# owner's, docs/plans/P1.md section 10, read against MLB's notice "individual, non-commercial, non-bulk use").
NON_COMMERCIAL_NOTE = "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features."
# Says requests are cached: not the "cached demo" wording rule 6 forbids over live data, so rule 6 exempts this exact text.
CACHING_NOTE = "Requests to the data sources are cached and the data is not downloaded in bulk."
LIVE_DISCLAIMERS = (
    "Data from the MLB Stats API and Baseball Savant (Statcast), made public by MLB Advanced Media. "
    "PitchCraft is an independent fan project and is not affiliated with MLB.",
    NON_COMMERCIAL_NOTE,
    CACHING_NOTE,
    "For information only: no predictions and no betting advice.",
)

# Active mode for this run - default to demo
ACTIVE_MODE = DATA_MODE_DEMO
