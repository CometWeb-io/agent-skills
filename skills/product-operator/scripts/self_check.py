#!/usr/bin/env python3
"""Offline package smoke check, not host discovery or LLM acceptance."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    old=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True
        assert spec.loader is not None
        spec.loader.exec_module(module)
    finally:sys.dont_write_bytecode=old
    return module


def main()->int:
    results=[]
    def check(name,fn):
        try:
            if fn() is False:raise ValueError('check did not pass')
            results.append({'check':name,'status':'passed'})
        except Exception:
            results.append({'check':name,'status':'failed'})
    try:
        brief=load('selfcheck_brief',ROOT/'scripts/prepare_brief.py'); k=brief.kernel
        evaluator=load('selfcheck_evaluator',ROOT/'scripts/run_evals.py')
        sample=brief.read(ROOT/'examples/brief.synthetic.pl.json')
        cases=k.load_json_arg(str(ROOT/'evals/golden-cases.json'))
        if not cases:raise ValueError('empty golden suite')
    except Exception:
        print(json.dumps({'status':'failed','reason':'could_not_load_bundled_resources'}));return 1
    required=['SKILL.md','VERSION','LICENSE','agents/openai.yaml','assets/icon.svg',
              'references/modes.md','references/source-routing.md','references/state-model.md',
              'references/prioritization.md','references/control-loop.md','references/output-contract.md',
              'references/delegation.md','references/safety.md','references/connector-playbook.md',
              'references/evaluation.md','references/local-workflow.md']
    check('bundled_resources',lambda:all((ROOT/n).is_file() and (ROOT/n).stat().st_size>0 for n in required))
    for case in cases:
        check('golden:'+case['id'],lambda case=case:evaluator.run_case(case)[0])
    def roundtrip():
        result=brief.assemble(sample)
        assert result['validation']['status']!='FAIL'
        report,integrity=k.unwrap_report(result['snapshot'])
        assert report==result['report']
        assert not result['plan']['held_implementation_action_ids']==[]
        assert report['readiness']['status']!='READY'
        assert not report['now']
        assert report['verify_now']
        files=brief.artifacts(result)
        manifest=json.loads(files['BRIEF-MANIFEST.json'])
        assert all(hashlib.sha256(files[n]).hexdigest()==sha for n,sha in manifest['files'].items())
    check('brief_snapshot_roundtrip',roundtrip)
    def rejected_snapshot():
        baseline=brief.assemble(sample)['snapshot'];baseline['report']['goal']='changed'
        try:brief.assemble(sample,previous=baseline)
        except ValueError:return True
        return False
    check('changed_snapshot_rejected',rejected_snapshot)
    def blocking_flags():
        data=copy.deepcopy(sample);data['critical_gap_open']=True
        return k.build_plan(data)['readiness']['status']=='BLOCKED'
    check('explicit_blocking_flag',blocking_flags)
    def integrity():
        path=ROOT/'PACKAGE-MANIFEST.json'
        if not path.is_file():
            return True # A source directory can be tested without a built ZIP.
        manifest=k.load_json_arg(str(path))
        assert manifest.get('schema')=='cometweb.package/v1'
        assert isinstance(manifest.get('files'),dict) and manifest['files']
        for name,sha in manifest['files'].items():
            target=ROOT/name
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            assert target.resolve().is_relative_to(ROOT)
            assert not target.is_symlink()
            assert target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==sha
        return True
    if (ROOT/'PACKAGE-MANIFEST.json').is_file():
        check('manifest_bytes_when_present',integrity)
    else:
        results.append({'check':'manifest_bytes_when_present','status':'not_assessed'})
    output={'status':'passed' if all(r['status'] in {'passed','not_assessed'} for r in results) else 'failed',
            'scope':'offline_bundled_smoke_only','checks':results,'python':sys.version.split()[0],
            'model_calls':0,'host_acceptance':'not_assessed','source_authentication':'not_performed'}
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if output['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
