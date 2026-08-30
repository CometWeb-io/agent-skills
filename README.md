# CometWeb Agent Skills

Private canonical monorepo for Comet-owned agent skills used across ChatGPT, Codex, API/agent workflows, and the CometWeb operating system.

## Source of truth

`skills/<skill-name>/` is the canonical source. Installed ChatGPT skills and generated `skill.zip` files are release artifacts only.

## Current foundation

| Skill | Version | Role |
| --- | ---: | --- |
| `cometweb-context` | 1.0.0 | Fresh, provenance-aware CometWeb context gateway |
| `skill-orchestrator` | 1.1.1 | Single-thread multi-skill router with optional context preflight |
| `skill-orchestrator-multiagent` | 1.1.0 | Isolated subagent-per-skill router with context preflight |
| `evidence-researcher` | 2.0.0 | Auditable evidence, provenance, falsifier, freshness, and contradiction layer |
| `ai-council` | 5.1.1 | Consequential decision layer with gates, temporal evidence, and living decisions |

The migration backlog is tracked in `registry/skills.json`.

## Repository layout

```text
skills/                  self-contained skill packages
registry/skills.json     catalog, lifecycle, migration backlog
tooling/                 repo-wide validators and packager
docs/                    architecture, standards, migration notes
.github/workflows/       CI gates
```

## Development loop

```bash
python3 -m pip install -r requirements-dev.txt
python3 tooling/validate_repo.py
python3 -m pytest -q tooling/tests skills/*/tests
python3 tooling/package_skill.py cometweb-context
python3 tooling/package_skill.py skill-orchestrator
python3 tooling/package_skill.py skill-orchestrator-multiagent
python3 tooling/package_skill.py evidence-researcher
python3 tooling/package_skill.py ai-council
```

Packages are written to `dist/<skill>/skill.zip` and are ignored by Git.

## Rules

- Keep each skill independently distributable.
- `SKILL.md` frontmatter contains only `name` and `description`.
- Active skills have `VERSION` and `CHANGELOG.md`.
- Behavior changes are test-first.
- Never commit secrets, `.env` files, credential stores, customer exports, or private vault contents.
- Do not hard-code live operational state when the skill can retrieve it from a system of record.
- Preserve typed boundaries: context is not evidence; evidence is not a decision; audit findings are not a release verdict.

## GitHub target

Intended remote: `MaciejZet/agent-skills` — **private**, default branch `main`.

## Publish the private GitHub remote

When GitHub CLI is authenticated locally:

```bash
./tooling/bootstrap_github.sh
```

This creates `MaciejZet/agent-skills` as a private repository if it does not exist, adds `origin`, and pushes `main`.
