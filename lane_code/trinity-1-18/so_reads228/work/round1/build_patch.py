"""Produce an additive patch against the supplied A10b tree, without Git."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');K=L/'work/round1/kit'
base='/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b'
paths=[p for p in K.iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.md') and p.name not in ('REPORT.md','ASSET_BUILD.json','DELIVERY_MANIFEST.json')]
for folder in ('tests','reference','so_read','evidence'):
    paths.extend(p for p in (K/folder).rglob('*') if p.is_file())
files={};lines=[]
for p in sorted(paths):
    raw=p.read_text();rel=str(p.relative_to(K));files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    lines.extend(difflib.unified_diff([],raw.splitlines(keepends=True),fromfile='/dev/null',tofile='b/read228/'+rel))
out=K/'patches';out.mkdir(exist_ok=True);path=out/'01_trinity_adapter.diff';path.write_text(''.join(lines))
(out/'MANIFEST.json').write_text(json.dumps(dict(schema=2,base=base,changes_existing_files=False,
    activation='New adapter entry points only; observation requires --observe, runtime path relocation requires --relocate-runtime, cache overlays default OFF.',
    patch=dict(path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),files=files,
    assets='A10b package/source are exact supplied bytes. Use delivered A10b/ or bootstrap228.py --input-A10b SOURCE --out DEST.'),sort_keys=True,indent=2)+'\n')
print(subprocess.check_output(['date','-u'],text=True).strip())
print(json.dumps(dict(files=len(files),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),changes_existing_files=False)))
