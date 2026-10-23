# Sample thresholds — proposal for D11 (P0.4)

Status: **approved by the owner on 2026-10-10 with the recommended values (arsenal 100 pitches, strikeout 70 BF, control 170 BF, contact risk as a count only); recorded as D24.** The analysis below is kept as the evidence behind D24.

## What the owner needs to decide

1. **Arsenal:** 100 pitches (keep D11) or another value. Recommendation: keep 100.
2. **Strikeout:** 70 batters faced. Recommendation: 70.
3. **Control:** 170 batters faced, accepting that about 4 in 10 starts are flagged as limited. Alternative in the table below.
4. **Contact risk (home-run rate):** no value is workable (needs 1,320 BF; no 2026 starter reached 894). Choose: drop the label, show counts only, or replace the metric.
5. **Season-to-date only:** the pipeline uses current-season data only, so April is mostly flagged. Confirm that is acceptable (it is the honest reading of D1), or ask for a carry-over from the previous season as a later task.

## What a threshold does

A dimension is flagged **limited** when the starter's sample before the game is below the threshold. The report then says the data is limited for that dimension and makes no claim beyond that (Phase 0 Gherkin "Limited sample is flagged, not filled"). Labels use rates, never counts (Gherkin "Labels use rates, not counts").

## Where the thresholds come from

