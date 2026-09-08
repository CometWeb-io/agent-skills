---
name: repo-to-roadmap
description: Analyze an entire software/product project and turn verified project truth into an evidence-based, dependency-aware, reusable roadmap. Use for first-time or delta whole-project baselines such as "analyze the whole repo/project", "what is left to build before target state", "create/update a roadmap from GitHub/Notion", "przeanalizuj całe repo", or "update the roadmap after recent changes". Inventory topology before searching, separate intent/presence/behavior/release/outcome truth, prove material absence instead of inferring it from search misses, expose coverage and contradictions, model capabilities/critical journeys, prioritize target blockers and gates, validate hard dependencies, and create immutable baseline/delta roadmap snapshots. Do not use for weekly sprint control, release-candidate GO/NO_GO gates, or "is build v1.2.3 ready to ship?" — use Product Operator or Release Readiness instead. Do not use as an implementation agent, narrow code review, or specialist security/SEO/CRO audit.
---

# Repo to Roadmap v2

Turn project evidence into a defensible roadmap that another human or agent can execute and later revalidate.

Keep the chain explicit:

`target state -> project topology -> evidence -> claims -> capabilities/gaps -> roadmap items -> acceptance proof -> living snapshot`

Default to read-only analysis. Do not create issues, edit repositories/docs, merge code, or trigger deployments unless the user separately asks for those side effects.

## 1. Select assessment mode

Choose exactly one mode and state it:

- **STANDARD** - default whole-project assessment. Account for every material project domain, then deep-read evidence-bearing surfaces. Do not imply every file was read.
- **EXHAUSTIVE** - use only when the user explicitly asks for every file/module or equivalent. Account for the complete in-scope file set at a pinned ref or disclose `EXHAUSTIVE_NOT_PROVEN`.
- **DELTA** - update a prior roadmap against a new commit/branch/release/date/assessment. Revalidate changed claims plus affected dependencies instead of starting over blindly.
- **FOCUSED** - use only when the user explicitly narrows scope to a package/module/release objective. Do not label it whole-project.

Never silently downgrade an explicit exhaustive request into sampling.

## 2. Establish the Assessment Contract

Resolve from existing context when possible; do not ask unnecessary questions.

Record:

- project/repository scope,
- target-state profile: `PROTOTYPE | INTERNAL_BETA | PUBLIC_BETA | CLIENT_READY | PAID_PRODUCTION | SCALE_READY | CUSTOM`,
- explicit end-state requirements,
- hard constraints/deadlines only when actually supplied,
- repository refs/commits when available,
- known product intent and approved decisions,
- available evidence systems/connectors,
- output destination or downstream consumer if relevant.

Read `references/target-profiles.md` when "done", "client-ready", "production-ready", beta, or scaling readiness must be defined.

If the target state is genuinely ambiguous and materially changes the roadmap, represent alternatives instead of inventing one.

Create stable target requirement IDs (`T-...`). Do not turn generic best practice into a mandatory target requirement without an applicability path.

## 3. Route each truth claim to its system of record

Read `references/tool-routing.md` for mixed sources/connectors.

Separate at least:

- **implementation presence** - source/config/schema exists,
- **behavior** - flow actually behaves as asserted,
- **release** - change is releasable/released at the claimed scope,
- **intent** - approved desired state,
- **outcome** - user/business/operational effect is observed,
- **operational truth** - deploy/recovery/monitoring/ownership behavior,
- **external current truth** - vendor/platform/standard/policy constraint.

Do not use:

- PRD/docs to prove shipped implementation,
- code presence to prove behavior,
- merged PR/commit to prove release,
- issue title to prove a defect,
- implementation quality to prove adoption/revenue/customer pain.

## 4. Inventory topology before judging

Read `references/discovery-and-coverage.md` and `references/project-truth-model.md`.

Build a Project Surface Graph before making roadmap claims. Cover applicable:

- apps/services/workers/jobs,
- entrypoints/routes/APIs/webhooks,
- data models/migrations/storage,
- auth/session/permissions,
- billing/entitlements,
- integrations/external dependencies,
- queues/schedulers/background work,
- config/secrets/env/feature flags,
- tests/test topology,
- CI/build/release,
- deployment/runtime/infrastructure,
- observability/errors/incidents,
- security/privacy-sensitive boundaries,
- analytics/telemetry,
- performance/scaling-sensitive paths,
- docs/runbooks/onboarding,
- issues/PRs/commits/branches,
- product/customer/support/incident evidence.

For large repositories use an available symbol/dependency/repository map as a context-routing aid. Use history hotspots/change coupling only to choose where to inspect deeper; never treat them as defects by themselves.

## 5. Trace critical journeys

Identify the user/operational journeys that define the target state and trace them end-to-end across packages/repos/services/data/external boundaries.

A journey is not verified because all components exist independently.

Examples:

