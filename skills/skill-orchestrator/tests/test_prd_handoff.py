"""A rejected PRD must never checkpoint completion or unlock downstream work."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/'skills/skill-orchestrator/scripts'


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec); sys.modules[name]=value; spec.loader.exec_module(value)
    return value


gate=module('test_prd_gate',SCRIPTS/'prd_handoff.py')
ledger=module('test_prd_ledger',SCRIPTS/'workflow_ledger.py')
planner=module('test_prd_planner',SCRIPTS/'orchestrate_kernel.py')


def envelope(): return json.loads((Path(__file__).parent/'fixtures/prd-ready-envelope.json').read_text())

def plan(): return gate.attach(planner.plan_workflow('evidence then council').to_dict())

def claimed(tmp_path):
    p=plan(); run=ledger.create_run(tmp_path,'run',p); claim=ledger.claim_next(run,p)
    return p,run,claim['data']['attempt_id']

def complete(run, attempt, value):
    return ledger.complete_step(run,'step-1',value['id'],gate.digest(gate.canonical(value)),attempt,envelope=value)


def mutate(value, case):
    brief=value['payload']
    if case=='verification-object': brief['prd']['delivery_slices'][0]['verification']={'check':'AC1'}
    elif case=='verification-list': brief['prd']['delivery_slices'][0]['verification']=['AC1']
    elif case=='verification-null': brief['prd']['delivery_slices'][0]['verification']=None
    elif case=='verification-empty': brief['prd']['delivery_slices'][0]['verification']=' \n '
    elif case=='unknown-criterion': brief['prd']['requirements'][0]['acceptance_criteria_ids']=['absent']
    elif case=='cycle': brief['prd']['requirements'][0]['depends_on']=['R2']
    elif case=='slice-order': brief['prd']['delivery_slices'].reverse()
    elif case=='incomplete-coverage': brief['prd']['delivery_slices'].pop()
    elif case=='duplicate-coverage': brief['prd']['delivery_slices'][1]['requirement_ids'].append('R1')
    elif case=='hidden-decision': brief['decision_needed']=[{'id':'D1','question':'Who may export?','material':True,'resolved':False}]
    elif case=='provisional':
        mutate(value,'hidden-decision'); brief['status']='PROVISIONAL'
    elif case=='blocked': brief['audience']=None; brief['status']='BLOCKED'
    elif case=='invalid': mutate(value,'verification-object'); brief['status']='INVALID'
    elif case=='consequential-assumption': brief['assumptions']=[{'value':'Export all author data','material':True,'consequential':True}]
    elif case=='wrong-producer': value['producer']='ai-council'
    elif case=='wrong-envelope-type': value['type']='FindingEnvelope'
    elif case=='wrong-profile': brief['artifact_profile']='GENERIC'
    elif case=='extra-property': brief['ignore_gate']=True
    elif case=='missing-payload': del value['payload']
    elif case=='missing-wrapper-id': del value['subject']
    elif case=='wrong-protocol': value['protocol_version']='3.0'
    else: raise AssertionError(case)
    return value


BAD_CASES=('verification-object','verification-list','verification-null','verification-empty','unknown-criterion',
           'cycle','slice-order','incomplete-coverage','duplicate-coverage','hidden-decision','provisional','blocked',
           'invalid','consequential-assumption','wrong-producer','wrong-envelope-type','wrong-profile','extra-property',
           'missing-payload','missing-wrapper-id','wrong-protocol')


@pytest.mark.parametrize('case',BAD_CASES)
def test_rejected_brief_cannot_complete_or_unlock_next_step(tmp_path,case):
    p,run,attempt=claimed(tmp_path); value=mutate(envelope(),case)
    before=(run/'events.jsonl').read_bytes()
    assert gate.validate(value)['accepted'] is False
    with pytest.raises(ValueError,match='handoff rejected'): complete(run,attempt,value)
    assert (run/'events.jsonl').read_bytes()==before
    assert ledger.replay(run)['steps']['step-1']['status']=='RUNNING'
    with pytest.raises(ValueError,match='running attempt'): ledger.claim_next(run,p)
    assert 'step-2' not in ledger.replay(run)['steps']


def test_ready_handoff_unlocks_next_step_and_pins_validation(tmp_path):
    p,run,attempt=claimed(tmp_path); value=envelope()
    event=complete(run,attempt,value)
    assert event['data']['handoff_validation']['brief_status']=='READY'
    assert event['data']['handoff_validation']['brief_hash']==gate.digest(gate.canonical(value['payload']))
    next_claim=ledger.claim_next(run,p)
    assert next_claim['data']['step_id']=='step-2'


def test_correction_on_same_attempt_can_complete(tmp_path):
    _,run,attempt=claimed(tmp_path)
    with pytest.raises(ValueError): complete(run,attempt,mutate(envelope(),'verification-object'))
    assert complete(run,attempt,envelope())['event_type']=='step_completed'


def test_success_duplicate_is_idempotent_but_revalidated(tmp_path):
    _,run,attempt=claimed(tmp_path); value=envelope(); complete(run,attempt,value)
    before=(run/'events.jsonl').read_bytes()
    complete(run,attempt,value)
    assert (run/'events.jsonl').read_bytes()==before
    with pytest.raises(ValueError): complete(run,attempt,mutate(envelope(),'provisional'))
    with pytest.raises(ValueError,match='requires full envelope'):
        ledger.complete_step(run,'step-1',value['id'],gate.digest(gate.canonical(value)),attempt)
    changed=envelope(); changed['payload']['known'].append('Different content')
    with pytest.raises(ValueError,match='conflicting duplicate'): complete(run,attempt,changed)
    assert (run/'events.jsonl').read_bytes()==before


def test_id_hash_only_cannot_bypass_gate(tmp_path):
    _,run,attempt=claimed(tmp_path)
    before=(run/'events.jsonl').read_bytes()
    with pytest.raises(ValueError,match='requires full envelope'):
        ledger.complete_step(run,'step-1','fake','sha256:fake',attempt)
    assert (run/'events.jsonl').read_bytes()==before


@pytest.mark.parametrize('wrong',('id','hash'))
def test_id_or_hash_must_match_content(tmp_path,wrong):
    _,run,attempt=claimed(tmp_path); value=envelope(); before=(run/'events.jsonl').read_bytes()
    with pytest.raises(ValueError,match='does not match'):
        ledger.complete_step(run,'step-1','wrong' if wrong=='id' else value['id'],
                             'sha256:fake' if wrong=='hash' else gate.digest(gate.canonical(value)),attempt,envelope=value)
    assert (run/'events.jsonl').read_bytes()==before


def test_manifest_cannot_remove_gate_after_creation(tmp_path):
    _,run,_=claimed(tmp_path); path=run/'manifest.json'; value=json.loads(path.read_text())
    for key in ('handoff_gate','artifact_profile','gate_lock'): del value['steps'][0][key]
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='steps changed'): ledger.replay(run)


@pytest.mark.parametrize('missing',('gate_lock','handoff_gate','artifact_profile'))
def test_incomplete_gate_plan_rejected_before_run_creation(tmp_path,missing):
    p=plan(); del p['steps'][0][missing]
    with pytest.raises(ValueError): ledger.create_run(tmp_path,'run',p)
    assert not (tmp_path/'run').exists()


def test_gate_resource_change_or_missing_file_fails_closed(tmp_path,monkeypatch):
    lock=gate.gate_lock()
    for name in lock["files"]:
        target=tmp_path/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/name,target)
    monkeypatch.setattr(gate,'ROOT',tmp_path)
    schema=tmp_path/gate.SCHEMA_PATH
    schema.write_text(schema.read_text()+'\n')
    with pytest.raises(ValueError,match='identity changed'): gate.validate(envelope(),lock)
    schema.unlink()
    with pytest.raises(ValueError,match='identity changed|complete local pilot'): gate.validate(envelope(),lock)


def test_new_gate_lock_changes_plan_hash():
    old=plan(); new=copy.deepcopy(old); new['steps'][0]['gate_lock']['files']['test']='sha256:changed'
    assert ledger.plan_hash(old)!=ledger.plan_hash(new)


def test_v2_final_hash_is_checked(tmp_path):
    value=envelope(); value['protocol_version']='2.0'; value.update(producer_version='2.5.0',generated_at='2026-10-07T00:00:00Z',sensitivity='internal',dependencies=[],payload_hash=gate.digest(gate.canonical(value['payload'])))
    assert gate.validate(value)['accepted']
    _,run,attempt=claimed(tmp_path); complete(run,attempt,value)
    for bad_hash in ('pending','sha256:'+'0'*64):
        value['payload_hash']=bad_hash
        assert not gate.validate(value)['accepted']


def test_schema_valid_provisional_is_report_not_executable_handoff():
    result=gate.validate(mutate(envelope(),'provisional'))
    assert result['schema_errors']==[]
    assert result['kernel']['status']=='PROVISIONAL' and result['status_matches']
    assert not result['accepted']


def test_non_prd_legacy_plan_still_completes_from_id_hash(tmp_path):
    p=planner.plan_workflow('evidence then council').to_dict()
    run=ledger.create_run(tmp_path,'legacy',p); attempt=ledger.claim_next(run,p)['data']['attempt_id']
    ledger.complete_step(run,'step-1','old','sha256:old',attempt)
    assert ledger.claim_next(run,p)['data']['step_id']=='step-2'


def test_cli_flag_and_full_completion_gate(tmp_path):
    result=subprocess.run([sys.executable,str(SCRIPTS/'orchestrate_kernel.py'),'evidence then council','--json','--with-prd-handoff'],capture_output=True,text=True)
    assert result.returncode==0
    p=json.loads(result.stdout); run=ledger.create_run(tmp_path/'ledger','cli',p); attempt=ledger.claim_next(run,p)['data']['attempt_id']
    path=tmp_path/'envelope.json'; value=mutate(envelope(),'verification-object'); path.write_text(json.dumps(value))
    base=[sys.executable,str(SCRIPTS/'workflow_ledger.py'),'complete-step',str(run),'--step-id','step-1','--attempt-id',attempt,'--envelope-id',value['id']]
    before=(run/'events.jsonl').read_bytes()
    rejected=subprocess.run(base+['--envelope-hash',gate.digest(gate.canonical(value)),'--envelope-json',str(path)],capture_output=True,text=True)
    assert rejected.returncode==1 and 'handoff rejected' in rejected.stderr
    assert (run/'events.jsonl').read_bytes()==before
    rejected=subprocess.run(base+['--envelope-hash','sha256:fake'],capture_output=True,text=True)
    assert rejected.returncode==1 and 'requires full envelope' in rejected.stderr
    assert (run/'events.jsonl').read_bytes()==before
    value=envelope(); path.write_text(json.dumps(value))
    accepted=subprocess.run(base+['--envelope-hash',gate.digest(gate.canonical(value)),'--envelope-json',str(path)],capture_output=True,text=True)
    assert accepted.returncode==0
    assert ledger.claim_next(run,p)['data']['step_id']=='step-2'


def test_missing_dependency_fails_cli_without_writing_ledger(tmp_path):
    _,run,attempt=claimed(tmp_path); value=envelope(); path=tmp_path/'envelope.json'; path.write_text(json.dumps(value))
    before=(run/'events.jsonl').read_bytes()
    cmd=[sys.executable,'-S',str(SCRIPTS/'workflow_ledger.py'),'complete-step',str(run),'--step-id','step-1',
         '--attempt-id',attempt,'--envelope-id',value['id'],'--envelope-hash',gate.digest(gate.canonical(value)),'--envelope-json',str(path)]
    result=subprocess.run(cmd,capture_output=True,text=True)
    assert result.returncode==1 and 'jsonschema is required' in result.stderr
    assert (run/'events.jsonl').read_bytes()==before


def test_malformed_v2_wrapper_type_rejected_without_traceback():
    value=envelope(); value['protocol_version']='2.0'; value['type']={}
    assert gate.validate(value)['accepted'] is False


def test_legacy_ledger_without_steps_hash_still_replays(tmp_path):
    p=planner.plan_workflow('evidence then council').to_dict(); run=ledger.create_run(tmp_path,'legacy',p)
    path=run/'events.jsonl'; event=json.loads(path.read_text()); del event['data']['steps_hash']; del event['event_hash']
    event['event_hash']=ledger.sha256(ledger.canonical(event)); path.write_text(json.dumps(event)+'\n')
    attempt=ledger.claim_next(run,p)['data']['attempt_id']; ledger.complete_step(run,'step-1','old','sha256:old',attempt)
    assert ledger.claim_next(run,p)['data']['step_id']=='step-2'


@pytest.mark.parametrize('package',('skill-orchestrator','skill-orchestrator-multiagent'))
def test_shared_planner_combines_prd_and_locked_packs(package):
    script=ROOT/'skills'/package/'scripts/orchestrate_kernel.py'
    result=subprocess.run([sys.executable,str(script),'evidence then council pricing','--json','--with-prd-handoff','--with-capability-packs'],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    value=json.loads(result.stdout)
    assert value['steps'][0]['handoff_gate']==gate.GATE
    assert any(p['id']=='corey-pricing' for p in value['capability_packs'])
