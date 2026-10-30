"""P2.4 gate 4a: the collector. Pools from the schedule alone, lazy per-pitcher lookups in seeded order, the seal.

No network: the schedule adapter and the series fetcher are replaced, the history store is a counting fake. Worlds are
tiny (`PER_STRATUM` is lowered) so every rule can be seen to decide one outcome.
"""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from data_pipeline import series as series_module
from evals import build_dataset as bd
from evals import collect as co
from evals import collect_sources as cs
from evals import request_ledger as rl

COLLECTION = date(2026, 10, 30)


def game(pk, day, away, home, kind="R", n=None, final=True):
    return cs.ListedGame(pk, day, kind, n, final, ((away, f"P{away}"), (home, f"P{home}")))


def hist(pid, rows, prior=5):
    """rows: (date, innings, batters faced, started)."""

    return cs.History(pid, tuple(cs.Appearance(d, i, b, s) for d, i, b, s in rows), prior)


class FakeStore:
    def __init__(self, histories, fail_on=None):
        self.histories, self.lookups, self.fetched, self.fail_on = histories, 0, [], fail_on

    def known(self, pid):
        return pid in self.fetched

    def get(self, pid):
        if pid not in self.fetched:
            if self.fail_on == pid:
                raise rl.CeilingReached("160 mlb requests already made in this collection")
            self.fetched.append(pid)
            self.lookups += 1
        return self.histories[pid]


def fill(games, histories):
    """The histories of every starter of `games` that the test did not define: no appearance at all."""

    for g in games:
        for pitcher in g.starters:
            if pitcher is not None:
                histories.setdefault(pitcher[0], hist(pitcher[0], []))
    return histories


def starts(pid, n, ip="5.0", bf=22, first=date(2026, 4, 1)):
    """n regular starts a week apart from `first`."""

    rows = []
    for k in range(n):
        d = date.fromordinal(first.toordinal() + 7 * k).isoformat()
        rows.append((d, bd.innings_from_ip(ip), bf, True))
    return rows


@pytest.fixture(autouse=True)
def small_world(monkeypatch):
    monkeypatch.setattr(bd, "PER_STRATUM", 2)


def plan(**caps):
    return co.Plan(date(2026, 3, 25), date(2026, 9, 27), COLLECTION, None, {"postseason": 40, "opener": 40, "limited": 40, "veteran": 40} | caps)


def series_ok(pk, as_of):
    return {"game_number": 1, "games_played": 0, "result": None, "is_over": False}


# --- the schedule: dates, finality, the postseason end -------------------------------------------------------


def test_the_schedule_is_asked_by_calendar_month_then_for_the_postseason_up_to_the_day_before_collection(monkeypatch):
    asked = []

    def fake(start, end, types=cs.GAME_TYPES):
        asked.append((start, end))
        return []

    monkeypatch.setattr(cs, "fetch_schedule", fake)
    co.load_games(plan())

    assert asked[0] == (date(2026, 3, 25), date(2026, 3, 31)) and asked[6] == (date(2026, 9, 1), date(2026, 9, 27))
    assert len(asked) == 8 and asked[7] == (date(2026, 9, 28), date(2026, 10, 29))  # the day before the collection date


def test_an_explicit_postseason_end_caps_the_last_request(monkeypatch):
    asked = []
    monkeypatch.setattr(cs, "fetch_schedule", lambda s, e, types=cs.GAME_TYPES: asked.append((s, e)) or [])
    co.load_games(co.Plan(date(2026, 3, 25), date(2026, 9, 27), COLLECTION, date(2026, 10, 20), {}))

    assert asked[-1] == (date(2026, 9, 28), date(2026, 10, 20))


def test_only_final_games_before_the_collection_date_are_kept_and_the_postseason_end_is_the_last_final_one(monkeypatch):
    games = [
        game(1, "2026-10-28", 1, 2, "D", 1),
        game(2, "2026-10-29", 3, 4, "L", 1, final=False),  # not final
        game(3, "2026-10-30", 5, 6, "L", 1),  # the collection date itself: not before it
        game(4, "2026-09-10", 7, 8),
    ]
    monkeypatch.setattr(cs, "fetch_schedule", lambda s, e, types=cs.GAME_TYPES: list(games))

    loaded = co.load_games(plan())

    assert sorted({g.game_pk for g in loaded.games}) == [1, 4]
    assert loaded.postseason_end == date(2026, 10, 28)


