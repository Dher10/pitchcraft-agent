"""R4-D4: the backfill runner: ceilings at the HTTP layer, resume, per-game isolation, published reports, the out-dir guard
(D66, D15, docs/plans/R4.md 4.1 to 4.5). No network: every dependency is a fake; the real wiring is exercised only
through the charged HTTP layer (`enforced`) and the argument checks of `main`.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_pipeline import archive_build as ab
from data_pipeline import archive_games as ag
from tests.test_archive_boxscore import box
from tests.test_archive_games import PUBLISHED, SOURCE, records, schedule_game

REPO = Path(__file__).resolve().parents[1]
DAY = "2026-10-23"


def day_records(*extra):
    return records(schedule_game(), *extra)


class World:
    """Fakes for every dependency, recording what was asked."""

    def __init__(self, days=None, boxes=None, fail=None, ceiling_on=None):
        self.days = days or {DAY: day_records()}
        self.boxes = boxes or {849805: box()}
        self.fail = fail or {}
        self.ceiling_on = ceiling_on or set()
        self.asked = SimpleNamespace(days=[], builds=[], boxes=[], history=[])

    def deps(self, published=None, ledger=None):
        def fetch_day(day):
            self.asked.days.append(day)
            if ledger is not None:
                ledger.charge("mlb")
            return self.days.get(day, [])

        def build_report(record):
            pk = record["game_pk"]
            self.asked.builds.append(pk)
            if pk in self.ceiling_on:
                raise ab.CeilingReached("savant")
            if pk in self.fail:
                raise self.fail[pk]
            return deepcopy(PUBLISHED), {}

        def fetch_box(pk):
            self.asked.boxes.append(pk)
            if ledger is not None:
                ledger.charge("mlb")
            if self.boxes.get(pk) is None:
                raise OSError("no boxscore")
            return self.boxes[pk]

        def prior(pid):
            self.asked.history.append(pid)
            return 8 if pid == 607259 else None

        return ab.Dependencies(fetch_day, build_report, fetch_box, prior, published)


def two_games():
    other = schedule_game(pk=849806, day=DAY, away=147, home=111, away_pp=1, home_pp=2, start="2026-10-24T01:00:00Z")
    return {DAY: records(schedule_game(), other)}


# --- the ledger and the ceilings ---------------------------------------------------------------------------------------

def test_the_ceilings_are_those_of_d66():
    assert ab.CEILINGS == {"mlb": 319, "savant": 190} and sum(ab.CEILINGS.values()) == 509


def test_the_ledger_counts_and_stops_exactly_at_the_ceiling():
    ledger = ab.Ledger({"mlb": 3, "savant": 1})
    for _ in range(3):
        ledger.charge("mlb")
    with pytest.raises(ab.CeilingReached) as caught:
        ledger.charge("mlb")
    assert caught.value.source == "mlb" and ledger.used == {"mlb": 3, "savant": 0}  # a refused request is not counted
    ledger.charge("savant")  # the other source has its own ceiling
    assert ledger.summary() == {"mlb": {"used": 3, "ceiling": 3}, "savant": {"used": 1, "ceiling": 1}}


def test_one_request_below_the_ceiling_passes_and_a_batch_that_would_pass_it_does_not():
    ledger = ab.Ledger({"mlb": 5, "savant": 5})
    ledger.charge("mlb", 5)
    ledger = ab.Ledger({"mlb": 5, "savant": 5})
    with pytest.raises(ab.CeilingReached):
        ledger.charge("mlb", 6)
    assert ledger.used["mlb"] == 0


@pytest.mark.parametrize("args", [("other", 1), ("mlb", -1)])
def test_an_unknown_source_or_a_negative_count_is_a_programming_error(args):
    with pytest.raises(ValueError):
        ab.Ledger().charge(*args)


def test_a_ceiling_is_not_an_exception_the_fetchers_can_swallow():
    assert not issubclass(ab.CeilingReached, Exception) and issubclass(ab.CeilingReached, BaseException)


def fake_pipeline(calls):
    ns = SimpleNamespace()
    ns._pitcher_statcast_run = {"requests": 0}

    def get_json(url, *args, **kwargs):
        calls.append(("mlb", url))
        return {"url": url}

    def savant_get(url, *args, **kwargs):
        calls.append(("savant", url))
        return "csv"

    def frame(*args, **kwargs):
        ns._pitcher_statcast_run["requests"] += 3  # one call may send several HTTP requests
        calls.append(("frame", args))
        return "frame"

    ns.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN = 20

    class PitcherStatcastBudgetExceeded(RuntimeError):
        pass

    ns.PitcherStatcastBudgetExceeded = PitcherStatcastBudgetExceeded
    ns._get_json, ns._savant_get, ns._statcast_pitcher_frame = get_json, savant_get, frame
    return ns


def test_enforced_charges_every_request_kind_and_restores_the_functions():
    calls = []
    pipeline = fake_pipeline(calls)
    originals = (pipeline._get_json, pipeline._savant_get, pipeline._statcast_pitcher_frame)
    ledger = ab.Ledger({"mlb": 10, "savant": 10})
    pauses = []
    with ab.enforced(ledger, pipeline, pause=pauses.append):
        pipeline._get_json("u1")
        pipeline._get_json("u2")
        pipeline._savant_get("s1")
        pipeline._statcast_pitcher_frame("a", "b")
    assert ledger.used == {"mlb": 2, "savant": 1 + 3}  # the frame is charged by the requests it really sent
    assert pauses == [ab.MLB_PAUSE_SECONDS] * 2
    assert (pipeline._get_json, pipeline._savant_get, pipeline._statcast_pitcher_frame) == originals


def test_enforced_restores_the_functions_when_the_block_fails():
    pipeline = fake_pipeline([])
    originals = (pipeline._get_json, pipeline._savant_get, pipeline._statcast_pitcher_frame)
    with pytest.raises(RuntimeError):
        with ab.enforced(ab.Ledger(), pipeline):
            raise RuntimeError("x")
    assert (pipeline._get_json, pipeline._savant_get, pipeline._statcast_pitcher_frame) == originals


def test_a_request_past_the_ceiling_is_never_sent_and_a_fetchers_except_exception_cannot_hide_it():
    calls = []
    pipeline = fake_pipeline(calls)
    ledger = ab.Ledger({"mlb": 1, "savant": 1})

    def fetcher():
        """The shape of the pipeline's fetchers: a broad except that records the failure and goes on."""

        try:
            return pipeline._get_json("second")
        except Exception:  # noqa: BLE001 - the point of the test
            return "filled with nothing"

    with ab.enforced(ledger, pipeline):
        pipeline._get_json("first")
        with pytest.raises(ab.CeilingReached):
            fetcher()
    assert [c for c in calls if c[0] == "mlb"] == [("mlb", "first")]


