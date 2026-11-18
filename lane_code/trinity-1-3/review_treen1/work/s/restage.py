import sys,json,os
from pathlib import Path
K=Path('/scratch/jjyeung/orch_n30/review_treen1/work/pkg');sys.path.insert(0,str(K/'work/tree_r1'))
os.environ['R2_FIXTURES']=str(K/'fixtures')
from launch_r1.build import build
I=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/w9f/work/build9fix/inputs')
out=Path('/scratch/jjyeung/orch_n30/review_treen1/work/restage_r1')
r=build(I/'config.json',I,out);print(json.dumps(r))
