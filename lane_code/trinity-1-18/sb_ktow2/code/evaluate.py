"""Shared CPU pricing helpers; v2 entry point is evaluate_v2.py."""
from common import *
import numpy as np
from metrics import K,mean
OUT=ROOT/'out/tower_frames'

def scored(rows,arm,lab):
 out=[]
 for r in rows:
  x=dict(r,arm=arm)
  if r['row_id'] not in lab:x.update(status='MISSING',missing='corrected label '+r['row_id'],score=None)
  else:x.update(label=lab[r['row_id']],score=100*K.mra(r['prediction'] if r['prediction'] is not None else float('nan'),lab[r['row_id']]))
  out.append(x)
 return out


def paired_scores(base,other):
 lookup={r['row_id']:r for r in base};out=[]
 for r in other:
  a=lookup.get(r['row_id'])
  if a is None or r.get('score') is None or a.get('score') is None:continue
  assert r['room']==a['room'] and r['split']==a['split']
  out.append(dict(r,delta=r['score']-a['score']))
 return out


def geometry(tw,own,depth_slots=None):
 from e2e_reader.geometry import from_tower
 from e2e_reader.stage1 import median_ratio
 slots=tw.get('depth_slots',tw['anchor_slots']) if depth_slots is None else depth_slots
 anchors=tw['anchor_slots'];lookup={int(s):i for i,s in enumerate(tw.get('depth_slots',anchors))};where=[lookup[int(i)] for i in anchors]
 scale=median_ratio(tw['depth_grid'][where],tw['depth_conf_grid'][where],own['depth'])
 hw=tw.get('source_hw')
 if hw is None:raise ValueError('MISSING source_hw from tower PHASE_COMPLETE.json')
 geo=from_tower(tw['raw_pose'],slots,tw['frame_indices'],tw['depth_grid'],tw['grid_uv'],own['gravity'],scale,hw)
 return geo,scale


def stored_tower(c):
 folder=capdir(c,'/scratch/jjyeung/k1/run_tower_sam_2');tw=npz(folder/'tower.npz');rec=read_json(folder/'PHASE_COMPLETE.json')
 assert rec['capture_sha256']==digest(c)
 assert INPUTS[str(local(folder/'tower.npz'))]==rec['files']['tower.npz']
 tw['source_hw']=np.array(rec['source_hw']);return tw


def emit(name,rows,status='OK',**extra):
 write_json(OUT/name,dict(status=status,rows=rows,**extra))


def items_file(rows,part,split):
 path=OUT/f'PER_ITEM_{part}_{split}.jsonl'
 with path.open('w') as f:
  for r in rows:f.write(json.dumps(clean(dict(r,input_sha256=dict(INPUTS))),sort_keys=True,allow_nan=False)+'\n')
 # Canonical combined output is rebuilt only from lane-owned, hashed part receipts.
 allrows=[]
 for p in sorted(OUT.glob('PER_ITEM_*_*.jsonl')):
  sha(p);allrows.extend(p.read_text().splitlines())
 (OUT/'PER_ITEM.jsonl').write_text('\n'.join(allrows)+'\n' if allrows else '')


def diagnostics(rows):
 operands=[f for r in rows for f in r['printed_frames']];bands={}
 for low,high,name in [(0,1,'0'),(1,2,'1'),(2,3,'2'),(3,5,'3-4'),(5,10**9,'5+')]:
  rr=[r for r in rows if low<=r['min_member_frames']<high];bands[name]=dict(n=len(rr),score=mean([r['score'] for r in rr if r.get('score') is not None]))
 return dict(operands=len(operands),share_three_plus=sum(len(v)>=3 for v in operands)/len(operands) if operands else None,by_minimum_member_frames=bands)


