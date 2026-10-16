"""The violations of the data contract that the code has today (P0.15-D3.2). TEMPORARY.

Each entry maps a violation code of `contract_checks.check_contract` to the findings of
`docs/DATA_CONTRACT.md` (section 4) it belongs to. `validate_payload` tolerates exactly these codes so
that the generator keeps publishing as it does today while the fixes land, one class at a time, in
P0.15-D2.1 to D2.5. Every fix deletes the entries of its findings; a test fails if the table has an
entry that no longer occurs in the payloads of the tests, or if a payload has a violation that is not in
it. The commit of P0.15-D2.5 deletes this module and the code of `validate_payload` that reads it.
"""

from __future__ import annotations

KNOWN_VIOLATIONS: dict[str, tuple[str, ...]] = {
    "rule1:constant_asserts_fact#matchups[].data_confidence.lineup_status": ("F5",),
    "rule1:constant_asserts_fact#matchups[].status": ("F5",),
    "rule4:writer.confidence.lineups#game_state": ("F5", "F16"),
    "rule4:writer.section.summary#game_state": ("F5", "F16"),
}
