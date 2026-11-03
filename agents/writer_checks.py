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
_OUTCOME = _word(_W["outcome"])
_INTENSITY = re.compile(r"(?<!\w)(?:" + "|".join(_W["intensity"]) + r")(?!\w)", re.I)  # "elite-level" counts; "below-average" has no such word
_WATCH_OUTCOME, _NUMBER_WORDS = _word(_W["watch_outcome"]), _word(_W["number_words"])
_PREDICTION, _TOPIC, _CAUSE, _TIME = (re.compile(_P[k], re.I) for k in ("prediction", "topic", "cause", "time"))
_INTERNAL, _UNKNOWN_TERMS = re.compile(_P["internal"], re.I), re.compile(_P["unknown_terms"], re.I)
_QUESTION_OPENER, _ZERO_CLAIM = re.compile(_P["question_opener"], re.I), re.compile(_P["zero_claim"], re.I)
_MOVEMENT_BAD, _MOVEMENT_CORE = re.compile(_P["movement_bad"], re.I), re.compile(_P["movement_core"], re.I)
_MOVEMENT_CLAUSE = re.compile(_P["movement_clause"], re.I)
_SERIES_STANDING, _LIMITED_WORDS = re.compile(_P["series_standing"], re.I), re.compile(_P["limited_words"], re.I)
_WATCH_FORM = re.compile(_P["watch_form"])
_OPENERS, _EXEMPT_CAPITALS = frozenset(LEX["openers"]), frozenset(LEX["exempt_capitals"])
_LABEL_TERMS = tuple(tuple(x) for x in LEX["label_terms"])
_TERM_PATTERNS = {k: re.compile(v) for k, v in LEX["term_patterns"].items()}
_IS = LEX["is_joiner"]
_DEFINING = LEX["patterns"]["defining_verbs"]
_BAD_CODE = "W0.error"
_STYLE_CODES = frozenset(LEX["style_codes"])
_STYLE = LEX["style"]
_S4 = _word(_STYLE["s4_verbs"])
_S7 = re.compile(_STYLE["s7_tails"], re.I)
_S8 = re.compile(_STYLE["s8_authority"], re.I)
_S2_FRAME = re.compile(_STYLE["s2_frame"])


def is_gate(code: str) -> bool:
    """Hard gates are accuracy, safety, policy and output-shape checks (D52). Style rules are scored, never gates. Unknown codes are gates."""

    return code not in _STYLE_CODES


def split_failures(found: list[dict]) -> tuple[list[dict], list[dict]]:
    return [f for f in found if is_gate(f["check"])], [f for f in found if not is_gate(f["check"])]


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


