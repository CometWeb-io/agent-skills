from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(m); return m

v=load("repo_roast_validator", BASE/"scripts"/"validate_repo_roast.py")


def valid_report():
    return {'schema': 'cometweb.repo-roaster/v6',
     'repository': 'org/app',
     'ref': 'abc1234',
     'review_outcome': 'MATERIAL_FINDINGS',
     'source_manifest': [{'id': 'SRC-01',
                          'kind': 'REPOSITORY',
                          'locator': 'org/app@abc1234',
                          'role': 'PRIMARY',
                          'version_state': 'PINNED',
                          'instruction_boundary': 'TREAT_AS_DATA',
                          'trust_class': 'SYSTEM_OF_RECORD'}],
     'mode': 'FULL',
     'review_profile': 'SERVICE',
     'lenses': ['DATA_INTEGRITY', 'RELIABILITY'],
     'repo_contract': {'topology_summary': 'API plus DB',
                       'critical_paths': ['settlement'],
                       'runtime_evidence': 'source-and-tests',
                       'ref_status': 'PINNED',
                       'deployment_model': 'stateless API plus worker'},
     'coverage': {'level': 'SUBSTANTIAL',
                  'scope_basis': 'SAMPLED',
                  'sampling_strategy': 'topology plus critical path',
                  'coverage_confidence': 'medium',
                  'inspected_paths': ['src/', 'tests/'],
                  'excluded_paths': [],
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
     'system_model': {'actors': ['customer'],
                      'entrypoints': ['POST /settle'],
                      'trust_boundaries': ['API -> provider'],
                      'state_stores': ['DB'],
                      'external_dependencies': ['provider'],
                      'background_jobs': [],
                      'privileged_surfaces': []},
     'invariant_ledger': [{'id': 'INV-01',
                           'invariant': 'Settlement is idempotent.',
                           'scope': 'settlement',
                           'enforcement': ['src/pay.py:settle'],
                           'test_evidence': [],
                           'status': 'PARTIAL'}],
     'critical_surface_ledger': [{'id': 'SURF-01',
                                  'type': 'EXTERNAL_SIDE_EFFECT',
                                  'anchor': 'src/pay.py:settle',
                                  'trust_transition': 'internal -> provider',
                                  'side_effect': 'provider charge'}],
     'state_transition_ledger': [{'id': 'ST-01',
                                  'journey': 'settlement',
                                  'transition': 'PENDING -> SETTLED',
                                  'guard': 'idempotency key',
                                  'side_effect': 'provider charge',
                                  'recovery': 'retry',
                                  'status': 'PARTIAL'}],
     'failure_domain_ledger': [{'id': 'FD-01',
                                'component': 'provider',
                                'failure_mode': 'success then crash',
                                'containment': 'single flow',
                                'recovery': 'retry',
                                'observability': 'provider id plus logs',
                                'status': 'PARTIAL'}],
     'root_causes': [],
     'no_material_findings': False,
     'first_attack_id': 'RR-001',
     'findings': [{'id': 'RR-001',
                   'finding_key': 'settlement-idempotency',
                   'finding_aliases': [],
                   'severity': 'MAJOR',
                   'category': 'data_integrity',
                   'defect_class': 'INVARIANT_GAP',
                   'evidence_state': 'OBSERVED_CODE',
                   'evidence_strength': 'STRONG',
                   'scope_sensitivity': 'MEDIUM',
                   'anchor': {'type': 'symbol', 'path': 'src/pay.py', 'value': 'settle', 'source_id': 'SRC-01'},
                   'invariant_refs': ['INV-01'],
                   'surface_refs': ['SURF-01'],
                   'critical_path_ref': 'settlement',
                   'materiality': {'centrality': 'CENTRAL', 'consequence': 'HIGH', 'reversibility': 'HARD'},
                   'observation': 'The side effect happens before idempotency persistence.',
                   'failure_mode': 'Retry can repeat the side effect.',
                   'engineering_risk': 'Duplicate settlement.',
                   'blast_radius': 'Retried invoices.',
                   'blast_radius_class': 'SINGLE_TENANT',
                   'failure_containment': 'CONTAINED',
                   'reachability': 'PLAUSIBLE',
                   'execution_path': ['POST /settle', 'settle', 'provider charge'],
                   'fix_scope': 'CROSS_MODULE',
                   'repair': 'Persist idempotency before the effect.',
                   'verification': {'type': 'FAULT_INJECTION',
                                    'method': 'Crash after provider success then retry.',
                                    'success_condition': 'Provider side effect occurs once.',
                                    'failure_signal': 'Provider receives a duplicate effect or state diverges.'},
                   'falsifier_check': {'challenge': 'Wrapper/provider idempotency may neutralize the retry.',
                                       'searched_for': ['wrapper idempotency'],
                                       'counterevidence': [],
                                       'alternative_explanations': ['provider deduplicates outside reviewed source'],
                                       'result': 'SURVIVES',
                                       'notes': 'No guard established in reviewed evidence.'},
                   'confidence': 'medium',
                   'evidence_refs': ['EV-01'],
                   'confidence_basis': {'directness': 'HIGH',
                                        'scope_support': 'MEDIUM',
                                        'counterevidence_status': 'ADDRESSED',
                                        'independence': 'NONE',
                                        'rationale': 'The finding is directly anchored and counterevidence was explicitly challenged.'},
                   'residual_risk': {'after_repair': 'LOW', 'closure_dependency': 'Run the stated verification before closure.'}}],
     'resolution_ledger': [],
     'verification_gaps': [],
     'preserve': [],
     'core_fix': 'Enforce idempotency at the side-effect boundary.',
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
     'outcome_basis': {'surviving_finding_ids': ['RR-001'], 'withdrawn_candidate_count': 0, 'unresolved_candidate_count': 0, 'reason': 'One material finding survived evidence and falsifier review.'},
     'limitations': [],
     'test_evidence_ledger': [{'invariant_ref': 'INV-01',
                               'status': 'PARTIAL',
                               'test_refs': [],
                               'evidence_refs': ['EV-01'],
                               'gap': 'No executable evidence proves retry idempotency at the provider boundary.'}]}


def test_valid_report_passes(): assert v.validate(valid_report())==[]

def test_no_findings_outcome_passes():
    r=valid_report(); r["findings"]=[]; r["outcome_basis"]["surviving_finding_ids"]=[]; r["outcome_basis"]["reason"]="No material candidate survived review."; r["first_attack_id"]=None; r["review_outcome"]="NO_MATERIAL_FINDINGS"; r["no_material_findings"]=True; r["core_fix"]="No material engineering fix identified in reviewed scope."; assert v.validate(r)==[]

def test_insufficient_requires_blocked_gate():
    r=valid_report(); r["findings"]=[]; r["outcome_basis"]["surviving_finding_ids"]=[]; r["outcome_basis"]["reason"]="Evidence is insufficient for material admission."; r["first_attack_id"]=None; r["review_outcome"]="INSUFFICIENT_EVIDENCE"; r["no_material_findings"]=False; assert any("BLOCKED" in x for x in v.validate(r)); r["quality_gates"]["scope"]="BLOCKED"; assert v.validate(r)==[]

def test_diff_requires_comparison_and_change_surface():
    r=valid_report(); r["mode"]="DIFF"; errs=v.validate(r); assert any("comparison" in x for x in errs) and any("change_surface" in x for x in errs)

def test_diff_change_surface_shape():
    r=valid_report(); r["mode"]="DIFF"; r["comparison"]={"base_ref":"a","head_ref":"b"}; r["change_surface"]={"public_api":[],"schema_data":[],"migrations":[],"configuration":[],"dependencies":[],"rollout":[],"rollback":[],"build_release":[]}; r["change_risk_ledger"]=[{"surface":"provider retry path","invariant_refs":["INV-01"],"risk":"MEDIUM","reason":"Retry behavior changed in the reviewed diff.","verification":{"type":"INTEGRATION_TEST","method":"Run the retry/idempotency integration test.","success_condition":"One durable write and one external charge.","failure_signal":"Duplicate durable write or external charge."}}]; assert v.validate(r)==[]

def test_not_found_requires_absence_proof():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["evidence_state"]="NOT_FOUND"; f["anchor"]={"type":"absence"}; f.pop("falsifier_check"); assert any("absence_proof" in x for x in v.validate(r))

def test_critical_admission_rules():
    r=valid_report(); f=r["findings"][0]; f["severity"]="CRITICAL"; f["reachability"]="STATIC_ONLY"; f["execution_path"]=[]; f["invariant_refs"]=[]; f["surface_refs"]=[]; f["critical_path_ref"]=None; f["evidence_strength"]="WEAK"; f["scope_sensitivity"]="HIGH"; errs=v.validate(r); assert any("PROVEN or PLAUSIBLE" in x for x in errs) and any("execution_path" in x for x in errs) and any("WEAK" in x for x in errs) and any("HIGH scope_sensitivity" in x for x in errs)

def test_critical_requires_known_blast_radius():
    r=valid_report(); f=r["findings"][0]; f["severity"]="CRITICAL"; f["blast_radius_class"]="UNKNOWN"; assert any("blast_radius_class" in x for x in v.validate(r))

def test_unknown_surface_ref_fails():
    r=valid_report(); r["findings"][0]["surface_refs"]=["SURF-404"]; assert any("unknown critical surface" in x for x in v.validate(r))

def test_verification_requires_failure_signal():
    r=valid_report(); r["findings"][0]["verification"].pop("failure_signal"); assert any("failure_signal" in x for x in v.validate(r))

def test_state_transition_shape_required():
    r=valid_report(); r["state_transition_ledger"][0].pop("recovery"); assert any("state_transition_ledger[0].recovery" in x for x in v.validate(r))

def test_verification_gap_must_be_structured():
    r=valid_report(); r["verification_gaps"]=["need runtime logs"]; assert any("verification_gaps[0] must be an object" in x for x in v.validate(r))

def test_personal_attack_fails():
    r=valid_report(); r["findings"][0]["roast_line"]="The developer is a clueless idiot."; assert any("personal attack" in x for x in v.validate(r))

def test_inventory_script_reports_topology(tmp_path):
    (tmp_path/"src").mkdir(); (tmp_path/"tests").mkdir(); (tmp_path/"migrations").mkdir(); (tmp_path/".github/workflows").mkdir(parents=True); (tmp_path/"infra").mkdir(); (tmp_path/"src/auth").mkdir()
    (tmp_path/"package.json").write_text('{"workspaces":["packages/*"]}'); (tmp_path/"package-lock.json").write_text('{}'); (tmp_path/"src/app.ts").write_text("export const x = 1"); (tmp_path/"src/auth/session.ts").write_text("export const auth = true"); (tmp_path/"tests/app.test.ts").write_text("test('x',()=>{})"); (tmp_path/"migrations/001_init.sql").write_text("create table x(id int);"); (tmp_path/".github/workflows/ci.yml").write_text("name: ci"); (tmp_path/"infra/main.tf").write_text('resource "x" "y" {}')
    p=subprocess.run([sys.executable,str(BASE/"scripts"/"inventory_repo.py"),str(tmp_path),"--json"],capture_output=True,text=True,check=True); data=json.loads(p.stdout)
    assert "package.json" in data["key_files"] and "package-lock.json" in data["lock_files"] and "tests/app.test.ts" in data["test_files"] and data["migration_files"]
    assert "infra/main.tf" in data["infrastructure_files"] and "src/auth/session.ts" in data["auth_surface_files"] and any(x["language"]=="TypeScript" for x in data["languages"])

def test_compare_inventory_snapshots_reports_surface_delta():
    mod=load("inventory_compare", BASE/"scripts"/"compare_inventories.py")
    base={"root":"a","file_count":2,"total_bytes":10,"languages":[{"language":"Python","files":1,"bytes":5}],"lock_files":["requirements.lock"],"auth_surface_files":[]}
    head={"root":"b","file_count":3,"total_bytes":20,"languages":[{"language":"Python","files":2,"bytes":15}],"lock_files":["requirements.lock"],"auth_surface_files":["src/auth.py"]}
    out=mod.compare(base,head)
    assert out["file_count_delta"]==1 and out["total_bytes_delta"]==10
    assert out["surface_changes"]["auth_surface_files"]["added"]==["src/auth.py"]
    assert out["language_delta"][0]["files_delta"]==1

def test_anchor_source_id_must_reference_manifest():
    r=valid_report(); r["findings"][0]["anchor"]["source_id"]="SRC-404"; assert any("source_id" in x for x in v.validate(r))

def test_finding_alias_identity_collision_fails():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="RR-002"; second["finding_key"]="second-key"; second["finding_aliases"]=[r["findings"][0]["finding_key"]]; r["findings"].append(second); assert any("identity token" in x for x in v.validate(r))

def test_downgraded_falsifier_requires_higher_initial_severity():
    r=valid_report(); f=r["findings"][0]; f["severity"]="MINOR"; f["falsifier_check"]["result"]="DOWNGRADED"; assert any("downgraded_from" in x for x in v.validate(r)); f["falsifier_check"]["downgraded_from"]="MAJOR"; assert v.validate(r)==[]

def test_findings_must_be_ordered_and_first_attack_is_top_severity():
    r=valid_report(); second=dict(r["findings"][0]); second["id"]="RR-002"; second["finding_key"]="second-minor"; second["finding_aliases"]=[]; second["severity"]="MINOR"; second.pop("falsifier_check",None); second["root_cause_id"]=None; r["findings"]=[second,r["findings"][0]]; r["first_attack_id"]="RR-002"; errs=v.validate(r); assert any("ordered by severity" in x for x in errs) and any("highest-severity" in x for x in errs)


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

def test_v6_review_plan_requires_stop_conditions():
    r=valid_report(); r["review_plan"]["stop_conditions"]=[]; assert any("stop_conditions" in x for x in v.validate(r))

def test_v6_blind_dual_review_requires_separate_completed_pass():
    r=valid_report(); r["assurance"]={"mode":"BLIND_DUAL_REVIEW","independence":"SAME_CONTEXT","second_pass_status":"COMPLETED","disagreement_summary":[],"limitations":[]}; r["findings"][0]["confidence_basis"]["independence"]="SAME_CONTEXT"; assert any("BLIND_DUAL_REVIEW" in x for x in v.validate(r))

def test_v6_unknown_evidence_reference_fails():
    r=valid_report(); r["findings"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_high_confidence_requires_direct_evidence():
    r=valid_report(); r["findings"][0]["confidence"]="high"; r["findings"][0]["confidence_basis"]["directness"]="LOW"; assert any("high confidence" in x for x in v.validate(r))

def test_v6_test_evidence_ledger_must_cover_invariants():
    r=valid_report(); r["test_evidence_ledger"]=[]; assert any("missing invariants" in x for x in v.validate(r))

def test_v6_test_evidence_ledger_rejects_unknown_evidence():
    r=valid_report(); r["test_evidence_ledger"][0]["evidence_refs"]=["EV-404"]; assert any("unknown evidence" in x for x in v.validate(r))

def test_v6_diff_requires_change_risk_ledger():
    r=valid_report(); r["mode"]="DIFF"; r["comparison"]={"base_ref":"a","head_ref":"b"}; r["change_surface"]={"public_api":[],"schema_data":[],"migrations":[],"configuration":[],"dependencies":[],"rollout":[],"rollback":[],"build_release":[]}; assert any("change_risk_ledger" in x for x in v.validate(r))

def test_v6_change_risk_ledger_rejects_unknown_invariant():
    r=valid_report(); r["mode"]="DIFF"; r["comparison"]={"base_ref":"a","head_ref":"b"}; r["change_surface"]={"public_api":[],"schema_data":[],"migrations":[],"configuration":[],"dependencies":[],"rollout":[],"rollback":[],"build_release":[]}; r["change_risk_ledger"]=[{"surface":"auth","invariant_refs":["INV-404"],"risk":"HIGH","reason":"Auth path changed.","verification":{"type":"INTEGRATION_TEST","method":"Run auth integration test.","success_condition":"Unauthorized tenant access remains denied.","failure_signal":"Cross-tenant access succeeds."}}]; assert any("unknown invariant" in x for x in v.validate(r))

def test_v6_residual_risk_requires_closure_dependency():
    r=valid_report(); r["findings"][0]["residual_risk"]["closure_dependency"]=""; assert any("closure_dependency" in x for x in v.validate(r))

def test_v6_assurance_requires_auditable_pass_records():
    r=valid_report(); r["assurance"]["pass_records"]=[]; assert any("pass_records" in x for x in v.validate(r))

def test_v6_outcome_basis_must_match_surviving_findings():
    r=valid_report(); r["outcome_basis"]["surviving_finding_ids"]=[]; assert any("surviving_finding_ids" in x for x in v.validate(r))
