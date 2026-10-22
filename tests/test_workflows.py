"""P1.0-a: the baseline every workflow in `.github/workflows/` keeps (docs/plans/P1.md, section 3.1).

`violations(text)` reads one workflow file and returns the codes of the rules it breaks. The real files must break
none; for each rule a small broken workflow must break exactly that one, so the guard is shown to fail. The checks read
the text and the parsed YAML; they do not run anything and make no request. The guard is a check for an agent or a
person adding a workflow by mistake, not a security boundary: a secret passed through a script file, or a step that
prints a secret in a way these patterns do not read, is not seen. The repository setting "Require actions to be pinned
to a full-length commit SHA" is what makes GitHub itself refuse an unpinned action.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ROOT / ".github" / "workflows"
FILES = sorted([*WORKFLOW_DIR.glob("*.yml"), *WORKFLOW_DIR.glob("*.yaml")])

RUNNER = "ubuntu-24.04"
PUBLISH_ENVIRONMENT = "data-publish"

# The first major of each action whose `runs.using` is node24, read in the action.yml of the tags on 2026-10-21 with
# `gh api repos/actions/<name>/contents/action.yml?ref=<sha>`: checkout v4.2.2 is node20 and v5.0.0 node24; setup-python
# v5.6.0 node20, v6.0.0 node24; setup-node v4.4.0 node20, v5.0.0 node24; cache v4.3.0 node20, v5.0.0 node24;
# upload-artifact v5.0.0 node20, v6.0.0 node24; download-artifact v6.0.0 node20, v7.0.0 node24. Raise a number only after
# reading the tag.
NODE24_MAJOR = {
    "actions/checkout": 5,
    "actions/setup-python": 6,
    "actions/setup-node": 5,
    "actions/cache": 5,
    "actions/upload-artifact": 6,
    "actions/download-artifact": 7,
}

# Only the version comment is read from the text (YAML drops comments); which actions a workflow uses is read from the
# parsed YAML, so a long comment or a flow mapping cannot hide one.
USES_LINE = re.compile(r"""uses:\s*['"]?(?P<ref>[^\s'"#,}]+)['"]?[ \t]*(?:\#[ \t]*(?P<comment>\S+))?""")
SECRET_EXPRESSION = re.compile(r"\$\{\{.*?\bsecrets\b.*?\}\}", re.DOTALL)
SHA = re.compile(r"^[0-9a-f]{40}$")
VERSION = re.compile(r"^v(?P<major>\d+)\.\d+\.\d+$")
PRINTERS = re.compile(r"\b(echo|printf|print|cat|tee|Write-Host|Write-Output|Write-Error)\b", re.IGNORECASE)
# `printf '%s' "$KEY" > "$RUNNER_TEMP/key"` writes a file (how the deploy key reaches ssh); stderr, /dev/null and the
# `$GITHUB_*` files (the step summary and the outputs, which are not masked like the log) do not count as one
TO_A_FILE = re.compile(r"""(?<![2-9&>])>>?(?!>)\s*(?!&|/dev/(?:std\w+|null)|["']?\$\{?GITHUB)\S""")


class WorkflowLoader(yaml.SafeLoader):
    """YAML as GitHub reads a workflow: only true and false are booleans (PyYAML's YAML 1.1 also reads yes, no, on, off)."""


WorkflowLoader.yaml_implicit_resolvers = {
    first: [(tag, pattern) for tag, pattern in resolvers if tag != "tag:yaml.org,2002:bool"]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
WorkflowLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))


def load(text: str) -> dict:
    doc = yaml.load(text, Loader=WorkflowLoader)  # noqa: S506 - a SafeLoader subclass
    assert isinstance(doc, dict)
    return doc


def jobs_of(doc: dict) -> dict:
    return doc.get("jobs") or {}


def steps_of(job: dict) -> list:
    return job.get("steps") or []


def environment_name(job: dict) -> str | None:
    environment = job.get("environment")
    return environment.get("name") if isinstance(environment, dict) else environment


def uses_of(doc: dict) -> list[str]:
    """Every `uses:` value of the parsed workflow: the steps, and the reusable-workflow calls of the jobs."""
    refs = []
    for job in jobs_of(doc).values():
        if "uses" in job:
            refs.append(str(job["uses"]))
        refs.extend(str(step["uses"]) for step in steps_of(job) if "uses" in step)
    return refs


