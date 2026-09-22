from __future__ import annotations
import hashlib,json,re
MODES={'LIGHT','STANDARD','DEEP'}; FLOORS={'A','B','C','D'}; MATERIAL={'critical','material','supporting'}
HEX64=re.compile(r'^[0-9a-f]{64}$')
def _text(v): return isinstance(v,str) and bool(v.strip())
def _canon(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def _hash(x): return hashlib.sha256(_canon(x).encode()).hexdigest()
def validate(x):
    if not isinstance(x,dict): return {'status':'INVALID','errors':['payload:not-object']}
    e=[]; mode=x.get('mode','STANDARD')
    if mode not in MODES:e.append('mode:invalid')
    for k in ('rubric_id','revision','purpose','target_type'):
        if not _text(x.get(k)):e.append(f'{k}:required')
    cb=x.get('candidate_blind'); frozen=x.get('frozen_before_review')
    if not isinstance(cb,bool):e.append('candidate_blind:boolean')
    if not isinstance(frozen,bool):e.append('frozen_before_review:boolean')
    if mode=='DEEP' and cb is not True:e.append('deep:candidate_blind-required')
    if mode=='DEEP' and frozen is not True:e.append('deep:pre-review-freeze-required')
    req=x.get('required_dimensions',[])
    if not isinstance(req,list) or not all(_text(v) for v in req) or len(req)!=len(set(req)):e.append('required_dimensions')
    criteria=x.get('criteria')
    if not isinstance(criteria,list) or not criteria:e.append('criteria:required'); criteria=[]
    ids=[]; dims=set(); blockers=0
    for i,c in enumerate(criteria):
        p=f'criteria[{i}]'
        if not isinstance(c,dict):e.append(p+':not-object');continue
        cid=c.get('id'); dim=c.get('dimension'); ids.append(cid)
        if not _text(cid):e.append(p+':id')
        if not _text(dim):e.append(p+':dimension')
        else:dims.add(dim)
        if c.get('observable') is not True:e.append(p+':observable')
        for k in ('description','pass_condition','fail_condition'):
            if not _text(c.get(k)):e.append(p+':'+k)
        floor=c.get('evidence_floor'); mat=c.get('materiality')
        if floor not in FLOORS:e.append(p+':evidence_floor')
        if mat not in MATERIAL:e.append(p+':materiality')
        blocker=c.get('blocker',False)
        if not isinstance(blocker,bool):e.append(p+':blocker-boolean')
        if blocker:
            blockers+=1
            if mat not in {'critical','material'}:e.append(p+':blocker-materiality')
            if floor not in {'A','B'}:e.append(p+':blocker-evidence-floor')
        if _text(c.get('pass_condition')) and _text(c.get('fail_condition')) and c.get('pass_condition').strip().casefold()==c.get('fail_condition').strip().casefold():e.append(p+':pass-fail-identical')
        if c.get('weight') is not None:
            w=c.get('weight')
            if not isinstance(w,(int,float)) or isinstance(w,bool) or not 0<=w<=1:e.append(p+':weight')
            if blocker and w==0:e.append(p+':blocker-zero-weight')
    clean=[v for v in ids if _text(v)]
    if len(clean)!=len(set(clean)):e.append('criteria:duplicate-id')
    missing=sorted(set(req)-dims) if isinstance(req,list) else []
    if missing:e.append('dimensions:missing')
    anti=x.get('anti_gaming')
    if not isinstance(anti,dict) or anti.get('no_hidden_criteria') is not True or anti.get('no_post_hoc_changes') is not True:e.append('anti_gaming:required')
    if e:return {'status':'INVALID','errors':e,'missing_dimensions':missing}
    canonical={k:x.get(k) for k in ('rubric_id','revision','purpose','target_type','mode','required_dimensions','criteria','anti_gaming')}
    status='READY_TO_FREEZE' if frozen else 'NEEDS_REVISION'
    return {'status':status,'errors':[],'rubric_hash':_hash(canonical),'criteria_count':len(criteria),'blocker_count':blockers,'missing_dimensions':missing,'frozen':bool(frozen)}
def evaluate_case(case):
    if not isinstance(case,dict):return validate(None)
    return validate(case.get('input'))
