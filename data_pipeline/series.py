"""The series context of a postseason game (P1.5-b, D43; docs/DATA_CONTRACT.md rule 1).

`matchups[i].series` is `{series_name, game_number, games_in_series, standing}` for a postseason game and `null` for any
other. The schedule gives the series name and the standing as free text, which is third-party text: it is published only
when it matches a strict pattern fixed from a measurement (`tests/fixtures/mlb_series_2026-10.json`, one real request of
2026-10-22 over 41 postseason games), and a standing only when its numbers can be true together. Anything else is
unavailable (`null`), never an unchecked string.

Pure: no network, no import of the fetchers. The fetchers, the provenance manifest and the claims registry all read
their vocabulary from here, so a rule is stated once.
"""

from __future__ import annotations

import re
from typing import Any

POSTSEASON_GAME_TYPES = ("F", "D", "L", "W")
SERIES_LENGTHS = (3, 5, 7)
MAX_GAMES = max(SERIES_LENGTHS)  # no postseason series has more games than this

# The seven names of the real answer: the wild card, division and championship series of each league, and the World Series.
SERIES_NAME = re.compile(r"(?:AL|NL) (?:Wild Card|Division|Championship) Series|World Series", re.ASCII)
# "ATL leads 1-0", "ATL wins 2-1", "Series tied 1-1" (the schedule's `seriesStatus.result`).
# ASCII digits only: `\d` alone also matches digits of other scripts, which are not a schedule's.
STANDING = re.compile(
    r"(?:(?P<team>[A-Z]{2,3}) (?P<verb>leads|wins) (?P<a>[0-9])-(?P<b>[0-9])|Series tied (?P<t>[0-9])-(?P<u>[0-9]))", re.ASCII
)


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def series_name(value: Any) -> str | None:
    """The series name when it is one of the seven the code knows, else None."""

    return value if isinstance(value, str) and SERIES_NAME.fullmatch(value) else None


def standing(value: Any, game_number: Any, games_in_series: Any = None) -> str | None:
    """
    The standing before game `game_number` when it is a recognized text whose numbers can be true, else None.

    True together means: the leader has more wins than the other side and fewer than the series needs, a tie has equal
    numbers and fewer than the series needs, a series that is won ("wins") is never the standing before a game, and no
    more games were played than came before this one.
    The wins a series needs follow from its length when the length is known (3, 5 or 7 games), else from the longest (7).
    """

    if not isinstance(value, str) or not _is_count(game_number) or not 2 <= game_number <= MAX_GAMES:
        return None
    match = STANDING.fullmatch(value)
    if match is None:
        return None
    # The wins a series needs: from its length when known; otherwise the most any series needs (four of seven), so a
    # lead or a tie of that many wins is refused whatever the series is.
    known = _is_count(games_in_series) and games_in_series in SERIES_LENGTHS
    needed = games_in_series // 2 + 1 if known else MAX_GAMES // 2 + 1
    if match["verb"] is not None:
        # "X wins 4-2" ends the series: no game comes after it, so it is never the standing before one.
        wins, losses = int(match["a"]), int(match["b"])
        if match["verb"] != "leads" or wins <= losses or wins >= needed:
            return None
    else:
        wins = losses = int(match["t"])
        if wins != int(match["u"]) or wins == 0 or wins >= needed:
            return None
    return value if wins + losses <= game_number - 1 else None


def build(
    game_type: Any,
    name: Any,
    game_number: Any,
    games_in_series: Any,
    result: Any,
) -> dict[str, Any] | None:
    """
    The `series` object of a game, or None when it is not a postseason game or the schedule does not name its series in
    words the code knows, or whose game number no series can have (more than seven, or beyond the length it states): the page
    then says nothing about a series. The first game has no standing; a standing that fails its check, or a length a
    series does not have, is unavailable inside the object.
    """

    if game_type not in POSTSEASON_GAME_TYPES or not isinstance(game_type, str):
        return None
    name = series_name(name)
    if name is None or not _is_count(game_number) or not 1 <= game_number <= MAX_GAMES:
        return None
    length = games_in_series if games_in_series in SERIES_LENGTHS and _is_count(games_in_series) else None
    if length is not None and game_number > length:
        return None  # a game beyond the length the same answer gives: the numbers cannot both be true
    return {
        "series_name": name,
        "game_number": game_number,
        "games_in_series": length,
        "standing": standing(result, game_number, length),
    }