- sign up -> first value,
- login -> protected action -> logout,
- checkout -> entitlement -> invoice,
- create -> persist -> retrieve -> mutate,
- deploy -> migrate -> health check -> rollback.

## 6. Maintain the Coverage Ledger

For every material domain use exactly:

`COMPLETE | PARTIAL | SAMPLED | UNAVAILABLE | NOT_APPLICABLE`

Record what was inspected, what was not, whether the domain is mandatory for the target state, and rationale for every `NOT_APPLICABLE`.

Run:

```bash
python scripts/roadmap_kernel.py coverage --coverage-json '@coverage.json'
```

Treat coverage score/grade as disclosure support, not proof of correctness.

If tree/file enumeration is unavailable, do not claim complete repo coverage from keyword search.

## 7. Build the Evidence Ledger

Read `references/evidence-model.md`.

Create stable claim IDs (`C-...`). Every material claim must record:

- claim text,
- claim lane/type,
- materiality,
- whether current-sensitive,
- supporting/contradicting evidence rows,
- source identity/ref/fingerprint when available,
- directness/freshness/scope match,
- independence group,
- confidence/status.

Run for material claims:

```bash
python scripts/roadmap_kernel.py evidence --claim-json '@claim.json'
```

Use the kernel confidence as a heuristic band, not calibrated probability.

### Current-sensitive evidence

A current-sensitive claim cannot be binding when its material support is `STALE`, `SUPERSEDED`, or `UNKNOWN`. Keep historical evidence for context, but do not let it make a current claim pass.

### Negative evidence

Before asserting a material `MISSING` capability, run the negative-evidence protocol from `references/evidence-model.md`.

A search miss means `UNKNOWN` or `NOT_FOUND_IN_SEARCH`, not `MISSING`.

## 8. Build the Capability Inventory

Model capabilities separately from files using stable capability IDs (`CAP-...`).

Use only:

`VERIFIED_WORKING | IMPLEMENTED_UNVERIFIED | PARTIAL | STUBBED | BROKEN | MISSING | UNKNOWN | NOT_APPLICABLE`

Link each capability to claim IDs and target requirement IDs.

This is the current-state model. Do not collapse it into a list of code smells.

## 9. Build the gap map

Compare capability state against the Target State Contract.

Classify material gaps as one or more of:

- `BLOCKER`
- `CORRECTNESS`
- `RELIABILITY`
- `SECURITY_PRIVACY`
- `DATA_INTEGRITY`
- `UX_PRODUCT`
- `OBSERVABILITY`
- `PERFORMANCE`
- `OPERATIONS`
- `GTM_ENABLEMENT`
- `TECH_DEBT`
- `VALIDATION`

A gap needs a credible impact path to a target requirement, user/business outcome, release/reliability/security risk, or enabling dependency.

Do not convert every code smell into roadmap work.

## 10. Route specialist deep dives

Read `references/composition.md`.

Use specialist skills when a material domain requires deeper authority/evidence. Keep this skill responsible for:

- cross-project synthesis,
- evidence normalization,
- capability/gap model,
- target-state linkage,
- dependencies,
- roadmap construction,
- snapshot/delta validity.

Invoke AI Council only for contested material choices not settled by project evidence alone. Import Council output as a decision input, never as proof that implementation exists.

## 11. Create roadmap candidates

Read `references/roadmap-model.md`.

Use item kinds:

`BUILD | FIX | HARDEN | VERIFY | VALIDATE | INSTRUMENT | MIGRATE | RETIRE | DOCUMENT | DECIDE`

Every item must include:

- stable ID (`R-...`),
- title and observable outcome,
- kind,
- problem claim refs,
- target requirement refs,
- why now,
- acceptance criteria with `criterion`, `verify_with`, and `proof`,
- hard dependency IDs,
- effort band `XS | S | M | L | XL`,
- evidence confidence,
- uncertainty,
- priority dimensions,
- optional mandatory gate + gate status,
- non-goal,
- success signal when meaningful.

Prefer root-cause items over symptom lists. Split items that can ship independently or need different acceptance proof.

Do not invent calendar estimates from repo size.

## 12. Apply gates before scores

Allowed mandatory gates:

`release | security | privacy | data_integrity | legal | core_flow`

Allowed gate statuses:

`NOT_REQUIRED | UNVERIFIED | CLEAR | CLEAR_WITH_CONTROLS | BLOCK`

Rules:

- `BLOCK` -> `BLOCKER`.
- `UNVERIFIED` material gate -> `VERIFY_NOW`.
- score cannot create/clear a gate.
- resolved `CLEAR | CLEAR_WITH_CONTROLS | BLOCK` gates must record `gate_basis`.
- suspected security/privacy/legal risk from a general pass remains unverified until appropriate authority/specialist evidence exists.

A non-gate item becomes `BLOCKER` only when a mandatory target requirement cannot be met without it and the blocking path is strongly evidenced.

