from __future__ import annotations
import copy
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("content_roast_validator", BASE / "scripts" / "validate_roast.py")
v = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v)


def valid_report():
    return {'schema': 'cometweb.content-roaster/v6',
     'artifact': 'pricing-v9',
     'review_outcome': 'MATERIAL_FINDINGS',
     'source_manifest': [{'id': 'SRC-01',
                          'kind': 'PAGE',
                          'locator': 'pricing-v9',
                          'role': 'PRIMARY',
                          'version_state': 'PINNED',
                          'instruction_boundary': 'TREAT_AS_DATA',
                          'trust_class': 'SYSTEM_OF_RECORD'}],
     'mode': 'FULL',
     'tone': 'BRUTAL',
     'lens': 'POSITIONING',
     'review_profile': 'PRICING',
     'review_contract': {'audience': 'agencies',
                         'desired_action': 'start pilot',
                         'decision_stage': 'evaluation',
                         'decision_cost': 'HIGH',
                         'known_constraints': [],
                         'unknowns': []},
     'coverage': {'level': 'COMPLETE',
                  'scope_basis': 'FULL_ARTIFACT',
                  'sampling_strategy': 'all sections',
                  'coverage_confidence': 'high',
                  'inspected': ['hero', 'proof'],
                  'not_inspected': [],
                  'limitations': []},
     'quality_gates': {'scope': 'PASS',
                       'contract': 'PASS',
                       'evidence': 'PASS',
                       'challenge': 'PASS',
                       'severity': 'PASS',
                       'repair': 'PASS',
                       'boundary': 'PASS',
                       'source_integrity': 'PASS',
                       'assurance': 'PASS'},
     'message_chain': {'problem': 'audit evidence is slow',
                       'promise': 'client-ready evidence',
                       'mechanism': 'structured checks',
                       'proof': 'limited',
                       'objection_handling': 'partial',
                       'action': 'start pilot'},
     'central_promise': 'Agencies get client-ready audit evidence.',
     'claim_map': [{'id': 'CL-01',
                    'claim': 'Client-ready evidence',
                    'claim_type': 'OUTCOME',
                    'decision_role': 'PRIMARY',
                    'anchor': {'type': 'quote', 'value': 'Client-ready evidence', 'source_id': 'SRC-01'},
                    'proof_status': 'WEAK',
                    'proof_burden': 'HIGH'}],
     'proof_debt_ledger': [{'id': 'PD-01',
                            'claim_ref': 'CL-01',
                            'debt_type': 'WEAK_PROOF',
                            'required_evidence': 'bounded proof',
                            'status': 'OPEN',
                            'why_it_matters': 'paid commitment depends on trust'}],
     'objection_ledger': [{'id': 'OB-01', 'objection': 'Will clients trust this?', 'relevance': 'Blocks pilot decision.', 'status': 'PARTIAL'}],
     'root_causes': [{'id': 'RC-01', 'label': 'generic-promise', 'summary': 'Promise lacks mechanism.', 'claim_refs': ['CL-01']}],
     'no_material_findings': False,
     'first_attack_id': 'CR-001',
     'findings': [{'id': 'CR-001',
                   'finding_key': 'hero-generic-promise',
                   'finding_aliases': [],
                   'severity': 'MAJOR',
                   'category': 'promise',
                   'evidence_state': 'OBSERVED',
                   'evidence_strength': 'STRONG',
                   'scope_sensitivity': 'LOW',
                   'anchor': {'type': 'quote', 'value': 'Everything you need', 'source_id': 'SRC-01'},
                   'claim_refs': ['CL-01'],
                   'root_cause_id': 'RC-01',
                   'decision_impact': 'DECISION',
                   'materiality': {'centrality': 'CENTRAL', 'consequence': 'HIGH', 'reversibility': 'EASY'},
                   'observation': 'The headline is generic.',
                   'failure_mode': 'The promise lacks audience and mechanism.',
                   'why_it_matters': 'The offer is hard to distinguish.',
                   'repair_class': 'COPY',
                   'repair': 'Name audience and mechanism.',
                   'verification': {'type': 'READER_TEST',
                                    'method': 'Give the hero to target readers.',
                                    'success_condition': 'Readers recover audience and mechanism.',
                                    'failure_signal': 'Readers still describe a generic category.'},
                   'falsifier_check': {'challenge': 'Mechanism may be explained before commitment.',
                                       'searched_for': ['hero qualifier'],
                                       'counterevidence': [],
                                       'alternative_explanations': ['terse brand hero'],
                                       'result': 'SURVIVES',
                                       'notes': 'None present before the CTA.'},
                   'confidence': 'high',
                   'evidence_refs': ['EV-01'],
                   'confidence_basis': {'directness': 'HIGH',
                                        'scope_support': 'HIGH',
                                        'counterevidence_status': 'ADDRESSED',
                                        'independence': 'NONE',
                                        'rationale': 'The finding is directly anchored and counterevidence was explicitly challenged.'},
                   'residual_risk': {'after_repair': 'LOW', 'closure_dependency': 'Run the stated verification before closure.'},
                   'diagnosis_ref': 'DX-01'}],
     'resolution_ledger': [],
     'verification_queue': [],
     'preserve': [],
     'core_fix': 'Make the primary promise specific.',
     'review_plan': {'objective': 'Find material failures without inflating false positives.',
                     'must_inspect': ['primary claim/invariant', 'highest-consequence path'],
                     'attack_surfaces': ['evidence-to-conclusion chain', 'counterevidence'],
                     'sampling_strategy': 'risk-first review of the pinned primary source',
                     'stop_conditions': ['stop when additional findings do not change repair or risk posture'],
                     'escalation_conditions': ['escalate when a top-severity finding remains scope-sensitive']},
     'assurance': {'mode': 'SINGLE_REVIEW',
                   'independence': 'NONE',
                   'second_pass_status': 'NOT_RUN',
                   'disagreement_summary': [],
                   'limitations': ['No independent second reviewer was run.'],
                   'pass_records': [{'pass_id': 'PASS-PRIMARY',
                                     'role': 'PRIMARY',
                                     'context_ref': 'current-context',
                                     'status': 'COMPLETED',
                                     'blind_to_prior_findings': False,
                                     'source_refs': ['SRC-01']}]},
     'evidence_register': [{'id': 'EV-01',
                            'source_id': 'SRC-01',
                            'kind': 'OBSERVATION',
                            'locator': 'primary reviewed evidence',
                            'summary': 'Direct evidence supporting the material review finding.',
                            'strength': 'STRONG',
                            'limitations': []}],
     'evidence_conflicts': [],
     'outcome_basis': {'surviving_finding_ids': ['CR-001'], 'withdrawn_candidate_count': 0, 'unresolved_candidate_count': 0, 'reason': 'One material finding survived evidence and falsifier review.'},
     'limitations': [],
     'diagnosis_ledger': [{'id': 'DX-01',
                           'claim_refs': ['CL-01'],
                           'diagnosis_class': 'POSITIONING',
                           'evidence_refs': ['EV-01'],
                           'repair_owner': 'CONTENT',
                           'summary': 'The primary promise is too generic for the decision burden.'}]}