def test_a_frame_is_not_sent_when_the_ceiling_is_spent():
    """A hard ceiling: the 191st Savant request is never made (it used to be checked only after the call)."""

    calls = []
    pipeline = fake_pipeline(calls)
    ledger = ab.Ledger({"mlb": 5, "savant": 3})
    ledger.used["savant"] = 3
    with ab.enforced(ledger, pipeline):
        with pytest.raises(ab.CeilingReached):
            pipeline._statcast_pitcher_frame()
    assert not [c for c in calls if c[0] == "frame"]


def test_a_frame_is_given_only_the_requests_the_ledger_has_left_and_the_cap_is_restored():
    seen = []
    pipeline = fake_pipeline(seen)

    def frame(*args, **kwargs):
        seen.append(pipeline.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN)
        pipeline._pitcher_statcast_run["requests"] += 1
        return "frame"

    pipeline._statcast_pitcher_frame = frame
    ledger = ab.Ledger({"mlb": 5, "savant": 7})
    ledger.used["savant"] = 5  # two left
    with ab.enforced(ledger, pipeline):
        pipeline._statcast_pitcher_frame()
    assert seen == [2] and pipeline.PITCHER_STATCAST_MAX_REQUESTS_PER_RUN == 20 and ledger.used["savant"] == 6


def test_when_the_pipelines_own_cap_stops_a_frame_at_the_ledgers_limit_it_is_the_end_of_the_run():
    pipeline = fake_pipeline([])

    def frame(*args, **kwargs):
        pipeline._pitcher_statcast_run["requests"] += 2
        raise pipeline.PitcherStatcastBudgetExceeded("cap")

    pipeline._statcast_pitcher_frame = frame
    ledger = ab.Ledger({"mlb": 5, "savant": 2})
    with ab.enforced(ledger, pipeline):
        with pytest.raises(ab.CeilingReached):
            pipeline._statcast_pitcher_frame()
    assert ledger.used["savant"] == 2


