from __future__ import annotations
import re

VALID_POLICIES={'SOURCE_BOUND','EVIDENCE_REQUIRED','CONTEXTUAL_DRAFT','CREATIVE'}
VALID_MODES={'LIGHT','STANDARD','DEEP'}
VALID_RISK={'LOW','MEDIUM','HIGH','CRITICAL'}
VALID_PRIORITY={'MUST','SHOULD','MAY'}
VALID_PRD_PRIORITY={'P0','P1','P2'}
REQUIRED_TEXT=('objective','audience')
HEX64=re.compile(r'^[0-9a-f]{64}$')


def _text(value):
    return isinstance(value,str) and bool(value.strip())


def _positive_int(value):
    return isinstance(value,int) and not isinstance(value,bool) and value>0


def _criteria(value):
    if not isinstance(value,list) or not value:
        return False, ['acceptance_criteria:missing']
    errors=[]; seen=set()
    for i,item in enumerate(value):
        if not isinstance(item,dict):
            errors.append(f'acceptance_criteria[{i}]:not-object'); continue
        cid=item.get('id')
        if not _text(cid): errors.append(f'acceptance_criteria[{i}]:id')
        elif cid in seen: errors.append(f'acceptance_criteria[{i}]:duplicate-id')
        else: seen.add(cid)
        if not _text(item.get('check')): errors.append(f'acceptance_criteria[{i}]:check')
        if item.get('observable') is not True: errors.append(f'acceptance_criteria[{i}]:not-observable')
        priority=item.get('priority','MUST')
        if not isinstance(priority,str) or priority not in VALID_PRIORITY: errors.append(f'acceptance_criteria[{i}]:priority')
        if priority=='MUST' and item.get('evidence_required') is True and not _text(item.get('verification_method')):
            errors.append(f'acceptance_criteria[{i}]:must-evidence-without-method')
    return not errors, errors


def _deliverables(value):
    if not isinstance(value,list) or not value:
        return False, ['deliverables:missing']
    errors=[]; seen=set()
    for i,item in enumerate(value):
        if _text(item):
            key=item.strip()
        elif isinstance(item,dict) and _text(item.get('id')) and _text(item.get('type')):
            key=item.get('id')
        else:
            errors.append(f'deliverables[{i}]:invalid'); continue
        if key in seen: errors.append(f'deliverables[{i}]:duplicate-id')
        else: seen.add(key)
    return not errors, errors


def _material_assumptions(value):
    if value is None: return [], []
    if not isinstance(value,list): return [], ['assumptions:not-list']
    material=[]; errors=[]
    for i,item in enumerate(value):
        if isinstance(item,str) and item.strip():
            material.append({'value':item,'material':True}); continue
        if not isinstance(item,dict):
            errors.append(f'assumptions[{i}]:invalid'); continue
        if not _text(item.get('value') or item.get('assumption')):
            errors.append(f'assumptions[{i}]:value'); continue
        if item.get('consequential') is True:
            errors.append(f'assumptions[{i}]:consequential-cannot-be-assumed')
        if item.get('material',True): material.append(item)
    return material, errors


def _open_decisions(value):
    if value is None: return [], []
    if not isinstance(value,list): return [], ['decision_needed:not-list']
    open_rows=[]; errors=[]; seen=set()
    for i,item in enumerate(value):
        if isinstance(item,str) and item.strip():
            open_rows.append({'question':item,'material':True,'resolved':False}); continue
        if not isinstance(item,dict):
            errors.append(f'decision_needed[{i}]:invalid'); continue
        key=item.get('id') or item.get('question') or item.get('decision')
        if not _text(item.get('question') or item.get('decision')):
            errors.append(f'decision_needed[{i}]:question'); continue
        if _text(key):
            if key in seen: errors.append(f'decision_needed[{i}]:duplicate-id')
            else: seen.add(key)
        if item.get('material',True) and not item.get('resolved',False): open_rows.append(item)
    return open_rows, errors


