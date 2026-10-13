"""A sentence knows what it is made of (P0.15-D3.1, contract rule 4).

`Catalog.__call__` returns a `Phrase`: the same text as before (it is a `str`), plus the catalog key,
the arguments it was filled with and, when the caller says so, the starter it is about. Joins and
capitalization of phrases are phrases too, so a sentence made of other sentences keeps its parts and
no text reaches the report without a record of where it came from.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from agents.language import Phrase, catalog_for

t = catalog_for("en")


def test_a_message_is_a_phrase_that_equals_its_text():
    phrase = t("analyst.watch.ahead", name="Alpha Livearm")

    assert isinstance(phrase, Phrase)
    assert phrase == "Can Alpha Livearm stay ahead of hitters early in counts?"
    assert (phrase.key, phrase.args, phrase.subject) == (
        "analyst.watch.ahead",
        {"name": "Alpha Livearm"},
        None,
    )
    assert json.dumps(phrase) == json.dumps(str(phrase))


@pytest.mark.parametrize("number, form, text", [(1, "one", "1 walk"), (2, "other", "2 walks"), (0, "other", "0 walks")])
def test_a_plural_is_a_phrase_with_the_full_catalog_key(number, form, text):
    phrase = t.count("walk", number)

    assert isinstance(phrase, Phrase) and phrase == text
    assert (phrase.key, phrase.args) == (f"count.walk.{form}", {"count": number})


def test_a_phrase_given_as_an_argument_is_kept_by_reference():
    inner = t.count("home_run", 3)

    outer = t("analyst.data.contact", name="Alpha Livearm", home_runs=inner, batters=210)

    assert outer == (
        "Alpha Livearm has allowed 3 home runs over 210 batters faced; "
        "no contact-risk rating is given because a home-run rate needs a far larger sample."
    )
    assert outer.args["home_runs"] is inner


def test_a_join_of_phrases_is_a_phrase_that_keeps_its_parts():
    first = t("analyst.read.he")
    last = t("writer.arsenal.no_contrast")

    joined = t.join(" ", [first, "a plain value", last])

    assert isinstance(joined, Phrase)
    assert joined == f"{first} a plain value {last}"
    assert joined.key == "@join"
    assert joined.args["sep"] == " "
    assert joined.args["parts"][0] is first and joined.args["parts"][2] is last
    assert joined.args["parts"][1] == "a plain value"


def test_an_empty_join_is_an_empty_phrase():
    joined = t.join("; ", [])

    assert isinstance(joined, Phrase) and joined == ""


def test_capitalizing_a_phrase_keeps_the_phrase():
    have = t("critic.limited.pitches", count=12)

    shown = have.capitalize()

    assert shown == "12 pitches".capitalize() and isinstance(shown, Phrase)
    assert (shown.key, shown.args) == ("@capitalize", {"of": have})
    assert shown.args["of"] is have


def test_any_other_string_operation_gives_a_plain_string():
    # The identity of a phrase is lost the moment the text is edited; the claims check then finds a
    # plain string where a phrase must be, so editing report text by hand cannot go unnoticed.
    phrase = t("analyst.watch.deep")

    for edited in (phrase.lower(), phrase.rstrip("?"), phrase[:5], phrase + "!", f"{phrase}"):
        assert type(edited) is str


def test_the_subject_is_set_by_the_caller_and_restored():
    with t.subject("away_starter"):
        inside = t("analyst.read.he")
        with t.subject("home_starter"):
            nested = t("analyst.read.he")
            joined = t.join(" ", [nested])
        again = t("analyst.read.he")
    outside = t("analyst.read.he")

    assert [p.subject for p in (inside, nested, joined, again, outside)] == [
        "away_starter",
        "home_starter",
        "home_starter",
        "away_starter",
        None,
    ]


def test_the_subject_is_restored_when_the_block_raises():
    with pytest.raises(RuntimeError):
        with t.subject("away_starter"):
            raise RuntimeError("boom")

    assert t("analyst.read.he").subject is None


def test_only_a_starter_slot_can_be_a_subject():
    with pytest.raises(ValueError):
        with t.subject("the_umpire"):
            pass


def test_a_deep_copy_keeps_what_a_phrase_is_made_of():
    inner = t.count("walk", 2)
    with t.subject("home_starter"):
        phrase = t("grader.plan.walks", primary="sinker", putaway="slider", walks=inner)

    copy = deepcopy(phrase)

    assert type(copy) is Phrase and copy == phrase
    assert (copy.key, copy.subject) == ("grader.plan.walks", "home_starter")
    assert copy.args["walks"] == inner and isinstance(copy.args["walks"], Phrase)
    assert copy.args["walks"].key == "count.walk.other"


def test_the_text_of_an_unknown_key_still_fails_loudly():
    from agents.language import MissingMessageError

    with pytest.raises(MissingMessageError):
        t("analyst.no_such_message")
