# Evidence Pack — Example Maps API free tier

## Research status

- Question: does the Example Maps API free tier allow commercial use, and what is its monthly request cap?
- Scope: public terms and pricing pages of Example Maps; no account-specific contract.
- as_of: 2026-09-30T11:00:00Z
- Mode: STANDARD
- Status: READY

## Bottom line

The free tier allows commercial use (C1) and is capped at 25,000 requests per month (C2), both from the provider's own current terms and pricing page. The evidence does not establish whether the cap is enforced as a hard limit or billed as overage (C3 is an inference). The highest-impact uncertainty is that the pricing page was updated on 2026-09-15 and the terms page still links to an older version.

## Material Claim Ledger

| Claim | Kind | Type | Status | Confidence | Best support | Opposition | Freshness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 — free tier allows commercial use | FACT | policy | VERIFIED | high | S1 terms §4.2 | none found (S3 searched) | CURRENT |
| C2 — free tier cap is 25,000 requests/month | FACT | quantity | VERIFIED | high | S2 pricing table | S4 blog post says 20,000 (2025, superseded) | CURRENT |
| C3 — requests above the cap are blocked, not billed | INFERENCE | behaviour | SUPPORTED | medium | S2 footnote "requests are throttled" | none | CURRENT |

## Contradictions and gaps

- C2 vs S4: the 2025 blog post says 20,000; S2 dated 2026-09-15 supersedes it. Resolved in favour of S2 (newer, system of record).
- Gap: no test of actual over-cap behaviour; C3 must not be treated as a fact.

## Coverage/readiness

- Material claim readiness: 3/3 assessed, 2 verified, 1 supported inference
- Authority-admissible support coverage: 100%
- Primary/system-of-record coverage: 100% (S1, S2 are the provider's own pages)
- Falsifier coverage: 3/3 claims searched for opposition
- Freshness coverage: 3/3 current as of 2026-09-30
- Unresolved critical contradictions/gaps: 0
- Unknown source independence: 0 material

## Handoff

- Safe for downstream use: C1, C2.
- Requires caveats: C3 (inference from a footnote).
- Must not be treated as facts: over-cap billing behaviour.
- Live evidence a decision skill must re-verify: S2 pricing table on the day of any purchase decision.

```json
{
  "id": "evidence-researcher:EvidenceEnvelope:example-maps-free-tier",
  "type": "EvidenceEnvelope",
  "producer": "evidence-researcher",
  "producer_version": "2.3.0",
  "protocol_version": "2.0",
  "subject": "Example Maps API free tier",
  "generated_at": "2026-09-30T11:00:00Z",
  "as_of": "2026-09-30T11:00:00Z",
  "sensitivity": "public",
  "dependencies": [],
  "payload": {
    "schema": "cometweb.evidence/v2",
    "research_contract": "Example Maps free tier: commercial use and request cap",
    "mode": "STANDARD",
    "as_of": "2026-09-30T11:00:00Z",
    "material_claims": [
      {"claim_id": "C1", "text": "Free tier allows commercial use", "epistemic_kind": "FACT", "status": "VERIFIED", "materiality": "critical"},
      {"claim_id": "C2", "text": "Free tier cap is 25,000 requests per month", "epistemic_kind": "FACT", "status": "VERIFIED", "materiality": "critical"},
      {"claim_id": "C3", "text": "Requests above the cap are blocked, not billed", "epistemic_kind": "INFERENCE", "status": "SUPPORTED", "materiality": "material"}
    ],
    "sources": [
      {"source_id": "S1", "locator": "https://maps.example.com/terms#4.2"},
      {"source_id": "S2", "locator": "https://maps.example.com/pricing"},
      {"source_id": "S3", "locator": "https://maps.example.com/faq"},
      {"source_id": "S4", "locator": "https://blog.example.com/maps-pricing-2025"}
    ],
    "evidence_edges": [
      {"edge_id": "E1", "claim_id": "C1", "source_id": "S1", "direction": "SUPPORT", "admission": "ACCEPTED"},
      {"edge_id": "E2", "claim_id": "C2", "source_id": "S2", "direction": "SUPPORT", "admission": "ACCEPTED"},
      {"edge_id": "E3", "claim_id": "C2", "source_id": "S4", "direction": "CONTRADICT", "admission": "REJECTED"},
      {"edge_id": "E4", "claim_id": "C3", "source_id": "S2", "direction": "SUPPORT", "admission": "CONTEXT_ONLY"}
    ],
    "gaps": [{"gap_id": "G1", "text": "over-cap behaviour untested", "blocking": false}],
    "contradictions": [{"contradiction_id": "X1", "claims": ["C2"], "status": "resolved", "materiality": "critical"}],
    "readiness": "READY",
    "evidence_pack_hash": "pending"
  },
  "payload_hash": "pending"
}
```
