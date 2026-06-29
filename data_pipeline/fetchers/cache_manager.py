"""
Read and write JSON snapshots to data_cache/raw/ and data_cache/processed/.
Used when ACTIVE_MODE is fetched_snapshot or live_partial.
"""

from __future__ import annotations

import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent.parent / "data_cache" / "raw"
PROCESSED_DIR = Path(__file__).parent.parent.parent / "data_cache" / "processed"


def save_raw(name: str, data: dict) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[CACHE] Saved raw snapshot: {path}")
    return path


def load_raw(name: str) -> dict | None:
    path = RAW_DIR / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def save_processed(name: str, data: dict) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[CACHE] Saved processed snapshot: {path}")
    return path


def load_processed(name: str) -> dict | None:
    path = PROCESSED_DIR / f"{name}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None
