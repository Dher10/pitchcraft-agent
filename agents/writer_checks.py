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
_OUTCOME = _word(_W["outcome"])
_INTENSITY = re.compile(r"(?<!\w)(?:" + "|".join(_W["intensity"]) + r")(?!\w)", re.I)  # "elite-level" counts; "below-average" has no such word
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
_DEFINING = LEX["patterns"]["defining_verbs"]
_BAD_CODE = "W0.error"


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


def _strip_possessive(token: str) -> str:
    """Soriano's -> Soriano; Angels' -> Angels (straight or curly apostrophe)."""

    return token.removesuffix("'s").removesuffix("’s").rstrip("'’")


def _entity_runs(text: str) -> list[tuple[list[str], bool]]:
    """Runs of consecutive capitalized words (possessives stripped) and whether the run opens the sentence."""

    runs: list[tuple[list[str], bool]] = []
    last_end = None
    for match in _CAPITALIZED.finditer(text):
        token = match.group(0)
        if not token[0].isupper():
            last_end = None
            continue
        if last_end is not None and match.start() - last_end == 1 and text[last_end] == " ":
            runs[-1][0].append(_strip_possessive(token))
        else:
            runs.append(([_strip_possessive(token)], match.start() == 0))
        last_end = match.end()
    return runs


def _name_paths(doc: dict) -> set[str]:
    paths = {"venue", "series.series_name"}
    for slot in wi.SLOTS:
        paths |= {f"starters.{slot}.name", f"starters.{slot}.team"}
    for side in wi.SIDES:
        paths |= {f"teams.{side}.name", f"teams.{side}.abbreviation"}
    return paths


def _phrases(doc: dict, index: dict) -> set[tuple]:
    """Names the writer may use: the canonical ones and the aliases built from the packet, nothing else."""

    phrases: set[tuple] = set()
    names = [index.get(p) for p in _name_paths(doc)] + [a for group in wi.name_aliases(doc).values() for a in group]
    for name in names:
        if isinstance(name, str):
            for run, _ in _entity_runs(_nfc(name)):
                phrases.add(tuple(run))
    return phrases


def _vocabulary(doc: dict, index: dict) -> set[str]:
    """Capitalized words that are not names: pitch names, labels, scope words, glossary terms."""

    vocab = set(_EXEMPT_CAPITALS)
    skip = _name_paths(doc)
    for path, value in index.items():
        if isinstance(value, str) and path not in skip and not path.startswith("aliases.") and not path.endswith(".meaning"):
            vocab.update(token for run, _ in _entity_runs(_nfc(value)) for token in run)
    for term in doc["glossary"]:
        vocab.update(token for run, _ in _entity_runs(_nfc(term)) for token in run)
    return vocab


def _run_allowed(run: list[str], starts: bool, phrases: set, vocab: set) -> bool:
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def ok(i: int, after_name: bool) -> bool:
        if i == len(run):
            return True
        if not after_name:  # two names side by side ("Colorado Angels") would be a team that does not exist
            for j in range(i + 1, min(len(run), i + 6) + 1):
                if tuple(run[i:j]) in phrases and ok(j, True):
                    return True
        if (run[i] in vocab or (i == 0 and starts and run[i] in _OPENERS)) and ok(i + 1, False):
            return True
        return False

    return ok(0, False)


def _first(pattern, text: str):
    match = pattern.search(text)
    return match.group(0) if match else None


def check_report_detailed(candidate: dict, doc: dict, rules_len: int) -> list[dict]:
    """Every failed check as {"check", "sentence", "token"}; the sentence is None for a report-level check.

    This is the owner's per-sentence detail: the offending token is the writer's own text or value, kept in the local run
    record only. The informed retry still receives closed codes, never this text."""

    if not _structure_ok(candidate):
        return [{"check": "W17.structure", "sentence": None, "token": None}]
    found: list[dict] = []

    def add(code: str, sentence: str | None, token) -> None:
        entry = {"check": code, "sentence": sentence, "token": None if token is None else str(token)}
        if entry not in found:
            found.append(entry)

    index = wi.evidence_index(doc)
    phrases, vocab = _phrases(doc, index), _vocabulary(doc, index)
    glossary = doc["glossary"]
    sentences = _all_sentences(candidate)
    watch_ids = {id(s) for s in candidate["sections"]["watch"]}
    texts = [_nfc(s["text"]) for s in sentences]
    scope_labels = {v for p, v in index.items() if isinstance(v, str) and p.endswith(".label")}

    for sentence, text in zip(sentences, texts):
        def fail(code: str, token=None, text=text) -> None:
            add(code, text, token)

        try:
            _check_sentence(sentence, text, doc, index, phrases, vocab, glossary, watch_ids, fail)
        except Exception:  # a malformed citation or value must reject the candidate, never crash the run
            fail(_BAD_CODE)

    def fail_at(i: int, code: str, token=None) -> None:
        add(code, texts[i], token)

    def fail_all(code: str, token=None) -> None:
        add(code, None, token)

    _terms(sentences, texts, glossary, fail_at)
    _scope_repeats(candidate, texts, scope_labels, fail_at)
    _limits(candidate, sentences, doc, fail_all)
    _series(doc, texts, fail_all)
    _coverage(doc, texts, scope_labels, fail_all)
    low, high = rules_len * (1 - LENGTH_TOLERANCE), rules_len * (1 + LENGTH_TOLERANCE)
    if not Decimal(low) <= Decimal(report_length(candidate)) <= Decimal(high):
        fail_all("W17.length", report_length(candidate))
    return found


