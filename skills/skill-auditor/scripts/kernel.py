from __future__ import annotations
import re

MODES={'LIGHT','STANDARD','DEEP','DELTA'}
CHECK_STATUSES={'PASS','FAIL','UNKNOWN','N_A'}
SEVERITIES={'BLOCKER','MAJOR','MINOR','NOTE'}
DEEP_REQUIRED={'topology_inventory','trigger_overlap','reference_integrity','dependency_graph','executable_coverage','package_unpacked','supply_chain','host_claims','version_contracts'}
SEMVER=re.compile(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$')
COMPAT={'BACKWARD_COMPATIBLE','BREAKING','UNKNOWN','NOT_APPLICABLE'}
HOST_STATUS={'STATIC_SHAPE_ONLY','REAL_HOST_VERIFIED','DEGRADED','UNSUPPORTED','UNKNOWN'}

def _text(v): return isinstance(v,str) and bool(v.strip())
def _list(v): return isinstance(v,list)
def _semver(v):
    if not _text(v): return None
    m=SEMVER.fullmatch(v.strip())
    return tuple(map(int,m.groups()[:3])) if m else None
def _bump(prev,cur):
    if cur<=prev:return 'INVALID'
    if cur[0]>prev[0]:return 'MAJOR'
    if cur[1]>prev[1]:return 'MINOR'
    return 'PATCH'

def validate(x):
    if not isinstance(x,dict): return {'status':'INVALID','errors':['payload:not-object'],'next_skill':None}
    errors=[];issues=[];unknown_material=0
    mode=x.get('mode','STANDARD');sid=x.get('skill_id')
    if mode not in MODES:errors.append('mode:invalid')
    if not _text(sid):errors.append('skill_id:required')
    cur=_semver(x.get('version'));prev=_semver(x.get('previous_version')) if x.get('previous_version') is not None else None
    if cur is None:errors.append('version:semver')
    if x.get('previous_version') is not None and prev is None:errors.append('previous_version:semver')
    if mode=='DELTA' and (not _text(x.get('baseline_version')) or x.get('baseline_version')==x.get('version')):errors.append('baseline_version:required-distinct')
    compat=x.get('contract_compatibility','NOT_APPLICABLE')
    if compat not in COMPAT:errors.append('contract_compatibility:invalid')
    bump=_bump(prev,cur) if prev and cur else None
    if bump=='INVALID':errors.append('version:not-increasing')
    if compat=='BREAKING' and bump!='MAJOR':issues.append('version:breaking-requires-major')
    if compat=='BREAKING' and x.get('migration_guide_present') is not True:issues.append('migration:guide-required')
    migration=x.get('migration_plan')
    if compat=='BREAKING':
        if not isinstance(migration,dict):issues.append('migration:plan-required')
        else:
            actions=migration.get('consumer_actions'); verifies=migration.get('verification_cases')
            if not isinstance(actions,list) or not actions or not all(_text(v) for v in actions):issues.append('migration:consumer-actions')
            if not _text(migration.get('rollback_ref')):issues.append('migration:rollback-ref')
            if not isinstance(verifies,list) or not verifies or not all(_text(v) for v in verifies):issues.append('migration:verification-cases')
    if compat=='UNKNOWN':unknown_material+=1
    host_status=x.get('runtime_host_status')
    if host_status is not None and host_status not in HOST_STATUS:errors.append('runtime_host_status:invalid')
    if x.get('runtime_support_claimed') is True and host_status!='REAL_HOST_VERIFIED':issues.append('hosts:runtime-claim-without-real-host-evidence')
    pkg=x.get('package')
    if not isinstance(pkg,dict):errors.append('package:not-object');pkg={}
    lines=pkg.get('skill_md_lines')
    if not isinstance(lines,int) or isinstance(lines,bool) or lines<1:errors.append('package:skill_md_lines')
    elif lines>500:issues.append('progressive-disclosure:skill-md-over-500')
    for key,issue in [('broken_references','references:broken'),('unresolved_dependencies','dependencies:unresolved'),('forbidden_artifacts','package:forbidden-artifacts'),('symlinks','package:symlinks')]:
        v=pkg.get(key,0)
        if not isinstance(v,int) or isinstance(v,bool) or v<0:errors.append(f'package:{key}')
        elif v>0:issues.append(issue)
    evals=pkg.get('behavior_eval_cases',0);neg=pkg.get('negative_routing_cases',0)
    if not isinstance(evals,int) or isinstance(evals,bool) or evals<0:errors.append('package:behavior_eval_cases')
    elif evals==0:issues.append('evals:none')
    if not isinstance(neg,int) or isinstance(neg,bool) or neg<0:errors.append('package:negative_routing_cases')
    elif neg==0:issues.append('routing:no-negative-cases')
    claims=pkg.get('runtime_host_claims',[]);verified=pkg.get('runtime_verified_hosts',[])
    if not _list(claims) or not all(_text(v) for v in claims):errors.append('package:runtime_host_claims')
    if not _list(verified) or not all(_text(v) for v in verified):errors.append('package:runtime_verified_hosts')
    if _list(claims) and _list(verified) and set(claims)-set(verified):issues.append('hosts:unverified-runtime-claim')
    bc=pkg.get('branch_coverage');ms=pkg.get('mutation_score')
    if bc is not None and (not isinstance(bc,(int,float)) or isinstance(bc,bool) or not 0<=bc<=1):errors.append('package:branch_coverage')
    elif isinstance(bc,(int,float)) and not isinstance(bc,bool) and bc<0.95:issues.append('evals:branch-coverage-below-95')
    if ms is not None and (not isinstance(ms,(int,float)) or isinstance(ms,bool) or not 0<=ms<=1):errors.append('package:mutation_score')
    elif isinstance(ms,(int,float)) and not isinstance(ms,bool) and ms<0.80:issues.append('evals:mutation-score-below-80')
    checks=x.get('checks',[])
    if not isinstance(checks,list):errors.append('checks:not-list');checks=[]
    for i,row in enumerate(checks):
        if not isinstance(row,dict):errors.append(f'check[{i}]:not-object');continue
        status=row.get('status');sev=row.get('severity','NOTE');material=row.get('material') is True
        if status not in CHECK_STATUSES:errors.append(f'check[{i}]:status');continue
        if sev not in SEVERITIES:errors.append(f'check[{i}]:severity');continue
        if status=='N_A' and not _text(row.get('rationale')):errors.append(f'check[{i}]:na-without-rationale')
        evidence=row.get('evidence',[])
        if material and status in {'PASS','FAIL'} and (not isinstance(evidence,list) or not evidence):errors.append(f'check[{i}]:material-without-evidence')
        if material and status=='UNKNOWN':unknown_material+=1
        if status=='FAIL' and sev in {'BLOCKER','MAJOR'}:issues.append(f'check[{i}]:{sev.lower()}')
    if mode=='DEEP':
        deep=x.get('deep_checks')
        if not isinstance(deep,dict):errors.append('deep_checks:required')
        elif any(deep.get(k) is not True for k in DEEP_REQUIRED):errors.append('deep_checks:incomplete')
    if errors:return {'status':'INVALID','errors':errors,'issues':issues,'unknown_material':unknown_material,'next_skill':None}
    if unknown_material:return {'status':'DEFER','errors':[],'issues':issues,'unknown_material':unknown_material,'next_skill':None}
    if issues:return {'status':'CHANGES_REQUIRED','errors':[],'issues':issues,'unknown_material':0,'next_skill':'skill-creator'}
    next_skill='skill-evaluator' if x.get('empirical_eval_required') is True else None
    return {'status':'PASS','errors':[],'issues':[],'unknown_material':0,'next_skill':next_skill,'empirical_effectiveness_proven':False,'version_bump':bump,'migration_required':compat=='BREAKING'}

def evaluate_case(case):
    if not isinstance(case,dict):return validate(None)
    return validate(case.get('input'))
