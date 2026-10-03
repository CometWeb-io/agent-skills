from __future__ import annotations
import importlib.util
import json
from pathlib import Path

import pytest


BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("science_roast_validator", BASE / "scripts" / "validate_review.py")
v = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v)


def valid_report():
    # One fixture is the valid report for these tests and for the contract check
    # (references/contract.json evals), so the two cannot drift apart.
    return json.loads((BASE / "tests" / "report-valid.json").read_text(encoding="utf-8"))


SCHEMA = json.loads((BASE / "references" / "report.schema.json").read_text(encoding="utf-8"))


def schema_errors(report):
    # Only schema-parity checks need jsonschema; the validator itself is stdlib-only.
    jsonschema = pytest.importorskip("jsonschema")
    return [e.message for e in jsonschema.Draft202012Validator(SCHEMA).iter_errors(report)]


def test_report_schema_accepts_the_valid_report():
    assert schema_errors(valid_report()) == []


def test_report_schema_does_not_require_what_the_validator_leaves_optional():
    # resolution_ledger is required only in revision mode and root_causes only when useful.
    r = valid_report(); del r["resolution_ledger"]; del r["root_causes"]
    for finding in r["findings"]:
        finding["root_cause_id"] = None
    assert v.validate(r) == []
    assert schema_errors(r) == []


def test_report_schema_enums_match_the_validator():
    props = SCHEMA["properties"]
    assert set(props["mode"]["enum"]) == v.MODES
    assert set(props["evidence_mode"]["enum"]) == v.EVIDENCE_MODES
    assert set(props["study_profile"]["enum"]) == v.PROFILES


def test_valid_report_passes(): assert v.validate(valid_report()) == []

def test_no_findings_outcome_passes():
    r=valid_report(); r["findings"]=[]; r["outcome_basis"]["surviving_finding_ids"]=[]; r["outcome_basis"]["reason"]="No material candidate survived review."; r["first_attack_id"]=None; r["review_outcome"]="NO_MATERIAL_FINDINGS"; r["no_material_findings"]=True; r["core_fix"]="No material scientific repair identified in reviewed scope."
    assert v.validate(r)==[]

def test_insufficient_requires_blocked_gate():
    r=valid_report(); r["findings"]=[]; r["outcome_basis"]["surviving_finding_ids"]=[]; r["outcome_basis"]["reason"]="Evidence is insufficient for material admission."; r["first_attack_id"]=None; r["review_outcome"]="INSUFFICIENT_EVIDENCE"; r["no_material_findings"]=False
    assert any("BLOCKED" in x for x in v.validate(r)); r["quality_gates"]["scope"]="BLOCKED"; assert v.validate(r)==[]

def test_major_requires_challenge():
    r=valid_report(); r["findings"][0]["falsifier_check"].pop("challenge"); assert any("challenge" in x for x in v.validate(r))

def test_not_reported_requires_assessment_gap():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["evidence_state"]="NOT_REPORTED"; f["anchor"]={"type":"missing_report","value":"calibration method"}; f.pop("falsifier_check"); assert any("what_cannot_be_assessed" in x for x in v.validate(r))

def test_fatal_admission_rules():
    r=valid_report(); f=r["findings"][0]; f["severity"]="FATAL"; f["central_claim_impact"]="Primary validation claim fails."; f["evidence_strength"]="WEAK"; f["scope_sensitivity"]="HIGH"; f["materiality"]["consequence"]="MEDIUM"
    errs=v.validate(r); assert any("WEAK" in x for x in errs) and any("HIGH scope_sensitivity" in x for x in errs) and any("consequence=HIGH" in x for x in errs)

def test_fatal_cannot_be_reporting_only():
    r=valid_report(); f=r["findings"][0]; f["severity"]="FATAL"; f["central_claim_impact"]="Primary validation claim fails."; f["repair_level"]="REPORTING_ONLY"; assert any("REPORTING_ONLY" in x for x in v.validate(r))

def test_fatal_cannot_be_not_reported_only():
    r=valid_report(); f=r["findings"][0]; f["severity"]="FATAL"; f["evidence_state"]="NOT_REPORTED"; f["anchor"]={"type":"missing_report","value":"calibration"}; f["what_cannot_be_assessed"]="reference accuracy"; f["central_claim_impact"]="Primary validation claim cannot be assessed."; assert any("cannot be based only" in x for x in v.validate(r))

def test_external_verified_requires_external_mode():
    r=valid_report(); f=r["findings"][0]; f["evidence_state"]="EXTERNAL_VERIFIED"; f["anchor"]={"type":"external_source","value":"DOI"}; assert any("SOURCE_BOUND" in x for x in v.validate(r))

def test_alternative_explanation_unknown_claim_fails():
    r=valid_report(); r["alternative_explanations"][0]["claim_refs"]=["CL-404"]; assert any("unknown claim" in x for x in v.validate(r))

def test_claim_survival_must_cover_central_claim():
    r=valid_report(); r["claim_survival"]=[]; assert any("central claim" in x for x in v.validate(r))