def check_report(candidate: dict, doc: dict, rules_len: int) -> list[str]:
    """Closed failure codes of `candidate` against the guide; [] means all checks passed."""

    return list(dict.fromkeys(f["check"] for f in check_report_detailed(candidate, doc, rules_len)))


def _check_sentence(sentence, text, doc, index, phrases, vocab, glossary, watch_ids, fail) -> None:
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
            fail("W1.evidence_path", e["path"])
            paths_ok = False
        elif not _same_value(e["value"], index[e["path"]]):
            fail("W1.evidence_value", e["path"])
            paths_ok = False
    paths = [e["path"] for e in cited]
    for path in paths:
        if path.endswith(".meaning"):
            fail("W11.definition", path)
    for term, entry in glossary.items():
        if _is_definition(text, term, _nfc(entry["meaning"])):
            fail("W11.definition", term)
    if not paths_ok:
        return
    cited_text = " ".join(_value_text(index[p]) for p in paths if p in index)
    cited_numbers = set(_numbers(cited_text))
    for token in _NUMBER.findall(text):
        if Decimal(token) not in cited_numbers:
            fail("W1.number", token)
    if _NUMBER_WORDS.search(text):
        fail("W1.number", _first(_NUMBER_WORDS, text))
    if _ZERO_CLAIM.search(text) and not any(isinstance(index[p], (int, float)) and not isinstance(index[p], bool) and index[p] == 0 for p in paths):
        fail("W1.number", _first(_ZERO_CLAIM, text))
    for run, starts in _entity_runs(text):
        if not _run_allowed(run, starts, phrases, vocab):
            fail("W1.entity", " ".join(run))
    if _QUESTION_OPENER.match(text) or "？" in text:
        fail("W15.question", _first(_QUESTION_OPENER, text) or "？")
    if _ARITHMETIC.search(text):
        fail("W2.arithmetic", _first(_ARITHMETIC, text))
    if _COMPARATIVE.search(text) and not _comparison_ok(text, cited, doc, index):
        fail("W2.comparison", _first(_COMPARATIVE, text))
    if _PREDICTION.search(text) or _OUTCOME.search(text):
        fail("W3.prediction", _first(_PREDICTION, text) or _first(_OUTCOME, text))
    if _TOPIC.search(text):
        fail("W4.topic", _first(_TOPIC, text))
    label_words = {w.lower() for p in paths if p in index and ("_label" in p or p.startswith("findings.")) for w in re.findall(r"[A-Za-z-]+", _value_text(index[p]))}
    for match in _INTENSITY.finditer(text):
        if match.group(0).lower() not in label_words:
            fail("W5.intensity", match.group(0))
    for term, key in _LABEL_TERMS:
        # A lineup note may speak of swing-and-miss (W5) when the term is in the cited note itself.
        note_text = " ".join(str(index[p]).lower() for p in paths if p.startswith("findings.lineup_notes.") and index[p] is not None)
        if term in text.lower() and not _LIMITED_WORDS.search(text) and term not in note_text and not any(p.endswith(key) for p in paths):
            fail("W5.label", term)
    for p in paths:
        if index.get(p) is None and p in index and not _LIMITED_WORDS.search(text):
            fail("W7.missing", p)
    if _CAUSE.search(text):
        fail("W10.cause", _first(_CAUSE, text))
    if _UNKNOWN_TERMS.search(text):
        fail("W11.unknown_term", _first(_UNKNOWN_TERMS, text))
    if _TIME.search(text):
        fail("W12.time", _first(_TIME, text))
    if "?" in text:
        fail("W15.question", "?")
    if _INTERNAL.search(text):
        fail("W16.internal", _first(_INTERNAL, text))
    if any(p.startswith("pitch_movement.") for p in paths):
        _movement(text, paths, index, fail)
    elif _MOVEMENT_BAD.search(text):
        fail("W8.form", _first(_MOVEMENT_BAD, text))
    if id(sentence) in watch_ids:
        if not _WATCH_FORM.match(text):
            fail("W15.form", text[:20])
        if _WATCH_OUTCOME.search(text):
            fail("W15.outcome", _first(_WATCH_OUTCOME, text))


