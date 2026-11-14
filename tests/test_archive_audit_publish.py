"""Publication and transport reproductions from the independent R4 data audit."""

import io
import json
import os
import subprocess
import urllib.error
import urllib.request
from email.message import Message
from urllib.response import addinfourl

import pytest

from data_pipeline import archive_build as ab, archive_finalize as fin, archive_games as ag
from data_pipeline.fetchers import live_pipeline as lp
from tests.test_archive_build import DAY, World as BuildWorld, two_games
from tests.test_archive_boxscore import box
from tests.test_archive_publish import (
    ARCHIVE, BUILT_AT, ROOT, V, built, clean_git_environment, folder, git,
    publish, real_payload, world,
)


@pytest.mark.parametrize("source", ["mlb", "savant"])
def test_redirects_cannot_send_a_second_uncharged_request(monkeypatch, source):
    sends = []
    def fake_http(handler, request):
        sends.append(request.full_url)
        headers = Message()
        redirect = not request.full_url.endswith("/redirected")
        if redirect:
            headers["Location"] = request.full_url + "/redirected"
        result = addinfourl(io.BytesIO(b"" if redirect else b'{"dates":[]}'), headers,
                            request.full_url, 302 if redirect else 200)
        result.msg = "Found" if redirect else "OK"
        return result
    monkeypatch.setattr(urllib.request.HTTPHandler, "http_open", fake_http)
    monkeypatch.setattr(urllib.request, "_opener", None)
    monkeypatch.setattr(lp, "_savant_run", {"requests": 0, "open_requests": 0})
    monkeypatch.setattr(lp, "_pitcher_statcast_run", {"requests": 0})
    monkeypatch.setattr(lp.time, "sleep", lambda seconds: None)
    original = urllib.request.urlopen
    ledger = ab.Ledger({"mlb": 1, "savant": 1})
    with ab.enforced(ledger, lp):
        with pytest.raises(urllib.error.HTTPError):
            (lp._get_json if source == "mlb" else lp._savant_get)("http://source.invalid/api/v1/schedule")
    assert len(sends) == 1 and ledger.used[source] == 1
    assert urllib.request.urlopen is original


def test_isolated_game_failure_does_not_block_valid_neighbors_cli(tmp_path, monkeypatch):
    deps = BuildWorld(days=two_games(), boxes={849805: box(), 849806: box()},
                      fail={849805: ag.ArchiveError(ag.GAME_NOT_FOUND)}).deps()
    monkeypatch.setattr(ab, "real_dependencies", lambda *args: deps)
    assert ab.main(["--out", str(tmp_path), "--start", DAY, "--end", DAY]) == 0
    assert (tmp_path / "games/849806.json").exists()
    assert not (tmp_path / "games/849805.json").exists()


def test_failed_rebuild_cannot_leave_an_invalid_old_candidate(tmp_path):
    ab.run([DAY], tmp_path, BuildWorld().deps(), ab.Ledger())
    path = tmp_path / "games/849805.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"] = {}
    path.write_text(ag.compact_json(document), encoding="utf-8")
    result = ab.run([DAY], tmp_path, BuildWorld(fail={849805: ValueError("private detail")}).deps(), ab.Ledger())
    assert result["failed"] and not path.exists()


@pytest.mark.parametrize("day", ["2025-10-01", "2026-07-04", "2027-10-01"])
def test_only_the_approved_postseason_window_can_start_requests(tmp_path, monkeypatch, capsys, day):
    def unexpected(*args):
        pytest.fail("unapproved season reached dependencies")
    monkeypatch.setattr(ab, "real_dependencies", unexpected)
    assert ab.main(["--out", str(tmp_path), "--start", day, "--end", day]) == 2
    assert "usage" in capsys.readouterr().err


def test_finalize_cannot_write_directly_under_protected_paths():
    with pytest.raises(Exception) as found:
        fin.build(ROOT / "public/data", V)
    assert str(found.value) == "out_under_published_paths"


def test_manifest_counts_are_recomputed_from_the_checked_index(folder):
    built(folder)
    path = folder / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["counts"] = {"games": 999, "notable": 999}
    path.write_text(ag.compact_json(manifest))
    assert "manifest:counts" in fin.check(folder)


def test_finalizing_unchanged_files_preserves_manifest_time(folder):
    built(folder)
    before = (folder / "manifest.json").read_bytes()
    assert fin.build(folder, V)["problems"] == []
    assert (folder / "manifest.json").read_bytes() == before


def test_workflow_style_recreated_manifest_does_not_make_a_new_commit(publish, world):
    assert publish.main(world.argv()) == 0
    head = world.head()
    path = world.candidate / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["built_at"] = "2026-11-14T14:00:00+00:00"
    path.write_text(ag.compact_json(manifest))
    assert publish.main(world.argv()) == 0
    assert world.head() == head


def test_an_already_published_payload_cannot_be_rewritten(publish, world, capsys):
    assert publish.main(world.argv()) == 0
    head = world.head()
    path = world.candidate / "games/849805.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    document["payload"]["matchups"][0]["report"]["headline"] = "rewritten"
    path.write_text(ag.compact_json(document), encoding="utf-8")
    assert fin.build(world.candidate, V, BUILT_AT)["problems"] == []
    assert publish.main(world.argv()) == 1
    assert "failed published_report_changed" in capsys.readouterr().out
    assert world.head() == head and git(world.work, "status", "--porcelain") == ""


def test_destination_directory_link_is_refused_before_any_write(publish, world, tmp_path):
    base = world.work / ARCHIVE
    base.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = base / "games"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True, check=True)
    else:
        link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(publish.pd.Failure) as found:
        publish._work_in(world.work, publish.candidate_files(world.candidate), "data: archive backfill 2026")
    assert found.value.code == "outside_allowlist"
    assert list(outside.iterdir()) == []
