"""In-sample upper bound: fit cue model + per-type threshold on ALL dev-S1 items of the step-544 arm (no hold-out)."""
import json,sys,numpy as np
sys.path.insert(0,'/scratch/jjyeung/orch_n30/b08_headrows/code')
from choice_join import fit_logistic,predict
P='/scratch/jjyeung/orch_n30/b08_headrows/work/join/CHOICE.per_item.jsonl'
rs=[json.loads(l) for l in open(P)]
sc={r['qid']:r for r in rs if r['arm']=='step544'}
cu=[r for r in rs if r['arm']=='cues_step544']
names=json.load(open(P.replace('.per_item.jsonl','.json')))['cue_names']
types=np.array([r['type'] for r in cu]);tn=sorted(set(types))
X=np.array([[r[k] for k in names] for r in cu]);y=np.array([r['head_better'] for r in cu])
T1=np.array([[float(t==u) for u in tn] for t in types])
h=np.array([sc[r['qid']]['fallback'] for r in cu]);d=np.array([sc[r['qid']]['direct'] for r in cu]);b=np.maximum(h,d)
out={}
for v,cols in {'printed':[k for k in names if k not in('prog_direct_disagree','two_call_disagree')],'all':names}.items():
  Xv=np.c_[X[:,[names.index(c) for c in cols]],T1];m=fit_logistic(Xv,y);p=predict(m,Xv)
  for t in tn:
    s=types==t;best=-1
    for th in np.r_[np.inf,np.unique(p[s]),-np.inf]:
      val=np.where(p[s]>=th,h[s],d[s]).mean();best=max(best,val)
    bf=max(h[s].mean(),d[s].mean());out[(v,t)]=(100*best,100*bf,100*b[s].mean(),(best-bf)/(b[s].mean()-bf))
for k,v in out.items():print(k,'policy %.1f fixed %.1f best %.1f share %.2f'%v)