def unpinned_or_old_actions(doc: dict, text: str) -> set[str]:
    comments: dict[str, list[str | None]] = {}  # per ref, in the order of the file: each use needs its own comment
    for line in text.splitlines():
        for match in USES_LINE.finditer(line):
            comments.setdefault(match["ref"], []).append(match["comment"])
    found = set()
    for ref in uses_of(doc):
        if ref.startswith("./"):
            continue
        name, _, version = ref.partition("@")
        if not SHA.match(version):
            found.add("unpinned_action")
            continue
        queue = comments.get(ref, [])
        comment = VERSION.match((queue.pop(0) if queue else None) or "")
        floor = NODE24_MAJOR.get(name)
        if comment is None or floor is None or int(comment["major"]) < floor:
            found.add("old_or_unversioned_action")
    return found


def missing_permissions(doc: dict) -> bool:
    return "permissions" not in doc


def wrong_runner(doc: dict) -> bool:
    return any(job.get("runs-on") != RUNNER for job in jobs_of(doc).values())


def uses_pull_request_target(doc: dict) -> bool:
    on = doc.get("on")
    return "pull_request_target" in (on if isinstance(on, (dict, list)) else [on])


def push_without_branches(doc: dict) -> bool:
    on = doc.get("on")
    if isinstance(on, dict):
        if "push" not in on:
            return False
        push = on["push"]
        return not (isinstance(push, dict) and push.get("branches"))
    return "push" in (on if isinstance(on, list) else [on])


def writes_contents(doc: dict) -> bool:
    blocks = [doc.get("permissions"), *(job.get("permissions") for job in jobs_of(doc).values())]
    for block in blocks:
        if block == "write-all":
            return True
        if isinstance(block, dict) and str(block.get("contents")) == "write":
            return True
    return False


def secret_outside_publish_job(doc: dict) -> bool:
    outside = {key: value for key, value in doc.items() if key != "jobs"}
    if SECRET_EXPRESSION.search(json.dumps(outside, default=str)):
        return True
    for job in jobs_of(doc).values():
        if environment_name(job) == PUBLISH_ENVIRONMENT:
            continue
        if SECRET_EXPRESSION.search(json.dumps(job, default=str)) or job.get("secrets") == "inherit":
            return True
    return False


def secret_names(*blocks) -> set[str]:
    return {
        name
        for block in blocks
        if isinstance(block, dict)
        for name, value in block.items()
        if SECRET_EXPRESSION.search(str(value))
    }


def prints_a_secret(doc: dict) -> bool:
    for job in jobs_of(doc).values():
        for step in steps_of(job):
            script = step.get("run")
            if not script:
                continue
            names = secret_names(doc.get("env"), job.get("env"), step.get("env"))
            for line in str(script).splitlines():
                if not PRINTERS.search(line) or (TO_A_FILE.search(line) and not re.search(r"\btee\b", line)):
                    continue
                if SECRET_EXPRESSION.search(line):
                    return True
                for name in names:
                    if re.search(rf"\$\{{?{name}\b|\$env:{name}\b|env\.{name}\b", line):
                        return True
    return False


def checkout_keeps_credentials(doc: dict) -> bool:
    for job in jobs_of(doc).values():
        for step in steps_of(job):
            if str(step.get("uses", "")).startswith("actions/checkout@"):
                flag = (step.get("with") or {}).get("persist-credentials")
                if flag not in (False, "false"):
                    return True
    return False


def violations(text: str) -> set[str]:
    doc = load(text)
    found = unpinned_or_old_actions(doc, text)
    for code, broken in (
        ("no_permissions", missing_permissions(doc)),
        ("wrong_runner", wrong_runner(doc)),
        ("pull_request_target", uses_pull_request_target(doc)),
        ("push_without_branches", push_without_branches(doc)),
        ("contents_write", writes_contents(doc)),
        ("secret_outside_publish_job", secret_outside_publish_job(doc)),
        ("secret_printed", prints_a_secret(doc)),
        ("checkout_keeps_credentials", checkout_keeps_credentials(doc)),
    ):
        if broken:
            found.add(code)
    return found


CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"

CLEAN = f"""
name: sample
on:
  push:
    branches: [v2]
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-24.04
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
      - run: echo hello
  publish:
    runs-on: ubuntu-24.04
    environment: data-publish
    steps:
      - uses: {CHECKOUT}
        with:
          persist-credentials: false
      - env:
          KEY: ${{{{ secrets.DATA_DEPLOY_KEY }}}}
        run: printf '%s' "$KEY" > "$RUNNER_TEMP/key"
"""


def broken(old: str, new: str) -> str:
    assert old in CLEAN, old
    return CLEAN.replace(old, new, 1)