def _invariants(value):
    if value is None: return [], []
    if not isinstance(value,list): return [], ['protected_invariants:not-list']
    errors=[]; out=[]; seen=set()
    for i,item in enumerate(value):
        if isinstance(item,str) and item.strip():
            iid=item.strip(); row={'id':iid,'rule':item.strip()}
        elif isinstance(item,dict) and _text(item.get('id')) and _text(item.get('rule') or item.get('description')):
            iid=item['id']; row=item
        else:
            errors.append(f'protected_invariants[{i}]:invalid'); continue
        if iid in seen: errors.append(f'protected_invariants[{i}]:duplicate-id')
        else: seen.add(iid); out.append(row)
    return out, errors


_MISSING=object()


def _delta_criteria(brief, side):
    value=brief.get('acceptance_criteria',_MISSING)
    if value is _MISSING: return {}, []
    if not isinstance(value,list): return {}, [f'{side}.acceptance_criteria:not-list']
    errors=[]; out={}; seen=set()
    for i,item in enumerate(value):
        if not isinstance(item,dict):
            errors.append(f'{side}.acceptance_criteria[{i}]:not-object'); continue
        cid=item.get('id')
        if not _text(cid):
            errors.append(f'{side}.acceptance_criteria[{i}]:id'); continue
        priority=item.get('priority','MUST')
        if not isinstance(priority,str) or priority not in VALID_PRIORITY:
            errors.append(f'{side}.acceptance_criteria[{i}]:priority')
        if cid in seen: errors.append(f'{side}.acceptance_criteria[{i}]:duplicate-id')
        else: seen.add(cid); out[cid]=item
    return out, errors


def _delta_invariants(brief, side):
    value=brief.get('protected_invariants',_MISSING)
    if value is _MISSING: return set(), []
    if not isinstance(value,list): return set(), [f'{side}.protected_invariants:not-list']
    errors=[]; out=set()
    for i,item in enumerate(value):
        if isinstance(item,str) and item.strip():
            iid=item.strip()
        elif isinstance(item,dict) and _text(item.get('id')) and _text(item.get('rule') or item.get('description')):
            iid=item['id']
        else:
            errors.append(f'{side}.protected_invariants[{i}]:invalid'); continue
        if iid in out: errors.append(f'{side}.protected_invariants[{i}]:duplicate-id')
        else: out.add(iid)
    return out, errors


def _rubric_lock_errors(brief):
    lock=brief.get('rubric_lock')
    if lock is None: return []
    if not isinstance(lock,dict): return ['rubric_lock:not-object']
    errors=[]
    if not _text(lock.get('pack_id')): errors.append('rubric_lock:pack-id')
    if not _text(lock.get('revision')): errors.append('rubric_lock:revision')
    digest=lock.get('sha256')
    if not isinstance(digest,str) or not HEX64.fullmatch(digest): errors.append('rubric_lock:sha256')
    if lock.get('locked_before_execution') is not True: errors.append('rubric_lock:not-prelocked')
    return errors


def _version_errors(brief):
    errors=[]
    bid=brief.get('brief_id'); ver=brief.get('brief_version')
    if bid is not None or ver is not None:
        if not _text(bid): errors.append('brief_id:required-with-version')
        if not _positive_int(ver): errors.append('brief_version:positive-int')
    parent=brief.get('supersedes_brief_id')
    if parent is not None and not _text(parent): errors.append('supersedes_brief_id:invalid')
    if _text(parent) and _text(bid) and parent==bid: errors.append('supersedes_brief_id:self')
    return errors


