"""The critic holds each claim to the starter it is about, not to the whole report (QA2-02).

QA2-02 probe: a limited starter (40 pitches) and a healthy one (150) both throw a Four-seam.
The check of the limited arsenal searched the entire report for his pitch names, found the
healthy starter's legitimate Four-seam sentence and blocked a valid game. A claim now belongs
to a starter when its sentence names only him, or when it has no name and sits in the section
titled with his name. A sentence that names both, or nobody, can only be held to a pitch the
other starter did not throw (the known limit of reading free text).
"""

from __future__ import annotations

from datetime import date
import json

import pytest

from agents import critic
from agents.language import catalog_for
from data_pipeline import demo_inputs, labels
from data_pipeline import generate_demo_json as gdj
from data_pipeline.fetchers import cache_manager
from data_pipeline.fetchers import live_pipeline as lp
from data_pipeline.validators import validate_payload
from tests.test_critic_pitch_names import A, B, matchup as pitch_matchup
from tests.test_live_sample_pipeline import API_STATS, frame, route
from tests.test_live_starters_no_demo_fields import _fake_live_game

T = catalog_for("en")
SCOPE = labels.make_scope(labels.SCOPE_REGULAR, "2026-07-14")


def sample(pitches: int) -> dict:
    return labels.build_sample(
        pitches=pitches,
        arsenal_scope=SCOPE,
        batters_faced=400,
        strikeouts=90,
        walks=30,
        home_runs=10,
        rates_source="mlb_api",
        rates_scope=SCOPE,
    )


def game(limited: str = "away_starter") -> dict:
    """A is the away starter, B the home one; both throw a Four-seam and a Slider."""

    base = pitch_matchup(
        away={"Four-seam": 60, "Slider": 40},
        home={"Four-seam": 55, "Slider": 30, "Changeup": 15},
    )
    for slot in ("away_starter", "home_starter"):
        base["starters"][slot]["sample"] = sample(40 if slot == limited else 150)
    return base


def report(*sections: tuple[str, str]) -> dict:
    return {
        "headline": "A headline",
        "short_summary": [],
        "sections": [{"title": title, "body": body} for title, body in sections],
    }


def limited_check(matchup: dict, rep: dict, name: str = A) -> dict:
    claim = T("critic.limited.claim", name=name)
    return next(c for c in critic.run(rep, matchup)["checks"] if c["claim"] == claim)


LIMITATION = f"{A} has only 40 pitches on record, so this report makes no arsenal claim for him."


# --- what the healthy starter shares with him is not held against the limited one ---------------------


def test_the_qa_probe_a_shared_pitch_in_the_healthy_starters_section_is_not_a_claim_about_the_limited_one():
    rep = report(
        (f"{A} vs Team B", LIMITATION),
        (f"{B} vs Team A", f"{B} works off a four-seam and a slider."),
    )

    assert limited_check(game(), rep)["status"] == "supported"


def test_a_shared_pitch_in_a_sentence_that_names_only_the_healthy_starter_is_fine_anywhere():
    rep = report(("Arsenal scout", f"{LIMITATION} {B} mixes a slider with his four-seam."))

    assert limited_check(game(), rep)["status"] == "supported"


def test_the_mirror_case_a_limited_home_starter_and_a_healthy_away_starter():
    rep = report(
        (f"{A} vs Team B", f"{A} works off a four-seam and a slider."),
        (f"{B} vs Team A", f"{B} has only 40 pitches on record."),
    )

    assert limited_check(game("home_starter"), rep, name=B)["status"] == "supported"


def test_a_sentence_naming_both_starters_and_a_shared_pitch_cannot_be_held_to_the_limited_one():
    rep = report(("Arsenal scout", f"{LIMITATION} {B} and {A} both see a slider."))

    assert limited_check(game(), rep)["status"] == "supported"