BROKEN = {
    "unpinned_action": broken(CHECKOUT, "actions/checkout@v7"),
    "old_or_unversioned_action": broken(CHECKOUT, "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2"),
    "no_permissions": broken("permissions:\n  contents: read\n", ""),
    "wrong_runner": broken("runs-on: ubuntu-24.04\n    steps:\n      - uses: " + CHECKOUT, "runs-on: ubuntu-latest\n    steps:\n      - uses: " + CHECKOUT),
    "pull_request_target": broken("on:\n  push:\n    branches: [v2]\n", "on:\n  pull_request_target:\n"),
    "push_without_branches": broken("  push:\n    branches: [v2]\n", "  push:\n    paths: ['a']\n"),
    "contents_write": broken("contents: read", "contents: write"),
    "secret_outside_publish_job": broken("      - run: echo hello\n", "      - env:\n          TOKEN: ${{ secrets.OTHER }}\n        run: ./use.sh\n"),
    "secret_printed": broken('printf \'%s\' "$KEY" > "$RUNNER_TEMP/key"', 'echo "$KEY"'),
    "checkout_keeps_credentials": broken(CHECKOUT + "\n        with:\n          persist-credentials: false\n      - run: echo hello", CHECKOUT + "\n      - run: echo hello"),
}


def test_the_clean_sample_breaks_no_rule():
    assert violations(CLEAN) == set()


@pytest.mark.parametrize("code", sorted(BROKEN))
def test_each_rule_fails_on_its_own_broken_workflow(code):
    assert violations(BROKEN[code]) == {code}


def test_every_rule_has_a_broken_sample():
    assert set(BROKEN) == {
        "unpinned_action",
        "old_or_unversioned_action",
        "no_permissions",
        "wrong_runner",
        "pull_request_target",
        "push_without_branches",
        "contents_write",
        "secret_outside_publish_job",
        "secret_printed",
        "checkout_keeps_credentials",
    }


BUILD_STEP = "      - run: echo hello\n"
PUBLISH_STEP = """run: printf '%s' "$KEY" > "$RUNNER_TEMP/key"\n"""
FIRST_CHECKOUT = "      - uses: " + CHECKOUT + "\n        with:\n          persist-credentials: false\n"
OLD_SHA = "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683"

def uncomment_second_checkout(text: str) -> str:
    """The same pinned ref used a second time with no version comment: each use needs its own."""
    second = text.index(CHECKOUT, text.index(CHECKOUT) + 1)
    return text[:second] + CHECKOUT.split(" #")[0] + text[second + len(CHECKOUT) :]


OTHER_FORMS = [
    # the trigger
    (lambda text: text.replace("on:\n  push:\n    branches: [v2]\n", "on: push\n"), "push_without_branches"),
    (lambda text: text.replace("on:\n  push:\n    branches: [v2]\n", "on: [push, workflow_dispatch]\n"), "push_without_branches"),
    (lambda text: text.replace("    branches: [v2]\n", "    branches-ignore: [main]\n"), "push_without_branches"),
    (lambda text: text.replace("on:\n  push:\n    branches: [v2]\n", "on: [pull_request_target]\n"), "pull_request_target"),
    # permissions and the runner
    (lambda text: text.replace("contents: read", "write-all"), "contents_write"),
    (lambda text: text.replace("runs-on: ubuntu-24.04", "runs-on: [self-hosted]", 1), "wrong_runner"),
    # actions: a long comment, a flow mapping and a quoted ref must not hide an unpinned or old one
    (lambda text: text.replace(CHECKOUT, "actions/checkout@v4 # pinned by tag", 1), "unpinned_action"),
    (lambda text: text.replace(CHECKOUT, OLD_SHA + " # v4.2.2 old", 1), "old_or_unversioned_action"),
    (lambda text: text.replace(CHECKOUT, '"actions/checkout@v4"', 1), "unpinned_action"),
    (lambda text: text.replace(CHECKOUT, OLD_SHA, 1), "old_or_unversioned_action"),
    (lambda text: text.replace(FIRST_CHECKOUT, "      - {uses: actions/checkout@v4, with: {persist-credentials: false}}\n", 1), "unpinned_action"),
    (lambda text: text.replace(CHECKOUT, "docker://alpine:3", 1), "unpinned_action"),
    (lambda text: text.replace("    runs-on: ubuntu-24.04\n    steps:", "    uses: org/repo/.github/workflows/x.yml@main\n    steps:", 1), "unpinned_action"),
    (lambda text: uncomment_second_checkout(text), "old_or_unversioned_action"),
    # secrets outside the publish job, in every spelling
    (lambda text: text.replace(BUILD_STEP, '      - run: echo "${{ secrets.OTHER }}"\n', 1), "secret_printed"),
    (lambda text: text.replace(BUILD_STEP, "      - run: ./use.sh ${{ secrets['OTHER'] }}\n", 1), "secret_outside_publish_job"),
    (lambda text: text.replace(BUILD_STEP, "      - run: ./use.sh ${{ toJSON(secrets) }}\n", 1), "secret_outside_publish_job"),
    (lambda text: text.replace("    runs-on: ubuntu-24.04\n    steps:", "    secrets: inherit\n    runs-on: ubuntu-24.04\n    steps:", 1), "secret_outside_publish_job"),
    # a secret printed to the log, or put where it is not masked like the log
    (lambda text: text.replace(PUBLISH_STEP, 'run: echo "$KEY" >> "$GITHUB_STEP_SUMMARY"\n'), "secret_printed"),
    (lambda text: text.replace(PUBLISH_STEP, 'run: echo "key=$KEY" >> $GITHUB_OUTPUT\n'), "secret_printed"),
    (lambda text: text.replace(PUBLISH_STEP, 'run: echo "$KEY" 2>/dev/null\n'), "secret_printed"),
    (lambda text: text.replace(PUBLISH_STEP, 'run: echo "$KEY" | tee "$RUNNER_TEMP/key"\n'), "secret_printed"),
    (lambda text: text.replace(PUBLISH_STEP, 'run: printf "%s" "${{ secrets.DATA_DEPLOY_KEY }}" >&2\n'), "secret_printed"),
    # checkout
    (lambda text: text.replace("persist-credentials: false", "persist-credentials: true", 1), "checkout_keeps_credentials"),
    (lambda text: text.replace("persist-credentials: false", "persist-credentials: no", 1), "checkout_keeps_credentials"),
]


