# Multiagent execution (Cursor / hosts with subagents)

Parent thread = **orchestrator only**. Each workflow step = **one isolated subagent**
that loads a single skill's `SKILL.md` and returns one CW-AIP envelope.

## Mandatory: Task / subagent per step

When the host exposes a subagent launcher (Cursor **Task** tool, cloud agent, or
equivalent):

1. Build payloads with the multiagent kernel. It ships only in the
   `skill-orchestrator-multiagent` package, so run it from that package's
   directory (a sibling of `skill-orchestrator` in every installer layout):
   ```bash
   cd ../skill-orchestrator-multiagent   # skip when already inside it
   python3 scripts/orchestrate_multiagent_kernel.py "<goal>" --json --workspace-root "<abs path>"
   ```
   If that package is not installed, there is no payload builder: run the
   workflow with `execution_mode=single_thread` instead.
2. For each entry in `subagent_tasks` **sequentially**:
   - Launch subagent with `subagent_type`, `description`, `prompt` from payload.
   - Set `run_in_background: false` unless the user explicitly asked for parallel work.
   - **Wait** for completion before the next step.
   - Parse and validate the full returned CW-AIP envelope BEFORE appending it to `prior_envelopes`.
   - For the optional PRD pilot, checkpoint through the canonical ledger and use
     the builder `--run-dir` mode to obtain the next task; see `references/prd-handoff.md`.
     PLAN_ONLY previews are not claimed attempts. Do not prelaunch deferred steps.
3. Parent merges envelopes into **Workflow result** — no domain execution in parent.

## Parent thread: allowed vs forbidden

| Allowed in parent | Forbidden in parent |
| --- | --- |
| Plan + archetype | Run Evidence Researcher retrieval |
| Scope confirmation | Council deliberation / GO/NO-GO |
| Launch Task/subagents | Web audit click-through |
| Validate envelope shape | Release gate scoring |
| Workflow result synthesis | Collapsing two steps into one reply |

## Subagent isolation contract

Each subagent prompt must include:

- skill name (exactly one),
- path hints to `SKILL.md`,
- prior envelopes as JSON,
- required output envelope type,
- explicit **do not** lines for downstream work.

Template: `references/subagent-prompt-template.md`.

## Parallel steps (rare)

Run subagents in parallel **only** when:

- steps have no envelope dependency,
- user explicitly requested parallel execution,
- skills touch disjoint resources.

Default: **strictly sequential**.

## Fallback when subagents unavailable

If the host has **no** Task/subagent API:

1. Stop before step 1.
2. Tell the user:
   - use `@skill-orchestrator` (single-thread), or
   - switch to a host with subagent support (Cursor Agent with Task), or
   - run each step manually in separate chats with envelope paste-between.

Do **not** silently fall back to single-thread multi-skill execution — that defeats
this skill's purpose.

## Cloud subagents (Cursor Cloud / isolated VM)

When local Task context is too small or you need a clean VM per step:

1. Launch a **cloud** subagent (`environment: cloud`) per step with the same prompt payload.
2. Each cloud run gets its own branch/worktree — good for repo-touching skills (`repo-to-roadmap`, `web-app-auditor` with artifacts).
3. Parent still merges envelopes only; do not re-run domain logic after cloud return.
4. Stop cloud agents when done to avoid idle billing.

Use local Task for quick evidence/Council chains; use cloud when the step mutates repo state or needs full browser/CI isolation.

## Envelope validation between steps

Before launching step *N+1*, validate step *N* output. The gate ships with
`skill-orchestrator-multiagent`; run it from that skill's directory:

```bash
cd ../skill-orchestrator-multiagent   # skip when already inside it
python3 scripts/validate_envelope.py /tmp/step1-evidence.json --expect-type EvidenceEnvelope
```

- It accepts CW-AIP v1 (`protocol_version: "1.0"`) and v2 (`"2.0"`) and checks the
  matching bundled core schema. Any other `protocol_version` fails.
- v1: every kind needs an object `payload`. `EvidenceEnvelope` and `DecisionHandoff`
  are checked against their bundled kind schemas, so a missing `research_contract`
  or `verdict` fails here, not in the next step.
- v2: `payload_hash` is recomputed and must match; `pending` passes only without
  `--final`. Pass `--final` for the last step and for anything leaving the workflow.
- Both versions: a `GO` verdict (and a release `GO_WITH_CONTROLS`) that lists
  blockers fails. Controls do not clear a blocker.
- v2 also: the same verdicts fail next to a `BLOCK` or `COUNSEL_REQUIRED` gate (any
  letter case), and a decision `GO` fails when `human_approval` is `required`,
  `pending` or `denied`.
- `--expect-type` takes the kind from the plan. A step planned as `DecisionHandoff`
  also accepts a v2 `DecisionEnvelope` (Council) or `ReleaseEnvelope` (Release
  Readiness); no other cross-version mapping exists.
- Beyond that it checks the envelope, not domain semantics. Full typed payload rules
  (evidence graph, decision gates) belong to the producing skill; in the repository,
  `tooling/validate_envelope.py` runs them for v2.

Requires `jsonschema`; validation fails closed if the dependency or a schema is
missing. In the repository, install the dev group with `uv sync --group dev`.
On failure, return the step to its subagent with the `FAIL:` lines; do not repair
the envelope in the parent.

## Verification before close

- [ ] One subagent run per planned step (or documented block with reason)
- [ ] Each step returned its envelope type
- [ ] Parent did not issue domain verdicts
- [ ] Council step ran in its own subagent if planned
