import json, sys, numpy as np
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/lever8/j1/kit')
import j1_common as G
O=Path('/scratch/jjyeung/orch_n30/lever8/j1/out')
dirs=[Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt/t1_gt/gt'),Path('/scratch/jjyeung/orch_n30/cont_ops24_c/gt/arkit_gt/gt'),
      Path('/scratch/jjyeung/orch_n30/lever5/r1x/gt21/t1'),Path('/scratch/jjyeung/orch_n30/lever5/r1x/gt21/ark')]
def gtpath(cap):
    stub=cap.replace('/','__') if not cap.startswith('arkitscenes/') else cap.split('/')[1]
    hit=None
    for d in dirs:
        p=d/(stub+'.npz')
        if p.is_file(): hit=p
    return hit
recs=[json.loads(l) for l in open(O/'ITEMS_J1.jsonl')]
h0={(r['item_id']):r for r in recs if r['arm']=='h0'}
h1={(r['item_id']):r for r in recs if r['arm']=='h1'}
targets=[]
for iid,r in h0.items():
    for o in r['operands']:
        if not o['frames_with_mask']:
            targets.append((r['capture'],iid,o['prompt'],o['instance_id'],o['frames_with_gt']))
print('h0 all-empty operands',len(targets),'over items',len({t[1] for t in targets}), 'unique (capture,prompt,inst)',len({(t[0],t[2],t[3]) for t in targets}))
bycap={}
for t in targets: bycap.setdefault(t[0],[]).append(t)
res=[]
for cap,ts in sorted(bycap.items()):
    d=G.read_json(O/'detect'/(G.stub(cap)+'.json.gz'))
    with np.load(gtpath(cap),allow_pickle=False) as z: inst=z['inst'].copy()
    for (_,iid,prompt,inst_id,fgt) in ts:
        tgt=inst==inst_id
        best=0.;bestcov=0.;nprop=0;bestf=None
        for f,fr in enumerate(d['text'][prompt]):
            g=tgt[f]
            for e in fr:
                nprop+=1
                m=G.unpack(e['mask'])[::2,::2]
                u=np.count_nonzero(m|g); i=np.count_nonzero(m&g)
                v=i/u if u else 0.
                if v>best: best=v;bestf=f+1
                if g.any(): bestcov=max(bestcov,i/g.sum())
        res.append((cap,iid,prompt,inst_id,len(fgt),nprop,round(best,3),round(bestcov,3)))
seen=set()
for r in res:
    k=(r[0],r[2],r[3])
    if k in seen: continue
    seen.add(k); print(*r)
u=[r for r in res if (r[0],r[2],r[3])]
bi=np.array([r[6] for r in res]); 
print('per operand-instance (with duplicates across items): max IoU <0.1:',int((bi<0.1).sum()),' 0.1-0.3:',int(((bi>=0.1)&(bi<0.3)).sum()),' 0.3-0.5:',int(((bi>=0.3)&(bi<0.5)).sum()),' n',len(bi))
print('no proposals at all:',sum(1 for r in res if r[5]==0), ' gt frames 0:',sum(1 for r in res if r[4]==0))
