import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
paths=['/scratch/jjyeung/mask_recall_run/results/dense_aliases/MANIFEST.json','/scratch/jjyeung/mask_recall_run/results/dense_aliases/priced/PER_ITEM.jsonl','/scratch/jjyeung/devs1_exports','/scratch/jjyeung/orch_cd/devs1_price/work/exports/devs1_r2']
for x in paths:
 p=Path(x);print(x,p.exists())
p=Path(paths[0])
if p.exists():
 m=json.loads(p.read_text());print('manifest fields',m.keys())
 for ds in ['scannet','scannetpp','arkitscenes']:
  c=next(c for c in m['captures'] if c['scene'].split('/')[0].startswith(ds));print('capture',c['scene'],c['group'])
  sid=c['scene'].replace('/','__')
  for root in [Path('/scratch/jjyeung/mask_recall_run/results/dense_aliases/candidates'),Path(paths[2])/('heads_'+c['group']+'_vcd'),Path(paths[3])/('heads_'+c['group']+'_vcd')]:print(root/(sid+'.npz'),(root/(sid+'.npz')).exists())
sys.path.insert(0,str(R/'o3_cache/work/kit'))
try:import bindings;print('bindings OK')
except Exception as e:print('bindings ERROR',repr(e))
