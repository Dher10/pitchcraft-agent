"""D6, minimal (QA-07): every agent that writes text takes a `language` parameter ('en' by
default) and its text lives in a catalog, not in the code.

English is the only catalog that ships (Spanish is v2.1). A pseudo-language proves the
point without translating anything: if every message really comes from the catalog,
switching to it leaves no English sentence of the agents in the output.
"""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import re

import pytest

from agents import critic, data_scout, language, matchup_analyst, postgame_grader, report_writer
from tests.golden_scenarios import agent_outputs, scenarios

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"
TEXT_AGENTS = (data_scout, matchup_analyst, report_writer, critic, postgame_grader)


# --- the parameter ----------------------------------------------------------------------------------


@pytest.mark.parametrize("agent", TEXT_AGENTS, ids=lambda a: a.__name__)
def test_every_text_agent_takes_language_with_en_as_default(agent):
    parameter = inspect.signature(agent.run).parameters.get("language")

    assert parameter is not None, f"{agent.__name__}.run has no language parameter"
    assert parameter.default == "en"


def test_the_qa_probe_report_writer_accepts_language_en(monkeypatch):
    matchup = scenarios(monkeypatch)["demo_upcoming"]
    findings = matchup_analyst.run(data_scout.run(matchup))

    assert report_writer.run(findings, matchup, language="en") == report_writer.run(findings, matchup)


def test_an_unknown_language_is_an_error_not_a_silent_english(monkeypatch):
    matchup = scenarios(monkeypatch)["demo_final"]
    packet = data_scout.run(matchup)
    findings = matchup_analyst.run(packet)
    report = report_writer.run(findings, matchup)
    calls = {
        "data_scout": lambda: data_scout.run(matchup, language="es"),
        "matchup_analyst": lambda: matchup_analyst.run(packet, language="es"),
        "report_writer": lambda: report_writer.run(findings, matchup, language="es"),
        "critic": lambda: critic.run(report, matchup, language="es"),
        "postgame_grader": lambda: postgame_grader.run(matchup, language="es"),
    }
    for call in calls.values():
        with pytest.raises(language.UnknownLanguageError):
            call()


def test_the_generator_passes_the_language_to_the_agents(monkeypatch):
    from data_pipeline import generate_demo_json as gdj

    assert inspect.signature(gdj.build_payload).parameters["language"].default == "en"
    with pytest.raises(language.UnknownLanguageError):
        gdj.build_payload(language="es")
    assert gdj.build_payload(language="en") == gdj.build_payload()


def test_the_default_and_an_explicit_en_give_the_same_output(monkeypatch):
    for name, matchup in scenarios(monkeypatch).items():
        assert agent_outputs(matchup) == agent_outputs(matchup, language="en"), name


# --- the catalog ------------------------------------------------------------------------------------


def _static_fragments(messages: dict) -> list[str]:
    """The fixed English text of the templates: what must disappear in another language."""

    fragments = []
    for value in messages.values():
        texts = [value] if isinstance(value, str) else [v for v in value if isinstance(v, str)]
        for text in texts:
            for piece in re.split(r"\{[^}]*\}", text):
                if len(piece.strip()) >= 12:
                    fragments.append(piece.strip())
    return fragments


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


@pytest.fixture()
def pseudo(monkeypatch):
    """A catalog where every message is «key» and the language rules (term lists) are empty."""

    english = language.CATALOGS["en"]
    messages = {
        key: (type(value)() if not isinstance(value, str) else "«" + key + "»")
        for key, value in english.items()
    }
    monkeypatch.setitem(language.CATALOGS, "xx", messages)
    return english


def test_the_english_catalog_has_the_text(pseudo):
    assert len(_static_fragments(pseudo)) > 40


def test_the_catalog_has_no_unused_or_missing_keys():
    used = set()
    for path in AGENTS_DIR.glob("*.py"):
        used |= set(
            re.findall(r'\bt(?:\.\w+)?\(\s*"([a-z_]+\.[a-z0-9_.]+)"', path.read_text(encoding="utf-8"))
        )
    known = set(language.CATALOGS["en"])

    assert used - known == set(), "keys used in the agents but missing from the catalog"
    # Keys built at run time (count.<noun>.one/other) are used through t.count(noun, n).
    dynamic = {
        key
        for key in known
        if key.startswith(("count.", "analyst.figure.", "critic.role.", "critic.pitch.supported_"))
    }
    assert known - used - dynamic == set(), "catalog entries no agent uses"


def test_a_pseudo_language_leaves_no_english_text_of_the_agents(monkeypatch, pseudo):
    fragments = _static_fragments(pseudo)
    leaks = []
    for name, matchup in scenarios(monkeypatch).items():
        data = json.dumps(matchup, ensure_ascii=False)
        out = agent_outputs(matchup, language="xx")
        for text in _strings(out):
            for fragment in fragments:
                # English that came in as data (labels, pitch names) is not the agents' text.
                if fragment in text and fragment not in data:
                    leaks.append((name, fragment))
    assert leaks == []


def test_the_pseudo_language_really_changes_the_output(monkeypatch, pseudo):
    matchup = scenarios(monkeypatch)["live_healthy"]

    out = agent_outputs(matchup, language="xx")

    assert "«" in json.dumps(out, ensure_ascii=False)
    assert out != agent_outputs(matchup)


# --- no hardcoded user-facing string ---------------------------------------------------------------


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def _raise_ids(tree: ast.AST) -> set[int]:
    return {id(n) for node in ast.walk(tree) if isinstance(node, ast.Raise) for n in ast.walk(node)}


def hardcoded_text(path: Path) -> list[str]:
    """String constants that read as text: a space and a word. Docstrings and `raise` messages
    (developer errors, never shown to a fan) are not user-facing."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_ids(tree) | _raise_ids(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            text = node.value
            if re.search(r"\s", text) and re.search(r"[A-Za-z]{2,}", text):
                found.append(f"{path.name}:{node.lineno}: {text[:60]!r}")
    return found


CATALOG_FILES = {"__init__.py", "language.py", "messages_en.py"}  # the catalog is where the text lives
AGENT_FILES = sorted(p for p in AGENTS_DIR.glob("*.py") if p.name not in CATALOG_FILES)


@pytest.mark.parametrize("path", AGENT_FILES, ids=lambda p: p.name)
def test_no_agent_hardcodes_a_user_facing_sentence(path):
    assert hardcoded_text(path) == []


def test_the_guard_does_catch_a_sentence(tmp_path):
    sample = tmp_path / "agent.py"
    sample.write_text('def run():\n    """Doc string."""\n    return f"He throws {x} hard."\n')

    assert hardcoded_text(sample)
