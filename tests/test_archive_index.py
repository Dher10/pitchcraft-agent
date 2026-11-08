"""R4-D5: the index, the notable-duel tags and the manifest (D66; docs/plans/R4.md 4.4 and 4.6; owner's answer to OQ5).

Pure code over game files built in memory. Every reason has a positive case and controls that fail if its condition is
weakened; an unknown input never makes a tag.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from data_pipeline import archive_games as ag
from data_pipeline import archive_index as ix
from data_pipeline import labels
from tests.test_archive_games import PUBLISHED, SOURCE, records, schedule_game

ABOVE = labels.SWING_MISS_ABOVE
BELOW = "Below-average swing-and-miss ability"
V = 5


def payload_with(away=ABOVE, home=ABOVE, away_limited=False, home_limited=False):
    payload = deepcopy(PUBLISHED)
    for side, label, limited in (("away", away, away_limited), ("home", home, home_limited)):
        starter = payload["matchups"][0]["starters"][f"{side}_starter"]
        starter["pitching_profile"]["swing_miss_label"] = label
        starter["sample"]["limited"]["strikeout"] = limited
    return payload


def doc(pk=849805, day="2026-10-23", game_type="W", over=False, payload=None, facts=(8, 9), season=2026, **kwargs):
    after = "MIL wins 4-1" if over else "MIL leads 1-0"
    (record,) = records(schedule_game(pk=pk, day=day, game_type=game_type, series_status={"isOver": over, "result": after}, **kwargs))
    document = ag.build_game_file(
        record, payload or payload_with(), ag.published_origin(PUBLISHED, record, SOURCE),
        starter_facts={side: None if n is False else {"id": 607259 if side == "away" else 694819, "prior_mlb_seasons": n}
                       for side, n in zip(("away", "home"), facts)},
    )
    document["origin"]["as_of"] = "2026-10-01"
    document["season"] = season
    return document


def reasons(document, v=V):
    return ix.notable_reasons(document, v)


# --- V ------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("bad", [None, 0, -1, 31, 5.0, "5", True])
def test_without_an_approved_veteran_threshold_nothing_is_computed(bad):
    with pytest.raises(ix.ArchiveIndexError) as caught:
        ix.notable_reasons(doc(), bad)
    assert caught.value.code == "veteran_min_not_set"
    with pytest.raises(ix.ArchiveIndexError):
        ix.build_index([doc()], 2026, bad)


# --- the four reasons ---------------------------------------------------------------------------------------------------

def test_series_clincher_needs_the_series_to_be_over():
    assert "series_clincher" in reasons(doc(over=True))
    assert "series_clincher" not in reasons(doc(over=False))
    document = doc(over=True)
    document["series"]["over"] = None  # unknown
    document["series"]["after"] = None
    assert "series_clincher" not in reasons(document)


def test_world_series_is_every_world_series_game_played_and_no_other_round():
    assert "world_series" in reasons(doc(game_type="W"))
    for other in ("D", "L", "F"):
        assert "world_series" not in reasons(doc(game_type=other))


def test_strikeout_duel_needs_both_starters_above_average_with_a_sample_that_is_not_limited():
    assert "strikeout_duel" in reasons(doc())
    assert "strikeout_duel" not in reasons(doc(payload=payload_with(away=BELOW)))
    assert "strikeout_duel" not in reasons(doc(payload=payload_with(home=BELOW)))
    assert "strikeout_duel" not in reasons(doc(payload=payload_with(away_limited=True)))
    assert "strikeout_duel" not in reasons(doc(payload=payload_with(home_limited=True)))


@pytest.mark.parametrize("label", [None, "", "above-average swing-and-miss ability", "Above-average swing-and-miss ability "])
def test_a_missing_or_loose_label_is_not_a_strong_strikeout_label(label):
    assert "strikeout_duel" not in reasons(doc(payload=payload_with(away=label)))


def test_an_unknown_limited_flag_is_not_not_limited():
    payload = payload_with()
    payload["matchups"][0]["starters"]["away_starter"]["sample"]["limited"]["strikeout"] = None
    assert "strikeout_duel" not in reasons(doc(payload=payload))
    payload = payload_with()
    del payload["matchups"][0]["starters"]["home_starter"]["sample"]["limited"]
    assert "strikeout_duel" not in reasons(doc(payload=payload))
    payload = payload_with()
    del payload["matchups"][0]["starters"]["home_starter"]["pitching_profile"]
    assert "strikeout_duel" not in reasons(doc(payload=payload))


def test_veteran_duel_needs_both_starters_to_have_v_earlier_seasons_inclusive():
    assert "veteran_duel" in reasons(doc(facts=(5, 5)))
    assert "veteran_duel" not in reasons(doc(facts=(4, 9)))
    assert "veteran_duel" not in reasons(doc(facts=(9, 4)))
    assert "veteran_duel" in reasons(doc(facts=(4, 9)), 4)  # V moves the line, nothing else does


def test_an_unknown_season_count_or_missing_fact_is_not_a_veteran():
    assert "veteran_duel" not in reasons(doc(facts=(None, 9)))
    assert "veteran_duel" not in reasons(doc(facts=(9, None)))
    assert "veteran_duel" not in reasons(doc(facts=(False, 9)))  # no fact at all for the away starter


def test_the_reasons_come_in_the_fixed_order_whatever_the_order_of_the_rules():
    everything = reasons(doc(over=True))
    assert everything == ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"] == list(ix.REASONS)
    assert reasons(doc(game_type="D", payload=payload_with(away=BELOW), facts=(1, 1))) == []


# --- the row and the index -----------------------------------------------------------------------------------------------

def test_a_row_carries_what_the_list_shows_and_no_report_text():
    row = ix.index_row(doc(over=True), V)
    assert row["game_pk"] == 849805 and row["round"] == "World Series" and row["status"] == "final"
    assert row["away"] == {"id": 139, "name": "Tampa Bay Rays", "abbreviation": PUBLISHED["matchups"][0]["teams"]["away"]["abbreviation"]}
    assert row["result"] == {"away_runs": 3, "home_runs": 5, "winner": "home"}
    assert row["starters"] == {"away": "Nick Martinez", "home": "Jacob Misiorowski"}
    assert row["report"] == {"origin": "published_live", "as_of": "2026-10-01", "starters_check": {"away": "unknown", "home": "unknown"}}
    assert row["notable"] == ["series_clincher", "strikeout_duel", "veteran_duel", "world_series"]
    assert len(str(row)) < 900  # about 0.5 KB a row: a 2,700-game season is about 1.3 MB


def test_a_row_is_built_only_from_a_valid_game_file():
    document = doc()
    document["result"]["winner"] = "away"
    with pytest.raises(ix.ArchiveIndexError) as caught:
        ix.index_row(document, V)
    assert caught.value.code == "invalid_game_file"


def three():
    return [doc(pk=849801, day="2026-10-21", game_type="D"), doc(pk=849803, day="2026-10-23"), doc(pk=849802, day="2026-10-23", over=True)]


def test_the_index_lists_valid_games_of_the_season_newest_first_with_a_stable_tie_break():
    index = ix.build_index(three(), 2026, V)
    assert [r["game_pk"] for r in index["games"]] == [849803, 849802, 849801]  # same day: the larger id first
    assert index["count"] == 3 and index["veteran_min"] == V and index["season"] == 2026 and index["archive_version"] == "1.0.0"
    assert index["notable_count"] == sum(1 for r in index["games"] if r["notable"])
    assert ix.validate_index(index) == []


def test_invalid_foreign_and_duplicate_files_are_not_listed():
    bad = doc(pk=849810)
    bad["result"]["winner"] = "away"
    other_season = doc(pk=849811, season=2025)
    again = doc(pk=849803, day="2026-10-24")
    index = ix.build_index(three() + [bad, other_season, again], 2026, V)
    assert [r["game_pk"] for r in index["games"]] == [849803, 849802, 849801]
    assert index["games"][0]["date"] == "2026-10-23"  # the first file of a game is the one listed


def test_an_empty_season_is_a_valid_empty_index():
    index = ix.build_index([], 2026, V)
    assert index["count"] == 0 and index["games"] == [] and ix.validate_index(index) == []


def test_the_index_is_exactly_what_the_game_files_give_and_changes_when_they_or_v_change():
    documents = three()
    index = ix.build_index(documents, 2026, V)
    assert ix.index_matches_documents(index, documents)
    changed = deepcopy(index)
    changed["games"][0]["result"]["away_runs"] = 99
    assert not ix.index_matches_documents(changed, documents)
    assert not ix.index_matches_documents(index, documents[:2])
    assert not ix.index_matches_documents(index, documents + [doc(pk=849899)])
    veterans = [doc(pk=849801, day="2026-10-21", facts=(6, 6))]
    assert ix.index_matches_documents(ix.build_index(veterans, 2026, 5), veterans)
    assert not ix.index_matches_documents(ix.build_index(veterans, 2026, 7), [doc(pk=849801, day="2026-10-21", facts=(6, 6))] + [doc(pk=849802)])
    assert not ix.index_matches_documents({}, documents) and not ix.index_matches_documents(None, documents)


def test_v_is_recorded_in_the_index_and_decides_the_tag():
    veterans = [doc(pk=849801, day="2026-10-21", game_type="D", facts=(6, 6))]
    assert "veteran_duel" in ix.build_index(veterans, 2026, 5)["games"][0]["notable"]
    assert "veteran_duel" not in ix.build_index(veterans, 2026, 7)["games"][0]["notable"]
    assert ix.build_index(veterans, 2026, 7)["veteran_min"] == 7


def test_notable_order_is_more_reasons_then_later_date_then_larger_id_and_games_with_none_are_left_out():
    rows = ix.build_index(
        [doc(pk=849801, day="2026-10-20", game_type="D", payload=payload_with(away=BELOW), facts=(1, 1)),  # none
         doc(pk=849802, day="2026-10-21", game_type="D"),                                                  # strikeout + veteran
         doc(pk=849803, day="2026-10-22", game_type="D", over=True, payload=payload_with(away=BELOW)),      # clincher + veteran
         doc(pk=849804, day="2026-10-22", game_type="W", over=True),                                       # all four
         doc(pk=849805, day="2026-10-22", game_type="D", over=True, payload=payload_with(away=BELOW))],    # same as 849803
        2026, V,
    )["games"]
    assert [r["game_pk"] for r in ix.notable_order(rows)] == [849804, 849805, 849803, 849802]


@pytest.mark.parametrize(
    "mutate",
    [lambda i: i.pop("count"), lambda i: i.__setitem__("archive_version", "0.9.0"), lambda i: i.__setitem__("count", 99),
     lambda i: i.__setitem__("notable_count", 0), lambda i: i.__setitem__("games", None),
     lambda i: i["games"].append(deepcopy(i["games"][0])), lambda i: i["games"].reverse(),
     lambda i: i["games"][0].__setitem__("notable", ["world_series", "series_clincher"]),
     lambda i: i["games"][0].__setitem__("notable", ["made_up"]), lambda i: i["games"][0].__setitem__("game_pk", "849803")],
)
def test_a_malformed_index_is_refused(mutate):
    index = ix.build_index(three(), 2026, V)
    mutate(index)
    assert ix.validate_index(index) != []
    assert ix.validate_index(None) == ["document"]


# --- the manifest ------------------------------------------------------------------------------------------------------------

def files_of(documents, index):
    files = {f"games/{d['game_pk']}.json": ag.compact_json(d) for d in documents}
    files[ix.INDEX_FILE.format(season=2026)] = ag.compact_json(index)
    return files


def test_the_manifest_lists_exactly_the_files_present_with_their_digests():
    documents = three()
    index = ix.build_index(documents, 2026, V)
    files = files_of(documents, index)
    manifest = ix.build_manifest(files, index, "2026-11-08T12:00:00+00:00")
    assert set(manifest["files"]) == set(files) and manifest["counts"] == {"games": 3, "notable": index["notable_count"]}
    assert manifest["seasons"] == [2026] and ix.verify_manifest(manifest, files) == []


def test_a_changed_missing_extra_or_oddly_named_file_is_found():
    documents = three()
    index = ix.build_index(documents, 2026, V)
    files = files_of(documents, index)
    manifest = ix.build_manifest(files, index, "2026-11-08T12:00:00+00:00")
    changed = dict(files, **{"games/849803.json": files["games/849803.json"] + " "})
    assert "digest" in ix.verify_manifest(manifest, changed)
    missing = {k: v for k, v in files.items() if k != "games/849801.json"}
    assert "file_set" in ix.verify_manifest(manifest, missing)
    assert "file_set" in ix.verify_manifest(manifest, dict(files, **{"games/849999.json": "{}"}))
    renamed = deepcopy(manifest)
    renamed["files"]["../x.json"] = renamed["files"].pop("games/849801.json")
    assert "name" in ix.verify_manifest(renamed, dict(files, **{"../x.json": files["games/849801.json"]}))
    assert ix.verify_manifest({}, files) == ["document"] and ix.verify_manifest(None, files) == ["document"]
    wrong = deepcopy(manifest)
    wrong["archive_version"] = "0.9.0"
    assert "archive_version" in ix.verify_manifest(wrong, files)


def _manifest_and_files():
    documents = three()
    index = ix.build_index(documents, 2026, V)
    files = files_of(documents, index)
    return ix.build_manifest(files, index, "2026-11-08T12:00:00+00:00"), files


@pytest.mark.parametrize(
    ("mutate", "label"),
    [
        (lambda m: m.__setitem__("seasons", 2026), "seasons"),
        (lambda m: m.__setitem__("seasons", []), "seasons"),
        (lambda m: m.__setitem__("seasons", ["../x"]), "seasons"),
        (lambda m: m.__setitem__("seasons", [True]), "seasons"),
        (lambda m: m.__setitem__("seasons", [20]), "seasons"),
        (lambda m: m.__setitem__("counts", {"games": 99, "notable": 99, "x": 1}), "counts"),
        (lambda m: m.__setitem__("counts", {"games": -1, "notable": 0}), "counts"),
        (lambda m: m.__setitem__("counts", None), "counts"),
        (lambda m: m.__setitem__("built_at", "yesterday"), "built_at"),
        (lambda m: m.__setitem__("built_at", "2026-11-08T12:00:00"), "built_at"),
        (lambda m: m.__setitem__("built_at", None), "built_at"),
        (lambda m: m.__setitem__("files", None), "files"),
        (lambda m: m["files"].__setitem__("games/849801.json", "xyz"), "digest"),
        (lambda m: m["files"].__setitem__("games/849801.json", 5), "digest"),
        (lambda m: m["files"].pop("index-2026.json"), "index_missing"),
        (lambda m: m["files"].__setitem__(5, "ab" * 32), "name"),
    ],
)
def test_a_malformed_manifest_gets_a_closed_label_never_an_exception_and_never_a_pass(mutate, label):
    manifest, files = _manifest_and_files()
    mutate(manifest)
    assert label in ix.verify_manifest(manifest, files)


@pytest.mark.parametrize("bad", [None, [], 5, {"index-2026.json": 5}, {"index-2026.json": None}, {5: "x"}])
def test_files_that_are_not_a_mapping_of_texts_are_a_closed_label_not_an_exception(bad):
    manifest, _ = _manifest_and_files()
    assert ix.verify_manifest(manifest, bad) == ["files"]


def test_a_manifest_whose_season_has_no_index_file_present_is_flagged():
    manifest, files = _manifest_and_files()
    without = {k: v for k, v in files.items() if k != "index-2026.json"}
    assert "index_missing" in ix.verify_manifest(manifest, without)


def test_a_manifest_needs_the_index_among_the_files():
    documents = three()
    index = ix.build_index(documents, 2026, V)
    with pytest.raises(ix.ArchiveIndexError) as caught:
        ix.build_manifest({f"games/{d['game_pk']}.json": "{}" for d in documents}, index, "2026-11-08T12:00:00+00:00")
    assert caught.value.code == "index_missing"


def test_the_module_makes_no_request_reads_no_file_and_imports_nothing_from_evals():
    from pathlib import Path

    source = Path(ix.__file__).read_text(encoding="utf-8")
    for forbidden in ("requests", "urllib", "socket", "open(", "read_text", "write_text", "import evals", "from evals", ".local",
                      "public/data", "evals/live"):
        assert forbidden not in source, forbidden
