# Product Teardown - example-org/queue-lib -> source-only

## Executive verdict
- Shape: SOURCE_ONLY
- Mode: SNAPSHOT
- Scope: retry and dead-letter modules at tag v3.2.0
- Evidence quality: implementation OBSERVED in source (E-001, E-002); no production or outcome evidence
- Destination evidence quality: none (no destination given)
- Best transferable idea: PT-001, capped exponential backoff with full jitter
- Most important false friend: copying the vendored dead-letter module wholesale
- Action mix: 1 CANDIDATE / 1 REVIEW_REQUIRED
- Mandatory blockers: PT-002 legal_ip review (licence of the vendored `src/dlq/` module is unclear)

## Source/version map
- SRC-1: example-org/queue-lib at tag v3.2.0 (commit 9f2c1e7). Code presence only: whether these paths run in any deployment was not established.

## Pattern portfolio / pattern families

### PT-001 - Capped exponential backoff with full jitter
- Category: reliability_operations
- Problem: synchronized retries amplify an outage.
- Source observation: `backoff_with_jitter` caps the delay and draws uniformly below the cap.
- Evidence: E-001
- Mechanism hypothesis: random spread under a cap desynchronizes clients.
- Destination problem evidence: none (SOURCE_ONLY)
- Chosen transfer mode: REIMPLEMENT
- Gates: legal_ip not_required, security_privacy not_required
- Validation: a destination would need retry-storm evidence before this moves past CANDIDATE.
- Verdict: CANDIDATE
- Confidence: source 0.90 / mechanism 0.80 / destination 0.00 / overall 0.45

### PT-002 - Dead-letter replay with per-message provenance
- Category: reliability_operations
- Problem: poison messages are lost or replayed blindly.
- Source observation: `src/dlq/` parks failures with their context and replays them selectively.
- Evidence: E-002
- Mechanism hypothesis: keeping failure context makes selective replay safe.
- Destination problem evidence: none (SOURCE_ONLY)
- Chosen transfer mode: INSPIRE only, pending review
- Gates: legal_ip review, security_privacy not_required
- Validation: licence review of `LICENSE-DLQ` before any transfer.
- Verdict: REVIEW_REQUIRED
- Confidence: source 0.80 / mechanism 0.70 / destination 0.00 / overall 0.35

## Implementation transfer packets
None: no pattern has destination evidence, so nothing is actionable yet.

## Rejected patterns / false friends
- Copying `src/dlq/` as code: blocked by the open licence question, and code reuse needs provenance review first.

## Unknowns that can change a verdict
- The licence terms in `LICENSE-DLQ` (decides PT-002).
- Any destination's retry behavior (decides PT-001).

```json
{
 "schema_version": "2.0",
 "shape": "SOURCE_ONLY",
 "mode": "SNAPSHOT",
 "as_of": "2026-10-02T11:00:00+02:00",
 "source_targets": [
  {"id": "SRC-1", "name": "example-org/queue-lib", "kind": "repository", "version": "tag v3.2.0 (commit 9f2c1e7)", "observed_at": "2026-10-02T10:00:00+02:00"}
 ],
 "evidence": [
  {"evidence_id": "E-001", "subject": "source", "target_id": "SRC-1", "source": "https://example.org/queue-lib", "locator": "src/retry.py:backoff_with_jitter @ 9f2c1e7", "source_type": "repository", "claim_lane": "source_implementation", "claim_state": "OBSERVED", "observed_at": "2026-10-02T10:10:00+02:00", "note": "Retries use capped exponential backoff with full jitter.", "confidence": 0.95, "independence_group": "queue-lib-repo"},
  {"evidence_id": "E-002", "subject": "source", "target_id": "SRC-1", "source": "https://example.org/queue-lib", "locator": "src/dlq/ (vendored, LICENSE-DLQ) @ 9f2c1e7", "source_type": "repository", "claim_lane": "source_implementation", "claim_state": "OBSERVED", "observed_at": "2026-10-02T10:20:00+02:00", "note": "Dead-letter replay module is vendored under a separate licence file with unclear terms.", "confidence": 0.85, "independence_group": "queue-lib-repo"}
 ],
 "patterns": [
  {"id": "PT-001", "name": "Capped exponential backoff with full jitter", "family_id": null, "category": "reliability_operations", "problem": "Synchronized retries amplify an outage.", "mechanism": "Spread retries randomly under a cap so clients desynchronize.", "source_observation": "backoff_with_jitter caps delay and draws uniformly in [0, cap].", "evidence_ids": ["E-001"], "target_evidence_ids": [], "transfer": {"problem_fit": 0.5, "mechanism_fit": 0.8, "source_evidence_strength": 0.9, "destination_evidence_strength": 0.0, "implementation_feasibility": 0.5, "expected_upside": 0.5, "reversibility": 0.5, "maintenance_fit": 0.5, "strategic_fit": 0.5, "differentiation": 0.3, "dependency_risk": 0.3, "complexity_tax": 0.3, "opportunity_cost": 0.3, "legal_ip_risk": 0.1, "security_privacy_risk": 0.1, "measurement_risk": 0.3}, "gates": {"legal_ip": "not_required", "security_privacy": "not_required"}, "implementation": {"transfer_mode": "REIMPLEMENT"}, "experiment": null, "interactions": {"requires": [], "enables": [], "conflicts_with": [], "substitutes_for": [], "bundles_with": []}, "confidence": {"source": 0.9, "mechanism": 0.8, "destination": 0.0, "execution": 0.7, "overall": 0.45}, "verdict": "CANDIDATE", "decision_reason": "Strong source evidence; no destination to establish fit."},
  {"id": "PT-002", "name": "Dead-letter replay with per-message provenance", "family_id": null, "category": "reliability_operations", "problem": "Poison messages are lost or replayed blindly.", "mechanism": "Park failures with their failure context and replay them selectively.", "source_observation": "src/dlq/ stores failure context and exposes selective replay.", "evidence_ids": ["E-002"], "target_evidence_ids": [], "transfer": {"problem_fit": 0.5, "mechanism_fit": 0.5, "source_evidence_strength": 0.8, "destination_evidence_strength": 0.0, "implementation_feasibility": 0.5, "expected_upside": 0.5, "reversibility": 0.5, "maintenance_fit": 0.5, "strategic_fit": 0.5, "differentiation": 0.3, "dependency_risk": 0.3, "complexity_tax": 0.3, "opportunity_cost": 0.3, "legal_ip_risk": 0.7, "security_privacy_risk": 0.1, "measurement_risk": 0.3}, "gates": {"legal_ip": "review", "security_privacy": "not_required"}, "implementation": {"transfer_mode": "INSPIRE"}, "experiment": null, "interactions": {"requires": [], "enables": [], "conflicts_with": [], "substitutes_for": [], "bundles_with": []}, "confidence": {"source": 0.8, "mechanism": 0.7, "destination": 0.0, "execution": 0.5, "overall": 0.35}, "verdict": "REVIEW_REQUIRED", "decision_reason": "Licence of the vendored module is unclear; even a close reimplementation needs IP review."}
 ]
}
```
