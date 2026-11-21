"""Synthetic run2 for compare.py: scale one capture's depth by 1.01, rotate one capture's anchor 5 by 0.3 deg."""
import importlib.util,json,hashlib,types,numpy as np
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/lever4/work/repeat')
spec=importlib.util.spec_from_file_location('relift',str(W/'kit/r1/relift.py'))
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);R.dependencies()
src=W/'kit/r1/returned';out=W/'test/perturbed/0.gz'
rows=list(R.Records(src/'0.gz',json.loads((src/'4.json').read_text())))
th=np.radians(.3);Rz=np.array([[np.cos(th),-np.sin(th),0],[np.sin(th),np.cos(th),0],[0,0,1]])
wr=R.fmt.Writer(out)
for row in rows:
    cap=row['metadata']['capture']
    if cap=='scannet/scene0515_00':
        d,uv=R.fmt.decode(row)
        new=R.fmt.encode(types.SimpleNamespace(depth_grid=d*1.01,grid_uv=uv),row['metadata'])
        row=dict(row,**{k:new[k] for k in ('arrays','arrays_sha256','depth_sha256','float16_max_error')})
    if cap=='arkitscenes/42446097':
        g=row['metadata']['geometry']
        for f in ('camera_to_world_metric','camera_to_world_unscaled'):
            C=np.asarray(g[f],float);C[4,:3,:3]=Rz@C[4,:3,:3];g[f]=C.tolist()
    wr.append(row)
wr.close()
h=hashlib.sha256(out.read_bytes()).hexdigest()
(W/'test/perturbed/4.json').write_text(json.dumps(dict(sha256=h,bytes=out.stat().st_size,items=len(rows),verified=True)))
print(h)
