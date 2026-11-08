"""Safe internal attempt serialization; not wired to public/live logs yet."""
from __future__ import annotations

import json
import re

from data_pipeline.contract_checks import RUN_ERROR_CODES

FIELDS = frozenset(("provider", "event", "code", "attempt", "input_tokens", "output_tokens", "request_digest"))


def encode_record(**fields: object) -> str:
    def reject():
        raise ValueError("malformed_response") from None

    if set(fields) != FIELDS:
        reject()
    for key, choices in (("provider", ("gemini", "groq", "rules", "nli")),
                         ("event", ("accepted", "rejected", "not_evaluated"))):
        if type(fields[key]) is not str or fields[key] not in choices:
            reject()
    code = fields["code"]
    if code is not None and (type(code) is not str or code not in RUN_ERROR_CODES):
        reject()
    if fields["event"] == "accepted" and code is not None:
        reject()
    if type(fields["attempt"]) is not int or fields["attempt"] not in (1, 2):
        reject()
    for key in ("input_tokens", "output_tokens"):
        value = fields[key]
        if value is not None and (type(value) is not int or not 0 <= value <= 200_000):
            reject()
    digest = fields["request_digest"]
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        reject()
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), allow_nan=False)
