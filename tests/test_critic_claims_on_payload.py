"""The claims of the critic about the data are checked on the payload (P0.15-D3.3a, contract rule 4).

Each family (`names`, `limited`, `command`, `scope`, `betting`) has a negative test: a payload that makes
the sentence false is broken in the data, not in the critic, and must be reported with the reason of that
family. The payloads are built by the generator (the corpus) and broken one thing at a time, so a code
appears only because of what the test changed. A sentence that reports a problem (`unsupported`) must
never be in a published file: the generator stops, and the check says so (`#published`).
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

import pytest

from agents.messages_en import EN_MESSAGES
from data_pipeline.claims import catalogs_of, verify_claims
from data_pipeline.claims_registry import _refs
from data_pipeline.contract_checks import check_contract
from tests.corpus import build, published

AWAY, HOME = "away_starter", "home_starter"
POST = {"kind": "regular_and_postseason", "through": "2026-07-03", "label": "2026 regular season and postseason through Jul 3"}


def codes(payload: dict[str, Any]) -> set[str]:
    return {violation.code for violation in check_contract(payload)}


def added(payload: dict[str, Any], edit: Callable[[dict[str, Any]], None]) -> set[str]:
    """The codes that appear when `edit(first matchup)` is applied."""

    copy = deepcopy(payload)
    edit(copy["matchups"][0])
    return codes(copy) - codes(payload)


def with_check(
    payload: dict[str, Any],
    index: int,
    claim: tuple[str, dict[str, Any]],
    evidence: tuple[str, dict[str, Any]],
    status: str | None = None,
    subject: str | None = None,
) -> dict[str, Any]:
    """A copy of the payload whose check `index` says something else, text and claims together.

    The text is rendered from the key and the arguments, so the claims still verify and the contract is
    asked about the sentence itself, not about a text that no claim explains.
    """

    copy = deepcopy(payload)
    matchup = copy["matchups"][0]
    claims = matchup["report"]["claims"]
    agents = catalogs_of(copy)[0]
    by_id = {c["id"]: c for c in claims}
    where = {f"critic_review.checks[{index}].claim", f"critic_review.checks[{index}].evidence"}
    drop: set[str] = set()
    queue = [c["id"] for c in claims if c["location"] in where]
    while queue:
        claim_id = queue.pop()
        if claim_id not in drop:
            drop.add(claim_id)
            queue.extend(_refs(by_id[claim_id]["args"].values()))
    claims[:] = [c for c in claims if c["id"] not in drop]
    for field, (key, args) in (("claim", claim), ("evidence", evidence)):
        location = f"critic_review.checks[{index}].{field}"
        claims.append({"id": f"x{index}{field}", "key": key, "args": args, "subject": subject, "location": location})
        matchup["critic_review"]["checks"][index][field] = agents.render(key, args)
    if status:
        matchup["critic_review"]["checks"][index]["status"] = status
    assert verify_claims(copy) == [], "the edited payload must keep verifiable claims"
    return copy


@pytest.fixture
def live(monkeypatch):
    return published(build(monkeypatch, "live_complete"))


@pytest.fixture
def debuts(monkeypatch):
    return published(build(monkeypatch, "live_debuts"))


def check_index(payload: dict[str, Any], claim_key: str) -> int:
    """The position of the check whose claim has this key."""

    claims = payload["matchups"][0]["report"]["claims"]
    for claim in claims:
        if claim["key"] == claim_key and claim["location"]:
            return int(claim["location"].split("[")[1].split("]")[0])
    raise AssertionError(f"no check with {claim_key}")


# --- names ----------------------------------------------------------------------------------------


def test_names_a_pitch_credited_to_a_starter_who_did_not_throw_it_is_found(live):
    """The report says Alpha can land his slider; the pitch mix now says he never threw one."""

    def edit(m):
        for row in m["charts"]["pitch_mix"]:
            if row["pitch"] == "Slider":
                row[AWAY].update(count=0, overall=0.0, vs_lhh=0.0, vs_rhh=0.0)

    new = added(live, edit)

    assert {"rule4:critic.names.claim#thrown", "rule4:critic.names.supported#thrown"} <= new


def test_names_a_pitch_the_other_starter_threw_does_not_excuse_it(live):
    """The mix still has the slider for Bravo; the sentence is Alpha's."""

    def edit(m):
        for row in m["charts"]["pitch_mix"]:
            if row["pitch"] == "Slider":
                row[AWAY].update(count=0, overall=0.0)
                row[HOME].update(count=50, overall=7.0)

    assert "rule4:critic.names.supported#thrown" in added(live, edit)


