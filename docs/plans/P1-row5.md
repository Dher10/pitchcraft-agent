# P1 row 5: P1.2-c publish script and `daily.yml`

Plan of record: `docs/plans/P1.md` sections 3.1, 4.2, 4.5, 4.6 and 11 (approved 2026-10-21); the owner's go-ahead for row 5 after G1 to G7 is 2026-10-22. This file only adds what the code needs that the plan leaves open.

Written for: the owner and the reviewer.

## Pieces

1. `data_pipeline/daily.py --check FILE`: re-validates a candidate with no network (JSON, `validate_payload`, live `fetched_snapshot`). Exit 0 valid, 1 invalid, 2 usage. Same sanitized `daily: failed {source, code}` line. The publish job runs it on the downloaded artifact.
2. `scripts/publish_data.py CANDIDATE [--repo DIR] [--remote URL] [--key-file PATH] [--dry-run]`:
   - copies the candidate to `public/data/pitchcraft-demo.json`; the run must start from a clean work tree;
   - skips (exit 0, nothing committed) when the file is unchanged apart from the three timestamps `generated_at`, `data_fetched_at`, `run_at`;
   - refuses (exit 1, work tree restored) if `git status` shows any path outside `public/data/` and `evals/live/` (D15);
   - commits as Daniel Herdenez <edherdenez@gmail.com> with the subject `data: daily update YYYY-MM-DD`, the date being the run's `target_date`;
   - pushes `HEAD:refs/heads/main` (never forced, from the branch `main` only; there is no branch option) with `GIT_SSH_COMMAND` = the key file, `IdentitiesOnly`, `StrictHostKeyChecking=yes` and a `known_hosts` file written from GitHub's three published host keys (pinned in the script; the fingerprints from `gh api meta` equal the ones in GitHub's documentation, read 2026-10-22);
   - `--dry-run` does all of it in a temporary clone of `--repo` and never pushes; prints the file list and the allowlist verdict.
3. `.github/workflows/daily.yml`: `build` (no secret, `contents: read`) and `publish` (environment `data-publish`, only on `main`, not on push, not on `dry_run`), triggers `schedule` 15:00 UTC, `workflow_dispatch` (`dry_run`, `date`) and `push` to `v2` only when `daily.yml` changes; `concurrency: daily-data`. The data cache `data_cache/raw` is restored with `actions/cache/restore` and saved with `actions/cache/save` under `if: always()` so a red run still keeps the Savant months it fetched. The `date` input reaches the shell only through an environment variable (and `daily.py` validates it as a date).
4. `tests/test_workflows.py`: `actions/cache/restore` and `actions/cache/save` get the floor of `actions/cache` (the guard did not know the sub-actions).

## Requests

Pushing this commit changes `daily.yml`, so its push to `v2` runs the daily job once: dry run 1 of the three allowed by D42, at most 20 Savant pitcher + 70 team batting + 10 hand requests and the MLB schedule/season-stats/series reads, with a cold cache. No other request. Tests make none (socket guard / local bare repositories).

## Not here

The real push with the deploy key (it can only happen on `main`, R6/R7), the no-games state (row 9), the heartbeat (row 10).
