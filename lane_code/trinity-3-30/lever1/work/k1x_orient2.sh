cd /scratch/jjyeung/orch_n30/lever1_c/r2/out; nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,collections,numpy as np,os,zipfile
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
caps={c['canonical']:c for c in m['captures']}
d=json.load(open('K1X.json'))
def mra(p,l):
    if p is None or not l: return 0.0
    r=abs(p-l)/l; return sum(1.0 for t in [0.5+0.05*i for i in range(10)] if r<1-t)/10
orient={}
for cap in {r['capture'] for r in d['rows'] if r['dataset']=='arkitscenes'}:
    p=caps[cap]['gt']['path']
    with np.load(p) as z:
        keys=list(z.keys()); a=z['inst'] if 'inst' in keys else z[keys[0]]
        orient[cap]='portrait' if a.shape[-2]>a.shape[-1] else 'landscape'
print('keys', keys, a.shape)
pairs=[('deployed/GT/G3T/own','deployed/G3T/G3T/own'),('GT/GT/G3T/own','GT/G3T/G3T/own'),('deployed/GT/GT/GT','deployed/G3T/G3T/own'),('GT/GT/GT/GT','GT/G3T/G3T/own')]
for split in ('heldout','train'):
  for a,b in pairs:
    acc=collections.defaultdict(list)
    for r in d['rows']:
        if r['split']!=split: continue
        g=orient.get(r['capture'],'scannet/pp') if r['dataset']=='arkitscenes' else 'scannet/pp'
        da=mra(r['cells'][a]['prediction'],r['label'])-mra(r['cells'][b]['prediction'],r['label'])
        acc[g].append(da)
    print(split, a,'-',b, {k:(len(v), round(100*np.mean(v),2)) for k,v in acc.items()})
print(collections.Counter(orient.values()))
PY
