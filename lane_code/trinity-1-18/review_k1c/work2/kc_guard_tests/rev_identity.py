import json,sys,hashlib
from pathlib import Path
WORK=Path('/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard/k1_build/work/kit_k1a/work')
sys.path.insert(0,str(WORK))
import k1_pipeline as K
K._native();B=K.B
import k1_phases as F, k1_guard as guard, gravity_guard as GG
from student_pilot import geometry_profiles as GP
print('GG file',GG.__file__, B.sha(GG.__file__)); print('F file',F.__file__,B.sha(F.__file__))
print('bindings file',B.__file__)
guard.install()
print('validate replaced', GP.GeometryContract.validate.__qualname__)
m=B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json')
assert B.sha('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json').startswith('e684e0c7')
sid=B.source_identity()
base='/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit'
print('sid files',len(sid),'all native under kc baseline',all(not p.startswith('/scratch/jjyeung/orch_n30/review_k1c') for p in sid))
n=0;prod=set();srcs=set()
for c in m['captures']:
    d,r=F.checked_phase(c,'/scratch/jjyeung/k1/run_tower_sam_2','tower_sam');n+=1;prod.add(r['producer_sha256']);srcs.add(json.dumps(r['sources'],sort_keys=True))
o=0
for c in m['captures'][:3]:
    d,r=F.checked_phase(c,'/scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/native/probe','own');o+=1;prod.add(r['producer_sha256']);srcs.add(json.dumps(r['sources'],sort_keys=True))
print('tower',n,'own',o,'producers',prod,'distinct source maps',len(srcs),'== current',srcs=={json.dumps(sid,sort_keys=True)})
