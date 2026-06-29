"""Assemble, validate, and write the PitchCraft v0.2.0 demo JSON."""

from __future__ import annotations

import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.demo_inputs import build_demo_payload
from data_pipeline.validators import ValidationError, validate_payload


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "public" / "data" / "pitchcraft-demo.json"


def main() -> int:
    payload = build_demo_payload()
    matchup_ids = [matchup["id"] for matchup in payload["matchups"]]

    print("PitchCraft demo JSON generator")
    print(f"Assembled matchups: {', '.join(matchup_ids)}")

    try:
        checks = validate_payload(payload)
    except ValidationError as exc:
        _print_checks(exc.checks)
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1

    _print_checks(checks)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote v{payload['metadata']['version']} demo JSON to {OUTPUT_PATH}")
    return 0


def _print_checks(checks: list[object]) -> None:
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        detail = f" - {check.detail}" if check.detail else ""
        print(f"[{status}] {check.description}{detail}")


if __name__ == "__main__":
    raise SystemExit(main())

