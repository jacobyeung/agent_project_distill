python3 - <<'PYEOF'
import json,base64,glob,os,re
K='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go'; O='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out'
pats=['000414','checkpoint_000','rng0','complete.json','m600','0db794d9','673c147c','419db274','121b35be','08ea4fa7','02bd40e2','6ed2c7aa_m600','/A.json','s.tar','dcd49569','87b68303','bd41c00d','2e0743c3','4f7fe483']
files={}
for f in sorted(glob.glob(K+'/k/*.json'))+[K+'/BUILD.json',K+'/SHA256SUMS.txt']+sorted(glob.glob(O+'/UPLOADS_*.json'))+sorted(glob.glob(O+'/UPLOADS_*.list')):
    raw=open(f).read()
    try:
        v=json.loads(raw); txt=base64.b64decode(v['payload']).decode() if isinstance(v,dict) and 'payload' in v else raw
    except Exception: txt=raw
    files[f.replace(O+'/','')]=txt
for b in sorted(glob.glob(K+'/b/*')): files[b.replace(O+'/','')]=open(b,errors='replace').read()
for p in pats:
    for f,t in files.items():
        n=t.count(p)
        if n:
            i=t.find(p); print(f'{p} | {f} | {n} | ...{t[max(0,i-200):i+120]!r}'[:520])
PYEOF
