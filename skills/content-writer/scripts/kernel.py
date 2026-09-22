from __future__ import annotations
from datetime import datetime

VALID_STATUS={'SUPPORTED','INFERRED','OPINION','EXAMPLE','UNRESOLVED','UNSUPPORTED'}
VALID_MODES={'DRAFT','REVISION','FINAL'}
VALID_POLICIES={'SOURCE_BOUND','EVIDENCE_REQUIRED','CONTEXTUAL_DRAFT','CREATIVE'}
FRESH={'CURRENT','NEAR_EXPIRY'}
AUTHORITATIVE={'PRIMARY','OFFICIAL','SYSTEM_OF_RECORD'}
GRADE={'D':1,'C':2,'B':3,'A':4}


def _text(value): return isinstance(value,str) and bool(value.strip())


def _dt(value):
    if not isinstance(value,str) or 'T' not in value: return None
    text=value[:-1]+'+00:00' if value.endswith('Z') else value
    try: out=datetime.fromisoformat(text)
    except ValueError: return None
    return out if out.tzinfo is not None else None


def _evidence_ok(ev,freshness_required=False):
    if not isinstance(ev,dict): return False
    if not _text(ev.get('source')) or not _text(ev.get('locator')): return False
    if freshness_required:
        if _dt(ev.get('observed_at')) is None: return False
        if ev.get('freshness_status') not in FRESH: return False
    return True


def _dependency_errors(claims):
    ids={c.get('claim_id') for c in claims if isinstance(c,dict) and _text(c.get('claim_id'))}
    graph={}
    errors=[]
    for i,c in enumerate(claims):
        if not isinstance(c,dict) or not _text(c.get('claim_id')): continue
        deps=c.get('basis_claim_ids',[])
        if deps is None: deps=[]
        if not isinstance(deps,list): errors.append(f'claim[{i}]:basis-not-list'); continue
        clean=[]
        for dep in deps:
            if not _text(dep): errors.append(f'claim[{i}]:basis-id'); continue
            if dep not in ids: errors.append(f'claim[{i}]:basis-missing:{dep}')
            clean.append(dep)
        graph[c['claim_id']]=clean
    visiting=set(); visited=set()
    def dfs(node):
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        for nxt in graph.get(node,[]):
            if nxt in graph and dfs(nxt): return True
        visiting.remove(node); visited.add(node); return False
    for node in graph:
        if dfs(node): errors.append('claim-dependency-cycle'); break
    return errors


def _invariant_errors(report):
    invariants=report.get('protected_invariants')
    if invariants is None: return []
    if not isinstance(invariants,list): return ['protected_invariants:not-list']
    ids=[]; errors=[]
    for i,item in enumerate(invariants):
        iid=item if _text(item) else item.get('id') if isinstance(item,dict) else None
        if not _text(iid): errors.append(f'protected_invariants[{i}]:invalid')
        else: ids.append(iid)
    checks=report.get('invariant_checks')
    if not isinstance(checks,list): return errors+['invariant_checks:not-list']
    by_id={c.get('id'):c for c in checks if isinstance(c,dict) and _text(c.get('id'))}
    for iid in ids:
        if iid not in by_id: errors.append(f'invariant:{iid}:missing-check')
        elif by_id[iid].get('state')!='PASS': errors.append(f'invariant:{iid}:not-pass')
    return errors


