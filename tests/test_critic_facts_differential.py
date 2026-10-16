"""The critic and `report_facts` read a report the same way (P0.15-D3.3b-3, owner 2026-10-13).

The registry of claims decides the conditions of the critic's data claims with `data_pipeline/report_facts.py`
and never runs the critic (D3.3a). That makes `report_facts` a second reading of the report text, written to
agree with the critic. This test measures the gap it leaves: it runs both over every report of the corpus and
of the matrix and fails if they disagree on anything the critic's data checks decide:

- which pitches a sentence names, and to which starter each sentence is attributed;
- which pitches the report credits to a starter who did not throw them (names);
- which pitch it names for a starter with a limited arsenal (limited arsenal);
- what it claims about command (wrong, below-average, plus or solid, none) and about whom;
- whether it says the groups of figures cover different samples, or claims one sample (scope);
- which words of betting language it uses, and where.

A report the generator publishes never holds a problem sentence (it stops on one), so the real reports only show
the two agreeing that there is nothing to find. To see the problems, each distinct matchup is also read with one
injected sentence at a time: every pitch and each of its aliases, said about either starter, both, or nobody, in
the section of either starter, in a neutral section and in the headline; command, scope and betting phrases. A
disagreement is a bug in one of the two readers and is fixed, not tolerated.
"""

from __future__ import annotations

from collections import Counter
from functools import cache
import json
from typing import Any

import pytest

from agents import critic
from agents.language import catalog_for
from data_pipeline import labels
from data_pipeline import report_facts as facts
from tests.matrix import outcomes
from tests.test_known_violations import corpus

T = catalog_for("en")
SLOTS = ("away_starter", "home_starter")
FACT_CLAIMS = {
    "names": T("critic.names.claim"),
    "scope": T("critic.scope.claim"),
    "betting": T("critic.betting.claim"),
}


# --- the matchups under test ------------------------------------------------------------------------


@cache
def all_matchups() -> tuple[tuple[str, dict[str, Any]], ...]:
    """(label, matchup) of every matchup of the corpus and of the 72 cases and hard cases of the matrix."""

    found: list[tuple[str, dict[str, Any]]] = []
    with pytest.MonkeyPatch.context() as monkeypatch:
        for name, payload in corpus(monkeypatch):
            found += [(f"{name}:{m['id']}", m) for m in payload["matchups"]]
    for name, outcome in outcomes().items():
        if outcome.payload:
            found += [(f"{name}:{m['id']}", m) for m in outcome.payload["matchups"]]
    return tuple(found)


def report_of(matchup: dict[str, Any]) -> dict[str, Any]:
    return {key: matchup["report"][key] for key in ("headline", "short_summary", "sections")}


def fine_world(matchup: dict[str, Any]) -> str:
    """
    What either reader looks at in a matchup besides its report, in detail: which pitches each starter threw,
    which arsenals are limited, the profile pitches and command labels, and which starters have groups of
    figures that differ. Names and strength scores are left out of it (the strength only appears in evidence text).
    """

    starters = matchup["starters"]
    mix = [(row["pitch"], [facts._was_thrown(row[slot]) for slot in SLOTS]) for row in matchup["charts"]["pitch_mix"]]
    return json.dumps(
        [
            mix,
            [(starters[slot].get("sample") or {}).get("limited", {}).get("arsenal") for slot in SLOTS],
            [
                [starters[slot]["pitching_profile"].get(key) for key in ("primary_pitch", "putaway_pitch", "command_label")]
                for slot in SLOTS
            ],
            [labels.scopes_differ(starters[slot]) for slot in SLOTS],
        ],
        sort_keys=True,
    )