| Rate | Published stabilization point | Source |
|---|---|---|
| Strikeout rate | 70 BF | [FanGraphs, Sample Size](https://library.fangraphs.com/principles/sample-size/); [FanGraphs, K rate after 70 BF](https://fantasy.fangraphs.com/looking-at-strikeout-rate-changes-after-70-batters-faced); [Baseball Prospectus](https://www.baseballprospectus.com/news/article/20516/baseball-therapy-should-i-worry-about-my-favorite-pitcher/) |
| Walk rate | 170 BF | FanGraphs Sample Size; Baseball Prospectus |
| Home-run rate | 1,320 BF | FanGraphs Sample Size; Baseball Prospectus (marked "estimate") |
| Ground-ball rate | 70 balls in play | FanGraphs Sample Size (the page lists BIP; a reader comment quotes the author saying the research used PA) |
| Pitch quality (aStuff+), not usage | median 72 pitches (31 for sliders, 58 four-seam, 61 slurves) | [Salorio, My Stuff+ Model](https://adamsalorio.substack.com/p/introducing-my-stuff-model-volume) |

"Stabilizes" here means the sample correlates 0.7 (R² .49) with another sample of the same size (Carleton's cut, as used by FanGraphs). Authors say these are not magic numbers.

**No published number covers pitch-mix usage or velocity.** The only pitch-level evidence I could verify is the Stuff+ figure above, which measures pitch quality, not how often a pitcher throws each pitch. So the 100-pitch arsenal threshold in D11 is a product choice, not a published stabilization point. I also found two other claims in search results (a 100-pitch figure for pitch classification in an arXiv paper and per-model figures in a Medium post) that I could not open and did not use.

## How I measured

- Source: MLB Stats API, one league-wide pitching request per week of the 2026 regular season (2026-03-25 to 2026-09-27, 27 requests, 1.5 s apart): `/api/v1/stats?stats=byDateRange&group=pitching&season=2026&playerPool=ALL&sportIds=1&limit=2000&startDate=2026-03-25&endDate=<week end>`. Fields: `numberOfPitches`, `battersFaced`, `baseOnBalls`, `gamesStarted`. No Statcast bulk download.
- Unit: every start of the season (4,858 starts by 377 pitchers, equal to the sum of final `gamesStarted`). The sample counted is the pitcher's season-to-date total at the start of that week, which is what the pipeline would have at game time. A second start in the same week gets the earlier sample (slightly understated).
- "Excl. first starts" removes each pitcher's first start of the year, where the sample is zero by construction (232 of the 377 first starts had no earlier 2026 pitches).
- Limits: API pitch counts can differ a little from Statcast pitch rows; the regular season only; openers and bulk pitchers count as starters when the API credits a start.

## The 2026 distribution (sample before each start)

| | p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|---|
| Pitches | 92 | 357 | 859 | 1,531 | 2,095 |
| Batters faced | 24 | 92 | 222 | 397 | 542 |
| Walks | 2 | 8 | 18 | 31 | 43 |

5.2% of starts (254) come with zero pitches in the sample, 6.3% with zero walks. At season end, 243 pitchers had 5 or more starts (median 473 BF, 1,839 pitches); the most batters faced by any starter was 894.

## Options per dimension

Each row shows how many starts would be flagged and how many pitchers end the season below the line. "All starts" is out of 4,858; "excl. first" is out of 4,481.

### Arsenal (pitches)

| Threshold | Flagged, all starts | Flagged, excl. first | Pitchers below it at season end (of 377) |
|---|---|---|---|
| 72 (Stuff+ median) | 315 (6.5%) | 1.2% | 4 |
| **100 (D11)** | **519 (10.7%)** | **5.5%** | **10** |
| 150 | 577 (11.9%) | 6.5% | 16 |
| 200 | 791 (16.3%) | 10.9% | 22 |
| 300 | 1,066 (21.9%) | 16.5% | 39 |

By month at 100: April 26%, May 6%, June 3%, July 3%, August 3%, September 2%. 100 pitches is about one start, so this flag is mostly "this pitcher has not started yet this season".

### Strikeout (batters faced)

| Threshold | Flagged, all starts | Flagged, excl. first | Pitchers below it at season end (of 377) |
|---|---|---|---|
| 35 | 546 (11.2%) | 6.0% | 16 |
| 50 | 774 (15.9%) | 10.6% | 23 |
| **70 (published)** | **994 (20.5%)** | **15.1%** | **35** |
| 100 | 1,286 (26.5%) | 21.2% | 56 |
| 140 | 1,701 (35.0%) | 29.9% | 82 |

By month at 70: April 58%, May 13%, June 8%, July 7%, August 6%, September 6%.

### Control (batters faced)

| Threshold | Flagged, all starts | Flagged, excl. first | Pitchers below it at season end (of 377) |
|---|---|---|---|
| 100 (not published) | 1,286 (26.5%) | 21.2% | 56 |
| 140 (not published) | 1,701 (35.0%) | 29.9% | 82 |
| **170 (published)** | **2,002 (41.2%)** | **36.4%** | **106** |
| 250 | 2,647 (54.5%) | 50.7% | 156 |

By month at 170: April 100%, May 49%, June 26%, July 18%, August 15%, September 16%. 170 BF is about six and a half starts. This is the dimension where honesty costs the most coverage. Choosing 100 or 140 flags fewer starts but has no published support; I do not recommend it.

### Contact risk (home-run rate, batters faced)

| Threshold | Flagged, all starts | Flagged, excl. first | Pitchers below it at season end (of 377) |
|---|---|---|---|
| 400 | 3,662 (75.4%) | 73.3% | 229 |
| 600 | 4,582 (94.3%) | 93.8% | 296 |
| 1,320 (published) | 4,858 (100%) | 100% | 377 |

At the published value every start in 2026 would be flagged: no starter passed 894 BF, and only 81 reached 600. A home-run-rate label cannot be both honest and useful in a single season.

Options for the owner: (a) drop the contact-risk label and keep the plain count ("allowed 12 home runs in 140 IP") with no rate claim; (b) replace the metric with one that stabilizes sooner, for example ground-ball rate (70 balls in play per FanGraphs), which Statcast can supply; (c) keep the label with a low threshold and accept that it is below the published point. I recommend (a) for v2.0-a and (b) as a later task.

## Rate bands (added with P0.5)

D24 fixes the sample thresholds. Turning a rate into a label also needs cut points, which D24 does not cover. P0.5 uses rounded quartiles of 2026 starters with 5 or more starts (243 pitchers, regular season through 2026-09-27; league averages 22.1% K and 8.9% BB):

| Rate | q25 | median | q75 | Label rule |
|---|---|---|---|---|
| Strikeouts per batter faced | 17.9% | 21.0% | 24.6% | 25% or more: above-average; under 18%: below-average; otherwise average |
| Walks per batter faced | 6.9% | 8.2% | 10.0% | 7% or less: solid command; 10% or more: below-average; otherwise average |

A label is given only when the dimension clears its D24 sample threshold. The cut points belong to one season's league environment and should be rechecked each year.

## For the postseason layer

The postseason starters are mostly regulars. Among the 243 pitchers with 5 or more starts: none is below 100 pitches or 70 BF at season end, 2 are below 100 BF, 27 are below 170 BF and 96 are below 400 BF. So arsenal and strikeout flags will be rare in October, control will still be flagged for about 1 starter in 9, and the contact-risk issue above does not go away.

## Recommended values

| Dimension | Metric | Threshold | Basis |
|---|---|---|---|
| Arsenal | pitches | 100 | D11 product choice; closest evidence is Stuff+ at 72 |
| Strikeout | batters faced | 70 | published |
| Control | batters faced | 170 | published |
| Contact risk | — | no rate label (option a) | published point is out of reach in a season |

If approved, the values go into `DECISIONS.md` and P0.5 implements them in one module.
