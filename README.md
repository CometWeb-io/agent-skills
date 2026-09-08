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
| CI | `.github/workflows/validate.yml` |

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

## Development loop

```bash
python3 -m pip install -r requirements-dev.txt
python3 tooling/validate_repo.py
python3 tooling/compatibility.py
python3 -m pytest -q tooling/tests skills/*/tests
python3 tooling/run_routing_evals.py
python3 tooling/package_skill.py cometweb-context
```

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

## Target (remaining P1/P2)

See `docs/TARGET.md`. Short version: generated OpenAI/Cursor adapters from registry,
immutable per-skill packages with eval reports, and a public-safe publish pipeline into
`MaciejZet/agent-skills`.
