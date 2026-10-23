"""P1.0-a: CI installs exactly what the requirements files say, down to the last transitive package.

`requirements.txt` pins the runtime tree (pybaseball and everything it pulls in) and `requirements-dev.txt` adds the
test tools, each as `name==version`. The closure test reads the metadata of the packages installed where the test runs
and requires every package a pinned one asks for (on Linux, the CI platform, with no extras) to be pinned too, so a new
transitive release cannot change what CI installs. A package that is not installed here is not followed; in CI all of
them are.
"""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
import re

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"^(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)==(?P<version>[A-Za-z0-9][A-Za-z0-9.!+_-]*)$")
LINUX = {
    "extra": "",
    "sys_platform": "linux",
    "platform_system": "Linux",
    "os_name": "posix",
    "platform_machine": "x86_64",
    "implementation_name": "cpython",
}


def read(path: str) -> tuple[list[str], list[str]]:
    """The pin lines and the `-r` includes of a requirements file (comments and blanks dropped)."""
    pins, includes = [], []
    for raw in (ROOT / path).read_text(encoding="utf-8").splitlines():
        line = raw.split(" #")[0].strip()
        if not line or line.startswith("#"):
            continue
        (includes if line.startswith("-r ") else pins).append(line)
    return pins, includes


def names(pins: list[str]) -> set[str]:
    return {canonicalize_name(PIN.match(pin)["name"]) for pin in pins}


RUNTIME_PINS, _ = read("requirements.txt")
DEV_PINS, DEV_INCLUDES = read("requirements-dev.txt")


@pytest.mark.parametrize("pin", [*RUNTIME_PINS, *DEV_PINS])
def test_every_line_is_an_exact_pin(pin):
    assert PIN.match(pin), pin


def test_the_dev_file_includes_the_runtime_file_and_nothing_else():
    assert DEV_INCLUDES == ["-r requirements.txt"]


def test_no_package_is_pinned_twice_with_two_versions():
    pinned = RUNTIME_PINS + DEV_PINS
    assert len(names(pinned)) == len(pinned)


@pytest.mark.parametrize("name", ["pybaseball", "pandas", "numpy", "requests"])
def test_the_runtime_tree_the_workflows_import_is_pinned(name):
    assert name in names(RUNTIME_PINS)


@pytest.mark.parametrize("name", ["pytest", "pyyaml"])
def test_the_test_tools_are_pinned_in_the_dev_file(name):
    assert name in names(DEV_PINS)


def missing_from(pinned: set[str], roots: set[str]) -> set[str]:
    missing, seen, queue = set(), set(), list(roots)
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        try:
            requires = metadata.requires(name) or []
        except metadata.PackageNotFoundError:
            continue
        for text in requires:
            requirement = Requirement(text)
            if requirement.marker is not None and not requirement.marker.evaluate(LINUX):
                continue
            wanted = canonicalize_name(requirement.name)
            if wanted not in pinned:
                missing.add(wanted)
            queue.append(wanted)
    return missing


def test_the_runtime_pins_close_over_what_they_require():
    pinned = names(RUNTIME_PINS)
    assert missing_from(pinned, pinned) == set()


def test_the_dev_pins_close_over_what_they_require():
    pinned = names(RUNTIME_PINS) | names(DEV_PINS)
    assert missing_from(pinned, pinned) == set()


def test_the_closure_check_fails_when_a_dependency_is_left_out():
    pinned = names(RUNTIME_PINS) - {"pandas"}
    assert "pandas" in missing_from(pinned, pinned)