def test_a_frame_that_fails_for_another_reason_is_charged_and_the_error_goes_on():
    pipeline = fake_pipeline([])

    def frame(*args, **kwargs):
        pipeline._pitcher_statcast_run["requests"] += 1
        raise pipeline.PitcherStatcastBudgetExceeded("the pipeline's own run cap, ledger has plenty left")

    pipeline._statcast_pitcher_frame = frame
    ledger = ab.Ledger({"mlb": 5, "savant": 50})
    with ab.enforced(ledger, pipeline):
        with pytest.raises(pipeline.PitcherStatcastBudgetExceeded):
            pipeline._statcast_pitcher_frame()
    assert ledger.used["savant"] == 1


# --- the out directory (D15) ---------------------------------------------------------------------------------------

@pytest.mark.parametrize(
    "relative", ["public/data", "public/data/archive", "public/data/archive/games", "evals/live", "evals/live/x",
                 "public/data/../data/x", "docs/../public/data"],
)
def test_candidates_are_never_written_under_the_published_paths(relative):
    assert not ab.out_dir_allowed(REPO / relative, REPO)


@pytest.mark.parametrize("relative", [".local/r4", "public", "public/other", "evals/data", "data_cache/archive"])
def test_other_paths_are_allowed(relative):
    assert ab.out_dir_allowed(REPO / relative, REPO)


def test_a_path_outside_the_repository_is_allowed(tmp_path):
    assert ab.out_dir_allowed(tmp_path, REPO)


def test_main_refuses_an_out_dir_under_the_published_paths_before_asking_anything(capsys):
    assert ab.main(["--out", str(REPO / "public" / "data" / "archive"), "--start", DAY, "--end", DAY]) == 2
    assert "out_under_published_paths" in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["--start", DAY], ["--end", DAY], ["--start", "2026-10-24", "--end", "2026-10-23"],
                                  ["--start", "2026-01-01", "--end", "2026-12-31"], ["--start", "x", "--end", "y"]])
def test_main_needs_a_valid_range(argv, tmp_path, capsys):
    assert ab.main(["--out", str(tmp_path), *argv]) == 2
    assert "usage" in capsys.readouterr().err


def test_days_between_is_inclusive_and_bounded():
    assert ab.days_between("2026-10-23", "2026-10-25") == ["2026-10-23", "2026-10-24", "2026-10-25"]
    assert ab.days_between("2026-10-23", "2026-10-23") == ["2026-10-23"]
    with pytest.raises(ValueError):
        ab.days_between("2026-01-01", "2026-12-31")


# --- the run ----------------------------------------------------------------------------------------------------------

def test_a_played_game_is_built_into_a_valid_compact_file(tmp_path):
    world = World()
    summary = ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    path = tmp_path / "games" / "849805.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert summary["built"] == [849805] and summary["failed"] == [] and summary["stopped"] is None
    assert ag.validate_game_file(document) == []
    assert document["origin"]["kind"] == "reconstructed" and document["origin"]["source"] is None
    assert document["starters_check"]["away"] == "started" and document["final_line"]["away"]["strikeouts"] == 7
    assert document["starter_facts"] == {"away": {"id": 607259, "prior_mlb_seasons": 8},
                                         "home": {"id": 694819, "prior_mlb_seasons": None}}
    assert path.read_text(encoding="utf-8") == ag.compact_json(document)
    assert not list(tmp_path.rglob("*.tmp"))


def test_the_boxscore_is_asked_once_per_game_and_supplies_the_starters_and_the_lines(tmp_path):
    """Zero extra requests for the final line (owner answer to OQ14): one boxscore per game, nothing else."""

    world = World(days=two_games(), boxes={849805: box(), 849806: box()})
    ledger = ab.Ledger()
    ab.run([DAY], tmp_path, world.deps(ledger=ledger), ledger)
    assert world.asked.boxes == [849805, 849806]
    assert ledger.used["mlb"] == 1 + 2  # one schedule day, one boxscore per game


def test_a_game_that_was_not_played_gets_no_file_and_no_boxscore(tmp_path):
    postponed = schedule_game(pk=849900, abstract="Final", detailed="Postponed", away_score=0, home_score=0)
    world = World(days={DAY: records(postponed)})
    summary = ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    assert summary["built"] == [] and world.asked.builds == [] and world.asked.boxes == []
    assert not (tmp_path / "games").exists()