# --- limited arsenal ------------------------------------------------------------------------------


def test_limited_a_starter_whose_arsenal_is_not_limited_has_no_such_claim(debuts):
    def edit(m):
        m["starters"][AWAY]["sample"]["limited"]["arsenal"] = False

    assert "rule4:critic.limited.claim#not_limited" in added(debuts, edit)


def test_limited_the_count_in_the_evidence_is_the_count_of_the_sample(debuts):
    def edit(m):
        m["starters"][AWAY]["sample"]["arsenal"]["pitches"] = 5

    assert "rule4:critic.limited.supported#count" in added(debuts, edit)


def test_limited_the_minimum_in_the_evidence_is_the_threshold_of_the_sample(debuts):
    def edit(m):
        m["starters"][AWAY]["sample"]["thresholds"]["arsenal"] = 50

    assert "rule4:critic.limited.supported#needed" in added(debuts, edit)


def test_limited_a_pitch_named_for_a_starter_with_a_limited_arsenal_is_found(debuts, monkeypatch):
    """The words that name a pitch are data (the catalog's vocabulary): let 'limited' name a slider."""

    aliases = {name: forms for name, forms in EN_MESSAGES["critic.pitch_aliases"].items()}
    aliases["slider"] = (*aliases["slider"], "limited")
    monkeypatch.setitem(EN_MESSAGES, "critic.pitch_aliases", aliases)

    assert "rule4:critic.limited.supported#named" in codes(debuts)


# --- command --------------------------------------------------------------------------------------


def test_command_a_below_average_claim_needs_a_below_average_label(live):
    def edit(m):
        m["starters"][HOME]["pitching_profile"]["command_label"] = "Solid command"

    assert "rule4:critic.command.below_claim#label" in added(live, edit)


def test_command_the_walks_in_the_evidence_are_the_walks_of_the_sample(live):
    def edit(m):
        m["starters"][HOME]["sample"]["rates"]["walks"] += 1

    assert "rule4:critic.command.walks#walks" in added(live, edit)


def test_command_the_batters_in_the_evidence_are_the_batters_of_the_sample(live):
    def edit(m):
        m["starters"][HOME]["sample"]["rates"]["batters_faced"] += 1

    assert "rule4:critic.command.walks#batters" in added(live, edit)


def test_command_the_scope_in_the_evidence_is_the_scope_of_the_counts(live):
    def edit(m):
        m["starters"][HOME]["season_summary"]["scopes"]["counts"] = POST

    assert "rule4:critic.command.walks#scope" in added(live, edit)


def test_command_a_label_claim_needs_a_plus_or_solid_label(live):
    """Bravo's label is below average; a check that says it is supported as a solid one is false."""

    index = check_index(live, "critic.command.below_claim")
    payload = with_check(
        live,
        index,
        ("critic.command.label_claim", {"name": "Bravo Liveleft"}),
        ("critic.command.walks", {"walks": 38, "batters": 380, "scope": "2026 regular season through Jul 3"}),
        subject=HOME,
    )

    assert "rule4:critic.command.label_claim#label" in codes(payload) - codes(live)


def test_command_a_check_that_found_no_command_claim_is_false_when_the_report_makes_one(live):
    index = check_index(live, "critic.command.below_claim")
    payload = with_check(
        live,
        index,
        ("critic.command.absent_claim", {}),
        ("critic.command.absent_evidence", {}),
        status="not_present",
    )

    new = codes(payload) - codes(live)

    assert {"rule4:critic.command.absent_claim#claim_made", "rule4:critic.command.absent_evidence#claim_made"} <= new


def test_command_evidence_without_a_walk_sample_is_false_when_there_is_one(live):
    index = check_index(live, "critic.command.below_claim")
    payload = with_check(
        live,
        index,
        ("critic.command.below_claim", {"name": "Bravo Liveleft"}),
        ("critic.command.none", {}),
        subject=HOME,
    )

    assert "rule4:critic.command.none#available" in codes(payload) - codes(live)


