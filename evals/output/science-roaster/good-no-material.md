# Science roast — example-org/cache-latency-note v1

- Artifact: `example-org/cache-latency-note v1` (SRC-01, pinned)
- Mode: QUICK, evidence mode SOURCE_BOUND, profile COMPUTATIONAL
- Outcome: NO_MATERIAL_FINDINGS

## What the paper actually claims

- CL-01: on the benchmark trace, the read-through cache lowers p95 latency (central, DESCRIPTIVE, Table 2).

## Fatal / major / minor findings

None. One candidate (the cache arm might run with a warm OS page cache) was withdrawn: the methods describe a cold-start protocol for every replay (EV-01).

## Claim-evidence / validity mismatches

- None. CL-01 stays descriptive and inside the benchmark trace; Table 2 reports replay-level intervals for both arms.

## External verification queue

- None: the claim needs no external source.

## What survives / minimal surviving claim

- CL-01 survives as stated: on this benchmark trace the cache lowers p95 latency.

## Core scientific fix

None required; keep the claim descriptive and scoped to the trace. Generalizing to production traffic would need new data.

```json
{
 "schema": "cometweb.science-roaster/v6",
 "artifact": "example-org/cache-latency-note v1",
 "review_outcome": "NO_MATERIAL_FINDINGS",
 "source_manifest": [
  {
   "id": "SRC-01",
   "kind": "MANUSCRIPT",
   "locator": "https://example.org/notes/cache-latency-v1.pdf",
   "role": "PRIMARY",
   "version_state": "PINNED",
   "instruction_boundary": "TREAT_AS_DATA",
   "trust_class": "SYSTEM_OF_RECORD"
  }
 ],
 "mode": "QUICK",
 "evidence_mode": "SOURCE_BOUND",
 "study_profile": "COMPUTATIONAL",
 "study_contract": {
  "research_question": "Does the read-through cache lower p95 latency on the benchmark trace?",
  "target_construct": "p95 request latency",
  "population": "benchmark trace replays",
  "analysis_population": "30 replays per arm",
  "unit_of_analysis": "replay",
  "reference": "NOT_APPLICABLE",
  "reference_status": "NOT_APPLICABLE",
  "estimand": "difference in p95 latency between arms",
  "primary_endpoint": "p95 latency",
  "evidence_status": "descriptive",
  "preregistration_status": "NOT_REPORTED",
  "novelty_claim": "none claimed",
  "missingness_strategy": "no missing replays",
  "multiplicity_strategy": "single endpoint",
  "dependence_structure": "independent replays"
 },
 "coverage": {
  "level": "COMPLETE",
  "scope_basis": "FULL_ARTIFACT",
  "sampling_strategy": "all sections",
  "coverage_confidence": "high",
  "inspected": [
   "methods",
   "results",
   "benchmark script"
  ],
  "not_inspected": [],
  "limitations": []
 },
 "quality_gates": {
  "scope": "PASS",
  "contract": "PASS",
  "evidence": "PASS",
  "challenge": "PASS",
  "severity": "PASS",
  "repair": "PASS",
  "boundary": "PASS",
  "source_integrity": "PASS",
  "assurance": "PASS"
 },
 "measurement_chain": {
  "construct": "p95 latency",
  "operationalization": "timer at client",
  "reference": "NOT_APPLICABLE",
  "transformation": "NOT_APPLICABLE",
  "endpoint": "p95 latency",
  "alignment_status": "ALIGNED"
 },
 "claim_map": [
  {
   "id": "CL-01",
   "claim": "On the benchmark trace the cache lowers p95 latency.",
   "central": true,
   "inferential_type": "DESCRIPTIVE",
   "evidence_role": "PRIMARY",
   "population_scope": "benchmark trace",
   "endpoint_scope": "p95 latency",
   "analysis_set": "30 replays per arm",
   "anchor": {
    "type": "table",
    "value": "Table 2",
    "source_id": "SRC-01"
   },
   "support_status": "SUPPORTED"
  }
 ],
 "validity_ledger": [
  {
   "domain": "STATISTICAL",
   "status": "SUPPORTED",
   "basis": "Replay-level intervals reported for both arms."
  }
 ],
 "analysis_integrity_ledger": [
  {
   "area": "DEPENDENCE",
   "status": "ADEQUATE",
   "basis": "Replays use separate processes and cold starts."
  }
 ],
 "alternative_explanations": [
  {
   "id": "AE-01",
   "claim_refs": [
    "CL-01"
   ],
   "explanation": "Warm OS page cache in the cache arm only.",
   "addressed_by": [
    "cold-start protocol"
   ],
   "status": "ADDRESSED"
  }
 ],
 "robustness_ledger": [
  {
   "claim_ref": "CL-01",
   "check": "rerun with shuffled arm order",
   "status": "ROBUST",
   "evidence": "Supplementary run order table."
  }
 ],
 "root_causes": [],
 "no_material_findings": true,
 "first_attack_id": null,
 "findings": [],
 "resolution_ledger": [],
 "external_verification_queue": [],
 "claim_survival": [
  {
   "claim_ref": "CL-01",
   "status": "SURVIVES_AS_STATED",
   "reason": "Descriptive claim stays inside the benchmark trace."
  }
 ],
 "survives": [
  "The descriptive p95 improvement on the benchmark trace."
 ],
 "minimal_surviving_claim": "On this benchmark trace the cache lowers p95 latency.",
 "core_fix": "None required; keep the claim descriptive and scoped to the trace.",
 "review_plan": {
  "objective": "Find material failures without inflating false positives.",
  "must_inspect": [
   "primary claim/invariant",
   "highest-consequence path"
  ],
  "attack_surfaces": [
   "evidence-to-conclusion chain",
   "counterevidence"
  ],
  "sampling_strategy": "risk-first review of the pinned primary source",
  "stop_conditions": [
   "stop when additional findings do not change repair or risk posture"
  ],
  "escalation_conditions": [
   "escalate when a top-severity finding remains scope-sensitive"
  ]
 },
 "assurance": {
  "mode": "SINGLE_REVIEW",
  "independence": "NONE",
  "second_pass_status": "NOT_RUN",
  "disagreement_summary": [],
  "limitations": [
   "No independent second reviewer was run."
  ],
  "pass_records": [
   {
    "pass_id": "PASS-PRIMARY",
    "role": "PRIMARY",
    "context_ref": "current-context",
    "status": "COMPLETED",
    "blind_to_prior_findings": false,
    "source_refs": [
     "SRC-01"
    ]
   }
  ]
 },
 "evidence_register": [
  {
   "id": "EV-01",
   "source_id": "SRC-01",
   "kind": "OBSERVATION",
   "locator": "Table 2",
   "summary": "Table 2 reports replay-level p95 for both arms with intervals.",
   "strength": "STRONG",
   "limitations": []
  }
 ],
 "evidence_conflicts": [],
 "outcome_basis": {
  "surviving_finding_ids": [],
  "withdrawn_candidate_count": 1,
  "unresolved_candidate_count": 0,
  "reason": "One candidate (warm page cache) was withdrawn after the cold-start protocol was found."
 },
 "limitations": [],
 "inferential_claim_ledger": [
  {
   "claim_ref": "CL-01",
   "estimand": "difference in p95 latency",
   "independent_unit": "replay",
   "analysis_population": "30 replays per arm",
   "uncertainty_basis": "bootstrap interval over replays",
   "multiplicity_status": "NOT_APPLICABLE",
   "identification_status": "DESCRIPTIVE_ONLY",
   "data_split_status": "NOT_APPLICABLE",
   "evidence_refs": [
    "EV-01"
   ]
  }
 ]
}
```
