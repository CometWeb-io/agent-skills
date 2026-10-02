# Repo Roaster: full workflow

The detailed procedure behind the step index in `SKILL.md`. Open this file before any non-QUICK review, and whenever a step's detail is needed in QUICK mode. The core contract, admission gates, and hard boundaries in `SKILL.md` still govern every step; nothing here relaxes them.

## Workflow steps

### 1. Pin target and evidence boundary

Build `source_manifest` for repository/ref, diff, runtime reproduction, logs, metrics, deployment config, or linked evidence. Record paths in scope, inaccessible areas, and whether the ref is `PINNED`, `MOVING`, or `UNKNOWN`. DIFF requires base and head refs.

### 1A-1D. Review setup

Follow `references/review-operations.md` (shared): plan the review budget, apply the source instruction firewall, build the evidence register, and choose the assurance mode.

### 2. Inventory before diagnosis

Map modules, manifests/workspaces, entrypoints, databases/migrations, external integrations, trust boundaries, tests, CI/CD, environment/config, infrastructure, observability, jobs/queues, generated/vendor areas, dependency locks, and risky state-mutating surfaces.

When local access exists run:

```bash
python3 scripts/inventory_repo.py /path/to/repo --json --git
```

For DIFF review, optionally add:

```bash
python3 scripts/inventory_repo.py /path/to/repo --json --git --base <base-ref> --head <head-ref>
```

The inventory is topology evidence, not a quality verdict.

### 3. Build the system model

Record actors, entrypoints, trust boundaries, state stores, external dependencies, background jobs, privileged surfaces, and deployment model. Use `unknown`/empty arrays rather than inventing topology.

### 4. Build the critical-invariant ledger

Record invariants that must never break, for example:

- authentication/authorization enforcement;
- tenant/user isolation;
- billing/entitlement consistency;
- idempotency around external side effects;
- migration compatibility;
- retry safety;
- destructive-operation authorization;
- cache/source-of-truth coherence;
- exactly-once/at-least-once assumptions;
- critical user-flow state transitions.

For each invariant record enforcement evidence, test evidence, and status `VERIFIED`, `PARTIAL`, `UNVERIFIED`, or `BROKEN` within the reviewed evidence.

### 5. Build critical-surface, state-transition, and failure-domain ledgers

`critical_surface_ledger` maps entrypoints, trust boundaries, state mutations, external side effects, jobs, migrations, public APIs, and privileged operations.

`state_transition_ledger` records critical state changes, guards, side effects, rollback/recovery behavior, and current evidence status.

`failure_domain_ledger` records component failure modes, containment, recovery path, and observability. These ledgers prevent an isolated code smell from being promoted into a systemic defect without a path.

### 6. Identify critical journeys

Prioritize call paths/state transitions where invariant failure creates the largest real blast radius. Do not assign CRITICAL to code that is merely ugly, unreachable, dev-only, or contained.

### 6A. Map invariants to executable evidence

Build `test_evidence_ledger` for every declared invariant. Record whether it is `COVERED`, `PARTIAL`, `ABSENT`, or `UNKNOWN`, name concrete test/runtime evidence, and link evidence ids. A test file name is not proof that the invariant is exercised; inspect the assertion or runtime signal.

For `DIFF`, also build `change_risk_ledger` linking changed surfaces to affected invariants, rollout/rollback concerns, and verification contracts. Small diffs can have large semantic blast radius.

### 7. Run the failure scan

Use `references/review-rubric.md`. Prefer cross-file/cross-layer failures with real reachable consequence over style issues.

### 8. Prove absence and reachability

Use `NOT_FOUND` only with `absence_proof`: searched scope, queries/locations, and why that scope is sufficient. If evidence is insufficient, put the concern in `verification_gaps`.

Reachability:

- `PROVEN`: test/runtime/trace/log or complete source path reaches the risky effect.
- `PLAUSIBLE`: concrete source path exists but runtime reachability was not directly executed.
- `STATIC_ONLY`: risky code/config is present but active path is not established.
- `UNKNOWN`: evidence is insufficient.

CRITICAL requires `PROVEN` or `PLAUSIBLE`, a non-empty execution path, evidence strength above WEAK, scope sensitivity below HIGH, and reference to a declared invariant/critical path/trust boundary.

### 9. Generate candidate findings

