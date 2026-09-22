from __future__ import annotations
from datetime import datetime

VALID_STATES={'PASS','FAIL','UNKNOWN','N/A'}
CONTROL_SEVERITY={'MINOR','NOTE'}
MODES={'STANDARD','DEEP','DELTA'}
PROFILES={'CUSTOM','GENERAL','EDITORIAL','RESEARCH','SALES','TECHNICAL_DOCS'}
GRADE={'D':1,'C':2,'B':3,'A':4}
HEX64=__import__('re').compile(r'^[0-9a-f]{64}$')
PROFILE_GATES={
 'CUSTOM':set(), 'GENERAL':{'brief_compliance','claim_integrity'},
 'EDITORIAL':{'brief_compliance','claim_integrity','format_qa'},
 'RESEARCH':{'brief_compliance','claim_integrity','references','format_qa'},
 'SALES':{'brief_compliance','claim_integrity','cta_integrity'},
 'TECHNICAL_DOCS':{'brief_compliance','claim_integrity','link_validation'},
}


def _text(value): return isinstance(value,str) and bool(value.strip())


def _dt(value):
    if not isinstance(value,str) or 'T' not in value: return None
    text=value[:-1]+'+00:00' if value.endswith('Z') else value
    try: out=datetime.fromisoformat(text)
    except ValueError: return None
    return out if out.tzinfo is not None else None


def _evidence_ok(ev,candidate_id,contract_id=None):
    if not isinstance(ev,dict): return False
    if not _text(ev.get('source')) or not _text(ev.get('locator')): return False
    if _dt(ev.get('observed_at')) is None: return False
    if ev.get('candidate_id')!=candidate_id: return False
    if contract_id and ev.get('contract_id') not in {None,contract_id}: return False
    return True


def _policy_lock_errors(payload):
    lock=payload.get('policy_lock')
    if lock is None: return []
    if not isinstance(lock,dict): return ['policy-lock:not-object']
    errors=[]
    if not _text(lock.get('pack_id')) or not _text(lock.get('revision')): errors.append('policy-lock:identity')
    if not isinstance(lock.get('sha256'),str) or not HEX64.fullmatch(lock.get('sha256')): errors.append('policy-lock:sha256')
    expected=payload.get('expected_policy_hash')
    if expected is not None and lock.get('sha256')!=expected: errors.append('policy-lock:hash-mismatch')
    if lock.get('locked_before_evaluation') is not True: errors.append('policy-lock:not-prelocked')
    return errors


def _candidate_id(payload):
    candidate=payload.get('candidate')
    if isinstance(candidate,dict) and _text(candidate.get('id')): return candidate.get('id')
    value=payload.get('candidate_id'); return value if _text(value) else None


def _contract_id(payload):
    contract=payload.get('contract')
    if isinstance(contract,dict) and _text(contract.get('id')): return contract.get('id')
    value=payload.get('contract_id'); return value if _text(value) else None


def _traceability(payload,gate_ids,mode):
    criteria=payload.get('criteria_ids')
    if criteria is None and mode!='DEEP': return []
    if not isinstance(criteria,list) or not criteria or not all(_text(x) for x in criteria): return ['criteria_ids:required']
    links=payload.get('traceability')
    if not isinstance(links,list): return ['traceability:not-list']
    errors=[]; mapped=set()
    for i,row in enumerate(links):
        if not isinstance(row,dict): errors.append(f'traceability[{i}]:not-object'); continue
        cid=row.get('criterion_id'); gid=row.get('gate_id')
        if cid not in criteria: errors.append(f'traceability[{i}]:criterion')
        if gid not in gate_ids: errors.append(f'traceability[{i}]:gate')
        if cid in criteria and gid in gate_ids: mapped.add(cid)
    for cid in criteria:
        if cid not in mapped: errors.append(f'traceability:missing:{cid}')
    return errors


def _control_ok(control,i,candidate_id,mode,as_of):
    if not isinstance(control,dict): return [f'control[{i}]:not-object']
    errors=[]
    if control.get('severity') not in CONTROL_SEVERITY: errors.append(f'control[{i}]:severity')
    if control.get('required_gate_bypass') is True: errors.append(f'control[{i}]:required-gate-bypass')
    if not _text(control.get('issue')) or not _text(control.get('owner')) or not _text(control.get('revisit_condition')): errors.append(f'control[{i}]:incomplete')
    if control.get('candidate_id') not in {None,candidate_id}: errors.append(f'control[{i}]:candidate-mismatch')
    waiver=control.get('waiver') is True
    if waiver or mode=='DEEP':
        approved=_dt(control.get('approved_at')); expires=_dt(control.get('expires_at'))
        if approved is None or expires is None or not _text(control.get('approver')): errors.append(f'control[{i}]:governance')
        elif expires<=approved: errors.append(f'control[{i}]:expiry-order')
        elif as_of and expires<=as_of: errors.append(f'control[{i}]:expired')
    return errors


