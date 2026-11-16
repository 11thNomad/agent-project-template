"""Check that the GitHub workflow and README.md agree.

The tests run offline. They read `.github/workflows/tests.yml` and `README.md`
from disk and compare what each one says. They do not run the workflow, so
they do not show that it passes on GitHub.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "tests.yml"
README_PATH = REPO_ROOT / "README.md"

# Runner labels start with the name GitHub gives the system's image.
SYSTEM_BY_LABEL_PREFIX = {"ubuntu-": "Linux", "windows-": "Windows", "macos-": "macOS"}

VERSION_LIST = r"(\d+\.\d+(?:(?:, | or | and )\d+\.\d+)*)"


def system_of(label: str) -> str:
    """The system a runner label such as `ubuntu-latest` stands for."""
    for prefix, system in SYSTEM_BY_LABEL_PREFIX.items():
        if label.startswith(prefix):
            return system
    raise AssertionError(f"cannot tell which system the runner {label!r} is")


def versions_after(text: str, lead: str) -> list[str]:
    """The Python versions the README lists straight after `lead`."""
    match = re.search(re.escape(lead) + " " + VERSION_LIST, text)
    assert match, f"the README no longer has {lead!r} followed by Python versions"
    return re.findall(r"\d+\.\d+", match.group(1))


def matrix_rows(job: dict) -> list[dict[str, str]]:
    """One row for each job GitHub starts from the matrix.

    Follows the rule in GitHub's documentation for `include`: an entry is added
    to each combination whose own values it does not overwrite.
    """
    matrix = job["strategy"]["matrix"]
    assert "exclude" not in matrix, "matrix_rows does not handle `exclude`"
    rows = [
        {"os": os_label, "python-version": version}
        for os_label in matrix["os"]
        for version in matrix["python-version"]
    ]
    for entry in matrix.get("include", []):
        matching = [
            row
            for row in rows
            if all(row[key] == entry[key] for key in ("os", "python-version") if key in entry)
        ]
        assert matching, f"the include entry {entry} would start a job of its own"
        for row in matching:
            row.update(entry)
    return rows


def run_commands(job: dict, row: dict[str, str]) -> list[str]:
    """The command lines the job runs for one matrix row, in order."""
    commands = []
    for step in job["steps"]:
        if "run" in step:
            expanded = re.sub(
                r"\$\{\{\s*matrix\.([\w-]+)\s*\}\}",
                lambda match: row[match.group(1)],
                step["run"],
            )
            assert "${{" not in expanded, f"cannot expand {step['run']!r}"
            commands.extend(expanded.splitlines())
    return commands


@pytest.fixture(scope="module")
def workflow_text() -> str:
    assert WORKFLOW_PATH.is_file(), "the workflow file does not exist"
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow(workflow_text: str) -> dict:
    return yaml.safe_load(workflow_text)


@pytest.fixture(scope="module")
def job(workflow: dict) -> dict:
    """The workflow's one job. A second job needs tests of its own."""
    jobs = workflow["jobs"]
    assert len(jobs) == 1, f"expected one job, found {sorted(jobs)}"
    return next(iter(jobs.values()))


