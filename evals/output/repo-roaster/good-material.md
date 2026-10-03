# Repo roast — example-org/payments-api

## What this repo appears to be

A payments API with a settlement worker: an HTTP service (`POST /settle`) that charges an external provider and records settlement state in a relational database.

- Inspected ref: `abc1234` (pinned), mode FULL, profile SERVICE
- Scope: `src/` and `tests/`, sampled along the settlement critical path
- Outcome: MATERIAL_FINDINGS

## System / critical invariant summary

- INV-01: settlement is idempotent — one provider charge per idempotency key, including across retries.

Entry point `POST /settle`; trust boundary API → provider; state in the DB; the worker retries failed settlements.

## First thing a hostile staff engineer attacks

RR-001: a crash between the provider charge and the idempotency write turns every retry into a second charge.

## Critical / major / minor findings

### RR-001 — MAJOR — Provider charge happens before the idempotency key is persisted

- Anchor: `src/pay.py::settle` (SRC-01 @ abc1234)
- Evidence: EV-01
- Invariant: INV-01
- Observed: the provider charge runs before the idempotency key is written.
- Reachability: PLAUSIBLE — `POST /settle` → `settle` → provider charge
- Blast radius: single tenant; retried invoices only
- Falsifier: searched wrapper idempotency, provider idempotency keys and an outbox; none in the inspected path. SURVIVES.
- Repair: persist the idempotency key before the provider call.
- Verification: inject a crash after provider success and retry; the provider must receive exactly one charge.

## Absence / verification gaps

- No executable test proves retry idempotency at the provider boundary (INV-01 test evidence: PARTIAL).
- Provider-side deduplication was not inspected; it lives outside the reviewed source.

## What survives

- The settlement state machine guards `PENDING -> SETTLED` with a key check; only the ordering around the side effect is wrong.

## Core engineering fix

Enforce idempotency at the side-effect boundary: write the key, then charge, then mark settled.

