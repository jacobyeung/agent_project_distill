"""Build the additive adapter patch against the authenticated A10b input, without Git."""
from pathlib import Path
import difflib,hashlib,json,subprocess
L=Path('/scratch/jjyeung/orch_n30/so_reads228');K=L/'work/round4/kit'
paths=[p for p in K.iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.md')
       and p.name not in ('REPORT.md','ASSET_BUILD.json','DELIVERY_MANIFEST.json')]
for folder in ('tests','reference','so_read','evidence'):
    paths.extend(p for p in (K/folder).rglob('*') if p.is_file())
files={};target=K/'patches/01_trinity_adapter.diff'
with target.open('w') as stream:
    for p in sorted(paths):
        raw=p.read_text();rel=str(p.relative_to(K));files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
        stream.writelines(difflib.unified_diff([],raw.splitlines(keepends=True),fromfile='/dev/null',tofile='b/read228/'+rel))
manifest=dict(schema=4,base='/scratch/jjyeung/orch_n30/so_in/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A10b',
    changes_existing_files=False,activation='Explicit adapter entry-point invocation; --observe required for observer; --on cache extension defaults OFF. Sealed files and runtime bytes are unchanged.',
    patch=dict(path=target.name,bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()),files=files,
    assets='Use delivered A10b/ or bootstrap228.py against the authenticated A10b input. Runtime bodies are staged by the coordinator; the patch contains the three full member lists and regression tests.')
(K/'patches/MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
print(subprocess.check_output(['date','-u'],universal_newlines=True).strip())
print(json.dumps(dict(files=len(files),**manifest['patch'],changes_existing_files=False),sort_keys=True))