def test_a_pitch_in_an_unattributed_sentence_that_the_healthy_starter_throws_too_is_not_attributed():
    rep = report(("Summary", "The slider matters in this game."))

    assert limited_check(game(), rep)["status"] == "supported"


# --- what is said about him is still held to the limitation --------------------------------------------


@pytest.mark.parametrize(
    "title, text",
    [
        ("Arsenal scout", f"{A} leans on a slider."),  # a sentence that names only him
        (f"{A} vs Team B", "His slider is the key."),  # no name, but his section
        ("Summary", f"{A} relies on the four-seam."),
        ("Arsenal scout", f"{A} runs a two-seam in on righties."),  # an alias of a pitch
        ("Arsenal scout", f"{A} sets hitters up with his fastball."),  # the generic word
    ],
)
def test_a_pitch_said_about_the_limited_starter_is_unsupported(title, text):
    rep = report((title, f"{LIMITATION} {text}"))

    check = limited_check(game(), rep)

    assert check["status"] == "unsupported", text
    assert "Only 40 pitches" in check["evidence"]


def test_a_pitch_only_he_throws_in_an_unattributed_sentence_is_still_unsupported():
    # The healthy starter does not throw a curveball; nobody else can own the sentence.
    matchup = pitch_matchup(
        away={"Four-seam": 60, "Curveball": 40}, home={"Four-seam": 70, "Slider": 30}
    )
    matchup["starters"]["away_starter"]["sample"] = sample(40)
    matchup["starters"]["home_starter"]["sample"] = sample(150)
    rep = report(("Summary", f"{LIMITATION} The curveball is the key."))

    assert limited_check(matchup, rep)["status"] == "unsupported"


def test_a_sentence_in_the_healthy_section_naming_the_limited_one_with_a_pitch_is_his_claim():
    rep = report((f"{B} vs Team A", f"{A} throws a slider here."))

    assert limited_check(game(), rep)["status"] == "unsupported"


# --- the whole game, through the real fetchers and the real generator ----------------------------------


@pytest.fixture()
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(cache_manager, "PROCESSED_DIR", tmp_path / "processed")
    monkeypatch.setattr(lp, "_run_errors", [])
    monkeypatch.setattr(lp, "season_dates", lambda season: (date(season, 3, 25), date(season, 9, 27)))


def live_payload(monkeypatch, away_pitches, home_pitches):
    route(monkeypatch, [("/stats?", API_STATS)])

    def fetch(pitcher_id, name, plain, sliders):
        monkeypatch.setattr(
            lp,
            "statcast_pitcher",
            lambda *a, **k: frame(n_plain=plain, extra_rows=[{"pitch_type": "SL"}] * sliders),
        )
        return lp.fetch_pitcher_statcast(pitcher_id, name, as_of="2026-07-14")

    away = fetch(11, "Limited Fastball", *away_pitches)
    home = fetch(22, "Healthy Fastball", *home_pitches)
    template = next(
        m for m in demo_inputs.build_demo_payload()["matchups"] if m["id"] == "matchup_001"
    )
    live = _fake_live_game(template)
    live.update(
        away_starter=away,
        home_starter=home,
        combined_charts={
            "pitch_mix": lp._combine_pitch_mix(away, home),
            "velocity_by_pitch": lp._combine_velocity(away, home),
        },
    )
    monkeypatch.setattr(
        gdj, "_live", {"fetched_date": "2026-07-15", "as_of": "2026-07-14", "live_games": [live]}
    )
    monkeypatch.setattr(
        gdj, "_live_status", {"mode": "fetched_snapshot", "reason": "Live run ok", "live_run": None}
    )
    return gdj.build_payload()


