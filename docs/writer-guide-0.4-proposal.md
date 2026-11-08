# Writer guide 0.4: proposals for the owner's approval

Status: PROPOSAL, nothing here is in the guide, the prompt or the checks yet. Evidence: the second run of the ten B1 dev examples (`docs/b1-dev-examples.md`; 20 model candidates, 457 sentences, 162 failed checks, none accepted; 17 of the 20 candidates come from the fallback model `gemini-3.1-flash-lite`; dev cases only). Style lens: the installed `humanizer` skill (patterns from Wikipedia's "Signs of AI writing"), used at design time only. It never runs on a report; a second model rewrite would break the evidence chain of each sentence and double the capacity problem. Before/after examples are from the dev outputs of that run, with the "after" written by hand from the same cited facts.

## Part A: rules that were too rigid, or input that was awkward, shown by the data

None of these needs the writer to say more. Each can be verified by code, so none weakens the evidence chain. They are decisions for you because they change a rule of the approved guide.

| # | What the model did | Count in run 2 | Proposal |
|---|---|---|---|
| A1 | Wrote the short form the usual way round: "earned run average (ERA)" instead of "ERA (earned run average)" | 21 of 28 `W11.expansion` failures | Accept either order. Code checks that the long and the short form are both there, in parentheses, once per report, first use cited. |
| A2 | Movement sentence with another verb or order: "moving 14.8 in. sideways and 14.2 in. up" without "compared with ...", or the clause placed after "and 18.1 in. up" | 6 `W8.form` | Accept "moves" or "moving", and the comparison clause once, at the start or the end. Both numbers and both directions are still verified against the cited values. |
| A3 | "Watch if ..." | 3 of the 4 `W15.form` (the fourth is "Watch the approach of ...", a model error) | Accept "Watch if" next to "Watch how" and "Watch whether". Same meaning, still a statement, still no outcome. |
| A4 | Rewrote the scope date: the postseason cases carry the label "2026 regular season" plus a separate `through` date, and the model wrote "through Sep 29" | 13 `W1.entity` ("Sep") and 1 `W1.number` ("Aug 6, 2026") | Tell the model to use the scope label exactly and not to build dates (prompt line), or let code verify a "Mon D" rendering of a cited ISO date. I recommend the label only: it is what the fan-visible product shows. |
| A5 | Compared figures with a comparison word ("a lower ERA than ...", "faster", "higher", "fewer", "versus") | 8 `W2.comparison`: 4 on ERA and WHIP, 4 on other figures | ERA, WHIP, OPS, K% and BB% reach the writer as strings ("8.08", ".712", "24.3%"), so no comparison on them can ever be verified. Give the writer a parallel numeric value for these five (not innings, whose ".1" means a third), so the verified comparison of W2 and W9 works for them. |
| A6 | Citation slips: `season_summary.era` without its prefix, `starters.X.thresholds.control` instead of `.sample.thresholds.control`, and the scope label written but not cited | 19 `W1.evidence_path` (34 minus the 15 of the lineup-note defect already fixed) and 6 of the 7 `W1.number` "2026" | No rule change. Keep strict; one more prompt line "write the full path as shown, and cite the scope label whenever you write it". |
| A7 | Dropped accents ("Jose Soriano") | 3 `W1.entity` and 3 of the 4 `W1.evidence_value`. "Eury Perez" and "loanDepot Park" also appear in an attempt that failed the structure check first, so no name check ran on them | No rule change (names are compared as written, after NFC). One more prompt line "keep accents and spelling exactly as in DATA". |
| A8 | Capacity: all 33 `http_429` were on the primary model, none on the fallback | 35 of 55 calls | A 429 is a rate or quota limit. Options for you: (1) pace the offline runner at 15 to 20 seconds between calls (the 5-second pause between items is not the D49 retry backoff, so D49 is untouched); (2) read the real limits of `gemini-3.5-flash` for this key in the AI Studio console and tell me the per-minute and per-day numbers, because the documentation lists none; (3) accept that with this key most B1 text will come from the fallback model, which D49 does not count as a primary success. |
| A9 | The other finding lists (`*_strengths`, `*_risks`) are still lists, so they can be cited by index only | none seen in run 2 | Same class as the fixed lineup-note defect. I would make them one string per list too, in the same commit as A5. |

Fixed already, no decision needed: the lineup notes were a list, so the natural citation `findings.lineup_notes.home` pointed at no value (15 of the 34 path failures). They are now one string per side; prompt version `p2.2-2`.

## Part B: style rules for guide 0.4

Counts come from the 20 candidates of run 2 (457 sentences). "Covered by" says which rubric dimension would already catch the problem: U1 is the pairwise fan-usefulness judge, L1 limited-data honesty, G2/R1 groundedness and relevance, S1 the per-rule guide compliance (so any rule added to the guide becomes scored by S1 automatically).

| # | Proposed rule | Pattern (humanizer lens) | Evidence | Covered by L1/U1? |
|---|---|---|---|---|
| S-1 | State the scope once per report, in one early sentence, and again only where a figure has a different scope. Replaces "once per section" in W12. | Repetition by rule: the same qualifier restated everywhere | "regular season through" appears 87 times in 20 candidates (about 4.4 per report) | No. U1 only judges unsupported time claims; S1 scores it once it is a rule. |
| S-2 | Do not give both lineups, or both starters, the same sentence frame. Say what the two sides share in one sentence and what differs in another. At most one run of OPS, K% and BB% per section. | Uniform rhythm, repeated openings and parallel structure (humanizer 6, 7) | "This group/That group/That lineup/This lineup" opens 18 sentences; "The" opens 77 of 457 | No. U1 might prefer the less repetitive text but does not test it. S1 once it is a rule. |
| S-3 | Every sentence carries a cited fact. No filler that only describes the report ("Both starters enter the matchup with distinct pitching profiles"). | Sayings that sound deep, inflated significance, empty closers (humanizer 3, 13) | "Both teams look to adjust to the specific arsenal styles of their opponents"; "Both pitchers are established starters with sufficient data" | Partly. G2/R1 catch an unsupported claim ("established starters"); a harmless empty sentence passes. U1 may notice padding. |
| S-4 | Plain verbs: use "uses", "has", "shows". Avoid "utilizes", "possesses", "exhibits", "displays", "features", "maintains", "demonstrates", "showcases", "highlights". | Overused AI words, avoiding "is/are/has" (humanizer 12, 18) | about 36 hits of utiliz\*, possess\*, exhibit\*, feature(s), maintain(s), demonstrat\*, display(s), showcas\*, highlight\* in 20 candidates | No. S1 once it is a rule (the check can be a small denylist like the others). |
| S-5 | Headline in sentence case, a plain sentence about the game or the duel; no trailing "Matchup" or "Preview". | Decorative headings, title case (humanizer 20) | 8 of 20 headlines capitalize common words ("Start", "Faces", "Matchup", "Duel", "Preview") | No. S1. |
| S-6 | A thing to watch names a cited figure and what to look at; it does not restate a label or say "handle the pitchers". | Vague connection, stacked qualifiers (humanizer 9, 14) | "Watch whether the Marlins lineup can handle the pitchers"; "Watch how the lineups handle the above-average swing-and-miss ability of each starter" | Yes, mostly. U1 asks that the fan "knows what to watch". |
| S-7 | No tails such as "in this matchup", "in that split", "in these encounters", "over the same period". | Filler transitions and run-ups (humanizer 4) | about 25 hits of "in this/that/such matchup(s)", "in this/that split", "in these encounters", "in the same period", "over the same period" | No. S1. |
| S-8 | Do not cite an authority for a plain fact ("according to their profiles"). | Borrowed authority (humanizer 17) | 2 hits | Partly: G2 (no uncited claim). |
| S-9 | State a limitation once per starter, in one sentence with its numbers; do not restate the same frame for each field. | Repetition by rule | `opener-824280`: a four-sentence confidence note that repeats one frame for both starters ("Control and strikeout data for Trey Yesavage are limited with 57 batters faced. 170 batters faced are required ...") | L1 checks that the limitation is stated, not that it is concise. S1. |

### Before and after (dev outputs only; "after" is written by hand from the same cited facts)

**S-1 and S-7 (limited-825104).**
Before: "Bryce Elder throws for the Braves at Chase Field for the 2026 regular season through Apr 3." / "Michael Soroka starts for the Diamondbacks over the 2026 regular season through Apr 3." / "The 2026 regular season through Apr 3 is the scope for these statistics."
After: "Bryce Elder starts for the Braves against Michael Soroka and the Diamondbacks at Chase Field. Every figure below covers the 2026 regular season through Apr 3."

**S-2 (limited-823836).**
Before: "The Miami Marlins lineup has a .734 OPS (on-base plus slugging) against right-handed pitchers over the 2026 regular season through Aug 6. This group posts a 21.0% K% (strikeout rate) and an 8.9% BB% (walk rate) in that matchup." and, in the next section, "The Los Angeles Angels lineup has a .687 OPS against right-handed pitchers over the 2026 regular season through Aug 6. That lineup records a 24.9% K% and an 8.3% BB% against right-handed pitchers."
After: "Against right-handed pitchers the Marlins have a .734 OPS (on-base plus slugging) and the Angels a .687. The Angels have the higher K% (strikeout rate), 24.9% to 21.0%." (The comparison quotes both values with the same measure and scope as W2 requires, but it can pass the checks only after A5, because K% reaches the writer as a string today.)

**S-3 (limited-823863 and veteran-824803).**
Before: "Both teams look to adjust to the specific arsenal styles of their opponents." / "Both pitchers are established starters with sufficient data for these profiles."
After: "Both starters use the four-seam fastball as their primary pitch." (cites `primary_pitch` for both; cut the other two sentences and add a cited fact only where there is one.)

**S-4 (opener-823769).**
Before: "Both pitchers possess above-average swing-and-miss ability according to their profiles."
After: "Both pitchers show above-average swing-and-miss ability." (also S-8)

**S-5 (limited-823863, veteran-824803).**
Before: "Tobias Myers and Eury Perez Start at loanDepot Park" / "Carlos Rodón and Shane Baz Matchup at Oriole Park"
After: "Myers and Eury Pérez meet at loanDepot park." (sentence case, accents kept, the venue spelled as the packet spells it)

**S-6 (limited-823836).**
Before: "Watch whether the Marlins lineup can handle the pitchers."
After: "Watch how often George Klassen throws his Four-seam, which makes up 38.6% of his pitches."

**S-9 (opener-824280).**
Before: a four-sentence confidence note that repeats one frame for both starters ("Control and strikeout data for Trey Yesavage are limited with 57 batters faced. 170 batters faced are required for a control read and 70 for a strikeout read. Control and strikeout data for Brenan Hanifee are limited with 33 batters faced. ...").
After: one sentence in the section where it applies, with no cause word: "Control and strikeout reads for Trey Yesavage are limited: 57 batters faced, with 170 and 70 needed."

## What I need from you

1. Part A: which of A1 to A5 and A9 to adopt (I recommend A1, A2, A3, A4 as label-only, A5 for all five string figures, A9), and your choice for A8.
2. Part B: which of S-1 to S-9 become guide 0.4 rules. Each becomes an S1-scored rule and, where it is a word list (S-4, S-5, S-7), a denylist check; S-1, S-2, S-3, S-6 and S-9 are style judgments the code can only partly check, so I would score them through S1 and the judge, not as code gates.
3. Whether to re-run the ten dev cases again after 0.4 (it needs a new run cap; 95 of 400 experiment calls are used) or to stop here and move to P2.3.