## 13. Prioritize with bounded heuristics

For non-binding decisions run:

```bash
python scripts/roadmap_kernel.py priority --item-json '@item.json'
python scripts/roadmap_kernel.py sensitivity --item-json '@item.json'
```

Use scores only as tie-breakers inside a lane.

Default lanes:

`BLOCKER | VERIFY_NOW | NOW | NEXT | LATER | PARK | VALIDATE`

If sensitivity is `FRAGILE`, disclose what assumption/evidence could change ordering. Do not present a point score as measured economic value.

## 14. Validate hard dependencies

Run:

```bash
python scripts/roadmap_kernel.py graph --items-json '@items.json'
```

Resolve:

- duplicate IDs,
- missing hard dependencies,
- cycles.

Use dependency leverage/critical-chain output to identify enabling foundations. Do not let architectural elegance outrank a proven target blocker.

## 15. Synthesize waves

Build waves only after evidence/gates/dependencies are valid.

For each wave state:

- objective,
- item IDs,
- exit criteria,
- hard prerequisites,
- parallelizable groups when useful,
- material risks/unknowns,
- evidence/trigger that would reprioritize it.

Use outcome milestones instead of arbitrary months when capacity is unknown.

If capacity/velocity/deadline is explicitly available, use it as a constraint rather than inventing one.

## 16. Validate the complete roadmap

Use the v2 machine payload shape from `references/output-contract.md`.

Run:

```bash
python scripts/roadmap_kernel.py validate --roadmap-json '@roadmap.json'
```

Fix errors before presenting. Surface material warnings.

Validation must check cross-references, acceptance proof, gates, coverage, hard graph, `XL` decomposition, claim admissibility, and unsupported blocker semantics.

## 17. Create a baseline snapshot

When the roadmap will be reused, saved, handed to another skill, or updated later, read `references/living-roadmap.md` and run:

```bash
python scripts/roadmap_kernel.py snapshot --roadmap-json '@roadmap.json'
```

Attach the snapshot hash to the final handoff. Preserve the snapshot as immutable once treated as final.

## 18. DELTA revalidation

For DELTA mode:

1. compare old/new refs and source fingerprints,
2. revalidate changed claims,
3. invalidate linked capabilities/items,
4. propagate through hard dependencies,
5. rerun priority only where binding inputs changed,
6. if Target State Contract changed materially, reopen broad priority ordering,
7. create a new snapshot; never overwrite the old one.

Run:

```bash
python scripts/roadmap_kernel.py delta --before-json '@before.json' --after-json '@after.json'
```

## 19. Format and hand off

Read `references/output-contract.md` for the human report and `references/handoffs.md` for downstream agent/skill consumption.

A downstream operator must receive stable IDs, dependencies, acceptance proof, claim refs, unresolved verification, watch triggers, and snapshot hash - not only prose.

## Non-negotiable rules

- Inventory before search-driven conclusions.
- Separate intent, presence, behavior, release, outcome, and operational truth.
- Preserve source identity and correlation.
- Do not turn stale/current-sensitive evidence into a current fact.
- Do not assert absence from a search miss.
- Do not claim behavior from code presence.
- Do not claim release from merged code.
- Do not claim outcome from code intuition.
- Do not let a numeric score create/clear a binding gate.
- Do not fabricate dates, capacity, ROI, or calibrated confidence.
- Do not call a sampled/unavailable project fully verified.
- Do not make a huge unordered backlog and call it a roadmap.
- Prefer a smaller roadmap with stronger evidence and explicit validation items.
- Prefer `VERIFY`/`VALIDATE` when cheap evidence can change an expensive decision.
- Keep daily execution selection downstream in `product-operator`.

## References

Read only what the current step needs:

- `references/target-profiles.md` - define target readiness and Target State Contract.
- `references/discovery-and-coverage.md` - project inventory, coverage, exhaustive/delta discovery.
- `references/project-truth-model.md` - project surface graph, capabilities, journeys, invariants, history signals.
- `references/evidence-model.md` - claim types, source authority, admissibility, negative evidence, contradictions.
- `references/roadmap-model.md` - item schema, gates, priority, sensitivity, dependencies, waves.
- `references/tool-routing.md` - repository/product/outcome/external source routing.
- `references/composition.md` - boundaries and specialist/Council composition.
- `references/living-roadmap.md` - immutable snapshots, watch triggers, delta invalidation.
- `references/handoffs.md` - product-operator/Council/specialist handoffs.
- `references/output-contract.md` - human and machine-readable final structure.
- `references/evaluation.md` - quality gate and anti-pattern evals.

Use `scripts/roadmap_kernel.py` for deterministic evidence admissibility, coverage, priority/sensitivity, hard dependency, snapshot/delta, and final validation logic. Do not recreate those calculations manually when code execution is available.
