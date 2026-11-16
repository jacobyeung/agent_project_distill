set +e
R=/scratch/jjyeung/orch_n30/native_r2
ls -la $R/work/obj $R/work/tree 2>&1 | head -40
python3 - <<'PY'
import tarfile,io,json,glob
import numpy as np
G='/scratch/jjyeung/orch_n30/native_r2/work/obj/geometry_8c58df1547371bdb.tar'
t=tarfile.open(G); ns=t.getnames(); print(len(ns), ns[:6])
j=[n for n in ns if n.endswith('.json')]; print('json members',len(j))
for n in j[:1]+[n for n in j if 'RAW' in n or 'MANIFEST' in n.upper()][:2]:
    print('MEMBER',n); print(t.extractfile(n).read()[:2500].decode(errors='replace'))
z=[n for n in ns if n.endswith('.npz')][0]
a=np.load(io.BytesIO(t.extractfile(z).read()))
for k in a.files: print(z,k,a[k].shape,a[k].dtype)
for f in glob.glob('/scratch/jjyeung/orch_n30/native_r2/work/tree/**/tower_read.py',recursive=True)[:1]:
    print('TOWER',f)
    for i,l in enumerate(open(f)):
        if any(s in l for s in ('WEIGHTS_SHA256','CONFIG_SHA256','REVISION','def run','dense_frames','weights_path','hf_hub','repo')): print(i+1,l.rstrip()[:200])
try:
    c=json.load(open('/scratch/jjyeung/orch_n30/native_r2/sub/b07a20b364/CONFIG.json')); print('CONFIG',json.dumps(c)[:3000])
except Exception as x: print('CONFIGERR',x)
PY