def test_valid_report_passes():
    assert v.validate(valid_report()) == []


def test_no_findings_outcome_passes():
    r = valid_report(); r["findings"] = []; r["root_causes"] = []; r["outcome_basis"]["surviving_finding_ids"] = []; r["outcome_basis"]["reason"] = "No material candidate survived review."; r["first_attack_id"] = None; r["review_outcome"] = "NO_MATERIAL_FINDINGS"; r["no_material_findings"] = True; r["core_fix"] = "No material fix identified in reviewed scope."
    assert v.validate(r) == []


def test_insufficient_evidence_requires_blocked_gate():
    r = valid_report(); r["findings"] = []; r["root_causes"] = []; r["outcome_basis"]["surviving_finding_ids"] = []; r["outcome_basis"]["reason"] = "Evidence is insufficient for material admission."; r["first_attack_id"] = None; r["review_outcome"] = "INSUFFICIENT_EVIDENCE"; r["no_material_findings"] = False
    assert any("BLOCKED" in x for x in v.validate(r))
    r["quality_gates"]["scope"] = "BLOCKED"
    assert v.validate(r) == []


def test_major_requires_adversarial_check_fields():
    r = valid_report(); r["findings"][0]["falsifier_check"].pop("challenge")
    assert any("challenge" in x for x in v.validate(r))


def test_high_scope_sensitivity_caps_confidence():
    r = valid_report(); r["findings"][0]["scope_sensitivity"] = "HIGH"
    assert any("cannot have high confidence" in x for x in v.validate(r))


