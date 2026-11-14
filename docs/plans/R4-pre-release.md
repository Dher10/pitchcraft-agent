# R4 pre-release hardening and interim A2

Approved by the owner's 2026-11-14 instruction, under D35 (including Codex).
Base: `7bbbd27`. Task: finish R4's data audit and real-run guard, then the
approved R4-A2 code; stop before R4-D8 or any release.

1. Read-only independent audit of `197bcac..7bbbd27`, including archive
   identity at the base. Record findings in `docs/qa/R4-data-audit-2026-11-14.md`.
2. Fix group 1, red first: bind envelope identity/time/starter facts to the
   embedded report; validate resume fully and against recovered published
   values; bind history cache identity; guard every writable builder directory;
   allow free cached frames at an exhausted HTTP budget.
   Files: `data_pipeline/archive_{games,build,history}.py`, their tests.
3. Fix group 2, red first: constrain publisher destinations before writes,
   keep published payloads immutable, validate manifest counts, preserve unchanged
   manifests, and distinguish isolated game failure from fatal CLI failure.
   Sweep additions within the audit scope: refuse uncharged urllib redirects,
   enforce the already approved 2026 postseason window, guard finalizer output,
   and remove invalid cached candidates before attempted rebuilds.
   Files: `data_pipeline/archive_{build,finalize,index}.py`,
   `scripts/publish_archive.py`, their tests.
4. Real-run guard, red first: share dry-run parser diagnostics with the builder;
   parser mismatch or rejected source final-line data stops the run with the
   existing closed `starter_unconfirmed` code. Cached incomplete games are
   rechecked; a stop prevents finalization/publication of the entire candidate.
   Files: boxscore/build/dryrun/finalize modules and tests as needed.
5. A2, red first: server reads the versioned 2026 index when present; exact
   missing-file fallback to the current daily archive; final scores, conditional
   Grade column, no links, existing style. Validate index fields at the reader
   boundary. Files: `lib/data.ts`, archive reader/types/tests,
   `components/ArchiveTable.tsx`, app wiring/tests, contract claims registry;
   `next.config.ts` only if file tracing requires it.

For each fix group/task: all five commands sequentially in the default terminal
(`python -m pytest`, `npm test`, `npx tsc --noEmit`, `npm run lint`,
`npm run build`), fresh independent reviewer, commit and push to `v2`, then
green CI before the next commit. Update PLAN, STATUS and status archive each time.
One writer; read-only audit/review agents. No edits to decisions or workflows,
no production requests, no writes to `public/data/` or `evals/live/`, no release.
Existing fixtures that contradict the strengthened identity rules are corrected
explicitly; published production payload values are preserved.

Sweep: all candidate/cache/raw output arguments, all game-file consumers,
all manifest derivations, every destination ancestor and file, source provenance
on resume, and the shared parser classifications. No schema/version change.
