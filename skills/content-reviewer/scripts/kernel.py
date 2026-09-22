from __future__ import annotations

SEVERITIES={'BLOCKER','MAJOR','MINOR','NOTE'}
EVIDENCE_KINDS={'OBSERVATION','EXTERNAL','INFERENCE'}
MODES={'LIGHT','STANDARD','DEEP','DELTA'}
AXES={'brief-compliance','reader-value','structure','claim-integrity','actionability','consistency','language-ux'}
GRADE={'D':1,'C':2,'B':3,'A':4}
COVERAGE_STATES={'COVERED','N/A','UNKNOWN'}
FINDING_STATES={'NEW','CARRIED','REOPENED'}


def _text(value): return isinstance(value,str) and bool(value.strip())


def _evidence_ok(ev,candidate_id=None):
    if not isinstance(ev,dict): return False
    if ev.get('kind') not in EVIDENCE_KINDS: return False
    if not _text(ev.get('source')) or not _text(ev.get('locator')): return False
    if candidate_id and ev.get('kind')=='OBSERVATION' and ev.get('candidate_id')!=candidate_id: return False
    return True


def _coverage(rows,required):
    if not isinstance(rows,list): return False,['coverage:not-list'],0
    errors=[]; seen={}; covered=0
    for i,row in enumerate(rows):
        if not isinstance(row,dict): errors.append(f'coverage[{i}]:not-object'); continue
        axis=row.get('axis'); state=row.get('state')
        if axis not in AXES: errors.append(f'coverage[{i}]:axis'); continue
        if axis in seen: errors.append(f'coverage[{i}]:duplicate-axis'); continue
        seen[axis]=row
        if state not in COVERAGE_STATES: errors.append(f'coverage[{i}]:state'); continue
        if state=='N/A' and not _text(row.get('rationale')): errors.append(f'coverage[{i}]:na-rationale')
        if state=='COVERED': covered+=1
    for axis in required:
        if axis not in seen: errors.append(f'coverage:missing:{axis}')
        elif seen[axis].get('state')=='UNKNOWN': errors.append(f'coverage:unknown:{axis}')
    return not errors,errors,covered


def review(payload):
    if not isinstance(payload,dict):
        return {'status':'INVALID','blockers':0,'majors':0,'errors':['payload:not-object'],'coverage_complete':False,'covered_axes':0}
    findings=payload.get('findings')
    if not isinstance(findings,list):
        return {'status':'INVALID','blockers':0,'majors':0,'errors':['findings:not-list'],'coverage_complete':False,'covered_axes':0}
    mode=payload.get('mode','STANDARD')
    errors=[]; seen=set(); fingerprints=set(); blockers=0; majors=0; covered_axes=0; coverage_complete=True
    if mode not in MODES: errors.append('mode:invalid')
    candidate_id=payload.get('candidate_id')
    if candidate_id is not None and not _text(candidate_id): errors.append('candidate_id:invalid')
    enforce_grade=payload.get('enforce_evidence_floor') is True
    required_axes=set(payload.get('required_axes',[])) if isinstance(payload.get('required_axes',[]),list) else set()
    if any(axis not in AXES for axis in required_axes): errors.append('required_axes:invalid')
    if mode=='DEEP' and not required_axes: required_axes=set(AXES)
    if mode in {'DEEP','DELTA'} or payload.get('coverage') is not None:
        ok,cov_errors,covered_axes=_coverage(payload.get('coverage'),required_axes)
        errors.extend(cov_errors); coverage_complete=ok
    for i,finding in enumerate(findings):
        if not isinstance(finding,dict): errors.append(f'{i}:not-object'); continue
        fid=finding.get('finding_id')
        if not _text(fid): errors.append(f'{i}:finding-id')
        elif fid in seen: errors.append(f'{i}:duplicate-id')
        else: seen.add(fid)
        fp=finding.get('fingerprint')
        if fp is not None:
            if not _text(fp): errors.append(f'{i}:fingerprint')
            elif fp in fingerprints: errors.append(f'{i}:duplicate-fingerprint')
            else: fingerprints.add(fp)
        sev=finding.get('severity')
        if sev not in SEVERITIES: errors.append(f'{i}:severity'); continue
        grade=finding.get('evidence_grade')
        if grade is not None and grade not in GRADE: errors.append(f'{i}:evidence-grade')
        if sev in {'BLOCKER','MAJOR'} and enforce_grade:
            minimum='A' if sev=='BLOCKER' else 'B'
            if grade not in GRADE: errors.append(f'{i}:evidence-grade-required')
            elif GRADE[grade]<GRADE[minimum]: errors.append(f'{i}:evidence-grade-below-floor')
        if sev=='BLOCKER': blockers+=1
        if sev=='MAJOR': majors+=1
        axis=finding.get('axis')
        if axis is not None and axis not in AXES: errors.append(f'{i}:axis')
        state=finding.get('finding_status','NEW')
        if state not in FINDING_STATES: errors.append(f'{i}:finding-status')
        if state=='CARRIED' and finding.get('revalidated') is not True: errors.append(f'{i}:carried-without-revalidation')
        if sev in {'BLOCKER','MAJOR'}:
            if not _text(finding.get('locator')) or not _text(finding.get('impact')): errors.append(f'{i}:material-without-locator-impact')
            evidence=finding.get('evidence')
            if not isinstance(evidence,list) or not evidence or not all(_evidence_ok(ev,candidate_id) for ev in evidence): errors.append(f'{i}:material-without-evidence')
        if finding.get('style_preference') is True and sev in {'BLOCKER','MAJOR'} and finding.get('brief_violation') is not True:
            errors.append(f'{i}:taste-cannot-be-material')
        if sev=='BLOCKER' and finding.get('blocks_acceptance') is not True: errors.append(f'{i}:blocker-must-block-acceptance')
    status='INVALID' if errors else ('CHANGES_REQUIRED' if blockers or majors else 'REVIEWED')
    return {'status':status,'blockers':blockers,'majors':majors,'errors':errors,'coverage_complete':coverage_complete and not any(e.startswith('coverage:') for e in errors),'covered_axes':covered_axes,'mode':mode}


def evaluate_case(case):
    if not isinstance(case,dict): return review(None)
    payload=case.get('input')
    if isinstance(payload,dict) and 'findings' in payload: return review(payload)
    return review(None)
