"""The writer guide's rules W1-W17 as code (docs/writer-guide.md, version 0.2).

`check_report(candidate, doc, rules_length)` returns closed failure codes ("W10.cause"); an empty list means every check
passed. These are lexical and structural checks on a candidate: they do not replace the NLI, the judge or the final integrity
gate, and a pass admits nothing to publication. Free text is never echoed into a code.

A candidate is {"headline": S, "summary_lines": [S, S, S],
"sections": {summary, away_vs_home, home_vs_away, arsenal, watch (3), confidence: [S, ...]}} where
S = {"text": str, "evidence": [{"path": str, "value": str}]}; paths index the writer input (agents/writer_input.py).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import unicodedata

from agents import writer_input as wi
from agents.security_policy import ModelRejected, validate_sentence

wi = wi  # re-exported for tests that read the evidence index through this module
SECTION_KEYS = ("summary", "away_vs_home", "home_vs_away", "arsenal", "watch", "confidence")
MAX_PER_SECTION = 6
MAX_EVIDENCE = 6
LENGTH_TOLERANCE = Decimal("0.20")

LEX = json.loads((Path(__file__).with_name("writer_lexicon.json")).read_text(encoding="utf-8"))["en"]  # English wording lives in data (D6)
_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?|\.\d+)")
_CAPITALIZED = re.compile(r"(?<![\w'’])[^\W\d_][\w'’-]*")  # filtered to an uppercase first letter (any script)


def _word(words) -> "re.Pattern":
    """Whole words only: "Four-seam" is not "four" and "below-average" is a label, not a comparison."""

    return re.compile(r"(?<![\w-])(?:" + "|".join(words) + r")(?![\w-])", re.I)


_W, _P = LEX["words"], LEX["patterns"]
_ARITHMETIC = _word(_W["arithmetic"])
_GREATER, _LESSER = _W["greater"], _W["lesser"]
_COMPARATIVE = _word((*_GREATER, *_LESSER, *_W["neutral"]))
_GREATER_RE, _LESSER_RE = _word(_GREATER), _word(_LESSER)
_OUTCOME, _INTENSITY = _word(_W["outcome"]), _word(_W["intensity"])
_WATCH_OUTCOME, _NUMBER_WORDS = _word(_W["watch_outcome"]), _word(_W["number_words"])
_PREDICTION, _TOPIC, _CAUSE, _TIME = (re.compile(_P[k], re.I) for k in ("prediction", "topic", "cause", "time"))
_INTERNAL, _UNKNOWN_TERMS = re.compile(_P["internal"], re.I), re.compile(_P["unknown_terms"], re.I)
_QUESTION_OPENER, _ZERO_CLAIM = re.compile(_P["question_opener"], re.I), re.compile(_P["zero_claim"], re.I)
_MOVEMENT_BAD, _MOVEMENT_FORM = re.compile(_P["movement_bad"], re.I), re.compile(_P["movement_form"], re.I)
_SERIES_STANDING, _LIMITED_WORDS = re.compile(_P["series_standing"], re.I), re.compile(_P["limited_words"], re.I)
_WATCH_FORM = re.compile(_P["watch_form"])
_OPENERS, _EXEMPT_CAPITALS = frozenset(LEX["openers"]), frozenset(LEX["exempt_capitals"])
_LABEL_TERMS = tuple(tuple(x) for x in LEX["label_terms"])
_TERM_PATTERNS = {k: re.compile(v) for k, v in LEX["term_patterns"].items()}
_IS = LEX["is_joiner"]
_BAD_CODE = "W0.error"


def definition_forms(term: str, definition: str) -> set[str]:
    """The sentences that count as the glossary definition of `term`: the definition as written, or `<term> is <definition>`."""

    first = definition[0].lower() + definition[1:] if definition[:2].isupper() is False else definition
    return {_nfc(definition), _nfc(f"{term}{_IS}{first}"), _nfc(f"{term[0].upper()}{term[1:]}{_IS}{first}")}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _capitals(text: str) -> list[str]:
    return [t for t in _CAPITALIZED.findall(text) if t[0].isupper()]


def _numbers(text: str) -> list[Decimal]:
    return [Decimal(token) for token in _NUMBER.findall(text)]


def _all_sentences(candidate: dict) -> list[dict]:
    return [candidate["headline"], *candidate["summary_lines"], *(s for key in SECTION_KEYS for s in candidate["sections"][key])]


def report_length(candidate: dict) -> int:
    return sum(len(_nfc(s["text"])) for s in _all_sentences(candidate))


def rules_length(report: dict) -> int:
    """The length, counted the same way, of a rules writer report."""

    total = len(report["headline"]) + sum(len(x) for x in report["short_summary"])
    for section in report["sections"]:
        total += len(section.get("body") or "") + sum(len(b) for b in section.get("bullets", []))
    return total


def _structure_ok(candidate: object) -> bool:
    try:
        sections = candidate["sections"]
        if set(candidate) != {"headline", "summary_lines", "sections"} or set(sections) != set(SECTION_KEYS):
            return False
        if len(candidate["summary_lines"]) != 3 or len(sections["watch"]) != 3:
            return False
        for key in SECTION_KEYS:
            if not 1 <= len(sections[key]) <= MAX_PER_SECTION:
                return False
        for s in _all_sentences(candidate):
            if set(s) != {"text", "evidence"} or type(s["text"]) is not str or not isinstance(s["evidence"], list) or len(s["evidence"]) > MAX_EVIDENCE:
                return False
            if any(type(e) is not dict or set(e) != {"path", "value"} or type(e["path"]) is not str or type(e["value"]) is not str for e in s["evidence"]):
                return False
        return True
    except (KeyError, TypeError):
        return False


def _value_text(value: object) -> str:
    return "null" if value is None else "true" if value is True else "false" if value is False else str(value)


def _same_value(cited: str, actual: object) -> bool:
    if actual is None:
        return cited == "null"
    if isinstance(actual, bool):
        return cited == _value_text(actual)
    if isinstance(actual, (int, float)):
        try:
            return Decimal(cited) == Decimal(str(actual))
        except InvalidOperation:
            return False
    return _nfc(cited) == _nfc(str(actual))


def _terminal(path: str) -> str:
    last = path.split(".")[-1]
    return re.sub(r"^(?:away|home)_starter_", "", last)


def _allowed_capitals(doc: dict) -> set[str]:
    allowed = set(_EXEMPT_CAPITALS)
    for value in wi.evidence_index(doc).values():
        if isinstance(value, str):
            allowed.update(_nfc(t).removesuffix("'s").removesuffix("’s") for t in _capitals(_nfc(value)))
    return allowed


def check_report(candidate: dict, doc: dict, rules_len: int) -> list[str]:
    """Closed failure codes of `candidate` against the guide; [] means all checks passed."""

    if not _structure_ok(candidate):
        return ["W17.structure"]
    failures: list[str] = []

    def fail(code: str) -> None:
        if code not in failures:
            failures.append(code)

    index = wi.evidence_index(doc)
    allowed = _allowed_capitals(doc)
    glossary = {entry["term"]: definition_forms(entry["term"], entry["definition"]) for entry in doc["glossary"]}
    sentences = _all_sentences(candidate)
    watch_ids = {id(s) for s in candidate["sections"]["watch"]}
    ordered_texts = [_nfc(s["text"]) for s in sentences]
    scope_labels = {v for p, v in index.items() if p.endswith("scope.label") or p.endswith(".label")}

    for sentence in sentences:
        try:
            _check_sentence(sentence, doc, index, allowed, glossary, watch_ids, fail)
        except Exception:  # a malformed citation or value must reject the candidate, never crash the run
            fail(_BAD_CODE)
    return _finish(candidate, doc, sentences, ordered_texts, glossary, scope_labels, rules_len, failures, fail)


def _check_sentence(sentence, doc, index, allowed, glossary, watch_ids, fail) -> None:
    text = _nfc(sentence["text"])
    try:
        validate_sentence(text)
    except ModelRejected:
        fail("W0.sentence")
        return
    cited = sentence["evidence"]
    if not cited:
        fail("W1.no_evidence")
    paths_ok = True
    for e in cited:
        if e["path"] not in index:
            fail("W1.evidence_path")
            paths_ok = False
        elif not _same_value(e["value"], index[e["path"]]):
            fail("W1.evidence_value")
            paths_ok = False
    paths = [e["path"] for e in cited]
    is_definition = bool(paths) and all(p.startswith("glossary.") for p in paths) and all(text in glossary.get(p[len("glossary."):], ()) for p in paths)
    if is_definition:
        return
    if not paths_ok:
        return
    cited_text = " ".join(_value_text(index[p]) for p in paths if p in index)
    cited_numbers = set(_numbers(cited_text))
    if any(n not in cited_numbers for n in _numbers(text)):
        fail("W1.number")
    if _NUMBER_WORDS.search(text):
        fail("W1.number")
    if _ZERO_CLAIM.search(text) and not any(isinstance(index[p], (int, float)) and not isinstance(index[p], bool) and index[p] == 0 for p in paths):
        fail("W1.number")
    for token in _capitals(text):
        name = token.removesuffix("'s").removesuffix("’s")
        # Any capitalized word must be in the packet; a sentence opener may also be a plain English opener.
        if name in allowed or (text.startswith(token) and name in _OPENERS):
            continue
        fail("W1.entity")
    if _QUESTION_OPENER.match(text) or "？" in text:
        fail("W15.question")
    if _ARITHMETIC.search(text):
        fail("W2.arithmetic")
    if _COMPARATIVE.search(text) and not _comparison_ok(text, cited, doc, index):
        fail("W2.comparison")
    if _PREDICTION.search(text) or _OUTCOME.search(text):
        fail("W3.prediction")
    if _TOPIC.search(text):
        fail("W4.topic")
    label_words = {w.lower() for p in paths if p in index and ("_label" in p or p.startswith("findings.")) for w in re.findall(r"[A-Za-z-]+", _value_text(index[p]))}
    if any(w.lower() not in label_words for w in _INTENSITY.findall(text)):
        fail("W5.intensity")
    for term, key in _LABEL_TERMS:
        if term in text.lower() and not _LIMITED_WORDS.search(text) and not any(p.endswith(key) for p in paths):
            fail("W5.label")
    if any(index.get(p) is None and p in index for p in paths) and not _LIMITED_WORDS.search(text):
        fail("W7.missing")
    if _CAUSE.search(text):
        fail("W10.cause")
    if _UNKNOWN_TERMS.search(text):
        fail("W11.unknown_term")
    if _TIME.search(text):
        fail("W12.time")
    if "?" in text:
        fail("W15.question")
    if _INTERNAL.search(text):
        fail("W16.internal")
    if any(p.startswith("pitch_movement.") for p in paths):
        _movement(text, paths, index, fail)
    elif _MOVEMENT_BAD.search(text):
        fail("W8.form")
    if id(sentence) in watch_ids:
        if not _WATCH_FORM.match(text):
            fail("W15.form")
        if _WATCH_OUTCOME.search(text):
            fail("W15.outcome")



def _finish(candidate, doc, sentences, ordered_texts, glossary, scope_labels, rules_len, failures, fail):
    _terms(ordered_texts, sentences, glossary, fail)
    _limits(candidate, sentences, doc, fail)
    _series(doc, ordered_texts, fail)
    _coverage(doc, ordered_texts, scope_labels, fail)
    low, high = rules_len * (1 - LENGTH_TOLERANCE), rules_len * (1 + LENGTH_TOLERANCE)
    if not Decimal(low) <= Decimal(report_length(candidate)) <= Decimal(high):
        fail("W17.length")
    return failures


def _comparison_ok(text: str, cited: list[dict], doc: dict, index: dict) -> bool:
    numeric = []
    for e in cited:
        value = index.get(e["path"])
        if isinstance(value, (int, float)) and not isinstance(value, bool) and e["path"] not in [x["path"] for x in numeric]:
            numeric.append(e)
    if len(numeric) != 2:
        return False
    first, second = numeric[0]["path"], numeric[1]["path"]
    values = [Decimal(str(index[first])).copy_abs(), Decimal(str(index[second])).copy_abs()]
    in_text = [n for n in _numbers(text) if n in values]
    if sorted(set(in_text)) != sorted(set(values)) and len(set(values)) == 2 or len(in_text) < 2:
        return False
    # The values are compared in the order they appear in the sentence.
    x, y = in_text[0], in_text[1]
    greater, lesser = _GREATER_RE.search(text), _LESSER_RE.search(text)
    if greater and lesser:
        return False
    if greater and not x > y:
        return False
    if lesser and not x < y:
        return False
    scopes = wi.scope_label(doc, first), wi.scope_label(doc, second)
    return scopes[0] is not None and scopes[0] == scopes[1] and _terminal(first) == _terminal(second)


def _movement(text: str, paths: list[str], index: dict, fail) -> None:
    match = _MOVEMENT_FORM.search(text)
    if not match or _MOVEMENT_BAD.search(text):
        fail("W8.form")
        return
    h = [p for p in paths if p.endswith(".h_break")]
    v = [p for p in paths if p.endswith(".v_break")]
    if len(h) != 1 or len(v) != 1 or h[0].rsplit(".", 1)[0] != v[0].rsplit(".", 1)[0]:
        fail("W8.form")
        return
    if not all(isinstance(index[p], (int, float)) and not isinstance(index[p], bool) for p in (h[0], v[0])):
        fail("W8.value")
        return
    hv, vv = Decimal(str(index[h[0]])), Decimal(str(index[v[0]]))
    direction = match.group(3).lower()
    if Decimal(match.group(1)) != abs(hv) or Decimal(match.group(2)) != abs(vv) or (vv > 0 and direction != "up") or (vv < 0 and direction != "down"):
        fail("W8.value")


def _terms(texts: list[str], sentences: list[dict], glossary: dict, fail) -> None:
    for term, forms in glossary.items():
        if term in _TERM_PATTERNS:
            pattern = _TERM_PATTERNS[term]
        elif term in ("K%", "BB%"):
            pattern = re.compile(re.escape(term))
        else:
            pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.I)
        defined = [i for i, t in enumerate(texts) if t in forms]
        if len(defined) > 1:
            fail("W11.definition")
        uses = [i for i, t in enumerate(texts) if t not in forms and pattern.search(t)]
        if uses and (not defined or defined[0] > uses[0]):
            fail("W11.order" if defined else "W11.definition")
    for i, t in enumerate(texts):
        for term, forms in glossary.items():
            if t not in forms and t.lower().startswith(term.lower() + _IS) and len(t) < 160:
                fail("W11.definition")


def _surname(name: str) -> str:
    return _nfc(name).split()[-1]


def _limits(candidate: dict, sentences: list[dict], doc: dict, fail) -> None:
    for slot in wi.SLOTS:
        starter = doc["starters"][slot]
        limited = starter["sample"]["limited"]
        name = _nfc(starter["name"])
        mentions = [s for s in sentences if _surname(name) in _nfc(s["text"])]
        if limited["arsenal"]:
            slot_prefixes = (f"starters.{slot}.pitching_profile.primary_pitch", f"starters.{slot}.pitching_profile.putaway_pitch",
                             f"starters.{slot}.pitching_profile.style_label", f"pitch_movement.{slot}.")
            for s in sentences:
                for e in s["evidence"]:
                    if e["path"].startswith(slot_prefixes) or (e["path"].startswith("pitch_mix.") and e["path"].split(".")[2:3] == [slot]):
                        fail("W6.arsenal")
        if any(limited.values()) and not any(_LIMITED_WORDS.search(s["text"]) for s in mentions):
            fail("W6.unsaid")


def _series(doc: dict, texts: list[str], fail) -> None:
    joined = " ".join(texts)
    series = doc.get("series")
    if series is None:
        if re.search(r"\bseries\b", joined, re.I):
            fail("W13.series")
        return
    if series.get("standing") is None and _SERIES_STANDING.search(joined):
        fail("W13.standing")


def _coverage(doc: dict, texts: list[str], scope_labels: set, fail) -> None:
    joined = " ".join(texts)
    if not all(_surname(doc["starters"][slot]["name"]) in joined for slot in wi.SLOTS):
        fail("W14.starter")
    for side in wi.SIDES:
        team = doc["teams"][side]
        if team["name"] not in joined and team["abbreviation"] not in joined and team["name"].split()[-1] not in joined:
            fail("W14.team")
    if not any(label in joined for label in scope_labels):
        fail("W12.scope")


def to_report(candidate: dict, rules_report: dict) -> dict:
    """The standard report shape (headline, short_summary, sections) with the rules writer's section titles."""

    texts = lambda key: " ".join(s["text"] for s in candidate["sections"][key])
    titles = [s["title"] for s in rules_report["sections"]]
    sections = [{"title": titles[i], "body": texts(key)} for i, key in enumerate(SECTION_KEYS) if key != "watch"]
    sections.insert(4, {"title": titles[4], "bullets": [s["text"] for s in candidate["sections"]["watch"]]})
    return {"headline": candidate["headline"]["text"], "short_summary": [s["text"] for s in candidate["summary_lines"]], "sections": sections}
