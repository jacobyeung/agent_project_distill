cd /scratch/jjyeung/orch_n30/sb_own400 && sha256sum kit/fov_variants.py kit/build_b.py && nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -B - <<'P'
import json,numpy as np
b=json.load(open('out/BARS_FROZEN.json'))
diffs={};ok=0;n=0;worst=1.0;offd=[]
for r in b['captures']:
  k=r['key']; ra=json.load(open(r['own544']['receipt'])); rb=json.load(open('in/own_400/native/probe/%s/PHASE_COMPLETE.json'%k))
  sa,sb=ra['sources'],rb['sources']
  for f in set(sa)|set(sb):
    if sa.get(f)!=sb.get(f): diffs[f.split('/')[-1]]=diffs.get(f.split('/')[-1],0)+1
  A=np.load(r['own544']['path'])['depth']; B=np.load('in/own_400/native/probe/%s/own.npz'%k)['depth']
  la=np.log(A).reshape(32,-1); lb=np.log(B).reshape(32,-1); la-=la.mean(1,keepdims=True); lb-=lb.mean(1,keepdims=True)
  C=(la@lb.T)/np.outer(np.linalg.norm(la,axis=1),np.linalg.norm(lb,axis=1))
  n+=1; ok+=int((C.argmax(1)==np.arange(32)).all()); worst=min(worst,float(np.diag(C).min())); offd.append(float(np.max(C-np.diag(np.diag(C))-2*np.eye(32))))
  # grid check: spatial transpose/flip would lower correlation
  la2=np.log(A); lb2=np.log(B)
print('captures',n,'anchor argmax all diagonal',ok,'min diag corr',round(worst,4),'max offdiag corr',round(max(offd),4))
print('source files differing (count of captures):',diffs)
k=b['captures'][0]['key']; ra=json.load(open(b['captures'][0]['own544']['receipt'])); rb=json.load(open('in/own_400/native/probe/%s/PHASE_COMPLETE.json'%k))
for f in ra['sources']:
  if ra['sources'][f]!=rb['sources'].get(f): print('A',f,ra['sources'][f][:12])
for f in rb['sources']:
  if rb['sources'][f]!=ra['sources'].get(f): print('B',f,rb['sources'][f][:12])
P
