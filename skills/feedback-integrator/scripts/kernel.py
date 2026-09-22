from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta

VALID_LAYER={'ROUTING','INSTRUCTION','REFERENCE','KERNEL','EVAL','HOST','PROCESS'}
SEVERITY={'NOTE':1,'MINOR':2,'MAJOR':3,'BLOCKER':4}
OUTCOMES={'CONFIRMED','FALSE_POSITIVE','RESOLVED','UNKNOWN'}


def _text(value): return isinstance(value,str) and bool(value.strip())


def _dt(value):
    if not isinstance(value,str) or 'T' not in value: return None
    text=value[:-1]+'+00:00' if value.endswith('Z') else value
    try: out=datetime.fromisoformat(text)
    except ValueError: return None
    return out if out.tzinfo is not None else None


def _regression_ready(row):
    test=row.get('regression_test')
    if isinstance(test,dict) and _text(test.get('id')) and _text(test.get('assertion')): return True
    gap=row.get('test_gap')
    return isinstance(gap,dict) and _text(gap.get('assertion')) and _text(gap.get('owner'))


def _proposal_ready(row):
    proposal=row.get('proposed_change')
    if not isinstance(proposal,dict): return False
    return _text(proposal.get('change')) and _text(proposal.get('expected_effect')) and _text(proposal.get('evaluation_plan'))


def integrate(records,min_count=2,as_of=None,window_days=None,strict=False):
    if not isinstance(records,list):
        return {'status':'INVALID','proposal_count':0,'watch_count':0,'retired_count':0,'invalid_count':1,'proposals':[],'watch':[],'retired':[],'invalid':[{'reason':'records:not-list'}]}
    now=_dt(as_of) if as_of is not None else None
    if as_of is not None and now is None:
        return {'status':'INVALID','proposal_count':0,'watch_count':0,'retired_count':0,'invalid_count':1,'proposals':[],'watch':[],'retired':[],'invalid':[{'reason':'as_of:invalid'}]}
    if window_days is not None and (not isinstance(window_days,int) or isinstance(window_days,bool) or window_days<=0):
        return {'status':'INVALID','proposal_count':0,'watch_count':0,'retired_count':0,'invalid_count':1,'proposals':[],'watch':[],'retired':[],'invalid':[{'reason':'window_days:invalid'}]}
    groups=defaultdict(list); invalid=[]; retired=[]
    for i,row in enumerate(records):
        if not isinstance(row,dict): invalid.append({'index':i,'reason':'record:not-object'}); continue
        pattern=row.get('pattern')
        if not _text(pattern): invalid.append({'index':i,'reason':'pattern'}); continue
        severity=row.get('severity','NOTE')
        if severity not in SEVERITY: invalid.append({'index':i,'reason':'severity'}); continue
        layer=row.get('root_layer')
        if layer is not None and layer not in VALID_LAYER: invalid.append({'index':i,'reason':'invalid-root-layer'}); continue
        outcome=row.get('outcome','CONFIRMED')
        if outcome not in OUTCOMES: invalid.append({'index':i,'reason':'outcome'}); continue
        observed=_dt(row.get('observed_at')) if row.get('observed_at') is not None else None
        if row.get('observed_at') is not None and observed is None: invalid.append({'index':i,'reason':'observed_at'}); continue
        if now and window_days and observed and observed < now-timedelta(days=window_days):
            retired.append({'pattern':pattern,'context_id':row.get('context_id'),'reason':'outside-learning-window'}); continue
        groups[pattern].append(row)
    proposals=[]; watch=[]
    for pattern,rows in groups.items():
        confirmed=[r for r in rows if r.get('outcome','CONFIRMED')=='CONFIRMED']
        false_positive=[r for r in rows if r.get('outcome')=='FALSE_POSITIVE']
        resolved=[r for r in rows if r.get('outcome')=='RESOLVED']
        contexts={r.get('context_id') for r in confirmed if _text(r.get('context_id'))}
        runs={r.get('run_id') for r in confirmed if _text(r.get('run_id'))}
        severity=max((r.get('severity','NOTE') for r in confirmed), key=lambda v:SEVERITY[v], default='NOTE')
        layers={r.get('root_layer') for r in confirmed if r.get('root_layer')}
        severe=any(r.get('severity')=='BLOCKER' and r.get('systemic') is True and r.get('evidence') for r in confirmed)
        regression_ready=any(_regression_ready(r) for r in confirmed)
        proposal_ready=any(_proposal_ready(r) for r in confirmed)
        independent=len(contexts)
        item={'pattern':pattern,'independence_count':independent,'run_count':len(runs),'severity':severity,'root_layers':sorted(layers),'false_positive_count':len(false_positive),'resolved_count':len(resolved)}
        if false_positive and len(false_positive)>=len(confirmed):
            item['reason']='false-positive-dominant'; watch.append(item); continue
        if resolved and not confirmed:
            item['reason']='resolved-no-current-recurrence'; retired.append(item); continue
        if len(layers)>1:
            item['reason']='root-cause-ambiguous'; watch.append(item); continue
        enough=independent>=min_count or severe
        if enough and regression_ready and (proposal_ready or not strict):
            item['root_layer']=next(iter(layers)) if layers else None; proposals.append(item)
        else:
            if not enough: item['reason']='insufficient-independent-contexts'
            elif not regression_ready: item['reason']='regression-test-or-test-gap-required'
            else: item['reason']='proposed-change-with-evaluation-plan-required'
            watch.append(item)
    status='INVALID' if invalid else ('PROPOSED' if proposals else ('WATCH' if watch else ('RETIRED' if retired else 'NO_SIGNAL')))
    return {'status':status,'proposal_count':len(proposals),'watch_count':len(watch),'retired_count':len(retired),'invalid_count':len(invalid),'proposals':proposals,'watch':watch,'retired':retired,'invalid':invalid}



def promotion(payload):
    if not isinstance(payload,dict): return {'status':'INVALID','errors':['promotion:not-object']}
    errors=[]
    if not _text(payload.get('baseline_version')) or not _text(payload.get('challenger_version')): errors.append('version:required')
    if payload.get('baseline_version')==payload.get('challenger_version'): errors.append('version:same')
    cases=payload.get('frozen_case_count'); runs=payload.get('repeated_runs'); improvements=payload.get('improvements'); regressions=payload.get('regressions')
    if not isinstance(cases,int) or isinstance(cases,bool) or cases<=0: errors.append('frozen-case-count')
    if not isinstance(runs,int) or isinstance(runs,bool) or runs<2: errors.append('repeated-runs')
    if not isinstance(improvements,int) or isinstance(improvements,bool) or improvements<0: errors.append('improvements')
    if not isinstance(regressions,int) or isinstance(regressions,bool) or regressions<0: errors.append('regressions')
    if not _text(payload.get('evaluation_scope')): errors.append('evaluation-scope')
    if errors: return {'status':'INVALID','errors':errors}
    if payload.get('safety_regression') is True or regressions>0: return {'status':'HOLD','errors':[],'reason':'regression'}
    if improvements<1: return {'status':'HOLD','errors':[],'reason':'no-repeatable-improvement'}
    return {'status':'PROMOTE','errors':[],'reason':'repeatable-improvement-no-regression'}

def evaluate_case(case):
    if not isinstance(case,dict): return integrate(None)
    payload=case.get('input')
    if not isinstance(payload,dict): return integrate(None)
    if case.get('operation')=='promotion': return promotion(payload)
    return integrate(payload.get('records'),payload.get('min_count',2),payload.get('as_of'),payload.get('window_days'),payload.get('strict',False))
