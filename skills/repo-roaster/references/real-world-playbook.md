# Real-world operational playbook

Use this guide for production repository reviews involving large codebases, PRs, monorepos, migrations, services, runtime/log/test evidence, or incomplete access.

## Intake

1. Pin commit/branch/base/head whenever possible.
2. Inventory before searching for defects.
3. Identify deployment/runtime boundary, trust boundaries, state stores, migrations, queues/jobs, and critical invariants.
4. Register runtime logs, metrics, test output, deployment config, and incident evidence as separate sources.
5. Create a review session manifest for multi-source, DIFF, RECHECK, or high-impact reviews.

## Evidence acquisition order

Prefer: exact source/config/test path -> call graph/state transition -> pinned diff/history -> runtime/test/log/metric evidence -> external framework behavior. Static suspicion never becomes runtime certainty merely because it is plausible.

## Production failure modes

- Search miss != absence: prove the search boundary.
- Test file != invariant coverage: inspect the assertion.
- A scary function is not CRITICAL if unreachable or contained.
- A tiny migration/permission/config diff can have global blast radius.
- Generated/vendor code may explain behavior but is rarely the right repair owner.
- Security review here is defensive evidence review, not exploit authorization.

## Review budget

Prioritize authorization/isolation, destructive state changes, idempotency/retry semantics, migration compatibility, external side effects, failure containment/recovery, deployment configuration, data integrity, and tests on critical invariants. Sample low-risk utility code after critical paths are covered.

## Closure

A fix closes only when the original failure condition is falsified by an appropriate test/repro/rehearsal. A code diff or ticket state is not verification. Preserve accepted residual risk separately from the defect report.
