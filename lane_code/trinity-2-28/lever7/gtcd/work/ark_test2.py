import json, sys, glob, os, zlib, struct
import numpy as np, torch, torch.nn.functional as F
from PIL import Image
G=json.load(open('/scratch/jjyeung/orch_n30/lever6/gtc/out/FRAMES_GTC.json'))
cid=sys.argv[1]
c=[x for x in G['captures'] if x['capture']=='arkitscenes/'+cid][0]
base=f'/scratch/jjyeung/orch_n30/cont_ops25_c/arkit_lowres/{cid}/{cid}_frames'
rows=np.loadtxt(base+'/lowres_wide.traj')
pngs={round(float(os.path.basename(p)[len(cid)+1:-4]),3):p for p in glob.glob(base+'/lowres_wide/*.png')}
f=c['frames'][1]; p=pngs[round(rows[f['index'],0],3)]
b=open(f['path'],'rb').read(); i=8; chunks=[]
while i<len(b):
    n,t=struct.unpack('>I4s',b[i:i+8]); chunks.append((t.decode(),n));
    if t in (b'tEXt',b'iTXt',b'zTXt'): print('text',b[i+8:i+8+n][:200])
    if t==b'IHDR': print('IHDR',struct.unpack('>IIBBBBB',b[i+8:i+8+13]))
    i+=12+n
print('chunks',[x for x in chunks if x[0]!='IDAT'][:10],'n_idat',sum(1 for x in chunks if x[0]=='IDAT'), 'idat sizes', sorted(set(x[1] for x in chunks if x[0]=='IDAT'))[:5])
served=np.asarray(Image.open(f['path']).convert('RGB')).astype(np.float64)
src=np.asarray(Image.open(p).convert('RGB'))
t=torch.from_numpy(src).permute(2,0,1)[None].double()
for mode in ['bilinear','bicubic']:
  for aa in [False,True]:
    for ac in [False]:
      r=F.interpolate(t,size=(480,640),mode=mode,align_corners=ac,antialias=aa)[0].permute(1,2,0).numpy()
      r=np.clip(np.round(r),0,255); d=np.abs(r-served); print(mode,aa,round(d.mean(),3),d.max())
# downsample served to 256x192 box and compare to src
ds=np.asarray(Image.fromarray(served.astype(np.uint8)).resize((256,192),Image.Resampling.BOX)).astype(int)
print('served->256 box vs src', np.abs(ds-src.astype(int)).mean())
# per-channel bias
print('mean served',served.mean(axis=(0,1)),'mean src',src.mean(axis=(0,1)))
