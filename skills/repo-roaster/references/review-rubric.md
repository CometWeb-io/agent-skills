# Repo Roaster review rubric

Use only dimensions material to the repository profile and requested lenses.

## 1. Topology and ownership

- Are modules/services/packages clearly bounded?
- Is dependency direction coherent or cyclic/hidden?
- Are shared abstractions truly shared contracts or accidental coupling?

## 2. Critical invariants

- Where are auth, isolation, billing, idempotency, schema, consistency, and destructive-action invariants enforced?
- Are invariants duplicated inconsistently across call sites?
- Are invariant tests behaviorally meaningful?

## 3. Trust boundaries and authorization

- Which inputs cross from less-trusted to more-privileged contexts?
- Is authentication confused with authorization?
- Are tenant/account/resource identifiers independently authorized rather than trusted from caller context?
- Are privileged admin/internal paths separately bounded?

## 4. State transitions and data integrity

- Are transitions explicit and validated?
- Can retries/duplicates reorder or repeat side effects?
- Are transactions aligned with external effects?
- Can partial failure leave split-brain/half-applied state?
- Are destructive operations reversible or guarded?

## 5. Concurrency and idempotency

- Are read-modify-write sequences race-safe?
- Is idempotency durable across process restart and retry?
- Are locks, unique constraints, compare-and-set, or transactional guards actually at the right boundary?

## 6. Error handling and partial failure

- Are timeouts bounded?
- Are retries backoff/jitter/limit aware?
- Are retryable and terminal failures distinguished?
- Does fallback preserve correctness or merely hide failure?

## 7. Failure domains and recovery

- What happens when each dependency is slow, unavailable, duplicated, inconsistent, or partially successful?
- Is failure contained or amplified across tenants/components?
- Is recovery automatic, manual, or unspecified?
- Can operators tell whether recovery succeeded?

## 8. Data/schema migrations

- Are migrations compatible with mixed-version deploys?
- Are backfills bounded, resumable, and idempotent?
- Is rollback realistic after irreversible data transformation?
- Are large-table/locking implications visible?

## 9. Test quality

- Do tests cover behavior/invariants, not merely function presence?
- Are dangerous branches/retries/concurrency/failure paths tested?
- Do mocks accidentally remove the behavior that needs proof?
- Can flaky or snapshot-heavy tests produce false green?

## 10. Runtime/config drift

- Is behavior materially controlled by env/config/feature flags not represented in source review?
- Are defaults safe?
- Can staging/local differ from production in ways that invalidate static conclusions?

## 11. Observability and incident diagnosability

- Are critical transitions, external effects, retries, and failures observable?
- Are logs/metrics correlated enough to reconstruct a transaction/request/job?
- Are alerts tied to user/system harm rather than raw noise?

## 12. Build and release

- Are artifacts reproducible enough to know what shipped?
- Are version/build inputs pinned?
- Do deploy and migration order assumptions appear in automation or only tribal knowledge?
- Is rollback a real tested path?

## 13. Supply chain

- Are lockfiles/provenance/update workflows present and coherent?
- Are generated/vendor files trusted without clear origin?
- Do scripts execute unpinned remote content or opaque install hooks?
- Do not call a dependency vulnerable without verified evidence.

## 14. Performance and resource bounds

- Are loops/queries/jobs bounded by input size?
- Are N+1 paths reachable on material workloads?
- Can cache behavior violate correctness or create stampedes?
- Are memory/file/socket/process resources released?

## 15. Security review

- Validate trust boundaries, input handling, authorization, secret handling, unsafe deserialization/template/shell/file paths, and privilege transitions.
- Static risk is not exploit proof. Do not claim exploitability without evidence.

## 16. Maintainability and change safety

- Does changing one concept require unrelated modules to change?
- Are duplicated rules likely to drift?
- Are abstractions hiding control flow or external effects?
- Are dead/legacy paths still reachable or merely present?

## 17. Developer experience

- Can a new contributor reproduce setup/build/test locally?
- Are scripts deterministic and discoverable?
- Are environment examples accurate enough to avoid hidden local knowledge?

## 18. AI-agent/tooling specific review

When profile is `AI_AGENT_SYSTEM`, inspect tool permission boundaries, instruction hierarchy, untrusted content reaching tool calls, confirmation points for consequential actions, secret/context exposure, loop/timeout controls, result validation, and eval coverage. Do not assume prompt injection alone proves an exploitable action path.
