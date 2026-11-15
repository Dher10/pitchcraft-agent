"""R4 pre-release audit reproductions. No production data or network writes."""

from copy import deepcopy
import json

import pytest

from data_pipeline import archive_build as ab, archive_games as ag, archive_history as ah
from data_pipeline import archive_finalize as fin
from data_pipeline.fetchers.mlb_schemas import SourceShapeError
from tests.test_archive_build import DAY, World, fake_pipeline
from tests.test_archive_games import good_file, PUBLISHED
from tests.test_archive_history import answer, ROWS


@pytest.mark.parametrize("change", [
    lambda d: d.update(date="2026-10-30"),
    lambda d: d["teams"]["away"].update(id=147, name="New York Yankees"),
    lambda d: d["origin"].update(as_of="2026-10-01"),
    lambda d: d["origin"].update(published_at="2026-10-25T12:00:00+00:00"),
    lambda d: d["origin"].update(built_at="2026-11-01T12:00:00+00:00"),
    lambda d: d["starter_facts"].update(away={"id": 999001, "prior_mlb_seasons": 8}),
    lambda d: d["starters_check"].update(away="started"),
    lambda d: d["payload"].update(matchups=[]),
])
def test_envelope_cannot_contradict_its_embedded_report(change):
    document = good_file()
    change(document)
    assert ag.validate_game_file(document)
    assert fin.game_problems(document)


def test_valid_published_values_remain_readable_control():
    assert ag.validate_game_file(good_file()) == []


def test_resume_rebuilds_a_rewritten_published_payload_from_the_recovered_blob(tmp_path):
    world = World()
    source = (deepcopy(PUBLISHED), "a" * 40, "b" * 64)
    ab.run([DAY], tmp_path, world.deps(published=[source]), ab.Ledger())
    path = tmp_path / "games/849805.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"]["matchups"][0]["report"]["headline"] = "rewritten"
    path.write_text(ag.compact_json(document), encoding="utf-8")
    result = ab.run([DAY], tmp_path, World().deps(published=[source]), ab.Ledger())
    assert result["built"] == [849805] and result["skipped"] == []
    assert json.loads(path.read_text(encoding="utf-8"))["payload"] == PUBLISHED


def test_resume_does_not_trust_an_empty_payload(tmp_path):
    document = good_file()
    document["payload"] = {}
    path = tmp_path / "849805.json"
    path.write_text(ag.compact_json(document), encoding="utf-8")
    assert not ab.existing_valid(path, 849805)


@pytest.mark.parametrize("relative", ["public/data/archive/history", "evals/live/history"])
def test_history_output_is_guarded_before_dependencies_or_requests(tmp_path, monkeypatch, capsys, relative):
    def unexpected(*args, **kwargs):
        pytest.fail("a forbidden output reached the dependencies")
    monkeypatch.setattr(ab, "real_dependencies", unexpected)
    root = ab.Path(ab.__file__).resolve().parents[1]
    assert ab.main(["--out", str(tmp_path), "--history-dir", str(root / relative),
                    "--start", DAY, "--end", DAY]) == 2
    assert "out_under_published_paths" in capsys.readouterr().err


def test_a_free_frame_cache_hit_is_allowed_at_the_http_ceiling():
    pipeline = fake_pipeline([])
    pipeline._statcast_pitcher_frame = lambda: "cached"
    ledger = ab.Ledger({"mlb": 0, "savant": 0})
    with ab.enforced(ledger, pipeline):
        assert pipeline._statcast_pitcher_frame() == "cached"
    assert ledger.used == {"mlb": 0, "savant": 0}


@pytest.mark.parametrize("damage", ["url", "sha256", "response"])
def test_history_cache_is_bound_to_the_requested_pitcher_and_season(tmp_path, damage):
    response = answer(ROWS)
    ah.HistoryStore(tmp_path, 2026, lambda url: response).response(11)
    path = tmp_path / "11_2026.json"
    record = json.loads(path.read_text())
    if damage == "url":
        record["url"] = ah.HISTORY_URL.format(pitcher_id=22, season=2025)
    else:
        record.pop(damage)
    path.write_text(json.dumps(record))
    with pytest.raises(SourceShapeError):
        ah.HistoryStore(tmp_path, 2026, lambda url: pytest.fail("bad cache fetched")).response(11)
