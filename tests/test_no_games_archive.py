"""P1.6: real daily/generator/validator chain, with the source fakes of test_daily.

The previous file is always temporary. Archive rows imitate earlier published
reports from this same fake schedule; no MLB/Savant request is possible.
"""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from data_pipeline import daily, demo_inputs, generate_demo_json as gdj
from data_pipeline.generator_texts import generator_catalog
from data_pipeline.schema import WORKFLOW_AGENTS
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_daily import GAME_DAY, SENTINEL, no_network, out, run, sources  # noqa: F401
from data_pipeline.fetchers import cache_manager, live_pipeline as lp

NEXT_DAY = "2026-07-16"


@pytest.fixture(autouse=True)
def previous(monkeypatch, tmp_path):
    path = tmp_path / "published.json"
    monkeypatch.setattr(gdj, "OUTPUT_PATH", path)
    return path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def empty_day(sources, out, day=NEXT_DAY):
    sources.schedule = {"dates": []}
    return daily.main(["--date", day, "--out", str(out)])


def seed(sources, previous):
    assert run(previous) == 0
    return read(previous)


def expected_row():
    return {
        "id": "2026-07-15:matchup_001", "date": GAME_DAY,
        "title": "Boston Red Sox vs New York Yankees", "status": "upcoming",
        "featured": True, "starter_summary": "Away Ace vs Home Ace",
        "result_label": None, "grade_label": None,
    }


def example_payload(monkeypatch, tmp_path):
    """A deterministic actual daily artifact for the manifest and page fixture."""
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 7, 16, 15, tzinfo=timezone.utc).astimezone(tz)

    no_network.__wrapped__(monkeypatch)
    fake = sources.__wrapped__(monkeypatch, tmp_path)
    monkeypatch.setattr(lp, "datetime", Clock)
    monkeypatch.setattr(gdj, "datetime", Clock)
    previous = tmp_path / "previous.json"
    monkeypatch.setattr(gdj, "OUTPUT_PATH", previous)
    seed(fake, previous)
    out = tmp_path / "empty-day.json"
    assert empty_day(fake, out) == 3
    return read(out)


def test_no_games_scheduled_gherkin_publishes_valid_live_archive(sources, previous, out, capsys):
    seed(sources, previous)
    assert empty_day(sources, out) == 3
    payload = read(out)
    assert payload["metadata"]["data_mode"] == "fetched_snapshot"
    status = payload["metadata"]["data_status"]
    assert status["mode"] == "fetched_snapshot" and status["reason"] is None
    assert status["live_run"]["status"] == "no_games"
    assert status["live_run"]["errors"] == []
    assert payload["matchups"] == [] and payload["featured_matchup_id"] is None
    assert payload["archive"] == [expected_row()]
    assert all(check.passed for check in validate_payload(payload))
    assert daily.main(["--check", str(out)]) == 0
    # Report-only sentences must not claim that agents wrote a report or that a featured game exists.
    outputs = [step["output"] for step in payload["agent_workflow"]["steps"]]
    assert outputs == ["Loaded data for 0 matchups."]
    assert "daily: failed" not in capsys.readouterr().err


def test_first_live_no_games_day_has_an_empty_archive(sources, previous, out):
    assert not previous.exists()
    assert empty_day(sources, out) == 3
    assert read(out)["archive"] == []


def test_request_audit_counts_real_boundaries_and_stays_out_of_public_data(sources, out, capsys):
    sources.schedule = {"dates": []}
    record, _ = lp.run_live_pipeline(NEXT_DAY)
    assert record["requests"] == {
        "mlb_api": {"schedule": 1}, "statcast_pitcher": 0,
        "savant_closed_months": 0, "savant_open_months": 0,
    }
    assert empty_day(sources, out) == 3
    log = next(line for line in capsys.readouterr().out.splitlines() if line.startswith("daily: requests "))
    assert json.loads(log.removeprefix("daily: requests ")) == record["requests"]
    assert "requests" not in read(out)["metadata"]["data_status"]["live_run"]


