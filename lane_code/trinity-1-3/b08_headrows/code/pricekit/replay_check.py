"""Check the mask adapter against the existing pricing contexts on real local GT."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from kitlib import *
import price_masks as P,collections
ROOT=Path('/scratch/jjyeung/orch_cd');out=HERE.parent/'out'
caps=rows(ROOT/'devs1_price/out/CAPTURES.jsonl');tasks=rows(ROOT/'devs1_price/out/ITEMS.jsonl');ref={(r['qid']):r for r in rows(ROOT/'devs1_price/out/PER_ITEM.jsonl') if r['source']=='g3t' and r['policy']=='frozen'}
chosen={}
for c in caps:
 ds=c['scene'].split('/')[0]
 for q in tasks:
  if q['scene']==c['scene'] and q['stratum']=='primary' and (ds,q['question_type']) not in chosen:chosen[ds,q['question_type']]=(c,q)
by=collections.defaultdict(list)
for c,q in chosen.values():by[c['scene']].append((c,q))
checks=[]
for scene,qs in by.items():
 c=qs[0][0];ds,sid=scene.split('/');gt,Kgt=P.L.load_base(c['pricing_gt'],c['anchor_indices']);gt.dataset=ds
 depth,pose,Ks=P.DP.tower_raw(ROOT/'devs1_price/work/exports/devs1_r2',ds,sid,c['group'],'g3t',c['anchor_indices'],gt.depth.shape[1:])
 ground=P.PR.GTGround(gt)
 if ds=='scannet':P.V.use_vocab(ground)
 for _,q in qs:
  objects={n.lower():[{k:gt.inst[k-1]==i for k in range(1,33) if (gt.inst[k-1]==i).any()} for i in ground.instances(n)] for n in q['operands']}
  base=P.base_geometry(depth,pose,Ks);base.valid=gt.valid.copy()
  absolute=q['question_type']=='object_abs_distance'
  raw_ctx=P.context(base,depth,pose,Ks,objects,absolute);raw_pred,raw_err=P.predict(q,raw_ctx)
  ref_ctx=P.L.ctx(gt,depth,pose,Ks,'frozen',absolute);raw_ref,ref_err=P.predict(q,ref_ctx)
  aligned=P.L.G.aligned_pose(pose,gt.c2w,gt.valid,1.)
  ctx=P.context(base,depth,aligned,Ks,objects,absolute);pred,err=P.predict(q,ctx);score=P.T.score(q['question_type'],pred,q['released_answer_in_options'])
  r=ref[q['qid']]
  def close(a,b):
   return (a is None and b is None) or (isinstance(a,str) and a==b) or (isinstance(a,(float,int)) and isinstance(b,(float,int)) and np.isclose(a,b,rtol=1e-5,atol=1e-5))
  checks.append(dict(qid=q['qid'],dataset=ds,type=q['question_type'],pred=pred,reference=r['pred'],score=score,reference_score=r['score'],match=bool(close(pred,r['pred']) and abs(score-r['score'])<1e-10 and close(raw_pred,raw_ref)),raw_pred=raw_pred,raw_reference=raw_ref,raw_aligned_differ=not close(raw_pred,pred),raw_score=P.T.score(q['question_type'],raw_pred,q['released_answer_in_options']),error=err))
  print(ds,q['question_type'],checks[-1]['match'],flush=True)
dump(out/'REPLAY_PARITY.json',dict(checks=checks,passed=sum(r['match'] for r in checks),total=len(checks)))
if not all(r['match'] for r in checks):sys.exit(1)
