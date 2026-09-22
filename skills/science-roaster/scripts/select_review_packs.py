#!/usr/bin/env python3
"""Select built-in review packs for this standalone skill package."""
from __future__ import annotations
import argparse,json
from pathlib import Path
SKILL_ID='science-roaster'
PACK_DIR=Path(__file__).resolve().parents[1]/'references'/'packs'

def packs():
    rows=[]
    for p in sorted(PACK_DIR.glob('*.json')):
        d=json.loads(p.read_text(encoding='utf-8'))
        if d.get('skill')==SKILL_ID: rows.append(d)
    return rows

def select(text,profile=None,explicit=None):
    explicit=set(explicit or []); lower=text.lower(); out={}
    rows=packs(); by_id={p.get('id'):p for p in rows}
    missing=explicit-set(by_id)
    if missing: raise ValueError('unknown pack(s): '+', '.join(sorted(missing)))
    for pid in explicit: out[pid]=by_id[pid]
    profile_candidates=[p for p in rows if profile and profile in p.get('activation',{}).get('profiles',[])]
    for p in rows:
        a=p.get('activation',{})
        signals=[sig for sig in a.get('signals',[]) if sig.lower() in lower]
        profile_match=bool(profile and profile in a.get('profiles',[]))
        if signals or (profile_match and len(profile_candidates)==1): out[p['id']]=p
    return [out[k] for k in sorted(out)]


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--text',required=True);ap.add_argument('--profile');ap.add_argument('--pack',action='append',default=[]);a=ap.parse_args()
    try: out=select(a.text,a.profile,a.pack)
    except ValueError as e: raise SystemExit(str(e)) from e
    print(json.dumps(out,indent=2,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
