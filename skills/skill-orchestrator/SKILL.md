---
name: skill-orchestrator
description: Plan and execute multi-skill CometWeb workflows with CW-AIP handoffs when the user wants one entry point instead of tagging each specialist. Use when the user asks to orchestrate, sequence, or run end-to-end flows (e.g. evidence then Council, audit then release, research then weekly ops), run everything needed for a goal, or chain Evidence Researcher with ai-council or other skills in order. Supports execution_mode auto|single_thread|isolated_subagents. Loads each step's SKILL.md, runs it fully, and passes envelopes between steps. Do not use for a single-domain task when one specialist skill is enough, for routing-only questions without execution, or to bypass AI Council decision policy or Release Readiness gate rules.
---

# Skill Orchestrator

Single entry point for **multi-skill workflows**. You plan the sequence, choose an
execution mode, run each specialist skill, and hand off via CW-AIP — without
collapsing research into decisions or skipping skill boundaries.

## Execution mode

| Mode | Behavior |
| --- | --- |
| `auto` | Prefer `isolated_subagents` when the host supports Task/subagents **and** the workflow benefits from isolation (Council + research, audit + release, ≥2 heavy specialists). Otherwise `single_thread`. |
| `single_thread` | Parent loads each `SKILL.md` and executes steps sequentially in this thread. |
| `isolated_subagents` | One subagent per step; parent only plans, launches, validates envelopes, and merges. |

`skill-orchestrator-multiagent` is a **thin alias** for `execution_mode=isolated_subagents`.
Do not maintain a divergent planning model there.

Optional context preflight: when the goal depends on current multi-source CometWeb
state, run `cometweb-context` first and pass the ContextEnvelope as a dependency.

## Boundaries

**Owns:**

- workflow archetype selection,
- `execution_mode` selection,
- ordered execution plan with envelope types,
- loading each step's `SKILL.md` (or launching a subagent that does),
- handoff summaries between steps,
- final workflow result (artifacts produced, gaps, what remains).

**Does not own:**

- Evidence Pack construction (Evidence Researcher),
- GO/NO-GO / Council deliberation (AI Council),
- release gate verdicts (Release Readiness),
- weekly priority reconciliation (Product Operator),
- domain findings (auditors, CI, SEO, etc.),
- ContextEnvelope construction (`cometweb-context`).

Read `references/workflow-archetypes.md` and `references/sequencing-rules.md`.
For isolated mode also read `references/multiagent-execution.md` (shared with the alias).

## Workflow

### 1. Plan

Run the kernel when the host allows:

```bash
python3 scripts/orchestrate_kernel.py "<user goal>" --json
```

If scripts are unavailable, infer the same archetype from the goal using
`references/workflow-archetypes.md`.

Present the plan before step 1 unless the user asked to run immediately:

```text
Workflow plan (research_then_council) · execution_mode=auto→isolated_subagents
  1. evidence-researcher — Evidence Pack
  2. ai-council — DecisionHandoff
```

### 2. Confirm scope (lightweight)

If the plan includes **ai-council** and the user did not mention a decision, ask once:
material decision in scope, or evidence-only?

If **release-readiness** is included without a pinned RC/build + environment, stop and
request the pin before gating.

### 3. Execute steps

**single_thread** — for each step (see `references/sequencing-rules.md`):

1. Read that skill's `SKILL.md`.
2. Execute its full workflow (scripts, validators, output contract).
3. Emit the CW-AIP envelope for the step.
4. Handoff summary before the next step.

**isolated_subagents** — for each step:

1. Build subagent payload (`scripts/orchestrate_multiagent_kernel.py` when available).
2. Launch host Task/subagent; do **not** run domain work in the parent.
3. Validate returned envelope type; append to `prior_envelopes`.

Protocol: [`protocol/cw-interchange-v1.md`](../../protocol/cw-interchange-v1.md)
(prefer CW-AIP v2 wrappers when producers emit them).

### 4. Close

Emit **Workflow result**:

- archetype used,
- `execution_mode` resolved,
- envelope IDs / hashes per step,
- accepted vs gap claims (if research ran),
- Council verdict if Council ran (otherwise explicitly `not run`),
- recommended next single skill if work continues.

## Archetype quick reference

| User intent | Steps |
| --- | --- |
| Verify claims → Council / Rada | evidence-researcher → ai-council |
| Evidence → weekly priorities | evidence-researcher → product-operator |
| QA audit → ship gate | web-app-auditor → release-readiness |
| Competitor delta → strategy | competitive-intelligence → (evidence-researcher?) → ai-council |
| Broad / "do everything" | evidence-researcher → optional operator → optional council |
| One skill only | delegate to that skill; do not orchestrate |

## Output contract

1. **Workflow plan** — archetype + ordered steps + execution_mode
2. **Step outputs** — one subsection per step with envelope type and pointer
3. **Workflow result** — synthesis without overstepping skill boundaries
4. **CW-AIP handoff block** — JSON or structured list of envelope metadata when useful

Never fold Evidence Researcher synthesis into a Council GO/NO-GO in the same step.
