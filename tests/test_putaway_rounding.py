"""D30 and the pitch ranking are decided on raw pitch counts, never on rounded shares (QA2-04).

QA2-04 probe: 374 sliders in 2,500 pitches is 14.96%. The chart shows 15.0%, and the put-away
rule (a second pitch counts only from 15% of the mix) took the rounded figure, so it named a
Slider. The same rounding also ordered pitches: two pitches at 20.02% and 19.98% both read
20.0%, and the tie went to the alphabet instead of to the pitch thrown more often.
"""

from __future__ import annotations

import pytest

from data_pipeline import labels
from data_pipeline.fetchers import live_pipeline as lp
from tests.test_live_sample_pipeline import frame

NOT_AVAILABLE = "Not available"


def profile_for(sliders: int, total: int = 2500) -> dict:
    return lp.process_pitcher_statcast(
        frame(n_plain=total - sliders, extra_rows=[{"pitch_type": "SL"}] * sliders), "Threshold"
    )


def test_the_qa_probe_just_below_15_percent_has_no_put_away_pitch():
    result = profile_for(374)  # 14.96%

    assert result["pitching_profile"]["putaway_pitch"] == NOT_AVAILABLE
    assert result["pitching_profile"]["style_label"] == "Four-seam starter"


def test_the_chart_still_shows_the_rounded_share():
    result = profile_for(374)

    assert result["pitch_mix"][1]["away_starter"]["overall"] == 15.0  # display only


def test_exactly_15_percent_is_a_put_away_pitch():
    result = profile_for(375)  # 15.00%

    assert result["pitching_profile"]["putaway_pitch"] == "Slider"
    assert result["pitching_profile"]["style_label"] == "Four-seam-Slider starter"


def test_just_above_15_percent_is_a_put_away_pitch():
    assert profile_for(376)["pitching_profile"]["putaway_pitch"] == "Slider"  # 15.04%


@pytest.mark.parametrize("count, total, qualifies", [(14, 100, False), (15, 100, True), (16, 100, True)])
def test_the_share_helper_cross_multiplies(count, total, qualifies):
    assert labels.share_at_least(count, total, labels.PUTAWAY_MIN_USAGE_PCT) is qualifies


def test_a_zero_total_has_no_share():
    assert labels.share_at_least(0, 0, 15) is False


def test_two_pitches_that_round_to_the_same_share_are_ranked_by_how_often_they_were_thrown():
    # 6000 four-seams, 2002 sliders (20.02%), 1998 changeups (19.98%): both read 20.0%.
    df = frame(
        n_plain=6000,
        extra_rows=[{"pitch_type": "SL"}] * 2002 + [{"pitch_type": "CH"}] * 1998,
    )

    result = lp.process_pitcher_statcast(df, "Tie")

    assert [row["pitch"] for row in result["pitch_mix"]] == ["Four-seam", "Slider", "Changeup"]
    assert result["pitch_mix"][1]["away_starter"]["overall"] == result["pitch_mix"][2]["away_starter"]["overall"]
    assert result["pitching_profile"]["putaway_pitch"] == "Slider"


def test_a_real_tie_in_the_counts_is_ranked_by_name_so_the_order_is_stable():
    df = frame(n_plain=60, extra_rows=[{"pitch_type": "SL"}] * 20 + [{"pitch_type": "CH"}] * 20)

    result = lp.process_pitcher_statcast(df, "Exact Tie")

    assert [row["pitch"] for row in result["pitch_mix"]] == ["Four-seam", "Changeup", "Slider"]
