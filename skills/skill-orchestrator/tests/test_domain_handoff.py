"""Real kernels, adversarial bindings and bounded sequential-parent retry."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[3]
def module(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
domain=module('domain_tests','skills/skill-orchestrator/scripts/domain_handoff.py')
gate=module('domain_gate_tests','skills/skill-orchestrator/scripts/prd_handoff.py')
ledger=module('domain_ledger_tests','skills/skill-orchestrator/scripts/workflow_ledger.py')
planner=module('domain_planner_tests','skills/skill-orchestrator/scripts/orchestrate_kernel.py')
CONTEXT={'question':'Should we review a fictional reversible local trial?', 'context':{'risk_level':'low','reversibility':'reversible','financial_impact':0,'strategic_impact':0,'risk_surfaces':['technical']},'mode':'LIGHT','decision_value':.1,'max_attempts':2}
def graph():return json.loads((Path(__file__).parent/'fixtures/domain-partial-graph.json').read_text())
def prd():return json.loads((Path(__file__).parent/'fixtures/prd-ready-envelope.json').read_text())
def wrap(payload,producer,id,prior):
    v=prd();v.update(payload=payload,producer=producer,id=id,type='EvidenceEnvelope' if producer=='evidence-researcher' else 'DecisionHandoff',dependencies=[e['id'] for e in prior]);return v
def research(prior):return wrap(domain.research_payload(graph(),prior),'evidence-researcher','research-test',prior)
def bundle(r):
    props=json.loads((ROOT/'skills/skill-orchestrator/references/domain-proposal.schema.json').read_text())['properties']
    proposal={k:False if v.get('type')=='boolean' else .9 if v.get('type')=='number' else [] if v.get('type')=='array' else 'Declared local trial' for k,v in props.items()}
    proposal.update(verdict='TEST',required_confidence=domain._council().required_confidence(domain._council().compile_decision_contract(CONTEXT['question'],CONTEXT['context']),0,CONTEXT['decision_value']),critical_gap='Implementation unobserved',freshness_status='UNKNOWN',controls_implemented=False,reversible_experiment_available=True,independence_grade='I1',memory_written=False)
    exp=props['experiment']['properties'];proposal['experiment']={k:[] if v.get('type')=='array' else None if 'anyOf' in v else 'Unknown, review before action' for k,v in exp.items()}
    memo=lambda role:dict(role_id=role,vote='DEFER',confidence=.5,claim_ids=[],assumptions=[],risks=['Missing implementation evidence'],falsifier='Observe failed trial',minority='No launch evidence')
    return dict(research_envelope=r,blind_memos=[memo('technical'),memo('product_customer')],judge=dict(accepted_claim_ids=[],rejected_claim_ids=[c['claim_id'] for c in r['payload']['evidence_graph']['claims']],critical_gaps=['Implementation unobserved'],freshness_status='UNKNOWN',gate_statuses={'technical':'CLEAR_WITH_CONTROLS'},controls_implemented=False,red_team=['Cannot launch'],falsifier='Observe failed trial',minority_preserved='No launch evidence'),proposal=proposal)
def plan():return gate.attach(planner.plan_workflow('evidence then council').to_dict(),with_domain_gates=True,domain_context=CONTEXT)
def checkpoint(run,step,e,p):
    task=ledger.claim_next(run,p);return ledger.complete_step(run,step,e['id'],domain.digest(e),task['data']['attempt_id'],envelope=e)
def test_real_partial_graph_is_admissible_only_for_gap_discussion():
    r=research([prd()]);b=bundle(r);out=domain.finalize_council(b,CONTEXT,[prd(),r]);assert out['verdict']=='DEFER';assert out['decision_bundle']['proposal']==b['proposal'];assert out['constraint_result']['execution_authorized'] is False;assert domain.validate(out,'ai-council',CONTEXT)['accepted']
@pytest.mark.parametrize('change',['hash','status','projection','extra','unknown-edge','false-ready'])
def test_research_rejects_producer_forgery(change):
    r=research([prd()])['payload']
    if change=='hash':r['evidence_pack_hash']='sha256:'+'0'*64
    elif change=='status':r['evidence_graph']['research_status']='READY'
    elif change=='projection':r['material_claims'][0]['text']='Invented observation'
    elif change=='extra':r['evidence_graph']['trust_me']=True
    elif change=='unknown-edge':r['evidence_graph']['evidence'][0]['source_id']='absent'
    else:r['evidence_graph']['claims'][0]['status']='VERIFIED'
    with pytest.raises((ValueError,KeyError)):domain.validate_research(r)
@pytest.mark.parametrize('change',['verdict','threshold','judge-admission','judge-state','unknown-memo','same-role','memory','wrong-research','unknown-freshness'])
def test_council_rejects_false_positive_and_role_corruption(change):
    r=research([prd()]);b=bundle(r);out=domain.finalize_council(b,CONTEXT,[prd(),r])
    if change=='verdict':out['verdict']='GO'
    elif change=='threshold':out['decision_bundle']['proposal']['required_confidence']=0
    elif change=='judge-admission':out['decision_bundle']['judge']['accepted_claim_ids']=['absent']
    elif change=='judge-state':out['decision_bundle']['proposal']['controls_implemented']=True
    elif change=='unknown-memo':out['decision_bundle']['blind_memos'][0]['claim_ids']=['absent']
    elif change=='same-role':out['decision_bundle']['blind_memos'][1]['role_id']='technical'
    elif change=='memory':out['decision_bundle']['proposal']['memory_written']=True
    elif change=='wrong-research':out['decision_bundle']['research_envelope']['producer']='brief-architect'
    else:out['decision_bundle']['judge']['freshness_status']='Prose that conceals missing evidence'
    with pytest.raises((ValueError,KeyError)):domain.validate(out,'ai-council',CONTEXT)
@pytest.mark.parametrize('attempts',[0,4,True,'2',None])
def test_retry_budget_is_typed_and_bounded(attempts):
    with pytest.raises(ValueError):domain.validate_context({**CONTEXT,'max_attempts':attempts})
def test_full_local_checkpoint_resume_and_duplicate_after_downstream(tmp_path):
    p=plan();run=ledger.create_run(tmp_path,'domain',p);a=prd();checkpoint(run,'step-1',a,p);r=research([a]);checkpoint(run,'step-2',r,p);d=wrap(domain.finalize_council(bundle(r),CONTEXT,[a,r]),'ai-council','decision',[a,r]);checkpoint(run,'step-3',d,p);assert ledger.replay(run)['status']=='COMPLETED'
    before=(run/'events.jsonl').read_bytes();ledger.complete_step(run,'step-2',r['id'],domain.digest(r),None,envelope=r);assert (run/'events.jsonl').read_bytes()==before
    assert ledger.replay(run)['steps']['step-2']['attempt_number']==1
@pytest.mark.parametrize('change',['dependencies','binding-hash','binding-order','substitute-research'])
def test_bad_binding_never_checkpoints_and_preserves_active_attempt(tmp_path,change):
    p=plan();run=ledger.create_run(tmp_path,'domain',p);a=prd();checkpoint(run,'step-1',a,p);r=research([a]);checkpoint(run,'step-2',r,p);d=wrap(domain.finalize_council(bundle(r),CONTEXT,[a,r]),'ai-council','decision',[a,r]);task=ledger.claim_next(run,p)
    if change=='dependencies':d['dependencies'].reverse()
    elif change=='binding-hash':d['payload']['upstream_bindings'][0]['envelope_hash']='sha256:'+'0'*64
    elif change=='binding-order':d['payload']['upstream_bindings'].reverse()
    else:d['payload']['decision_bundle']['research_envelope']['subject']='Substituted checkpoint'
    before=(run/'events.jsonl').read_bytes()
    with pytest.raises(ValueError):ledger.complete_step(run,'step-3',d['id'],domain.digest(d),task['data']['attempt_id'],envelope=d)
    assert before==(run/'events.jsonl').read_bytes();assert ledger.replay(run)['steps']['step-3']['status']=='RUNNING'
def test_exhausted_retry_is_durable_and_no_third_attempt(tmp_path):
    p=plan();run=ledger.create_run(tmp_path,'domain',p);first=ledger.claim_next(run,p);ledger.fail_step(run,'step-1','first failed',first['data']['attempt_id']);second=ledger.claim_next(run,p);assert second['data']['attempt_number']==2;assert first['data']['attempt_id']!=second['data']['attempt_id'];ledger.fail_step(run,'step-1','second failed',second['data']['attempt_id']);state=ledger.claim_next(run,p);assert state['steps']['step-1']['status']=='BLOCKED';assert state['steps']['step-1']['attempt_number']==2
    with pytest.raises(ValueError,match='blocked'):ledger.claim_next(run,p)

@pytest.mark.parametrize('value',[True,-.1,1.1,'0.1',None,float('nan'),float('inf')])
def test_decision_value_must_be_finite_typed_scope(value):
    with pytest.raises(ValueError):domain.validate_context({**CONTEXT,'decision_value':value})
def test_ready_material_graph_can_clear_and_supporting_claim_does_not_inflate():
    g=json.loads((Path(__file__).parent/'fixtures/domain-ready-graph.json').read_text())
    r=wrap(domain.research_payload(g,[prd()]),'evidence-researcher','ready',[prd()]);b=bundle(r);ids=[c['claim_id'] for c in g['claims']];b['judge'].update(accepted_claim_ids=ids,rejected_claim_ids=[],critical_gaps=[],freshness_status='CLEAR',gate_statuses={'technical':'CLEAR'},controls_implemented=True);b['proposal'].update(verdict='GO',confidence=1.,required_confidence=domain._council().required_confidence(domain._council().compile_decision_contract(CONTEXT['question'],CONTEXT['context']),1,CONTEXT['decision_value']),critical_gap=None,freshness_status='CLEAR',controls_implemented=True)
    assert domain.finalize_council(b,CONTEXT,[prd(),r])['verdict']=='GO'
    b['judge']['accepted_claim_ids']=[];b['proposal']['required_confidence']=domain._council().required_confidence(domain._council().compile_decision_contract(CONTEXT['question'],CONTEXT['context']),0,CONTEXT['decision_value']);out=domain.finalize_council(b,CONTEXT,[prd(),r]);assert out['verdict']=='DEFER';assert out['constraint_result']['evidence_coverage']==0

def test_supporting_admission_cannot_replace_material_evidence():
    g=json.loads((Path(__file__).parent/'fixtures/domain-ready-graph.json').read_text())
    c=copy.deepcopy(g['claims'][0]);c.update(claim_id='clm_supporting',materiality='supporting');g['claims'].append(c)
    e=copy.deepcopy(g['evidence'][0]);e.update(evidence_id='ev_supporting',claim_id='clm_supporting');g['evidence'].append(e)
    s=copy.deepcopy(g['searches'][0]);s.update(search_id='srch_supporting',claim_id='clm_supporting');g['searches'].append(s)
    r=wrap(domain.research_payload(g,[prd()]),'evidence-researcher','support-only-admission',[prd()]);b=bundle(r)
    b['judge'].update(accepted_claim_ids=['clm_supporting'],rejected_claim_ids=[g['claims'][0]['claim_id']],critical_gaps=[],freshness_status='CLEAR',gate_statuses={'technical':'CLEAR'},controls_implemented=True)
    b['proposal'].update(verdict='GO',confidence=1.,required_confidence=domain._council().required_confidence(domain._council().compile_decision_contract(CONTEXT['question'],CONTEXT['context']),0,CONTEXT['decision_value']),critical_gap=None,freshness_status='CLEAR',controls_implemented=True)
    # Supporting claims are absent from the kernel's material-ready admission set.
    with pytest.raises(ValueError,match='Judge admitted unsupported'):
        domain.finalize_council(b,CONTEXT,[prd(),r])


def test_research_parent_timestamp_is_bound_independently_of_schema():
    payload = research([prd()])["payload"]
    stamp = payload["evidence_graph"]["research_contract"]["as_of"]
    assert domain.validate(payload,"evidence-researcher",CONTEXT,expected_report_as_of=stamp)["accepted"]
    with pytest.raises(ValueError,match="differs from parent"):
        domain.validate(payload,"evidence-researcher",CONTEXT,expected_report_as_of="2026-10-08T10:00:00Z")

def test_retry_status_error_contains_kernel_status_without_repairing_payload():
    g = graph(); expected = domain.audit_graph(g)["research_status"]
    g["research_status"] = "READY" if expected != "READY" else "PARTIAL"
    original = copy.deepcopy(g)
    with pytest.raises(ValueError,match="expected=" + expected): domain.audit_graph(g)
    assert g == original
