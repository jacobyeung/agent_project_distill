cd /scratch/jjyeung/orch_n30/sb_own400 && ls in/own_400 in/own_400/metadata | head -20; grep -l "boundaries" in/own_400/*.json in/own_400/metadata/* 2>/dev/null | head; grep -o '"[^"]*boundaries.py"[^,}]*' in/own_400/COMPLETE.json in/own_400/metadata/* 2>/dev/null | head -5
ls -la /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/boundaries.py 2>&1; sha256sum /scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a/native_kit/boundaries.py 2>/dev/null | cut -c1-12
nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,numpy as np
b=json.load(open('out/BARS_FROZEN.json')); res={'id':[], 'T':[], 'flipU':[], 'flipV':[]}
for r in b['captures']:
  A=np.log(np.load(r['own544']['path'])['depth']); B=np.log(np.load('in/own_400/native/probe/%s/own.npz'%r['key'])['depth'])
  def c(x,y):
    x=x-x.mean((1,2),keepdims=True); y=y-y.mean((1,2),keepdims=True); return float(((x*y).sum((1,2))/np.sqrt((x*x).sum((1,2))*(y*y).sum((1,2)))).mean())
  res['id'].append(c(A,B)); res['T'].append(c(A,B.transpose(0,2,1))); res['flipU'].append(c(A,B[:,:,::-1])); res['flipV'].append(c(A,B[:,::-1,:]))
r={k:(round(float(np.min(v)),4),round(float(np.median(v)),4),round(float(np.max(v)),4)) for k,v in res.items()}
print('spatial corr min/median/max',r,'identity beats all alternatives in',sum(1 for i in range(len(res['id'])) if res['id'][i]>max(res['T'][i],res['flipU'][i],res['flipV'][i])),'of',len(res['id']))
P
