# Case-study notes (owner's findings, in the owner's words)

Raw material for the case study. Entries are the owner's own statements, recorded as given on Nov 4 2026 after the dev labeling practice. Nothing here is a measured result; measured results come from the labeled test sample.

## U1 blinding limitation (Nov 4 2026)

"I could identify the LLM report by its style in the pairs, so the U1 result may be biased and must be reported with that limitation."

How to apply: every U1 number (win, tie, loss of the model report against the rules report) is reported with this limitation next to it, for dev and for test. The pairs hide source labels and randomize left/right, but the style of the model text gives it away to this reader.

## Qualitative verdict (Nov 4 2026)

"The LLM text is clearly more readable and useful than the rules text, but it still reads like statistics joined sentence by sentence, not like a person telling the story of the matchup. The guardrails that prevent invention are what flatten the voice."

## Known limitation: similarity claims have no code gate

No code gate catches similarity or contrast claims between the two starters or lineups ("similar profiles", "contrasting", "opposite"). They are caught only by the owner's labels (protocol v2, hard-case rule 6, which labels them unsupported unless the fact table says so) and by the judge prompt `judge-p2`.

## Backlog (next phase, not now)

Code computes the story angles as citable facts, and the LLM narrates them as one human paragraph per matchup side:

- pitcher profile type (for example strikeout versus contact) and pitch-family mix;
- the key matchup;
- the lineup's main weakness.

Still no predictions. The angles are facts with ids, so the existing citation and gate machinery applies to them unchanged. Not started; it needs its own plan and decision.

## U1 result: stated versus revealed preference (Nov 7 2026, owner)

Owner statement: after labeling the sentences, the general impression was that the LLM prose reads better; comparing whole reports side by side, the owner chose the rules report in 7 of 10 non-tie pairs (model report 3 wins, 1 tie, 7 losses over 11 pairs). The rules reports are about 25% longer and carry more information. Both can hold: the LLM writes better sentences but says less. The mapping and computation were verified (hash evidence, orientation test; `docs/results-planB.md` section 12.1) and the owner checked the filled files. The result stands as computed, with the blinding limitation above.

