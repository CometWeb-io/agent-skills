# CometWeb Agent Skills (private canonical)

Private canonical monorepo for Comet-owned agent skills used across ChatGPT, Codex,
Cursor, Claude Code, and CometWeb operating workflows.

Public distribution mirror: [`MaciejZet/agent-skills`](https://github.com/MaciejZet/agent-skills)
(generated / synced subset — do not treat as a second hand-edited source of truth once
the publish pipeline is live).

## Current state (as of this commit)

| Area | Status |
| --- | --- |
| Active skills on disk | 15 packages under `skills/` (incl. `cometweb-context`) |
| Registry | `registry/skills.json` — single source for lifecycle + routing metadata |
| Protocol | CW-AIP v1 (compat) + CW-AIP v2 core/payload schemas |
| Tooling | `tooling/` validators, compatibility, packager, adapter generator |
| Evals | routing suite + context behavior fixtures |
| Validation | Local `tooling/validate_local.py`; Actions paused per owner |

## Foundation vs domain

**Foundation (platform):**

| Skill | Role |
| --- | --- |
| `cometweb-context` | Provenance-aware context gateway → ContextEnvelope |
| `evidence-researcher` | Auditable Evidence Packs |
| `skill-orchestrator` | Multi-skill workflows (`execution_mode`: auto / single_thread / isolated_subagents) |
| `ai-council` | Consequential decisions (LIGHT / STANDARD / DEEP) |

`skill-orchestrator-multiagent` is a **thin alias** for `execution_mode=isolated_subagents`.
Do not diverge its planning model from `skill-orchestrator`.

**Domain specialists** (product-operator, release-readiness, web-app-auditor, …) remain
first-class skills; they are not “foundation OS”, but they ship in this repo.

## Repository layout

```text
registry/                 skills.json, hosts.json, schemas
protocol/
  cw-aip-v1/              legacy interchange (compat)
  cw-aip-v2/              unified core + typed payloads
tooling/                  validate, compatibility, package, generate adapters
evals/
  routing/                trigger / collision cases
  behavior/               skill behavior fixtures
skills/<name>/            self-contained skill packages
docs/                     architecture notes
.github/workflows/        CI gates
```

## Development loop — local validation

The owner has paused GitHub Actions because its budget is exhausted. Keep Actions
and public distribution disabled during private integration. Use a full trusted
checkout, not the pending file overlay.

```bash
# Initial dependency setup, only when needed in your development environment:
python3 -m pip install -r requirements-dev.txt
# Inventory and command plan only; no tests executed:
python3 tooling/validate_local.py --plan
# Execute checks; the output directory must be new and outside the checkout:
python3 tooling/validate_local.py --output ../cometweb-validation-2026-09-13
```

The runner checks the saved adapters without regenerating them, captures separate
logs and JUnit, and binds results to HEAD plus working-tree/index fingerprints.
Failures, skipped tests, missing test output and source changes cannot produce a
fully passing result. It does not install dependencies or publish anything.

See [local validation](docs/LOCAL-VALIDATION.md) for scope, limitations and exit
codes. The pending 137-file bundle is **not** integrated by adding this runner;
see [integration status](docs/INTEGRATION-STATUS.md).

## Rules

- `registry/skills.json` is the routing source of truth; generated adapters must not be
  hand-edited as primary policy.
- `SKILL.md` frontmatter: `name` + `description` (host-safe length; Codex ≤ 1024).
- Active skills have `VERSION` and `CHANGELOG.md`.
- Behavior changes are test-first.
- Never commit secrets, `.env`, credential stores, customer exports, or private vault contents.
- Typed boundaries: context ≠ evidence ≠ decision ≠ release verdict.
- Do not hard-code live operational bindings into skill logic when a machine-readable
  source registry can hold them.

## CometWeb publication design

When creating or revising CometWeb ebooks, PDF reports, or audit workbooks, read
[`docs/COMETWEB-EBOOK-DESIGN-RULES.md`](docs/COMETWEB-EBOOK-DESIGN-RULES.md).
The series rules cover red before/defect states, verified green outcomes, rounded
status labels with icons, authentic branding, reference-cover hierarchy, and rendered
PDF checks. They are project-specific design rules, not a replacement for the generic
`ai-humanize` editing contract or a claim of accessibility certification.

## Target (remaining P1/P2)

See `docs/TARGET.md`. Short version: generated OpenAI/Cursor adapters from registry,
immutable per-skill packages with eval reports, and a public-safe publish pipeline into
`MaciejZet/agent-skills`.
