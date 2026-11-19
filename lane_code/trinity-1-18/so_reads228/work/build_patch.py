"""Emit an additive unified diff; no original A4 code or sealed member is changed."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');O=L/'out'
allowed=[]
for p in O.iterdir():
    if p.is_file() and p.suffix in ('.py','.sh','.json','.md') and p.name not in ('REPORT.md','ASSET_BUILD.json'):
        allowed.append(p)
for folder in ('tests','reference','so_read'):
    allowed.extend(p for p in (O/folder).rglob('*') if p.is_file())
lines=[];files={}
for p in sorted(allowed):
    raw=p.read_text();rel=str(p.relative_to(O));files[rel]=hashlib.sha256(raw.encode()).hexdigest()
    lines.extend(difflib.unified_diff([],raw.splitlines(keepends=True),fromfile='/dev/null',tofile='b/read228/'+rel))
target=O/'patches/01_trinity_adapter.diff';target.parent.mkdir(exist_ok=True)
target.write_text(''.join(lines))
(O/'patches/MANIFEST.json').write_text(json.dumps(dict(schema=1,
    base='/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops16/work/c15/r1route/out3/A4',
    changes_existing_files=False,activation='Explicit run228.sh or read228.sh invocation; cache extensions default OFF',
    patch=dict(path=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()),
    files=files,assets='Use delivered A4/ or bootstrap228.py with the supplied A4 mirror; original sealed code is not part of this additive patch.'),indent=2,sort_keys=True)+'\n')
print(subprocess.check_output(['date','-u'],text=True).strip())
print(json.dumps(dict(patch=str(target),files=len(files),bytes=target.stat().st_size,changes_existing_files=False)))
