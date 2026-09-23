#!/usr/bin/env python3
"""Build a validated operating brief from supplied records; no live reads or writes.

Only --output persists artifacts, into a new private local directory. This is not
an agent runner, installation check, source authenticator or action executor.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re
import sys

SKILL_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('brief_operator_kernel', SKILL_ROOT/'scripts/operator_kernel.py')
kernel = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_old_bytecode = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _spec.loader.exec_module(kernel)
finally:
    sys.dont_write_bytecode = _old_bytecode
MAX_INPUT = 4 * 1024 * 1024
VERSION = '1.0.0'


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()


def plain(value: object) -> str:
    """Show supplied prose as literal text, not HTML, links, images or Markdown instructions."""
    text = str(value)
    text = ''.join(f'[U+{ord(c):04X}]' if (ord(c)<32 or c in '\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069') else c for c in text)
    text = html.escape(text, quote=False)
    return re.sub(r'([\\`*_{}\[\]()#+.!|>~\-])', r'\\\1', text)


def assemble(payload: dict, *, previous: dict | None = None) -> dict:
    kernel.object_value(payload, 'brief input')
    kernel.check_json(payload)
    source = copy.deepcopy(payload)
    unknowns = kernel.list_value(source.get('unknowns', []), 'unknowns', maximum=3)
    blockers = kernel.unique_rows(source.get('blockers', []), 'blockers')
    # Explicit material gaps and diagnostic blockers cannot be lost at the bridge.
    plan_input = copy.deepcopy(source)
    plan_input['critical_gap_open'] = kernel.flag(source, 'critical_gap_open') or bool(blockers)
    plan_input['material_unknowns_open'] = kernel.flag(source, 'material_unknowns_open') or bool(unknowns)
    plan = kernel.build_plan(plan_input)
    mode = source.get('mode', 'DELTA' if previous is not None else 'STANDARD')
    if mode not in kernel.ALLOWED_MODES or (mode == 'DELTA' and previous is None):
        raise kernel.InputError('DELTA requires a real baseline; use a supported mode')
    immediate = plan['immediate_actions']
    verify_now = [r for r in immediate if r['action_type']=='verify']
    now = [r for r in immediate if r['action_type']=='implement']
    selected = {r['id'] for r in immediate + plan['next_actions']}
    ranked = kernel.rank_candidates(copy.deepcopy(source.get('candidates', [])))['ranked']
    stop = [r for r in ranked if r['action_type']=='stop']
    later = [r for r in ranked if r['id'] not in selected and r['action_type']!='stop']
    coverage = copy.deepcopy(source.get('coverage', {}))
    for lane in ('github','notion','product_context','outcome_data'):
        coverage.setdefault(lane,'unavailable')
    decision = source.get('decision', f"{plan['readiness']['status']}: {len(immediate)} immediate action(s); remaining work follows dependencies and evidence gates.")
    if not kernel.nonempty(decision):
        raise kernel.InputError('decision must be nonempty text when supplied')
    report = {
        'protocol_version':kernel.PROTOCOL_VERSION, 'mode':mode,
        **{key:source[key] for key in ('target','goal','horizon','as_of')},
        'decision':decision, 'decision_origin':'provided' if 'decision' in source else 'derived', 'mutations':'read-only', 'coverage':coverage,
        'readiness':copy.deepcopy(plan['readiness']), 'blockers':copy.deepcopy(blockers),
        'verify_now':verify_now, 'now':now, 'next':plan['next_actions'],
        'later':later, 'stop':stop, 'watch':[], 'unknowns':copy.deepcopy(unknowns),
        'state_items':copy.deepcopy(source.get('state_items',[])),
        'drift':copy.deepcopy(plan['reconciliation']['issues']), 'delegations':[],
        'source_input_hash':kernel.sha256_json(source),
        'plan_input_hash':plan['input_hash'],
        'assessment_scope':'supplied_records_only', 'evidence_authentication':'not_performed',
        'authorization':'not_provided',
    }
    for key in ('environment','revision','config_fingerprint','coverage_exclusions',
                'outcome_required','unresolved_gate','critical_gap_open','material_unknowns_open','material_current_evidence_block','blocker_resolutions'):
        if key in source:
            report[key] = copy.deepcopy(source[key])
    validation = kernel.validate_report(report)
    if validation['status']=='FAIL':
        raise kernel.InputError('generated report did not validate: '+'; '.join(validation['errors']))
    snapshot = kernel.snapshot_report(report)
    delta = None
    if previous is not None:
        baseline,_ = kernel.unwrap_report(previous)
        if kernel.validate_report(baseline)['status']=='FAIL':
            raise kernel.InputError('baseline report does not validate')
        delta = kernel.delta_reports(previous, snapshot)
        if delta['comparison_status']=='comparable' and delta['unverified_removed_blockers']:
            # A disappearance in a comparable baseline is not a closure. Recompute
            # the plan under a derived gap instead of merely warning after NOW.
            guarded=copy.deepcopy(source)
            guarded['critical_gap_open']=True
            guarded['mode']='STANDARD' if mode=='DELTA' else mode
            result=assemble(guarded)
            result['report']['mode']=mode
            result['report']['source_input_hash']=kernel.sha256_json(source)
            result['report']['baseline_guard_ids']=delta['unverified_removed_blockers']
            result['plan']['baseline_guard_ids']=delta['unverified_removed_blockers']
            reason='unverified_baseline_blocker_removal'
            result['report']['readiness']['reasons'].append(reason)
            result['plan']['readiness']['reasons'].append(reason)
            result['validation']=kernel.validate_report(result['report'])
            if result['validation']['status']=='FAIL':
                raise kernel.InputError('baseline-constrained report did not validate')
            result['snapshot']=kernel.snapshot_report(result['report'])
            result['delta']=kernel.delta_reports(previous,result['snapshot'])
            return result
    return {'report':report,'plan':plan,'snapshot':snapshot,'validation':validation,'delta':delta}


LABELS = {
    'pl': {'title':'Plan pracy produktu','scope':'Zakres: dostarczone zapisy; bez weryfikacji produktu na żywo.',
           'goal':'Cel','target':'Produkt / repo','horizon':'Horyzont','time':'Stan na','ready':'Gotowość do planowania',
           'verify':'Sprawdź teraz','now':'Zrób teraz','next':'Następne kroki','later':'Poza bieżącą listą','stop':'Wstrzymane inicjatywy',
           'id':'ID','action':'Działanie','why':'Dlaczego','done':'Warunek zakończenia','evidence':'Dowody','confidence':'Pewność',
           'none':'Brak wskazanych działań.','issues':'Blokady i luki','sources':'Pokrycie źródeł',
           'summary':'Decyzja operacyjna','delta':'Zmiany względem poprzedniej oceny','warning':'Uwagi walidatora',
           'foot':'Raport nie jest zgodą na wdrożenie. Hash potwierdza spójność treści, nie prawdziwość ani autorstwo dowodów.'},
    'en': {'title':'Product operating brief','scope':'Scope: supplied records; no live product verification.',
           'goal':'Goal','target':'Product / repository','horizon':'Horizon','time':'As of','ready':'Planning readiness',
           'verify':'Verify now','now':'Now','next':'Next','later':'Outside the current shortlist','stop':'Stopped initiatives',
           'id':'ID','action':'Action','why':'Why','done':'Done when','evidence':'Evidence','confidence':'Confidence',
           'none':'No actions selected.','issues':'Blockers and gaps','sources':'Source coverage',
           'summary':'Operating decision','delta':'Changes since the previous assessment','warning':'Validator notes',
           'foot':'This is not deployment authorization. Hashes establish content consistency, not evidence truth or authorship.'}
}


def render(result: dict, language: str = 'pl') -> str:
    if language not in LABELS:
        raise kernel.InputError('language must be pl or en')
    labels=LABELS[language]; report=result['report']; plan=result['plan']
    lines=[f"# {labels['title']}",'',labels['scope'],'']
    for field, label in [('target','target'),('goal','goal'),('horizon','horizon'),('as_of','time')]:
        lines += [f"**{labels[label]}:** {plain(report[field])}",'']
    lines += [f"**{labels['ready']}: {report['readiness']['status']}**",'']
    for reason in report['readiness']['reasons']:
        lines += ['- '+plain(reason)]
    lines += ['',f"## {labels['summary']}",'',plain(report['decision'] if report.get('decision_origin')!='derived' or language=='en' else f"{report['readiness']['status']}: liczba działań do podjęcia od razu: {len(plan['immediate_actions'])}. Pozostała praca podlega zależnościom i warunkom dowodowym."),'',f"## {labels['sources']}",'', ('| Źródło | Stan |' if language=='pl' else '| Lane | State |'),'| --- | --- |']
    lines += [f'| {plain(k)} | {plain(v)} |' for k,v in sorted(report['coverage'].items())]
    for field,label in [('verify_now','verify'),('now','now'),('next','next'),('later','later'),('stop','stop')]:
        rows=report[field];lines+=['',f"## {labels[label]}",'']
        if not rows:
            lines.append(labels['none']);continue
        for row in rows:
            lines += [f"### {plain(row['id'])} — {plain(row['action'])}",'',
                      f"{labels['why']}: {plain(row.get('why_now',row.get('rationale','—')))}",'',
                      f"{labels['done']}: {plain(row['done_when'])}",'',
                      f"{labels['confidence']}: {row['confidence']}",'']
            if row.get('depends_on'):
                lines += [('Wymaga: ' if language=='pl' else 'Depends on: ')+plain(', '.join(row['depends_on'])),'']
            for ev in row['evidence']:
                lines += [f"{labels['evidence']}: {plain(ev['source'])} · {plain(ev['locator'])} — {plain(ev['claim'])}",'']
    lines+=['',f"## {labels['issues']}",'']
    diagnostics={
        'blockers':report['blockers'], 'unknowns':report['unknowns'], 'drift':report['drift'],
        'blocked_by':plan['sequence']['blocked_by'],
        'held_by_readiness_action_ids':plan['held_by_readiness_action_ids'],
        'not_shortlisted_ids':[r['id'] for r in report['later']],
    }
    # Literal, escaped text; no executable HTML/Markdown from supplied records.
    for name,value in diagnostics.items():
        if value:lines += [f"**{name}:** {plain(json.dumps(value,ensure_ascii=False,sort_keys=True))}",'']
    if result['delta'] is not None:
        lines+=['',f"## {labels['delta']}",'',plain(json.dumps(result['delta'],ensure_ascii=False,sort_keys=True)),'']
    if result['validation']['warnings']:
        lines+=['',f"## {labels['warning']}",'']+[plain(x) for x in result['validation']['warnings']]
    lines+=['',labels['foot'],'']
    return '\n'.join(lines)


def artifacts(result: dict, *, language: str='pl') -> dict[str, bytes]:
    files={'brief.md':render(result,language).encode(), 'operator-report.json':json_bytes(result['report']),
           'operator-plan.json':json_bytes(result['plan']), 'operator-snapshot.json':json_bytes(result['snapshot']),
           'validation.json':json_bytes(result['validation'])}
    if result['delta'] is not None:files['delta.json']=json_bytes(result['delta'])
    manifest={'schema':'cometweb.operator-brief/v1','generator_version':VERSION,
              'source_input_hash':result['report']['source_input_hash'],
              'files':{n:hashlib.sha256(b).hexdigest() for n,b in sorted(files.items())},
              'runtime_acceptance':'not_assessed','evidence_authentication':'not_performed',
              'authorization':'not_provided'}
    files['BRIEF-MANIFEST.json']=json_bytes(manifest)
    return files


def publish(files: dict[str,bytes], output: Path) -> None:
    """Only a fresh local directory; do not overwrite snapshots or the source skill."""
    output=output.expanduser().absolute()
    if output.exists() and output.is_symlink():
        raise kernel.InputError('output itself must not be a symlink')
    if not output.parent.is_dir():
        raise kernel.InputError('output parent must exist')
    if output.resolve().is_relative_to(SKILL_ROOT):
        raise kernel.InputError('output must be outside the installed skill')
    if any(Path(n).name!=n or n in {'.','..'} for n in files):
        raise kernel.InputError('invalid artifact filename')
    output.mkdir(mode=0o700,exist_ok=False)
    written=[]
    try:
        for name,data in sorted(files.items()):
            target=output/name
            with target.open('xb') as handle:
                written.append(target); handle.write(data)
    except BaseException:
        for path in reversed(written):path.unlink(missing_ok=True)
        output.rmdir()
        raise


def read(path: Path) -> dict:
    path = path.expanduser().absolute()
    if path.is_symlink() or not path.is_file():
        raise kernel.InputError('input must be a regular local file without being a symlink')
    with path.open('rb') as stream:blob=stream.read(MAX_INPUT+1)
    if len(blob)>MAX_INPUT:raise kernel.InputError('input exceeds byte limit')
    value=json.loads(blob,object_pairs_hook=kernel._unique_pairs,parse_constant=kernel._reject_constant)
    kernel.object_value(value,'input');return value


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--previous',type=Path)
    parser.add_argument('--output',type=Path,help='Fresh directory; omit to print without saving')
    parser.add_argument('--language',choices=('pl','en'),default='pl')
    args=parser.parse_args(argv)
    try:
        result=assemble(read(args.input),previous=read(args.previous) if args.previous else None)
        bundle=artifacts(result,language=args.language)
        if args.output is not None:
            publish(bundle,args.output)
            print(json.dumps({'artifact_status':'created','planning_readiness':result['report']['readiness']['status'],
                              'files':sorted(bundle),'authorization':'not_provided'},ensure_ascii=False))
        else:
            print(bundle['brief.md'].decode(),end='')
        # CLI success is artifact generation, not permission to implement or deploy.
        return 0
    except (OSError,ValueError,TypeError,KeyError,RecursionError):
        print(json.dumps({'artifact_status':'not_created','error':'invalid input, baseline, or output destination',
                          'authorization':'not_provided'}),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
