"""What the report says about the data, read from the payload (P0.15-D3.3a).

`data_pipeline/report_facts.py` answers, from the fields of a matchup and the text of its report, the five
questions the critic's data checks ask: which pitch is named for a starter who did not throw it, which pitch
is named for a starter with a limited arsenal, what the report claims about command, whether it says the
samples differ, and whether it uses betting language. The registry of claims uses it instead of running
the critic.

These tests hold it to the critic on the cases the critic's own tests use: where the critic finds a problem
the facts find it, where the critic finds none the facts find none. The critic is the control; if it
changes, these tests say that the contract's reading of the report must change with it.
"""

from __future__ import annotations

import pytest

from agents import critic
from agents.language import catalog_for
from data_pipeline import labels
from data_pipeline import report_facts as facts
from tests.test_critic_attribution import A, B, LIMITATION, game, report, sample
from tests.test_critic_pitch_names import GAME as PITCH_GAME

T = catalog_for("en")
AWAY, HOME = "away_starter", "home_starter"
SCOPE = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")
POST = labels.make_scope(labels.SCOPE_REGULAR_POSTSEASON, "2026-07-14")


def one_section(*sentences: str) -> dict:
    return {"headline": "h", "short_summary": [], "sections": [{"title": "t", "body": " ".join(sentences)}]}


def check(matchup: dict, rep: dict, claim: str) -> dict:
    return next(c for c in critic.run(rep, matchup)["checks"] if c["claim"] == claim)


# --- names ----------------------------------------------------------------------------------------

NAMES_OK = [
    f"{A} leans on a four-seam fastball.",
    f"{A} works off a fastball.",
    f"{B} runs a two-seam in on righties.",
    f"{B} has a cut fastball.",
    f"{B} throws two-seam fastballs and changeups.",
    "A fastball sets the tone.",
]
NAMES_BAD = [
    (f"{B} throws a slider.", HOME, "slider"),
    (f"{A} runs a two-seam in on righties.", AWAY, "sinker"),
    (f"{A} has a splitter.", AWAY, "splitter"),
    ("The knuckleball is a weapon.", None, "knuckleball"),
]


@pytest.mark.parametrize("sentence", NAMES_OK)
def test_names_a_pitch_the_starter_threw_is_not_a_problem_for_the_critic_nor_for_the_facts(sentence):
    rep = one_section(sentence)

    assert check(PITCH_GAME, rep, T("critic.names.claim"))["status"] == "supported"
    assert facts.pitches_not_thrown(PITCH_GAME, rep, T) == []


@pytest.mark.parametrize("sentence, owner, pitch", NAMES_BAD)
def test_names_a_pitch_the_starter_did_not_throw_is_a_problem_for_both(sentence, owner, pitch):
    rep = one_section(sentence)

    assert check(PITCH_GAME, rep, T("critic.names.claim"))["status"] == "unsupported"
    assert facts.pitches_not_thrown(PITCH_GAME, rep, T) == [(owner, pitch)]


def test_names_the_name_of_a_starter_is_not_a_pitch():
    """A pitcher called 'Fastball' threw no pitch by that name."""

    matchup = game()
    matchup["starters"][AWAY]["name"] = "Fastball Freddy"
    rep = one_section("Fastball Freddy takes the mound.")

    assert check(matchup, rep, T("critic.names.claim"))["status"] == "supported"
    assert facts.pitches_not_thrown(matchup, rep, T) == []


def test_names_a_section_titled_with_a_starter_holds_the_unnamed_sentences_to_him():
    matchup = PITCH_GAME
    rep = {
        "headline": "h",
        "short_summary": [],
        "sections": [{"title": f"{A} vs Team B", "body": "His sinker is the key."}],
    }

    assert check(matchup, rep, T("critic.names.claim"))["status"] == "unsupported"
    assert facts.pitches_not_thrown(matchup, rep, T) == [(AWAY, "sinker")]


# --- limited arsenal ------------------------------------------------------------------------------

LIMITED_OK = [
    [(f"{A} vs Team B", LIMITATION), (f"{B} vs Team A", f"{B} works off a four-seam and a slider.")],
    [("Arsenal scout", f"{LIMITATION} {B} mixes a slider with his four-seam.")],
    [("Arsenal scout", f"{LIMITATION} {B} and {A} both see a slider.")],
    [("Summary", "The slider matters in this game.")],
]
LIMITED_BAD = [
    [("Arsenal scout", f"{LIMITATION} {A} leans on a slider.")],
    [(f"{A} vs Team B", f"{LIMITATION} His slider is the key.")],
    [("Summary", f"{LIMITATION} {A} relies on the four-seam.")],
    [("Arsenal scout", f"{LIMITATION} {A} runs a two-seam in on righties.")],
    [("Arsenal scout", f"{LIMITATION} {A} sets hitters up with his fastball.")],
]


