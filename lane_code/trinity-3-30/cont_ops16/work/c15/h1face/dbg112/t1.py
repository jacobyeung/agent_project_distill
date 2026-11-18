import json,sys,copy,time
from pathlib import Path
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/reader'
sys.path.insert(0,K)
c=json.load(open('/scratch/jjyeung/orch_n30/cont_ops/work/h1read/kit/build/a5f07824bb3/CONFIG.json'))
e=copy.deepcopy(c['extra'])
for n,f in e['files'].items(): f['path']='/scratch/jjyeung/orch_n30/cont_ops/work/h1read/assets/'+n
import x7, read_filter as F
t=time.time()
rows,fr=x7.stage_assets(e,'/scratch/jjyeung/orch_n30/cont_ops/work/h1read/dbg112/w')
print('staged',len(rows),time.time()-t)
p=F.population(rows,c['spec']); print(json.dumps(p)[:400]); print(len(F.select(rows,c['spec'])))
print('spec population', json.dumps(c['spec']['population'])[:400])
