from __future__ import annotations
import hashlib,json,math,re
HEX64=re.compile(r'^[0-9a-f]{64}$'); LEAK={'CLEAN','SUSPECT','CONTAMINATED'}
MODES={'STANDARD','DEEP'}; CLASSES={'discovery','forced','negative-control','adversarial','regression'}; DIFF={'easy','medium','hard','edge'}; SPLITS={'dev','holdout'}; CONTAM={'CLEAN','SUSPECTED','KNOWN'}; LANES={'SYNTHETIC','REAL_TASK','INCIDENT','USER_SUPPLIED'}; REQUIRED_CLASSES=CLASSES
def _text(v):return isinstance(v,str) and bool(v.strip())
def _norm(v):return ' '.join(str(v or '').casefold().split())
def _hash(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate(x):
    if not isinstance(x,dict):return {'status':'INVALID','errors':['payload:not-object'],'split_counts':{'dev':0,'holdout':0},'missing_classes':[],'contaminated_holdout':0}
    e=[]; mode=x.get('mode','STANDARD')
    if not isinstance(mode,str) or mode not in MODES:e.append('mode:invalid')
    for k in ('benchmark_id','revision','objective','target_skill'):
        if not _text(x.get(k)):e.append(f'{k}:required')
    required=x.get('required_classes',[])
    if not isinstance(required,list) or not required or not all(v in REQUIRED_CLASSES for v in required):e.append('required_classes')
    cases=x.get('cases')
    if not isinstance(cases,list) or not cases:e.append('cases:required');cases=[]
    ids=[]; prompts=[]; cls={}; split={'dev':0,'holdout':0}; contaminated_holdout=0; provenance=0
    for i,c in enumerate(cases):
        p=f'cases[{i}]'
        if not isinstance(c,dict):e.append(p+':not-object');continue
        cid=c.get('id'); ids.append(cid)
        if not _text(cid):e.append(p+':id')
        klass=c.get('class'); difficulty=c.get('difficulty'); sp=c.get('split'); con=c.get('contamination_status'); lane=c.get('source_lane')
        if klass not in CLASSES:e.append(p+':class')
        else:cls[klass]=cls.get(klass,0)+1
        if difficulty not in DIFF:e.append(p+':difficulty')
        if sp not in SPLITS:e.append(p+':split')
        else:split[sp]+=1
        if con not in CONTAM:e.append(p+':contamination')
        if lane not in LANES:e.append(p+':source_lane')
        if _text(c.get('provenance_ref')):provenance+=1
        elif lane!='SYNTHETIC':e.append(p+':provenance_ref')
        prompt=c.get('prompt'); prompts.append(_norm(prompt))
        if not _text(prompt):e.append(p+':prompt')
        if not _text(c.get('expected_behavior')):e.append(p+':expected_behavior')
        a=c.get('assertions')
        if not isinstance(a,list) or not a or not all(_text(v) for v in a):e.append(p+':assertions')
        if sp=='holdout' and con in {'KNOWN','SUSPECTED'}:contaminated_holdout+=1
    goodids=[v for v in ids if _text(v)]
    if len(goodids)!=len(set(goodids)):e.append('cases:duplicate-id')
    goodprompts=[p for p in prompts if p]
    if len(goodprompts)!=len(set(goodprompts)):e.append('cases:duplicate-prompt')
    missing=sorted(set(required)-set(cls)) if isinstance(required,list) else []
    if missing:e.append('classes:missing')
    if contaminated_holdout:e.append('holdout:contaminated')
    n=len(cases)
    leakage=x.get('leakage_scan')
    leakage_status=None
    # DEEP requires a scan; a scan supplied in STANDARD is checked too, never ignored.
    scope='deep:leakage-' if mode=='DEEP' else 'leakage:'
    if mode=='DEEP' and not isinstance(leakage,dict):e.append('deep:leakage-scan-required')
    elif leakage is not None and not isinstance(leakage,dict):e.append('leakage:not-object')
    elif leakage is not None:
        leakage_status=leakage.get('status')
        if leakage_status not in LEAK:e.append(scope+'status')
        fp=leakage.get('corpus_fingerprint')
        if leakage_status=='CLEAN' and (not isinstance(fp,str) or not HEX64.fullmatch(fp)):e.append(scope+'fingerprint')
        if leakage_status=='CONTAMINATED':e.append('holdout:leakage-contaminated')
        elif leakage_status=='SUSPECT':e.append('holdout:leakage-suspect')
    if mode=='DEEP' and n:
        min_hold=max(2,math.ceil(n*0.2))
        if split['holdout']<min_hold:e.append('deep:holdout-too-small')
        if cls and max(cls.values())/n>0.70:e.append('deep:class-dominance')
    if e:
        status='CONTAMINATED' if any(v in {'holdout:contaminated','holdout:leakage-contaminated'} for v in e) else ('INVALID' if any(v in {'deep:leakage-status','deep:leakage-fingerprint','leakage:status','leakage:fingerprint','leakage:not-object'} for v in e) else ('NEEDS_REVISION' if 'holdout:leakage-suspect' in e or 'deep:leakage-scan-required' in e else ('NEEDS_REBALANCE' if 'required_classes' not in e and any(v.startswith('deep:') or v=='classes:missing' for v in e) and all(not v.startswith('cases:') and ':required' not in v for v in e) else 'INVALID')))
        return {'status':status,'errors':e,'split_counts':split,'missing_classes':missing,'contaminated_holdout':contaminated_holdout}
    canonical={k:x.get(k) for k in ('benchmark_id','revision','objective','target_skill','mode','required_classes','cases')}
    return {'status':'READY_TO_FREEZE','errors':[],'benchmark_hash':_hash(canonical),'case_count':n,'class_counts':cls,'split_counts':split,'provenance_coverage':round(provenance/n,3) if n else 0,'leakage_status':leakage_status or 'NOT_REQUIRED'}
def evaluate_case(case):
    if not isinstance(case,dict):return validate(None)
    return validate(case.get('input'))


PASSING={'READY_TO_FREEZE'}

def main(argv=None):
    """Validate one JSON payload from a file or stdin; exit 1 when it does not pass."""
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("payload", nargs="?", type=argparse.FileType("r", encoding="utf-8"),
                        default=sys.stdin, help="JSON file (default: stdin)")
    args = parser.parse_args(argv)
    try:
        payload = json.load(args.payload)
    except json.JSONDecodeError as exc:
        parser.error(f"payload is not JSON: {exc}")
    result = validate(payload)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in PASSING else 1


if __name__ == "__main__":
    raise SystemExit(main())
