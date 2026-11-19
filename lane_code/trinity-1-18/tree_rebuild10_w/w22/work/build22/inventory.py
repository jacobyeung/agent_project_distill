from pathlib import Path
import json,sys,hashlib
L=Path(__file__).resolve().parents[2];sys.path[:0]=[str(L/'work/build21'),str(L/'work/tree_r1')]
import joblib as J
paths=['/scratch/jjyeung/orch_n30/sb_rowA/out/CAMERA_ROWS.jsonl','/scratch/jjyeung/orch_n30/sb_rowA/out/WORDINGS.json','/scratch/jjyeung/orch_n30/sb_rowD7f/out/NEW_ROWS.jsonl','/scratch/jjyeung/orch_n30/sb_rowD7f/out/SOURCE_MAP.jsonl','/scratch/jjyeung/orch_n30/sb_d7bind/BINDING.jsonl','/scratch/jjyeung/orch_n30/sb_d7bind/BINDING_CHECKS.json','/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_an/V7_ROWS_NAMING_REMOVE.json']
out={}
for raw in paths:
 p=Path(raw);out[p.name]=dict(path=raw,bytes=p.stat().st_size,sha256=J.sha(p))
 print(p.name,out[p.name])
 if p.suffix=='.jsonl':
  with p.open() as f:r=json.loads(next(f))
  print('sample',json.dumps(r,ensure_ascii=False)[:2200])
 else:
  v=J.load(p);print('shape',[(k,type(x).__name__,len(x) if isinstance(x,(list,dict,str)) else x) for k,x in v.items()])
  if p.name=='WORDINGS.json':print('heldout', {k:v[k] for k in v if 'held' in k})
cfg=J.load(L/'work/build21/inputs/config.json')
p=Path(cfg['streams']['vqa']['path']);v=J.load(p);print('vqa',v['database'])
out['vqa']=v['database']
J.write(L/'work/build22/INVENTORY.json',out)
