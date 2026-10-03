# Evidence Graph v2

## Contents

- Model
- Claim row and epistemic/status rules
- Source row
- Evidence edge
- Contradiction row
- Search record
- Gap row
- Root object
- Accepted values

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

`migrate-v1` adds `legacy_contradiction_tested` to migrated claims: the v1 flag kept as history only. The gate ignores it; `contradiction_tested` starts `false` until a real falsifier search is recorded.

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

`source_state` is one of `final`, `draft`, `superseded`, `withdrawn` (compared case-insensitively; default `final`). `superseded_by` is accepted as a legacy alias of `superseded_by_source_id`. `verified_research_id` binds a zero-cache inspection to one research run (see `freshness.md`). A source passed alone to the `temporal` command may carry `claim_type` when `--claim-type` is omitted. `independence_confidence` is recorded, not validated.

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

`authority_fit`, `directness` and `scope_fit` take `high`, `medium`, `low` or `unknown`; `measurement_quality` also takes `not_applicable`. `evidence_form` and `summary` are free text.

## Contradiction row

```json
{
  "contradiction_id": "ctr_...",
  "claim_id": "clm_...",
  "evidence_ids": ["ev_..."],
  "type": "version_mismatch",
  "severity": "critical",
  "resolution": "UNRESOLVED",
  "explanation": "What differs and what observation would settle it",
  "resolution_basis_evidence_ids": []
}
```

`severity` takes the claim materiality values (`critical`, `material`, `supporting`). `resolution` is one of `RESOLVED_SCOPE`, `RESOLVED_TIME`, `RESOLVED_DEFINITION`, `RESOLVED_METHOD`, `RESOLVED_SUPERSEDED`, `RESOLVED_AUTHORITY`, `UNRESOLVED`. `type` uses the disagreement classes in `contradiction-protocol.md`; the kernel records it but does not validate it, nor `explanation` or `resolution_basis_evidence_ids`. Every `evidence_ids` entry must be an edge for the same claim.

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
  "sanitized_for_external": false,
  "absence_basis": null,
  "notes": null
}
```

Purposes: `SUPPORT`, `FALSIFIER`, `RETRACTION`, `VERSION`, `NEGATIVE_CASE`, `ABSENCE_TEST`, `LINEAGE`.

`source_lane` is one of `PUBLIC`, `PRIVATE`, `USER_SUPPLIED`, `REPOSITORY`, `DATABASE`, `HUMAN`. A `PUBLIC` search in a `PRIVATE` or `USER_SUPPLIED` research lane must set `sanitized_for_external: true`. An `ABSENCE_TEST` needs `absence_basis` with non-empty `expected_location`, `detection_logic` and `coverage_limitations`. `novelty_count` is for the analyst; the kernel does not read it (the `stop` command takes `--no-novelty-rounds` instead).

## Gap row

Use explicit gap objects for missing primary evidence, access problems, scope uncertainty, method limitations, version ambiguity, freshness blockers, or unresolved contradictions. Every critical/material gap should say what evidence would close it.

```json
{
  "gap_id": "gap_...",
  "claim_id": "clm_...",
  "severity": "material",
  "gap_type": "missing_primary",
  "description": "What is missing",
  "what_closes_it": "Evidence that would close the gap"
}
```

`severity` is `critical`, `material` or `minor`; open critical/material gaps keep the pack from `READY`. `claim_id` may be null for a pack-level gap. A missing `what_closes_it` is a warning. `gap_type` and `description` are free text the kernel does not read.

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

`research_status` and `stop_reason` are informational and excluded from `pack_hash`; the `audit` command computes the authoritative status.

Keep recommendations outside the Evidence Pack unless a consuming workflow explicitly adds a downstream section.

## Accepted values

- `claim_type`: `law_regulation`, `regulatory_guidance`, `security_advisory`, `vendor_policy`, `competitor_pricing`, `official_technical_docs`, `repository_behavior`, `internal_metric`, `internal_process_state`, `company_announcement`, `market_metric`, `academic_evidence`, `historical_fact`, `current_fact`, `product_behavior`, `qualitative_experience`, `doctrine_framework`, `service_status`, `dataset_fact`. Another value is a warning and needs an explicit `freshness_ttl_days`.
- `materiality`: `critical`, `material`, `supporting`. `temporal_sensitivity`: `high`, `medium`, `low`, `static`. `confidence`: `high`, `medium`, `low`.
- `source_class`: `LIVE_WEB`, `PRIVATE_KNOWLEDGE`, `USER_FILE`, `REPOSITORY`, `DATABASE_SYSTEM_OF_RECORD`, `ACADEMIC_SOURCE`, `HUMAN_EXPERT_EVIDENCE`, `DECISION_MEMORY`, `FRAMEWORK`.
- `source_role`: `SYSTEM_OF_RECORD`, `PRIMARY`, `OFFICIAL`, `SECONDARY`, `AGGREGATOR`, `EXPERT`, `DOCTRINE`.
- `provenance_lane` and `research_contract.privacy_lane`: `PUBLIC`, `PRIVATE`, `USER_SUPPLIED`.