def _structure_ok(candidate: object, *, expanded=False) -> bool:
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
            if set(s) != {"text", "evidence"} or type(s["text"]) is not str or not isinstance(s["evidence"], list) or len(s["evidence"]) > (MAX_EVIDENCE * 4 if expanded else MAX_EVIDENCE):
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
            prefix = text[:match.start()].rstrip(' \t\n\"\u201c\u201d\'')
            starts = not prefix or prefix.endswith(("!", "?"))
            if prefix.endswith("."):
                last = prefix.split()[-1].rstrip('\"\u201d')
                starts = last.lower() not in LEX["instrument"]["abbreviations"] and not re.fullmatch(r"[A-Z]\.", last)
            runs.append(([_strip_possessive(token)], starts))
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

    if not _structure_ok(candidate, expanded=True):
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
    _style(candidate, doc, index, texts, scope_labels, phrases, vocab, fail_at)
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
    # A definition of a glossary term in the prose: the approved wording is a style finding (W11.inline), any other wording is
    # an unverified claim and a gate (W11.definition, D52).
    cited_terms = {p[len("glossary."):-len(".meaning")] for p in paths if p.startswith("glossary.") and p.endswith(".meaning")}
    for term, entry in glossary.items():
        meaning = _nfc(entry["meaning"])
        if term in cited_terms or _is_definition(text, term, meaning):
            fail("W11.inline" if _norm(text) in _approved_forms(term, meaning) else "W11.definition", term)
    if not paths_ok:
        return
    cited_text = " ".join(_value_text(index[p]) for p in paths if p in index)
    # A complete scope's cutoff supports natural month-day wording as well as ISO.
    from datetime import date
    for p in paths:
        if p.endswith(".through") and isinstance(index.get(p), str):
            try:
                cutoff = date.fromisoformat(index[p])
                cited_text += f" {cutoff.day} {cutoff.month}"
            except ValueError:
                pass
    cited_numbers = set(_numbers(cited_text))
    for token in _NUMBER.findall(text):
        if Decimal(token) not in cited_numbers:
            fail("W1.number", token)
    for pattern, fields in LEX["instrument"]["measured_values"]:
        for match in re.finditer(pattern, text, re.I):
            number = Decimal(match["value"])
            from agents.fact_table import subject_field
            owners = _measurement_owners(text, match, fields, doc, index, paths)
            if not owners or not all(any(p.rsplit(".", 1)[-1] in fields and number in _numbers(_value_text(index[p])) and subject_field(doc, p)[0] == owner for p in paths) for owner in owners):
                fail("W1.number", match["value"])
    if not _scope_time_ok(text, paths, doc, index):
        fail("W12.time", text)
    if _NUMBER_WORDS.search(text):
        fail("W1.number", _first(_NUMBER_WORDS, text))
    if _ZERO_CLAIM.search(text) and not any(isinstance(index[p], (int, float)) and not isinstance(index[p], bool) and index[p] == 0 for p in paths):
        fail("W1.number", _first(_ZERO_CLAIM, text))
    if any(p.endswith(".through") for p in paths):
        vocab = vocab | set(LEX["instrument"]["months"])
    for run, starts in _entity_runs(text):
        if not _run_allowed(run, starts, phrases, vocab):
            fail("W1.entity", " ".join(run))
    if _QUESTION_OPENER.match(text) or "？" in text:
        fail("W15.question", _first(_QUESTION_OPENER, text) or "？")
    if _ARITHMETIC.search(text):
        fail("W2.arithmetic", _first(_ARITHMETIC, text))
    if forbidden := _forbidden_comparison(text, doc):
        fail("W2.comparison", forbidden)
    if _PREDICTION.search(text) or _OUTCOME.search(text):
        fail("W3.prediction", _first(_PREDICTION, text) or _first(_OUTCOME, text))
    if _TOPIC.search(text):
        fail("W4.topic", _first(_TOPIC, text))
    _check_label_values(text, paths, index, fail)
    for term, key in _LABEL_TERMS:
        # A lineup note may speak of swing-and-miss (W5) when the term is in the cited note itself.
        note_text = " ".join(str(index[p]).lower() for p in paths if p.startswith("findings.lineup_notes.") and index[p] is not None)
        finding_text = " ".join(str(index[p]).lower() for p in paths if p.startswith("findings.") and index[p] is not None)
        if term in text.lower() and not _LIMITED_WORDS.search(text) and term not in note_text and term not in finding_text and not any(p.endswith(key) for p in paths):
            fail("W5.label", term)
    for p in paths:
        if index.get(p) is None and p in index and not _LIMITED_WORDS.search(text):
            fail("W7.missing", p)
    if re.search(LEX["instrument"]["authority"], text, re.I):
        fail("W1.authority", re.search(LEX["instrument"]["authority"], text, re.I).group())
    if _CAUSE.search(text) and not _cause_ok(text, paths, doc, index):
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


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip().rstrip(".").strip()


def _approved_forms(term: str, meaning: str) -> set[str]:
    """The sentences that are the approved definition of `term`: the meaning as written, or `<term> is <meaning>`."""

    return {_norm(meaning), _norm(f"{term}{_IS}{meaning}")}


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


def _label_normalized(text: str) -> str:
    return " ".join(re.findall(r"[^\W_]+", _nfc(text).casefold()))


def _label_phrase(quality, dimension, prefix):
    dim = _label_normalized(dimension)
    if dim == LEX["instrument"]["w5_generic_rate"]:
        activities = [(m.end(), value) for activity,value in LEX["instrument"]["label_rate_activities"].items() for m in re.finditer(activity, prefix)]
        if activities:
            dim = max(activities)[1]
    return f"{_label_normalized(quality)} {dim}"


