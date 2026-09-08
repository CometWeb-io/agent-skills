# Evaluation and Golden Cases

Use this file when modifying the skill or engine. Optimize for false-green prevention, decision clarity, and practical release throughput.

## Core invariants

A valid implementation must preserve:

1. Missing artifact identity cannot produce unconditional `GO`.
2. Unknown scope flag cannot produce unconditional `GO`.
3. Incomplete risk-surface assessment cannot produce unconditional `GO`.
4. Missing required gate cannot produce `GO` merely because remaining checks score highly.
5. A required gate must have at least one applicable binding check.
6. Binding/blocker/critical failure cannot be averaged away.
7. Binding pass with claimed/missing/stale/mismatched evidence cannot produce unconditional pass.
8. Candidate-verified binding evidence must match assessed candidate.
9. Binding pass requires a verification timestamp.
10. High-risk R3 release cannot run in FAST/STANDARD mode.
11. Threshold overrides cannot weaken risk-tier floors.
12. `N/A` requires rationale and earns no credit.
13. `PASS_WITH_CONTROLS` requires current control metadata.
14. `ACCEPTED_RISK` is forbidden for binding/blocker/critical findings.
15. `ACCEPTED_RISK` requires explicit approver, owner, rationale, mitigation, and expiry.
16. Missing required governance gate → `DEFER`.
17. Governance `BLOCK` → `NO_GO` and cannot be score-overridden.
18. Governance `COUNSEL_REQUIRED` → `DEFER`.
19. Governance `CLEAR_WITH_CONTROLS` cannot yield unconditional `GO`.
20. Paid product requires billing-entitlement gate even when no billing code changed.
21. Billing change requires both entitlement and state-transition gates.
22. Sensitive-data change routes privacy governance.
23. New candidate creates a distinct snapshot hash.
24. Delta analysis surfaces new blockers and missing gates.
25. `GO` never implies deployment authorization.

## Golden scenarios

### 1. Routine green SaaS patch

Known scope, exact candidate, all baseline gates, current evidence, no residual risk.
Expected: `GO`.

### 2. High score but omitted rollback/recovery gate

All other checks green.
Expected: `DEFER` with `recovery_strategy` in missing required gates.

### 3. Auth change assessed in STANDARD mode

Auth gate present and green.
Expected: `DEFER` because R3 requires DEEP.

### 4. Auth change DEEP with direct authorization tests

Complete high-risk scope and evidence.
Expected: can reach `GO` if all other gates pass.

### 5. Security blocker

Candidate-specific or credible claimed critical failure.
Expected: `NO_GO`.

### 6. Security "pass" from old commit

Candidate mismatch.
Expected: binding unknown → `DEFER`.

### 7. Green CI but unknown risk flags

Expected: `DEFER` because gate set may be incomplete.

### 8. Paid release with no billing checks

Expected: `DEFER`, missing `billing_entitlements`.

### 9. Billing logic change with only checkout happy path

Missing `billing_state_transitions` or inadequate evidence.
Expected: `DEFER` or `NO_GO` depending known failure.

### 10. Data migration with untested recovery

Expected: `DEFER` if recovery evidence unknown; `NO_GO` if known unsafe.

### 11. Major non-binding docs risk explicitly accepted

Valid owner/approver/expiry/mitigation.
Expected: `GO_WITH_CONTROLS`, never `GO`.

### 12. Attempt to waive binding security finding

Expected: invalid manifest or blocking result; never conditional green.

### 13. Privacy surface unresolved

Sensitive-data release without privacy gate.
Expected: `DEFER`.

### 14. Current governance block

Expected: `NO_GO` regardless of score.

### 15. Mobile store release

Requires store delivery + platform policy gate; staged rollout/recovery evidence proportional to risk.
Expected: `GO/GO_WITH_CONTROLS` only after complete gates.

### 16. Release after production incident

General CI green but no exact incident regression evidence.
Expected: missing/unknown `incident_regression` → `DEFER`.

### 17. New commit after successful assessment

Previous manifest cannot cover new candidate.
Expected: new snapshot; candidate delta reported; candidate-bound evidence revalidated.

### 18. Expired compensating control

Expected: controlled check downgrades to unknown → `DEFER` when binding.

## Champion/challenger metrics

When evolving the skill, compare identical frozen scenarios and measure:

Benefits:

- false-positive GO catch rate;
- missing-gate catch rate;
- candidate-mismatch catch rate;
- stale-evidence catch rate;
- correct NO_GO vs DEFER distinction;
- correct risk-tier/mode routing;
- governance-block preservation;
- useful blocker closure instructions;
- delta/revalidation correctness.

Costs:

- manifest complexity;
- tool calls required;
- review latency;
- unnecessary DEFER rate on low-risk releases;
- redundant specialist invocation.

Prefer a challenger only when it reduces false-green risk without causing large, systematic low-risk review friction.

## Current automated tests

Run:

```bash
python tests/test_readiness_engine.py
```

The unit suite should cover the invariants above. Add a regression test before fixing any newly discovered false-positive/false-negative engine bug.
