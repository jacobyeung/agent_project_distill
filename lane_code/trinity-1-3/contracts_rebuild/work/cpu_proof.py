from pathlib import Path
import sys
import json
import contextlib
L=Path(__file__).resolve().parents[1]
tree,mode=sys.argv[1:3]
sys.path[:0]=[str(L/'work/trees'/tree),str(L/'work/tests')]
from fixtures_contracts import fixture,session,response,CALLS
import numpy as np
try:from trace_format.contracts import contract_epoch
except ImportError:contract_epoch=lambda _:contextlib.nullcontext()
records={}
with contract_epoch(mode!='off'):
    for kind in ('landscape','portrait','nadir','nadir_positive','vertical','inverted','inverted_portrait','rolled','small','mdg'):
        c,make=fixture('landscape' if kind in ('small','mdg') else kind)
        record=dict(source=str(L/'work/tests/fixtures_contracts.py'),plane=float(np.linalg.norm(c.camera_to_world[0,2,:2])),
            optical_horizontal=float(np.linalg.norm(c.camera_to_world[0,:2,2])),margin=float(-c.camera_to_world[0,2,1]),responses={})
        try:
            g=make();record['verdict']='pass'
            s=session(g,L/f'work/tmp/proof_{tree}_{mode}_{kind}',small=kind=='small',policy=kind=='mdg')
            for call in CALLS:
                record['responses'][call]=response(s,call)
        except ValueError as e:record['verdict']=str(e)
        records[kind]=record
(L/f'out/CPU_{tree}_{mode}.json').write_text(json.dumps(records,indent=2))
print({kind:r['verdict'] for kind,r in records.items()})
