from pathlib import Path
import json,sys
L=Path(__file__).resolve().parents[2];sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import load,pinned
c=load(L/'work/build21/inputs/config.json')
for k in ('row_sources','routing_inputs','source_membership','extent_receipt','row_slice_inputs'):
    v=c['r1_training'].get(k,c.get(k));print(k,json.dumps(v)[:2500])
    if k=='row_sources':print('sources',json.dumps(load(pinned(v)))[:3000])
u=Path('/scratch/jjyeung/orch_n30/sb_k1list/out/u2.json');print('u2',u.stat().st_size)
with u.open() as f:print('first',next(f)[:500])
