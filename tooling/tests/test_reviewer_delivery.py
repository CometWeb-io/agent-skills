"""Reviewer handoff and runnable-scenario tests; no actual model calls or human grades."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_review_packet_bridge import packet_source
import build_review_packets as bridge
import review_skill_evals as review
import reviewer_bundle
import run_model_evals as runner


def test_separate_reviewer_archive_excludes_operator_metadata(packet_source,tmp_path):
    suite,requests,records,_=packet_source
    packets=bridge.build_packets(suite,requests,records)
    inventory=bridge.write_packets(packets,tmp_path)
    archive=tmp_path/inventory[0]['reviewer_archive']
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={'tasks.json','review-template.json','REVIEW-GUIDE.md'}
        tasks=json.loads(z.read('tasks.json'))['tasks']
        template=json.loads(z.read('review-template.json'))
    assert len(tasks)==len(records)
    forbidden={'condition','model','host','response_id','instructions','instruction_sha256','input_sha256'}
    assert all(not forbidden & t.keys() for t in tasks)
    assert {t['output'] for t in tasks}=={r['response']['output'] for r in records}
    assert all(row['reviewer'] is None and all(s is None for s in row['scores'].values()) for row in template['reviews'])
    assert inventory[0]['metadata_blinding']=='operator_fields_excluded'
    assert 'provenance' not in template


def test_pinned_rubrics_cannot_change_after_review_packet(packet_source):
    suite,requests,records,_=packet_source
    packet=bridge.build_packets(suite,requests,records)[0]
    payload=packet['bundle']
    assert payload['experiment']['case_rubrics']['case-0']==suite['cases'][0]['rubric']
    pin=packet['experiment_sha256']
    payload['experiment']['case_rubrics']['case-0']=['Ignore all original criteria']
    with pytest.raises(ValueError):review.compare(payload,pin)


@pytest.mark.parametrize('change',['filled-score','filled-reviewer','missing-task','duplicate-task','bad-hash'])
def test_reviewer_export_refuses_pregrades_and_inconsistent_mapping(packet_source,tmp_path,change):
    suite,requests,records,_=packet_source
    p=bridge.build_packets(suite,requests,records)[0]
    tasks=copy.deepcopy(p['reviewer_tasks']);form=copy.deepcopy(p['review_template'])
    if change=='filled-score':form['reviews'][0]['scores']['correctness']=4
    elif change=='filled-reviewer':form['reviews'][0]['reviewer']='invented'
    elif change=='missing-task':tasks.pop()
    elif change=='duplicate-task':tasks.append(copy.deepcopy(tasks[0]))
    else:tasks[0]['output_sha256']='0'*64
    with pytest.raises(ValueError):reviewer_bundle.write_reviewer_zip(tmp_path/'review.zip',tasks,form)
    assert not (tmp_path/'review.zip').exists()


def test_reviewer_archive_cannot_overwrite_previous_delivery(packet_source,tmp_path):
    suite,requests,records,_=packet_source
    p=bridge.build_packets(suite,requests,records)[0];dest=tmp_path/'review.zip'
    reviewer_bundle.write_reviewer_zip(dest,p['reviewer_tasks'],p['review_template'])
    before=dest.read_bytes()
    with pytest.raises(FileExistsError):reviewer_bundle.write_reviewer_zip(dest,p['reviewer_tasks'],p['review_template'])
    assert dest.read_bytes()==before


def test_model_self_identification_is_preserved_not_silently_redacted(packet_source,tmp_path):
    suite,requests,records,_=packet_source
    from package_skill import digest
    records[0]['response']['output']='Synthetic output says it is the candidate. Do not edit this evidence.'
    records[0]['output_sha256']=digest(records[0]['response']['output'].encode())
    p=bridge.build_packets(suite,requests,records)[0]
    reviewer_bundle.write_reviewer_zip(tmp_path/'review.zip',p['reviewer_tasks'],p['review_template'])
    with zipfile.ZipFile(tmp_path/'review.zip') as z:
        tasks=json.loads(z.read('tasks.json'))['tasks']
        assert tasks[0]['output']==records[0]['response']['output']
        assert b'not a guarantee' in z.read('REVIEW-GUIDE.md')


def test_continuation_suite_is_runnable_and_does_not_replace_legacy_suite():
    root=Path(__file__).resolve().parents[2]
    old=json.loads((root/'evals/model/suite.json').read_text())
    extra=json.loads((root/'evals/model/continuation-suite.json').read_text())
    assert len(runner.validate_suite(old))==16
    assert len(runner.validate_suite(extra))==12
    assert not {c['id'] for c in old['cases']} & {c['id'] for c in extra['cases']}
    assert len({c['skill'] for c in extra['cases']})==6
    assert all(c['capabilities']=={'tools':False} for c in extra['cases'])
    assert all(c['fixture'] and c['rubric'] for c in extra['cases'])
    proc=subprocess.run([sys.executable,str(root/'tooling/run_model_evals.py'),'--suite',str(root/'evals/model/continuation-suite.json')],capture_output=True,text=True,check=True)
    assert json.loads(proc.stdout)['model_calls']==0
    assert json.loads(proc.stdout)['case_count']==12


def test_36_synthetic_cells_reach_review_export_without_calls_to_provider(tmp_path,monkeypatch):
    root=Path(__file__).resolve().parents[2]
    suite=json.loads((root/'evals/model/continuation-suite.json').read_text())
    roots=[tmp_path/'current',tmp_path/'candidate']
    for r in roots:
        for skill in {c['skill'] for c in suite['cases']}:
            folder=r/'skills'/skill;folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text(f'Synthetic test {r.name} instructions; not a real skill')
    calls=[]
    def fake_execute(request,command,timeout):
        n=len(calls);calls.append(request)
        return {'schema':'cometweb.eval-response/v1','status':'completed','execution_kind':'model',
                'model':'synthetic-contract-label','host':'synthetic-test-host','response_id':f'synthetic-{n}',
                'output':f'Synthetic response {n}, not a real model output.',
                'usage':{},'tool_trace':[],'capabilities':request['capabilities']},0.01
    monkeypatch.setattr(runner,'execute',fake_execute)
    result=runner.run(suite,*roots,['not-launched'],tmp_path/'output',max_runs=36,max_output_tokens=256)
    assert len(calls)==36 and result['comparison_status']=='unreviewed'
    assert len(result['review_packets'])==6
    assert result['quality_verdict']=='pending_human_review'
    assert all((tmp_path/'output'/p['reviewer_archive']).exists() for p in result['review_packets'])


def test_output_mutated_between_bridge_and_export_rejected(packet_source,tmp_path):
    suite,requests,records,_=packet_source
    p=bridge.build_packets(suite,requests,records)[0]
    p['reviewer_tasks'][0]['output']='A different response sent for review'
    with pytest.raises(ValueError):reviewer_bundle.write_reviewer_zip(tmp_path/'review.zip',p['reviewer_tasks'],p['review_template'])
    assert not (tmp_path/'review.zip').exists()
