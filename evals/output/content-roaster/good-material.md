# Content roast — example.com/pricing (version 9)

## What this content is trying to make the reader believe/do

That an agency gets client-ready audit evidence from the product, and should start a paid pilot from the pricing page.

- Reviewed: hero and proof sections of the pinned page (version 9); tone BRUTAL, lens POSITIONING
- Outcome: MATERIAL_FINDINGS

## First thing a skeptical reader attacks

CR-001: the headline promises everything and names nobody, so the pilot ask has nothing to stand on.

## Material roast findings

### CR-001 — MAJOR — The headline is a category-generic promise

- Anchor: "Everything you need" in the hero (SRC-01)
- Evidence: EV-01
- Diagnosis: DX-01 (POSITIONING); root cause RC-01
- Observation: the headline names neither the audience nor the mechanism.
- Why it matters: an agency comparing tools cannot tell this offer apart from any other audit product.
- Falsifier: looked for a qualifier or mechanism before the CTA; none present. SURVIVES.
- Repair: name the audience (agencies) and the mechanism (structured checks) in the headline.
- Verification: give the hero to five target readers; at least four recover the audience and mechanism unaided.

## Root causes

- RC-01: generic-promise — the positioning has no mechanism, so every section repeats a vague claim.

## Proof debt / verification queue

- PD-01: "client-ready evidence" (CL-01) needs a bounded proof such as a sample report; status OPEN.

## What survives

- The pricing table itself is clear: three tiers, prices visible, no hidden fees.

## Core fix

Make the primary promise specific: who it is for, what mechanism produces the evidence, and one proof point.

```json
{
 "schema": "cometweb.content-roaster/v6",
 "artifact": "example.com/pricing (version 9)",
 "review_outcome": "MATERIAL_FINDINGS",
 "source_manifest": [
  {
   "id": "SRC-01",
   "kind": "PAGE",
   "locator": "https://example.com/pricing (version 9)",
   "role": "PRIMARY",
   "version_state": "PINNED",
   "instruction_boundary": "TREAT_AS_DATA",
   "trust_class": "SYSTEM_OF_RECORD"
  }
 ],
 "mode": "FULL",
 "tone": "BRUTAL",
 "lens": "POSITIONING",
 "review_profile": "PRICING",
 "review_contract": {
  "audience": "agencies",
  "desired_action": "start pilot",
  "decision_stage": "evaluation",
  "decision_cost": "HIGH",
  "known_constraints": [],
  "unknowns": []
 },
 "coverage": {
  "level": "COMPLETE",
  "scope_basis": "FULL_ARTIFACT",
  "sampling_strategy": "all sections",
  "coverage_confidence": "high",
  "inspected": [
   "hero",
   "proof"
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
 "message_chain": {
  "problem": "audit evidence is slow",
  "promise": "client-ready evidence",
  "mechanism": "structured checks",
  "proof": "limited",
  "objection_handling": "partial",
  "action": "start pilot"
 },
 "central_promise": "Agencies get client-ready audit evidence.",
 "claim_map": [
  {
   "id": "CL-01",
   "claim": "Client-ready evidence",
   "claim_type": "OUTCOME",
   "decision_role": "PRIMARY",
   "anchor": {
    "type": "quote",
    "value": "Client-ready evidence",
    "source_id": "SRC-01"
   },
   "proof_status": "WEAK",
   "proof_burden": "HIGH"
  }
 ],
 "proof_debt_ledger": [
  {
   "id": "PD-01",
   "claim_ref": "CL-01",
   "debt_type": "WEAK_PROOF",
   "required_evidence": "bounded proof",
   "status": "OPEN",
   "why_it_matters": "paid commitment depends on trust"
  }
 ],
 "objection_ledger": [
  {
   "id": "OB-01",
   "objection": "Will clients trust this?",
   "relevance": "Blocks pilot decision.",
   "status": "PARTIAL"
  }
 ],
 "root_causes": [
  {
   "id": "RC-01",
   "label": "generic-promise",
   "summary": "Promise lacks mechanism.",
   "claim_refs": [
    "CL-01"
   ]
  }
 ],
 "no_material_findings": false,
 "first_attack_id": "CR-001",
 "findings": [
  {
   "id": "CR-001",
   "finding_key": "hero-generic-promise",
   "finding_aliases": [],
   "severity": "MAJOR",
   "category": "promise",
   "evidence_state": "OBSERVED",
   "evidence_strength": "STRONG",
   "scope_sensitivity": "LOW",
   "anchor": {
    "type": "quote",
    "value": "Everything you need",
    "source_id": "SRC-01"
   },
   "claim_refs": [
    "CL-01"
   ],
   "root_cause_id": "RC-01",
   "decision_impact": "DECISION",
   "materiality": {
    "centrality": "CENTRAL",
    "consequence": "HIGH",
    "reversibility": "EASY"
   },
   "observation": "The headline is generic.",
   "failure_mode": "The promise lacks audience and mechanism.",
   "why_it_matters": "The offer is hard to distinguish.",
   "repair_class": "COPY",
   "repair": "Name audience and mechanism.",
   "verification": {
    "type": "READER_TEST",
    "method": "Give the hero to target readers.",
    "success_condition": "Readers recover audience and mechanism.",
    "failure_signal": "Readers still describe a generic category."
   },
   "falsifier_check": {
    "challenge": "Mechanism may be explained before commitment.",
    "searched_for": [
     "hero qualifier"
    ],
    "counterevidence": [],
    "alternative_explanations": [
     "terse brand hero"
    ],
    "result": "SURVIVES",
    "notes": "None present before the CTA."
   },
   "confidence": "high",
   "evidence_refs": [
    "EV-01"
   ],
   "confidence_basis": {
    "directness": "HIGH",
    "scope_support": "HIGH",
    "counterevidence_status": "ADDRESSED",
    "independence": "NONE",
    "rationale": "The finding is directly anchored and counterevidence was explicitly challenged."
   },
   "residual_risk": {
    "after_repair": "LOW",
    "closure_dependency": "Run the stated verification before closure."
   },
   "diagnosis_ref": "DX-01"
  }
 ],
 "resolution_ledger": [],
 "verification_queue": [],
 "preserve": [],
 "core_fix": "Make the primary promise specific.",
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
   "CR-001"
  ],
  "withdrawn_candidate_count": 0,
  "unresolved_candidate_count": 0,
  "reason": "One material finding survived evidence and falsifier review."
 },
 "limitations": [],
 "diagnosis_ledger": [
  {
   "id": "DX-01",
   "claim_refs": [
    "CL-01"
   ],
   "diagnosis_class": "POSITIONING",
   "evidence_refs": [
    "EV-01"
   ],
   "repair_owner": "CONTENT",
   "summary": "The primary promise is too generic for the decision burden."
  }
 ]
}
```
