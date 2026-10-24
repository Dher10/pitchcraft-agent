"""P1.2-c: the shape of `.github/workflows/daily.yml` (docs/plans/P1.md, 4.2 and 4.6).

The file is read as GitHub reads it (the parser of `tests/test_workflows.py`) and nothing runs. What matters, and is
pinned here: the job that holds the secret is the only one that does, it runs only on `main`, only when asked to publish
and only after the build; the build job has no secret, no write permission and cannot change a published file; a
workflow input never reaches a shell as text; the key file is written with a private mode and removed at the end.
The generic rules (pinned actions, permissions, runner, no printed secret) are `tests/test_workflows.py`'s and apply to
this file too.
"""

from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess

import pytest

from tests.test_workflows import PUBLISH_ENVIRONMENT, RUNNER, jobs_of, load, steps_of, violations

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / ".github" / "workflows" / "daily.yml"


@pytest.fixture(scope="module")
def text() -> str:
    return PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def doc(text) -> dict:
    return load(text)


def runs(job: dict) -> list[str]:
    return [str(step["run"]) for step in steps_of(job) if "run" in step]


def uses(job: dict, prefix: str) -> list[dict]:
    return [step for step in steps_of(job) if str(step.get("uses", "")).startswith(prefix)]


def index_of(job: dict, needle: str) -> int:
    for position, step in enumerate(steps_of(job)):
        if needle in str(step.get("run", "")):
            return position
    raise AssertionError(f"no step runs {needle!r}")


def test_the_workflow_exists_and_breaks_none_of_the_generic_rules(text):
    assert violations(text) == set()


# --- when it runs ---------------------------------------------------------------------------------------------


def test_it_runs_once_a_day_at_15_utc(doc):
    assert doc["on"]["schedule"] == [{"cron": "0 15 * * *"}]


def test_a_push_runs_it_only_on_v2_and_only_when_this_file_changes(doc):
    assert doc["on"]["push"] == {"branches": ["v2"], "paths": [".github/workflows/daily.yml"]}


def test_it_can_be_started_by_hand_with_a_dry_run_flag_and_a_date(doc):
    inputs = doc["on"]["workflow_dispatch"]["inputs"]

    assert set(inputs) == {"dry_run", "date"}
    assert inputs["dry_run"]["type"] == "boolean" and inputs["dry_run"]["default"] is False
    assert inputs["date"]["type"] == "string" and not inputs["date"].get("required")


def test_no_other_trigger_exists(doc):
    assert set(doc["on"]) == {"schedule", "push", "workflow_dispatch"}


def test_two_runs_never_overlap_and_a_running_one_is_not_cancelled(doc):
    assert doc["concurrency"] == {"group": "daily-data", "cancel-in-progress": False}


def test_the_default_permission_is_read_only(doc):
    assert doc["permissions"] == {"contents": "read"}


# --- the two jobs ---------------------------------------------------------------------------------------------


def test_there_are_two_jobs_build_then_publish(doc):
    jobs = jobs_of(doc)

    assert list(jobs) == ["build", "publish"] and jobs["publish"]["needs"] == "build"
    assert all(job["runs-on"] == RUNNER and job["timeout-minutes"] <= 60 for job in jobs.values())


def test_the_build_job_has_no_secret_no_environment_and_only_read_access(doc, text):
    build = jobs_of(doc)["build"]

    assert "environment" not in build and "secrets" not in str(build)
    assert build.get("permissions", {"contents": "read"}) == {"contents": "read"}
    assert "secrets." not in text.split("  publish:")[0]


def test_only_the_publish_job_has_the_environment_and_the_one_secret(doc, text):
    publish = jobs_of(doc)["publish"]

    assert publish["environment"] == PUBLISH_ENVIRONMENT or publish["environment"] == {"name": PUBLISH_ENVIRONMENT}
    assert re.findall(r"secrets\.([A-Za-z0-9_]+)", text) == ["DATA_DEPLOY_KEY"]
    assert publish.get("permissions", {"contents": "read"}) == {"contents": "read"}