def _label_claims(text: str, known_values: set[str]):
    qualities = sorted({_label_normalized(w) for w in (*LEX["instrument"]["label_qualities"], *_W["intensity"])}, key=len, reverse=True)
    quality = "(?:" + "|".join(re.escape(w) for w in qualities) + ")"
    dimension = "(?:" + LEX["instrument"]["w5_dimensions"] + ")"
    patterns = [pattern.format(quality=quality, dimension=dimension, postpositive=LEX["instrument"]["label_postpositive"]) for pattern in LEX["instrument"]["w5_claim_patterns"]]
    claims = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            claims.append((match.start(), match.end(), _label_phrase(match["quality"], match["dimension"], text[:match.start()])))
    # Full enum values also cover non-adjectival style labels. Retain the
    # longest phrase, so 'average command' cannot hide 'below-average command'.
    claims += [(m.start(), m.end(), value) for value in known_values if value for m in re.finditer(r"(?<!\w)" + re.escape(value) + r"(?!\w)", text)]
    return [claim for claim in sorted(set(claims)) if not any(a <= claim[0] and b >= claim[1] and b-a > claim[1]-claim[0] for a,b,_ in claims)]


def _check_label_values(text, paths, index, fail):
    known = {_label_normalized(value) for path,value in index.items() if path.endswith("_label") and isinstance(value, str)}
    sources = [_label_normalized(index[p]) for p in paths if isinstance(index.get(p), str) and (p.endswith("_label") or p.startswith("findings."))]
    supported = {phrase for source in sources for _,_,phrase in _label_claims(source, known)}
    normalized = _label_normalized(text)
    name_words = {word for path,value in index.items() if path.endswith(".name") and isinstance(value, str) for word in _label_normalized(value).split()}
    comparators = {_label_normalized(word) for word in (*_GREATER, *_LESSER, *_W["neutral"])}
    claims = _label_claims(normalized, known)
    # Discover style forms independently of the complete enum values in
    # this packet; an absent/reordered style must still be checked.
    asserted = {phrase for _,_,phrase in claims}
    # Discover a modifier even when it is absent from every known label;
    # bare mentions (function words/verbs) do not assert a label value.
    for pattern in LEX["instrument"]["w5_open_patterns"]:
        for match in re.finditer(pattern, text, re.I):
            quality = _label_normalized(match["quality"])
            if quality in LEX["instrument"]["w5_nonqualifiers"] or quality in name_words or quality in comparators or not any(char.isalpha() for char in quality):
                continue
            phrase = _label_phrase(quality, match["dimension"], _label_normalized(text[:match.start()]))
            if not any(phrase == value or phrase in value for value in asserted):
                asserted.add(phrase)
                if phrase not in supported:
                    fail("W5.label", phrase)
    for pattern in LEX["instrument"]["w5_style_patterns"]:
        for match in re.finditer(pattern, text, re.I):
            phrase = _label_normalized(match["value"])
            if phrase not in asserted and phrase not in LEX["instrument"]["w5_starter_roles"]:
                asserted.add(phrase)
                if phrase not in supported:
                    fail("W5.label", phrase)
    verified = []
    for start,end,phrase in claims:
        if phrase not in supported:
            fail("W5.label", phrase)
        else:
            verified.append((start,end))
    for match in _INTENSITY.finditer(normalized):
        if not any(start <= match.start() and end >= match.end() for start,end in verified):
            fail("W5.intensity", match.group())


def _forbidden_comparison(text: str, doc: dict) -> str | None:
    """D62: no figure comparisons; exempt only split/matchup and movement baseline."""
    for match in _COMPARATIVE.finditer(text):
        if re.fullmatch(LEX["instrument"]["versus_token"], match.group(), re.I):
            if re.match(LEX["instrument"]["split_versus"], text[match.start():], re.I):
                continue
            # A matchup joins two adjacent named participants, never figures.
            mentions = _subject_mentions(text, doc)
            before = {name for _, end, name in mentions if end <= match.start() and not text[end:match.start()].strip()}
            after = {name for start, _, name in mentions if start >= match.end() and not text[match.end():start].strip()}
            if any(left != right for left in before for right in after):
                continue
        if _MOVEMENT_CLAUSE.match(text, match.start()):
            continue
        return match.group()
    return None