def test_blocker_requires_primary_central_and_nonweak():
    r = valid_report(); f = r["findings"][0]; f["severity"] = "BLOCKER"; f["evidence_strength"] = "WEAK"; f["materiality"]["centrality"] = "SUPPORTING"; r["claim_map"][0]["decision_role"] = "SUPPORTING"
    errs = v.validate(r)
    assert any("PRIMARY" in x for x in errs) and any("WEAK" in x for x in errs) and any("CENTRAL" in x for x in errs)


def test_missing_requires_omission_basis():
    r = valid_report(); f = r["findings"][0]; f["severity"] = "MINOR"; f["evidence_state"] = "MISSING"; f["anchor"] = {"type":"missing_element","value":"case study"}; f.pop("falsifier_check")
    assert any("omission_basis" in x for x in v.validate(r))


def test_guarantee_requires_very_high_burden():
    r = valid_report(); r["claim_map"][0]["claim_type"] = "GUARANTEE"
    assert any("VERY_HIGH" in x for x in v.validate(r))


def test_proof_debt_unknown_claim_fails():
    r = valid_report(); r["proof_debt_ledger"][0]["claim_ref"] = "CL-404"
    assert any("unknown claim" in x for x in v.validate(r))


def test_verification_requires_failure_signal():
    r = valid_report(); r["findings"][0]["verification"].pop("failure_signal")
    assert any("failure_signal" in x for x in v.validate(r))


def test_unknown_root_cause_fails():
    r = valid_report(); r["findings"][0]["root_cause_id"] = "RC-404"
    assert any("unknown root cause" in x for x in v.validate(r))


def test_delta_requires_comparison():
    r = valid_report(); r["mode"] = "DELTA"
    assert any("comparison" in x for x in v.validate(r))


def test_invalid_sha_fails():
    r = valid_report(); r["source_manifest"][0]["sha256"] = "abc"
    assert any("sha256" in x for x in v.validate(r))


def test_personal_attack_fails():
    r = valid_report(); r["findings"][0]["roast_line"] = "The writer is a clueless idiot."
    assert any("personal attack" in x for x in v.validate(r))

def test_anchor_source_id_must_reference_manifest():
    r=valid_report(); r["findings"][0]["anchor"]["source_id"]="SRC-404"; assert any("source_id" in x for x in v.validate(r))

def test_finding_alias_identity_collision_fails():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="CR-002"; second["finding_key"]="second-key"; second["finding_aliases"]=[r["findings"][0]["finding_key"]]; r["findings"].append(second); assert any("identity token" in x for x in v.validate(r))

def test_downgraded_falsifier_requires_higher_initial_severity():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["falsifier_check"]["result"]="DOWNGRADED"; assert any("downgraded_from" in x for x in v.validate(r)); f["falsifier_check"]["downgraded_from"]="MAJOR"; assert v.validate(r)==[]

def test_blocker_requires_high_consequence_and_nonlow_confidence():
    r=valid_report(); f=r["findings"][0]; f["severity"]="BLOCKER"; f["materiality"]["consequence"]="MEDIUM"; f["confidence"]="low"; errs=v.validate(r); assert any("consequence=HIGH" in x for x in errs) and any("low confidence" in x for x in errs)

def test_claim_map_requires_primary_claim():
    r=valid_report(); r["claim_map"][0]["decision_role"]="SUPPORTING"; assert any("PRIMARY claim" in x for x in v.validate(r))

def test_unresolved_high_burden_primary_claim_requires_proof_debt():
    r=valid_report(); r["proof_debt_ledger"]=[]; assert any("proof_debt_ledger entry" in x for x in v.validate(r))

def test_findings_must_be_ordered_and_first_attack_is_top_severity():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="CR-002"; second["finding_key"]="second-minor"; second["finding_aliases"]=[]; second["severity"]="MINOR"; second.pop("falsifier_check",None); second["root_cause_id"]=None; r["findings"]=[second,r["findings"][0]]; r["first_attack_id"]="CR-002"; errs=v.validate(r); assert any("ordered by severity" in x for x in errs) and any("highest-severity" in x for x in errs)


def test_primary_source_is_required():
    r=valid_report(); r["source_manifest"][0]["role"]="SUPPORTING"; assert any("PRIMARY source" in x for x in v.validate(r))

