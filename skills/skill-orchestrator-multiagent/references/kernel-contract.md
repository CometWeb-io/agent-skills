# Script contract

What the two scripts in this package print and read. The plan itself
(`archetype`, `steps[]`) is the `skill-orchestrator` kernel output, documented in
`references/workflow-archetypes.md`; `references/contract.json` holds the scripts,
these lists and the bundled schemas to each other.

## Payload builder

`python3 scripts/orchestrate_multiagent_kernel.py "<goal>" --json --workspace-root "<abs path>"`
takes the goal and an optional workspace root, and prints:

```text
execution_mode: isolated_subagents
parent_role: orchestrator_only
plan: the skill-orchestrator plan for the goal
subagent_tasks[]: one per plan step, in order
  step_index: 1-based position
  step_total: number of steps
  skill: the one skill this subagent runs
  subagent_type: host Task type, generalPurpose or explore
  description: short Task label
  prompt: the filled isolation prompt
  envelope_out: the CW-AIP type the step must return, or null
  run_in_background: always false; steps run sequentially
parent_must_not[]: work the parent thread may not do
```

## Envelope gate

`python3 scripts/validate_envelope.py <envelope.json> [--expect-type TYPE] [--final]`
reads one envelope and prints `OK:` or one `FAIL:` line per error. It dispatches on
`protocol_version`: `1.0` is checked against `envelope.core.schema.json` (or, for
`EvidenceEnvelope` and `DecisionHandoff`, the kind schema that includes it), `2.0`
against `cw-aip-v2.core.schema.json`; any other value fails.

```text
id, producer, subject, as_of: required strings
type: v1 ArtifactEnvelope|EvidenceEnvelope|FindingEnvelope|DecisionHandoff|SpecialistHandoff|SnapshotMetadata
      v2 adds ContextEnvelope|DecisionEnvelope|RoadmapEnvelope|ReleaseEnvelope (DecisionHandoff is v1 only)
protocol_version: 1.0|2.0
source, locator, claim, status: optional v1 strings
authority: v1 PRIMARY|DERIVATIVE|HEURISTIC|USER_ASSERTED|UNKNOWN
freshness: v1 CURRENT|STALE|UNKNOWN|NOT_YET_EFFECTIVE|SUPERSEDED
confidence: v1 number 0..1 or a label
dependencies[]: envelope ids this one builds on (required in v2)
producer_version, generated_at: required in v2
sensitivity: v2 public|internal|confidential|restricted
payload: object; required for every v1 kind listed above and for v2
payload_hash: v2 sha256 of the canonical payload, recomputed here; pending passes only without --final
```

Kind payloads the gate checks:

```text
EvidenceEnvelope (v1) payload:
  research_contract: required
  material_claims[]: required
    claim_id, text, epistemic_kind, status: required
    epistemic_kind: FACT|INFERENCE; a claim without it is refused
  evidence_pack_hash: required
  gaps[], contradictions[]: optional
DecisionHandoff (v1), DecisionEnvelope and ReleaseEnvelope (v2) payload:
  verdict: the producing skill's verdict; GO and GO_WITH_CONTROLS authorize action
  blockers[]: must be empty next to an authorizing verdict
  controls[], release_candidate, environment: v1 optional
  gates[]: v2; a gate whose status is BLOCK or COUNSEL_REQUIRED (any case) rejects an authorizing verdict
    gate_id: named in the error
  human_approval: v2 DecisionEnvelope; a GO passes only with not_required or granted
```

`GO_WITH_CONTROLS` authorizes only on a `ReleaseEnvelope`; for a v2 decision only `GO`
does. Everything else in a payload belongs to the producing skill.

## Shared local pilot planner

The shared orchestrate_kernel CLI supports optional capability packs and the PRD
prerequisite. `capability_packs` stores locked pointers with `role_id` and
`source_commit`. Helpers are loaded from the canonical skill-orchestrator package;
the full local skill tree is required. The isolated builder accepts
`--with-prd-handoff` and `--with-capability-packs`. PRD mode exposes one briefing
preview and `dispatch_status: PLAN_ONLY`, plus `deferred_step_ids`. For execution,
`--run-dir PATH --plan-json FILE --prior-envelopes-json FILE` validates the exact
completed envelope prefix, then returns at most one claimed task. It adds `step_id`,
`attempt_id`, `handoff_gate`, `gate_lock`, `prior_envelope_ids`, and optional
`artifact_profile`. Statuses are CLAIMED, COMPLETED, CANCELLED, STALE_PLAN. Invalid
or active input fails with exit 1 and no new claim. JSON output on resumed/terminal
runs includes `plan`, `dispatch_status`, `subagent_tasks`; planning-only parent metadata
is not repeated. Follow `references/prd-handoff.md` for canonical completion/retry.

Council task prompts include selected `capability_packs` as locked role-scoped FRAMEWORK
pointers. Dispatch rechecks registry file integrity and exact selected pointers.

The builder reads `event_type` and `plan_hash` from canonical ledger state/claim;
`envelope_id`, `envelope_hash` and `accepted` bind supplied content to checkpoints.

## Local specialist profile preview

`--specialist-profile <id>` emits one pinned canonical-owner task plus a separate schema-bound profile sidecar requirement. Read [specialist-profiles.md](specialist-profiles.md) for identifiers and limits. It cannot be combined with the PRD ledger or Council pack flags. It does not execute a model.

The plan/task field `specialist_profile` contains the full locked profile record. The task field `profile_output_schema` points to its local closed sidecar schema. Both are optional and only emitted for the explicit profile preview.
