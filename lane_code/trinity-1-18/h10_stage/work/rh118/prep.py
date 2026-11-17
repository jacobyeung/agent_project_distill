import json,sys,tarfile
from pathlib import Path
L=Path('/scratch/jjyeung/b01ec87a6f29b'); sys.path[:0]=[str(L/'p')]
with tarfile.open('/scratch/jjyeung/orch_n30/h10_stage/work/rh118/0.tgz') as t: cfg=json.load(t.extractfile('9.json'))
inputs=json.load(open('/scratch/jjyeung/orch_n30/h10_stage/work/rh118/1rh.json'))
from orchard_h10.common import sha
for n,f in inputs['files'].items():
    assert Path(f['path']).stat().st_size==f['bytes'] and sha(f['path'])==f['sha256'], n
print('files ok',flush=True)
from orchard_h10.prepare import run
run(cfg,inputs); print('READY',(L/'d/READY.json').read_text(),flush=True)