def features(matchup: dict[str, Any]) -> frozenset[tuple]:
    """
    What a matchup can show the readers, as a set of facts: for each starter, together, whether his arsenal is
    limited, whether his groups of figures differ and what kind of command label he has; and how the two pitch
    sets relate (a pitch both threw, a pitch only the away or only the home starter threw).
    """

    starters = matchup["starters"]
    thrown = [facts.thrown_by(matchup, slot) for slot in SLOTS]
    found = {("pitch sets", bool(thrown[0] & thrown[1]), bool(thrown[0] - thrown[1]), bool(thrown[1] - thrown[0]))}
    for slot in SLOTS:
        starter = starters[slot]
        label = (starter["pitching_profile"].get("command_label") or "").lower()
        command = "none" if not label else "below" if labels.COMMAND_BELOW.lower() in label else "strong" if any(t in label for t in facts.COMMAND_STRONG_TERMS) else "other"
        found.add(
            (
                "starter",
                slot,
                bool((starter.get("sample") or {}).get("limited", {}).get("arsenal")),
                bool(labels.scopes_differ(starter)),
                command,
            )
        )
    return frozenset(found)


@cache
def distinct_worlds() -> dict[str, tuple[str, dict[str, Any]]]:
    """
    The few matchups the sentences are injected into: chosen, greedily, so that between them every value of every
    feature above (each combination for a starter) is present. How a pitch is named does not depend on the world, so the worlds can be few; the
    reports of every matchup are read as they are, with their own names and mixes, in the first test.
    """

    candidates = [(label, matchup, features(matchup)) for label, matchup in all_matchups()]
    wanted = frozenset().union(*(f for _, _, f in candidates))
    chosen: dict[str, tuple[str, dict[str, Any]]] = {}
    covered: frozenset[tuple] = frozenset()
    while covered != wanted:
        label, matchup, found = max(candidates, key=lambda item: len(item[2] - covered))
        chosen[label] = (label, matchup)
        covered |= found
    return chosen


@cache
def distinct_reports() -> list[tuple[str, dict[str, Any]]]:
    seen: dict[str, tuple[str, dict[str, Any]]] = {}
    for label, matchup in all_matchups():
        seen.setdefault(fine_world(matchup) + json.dumps(report_of(matchup), sort_keys=True), (label, matchup))
    return list(seen.values())


# --- what each reader says ---------------------------------------------------------------------------