def _subject_mentions(text, doc):
    mentions = []
    aliases = wi.name_aliases(doc)
    for group, keys in (("starters", wi.SLOTS), ("teams", wi.SIDES)):
        for key in keys:
            name = doc[group][key]["name"]
            for alias in [name, *aliases[key]]:
                mentions.extend((m.start(), m.end(), name) for m in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I))
    for key, pattern in LEX["instrument"]["subject_roles"].items():
        group = "starters" if key in wi.SLOTS else "teams"
        mentions.extend((m.start(), m.end(), doc[group][key]["name"]) for m in re.finditer(pattern, text, re.I))
    return sorted(set(mentions))


def _mentioned_subjects(text, doc):
    return list(dict.fromkeys(name for _, _, name in _subject_mentions(text, doc)))


def _measurement_after(text, doc):
    for entry in doc["glossary"].values():
        if entry["short"] and (short := re.match(r"\s*\(" + re.escape(entry["short"]) + r"\)", text, re.I)):
            return text[short.end():]
    return text


def _post_measurement_owner(after, doc, eligible):
    after = _measurement_after(after, doc)
    owners = set()
    last_end = None
    for start,end,name in _subject_mentions(after, doc):
        if last_end is not None:
            if start < last_end:
                continue
            if re.fullmatch(LEX["instrument"]["measurement_owner_conjunction"], after[last_end:start], re.I) and not re.match(LEX["instrument"]["measurement_new_claim"], after[end:], re.I):
                owners.add(name)
                last_end = end
                continue
            break
        if name not in eligible:
            continue
        if re.fullmatch(LEX["instrument"]["measurement_after_owner"], after[:start], re.I) or (
            re.fullmatch(LEX["instrument"]["measurement_relative_owner_head"], after[:start], re.I)
            and re.match(LEX["instrument"]["measurement_relative_owner_verb"], after[end:], re.I)
        ):
            owners.add(name)
            last_end = end
    return owners