@pytest.fixture(scope="module")
def tests_section() -> str:
    """The README's "Run the tests" section."""
    match = re.search(
        r"^## Run the tests\n(.*?)(?=^## |\Z)",
        README_PATH.read_text(encoding="utf-8"),
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, 'the README has no "Run the tests" section'
    return match.group(1)


def test_workflow_exists_and_parses_as_yaml(workflow: dict) -> None:
    assert isinstance(workflow, dict)
    assert workflow["jobs"]


def test_workflow_runs_on_push_to_main_and_on_pull_requests(
    workflow: dict, tests_section: str
) -> None:
    # PyYAML follows YAML 1.1, which reads the bare key `on` as the boolean true.
    triggers = workflow[True]
    # A push filter that names only `main`, and no filter on pull requests.
    assert triggers == {"push": {"branches": ["main"]}, "pull_request": None}
    assert "on every push to `main` and on every pull request" in tests_section


def test_workflow_permissions_are_read_only(workflow: dict, job: dict) -> None:
    assert workflow["permissions"] == {"contents": "read"}
    assert "permissions" not in job, "a job must not widen the workflow's permissions"


def test_workflow_runs_the_readme_commands(job: dict, tests_section: str) -> None:
    blocks = re.findall(r"^```\n(.*?)^```$", tests_section, flags=re.MULTILINE | re.DOTALL)
    readme_commands = [line for block in blocks for line in block.splitlines()]
    assert readme_commands[-1].endswith("python -m pytest"), "the README lost its test command"

    # The README gives the commands for Windows and one change for other systems.
    change = re.search(r"use `(.+?)` in place of `(.+?)`", tests_section)
    assert change, "the README no longer says how the commands change off Windows"
    new, old = change.groups()
    assert any(old in command for command in readme_commands)

    rows = matrix_rows(job)
    assert rows
    for row in rows:
        if system_of(row["os"]) == "Windows":
            expected = readme_commands
        else:
            expected = [command.replace(old, new) for command in readme_commands]
        assert run_commands(job, row) == expected, f"wrong commands for {row}"


def test_a_failing_command_fails_the_workflow(job: dict) -> None:
    # `if` can skip a step and `continue-on-error` can hide its failure.
    for holder in [job, *job["steps"]]:
        assert "if" not in holder
        assert "continue-on-error" not in holder


def test_workflow_covers_the_python_versions_the_readme_claims(
    job: dict, tests_section: str
) -> None:
    in_matrix = job["strategy"]["matrix"]["python-version"]
    assert all(isinstance(version, str) for version in in_matrix), "quote the versions"
    assert versions_after(tests_section, "The tests support Python") == in_matrix
    assert versions_after(tests_section, "runs the commands above on Python") == in_matrix

    # The version the README says the tests were run with by hand.
    by_hand = re.search(r"Tested with .+? on Python (\d+\.\d+)", tests_section)
    assert by_hand, 'the README lost its "Tested with" sentence'
    assert by_hand.group(1) in in_matrix

    # The matrix only counts if each job installs the version it names.
    setup = [step for step in job["steps"] if step.get("uses", "").startswith("actions/setup-python@")]
    assert len(setup) == 1
    assert setup[0]["with"]["python-version"] == "${{ matrix.python-version }}"


def test_workflow_covers_the_systems_the_readme_claims(job: dict, tests_section: str) -> None:
    in_matrix = job["strategy"]["matrix"]["os"]
    assert job["runs-on"] == "${{ matrix.os }}"

    sentence = re.search(r"runs the commands above on Python .+", tests_section)
    assert sentence, "the README no longer says what the workflow covers"
    claimed = re.findall(r"(\w+) \(`([\w.-]+)`\)", sentence.group(0))
    assert claimed, "the README no longer names the workflow's runners"
    assert [label for _, label in claimed] == in_matrix
    for system, label in claimed:
        assert system_of(label) == system

    # The system the README says the tests were run on by hand.
    by_hand = re.search(r"Tested with .+? on Python [\d.]+ and (\w+)", tests_section)
    assert by_hand, 'the README lost its "Tested with" sentence'
    assert by_hand.group(1) in {system for system, _ in claimed}


def test_every_action_is_pinned_to_a_full_commit_sha(workflow_text: str, job: dict) -> None:
    used = [step["uses"] for step in job["steps"] if "uses" in step]
    assert used, "the workflow uses no actions"
    for action in used:
        assert re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", action), f"{action} is not pinned"

    # Each `uses` line carries its version in a comment, which the YAML parser drops.
    lines = [line.strip() for line in workflow_text.splitlines() if "uses:" in line]
    assert len(lines) == len(used)
    for line in lines:
        assert re.fullmatch(r"(- )?uses: \S+@[0-9a-f]{40} # v\d+\.\d+\.\d+", line), line
