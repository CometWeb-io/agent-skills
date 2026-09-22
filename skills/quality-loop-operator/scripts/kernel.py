from __future__ import annotations
import re
from datetime import datetime

PROFILES={
 'EDITORIAL':['brief-architect','content-writer','content-reviewer','content-roaster','repair-operator','artifact-acceptance'],
 'SALES':['brief-architect','content-writer','content-reviewer','content-roaster','repair-operator','artifact-acceptance'],
 'TECHNICAL_DOCS':['brief-architect','content-writer','content-reviewer','content-roaster','repair-operator','artifact-acceptance'],
 'RESEARCH':['brief-architect','content-writer','content-reviewer','science-roaster','repair-operator','artifact-acceptance'],
 'REPO_DEEP':['repo-roaster','repair-operator'],
 'SKILL_QUALITY':['skill-auditor','rubric-designer','benchmark-curator','skill-evaluator'],
}
MODES={'LIGHT','STANDARD','DEEP','DELTA'}
STATES={'PENDING','RUNNING','PASS','CHANGES_REQUIRED','BLOCKED','DEFER','SKIPPED'}
HEX64=re.compile(r'^[0-9a-f]{64}$')
DEBT_SEV={'BLOCKER','MAJOR','MINOR','NOTE'};DEBT_STATUS={'OPEN','CLOSED','SUPERSEDED'}
ROLLOUT_STATES={'NOT_REQUESTED','READY_FOR_CANARY','CANARY_RUNNING','READY_FOR_STAGED','STAGED_RUNNING','READY_FOR_FULL','FULL','ROLLBACK_REQUIRED','DEPRECATED','BLOCKED'}
COMPAT_STATES={'BACKWARD_COMPATIBLE','BREAKING','UNKNOWN'}
HOST_SUPPORT={'REAL_HOST_VERIFIED','STATIC_SHAPE_ONLY','DEGRADED','UNSUPPORTED','UNKNOWN'}
PAIRED_STATUS={'SIGNIFICANT_IMPROVEMENT','SIGNIFICANT_REGRESSION','NONINFERIOR','INCONCLUSIVE','INSUFFICIENT_DATA','NOT_USED'}
STABILITY_STATUS={'STABLE','FLAKY','INSUFFICIENT_DATA','NOT_USED'}

def _text(v): return isinstance(v,str) and bool(v.strip())
def _dt(v):
    if not _text(v) or 'T' not in v:return None
    t=v[:-1]+'+00:00' if v.endswith('Z') else v
    try:d=datetime.fromisoformat(t)
    except ValueError:return None
    return d if d.tzinfo is not None else None

def _lock_ok(lock, required):
    if lock is None: return (not required, [] if not required else ['policy-lock:required'])
    if not isinstance(lock,dict): return False,['policy-lock:not-object']
    e=[]
    if not _text(lock.get('pack_id')): e.append('policy-lock:pack-id')
    if not _text(lock.get('revision')): e.append('policy-lock:revision')
    digest=lock.get('sha256')
    if not isinstance(digest,str) or not HEX64.fullmatch(digest): e.append('policy-lock:sha256')
    if lock.get('locked_before_evaluation') is not True: e.append('policy-lock:not-prelocked')
    return not e,e