def _is_definition(text: str, term: str, meaning: str) -> bool:
    """True when the sentence writes the glossary definition into the prose.

    Three shapes: the meaning as the whole sentence; a long meaning that opens the sentence; or a sentence that begins
    `<term> is/means/refers to/stands for` and carries no number (so `ERA is 8.08` is a figure, `ERA is the average ...` is a
    definition). A sentence that merely contains a short meaning ("He has 39 strikeouts.") is ordinary prose."""

    t, m = text.lower().rstrip(". "), meaning.lower().rstrip(". ")
    if t == m or (len(m) >= 25 and t.startswith(m[:25])):
        return True
    if re.match(re.escape(term.lower()) + _DEFINING, t) and not re.search(r"\d", t):
        return True
    return False


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


def _term_pattern(term: str):
    if term in _TERM_PATTERNS:
        return _TERM_PATTERNS[term]
    if term in ("K%", "BB%"):
        return re.compile(re.escape(term))
    return re.compile(r"\b" + re.escape(term) + r"\b", re.I)


def _terms(sentences: list[dict], texts: list[str], glossary: dict, fail_at) -> None:
    """A term with a short form gets it in parentheses, cited, on its first use and only once per report."""

    for term, entry in glossary.items():
        short = entry["short"]
        pattern = _term_pattern(term)
        uses = [(i, m) for i, t in enumerate(texts) for m in pattern.finditer(t)]
        if not uses or short is None:
            continue
        expansion = re.compile("(?:" + pattern.pattern + ")" + re.escape(" (" + short + ")"), pattern.flags)
        first_i, first_match = uses[0]
        cited = [e["path"] for e in sentences[first_i]["evidence"]]
        if not expansion.match(texts[first_i], first_match.start()) or f"glossary.{term}.short" not in cited:
            fail_at(first_i, "W11.expansion", term)
        seen = [i for i, t in enumerate(texts) for _ in expansion.finditer(t)]
        if len(seen) > 1:
            fail_at(seen[1], "W11.repeat", term)


def _scope_repeats(candidate: dict, texts: list[str], scope_labels: set, fail_at) -> None:
    """A scope is stated once per section (the headline and summary lines count as one), not in every sentence."""

    groups, start = [range(0, 4)], 4
    for key in SECTION_KEYS:
        groups.append(range(start, start + len(candidate["sections"][key])))
        start += len(candidate["sections"][key])
    for group in groups:
        for label in scope_labels:
            hits = [i for i in group if label in texts[i]]
            if len(hits) > 1:
                fail_at(hits[1], "W12.repeat", label)


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


def lexical_failures(text: str, doc: dict) -> list[dict]:
    """Calibration only: the words the word-level checks flag in text that carries no citations (the rules writer's report).

    Evidence, number-matching and glossary checks need citations and are not run. A hit is a word or shape a check flags;
    whether it would be a violation depends on the citations (a comparison word is allowed when both values are quoted, and an
    entity run such as a sentence-opening question word is a limit of the heuristic, not a forbidden pattern)."""

    index = wi.evidence_index(doc)
    phrases, vocab = _phrases(doc, index), _vocabulary(doc, index)
    out: list[dict] = []
    sentences = [x.strip() for x in re.split(r"(?<=[.!?;])\s+(?=[A-Z])", text) if x.strip()]
    checks = (("W1.number", _NUMBER_WORDS), ("W2.arithmetic", _ARITHMETIC), ("W2.comparison", _COMPARATIVE), ("W3.prediction", _PREDICTION),
              ("W3.prediction", _OUTCOME), ("W4.topic", _TOPIC), ("W5.intensity", _INTENSITY), ("W10.cause", _CAUSE), ("W11.unknown_term", _UNKNOWN_TERMS),
              ("W12.time", _TIME), ("W16.internal", _INTERNAL))
    for sentence in sentences:
        s = _nfc(sentence)
        for code, pattern in checks:
            for match in pattern.finditer(s):
                out.append({"check": code, "sentence": s, "token": match.group(0)})
        if "?" in s or _QUESTION_OPENER.match(s):
            out.append({"check": "W15.question", "sentence": s, "token": "?"})
        for run, starts in _entity_runs(s):
            if not _run_allowed(run, starts, phrases, vocab):
                out.append({"check": "W1.entity", "sentence": s, "token": " ".join(run)})
    return out
