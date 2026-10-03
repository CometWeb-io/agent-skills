#!/usr/bin/env python3
"""Flag source-control and secret-like indicators before review; flags are not vulnerability verdicts."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
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

_OPEN_FLAGS=os.O_RDONLY|getattr(os,'O_NONBLOCK',0)|getattr(os,'O_CLOEXEC',0)
_NOFOLLOW=getattr(os,'O_NOFOLLOW',0)

def _read_open(name,max_bytes:int,dir_fd=None,follow:bool=False):
    """Open, then check what was opened: fstat on the descriptor, not a stat of the path.

    Returns bytes, or None when the file is not a regular file, is over max_bytes, or
    cannot be read. O_NOFOLLOW refuses a symlink swapped in after the walk listed the
    name; O_NONBLOCK keeps a FIFO swapped in from blocking the scan.
    """
    try: fd=os.open(name,_OPEN_FLAGS|(0 if follow else _NOFOLLOW),dir_fd=dir_fd)
    except OSError: return None
    try:
        st=os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_size>max_bytes: return None
        chunks=[]; total=0
        while total<=max_bytes:
            chunk=os.read(fd,min(1<<20,max_bytes+1-total))
            if not chunk: break
            chunks.append(chunk); total+=len(chunk)
        return None if total>max_bytes else b''.join(chunks)
    except OSError: return None
    finally: os.close(fd)

def files(root:Path,max_files:int,max_bytes:int):
    """Yield (path, bytes-or-None) for regular files; symlinks and special files are not listed.

    The walk holds a descriptor for each directory (os.fwalk) and opens names relative
    to it, so a directory replaced by a symlink mid-scan cannot redirect the read.
    """
    if root.is_file(): yield root,_read_open(root,max_bytes,follow=True); return
    n=0
    top=os.path.realpath(root)
    for base,dirs,names,dir_fd in os.fwalk(top):
        dirs[:]=[d for d in sorted(dirs) if d not in IGNORE]
        for name in sorted(names):
            try: st=os.stat(name,dir_fd=dir_fd,follow_symlinks=False)
            except OSError: continue
            if not stat.S_ISREG(st.st_mode): continue
            yield root/os.path.relpath(os.path.join(base,name),top),_read_open(name,max_bytes,dir_fd=dir_fd); n+=1
            if n>=max_files: return

def scan(path:Path,max_files:int=5000,max_bytes:int=2_000_000)->dict:
    flags=[]; scanned=0; skipped=0
    for p,raw in files(path,max_files,max_bytes):
        if raw is None or b'\x00' in raw[:4096]: skipped+=1; continue
        text=raw.decode('utf-8','replace'); scanned+=1
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
