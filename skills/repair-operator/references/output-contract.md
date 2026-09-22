# Output contract

Return a repair ledger tied to the original finding IDs.

```text
schema: cometweb.repair-ledger/v1
mode: STANDARD|DEEP
candidate_id
base_candidate_id?
items[]:
  repair_id
  finding_ids[]
  repair_class: PATCH|REWRITE|REANALYSIS|REDESIGN|VERIFY_FIRST|ROLLBACK|WONT_FIX
  patch_risk: LOW|MEDIUM|HIGH|CRITICAL
  root_cause
  depends_on[]
  verification_plan?
  rollback_plan?
  protected_invariants[]
  status: OPEN|PLANNED|IN_PROGRESS|UNVERIFIED|CLOSED|DEFERRED|WONT_FIX|REOPENED
  verification_evidence[]
regressions[]
remaining_open[]
```

Lead with blocking OPEN/UNVERIFIED work, then proven closures. Never use "fixed" for an item whose fresh candidate-bound verification did not run. HIGH/CRITICAL mutation requires a rollback/reversal plan.
