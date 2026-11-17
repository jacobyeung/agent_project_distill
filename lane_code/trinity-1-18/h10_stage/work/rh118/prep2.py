"""Rehearsal only: redo prepare.run's manifest/binding/settings/READY for new code bytes; restore (stage) already done and unchanged."""
import json,sys,tarfile,inspect
from pathlib import Path
L=Path('/scratch/jjyeung/b01ec87a6f29b'); sys.path[:0]=[str(L/'p')]
with tarfile.open('/scratch/jjyeung/orch_n30/h10_stage/work/rh118/0_446a4323.tgz') as t: cfg=json.load(t.extractfile('9.json'))
inputs=json.load(open('/scratch/jjyeung/orch_n30/h10_stage/work/rh118/1rh.json'))
import orchard_h10.prepare as P
src=inspect.getsource(P.run)
a=src.index("    stage(path('full_weights')"); b=src.index("    sam=dict(")
src=src[:a]+src[b:]
ns=dict(vars(P)); exec(src,ns); ns['run'](cfg,inputs)
print('READY',(L/'d/READY.json').read_text(),flush=True)