@pytest.mark.parametrize("sections", LIMITED_OK)
def test_limited_what_the_healthy_starter_shares_is_not_held_against_the_limited_one(sections):
    rep = report(*sections)
    verdict = check(game(), rep, T("critic.limited.claim", name=A))

    assert verdict["status"] == "supported"
    assert facts.pitches_named_for(game(), rep, AWAY, T) == []


@pytest.mark.parametrize("sections", LIMITED_BAD)
def test_limited_a_pitch_said_about_the_limited_starter_is_a_problem_for_both(sections):
    rep = report(*sections)
    verdict = check(game(), rep, T("critic.limited.claim", name=A))

    assert verdict["status"] == "unsupported"
    assert facts.pitches_named_for(game(), rep, AWAY, T) != []


# --- command --------------------------------------------------------------------------------------


def command_game() -> dict:
    matchup = game()
    matchup["starters"][AWAY]["pitching_profile"]["command_label"] = "Below-average command"
    matchup["starters"][HOME]["pitching_profile"]["command_label"] = "Solid command"
    return matchup


COMMAND_CASES = [
    (f"{A} carries below-average command risk.", "below", AWAY),
    (f"{B} has solid command.", "label", HOME),
    (f"{A} has solid command.", "wrong", AWAY),
    (f"{B} has below-average command.", "wrong", HOME),
    ("Below-average command is the risk in this game.", "below", AWAY),
    ("Command is the subject of the game.", "label", HOME),
    ("The game is about pitch mix.", "absent", None),
]


def critic_kind(matchup: dict, rep: dict) -> str:
    claims = {
        "wrong": [T("critic.command.wrong_claim", name=n) for n in (A, B)],
        "below": [T("critic.command.below_claim", name=n) for n in (A, B)],
        "label": [T("critic.command.label_claim", name=n) for n in (A, B)],
        "absent": [T("critic.command.absent_claim")],
    }
    published_claims = {c["claim"] for c in critic.run(rep, matchup)["checks"]}
    return next(kind for kind, texts in claims.items() if published_claims & set(texts))


@pytest.mark.parametrize("sentence, kind, slot", COMMAND_CASES)
def test_command_the_facts_find_what_the_critic_finds(sentence, kind, slot):
    matchup, rep = command_game(), one_section(sentence)

    assert critic_kind(matchup, rep) == kind
    assert facts.command_finding(matchup, rep, T) == (kind, slot)


# --- scope ----------------------------------------------------------------------------------------


def scope_game(differ: bool) -> dict:
    matchup = game()
    for slot in (AWAY, HOME):
        starter = matchup["starters"][slot]
        starter["sample"] = sample(150)
        starter["season_summary"] = {
            "era": "3.00",
            "whip": "1.10",
            "innings": "100.0",
            "strikeouts": 90,
            "walks": 30,
            "home_runs_allowed": 10,
            "scopes": {"season_rates": SCOPE, "counts": POST if differ and slot == AWAY else SCOPE},
        }
    return matchup


SCOPE_CASES = [
    (False, f"{A} and {B} work off four-seams.", "same", ()),
    (True, f"The figures for {A} cover different samples.", "supported", (A,)),
    (True, f"{A} works off a four-seam.", "unsupported", (A,)),
    (True, f"All pitcher figures cover the same games for {A}.", "all_claimed", (A,)),
]


@pytest.mark.parametrize("differ, sentence, kind, who", SCOPE_CASES)
def test_scope_the_facts_find_what_the_critic_finds(differ, sentence, kind, who):
    matchup, rep = scope_game(differ), one_section(sentence)
    verdict = check(matchup, rep, T("critic.scope.claim"))
    expected = {"same": "not_present", "supported": "supported"}.get(kind, "unsupported")

    assert verdict["status"] == expected
    assert facts.scope_finding(matchup, rep, T) == (kind, who)


# --- betting --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sentence, terms",
    [
        (f"{A} will win this one.", ["will win"]),
        ("Our pick for the night.", ["pick"]),
        ("A clean matchup of arsenals.", []),
    ],
)
def test_betting_the_facts_find_the_terms_the_critic_finds(sentence, terms):
    rep = one_section(sentence)
    verdict = check(PITCH_GAME, rep, T("critic.betting.claim"))

    assert (verdict["status"] == "unsupported") == bool(terms)
    assert [term for term, _ in facts.betting_terms(rep, T)] == terms


def test_betting_the_headline_and_the_summary_lines_are_read_too():
    rep = {"headline": "A lock tonight", "short_summary": ["Bet on it"], "sections": []}

    found = facts.betting_terms(rep, T)

    assert {location for _, location in found} == {"headline", "short_summary[0]"}