def test_the_qa_probe_a_limited_and_a_healthy_starter_sharing_four_seam_and_slider_publish(
    isolated, monkeypatch
):
    # Limited: 28 four-seams + 12 sliders = 40 pitches. Healthy: 100 + 50 = 150. Both throw both.
    payload = live_payload(monkeypatch, (28, 12), (100, 50))

    live = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    assert live["starters"]["away_starter"]["sample"]["limited"]["arsenal"] is True
    assert live["starters"]["home_starter"]["sample"]["limited"]["arsenal"] is False
    assert {row["pitch"] for row in live["charts"]["pitch_mix"]} == {"Four-seam", "Slider"}
    statuses = {check["status"] for check in live["critic_review"]["checks"]}
    assert "unsupported" not in statuses
    assert "four-seam" in json.dumps(live["report"]).lower()  # the healthy starter's own sentence
    assert all(check.passed for check in validate_payload(payload))


def test_the_same_game_still_stops_if_the_limited_starters_section_describes_his_pitch(
    isolated, monkeypatch
):
    payload = live_payload(monkeypatch, (28, 12), (100, 50))
    live = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    away = live["starters"]["away_starter"]["name"]
    rep = json.loads(json.dumps(live["report"]))
    rep["sections"][1]["body"] += " His slider is his put-away pitch."  # the away starter's section
    assert away in rep["sections"][1]["title"]

    review = critic.run(rep, live)

    check = next(c for c in review["checks"] if c["claim"] == T("critic.limited.claim", name=away))
    assert check["status"] == "unsupported"


# --- command claims are about a starter too -------------------------------------------------------------


def command_game(away_label: str, home_label: str) -> dict:
    base = game("none")
    base["starters"]["away_starter"]["pitching_profile"]["command_label"] = away_label
    base["starters"]["home_starter"]["pitching_profile"]["command_label"] = home_label
    return base


def command_check(matchup: dict, rep: dict) -> dict:
    claims = {
        T("critic.command.absent_claim"),
        *(
            T(key, name=name)
            for key in ("critic.command.below_claim", "critic.command.label_claim", "critic.command.wrong_claim")
            for name in (A, B)
        ),
    }
    return next(c for c in critic.run(rep, matchup)["checks"] if c["claim"] in claims)


BELOW, SOLID, AVERAGE = labels.COMMAND_BELOW, labels.COMMAND_SOLID, labels.COMMAND_AVERAGE


def test_a_below_average_claim_about_the_starter_who_has_that_label_is_supported():
    rep = report(("Summary", f"{A} shows below-average command."))

    check = command_check(command_game(BELOW, SOLID), rep)

    assert check["status"] == "supported" and A in check["claim"]


def test_a_below_average_claim_about_the_wrong_starter_is_unsupported_even_if_the_other_has_it():
    # The whole-report scan found "below-average command" and the first below-average starter (A).
    rep = report(("Summary", f"{B} shows below-average command."))

    check = command_check(command_game(BELOW, SOLID), rep)

    assert check["status"] == "unsupported"
    assert B in check["claim"] and B in check["evidence"]


def test_a_solid_claim_about_a_starter_without_that_label_is_unsupported():
    rep = report(("Summary", f"{A} shows solid command."))

    assert command_check(command_game(BELOW, SOLID), rep)["status"] == "unsupported"


def test_a_solid_claim_about_the_starter_who_has_it_is_supported():
    rep = report(("Summary", f"{B} shows solid command."))

    check = command_check(command_game(BELOW, SOLID), rep)

    assert check["status"] == "supported" and B in check["claim"]


def test_a_command_claim_in_the_starters_own_section_without_his_name_belongs_to_him():
    rep = report((f"{B} vs Team A", "He shows below-average command."))

    assert command_check(command_game(BELOW, SOLID), rep)["status"] == "unsupported"


def test_an_unattributed_below_average_claim_is_supported_if_some_starter_has_the_label():
    rep = report(("Summary", "Below-average command is the concern here."))

    check = command_check(command_game(BELOW, SOLID), rep)

    assert check["status"] == "supported" and A in check["claim"]


