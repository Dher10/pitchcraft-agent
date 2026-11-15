# Fonts

## Big Shoulders Display (display face, D67)

`big-shoulders-display-latin-wght-normal.woff2`: the unmodified Latin, variable-weight (100 to 900), normal-style file from the npm package `@fontsource-variable/big-shoulders-display@5.3.0`, copied on 2026-11-15 from the owner's design export (`docs/design/fonts/`). Used for page titles, names of starters and clubs in heads, the wordmark and every featured number. Loaded with `next/font/local` as `--font-display` in `app/layout.tsx`. The copyright notice and the SIL Open Font License 1.1 are in `LICENSE-big-shoulders-display.txt`.

## IBM Plex

Unmodified Latin, normal-style WOFF2 files from the exact npm packages
`@fontsource/ibm-plex-sans@5.3.0` (400, 500, 600, 700) and
`@fontsource/ibm-plex-mono@5.3.0` (500, 600), downloaded on 2026-10-23.
These preserve the families, weights and subset used by the root layout.
The build uses `next/font/local`; it does not contact Google Fonts.

The original IBM copyright notices and SIL Open Font License 1.1 are
retained verbatim in OFL.txt and OFL-mono.txt. Redistribution with the
application is permitted by that license; the font files are not sold alone.

IBM Plex Mono is retired by the design system. It stays until the unit that removes its last use (U6, `docs/plans/R4-U.md`).

Package archive SHA-512 integrity from npm:

- Sans: `sha512-CbE4CbbEEZJX860XyUiRpsksXIQR8Rp2XDva2VO53NJox9tVNtusrysd2x5YkUEY3ErQ66W1IiiQL8/wihhw5w==`
- Mono: `sha512-eTgnZjZEGk1QtD3ZstF+Vclo2HLAni8YMy34/DxllwZvyz1lR/1RF/xTiAquOBO7MvqBx8D2Ig2WCPMVfdZu7Q==`
