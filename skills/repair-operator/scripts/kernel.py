from __future__ import annotations
from datetime import datetime

VALID_STATUS={'PLANNED','IN_PROGRESS','UNVERIFIED','CLOSED','OPEN','DEFERRED','WONT_FIX','REOPENED'}
VALID_CLASS={'PATCH','REWRITE','REANALYSIS','REDESIGN','VERIFY_FIRST','WONT_FIX','ROLLBACK'}
EFFORT={'XS':1,'S':2,'M':3,'L':5,'XL':8}
BLAST={'LOCAL','SECTION','CROSS_ARTIFACT','SYSTEM'}
REVERSIBILITY={'EASY','MODERATE','HARD','IRREVERSIBLE'}
PATCH_RISK={'LOW','MEDIUM','HIGH','CRITICAL'}


def _text(value): return isinstance(value,str) and bool(value.strip())


def _dt(value):
    if not isinstance(value,str) or 'T' not in value: return None
    text=value[:-1]+'+00:00' if value.endswith('Z') else value
    try: out=datetime.fromisoformat(text)
    except ValueError: return None
    return out if out.tzinfo is not None else None


def _verification_ok(ev,candidate_id):
    if not isinstance(ev,dict): return False
    if ev.get('fresh') is not True or ev.get('result')!='PASS': return False
    if not _text(ev.get('method')) or not ev.get('evidence'): return False
    if _dt(ev.get('observed_at')) is None: return False
    if not _text(candidate_id) or ev.get('candidate_id')!=candidate_id: return False
    return True


def _decision_ok(value,deep=False):
    if not isinstance(value,dict): return False
    if not (_text(value.get('owner')) and _text(value.get('rationale')) and _dt(value.get('decided_at')) is not None): return False
    if deep and _dt(value.get('expires_at')) is None: return False
    return True


def _verification_plan_ok(plan):
    if not isinstance(plan,dict): return False
    checks=plan.get('checks')
    return _text(plan.get('method')) and isinstance(checks,list) and bool(checks) and all(_text(x) for x in checks)


def _invariants_ok(rows):
    if rows is None: return True
    if not isinstance(rows,list): return False
    return all(isinstance(x,dict) and _text(x.get('id')) and x.get('state')=='PASS' for x in rows)


def _dependency_cycles(items):
    ids={x.get('repair_id') for x in items if isinstance(x,dict) and _text(x.get('repair_id'))}
    graph={}; errors=[]
    for i,item in enumerate(items):
        if not isinstance(item,dict) or not _text(item.get('repair_id')): continue
        deps=item.get('depends_on',[])
        if deps is None: deps=[]
        if not isinstance(deps,list): errors.append(f'{i}:depends-on-not-list'); continue
        clean=[]
        for dep in deps:
            if not _text(dep): errors.append(f'{i}:depends-on-id'); continue
            if dep not in ids: errors.append(f'{i}:depends-on-missing:{dep}')
            clean.append(dep)
        graph[item['repair_id']]=clean
    visiting=set(); visited=set()
    def dfs(node):
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        for nxt in graph.get(node,[]):
            if nxt in graph and dfs(nxt): return True
        visiting.remove(node); visited.add(node); return False
    for node in graph:
        if dfs(node): errors.append('repair-dependency-cycle'); break
    return errors