def test_command_a_strength_score_that_the_matchup_does_not_have_is_found(live):
    """A live matchup has no strength profile (D24); a 'Command signal' sentence has nothing to cite."""

    index = check_index(live, "critic.command.below_claim")
    payload = with_check(
        live,
        index,
        ("critic.command.below_claim", {"name": "Bravo Liveleft"}),
        ("critic.command.strength", {"value": 55}),
        subject=HOME,
    )

    assert "rule4:critic.command.strength#value" in codes(payload) - codes(live)


# --- scope ----------------------------------------------------------------------------------------


def test_scope_the_same_games_for_every_group_is_false_when_a_starters_groups_differ(live):
    def edit(m):
        m["starters"][AWAY]["season_summary"]["scopes"]["counts"] = POST

    new = added(live, edit)

    assert "rule4:critic.scope.same#differs" in new


def test_scope_a_report_that_says_all_the_figures_cover_one_sample_when_they_do_not_is_found(live):
    """The report of the live matchup says 'all pitcher figures cover ...' about Alpha."""

    def edit(m):
        m["starters"][AWAY]["season_summary"]["scopes"]["counts"] = POST

    assert "rule4:critic.scope.claim#all_claimed" in added(live, edit)


def test_scope_a_report_that_does_not_say_the_samples_differ_when_they_do_is_found(live, monkeypatch):
    """Silent report: the words that mark an 'all figures' claim are the catalog's; let the report not use them."""

    monkeypatch.setitem(EN_MESSAGES, "critic.scope.all_marker", "words the report never says")

    def edit(m):
        m["starters"][AWAY]["season_summary"]["scopes"]["counts"] = POST

    assert "rule4:critic.scope.claim#unsaid" in added(live, edit)


def test_scope_a_supported_note_needs_a_starter_whose_groups_differ(live):
    index = check_index(live, "critic.scope.claim")
    payload = with_check(
        live,
        index,
        ("critic.scope.claim", {}),
        ("critic.scope.supported", {"who": "Alpha Livearm"}),
        status="supported",
    )

    new = codes(payload) - codes(live)

    assert {"rule4:critic.scope.supported#who", "rule4:critic.scope.supported#marker"} <= new


# --- betting --------------------------------------------------------------------------------------


def test_betting_a_report_with_a_term_of_the_vocabulary_does_not_have_the_absent_check(live, monkeypatch):
    """The terms are the catalog's; let one of them be a word the report says."""

    monkeypatch.setitem(EN_MESSAGES, "critic.betting_terms", (*EN_MESSAGES["critic.betting_terms"], "matchup"))

    new = codes(live)

    assert {"rule4:critic.betting.claim#language", "rule4:critic.betting.absent#language"} <= new


# --- a problem is never published -----------------------------------------------------------------

PROBLEMS = {
    "critic.names.credited": ({"name": "Alpha Livearm", "pitch": "slider"}, "critic.names.claim", {}),
    "critic.names.nobody": ({"pitch": "slider"}, "critic.names.claim", {}),
    "critic.names.unsupported": ({"problems": "slider is named"}, "critic.names.claim", {}),
    "critic.command.wrong_evidence": (
        {"name": "Alpha Livearm", "wording": "solid command", "label": "Below-average command"},
        "critic.command.wrong_claim",
        {"name": "Alpha Livearm"},
    ),
    "critic.scope.unsupported": ({"who": "Alpha Livearm"}, "critic.scope.claim", {}),
    "critic.scope.all_claimed": ({"who": "Alpha Livearm"}, "critic.scope.claim", {}),
    "critic.betting.unsupported": ({"flagged": "'bet' in headline"}, "critic.betting.claim", {}),
    "critic.limited.unsupported": (
        {"have": "5 pitches", "needed": 100, "named": "Slider"},
        "critic.limited.claim",
        {"name": "Alpha Livearm"},
    ),
}


@pytest.mark.parametrize("key", sorted(PROBLEMS))
def test_a_sentence_that_reports_a_problem_is_not_in_a_published_file(live, key):
    args, claim_key, claim_args = PROBLEMS[key]
    payload = with_check(live, 0, (claim_key, claim_args), (key, args), status="unsupported", subject=AWAY)

    assert f"rule4:{key}#published" in codes(payload)
