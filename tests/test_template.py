"""Render the template with Copier and check the generated project.

The tests run offline and make no model calls. Each render works from a plain
copy of `copier.yml` and `template/`, so the tests check the files as they are
on disk and do not depend on git state (commits, tags or uncommitted changes).
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest
from copier import run_copy

REPO_ROOT = Path(__file__).resolve().parent.parent

ANSWERS = {
    "project_name": "Example Project",
    "purpose": "Checks that the template renders the answers it is given.",
    "github_handle": "example-owner",
    "gated_paths": "CLAUDE.md, SPEC.md, contracts/, src/release.py",
}

REQUIRED_FILES = [
    "SPEC.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    ".gitignore",
    # Copier needs this file to pull later template changes into the project.
    ".copier-answers.yml",
]

SPEC_HEADINGS = [
    "Purpose and scope",
    "What done looks like",
    "Architecture",
    "Contracts and data formats",
    "Fixed constraints and approval gates",
    "Open questions",
    "Build order and handoff",
]

CLAUDE_HEADINGS = [
    "Owner decisions",
    "Amendments to the spec",
    "Hard rules",
    "Approval gates",
    "How work is organised",
    "Evidence and improvement",
    "Commands",
]

JINJA_MARKERS = ["{{", "}}", "{%", "%}", "{#", "#}"]


def render(tmp_path: Path, answers: dict[str, str]) -> Path:
    """Render the template into a new folder under tmp_path and return it."""
    source = tmp_path / "template-source"
    source.mkdir()
    shutil.copy2(REPO_ROOT / "copier.yml", source / "copier.yml")
    shutil.copytree(REPO_ROOT / "template", source / "template")
    destination = tmp_path / "generated-project"
    run_copy(str(source), destination, data=answers, defaults=True, quiet=True)
    return destination


def read(project: Path, name: str) -> str:
    return (project / name).read_text(encoding="utf-8")


def section_headings(text: str) -> list[str]:
    """The level-2 headings of a Markdown file, in order."""
    return re.findall(r"^## (.+)$", text, flags=re.MULTILINE)


def section_body(text: str, heading: str) -> str:
    """The text between one level-2 heading and the next."""
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, f"no section headed {heading!r}"
    return match.group(1)


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return render(tmp_path_factory.mktemp("render"), ANSWERS)


@pytest.mark.parametrize("name", REQUIRED_FILES)
def test_required_file_exists(project: Path, name: str) -> None:
    path = project / name
    assert path.is_file(), f"{name} was not generated"
    assert path.stat().st_size > 0, f"{name} is empty"


def test_spec_has_every_required_section(project: Path) -> None:
    assert section_headings(read(project, "SPEC.md")) == SPEC_HEADINGS


def test_claude_has_every_required_section(project: Path) -> None:
    assert section_headings(read(project, "CLAUDE.md")) == CLAUDE_HEADINGS


def test_build_order_is_a_table_with_done_when(project: Path) -> None:
    build_order = section_body(read(project, "SPEC.md"), "Build order and handoff")
    assert "| Step | What is built | Done when |" in build_order


@pytest.mark.parametrize("name", ["SPEC.md", "CLAUDE.md", "README.md"])
def test_project_name_and_purpose_are_substituted(project: Path, name: str) -> None:
    text = read(project, name)
    assert text.startswith(f"# {ANSWERS['project_name']}")
    assert ANSWERS["purpose"] in text


@pytest.mark.parametrize("name", ["CLAUDE.md", "README.md"])
def test_github_handle_is_substituted(project: Path, name: str) -> None:
    assert f"`{ANSWERS['github_handle']}`" in read(project, name)


def test_no_template_markup_is_left(project: Path) -> None:
    files = [path for path in project.rglob("*") if path.is_file()]
    assert files, "the render produced no files"
    leftovers = []
    for path in files:
        relative = path.relative_to(project).as_posix()
        if path.suffix == ".jinja":
            leftovers.append(f"{relative}: still has the .jinja suffix")
        if any(marker in path.name for marker in JINJA_MARKERS):
            leftovers.append(f"{relative}: markup in the file name")
        text = path.read_text(encoding="utf-8")
        for marker in JINJA_MARKERS:
            if marker in text:
                leftovers.append(f"{relative}: contains {marker!r}")
    assert leftovers == []


def test_gated_paths_from_the_answers_are_listed(project: Path) -> None:
    gates = section_body(read(project, "CLAUDE.md"), "Approval gates")
    for path in ["CLAUDE.md", "SPEC.md", "contracts/", "src/release.py"]:
        assert f"- `{path}`\n" in gates


def test_a_gated_path_given_as_an_answer_appears_in_the_gates(tmp_path: Path) -> None:
    # A path that appears nowhere in the template itself, so it can only have
    # come from the answer.
    answers = {**ANSWERS, "gated_paths": "infra/deploy.yml"}
    project = render(tmp_path, answers)
    gates = section_body(read(project, "CLAUDE.md"), "Approval gates")
    listed = re.findall(r"^- `(.+)`$", gates, flags=re.MULTILINE)
    assert listed == ["infra/deploy.yml"]