def _measurement_owners(text, match, fields, doc, index, paths):
    """Bind this numeric claim locally, rather than pooling named owners.

    This is lexical ownership checking only: NLI still sees the original
    unchanged sentence. Ambiguous joint claims need support for every owner.
    """
    from agents.fact_table import subject_field
    eligible = {subject_field(doc, p)[0] for p in index if p.rsplit(".", 1)[-1] in fields}

    def mentions(part):
        return [(a,b,name) for a,b,name in _subject_mentions(part, doc) if name in eligible]

    anchor = match.start("value")
    stops = []
    for stop in re.finditer(LEX["instrument"]["measurement_stops"], text):
        word = text[:stop.end()].split()[-1]
        if word.lower() not in LEX["instrument"]["abbreviations"] and not re.fullmatch(r"[A-Z]\.", word):
            stops.append(stop)
    start = max((s.end() for s in stops if s.end() <= anchor), default=0)
    end = min((s.start() for s in stops if s.start() >= anchor), default=len(text))
    region = text[start:end]
    local_anchor = anchor - start
    joins = list(re.finditer(LEX["instrument"]["measurement_joiners"], region, re.I))
    bounds = [0, *(j.end() for j in joins), len(region)]
    chunk = max(i for i in range(len(bounds)-1) if bounds[i] <= local_anchor)
    chunks = [region[bounds[i]:(joins[i].start() if i < len(joins) else len(region))] for i in range(len(bounds)-1)]
    clause = chunks[chunk]
    offset = local_anchor - bounds[chunk]
    direction = _word((*_GREATER, *_LESSER)).search(clause)
    counterparts = [m for m in re.finditer(LEX["instrument"]["measurement_counterpart"], clause, re.I) if m.end() <= offset]
    prefix = clause[:offset]
    for group, pattern in LEX["instrument"]["measurement_shared_roles"].items():
        if re.search(pattern, prefix, re.I):
            shared = {item["name"] for item in doc[group].values()}
            return eligible & shared
    if counterparts:
        prefix = clause[counterparts[-1].end():offset]
    elif direction:
        prefix = clause[:min(offset, direction.start())]
    before = mentions(prefix)
    if not before and _subject_mentions(prefix, doc) and re.search(LEX["instrument"]["measurement_ownership"], prefix, re.I):
        return set()  # an explicit owner of another measure type is not anonymous
    first = next((m for m in _NUMBER.finditer(region) if any(Decimal(m[0]) in _numbers(_value_text(index[p])) for p in paths if p.rsplit(".",1)[-1] in fields)), None)
    initial = mentions(region[:first.start()]) if first else []
    joint = {name for _,_,name in initial}
    if len(joint) > 1 and re.search(LEX["instrument"]["measurement_joint_predicate"], region[initial[-1][1]:first.start()], re.I):
        return joint
    if before:
        return {before[-1][2]}
    after = _measurement_after(text[match.end():start + bounds[chunk] + len(clause)], doc)
    if following := _post_measurement_owner(text[match.end():end], doc, eligible):
        return following
    # A relative clause refers to the nearby comparison object, rather than
    # inheriting the earlier clause's primary subject.
    if re.match(LEX["instrument"]["measurement_relative_actor"], clause, re.I):
        prior = mentions(region[:bounds[chunk]])
        if prior:
            return {prior[-1][2]}
    # Coordinated comparison-object figures can share one trailing owner:
    # "... compared with the ERA and WHIP of Gausman".
    object_markers = list(re.finditer(LEX["instrument"]["measurement_counterpart"], region[:local_anchor], re.I))
    if object_markers and (counterparts or not direction):
        tail = region[object_markers[-1].end():]
        tail_owners = set()
        for a,b,name in _subject_mentions(tail, doc):
            if name in eligible and re.search(LEX["instrument"]["measurement_tail_owner"], tail[:a], re.I):
                tail_owners.add(name)
        if len(tail_owners) == 1:
            return tail_owners
    # Inherit a subject across coordinated measures, not across another
    # player's comparison-object mention ("... than Gausman and a lower...").
    inherited = set()
    for previous in reversed(chunks[:chunk]):
        comparison = _word((*_GREATER, *_LESSER)).search(previous)
        actors = mentions(previous[:comparison.start()] if comparison else previous)
        if actors:
            inherited = {actors[-1][2]}
            break
    other_after = {name for a,b,name in _subject_mentions(after, doc) if name not in eligible and re.fullmatch(LEX["instrument"]["measurement_after_owner"], after[:a], re.I)}
    if other_after:
        # "... WHIP for Houston" is an affiliation when its named starter is
        # already established, not a new owner of the pitcher measurement.
        affiliated = {doc["starters"][slot]["name"] for slot in wi.SLOTS if doc["teams"][slot.removesuffix("_starter")]["name"] in other_after}
        return inherited if inherited and inherited <= affiliated else set()
    if inherited:
        return inherited
    regional = {name for _,_,name in mentions(region)}
    if len(regional) == 1:
        return regional
    global_owners = {name for _,_,name in mentions(text)}
    if len(global_owners) == 1:
        return global_owners
    if global_owners:
        return set()  # no unambiguous antecedent for this particular claim
    cited = {subject_field(doc,p)[0] for p in paths if p.rsplit(".",1)[-1] in fields}
    return cited  # every possible cited owner must independently support it


def _scope_time_ok(text, paths, doc, index):
    from agents.fact_table import scope_path, subject_field
    subjects = _mentioned_subjects(text, doc)
    # The handedness split is part of a cited lineup value's scope too.
    hand_matches = list(re.finditer(LEX["instrument"]["split_claim"], text, re.I))
    side_paths = {p.split(".")[1] for p in paths if p.startswith("teams.") and ".offense_profile." in p}
    side_paths |= {p.rsplit(".", 1)[-1] for p in paths if p.startswith("findings.lineup_notes.")}
    previous = 0
    for match in hand_matches:
        named = _mentioned_subjects(text[previous:match.start()], doc)
        named_sides = {side for side in side_paths if doc["teams"][side]["name"] in named}
        sides = named_sides or side_paths
        actual = {doc["teams"][side]["offense_profile"]["vs_pitcher_hand"] for side in sides}
        if actual != {LEX["instrument"]["split_hands"][match["hand"].lower()]}:
            return False
        previous = match.end()
    matches = list(re.finditer(LEX["instrument"]["through_date"], text, re.I))
    claimed_kind = _scope_kind(text) if matches or re.search(LEX["instrument"]["scope_claim_context"], text, re.I) else None
    if not matches and claimed_kind is None:
        return True
    scopes = {scope_path(p) for p in paths if scope_path(p) and index.get(scope_path(p) + ".label") is not None}
    scopes.discard(None)
    if not scopes:
        return False
    supported = {subject_field(doc, base + ".label")[0] for base in scopes}
    for slot in wi.SLOTS:
        if doc["starters"][slot]["name"] in supported:
            supported.add(doc["teams"][slot.removesuffix("_starter")]["name"])
    if subjects and not set(subjects) <= supported:
        return False
    broad = re.search(LEX["instrument"]["broad_scope"], text, re.I)
    relevant = {p.rsplit(".",1)[0] for p in index if p.endswith(".through")} if broad else scopes
    if claimed_kind is not None and any(_scope_kind(str(index.get(base + ".label"))) != claimed_kind for base in relevant):
        return False
    years = re.findall(LEX["instrument"]["scope_year"], text, re.I)
    if years and any(not str(index.get(base + ".label")).startswith(year) for year in years for base in relevant):
        return False
    if broad and len({str(index.get(base + ".label")).split(LEX["instrument"]["scope_joiner"])[0] for base in relevant}) != 1:
        return False
    cited_dates = {str(index.get(base + ".through")) for base in relevant}
    for match in matches:
        raw = match["date"]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            if cited_dates != {raw}:
                return False
        else:
            words = raw.split()
            month = LEX["instrument"]["month_numbers"].get(words[0].rstrip(".").lower())
            if not month or any(date[5:] != f"{month:02d}-{int(words[1]):02d}" for date in cited_dates):
                return False
    return True


