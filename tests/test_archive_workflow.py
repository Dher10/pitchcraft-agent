"""The step summary of archive-backfill.yml shows the owner what V should be (owner, Nov 12).

The owner sets V from the full postseason during the workflow dry run on main, so the run prints the prior MLB seasons of
all built starters and the veteran_duel count for V = 1..10, even when the build step failed half way.
"""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "archive-backfill.yml"


def steps():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["build"]["steps"]


def census():
    found = [step for step in steps() if "archive_dryrun" in str(step.get("run", ""))]
    assert len(found) == 1, "exactly one step prints the census"
    return found[0]


def test_the_census_step_prints_the_distribution_and_the_veteran_counts_for_one_to_ten_into_the_summary():
    run = census()["run"]
    assert "python -m data_pipeline.archive_dryrun --census" in run
    assert '--out "$RUNNER_TEMP/candidate"' in run
    assert "--veteran-sweep 1,2,3,4,5,6,7,8,9,10" in run
    assert '>> "$GITHUB_STEP_SUMMARY"' in run


def test_it_runs_after_the_build_step_even_when_that_step_failed():
    names = [step.get("name") for step in steps()]
    census_name = census()["name"]
    assert names.index(census_name) > names.index("Build the game files")
    assert str(census()["if"]).strip() == "always()"


def test_it_needs_no_v_and_no_secret_and_never_fails_the_job():
    step = census()
    text = str(step)
    assert "--veteran-min" not in text and "inputs.veteran_min" not in text and "secrets." not in text
    # a failure of the census (no game files yet) is said in the summary, never a failed job
    assert "||" in step["run"]


def test_the_census_does_not_replace_the_real_judgement_of_the_folder():
    run = "\n".join(str(step.get("run", "")) for step in steps())
    assert "archive_finalize check" in run and "archive_finalize build" in run
