#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BUNDLE=ROOT/'bundle'; OUTPUT=BUNDLE/'checksums.json'
def build():
    files={p.relative_to(BUNDLE).as_posix():{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(BUNDLE.rglob('*')) if p.is_file() and p!=OUTPUT and p.name!='.DS_Store'}
    return json.dumps({'schema':'okf-checksums.v1','files':files},indent=2,sort_keys=True)+'\n'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); a=ap.parse_args(); expected=build()
    if a.check:
        ok=OUTPUT.is_file() and OUTPUT.read_text()==expected; print('checksums verified' if ok else 'checksums out of date'); return 0 if ok else 1
    OUTPUT.write_text(expected); print(f'wrote {len(json.loads(expected)["files"]):,} checksums'); return 0
if __name__=='__main__': raise SystemExit(main())
