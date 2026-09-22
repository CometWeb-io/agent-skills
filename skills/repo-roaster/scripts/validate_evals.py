#!/usr/bin/env python3
"""Validate one Roaster skill's behavior, trigger, and metamorphic eval corpus."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path

def _text(v): return isinstance(v,str) and bool(v.strip())
def validate(root:Path)->list[str]:
 e=[]; sid=root.name; d=root/'evals'
 try: behavior=json.loads((d/'evals.json').read_text())
 except Exception as x:return [f'evals/evals.json unreadable: {x}']
 if behavior.get('skill_name')!=sid:e.append('evals.json skill_name mismatch')
 rows=behavior.get('evals')
 if not isinstance(rows,list) or len(rows)<24:e.append('evals.json requires at least 24 behavior evals');rows=rows if isinstance(rows,list) else []
 ids=set()
 for i,row in enumerate(rows):
  p=f'evals[{i}]'
  if not isinstance(row,dict):e.append(f'{p} must be object');continue
  rid=row.get('id')
  if rid in ids:e.append(f'{p}.id duplicate')
  ids.add(rid)
  for k in ('prompt','expected_output'):
   if not _text(row.get(k)):e.append(f'{p}.{k} required')
  if not isinstance(row.get('files'),list):e.append(f'{p}.files must be list')
  a=row.get('assertions')
  if not isinstance(a,list) or len(a)<2 or not all(_text(x) for x in a):e.append(f'{p}.assertions requires >=2 strings')
  tags=row.get('tags')
  if not isinstance(tags,list) or not tags or not all(_text(x) for x in tags):e.append(f'{p}.tags requires a non-empty string list')
 try: tr=json.loads((d/'trigger-evals.json').read_text())
 except Exception as x:e.append(f'trigger-evals unreadable: {x}');tr=[]
 if not isinstance(tr,list) or len(tr)<36:e.append('trigger-evals requires at least 36 rows');tr=tr if isinstance(tr,list) else []
 pos=neg=0
 for i,row in enumerate(tr):
  if not isinstance(row,dict) or not _text(row.get('query')) or not isinstance(row.get('should_trigger'),bool):e.append(f'trigger-evals[{i}] invalid');continue
  pos+=row['should_trigger'];neg+=not row['should_trigger']
 if pos<8 or neg<8:e.append('trigger-evals requires >=8 positive and >=8 negative near-misses')
 try: meta=json.loads((d/'metamorphic-evals.json').read_text())
 except Exception as x:e.append(f'metamorphic-evals unreadable: {x}');meta={}
 if isinstance(meta,dict): mr=meta.get('relations')
 else: mr=None
 if not isinstance(mr,list) or len(mr)<12:e.append('metamorphic-evals requires at least 12 relations');mr=mr if isinstance(mr,list) else []
 for i,row in enumerate(mr):
  if not isinstance(row,dict) or not all(_text(row.get(k)) for k in ('id','base_prompt','transformation','invariant')):e.append(f'metamorphic-evals[{i}] invalid')
 # Safety/regression content guards: these are corpus presence checks, not model-level behavior grades.
 tagset={tag for row in rows if isinstance(row,dict) for tag in row.get('tags',[]) if isinstance(tag,str)}
 required_tags={'source_safety','false_positive_control','revision','domain_specific','operational','multi_source','partial_scope'}
 missing_tags=required_tags-tagset
 if missing_tags:e.append('behavior eval taxonomy missing: '+', '.join(sorted(missing_tags)))
 if sid in {'content-roaster','science-roaster'} and 'boundary_handoff' not in tagset:e.append('behavior eval taxonomy requires boundary_handoff')
 if sid=='repo-roaster' and not {'absence_proof','static_runtime'}<=tagset:e.append('repo eval taxonomy requires absence_proof and static_runtime')
 prompts=' '.join(str(x.get('prompt','')) for x in rows if isinstance(x,dict)).lower()
 if not any(k in prompts for k in ('ignore the reviewer','system:','readme says')):e.append('behavior evals require an embedded-instruction/source-injection case')
 if not any(k in prompts for k in ('clean ','no material','well-powered and clean','do not invent','strong tests')):e.append('behavior evals require a clean/restraint case')
 if not any(k in prompts for k in ('re-review','recheck','revision')):e.append('behavior evals require a revision/recheck case')
 return e

def main():
 ap=argparse.ArgumentParser();ap.add_argument('skill_root',nargs='?',type=Path,default=Path(__file__).resolve().parents[1]);a=ap.parse_args();e=validate(a.skill_root)
 if e:
  for x in e: print('FAIL:',x,file=sys.stderr)
  return 1
 print(f'OK: {a.skill_root.name} eval corpus');return 0
if __name__=='__main__':raise SystemExit(main())
