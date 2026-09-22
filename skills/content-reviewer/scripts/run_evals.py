#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
_KERNEL_SPEC=importlib.util.spec_from_file_location('content_reviewer_kernel',ROOT/'scripts'/'kernel.py')
kernel=importlib.util.module_from_spec(_KERNEL_SPEC)
assert _KERNEL_SPEC.loader is not None
_KERNEL_SPEC.loader.exec_module(kernel)

_MISSING=object()
def get_path(obj,path):
    cur=obj
    for part in path.split('.'):
        if isinstance(cur,list):
            try: cur=cur[int(part)]
            except (ValueError,IndexError,TypeError): return _MISSING
        elif isinstance(cur,dict):
            if part not in cur: return _MISSING
            cur=cur[part]
        else: return _MISSING
    return cur

def case_passes(got,case):
    if not all(got.get(k)==v for k,v in case.get('expect',{}).items()): return False
    for path,value in case.get('expect_paths',{}).items():
        if get_path(got,path)!=value: return False
    return True

def main() -> int:
    if len(sys.argv)>1:
        print('usage: run_evals.py', file=sys.stderr); return 2
    cases=json.loads((ROOT/'evals'/'cases.json').read_text(encoding='utf-8'))
    failures=[]
    for case in cases:
        try:
            got=kernel.evaluate_case(case)
            if not case_passes(got,case): failures.append({'id':case.get('id'),'expect':case.get('expect'),'expect_paths':case.get('expect_paths',{}),'got':got})
        except Exception as exc:
            failures.append({'id':case.get('id'),'error':repr(exc)})
    out={'total':len(cases),'passed':len(cases)-len(failures),'failures':failures,'status':'PASS' if not failures else 'FAIL'}
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if not failures else 1

if __name__=='__main__': raise SystemExit(main())