def test_an_unreadable_boxscore_makes_the_starters_unknown_and_the_file_is_still_valid(tmp_path):
    world = World(boxes={849805: None})
    ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    document = json.loads((tmp_path / "games" / "849805.json").read_text(encoding="utf-8"))
    assert document["starters_check"]["away"] == "unknown" and document["final_line"] == {"away": None, "home": None}
    assert ag.validate_game_file(document) == []


def test_a_second_run_skips_a_valid_file_and_asks_for_nothing_else(tmp_path):
    world = World()
    ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    again = World()
    ledger = ab.Ledger()
    summary = ab.run([DAY], tmp_path, again.deps(ledger=ledger), ledger)
    assert summary["skipped"] == [849805] and summary["built"] == [] and again.asked.builds == [] and again.asked.boxes == []
    assert ledger.used == {"mlb": 1, "savant": 0}  # only the day's schedule


def test_a_corrupt_or_foreign_file_is_rebuilt_not_trusted(tmp_path):
    world = World()
    ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    path = tmp_path / "games" / "849805.json"
    path.write_text("{not json", encoding="utf-8")
    again = World()
    assert ab.run([DAY], tmp_path, again.deps(), ab.Ledger())["built"] == [849805]
    document = json.loads(path.read_text(encoding="utf-8"))
    document["game_pk"] = 849999
    path.write_text(json.dumps(document), encoding="utf-8")
    assert ab.run([DAY], tmp_path, World().deps(), ab.Ledger())["built"] == [849805]
    assert ab.run([DAY], tmp_path, World().deps(), ab.Ledger(), resume=False)["built"] == [849805]


def test_a_failing_game_leaves_no_file_and_the_others_are_built(tmp_path):
    world = World(days=two_games(), boxes={849805: box(), 849806: box()}, fail={849805: ag.ArchiveError(ag.GAME_NOT_FOUND)})
    summary = ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    assert summary["failed"] == [{"game_pk": 849805, "code": "game_not_found"}] and summary["built"] == [849806]
    assert not (tmp_path / "games" / "849805.json").exists() and (tmp_path / "games" / "849806.json").exists()


def test_an_unexpected_error_is_a_closed_code_never_its_text(tmp_path):
    world = World(fail={849805: RuntimeError("secret path C:/x and a key")})
    summary = ab.run([DAY], tmp_path, world.deps(), ab.Ledger())
    assert summary["failed"] == [{"game_pk": 849805, "code": "unexpected_error"}]
    assert "secret" not in json.dumps(summary)


def test_a_ceiling_stops_the_run_keeps_the_games_built_and_writes_nothing_for_the_game_in_progress(tmp_path):
    world = World(days=two_games(), boxes={849805: box(), 849806: box()}, ceiling_on={849806})
    summary = ab.run([DAY, "2026-10-24"], tmp_path, world.deps(), ab.Ledger())
    assert summary["stopped"] == "ceiling_reached" and summary["built"] == [849805]
    assert summary["failed"][-1] == {"game_pk": None, "code": "ceiling_reached", "source": "savant"}
    assert not (tmp_path / "games" / "849806.json").exists()
    assert world.asked.days == [DAY]  # the run did not go on to the next day


def test_a_ceiling_reached_by_the_ledger_during_the_day_request_stops_before_any_build(tmp_path):
    ledger = ab.Ledger({"mlb": 0, "savant": 190})
    summary = ab.run([DAY], tmp_path, World().deps(ledger=ledger), ledger)
    assert summary["stopped"] == "ceiling_reached" and summary["built"] == [] and not (tmp_path / "games").exists()


def test_a_day_that_cannot_be_read_is_recorded_and_the_other_days_go_on(tmp_path):
    from data_pipeline.fetchers.mlb_schemas import SourceShapeError

    class Days(World):
        def deps(self, published=None, ledger=None):
            deps = super().deps(published, ledger)
            inner = deps.fetch_day

            def fetch_day(day):
                if day == "2026-10-22":
                    raise SourceShapeError("secret detail of the answer")
                if day == "2026-10-24":
                    raise OSError("connection reset by C:/path")
                return inner(day)

            deps.fetch_day = fetch_day
            return deps

    summary = ab.run(["2026-10-22", DAY, "2026-10-24"], tmp_path, Days().deps(), ab.Ledger())
    assert summary["built"] == [849805]
    assert summary["failed"] == [{"game_pk": None, "day": "2026-10-22", "code": "malformed_response"},
                                 {"game_pk": None, "day": "2026-10-24", "code": "request_failed"}]
    assert "secret" not in json.dumps(summary) and "C:/path" not in json.dumps(summary)


