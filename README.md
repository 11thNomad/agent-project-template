# agent-project-template

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

You need Python 3.10 or later and git. Set up once, from this folder:

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Then one command makes a project. Run it from the folder that contains this one:

```
agent-project-template\.venv\Scripts\copier copy agent-project-template my-new-project
```

These commands are written for Windows. On macOS or Linux, use `.venv/bin/` in place of `.venv\Scripts\`.

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
agent-project-template\.venv\Scripts\copier update my-new-project
```

Copier finds the template through the path saved in the project's `.copier-answers.yml`. That path is the one typed in the copy command, so it only resolves from the folder where that command was run. Do not edit `.copier-answers.yml` by hand.

## Run the tests

```
.venv\Scripts\python -m pytest
```

The tests run offline and make no model calls. They render the template into a temporary folder and check that the required files exist, that `SPEC.md` and `CLAUDE.md` have every required section, that the answers are substituted, that no template markup is left, that the gated paths given as an answer appear under "Approval gates", and that an answer with no gated paths is rejected.

Tested with Copier 9.19.1 and pytest 9.2.0 on Python 3.13.1 and Windows 11. `requirements.txt` pins every installed package.

## AI involvement

This template, its tests and this README were drafted with AI assistance (Claude).

## Licence

Apache-2.0. See `LICENSE`. The same text is in `template/LICENSE` and becomes the licence file of each new project.
