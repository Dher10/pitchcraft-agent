"""Language catalogs for the text-writing agents (decision D6).

The agents never hold a sentence: they ask a catalog for a message by key and fill in the
parameters. `language` is a parameter of every agent's `run`, English is the default, and
an unknown language is an error (it never falls back to English silently).

Only English ships. Spanish arrives in v2.1 as one more entry in CATALOGS; nothing in the
agents changes. A message is a str.format template; a value that is a tuple holds a list of
terms (the words a language-specific check looks for), and a dict holds a vocabulary.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from agents.messages_en import EN_MESSAGES

DEFAULT_LANGUAGE = "en"

# The starters a sentence can be about (the same slots as `data_pipeline.schema.STARTER_SLOTS`).
SUBJECT_SLOTS = ("away_starter", "home_starter")

Messages = dict[str, Any]

CATALOGS: dict[str, Messages] = {"en": EN_MESSAGES}


class Phrase(str):
    """
    A sentence that knows what it was made of (contract rule 4).

    It is the text, exactly as before (a `str`), plus the catalog `key`, the `args` it was filled
    with (a phrase given as an argument stays a phrase) and the starter `subject` it is about, when
    the caller said so. Joining phrases (`Catalog.join`) and capitalizing one (`capitalize`) give
    phrases too, with the pseudo keys `@join` and `@capitalize`. Any other string operation gives a
    plain `str`: the record is lost on purpose, so text edited by hand is found by the claims check.
    """

    key: str | None
    args: dict[str, Any]
    subject: str | None

    def __new__(
        cls,
        text: str,
        key: str | None = None,
        args: dict[str, Any] | None = None,
        subject: str | None = None,
    ) -> "Phrase":
        phrase = super().__new__(cls, text)
        phrase.key = key
        phrase.args = {} if args is None else args
        phrase.subject = subject
        return phrase

    def capitalize(self) -> "Phrase":  # type: ignore[override]
        return Phrase(str.capitalize(self), "@capitalize", {"of": self}, self.subject)


class UnknownLanguageError(ValueError):
    """The requested language has no catalog."""


class MissingMessageError(KeyError):
    """A message key is not in the catalog of the language."""


class Catalog:
    """Read access to the messages of one language."""

    def __init__(self, language: str, messages: Messages) -> None:
        self.language = language
        self._messages = messages
        self._subject: str | None = None

    def _get(self, key: str) -> Any:
        try:
            return self._messages[key]
        except KeyError:
            raise MissingMessageError(f"{key!r} is not in the {self.language!r} catalog") from None

    def __call__(self, key: str, **params: Any) -> Phrase:
        """The message `key` with its parameters filled in, as a phrase that remembers both."""

        return Phrase(self._get(key).format(**params), key, dict(params), self._subject)

    def render(self, key: str, params: dict[str, Any]) -> str:
        """The plain text of message `key` for `params` (what the claims check compares with)."""

        return self._get(key).format(**params)

    def count(self, noun: str, number: int) -> Phrase:
        """'1 walk' / '2 walks': the noun and its plural come from the catalog."""

        form = "one" if number == 1 else "other"
        key = f"count.{noun}.{form}"
        return Phrase(self._get(key).format(count=number), key, {"count": number}, self._subject)

    def join(self, separator: str, parts: Sequence[str]) -> Phrase:
        """The parts one after another: a phrase that keeps them (plain strings are values)."""

        parts = list(parts)
        return Phrase(separator.join(parts), "@join", {"sep": separator, "parts": parts}, self._subject)

    @contextmanager
    def subject(self, slot: str) -> Iterator[None]:
        """Phrases made inside the block are about the starter in `slot` (restored afterwards)."""

        if slot not in SUBJECT_SLOTS:
            raise ValueError(f"{slot!r} is not a starter slot ({', '.join(SUBJECT_SLOTS)})")
        previous = self._subject
        self._subject = slot
        try:
            yield
        finally:
            self._subject = previous

    def terms(self, key: str) -> tuple[str, ...]:
        """A list of terms (forbidden words, required words, markers) for this language."""

        return tuple(self._get(key))

    def vocabulary(self, key: str) -> dict[str, tuple[str, ...]]:
        """A vocabulary: canonical name -> the ways this language writes it."""

        return {name: tuple(forms) for name, forms in self._get(key).items()}


def catalog_for(language: str = DEFAULT_LANGUAGE) -> Catalog:
    """The catalog of `language`; raises UnknownLanguageError if there is none."""

    if language not in CATALOGS:
        known = ", ".join(sorted(CATALOGS))
        raise UnknownLanguageError(f"no catalog for language {language!r} (available: {known})")
    return Catalog(language, CATALOGS[language])