def critic_checks(matchup: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    return critic.run(report, matchup)["checks"]


def one(checks: list[dict[str, str]], claim: str) -> dict[str, str]:
    found = [check for check in checks if check["claim"] == claim]
    assert len(found) == 1, f"{len(found)} checks say {claim!r}"
    return found[0]


def command_kind(checks: list[dict[str, str]], names: list[str]) -> tuple[str, str | None]:
    """The critic's command verdict as (kind, slot), read from the claim it published."""

    published = {check["claim"]: check for check in checks}
    for kind, key in (("wrong", "critic.command.wrong_claim"), ("below", "critic.command.below_claim"), ("label", "critic.command.label_claim")):
        for slot, name in zip(SLOTS, names):
            if T(key, name=name) in published:
                return kind, slot
    assert T("critic.command.absent_claim") in published, "the critic published no command check"
    return "absent", None


def disagreements(matchup: dict[str, Any], report: dict[str, Any]) -> list[str]:
    """Every way the critic and `report_facts` read `report` differently, as short sentences."""

    names = [matchup["starters"][slot]["name"] for slot in SLOTS]
    wrong: list[str] = []

    # who each sentence is about, which pitches it names, which pitches each starter threw
    owned_critic = critic._owned_sentences(report, matchup)
    owned_facts = facts.owned_sentences(matchup, report)
    if owned_critic != owned_facts:
        wrong.append(f"attribution: critic {owned_critic} / facts {owned_facts}")
    for owner, sentence in owned_critic:
        by_critic = critic._named_pitches(T, critic._without_names(sentence, names))
        by_facts = facts._named_pitches(T, facts._without_names(sentence, names))
        if by_critic != by_facts:
            wrong.append(f"pitches named in {sentence!r}: critic {sorted(by_critic)} / facts {sorted(by_facts)}")
    for slot in SLOTS:
        if critic._thrown_by(matchup, slot) != facts.thrown_by(matchup, slot):
            wrong.append(f"pitches thrown by {slot}: critic {sorted(critic._thrown_by(matchup, slot))} / facts {sorted(facts.thrown_by(matchup, slot))}")

    checks = critic_checks(matchup, report)

    # names
    problems = facts.pitches_not_thrown(matchup, report, T)
    rendered = [
        T("critic.names.credited", name=names[SLOTS.index(owner)], pitch=pitch) if owner else T("critic.names.nobody", pitch=pitch)
        for owner, pitch in problems
    ]
    want = (
        ("unsupported", T("critic.names.unsupported", problems=T.join("; ", list(dict.fromkeys(rendered)))))
        if problems
        else ("supported", T("critic.names.supported"))
    )
    got = one(checks, FACT_CLAIMS["names"])
    if (got["status"], got["evidence"]) != want:
        wrong.append(f"names: critic {(got['status'], got['evidence'])} / facts {want}")

    # limited arsenal: the critic checks it only for a starter whose arsenal is limited
    for slot, name in zip(SLOTS, names):
        sample = matchup["starters"][slot].get("sample")
        claim = T("critic.limited.claim", name=name)
        published = [check for check in checks if check["claim"] == claim]
        if not (sample and sample["limited"]["arsenal"]):
            if published:
                wrong.append(f"limited: the critic checks {name} whose arsenal is not limited")
            continue
        named = facts.pitches_named_for(matchup, report, slot, T)
        pitches = sample["arsenal"]["pitches"]
        needed = sample["thresholds"]["arsenal"]
        if pitches is None:  # an unknown count is not "none on record" (F14)
            want = (
                ("unsupported", T("critic.limited.unsupported_unavailable", needed=needed, named=T.join(", ", named)))
                if named
                else ("supported", T("critic.limited.supported_unavailable", needed=needed))
            )
        else:
            have = T("critic.limited.pitches", count=pitches) if pitches else T("critic.limited.none")
            want = (
                ("unsupported", T("critic.limited.unsupported", have=have, needed=needed, named=T.join(", ", named)))
                if named
                else ("supported", T("critic.limited.supported", have=have.capitalize(), needed=needed))
            )
        if len(published) != 1 or (published[0]["status"], published[0]["evidence"]) != want:
            wrong.append(f"limited arsenal of {name}: critic {[(c['status'], c['evidence']) for c in published]} / facts {want}")

    # command
    want_kind = facts.command_finding(matchup, report, T)
    got_kind = command_kind(checks, names)
    if want_kind != got_kind:
        wrong.append(f"command: critic {got_kind} / facts {want_kind}")

    # scope
    kind, who = facts.scope_finding(matchup, report, T)
    joined = T.join(", ", list(who))
    want = {
        "same": ("not_present", T("critic.scope.same")),
        "all_claimed": ("unsupported", T("critic.scope.all_claimed", who=joined)),
        "supported": ("supported", T("critic.scope.supported", who=joined)),
        "unsupported": ("unsupported", T("critic.scope.unsupported", who=joined)),
    }[kind]
    got = one(checks, FACT_CLAIMS["scope"])
    if (got["status"], got["evidence"]) != want:
        wrong.append(f"scope: critic {(got['status'], got['evidence'])} / facts {want}")

    # betting
    terms = facts.betting_terms(report, T)
    want = (
        ("unsupported", T("critic.betting.unsupported", flagged=T.join(", ", [T("critic.betting.item", term=t, location=w) for t, w in terms])))
        if terms
        else ("not_present", T("critic.betting.absent"))
    )
    got = one(checks, FACT_CLAIMS["betting"])
    if (got["status"], got["evidence"]) != want:
        wrong.append(f"betting: critic {(got['status'], got['evidence'])} / facts {want}")
    return wrong


def verdicts(matchup: dict[str, Any], report: dict[str, Any]) -> set[str]:
    """Which branches of the critic's data checks a report reaches, for the coverage test."""

    names = [matchup["starters"][slot]["name"] for slot in SLOTS]
    checks = critic_checks(matchup, report)
    scope = one(checks, FACT_CLAIMS["scope"])
    all_claimed = scope["evidence"] == T("critic.scope.all_claimed", who=scope["evidence"].split("figures for ")[-1].split(" cover")[0])
    found = {f"names:{one(checks, FACT_CLAIMS['names'])['status']}", f"scope:{scope['status']}{':all_claimed' if all_claimed else ''}"}
    found.add(f"betting:{one(checks, FACT_CLAIMS['betting'])['status']}")
    found.add(f"command:{command_kind(checks, names)[0]}")
    for slot, name in zip(SLOTS, names):
        sample = matchup["starters"][slot].get("sample")
        if sample and sample["limited"]["arsenal"]:
            found.add(f"limited:{one(checks, T('critic.limited.claim', name=name))['status']}")
    return found


# --- the injected sentences --------------------------------------------------------------------------

PITCH_FORMS = [form for forms in catalog_for("en").vocabulary("critic.pitch_aliases").values() for form in forms] + [
    T("critic.generic_fastball")
]
COMMAND_PHRASES = ("below-average command", "solid command", "plus command", "average command")
PLACEMENTS = ("section of away", "section of home", "neutral section", "headline")
NEUTRAL_AND_OWN = ("section of away", "neutral section")


def place(report: dict[str, Any], placement: str, text: str, names: list[str]) -> dict[str, Any]:
    out = {"headline": report["headline"], "short_summary": list(report["short_summary"]), "sections": list(report["sections"])}
    if placement == "section of away":
        out["sections"].append({"title": f"{names[0]} outlook", "body": text})
    elif placement == "section of home":
        out["sections"].append({"title": f"{names[1]} outlook", "body": text})
    elif placement == "neutral section":
        out["sections"].append({"title": "Notes", "body": text})
    elif placement == "bullet":
        out["sections"].append({"title": "Notes", "body": "", "bullets": [text]})
    elif placement == "short summary":
        out["short_summary"].append(text)
    else:
        out["headline"] = text
    return out


def sentences(kind: str, names: list[str], salt: int | None = None):
    """
    (label, subject, text, placements) for every injected sentence of one kind. A sentence is said about
    either starter, about both, or about nobody; the first form of each pitch goes to every place, its aliases
    to the section of the away starter and the neutral section (they only change how the pitch is named).

    With a `salt`, each world reads a rotating part of the forms (half of the pitches, a third of the aliases,
    half of the betting terms): how a pitch is named does not depend on the world, so the forms spread over
    the worlds and every one is read in several of them, while the cost stays within the time of the suite.
    """

    a, b = names
    marker, all_marker = T("critic.scope.marker"), T("critic.scope.all_marker")
    if kind == "pitch":
        canonical = {forms[0] for forms in T.vocabulary("critic.pitch_aliases").values()} | {T("critic.generic_fastball")}
        for position, form in enumerate(PITCH_FORMS):
            wide = form in canonical
            if salt is not None and (position + salt) % (2 if wide else 3):
                continue
            yield form, "A", f"{a} throws a {form}.", PLACEMENTS if wide else NEUTRAL_AND_OWN
            yield form, "B", f"{b} throws a {form}.", PLACEMENTS if wide else ("section of away",)
            yield form, "nobody", f"The {form} sets the tone.", PLACEMENTS if wide else NEUTRAL_AND_OWN
            yield form, "both", f"{a} and {b} both throw a {form}.", ("neutral section",)
    elif kind == "command":
        for phrase in COMMAND_PHRASES:
            yield phrase, "A", f"{a} has {phrase}.", PLACEMENTS
            yield phrase, "B", f"{b} has {phrase}.", PLACEMENTS
            yield phrase, "nobody", f"The game turns on {phrase}.", PLACEMENTS
            yield phrase, "both", f"{a} and {b} differ in {phrase}.", ("neutral section",)
        yield "bare command word", "nobody", "Command is the subject of the game.", PLACEMENTS
    elif kind == "scope":
        for label, sentence in (("marker", f"{{}} figures cover {marker}."), ("all marker", f"{all_marker.capitalize()} the same games for {{}}.")):
            yield label, "A", sentence.format(a), PLACEMENTS
            yield label, "B", sentence.format(b), PLACEMENTS
            yield label, "nobody", sentence.format("this starter"), PLACEMENTS
            yield label, "both", sentence.format(f"{a} and {b}"), ("neutral section",)
    else:  # betting: where it sits matters (the critic reports the location)
        for position, term in enumerate(T.terms("critic.betting_terms")):
            if salt is not None and (position + salt) % 2:
                continue
            yield term, "nobody", f"This one is a {term} tonight.", ("headline", "short summary", "neutral section", "bullet")


def confidence_sentences(matchup: dict[str, Any]) -> list[tuple[str, str]]:
    """
    (label, text) of every sentence the confidence note is built from (P0.15-D2.1b), in every state of its
    parts and whether or not the matchup is in that state: the readers must not see a claim about a pitch, a
    command, a scope or a bet in them, wherever they are said.
    """

    away, home = (matchup["starters"][slot]["name"] for slot in SLOTS)
    team_a, team_h = (matchup["teams"][side]["name"] for side in ("away", "home"))
    items = [T("writer.confidence.item.pitchers"), T("writer.confidence.item.pitch_data"), T("writer.confidence.item.offense")]
    return [
        ("snapshot, one item", T("writer.confidence.snapshot", items=items[0])),
        ("snapshot, two items", T("writer.confidence.snapshot", items=T("writer.confidence.list_two", first=items[0], second=items[1]))),
        (
            "snapshot, three items",
            T("writer.confidence.snapshot", items=T("writer.confidence.list_three", first=items[0], second=items[1], third=items[2])),
        ),
        ("pitch data one (away)", T("writer.confidence.pitch_data.one", with_data=away, without_data=home)),
        ("pitch data one (home)", T("writer.confidence.pitch_data.one", with_data=home, without_data=away)),
        ("pitch data none", T("writer.confidence.pitch_data.none")),
        ("offense one (away)", T("writer.confidence.offense.one", with_split=team_a, without_split=team_h)),
        ("offense one (home)", T("writer.confidence.offense.one", with_split=team_h, without_split=team_a)),
        ("offense none", T("writer.confidence.offense.none")),
        ("lineups", T("writer.confidence.lineups")),
        ("unnamed lead pitch", T("analyst.data.arsenal_unnamed", name=away)),
        ("no contrast, unnamed", T("writer.arsenal.no_contrast_unnamed")),
        ("unavailable pitch count", T("analyst.have.pitches_unavailable")),
        ("unavailable batters faced", T("analyst.have.batters_unavailable")),
        ("critic: pitch count not available", T("critic.limited.supported_unavailable", needed=100)),
    ]


def variants(matchup: dict[str, Any], salt: int | None = None):
    """(label, report) for each injected sentence in each place it can sit (all of them without a `salt`)."""

    names = [matchup["starters"][slot]["name"] for slot in SLOTS]
    # A real report of a starter whose groups differ already says so; to see what the readers do when it does
    # not, the scope sentences go onto a bare report. The rest go onto the real one.
    bare = {"headline": "Matchup notes", "short_summary": [], "sections": [{"title": "Notes", "body": "Nothing else is said."}]}
    yield "bare report", bare
    for kind in ("pitch", "command", "scope", "betting"):
        base = bare if kind == "scope" else report_of(matchup)
        for label, subject, text, placements in sentences(kind, names, salt):
            for placement in placements:
                yield f"{kind} {label!r} about {subject} in {placement}", place(base, placement, text, names)
    for label, text in confidence_sentences(matchup):
        for placement in (*PLACEMENTS, "bullet", "short summary"):
            yield f"confidence {label!r} in {placement}", place(report_of(matchup), placement, text, names)
    # The critic's own note names betting ("bet" is one of the terms the scan looks for): were it said inside a
    # report, both readers must flag it the same way (P0.15-D2.1c).
    for placement in (*PLACEMENTS, "bullet", "short summary"):
        yield f"critic note in {placement}", place(report_of(matchup), placement, T("critic.note.no_betting"), names)


def awkward(matchup: dict[str, Any]):
    """
    (label, matchup, report) for the texts that tell the readers apart if anything does: a starter whose name is
    a pitch, sentences glued together or split by a newline, the two names in a title or in different cases,
    several claims in one body, a bullet that names nobody inside a starter's section.
    """

    names = [matchup["starters"][slot]["name"] for slot in SLOTS]
    a, b = names
    base = report_of(matchup)
    sections = lambda *pairs: {**base, "sections": [{"title": t, "body": body} for t, body in pairs]}  # noqa: E731
    yield "two claims in one body", matchup, sections((f"{a} outlook", f"{a} throws a slider. {b} has solid command. The curveball matters."))
    yield "no space after the period", matchup, sections(("Notes", f"{a} throws a slider.{b} has below-average command."))
    yield "a newline between sentences", matchup, sections(("Notes", f"{a} has plus command.\n{b} throws a splitter."))
    yield "both names in the title", matchup, sections((f"{a} vs {b}", "A sinker and below-average command decide it."))
    yield "title names one, body names the other", matchup, sections((f"{a} outlook", f"{b} throws a cutter and has solid command."))
    yield "name in lower case", matchup, sections(("Notes", f"{a.lower()} throws a knuckleball."))
    yield "a pitch inside a longer word", matchup, sections(("Notes", "The sliders and the curveballs and the changeups decide it."))
    yield "an alias in the headline", matchup, {**base, "headline": f"{a} brings a two-seam and a cut fastball"}
    yield "a bullet in a starter's section", matchup, {**base, "sections": [{"title": f"{b} outlook", "body": "", "bullets": ["His slider is the key.", "Below-average command can hurt."]}]}
    for pitch_name in ("Fastball", "Slider", "Changeup"):
        renamed = json.loads(json.dumps(matchup))
        renamed["starters"]["away_starter"]["name"] = f"{pitch_name} Freddy"
        yield f"a starter named {pitch_name} Freddy", renamed, sections(
            ("Notes", f"{pitch_name} Freddy takes the mound. {pitch_name} Freddy throws a splitter."),
            (f"{pitch_name} Freddy outlook", "His fastball is the key."),
        )


# --- the tests ---------------------------------------------------------------------------------------


def test_the_two_readers_agree_on_every_report_the_corpus_and_the_matrix_publish():
    wrong = []
    for label, matchup in distinct_reports():
        wrong += [f"{label}: {item}" for item in disagreements(matchup, report_of(matchup))]

    assert wrong == [], "\n".join(wrong[:20])


@pytest.mark.parametrize("position", range(len(distinct_worlds())), ids=lambda position: f"world-{position}")
def test_the_two_readers_agree_on_one_injected_sentence_at_a_time(position):
    label, matchup = list(distinct_worlds().values())[position]
    wrong = []
    for variant, report in variants(matchup, salt=position):
        wrong += [f"{label} / {variant}: {item}" for item in disagreements(matchup, report)]
    for variant, changed, report in awkward(matchup):
        wrong += [f"{label} / {variant}: {item}" for item in disagreements(changed, report)]

    assert wrong == [], f"{len(wrong)} disagreement(s):\n" + "\n".join(wrong[:20])


def few_worlds() -> list[tuple[str, dict[str, Any]]]:
    """A healthy pair, a limited arsenal, groups that differ and a below-average command: enough to reach every branch."""

    picked: dict[str, tuple[str, dict[str, Any]]] = {}
    for label, matchup in distinct_worlds().values():
        starters = matchup["starters"].values()
        kinds = [
            "limited" if any((s.get("sample") or {}).get("limited", {}).get("arsenal") for s in starters) else None,
            "differ" if any(labels.scopes_differ(s) for s in starters) else None,
            "below" if any(s["pitching_profile"].get("command_label") == labels.COMMAND_BELOW for s in starters) else None,
            "healthy",
        ]
        for kind in kinds:
            if kind:
                picked.setdefault(kind, (label, matchup))
    return list(picked.values())


def test_the_differential_reaches_every_branch_of_the_critics_data_checks():
    """Control: an agreement on branches nobody reaches would prove nothing."""

    reached: Counter[str] = Counter()
    for _, matchup in few_worlds():
        for _, report in variants(matchup):
            reached.update(verdicts(matchup, report))

    for want in (
        "names:supported", "names:unsupported",
        "limited:supported", "limited:unsupported",
        "command:absent", "command:wrong", "command:below", "command:label",
        "scope:not_present", "scope:supported", "scope:unsupported", "scope:unsupported:all_claimed",
        "betting:not_present", "betting:unsupported",
    ):
        assert reached[want] > 0, f"no report reached {want}: {dict(reached)}"


def test_the_differential_sees_a_disagreement_when_there_is_one(monkeypatch):
    """Control: with one reader made wrong the comparison is not empty (a differential that cannot fail is worth nothing)."""

    label, matchup = next(iter(distinct_worlds().values()))
    injected = next(report for name, report in variants(matchup) if name.startswith("pitch 'slider' about A in section of away"))
    assert disagreements(matchup, injected) == []

    monkeypatch.setattr(facts, "_named_pitches", lambda catalog, sentence: set())
    assert any("pitches named" in item for item in disagreements(matchup, injected))
    monkeypatch.undo()
    monkeypatch.setattr(facts, "betting_terms", lambda report, catalog: [])
    betting = next(report for name, report in variants(matchup) if name.startswith("betting 'bet'"))
    assert any(item.startswith("betting") for item in disagreements(matchup, betting))


def test_the_worlds_cover_the_cases_that_have_been_a_problem():
    """Control: a limited arsenal, groups that differ and a pair that shares a pitch are all among the matchups read."""

    limited = differ = shared = 0
    for _, matchup in distinct_worlds().values():
        starters = matchup["starters"]
        limited += any((s.get("sample") or {}).get("limited", {}).get("arsenal") for s in starters.values())
        differ += any(labels.scopes_differ(s) for s in starters.values())
        thrown = [facts.thrown_by(matchup, slot) for slot in SLOTS]
        shared += bool(thrown[0] & thrown[1])

    assert limited and differ and shared
    assert len(distinct_worlds()) >= 6


def test_the_sentences_of_the_confidence_note_are_no_claim_for_either_reader():
    """A sentence of the note says nothing about a pitch, a command, a scope or a bet, wherever it sits."""

    read = 0
    for label, matchup in few_worlds():
        base = verdicts(matchup, report_of(matchup))
        for variant, report in variants(matchup):
            if variant.startswith("confidence "):
                assert verdicts(matchup, report) == base, f"{label} / {variant}"
                read += 1

    assert read >= 10 * 6 * len(few_worlds())  # ten sentences, six places, every world


def test_the_critics_own_note_is_flagged_by_both_readers_when_it_sits_in_a_report():
    """It names betting, so inside a report the scan finds it: the two readers must say so together."""

    for label, matchup in few_worlds():
        for variant, report in variants(matchup):
            if variant.startswith("critic note"):
                assert disagreements(matchup, report) == [], f"{label} / {variant}"
                assert facts.betting_terms(report, T), f"{label} / {variant}"


def test_the_two_readers_agree_when_a_share_is_null():
    """P0.15-D2.2c: the critic and `report_facts` read `overall`; a null is a pitch not thrown for both, with or without raw counts."""

    from tests.matrix import hard_outcome

    matchup = json.loads(json.dumps(hard_outcome("home_debut_away_healthy").matchup))
    nulled = 0
    for row in matchup["charts"]["pitch_mix"]:
        for slot in SLOTS:
            if row[slot]["total"] == 0:
                row[slot]["overall"] = None
                nulled += 1
    assert nulled > 0

    assert disagreements(matchup, report_of(matchup)) == []

    for row in matchup["charts"]["pitch_mix"]:  # the demo's shape: no raw counts, only the share
        for slot in SLOTS:
            row[slot].pop("count", None)
            row[slot].pop("total", None)
    assert disagreements(matchup, report_of(matchup)) == []