def test_only_one_game_can_be_asked_for(tmp_path):
    world = World(days=two_games(), boxes={849805: box(), 849806: box()})
    summary = ab.run([DAY], tmp_path, world.deps(), ab.Ledger(), only=849806)
    assert summary["built"] == [849806] and world.asked.builds == [849806]


# --- the published reports ---------------------------------------------------------------------------------------------

COMMIT = "abf58e1" + "0" * 33


def test_a_published_report_becomes_a_published_live_file_with_its_lineage(tmp_path):
    world = World()
    summary = ab.run([DAY], tmp_path, world.deps(published=[(deepcopy(PUBLISHED), COMMIT, "ab" * 32)]), ab.Ledger())
    document = json.loads((tmp_path / "games" / "849805.json").read_text(encoding="utf-8"))
    assert summary["built"] == [849805] and world.asked.builds == []  # not rebuilt: no Savant request
    assert document["origin"]["kind"] == "published_live" and document["origin"]["source"] == {"commit": COMMIT, "sha256": "ab" * 32}
    assert document["payload"] == PUBLISHED
    assert ag.validate_game_file(document) == []


def test_a_published_report_that_matches_no_game_is_a_failure_and_the_game_is_rebuilt(tmp_path):
    changed = deepcopy(PUBLISHED)
    changed["matchups"][0]["starters"]["away_starter"]["id"] = "5"
    world = World()
    summary = ab.run([DAY], tmp_path, world.deps(published=[(changed, COMMIT, "ab" * 32)]), ab.Ledger())
    assert {"game_pk": None, "code": "game_not_found"} in summary["failed"]
    document = json.loads((tmp_path / "games" / "849805.json").read_text(encoding="utf-8"))
    assert document["origin"]["kind"] == "reconstructed"  # never published_live without a proven match


def test_two_published_reports_for_one_game_are_refused(tmp_path):
    item = (deepcopy(PUBLISHED), COMMIT, "ab" * 32)
    summary = ab.run([DAY], tmp_path, World().deps(published=[item, deepcopy(item)]), ab.Ledger())
    assert {"game_pk": None, "code": "game_not_found"} in summary["failed"]


def test_a_published_report_of_another_day_is_left_for_its_day(tmp_path):
    world = World(days={DAY: day_records(), "2026-10-24": []})
    summary = ab.run(["2026-10-24"], tmp_path, world.deps(published=[(deepcopy(PUBLISHED), COMMIT, "ab" * 32)]), ab.Ledger())
    assert summary["built"] == [] and summary["failed"] == []


def test_a_published_payload_that_is_not_a_live_single_report_is_refused(tmp_path):
    bad = deepcopy(PUBLISHED)
    bad["metadata"]["data_mode"] = "demo_cached"
    summary = ab.run([DAY], tmp_path, World().deps(published=[(bad, COMMIT, "ab" * 32)]), ab.Ledger())
    assert {"game_pk": None, "code": "game_not_found"} in summary["failed"]


def test_a_published_file_is_read_by_its_commit_name_and_its_bytes(tmp_path):
    raw = (REPO / "tests" / "fixtures" / "archive_published_ws_g1.json").read_bytes()
    (tmp_path / f"{COMMIT}.json").write_bytes(raw)
    (payload, commit, digest), = ab._read_published(tmp_path)
    import hashlib

    assert commit == COMMIT and digest == hashlib.sha256(raw).hexdigest() and payload == PUBLISHED
    (tmp_path / "notacommit.json").write_bytes(raw)
    with pytest.raises(ValueError):
        ab._read_published(tmp_path)


# --- guards -----------------------------------------------------------------------------------------------------------

def test_the_runner_reads_no_sealed_set_and_nothing_under_the_published_paths():
    source = Path(ab.__file__).read_text(encoding="utf-8")
    for forbidden in ("import evals", "from evals", ".local", "packets", "evals/data"):
        assert forbidden not in source, forbidden
    # it names the published paths only to refuse them
    assert source.count('"public/data"') == 1 and ab.OUT_FORBIDDEN == ("public/data", "evals/live")
