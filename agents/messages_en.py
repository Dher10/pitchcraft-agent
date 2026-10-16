"""English messages of the text-writing agents (decision D6). One entry per sentence.

Keys are `<agent>.<area>.<name>`. A str is a str.format template; a tuple is a list of
terms (words a check looks for in the English text); a dict is a vocabulary. Spanish (v2.1)
is a second file with the same keys. Words that belong to the DATA (pitch names, labels such
as "Above-average swing-and-miss ability") are not here: they come from the pipeline.
"""

from __future__ import annotations

EN_MESSAGES: dict[str, object] = {
    # --- plural forms: t.count("walk", n) -----------------------------------------------------------
    "count.walk.one": "{count} walk",
    "count.walk.other": "{count} walks",
    "count.earned_run.one": "{count} earned run",
    "count.earned_run.other": "{count} earned runs",
    "count.hit.one": "{count} hit",
    "count.hit.other": "{count} hits",
    "count.batter.one": "{count} batter",
    "count.batter.other": "{count} batters",
    "count.strikeout.one": "{count} strikeout",
    "count.strikeout.other": "{count} strikeouts",
    "count.home_run.one": "{count} home run",
    "count.home_run.other": "{count} home runs",
    # --- data scout ---------------------------------------------------------------------------------
    "scout.final.note_1": "Completed demo game used to show the postgame grading flow.",
    "scout.final.note_2": "Grades are PitchCraft-specific and explainable, not official metrics.",
    "scout.demo.note_1": "This demo uses cached data to guarantee stable judging.",
    "scout.demo.note_2": "Live data integration can be added after the capstone.",
    # --- matchup analyst ----------------------------------------------------------------------------
    "analyst.summary": (
        "This matchup features {label}. The scouting note is matchup fit, with each pressure "
        "point shaping what to watch."
    ),
    "analyst.label.against": "{away} against {home}",
    "analyst.list_and": "{first} and {second}",
    "analyst.watch.question": "Can {name} {action}?",
    "analyst.watch.action.ahead": "stay ahead of hitters early in counts",
    "analyst.watch.action.land": "land the {putaway} early in counts",
    "analyst.watch.action.efficient": "work efficiently through the lineup",
    "analyst.watch.action.keep": "keep the ball {goal}",
    "analyst.watch.deep": "Which lineup forces more deep counts by the third inning?",
    "analyst.goal.low": "low",
    "analyst.goal.zone": "in the zone",
    "analyst.demo.away_read": "{name}'s {primary}-{putaway} combination gives him {swing_miss}. {offense}",
    "analyst.demo.home_read": (
        "{name} needs to {command_note} and use the {putaway} to {contact_note}. {offense}"
    ),
    "analyst.fallback.swing_path": "a defined swing-and-miss path",
    "analyst.fallback.swing_data": "Limited swing-and-miss data available",
    "analyst.fallback.command": "Average command this season",
    "analyst.fallback.contact": "Moderate contact risk",
    "analyst.command_note.edge": "keep the command edge visible",
    "analyst.command_note.below": "avoid letting below-average command turn into free passes",
    "analyst.command_note.default": "avoid predictable counts",
    "analyst.contact_note.low": "manage contact",
    "analyst.contact_note.high": "limit hard contact",
    "analyst.contact_note.default": "disrupt timing",
    "analyst.strength.swing_miss": "Above-average swing-and-miss ability",
    "analyst.strength.command": "{label} supports strike-zone control",
    "analyst.strength.contact": "Low contact-risk profile supports contact management",
    "analyst.strength.trending": "Recent form is trending in the right direction",
    "analyst.risk.command": "Below-average command can create deep-count traffic",
    "analyst.risk.contact": "Contact risk can turn missed spots into damage",
    "analyst.risk.volatile": "Recent form has been volatile",
    "analyst.style.pair": "{primary} to set up, {putaway} to finish",
    "analyst.style.single": "{primary} as the main pitch",
    "analyst.offense.unavailable": (
        "Season offense data against {hand} pitching is not available for this lineup yet."
    ),
    "analyst.offense.unavailable_no_hand": (
        "Season offense data cannot be matched to this pitcher's hand, so the lineup read makes no offense claims."
    ),
    "analyst.offense.strong": (
        "This lineup hits well against {hand} pitching ({ops} OPS), so {name} cannot live over the middle."
    ),
    "analyst.offense.average": (
        "This lineup is roughly average against {hand} pitching ({ops} OPS), "
        "with no glaring weakness to attack."
    ),
    "analyst.offense.weak": (
        "This lineup has struggled against {hand} pitching ({ops} OPS), "
        "which gives {name} an edge if he gets ahead."
    ),
    "analyst.offense.note_strikeouts": "They also strike out often, which favors a swing-and-miss approach",
    "analyst.offense.note_walks": "They draw walks at an above-average rate, so {name} needs efficient strikes",
    "analyst.offense.with_notes": "{read} {notes}.",
    "analyst.pressure.ops": "has strong OPS against this pitcher's hand",
    "analyst.pressure.strikeouts": "has elevated swing-and-miss risk",
    "analyst.pressure.walks": "draws walks at an above-average rate",
    "analyst.read.combination": "{name} works off a {primary}-{putaway} combination.",
    "analyst.read.mainly": "{name} works mainly off a {primary}.",
    "analyst.read.he": "He",
    "analyst.read.shows": "{subject} shows {label}{qualifier}.",
    "analyst.read.qualifier": " (regular-season rates)",
    "analyst.read.qualifier_both": " (regular season and postseason rates)",
    "analyst.have.pitches": "{count} pitches",
    "analyst.have.no_pitches": "no pitches on record",
    "analyst.have.batters": "{count} batters faced",
    "analyst.have.no_batters": "no batters faced on record",
    "analyst.have.pitches_unavailable": "pitch count not available",
    "analyst.have.batters_unavailable": "batters faced not available",
    "analyst.data.arsenal": (
        "{name}'s arsenal data is limited ({have}; {needed} needed), "
        "so this report makes no arsenal claim for him."
    ),
    "analyst.data.arsenal_unnamed": (
        "{name} throws pitches the data does not name, so this report makes no arsenal claim for him."
    ),
    "analyst.data.strikeout": (
        "Strikeout data for {name} is limited ({have}; {needed} needed), "
        "so no swing-and-miss claim is made."
    ),
    "analyst.data.control": (
        "Control data for {name} is limited ({have}; {needed} needed), so no command claim is made."
    ),
    "analyst.data.contact": (
        "{name} has allowed {home_runs} over {batters} batters faced; "
        "no contact-risk rating is given because a home-run rate needs a far larger sample."
    ),
    "analyst.data.no_home_runs": "Home runs allowed are not available for {name}.",
    "analyst.figure.era": "ERA",
    "analyst.figure.whip": "WHIP",
    "analyst.figure.innings": "innings",
    "analyst.figure.counts": "the strikeout, walk and home-run counts",
    "analyst.figure.pitch_data": "the pitch mix, velocity and movement",
    "analyst.figure.list_and": "{head} and {last}",
    "analyst.scope.season_figures": "{figures} cover the {label}; ",
    "analyst.scope.no_season_figures": "no season figures are available; ",
    "analyst.scope.differ": (
        "{who}: {season}the pitch mix, velocity and movement cover the {arsenal}. "
        "They are different samples."
    ),
    "analyst.scope.groups": "{who}: {parts}. They are different samples.",
    "analyst.scope.group_part": "{figures} cover the {label}",
    "analyst.scope.none": "{who}: no season figures are available.",
    "analyst.scope.same": "{who}: all pitcher figures cover the {label}.",
    "analyst.scope.offense": "Team offense splits cover the {label}.",
    # --- report writer ------------------------------------------------------------------------------
    "writer.default_strength": "Has a defined scouting note for this matchup fit",
    "writer.watch_line": "The early what to watch is {observation}.",
    "writer.watch_whether": "whether {name} can {action}",
    "writer.section.summary": "Matchup Summary",
    "writer.section.vs_team": "{pitcher} vs {team}",
    "writer.section.arsenal": "Arsenal Scout",
    "writer.section.watch": "Three Things to Watch",
    "writer.section.confidence": "Data Confidence Note",
    "writer.strength": "{name} brings this strength: {strength}.",
    "writer.strength_none": "{name} has no claimed strength because the data is limited.",
    "writer.arsenal.contrast": (
        "The main contrast is {away_style} versus {home_style}. "
        "The primary pitch contrast is {away_primary} against {home_primary}, "
        "a scouting note for matchup fit and each pressure point."
    ),
    "writer.arsenal.works_off": "{name} works off {style}.",
    "writer.arsenal.no_contrast_unnamed": (
        "No arsenal contrast is drawn because one starter's pitches are not named in the data."
    ),
    "writer.arsenal.no_contrast": (
        "No arsenal contrast is drawn because at least one arsenal has too little data."
    ),
    "writer.confidence.limited": (
        "Samples below the minimum are flagged as limited and no claim is made from them."
    ),
    "writer.confidence.snapshot": "This report uses a fetched live snapshot with {items}.",
    "writer.confidence.item.pitchers": "probable pitchers",
    "writer.confidence.item.pitch_data": "Statcast pitch data",
    "writer.confidence.item.offense": "season offense splits",
    "writer.confidence.list_two": "{first} and {second}",
    "writer.confidence.list_three": "{first}, {second}, and {third}",
    "writer.confidence.pitch_data.one": (
        "Statcast pitch data was available for {with_data} but not for {without_data}, "
        "so the pitch read makes no arsenal claims about {without_data}."
    ),
    "writer.confidence.pitch_data.none": (
        "Statcast pitch data was not available for either starter, so the pitch read makes no arsenal claims."
    ),
    "writer.confidence.offense.one": (
        "Season offense splits were available for the {with_split} lineup but not for the {without_split} "
        "lineup, so the lineup read makes no offense claims about the {without_split} lineup."
    ),
    "writer.confidence.offense.none": (
        "Season offense splits were not available for this game, so the lineup read makes no offense claims."
    ),
    "writer.confidence.lineups": "Lineups can still change before first pitch.",
    "writer.confidence.demo": (
        "This report is based on cached demo data for the capstone. Live lineup "
        "confirmation is not required for this version."
    ),
    "writer.forbidden_terms": ("bet", "odds", "pick", "lock", "guaranteed", "win probability", "prediction"),
    "writer.required_terms": ("matchup fit", "what to watch", "scouting note", "pressure point"),
    # --- critic -------------------------------------------------------------------------------------
    "critic.summary.unsupported": (
        "The critic checked {checked} claims and found {unsupported} the data does not back up; "
        "this report must not be published."
    ),
    "critic.summary.warnings": "The critic checked {checked} claims: none unsupported, {warnings} with a warning.",
    "critic.summary.supported": "The critic checked {checked} claims and found them supported by the data.",
    "critic.note.no_betting": "No betting or outcome-prediction language found.",
    "critic.role.primary": "primary",
    "critic.role.putaway": "put-away",
    "critic.pitch.claim": "{name}'s {role} pitch is {pitch}.",
    "critic.pitch.absent": "{pitch} does not appear in {name}'s pitch mix.",
    "critic.pitch.supported_primary": "Pitch mix shows {usage}% {pitch} usage.",
    "critic.pitch.supported_putaway": "Put-away pitch usage at {usage}% supports this claim.",
    "critic.pitch.low": (
        "{pitch} is only {usage}% of {name}'s pitch mix, "
        "below the {minimum}% the report treats as a {role} pitch."
    ),
    "critic.pitch.low_counts": (
        "{pitch} is {count} of {total} pitches ({usage}%) in {name}'s pitch mix, "
        "below the {minimum}% the report treats as a {role} pitch."
    ),
    "critic.names.claim": "The report names only pitches that appear in the pitch mix.",
    "critic.names.supported": "Every pitch named in the report was thrown by the starter it is credited to.",
    "critic.names.credited": "{name} is credited with {pitch}, which he did not throw",
    "critic.names.nobody": "{pitch} is named, but neither starter threw it",
    "critic.names.unsupported": "{problems} in this data.",
    "critic.generic_fastball": "fastball",
    "critic.pitch_aliases": {
        "four-seam": ("four-seam", "four seam", "4-seam"),
        "sinker": ("sinker", "two-seam", "two seam", "2-seam"),
        "cutter": ("cutter", "cut fastball"),
        "slider": ("slider",),
        "sweeper": ("sweeper",),
        "slurve": ("slurve",),
        "curveball": ("curveball", "curve ball", "knuckle curve"),
        "changeup": ("changeup", "change-up"),
        "splitter": ("splitter", "split-finger", "split finger"),
        "knuckleball": ("knuckleball",),
        "forkball": ("forkball",),
        "eephus": ("eephus",),
    },
    "critic.limited.claim": "{name}'s arsenal is limited.",
    "critic.limited.pitches": "{count} pitches",
    "critic.limited.none": "no pitches on record",
    "critic.limited.unsupported": "Only {have} (minimum {needed}), but the report names {named}.",
    "critic.limited.supported": "{have}, below the {needed} needed; the report makes no arsenal claim.",
    "critic.limited.unsupported_unavailable": (
        "Pitch count not available (the minimum is {needed}), but the report names {named}."
    ),
    "critic.limited.supported_unavailable": (
        "Pitch count not available (the minimum is {needed}); the report makes no arsenal claim."
    ),
    "critic.command.word": "command",
    "critic.command.below_claim": "{name} carries below-average command risk.",
    "critic.command.label_claim": "{name}'s command label is supported.",
    "critic.command.wrong_claim": "The report's command claim about {name} matches the data.",
    "critic.command.wrong_evidence": (
        "The report says {name} has {wording}, but his command label is {label}."
    ),
    "critic.command.no_label": "not available",
    "critic.command.absent_claim": "The report makes a command claim.",
    "critic.command.absent_evidence": "No command claim requiring correction was found.",
    "critic.command.strength": "Command signal is {value} in the strength profile.",
    "critic.command.walks": "{walks} walks in {batters} batters faced ({scope}).",
    "critic.command.none": "No walk-rate sample is available.",
    "critic.scope.claim": "Pitch data and season figures are not presented as one sample.",
    "critic.scope.same": "Each starter's figures cover the same games.",
    "critic.scope.marker": "different samples",
    "critic.scope.all_marker": "all pitcher figures cover",
    "critic.scope.all_claimed": (
        "The report says all the figures for {who} cover one sample, but they cover different games."
    ),
    "critic.scope.supported": "The report says the figures for {who} cover different samples.",
    "critic.scope.unsupported": (
        "Pitch data and season figures for {who} cover different games "
        "(postseason is in one and not the other), but the report does not say so."
    ),
    "critic.betting_terms": (
        "bet",
        "odds",
        "pick",
        "lock",
        "guaranteed",
        "win probability",
        "predicts the winner",
        "will win",
    ),
    "critic.betting.claim": "The report predicts the winner.",
    "critic.betting.item": "'{term}' in {location}",
    "critic.betting.unsupported": "Outcome or betting language found: {flagged}.",
    "critic.betting.absent": "No win prediction or betting language found.",
    # --- postgame grader ----------------------------------------------------------------------------
    "grader.explanation.standout": (
        "A Game Score of {score} reflects a standout start - he worked deep, "
        "missed bats, and controlled the run damage."
    ),
    "grader.explanation.solid": (
        "A Game Score of {score} reflects a solid, above-average start - he worked "
        "deep, limited walks, and kept the damage in check."
    ),
    "grader.explanation.mixed": (
        "A Game Score of {score} reflects a mixed start - there were useful innings, "
        "but traffic kept it from becoming a clean outing."
    ),
    "grader.explanation.rough": (
        "A Game Score of {score} reflects a rough outing - the hits and walks piled "
        "up and shortened his night."
    ),
    "grader.explanation.difficult": (
        "A Game Score of {score} reflects a difficult outing - too much traffic and "
        "run damage overwhelmed the bright spots."
    ),
    "grader.plan.matched": (
        "The plan was to command the {primary} and finish with the {putaway}; "
        "{walks} and {earned_runs} show the execution mostly matched it."
    ),
    "grader.plan.walks": (
        "The plan was to use the {primary} to reach {putaway} counts, but "
        "{walks} kept him from controlling the sequence."
    ),
    "grader.plan.partial": (
        "The plan was built around the {primary} and {putaway}, but "
        "{hits} and {earned_runs} left only partial execution."
    ),
    "grader.next.walks": "The next checkpoint is tightening strike-zone control before traffic builds.",
    "grader.next.hits": "The next checkpoint is limiting contact before counts turn stressful.",
    "grader.next.runs": "The next checkpoint is cutting off big innings after the first damage.",
    "grader.next.chase": "The next checkpoint is getting more chase from the {putaway}.",
    "grader.next.default": "The next checkpoint is repeating that walk suppression deep into another start.",
    "grader.call.command.note": "{name} needed his command edge to limit free passes.",
    "grader.call.command.evidence": "He issued {walks} over {innings} innings.",
    "grader.call.walk_risk.note": "{name} carried elevated walk risk.",
    "grader.call.walk_risk.evidence": "He walked {batters} and exited after {innings} innings.",
    "grader.call.swing_miss.note": "{name} had swing-and-miss upside from the scouting profile.",
    "grader.call.swing_miss.evidence": (
        "He recorded {strikeouts}, but the full line landed at a Game Score of {score}."
    ),
}