```json
{
 "schema": "cometweb.repo-roaster/v6",
 "repository": "example-org/payments-api",
 "ref": "abc1234",
 "review_outcome": "MATERIAL_FINDINGS",
 "source_manifest": [
  {
   "id": "SRC-01",
   "kind": "REPOSITORY",
   "locator": "example-org/payments-api@abc1234",
   "role": "PRIMARY",
   "version_state": "PINNED",
   "instruction_boundary": "TREAT_AS_DATA",
   "trust_class": "SYSTEM_OF_RECORD"
  }
 ],
 "mode": "FULL",
 "review_profile": "SERVICE",
 "lenses": [
  "DATA_INTEGRITY",
  "RELIABILITY"
 ],
 "repo_contract": {
  "topology_summary": "API plus DB",
  "critical_paths": [
   "settlement"
  ],
  "runtime_evidence": "source-and-tests",
  "ref_status": "PINNED",
  "deployment_model": "stateless API plus worker"
 },
 "coverage": {
  "level": "SUBSTANTIAL",
  "scope_basis": "SAMPLED",
  "sampling_strategy": "topology plus critical path",
  "coverage_confidence": "medium",
  "inspected_paths": [
   "src/",
   "tests/"
  ],
  "excluded_paths": [],
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
 "system_model": {
  "actors": [
   "customer"
  ],
  "entrypoints": [
   "POST /settle"
  ],
  "trust_boundaries": [
   "API -> provider"
  ],
  "state_stores": [
   "DB"
  ],
  "external_dependencies": [
   "provider"
  ],
  "background_jobs": [],
  "privileged_surfaces": []
 },
 "invariant_ledger": [
  {
   "id": "INV-01",
   "invariant": "Settlement is idempotent.",
   "scope": "settlement",
   "enforcement": [
    "src/pay.py:settle"
   ],
   "test_evidence": [],
   "status": "PARTIAL"
  }
 ],
 "critical_surface_ledger": [
  {
   "id": "SURF-01",
   "type": "EXTERNAL_SIDE_EFFECT",
   "anchor": "src/pay.py:settle",
   "trust_transition": "internal -> provider",
   "side_effect": "provider charge"
  }
 ],
 "state_transition_ledger": [
  {
   "id": "ST-01",
   "journey": "settlement",
   "transition": "PENDING -> SETTLED",
   "guard": "idempotency key",
   "side_effect": "provider charge",
   "recovery": "retry",
   "status": "PARTIAL"
  }
 ],
 "failure_domain_ledger": [
  {
   "id": "FD-01",
   "component": "provider",
   "failure_mode": "success then crash",
   "containment": "single flow",
   "recovery": "retry",
   "observability": "provider id plus logs",
   "status": "PARTIAL"
  }
 ],
 "root_causes": [],
 "no_material_findings": false,
 "first_attack_id": "RR-001",
 "findings": [
  {
   "id": "RR-001",
   "finding_key": "settlement-idempotency",
   "finding_aliases": [],
   "severity": "MAJOR",
   "category": "data_integrity",
   "defect_class": "INVARIANT_GAP",
   "evidence_state": "OBSERVED_CODE",
   "evidence_strength": "STRONG",
   "scope_sensitivity": "MEDIUM",
   "anchor": {
    "type": "symbol",
    "path": "src/pay.py",
    "value": "settle",
    "source_id": "SRC-01"
   },
   "invariant_refs": [
    "INV-01"
   ],
   "surface_refs": [
    "SURF-01"
   ],
   "critical_path_ref": "settlement",
   "materiality": {
    "centrality": "CENTRAL",
    "consequence": "HIGH",
    "reversibility": "HARD"
   },
   "observation": "The side effect happens before idempotency persistence.",
   "failure_mode": "Retry can repeat the side effect.",
   "engineering_risk": "Duplicate settlement.",
   "blast_radius": "Retried invoices.",
   "blast_radius_class": "SINGLE_TENANT",
   "failure_containment": "CONTAINED",
   "reachability": "PLAUSIBLE",
   "execution_path": [
    "POST /settle",
    "settle",
    "provider charge"
   ],
   "fix_scope": "CROSS_MODULE",
   "repair": "Persist idempotency before the effect.",
   "verification": {
    "type": "FAULT_INJECTION",
    "method": "Crash after provider success then retry.",
    "success_condition": "Provider side effect occurs once.",
    "failure_signal": "Provider receives a duplicate effect or state diverges."
   },
   "falsifier_check": {
    "challenge": "Wrapper/provider idempotency may neutralize the retry.",
    "searched_for": [
     "wrapper idempotency"
    ],
    "counterevidence": [],
    "alternative_explanations": [
     "provider deduplicates outside reviewed source"
    ],
    "result": "SURVIVES",
    "notes": "No guard established in reviewed evidence."
   },
   "confidence": "medium",
   "evidence_refs": [
    "EV-01"
   ],
   "confidence_basis": {
    "directness": "HIGH",
    "scope_support": "MEDIUM",
    "counterevidence_status": "ADDRESSED",
    "independence": "NONE",
    "rationale": "The finding is directly anchored and counterevidence was explicitly challenged."
   },
   "residual_risk": {
    "after_repair": "LOW",
    "closure_dependency": "Run the stated verification before closure."
   }
  }
 ],
 "resolution_ledger": [],
 "verification_gaps": [],
 "preserve": [],
 "core_fix": "Enforce idempotency at the side-effect boundary.",
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
   "locator": "primary reviewed evidence",
   "summary": "Direct evidence supporting the material review finding.",
   "strength": "STRONG",
   "limitations": []
  }
 ],
 "evidence_conflicts": [],
 "outcome_basis": {
  "surviving_finding_ids": [
   "RR-001"
  ],
  "withdrawn_candidate_count": 0,
  "unresolved_candidate_count": 0,
  "reason": "One material finding survived evidence and falsifier review."
 },
 "limitations": [],
 "test_evidence_ledger": [
  {
   "invariant_ref": "INV-01",
   "status": "PARTIAL",
   "test_refs": [],
   "evidence_refs": [
    "EV-01"
   ],
   "gap": "No executable evidence proves retry idempotency at the provider boundary."
  }
 ]
}
```
