# Engineering practices

How code is written in this repo, for any agent or person. These are the habits that would have prevented the findings of QA runs 1 to 4 (see `docs/qa/`). They serve `docs/DATA_CONTRACT.md` (D34): the contract says what the published file may contain, this file says how to write code that keeps it true. Git, identity and commit rules are in `docs/CONTRIBUTING.md`; this file does not repeat them.

## 1. Validate at the boundary

Check every answer from outside (MLB API, Statcast, Savant, a cache file, the snapshot between the pipeline and the generator) whole, right after parsing and before anything reads it. A mandatory field that is missing, an error envelope, a wrong type or a malformed row is a recorded source failure, never an empty list, a zero or a default. A valid empty answer stays valid.

- One explicit schema per endpoint (`data_pipeline/fetchers/mlb_schemas.py`); one row check per Statcast frame (`validate_statcast_rows`). Inside the boundary, access mandatory fields directly: no `.get(<mandatory>, [])` and no `or []` that turns an error into emptiness.
- Unknown is `null`, never `0` and never a guessed default (a throwing hand of "R"). Contract rule 2.
- A malformed answer (a needed column missing or with no usable value) is rejected whole; a figure that cannot be read from a sound answer is unavailable plus a recorded error; a well-formed but incomplete answer is degraded. The criterion and its examples are in the contract, rule 2 ("Malformed or incomplete").

## 2. Decide on raw values

A threshold, a ranking or a "does this exist" test is evaluated on the raw count or measurement, not on a number already rounded for display.

- 374 of 2,500 pitches is 14.96%, drawn as 15.0%: it is below the 15% minimum (`labels.share_at_least` cross-multiplies counts). A pitch thrown 1 in 3,000 times rounds to 0.0% and was still thrown.
- The published JSON carries the raw numbers a check needs (`count`, `total`), so the validator and the critic can repeat the decision.
- Only the last step, the text the fan reads, rounds.

## 3. Red tests first

For every bug and every new rule, write the test before the code, run it, and see it fail for the reason you expect. Then change the code. A test that has never failed has not shown it can.

- A test reproduces the QA probe (or the finding) end to end, through the real fetchers and the real generator where the bug lived, not through a stub that already contains the fix.
- State in the task report how many of the new tests failed before the fix. The ones that passed are controls and are named as such.
- Delete tests that lock in unsafe behavior; never loosen an old fixture to make a new rule pass without saying why (an old fixture that lacks a field the real source always sends is updated, not weakened).

## 4. Invariants and combinations

A single-case test proves one case. Where behavior depends on several independent conditions (API complete, partial or absent; regular season or with postseason; debut, limited or healthy starter; normal day or opening day; hand present or missing), write the invariant once and run it over the product of the conditions.

- The invariants are the contract's rules (section 2 of `docs/DATA_CONTRACT.md`) applied generically: to every field, every group of figures, every emitted phrase. A new field or phrase is covered without writing a new test for it.
- Schemas and registries drive the tests where they can: one negative test per required field generated from the schema; one check per registered claim generated from the registry.
- For every generic check, keep a negative test that feeds it a payload that breaks the rule and requires it to fail.

## 5. Fixtures that do not hide the hard case

A fixture is a claim about what the real source sends. Build it with the pipeline's own functions, from the shape of a real answer, and keep the awkward member in it.

- Include the starter with no pitches, the frame with a column that is entirely null, the month with no rows, the opening day, the hand the lookup returns that the generator does not expect (`S`), the pitch code that is not in the name map.
- A live fixture never starts from a demo payload; a test for "no demo value in live data" uses a demo whose every leaf is a sentinel.
- Prefer a fixture generated from a real file in the local cache over one typed by hand. When one must be typed by hand, say which real answer it imitates.

## 6. Fix the class, not the probe

When a finding shows a mistake, name the class it belongs to and fix it with one mechanism, not with another layer over the probe that was reported.

- Ask, before writing the fix: where else does the code do the same thing? Search for it (a sweep) and list the result in the plan.
- An item from a sweep that touches a decision boundary or a user-visible claim is fixed, not recorded (`docs/CONTRIBUTING.md`, "Sweeps").
- Prefer a structural fix that makes the mistake impossible: the live matchup is built from an empty skeleton and cannot inherit a demo value; every scope is read from one function and cannot disagree; every phrase is emitted through one function that records its condition.
- Do not change a test to match a probe's output. If the probe is wrong, say why.

## 7. Self-review before showing a commit

Before you show the owner a commit (the changed files and the message), review your own diff the way the QA gate will. Go through the ten areas of `docs/QA_PROTOCOL.md` and the contract:

1. Spec conformance: does the task meet its `PLAN.md` description, and does each Gherkin scenario it touches have a test that would fail on regression?
2. Data integrity and leakage: `as_of`, scopes, no demo value in live data.
3. Logic: thresholds and boundaries (equal to the threshold, zero denominators, `None` versus `0`).
4. Error handling: network failure, empty and malformed answers; failures are explicit, never a silent fallback.
5. Security: no secret, no unescaped string, no unpinned action.
6. Usage limits: request caps enforced in code, caches that prevent repeats.
7. Test quality: could each new test fail? Pick a plausible bug and check that a test would catch it.
8. Frontend: `null` renders an explicit "not available" state; no text claims what the data does not support.
9. Docs versus code: `PLAN.md`, `STATUS.md` and `DECISIONS.md` say what the code does.
10. Git hygiene: identity, message format, one task, nothing unrelated in the diff.

Add the contract: for each rule of `docs/DATA_CONTRACT.md`, say in one line whether the change touches it and how the new or changed field, sentence or error satisfies it. Anything you find, fix before showing the commit; anything you decide to leave, say so in `STATUS.md` with the reason.

Also check the shape of the diff:

- `git diff --stat` shows only the lines you changed (no line-ending rewrites). Files are LF in the repo (`.gitattributes`); if a stat is far larger than your change, fix the line endings before showing the commit.

Run `python -m pytest` and `npm test` in the default terminal, with nothing changed in PATH or locale, and `npx tsc --noEmit`, `npm run lint` and `npm run build` when TypeScript changed. The verification line of the commit is their real result.
