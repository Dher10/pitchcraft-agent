"""No condition of a claim about data runs the critic again (P0.15-D3.3a, contract rule 4).

A claim of the critic about the data (`critic.names.*`, `limited.*`, `command.*`, `scope.*`, `betting.*`)
is checked against the fields it speaks about: the pitch mix, `sample`, `scopes`, the labels and the text
of the report. Asking the critic what it finds on the published matchup proves nothing: it repeats its own
answer. Only the claims about the process (`critic.summary.*` and the notes, which count the published
checks) may look at the checks, and they read them from the payload, never by running the critic.

Two guards, so the rule cannot come back by another door:

- static: the modules that check the contract do not import the critic;
- dynamic: with every function of the critic made to fail, the whole contract still runs over the corpus.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from agents import critic
from data_pipeline.contract_checks import check_contract
from tests.corpus import corpus

DATA_PIPELINE = Path(__file__).resolve().parents[1] / "data_pipeline"
# The modules that decide whether a payload keeps the contract. `report_facts` is where the conditions read
# the text of the report; it appears with D3.3a and is held to the same rule.
CHECKERS = ("claims_registry.py", "contract_checks.py", "provenance.py", "report_facts.py")


def imported_names(path: Path) -> set[str]:
    """Every module a file imports, as dotted names, and every `module.name` of a `from` import."""

    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


@pytest.mark.parametrize("module", CHECKERS)
def test_a_module_that_checks_the_contract_does_not_import_the_critic(module):
    path = DATA_PIPELINE / module
    if not path.exists():
        pytest.skip(f"{module} does not exist yet")

    assert "agents.critic" not in imported_names(path)


def test_the_guard_sees_the_import_it_is_looking_for(tmp_path):
    """Control: the scan finds both spellings of the import, so a clean result means something."""

    (tmp_path / "a.py").write_text("from agents import critic as c\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import agents.critic\n", encoding="utf-8")

    assert "agents.critic" in imported_names(tmp_path / "a.py")
    assert "agents.critic" in imported_names(tmp_path / "b.py")


def test_the_contract_runs_over_the_whole_corpus_with_the_critic_unable_to_run(monkeypatch):
    payloads = list(corpus(monkeypatch))  # built first: the generator itself runs the critic
    assert len(payloads) > 15

    def boom(*args, **kwargs):
        raise AssertionError("a condition of the contract ran the critic again")

    own = [name for name, value in vars(critic).items() if inspect.isfunction(value) and value.__module__ == critic.__name__]
    assert "run" in own and len(own) > 10
    for name in own:
        monkeypatch.setattr(critic, name, boom)

    for name, payload in payloads:
        check_contract(payload)  # raises if any condition reaches the critic
