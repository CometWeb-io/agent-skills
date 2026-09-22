# Output contract

The **finished requested prose is primary**. Do not replace it with a process report.

For substantial factual work, retain a compact sidecar. v1.3 retains the existing schema and adds mode, candidate lineage, source-policy and dependency fields.

```text
schema: cometweb.content-draft/v1
brief_id
candidate_id
parent_candidate_id?
mode: DRAFT | REVISION | FINAL
source_mode: SOURCE_BOUND | EVIDENCE_REQUIRED | CONTEXTUAL_DRAFT | CREATIVE
approved_source_ids[]?
claim_ledger[]:
  claim_id
  text_or_locator
  material: true|false
  risk?: LOW|MEDIUM|HIGH|CRITICAL
  status: SUPPORTED|INFERRED|OPINION|EXAMPLE|UNRESOLVED|UNSUPPORTED
  presented_as_fact: true|false
  freshness_required: true|false
  evidence[]: {source_id?, source, locator, authority?, observed_at?, freshness_status?}
  depends_on_claim_ids[]
protected_invariants[]
invariant_checks[]: {invariant_id, status:PASS|FAIL|UNKNOWN}
unresolved[]
release_eligible
recommended_next_skill
```

Do not expose the full ledger unless useful to the user or a downstream reviewer. `PASS` from the kernel means the sidecar obeys claim/source/invariant rules; it does not independently verify source truth.