def decide(payload):
    if not isinstance(payload,dict): return {'verdict':'DEFER','errors':['payload:not-object']}
    candidate_id=_candidate_id(payload); contract_id=_contract_id(payload)
    if candidate_id is None or contract_id is None: return {'verdict':'DEFER','errors':['candidate-or-contract-unbound']}
    mode=payload.get('mode','STANDARD'); profile=payload.get('profile','CUSTOM')
    if mode not in MODES: return {'verdict':'DEFER','errors':['mode:invalid']}
    if profile not in PROFILES: return {'verdict':'DEFER','errors':['profile:invalid']}
    as_of=_dt(payload.get('as_of')) if payload.get('as_of') is not None else None
    if payload.get('as_of') is not None and as_of is None: return {'verdict':'DEFER','errors':['as_of:invalid']}
    lock_errors=_policy_lock_errors(payload)
    if lock_errors: return {'verdict':'DEFER','errors':lock_errors}
    minimum_grade=payload.get('minimum_gate_evidence_grade')
    if minimum_grade is not None and minimum_grade not in GRADE: return {'verdict':'DEFER','errors':['minimum-gate-evidence-grade:invalid']}
    gates=payload.get('gates')
    if not isinstance(gates,list): return {'verdict':'DEFER','errors':['gates:not-list']}
    required=[]; gate_errors=[]; seen=set(); by_id={}
    for i,gate in enumerate(gates):
        if not isinstance(gate,dict): gate_errors.append(f'gate[{i}]:not-object'); continue
        gid=gate.get('gate_id')
        if not _text(gid): gate_errors.append(f'gate[{i}]:gate-id')
        elif gid in seen: gate_errors.append(f'gate[{i}]:duplicate-id')
        else: seen.add(gid); by_id[gid]=gate
        state=gate.get('state')
        if state not in VALID_STATES: gate_errors.append(f'gate[{i}]:state'); continue
        if gate.get('required') is True:
            required.append(gate)
            if state=='PASS':
                evidence=gate.get('evidence')
                if not isinstance(evidence,list) or not evidence or not all(_evidence_ok(ev,candidate_id,contract_id) for ev in evidence): gate_errors.append(f'gate[{i}]:pass-without-candidate-evidence')
                if minimum_grade:
                    grade=gate.get('evidence_grade')
                    if grade not in GRADE: gate_errors.append(f'gate[{i}]:evidence-grade-required')
                    elif GRADE[grade]<GRADE[minimum_grade]: gate_errors.append(f'gate[{i}]:evidence-grade-below-floor')
            if state=='N/A':
                if gate.get('na_allowed') is not True: gate_errors.append(f'gate[{i}]:required-na-not-allowed')
                if not _text(gate.get('na_rationale')): gate_errors.append(f'gate[{i}]:na-without-rationale')
    missing_profile=sorted(PROFILE_GATES[profile]-set(by_id))
    if missing_profile: gate_errors.extend(f'profile-missing-gate:{gid}' for gid in missing_profile)
    gate_errors.extend(_traceability(payload,set(by_id),mode))
    if gate_errors: return {'verdict':'DEFER','errors':gate_errors}
    if not required: return {'verdict':'DEFER','errors':['no-required-gates']}
    if any(g.get('state')=='FAIL' for g in required): return {'verdict':'NOT_READY','errors':[]}
    if any(g.get('state')=='UNKNOWN' for g in required): return {'verdict':'DEFER','errors':[]}
    findings=payload.get('findings',[])
    if not isinstance(findings,list): return {'verdict':'DEFER','errors':['findings:not-list']}
    for i,finding in enumerate(findings):
        if not isinstance(finding,dict): return {'verdict':'DEFER','errors':[f'finding[{i}]:not-object']}
        if finding.get('severity') in {'BLOCKER','MAJOR'} and finding.get('open',True) and finding.get('blocks_acceptance',True): return {'verdict':'NOT_READY','errors':[]}
    controls=payload.get('controls',[])
    if not isinstance(controls,list): return {'verdict':'DEFER','errors':['controls:not-list']}
    control_errors=[]
    for i,control in enumerate(controls): control_errors.extend(_control_ok(control,i,candidate_id,mode,as_of))
    if control_errors: return {'verdict':'NOT_READY','errors':control_errors}
    return {'verdict':'READY_WITH_CONTROLS' if controls else 'READY','errors':[],'profile':profile,'mode':mode}


def evaluate_case(case):
    if not isinstance(case,dict): return decide(None)
    return decide(case.get('input'))
