"""Build an additive patch against the authenticated A10b input; use no Git."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

L=Path('/scratch/jjyeung/orch_n30/so_reads228');K=L/'work/round2/kit'
base='/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b'
paths=[p for p in K.iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.md')
       and p.name not in ('REPORT.md','ASSET_BUILD.json','DELIVERY_MANIFEST.json')]
for folder in ('tests','reference','so_read','evidence'):
    paths.extend(p for p in (K/folder).rglob('*') if p.is_file())
files={};lines=[]
for p in sorted(paths):
    raw=p.read_text();rel=str(p.relative_to(K));files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    lines.extend(difflib.unified_diff([],raw.splitlines(keepends=True),fromfile='/dev/null',tofile='b/read228/'+rel))
out=K/'patches';out.mkdir(exist_ok=True);path=out/'01_trinity_adapter.diff';path.write_text(''.join(lines))
manifest=dict(schema=3,base=base,changes_existing_files=False,
    activation='Invoke the new adapter entry points explicitly; observation requires --observe; optional cache overlays default OFF. No runtime-byte relocation.',
    patch=dict(path=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()),files=files,
    assets='A10b package/source retain exact input bytes. Use delivered A10b/ or bootstrap228.py --input-A10b SOURCE --out DEST.')
(out/'MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(subprocess.check_output(['date','-u'],text=True).strip())
print(json.dumps(dict(files=len(files),**manifest['patch'],changes_existing_files=False),sort_keys=True))
