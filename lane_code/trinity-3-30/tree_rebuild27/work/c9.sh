cd /scratch/jjyeung/orch_n30/tree_rebuild10_w/w27fix && /scratch/jjyeung/envs/p1cpu/bin/python -I -B - <<'PY'
import sys,re
sys.path.insert(0,'n_go/b')
import z
from pathlib import Path
d=z.load(Path('n_go/k/l.json'))
def walk(v,path):
    if isinstance(v,dict):
        for k,x in v.items(): walk(x,path+'.'+str(k))
    elif isinstance(v,list):
        for i,x in enumerate(v): walk(x,path+'['+str(i)+']')
    elif isinstance(v,str) and v.startswith('/project'):
        if 'l_94a76bda/in/cr/' not in v: print(path[:70],'=',v[:170])
walk(d,'l')
print('TOPKEYS',list(d) if isinstance(d,dict) else type(d))
PY
grep -n "l.json\|\"small\"\|'small'" n_go/job.sh | head -12 | cut -c1-200
