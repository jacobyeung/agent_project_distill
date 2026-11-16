"""Frozen candidate/price execution shared by K1 and the read-only dev-S1 replay."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import gate
def pricing(models=None,*,fixture=False):
 sys.path.insert(0,str(gate.ROOT/'mask_recall/out/kit/work'))
 import price_masks as p
 if not fixture and models is None:raise ValueError('K1 requires eligible refitted coefficients')
 if models is not None:p.MODELS=json.loads(Path(models).read_text())
 return p
def price_capture(c,raw,head,exports,items,models=None,*,fixture=False):
 if not fixture and not gate.eligible(*c['scene'].split('/')):raise ValueError('Ineligible capture')
 p=pricing(models,fixture=fixture);ds,scene=c['scene'].split('/');hw=tuple(x//2 for x in c['hw']);p.SG.H,p.SG.W=hw
 depth,pose,Ks=p.DP.tower_raw(exports,ds,scene,c['group'],'g3t',c['anchor_indices'],hw)
 geom=p.SG.GeomTower(head);cs=p.candidates(c,raw,head)
 unique={n:p.selected(cc,geom)[0] for n,cc in cs.items()}
 base=p.base_geometry(depth,pose,Ks);contexts={};out=[]
 for q in items:
  absolute=q['question_type']=='object_abs_distance'
  if absolute not in contexts:contexts[absolute]=p.context(base,depth,pose,Ks,unique,absolute)
  pred,error=(None,'No linked candidate for a required operand') if any(not cs.get(n.lower()) for n in q['operands']) else p.predict(q,contexts[absolute])
  out.append(dict(qid=q['qid'],pred=pred,error=error))
 return out