@pytest.mark.parametrize("mode", ["demo_cached", "demo_fallback"])
def test_demo_origins_never_supply_archive_rows(sources, previous, out, mode):
    demo = demo_inputs.build_demo_payload()
    demo["metadata"]["data_mode"] = mode
    previous.write_text(json.dumps(demo), encoding="utf-8")
    assert empty_day(sources, out) == 3
    assert read(out)["archive"] == []


def test_live_game_day_also_carries_previous_reports(sources, previous, out):
    seed(sources, previous)
    sources.schedule = deepcopy(sources.schedule)
    game = sources.schedule["dates"][0]["games"][0]
    game.update(officialDate=NEXT_DAY, gameDate=f"{NEXT_DAY}T23:05:00Z")
    assert daily.main(["--date", NEXT_DAY, "--out", str(out)]) == 0
    assert read(out)["archive"] == [expected_row()]
    assert read(out)["matchups"][0]["date"] == NEXT_DAY


def test_same_day_rerun_never_archives_todays_matchup(sources, previous, out):
    seed(sources, previous)
    assert run(out) == 0
    assert read(out)["archive"] == []


def test_repeated_empty_days_retain_each_report_once(sources, previous, out):
    seed(sources, previous)
    assert empty_day(sources, out) == 3
    previous.write_bytes(out.read_bytes())
    assert empty_day(sources, out, "2026-07-17") == 3
    assert read(out)["archive"] == [expected_row()]


def test_daily_ids_reused_on_different_days_do_not_erase_reports(sources, previous, out):
    seed(sources, previous)
    sources.schedule = deepcopy(sources.schedule)
    sources.schedule["dates"][0]["games"][0].update(officialDate=NEXT_DAY, gameDate=f"{NEXT_DAY}T23:05:00Z")
    assert daily.main(["--date", NEXT_DAY, "--out", str(out)]) == 0
    previous.write_bytes(out.read_bytes())
    assert empty_day(sources, out, "2026-07-17") == 3
    assert [row["id"] for row in read(out)["archive"]] == ["2026-07-16:matchup_001", "2026-07-15:matchup_001"]


def test_archive_carries_every_published_report_from_a_multi_game_day(sources, previous, out):
    game = deepcopy(sources.schedule["dates"][0]["games"][0])
    sources.schedule = {"dates": [{"games": [{**deepcopy(game), "gamePk": pk} for pk in range(1, 6)]}]}
    published = seed(sources, previous)
    assert len(published["matchups"]) == 3
    assert published["metadata"]["data_status"]["live_run"]["games_live"] == 3  # current three-game limit
    assert empty_day(sources, out) == 3
    assert {row["id"] for row in read(out)["archive"]} == {
        "2026-07-15:matchup_001", "2026-07-15:matchup_live_2", "2026-07-15:matchup_live_3",
    }


def test_archive_retains_the_latest_sixty_reports(sources, previous, out):
    payload = seed(sources, previous)
    rows = []
    for days in range(1, 61):
        day = (date.fromisoformat(GAME_DAY) - timedelta(days=days)).isoformat()
        rows.append({**expected_row(), "id": f"{day}:matchup_001", "date": day})
    payload["archive"] = rows  # newest first, as an actual publisher writes it
    previous.write_text(json.dumps(payload), encoding="utf-8")
    assert empty_day(sources, out) == 3
    archive = read(out)["archive"]
    assert len(archive) == 60
    assert archive[0] == expected_row()
    assert archive[-1]["date"] == "2026-05-17"


