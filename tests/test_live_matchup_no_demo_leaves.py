"""A live matchup carries no leaf that comes from the demo (QA4-03 and its root, PLAN.md P0.15-A).

Run 4 found the game time zone of the Oracle Park demo under a live Yankee Stadium game. The cause was
structural: the live matchup was a deep copy of `matchup_001` patched field by field, so every field
nobody remembered to overwrite was inherited. These tests close the class, not the field:

1. Every leaf of every live matchup is compared with the demo's leaf at the same path (against every
   demo matchup); a leaf that is equal and does not come from the snapshot fails.
2. The demo is poisoned: every leaf of the template matchup, of the template archive row and the
   `generated_at` of the metadata is replaced by a value that cannot occur anywhere else. Any trace of
   it in the live output was inherited, whatever its value would have been.
3. The live builder does not import the demo or copy a matchup.

The matchup is built four ways: from the real pipeline (without and with a venue time zone in the
schedule), from a complete hand-made snapshot and from the smallest one the pipeline can write.
Booleans cannot be told apart this way; the only ones in a matchup are set by the builder.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_pipeline import demo_inputs
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import live_pipeline as lp
from tests import test_as_of_end_to_end as e2e
from tests.live_helpers import hand_snapshot, leaves, schedule_with_zone, use_snapshot
from tests.test_as_of_end_to_end import leaky_sources  # noqa: F401  (fixture)

REPO_ROOT = Path(__file__).resolve().parents[1]

# Leaves that are equal to the demo's on purpose: values the live builder itself assigns. Each one needs
# a reason; `test_every_allowed_constant_is_still_equal_to_the_demo` fails when one stops being equal.
ALLOWED_SAME = {
    ("id",): "slot identifier: the featured live game takes the featured slot, matchup_001",
    ("status",): "the builder marks every live game 'upcoming' (pregame)",
    ("is_featured",): "the builder marks the first live game as the featured one",
}
VARIANTS = ("real_pipeline", "real_pipeline_with_zone", "complete_snapshot", "minimal_snapshot")


@pytest.fixture(params=VARIANTS)
def live(request, monkeypatch) -> SimpleNamespace:
    """The generator input of one variant is installed; returns the snapshot behind it."""

    if request.param.startswith("real_pipeline"):
        request.getfixturevalue("leaky_sources")
        zone = "America/New_York" if request.param.endswith("zone") else None
        monkeypatch.setattr(e2e, "SCHEDULE", schedule_with_zone(e2e.SCHEDULE, zone))
        # The hands the demo's starters do not have (away R, home L), so a hand cannot match by chance.
        monkeypatch.setattr(
            lp,
            "statcast_pitcher",
            lambda start, end, player_id: e2e.STATCAST.assign(p_throws="L" if player_id == 11 else "R"),
        )
        record, snapshot = lp.run_live_pipeline(e2e.GAME_DAY, as_of=e2e.CUTOFF)
        assert record["status"] == "ok" and record["errors"] == [], record
    else:
        snapshot = hand_snapshot(complete=request.param == "complete_snapshot")
    use_snapshot(monkeypatch, snapshot)
    return SimpleNamespace(name=request.param, snapshot=snapshot)


def live_matchups(payload: dict) -> list[dict]:
    return [m for m in payload["matchups"] if m["id"] == "matchup_001" or m["id"].startswith("matchup_live_")]


def where(path: tuple) -> str:
    return ".".join(str(step) for step in path)


# --- 1. equal to the demo at the same path ----------------------------------------------------------


def test_no_live_leaf_equals_the_demo_value_at_the_same_path(live):
    payload = gdj.build_payload()

    demo = {m["id"]: dict(leaves(m)) for m in demo_inputs.build_demo_payload()["matchups"]}
    in_snapshot = {
        value
        for _, value in leaves(live.snapshot)
        if isinstance(value, (str, int, float)) and not isinstance(value, bool)
    }
    inherited = []
    for matchup in live_matchups(payload):
        for path, value in leaves(matchup):
            if value is None or isinstance(value, bool) or path in ALLOWED_SAME or value in in_snapshot:
                continue
            for demo_id, demo_leaves in demo.items():
                if path in demo_leaves and demo_leaves[path] == value:
                    inherited.append(f"{matchup['id']}.{where(path)} = {value!r} (as in {demo_id})")
    assert inherited == [], f"[{live.name}] values equal to the demo's, not from the snapshot:\n" + "\n".join(inherited)


def test_every_allowed_constant_is_still_equal_to_the_demo(monkeypatch):
    use_snapshot(monkeypatch, hand_snapshot(complete=True))
    payload = gdj.build_payload()

    primary = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    demo = dict(leaves(next(m for m in demo_inputs.build_demo_payload()["matchups"] if m["id"] == "matchup_001")))
    live_leaves = dict(leaves(primary))
    stale = [where(path) for path in ALLOWED_SAME if live_leaves.get(path) != demo.get(path)]
    assert stale == [], f"allowed constants that are no longer equal to the demo's (remove them): {stale}"


# --- 2. poisoned demo ---------------------------------------------------------------------------------

POISON_TEXT = "«DEMO»"
POISON_NUMBER = 90_000_000


def poisoned(value, path: tuple = (), counter: list[int] | None = None):
    """A copy where every string and number is replaced by a value that exists nowhere else."""

    counter = counter if counter is not None else [0]
    if isinstance(value, dict):
        return {key: poisoned(child, (*path, key), counter) for key, child in value.items()}
    if isinstance(value, list):
        return [poisoned(child, (*path, index), counter) for index, child in enumerate(value)]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str):
        return f"{POISON_TEXT}{where(path)}"
    counter[0] += 1
    return POISON_NUMBER + counter[0]


def is_poison(value) -> bool:
    if isinstance(value, str):
        return POISON_TEXT in value
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= POISON_NUMBER


def test_nothing_of_a_poisoned_demo_reaches_a_live_matchup(live, monkeypatch):
    matchups = deepcopy(demo_inputs.MATCHUPS)
    template = next(i for i, m in enumerate(matchups) if m["id"] == "matchup_001")
    keep_id = matchups[template]["id"]
    matchups[template] = poisoned(matchups[template])
    matchups[template]["id"] = keep_id  # the slot the live game takes is found by this id
    archive = deepcopy(demo_inputs.ARCHIVE)
    archive[0] = poisoned(archive[0])
    metadata = {**demo_inputs.METADATA, "generated_at": f"{POISON_TEXT}generated_at"}
    monkeypatch.setattr(demo_inputs, "MATCHUPS", matchups)
    monkeypatch.setattr(demo_inputs, "ARCHIVE", archive)
    monkeypatch.setattr(demo_inputs, "METADATA", metadata)

    payload = demo_inputs.build_demo_payload()
    gdj._apply_live_snapshot(payload)

    found = []
    for matchup in live_matchups(payload):
        found += [f"{matchup['id']}.{where(path)}" for path, value in leaves(matchup) if is_poison(value)]
    found += [f"archive[0].{where(path)}" for path, value in leaves(payload["archive"][0]) if is_poison(value)]
    found += [f"metadata.{where(path)}" for path, value in leaves(payload["metadata"]) if is_poison(value)]
    assert found == [], f"[{live.name}] inherited from the demo:\n" + "\n".join(found)


# --- 3. the live builder cannot reach the demo ----------------------------------------------------------


def test_the_live_matchup_builder_neither_imports_the_demo_nor_copies_a_matchup():
    source = (REPO_ROOT / "data_pipeline" / "live_matchup.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name.split(".")[-1]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    } | {node.module.split(".")[-1] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert "demo_inputs" not in imported
    assert "deepcopy" not in imported and "copy" not in imported
    assert "deepcopy" not in source


def test_applying_a_live_snapshot_copies_no_demo_matchup():
    assert "deepcopy" not in inspect.getsource(gdj._apply_live_snapshot)
