from __future__ import annotations
import re

MODES={'STANDARD','DEEP'}
EXECUTION={'SPEC_ONLY','LOCAL_DETERMINISTIC','REAL_HOST'}
AGREEMENT={'CALIBRATED','NEEDS_REVIEW','INSUFFICIENT_DATA','NOT_USED'}
PARETO={'FRONTIER','DOMINATED','UNKNOWN','NOT_COMPUTED'}
PAIRED={'SIGNIFICANT_IMPROVEMENT','SIGNIFICANT_REGRESSION','NONINFERIOR','INCONCLUSIVE','INSUFFICIENT_DATA','NOT_USED'}
STABILITY={'STABLE','FLAKY','INSUFFICIENT_DATA','NOT_USED'}
HEX64=re.compile(r'^[0-9a-f]{64}$')

def _text(v): return isinstance(v,str) and bool(v.strip())
def _ids(v): return isinstance(v,list) and all(_text(x) for x in v) and len(v)==len(set(v))
def _metric_block(v): return isinstance(v,dict) and all(isinstance(v.get(k),int) and not isinstance(v.get(k),bool) and v.get(k)>=0 for k in ('passed','total','trigger_tp','trigger_fp','trigger_fn'))
def _rate(a,b): return a/b if b else None

def validate(x):
    if not isinstance(x,dict): return {'status':'INVALID','errors':['payload:not-object'],'promotion_eligible':False}
    errors=[]; mode=x.get('mode','STANDARD'); execution=x.get('execution_mode','SPEC_ONLY')
    if mode not in MODES: errors.append('mode:invalid')
    if execution not in EXECUTION: errors.append('execution_mode:invalid')
    if not _text(x.get('skill_id')): errors.append('skill_id:required')
    if not _text(x.get('candidate_version')): errors.append('candidate_version:required')
    if not _text(x.get('baseline_version')): errors.append('baseline_version:required')
    sh=x.get('suite_hash'); bsh=x.get('baseline_suite_hash'); rh=x.get('rubric_hash'); bh=x.get('benchmark_hash')
    if not isinstance(rh,str) or not HEX64.fullmatch(rh): errors.append('rubric_hash')
    if not isinstance(bh,str) or not HEX64.fullmatch(bh): errors.append('benchmark_hash')
    if not isinstance(sh,str) or not HEX64.fullmatch(sh): errors.append('suite_hash')
    if not isinstance(bsh,str) or not HEX64.fullmatch(bsh): errors.append('baseline_suite_hash')
    if isinstance(sh,str) and isinstance(bsh,str) and HEX64.fullmatch(sh) and HEX64.fullmatch(bsh) and sh!=bsh: errors.append('suite_hash:mismatch')
    declared=x.get('declared_case_ids'); executed=x.get('executed_case_ids')
    if not _ids(declared): errors.append('declared_case_ids')
    if not _ids(executed): errors.append('executed_case_ids')
    if _ids(declared) and _ids(executed) and set(declared)!=set(executed): errors.append('executed_cases:cherry-pick')
    for key in ('negative_control_count','discovery_case_count','forced_case_count'):
        v=x.get(key)
        if not isinstance(v,int) or isinstance(v,bool) or v<1: errors.append(key)
    runs=x.get('runs_per_case')
    if not isinstance(runs,int) or isinstance(runs,bool) or runs<1: errors.append('runs_per_case')
    runtime=x.get('runtime_executed') is True
    judge=x.get('judge_agreement',{'status':'NOT_USED'})
    if not isinstance(judge,dict) or judge.get('status') not in AGREEMENT: errors.append('judge_agreement:invalid')
    elif x.get('uses_llm_judge') is True and mode=='DEEP' and judge.get('status')!='CALIBRATED': errors.append('judge_agreement:deep-not-calibrated')
    pareto=x.get('pareto_status','NOT_COMPUTED')
    if pareto not in PARETO: errors.append('pareto_status:invalid')
    paired=x.get('paired_analysis',{'status':'NOT_USED'})
    stability=x.get('stability',{'status':'NOT_USED'})
    paired_status=paired.get('status') if isinstance(paired,dict) else None
    stability_status=stability.get('status') if isinstance(stability,dict) else None
    if paired_status not in PAIRED: errors.append('paired_analysis:invalid')
    if stability_status not in STABILITY: errors.append('stability:invalid')
    if execution=='REAL_HOST':
        cfg=x.get('config'); base=x.get('baseline_config')
        if not isinstance(cfg,dict) or not all(_text(cfg.get(k)) for k in ('host','model','harness_version')): errors.append('config:real-host')
        if not isinstance(base,dict) or not all(_text(base.get(k)) for k in ('host','model','harness_version')): errors.append('baseline_config:real-host')
        if isinstance(cfg,dict) and isinstance(base,dict) and any(cfg.get(k)!=base.get(k) for k in ('host','model','harness_version','reasoning_effort')): errors.append('config:mismatch')
        minimum=5 if mode=='DEEP' else 3
        if isinstance(runs,int) and not isinstance(runs,bool) and runs<minimum: errors.append('runs_per_case:insufficient')
        if mode=='DEEP':
            if paired_status in {'NOT_USED','INSUFFICIENT_DATA'}: errors.append('paired_analysis:deep-required')
            if stability_status!='STABLE': errors.append('stability:deep-not-stable')
    if execution=='SPEC_ONLY':
        if runtime: errors.append('spec-only:runtime-flag')
        if errors: return {'status':'INVALID','errors':errors,'promotion_eligible':False}
        return {'status':'DESIGN_READY','errors':[],'promotion_eligible':False,'empirical_claim_allowed':False,'paired_status':paired_status,'stability_status':stability_status}
    if not runtime: errors.append('runtime_executed:required')
    cand=x.get('candidate'); base=x.get('baseline')
    if not _metric_block(cand): errors.append('candidate:metrics')
    if not _metric_block(base): errors.append('baseline:metrics')
    if _metric_block(cand) and cand['passed']>cand['total']: errors.append('candidate:passed>total')
    if _metric_block(base) and base['passed']>base['total']: errors.append('baseline:passed>total')
    if _metric_block(cand) and _metric_block(base) and cand['total']!=base['total']: errors.append('metrics:total-mismatch')
    regress=x.get('invariant_regressions',0)
    if not isinstance(regress,int) or isinstance(regress,bool) or regress<0: errors.append('invariant_regressions')
    policy=x.get('promotion_policy',{})
    if not isinstance(policy,dict): errors.append('promotion_policy:not-object'); policy={}
    min_delta=policy.get('min_pass_rate_delta',0.05); precision_floor=policy.get('trigger_precision_floor',0.90); recall_floor=policy.get('trigger_recall_floor',0.90); max_token_ratio=policy.get('max_token_ratio',1.50); max_duration_ratio=policy.get('max_duration_ratio',2.00)
    for key,val in [('min_pass_rate_delta',min_delta),('trigger_precision_floor',precision_floor),('trigger_recall_floor',recall_floor),('max_token_ratio',max_token_ratio),('max_duration_ratio',max_duration_ratio)]:
        if not isinstance(val,(int,float)) or isinstance(val,bool) or val<0: errors.append(f'promotion_policy:{key}')
    if errors: return {'status':'INVALID','errors':errors,'promotion_eligible':False,'paired_status':paired_status,'stability_status':stability_status}
    common={'errors':[],'paired_status':paired_status,'stability_status':stability_status}
    if paired_status=='SIGNIFICANT_REGRESSION': return {'status':'REGRESSION','promotion_eligible':False,'empirical_claim_allowed':True,**common}
    if stability_status=='FLAKY': return {'status':'TRADEOFF','promotion_eligible':False,'tradeoff':'FLAKY_BEHAVIOR',**common}
    if pareto=='DOMINATED': return {'status':'TRADEOFF','promotion_eligible':False,'tradeoff':'PARETO_DOMINATED',**common}
    if cand['total']==0 or base['total']==0: return {'status':'INSUFFICIENT_EVIDENCE','promotion_eligible':False,**common}
    cand_rate=cand['passed']/cand['total']; base_rate=base['passed']/base['total']; delta=cand_rate-base_rate
    pden=cand['trigger_tp']+cand['trigger_fp']; rden=cand['trigger_tp']+cand['trigger_fn']; precision=_rate(cand['trigger_tp'],pden); recall=_rate(cand['trigger_tp'],rden)
    metrics={'pass_rate_delta':round(delta,4)}
    if precision is None or recall is None: return {'status':'INSUFFICIENT_EVIDENCE','promotion_eligible':False,**metrics,**common}
    metrics.update({'trigger_precision':round(precision,4),'trigger_recall':round(recall,4)})
    if regress>0 or delta<0: return {'status':'REGRESSION','promotion_eligible':False,**metrics,**common}
    if precision<precision_floor or recall<recall_floor: return {'status':'TRADEOFF','promotion_eligible':False,'tradeoff':'TRIGGER_QUALITY',**metrics,**common}
    ct=cand.get('tokens'); bt=base.get('tokens'); cd=cand.get('duration_s'); bd=base.get('duration_s')
    token_ratio=(ct/bt) if isinstance(ct,(int,float)) and isinstance(bt,(int,float)) and not isinstance(ct,bool) and not isinstance(bt,bool) and bt>0 else 1.0
    duration_ratio=(cd/bd) if isinstance(cd,(int,float)) and isinstance(bd,(int,float)) and not isinstance(cd,bool) and not isinstance(bd,bool) and bd>0 else 1.0
    metrics.update({'token_ratio':round(token_ratio,3),'duration_ratio':round(duration_ratio,3)})
    if token_ratio>max_token_ratio or duration_ratio>max_duration_ratio: return {'status':'TRADEOFF','promotion_eligible':False,'tradeoff':'RESOURCE_BUDGET',**metrics,**common}
    if mode=='DEEP' and execution=='REAL_HOST' and paired_status=='INCONCLUSIVE': return {'status':'INSUFFICIENT_EVIDENCE','promotion_eligible':False,**metrics,**common}
    if delta>=min_delta:
        if mode=='DEEP' and execution=='REAL_HOST' and paired_status!='SIGNIFICANT_IMPROVEMENT':
            return {'status':'NO_MATERIAL_CHANGE','promotion_eligible':False,'empirical_claim_allowed':True,**metrics,**common}
        return {'status':'IMPROVED','promotion_eligible':True,'empirical_claim_allowed':True,**metrics,**common}
    return {'status':'NO_MATERIAL_CHANGE','promotion_eligible':False,'empirical_claim_allowed':True,**metrics,**common}

def evaluate_case(case):
    if not isinstance(case,dict): return validate(None)
    return validate(case.get('input'))
