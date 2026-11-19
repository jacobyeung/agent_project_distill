"""Materialize the frozen GPU inventory and SAM environment on local disk; no network."""
import hashlib
import json
import os
from pathlib import Path
import shutil
ROOT = Path(__file__).resolve().parent
ENV = Path('/scratch/jjyeung/envs/sam3_capretry_native_v1')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20), b''): h.update(chunk)
    return h.hexdigest()


def main():
    old = ROOT/'out/STAGING_GATE_INPUT.json'
    source_hash = sha(old)
    inventory = json.loads(old.read_text())['inventory']
    files = {}
    for row in inventory:
        src=Path(row['path'])
        oldroot='/scratch/jjyeung/orch_n30/sb_ph2gate'
        if str(src).startswith(oldroot+'/'):
            src=ROOT/src.relative_to(oldroot)
        dest=src if src.is_relative_to(ROOT) else ROOT/'payload/files'/str(src).lstrip('/')
        files[src]=(dest,row['roles'])
    for base, dirs, names in os.walk(ENV):
        dirs[:]=[d for d in dirs if d != '__pycache__']
        for name in names:
            p=Path(base)/name
            if p.suffix != '.pyc': files[p]=(ROOT/'payload/environment'/p.relative_to(ENV), ['sam_environment'])
    for p in sorted((ROOT/'sb_mask_phrase/part2').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            files[p]=(p,['control'])
    for name in ('DECISION.json',):
        p=ROOT/'sb_mask_phrase/out'/name; files[p]=(p,['plan_input','control'])
    rows=[]
    for i,(src,(dest,roles)) in enumerate(sorted(files.items())):
        if not src.is_file():
            rows.append(dict(path=str(src),staged_path=str(dest.relative_to(ROOT)),roles=roles,bytes=None,status='MISSING'))
            continue
        if not str(src.resolve()).startswith('/scratch/'):
            raise RuntimeError(f'External symlink requires explicit staging review: {src} -> {src.resolve()}')
        if src != dest:
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dest,follow_symlinks=True)
        rows.append(dict(path=str(src),staged_path=str(dest.relative_to(ROOT)),roles=roles,bytes=dest.stat().st_size,
                         sha256=sha(dest),status='PASS'))
        if i % 10000 == 0: print('staged',i,flush=True)
    record=dict(status='PASS' if all(r['status']=='PASS' for r in rows) else 'MISSING',inventory=rows,
                input_sha256={str(old):source_hash,str(Path(__file__)):sha(Path(__file__))})
    (ROOT/'out/STAGING_MATERIALIZED.json').write_text(json.dumps(record,indent=1)+'\n')
    print('materialized files',len(rows),'bytes',sum(r['bytes'] or 0 for r in rows),flush=True)

if __name__=='__main__': main()
