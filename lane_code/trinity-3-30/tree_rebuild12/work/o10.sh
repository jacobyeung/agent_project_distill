P=/project/community/jjyeung; X=$P/okh7/x_22c714e1
cd $X/q/b && timeout 300 python3 -I -s -B - <<'PY'
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
z.json=J()
spec=z.load(Path('/project/community/jjyeung/okh7/x_22c714e1/q/k/p.json'))
print('p_identity',spec.get('p_identity')); print('keys',sorted(spec))
M=Path('/project/community/jjyeung/okh7/h_6ed2c7aa/m400')
values,metadata=z.small_archive(M/'s.tar')
e=json.load(open(M/'e.json'));pins=e['pins']
a=metadata[pins['artifact']['sha256']]
print('artifact',{k:a.get(k) for k in ('step','config_sha256','schema','run')})
print('pins', {k:(v.get('sha256','')[:12], v.get('path','')[-60:]) for k,v in pins.items()})
c=metadata[pins['config']['sha256']]; print('config keys',sorted(c)[:30])
r=json.load(open(M/'r.json')); print('r.json', json.dumps(r)[:600])
PY
