"""Versioned lexical checks, not an evidence or semantic admission gate."""
from __future__ import annotations

import html
import re
import unicodedata
from urllib.parse import unquote

POLICY_VERSION = "p2-sec-1"
SENTENCE_CAP = 300
FACT_CAP = 2400


class ModelRejected(ValueError):
    """Safe existing code only; never put untrusted data in an exception."""
    def __init__(self):
        super().__init__("malformed_response")


_MARKUP = re.compile(r"[<>`*_#\[\]{}\\|]|~~|^\s*(?:[-+]\s|[0-9]+\.\s)|%[0-9a-f]{2}|&(?:#\w+|\w+);|(?:[a-z][a-z0-9+.-]*://|www\.|(?:data|javascript|mailto):\S)|[\w.+-]+@[\w.-]+|(?:[a-z0-9-]+\.)+[a-z]{2,63}\b", re.I)
_INVISIBLE = frozenset("\u034f\u115f\u1160\u17b4\u17b5\u2800\u3164\uffa0")
_POLICY = re.compile(
    r"\b(?:idiot|stupid|loser|trash|garbage|injury|injuries|injured|surgery|diagnosed|"
    r"wife|girlfriend|divorce|married|pregnant|bet|bets|betting|odds|gamble|gambling|"
    r"wager|moneyline|parlay|prediction|predict|guarantee)\b|\bwill\s+(?:win|lose)\b|"
    r"\bb[\W_]+e[\W_]+t(?:[\W_]+t[\W_]+i[\W_]+n[\W_]+g)?\b", re.I
)
_CONFUSABLES = str.maketrans({
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p", "\u0441": "c",
    "\u0445": "x", "\u0456": "i", "\u0443": "y", "\u03bf": "o", "\u03b5": "e",
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
})


def bounded_text(value: object, cap: int) -> str:
    if type(value) is not str or not 1 <= len(value) <= cap:
        raise ModelRejected()
    if any(unicodedata.category(c).startswith("C") or c in _INVISIBLE or
           0x180B <= ord(c) <= 0x180F or 0xFE00 <= ord(c) <= 0xFE0F or 0xE0100 <= ord(c) <= 0xE01EF or
           (unicodedata.category(c).startswith("Z") and c != " ") for c in value):
        raise ModelRejected()
    # Check decoded/normalized views without changing the evidence-bearing value.
    if _MARKUP.search(value):
        raise ModelRejected()
    checked = value
    for _ in range(4):
        checked = html.unescape(unquote(checked))
    if _MARKUP.search(unicodedata.normalize("NFKC", checked)):
        raise ModelRejected()
    return value


def validate_sentence(value: object) -> str:
    text = bounded_text(value, SENTENCE_CAP)
    normalized = unicodedata.normalize("NFKD", text.casefold()).translate(_CONFUSABLES)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    if _POLICY.search(normalized):
        raise ModelRejected()
    return text
