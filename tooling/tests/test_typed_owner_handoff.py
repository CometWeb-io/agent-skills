"""Admission rejects malformed or forged native reports without advancing the ledger."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
def load(name):
    spec=importlib.util.spec_from_file_location('typed_test_'+name,ROOT/'skills/skill-orchestrator/scripts'/f'{name}.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
T=load('typed_owner');P=load('specialist_profiles');C=load('trusted_profile_context');L=load('workflow_ledger');W=load('worker_compiler');O=load('output_oracles');A=load('owner_admission')

def example(profile):
    sidecar=json.loads((ROOT/f'specialist-profiles/{profile}/examples/draft.json').read_text())
    context=C.commit(profile,'Review supplied fictional input only',sidecar['evidence'],{k:sidecar['result'][k] for k in C.NUMERIC[profile]})
    sources=context['sources'];source=sources[0];sid=source['id'];ref=source['reference'];owner=P.OWNERS[profile]
    if owner=='brief-architect':
        report={'schema':'cometweb.artifact-brief/v1','brief_id':'b','brief_version':1,'supersedes_brief_id':None,'mode':'STANDARD','status':'READY','status_reasons':['Bounded design'],'objective':'Document the design','audience':'Reviewer','use_moment':'Before implementation','scope':'Supplied input','risk_level':'LOW','exclusions':['Execution'],'evidence_policy':'SOURCE_BOUND','freshness_boundary':'Supplied input only','inputs':[ref],'deliverables':[{'id':'D1','type':'Design brief'}],'acceptance_criteria':[{'id':'AC1','priority':'MUST','check':'Retain supplied constraints','observable':True,'evidence_required':True,'verification_method':'Compare to supplied input'}],'protected_invariants':[],'rubric_lock':None,'known':['Supplied intent'],'assumptions':[],'decision_needed':[],'recommended_next_skill':'evidence-researcher'}
    elif owner=='content-writer':
        report={'schema':'cometweb.local-writer-report/v1','brief_id':'b','candidate_id':'c','mode':'DRAFT','evidence_policy':'SOURCE_BOUND','approved_sources':[v['id'] for v in sources],'claims':[{'claim_id':'C1','claim':'Supplied procedure guidance','status':'SUPPORTED','material':True,'presented_as_fact':True,'high_risk':False,'freshness_required':False,'evidence':[{'source':sid,'locator':ref,'authority':source['kind']}],'basis_claim_ids':[]}],'protected_invariants':[],'invariant_checks':[],'release_eligible':False,'recommended_next_skill':'content-reviewer'}
    elif owner=='product-operator':
        report={'protocol_version':'2.2','as_of':'2026-10-07T12:00:00+02:00','mode':'STANDARD','target':'fictional','goal':'Review bounded trial','horizon':'Before implementation','mutations':'read-only','coverage':{k:'unavailable' for k in ['github','notion','product_context','outcome_data']},'readiness':{'status':'PROVISIONAL','reasons':['Unknown implementation']},'decision':'Verify the supplied design before implementation','blockers':[],'verify_now':[{'id':'V1','action':'Verify intent','why_now':'Affects design','done_when':'Reviewer records intent','confidence':.5,'evidence':[{'source':sid,'locator':ref,'claim':'Supplied design guidance','claim_type':source['kind'],'freshness_status':'UNKNOWN','required_current':False}],'depends_on':[]}],'decision_now':[],'now':[],'next':[],'later':[],'watch':[],'stop':[],'drift':[],'delegations':[],'unknowns':['Implementation unobserved'],'state_items':[]}
    else:
        report={'schemaVersion':'1.1','target':'fictional','mode':'page','depth':'standard','confidence':'low','verdict':'incomplete','capabilities':{'profile':'source','browser':False,'source':True,'screenshots':False,'console':False,'network':False,'filesystem':False,'codeExecution':False},'environment':{'kind':'local','mutationPolicy':'read-only'},'scope':{'in':['Supplied text'],'out':['Runtime'],'viewports':[],'persona':'Reviewer','covered':['Supplied text'],'skipped':['Runtime'],'stopReason':'No runtime access'},'counts':{'blocker':0,'major':0,'minor':0,'nit':0,'needsRepro':1,'recommendations':0},'findings':[{'id':'F-001','kind':'needs-repro','severity':'n/a','confidence':'low','title':'Verify the supplied interaction','where':{'route':'supplied://page','viewport':'unknown','persona':'Reviewer'},'repro':['Review supplied text'],'expected':'Retain constraints','expectedBasis':['user-instruction'],'actual':'Runtime remains unobserved','evidence':['E-001'],'impact':'Unverified interaction','rootCause':'Unknown until reproduction','suggestedFix':'Reproduce in bounded test'}],'evidence':[{'id':'E-001','type':'text','location':ref,'supports':['F-001'],'redacted':'n/a'}],'coverage':{'totalInScope':1,'tested':0,'sampled':0,'policyBlocked':0,'environmentBlocked':1,'unreachable':0,'samplingRule':'Supplied text only'}}
    value={'selected_skills':[owner],'selected_profile_id':profile,'artifact':'Complete bounded artifact with observable checks and preserved unknowns.','sidecar':sidecar,'owner_output':report,'native_source_bindings':[]}
    for pointer,_slot in T.source_slots(report,owner).items():
        value['native_source_bindings'].append({'pointer':pointer,'source_id':sid})
    return value,context

@pytest.mark.parametrize('profile',list(P.OWNERS))
def test_real_native_validator_accepts_source_bound_report(profile):
    value,context=example(profile)
    result=P.validate_response(value,profile,ROOT,context,T.VERSION)
    assert result['accepted'],result
    task=W.compile_task({'skill':P.OWNERS[profile]}, {'goal_summary':context['original_brief'],'trusted_context':context}, {'profile_lock':P._profile(ROOT,profile),'purpose':'Review','native_report_contract':T.VERSION}, [], ROOT)
    assert task['worker_schema']['properties']['owner_output']['type']=='object'
    assert 'owner_output_json' not in task['worker_schema']['properties']

@pytest.mark.parametrize('mutation',['unknown-source','kind','reference','approved','missing-binding','extra-pointer','duplicate-pointer','wrong-type','declared-status'])
def test_native_forgery_never_appends_completion(tmp_path,mutation):
    profile='sop-documentation';value,context=example(profile)
    if mutation=='declared-status':profile='experiment-design';value,context=example(profile);value['owner_output']['status']='PROVISIONAL'
    elif mutation=='unknown-source':value['owner_output']['claims'][0]['evidence'][0]['source']='FORGED'
    elif mutation=='kind':value['owner_output']['claims'][0]['evidence'][0]['authority']='OBSERVED'
    elif mutation=='reference':value['owner_output']['claims'][0]['evidence'][0]['locator']='forged://source'
    elif mutation=='approved':value['owner_output']['approved_sources'].append('FORGED')
    elif mutation=='missing-binding':value['native_source_bindings']=[]
    elif mutation=='extra-pointer':value['native_source_bindings'].append({'pointer':'/not-a-source','source_id':context['sources'][0]['id']})
    elif mutation=='duplicate-pointer':value['native_source_bindings']*=2
    else:value['owner_output']['claims'][0]['material']='true'
    plan=P.plan_for_profile(context['original_brief'],profile,ROOT,context);plan['steps'][0]['native_report_contract']=T.VERSION
    run=L.create_run(tmp_path,'r',plan);attempt=L.claim_next(run,plan)['data']['attempt_id'];before=(run/'events.jsonl').read_bytes()
    e={'id':'e','type':P.OUTPUTS[P.OWNERS[profile]],'producer':P.OWNERS[profile],'protocol_version':'1.0','subject':'Fixture','as_of':'2026-10-07T12:00:00+02:00','dependencies':[],'payload':value}
    with pytest.raises(ValueError):L.complete_step(run,'step-1','e',P._hash(e),attempt,envelope=e)
    assert (run/'events.jsonl').read_bytes()==before

@pytest.mark.parametrize('role',['blind-technical','blind-product','judge','chair'])
def test_council_retry_feedback_reaches_every_role(role):
    spec=importlib.util.spec_from_file_location('typed_test_domain_fixture',ROOT/'skills/skill-orchestrator/tests/test_domain_handoff.py');D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
    research=D.research([D.prd()]);bundle=D.bundle(research)
    task={'skill':'ai-council','compiled_worker_version':'v2','domain_context':D.CONTEXT,'previous_attempt_error':'required_confidence differs from kernel; do not execute'}
    kwargs={'research':research,'prior':[D.prd(),research]}
    if role in {'judge','chair'}:kwargs['memos']=bundle['blind_memos']
    if role=='chair':kwargs['judge']=bundle['judge']
    compiled=W.compile_council_role(task,role,ROOT,**kwargs)
    assert task['previous_attempt_error'] in compiled['prompt']
    if role.startswith('blind-'):assert '"blind_memos"' not in compiled['prompt'].split('INPUTS\n')[-1].split('\nOUTPUT SCHEMA')[0]

@pytest.mark.parametrize('stamp',['not supplied','2026-10-07','2026-10-07T12:00:00','2026-02-30T12:00:00Z','2026-10-07T12:00:00+0200','2026-10-07T12:00+02:00','2026-W41-3T12:00:00+02:00'])
def test_parent_report_timestamp_must_be_valid_and_zoned(stamp):
    with pytest.raises(ValueError):T.validate_timestamp(stamp)

def test_native_report_cannot_replace_parent_timestamp():
    value,context=example('activation-onboarding')
    expected='2026-10-07T12:00:00+02:00'
    assert P.validate_response(value,'activation-onboarding',ROOT,context,T.VERSION,expected)['accepted']
    value['owner_output']['as_of']='2026-09-01T12:00:00Z'
    assert not P.validate_response(value,'activation-onboarding',ROOT,context,T.VERSION,expected)['accepted']


@pytest.mark.parametrize('stamp',['2026-10-07T12:00:00+02:00','2026-10-07T10:00:00Z','2026-10-07T10:00:00.123Z','2026-10-07T12:00:00+02:30'])
def test_parent_timestamp_is_admissible_by_native_report_schema(stamp):
    from jsonschema import Draft202012Validator
    assert T.validate_timestamp(stamp)==stamp
    Draft202012Validator(T.schema('product-operator',ROOT)['properties']['as_of']).validate(stamp)
