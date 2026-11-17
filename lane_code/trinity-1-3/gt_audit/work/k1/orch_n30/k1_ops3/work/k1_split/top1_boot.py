"""Capture-clustered bootstrap of accept-head top-1, portrait minus landscape ARKitScenes (held-out)."""
import collections,json,sys
from pathlib import Path
import numpy as np
KIT=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work');sys.path[:0]=[str(KIT),str(KIT/'refit')]
import train as T
A=Path(sys.argv[1]);inv=json.loads(Path(sys.argv[2]).read_text())
tr=json.loads((A/'tables/TABLE_RECEIPT.json').read_text());cmap=tr['gt_canvas_map']
models=json.loads((A/'refit/MODELS.json').read_text());cur=json.loads((T.gate.ROOT/'devs1_masks/out/kit/work/vendor/MODELS.json').read_text())
_,g=T.L.load(str(A/'tables/candidates.jsonl'));cs,_=T.split_rows([r for x in g.values() for r in x],inv['pilot']);rows=[r for r in cs['heldout'] if r['y']>=0]
out={}
for tag,m in [('current',cur['accept']),('refit',models['accept'])]:
 p=T.probability(m,rows);grp=collections.defaultdict(list)
 for r,s in zip(rows,p):grp[r['object_id']].append((r,float(s)))
 per=collections.defaultdict(list)
 for o,v in grp.items():
  r=max(v,key=lambda x:(x[1],x[0].get('features',{}).get('peak',0)))[0];sc=r['scene']
  side='portrait' if cmap.get(sc,'identity').startswith('stretch') else ('landscape_arkitscenes' if sc.startswith('arkitscenes/') else None)
  if side:per[(side,sc)].append(r['y'])
 caps={s:[k for k in per if k[0]==s] for s in ('portrait','landscape_arkitscenes')}
 stat=lambda ks:np.mean([y for k in ks for y in per[k]])
 point=stat(caps['portrait'])-stat(caps['landscape_arkitscenes']);rng=np.random.default_rng(20261116);d=[]
 for _ in range(10000):
  d.append(stat([caps['portrait'][i] for i in rng.integers(0,len(caps['portrait']),len(caps['portrait']))])-stat([caps['landscape_arkitscenes'][i] for i in rng.integers(0,len(caps['landscape_arkitscenes']),len(caps['landscape_arkitscenes']))]))
 out[tag]=dict(portrait_minus_landscape_arkit=point,ci95=[float(np.percentile(d,2.5)),float(np.percentile(d,97.5))],captures={s:len(v) for s,v in caps.items()},draws=10000,seed=20261116)
print(json.dumps(out,indent=1))
