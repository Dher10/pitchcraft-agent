"""Offline MLB season-date reference. Refresh once per season; never infer a missing season's end."""

from datetime import date
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from data_pipeline.fetchers import mlb_schemas

REFERENCE_DIR = Path(__file__).with_name("reference")


@lru_cache(maxsize=1)
def _calendar() -> dict[int, date]:
    result: dict[int, date] = {}
    for path in sorted(REFERENCE_DIR.glob("mlb_seasons_[0-9][0-9][0-9][0-9].json")):
        raw = path.read_bytes()
        source = json.loads(path.with_suffix(".source.json").read_bytes())
        if sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("season reference checksum mismatch")
        payload = json.loads(raw)
        mlb_schemas.validate(mlb_schemas.SEASONS, payload, "saved seasons response")
        for entry in payload["seasons"]:
            season = entry["seasonId"]
            if not isinstance(season, str) or len(season) != 4 or not season.isascii() or not season.isdigit():
                raise ValueError("invalid season in reference")
            year = int(season)
            first = date.fromisoformat(entry["regularSeasonStartDate"])
            last = date.fromisoformat(entry["regularSeasonEndDate"])
            if first.year != year or last.year != year or first > last or year in result:
                raise ValueError("inconsistent season reference")
            result[year] = last
    return result


def regular_season_end(year: int) -> date | None:
    return _calendar().get(year)
