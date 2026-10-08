"""Admission of profile carriers through actual generator, wrapper and durable ledger."""
import copy,importlib.util,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
 spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
profiles=load('profile_gate_v2','skills/skill-orchestrator/scripts/specialist_profiles.py')
ledger=load('profile_ledger_v2','skills/skill-orchestrator/scripts/workflow_ledger.py')
BUILDER=ROOT/'skills/skill-orchestrator-multiagent/scripts/orchestrate_multiagent_kernel.py'
IDS=tuple(profiles.OWNERS)
def response(pid):return {'selected_skills':[profiles.OWNERS[pid]],'selected_profile_id':pid,'artifact':'Complete owner artifact: supplied findings, bounded hypothesis and observable follow-up test; procedure verification and expected result are included here.','sidecar':json.loads((ROOT/f'specialist-profiles/{pid}/examples/draft.json').read_text())}
def envelope(pid):return {'id':'profile-demo','type':profiles.OUTPUTS[profiles.OWNERS[pid]],'producer':profiles.OWNERS[pid],'protocol_version':'1.0','subject':'Fictional profile test','as_of':'2026-10-07T12:00:00+02:00','dependencies':[],'payload':response(pid)}
def setup(tmp_path,pid):
 p=profiles.plan_for_profile('Prepare fictional local artifact',pid);run=ledger.create_run(tmp_path,'run',p);e=ledger.claim_next(run,p);return p,run,e['data']['attempt_id']
def complete(run,pid,attempt,value=None):
 v=value or envelope(pid);return ledger.complete_step(run,'step-1',v['id'],profiles._hash(v),attempt,envelope=v)
@pytest.mark.parametrize('pid',IDS)
def test_standalone_profile_entrypoint_and_complete_response(pid):
 entry=profiles._profile(ROOT,pid)['entrypoint'];assert entry.endswith('PROFILE.md');assert not (ROOT/f'specialist-profiles/{pid}/SKILL.md').exists();assert profiles.validate_response(response(pid),pid)['accepted']
@pytest.mark.parametrize('pid',IDS)
def test_profile_completes_with_proof_and_duplicate_is_idempotent(tmp_path,pid):
 p,run,a=setup(tmp_path,pid);e=complete(run,pid,a);assert e['data']['handoff_validation']['profile_accepted'];assert ledger.replay(run)['status']=='COMPLETED';before=(run/'events.jsonl').read_bytes();complete(run,pid,a);assert before==(run/'events.jsonl').read_bytes()
@pytest.mark.parametrize('change',['profile-as-skill','profile-only','wrong-profile','blank-artifact','delegate-essential','unknown-source','bad-type','wrong-producer','extra-field','authorization'])
def test_invalid_owner_response_never_appends_completion(tmp_path,change):
 pid='conversion-audit';p,run,a=setup(tmp_path,pid);v=envelope(pid);q=v['payload']
 if change=='profile-as-skill':q['selected_skills'].append(pid)
 elif change=='profile-only':q['selected_skills']=[pid]
 elif change=='wrong-profile':q['selected_profile_id']='activation-onboarding'
 elif change=='blank-artifact':q['artifact']='  '
 elif change=='delegate-essential':q['artifact']='Hypotheses and the follow-up test are in the sidecar.'
 elif change=='unknown-source':q['sidecar']['result']['hypotheses'][0]['source_ids']=['absent']
 elif change=='bad-type':q['sidecar']['result']['observations'][0]['verification']={}
 elif change=='wrong-producer':v['producer']='ai-council'
 elif change=='extra-field':q['execute_now']=True
 else:q['sidecar']['execution_authorized']=True
 before=(run/'events.jsonl').read_bytes()
 with pytest.raises(ValueError):complete(run,pid,a,v)
 assert before==(run/'events.jsonl').read_bytes();assert ledger.replay(run)['steps']['step-1']['status']=='RUNNING'
 with pytest.raises(ValueError,match='running attempt'):ledger.claim_next(run,p)
def test_explicit_retry_exhaustion_is_durable(tmp_path):
 p,run,a=setup(tmp_path,'conversion-audit');ledger.fail_step(run,'step-1','invalid first',a);b=ledger.claim_next(run,p)['data'];assert b['attempt_id']!=a and b['attempt_number']==2;ledger.fail_step(run,'step-1','invalid second',b['attempt_id']);assert ledger.claim_next(run,p)['status']=='BLOCKED';assert ledger.replay(run)['steps']['step-1']['attempt_number']==2
@pytest.mark.parametrize('pid',IDS)
def test_builder_resume_checks_full_prefix_and_dispatches_no_completed_task(tmp_path,pid):
 p,run,a=setup(tmp_path,pid);complete(run,pid,a);(tmp_path/'plan.json').write_text(json.dumps(p));(tmp_path/'prefix.json').write_text(json.dumps([envelope(pid)]));cmd=[sys.executable,str(BUILDER),'--json','--run-dir',str(run),'--plan-json',str(tmp_path/'plan.json'),'--prior-envelopes-json',str(tmp_path/'prefix.json')];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr;assert json.loads(r.stdout)['subagent_tasks']==[];v=envelope(pid);v['payload']['artifact']+=' Changed';(tmp_path/'prefix.json').write_text(json.dumps([v]));assert subprocess.run(cmd,capture_output=True).returncode!=0
@pytest.mark.parametrize('field',['alpha','power','baseline_rate','sample_size_per_variant','mde_absolute'])
def test_framework_cannot_back_a_numeric_parameter(field):
 v=response('experiment-design')['sidecar'];v['result'][field]=120 if field=='sample_size_per_variant' else .1;v['evidence'][0]['kind']='FRAMEWORK';v['result']['parameter_source_ids'][field]=['S1'];assert not profiles.validate_sidecar(v)['accepted']
def test_method_guidance_and_supplied_parameters_can_coexist():
 v=response('experiment-design')['sidecar'];v['evidence'].append({'id':'F1','kind':'FRAMEWORK','reference':'Supplied methodology note','summary':'Guidance only'});v['result'].update(alpha=.01,power=.9,framework_source_ids=['F1']);v['result']['parameter_source_ids'].update(alpha=['S1'],power=['S1']);assert profiles.validate_sidecar(v)['accepted']
def test_framework_in_factual_observation_rejected_even_with_user_source():
 v=response('conversion-audit')['sidecar'];v['evidence'].append({'id':'F1','kind':'FRAMEWORK','reference':'Heuristic','summary':'Not an observation'});v['result']['observations'][0]['source_ids'].append('F1');assert not profiles.validate_sidecar(v)['accepted']
def test_provenance_note_does_not_hide_owner_content():
 v=response('conversion-audit');v['artifact']+=' Provenance metadata is also provided in the sidecar.';assert profiles.validate_response(v,'conversion-audit')['accepted']