def _scope_kind(text):
    return next((kind for kind, pattern in LEX["instrument"]["scope_kinds"].items() if re.search(pattern, text, re.I)), None)


def _cause_ok(text, paths, doc, index):
    from agents.fact_table import limitation_paths
    lower = text.lower()
    # A finding states a specific cause/consequence for a specific starter.
    for path in paths:
        match = re.fullmatch(r"findings\.(away_starter|home_starter)_(?:risks|strengths)", path)
        if not match or not isinstance(index.get(path), str):
            continue
        slot = match[1]
        names = [doc["starters"][slot]["name"], *wi.name_aliases(doc)[slot]]
        if not any(re.search(r"\b" + re.escape(n.lower()) + r"\b", lower) for n in names):
            continue
        for finding in index[path].split(";"):
            cause = re.fullmatch(LEX["instrument"]["finding_cause"], finding.strip(), re.I)
            if cause and cause[1].lower() in lower and cause[2].lower() in lower:
                # No unrelated extra causal clause or asserted consequence.
                connector = _CAUSE.search(lower)
                name_pattern = "(?:" + "|".join(re.escape(n.lower()) for n in sorted(names, key=len, reverse=True)) + ")"
                frame = LEX["instrument"]["finding_consequence_frame"].format(name=name_pattern, effect=re.escape(cause[2].lower()))
                if connector and len(list(_CAUSE.finditer(text))) == 1 and re.fullmatch(frame, lower[:connector.start()].strip(" .")) and re.fullmatch(LEX["instrument"]["finding_reason_only"], lower[connector.end():].strip(" .")):
                    return True
    # Limited-sample label availability is the only code-derived cause.
    if len(list(_CAUSE.finditer(text))) != 1 or not re.search(LEX["instrument"]["limited_reason"], lower) or not re.search(LEX["instrument"]["missing_label"], lower):
        return False
    cause = _CAUSE.search(lower)
    reason = lower[cause.end():].strip(" .")
    if re.fullmatch(LEX["instrument"]["sample_reason_only"], reason) is None:
        return False
    dims = [dim for dim, pattern in LEX["instrument"]["label_dimensions"].items() if re.search(pattern, lower)]
    slots = [slot for slot in wi.SLOTS if any(re.search(r"\b" + re.escape(n.lower()) + r"\b", lower) for n in [doc["starters"][slot]["name"], *wi.name_aliases(doc)[slot]])]
    if re.search(LEX["instrument"]["both_starters"], lower):
        slots = list(wi.SLOTS)
    if not (dims and slots) or not all((proof := limitation_paths(doc, slot, dim)) and set(proof) <= set(paths) for slot in slots for dim in dims):
        return False
    # A rule proves label unavailability only, never an additional baseball
    # consequence or a negation of the supported missing-label claim.
    consequence = lower[:cause.start()]
    names = [n for slot in slots for n in [doc["starters"][slot]["name"], *wi.name_aliases(doc)[slot]]]
    for name in sorted(names, key=len, reverse=True):
        consequence = re.sub(r"\b" + re.escape(name.lower()) + r"\b", "", consequence)
    for pattern in [*LEX["instrument"]["label_dimensions"].values(), *LEX["instrument"]["limited_claim_parts"]]:
        consequence = re.sub(pattern, "", consequence, flags=re.I)
    return re.search(r"\w", consequence) is None