def test_a_postseason_with_no_final_game_has_no_end_and_no_pool(monkeypatch):
    monkeypatch.setattr(cs, "fetch_schedule", lambda s, e, types=cs.GAME_TYPES: [game(1, "2026-09-10", 7, 8)])

    loaded = co.load_games(plan())

    assert loaded.postseason_end is None and co.pools(loaded.games)["postseason"] == []


# --- pools: objective filters from the schedule alone ---------------------------------------------------------


def season(pitcher, n, kind="R"):
    """n final games where `pitcher` is the home starter, a week apart, against a different opponent each time."""

    return [game(1000 * pitcher + k, date.fromordinal(date(2026, 4, 1).toordinal() + 7 * k).isoformat(), 9000 + 100 * pitcher + k, pitcher, kind) for k in range(n)]


def test_start_indexes_count_a_pitchers_listed_final_regular_starts_up_to_and_including_the_game():
    games = season(5, 4)

    index, totals = co.start_indexes(games)

    assert [index[(g.game_pk, 5)] for g in games] == [1, 2, 3, 4] and totals[5] == 4


def test_the_pools_follow_the_frozen_start_index_rules():
    games = season(5, 12)  # starter 5: indexes 1..12; each opponent is new and has a single start (index 1)
    pools = co.pools(games)

    veteran = {g.game_pk for g in pools["veteran"]}
    limited = {g.game_pk for g in pools["limited"]}
    opener = {g.game_pk for g in pools["opener"]}
    assert veteran == set() and limited == {5001, 5002, 5003, 5004, 5005}  # veteran needs BOTH starters at index >= 10
    assert opener == {g.game_pk for g in games[1:]}  # index >= 2 for one of the starters


def test_a_game_without_two_listed_starters_is_in_no_pool():
    games = season(5, 4)
    games[1] = cs.ListedGame(games[1].game_pk, games[1].official_date, "R", None, True, ((9101, "x"), None))

    pools = co.pools(games)

    assert all(games[1].game_pk not in {g.game_pk for g in pool} for pool in pools.values())


def test_the_postseason_pool_is_the_postseason_games_in_seeded_rank_order():
    games = [game(10 + k, "2026-10-1%d" % k, 100 + k, 200 + k, "D", 1) for k in range(5)] + season(5, 3)

    pool = co.pools(games)["postseason"]

    assert {g.game_pk for g in pool} == {10, 11, 12, 13, 14}
    assert [bd.rank(g.game_pk) for g in pool] == sorted(bd.rank(g.game_pk) for g in pool)


def test_the_opener_pool_tries_the_pitchers_with_the_fewest_listed_starts_first():
    rare = season(7, 3)  # three starts in all
    often = season(8, 12)
    pool = co.pools(rare + often)["opener"]

    assert pool[0].game_pk in {g.game_pk for g in rare}  # a game of the pitcher with 3 starts comes before any of 12


# --- lazy selection --------------------------------------------------------------------------------------------


def test_an_opener_is_found_by_its_previous_innings_and_costs_one_lookup_per_new_pitcher():
    games = season(7, 3)
    histories = fill(games, {7: hist(7, starts(7, 3, ip="1.0", bf=6))})

    result = co.select_cases(games, FakeStore(histories), plan(), series_ok)

    opener = result.selection.cases["opener"]
    assert [c.pitcher_ids[1] for c in opener] == [7] * len(opener) and len(opener) == 1  # one pitcher cannot start two cases
    assert opener[0].traits["opener"]["evidence"]["average_innings"] == 1.0
    assert result.lookups["opener"] >= 2 and result.selection.short["opener"] == 1


def test_a_pitcher_fetched_for_one_stratum_costs_nothing_in_the_next():
    games = season(7, 3)
    store = FakeStore(fill(games, {7: hist(7, starts(7, 3, ip="1.0", bf=6))}))

    result = co.select_cases(games, store, plan(), series_ok)

    assert sum(result.lookups.values()) == store.lookups  # each fetched pitcher is charged once, to the first stratum that needed him
    assert len(store.fetched) == len(set(store.fetched))


