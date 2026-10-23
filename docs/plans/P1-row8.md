# P1 row 8: P1.9 data attribution

Plan of record: `docs/plans/P1.md` section 6 (row 8) and the texts of section 10 (approved 2026-10-21, answer 3). This file adds what the code needs that the plan leaves open.

Written for: the owner and the reviewer.

## What changes

1. `config.LIVE_DISCLAIMERS` has four notes, in this order: the attribution (unchanged), "PitchCraft is free and non-commercial: no ads, no sponsorships and no paid features." (`NON_COMMERCIAL_NOTE`), "Requests to the data sources are cached and the data is not downloaded in bulk." (`CACHING_NOTE`, live only, because only a live run fetches), and the information-only note (unchanged). The demo file's notes gain the non-commercial sentence only.
2. **Rule 6 and the word "cached" (a consequence of the approved text, for the owner to correct).** Rule 6 forbids the word "cached" in a live file's sources and notes (F3: a live page must not say it is a cached demo). The approved caching note contains the word with another meaning. Rule 6 now exempts that exact sentence in `disclaimers` and nothing else: the same sentence among the sources, a longer or changed sentence, or any other text with the word is still `rule6:cached_wording` (`tests/test_attribution.py`). The tests that looked for demo words in a live file skip that one sentence.
3. MLB's notice (`http://gdx.mlb.com/components/copyright.txt`, read 2026-10-23) says: the materials are proprietary to MLB Advanced Media and "only individual, non-commercial, non-bulk use ... is permitted". The approved sentences say non-commercial, cached and not bulk; the existing attribution says the data comes from MLB and that PitchCraft is not affiliated. Nothing is added beyond the approved texts. The owner approves the final wording; if the owner wants the notice's own sentence quoted, that is a new text.
4. Tests: both modes render the attribution/non-commercial notes (the live file's four, the demo's); the page draws no link, image, script, frame or form; a scan of the site's source finds no ad, tracker or script of its own, no host other than MLB, Baseball Savant and the SVG namespace, no `href`, and the analytics package only in `app/layout.tsx` and only with an exact version (P1.10 adds it), with the scanners shown to fail on bad samples.

## Requests

None. One read of MLB's published notice (not the API).
