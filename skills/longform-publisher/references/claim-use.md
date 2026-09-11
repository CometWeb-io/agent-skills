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

- CRITICAL/MATERIAL FACT claims require admitted evidence or an explicit unresolved/scoped-out state that prevents overclaiming.
- Attribution must follow the actual source claim; do not turn reported opinion into fact.
- `AUTHOR_ASSERTION` and `OPINION` do not require fake citations, but must not impersonate external evidence.
- Keep uncertainty, modal force, scope, chronology and causal direction aligned with evidence.
- Register exact fragile values in `protected_facts[]` when an edit could silently change them.