def _movement(text: str, paths: list[str], index: dict, fail) -> None:
    match = _MOVEMENT_CORE.search(text)
    clauses = _MOVEMENT_CLAUSE.findall(text)
    stripped = text.rstrip(". ").lower()
    clause = _MOVEMENT_CLAUSE.pattern
    at_end = stripped.endswith(clause)
    at_start = text.lower().startswith(clause)
    if not match or _MOVEMENT_BAD.search(text) or len(clauses) != 1 or not (at_end or at_start):
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
    """A term with a short form gets it on its first use, in either order ("OPS (on-base plus slugging)" or "on-base plus slugging
    (OPS)"), cited, and only once per report (guide 0.4, A1)."""

    for term, entry in glossary.items():
        short = entry["short"]
        pattern = _term_pattern(term)
        uses = [(i, m) for i, t in enumerate(texts) for m in pattern.finditer(t)]
        if not uses or short is None:
            continue
        forward = re.compile("(?:" + pattern.pattern + ")" + re.escape(" (" + short + ")"), pattern.flags)
        reverse = re.compile("(?i:" + re.escape(short) + r") \((?:" + pattern.pattern + r")\)", pattern.flags)
        first_i, first_match = uses[0]
        first_text = texts[first_i]
        inside_reverse = any(m.start() < first_match.start() < m.end() for m in reverse.finditer(first_text))
        cited = [e["path"] for e in sentences[first_i]["evidence"]]
        if not (forward.match(first_text, first_match.start()) or inside_reverse) or f"glossary.{term}.short" not in cited:
            fail_at(first_i, "W11.expansion", term)
        seen = [i for i, t in enumerate(texts) for _ in (*forward.finditer(t), *reverse.finditer(t))]
        if len(seen) > 1:
            fail_at(seen[1], "W11.repeat", term)


def _style(candidate: dict, doc: dict, index: dict, texts: list[str], scope_labels: set, phrases: set, vocab: set, fail_at) -> None:
    """Detectors for the style rules S-1, S-2, S-4, S-5, S-7 and S-8. They feed S1; none of them is a gate (D52).
    S-3, S-6 and S-9 are judged by S1, not by code."""

    for label in scope_labels:  # S-1: each scope once per report
        hits = [i for i, t in enumerate(texts) if label in t]
        if len(hits) > 1:
            fail_at(hits[1], "S-1", label)
    openers: dict[str, list[int]] = {}
    frames: list[int] = []
    for i, text in enumerate(texts):
        first = re.match(r"[^\W\d_][\w'’-]*", text)
        if first and first.group(0).lower() != "watch" and i != 0:
            openers.setdefault(first.group(0).lower(), []).append(i)
        if _S2_FRAME.match(text):
            frames.append(i)
        for match in _S4.finditer(text):
            fail_at(i, "S-4", match.group(0))
        for match in _S7.finditer(text):
            fail_at(i, "S-7", match.group(0))
        for match in _S8.finditer(text):
            fail_at(i, "S-8", match.group(0))
    for word, hits in openers.items():
        if len(hits) > _STYLE["s2_max_same_opener"]:
            fail_at(hits[_STYLE["s2_max_same_opener"]], "S-2", word)
    if len(frames) > 1:
        fail_at(frames[1], "S-2", _S2_FRAME.match(texts[frames[1]]).group(0))
    headline = texts[0]
    name_tokens = {t for phrase in phrases for t in phrase}
    for run, opens in _entity_runs(headline):
        for token in run[1:] if opens else run:
            if token not in name_tokens and token not in vocab:
                fail_at(0, "S-5", token)
    last = re.findall(r"[^\W\d_][\w'’-]*", headline)
    if last and last[-1].lower() in _STYLE["s5_tag_words"]:
        fail_at(0, "S-5", last[-1])


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
    whether it would be a violation depends on context (split/matchup versus is allowed, and an
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
