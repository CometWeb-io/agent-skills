# Output contract

The **finished requested prose is primary**. Do not replace it with a process report.

For substantial factual work, retain a compact sidecar. v1.3 retains the existing schema and adds mode, candidate lineage, source-policy and dependency fields.

```text
schema: cometweb.content-draft/v1
brief_id
candidate_id
parent_candidate_id?                # REVISION: required and different from candidate_id
mode: DRAFT | REVISION | FINAL      # default FINAL; DRAFT is never release_eligible
evidence_policy: SOURCE_BOUND | EVIDENCE_REQUIRED | CONTEXTUAL_DRAFT | CREATIVE
                                    # default EVIDENCE_REQUIRED; CONTEXTUAL_DRAFT is never release_eligible
approved_sources[]?                 # SOURCE_BOUND: every evidence source must be listed here
evidence_floor?: {critical, material, supporting}   # each A|B|C|D
claims[]:
  claim_id                          # unique
  text_or_locator
  material: true|false
  high_risk?: true|false            # material SUPPORTED needs PRIMARY, OFFICIAL or
                                    # SYSTEM_OF_RECORD authority on some evidence
  status: SUPPORTED|INFERRED|OPINION|EXAMPLE|UNRESOLVED|UNSUPPORTED
  presented_as_fact: true|false
  freshness_required: true|false
  evidence[]: {source_id?, source, locator, authority?, observed_at?, freshness_status?: CURRENT|NEAR_EXPIRY}
  evidence_grade?: A|B|C|D          # required on material SUPPORTED when evidence_floor applies
  basis_claim_ids[]                 # claim ids in this ledger; no cycles
protected_invariants[]              # an id string, or {id}
invariant_checks[]: {id, state: PASS|FAIL|UNKNOWN}   # every invariant needs a PASS check
unresolved[]
release_eligible
recommended_next_skill
```

`schema`, `source_id`, `text_or_locator`, `unresolved` and
`recommended_next_skill` are for the reader; the kernel does not check them.
An invariant check `state` other than PASS fails that invariant.

`kernel.validate(report)` returns `{status: PASS|FAIL, errors[],
release_eligible, unresolved_material, mode}`. `release_eligible` needs PASS,
no material UNRESOLVED/UNSUPPORTED claim, a mode other than DRAFT, and a policy
other than CONTEXTUAL_DRAFT. A report that is not an object fails with
`report:not-object`, and one whose `claims` is not a list with `claims:not-list`;
both report the default mode `FINAL` unless the report names another, and a mode
that is not one of the three is reported as `FINAL` next to `mode:invalid`.

Do not expose the full ledger unless useful to the user or a downstream reviewer. `PASS` from the kernel means the sidecar obeys claim/source/invariant rules; it does not independently verify source truth.
