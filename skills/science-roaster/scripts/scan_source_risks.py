#!/usr/bin/env python3
"""Flag source-control and secret-like indicators before review; flags are not vulnerability verdicts."""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
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

def _windows_fd(name,follow:bool,boundary=None):
    """Check the opened Windows handle before reading, including junction escapes."""
    import ctypes
    from ctypes import wintypes
    import msvcrt

    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.CreateFileW.argtypes=(wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE)
    api.CreateFileW.restype=wintypes.HANDLE
    api.GetFileInformationByHandleEx.argtypes=(wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.DWORD)
    api.GetFileInformationByHandleEx.restype=wintypes.BOOL
    api.GetFinalPathNameByHandleW.argtypes=(wintypes.HANDLE,wintypes.LPWSTR,wintypes.DWORD,wintypes.DWORD)
    api.GetFinalPathNameByHandleW.restype=wintypes.DWORD
    api.CloseHandle.argtypes=(wintypes.HANDLE,)
    api.CloseHandle.restype=wintypes.BOOL
    handle=api.CreateFileW(str(name),0x80000000,7,None,3,0x02000000|(0 if follow else 0x00200000),None)
    if handle==wintypes.HANDLE(-1).value: return None
    try:
        attributes=(wintypes.DWORD*2)()
        if not api.GetFileInformationByHandleEx(handle,9,attributes,ctypes.sizeof(attributes)): return None
        if attributes[0]&0x10 or (not follow and attributes[0]&0x400): return None
        if boundary is not None:
            buffer=ctypes.create_unicode_buffer(32768)
            size=api.GetFinalPathNameByHandleW(handle,buffer,len(buffer),0)
            if not size or size>=len(buffer): return None
            final=buffer.value
            if final.startswith('\\\\?\\UNC\\'): final='\\\\'+final[8:]
            elif final.startswith('\\\\?\\'): final=final[4:]
            final=os.path.normcase(final); boundary=os.path.normcase(str(boundary))
            if os.path.commonpath((final,boundary))!=boundary: return None
        fd=msvcrt.open_osfhandle(handle,os.O_RDONLY|os.O_BINARY)
        handle=None
        return fd
    except (OSError,ValueError): return None
    finally:
        if handle is not None: api.CloseHandle(handle)


def _read_open(name,max_bytes:int,dir_fd=None,follow:bool=False,boundary=None):
    """Open, then check what was opened: fstat on the descriptor, not a stat of the path.

    Returns bytes, or None when the file is not a regular file, is over max_bytes, or
    cannot be read. O_NOFOLLOW refuses a symlink swapped in after the walk listed the
    name; O_NONBLOCK keeps a FIFO swapped in from blocking the scan.
    """
    try: fd=_windows_fd(name,follow,boundary) if os.name=='nt' else os.open(name,_OPEN_FLAGS|(0 if follow else _NOFOLLOW),dir_fd=dir_fd)
    except OSError: return None
    if fd is None: return None
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
    to it; Windows checks the final handle path before reading any content.
    """
    if root.is_file(): yield root,_read_open(root,max_bytes,follow=True); return
    n=0
    top=os.path.realpath(root)
    if os.name=='nt':
        for base,dirs,names in os.walk(top):
            kept=[]
            for directory in sorted(dirs):
                try: st=os.lstat(os.path.join(base,directory))
                except OSError: continue
                if directory not in IGNORE and not st.st_file_attributes&0x400: kept.append(directory)
            dirs[:]=kept
            for name in sorted(names):
                path=Path(base)/name
                try: st=path.lstat()
                except OSError: continue
                if not stat.S_ISREG(st.st_mode) or st.st_file_attributes&0x400: continue
                yield root/path.relative_to(top),_read_open(path,max_bytes,boundary=top); n+=1
                if n>=max_files: return
        return
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

def _atomic_write(path: Path, text: str) -> None:
    """Write output without following a planted output symlink."""
    if path.is_symlink():
        raise ValueError("output must not be a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('path',type=Path); ap.add_argument('--max-files',type=int,default=5000); ap.add_argument('--max-bytes',type=int,default=2_000_000); ap.add_argument('--output',type=Path); a=ap.parse_args()
    if not a.path.exists(): raise SystemExit(f'path not found: {a.path}')
    out=scan(a.path,a.max_files,a.max_bytes); text=json.dumps(out,indent=2,ensure_ascii=False)+'\n'
    if a.output:
        try:
            _atomic_write(a.output, text)
        except (OSError, ValueError) as exc:
            print(f'error: {exc}', file=sys.stderr)
            return 2
        print(f'OK: wrote {a.output}')
    else:
        print(text,end='')
    return 0
if __name__=='__main__': raise SystemExit(main())