def validate(payload):
    if not isinstance(payload,dict): return {'status':'INVALID','closed':0,'open':0,'errors':['payload:not-object']}
    items=payload.get('items')
    if not isinstance(items,list): return {'status':'INVALID','closed':0,'open':0,'errors':['items:not-list']}
    candidate_id=payload.get('candidate_id'); strict=payload.get('strict_closure') is True or payload.get('mode')=='DEEP'
    errors=[]; closed=0; open_count=0; seen=set(); finding_to_repair={}; effort_units=0; portfolio_mode=payload.get('portfolio_mode') is True
    if candidate_id is not None and not _text(candidate_id): errors.append('candidate_id:invalid')
    errors.extend(_dependency_cycles(items))
    for i,item in enumerate(items):
        if not isinstance(item,dict): errors.append(f'{i}:not-object'); continue
        rid=item.get('repair_id')
        if not _text(rid): errors.append(f'{i}:repair-id')
        elif rid in seen: errors.append(f'{i}:duplicate-id')
        else: seen.add(rid)
        status=item.get('status'); repair_class=item.get('repair_class'); patch_risk=item.get('patch_risk','LOW')
        if status not in VALID_STATUS: errors.append(f'{i}:status')
        if repair_class not in VALID_CLASS: errors.append(f'{i}:repair-class')
        if patch_risk not in PATCH_RISK: errors.append(f'{i}:patch-risk')
        if portfolio_mode:
            effort=item.get('effort_band'); blast=item.get('blast_radius'); rev=item.get('reversibility')
            if effort not in EFFORT: errors.append(f'{i}:effort-band')
            else: effort_units+=EFFORT[effort]
            if blast not in BLAST: errors.append(f'{i}:blast-radius')
            if rev not in REVERSIBILITY: errors.append(f'{i}:reversibility')
            if rev=='IRREVERSIBLE' and item.get('explicit_approval_required') is not True: errors.append(f'{i}:irreversible-without-approval-gate')
        finding_ids=item.get('finding_ids')
        if not isinstance(finding_ids,list) or not finding_ids or not all(_text(x) for x in finding_ids): errors.append(f'{i}:orphan-repair')
        else:
            for fid in finding_ids:
                if fid in finding_to_repair and item.get('supersedes_repair_id')!=finding_to_repair[fid]: errors.append(f'{i}:finding-owned-by-multiple-active-repairs:{fid}')
                else: finding_to_repair[fid]=rid
        if patch_risk in {'HIGH','CRITICAL'} and not _text(item.get('rollback_plan')): errors.append(f'{i}:high-risk-without-rollback')
        if status in {'OPEN','PLANNED','IN_PROGRESS','UNVERIFIED','DEFERRED','REOPENED'}: open_count+=1
        if status=='REOPENED' and not _text(item.get('reopen_of')): errors.append(f'{i}:reopened-without-origin')
        if status=='CLOSED':
            if repair_class in {'VERIFY_FIRST','WONT_FIX'}: errors.append(f'{i}:closed-invalid-repair-class')
            if not _text(item.get('root_cause')) or not _text(item.get('done_when')): errors.append(f'{i}:closed-without-root-cause-done-when')
            if strict and not _verification_plan_ok(item.get('verification_plan')): errors.append(f'{i}:closed-without-verification-plan')
            if not _invariants_ok(item.get('protected_invariant_checks')): errors.append(f'{i}:closed-with-broken-invariant')
            evidence=item.get('verification_evidence')
            if not isinstance(evidence,list) or not evidence or not all(_verification_ok(ev,candidate_id) for ev in evidence): errors.append(f'{i}:closed-without-candidate-bound-verification')
            elif item.get('regression_detected') is True: errors.append(f'{i}:closed-with-regression')
            else: closed+=1
        if status=='WONT_FIX':
            if repair_class!='WONT_FIX': errors.append(f'{i}:wont-fix-class-mismatch')
            if not _decision_ok(item.get('decision_source'),strict): errors.append(f'{i}:wont-fix-without-authorized-decision')
        if status=='DEFERRED' and not _text(item.get('defer_reason')): errors.append(f'{i}:deferred-without-reason')
    return {'status':'INVALID' if errors else 'VALID','closed':closed,'open':open_count,'errors':errors,'strict_closure':strict,'portfolio_mode':portfolio_mode,'effort_units':effort_units}


def evaluate_case(case):
    if not isinstance(case,dict): return validate(None)
    return validate(case.get('input'))