Each candidate needs a stable `finding_key`, optional aliases, severity, category, defect class, evidence state, evidence strength, scope sensitivity, exact anchor with `source_id`, invariant/surface refs, observation, failure mode, engineering risk, materiality, blast radius/class, failure containment, reachability, optional execution path, repair scope, repair, verification contract, and confidence. `roast_line` is optional.

Every admitted finding also records `evidence_refs`, a structured `confidence_basis`, and `residual_risk` after the proposed repair. High confidence is not a writing style: it requires direct enough evidence, sufficient scope support, and addressed counterevidence.

Unverified areas belong in `verification_gaps`, not the defect list.

Severity:

- `CRITICAL`: plausible path to security-boundary failure, cross-tenant exposure, irreversible material data loss/corruption, or systemic production failure.
- `MAJOR`: material correctness, reliability, architecture, testability, migration, supply-chain, operability, or change-safety risk.
- `MINOR`: bounded maintainability, clarity, or hygiene issue.

### 10. Run Challenger -> Defender -> Arbiter

Before admitting CRITICAL or MAJOR, open `references/severity-calibration.md`, then open `references/adversarial-protocol.md`. Search guards, wrappers, call-site constraints, tests, feature flags, configuration, generated/runtime conditions, environment assumptions, deployment topology, and contradictory evidence that could neutralize or contain the issue. Emit only the post-arbitration finding.

### 11. Compress root causes

If several findings are consequences of one missing invariant/boundary, group them under one root cause. Do not count every call site as an independent defect.

### 12. Test the repair

Run the counterfactual repair test. Verification must state method, success condition, and failure signal. Prefer reproduction, fault injection, concurrency test, contract test, migration rehearsal, rollback rehearsal, or static rule only when it can actually falsify the failure mode.

### 13. Model DIFF change surface

In DIFF mode build `change_surface` covering public API, schema/data, migrations, configuration, dependencies, feature flags/rollout, build/release behavior, and rollback. A small textual diff can have a large semantic blast radius.

### 14. Recheck revisions

For RECHECK open `references/revision-protocol.md`. Preserve stable finding keys, rerun original verification, distinguish artifact change from reviewer-scope change, and scan modified paths for regressions. When inventory snapshots exist, compare topology deterministically with `python3 scripts/compare_inventories.py base-inventory.json head-inventory.json --json`; treat the delta as a navigation signal, not as a defect verdict.

### 15. Preserve what works

Record strong boundaries, tests, invariants, tooling, containment, or design choices worth preserving. Do not force praise.

### Assurance and disagreement closure

Follow the closure section of `references/review-operations.md` before declaring the outcome.

### 16. Declare review outcome

Choose exactly one:

- `MATERIAL_FINDINGS`
- `NO_MATERIAL_FINDINGS`
- `INSUFFICIENT_EVIDENCE`

If evidence is insufficient, mark at least one quality gate `BLOCKED`, return no material defects, and list evidence needed in `verification_gaps`. This is not proof the repo is safe or unsafe.

### 17. End with one core engineering fix

Return exactly one highest-leverage technical repair, or a bounded no-fix/evidence-needed statement. Do not substitute a roadmap or release verdict.

## Lens definitions

Default to `GENERAL`; use one or more when the request narrows scope:

- `ARCHITECTURE`: boundaries, coupling, layering, ownership, dependency direction.
- `CORRECTNESS`: control flow, state transitions, errors, invariants, edge cases.
- `DATA_INTEGRITY`: transactions, idempotency, concurrency, migrations, tenant/user isolation, destructive operations.
- `TESTABILITY`: behavior coverage, test seams, brittle fixtures, false-green paths.
- `SECURITY_REVIEW`: trust boundaries, authorization, validation, secret/privilege handling; no exploitation.
- `PERFORMANCE`: N+1, unbounded work, caching failures, leaks, blocking hot paths.
- `RELIABILITY`: retries, timeouts, idempotency, partial failure, backpressure, failover, recovery.
- `OPERABILITY`: observability, runbooks, rollout/rollback, configuration, alertability, incident diagnosability.
- `SUPPLY_CHAIN`: dependency provenance, lockfiles, update path, build inputs, generated/vendor boundaries.
- `BUILD_RELEASE`: build reproducibility, artifact boundaries, environment drift, CI/CD assumptions, migration/rollback coupling.
- `MAINTAINABILITY`: duplication, hidden coupling, dead code, abstraction debt, change blast radius.
- `DX`: setup friction, scripts, docs, local reproducibility, dependency hygiene.

Open `references/review-rubric.md` for FULL or FORENSIC mode.
