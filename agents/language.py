"""Language catalogs for the text-writing agents (decision D6).

The agents never hold a sentence: they ask a catalog for a message by key and fill in the
parameters. `language` is a parameter of every agent's `run`, English is the default, and
an unknown language is an error (it never falls back to English silently).

Only English ships. Spanish arrives in v2.1 as one more entry in CATALOGS; nothing in the
agents changes. A message is a str.format template; a value that is a tuple holds a list of
terms (the words a language-specific check looks for), and a dict holds a vocabulary.
"""

from __future__ import annotations

from typing import Any

from agents.messages_en import EN_MESSAGES

DEFAULT_LANGUAGE = "en"

Messages = dict[str, Any]

CATALOGS: dict[str, Messages] = {"en": EN_MESSAGES}


class UnknownLanguageError(ValueError):
    """The requested language has no catalog."""


class MissingMessageError(KeyError):
    """A message key is not in the catalog of the language."""


class Catalog:
    """Read access to the messages of one language."""

    def __init__(self, language: str, messages: Messages) -> None:
        self.language = language
        self._messages = messages

    def _get(self, key: str) -> Any:
        try:
            return self._messages[key]
        except KeyError:
            raise MissingMessageError(f"{key!r} is not in the {self.language!r} catalog") from None

    def __call__(self, key: str, **params: Any) -> str:
        """The message `key` with its parameters filled in."""

        return self._get(key).format(**params)

    def count(self, noun: str, number: int) -> str:
        """'1 walk' / '2 walks': the noun and its plural come from the catalog."""

        form = "one" if number == 1 else "other"
        return self._get(f"count.{noun}.{form}").format(count=number)

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