def test_a_pitcher_with_no_previous_start_is_not_an_opener():
    games = season(7, 3)  # pitcher 7 has a 2nd and 3rd listed start, so the games are in the opener pool, but his log is empty
    store = FakeStore(fill(games, {}))

    result = co.select_cases(games, store, plan(), series_ok)

    assert result.selection.cases["opener"] == () and 7 in store.fetched  # examined, and rejected: unknown is not zero


def pair_world(a, b, n=12):
    """n games between the same two starters, a week apart from April 1: for each of them the k-th game is the k-th listed start."""

    return [game(100 * a + k, date.fromordinal(date(2026, 4, 1).toordinal() + 7 * k).isoformat(), a, b) for k in range(n)]


def test_a_veteran_needs_every_threshold_and_three_prior_seasons():
    games = pair_world(31, 32) + pair_world(33, 34)
    big = starts(0, 20, bf=40, first=date(2026, 3, 1))  # 200 batters faced before the first April start: every threshold cleared
    histories = {31: hist(31, big, 5), 32: hist(32, big, 5), 33: hist(33, big, 5), 34: hist(34, big, 2)}  # 34: two prior seasons only

    result = co.select_cases(games, FakeStore(histories), plan(), series_ok)

    veterans = result.selection.cases["veteran"]
    assert len(veterans) == 1 and set(veterans[0].pitcher_ids) == {31, 32}
    assert veterans[0].game_pk >= 3100 + 9  # the 10th listed start or later: inside the frozen veteran pool
    assert all(34 not in c.pitcher_ids for c in veterans)


def test_an_unknown_prior_season_count_never_makes_a_veteran():
    games = pair_world(31, 32)
    big = starts(0, 20, bf=40, first=date(2026, 3, 1))
    histories = {31: hist(31, big, None), 32: hist(32, big, 5)}

    assert co.select_cases(games, FakeStore(histories), plan(), series_ok).selection.cases["veteran"] == ()


def test_the_screening_cap_of_a_stratum_stops_its_lookups_and_reports_it_short():
    games = season(7, 6) + season(8, 6)
    store = FakeStore(fill(games, {7: hist(7, starts(7, 6, ip="1.0", bf=6)), 8: hist(8, starts(8, 6, ip="1.0", bf=6))}))

    result = co.select_cases(games, store, plan(opener=2), series_ok)

    assert result.lookups["opener"] <= 2 and result.stopped["opener"] == "screen_cap"


def test_reaching_the_ledger_ceiling_stops_the_whole_collection_and_keeps_what_was_found():
    games = season(7, 4) + [game(50, "2026-10-01", 61, 62, "D", 1)]
    histories = fill(games, {})
    result = co.select_cases(games, FakeStore(histories, fail_on=7), plan(), series_ok)

    assert result.halted == "ceiling_reached"
    assert [c.game_pk for c in result.selection.cases["postseason"]] == [50]  # found before the stop, kept


def test_a_postseason_case_carries_its_standing_and_a_leaking_one_is_skipped():
    games = [game(10, "2026-10-01", 61, 62, "D", 1), game(11, "2026-10-02", 63, 64, "D", 2)]
    histories = {pid: hist(pid, []) for pid in (61, 62, 63, 64)}

    def standing(pk, as_of):
        if pk == 10:
            return {"game_number": 1, "games_played": 0, "result": None, "is_over": False}
        return {"game_number": 2, "games_played": 1, "result": "CLE wins 4-1", "is_over": True}  # a finished series: a leak

    result = co.select_cases(games, FakeStore(histories), plan(), standing)

    cases = result.selection.cases["postseason"]
    assert [c.game_pk for c in cases] == [10] and result.series[10] == {"game_number": 1, "games_played": 0, "result": None, "is_over": False}
    assert result.skipped["postseason"] == {11: "series_leak"}


def test_the_as_of_of_every_case_is_the_day_before_the_game():
    games = [game(10, "2026-10-01", 61, 62, "D", 1)]
    result = co.select_cases(games, FakeStore({61: hist(61, []), 62: hist(62, [])}), plan(), series_ok)

    assert result.selection.cases["postseason"][0].as_of == "2026-09-30"


