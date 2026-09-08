# Evidence Graph v2

## Contents

- Model
- Claim row and epistemic/status rules
- Source row
- Evidence edge
- Search record
- Gap row
- Root object

## Model

Keep six node/edge families separate:

1. Research Contract
2. Claims
3. Sources
4. Evidence edges
5. Contradictions
6. Searches and gaps

This normalization prevents a common failure in v1-style ledgers: treating one source row as if its authority, directness, scope fit, and temporal relevance were identical for every claim it touches.

## Claim row

```json
{
  "claim_id": "clm_...",
  "claim_text": "Atomic falsifiable proposition",
  "claim_type": "vendor_policy",
  "materiality": "critical",
  "epistemic_kind": "FACT",
  "temporal_sensitivity": "high",
  "scope": {},
  "depends_on_claim_ids": [],
  "contradiction_tested": true,
  "status": "VERIFIED",
  "confidence": "high",
  "notes": null
}
```

### Epistemic kinds

- `FACT` — proposition intended to be established directly from evidence.
- `INFERENCE` — conclusion derived from other claims; must use `depends_on_claim_ids`.

Do not mark an inference `VERIFIED`. Use `SUPPORTED_INFERENCE` only when its dependencies are adequately established.

### Claim statuses

- `VERIFIED` — FACT has sufficient accepted, scoped, admissible evidence.
- `SUPPORTED_INFERENCE` — INFERENCE rests on ready dependency claims and survives falsifier review.
- `PARTIAL` — useful support exists but a material dimension remains weak.
- `UNSUPPORTED` — no accepted evidence establishes the claim.
- `CONTRADICTED` — accepted opposition defeats the claim as written.
- `UNKNOWN` — research is insufficient to classify it.

## Source row

```json
{
  "source_id": "src_...",
  "title": "Official policy",
  "canonical_ref": "https://example.com/policy",
  "source_class": "LIVE_WEB",
  "source_role": "OFFICIAL",
  "provenance_lane": "PUBLIC",
  "independence_group": "example-vendor-origin",
  "independence_confidence": "high",
  "source_state": "final",
  "published_at": null,
  "effective_from": null,
  "effective_to": null,
  "last_verified_at": null,
  "expires_at": null,
  "source_version": null,
  "superseded_by_source_id": null,
  "requires_live_verification": false,
  "verified_for_research": false,
  "freshness_ttl_days": null,
  "derived_from_source_ids": [],
  "content_hash": null,
  "notes": null
}
```

`canonical_ref` can be a canonical URL, file/document reference, repository object, database/system-of-record reference, or stable human-expert record identifier. Do not put secrets into it.

## Evidence edge

```json
{
  "evidence_id": "ev_...",
  "claim_id": "clm_...",
  "source_id": "src_...",
  "direction": "SUPPORT",
  "locator": "section 4.2 / lines 80-96 / commit:path / row key",
  "evidence_form": "paraphrase",
  "summary": "Minimal claim-relevant summary",
  "authority_fit": "high",
  "directness": "high",
  "scope_fit": "high",
  "measurement_quality": "not_applicable",
  "admission": "ACCEPTED",
  "notes": null
}
```

Allowed directions:

- `SUPPORT`
- `CONTRADICT`
- `CONTEXT`

Allowed admission states:

- `ACCEPTED` — may enter the material reasoning path.
- `CONTEXT_ONLY` — useful context but cannot establish/refute the claim.
- `REJECTED` — inadmissible for this claim.

## Search record

```json
{
  "search_id": "srch_...",
  "claim_id": "clm_...",
  "purpose": "FALSIFIER",
  "source_lane": "PUBLIC",
  "query_summary": "Sanitized description of what was checked",
  "completed": true,
  "completed_at": "...",
  "result_source_ids": ["src_..."],
  "novelty_count": 1,
  "notes": null
}
```

Purposes: `SUPPORT`, `FALSIFIER`, `RETRACTION`, `VERSION`, `NEGATIVE_CASE`, `ABSENCE_TEST`, `LINEAGE`.

## Gap row

Use explicit gap objects for missing primary evidence, access problems, scope uncertainty, method limitations, version ambiguity, freshness blockers, or unresolved contradictions. Every critical/material gap should say what evidence would close it.

## Root object

```json
{
  "schema_version": "2.0",
  "research_id": "res_...",
  "research_contract": {},
  "claims": [],
  "sources": [],
  "evidence": [],
  "contradictions": [],
  "searches": [],
  "gaps": [],
  "research_status": "PARTIAL",
  "stop_reason": null
}
```

Keep recommendations outside the Evidence Pack unless a consuming workflow explicitly adds a downstream section.
