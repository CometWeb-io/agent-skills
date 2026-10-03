# Claim-use contract

Longform Publisher consumes evidence; it does not recreate the full Evidence Researcher graph.

For each material claim used in the manuscript record:

```text
id
section_id
claim_text
materiality: CRITICAL | MATERIAL | SUPPORTING
claim_kind: FACT | AUTHOR_ASSERTION | OPINION | SYNTHESIS
support_status: SUPPORTED | UNRESOLVED | SCOPED_OUT | NOT_REQUIRED
evidence_refs[]
citation_state: REQUIRED | PRESENT | NOT_REQUIRED
citation_marker (when deterministic marker checking is useful)
volatile_current: true | false
freshness_state
```

Rules:

- A CRITICAL or MATERIAL FACT claim passes `validate` only as `support_status: SUPPORTED` with at least one `evidence_refs` entry that resolves to a registered source. `UNRESOLVED` and `SCOPED_OUT` are the honest record for one that lacks support, and `validate` still returns `MATERIAL_CLAIM_UNSUPPORTED` for it, so it cannot ship as stated: remove it, narrow it to what the evidence supports, or reclassify it as `AUTHOR_ASSERTION`/`OPINION` when that is what it is, and track the open question in `unresolved_gaps[]`.
- `materiality`, `claim_kind`, `support_status` and `citation_state` take only the values above, in capitals. Any other value returns `FIELD_VALUE_INVALID:claim_uses.<field>`; a lowercase `material` used to skip the support check instead of failing it.
- Attribution must follow the actual source claim; do not turn reported opinion into fact.
- `AUTHOR_ASSERTION` and `OPINION` do not require fake citations, but must not impersonate external evidence.
- Keep uncertainty, modal force, scope, chronology and causal direction aligned with evidence.
- Register exact fragile values in `protected_facts[]` when an edit could silently change them.
