"""D57: the ten-dev experiment inputs, recorded once and verified before calls.

Only guide/glossary and manifest metadata are read here; no packet contents,
held-out outputs, credentials or network. Packet loaders independently verify
each dev packet against the sealed manifest before the writer reads it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from agents import call_budget, fact_renderer, llm_report_writer as lw, nli_cache, writer_policy

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "evals/data/writer/experiment-freeze.json"


class FrozenInputsChanged(ValueError):
    """The frozen input record is absent, unreadable or differs from runtime inputs."""


def text_sha256(path):
    """LF-normalized text identity, matching the guide/glossary locks across checkouts."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def current_inputs(dataset, case_ids):
    dataset = Path(dataset)
    manifest = json.loads((dataset / "packets_manifest.json").read_text(encoding="utf-8"))
    entries = {e["id"]: e for e in manifest["cases"]}
    if len(case_ids) != 10 or len(set(case_ids)) != 10 or any(entries[c]["split"] != "dev" for c in case_ids):
        raise FrozenInputsChanged("dev cases differ")
    glossary = json.loads((dataset / "glossary.json").read_text(encoding="utf-8"))
    prompt = {"version": lw.PROMPT_VERSION, "lexicon": lw.LEX, "schema": lw.SCHEMA,
              "guide": lw.guide_text(), "max_output_tokens": lw.MAX_OUTPUT_TOKENS}
    return {
        "guide": {"version": "0.4", "sha256": lw.guide_sha256()},
        "glossary": {"version": glossary["version"], "sha256": text_sha256(dataset / "glossary.json")},
        "prompt": {"version": lw.PROMPT_VERSION, "sha256": lw.digest(prompt)},
        "packets_manifest_sha256": text_sha256(dataset / "packets_manifest.json"),
        "dev_cases": [{key: entries[c][key] for key in ("id", "packet_sha256", "findings_sha256")} for c in case_ids],
        "writer": {"models": list(writer_policy.WRITER_MODELS), "thinking": "LOW", "temperature": "default",
                   "pacing_seconds": writer_policy.PACING_SECONDS, "timeout": writer_policy.WRITER_TIMEOUT,
                   "backoff_seconds": writer_policy.BACKOFF_SECONDS},
        "experiment_cap": call_budget.EXPERIMENT_CAP,
        "nli_mode": "score_only", "nli_identity": nli_cache.identity(),
        "renderer_identity": fact_renderer.renderer_identity(),
        "evaluators": {name: text_sha256(ROOT / name) for name in
                       ("agents/writer_checks.py", "agents/writer_input.py", "agents/llm_report_writer.py",
                        "agents/nli_admission.py", "agents/writer_policy.py", "evals/run_b1.py")},
    }


def verify_frozen(record_path, dataset, case_ids):
    try:
        record = json.loads(Path(record_path).read_text(encoding="utf-8"))
        if type(record["run_cap"]) is not int or record["run_cap"] != 30 or record["inputs"] != current_inputs(dataset, case_ids):
            raise FrozenInputsChanged("frozen inputs changed")
        return record
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise FrozenInputsChanged("frozen inputs changed") from error