def test_publish_runs_only_on_main_only_when_not_a_push_and_not_a_dry_run(doc):
    condition = str(jobs_of(doc)["publish"]["if"])

    assert "github.ref == 'refs/heads/main'" in condition
    assert "github.event_name != 'push'" in condition
    assert "inputs.dry_run != true" in condition
    assert all(word not in condition for word in (" || ", "always()", "failure()", "cancelled()"))


# --- inputs never reach a shell ----------------------------------------------------------------------------------


def test_no_expression_is_written_into_a_shell_script(doc):
    for name, job in jobs_of(doc).items():
        for script in runs(job):
            assert "${{" not in script, f"{name}: {script}"


def test_the_date_input_reaches_the_build_only_through_an_environment_variable(doc):
    build = jobs_of(doc)["build"]
    steps = [step for step in steps_of(build) if "inputs.date" in str(step)]

    assert len(steps) == 1 and steps[0]["env"]["INPUT_DATE"] == "${{ inputs.date }}"
    assert 'INPUT_DATE"' in steps[0]["run"] and "--date" in steps[0]["run"]


# --- the build job ---------------------------------------------------------------------------------------------------


def test_the_build_checks_out_without_credentials_and_installs_the_pinned_tree(doc):
    build = jobs_of(doc)["build"]

    assert uses(build, "actions/checkout@")[0]["with"]["persist-credentials"] is False
    assert uses(build, "actions/setup-python@")[0]["with"]["python-version"] == "3.14"
    assert any("pip install -r requirements.txt" in script for script in runs(build))


def test_the_data_cache_is_restored_first_and_saved_even_when_the_run_fails(doc):
    build = jobs_of(doc)["build"]
    restore = uses(build, "actions/cache/restore@")[0]
    save = uses(build, "actions/cache/save@")[0]

    assert restore["with"]["path"] == save["with"]["path"] == "data_cache/raw"
    assert restore["with"]["key"] == save["with"]["key"] == "data-cache-${{ github.run_id }}"
    assert restore["with"]["restore-keys"].strip() == "data-cache-"
    assert str(save["if"]) == "always()"
    steps = steps_of(build)
    run_step = next(i for i, s in enumerate(steps) if "data_pipeline.daily" in str(s.get("run", "")))
    assert steps.index(restore) < run_step < steps.index(save)


def test_the_publish_job_restores_and_saves_no_cache(doc):
    publish = jobs_of(doc)["publish"]

    assert uses(publish, "actions/cache") == []


def test_the_build_makes_the_candidate_outside_the_repository_and_as_a_dry_run(doc):
    script = next(s for s in runs(jobs_of(doc)["build"]) if "data_pipeline.daily" in s)

    assert "--dry-run" in script and '--out "$RUNNER_TEMP/candidate/pitchcraft-demo.json"' in script
    assert "public/data" not in script and "evals/live" not in script
    assert 'exit "$status"' in script  # a failed run is a red job, whatever else the step prints


def test_the_build_summary_carries_only_the_lines_the_scripts_print_for_it(doc):
    script = next(s for s in runs(jobs_of(doc)["build"]) if "data_pipeline.daily" in s)

    assert "GITHUB_STEP_SUMMARY" in script and "grep -h '^daily: '" in script


@pytest.mark.parametrize("daily_exit,want", [(0, 0), (3, 0), (1, 1), (2, 2)])
def test_build_step_accepts_only_valid_live_exit_codes(doc, tmp_path, daily_exit, want):
    """Execute the actual shell step; the python function prevents every source request."""
    from tests.test_commit_msg_hook import _find_sh

    shell = Path(_find_sh()).with_name("bash.exe" if os.name == "nt" else "bash")
    script = next(s for s in runs(jobs_of(doc)["build"]) if "data_pipeline.daily" in s)
    stub = f"python() {{ return {daily_exit}; }}\ncat() {{ :; }}\ngrep() {{ :; }}\n"
    path = tmp_path / "step.sh"
    path.write_text(stub + script, encoding="utf-8", newline="\n")
    result = subprocess.run(
        [str(shell), "-e", str(path)], capture_output=True, text=True,
        env={**os.environ, "RUNNER_TEMP": tmp_path.as_posix(),
             "GITHUB_STEP_SUMMARY": (tmp_path / "summary").as_posix(), "INPUT_DATE": ""},
    )
    assert result.returncode == want, result.stderr


