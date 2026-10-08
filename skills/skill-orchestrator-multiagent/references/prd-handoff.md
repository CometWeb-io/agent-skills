# Optional local PRD handoff

Use only when the requested workflow explicitly requires a PRD before downstream
execution. The whole local skill tree must be present: brief-architect provides the
producer schema/kernel; skill-orchestrator-multiagent provides the existing CW-AIP
wrapper validator and schemas. PRD validation requires `jsonschema` as declared in
requirements.txt. Missing resources/dependency stop this mode; they are not installed
automatically. Ordinary planning and non-PRD completion retain their existing behavior.

From either orchestrator package, enter the canonical directory and generate the plan:

```bash
cd ../skill-orchestrator
python3 scripts/orchestrate_kernel.py 'evidence then council' --json --with-prd-handoff
```

The flag prepends brief-architect with ArtifactEnvelope, `artifact_profile: PRD`,
`handoff_gate: prd-schema-kernel/v1` and `gate_lock`. The lock includes SHA-256 of the
PRD producer schema, brief kernel, handoff helper, CW-AIP validator and core/kind schemas.
All downstream steps must declare a supported envelope type. They receive
`handoff_gate: cw-aip-final/v1`: full final wrapper validation, exact planned producer
and type, canonical content hash. This is not full downstream domain validation.
A changed lock requires a new plan/run. The lock participates in the normal plan hash.
This adds a briefing prerequisite to the selected workflow; it does not grant permission
to implement, publish, or let Council issue a verdict without its own evidence checks.

Generate the brief using the PRD schema in the host's structured output mechanism.
Wrap the canonical brief directly as `payload` of a CW-AIP ArtifactEnvelope, with
producer brief-architect. Both v1 and final v2 wrappers are supported. A v2 draft
payload hash (`pending`) or a mismatched payload hash is rejected.

Validate BEFORE adding the envelope to prior results or dispatching the next step:

```bash
cd ../skill-orchestrator
python3 scripts/prd_handoff.py envelope.json
```

The gate checks wrapper type/producer, JSON schema, full brief readiness kernel and
agreement of declared/computed status. It accepts only READY. PROVISIONAL and BLOCKED
may be truthful brief reports, but are not executable handoffs. INVALID, unknown IDs,
cycles, incorrect slice order/coverage and wrong verification types stop handoff.
Do not coerce fields, clear decisions or override status to make the gate pass.
The kernel checks declared structure/decisions; it cannot prove factual truth or that
all consequential choices have been disclosed. Content review remains necessary.

For a ledger-backed run, call complete-step with the FULL envelope:

```bash
cd ../skill-orchestrator
python3 scripts/workflow_ledger.py complete-step "$RUN_DIR" \
  --step-id step-1 --attempt-id ATTEMPT --envelope-id ENVELOPE \
  --envelope-hash HASH --envelope-json envelope.json
```

HASH is `sha256:` plus SHA-256 of canonical full-envelope JSON (UTF-8, sorted keys,
no extra whitespace, ensure_ascii=false, allow_nan=false); it is returned by the gate.
A protected step cannot complete from an ID/hash alone. The ledger independently
validates again, matches ID/hash to the checked content, and records `handoff_validation`
with `gate_lock_hash`, `brief_hash` and `brief_status`. It records no raw brief.
New runs bind manifest step definitions via `steps_hash` in run_created; removing a
gate from the manifest is rejected during replay. Legacy non-PRD ledgers still replay.

Rejected input appends no completion event and leaves the active attempt RUNNING.
Claim-next/resume therefore cannot dispatch a downstream step. Supply corrected input
for that same attempt, or explicitly block/fail/cancel it using the ledger commands.
Duplicate successful completion remains idempotent only for the same checked envelope.
The ledger is a local operational guard, not an authentication boundary against an
actor who can rewrite all files and hashes.

## Gate diagnostics

The JSON result includes `accepted`, `wrapper_errors`, `schema_errors`, `kernel`
and `status_matches`. It also exposes content hashes and the envelope ID. Wrapper
checks bind `producer` to brief-architect and validate the brief in `payload`.
Only accepted=true allows the handoff; diagnostics are not instructions or permission.

## Isolated generator and resume

Generate with `skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py`
using `--json --with-prd-handoff` (optionally `--with-capability-packs`). The result is
`dispatch_status: PLAN_ONLY`: a briefing preview, not an active claim. Save `plan`,
create the canonical ledger run, then dispatch through:

```bash
cd ../skill-orchestrator-multiagent
python3 scripts/orchestrate_multiagent_kernel.py --json --run-dir "$RUN_DIR" \
  --plan-json plan.json --prior-envelopes-json accepted-prefix.json
```

