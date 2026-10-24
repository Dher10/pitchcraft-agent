# MLB season calendar reference

`mlb_seasons_2026.json` is the unmodified 830-byte response to one owner-authorized
request, made outside tests at 2026-10-24T03:10:07 UTC (2026-10-23 locally):

https://statsapi.mlb.com/api/v1/seasons/2026?sportId=1

SHA-256: `86b6a157a6ff38761eb2e4df0edb10ab9209689a430a92ec902c584a1eb2d510`

The machine-readable source URL, retrieval time, digest and request count are
in `mlb_seasons_2026.source.json`. Keep the original bytes and MLB copyright
notice. This is calendar data, not a calendar encoded in Python.

Label generation and offline validation share `season_calendar.py`, which
reads these files without fetching anything, checks the digest and source
shape, and retains prior years when new yearly fixtures are added. If the
season is absent, labels retain the explicit through-date wording.

Refresh once per season before opening day, with one seasons-endpoint request
for that year and a corresponding source/digest file. Keep earlier fixtures
so historical labels remain reproducible. Never acquire or refresh in tests.
