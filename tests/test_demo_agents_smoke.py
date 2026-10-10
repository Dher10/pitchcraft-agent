"""Smoke test: the five agents run in memory over the demo data.

Does not import live_pipeline or generate_demo_json (both touch the cache and
public/data), and checks that nothing under public/data or data_cache changes.
"""

from __future__ import annotations

from pathlib import Path

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from data_pipeline import demo_inputs

REPO_ROOT = Path(__file__).resolve().parents[1]
WATCHED_DIRS = ("public/data", "data_cache")


def _snapshot() -> dict[str, tuple[int, int]]:
    state = {}
    for rel in WATCHED_DIRS:
        base = REPO_ROOT / rel
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file():
                stat = path.stat()
                state[str(path)] = (stat.st_size, stat.st_mtime_ns)
    return state


def test_five_agents_run_on_demo_data_without_writing_files():
    before = _snapshot()
    matchups = demo_inputs.build_demo_payload()["matchups"]
    assert matchups

    graded = 0
    for matchup in matchups:
        packet = data_scout.run(matchup)
        assert packet["availability"]
        assert packet["data_confidence"]

        findings = matchup_analyst.run(packet)
        assert findings["matchup_headline"]

        report = report_writer.run(findings, matchup)
        assert report["sections"]

        review = critic.run(report, matchup)
        assert review["checks"]

        if matchup["status"] == "final":
            postgame = postgame_grader.run(matchup)
            assert postgame["starter_lines"]
            graded += 1

    assert graded >= 1
    assert _snapshot() == before