def test_no_game_or_starter_is_shared_between_strata():
    games = season(7, 8) + season(8, 8) + [game(50, "2026-10-01", 7, 8, "D", 1)]
    histories = fill(games, {7: hist(7, starts(7, 8, ip="1.0", bf=6)), 8: hist(8, starts(8, 8, ip="1.0", bf=6))})

    result = co.select_cases(games, FakeStore(histories), plan(), series_ok)

    all_cases = [c for cases in result.selection.cases.values() for c in cases]
    pitchers = [p for c in all_cases for p in c.pitcher_ids]
    assert len({c.game_pk for c in all_cases}) == len(all_cases) and len(set(pitchers)) == len(pitchers)


# --- the record, its hash and the seal --------------------------------------------------------------------------


def finished():
    games = [game(10, "2026-10-01", 61, 62, "D", 1), game(11, "2026-10-02", 63, 64, "D", 1)]
    histories = {pid: hist(pid, []) for pid in (61, 62, 63, 64)}
    return co.select_cases(games, FakeStore(histories), plan(), series_ok)


def test_the_selection_file_is_deterministic_and_each_case_has_a_hash(tmp_path):
    first, second = finished(), finished()
    co.write_selection(tmp_path / "a", first, plan())
    co.write_selection(tmp_path / "b", second, plan())

    a = (tmp_path / "a" / "selection.json").read_bytes()
    assert a == (tmp_path / "b" / "selection.json").read_bytes()
    record = json.loads(a)
    assert {c["case_id"] for c in record["cases"]} == {"postseason-10", "postseason-11"}
    assert all(len(c["sha256"]) == 64 for c in record["cases"]) and record["collection_date"] == "2026-10-30"


def test_a_changed_fact_changes_the_case_hash():
    result = finished()
    case = result.selection.cases["postseason"][0]
    record = co.case_record(case, result)
    changed = {**record, "series": {**record["series"], "games_played": 1}}

    assert co.case_hash(record) != co.case_hash(changed)


def test_sealing_a_short_selection_is_refused_unless_allowed_and_a_complete_one_writes_split_and_lock(tmp_path):
    short = finished()  # postseason full (2), the other strata empty
    co.write_selection(tmp_path, short, plan())
    with pytest.raises(co.NotComplete):
        co.seal(tmp_path)

    lock = co.seal(tmp_path, allow_short=True)

    bd.verify_split_lock(tmp_path)  # control: the lock matches
    split = json.loads((tmp_path / "split.json").read_text(encoding="utf-8"))
    selected = {c["case_id"]: c["sha256"] for c in json.loads((tmp_path / "selection.json").read_text(encoding="utf-8"))["cases"]}
    assert {c["id"]: c["sha256"] for c in split["cases"]} == selected and (tmp_path / "split.lock").read_text().strip() == lock
    with pytest.raises(bd.SplitChanged):
        co.seal(tmp_path, allow_short=True)  # sealed once, never rewritten


# --- the command line ---------------------------------------------------------------------------------------------


def test_the_collection_date_is_the_actual_run_date_unless_given():
    assert co.resolve_collection_date("today", today=date(2026, 11, 2)) == date(2026, 11, 2)
    assert co.resolve_collection_date("2026-10-30", today=date(2026, 11, 2)) == date(2026, 10, 30)
    with pytest.raises(ValueError):
        co.resolve_collection_date("tomorrow", today=date(2026, 11, 2))


def test_the_postseason_end_is_auto_unless_a_date_is_given():
    assert co.parse_args(["select", "--out", "x"]).postseason_end == "auto"
    assert co.parse_args(["select", "--out", "x", "--postseason-end", "2026-10-20"]).postseason_end == "2026-10-20"


@pytest.mark.parametrize("out", ["public/data/x", "evals/live", "./public/data", "evals/live/sub"])
def test_the_output_may_never_be_the_published_data(out):
    with pytest.raises(co.ForbiddenPath):
        co.check_output_path(Path(out))


def test_the_default_output_and_cache_paths_are_allowed():
    co.check_output_path(Path("evals/data/dataset"))
    co.check_output_path(Path("data_cache/raw/pitcher_history"))


def test_the_veteran_pool_starts_exactly_at_the_tenth_listed_start_of_both_starters():
    games = pair_world(31, 32, n=10)  # the 9th game is each starter's 9th start, the 10th game their 10th

    assert [g.game_pk for g in co.pools(games)["veteran"]] == [3109]


# --- the real store and the real ledger (a fake that is more capable than the real object hides bugs) ---------------


