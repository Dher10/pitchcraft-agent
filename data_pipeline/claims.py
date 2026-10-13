"""Every sentence of the published file is recorded with what it was made of (contract rule 4).

The agents and the generator write their sentences through a `Catalog`, which returns `Phrase`
objects (the text plus the catalog key and the arguments). `attach_claims` walks the text fields of
a payload, writes one claim per field into `matchups[i].report.claims` (the sentences of a matchup,
locations relative to the matchup) and `claims` (the generator's sentences, locations from the
root), and leaves plain strings in the file. A text field that holds a plain string is refused: it
did not come from the catalog.

`verify_claims` is what `validate_payload` runs on the published JSON. It renders every claim again
from its key and arguments and requires the text in the file to be exactly that, so the text of a
report is exactly its registered phrases and a sentence edited, swapped or added by hand is found.

A claim is `{id, key, args, subject, location}`:

- `key`: a catalog key, or the pseudo keys `@join` (args `sep` and `parts`) and `@capitalize` (arg `of`).
- `args`: values copied from the payload (names, numbers, labels) or `{"claim": id}`, a reference to
  another claim that is part of this sentence. Never anything else (no objects, no exception text).
- `subject`: `away_starter`, `home_starter` or `null`, the starter the sentence is about.
- `location`: where the sentence is in the file, or `null` for a part of another sentence.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
import numbers
from typing import Any

from agents.language import (
    DEFAULT_LANGUAGE,
    SUBJECT_SLOTS,
    Catalog,
    MissingMessageError,
    Phrase,
    UnknownLanguageError,
    catalog_for,
)
from data_pipeline.generator_texts import GENERATOR_PREFIX, generator_catalog

JOIN_KEY = "@join"
CAPITALIZE_KEY = "@capitalize"
CLAIM_FIELDS = ("id", "key", "args", "subject", "location")

ANY_INDEX = "[*]"  # every item of a list
ANY_KEY = "*"  # every key of an object

# The fields that hold a sentence written by an agent, relative to a matchup.
MATCHUP_TEXT_PATHS: tuple[tuple[str, ...], ...] = (
    ("report", "headline"),
    ("report", "short_summary", ANY_INDEX),
    ("report", "sections", ANY_INDEX, "title"),
    ("report", "sections", ANY_INDEX, "body"),
    ("report", "sections", ANY_INDEX, "bullets", ANY_INDEX),
    ("critic_review", "summary"),
    ("critic_review", "checks", ANY_INDEX, "claim"),
    ("critic_review", "checks", ANY_INDEX, "evidence"),
    ("critic_review", "revision_notes", ANY_INDEX),
    ("data_confidence", "notes", ANY_INDEX),
    ("postgame", "starter_lines", ANY_KEY, "grade_explanation"),
    ("postgame", "starter_lines", ANY_KEY, "plan_vs_execution"),
    ("postgame", "starter_lines", ANY_KEY, "what_to_watch_next"),
    ("postgame", "call_check", ANY_INDEX, "pregame_note"),
    ("postgame", "call_check", ANY_INDEX, "postgame_evidence"),
)

# The fields that hold a sentence written by the generator, relative to the root.
ROOT_TEXT_PATHS: tuple[tuple[str, ...], ...] = (
    ("metadata", "last_updated_label"),
    ("agent_workflow", "description"),
    ("agent_workflow", "steps", ANY_INDEX, "output"),
)


class UnregisteredTextError(ValueError):
    """A text field holds a string that did not come from a catalog."""


# --- locating text -------------------------------------------------------------------------------


def _locate(node: Any, pattern: tuple[str, ...], prefix: str) -> Iterator[tuple[str, Any, Any]]:
    """(location, container, key) of every field of `node` that `pattern` reaches and that exists."""

    head, rest = pattern[0], pattern[1:]
    if head == ANY_INDEX:
        if not isinstance(node, list):
            return
        keys: list[Any] = list(range(len(node)))
    elif head == ANY_KEY:
        if not isinstance(node, Mapping):
            return
        keys = list(node)
    else:
        if not isinstance(node, Mapping) or head not in node:
            return
        keys = [head]
    for key in keys:
        location = f"{prefix}[{key}]" if isinstance(key, int) else (f"{prefix}.{key}" if prefix else str(key))
        if rest:
            yield from _locate(node[key], rest, location)
        else:
            yield location, node, key


def text_leaves(node: Any, patterns: tuple[tuple[str, ...], ...]) -> list[tuple[str, str]]:
    """(location, text) of every text field of `node`: the string fields the patterns reach."""

    leaves: list[tuple[str, str]] = []
    for pattern in patterns:
        for location, container, key in _locate(node, pattern, ""):
            value = container[key]
            if isinstance(value, str):
                leaves.append((location, value))
    return leaves


# --- attaching -----------------------------------------------------------------------------------


def attach_claims(payload: dict[str, Any], language: str = DEFAULT_LANGUAGE) -> None:
    """
    Record the claims of every text field of `payload` and leave plain strings in the fields.

    Raises `UnregisteredTextError` for a text field that is not a phrase and `TypeError` for an
    argument that is not a payload value.
    """

    payload.setdefault("metadata", {})["language"] = language
    for matchup in payload.get("matchups", []):
        report = matchup.setdefault("report", {})
        report["claims"] = _collect(matchup, MATCHUP_TEXT_PATHS)
    payload["claims"] = _collect(payload, ROOT_TEXT_PATHS)


class _Collector:
    def __init__(self) -> None:
        self.claims: list[dict[str, Any]] = []
        self._ids: dict[int, str] = {}
        self._alive: list[Phrase] = []  # an id() is only unique while the object lives

    def located(self, phrase: Phrase, location: str) -> None:
        self._make(phrase, location)

    def _make(self, phrase: Phrase, location: str | None) -> dict[str, Any]:
        claim: dict[str, Any] = {
            "id": f"c{len(self.claims) + 1}",
            "key": phrase.key,
            "args": {},
            "subject": phrase.subject,
            "location": location,
        }
        self.claims.append(claim)  # the sentence comes before its parts
        claim["args"] = {name: self._value(phrase.key, name, value) for name, value in phrase.args.items()}
        return claim

    def _reference(self, phrase: Phrase) -> str:
        known = self._ids.get(id(phrase))
        if known is None:
            self._alive.append(phrase)
            known = self._ids[id(phrase)] = self._make(phrase, None)["id"]
        return known

    def _value(self, key: str | None, name: str, value: Any) -> Any:
        if isinstance(value, Phrase):
            if value.key is None:
                raise UnregisteredTextError(f"argument {name!r} of {key!r} is a phrase with no key")
            return {"claim": self._reference(value)}
        if isinstance(value, (list, tuple)):
            return [self._value(key, name, item) for item in value]
        if value is None or isinstance(value, (str, bool)):
            return value
        if isinstance(value, numbers.Integral):
            return int(value)
        if isinstance(value, numbers.Real):
            return float(value)
        raise TypeError(f"argument {name!r} of {key!r} is a {type(value).__name__}, not a payload value")


def _collect(node: dict[str, Any], patterns: tuple[tuple[str, ...], ...]) -> list[dict[str, Any]]:
    collector = _Collector()
    fields: list[tuple[str, dict[str, Any], Any]] = []
    for pattern in patterns:
        for location, container, key in _locate(node, pattern, ""):
            value = container[key]
            if not isinstance(value, str):
                continue
            if not isinstance(value, Phrase) or value.key is None:
                raise UnregisteredTextError(
                    f"{location}: the text is not a registered phrase (it did not come from a catalog, "
                    f"or it was edited): {str(value)[:80]!r}"
                )
            fields.append((location, container, key))
    for location, container, key in fields:
        collector.located(container[key], location)
    for location, container, key in fields:
        container[key] = str(container[key])  # plain text in the file; the claim holds the record
    return collector.claims


# --- verifying -----------------------------------------------------------------------------------


def verify_claims(payload: Mapping[str, Any]) -> list[str]:
    """What is wrong with the claims of a published payload (an empty list when nothing is)."""

    metadata = payload.get("metadata")
    language = metadata.get("language") if isinstance(metadata, Mapping) else None
    try:
        agents = catalog_for(language)  # type: ignore[arg-type]
    except UnknownLanguageError:
        return [f"metadata.language {language!r} has no catalog, so the claims cannot be checked"]
    catalogs = (agents, generator_catalog())

    problems = _verify_list("root claims", payload.get("claims"), payload, ROOT_TEXT_PATHS, "", catalogs)
    matchups = payload.get("matchups")
    for index, matchup in enumerate(matchups if isinstance(matchups, list) else []):
        label = f"matchups[{index}]"
        report = matchup.get("report") if isinstance(matchup, Mapping) else None
        claims = report.get("claims") if isinstance(report, Mapping) else None
        problems += _verify_list(
            f"{label} report.claims", claims, matchup, MATCHUP_TEXT_PATHS, f"{label}.", catalogs
        )
    return problems


def _verify_list(
    name: str,
    claims: Any,
    container: Any,
    patterns: tuple[tuple[str, ...], ...],
    prefix: str,
    catalogs: tuple[Catalog, Catalog],
) -> list[str]:
    if not isinstance(claims, list):
        return [f"{name} is missing"]
    problems: list[str] = []
    by_id: dict[str, Mapping[str, Any]] = {}
    for position, claim in enumerate(claims):
        if not isinstance(claim, Mapping) or set(claim) != set(CLAIM_FIELDS):
            problems.append(f"{name}: item {position} is not a claim with the fields {', '.join(CLAIM_FIELDS)}")
            continue
        if claim["id"] in by_id:
            problems.append(f"{name}: duplicate claim id {claim['id']!r}")
            continue
        by_id[claim["id"]] = claim

    memo: dict[str, str | None] = {}
    referenced: set[str] = set()
    reported: set[tuple[str, str]] = set()

    def report(kind: str, message: str) -> None:
        if (kind, message) not in reported:
            reported.add((kind, message))
            problems.append(f"{name}: {message}")

    def resolve(value: Any, stack: tuple[str, ...]) -> tuple[bool, Any]:
        if isinstance(value, Mapping):
            if set(value) != {"claim"}:
                return False, None
            referenced.add(value["claim"])
            text = render(value["claim"], stack)
            return text is not None, text
        if isinstance(value, list):
            items = [resolve(item, stack) for item in value]
            return all(ok for ok, _ in items), [item for _, item in items]
        return True, value

    def render(claim_id: str, stack: tuple[str, ...]) -> str | None:
        if claim_id in stack:
            report("cycle", f"claim {claim_id!r} refers to itself")
            return None
        if claim_id in memo:
            return memo[claim_id]
        claim = by_id.get(claim_id)
        if claim is None:
            report("missing", f"a sentence refers to claim {claim_id!r}, which does not exist")
            return None
        memo[claim_id] = None  # failures below leave None; a success replaces it
        key, args = claim["key"], claim["args"]
        if not isinstance(key, str) or not isinstance(args, Mapping):
            report("shape", f"claim {claim_id!r} has no key or no arguments")
            return None
        if claim["subject"] not in (None, *SUBJECT_SLOTS):
            report("subject", f"claim {claim_id!r} has subject {claim['subject']!r}, not a starter slot")
        resolved: dict[str, Any] = {}
        for arg_name, value in args.items():
            ok, resolved_value = resolve(value, (*stack, claim_id))
            if not ok:
                if not (isinstance(value, Mapping) and "claim" in value):
                    report("arg", f"claim {claim_id!r} has an argument {arg_name!r} that is not a payload value")
                return None
            resolved[arg_name] = resolved_value
        text = _render(key, resolved, catalogs, lambda message: report("render", f"claim {claim_id!r} {message}"))
        memo[claim_id] = text
        return text

    for claim_id in by_id:
        render(claim_id, ())

    leaves = dict(text_leaves(container, patterns))
    seen: dict[str, str] = {}
    for claim_id, claim in by_id.items():
        location = claim["location"]
        if location is None:
            continue
        if not isinstance(location, str) or location not in leaves:
            report("location", f"claim {claim_id!r} is at {location!r}, which is not a text field of the file")
            continue
        if location in seen:
            report("twice", f"{prefix}{location} has more than one claim ({seen[location]!r} and {claim_id!r})")
            continue
        seen[location] = claim_id
        text = memo.get(claim_id)
        if text is not None and text != leaves[location]:
            report(
                "text",
                f"{prefix}{location}: the text differs from claim {claim_id!r} ({claim['key']}); "
                f"the file says {leaves[location][:70]!r}, the claim says {text[:70]!r}",
            )
    for location in leaves:
        if location not in seen:
            report("uncovered", f"{prefix}{location}: the text field has no claim")
    for claim_id, claim in by_id.items():
        if claim["location"] is None and claim_id not in referenced:
            report("orphan", f"claim {claim_id!r} ({claim['key']}) is not part of any sentence")
    return problems


def _render(key: str, args: dict[str, Any], catalogs: tuple[Catalog, Catalog], fail: Any) -> str | None:
    if key == JOIN_KEY:
        separator, parts = args.get("sep"), args.get("parts")
        if not isinstance(separator, str) or not isinstance(parts, list):
            fail("is a join without a separator or a list of parts")
            return None
        return separator.join(str(part) for part in parts)
    if key == CAPITALIZE_KEY:
        if not isinstance(args.get("of"), str):
            fail("capitalizes something that is not text")
            return None
        return str.capitalize(args["of"])
    agents, generator = catalogs
    catalog = generator if key.startswith(GENERATOR_PREFIX) else agents
    try:
        return catalog.render(key, args)
    except MissingMessageError:
        fail(f"uses the key {key!r}, which is not in the {catalog.language!r} catalog")
    except KeyError as exc:
        fail(f"({key}) lacks the argument {exc}")
    except (IndexError, ValueError, AttributeError) as exc:
        fail(f"({key}) cannot be rendered: {exc}")
    return None
