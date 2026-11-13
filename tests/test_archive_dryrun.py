"""The report of the R4-D7 dry run (data_pipeline/archive_dryrun.py). Pure: reads files, never the network.

Its job is to tell apart an unknown starter that MLB did not give from one our parser failed to read (owner, Nov 12: the
second must stop the work), and to measure the request counts, the notable distribution and the veteran threshold.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from data_pipeline import archive_build as ab
from data_pipeline import archive_dryrun as dr
from data_pipeline import archive_games as ag
from tests.test_archive_boxscore import box
from tests.test_archive_build import DAY, World

PROBABLE = 607259


def built(tmp_path):
    """One game built by the real runner with fakes; returns its game file."""

    ab.run([DAY], tmp_path, World().deps(), ab.Ledger())
    return json.loads((tmp_path / "games" / "849805.json").read_text(encoding="utf-8"))


# --- each unknown starter has a reason, and only "MLB gave nothing" is not our fault ------------------------------------

def test_a_readable_side_is_readable():
    assert dr.classify_side(box(), "away", PROBABLE) == "readable"


def test_a_probable_starter_who_did_not_start_is_still_readable():
    assert dr.classify_side(box(away_pitchers=(999, 607259)), "away", PROBABLE) == "readable"


def test_no_boxscore_is_not_a_parser_problem():
    assert dr.classify_side(None, "away", PROBABLE) == "boxscore_not_fetched"


def test_a_report_without_a_probable_starter_is_not_a_parser_problem():
    assert dr.classify_side(box(), "away", None) == "no_probable_starter"


def test_an_empty_pitcher_list_is_mlb_giving_nothing():
    raw = box()
    raw["teams"]["away"]["pitchers"] = []
    assert dr.classify_side(raw, "away", PROBABLE) == "mlb_lacks_data"


@pytest.mark.parametrize("break_it", [
    lambda raw: raw.pop("teams"),
    lambda raw: raw["teams"].pop("away"),
    lambda raw: raw["teams"]["away"].pop("pitchers"),
    lambda raw: raw["teams"]["away"].update(pitchers="607259"),
    lambda raw: raw["teams"]["away"].update(pitchers={"0": 607259}),
    lambda raw: raw["teams"]["away"].pop("players"),
    lambda raw: raw["teams"]["away"].update(players={}),
    lambda raw: raw["teams"]["away"]["players"]["ID607259"]["person"].update(id=1),
    lambda raw: raw["teams"]["away"]["players"]["ID607259"]["person"].pop("fullName"),
    lambda raw: raw["teams"]["away"].update(pitchers=["607259", 111]),
])
def test_data_that_is_there_but_not_read_is_a_parser_mismatch(break_it):
    raw = box()
    break_it(raw)
    assert dr.classify_side(raw, "away", PROBABLE) == "parser_mismatch"


def test_a_broken_side_is_our_parser_even_when_the_report_has_no_probable_starter():
    """The missing probable starter must not hide a shape we cannot read (reviewer round 1, finding 1)."""

    raw = box()
    raw["teams"]["away"].pop("players")
    assert dr.classify_side(raw, "away", None) == "parser_mismatch"


def test_an_empty_pitcher_list_without_a_probable_starter_is_still_mlb_giving_nothing():
    raw = box()
    raw["teams"]["away"]["pitchers"] = []
    assert dr.classify_side(raw, "away", None) == "mlb_lacks_data"


def test_the_other_side_is_not_blamed():
    raw = box()
    raw["teams"]["away"].pop("players")
    assert dr.classify_side(raw, "home", 694819) == "readable"


# --- final-line fields: absent is MLB's, present but rejected is ours ---------------------------------------------------

def test_a_good_line_has_no_mismatch():
    assert dr.line_mismatches(box(), "away") == []


def test_a_field_mlb_does_not_give_is_not_a_mismatch():
    raw = box()
    del raw["teams"]["away"]["players"]["ID607259"]["stats"]["pitching"]["strikeOuts"]
    assert dr.line_mismatches(raw, "away") == []


@pytest.mark.parametrize("field,key,value", [
    ("hits", "hits", "4"), ("hits", "hits", 4.0), ("hits", "hits", -1), ("earned_runs", "earnedRuns", True),
    ("walks", "baseOnBalls", "2"), ("strikeouts", "strikeOuts", "7"), ("innings_pitched", "inningsPitched", 6.1),
    ("innings_pitched", "inningsPitched", "6.3"),
])
def test_a_field_that_is_given_but_not_read_is_a_mismatch(field, key, value):
    raw = box()
    raw["teams"]["away"]["players"]["ID607259"]["stats"]["pitching"][key] = value
    assert dr.line_mismatches(raw, "away") == [field]


def test_a_starter_with_no_pitching_stats_at_all_is_a_mismatch_not_a_guess():
    raw = box()
    del raw["teams"]["away"]["players"]["ID607259"]["stats"]
    assert dr.line_mismatches(raw, "away") == ["stats"]


def test_no_line_is_asked_of_a_side_that_could_not_be_read():
    assert dr.line_mismatches(None, "away") == []


# --- rows, the stop rule ------------------------------------------------------------------------------------------------

def test_a_row_per_side_says_probable_actual_check_and_class(tmp_path):
    document = built(tmp_path)
    rows = dr.starter_rows([document], {849805: box()})
    assert [(r["side"], r["probable_id"], r["actual"], r["check"], r["class"]) for r in rows] == [
        ("away", 607259, {"id": 607259, "name": "Nick Martinez"}, "started", "readable"),
        ("home", 694819, {"id": 694819, "name": "Jacob Misiorowski"}, "started", "readable"),
    ]
    assert {r["game_pk"] for r in rows} == {849805}


def test_a_game_with_no_raw_file_is_not_fetched(tmp_path):
    document = built(tmp_path)
    rows = dr.starter_rows([document], {})
    assert {r["class"] for r in rows} == {"boxscore_not_fetched"}


def test_only_our_failures_stop_the_work():
    rows = [
        {"game_pk": 1, "side": "away", "class": "mlb_lacks_data", "line_mismatches": []},
        {"game_pk": 1, "side": "home", "class": "no_probable_starter", "line_mismatches": []},
    ]
    assert dr.stop_reasons(rows) == []


def test_a_parser_mismatch_or_a_rejected_field_stops_the_work():
    rows = [
        {"game_pk": 1, "side": "away", "class": "parser_mismatch", "line_mismatches": []},
        {"game_pk": 2, "side": "home", "class": "readable", "line_mismatches": ["hits"]},
    ]
    reasons = dr.stop_reasons(rows)
    assert len(reasons) == 2 and "1" in reasons[0] and "parser_mismatch" in reasons[0] and "hits" in reasons[1]


def test_a_boxscore_that_was_not_fetched_stops_the_work_too():
    """A fetch that failed is not proof that MLB lacks the data: the dry run is repeated, not accepted."""

    rows = [{"game_pk": 2, "side": "away", "class": "boxscore_not_fetched", "line_mismatches": []}]
    assert dr.stop_reasons(rows) != []


# --- requests -----------------------------------------------------------------------------------------------------------

LINE_A = 'archive: {"built": [1], "failed": [], "requests": {"mlb": {"ceiling": 319, "used": 12}, "savant": {"ceiling": 190, "used": 30}}, "skipped": [], "stopped": null}'
LINE_B = 'archive: {"built": [2], "failed": [], "requests": {"mlb": {"ceiling": 319, "used": 7}, "savant": {"ceiling": 190, "used": 4}}, "skipped": [], "stopped": null}'


def test_summaries_are_found_among_other_lines():
    found = dr.parse_summaries("noise\n" + LINE_A + "\nmore noise\n" + LINE_B + "\n")
    assert [s["built"] for s in found] == [[1], [2]]


def test_a_summary_that_is_not_json_is_refused():
    with pytest.raises(ValueError):
        dr.parse_summaries("archive: {not json")


def test_requests_are_added_by_source_and_judged_against_the_ceiling():
    total = dr.total_requests(dr.parse_summaries(LINE_A + "\n" + LINE_B))
    assert total == {"mlb": {"used": 19, "ceiling": 319, "within": True}, "savant": {"used": 34, "ceiling": 190, "within": True}}


def test_a_total_past_a_ceiling_is_said():
    over = LINE_A.replace('"used": 12', '"used": 319')
    total = dr.total_requests(dr.parse_summaries(over + "\n" + LINE_B))
    assert total["mlb"]["within"] is False and total["savant"]["within"] is True


def test_summaries_with_different_ceilings_are_refused():
    other = LINE_B.replace('"ceiling": 319', '"ceiling": 100')
    with pytest.raises(ValueError):
        dr.total_requests(dr.parse_summaries(LINE_A + "\n" + other))


def test_no_summary_is_refused():
    with pytest.raises(ValueError):
        dr.total_requests([])


def summary_with(**changes):
    value = json.loads(LINE_A[len("archive: "):])
    value.update(changes)
    return value


def test_a_clean_run_has_no_problem():
    summaries = [summary_with()]
    assert dr.run_problems(summaries, dr.total_requests(summaries), files=1) == []


def test_a_failed_game_is_a_problem_with_its_code():
    summaries = [summary_with(failed=[{"game_pk": 7, "code": "game_not_found"}])]
    problems = dr.run_problems(summaries, dr.total_requests(summaries), files=1)
    assert len(problems) == 1 and "game_not_found" in problems[0]


def test_a_run_stopped_by_a_ceiling_is_a_problem():
    summaries = [summary_with(stopped="ceiling_reached")]
    problems = dr.run_problems(summaries, dr.total_requests(summaries), files=1)
    assert len(problems) == 1 and "ceiling_reached" in problems[0]


def test_requests_past_a_ceiling_are_a_problem():
    summaries = [summary_with()]
    summaries[0]["requests"]["mlb"]["used"] = 320
    problems = dr.run_problems(summaries, dr.total_requests(summaries), files=1)
    assert len(problems) == 1 and "mlb" in problems[0]


def test_game_files_that_are_not_the_games_the_runs_built_or_skipped_are_a_problem():
    summaries = [summary_with(built=[1, 2], skipped=[3])]
    assert dr.run_problems(summaries, dr.total_requests(summaries), files=3) == []
    assert dr.run_problems(summaries, dr.total_requests(summaries), files=2) != []


# --- the notable distribution and V -------------------------------------------------------------------------------------

def doc_with(base, seasons, over=False, round_=None, ids=(1, 2)):
    """A copy of a built game (a World Series one) with the given seasons (None = unknown), series state and round."""

    document = deepcopy(base)
    document["series"]["over"] = over
    document["starter_facts"] = {
        side: {"id": pid, "prior_mlb_seasons": value} for side, value, pid in zip(("away", "home"), seasons, ids)
    }
    document["round"] = round_ or ag.ROUND_OF_TYPE["D"]
    return document


def test_the_table_counts_each_reason_and_the_veteran_rule_by_v(tmp_path):
    base = built(tmp_path)
    docs = [
        doc_with(base, (9, 6)),
        doc_with(base, (9, 2), over=True),
        doc_with(base, (9, None), round_=ag.ROUND_OF_TYPE["W"]),
        doc_with(base, (None, None)),
    ]
    table = dr.notable_table(docs, [1, 3, 6, 7])
    assert table["games"] == 4
    assert table["fixed"]["series_clincher"] == 1 and table["fixed"]["world_series"] == 1
    assert {v: table["by_v"][v]["veteran_duel"] for v in (1, 3, 6, 7)} == {1: 2, 3: 1, 6: 1, 7: 0}


def test_an_unknown_seasons_count_is_never_a_veteran_at_any_v(tmp_path):
    base = built(tmp_path)
    table = dr.notable_table([doc_with(base, (20, None))], [1, 2, 30])
    assert all(table["by_v"][v]["veteran_duel"] == 0 for v in (1, 2, 30))


def test_any_counts_a_game_once_however_many_reasons_it_has(tmp_path):
    base = built(tmp_path)
    both = doc_with(base, (9, 9), over=True, round_=ag.ROUND_OF_TYPE["W"])
    entry = dr.notable_table([both], [5])["by_v"][5]
    assert entry["any"] == 1 and entry["share"] == 1.0


def test_an_empty_set_has_no_share_not_a_division_by_zero():
    table = dr.notable_table([], [5])
    assert table["games"] == 0 and table["by_v"][5]["share"] is None


def test_prior_seasons_are_counted_per_distinct_starter(tmp_path):
    base = built(tmp_path)
    first = doc_with(base, (9, 3), ids=(1, 5))
    second = doc_with(base, (9, None), ids=(1, 2))  # starter 1 again, in a second game
    spread = dr.prior_seasons_distribution([first, second])
    assert spread["starters"] == 3 and spread["known"] == {3: 1, 9: 1} and spread["unknown"] == 1


# --- the report ---------------------------------------------------------------------------------------------------------

def make_dir(tmp_path, raw_answer=None):
    out, raw = tmp_path / "out", tmp_path / "raw"
    built(out)
    raw.mkdir()
    (raw / "849805.json").write_text(json.dumps(raw_answer if raw_answer is not None else box()), encoding="utf-8")
    summary = tmp_path / "summary.txt"
    summary.write_text(LINE_A + "\n", encoding="utf-8")
    return out, raw, summary


def argv(out, raw, summary, sweep="1,5"):
    return ["--out", str(out), "--raw-dir", str(raw), "--summary", str(summary), "--veteran-sweep", sweep]


def test_the_report_has_every_section_and_no_stop_when_all_is_read(tmp_path, capsys):
    out, raw, summary = make_dir(tmp_path)
    code = dr.main(argv(out, raw, summary))
    text = capsys.readouterr().out
    assert code == 0
    for heading in ("REQUESTS", "STARTERS", "NOTABLE", "PRIOR MLB SEASONS"):
        assert heading in text
    assert "world_series" in text and "STOP" not in text


def test_the_report_stops_with_a_nonzero_exit_on_a_parser_mismatch(tmp_path, capsys):
    broken = box()
    broken["teams"]["away"].pop("players")
    out, raw, summary = make_dir(tmp_path, raw_answer=broken)
    code = dr.main(argv(out, raw, summary, "5"))
    text = capsys.readouterr().out
    assert code == 3 and "STOP" in text and "parser_mismatch" in text


@pytest.mark.parametrize("changes", [
    {"failed": [{"game_pk": 7, "code": "request_failed"}]},
    {"stopped": "ceiling_reached"},
])
def test_a_run_that_did_not_succeed_never_ends_as_a_clean_report(tmp_path, capsys, changes):
    out, raw, _ = make_dir(tmp_path)
    summary = tmp_path / "bad.txt"
    summary.write_text("archive: " + json.dumps(summary_with(**changes)) + "\n", encoding="utf-8")
    code = dr.main(argv(out, raw, summary, "5"))
    text = capsys.readouterr().out
    assert code == 3 and "STOP" in text and "nothing stops the work" not in text


def test_the_clean_report_says_nothing_stops_the_work(tmp_path, capsys):
    out, raw, summary = make_dir(tmp_path)
    assert dr.main(argv(out, raw, summary, "5")) == 0
    assert "nothing stops the work" in capsys.readouterr().out


def test_the_report_is_refused_without_game_files(tmp_path):
    assert dr.main(argv(tmp_path / "empty", tmp_path, tmp_path / "x", "5")) == 2


@pytest.mark.parametrize("sweep", ["", "0", "31", "a", "3,3", "5,2"])
def test_a_bad_sweep_is_refused(sweep, tmp_path):
    out, raw, summary = make_dir(tmp_path)
    assert dr.main(argv(out, raw, summary, sweep)) == 2


def test_the_report_writes_nothing(tmp_path, capsys):
    out, raw, summary = make_dir(tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    dr.main(argv(out, raw, summary, "5"))
    assert sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")) == before
