"""The payloads the contract tests run over (PLAN.md P0.15-D3). Not a test module.

Four real payloads built by the generator (demo, demo after a failed live run, a live game with
everything the pipeline can give, a live game of two debuts), the eighteen golden scenarios of the
agents, and the file the app serves. Each is a payload after a trip through JSON: what the file holds.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from agents import critic, data_scout, matchup_analyst, postgame_grader, report_writer
from data_pipeline import generate_demo_json as gdj
from data_pipeline.claims import attach_claims
from data_pipeline.generator_texts import generator_catalog
from tests.golden_scenarios import scenarios
from tests.live_helpers import CUTOFF, GAME_DAY, RUN_AT, hand_snapshot, use_snapshot

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVED = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"
GOLDEN = Path(__file__).parent / "fixtures" / "agents_en_golden.json"

KINDS = ("demo", "fallback", "live_complete", "live_debuts", "live_errors")
GOLDEN_NAMES = list(json.loads(GOLDEN.read_text(encoding="utf-8")))


def published(payload: dict[str, Any]) -> dict[str, Any]:
    """What the file holds: the payload after a trip through JSON."""

    return json.loads(json.dumps(payload))


def build(monkeypatch, kind: str) -> dict[str, Any]:
    """The payload the generator builds for `kind` (one of KINDS)."""

    if kind == "demo":
        monkeypatch.setattr(gdj, "_live", None)
        monkeypatch.setattr(gdj, "_live_status", {"mode": "demo_cached", "reason": {"source": "pipeline", "code": "no_live_run"}, "live_run": None})
    elif kind == "fallback":
        monkeypatch.setattr(gdj, "_live", None)
        status = {"mode": "demo_fallback", "reason": {"source": "mlb_schedule", "code": "request_failed"}, "live_run": None}
        monkeypatch.setattr(gdj, "_live_status", status)
    else:
        use_snapshot(monkeypatch, hand_snapshot(complete=kind != "live_debuts"))
        if kind == "live_errors":  # a live run that recorded a source error, as the run record does
            status = dict(gdj._live_status)
            status["live_run"] = {
                "status": "ok",
                "run_at": RUN_AT,
                "target_date": GAME_DAY,
                "as_of": CUTOFF,
                "games_scheduled": 1,
                "games_live": 1,
                "errors": [{"source": "statcast_pitcher", "code": "malformed_rows"}],
                "warnings": [{"source": "statcast_pitcher", "code": "unmapped_pitch_type"}],
            }
            monkeypatch.setattr(gdj, "_live_status", status)
    return gdj.build_payload()


def corpus(monkeypatch):
    """(name, payload) of every payload the contract tests run over: the generator's, the golden ones and the served file."""

    for kind in KINDS:
        yield kind, published(build(monkeypatch, kind))
    for name in GOLDEN_NAMES:
        yield f"golden:{name}", published(golden_payload(monkeypatch, name))
    yield "served", served()


def golden_payload(monkeypatch, name: str) -> dict[str, Any]:
    """One golden scenario run through the five agents and wrapped as a payload with its claims."""

    return payload_of(scenarios(monkeypatch)[name])


def payload_of(matchup: dict[str, Any]) -> dict[str, Any]:
    """A matchup run through the five agents and wrapped as a payload with its claims."""

    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, matchup)
    review = critic.run(report, matchup)
    wrapped = deepcopy(matchup)
    wrapped.update(report=report, critic_review=review, data_confidence=packet["data_confidence"], postgame=None)
    if matchup["status"] == "final":
        wrapped["postgame"] = postgame_grader.run(matchup)
    if wrapped["data_confidence"]["level"] == "fetched_snapshot":
        wrapped["data_confidence"] = dict(
            wrapped["data_confidence"],
            notes=[generator_catalog()("generator.confidence.live_note", date=GAME_DAY, matchup_id=wrapped["id"])],
        )
    metadata = {"data_mode": "demo_cached"}
    if wrapped["data_confidence"]["level"] == "fetched_snapshot":
        metadata["data_fetched_at"] = RUN_AT  # the live note says the day of the fetch (D39); the wrapper is not a published file
    payload = {"metadata": metadata, "matchups": [wrapped]}
    attach_claims(payload)
    return payload


def served() -> dict[str, Any]:
    return json.loads(SERVED.read_text(encoding="utf-8"))