@pytest.mark.parametrize("bad", ["json", "demo_matchup", "demo_archive", "missing_field", "mode_disagrees"])
def test_malformed_previous_live_input_fails_closed(sources, previous, out, bad):
    payload = seed(sources, previous)
    if bad == "demo_matchup":
        payload["matchups"][0]["data_confidence"]["level"] = "cached"
    elif bad == "demo_archive":
        payload["archive"] = [demo_inputs.build_demo_payload()["archive"][1]]
    elif bad == "missing_field":
        del payload["matchups"][0]["starters"]["away_starter"]["name"]
    elif bad == "mode_disagrees":
        payload["metadata"]["data_status"]["mode"] = "demo_fallback"
    previous.write_text("{broken" if bad == "json" else json.dumps(payload), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(SENTINEL)
    assert empty_day(sources, out) == 1
    assert out.read_bytes() == SENTINEL


@pytest.mark.parametrize("field,value", [
    ("status", "ok"), ("games_scheduled", 1), ("games_live", 1),
    ("games_scheduled", False), ("target_date", "bad"),
    ("as_of", NEXT_DAY), ("run_at", "not an instant"),
    ("errors", [{"source": "mlb_schedule", "code": "request_failed"}]),
])
def test_empty_live_payload_requires_a_genuine_no_games_record(sources, out, field, value):
    assert empty_day(sources, out) == 3
    payload = read(out)
    payload["metadata"]["data_status"]["live_run"][field] = value
    with pytest.raises(ValidationError):
        validate_payload(payload)


@pytest.mark.parametrize("field,value", [
    ("date", NEXT_DAY), ("date", "2026-07-17"), ("date", "bad"),
    ("status", "demo"), ("result_label", "BOS 5 - NYY 3"),
    ("grade_label", "Starter Duel: A"), ("id", "matchup_002"),
    ("featured", "yes"), ("title", None), ("extra", "unlisted"),
])
def test_false_archive_rows_are_rejected_by_publication(sources, previous, out, field, value):
    seed(sources, previous)
    assert empty_day(sources, out) == 3
    payload = read(out)
    payload["archive"][0][field] = value
    with pytest.raises(ValidationError):
        validate_payload(payload)


def test_unavailable_source_state_is_kept_in_the_archive(sources, previous, out):
    payload = seed(sources, previous)
    payload["matchups"][0]["status"] = None
    previous.write_text(json.dumps(payload), encoding="utf-8")
    assert empty_day(sources, out) == 3
    assert read(out)["archive"][0]["status"] is None


def test_page_fixture_is_the_actual_offline_daily_artifact(monkeypatch, tmp_path):
    actual = example_payload(monkeypatch, tmp_path)
    assert actual == read(Path(__file__).parent / "fixtures" / "no_games_live.json")


@pytest.mark.parametrize("no_games", [False, True])
def test_standalone_generator_also_carries_the_previous_live_reports(sources, previous, no_games):
    seed(sources, previous)
    sources.schedule = deepcopy(sources.schedule)
    sources.schedule["dates"][0]["games"][0].update(officialDate=NEXT_DAY, gameDate=f"{NEXT_DAY}T23:05:00Z")
    if no_games:
        sources.schedule = {"dates": []}
    record, snapshot = lp.run_live_pipeline(NEXT_DAY)
    cache_manager.save_processed("live_run", record)
    if snapshot is not None:
        cache_manager.save_processed("live_matchup", snapshot)
    gdj.refresh_live_input()
    assert gdj.main() == 0
    assert read(previous)["archive"] == [expected_row()]


def test_standalone_generator_rejects_malformed_prior_live_input(sources, previous, capsys):
    payload = seed(sources, previous)
    del payload["matchups"][0]["starters"]["away_starter"]["name"]
    previous.write_text(json.dumps(payload), encoding="utf-8")
    before = previous.read_bytes()
    sources.schedule = {"dates": []}
    record, _ = lp.run_live_pipeline(NEXT_DAY)
    cache_manager.save_processed("live_run", record)
    gdj.refresh_live_input()
    assert gdj.main() == 1
    assert previous.read_bytes() == before
    assert "previous" in capsys.readouterr().err


@pytest.mark.parametrize("key,agent,args", [
    ("generator.workflow.identified", 1, {}), ("generator.workflow.generated", 2, {}),
    ("generator.workflow.checked", 3, {"warnings": 0}), ("generator.workflow.graded_none", 4, {}),
])
def test_empty_days_reject_report_only_workflow_claims(sources, out, key, agent, args):
    assert empty_day(sources, out) == 3
    payload = read(out)
    payload["agent_workflow"]["steps"].append({
        "agent": WORKFLOW_AGENTS[agent], "status": "not_applicable" if agent == 4 else "pending",
        "output": str(generator_catalog()(key, **args)),
    })
    payload["claims"].append({"id": "c9000", "key": key, "args": args, "subject": None,
                              "location": "agent_workflow.steps[1].output"})
    with pytest.raises(ValidationError, match=f"rule4:{key}#report"):
        validate_payload(payload)
