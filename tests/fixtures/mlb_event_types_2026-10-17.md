# MLB event types metadata

- Source: https://statsapi.mlb.com/api/v1/eventTypes
- Retrieved: 2026-10-17, one owner-authorized request (P0.16-c2 / D16).
- Response: `mlb_event_types_2026-10-17.json`, unchanged response bytes.
- SHA-256: `138a1ac2d9fb7d193fd9eb3cb289d5e0fc9ddf0f946a998d7eb3130ee4d3fc05`
- 74 unique codes: 27 `plateAppearance=true`, 47 `plateAppearance=false`.
- Public MLB metadata, cached for non-commercial tests; tests make no requests.

`test_event_types_metadata.py` checks the entire domain and every PA/hit flag
against the production map. The PA scoring classes are explicit; no default
turns a new code into an out or a PA. `truncated_pa` is the previously supported
Savant-only non-PA extension, absent from this metadata response.

The metadata labels `fan_interference` and `os_ruling_pending_primary` as PA
without a hit; they use the non-hit at-bat class, without asserting an out.
`batter_interference` is an at-bat out, unlike catcher's interference (excluded
from at-bats). `grounded_into_triple_play` is marked non-PA in this response;
`triple_play` and `strikeout_triple_play` are PA and count one batter each.
