# CometWeb Agent Skills

[![Validate](https://github.com/CometWeb-io/agent-skills/actions/workflows/validate.yml/badge.svg)](https://github.com/CometWeb-io/agent-skills/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-informational.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/skills-18-informational.svg)](#skills)

Schema-driven agent skills for research, product operations, QA, release
readiness, and evidence-based decisions.

This repository contains 18 reusable skill packages for Cursor, Claude Code,
Codex, and other compatible agent hosts. Each skill combines clear routing
guidance with structured outputs, references, scripts, and tests where
deterministic behavior matters.

This is an open-source skill toolkit, not a hosted automation product. It does
not include built-in Apollo, LinkedIn, CRM, or outbound-campaign execution,
and it does not send messages or mutate external systems by itself. A host or
connector must provide those capabilities explicitly, with the user's
authorization.

**Version:** `2.0.0` · **License:** [MIT](LICENSE)

## Why these skills

Agent skills should do more than provide a large prompt. CometWeb skills are
designed to:

- route a request to the right specialist and define when not to use it;
- separate context, evidence, decisions, audits, and release verdicts;
- produce reusable, structured handoffs between skills;
- keep important behavior enforceable through scripts, schemas, tests, and evals;
- work across multiple agent hosts without duplicating the source package.

## Skills

### Foundation and orchestration

| Skill | Use it for |
| --- | --- |
| [`ai-council`](skills/ai-council/) | Evidence-governed decisions, risk gates, forecasts, and GO / TEST / DEFER verdicts. |
| [`cometweb-context`](skills/cometweb-context/) | Fresh, provenance-aware context snapshots before work that depends on current project state. |
| [`evidence-researcher`](skills/evidence-researcher/) | Claim decomposition, source verification, falsifiers, contradictions, and Evidence Packs. |
| [`portfolio-operator`](skills/portfolio-operator/) | Cross-project focus, capacity conflicts, and pause / delegate decisions. |
| [`skill-orchestrator`](skills/skill-orchestrator/) | Multi-skill workflows with ordered steps and CW-AIP handoffs. |
| [`skill-orchestrator-multiagent`](skills/skill-orchestrator-multiagent/) | Isolated subagent execution for multi-skill workflows. |

### Product, research, and partnerships

| Skill | Use it for |
| --- | --- |
| [`ai-humanize`](skills/ai-humanize/) | Natural English and Polish rewrites that preserve meaning and voice. |
| [`competitive-intelligence`](skills/competitive-intelligence/) | Competitor watchlists, change detection, and recurring delta digests. |
| [`design-partner-finder`](skills/design-partner-finder/) | Finding, qualifying, and managing design partners and early adopters. |
| [`product-operator`](skills/product-operator/) | Weekly product control loops, roadmap drift, and now / next / later / stop actions. |
| [`product-teardown`](skills/product-teardown/) | Evidence-backed product, UX, architecture, and implementation pattern analysis. |
| [`repo-to-roadmap`](skills/repo-to-roadmap/) | Whole-project baselines, gap inventories, dependencies, and target-state roadmaps. |

### Publication, operations, QA, and release

| Skill | Use it for |
| --- | --- |
| [`customer-ops`](skills/customer-ops/) | Support triage, incidents, account risk, commitments, and engineering handoffs. |
| [`ebook-publisher`](skills/ebook-publisher/) | Research-backed ebooks, white papers, workbooks, and publication QA. |
| [`longform-publisher`](skills/longform-publisher/) | Canonical long-form manuscripts and release-ready derived documents. |
| [`release-readiness`](skills/release-readiness/) | Candidate-bound production gates and GO / GO_WITH_CONTROLS / NO_GO / DEFER verdicts. |
| [`seo-geo-aeo-maxxing`](skills/seo-geo-aeo-maxxing/) | Multi-pillar SEO / GEO / AEO visibility audits. |
| [`web-app-auditor`](skills/web-app-auditor/) | Evidence-driven click-through QA for websites and web applications. |

## Installation

Clone the repository, then run the installer for the hosts you use:

```bash
git clone https://github.com/CometWeb-io/agent-skills.git
cd agent-skills
./scripts/install-all.sh
```

`install-all.sh` installs the skills for Cursor, Claude Code, Codex, Qwen
Code, Qoder, and Lingma. To install selected hosts instead:

```bash
./scripts/install-cursor.sh
./scripts/install-codex.sh
./scripts/install-claude.sh
```

The installers discover every package under `skills/*/SKILL.md`, so newly
registered skills do not require a hard-coded installer list.

## Cursor Marketplace

To add the repository as a Cursor marketplace:

1. Open **Settings → Plugins → Add marketplace**.
2. Enter `CometWeb-io/agent-skills`.
3. Select the marketplace and install `CometWeb Agent Skills`.

The repository includes the Cursor marketplace manifests under
`.cursor-plugin/`. The Claude Code marketplace manifests remain under
`.claude-plugin/`.

## Usage

Describe the outcome you need in your agent host. The routing metadata will
select the specialist when the request matches its scope. You can also name a
skill directly:

```text
Build an Evidence Pack for these pricing claims, including falsifiers.
```

```text
Audit the registration flow, then run release readiness on the candidate.
```

For multi-step work, use `skill-orchestrator`; use
`skill-orchestrator-multiagent` when each specialist should run in isolation.

### What the quality claims mean

- Registry metadata, schemas, validators, routing evals, and unit tests are
  checked in CI.
- Those checks prove deterministic contracts and repository consistency; they
  do not prove that every model, host, connector, or workflow produces a
  correct result in production.
- Runtime compatibility is capability-dependent. A host may load a skill while
  still lacking browser, filesystem, code-execution, or connector access.
- External side effects belong at the host boundary. Skills may prepare a
  draft, decision, or handoff; the host controls authorization and execution.

## What a skill costs, and what its tests are worth

Correctness is gated in twelve places. Two things the gates themselves depend
on are measured rather than assumed.

Context is the resource that decides whether a skill can be loaded at all.
[`docs/generated-context-budget.md`](docs/generated-context-budget.md) records
what each SKILL.md costs a host at the front door, and what it keeps behind it
in references. `tooling/context_budget.py --check` fails when a front door grows
without that cost being accepted deliberately.

A passing test suite is worth only what it would fail on.
[`docs/generated-eval-strength.md`](docs/generated-eval-strength.md) records, per
skill, how many of its kernel's branches its own eval harness actually holds —
measured by removing one branch at a time and checking whether a case goes red.
`tooling/eval_strength.py --check` fails when a rule stops being pinned.

## Repository structure

```text
skills/<name>/       Self-contained skill packages
registry/            Routing, lifecycle, and host compatibility metadata
protocol/            CW-AIP v1 compatibility and CW-AIP v2 schemas
tooling/             Validators, compatibility checks, and adapter tooling
evals/               Routing and behavior evaluation fixtures
fixtures/            Shared synthetic inputs used by tests and evals
profiles/            Deployment profiles consumed by the registry
extras/              Host-specific routing assets
scripts/             Per-host installers
docs/                Protocol notes and generated reference tables
```

Each package can contain a `SKILL.md`, references, scripts, tests, examples,
and host metadata. The registry describes the package contract; the skill
directory contains its implementation and supporting evidence. Business
specific workflows use the same CW-AIP handoff envelope; this repository does
not maintain a second business-only protocol.

## Development and validation

Install the development dependencies:

```bash
python3 -m pip install -r requirements-dev.txt
```

Run the test suite:

```bash
python3 -m pytest -q
```

Run the local repository gate, with per-check logs and a JUnit report outside
the checkout:

```bash
python3 tooling/validate_local.py --output ../agent-skills-validation-run-01 --timeout 900
```

Choose a new output directory outside the checkout for each run. The verdict is
in `../agent-skills-validation-run-01/report.json`. A check counts as `passed` only
when it exits zero and nothing was skipped, so an unproven test never reads as
a green one. Use `--plan` to print the command list without executing it.
Run the public-safety scan separately before proposing changes; CI also performs
that check.

Before opening a pull request, read
[`CONTRIBUTING.md`](CONTRIBUTING.md). Changes should keep routing explicit,
preserve typed handoff boundaries, and add tests or eval coverage when
behavior changes.

## Security

Report vulnerabilities privately — see [`SECURITY.md`](SECURITY.md). Everyday
participation is covered by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Documentation

[`docs/`](docs/README.md) indexes the repository's documents: direction and
quality policy, local validation, the publication and visual standards, and the
generated tables that must not be hand-edited.

## Protocol

Skills use the CometWeb Agent Interchange Protocol (CW-AIP) for typed handoffs:

- [`CW-AIP v1`](protocol/cw-aip-v1/)
- [`CW-AIP v2`](protocol/cw-aip-v2/)

## License

CometWeb Agent Skills is released under the [MIT License](LICENSE).
