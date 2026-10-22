"""P1.2-b: `python -m data_pipeline.daily` builds the day's file and replaces nothing unless it is valid and live.

The whole chain runs (`run_live_pipeline`, the generator, `validate_payload`) over fake sources; the only thing faked is
the network. A guard on the socket makes a test that would reach MLB or Savant fail instead of asking them.

The rule under test (docs/plans/P1.md, 4.2): the file named by `--out` is written only when every step passed and the
payload is a live one. Every failure leaves it byte for byte as it was, or absent, and exits 1 with a sanitized
`{source, code}`. A demo or fallback payload is never a candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
import socket

import pytest

from data_pipeline import daily
from data_pipeline import generate_demo_json as gdj
from data_pipeline.contract_checks import RUN_ERROR_CODES, RUN_SOURCES
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import ValidationError, validate_payload
from tests.test_as_of_end_to_end import SCHEDULE, STATCAST, FakeResponse  # the fake sources

ROOT = Path(__file__).resolve().parents[1]
GAME_DAY = "2026-07-15"
SENTINEL = b'{"sentinel": "the previous published file"}\n'


class Sources:
    """The fake network of one test: what the schedule answers, and every request that reached it."""

    def __init__(self) -> None:
        self.schedule: object = SCHEDULE
        self.schedule_error: Exception | None = None
        self.requests: list[str] = []


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("a test reached the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture
def sources(monkeypatch, tmp_path):
    fake = Sources()
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "real_processed")
    monkeypatch.setattr(lp, "TEAM_BATTING_CACHE_DIR", tmp_path / "team_batting")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "_run_warnings", [])
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(lp, "season_dates", lambda season: (lp.date(season, 3, 25), lp.date(season, 9, 27)))
    # What a test of this module leaves in the generator must not reach the next one.
    monkeypatch.setattr(gdj, "_live", gdj._live)
    monkeypatch.setattr(gdj, "_live_status", gdj._live_status)

    def fake_urlopen(req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        fake.requests.append(url)
        if "schedule" in url:
            if fake.schedule_error is not None:
                raise fake.schedule_error
            return FakeResponse(fake.schedule)
        if "/stats?" in url:
            return FakeResponse({"stats": [{"splits": [{"stat": {
                "era": "3.10", "whip": "1.05", "inningsPitched": "9.1", "strikeOuts": 9,
                "baseOnBalls": 3, "homeRuns": 2, "battersFaced": 37}}]}]})
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(lp.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(lp, "statcast_pitcher", lambda start, end, player_id: STATCAST.copy())
    monkeypatch.setattr(lp, "_get_text", lambda url, timeout=60: "")
    return fake


@pytest.fixture
def out(tmp_path):
    return tmp_path / "candidate" / "pitchcraft-demo.json"


def run(out: Path, *extra: str) -> int:
    return daily.main(["--date", GAME_DAY, "--out", str(out), *extra])


def last_failure(capsys) -> dict:
    """The `{source, code}` the run printed on stderr, as the workflow summary will read it."""

    lines = [line for line in capsys.readouterr().err.splitlines() if line.startswith("daily: failed ")]
    assert len(lines) == 1, lines
    return json.loads(lines[0].removeprefix("daily: failed "))


# --- a good run -----------------------------------------------------------------------------------------------


def test_a_good_run_writes_a_valid_live_file_and_exits_0(sources, out):
    assert run(out) == 0

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["metadata"]["data_mode"] == "fetched_snapshot"
    assert payload["metadata"]["data_status"]["mode"] == "fetched_snapshot"
    assert payload["metadata"]["data_status"]["live_run"]["status"] == "ok"
    assert [m["id"] for m in payload["matchups"]] == ["matchup_001"] and payload["archive"] == []
    assert all(check.passed for check in validate_payload(payload))


def test_the_file_is_written_the_way_the_generator_writes_it(sources, out):
    run(out)

    text = out.read_text(encoding="utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert text == json.dumps(json.loads(text), indent=2, allow_nan=False) + "\n"


def test_the_output_directory_is_created_and_an_old_file_is_replaced(sources, out):
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 0

    assert out.read_bytes() != SENTINEL and json.loads(out.read_text(encoding="utf-8"))["matchups"]


def test_a_good_run_says_what_it_made(sources, out, capsys):
    run(out)

    line = [l for l in capsys.readouterr().out.splitlines() if l.startswith("daily: ok ")]
    assert len(line) == 1
    assert json.loads(line[0].removeprefix("daily: ok ")) == {
        "target_date": GAME_DAY, "games_scheduled": 1, "games_live": 1, "matchups": 1, "errors": [], "warnings": [],
    }


def test_the_run_asks_only_for_the_day_it_was_given(sources, out):
    run(out)

    assert any("schedule" in url and GAME_DAY in url for url in sources.requests)


def test_no_trace_of_the_run_is_left_in_the_local_cache_or_the_generator(sources, out, tmp_path):
    before = (gdj._live, dict(gdj._live_status))

    run(out)

    assert not (tmp_path / "real_processed").exists()
    assert cache_manager.PROCESSED_DIR == tmp_path / "real_processed"
    assert (gdj._live, gdj._live_status) == before


# --- every failure leaves the previous file alone ---------------------------------------------------------------


def schedule_with(game_edit=None, games=None) -> dict:
    schedule = json.loads(json.dumps(SCHEDULE))
    day = schedule["dates"][0]
    if games is not None:
        day["games"] = games
    if game_edit is not None:
        game_edit(day["games"][0])
    return schedule


def failure_schedule_unreachable(sources):
    sources.schedule_error = OSError("down")
    return {"source": "mlb_schedule", "code": "request_failed"}


def failure_no_games(sources):
    sources.schedule = {"dates": []}
    return {"source": "mlb_schedule", "code": "no_games"}


def failure_no_usable_game(sources):
    sources.schedule = schedule_with(lambda game: game["teams"]["away"].pop("probablePitcher"))
    return {"source": "pipeline", "code": "no_usable_games"}


def failure_malformed_schedule(sources):
    sources.schedule = {"unexpected": "shape"}
    return {"source": "mlb_schedule", "code": "malformed_response"}


FAILURES = {
    "schedule_unreachable": failure_schedule_unreachable,
    "no_games": failure_no_games,
    "no_usable_game": failure_no_usable_game,
    "malformed_schedule": failure_malformed_schedule,
}


@pytest.mark.parametrize("family", FAILURES)
@pytest.mark.parametrize("before", ["a previous file", "no file"])
def test_a_run_that_fails_leaves_the_output_as_it_was_and_exits_1(sources, out, capsys, family, before):
    expected = FAILURES[family](sources)
    out.parent.mkdir(parents=True)
    if before == "a previous file":
        out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert (out.read_bytes() if out.exists() else None) == (SENTINEL if before == "a previous file" else None)
    assert last_failure(capsys) == expected
    assert expected["source"] in RUN_SOURCES and expected["code"] in RUN_ERROR_CODES


def test_a_snapshot_that_does_not_belong_to_the_run_is_not_published(sources, out, capsys, monkeypatch):
    real = lp.run_live_pipeline

    def other_run(*args, **kwargs):
        record, snapshot = real(*args, **kwargs)
        snapshot["run_at"] = "2020-01-01T00:00:00+00:00"
        return record, snapshot

    monkeypatch.setattr(lp, "run_live_pipeline", other_run)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    assert last_failure(capsys) == {"source": "snapshot", "code": "snapshot_mismatch"}


def test_a_snapshot_of_another_schema_is_not_published(sources, out, capsys, monkeypatch):
    real = lp.run_live_pipeline

    def old_snapshot(*args, **kwargs):
        record, snapshot = real(*args, **kwargs)
        snapshot["schema_version"] = "0.0.1"
        return record, snapshot

    monkeypatch.setattr(lp, "run_live_pipeline", old_snapshot)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    assert last_failure(capsys) == {"source": "snapshot", "code": "snapshot_schema_mismatch"}


def test_a_critic_that_blocks_a_claim_stops_the_file(sources, out, capsys, monkeypatch):
    def blocked(*args, **kwargs):
        raise gdj.CriticBlocked("matchup_001: a claim the data does not back up")

    monkeypatch.setattr(gdj, "_run_agents", blocked)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    failure = last_failure(capsys)
    assert failure == {"source": "pipeline", "code": "critic_unsupported"}


def test_a_payload_that_fails_validation_stops_the_file(sources, out, capsys, monkeypatch):
    real = gdj.build_payload

    def broken(*args, **kwargs):
        payload = real(*args, **kwargs)
        del payload["matchups"][0]["report"]["sections"]
        return payload

    monkeypatch.setattr(gdj, "build_payload", broken)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    assert last_failure(capsys) == {"source": "pipeline", "code": "validation_failed"}


def test_the_validator_is_the_one_of_the_generator(sources, out, capsys, monkeypatch):
    def refuse(payload):
        raise ValidationError([])

    monkeypatch.setattr(daily, "validate_payload", refuse)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL and last_failure(capsys)["code"] == "validation_failed"


def test_a_number_that_is_not_finite_stops_the_file(sources, out, capsys, monkeypatch):
    real = gdj.build_payload

    def with_nan(*args, **kwargs):
        payload = real(*args, **kwargs)
        payload["metadata"]["not_a_number"] = float("nan")
        return payload

    monkeypatch.setattr(gdj, "build_payload", with_nan)
    monkeypatch.setattr(daily, "validate_payload", lambda payload: [])
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL and last_failure(capsys)["code"] == "unexpected_error"


@pytest.mark.parametrize("mode", ["demo_fallback", "demo_cached"])
def test_a_demo_payload_is_never_a_candidate_even_if_it_validates(sources, out, capsys, monkeypatch, mode):
    real = gdj.build_payload

    def demo(*args, **kwargs):
        payload = real(*args, **kwargs)
        payload["metadata"]["data_mode"] = mode
        payload["metadata"]["data_status"]["mode"] = mode
        return payload

    monkeypatch.setattr(gdj, "build_payload", demo)
    monkeypatch.setattr(daily, "validate_payload", lambda payload: [])
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    assert last_failure(capsys) == {"source": "pipeline", "code": "unexpected_error"}


def test_an_exception_nobody_expected_is_an_unexpected_error_and_leaves_the_file(sources, out, capsys, monkeypatch):
    def explode(*args, **kwargs):
        raise RuntimeError("secret internals: /home/runner/token=abc")

    monkeypatch.setattr(gdj, "build_payload", explode)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    captured = capsys.readouterr()
    assert out.read_bytes() == SENTINEL
    assert "daily: failed " + json.dumps({"source": "pipeline", "code": "unexpected_error"}) in captured.err
    assert "token=abc" not in captured.out + captured.err


def test_the_file_is_replaced_in_one_step_or_not_at_all(sources, out, capsys, monkeypatch):
    def fail(source, target):
        raise OSError("disk full")

    monkeypatch.setattr(daily.os, "replace", fail)
    out.parent.mkdir(parents=True)
    out.write_bytes(SENTINEL)

    assert run(out) == 1

    assert out.read_bytes() == SENTINEL
    assert [p.name for p in out.parent.iterdir()] == [out.name]
    assert last_failure(capsys)["code"] == "unexpected_error"


def test_the_failure_line_is_only_a_source_and_a_code(sources, out, capsys):
    failure_no_games(sources)

    run(out)

    assert set(last_failure(capsys)) == {"source", "code"}


# --- --dry-run ------------------------------------------------------------------------------------------------


def test_dry_run_still_writes_the_candidate_and_nothing_else(sources, out, tmp_path):
    served = ROOT / "public" / "data" / "pitchcraft-demo.json"
    served_before = served.read_bytes()

    assert run(out, "--dry-run") == 0

    assert json.loads(out.read_text(encoding="utf-8"))["matchups"]
    assert served.read_bytes() == served_before
    assert sorted(p.name for p in out.parent.iterdir()) == [out.name]
    assert not (tmp_path / "real_processed").exists()


@pytest.mark.parametrize("inside", ["public/data/pitchcraft-demo.json", "evals/live/today.json", "public/data/x/y.json"])
def test_dry_run_refuses_an_output_inside_the_published_paths_before_any_request(
    sources, capsys, monkeypatch, tmp_path, inside
):
    # The published paths are pointed at a temporary tree: if the refusal regressed, no real file could be overwritten.
    monkeypatch.setattr(daily, "PUBLISHED_PATHS", (tmp_path / "public" / "data", tmp_path / "evals" / "live"))
    target = tmp_path / inside

    code = daily.main(["--date", GAME_DAY, "--out", str(target), "--dry-run"])

    assert code == 2 and sources.requests == []
    assert not target.exists()
    assert "dry-run" in capsys.readouterr().err


def test_the_real_published_paths_are_the_ones_of_d15():
    assert daily.PUBLISHED_PATHS == (ROOT / "public" / "data", ROOT / "evals" / "live")


def test_without_dry_run_the_output_path_is_not_restricted(sources, out):
    assert run(out) == 0


def test_the_output_is_required(sources, capsys):
    with pytest.raises(SystemExit) as caught:
        daily.main(["--date", GAME_DAY])

    assert caught.value.code == 2 and sources.requests == []


def test_a_date_that_is_not_a_date_is_a_usage_error_and_asks_nobody(sources, out):
    with pytest.raises(SystemExit) as caught:
        daily.main(["--date", "yesterday", "--out", str(out)])

    assert caught.value.code == 2 and sources.requests == [] and not out.exists()


# --- --check (the publish job re-validates the artifact it downloaded; no network) ------------------------------


def check(path: Path, *extra: str) -> int:
    return daily.main(["--check", str(path), *extra])


@pytest.fixture
def candidate(sources, out):
    assert run(out) == 0
    sources.requests.clear()
    return out


def test_check_accepts_the_candidate_a_good_run_wrote_and_asks_nobody(candidate, sources, capsys):
    before = candidate.read_bytes()

    assert check(candidate) == 0

    assert sources.requests == [] and candidate.read_bytes() == before
    assert "daily: check ok" in capsys.readouterr().out


def test_check_refuses_the_committed_demo_file(sources, capsys):
    demo = ROOT / "public" / "data" / "pitchcraft-demo.json"

    assert check(demo) == 1

    assert last_failure(capsys) == {"source": "pipeline", "code": "unexpected_error"}


def test_check_refuses_a_file_that_fails_validation(candidate, capsys):
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    del payload["matchups"][0]["report"]["sections"]
    candidate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    assert check(candidate) == 1

    assert last_failure(capsys) == {"source": "pipeline", "code": "validation_failed"}


@pytest.mark.parametrize("mode", ["demo_fallback", "demo_cached"])
def test_check_refuses_a_demo_file_even_if_it_validates(candidate, capsys, monkeypatch, mode):
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    payload["metadata"]["data_mode"] = mode
    payload["metadata"]["data_status"]["mode"] = mode
    candidate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(daily, "validate_payload", lambda payload: [])

    assert check(candidate) == 1

    assert last_failure(capsys) == {"source": "pipeline", "code": "unexpected_error"}


@pytest.mark.parametrize("field", ["data_mode", "data_status.mode"])
def test_check_refuses_a_file_whose_two_mode_fields_disagree(candidate, capsys, monkeypatch, field):
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    if field == "data_mode":
        payload["metadata"]["data_mode"] = "demo_fallback"
    else:
        payload["metadata"]["data_status"]["mode"] = "demo_fallback"
    candidate.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(daily, "validate_payload", lambda payload: [])

    assert check(candidate) == 1

    assert last_failure(capsys) == {"source": "pipeline", "code": "unexpected_error"}


@pytest.mark.parametrize(
    "text",
    ["", "not json", "[]", '"a string"', "null", '{"metadata": {"data_status": {"mode": "fetched_snapshot"}}}'],
)
def test_check_refuses_text_that_is_not_a_payload(tmp_path, capsys, text):
    path = tmp_path / "x.json"
    path.write_text(text, encoding="utf-8")

    assert check(path) == 1

    failure = last_failure(capsys)
    assert set(failure) == {"source", "code"} and failure["source"] == "pipeline"


def test_check_refuses_a_missing_file(tmp_path, capsys):
    assert check(tmp_path / "nope.json") == 1

    assert last_failure(capsys)["source"] == "pipeline"


def test_check_refuses_a_number_that_is_not_finite(candidate, capsys, monkeypatch):
    text = candidate.read_text(encoding="utf-8")
    candidate.write_text(text.replace('"matchups": [', '"not_a_number": NaN, "matchups": [', 1), encoding="utf-8")
    monkeypatch.setattr(daily, "validate_payload", lambda payload: [])

    assert check(candidate) == 1

    assert last_failure(capsys)["source"] == "pipeline"


def test_check_never_echoes_the_text_of_the_file_it_refused(tmp_path, capsys):
    path = tmp_path / "x.json"
    path.write_text("secret internals: /home/runner/token=abc", encoding="utf-8")

    assert check(path) == 1

    captured = capsys.readouterr()
    assert "token=abc" not in captured.out + captured.err


@pytest.mark.parametrize("extra", [["--out", "x.json"], ["--date", GAME_DAY], ["--dry-run"]])
def test_check_is_alone(tmp_path, capsys, extra):
    path = tmp_path / "x.json"
    path.write_text("{}", encoding="utf-8")

    with pytest.raises(SystemExit) as caught:
        check(path, *extra)

    assert caught.value.code == 2


# --- schema 0.9.0 (P1.5-a): the series field --------------------------------------------------------------------


def test_the_snapshot_of_each_live_game_carries_series_null_until_row_7(sources):
    snapshot = lp.build_live_snapshot(GAME_DAY)

    assert snapshot["live_games"] and all("series" in game and game["series"] is None for game in snapshot["live_games"])


def test_a_good_run_publishes_series_null_for_its_matchups(sources, out):
    assert run(out) == 0

    matchups = json.loads(out.read_text(encoding="utf-8"))["matchups"]
    assert matchups and all("series" in matchup and matchup["series"] is None for matchup in matchups)


# --- structure ------------------------------------------------------------------------------------------------


def test_the_cli_runs_as_a_module():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "data_pipeline.daily", "--help"], cwd=ROOT, capture_output=True, text=True, timeout=120
    )

    assert result.returncode == 0 and "--out" in result.stdout and "--dry-run" in result.stdout and "--date" in result.stdout
