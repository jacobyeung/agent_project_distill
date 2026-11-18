import sys,json,os
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_tree10/work/pkg');sys.path.insert(0,str(K/'work/tree_r1'))
os.environ['R2_FIXTURES']=str(K/'fixtures')
from launch_r1.build import build,verify
from launch_r2.build import verify as verify2
I=K/'work/build10/inputs'
out=Path('/scratch/jjyeung/orch_n30/review_tree10/work/restage_r1')
r=build(I/'config.json',I,out)
print(json.dumps(dict(kit_sha=r.get('kit_sha256'),admission=r.get('admission'),go=r.get('GO',r.get('go')),blockers=r.get('blockers'))))
print('verify restaged',verify(out))
print('verify lane r1',verify(Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w10/work/build10/kits/r1')))
for arm in ('a0','a2'): print('verify lane',arm,verify2(Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w10/work/build10/kits')/arm))
