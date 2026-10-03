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
