"""Corpus admission and instruction availability, not model behavior evidence."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tooling'))
from run_model_evals import prepare, validate_suite


def test_hard_corpus_covers_each_registered_skill_without_leaking_keys_to_requests():
    suite=json.loads((ROOT/'evals/model/hard-all34-suite.json').read_text())
    cases=validate_suite(suite)
    ids={s['id'] for s in json.loads((ROOT/'registry/skills.json').read_text())['skills']}
    assert len(ids)==34 and len(cases)==68
    assert {(c['skill'],c['kind']) for c in cases}=={(s,k) for s in ids for k in ('hard','negative_control')}
    for case in cases:
        baseline=prepare(case,'no_skill',ROOT,ROOT,3072)
        current=prepare(case,'current',ROOT,ROOT,3072)
        assert baseline['instructions']=={}
        assert baseline['prompt']==current['prompt'] and baseline['fixture']==current['fixture']
        assert baseline['capabilities']==current['capabilities']=={'tools':False}
        assert 'rubric' not in current and 'kind' not in current
        assert all('evaluation.md' not in name for name in current['instructions'])
    alias=next(c for c in cases if c['skill']=='skill-orchestrator-multiagent')
    assert 'alias-of/skill-orchestrator/SKILL.md' in prepare(alias,'current',ROOT,ROOT,3072)['instructions']


def test_hard_suite_inspection_is_not_execution():
    result=subprocess.run([sys.executable,str(ROOT/'tooling/run_model_evals.py'),
                           '--suite',str(ROOT/'evals/model/hard-all34-suite.json')],
                          capture_output=True,text=True,check=True)
    report=json.loads(result.stdout)
    assert report['status']=='not_run' and report['model_calls']==0
    assert report['runtime_acceptance']=='not_assessed'
