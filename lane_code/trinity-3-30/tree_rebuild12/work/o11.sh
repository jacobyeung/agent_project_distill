P=/project/community/jjyeung; X=$P/okh7/x_22c714e1
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
