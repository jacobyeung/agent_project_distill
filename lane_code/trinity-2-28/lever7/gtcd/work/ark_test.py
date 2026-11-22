import json, sys, glob, os, hashlib
import numpy as np
from PIL import Image
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
cid=sys.argv[1]
c=[x for x in G['captures'] if x['capture']=='arkitscenes/'+cid][0]
base=f'/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/{cid}/{cid}_frames'
rows=np.loadtxt(base+'/lowres_wide.traj')
pngs={round(float(os.path.basename(p)[len(cid)+1:-4]),3):p for p in glob.glob(base+'/lowres_wide/*.png')}
names=sorted(pngs)
print('traj rows',len(rows),'local pngs',len(pngs),'anchor_last',c['anchor_indices'][-1])
for f in c['frames'][:4]:
    i=f['index']
    served=np.asarray(Image.open(f['path']).convert('RGB'))
    ts=round(rows[i,0],3) if i<len(rows) else None
    p=pngs.get(ts)
    # nearest
    near=min(names,key=lambda t:abs(t-rows[i,0])) if i<len(rows) else None
    print('idx',i,'served',served.shape,'traj ts',rows[i,0] if i<len(rows) else None,'exact local',p is not None,'nearest',near)
    p=p or pngs[near]
    src=Image.open(p).convert('RGB'); print(' src size',src.size, Image.open(p).mode)
    best=None
    for rot in [None, Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_270, Image.Transpose.ROTATE_180]:
        s=src.transpose(rot) if rot is not None else src
        for nm,flt in [('nearest',Image.Resampling.NEAREST),('bilinear',Image.Resampling.BILINEAR),('bicubic',Image.Resampling.BICUBIC),('lanczos',Image.Resampling.LANCZOS),('box',Image.Resampling.BOX)]:
            r=np.asarray(s.resize((served.shape[1],served.shape[0]),flt)).astype(int)
            if r.shape!=served.shape: continue
            d=np.abs(r-served.astype(int))
            key=(d.mean(),str(rot),nm,int(d.max()),bool((d==0).all()))
            best=key if best is None or key<best else best
    print(' best',best)
