# Discovery and Coverage v2

## Purpose

Make whole-project analysis auditable and context-efficient. Inventory first, route attention second, deep-read third.

## Assessment pin

Record when available:

- repository/project identity,
- repo set for multi-repo products,
- branch/ref/commit per repository,
- assessment timestamp,
- target-state profile,
- connector/source limitations.

If a material repo cannot be pinned or enumerated, disclose that whole-project truth is qualified.

## Discovery sequence

### 1. Topology inventory

Start from repository/workspace/package/service structure. Do not start from TODO search.

Identify when applicable:

1. Product/UI surfaces
2. Services/APIs
3. Data/storage/migrations
4. AuthN/AuthZ/session/permissions
5. Billing/entitlements/payments
6. Integrations/webhooks/external APIs
7. Jobs/queues/schedulers/workers
8. Configuration/secrets/environment handling
9. Tests/fixtures/test infrastructure
10. CI/build/release automation
11. Deployment/infrastructure/runtime
12. Observability/logging/errors/incidents
13. Security/privacy/data handling
14. Analytics/telemetry/experimentation
15. Performance/scalability-sensitive paths
16. Documentation/runbooks/onboarding
17. Work history: issues/PRs/commits/branches
18. Product/customer/intent evidence
19. Support/incident/customer-ops evidence when available

### 2. Project Surface Graph

Use `references/project-truth-model.md`. Map high-value nodes and dependency edges. For large repositories use a symbol/dependency/repository map if available to route attention efficiently.

### 3. Critical journeys

Trace the workflows that define the requested target state end-to-end. A whole-project roadmap that never verifies critical journeys is usually a code inventory, not a product readiness assessment.

### 4. Evidence-bearing deep reads

Deep-read:

- entrypoints and route declarations,
- schemas/migrations,
- auth/permission checks,
- billing/entitlement enforcement,
- CI/release/deployment paths,
- critical business logic,
- tests proving critical journeys,
- configuration/feature flags,
- runtime/observability hooks,
- product requirements tied to critical outcomes.

### 5. History-assisted triage

Use commits/PRs/issues and, where tooling permits, change hotspots or temporal coupling to decide where hidden coupling/risk may exist. Treat this as triage, not defect evidence.

## Coverage statuses

Use exactly:

- `COMPLETE`
- `PARTIAL`
- `SAMPLED`
- `UNAVAILABLE`
- `NOT_APPLICABLE`

For each domain record:

- stable domain key,
- status,
- inspected surfaces,
- omitted/unavailable surfaces,
- mandatory-for-target boolean,
- `not_applicable_reason` when N/A,
- evidence/claim IDs if useful,
- notes.

`NOT_APPLICABLE` without a reason is invalid for a material domain.

## Coverage semantics

- `COMPLETE` means all material surfaces in that domain were inspected at the depth required for the target-state conclusion.
- `PARTIAL` means important surfaces were inspected but known subareas remain unchecked.
- `SAMPLED` means representative examples only.
- `UNAVAILABLE` means access/tool/format/size prevented verification.
- `NOT_APPLICABLE` means the domain genuinely does not apply to the target state.

Never collapse `SAMPLED` into `COMPLETE` because many files were read.

## STANDARD mode

Require every material domain to be accounted for, but allow targeted deep-reading. Whole-project scope means all material surfaces were considered, not every file read.

## EXHAUSTIVE mode

When the user explicitly requests every file/every module:

1. Enumerate the complete in-scope file list at a pinned ref.
2. Classify generated/vendor/binary/lock/artifact files.
3. Account for each file as `INSPECTED`, `EXCLUDED_GENERATED`, `EXCLUDED_VENDOR`, `BINARY_UNREADABLE`, or `UNAVAILABLE`.
4. Preserve counts and exclusions.
5. If enumeration/pagination/indexing prevents proof, return `EXHAUSTIVE_NOT_PROVEN`.

Do not substitute code search for complete file enumeration.

### Executable file accounting

When Git/filesystem execution is available, read [file-accounting.md](file-accounting.md)
and run `scripts/coverage_inventory.py` before claiming exhaustive coverage. It
reconstructs the pinned Git tree, creates an initially unreviewed per-file ledger,
and checks all review rows against exact object identities. Complete connector
exports can be imported with an independently obtained tree pin.

Keep the inventory and review ledger next to the roadmap. Kernel 2.0.1 now
requires their raw objects under `file_coverage` for EXHAUSTIVE validation and
matches every bundle to the pinned `assessment.repos` scope. Use
`roadmap_kernel.py validate --roadmap-json @roadmap.json --require-valid`.
Save `assessment_contract_sha256` before review and pass --expected-scope-sha256
when the declared scope must not be silently narrowed. Read file-accounting.md
for the exact input shape and explicit exclusion policy. The numeric domain
coverage score alone is still not proof that each file was inspected.

Report `EXHAUSTIVE_NOT_PROVEN` while files are missing, unavailable, unreadable or
submodules are unexpanded. `ACCOUNTED_WITH_EXCLUSIONS` must disclose the excluded
paths and rationale, not imply that every file was inspected. Even
`INSPECTION_RECORDS_COMPLETE` only describes supplied review records: it does not
prove source review quality, current runtime behavior or release readiness.
Never fabricate reviewer, evidence or summary fields to complete the ledger.

## DELTA mode

Inventory the old and new scope/ref. Inspect changed surfaces plus dependency paths that could invalidate previous claims. Use `references/living-roadmap.md`.

## Multi-repo projects

Create a repo map with:

- repo role,
- ownership if known,
- version/ref,
- runtime/deploy relation,
- data/API/event dependency,
- availability status.

Do not call a roadmap project-wide when a required repository is unavailable unless the target scope explicitly excludes it.

## Connector limitations

If the active repository connector supports search but not reliable tree/directory enumeration, do not claim complete repo coverage. Mark inventory-dependent domains `PARTIAL`, `SAMPLED`, or `UNAVAILABLE` as appropriate and state the limitation.
