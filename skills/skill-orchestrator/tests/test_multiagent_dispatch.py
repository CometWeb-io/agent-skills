"""Actual task dispatch stays sequential and bound to validated checkpoints."""
from pathlib import Path
import importlib.util,json,subprocess,sys
import pytest
ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/'skills/skill-orchestrator/scripts'
BUILDER=ROOT/'skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path); value=importlib.util.module_from_spec(spec); sys.modules[name]=value; spec.loader.exec_module(value); return value
ledger=module('dispatch_test_ledger',SCRIPTS/'workflow_ledger.py')
gate=module('dispatch_test_gate',SCRIPTS/'prd_handoff.py')

def cli(args):
    r=subprocess.run([sys.executable,str(BUILDER),*map(str,args)],capture_output=True,text=True)
    return r,json.loads(r.stdout) if r.returncode==0 else None

def envs():
    first=json.loads((Path(__file__).parent/'fixtures/prd-ready-envelope.json').read_text())
    def wrap(kind,producer,id,payload): return {'id':id,'type':kind,'producer':producer,'protocol_version':'1.0','subject':'synthetic dispatch','as_of':'2026-10-07','payload':payload}
    research=wrap('EvidenceEnvelope','evidence-researcher','evidence-test',{'research_contract':'Synthetic local test only','material_claims':[{'claim_id':'C1','text':'Fixture supplies a local SQLite requirement.','epistemic_kind':'FACT','status':'VERIFIED_IN_FIXTURE'}],'evidence_pack_hash':'synthetic-fixture','gaps':['No real implementation or demand evidence'],'contradictions':[]})
    council=wrap('DecisionHandoff','ai-council','decision-test',{'verdict':'TEST','blockers':[],'controls':['No deployment or real data'],'reason':'Synthetic limited trial, not a business outcome'})
    return [first,research,council]

def setup(tmp):
    r,v=cli(['evidence then council','--json','--with-prd-handoff']); assert r.returncode==0,r.stderr
    plan=v['plan']; file=tmp/'plan.json'; file.write_text(json.dumps(plan)); run=ledger.create_run(tmp/'ledger','run',plan)
    return plan,file,run,v

def dispatch(file,run,tmp,prior):
    f=tmp/'prior.json'; f.write_text(json.dumps(prior)); return cli(['--json','--run-dir',run,'--plan-json',file,'--prior-envelopes-json',f])

def finish(run,task,envelope):
    return ledger.complete_step(run,task['step_id'],envelope['id'],gate.digest(gate.canonical(envelope)),task['attempt_id'],envelope=envelope)

def test_preview_exposes_only_brief_and_pins_local_skill_paths(tmp_path):
    _,_,_,v=setup(tmp_path)
    assert [t['skill'] for t in v['subagent_tasks']]==['brief-architect']
    assert v['dispatch_status']=='PLAN_ONLY'
    assert str(ROOT/'skills/brief-architect/SKILL.md') in v['subagent_tasks'][0]['prompt']
    assert '~/.cursor/skills' not in v['subagent_tasks'][0]['prompt']
    assert v['deferred_step_ids']==['step-2','step-3']

def test_complete_three_step_chain_and_resume_without_replaying_completed_steps(tmp_path):
    _,file,run,_=setup(tmp_path); prior=[]
    for expected,envelope in zip(('brief-architect','evidence-researcher','ai-council'),envs(),strict=True):
        r,v=dispatch(file,run,tmp_path,prior); assert r.returncode==0,r.stderr
        task=v['subagent_tasks'][0]; assert task['skill']==expected
        assert task['prior_envelope_ids']==[e['id'] for e in prior]
        finish(run,task,envelope); prior.append(envelope)
    r,v=dispatch(file,run,tmp_path,prior); assert r.returncode==0
    assert v['dispatch_status']=='COMPLETED' and v['subagent_tasks']==[]
    assert ledger.replay(run)['status']=='COMPLETED'

@pytest.mark.parametrize('problem',('missing','tampered','reordered','duplicate'))
def test_bad_prior_prefix_cannot_claim_or_release_next_step(tmp_path,problem):
    _,file,run,_=setup(tmp_path); envelopes=envs()
    r,v=dispatch(file,run,tmp_path,[]); finish(run,v['subagent_tasks'][0],envelopes[0])
    prior=[envelopes[0]]
    if problem=='missing': prior=[]
    elif problem=='tampered': prior[0]['payload']['known'].append('altered after checkpoint')
    elif problem=='reordered': prior=[envelopes[1]]
    else: prior*=2
    before=(run/'events.jsonl').read_bytes(); r,v=dispatch(file,run,tmp_path,prior)
    assert r.returncode==1 and v is None
    assert (run/'events.jsonl').read_bytes()==before

@pytest.mark.parametrize('stage',('prd','research','council'))
def test_rejected_input_failure_retry_and_resume(stage,tmp_path):
    _,file,run,_=setup(tmp_path); prior=[]
    for envelope in envs():
        r,v=dispatch(file,run,tmp_path,prior); assert r.returncode==0,r.stderr
        task=v['subagent_tasks'][0]
        if task['skill']=={'prd':'brief-architect','research':'evidence-researcher','council':'ai-council'}[stage]:
            bad=json.loads(json.dumps(envelope))
            if stage=='prd': bad['payload']['prd']['delivery_slices'][0]['verification']={}
            elif stage=='research': del bad['payload']['research_contract']
            else: bad['payload'].update(verdict='GO',blockers=['binding block'])
            before=(run/'events.jsonl').read_bytes()
            with pytest.raises(ValueError): finish(run,task,bad)
            assert (run/'events.jsonl').read_bytes()==before
            r,_=dispatch(file,run,tmp_path,prior); assert r.returncode==1
            ledger.fail_step(run,task['step_id'],'explicitly closed rejected attempt',task['attempt_id'])
            r,v=dispatch(file,run,tmp_path,prior); assert r.returncode==0,r.stderr
            retry=v['subagent_tasks'][0]; assert retry['skill']==task['skill'] and retry['attempt_id']!=task['attempt_id']
            assert ledger.replay(run)['steps'][retry['step_id']]['attempt_number']==2
            task=retry
        finish(run,task,envelope); prior.append(envelope)
    assert ledger.replay(run)['status']=='COMPLETED'

def test_stale_plan_returns_no_dispatch(tmp_path):
    plan,file,run,_=setup(tmp_path); plan['goal_summary']+=' changed'; file.write_text(json.dumps(plan))
    r,v=dispatch(file,run,tmp_path,[])
    assert r.returncode==0 and v['dispatch_status']=='STALE_PLAN' and v['subagent_tasks']==[]

def test_live_running_attempt_is_not_duplicated_after_parent_restart(tmp_path):
    _,file,run,_=setup(tmp_path); r,v=dispatch(file,run,tmp_path,[]); assert r.returncode==0
    before=(run/'events.jsonl').read_bytes(); r,_=dispatch(file,run,tmp_path,[])
    assert r.returncode==1 and (run/'events.jsonl').read_bytes()==before


def test_opt_in_packs_reach_only_council_task():
    builder=module('dispatch_pack_builder',BUILDER)
    plan=builder.build_multiagent_plan('customer research evidence then council pricing offers',with_prd_handoff=True,with_capability_packs=True)['plan']
    assert plan['capability_packs']
    for index in (0,1):
        task=builder._task(plan,index,[],None,gated=True)
        assert 'capability_packs' not in task
    task=builder._task(plan,2,[],None,gated=True)
    assert task['capability_packs']==plan['capability_packs']
    assert 'FRAMEWORK only' in task['prompt']
