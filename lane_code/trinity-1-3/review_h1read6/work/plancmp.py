import json,sys,hashlib
from pathlib import Path
K='/scratch/jjyeung/orch_n30/cont_ops/work/h1read'
ROOT=Path(sys.argv[1]); sys.path.insert(0,str(ROOT/'kit/launcher'))
import orchard_launcher as L, binding as B
out=Path(sys.argv[2]); out.mkdir(exist_ok=True)
for b in sorted(Path(K+'/kit/build').iterdir()):
    c=json.loads((b/'CONFIG.json').read_text()); s=c['spec']; eb=s['export_binding']
    gen=eb['generation'] if eb['generation'] in B.STOPS else None
    try:
        n=L.prepare(c['token'],out/b.name,s['step'],run=eb['run'],families=c['families'],generation=gen,types=c.get('types'))
    except Exception as e:
        print(b.name,'REFUSED',e); continue
    same_spec=L.canonical(c['spec'])==L.canonical(n['spec']) and json.dumps(c['spec'],sort_keys=True)==json.dumps(n['spec'],sort_keys=True)
    diff=sorted(k for k in set(c)|set(n) if c.get(k)!=n.get(k))
    batch=(b/'BATCH.sh').read_bytes()==(out/b.name/'BATCH.sh').read_bytes()
    print(b.name,eb['run'],s['step'],c['families'],c.get('types'),'spec_equal',same_spec,'plan_sha_equal',c['plan_sha256']==n['plan_sha256'],'cfg_diff',diff,'batch_equal',batch)
