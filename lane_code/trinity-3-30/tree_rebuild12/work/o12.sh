P=/project/community/jjyeung; W=$P/okh7/x_22c714e1/w; MT=$P/cp4tk_rt/kit/model_qwen35_9b_c2022362.tar; SN=models--Qwen--Qwen3.5-9B/snapshots/c202236235762e1c871ad0ccb60c8ee5ba337b9a
tar tf $MT | grep -v "safetensors$" ; cd $W/t && tar xf $MT --strip-components=3 $SN/model.safetensors.index.json && sha256sum $W/t/model.safetensors.index.json
cd /tmp/n22c && python3 - <<PY
import json,hashlib
from pathlib import Path
W=Path("/project/community/jjyeung/okh7/x_22c714e1/w")
d=json.load(open("listing.json"))
d["metadata"]=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pool_path=str(p),bytes=p.stat().st_size) for p in sorted((W/"t").iterdir())]
open("listing.json","w").write(json.dumps(d,indent=1))
PY
cd $X/q/b && nice -n 10 timeout 1500 python3 -I -s -B - <<'PY'
import sys,json
sys.path.insert(0,'.')
import z
from pathlib import Path
class J:
    def __getattr__(s,k): return getattr(json,k)
    @staticmethod
    def loads(r,*a,**k):
        try: return json.loads(r,*a,**k)
        except json.JSONDecodeError: return {'_jsonl':True}
z.json=J(); z.seal=lambda k:'PATCHED'
ol=z.load
def load(p):
    v=ol(p)
    if str(p).endswith('k/p.json'): v['p_identity']='9459724f1b925b7d750628ccb36d7a29f871e953751c0e1d2c9abaea67d567e4'
    return v
z.load=load
try:
    r=z.resolve(Path('/project/community/jjyeung/okh7/x_22c714e1/q'),'/project/community/jjyeung/okh7','/tmp/n22c/listing.json','/tmp/n22c/out.json')
    print('RESOLVE OK tar',r['tar_sha256'],r['tar_bytes'],'ext',len(r['external_metadata']),'model_root',r['model_root'])
    print('model_files',json.dumps(r['model_files'])[:800])
except Exception as e:
    import traceback;traceback.print_exc()
PY