def _prd_profile(brief):
    profile=brief.get('artifact_profile')
    if profile is None:
        return ([], ['prd:profile-required']) if 'prd' in brief else ([], [])
    if profile!='PRD': return [], ['artifact_profile:invalid']
    prd=brief.get('prd')
    if prd is None: return ['prd'], []
    if not isinstance(prd,dict): return [], ['prd:not-object']
    missing=[]; errors=[]
    reqs=prd.get('requirements'); slices=prd.get('delivery_slices')
    for key in ('requirements','delivery_slices'):
        value=prd.get(key)
        if value is None or value==[]: missing.append('prd.'+key)
        elif not isinstance(value,list): errors.append('prd.'+key+':not-list')
    for key in ('implementation_constraints','data_contracts','interface_contracts','non_goals'):
        if not isinstance(prd.get(key),list): errors.append('prd.'+key+':not-list')
    if not isinstance(reqs,list) or not isinstance(slices,list): return missing,errors
    ac=brief.get('acceptance_criteria')
    ac_ids={x['id'] for x in ac if isinstance(x,dict) and _text(x.get('id'))} if isinstance(ac,list) else set()
    ids=set(); deps={}
    for i,row in enumerate(reqs):
        prefix=f'prd.requirements[{i}]'
        if not isinstance(row,dict): errors.append(prefix+':not-object'); continue
        rid=row.get('id')
        if not _text(rid): errors.append(prefix+':id'); continue
        if rid in ids: errors.append(prefix+':duplicate-id')
        ids.add(rid)
        if not _text(row.get('description')): errors.append(prefix+':description')
        if not isinstance(row.get('priority'),str) or row['priority'] not in VALID_PRD_PRIORITY: errors.append(prefix+':priority')
        refs=row.get('acceptance_criteria_ids')
        if not isinstance(refs,list) or not refs or any(not _text(x) for x in refs): errors.append(prefix+':criteria-refs')
        elif len(set(refs))!=len(refs) or any(x not in ac_ids for x in refs): errors.append(prefix+':unknown-or-duplicate-criterion')
        refs=row.get('depends_on')
        if not isinstance(refs,list) or any(not _text(x) for x in refs): errors.append(prefix+':dependency-refs')
        elif len(set(refs))!=len(refs): errors.append(prefix+':duplicate-dependency')
        else: deps[rid]=refs
    for _rid, refs in deps.items():
        if any(x not in ids for x in refs): errors.append('prd.requirements:unknown-dependency')
    # Iterative topological removal avoids recursion limits on malformed/deep DAGs.
    pending=set(ids); resolved=set()
    # Each pass resolves at least one requirement; bound malformed graphs even
    # when the diagnostic branch is damaged or changed independently.
    for _ in range(len(ids)):
        if not pending: break
        ready={rid for rid in pending if all(x in resolved for x in deps.get(rid,[]))}
        if not ready: errors.append('prd.requirements:cycle-or-unresolved-dependency'); break
        pending-=ready; resolved|=ready
    scheduled={}; slice_ids=set()
    for i,row in enumerate(slices):
        prefix=f'prd.delivery_slices[{i}]'
        if not isinstance(row,dict): errors.append(prefix+':not-object'); continue
        sid=row.get('id')
        if not _text(sid): errors.append(prefix+':id')
        elif sid in slice_ids: errors.append(prefix+':duplicate-id')
        else: slice_ids.add(sid)
        if not _text(row.get('verification')): errors.append(prefix+':verification')
        refs=row.get('requirement_ids')
        if not isinstance(refs,list) or not refs or any(not _text(x) for x in refs): errors.append(prefix+':requirement-refs'); continue
        for rid in refs:
            if rid not in ids: errors.append(prefix+':unknown-requirement')
            if rid in scheduled: errors.append(prefix+':duplicate-requirement')
            else: scheduled[rid]=i
    if set(scheduled)!=ids: errors.append('prd.delivery_slices:incomplete-coverage')
    for rid,refs in deps.items():
        if rid in scheduled and any(x in scheduled and scheduled[x]>=scheduled[rid] for x in refs):
            errors.append('prd.delivery_slices:dependency-order')
    return missing,errors


