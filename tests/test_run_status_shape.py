"""The run's errors, warnings and the reason of a fallback are a source and a code, nothing else (P0.15-D2.3c, F10).

At HEAD `_run_summary` published every error as the run recorded it (`{source, message, pitcher_id, ...}`, the raw
text of the exception included) and `reason` was a sentence that could carry one too ("Live run unreadable: ..."). Rule 8:
no internals in the public file. Now the record in `data_cache` keeps everything (it is local), and what the file says
is `{source, code}` from the closed sets of `contract_checks` (schema 0.6.0, D38): deduplicated, at most 20, and `reason`
is `null` for a live file and `{source, code}` for a fallback. The console log keeps readable text.

Controls (they pass before the change): the local record keeps the whole message, a warning does not change the run
status, a raw message in a live file is still a rule 8 violation.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
import urllib.error

import pandas as pd
import pytest

from data_pipeline import contract_checks as cc
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager, mlb_schemas
from data_pipeline.fetchers import live_pipeline as lp
from tests.test_snapshot_dates import isolated, pair, resolve, template  # noqa: F401
from tests.test_isolated_games import two_games  # noqa: F401

PIPELINE = Path(lp.__file__)


def run_with(errors=(), warnings=(), **fields):
    return {
        "status": "ok",
        "run_at": "2026-07-15T12:00:00+00:00",
        "target_date": "2026-07-15",
        "as_of": "2026-07-14",
        "games_scheduled": 1,
        "games_live": 1,
        "errors": list(errors),
        "warnings": list(warnings),
        **fields,
    }


# --- the closed sets (D38) ------------------------------------------------------------------------------------


def test_the_closed_sets_are_the_ones_of_d38_and_d39():
    assert cc.RUN_SOURCES == (
        "mlb_schedule",
        "mlb_person",
        "mlb_season_stats",
        "mlb_team_splits",
        "mlb_series_status",
        "statcast_pitcher",
        "savant_team_batting",
        "snapshot",
        "pipeline",
    )
    assert cc.RUN_ERROR_CODES == (
        "request_failed",
        "malformed_response",
        "malformed_rows",
        "missing_column",
        "unusable_column",
        "budget_spent",
        "unknown_value",
        "incomplete_sample",
        "unexpected_error",
        "no_games",
        "no_usable_games",
        "game_rejected",
        "snapshot_mismatch",
        "snapshot_schema_mismatch",
        "no_live_run",
    )


# --- every call site passes a source and a code of the closed sets --------------------------------------------


def _calls(name):
    """The calls of `name` in the pipeline, except the one inside `_record_failure` (it forwards a code)."""

    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    forwarding = {
        id(node)
        for function in ast.walk(tree)
        if isinstance(function, ast.FunctionDef) and function.name == "_record_failure"
        for node in ast.walk(function)
    }
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
        and id(node) not in forwarding
    ]


def test_every_place_that_records_an_error_is_a_call_the_checks_below_can_see():
    # 11 call sites at HEAD (the plan said 13; the count is of the code). A site that goes around the two functions
    # would not be checked, so the textual count must equal the calls found (+1 for each `def`).
    text = PIPELINE.read_text(encoding="utf-8")
    found = len(_calls("_record_error")) + len(_calls("_record_failure"))
    assert found == 11 and text.count("_record_error(") + text.count("_record_failure(") == found + 3  # + the two `def` and the forwarding call


def test_every_call_site_names_a_source_and_a_code_of_the_closed_sets():
    for call in _calls("_record_error"):
        source, code = call.args[0], call.args[1]
        assert isinstance(source, ast.Constant) and source.value in cc.RUN_SOURCES, ast.dump(call)
        assert isinstance(code, ast.Constant) and code.value in cc.RUN_ERROR_CODES, ast.dump(call)
    for call in _calls("_record_failure"):  # the code of an exception is decided by one function
        source = call.args[0]
        assert isinstance(source, ast.Constant) and source.value in cc.RUN_SOURCES, ast.dump(call)


def test_every_warning_site_names_a_source_and_a_code_of_the_closed_sets():
    warnings = _calls("_record_warning")
    assert len(warnings) == 2  # a new site is a new decision: it must be in the sets, or the file drops it
    for call in warnings:
        source, code = call.args[0], call.args[1]
        assert isinstance(source, ast.Constant) and source.value in cc.RUN_SOURCES, ast.dump(call)
        assert isinstance(code, ast.Constant) and code.value in cc.RUN_WARNING_CODES, ast.dump(call)


def test_a_recorded_error_keeps_its_code_its_message_and_its_context_locally(monkeypatch):
    monkeypatch.setattr(lp, "_run_errors", [])

    lp._record_error("statcast_pitcher", "malformed_rows", "3 rows without a date", pitcher_id=7)

    assert lp._run_errors == [
        {"source": "statcast_pitcher", "code": "malformed_rows", "message": "3 rows without a date", "pitcher_id": 7}
    ]


@pytest.mark.parametrize(
    ("exc", "code"),
    [
        (urllib.error.URLError("down"), "request_failed"),
        (urllib.error.HTTPError("u", 503, "x", {}, None), "request_failed"),  # type: ignore[arg-type]
        (TimeoutError("slow"), "request_failed"),
        (OSError("reset"), "request_failed"),
        (mlb_schemas.SourceShapeError("schedule: dates is missing"), "malformed_response"),
        (json.JSONDecodeError("bad", "{", 0), "malformed_response"),
        (pd.errors.ParserError("bad csv"), "malformed_response"),
        (lp.MalformedResponse("not the CSV"), "malformed_response"),
        (lp.TruncatedResponse("25000 rows: result may be truncated"), "malformed_response"),
        (lp.MalformedRows("3 malformed rows"), "malformed_rows"),
        (lp.MissingColumn("no pitch_type"), "missing_column"),
        (lp.UnusableColumn("no usable stand"), "unusable_column"),
        (lp.SavantRequestCapExceeded("cap"), "budget_spent"),
        (lp.SavantOpenMonthBudgetExceeded("open cap"), "budget_spent"),
        (lp.UnknownValue("hand 'X'"), "unknown_value"),
        (KeyError("stand"), "unexpected_error"),
        (ValueError("as_of is not in season"), "unexpected_error"),
    ],
)
def test_an_exception_has_one_code(exc, code):
    assert lp.error_code(exc) == code


def test_the_validators_raise_the_class_of_their_code():
    frame = pd.DataFrame({"pitch_type": ["FF"], "stand": ["R"]})
    with pytest.raises(lp.MissingColumn):
        lp._require_columns(frame, ("game_date",), "x")
    typeless = pd.DataFrame({"pitch_type": [None], "stand": ["R"]})
    with pytest.raises(lp.UnusableColumn):
        lp.require_usable_pitch_columns(typeless, "x")


def test_a_failed_fetch_is_recorded_with_the_code_of_the_failure(monkeypatch, isolated):  # noqa: F811
    monkeypatch.setattr(lp, "_run_errors", [])

    def down(req, timeout=None):
        raise urllib.error.URLError("connection refused: https://statsapi.mlb.com/secret")

    monkeypatch.setattr(lp.urllib.request, "urlopen", down)

    assert lp.fetch_todays_games("2026-07-15") == []

    assert [(e["source"], e["code"]) for e in lp._run_errors] == [("mlb_schedule", "request_failed")]
    assert "refused" in lp._run_errors[0]["message"]  # control: the local record keeps the message


# --- what the file says ---------------------------------------------------------------------------------------


def test_the_summary_carries_a_source_and_a_code_and_nothing_else():
    record = run_with(
        errors=[
            {"source": "statcast_pitcher", "code": "malformed_rows", "message": "KeyError: 'stand'", "pitcher_id": 7},
            {"source": "mlb_person", "code": "budget_spent", "message": "budget of 10 is spent", "pitcher_id": 8},
        ],
        warnings=[{"source": "statcast_pitcher", "code": "unmapped_pitch_type", "message": "FA", "pitch": "FA"}],
    )

    summary = gdj._run_summary(record)

    assert summary["errors"] == [
        {"source": "statcast_pitcher", "code": "malformed_rows"},
        {"source": "mlb_person", "code": "budget_spent"},
    ]
    assert summary["warnings"] == [{"source": "statcast_pitcher", "code": "unmapped_pitch_type"}]


def test_the_summary_deduplicates_and_keeps_the_first_of_each():
    same = {"source": "statcast_pitcher", "code": "malformed_rows", "message": "a", "pitcher_id": 1}
    other = {"source": "mlb_person", "code": "request_failed", "message": "b"}
    record = run_with(errors=[same, {**same, "pitcher_id": 2, "message": "c"}, other, same])

    assert gdj._run_summary(record)["errors"] == [
        {"source": "statcast_pitcher", "code": "malformed_rows"},
        {"source": "mlb_person", "code": "request_failed"},
    ]


def test_the_summary_has_at_most_20_errors_and_20_warnings():
    sources = ("mlb_schedule", "mlb_person", "mlb_season_stats", "mlb_team_splits", "mlb_series_status")
    errors = [{"source": s, "code": c, "message": "x"} for s in sources for c in cc.RUN_ERROR_CODES[:6]]
    warnings = [{"source": s, "code": "unknown_team", "message": "x"} for s in cc.RUN_SOURCES]

    summary = gdj._run_summary(run_with(errors=errors, warnings=warnings * 4))

    assert len(errors) > 20 and len(summary["errors"]) == 20
    assert len(summary["warnings"]) <= 20 and len(summary["warnings"]) == len({s["source"] for s in summary["warnings"]})


@pytest.mark.parametrize(
    "error",
    [
        {"source": "my_laptop", "code": "malformed_rows", "message": "x"},
        {"source": "statcast_pitcher", "code": "KeyError", "message": "x"},
        {"source": "statcast_pitcher", "message": "KeyError: 'stand'"},
        {"message": "x"},
    ],
)
def test_a_record_that_is_not_in_the_closed_sets_is_published_as_unexpected(error):
    summary = gdj._run_summary(run_with(errors=[error]))

    assert len(summary["errors"]) == 1 and set(summary["errors"][0]) == {"source", "code"}
    assert summary["errors"][0]["code"] == "unexpected_error"
    assert summary["errors"][0]["source"] == (error["source"] if error.get("source") in cc.RUN_SOURCES else "pipeline")


def test_a_record_without_a_warnings_list_has_none():
    record = run_with()
    del record["warnings"]

    assert gdj._run_summary(record)["warnings"] == []


# --- the reason of each fallback ------------------------------------------------------------------------------


def status_of(run=None, snapshot=None, raw_run=None):
    if raw_run is not None:
        path = cache_manager.PROCESSED_DIR / "live_run.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw_run)
    elif run is not None:
        cache_manager.save_processed("live_run", run)
    if snapshot is not None:
        cache_manager.save_processed("live_matchup", snapshot)
    return gdj._resolve_live_input()


def reason(status):
    return status["reason"]


def test_a_live_file_has_no_reason(template):  # noqa: F811
    run, snapshot = pair(template)

    live, status = resolve(run, snapshot)

    assert live is not None and status["mode"] == "fetched_snapshot" and status["reason"] is None


def test_an_unreadable_run_record(isolated):  # noqa: F811
    _, status = status_of(raw_run="{not json")

    assert status["mode"] == "demo_fallback"
    assert reason(status) == {"source": "snapshot", "code": "malformed_response"}


def test_an_unreadable_snapshot(isolated):  # noqa: F811
    path = cache_manager.PROCESSED_DIR / "live_matchup.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json")

    _, status = status_of(run=run_with())

    assert reason(status) == {"source": "snapshot", "code": "malformed_response"}


def test_a_failed_run_says_the_code_of_its_first_error(isolated):  # noqa: F811
    errors = [
        {"source": "mlb_schedule", "code": "request_failed", "message": "down"},
        {"source": "statcast_pitcher", "code": "malformed_rows", "message": "x"},
    ]

    snapshot, status = status_of(run=run_with(status="failed", games_live=0, errors=errors))

    assert snapshot is None and reason(status) == {"source": "mlb_schedule", "code": "request_failed"}


def test_a_failed_run_with_no_error_on_record_is_unexpected(isolated):  # noqa: F811
    _, status = status_of(run=run_with(status="failed", games_live=0))

    assert reason(status) == {"source": "pipeline", "code": "unexpected_error"}


def test_a_day_without_games(isolated):  # noqa: F811
    _, status = status_of(run=run_with(status="no_games", games_scheduled=0, games_live=0))

    assert reason(status) == {"source": "mlb_schedule", "code": "no_games"}


def test_games_but_none_usable(isolated):  # noqa: F811
    _, status = status_of(run=run_with(status="no_usable_games", games_live=0))

    assert reason(status) == {"source": "pipeline", "code": "no_usable_games"}


def test_the_snapshot_of_another_run(template):  # noqa: F811
    run, snapshot = pair(template)
    snapshot["run_at"] = "2026-07-04T12:00:00+00:00"

    _, status = resolve(run, snapshot)

    assert reason(status) == {"source": "snapshot", "code": "snapshot_mismatch"}


def test_a_snapshot_that_fails_a_run_level_check(template):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=False)
    snapshot["as_of"] = "2026-07-20"
    run["as_of"] = "2026-07-20"

    _, status = resolve(run, snapshot)

    assert reason(status) == {"source": "snapshot", "code": "snapshot_mismatch"}


def test_every_game_unsafe(template):  # noqa: F811
    run, snapshot = pair(template)
    snapshot["live_games"][0]["home_starter"]["throws"] = "X"

    live, status = resolve(run, snapshot)

    assert live is None and reason(status) == {"source": "snapshot", "code": "game_rejected"}


def test_the_schema_of_the_snapshot(template):  # noqa: F811
    run, snapshot = pair(template)
    snapshot["schema_version"] = "0.5.0"

    _, status = resolve(run, snapshot)

    assert reason(status) == {"source": "snapshot", "code": "snapshot_schema_mismatch"}


def test_every_reason_of_every_fallback_is_in_the_closed_sets(template):  # noqa: F811
    run, snapshot = pair(template)
    snapshot["live_games"][0]["home_starter"]["throws"] = "X"
    _, status = resolve(run, snapshot)

    assert cc._is_source_and_code(status["reason"], cc.RUN_ERROR_CODES)


def test_control_without_any_run_the_demo_says_it_is_the_demo(isolated):  # noqa: F811
    snapshot, status = gdj._resolve_live_input()

    assert snapshot is None and status["mode"] == "demo_cached" and status["live_run"] is None
    assert status["reason"] == {"source": "pipeline", "code": "no_live_run"}  # D39: no free sentence in `reason`
    assert cc._is_source_and_code(status["reason"], cc.RUN_ERROR_CODES)


# --- the dropped game is published as a code, not as its text -------------------------------------------------


def test_a_dropped_game_is_published_as_a_code_with_no_message(template):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=True)

    _, status = resolve(run, snapshot)

    assert {"source": "snapshot", "code": "game_rejected"} in status["live_run"]["errors"]
    assert all(set(e) == {"source", "code"} for e in status["live_run"]["errors"])


def test_the_games_live_of_the_summary_are_the_games_the_file_shows(template):  # noqa: F811
    run, snapshot, _ = two_games(template, bad_first=True)
    run["games_live"] = 2

    _, status = resolve(run, snapshot)

    assert status["live_run"]["games_live"] == 1


def test_control_the_games_live_of_a_run_with_no_dropped_game_is_the_run_s(template):  # noqa: F811
    run, snapshot = pair(template)

    _, status = resolve(run, snapshot)

    assert status["live_run"]["games_live"] == run["games_live"]


# --- controls --------------------------------------------------------------------------------------------------


def test_control_a_raw_message_in_a_live_file_is_still_a_violation(template, monkeypatch):  # noqa: F811
    from tests.test_contract_checks import build, published  # the corpus the contract tests use

    payload = published(build(monkeypatch, "live_errors"))
    assert not [v for v in cc.check_contract(payload) if v.code.startswith("rule8:")]  # what the summary publishes
    payload["metadata"]["data_status"]["live_run"]["errors"][0]["message"] = "KeyError: 'stand'"

    assert "rule8:error_shape" in {v.code for v in cc.check_contract(payload)}


def test_control_a_warning_does_not_change_the_run_status():
    assert lp._run_status({"games_live": 1}, []) == "ok"