@pytest.mark.parametrize("mutation,code", OTHER_FORMS)
def test_other_forms_of_the_same_rules_fail_with_that_rule(mutation, code):
    changed = mutation(CLEAN)

    assert changed != CLEAN
    assert code in violations(changed)


def test_the_file_exemption_of_a_printed_secret_is_only_for_a_real_file():
    ok = CLEAN.replace(PUBLISH_STEP, 'run: printf "%s\\n" "$KEY" >> "$RUNNER_TEMP/key"\n')

    assert ok != CLEAN and violations(ok) == set()


def test_a_secret_bound_in_the_workflow_env_and_printed_is_seen():
    text = CLEAN.replace("permissions:\n  contents: read\n", "permissions:\n  contents: read\nenv:\n  KEY: ${{ secrets.X }}\n", 1)
    text = text.replace("      - run: echo hello\n", "      - run: echo $KEY\n", 1)
    assert {"secret_printed", "secret_outside_publish_job"} <= violations(text)


def test_a_local_action_is_not_an_unpinned_action():
    assert violations(CLEAN.replace("      - run: echo hello\n", "      - uses: ./.github/actions/local\n", 1)) == set()


def test_a_workflow_with_workflow_dispatch_only_needs_no_branches():
    assert violations(CLEAN.replace("on:\n  push:\n    branches: [v2]\n", "on:\n  workflow_dispatch:\n", 1)) == set()


def test_there_is_at_least_one_workflow_to_check():
    assert FILES, "no workflow files found"


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_every_real_workflow_breaks_no_rule(path):
    assert violations(path.read_text(encoding="utf-8")) == set(), path.name


def test_the_probe_workflow_and_the_components_job_pass_the_rules_today():
    probe = (WORKFLOW_DIR / "statcast-probe.yml").read_text(encoding="utf-8")
    assert violations(probe) == set()
    components = load((WORKFLOW_DIR / "tests.yml").read_text(encoding="utf-8"))["jobs"]["components"]
    sample = {"on": {"workflow_dispatch": None}, "permissions": {"contents": "read"}, "jobs": {"components": components}}
    assert not checkout_keeps_credentials(sample) and not wrong_runner(sample)


def test_the_tests_workflow_has_the_site_job_with_the_three_checks():
    jobs = load((WORKFLOW_DIR / "tests.yml").read_text(encoding="utf-8"))["jobs"]
    assert {"pytest", "components", "site"} <= set(jobs)
    commands = "\n".join(str(step.get("run", "")) for step in steps_of(jobs["site"]))
    for command in ("npm ci", "npx tsc --noEmit", "npm run lint", "npm run build"):
        assert command in commands
    assert "npm test" in "\n".join(str(step.get("run", "")) for step in steps_of(jobs["components"]))