def readiness(brief):
    if not isinstance(brief,dict):
        return {'status':'INVALID','missing':[],'errors':['brief:not-object'],'open_material_decisions':0,'material_assumptions':0,'mode':'STANDARD'}
    missing=[]; errors=[]
    mode=brief.get('mode','STANDARD')
    if not isinstance(mode,str) or mode not in VALID_MODES: errors.append('mode:invalid')
    risk=brief.get('risk_level','LOW')
    if not isinstance(risk,str) or risk not in VALID_RISK: errors.append('risk_level:invalid')
    for key in REQUIRED_TEXT:
        if not _text(brief.get(key)): missing.append(key)
    ok, errs=_deliverables(brief.get('deliverables'))
    if not ok:
        if 'deliverables:missing' in errs: missing.append('deliverables')
        errors.extend(e for e in errs if e!='deliverables:missing')
    ok, errs=_criteria(brief.get('acceptance_criteria'))
    if not ok:
        if 'acceptance_criteria:missing' in errs: missing.append('acceptance_criteria')
        errors.extend(e for e in errs if e!='acceptance_criteria:missing')
    policy=brief.get('evidence_policy')
    if policy is None or policy=='': missing.append('evidence_policy')
    elif not isinstance(policy,str) or policy not in VALID_POLICIES: errors.append('evidence_policy:invalid')
    decisions, dec_errors=_open_decisions(brief.get('decision_needed'))
    assumptions, asm_errors=_material_assumptions(brief.get('assumptions'))
    invariants, inv_errors=_invariants(brief.get('protected_invariants'))
    errors.extend(dec_errors); errors.extend(asm_errors); errors.extend(inv_errors); errors.extend(_version_errors(brief)); errors.extend(_rubric_lock_errors(brief))
    if mode=='DEEP':
        if not _text(brief.get('use_moment')): missing.append('use_moment')
        if not _text(brief.get('scope')): missing.append('scope')
        if isinstance(risk,str) and risk in {'HIGH','CRITICAL'} and not invariants: missing.append('protected_invariants')
    prd_missing, prd_errors=_prd_profile(brief)
    missing.extend(prd_missing); errors.extend(prd_errors)
    if errors:
        return {'status':'INVALID','missing':sorted(set(missing)),'errors':errors,'open_material_decisions':len(decisions),'material_assumptions':len(assumptions),'mode':mode if isinstance(mode,str) and mode in VALID_MODES else 'STANDARD'}
    if missing:
        return {'status':'BLOCKED','missing':sorted(set(missing)),'errors':[],'open_material_decisions':len(decisions),'material_assumptions':len(assumptions),'mode':mode}
    if decisions or assumptions:
        return {'status':'PROVISIONAL','missing':[],'errors':[],'open_material_decisions':len(decisions),'material_assumptions':len(assumptions),'mode':mode}
    return {'status':'READY','missing':[],'errors':[],'open_material_decisions':0,'material_assumptions':0,'mode':mode}


def delta(old,new):
    if not isinstance(old,dict) or not isinstance(new,dict):
        return {'status':'INVALID','material_changes':[],'requires_downstream_revalidation':True,'errors':['brief-delta:not-object']}
    fields=('objective','audience','evidence_policy','scope','use_moment','risk_level','artifact_profile','prd')
    changes=[]
    for field in fields:
        if old.get(field)!=new.get(field): changes.append(field)
    old_criteria, old_criteria_errors=_delta_criteria(old,'old')
    new_criteria, new_criteria_errors=_delta_criteria(new,'new')
    if old_criteria!=new_criteria: changes.append('acceptance_criteria')
    old_inv, old_inv_errors=_delta_invariants(old,'old')
    new_inv, new_inv_errors=_delta_invariants(new,'new')
    if old_inv!=new_inv: changes.append('protected_invariants')
    if old.get('rubric_lock')!=new.get('rubric_lock'): changes.append('rubric_lock')
    errors=old_criteria_errors+new_criteria_errors+old_inv_errors+new_inv_errors
    if errors:
        return {'status':'INVALID','material_changes':[],'requires_downstream_revalidation':True,'errors':errors}
    return {'status':'CHANGED' if changes else 'UNCHANGED','material_changes':changes,'requires_downstream_revalidation':bool(changes),'errors':[]}


def evaluate_case(case):
    if not isinstance(case,dict): return readiness(None)
    if case.get('operation')=='delta': return delta(case.get('old'),case.get('new'))
    return readiness(case.get('input'))
