cd /scratch/jjyeung/orch_n30/lever1_c/r2/out; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
import json,collections,math
m=json.load(open('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json'))
caps={c['canonical']:c for c in m['captures']}
c0=[c for c in m['captures'] if c['canonical'].startswith('arkit')][0]
print(sorted(c0.keys()))
for k in c0:
    if any(s in k.lower() for s in ('rot','sky','orient','portrait','hw','size')): print(k, str(c0[k])[:200])
d=json.load(open('K1X.json'))
def mra(p,l):
    if p is None or l is None or l<=0: return 0.0
    r=abs(p-l)/l; return sum(1.0 for t in [0.5+0.05*i for i in range(10)] if r<1-t)/10
print(d['contract'].keys() if isinstance(d['contract'],dict) else '')
# orientation from geometry dict?
g=d['geometry']; k0=next(iter(g)); print('geometry sample', k0, str(g[k0])[:600])
PY