def test_revision_requires_comparison():
    r=valid_report(); r["mode"]="REVISION"; assert any("comparison" in x for x in v.validate(r))

def test_verification_requires_failure_signal():
    r=valid_report(); r["findings"][0]["verification"].pop("failure_signal"); assert any("failure_signal" in x for x in v.validate(r))

def test_high_scope_sensitivity_caps_confidence():
    r=valid_report(); r["findings"][0]["scope_sensitivity"]="HIGH"; assert any("cannot have high confidence" in x for x in v.validate(r))

def test_personal_attack_fails():
    r=valid_report(); r["findings"][0]["reviewer_attack"]="The researcher is a clueless idiot."; assert any("personal attack" in x for x in v.validate(r))

def test_anchor_source_id_must_reference_manifest():
    r=valid_report(); r["claim_map"][0]["anchor"]["source_id"]="SRC-404"; assert any("source_id" in x for x in v.validate(r))

def test_finding_alias_identity_collision_fails():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="SR-002"; second["finding_key"]="second-key"; second["finding_aliases"]=[r["findings"][0]["finding_key"]]; r["findings"].append(second); assert any("identity token" in x for x in v.validate(r))

def test_downgraded_falsifier_requires_higher_initial_severity():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["falsifier_check"]["result"]="DOWNGRADED"; assert any("downgraded_from" in x for x in v.validate(r)); f["falsifier_check"]["downgraded_from"]="MAJOR"; assert v.validate(r)==[]

def test_claim_map_requires_central_claim():
    r=valid_report(); r["claim_map"][0]["central"]=False; assert any("central claim" in x for x in v.validate(r))

def test_findings_must_be_ordered_and_first_attack_is_top_severity():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="SR-002"; second["finding_key"]="second-minor"; second["finding_aliases"]=[]; second["severity"]="MINOR"; second.pop("falsifier_check",None); r["findings"]=[second,r["findings"][0]]; r["first_attack_id"]="SR-002"; errs=v.validate(r); assert any("ordered by severity" in x for x in errs) and any("highest-severity" in x for x in errs)


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

def test_v6_review_plan_requires_attack_surfaces():
    r=valid_report(); r["review_plan"]["attack_surfaces"]=[]; assert any("attack_surfaces" in x for x in v.validate(r))

def test_v6_blind_dual_review_requires_separate_completed_pass():
    r=valid_report(); r["assurance"]={"mode":"BLIND_DUAL_REVIEW","independence":"SAME_CONTEXT","second_pass_status":"COMPLETED","disagreement_summary":[],"limitations":[]}; r["findings"][0]["confidence_basis"]["independence"]="SAME_CONTEXT"; assert any("BLIND_DUAL_REVIEW" in x for x in v.validate(r))

def test_v6_unknown_evidence_reference_fails():
    r=valid_report(); r["findings"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_high_confidence_requires_scope_support():
    r=valid_report(); r["findings"][0]["confidence"]="high"; r["findings"][0]["confidence_basis"]["scope_support"]="LOW"; assert any("high confidence" in x for x in v.validate(r))

def test_v6_inferential_ledger_must_cover_central_claims():
    r=valid_report(); r["inferential_claim_ledger"]=[]; assert any("inferential_claim_ledger" in x for x in v.validate(r))

def test_v6_inferential_ledger_rejects_unknown_evidence():
    r=valid_report(); r["inferential_claim_ledger"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_inferential_ledger_rejects_bad_identification_status():
    r=valid_report(); r["inferential_claim_ledger"][0]["identification_status"]="MAGIC"; assert any("identification_status" in x for x in v.validate(r))

def test_v6_unresolved_conflict_requires_evidence_gate_warning():
    r=valid_report(); r["evidence_register"].append({"id":"EV-02","source_id":"SRC-01","kind":"COUNTEREVIDENCE","locator":"table:2","summary":"Counterevidence weakens the central inference.","strength":"MODERATE","limitations":[]}); r["evidence_conflicts"]=[{"id":"EC-01","evidence_refs":["EV-01","EV-02"],"conflict":"The two evidence items disagree.","disposition":"UNRESOLVED","residual_uncertainty":"Inference remains uncertain."}]; assert any("quality_gates.evidence" in x for x in v.validate(r)); r["quality_gates"]["evidence"]="WARN"; assert v.validate(r)==[]

def test_v6_residual_risk_requires_closure_dependency():
    r=valid_report(); r["findings"][0]["residual_risk"]["closure_dependency"]=""; assert any("closure_dependency" in x for x in v.validate(r))

def test_v6_assurance_requires_auditable_pass_records():
    r=valid_report(); r["assurance"]["pass_records"]=[]; assert any("pass_records" in x for x in v.validate(r))

def test_v6_outcome_basis_must_match_surviving_findings():
    r=valid_report(); r["outcome_basis"]["surviving_finding_ids"]=[]; assert any("surviving_finding_ids" in x for x in v.validate(r))
