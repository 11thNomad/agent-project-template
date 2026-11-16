# agent-project-template

![tests](https://github.com/11thNomad/agent-project-template/actions/workflows/tests.yml/badge.svg)

A [Copier](https://copier.readthedocs.io/) template for projects that are built by several AI agent sessions under one owner. A project made from it starts with three things: a spec skeleton, rules for builder sessions, and approval gates.

## What a new project contains

| File | What it is |
| --- | --- |
| `SPEC.md` | A spec skeleton. Each section has a short note on what belongs there: purpose and scope, exit criteria that code can check, architecture, contracts and data formats, fixed constraints and approval gates, open questions, and a build-order table with a "done when" for each step. |
| `CLAUDE.md` | Rules for builder sessions: dated owner decisions, amendments to the spec, hard rules, approval gates, how work is organised, evidence and improvement, and commands. |
| `LICENSE` | The Apache License 2.0, as published at apache.org. |
| `README.md` | A short description of the project. |
| `.gitignore` | Ignores secrets files, virtual environments and caches. |
| `.copier-answers.yml` | The answers given to Copier. Copier needs it to update the project later. |

The rules describe one way of working. One orchestrator session holds the build order and hands out one step at a time. Builder sessions do one step, with tests, then stop and report. The owner approves changes to gated paths and every real-world action. Results come from code and tests, never from a session's own report.

## Make a new project

You need git and Copier. Install Copier first. Its [installation instructions](https://copier.readthedocs.io/en/stable/#installation) give the Python and git versions it needs and the ways to install it. This template is tested with Copier 9.19.1.

Then one command makes a project. Run it from the folder where the new project should go:

```
copier copy gh:11thNomad/agent-project-template my-new-project
```

`gh:11thNomad/agent-project-template` is Copier's short form for `https://github.com/11thNomad/agent-project-template`. Copier fetches the template from that address, so you do not need a local copy of this repository.

Copier asks four questions:

| Question | Answer |
| --- | --- |
| `project_name` | The project's name, as it should appear in headings. |
| `purpose` | One line saying what the project is for. |
| `github_handle` | The owner's GitHub handle, without the @. |
| `gated_paths` | Paths that need the owner's approval to change, separated by commas. The default is `CLAUDE.md, SPEC.md`. At least one path is needed: Copier rejects an answer that is empty or holds only spaces and commas. |

To skip the prompts, pass each answer with `-d`, for example `-d "gated_paths=CLAUDE.md, SPEC.md, contracts/"`.

Copier uses the template's latest git tag. When the template has no tags, it uses the latest commit.

## Pull template changes into a project later

The project must be a git repository with nothing uncommitted. Run this from the same folder as the copy command:

```
copier update my-new-project
```

Copier finds the template through the address saved in the project's `.copier-answers.yml`. That address is the one typed in the copy command. Do not edit `.copier-answers.yml` by hand.

## Run the tests

GitHub runs the tests on every push to `main` and on every pull request. The workflow is `.github/workflows/tests.yml`. The badge at the top of this page shows its status.

To run the tests yourself, you need a local copy of this repository. The tests support Python 3.11, 3.12, 3.13 and 3.14. Set up once, from this folder:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Then run the tests:

```
.venv\Scripts\python -m pytest
```

These commands are written for Windows. On macOS or Linux, use `.venv/bin/` in place of `.venv\Scripts\`.

The tests run offline and make no model calls. They render the template into a temporary folder and check that the required files exist, that `SPEC.md` and `CLAUDE.md` have every required section, that the answers are substituted, that no template markup is left, that the gated paths given as an answer appear under "Approval gates", and that an answer with no gated paths is rejected. They also check that the workflow agrees with this README.

The workflow runs the commands above on Python 3.11, 3.12, 3.13 and 3.14, each on Linux (`ubuntu-latest`) and on Windows (`windows-latest`). It does not cover macOS.

Tested with Copier 9.19.1 and pytest 9.2.0 on Python 3.13.1 and Windows 11. `requirements.txt` pins every installed package. The pinned packages do not install on Python 3.10. Python 3.15 is not covered: the pinned PyYAML has no wheel for it, so pip has to build it from source.

## AI involvement

This template, its tests, its GitHub workflow and this README were drafted with AI assistance (Claude).

## Licence

Apache-2.0. See `LICENSE`. The same text is in `template/LICENSE` and becomes the licence file of each new project.
