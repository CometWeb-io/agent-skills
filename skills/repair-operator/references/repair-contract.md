# Repair contract

```text
repair_id
finding_ids[]
repair_class: PATCH|REWRITE|REANALYSIS|REDESIGN|VERIFY_FIRST|WONT_FIX
root_cause
protected_invariants[]
dependencies[]
planned_change
done_when
status: PLANNED|IN_PROGRESS|UNVERIFIED|CLOSED|OPEN|DEFERRED|WONT_FIX
verification_evidence[]: {fresh:true, result:PASS, method, evidence[], candidate_id, observed_at}
regression_detected
remaining_risk
defer_reason
decision_source: {owner, rationale, decided_at}
```

`CLOSED` requires root cause + done condition + non-empty fresh candidate-bound verification with timezone-aware `observed_at`; no detected regression. `WONT_FIX` requires `repair_class: WONT_FIX` and explicit authorized decision source. `DEFERRED` requires a concrete reason. Preserve every source finding ID through the ledger.