def validate(payload):
    if not isinstance(payload,dict): return {'status':'INVALID','next_stage':None,'errors':['payload:not-object']}
    profile=payload.get('profile'); mode=payload.get('mode','STANDARD'); errors=[]
    if profile not in PROFILES: errors.append('profile:invalid')
    if mode not in MODES: errors.append('mode:invalid')
    cid=payload.get('candidate_id'); contract=payload.get('contract_id')
    if not _text(cid): errors.append('candidate_id:required')
    if not _text(contract): errors.append('contract_id:required')
    base=payload.get('base_candidate_id')
    if mode=='DELTA' and (not _text(base) or base==cid): errors.append('base_candidate_id:required-distinct')
    _,lock_errors=_lock_ok(payload.get('policy_lock'), mode in {'DEEP','DELTA'})
    errors.extend(lock_errors)
    adaptive=payload.get('adaptive_depth')
    if adaptive is not None:
        if not isinstance(adaptive,dict) or adaptive.get('recommended_mode') not in MODES: errors.append('adaptive_depth:invalid')
        elif adaptive.get('recommended_mode')!=mode and not (adaptive.get('override_approved') is True and _text(adaptive.get('override_rationale'))): errors.append('adaptive_depth:mode-mismatch')
    replay=payload.get('replay_status')
    if replay not in {None,'REPRODUCIBLE','DRIFT','INCOMPLETE'}: errors.append('replay_status:invalid')
    cache=payload.get('cache_reuse',[])
    if not isinstance(cache,list): errors.append('cache_reuse:not-list'); cache=[]
    for i,row in enumerate(cache):
        if not isinstance(row,dict): errors.append(f'cache[{i}]:not-object'); continue
        if row.get('decision')=='REUSE' and row.get('fingerprint_match') is not True: errors.append(f'cache[{i}]:unsafe-reuse')
        if row.get('decision')=='REUSE' and row.get('source_status')!='PASS': errors.append(f'cache[{i}]:source-not-pass')
    as_of=_dt(payload.get('as_of')) if payload.get('quality_debt') is not None else None
    debt=payload.get('quality_debt',[]);blocking_debt=0
    if not isinstance(debt,list): errors.append('quality_debt:not-list'); debt=[]
    if debt and as_of is None: errors.append('quality_debt:as_of-required')
    for i,row in enumerate(debt):
        if not isinstance(row,dict): errors.append(f'debt[{i}]:not-object'); continue
        if row.get('candidate_id') not in {None,cid}: errors.append(f'debt[{i}]:candidate-mismatch')
        sev=row.get('severity');status=row.get('status')
        if sev not in DEBT_SEV: errors.append(f'debt[{i}]:severity'); continue
        if status not in DEBT_STATUS: errors.append(f'debt[{i}]:status'); continue
        due=_dt(row.get('due_at')) if row.get('due_at') is not None else None
        expired=bool(status=='OPEN' and due and as_of and due<=as_of)
        if status=='OPEN' and (sev=='BLOCKER' or (expired and (sev=='MAJOR' or row.get('kind') in {'WAIVER','CONTROL'}))): blocking_debt+=1
        if status=='CLOSED' and not row.get('closure_evidence'): errors.append(f'debt[{i}]:closed-without-evidence')
    required=PROFILES.get(profile,[])
    rows=payload.get('stages')
    if not isinstance(rows,list): errors.append('stages:not-list'); rows=[]
    by={}; last_index=-1
    for i,row in enumerate(rows):
        if not isinstance(row,dict): errors.append(f'stage[{i}]:not-object'); continue
        skill=row.get('skill'); state=row.get('state')
        if skill not in required: errors.append(f'stage[{i}]:unexpected-skill'); continue
        if skill in by: errors.append(f'stage[{i}]:duplicate-skill'); continue
        if state not in STATES: errors.append(f'stage[{i}]:state'); continue
        idx=required.index(skill)
        if idx<last_index: errors.append(f'stage[{i}]:out-of-order')
        last_index=max(last_index,idx); by[skill]=row
        if row.get('candidate_id') not in {None,cid}: errors.append(f'stage[{i}]:candidate-mismatch')
        if row.get('contract_id') not in {None,contract}: errors.append(f'stage[{i}]:contract-mismatch')
        if state=='SKIPPED':
            if row.get('skip_allowed') is not True or not _text(row.get('skip_rationale')): errors.append(f'stage[{i}]:unjustified-skip')
            if mode=='DEEP': errors.append(f'stage[{i}]:deep-required-skip')
    if profile=='SKILL_QUALITY':
        rub=by.get('rubric-designer'); bm=by.get('benchmark-curator'); ev=by.get('skill-evaluator')
        rub_hash=rub.get('rubric_hash') if isinstance(rub,dict) and rub.get('state')=='PASS' else None
        bm_hash=bm.get('benchmark_hash') if isinstance(bm,dict) and bm.get('state')=='PASS' else None
        if rub_hash is not None and (not isinstance(rub_hash,str) or not HEX64.fullmatch(rub_hash)): errors.append('skill-quality:rubric-hash')
        if isinstance(bm,dict) and bm.get('state')=='PASS':
            if not isinstance(bm_hash,str) or not HEX64.fullmatch(bm_hash): errors.append('skill-quality:benchmark-hash')
            if rub_hash is None or bm.get('rubric_hash')!=rub_hash: errors.append('skill-quality:benchmark-rubric-mismatch')
        if isinstance(ev,dict) and ev.get('state')=='PASS':
            if rub_hash is None or ev.get('rubric_hash')!=rub_hash: errors.append('skill-quality:evaluator-rubric-mismatch')
            if bm_hash is None or ev.get('benchmark_hash')!=bm_hash: errors.append('skill-quality:evaluator-benchmark-mismatch')
    lifecycle=payload.get('runtime_lifecycle')
    rollout_status='NOT_REQUESTED'
    if lifecycle is not None:
        if not isinstance(lifecycle,dict): errors.append('runtime_lifecycle:not-object')
        else:
            rollout_status=lifecycle.get('state','NOT_REQUESTED')
            if not isinstance(rollout_status,str) or rollout_status not in ROLLOUT_STATES: errors.append('runtime_lifecycle:state')
            compat=lifecycle.get('contract_compatibility','UNKNOWN'); host=lifecycle.get('host_support','UNKNOWN')
            if not isinstance(compat,str) or compat not in COMPAT_STATES: errors.append('runtime_lifecycle:compatibility')
            if not isinstance(host,str) or host not in HOST_SUPPORT: errors.append('runtime_lifecycle:host-support')
            material=lifecycle.get('material_change') is True
            obs=lifecycle.get('observation_runs',0); minobs=lifecycle.get('min_observation_runs',20)
            if not isinstance(obs,int) or isinstance(obs,bool) or obs<0: errors.append('runtime_lifecycle:observation-runs')
            if not isinstance(minobs,int) or isinstance(minobs,bool) or minobs<1: errors.append('runtime_lifecycle:min-observation-runs')
            advanced=rollout_status in {'READY_FOR_STAGED','STAGED_RUNNING','READY_FOR_FULL','FULL'}
            stability=lifecycle.get('stability_status','NOT_USED'); paired=lifecycle.get('paired_status','NOT_USED')
            if stability not in STABILITY_STATUS: errors.append('runtime_lifecycle:stability-status')
            if paired not in PAIRED_STATUS: errors.append('runtime_lifecycle:paired-status')
            if material and advanced and lifecycle.get('canary_passed') is not True: errors.append('runtime_lifecycle:canary-required')
            if material and advanced and isinstance(obs,int) and not isinstance(obs,bool) and isinstance(minobs,int) and not isinstance(minobs,bool) and obs<minobs: errors.append('runtime_lifecycle:observation-window')
            if advanced and stability!='STABLE': errors.append('runtime_lifecycle:stability-required')
            if rollout_status in {'READY_FOR_FULL','FULL'} and paired not in {'SIGNIFICANT_IMPROVEMENT','NONINFERIOR'}: errors.append('runtime_lifecycle:paired-evidence-required')
            if material and not _text(lifecycle.get('rollback_version')): errors.append('runtime_lifecycle:rollback-version')
            if compat=='BREAKING' and lifecycle.get('major_version_bump') is not True: errors.append('runtime_lifecycle:breaking-major-required')
            if compat=='BREAKING' and lifecycle.get('migration_guide_present') is not True: errors.append('runtime_lifecycle:migration-guide-required')
            if lifecycle.get('removing_public_contract') is True and not _text(lifecycle.get('deprecation_record')): errors.append('runtime_lifecycle:deprecation-record')
            if rollout_status=='DEPRECATED' and not _text(lifecycle.get('deprecation_notice')): errors.append('runtime_lifecycle:deprecation-notice')
            if rollout_status=='FULL' and host!='REAL_HOST_VERIFIED': errors.append('runtime_lifecycle:full-needs-real-host')
            if rollout_status=='ROLLBACK_REQUIRED' and lifecycle.get('rollback_executable') is not True: errors.append('runtime_lifecycle:rollback-not-executable')
    conflicts=payload.get('reconciliation',[])
    if not isinstance(conflicts,list): errors.append('reconciliation:not-list'); conflicts=[]
    unresolved=0
    for i,row in enumerate(conflicts):
        if not isinstance(row,dict): errors.append(f'reconciliation[{i}]:not-object'); continue
        if row.get('candidate_id') not in {None,cid}: errors.append(f'reconciliation[{i}]:candidate-mismatch')
        if row.get('status')=='CONFLICT' and row.get('resolved') is not True: unresolved+=1
        if row.get('resolved') is True and not _text(row.get('resolution_basis')): errors.append(f'reconciliation[{i}]:resolution-without-basis')
    if errors: return {'status':'INVALID','next_stage':None,'errors':errors,'unresolved_conflicts':unresolved,'blocking_quality_debt':blocking_debt}
    if blocking_debt:return {'status':'BLOCKED','next_stage':'quality-debt-resolution','errors':[],'unresolved_conflicts':unresolved,'blocking_quality_debt':blocking_debt}
    if replay in {'DRIFT','INCOMPLETE'}:return {'status':'BLOCKED','next_stage':'revalidation','errors':[],'unresolved_conflicts':unresolved,'blocking_quality_debt':0}
    if unresolved: return {'status':'NEEDS_RECONCILIATION','next_stage':'finding-reconciliation','errors':[],'unresolved_conflicts':unresolved,'blocking_quality_debt':0}
    for skill in required:
        row=by.get(skill)
        if row and row.get('state') in {'BLOCKED','DEFER'}:return {'status':'BLOCKED','next_stage':skill,'errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
    for skill in required:
        row=by.get(skill)
        if row is None or row.get('state') in {'PENDING','RUNNING'}:return {'status':'READY_FOR_NEXT','next_stage':skill,'errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
        if row.get('state')=='CHANGES_REQUIRED' and skill=='repair-operator':return {'status':'READY_FOR_NEXT','next_stage':'repair-operator','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
    if profile=='REPO_DEEP':return {'status':'COMPLETE','next_stage':'release-readiness','errors':[],'unresolved_conflicts':0,'software_release_verdict':'NOT_OWNED','blocking_quality_debt':0}
    if profile=='SKILL_QUALITY':
        result=by.get('skill-evaluator',{}).get('result')
        if result in {'REGRESSION','TRADEOFF'}:return {'status':'CHANGES_REQUIRED','next_stage':'skill-creator','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
        if result in {'INSUFFICIENT_EVIDENCE','DESIGN_READY',None}:return {'status':'BLOCKED','next_stage':'skill-evaluator','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
        if lifecycle is not None:
            if rollout_status in {'BLOCKED','ROLLBACK_REQUIRED'}: return {'status':'CHANGES_REQUIRED','next_stage':'rollback' if rollout_status=='ROLLBACK_REQUIRED' else 'runtime-compatibility','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0,'skill_evaluation_result':result,'rollout_status':rollout_status}
            if rollout_status in {'READY_FOR_CANARY','CANARY_RUNNING'}: return {'status':'READY_FOR_ROLLOUT','next_stage':'canary','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0,'skill_evaluation_result':result,'rollout_status':rollout_status}
            if rollout_status in {'READY_FOR_STAGED','STAGED_RUNNING'}: return {'status':'READY_FOR_ROLLOUT','next_stage':'staged-rollout','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0,'skill_evaluation_result':result,'rollout_status':rollout_status}
            if rollout_status=='READY_FOR_FULL': return {'status':'READY_FOR_ROLLOUT','next_stage':'full-rollout','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0,'skill_evaluation_result':result,'rollout_status':rollout_status}
        return {'status':'COMPLETE','next_stage':None,'errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0,'skill_evaluation_result':result,'rollout_status':rollout_status}
    acceptance=by.get('artifact-acceptance',{})
    if acceptance.get('state')!='PASS':return {'status':'BLOCKED','next_stage':'artifact-acceptance','errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}
    return {'status':'COMPLETE','next_stage':None,'errors':[],'unresolved_conflicts':0,'blocking_quality_debt':0}

def evaluate_case(case):
    if not isinstance(case,dict): return validate(None)
    return validate(case.get('input'))