def validate(report):
    if not isinstance(report,dict):
        return {'status':'FAIL','errors':['report:not-object'],'release_eligible':False,'unresolved_material':0,'mode':'DRAFT'}
    claims=report.get('claims',[])
    if not isinstance(claims,list):
        return {'status':'FAIL','errors':['claims:not-list'],'release_eligible':False,'unresolved_material':0,'mode':report.get('mode','DRAFT')}
    errors=[]; unresolved_material=0; seen=set()
    mode=report.get('mode','FINAL')
    if mode not in VALID_MODES: errors.append('mode:invalid')
    policy=report.get('evidence_policy','EVIDENCE_REQUIRED')
    if policy not in VALID_POLICIES: errors.append('evidence_policy:invalid')
    candidate_id=report.get('candidate_id'); brief_id=report.get('brief_id')
    if candidate_id is not None and not _text(candidate_id): errors.append('candidate_id:invalid')
    if brief_id is not None and not _text(brief_id): errors.append('brief_id:invalid')
    if mode=='REVISION':
        parent=report.get('parent_candidate_id')
        if not _text(candidate_id) or not _text(parent): errors.append('revision:candidate-parent-required')
        elif candidate_id==parent: errors.append('revision:parent-same-as-candidate')
    approved=set(x for x in report.get('approved_sources',[]) if _text(x)) if isinstance(report.get('approved_sources',[]),list) else set()
    floors=report.get('evidence_floor')
    if floors is not None:
        if not isinstance(floors,dict): errors.append('evidence_floor:not-object'); floors={}
        else:
            for key in ('critical','material','supporting'):
                if key in floors and floors[key] not in GRADE: errors.append(f'evidence_floor:{key}')
    for i,claim in enumerate(claims):
        if not isinstance(claim,dict): errors.append(f'claim[{i}]:not-object'); continue
        cid=claim.get('claim_id')
        if not _text(cid): errors.append(f'claim[{i}]:claim-id')
        elif cid in seen: errors.append(f'claim[{i}]:duplicate-id')
        else: seen.add(cid)
        status=claim.get('status')
        if status not in VALID_STATUS: errors.append(f'claim[{i}]:invalid-status'); continue
        material=claim.get('material') is True; presented=claim.get('presented_as_fact') is True
        if status in {'OPINION','EXAMPLE','UNRESOLVED','UNSUPPORTED'} and presented:
            errors.append(f'claim[{i}]:nonfact-presented-as-fact')
        if material and status=='SUPPORTED':
            evidence=claim.get('evidence')
            if not isinstance(evidence,list) or not evidence: errors.append(f'claim[{i}]:supported-without-evidence')
            elif not all(_evidence_ok(ev,claim.get('freshness_required') is True) for ev in evidence): errors.append(f'claim[{i}]:bad-evidence')
            else:
                if policy=='SOURCE_BOUND' and (not approved or any(ev.get('source') not in approved for ev in evidence)):
                    errors.append(f'claim[{i}]:source-not-approved')
                if claim.get('high_risk') is True and not any(ev.get('authority') in AUTHORITATIVE for ev in evidence):
                    errors.append(f'claim[{i}]:high-risk-missing-authority')
                if floors:
                    use='critical' if claim.get('high_risk') is True else 'material'
                    minimum=floors.get(use)
                    grade=claim.get('evidence_grade')
                    if minimum and grade not in GRADE: errors.append(f'claim[{i}]:evidence-grade-required')
                    elif minimum and GRADE[grade]<GRADE[minimum]: errors.append(f'claim[{i}]:evidence-grade-below-floor')
        if material and status=='INFERRED':
            basis=claim.get('basis_claim_ids')
            if not isinstance(basis,list) or not basis or not all(_text(x) for x in basis): errors.append(f'claim[{i}]:inference-without-basis')
            if presented: errors.append(f'claim[{i}]:inference-presented-as-fact')
        if material and status in {'UNRESOLVED','UNSUPPORTED'}: unresolved_material+=1
    errors.extend(_dependency_errors(claims)); errors.extend(_invariant_errors(report))
    valid=not errors
    release_eligible=valid and unresolved_material==0 and mode!='DRAFT'
    if policy=='CONTEXTUAL_DRAFT': release_eligible=False
    return {'status':'PASS' if valid else 'FAIL','errors':errors,'release_eligible':release_eligible,'unresolved_material':unresolved_material,'mode':mode}


def evaluate_case(case):
    if not isinstance(case,dict): return validate(None)
    return validate(case.get('input'))