def test_a_game_with_no_command_language_is_not_present():
    rep = report(("Summary", f"{A} and {B} meet on Saturday."))

    assert command_check(command_game(BELOW, SOLID), rep)["status"] == "not_present"


def test_no_one_with_the_label_means_no_support_for_an_unattributed_claim():
    rep = report(("Summary", "Below-average command is the concern here."))

    assert command_check(command_game(AVERAGE, AVERAGE), rep)["status"] == "not_present"


# --- a report that lost its text cannot pass the text checks ---------------------------------------------


@pytest.mark.parametrize("missing", ["headline", "short_summary", "sections"])
def test_a_report_without_its_text_fields_is_an_error_not_a_clean_pass(missing):
    rep = report(("Summary", LIMITATION))
    del rep[missing]

    with pytest.raises(KeyError):
        critic.run(rep, game())


# --- the pitch-name check holds a sentence to the starter it is about (QA3-04) ------------------------
# A throws a Four-seam and a Slider; B throws those and a Changeup too. A changeup said about A,
# in his own section, is false even though B throws one.

NAMES_CLAIM = "The report names only pitches that appear in the pitch mix."


def names_check(rep: dict, matchup: dict | None = None) -> dict:
    review = critic.run(rep, matchup or game())
    return next(c for c in review["checks"] if c["claim"] == NAMES_CLAIM)


def test_a_pitch_only_the_opponent_threw_in_the_starters_own_section_is_unsupported():
    rep = report((f"{A} vs Team B", "His changeup is his best weapon."))

    check = names_check(rep)

    assert check["status"] == "unsupported"
    assert A in check["evidence"] and "changeup" in check["evidence"]


def test_the_same_sentence_in_the_section_of_the_starter_who_threw_it_is_supported():
    rep = report((f"{B} vs Team A", "His changeup is his best weapon."))

    assert names_check(rep)["status"] == "supported"


def test_a_pitch_only_the_opponent_threw_in_a_bullet_of_the_starters_own_section_is_unsupported():
    rep = {
        "headline": "h",
        "short_summary": [],
        "sections": [{"title": f"{A} vs Team B", "body": "A quiet start.", "bullets": ["His changeup plays up."]}],
    }

    assert names_check(rep)["status"] == "unsupported"


def test_a_sentence_naming_the_other_starter_inside_this_section_is_judged_by_the_named_one():
    rep = report((f"{A} vs Team B", f"{B} counters with a changeup."))

    assert names_check(rep)["status"] == "supported"


def test_a_sentence_naming_both_starters_is_held_to_the_two_together():
    rep = report((f"{A} vs Team B", f"{A} and {B} face a changeup."))

    assert names_check(rep)["status"] == "supported"


def test_an_unattributed_sentence_outside_any_starters_section_is_held_to_the_two_together():
    rep = report(("Summary", "The changeup matters in this game."))

    assert names_check(rep)["status"] == "supported"


def test_an_unattributed_pitch_nobody_threw_is_still_unsupported():
    rep = report(("Summary", "The knuckleball matters in this game."))

    assert names_check(rep)["status"] == "unsupported"


def test_the_qa_probe_a_slider_in_the_section_of_the_starter_who_never_threw_one(isolated, monkeypatch):
    # A: 150 four-seams (healthy, no slider). B: 100 four-seams and 50 sliders.
    payload = live_payload(monkeypatch, (150, 0), (100, 50))
    live = next(m for m in payload["matchups"] if m["id"] == "matchup_001")
    away = live["starters"]["away_starter"]["name"]
    section = next(s for s in live["report"]["sections"] if away in s["title"])
    section["body"] += " His slider is his best weapon."

    review = critic.run(live["report"], live)

    check = next(c for c in review["checks"] if c["claim"] == NAMES_CLAIM)
    assert check["status"] == "unsupported" and "slider" in check["evidence"]
    live["critic_review"] = review
    with pytest.raises(Exception, match="unsupported"):
        validate_payload(payload)