@pytest.fixture
def real_wire(monkeypatch, tmp_path):
    """The real HistoryStore, ledger and series fetcher; only the network call is replaced."""

    from data_pipeline.fetchers import live_pipeline as lp

    asked = []
    answers = {}

    def get_json(url, timeout=8):
        asked.append(url)
        for fragment, answer in answers.items():
            if fragment in url:
                return answer
        raise OSError("no canned answer")

    monkeypatch.setattr(lp, "_get_json", get_json)
    ledger = rl.RequestLedger(tmp_path / "ledger.jsonl")
    store = cs.HistoryStore(tmp_path / "h", 2026)
    with rl.counted_mlb(ledger):
        yield asked, answers, ledger, store


def log_answer(rows):
    return {
        "stats": [
            {"type": {"displayName": "gameLog"}, "splits": [{"date": d, "stat": {"inningsPitched": "1.0", "battersFaced": 6, "gamesStarted": 1, "gamesPlayed": 1}} for d in rows]},
            {"type": {"displayName": "yearByYear"}, "splits": [{"season": "2024", "stat": {"gamesPlayed": 30}}]},
        ]
    }


def test_the_real_store_runs_a_selection_and_charges_each_pitcher_once(real_wire):
    asked, answers, ledger, store = real_wire
    games = season(7, 3)
    answers["/people/"] = log_answer(["2026-04-01", "2026-04-08", "2026-04-15"])

    result = co.select_cases(games, store, plan(), series_ok, lambda: ledger.refused)

    assert result.lookups["opener"] == len(asked) == ledger.count("mlb") and store.known(7)
    assert len(asked) == len(set(asked))  # no pitcher was asked for twice
    assert result.selection.cases["opener"]


def test_a_pitcher_in_the_disk_cache_is_known_and_costs_no_request(real_wire):
    asked, answers, ledger, store = real_wire
    answers["/people/"] = log_answer(["2026-04-01"])
    store.get(7)
    reopened = cs.HistoryStore(store.directory, 2026)

    assert reopened.known(7) and not reopened.known(8)
    reopened.get(7)
    assert len(asked) == 1


def test_a_series_request_refused_at_the_ceiling_halts_the_collection_instead_of_looking_like_a_leak(real_wire, monkeypatch):
    asked, answers, ledger, store = real_wire
    from data_pipeline.fetchers import live_pipeline as lp

    games = [game(10, "2026-10-01", 61, 62, "D", 1)]
    answers["/people/"] = log_answer([])
    monkeypatch.setitem(rl.CEILINGS, "mlb", 2)  # the two pitcher lookups use it up: the series request is refused

    result = co.select_cases(games, store, plan(), lp.fetch_series_status, lambda: ledger.refused)

    assert result.halted == "ceiling_reached" and result.skipped["postseason"] == {}
    assert result.selection.cases["postseason"] == ()


def test_a_malformed_history_halts_with_a_closed_code_and_keeps_what_was_found(real_wire):
    asked, answers, ledger, store = real_wire
    games = [game(10, "2026-10-01", 61, 62, "D", 1)] + season(7, 3)
    answers["/people/61/"] = log_answer([])
    answers["/people/62/"] = log_answer([])
    answers["/people/"] = {"stats": []}  # no gameLog block: malformed

    result = co.select_cases(games, store, plan(), series_ok, lambda: ledger.refused)

    assert result.halted == "source_shape" and [c.game_pk for c in result.selection.cases["postseason"]] == [10]


def test_a_stratum_over_its_cap_still_takes_later_games_whose_pitchers_are_known():
    games = season(7, 3) + season(8, 2)  # pitcher 8 has fewer listed starts, so his game is tried first and is over the cap
    store = FakeStore(fill(games, {7: hist(7, starts(7, 3, ip="1.0", bf=6)), 8: hist(8, starts(8, 2, ip="1.0", bf=6))}))
    store.fetched += [7, 9701, 9702]  # pitcher 7 and his opponents are already known: no lookup left to pay

    result = co.select_cases(games, store, plan(opener=0), series_ok)

    assert any(c.pitcher_ids[1] == 7 for c in result.selection.cases["opener"])  # costs 0 lookups, so the cap does not stop it
    assert result.stopped["opener"] == "screen_cap"  # but the stratum still reports that the cap stopped other games