def test_no_script_pipes_one_command_into_another_so_no_failure_is_hidden(doc):
    # A step runs under `bash -e` without pipefail: `cmd | tee file` takes the status of `tee`, and a failed rehearsal
    # would leave the job green. Every command writes to a file or to the summary and the step exits with its status.
    single_pipe = re.compile(r"(?<!\|)\|(?!\|)")
    for name, job in jobs_of(doc).items():
        for script in runs(job):
            assert not single_pipe.search(script), f"{name}: {script}"
            assert "|| true" not in script and "set +e" not in script, f"{name}: {script}"
    assert "continue-on-error" not in str(doc)


def test_the_rehearsal_exits_with_the_status_of_the_script_it_rehearses(doc):
    script = next(s for s in runs(jobs_of(doc)["build"]) if "scripts/publish_data.py" in s)

    assert "status=0" in script and "|| status=$?" in script and 'exit "$status"' in script
    assert script.index("GITHUB_STEP_SUMMARY") < script.index('exit "$status"')


def test_the_build_checks_the_publication_as_a_dry_run_after_the_candidate_exists(doc):
    build = jobs_of(doc)["build"]
    script = next(s for s in runs(build) if "scripts/publish_data.py" in s)

    assert "--dry-run" in script and '"$RUNNER_TEMP/candidate/pitchcraft-demo.json"' in script
    assert index_of(build, "data_pipeline.daily") < index_of(build, "scripts/publish_data.py")


def test_the_candidate_is_uploaded_for_seven_days_and_only_if_the_build_passed(doc):
    upload = uses(jobs_of(doc)["build"], "actions/upload-artifact@")[0]

    assert upload["with"]["name"] == "candidate" and upload["with"]["retention-days"] == 7
    assert upload["with"]["if-no-files-found"] == "error"
    assert "if" not in upload  # the default is success(): a failed build uploads nothing for publish to find


# --- the publish job ---------------------------------------------------------------------------------------------


def test_publish_downloads_the_artifact_and_checks_it_again_before_anything_else(doc):
    publish = jobs_of(doc)["publish"]
    download = uses(publish, "actions/download-artifact@")[0]

    assert download["with"]["name"] == "candidate"
    assert uses(publish, "actions/checkout@")[0]["with"]["persist-credentials"] is False
    steps = steps_of(publish)
    check = index_of(publish, "data_pipeline.daily --check")
    assert steps.index(download) < check < index_of(publish, "scripts/publish_data.py")
    assert 'pitchcraft-demo.json' in publish["steps"][check]["run"]


def test_the_key_reaches_a_private_file_through_the_environment_and_is_removed_at_the_end(doc):
    publish = jobs_of(doc)["publish"]
    steps = steps_of(publish)
    writing = next(s for s in steps if "DATA_DEPLOY_KEY" in str(s.get("env", {})))

    assert writing["env"] == {"DATA_DEPLOY_KEY": "${{ secrets.DATA_DEPLOY_KEY }}"}
    assert "umask 077" in writing["run"] and '> "$RUNNER_TEMP/deploy_key"' in writing["run"]
    assert "echo" not in writing["run"] and "cat" not in writing["run"]
    last = steps[-1]
    assert str(last["if"]) == "always()" and 'rm -f "$RUNNER_TEMP/deploy_key"' in last["run"]
    assert steps.index(writing) < index_of(publish, "scripts/publish_data.py") < len(steps) - 1


def test_publish_runs_the_script_for_real_with_the_key_and_the_candidate(doc):
    script = next(s for s in runs(jobs_of(doc)["publish"]) if "scripts/publish_data.py" in s)

    assert '--key-file "$RUNNER_TEMP/deploy_key"' in script and "--dry-run" not in script
    assert '"$RUNNER_TEMP/candidate/pitchcraft-demo.json"' in script


def test_no_job_writes_to_a_published_path_by_hand(text):
    assert "git push" not in text and "git commit" not in text and "git add" not in text
    assert "public/data" not in text.replace("public/data/pitchcraft-demo.json", "")
