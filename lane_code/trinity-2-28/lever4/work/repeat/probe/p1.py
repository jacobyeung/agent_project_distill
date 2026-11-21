import sys,importlib.util,json
spec=importlib.util.spec_from_file_location('relift','/scratch/jjyeung/orch_n30/lever4/work/repeat/kit/r1/relift.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);R.dependencies()
K='/scratch/jjyeung/orch_n30/lever4/work/repeat/kit/r1/returned/'
rc=json.loads(open(K+'4.json').read())
rows=list(R.Records(K+'0.gz',rc))
r=rows[0]
print(len(rows),list(r.keys()))
md=r['metadata'];print(list(md.keys()));g=md['geometry'];print({k:(type(v).__name__, len(v) if isinstance(v,list) else v) for k,v in g.items()})
print(json.dumps(r['parity'])[:600])
print({k:r[k] for k in r if k not in ('arrays','metadata','parity')})
import numpy as np
print(np.asarray(g['camera_to_world_metric']).shape,np.asarray(g['K']).shape, g.get('scale'))