The accepted prefix is an ordered array of FULL envelopes, initially `[]`. The builder
revalidates every completed envelope against its locked gate and recorded ID/hash,
then claims exactly one attempt and embeds the prefix in its isolated prompt. Tasks
pin skill paths to this local tree, never an installed copy. Missing, duplicate,
reordered or changed inputs dispatch nothing. Only append after successful completion.
A restart resumes from checkpoints; it never silently reclaims a RUNNING attempt.
Explicit fail-step closes an unsuccessful attempt; the next claim increments its
attempt_number and has a new attempt_id. Changed plans are STALE_PLAN and dispatch
nothing. COMPLETED/CANCELLED return no tasks. The task builder does not launch agents;
a host adapter must run each task in its own isolated context.

Downstream validation proof stores `payload_hash`, `expected_type` and `producer`
with `gate_lock_hash`; these are checked against the planned skill/type on replay.

## Research/Council domain gate (local LIGHT qualification)

The multiagent generator accepts `--with-prd-handoff --with-domain-gates` and
`--domain-context-json path.json`. The plan must contain exactly brief-architect,
evidence-researcher, ai-council in that order. `domain_context` declares question,
context, mode LIGHT, decision_value (finite number 0..1), and max_attempts (integer 1..3). These trusted
plan inputs are pinned in the manifest; downstream output cannot change them.
The default retry budget is 2. This qualifies a single sequential parent; it is not
a distributed dispatcher or a native host Task/discovery test.

The downstream gate is `research-council-schema-kernel/v1`. Its source lock includes
domain_handoff.py, every domain JSON schema, and actual Evidence/Council kernels.
Research payloads carry the full evidence_graph. The helper audits the graph in a
fresh process, compares declared research_status with the audit and recomputes
evidence_pack_hash, projections, gaps and contradictions. Partial/stale evidence
is valid for discussing gaps; it cannot clear a positive trial or launch handoff.

Council payloads carry decision_bundle: the unchanged research_envelope, two
blind_memos (technical and product_customer), judge and original proposal. Judge
may admit only claims the actual Evidence audit marks ready. Confidence thresholds,
freshness and required gatekeepers are recomputed from the pinned plan. A model
proposal is retained unchanged. constraint_result records both kernel_verdict
and the final verdict: the local admission rule additionally downgrades GO/TEST
to DEFER whenever research is not READY. execution_authorized remains false.
The helper cannot prove model-process independence: the host harness must record
separate blind processes without shared memos. No factual truth is inferred from
a valid schema.

upstream_bindings contains ordered step_id, envelope_id and envelope_hash for the
completed prefix. The ledger matches these and dependencies exactly and rejects
Council research substitution. domain_validation reports accepted, domain_status
and domain_hash; handoff_validation persists domain_accepted and the domain hash.
Invalid input appends no completion. Explicit fail-step closes the attempt; the
next claim is a fresh identity. At max_attempts, step_retry_exhausted durably blocks
the run and dispatches nothing. Completed steps preserve attempt_number and resume
without rerunning. Duplicate completion revalidates and remains idempotent even
after downstream completion. All inputs must remain available for prefix revalidation.

CLI for domain payloads (full CW-AIP completion still goes through prd_handoff):

```sh
cd ../skill-orchestrator
python3 scripts/domain_handoff.py payload.json --producer ai-council --context-json context.json
```

Schema files: domain-research.schema.json, domain-council.schema.json,
domain-evidence-graph.schema.json, domain-memo.schema.json, domain-judge.schema.json,
domain-proposal.schema.json. Arrays and objects are bounded/closed by the schemas
where declared. Finite JSON and kernel admission remain mandatory.

Additional literal contract vocabulary (role inputs, helper results and bounded ledger events):
```text
accepted_claim_ids
args
blind_memos
blockers
claim_id
claim_ids
claim_text
claims
confidence
context
contradictions
controls
controls_implemented
coverage
critical_gap
critical_gaps
decision_bundle
decision_value
dependencies
description
domain_accepted
domain_context
domain_hash
domain_status
domain_validation
epistemic_kind
evidence_graph
explanation
freshness_status
function
gaps
gate_statuses
gatekeepers
judge
kwargs
material_claim_count
max_attempts
mode
pack_hash
proposal
question
ready
rejected_claim_ids
required_confidence
research_contract
research_envelope
research_status
retry_limit
reversible_experiment_available
roles
type
upstream_bindings
valid
validation
verdict
```

Material coverage counts only admitted critical/material claims. Supporting claim IDs never inflate coverage. A positive handoff additionally requires every declared material claim admitted by Judge. This conservative local rule can defer a kernel proposal; it does not modify it.

The graph field `materiality` distinguishes supporting, material and critical claims.