def test_weak_evidence_cannot_have_high_confidence():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["evidence_strength"]="WEAK"; f["confidence"]="high"; f.pop("falsifier_check",None); assert any("WEAK evidence cannot have high confidence" in x for x in v.validate(r))

def test_adversarial_check_requires_steelman_alternative():
    r=valid_report(); r["findings"][0]["falsifier_check"]["alternative_explanations"]=[]; assert any("alternative_explanations" in x for x in v.validate(r))

def test_resolved_revision_requires_passed_verification():
    r=valid_report(); r["resolution_ledger"]=[{"finding_key":"old-key","status":"RESOLVED","evidence":"fix claimed","verification_status":"NOT_RUN","change_basis":"ARTIFACT_CHANGED"}]; assert any("RESOLVED requires verification_status=PASSED" in x for x in v.validate(r)); r["resolution_ledger"][0]["verification_status"]="PASSED"; assert v.validate(r)==[]

def test_resolution_ledger_requires_change_basis():
    r=valid_report(); r["resolution_ledger"]=[{"finding_key":"old-key","status":"OPEN","evidence":"failure still observed","verification_status":"FAILED"}]; assert any("change_basis" in x for x in v.validate(r))

def test_v6_source_instruction_boundary_is_enforced():
    r=valid_report(); r["source_manifest"][0]["instruction_boundary"]="FOLLOW_INSTRUCTIONS"; assert any("TREAT_AS_DATA" in x for x in v.validate(r))

def test_v6_source_trust_class_is_enforced():
    r=valid_report(); r["source_manifest"][0]["trust_class"]="TRUSTED_BY_VIBES"; assert any("trust_class" in x for x in v.validate(r))

def test_v6_review_plan_requires_must_inspect():
    r=valid_report(); r["review_plan"]["must_inspect"]=[]; assert any("must_inspect" in x for x in v.validate(r))

def test_v6_blind_dual_review_requires_separate_completed_pass():
    r=valid_report(); r["assurance"]={"mode":"BLIND_DUAL_REVIEW","independence":"SAME_CONTEXT","second_pass_status":"COMPLETED","disagreement_summary":[],"limitations":[]}; r["findings"][0]["confidence_basis"]["independence"]="SAME_CONTEXT"; assert any("BLIND_DUAL_REVIEW" in x for x in v.validate(r))

def test_v6_unknown_evidence_reference_fails():
    r=valid_report(); r["findings"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_high_confidence_requires_counterevidence_control():
    r=valid_report(); r["findings"][0]["confidence"]="high"; r["findings"][0]["confidence_basis"]["counterevidence_status"]="UNKNOWN"; assert any("high confidence" in x for x in v.validate(r))

def test_v6_unresolved_conflict_requires_evidence_gate_warning():
    r=valid_report(); r["evidence_register"].append({"id":"EV-02","source_id":"SRC-01","kind":"COUNTEREVIDENCE","locator":"section:proof","summary":"Counterevidence weakens the claim.","strength":"MODERATE","limitations":[]}); r["evidence_conflicts"]=[{"id":"EC-01","evidence_refs":["EV-01","EV-02"],"conflict":"Evidence points in opposing directions.","disposition":"UNRESOLVED","residual_uncertainty":"Net claim support remains uncertain."}]; assert any("quality_gates.evidence" in x for x in v.validate(r)); r["quality_gates"]["evidence"]="WARN"; assert v.validate(r)==[]

def test_v6_residual_risk_requires_closure_dependency():
    r=valid_report(); r["findings"][0]["residual_risk"]["closure_dependency"]=""; assert any("closure_dependency" in x for x in v.validate(r))

def test_v6_finding_requires_known_diagnosis_ref():
    r=valid_report(); r["findings"][0]["diagnosis_ref"]="DX-404"; assert any("diagnosis_ledger" in x for x in v.validate(r))

def test_v6_diagnosis_ledger_rejects_unknown_evidence():
    r=valid_report(); r["diagnosis_ledger"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_assurance_requires_auditable_pass_records():
    r=valid_report(); r["assurance"]["pass_records"]=[]; assert any("pass_records" in x for x in v.validate(r))

def test_v6_outcome_basis_must_match_surviving_findings():
    r=valid_report(); r["outcome_basis"]["surviving_finding_ids"]=[]; assert any("surviving_finding_ids" in x for x in v.validate(r))
