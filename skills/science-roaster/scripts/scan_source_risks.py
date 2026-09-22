#!/usr/bin/env python3
"""Flag source-control and secret-like indicators before review; flags are not vulnerability verdicts."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

IGNORE={'.git','node_modules','vendor','dist','build','.venv','venv','__pycache__','.pytest_cache'}
CONTROL=[
 ('ignore_instructions',re.compile(r'(?i)ignore (all |any )?(previous|prior|system|developer) instructions')),
 ('role_override',re.compile(r'(?i)you are now|act as (the )?(system|developer)|replace your instructions')),
 ('tool_coercion',re.compile(r'(?i)(call|invoke|use) (the )?(tool|connector|shell|terminal).*(without|ignore|bypass)')),
 ('secret_request',re.compile(r'(?i)(reveal|print|exfiltrate|send).*(secret|token|password|system prompt|credentials)')),
]
ZERO_WIDTH=re.compile('[\u200b\u200c\u200d\u2060\ufeff]')
SECRET=[
 ('openai_key',re.compile(r'\bsk-[A-Za-z0-9_-]{20,}')),
 ('github_token',re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}')),
 ('aws_access_key',re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
]

def files(root:Path,max_files:int):
    if root.is_file(): yield root; return
    n=0
    for base,dirs,names in os.walk(root):
        dirs[:]=[d for d in sorted(dirs) if d not in IGNORE]
        for name in sorted(names):
            p=Path(base)/name
            if p.is_symlink() or not p.is_file(): continue
            yield p; n+=1
            if n>=max_files: return

def scan(path:Path,max_files:int=5000,max_bytes:int=2_000_000)->dict:
    flags=[]; scanned=0; skipped=0
    for p in files(path,max_files):
        try:
            if p.stat().st_size>max_bytes: skipped+=1; continue
            raw=p.read_bytes()
            if b'\x00' in raw[:4096]: skipped+=1; continue
            text=raw.decode('utf-8','replace'); scanned+=1
        except OSError: skipped+=1; continue
        rel=str(p if path.is_file() else p.relative_to(path))
        for line_no,line in enumerate(text.splitlines(),1):
            if ZERO_WIDTH.search(line): flags.append({'path':rel,'line':line_no,'kind':'zero_width_unicode','excerpt':line[:180]})
            for kind,pat in CONTROL:
                if pat.search(line): flags.append({'path':rel,'line':line_no,'kind':kind,'excerpt':line[:180]})
            for kind,pat in SECRET:
                if pat.search(line): flags.append({'path':rel,'line':line_no,'kind':kind,'excerpt':'[credential-like value redacted]'})
    return {'schema':'cometweb.roaster-source-risk-scan/v1','root':str(path),'files_scanned':scanned,'files_skipped':skipped,'flags':flags,
            'note':'Flags indicate review hazards or credential-like text. They do not establish exploitability, intent, or a defect.'}

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('path',type=Path); ap.add_argument('--max-files',type=int,default=5000); ap.add_argument('--max-bytes',type=int,default=2_000_000); ap.add_argument('--output',type=Path); a=ap.parse_args()
    if not a.path.exists(): raise SystemExit(f'path not found: {a.path}')
    out=scan(a.path,a.max_files,a.max_bytes); text=json.dumps(out,indent=2,ensure_ascii=False)+'\n'
    if a.output: a.output.write_text(text,encoding='utf-8'); print(f'OK: wrote {a.output}')
    else: print(text,end='')
    return 0
if __name__=='__main__': raise SystemExit(main())
